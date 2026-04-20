import json
import logging
from pyexpat.errors import messages
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from datetime import timedelta
from diario.models import Diario, Pergunta, Resposta, SessaoEmocional
from accounts.models import Aluno
from analise.models import SessaoEmocional, AnaliseResposta
from django.db.models import Avg, Count
from .services.sentimento_service import analisar_e_salvar
from .services.chat_service import gerar_pergunta_diario

logger = logging.getLogger(__name__)
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

# --- 1. Regras de quem é quem ---
def is_aluno(user):
    return user.is_authenticated and user.tipo_usuario == 'aluno'

def is_educador(user):
    return user.is_authenticated and user.tipo_usuario == 'educador'

# --- 2. Os Decorators (Os "Seguranças") ---
# Se não for aluno, bloqueia.
aluno_required = user_passes_test(is_aluno, login_url='/login/', redirect_field_name=None)

# Se não for educador, bloqueia.
educador_required = user_passes_test(is_educador, login_url='/login/', redirect_field_name=None)

EMOCOES_ATENCAO = ['triste', 'muito_triste', 'ansioso', 'irritado', 'tristeza', 'medo', 'raiva']

EMOCAO_EMOJI = {
    'muito_feliz': '😄', 'feliz': '😊', 'neutro': '😐',
    'triste': '😢', 'muito_triste': '😭', 'ansioso': '😰',
    'irritado': '😠', 'cansado': '😴', 'alegria': '😊',
    'tristeza': '😢', 'medo': '😨', 'raiva': '😠',
    'surpresa': '😲', 'nojo': '🤢',
}


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
            except Diario.DoesNotExist: pass
        return render(request, 'analise/chat.html', {'mensagem_inicial': mensagem_inicial})

    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            texto_aluno = dados.get('texto_resposta', '').strip()

            if not texto_aluno:
                return JsonResponse({'erro': 'O texto não pode estar vazio.'}, status=400)

            diario_id = request.session.get('diario_atual_id')
            if not diario_id:
                return JsonResponse({'erro': 'Sessão expirada.'}, status=400)

            diario_vinculo = Diario.objects.get(id=diario_id)
            
            # 1. Cria o objeto primeiro (necessário para sua função de análise funcionar)
            pergunta_vinculo = Pergunta.objects.order_by("?").first()
            if not pergunta_vinculo:
                pergunta_vinculo = Pergunta.objects.create(texto="Como você está?")

            nova_resposta = Resposta.objects.create(
                texto_resposta=texto_aluno,
                diario=diario_vinculo,
                pergunta=pergunta_vinculo
            )

            # 2. Usa suas funções originais
            resultado_ia = analisar_e_salvar(nova_resposta)
            emocao_ptbr = resultado_ia["label"] if resultado_ia else "neutro"

            respostas_anteriores = Resposta.objects.filter(diario=diario_vinculo).exclude(id=nova_resposta.id).order_by('id')
            historico = []
            for resp in respostas_anteriores:
                historico.append({"papel": "user", "texto": resp.texto_resposta})
                historico.append({"papel": "model", "texto": resp.resposta_ia or "Entendo."})

            perfil_aluno = None
            try:
                aluno = request.user.perfil_aluno
                perfil_aluno = {
                    'nome': request.user.get_full_name(),
                    'tipo_deficiencia': aluno.get_tipo_deficiencia_display(),
                }
            except: pass

            # 3. Chama a IA
            resposta_bot = gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno, historico)

            # 🛡️ PROTEÇÃO: Se a IA falhou, APAGAMOS a resposta do banco
            if "Desculpe, tive um probleminha" in resposta_bot:
                nova_resposta.delete() # Remove para não contar no limite de 5
                return JsonResponse({'erro': 'A IA travou. Tente falar de outra forma.'}, status=500)

            # 4. SUCESSO: Salva a resposta da IA e verifica limite
            nova_resposta.resposta_ia = resposta_bot
            nova_resposta.save()

            total_mensagens = Resposta.objects.filter(diario=diario_vinculo).count()

            if total_mensagens >= 5:
                resposta_bot = "Agradeço por compartilhar. Nossa sessão chegou ao fim. Por favor, procure o NAPNE. 💙"
                nova_resposta.resposta_ia = resposta_bot
                nova_resposta.save()

            return JsonResponse({
                'sucesso': True,
                'mensagem_aluno': texto_aluno,
                'emocao_detectada': emocao_ptbr,
                'resposta_assistente': resposta_bot,
                'fim_de_sessao': total_mensagens >= 5
            }, status=200)

        except Exception as e:
            logger.error(f"Erro na View: {e}")
            return JsonResponse({'erro': 'Erro interno no servidor.'}, status=500)




@educador_required
def painel_napne(request):
    hoje = timezone.now().date()

    total_alunos = Aluno.objects.count()

    registros_recentes = SessaoEmocional.objects.filter(
        data_inicio__gte=timezone.now() - timedelta(hours=48)
    ).count()

    ativos_hoje = SessaoEmocional.objects.filter(
        data_inicio__date=hoje
    ).values('aluno').distinct().count()

    alunos_atencao = []
    for aluno in Aluno.objects.select_related('usuario').all():
        ultima_sessao = SessaoEmocional.objects.filter(
            aluno=aluno
        ).order_by('-data_inicio').first()

        if ultima_sessao and ultima_sessao.emocao_selecionada in EMOCOES_ATENCAO:
            alunos_atencao.append({
                'aluno': aluno,
                'ultima_sessao': ultima_sessao,
                'emoji': EMOCAO_EMOJI.get(ultima_sessao.emocao_selecionada, '😐'),
            })

    atividade_recente = []
    for sessao in SessaoEmocional.objects.select_related('aluno__usuario').order_by('-data_inicio')[:20]:
        atividade_recente.append({
            'sessao': sessao,
            'emoji': EMOCAO_EMOJI.get(sessao.emocao_selecionada, '😐'),
            'precisa_atencao': sessao.emocao_selecionada in EMOCOES_ATENCAO,
            'nome': sessao.aluno.usuario.get_full_name() if sessao.aluno else 'Aluno desconhecido',
        })

    return render(request, 'analise/painel_napne.html', {
        'total_alunos': total_alunos,
        'registros_recentes': registros_recentes,
        'ativos_hoje': ativos_hoje,
        'total_atencao': len(alunos_atencao),
        'alunos_atencao': alunos_atencao,
        'atividade_recente': atividade_recente,
    })


@educador_required
def perfil_aluno_napne(request, aluno_id): # Usei o nome da rota do NAPNE
    aluno = get_object_or_404(Aluno, id=aluno_id)
    
    # 1. Busca todas as sessões
    sessoes_qs = SessaoEmocional.objects.filter(aluno=aluno).order_by('-data_inicio')
    
    total_registro = sessoes_qs.count()
    total_alertas = sessoes_qs.filter(emocao_selecionada__in=EMOCOES_ATENCAO).count()

    sessoes_processadas = []
    for sessao in sessoes_qs:
        analises = []
        # Tenta pegar o diário. Se não houver, o 'hasattr' evita o erro e não pula a sessão
        if hasattr(sessao, 'diario'):
            respostas = Resposta.objects.filter(diario=sessao.diario).prefetch_related('analiseresposta')
            for resp in respostas:
                try:
                    ana = resp.analiseresposta
                    analises.append({
                        'sentimento': ana.sentimento_detectado or 'neutro',
                        'score': round((ana.score_sentimento or 0) * 100),
                        'texto': resp.texto_resposta,
                    })
                except:
                    pass

        sessoes_processadas.append({
            'sessao': sessao,
            'analises': analises,
            'emoji': EMOCAO_EMOJI.get(sessao.emocao_selecionada, '😐'),
            'precisa_atencao': sessao.emocao_selecionada in EMOCOES_ATENCAO,
        })

    # 2. Dados do Gráfico
    historico_reverso = reversed(sessoes_processadas[:10])
    datas_grafico = []
    scores_grafico = []

    for item in historico_reverso:
        datas_grafico.append(item['sessao'].data_inicio.strftime('%d/%m'))
        # Se não houver análise, usamos 50 (neutro) para o gráfico não quebrar
        score = item['analises'][0]['score'] if item['analises'] else 50
        scores_grafico.append(score)

    return render(request, 'analise/perfil_aluno_napne.html', {
        'aluno': aluno,
        'sessoes': sessoes_processadas, # O HTML agora usa 'sessoes'
        'total_registro': total_registro,
        'total_alertas': total_alertas,
        'datas_grafico': datas_grafico,
        'scores_grafico': scores_grafico,
    })


@educador_required
def listar_alunos(request):

    # 1. Filtro de busca (CORREÇÃO DO 'NONE' AQUI 👇)
    buscar_aluno = request.GET.get('buscar', '')
    tipo_deficiencia = request.GET.get('deficiencia', '')

    # 2. Pega todos os alunos do banco
    todos_alunos = Aluno.objects.select_related('usuario').all().order_by('usuario__first_name')

    # O "if" continua funcionando perfeitamente, pois texto vazio ('') é considerado Falso no Python
    if tipo_deficiencia:
       todos_alunos =  todos_alunos.filter(tipo_deficiencia=tipo_deficiencia)

    if buscar_aluno:
        todos_alunos = todos_alunos.filter(usuario__first_name__icontains=buscar_aluno)

    
    # 3. Cria uma lista vazia que vai guardar os "pacotes" de dados de cada aluno
    alunos_lista = []
    
    # 4. Passa por cada aluno para calcular as estatísticas dele
    for aluno in todos_alunos:
        # Busca todas as sessões desse aluno específico, da mais recente para a mais antiga
        sessoes = SessaoEmocional.objects.filter(aluno=aluno).order_by('-data_inicio')
        
        total_registros = sessoes.count()
        ultima_sessao = sessoes.first() # Pega só a primeira da lista (a mais recente)
        
        # Variáveis padrão caso o aluno nunca tenha feito um registro
        precisa_atencao = False
        data_ultimo_registro = None
        emoji_ultimo = ''
        
        # Se o aluno tiver pelo menos um registro, atualizamos as variáveis
        if ultima_sessao:
            data_ultimo_registro = ultima_sessao.data_inicio
            emoji_ultimo = EMOCAO_EMOJI.get(ultima_sessao.emocao_selecionada, '😐')
            
            # Verifica se a última emoção acende o alerta amarelo
            if ultima_sessao.emocao_selecionada in EMOCOES_ATENCAO:
                precisa_atencao = True
                
        # 5. Guarda tudo no dicionário que o nosso HTML está esperando
        alunos_lista.append({
            'aluno': aluno,
            'total_registros': total_registros,
            'data_ultimo_registro': data_ultimo_registro,
            'emoji_ultimo': emoji_ultimo,
            'precisa_atencao': precisa_atencao
        })

    # 6. Envia os dados processados para a tela
    return render(request, 'analise/listar_alunos.html', {
        'alunos_lista': alunos_lista,
        'total_alunos': todos_alunos.count(),
        'buscar_aluno': buscar_aluno,
        'tipo_deficiencia': tipo_deficiencia
    })


@aluno_required
def historico_emocional(request):
    try:
        aluno = request.user.perfil_aluno
    except Exception:
        aluno = None

    sessoes = []

    if aluno:
        sessoes_qs = SessaoEmocional.objects.filter(
            aluno=aluno
        ).order_by('-data_inicio')

        for sessao in sessoes_qs:
            # Busca o diário vinculado
            try:
                diario = sessao.diario
            except Exception:
                continue

            # Busca todas as respostas do diário com suas análises
            respostas = Resposta.objects.filter(
                diario=diario
            ).prefetch_related('analiseresposta')

            analises = []
            for resposta in respostas:
                try:
                    analise = resposta.analiseresposta
                    analises.append({
                        'sentimento': analise.sentimento_detectado or 'neutro',
                        'score': round((analise.score_sentimento or 0) * 100),
                        'texto': resposta.texto_resposta,
                    })
                except Exception:
                    pass

            # Emoção predominante da sessão (maior score)
            emocao_predominante = sessao.emocao_selecionada
            score_predominante = 0
            if analises:
                melhor = max(analises, key=lambda x: x['score'])
                emocao_predominante = melhor['sentimento']
                score_predominante = melhor['score']

            emoji = EMOCAO_EMOJI.get(sessao.emocao_selecionada, '😐')
            precisa_atencao = sessao.emocao_selecionada in EMOCOES_ATENCAO

            sessoes.append({
                'sessao': sessao,
                'diario': diario,
                'analises': analises,
                'emocao_predominante': emocao_predominante,
                'score_predominante': score_predominante,
                'emoji': emoji,
                'precisa_atencao': precisa_atencao,
            })

    return render(request, 'analise/perfil_aluno_napne.html', {
        'sessoes': sessoes,
        'total_sessoes': len(sessoes),
    })


@educador_required
def estatisticas_gerais(request):
    hoje = timezone.now()
    trinta_dias_atras = hoje - timedelta(days=30)

    # 1. Busca sessoes dos últimos 30 dias
    sessoes_periodo = SessaoEmocional.objects.filter(data_inicio__gte=trinta_dias_atras)

    total_registros = sessoes_periodo.count()
    alunos_ativos = sessoes_periodo.values('aluno').distinct().count()
    alertas_atencao = sessoes_periodo.filter(emocao_selecionada__in=['triste', 'ansioso', 'medo', 'irritado']).count()

    # 2. Bem-estar médio (Baseado na IA)
    analises = AnaliseResposta.objects.filter(resposta__diario__sessao_emocional__in=sessoes_periodo)
    media_score = analises.aggregate(Avg('score_sentimento'))['score_sentimento__avg']
    bem_estar_medio = round(media_score * 100) if media_score else 0

    # 3. Dados para o Gráfico de Distribuição (Conta quantas vezes cada emoção apareceu)
    distribuicao = sessoes_periodo.values('emocao_selecionada').annotate(total=Count('id')).order_by('-total')
    labels_dist = [item['emocao_selecionada'].capitalize() for item in distribuicao]
    valores_dist = [item['total'] for item in distribuicao]

    # 4. Dados reais para as Barras de Níveis Médios
    if total_registros > 0:
        tristes = sessoes_periodo.filter(emocao_selecionada__in=['triste', 'irritado']).count()
        ansiosos = sessoes_periodo.filter(emocao_selecionada__in=['ansioso', 'medo']).count()
        nivel_tristeza = round((tristes / total_registros) * 100)
        nivel_ansiedade = round((ansiosos / total_registros) * 100)
    else:
        nivel_tristeza = 0
        nivel_ansiedade = 0

    return render(request, 'analise/estatisticas_gerais.html', {
        'total_registros': total_registros,
        'alunos_ativos': alunos_ativos,
        'alertas_atencao': alertas_atencao,
        'bem_estar_medio': bem_estar_medio,
        
        # Gráfico (convertido para o JS ler)
        'labels_dist': labels_dist,
        'valores_dist': valores_dist,
        
        # Barras de Progresso
        'nivel_tristeza': nivel_tristeza,
        'nivel_ansiedade': nivel_ansiedade,
    })


@educador_required
def configuracoes_servidor(request):
    if request.method == 'POST':
        senha_atual = request.POST.get('senha_atual')
        nova_senha = request.POST.get('nova_senha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if senha_atual and nova_senha and confirmar_senha:
            if not request.user.check_password(senha_atual):
                messages.error(request, 'A senha atual está incorreta.')
            elif nova_senha != confirmar_senha:
                messages.error(request, 'As novas senhas não coincidem.')
            elif len(nova_senha) < 8:
                messages.error(request, 'A nova senha deve ter pelo menos 8 caracteres.')
            else:
                request.user.set_password(nova_senha)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Senha do servidor atualizada com sucesso! 🚀')
                return redirect('configuracoes_servidor')
        else:
            messages.error(request, 'Preencha todos os campos para trocar a senha.')

    # Aponta para a pasta do app analise
    return render(request, 'analise/configuracoes_servidor.html')

