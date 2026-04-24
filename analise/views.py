import json
import logging
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count
from django.contrib import messages

# Imports dos Models
from diario.models import Diario, Pergunta, Resposta, SessaoEmocional
from accounts.models import Aluno
from analise.models import AnaliseResposta

# Services
from .services.sentimento_service import analisar_e_salvar
from .services.chat_service import gerar_pergunta_diario

logger = logging.getLogger(__name__)

# --- 1. Regras de Acesso ---
def is_aluno(user):
    return user.is_authenticated and user.tipo_usuario == 'aluno'

def is_educador(user):
    return user.is_authenticated and user.tipo_usuario == 'educador'

aluno_required = user_passes_test(is_aluno, login_url='/login/', redirect_field_name=None)
educador_required = user_passes_test(is_educador, login_url='/login/', redirect_field_name=None)

EMOCOES_ATENCAO = ['triste', 'muito_triste', 'ansioso', 'irritado', 'tristeza', 'medo', 'raiva']

EMOCAO_EMOJI = {
    'muito_feliz': '😄', 'feliz': '😊', 'neutro': '😐',
    'triste': '😢', 'muito_triste': '😭', 'ansioso': '😰',
    'irritado': '😠', 'cansado': '😴', 'alegria': '😊',
    'tristeza': '😢', 'medo': '😨', 'raiva': '😠',
    'surpresa': '😲', 'nojo': '🤢',
}


# --- 2. Chat e Desabafo ---
@login_required
@aluno_required
def enviar_desabafo(request):
    if request.method == "GET":
        diario_id = request.session.get('diario_atual_id')
        mensagem_inicial = "Olá! Este é o seu espaço seguro. Como você está se sentindo hoje?"
        if diario_id:
            try:
                diario = Diario.objects.get(id=diario_id)
                if diario.mensagem_inicial_ia:
                    mensagem_inicial = diario.mensagem_inicial_ia
            except Diario.DoesNotExist:
                pass
        return render(request, 'analise/chat.html', {'mensagem_inicial': mensagem_inicial})

    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            texto_aluno = dados.get('texto_resposta', '').strip()
            diario_id = request.session.get('diario_atual_id')

            if not diario_id:
                return JsonResponse({'erro': 'Sessão expirada.'}, status=400)

            diario_vinculo = Diario.objects.get(id=diario_id)
            
            # 1. Contagem ATUAL de mensagens
            total_mensagens = Resposta.objects.filter(diario=diario_vinculo).count()

            # 2. Salva a resposta do aluno
            nova_resposta = Resposta.objects.create(
                texto_resposta=texto_aluno,
                diario=diario_vinculo,
                pergunta=Pergunta.objects.order_by("?").first()
            )

            # 3. IA de Sentimento
            emocao_ptbr = 'neutro'
            try:
                resultado_ia = analisar_e_salvar(nova_resposta)
                emocao_ptbr = resultado_ia["label"] if resultado_ia else "neutro"
            except: pass

            # 4. Geração de resposta (Agora enviando o diario_id para ter MEMÓRIA)
            perfil = None
            al = getattr(request.user, 'perfil_aluno', None)
            if al:
                perfil = {
                    'nome': request.user.username,
                    'tipo_deficiencia': al.get_tipo_deficiencia_display(),
                    'necessidades_especificas': al.necessidades_especificas
                }
            
            # AQUI: Adicionamos o diario_id para a IA ler o histórico
            resposta_bot = gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil, diario_id=diario_id)

            # 5. Lógica de Encerramento (Sexta interação ou limite atingido)
            novo_total = total_mensagens + 1
            fim_de_sessao = novo_total >= 5

            if fim_de_sessao:
                resposta_bot = (
                    "Agradeço muito por confiar em mim e compartilhar seus sentimentos hoje. "
                    "Nossa conversa de hoje termina aqui, mas lembre-se: eu estarei aqui amanhã se precisar desabafar de novo. "
                    "Se estiver se sentindo muito sobrecarregado, não deixe de procurar o NAPNE. 💙"
                )

            return JsonResponse({
                'sucesso': True,
                'mensagem_aluno': texto_aluno,
                'emocao_detectada': emocao_ptbr,
                'resposta_assistente': resposta_bot,
                'fim_de_sessao': fim_de_sessao,
                'progresso': novo_total  # Enviamos o número para a barra de progresso
            })

        except Exception as e:
            return JsonResponse({'erro': str(e)}, status=500)


# --- 3. NAPNE e Estatísticas (Corrigidos para data_criacao) ---
@login_required
@educador_required
def painel_napne(request):
    hoje = timezone.now().date()
    
    # 1. Alunos ativos hoje (usando o novo campo data_criacao)
    ativos_hoje = SessaoEmocional.objects.filter(data_criacao__date=hoje).values('aluno').distinct().count()
    
    # 2. Lógica para o Card de Alunos que Requerem Atenção
    # Pegamos as sessões de hoje que estão na lista de EMOCOES_ATENCAO
    sessoes_atencao = SessaoEmocional.objects.filter(
        data_criacao__date=hoje, 
        emocao_selecionada__in=EMOCOES_ATENCAO
    ).select_related('aluno__usuario').order_by('-data_criacao')

    # Criamos uma lista processada para o HTML não quebrar e não repetir aluno
    alunos_atencao_processados = []
    ids_vistos = set()

    for sessao in sessoes_atencao:
        if sessao.aluno_id not in ids_vistos:
            alunos_atencao_processados.append({
                'aluno': sessao.aluno,
                'emoji': EMOCAO_EMOJI.get(sessao.emocao_selecionada, '😐'),
                'data': sessao.data_criacao
            })
            ids_vistos.add(sessao.aluno_id)

    # 3. Atividade Recente (Histórico lateral/inferior)
    atividade_recente = []
    recentes_qs = SessaoEmocional.objects.select_related('aluno__usuario').order_by('-data_criacao')[:20]
    
    for sessao in recentes_qs:
        atividade_recente.append({
            'sessao': sessao,
            'emoji': EMOCAO_EMOJI.get(sessao.emocao_selecionada, '😐'),
            'precisa_atencao': sessao.emocao_selecionada in EMOCOES_ATENCAO,
            'nome': sessao.aluno.usuario.get_full_name() if sessao.aluno else 'Aluno desconhecido',
        })

    return render(request, 'analise/painel_napne.html', {
        'total_alunos': Aluno.objects.count(),
        'ativos_hoje': ativos_hoje,
        'precisa_atencao': alunos_atencao_processados, # Agora com os emojis certos!
        'atividade_recente': atividade_recente,
    })


@login_required
@educador_required
def perfil_aluno_napne(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    
    # 1. Busca todas as sessões do aluno (usando o campo corrigido data_criacao)
    sessoes_qs = SessaoEmocional.objects.filter(aluno=aluno).order_by('-data_criacao')
    
    # 2. Cálculos para o cabeçalho
    total_registros = sessoes_qs.count()
    total_alertas = sessoes_qs.filter(emocao_selecionada__in=EMOCOES_ATENCAO).count()
    
    # 3. Lógica do Gráfico (FORA DO LOOP)
    # Pegamos as 10 últimas sessoes e invertemos para a ordem cronológica correta (esquerda para direita)
    grafico_qs = list(sessoes_qs[:10])[::-1] 
    datas_grafico = [s.data_criacao.strftime("%d/%m") for s in grafico_qs]
    
    mapeamento_humor = {
        'muito_feliz': 100, 'feliz': 80, 'neutro': 50, 
        'triste': 30, 'muito_triste': 10, 'ansioso': 25, 'irritado': 20
    }
    scores_grafico = [mapeamento_humor.get(s.emocao_selecionada, 50) for s in grafico_qs]

    # 4. Construção do Histórico (Loop limpo)
    historico = []
    for sessao in sessoes_qs:
        diario = getattr(sessao, 'diario', None)
        analises = []
        
        if diario:
            # select_related evita o problema de N+1 consultas ao banco
            respostas = Resposta.objects.filter(diario=diario).select_related('analiseresposta')
            for resp in respostas:
                try:
                    an = resp.analiseresposta
                    analises.append({
                        'sentimento': an.sentimento_detectado or 'neutro',
                        'score': round((an.score_sentimento or 0) * 100),
                        'texto': resp.texto_resposta,
                    })
                except: 
                    pass

        historico.append({
            'sessao': sessao,
            'analises': analises,
            'emoji': EMOCAO_EMOJI.get(sessao.emocao_selecionada, '😐'),
            'precisa_atencao': sessao.emocao_selecionada in EMOCOES_ATENCAO,
        })

    context = {
        'aluno': aluno, 
        'historico': historico, # Verifique se no HTML você usa 'historico' ou 'sessoes'
        'total_registros': total_registros,
        'total_alertas': total_alertas,
        'datas_grafico': datas_grafico,
        'scores_grafico': scores_grafico,
    }

    return render(request, 'analise/perfil_aluno_napne.html', context)


@login_required
@educador_required
def listar_alunos(request): # REMOVIDO o aluno_id daqui
    buscar = request.GET.get('buscar', '')
    tipo_deficiencia = request.GET.get('deficiencia', '')
    
    # Busca base de todos os alunos
    todos_alunos = Aluno.objects.select_related('usuario').all().order_by('usuario__first_name')
    
    # Aplica os filtros na query geral
    if tipo_deficiencia:
        todos_alunos = todos_alunos.filter(tipo_deficiencia=tipo_deficiencia)
    
    if buscar:
        todos_alunos = todos_alunos.filter(usuario__first_name__icontains=buscar)

    alunos_lista = []
    for a in todos_alunos:
        # Buscamos as sessões deste aluno específico 'a'
        sessoes_aluno = SessaoEmocional.objects.filter(aluno=a).order_by('-data_criacao')
        ultima = sessoes_aluno.first()
        
        # Calculamos o total de registros deste aluno específico
        total_registros_individual = sessoes_aluno.count()

        alunos_lista.append({
            'aluno': a,
            'total_registros': total_registros_individual, # AQUI: O valor para o seu HTML
            'emoji_ultimo': EMOCAO_EMOJI.get(ultima.emocao_selecionada, '😐') if ultima else '',
            'data_ultimo_registro': ultima.data_criacao if ultima else None,
            'precisa_atencao': ultima.emocao_selecionada in EMOCOES_ATENCAO if ultima else False
        })

    return render(request, 'analise/listar_alunos.html', {
        'alunos_lista': alunos_lista,
        'total_alunos': todos_alunos.count(), # Total de alunos cadastrados no sistema
        'tipo_deficiencia': tipo_deficiencia,
        'buscar': buscar,
    })
    
 
    
@login_required
@aluno_required
def historico_emocional(request):
    aluno = getattr(request.user, 'perfil_aluno', None)
    # Ajustado para data_criacao
    sessoes_qs = SessaoEmocional.objects.filter(aluno=aluno).order_by('-data_criacao') if aluno else []
    
    historico = []
    for s in sessoes_qs:
        historico.append({
            'sessao': s,
            'emoji': EMOCAO_EMOJI.get(s.emocao_selecionada, '😐'),
            'precisa_atencao': s.emocao_selecionada in EMOCOES_ATENCAO,
        })
    return render(request, 'analise/perfil_aluno_napne.html', {'sessoes': historico})


@login_required
@educador_required
def estatisticas_gerais(request):
    trinta_dias = timezone.now() - timedelta(days=30)
    # Filtro base usando o campo corrigido data_criacao
    sessoes_qs = SessaoEmocional.objects.filter(data_criacao__gte=trinta_dias)
    
    # 1. KPIs Básicos
    total_registros = sessoes_qs.count()
    alunos_ativos = sessoes_qs.values('aluno').distinct().count()
    alertas_atencao = sessoes_qs.filter(emocao_selecionada__in=EMOCOES_ATENCAO).count()

    # 2. Distribuição para o Gráfico de Pizza/Rosca
    distribuicao = sessoes_qs.values('emocao_selecionada').annotate(total=Count('id')).order_by('-total')
    
    # 3. Cálculo de Níveis Médios (Lógica de Bem-estar)
    # Mapeamos as emoções para pesos de 0 a 100
    mapeamento = {
        'muito_feliz': 100, 'feliz': 80, 'neutro': 50, 
        'triste': 30, 'muito_triste': 10, 'ansioso': 25, 'irritado': 20
    }
    
    # Inicializamos variáveis
    soma_bem_estar = 0
    cont_tristeza = 0
    cont_ansiedade = 0
    
    for s in sessoes_qs:
        peso = mapeamento.get(s.emocao_selecionada, 50)
        soma_bem_estar += peso
        if s.emocao_selecionada in ['triste', 'muito_triste']:
            cont_tristeza += 1
        if s.emocao_selecionada == 'ansioso':
            cont_ansiedade += 1

    # Cálculo das porcentagens para as barras de progresso
    def calcular_porcentagem(parte, total):
        return round((parte / total * 100)) if total > 0 else 0

    bem_estar_medio = round(soma_bem_estar / total_registros) if total_registros > 0 else 0
    nivel_tristeza = calcular_porcentagem(cont_tristeza, total_registros)
    nivel_ansiedade = calcular_porcentagem(cont_ansiedade, total_registros)

    context = {
        'total_registros': total_registros,
        'alunos_ativos': alunos_ativos,
        'alertas_atencao': alertas_atencao,
        'bem_estar_medio': bem_estar_medio,
        'nivel_tristeza': nivel_tristeza,
        'nivel_ansiedade': nivel_ansiedade,
        'labels_dist': [item['emocao_selecionada'].capitalize() for item in distribuicao],
        'valores_dist': [item['total'] for item in distribuicao],
    }
    
    return render(request, 'analise/estatisticas_gerais.html', context)
  
@login_required  
@educador_required
def configuracoes_servidor(request):
    if request.method == 'POST':
        nova = request.POST.get('nova_senha')
        if nova and len(nova) >= 8:
            request.user.set_password(nova)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Senha atualizada!')
    return render(request, 'analise/configuracoes_servidor.html')