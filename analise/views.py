import json
import logging
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.db.models import Avg, Count

# Imports dos Models (Certifique-se que os caminhos estão corretos)
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

# Mapeamentos
EMOCOES_ATENCAO = ['triste', 'muito_triste', 'ansioso', 'irritado', 'tristeza', 'medo', 'raiva']
EMOCAO_EMOJI = {
    'muito_feliz': '😄', 'feliz': '😊', 'neutro': '😐',
    'triste': '😢', 'muito_triste': '😭', 'ansioso': '😰',
    'irritado': '😠', 'cansado': '😴', 'alegria': '😊',
    'tristeza': '😢', 'medo': '😨', 'raiva': '😠',
    'surpresa': '😲', 'nojo': '🤢',
}

# --- 2. Chat e Desabafo (Aluno) ---
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

            diario_vinculo = get_object_or_404(Diario, id=diario_id)
            total_mensagens = Resposta.objects.filter(diario=diario_vinculo).count()

            if total_mensagens >= 5:
                return JsonResponse({
                    'sucesso': True,
                    'resposta_assistente': "Nossa sessão chegou ao fim. Procure o NAPNE se precisar. 💙",
                    'fim_de_sessao': True
                }, status=200)

            # Salva Resposta
            nova_resposta = Resposta.objects.create(
                texto_resposta=texto_aluno,
                diario=diario_vinculo,
                pergunta=Pergunta.objects.order_by("?").first()
            )

            # IA Sentimento
            emocao_ptbr = 'neutro'
            try:
                resultado_ia = analisar_e_salvar(nova_resposta)
                emocao_ptbr = resultado_ia["label"] if resultado_ia else "neutro"
            except Exception: pass

            # IA Resposta (Groq/Llama)
            try:
                perfil = None
                al = getattr(request.user, 'perfil_aluno', None)
                if al:
                    perfil = {'nome': request.user.username, 'tipo_deficiencia': al.get_tipo_deficiencia_display()}
                resposta_bot = gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil)
            except Exception:
                resposta_bot = "Entendo. Me conte mais sobre isso."

            # Verifica fim de sessão após responder
            novo_total = Resposta.objects.filter(diario=diario_vinculo).count()
            fim = novo_total >= 5
            if fim:
                resposta_bot = "Agradeço por compartilhar. Sessão encerrada. Lembre-se de procurar o NAPNE. 💙"

            return JsonResponse({
                'sucesso': True,
                'mensagem_aluno': texto_aluno,
                'emocao_detectada': emocao_ptbr,
                'resposta_assistente': resposta_bot,
                'fim_de_sessao': fim
            })
        except Exception as e:
            return JsonResponse({'sucesso': False, 'erro': str(e)}, status=500)

# --- 3. Painel e Histórico do Aluno ---
@aluno_required
def historico_emocional(request):
    aluno = getattr(request.user, 'perfil_aluno', None)
    sessoes = []
    if aluno:
        # Trocado data_inicio por data_criacao
        sessoes_qs = SessaoEmocional.objects.filter(aluno=aluno).order_by('-data_criacao')
        for sessao in sessoes_qs:
            emoji = EMOCAO_EMOJI.get(sessao.emocao_selecionada, '😐')
            sessoes.append({
                'sessao': sessao,
                'emoji': emoji,
                'precisa_atencao': sessao.emocao_selecionada in EMOCOES_ATENCAO,
            })
    return render(request, 'analise/perfil_aluno_napne.html', {'sessoes': sessoes})

# --- 4. Painel Educador (NAPNE) ---
@educador_required
def painel_napne(request):
    hoje = timezone.now().date()
    # Trocado data_inicio por data_criacao
    ativos_hoje = SessaoEmocional.objects.filter(data_criacao__date=hoje).values('aluno').distinct().count()
    
    atividade_recente = []
    for sessao in SessaoEmocional.objects.select_related('aluno__usuario').order_by('-data_criacao')[:20]:
        atividade_recente.append({
            'sessao': sessao,
            'emoji': EMOCAO_EMOJI.get(sessao.emocao_selecionada, '😐'),
            'precisa_atencao': sessao.emocao_selecionada in EMOCOES_ATENCAO,
            'nome': sessao.aluno.usuario.get_full_name() if sessao.aluno else 'Aluno desconhecido',
        })

    return render(request, 'analise/painel_napne.html', {
        'total_alunos': Aluno.objects.count(),
        'ativos_hoje': ativos_hoje,
        'atividade_recente': atividade_recente,
    })

@educador_required
def estatisticas_gerais(request):
    hoje = timezone.now()
    trinta_dias = hoje - timedelta(days=30)
    # Trocado data_inicio por data_criacao
    sessoes = SessaoEmocional.objects.filter(data_criacao__gte=trinta_dias)
    
    distribuicao = sessoes.values('emocao_selecionada').annotate(total=Count('id')).order_by('-total')
    labels = [item['emocao_selecionada'].capitalize() for item in distribuicao]
    valores = [item['total'] for item in distribuicao]

    return render(request, 'analise/estatisticas_gerais.html', {
        'total_registros': sessoes.count(),
        'labels_dist': labels,
        'valores_dist': valores,
    })

@educador_required
def configuracoes_servidor(request):
    if request.method == 'POST':
        nova = request.POST.get('nova_senha')
        if nova and len(nova) >= 8:
            request.user.set_password(nova)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Senha atualizada!')
            return redirect('configuracoes_servidor')
    return render(request, 'analise/configuracoes_servidor.html')

@educador_required
def listar_alunos(request):
    buscar = request.GET.get('buscar', '')
    alunos = Aluno.objects.select_related('usuario').all().order_by('usuario__first_name')
    if buscar:
        alunos = alunos.filter(usuario__first_name__icontains=buscar)

    alunos_lista = []
    for a in alunos:
        # Trocado data_inicio por data_criacao
        ultima = SessaoEmocional.objects.filter(aluno=a).order_by('-data_criacao').first()
        alunos_lista.append({
            'aluno': a,
            'emoji_ultimo': EMOCAO_EMOJI.get(ultima.emocao_selecionada, '😐') if ultima else '',
            'precisa_atencao': ultima.emocao_selecionada in EMOCOES_ATENCAO if ultima else False
        })
    return render(request, 'analise/listar_alunos.html', {'alunos_lista': alunos_lista})