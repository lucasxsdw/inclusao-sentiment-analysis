import json
import logging
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from diario.models import Diario, Pergunta, Resposta, SessaoEmocional
from accounts.models import Aluno

from .services.sentimento_service import analisar_e_salvar
from .services.chat_service import gerar_pergunta_diario

logger = logging.getLogger(__name__)

EMOCOES_ATENCAO = ['triste', 'muito_triste', 'ansioso', 'irritado', 'tristeza', 'medo', 'raiva']

EMOCAO_EMOJI = {
    'muito_feliz': '😄', 'feliz': '😊', 'neutro': '😐',
    'triste': '😢', 'muito_triste': '😭', 'ansioso': '😰',
    'irritado': '😠', 'cansado': '😴', 'alegria': '😊',
    'tristeza': '😢', 'medo': '😨', 'raiva': '😠',
    'surpresa': '😲', 'nojo': '🤢',
}


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

            if not texto_aluno:
                return JsonResponse({'erro': 'O texto não pode estar vazio.'}, status=400)

            diario_id = request.session.get('diario_atual_id')
            if not diario_id:
                return JsonResponse({'erro': 'Sessão expirada. Volte à página inicial.'}, status=400)

            diario_vinculo = Diario.objects.get(id=diario_id)
            pergunta_vinculo = Pergunta.objects.order_by("?").first()

            if not pergunta_vinculo:
                return JsonResponse({'erro': 'Nenhuma pergunta cadastrada no sistema.'}, status=500)

            nova_resposta = Resposta.objects.create(
                texto_resposta=texto_aluno,
                diario=diario_vinculo,
                pergunta=pergunta_vinculo
            )

            resultado_ia = analisar_e_salvar(nova_resposta)
            emocao_ptbr = resultado_ia["label"] if resultado_ia else "neutro"

            perfil_aluno = None
            if request.user.is_authenticated:
                try:
                    aluno = Aluno.objects.get(usuario=request.user)
                    perfil_aluno = {
                        'nome': request.user.get_full_name(),
                        'tipo_deficiencia': aluno.get_tipo_deficiencia_display(),
                        'necessidades_especificas': aluno.necessidades_especificas or 'Não informado'
                    }
                except Aluno.DoesNotExist:
                    pass

            total_mensagens = Resposta.objects.filter(diario=diario_vinculo).count()

            if total_mensagens >= 5:
                resposta_bot = "Agradeço muito por compartilhar seus sentimentos comigo hoje. Nossa sessão chegou ao fim. Lembre-se: este chat é um apoio inicial e não substitui o acompanhamento psicológico profissional. Por favor, procure o NAPN ou um profissional de saúde se precisar de mais ajuda. Você é muito importante! 💙"
            else:
                resposta_bot = gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno)

            return JsonResponse({
                'sucesso': True,
                'mensagem_aluno': texto_aluno,
                'emocao_detectada': emocao_ptbr,
                'resposta_assistente': resposta_bot,
                'fim_de_sessao': total_mensagens >= 5
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'erro': 'Formato inválido.'}, status=400)
        except Exception as e:
            logger.error(f"Erro na View: {e}")
            return JsonResponse({'erro': 'Erro interno no servidor.'}, status=500)

    return JsonResponse({'erro': 'Método não permitido.'}, status=405)


@login_required
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


@login_required
def perfil_aluno_napne(request, aluno_id):
    # 1. Busca o aluno ou dá erro 404
    aluno = get_object_or_404(Aluno, id=aluno_id)

    # 2. Busca as sessões
    sessoes_queryset = SessaoEmocional.objects.filter(aluno=aluno).order_by('-data_inicio')
    
    # 3. Cálculos para o Header (o que estava faltando na outra view)
    total_registro = sessoes_queryset.count()
    total_alertas = sessoes_queryset.filter(emocao_selecionada__in=EMOCOES_ATENCAO).count()

    # 4. Construção do histórico detalhado (IA e Respostas)
    historico = []
    for sessao in sessoes_queryset:
        analises = []
        # Verifica se existe um diário vinculado à sessão
        if sessao.diario:
            for resposta in Resposta.objects.filter(diario=sessao.diario):
                try:
                    # Busca a análise feita pela IA para cada resposta
                    analise = resposta.analiseresposta
                    analises.append({
                        'sentimento': analise.sentimento_detectado or 'neutro',
                        'score': round((analise.score_sentimento or 0) * 100),
                        'texto': resposta.texto_resposta,
                    })
                except Exception:
                    # Se não houver análise da IA ainda, coloca o texto puro
                    analises.append({
                        'sentimento': 'pendente',
                        'score': 0,
                        'texto': resposta.texto_resposta,
                    })

        historico.append({
            'sessao': sessao,
            'analises': analises,
            'emoji': EMOCAO_EMOJI.get(sessao.emocao_selecionada, '😐'),
            'precisa_atencao': sessao.emocao_selecionada in EMOCOES_ATENCAO,
        })

    # 5. Renderização Única
    return render(request, 'analise/perfil_aluno_napne.html', {
        'aluno': aluno,
        'historico': historico,
        'total_registro': total_registro,  # Variável para o seu header
        'total_alertas': total_alertas,    # Variável para o seu header
    })



@login_required
def listar_alunos(request):

    # filtro de busca 
    buscar_aluno = request.GET.get('buscar')
    tipo_deficiencia = request.GET.get('deficiencia')

    # 1. Pega todos os alunos do banco
    todos_alunos = Aluno.objects.select_related('usuario').all().order_by('usuario__first_name')

    if tipo_deficiencia:
       todos_alunos =  todos_alunos.filter(tipo_deficiencia=tipo_deficiencia)

    if buscar_aluno:
        todos_alunos = todos_alunos.filter(usuario__first_name__icontains=buscar_aluno)

    
    # 2. Cria uma lista vazia que vai guardar os "pacotes" de dados de cada aluno
    alunos_lista = []
    
    # 3. Passa por cada aluno para calcular as estatísticas dele
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
                
        # 4. Guarda tudo no dicionário que o nosso HTML está esperando
        alunos_lista.append({
            'aluno': aluno,
            'total_registros': total_registros,
            'data_ultimo_registro': data_ultimo_registro,
            'emoji_ultimo': emoji_ultimo,
            'precisa_atencao': precisa_atencao
        })

    # 5. Envia os dados processados para a tela
    return render(request, 'analise/listar_alunos.html', {
        'alunos_lista': alunos_lista,
        'total_alunos': todos_alunos.count(),
        'buscar_aluno': buscar_aluno,
        'tipo_deficiencia': tipo_deficiencia

    })


