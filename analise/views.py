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

            if not texto_aluno:
                return JsonResponse({'erro': 'O texto não pode estar vazio.'}, status=400)

            diario_id = request.session.get('diario_atual_id')
            if not diario_id:
                return JsonResponse({'erro': 'Sessão expirada.'}, status=400)

            diario_vinculo = Diario.objects.get(id=diario_id)
            
            # Limite de 5 mensagens
            if Resposta.objects.filter(diario=diario_vinculo).count() >= 5:
                return JsonResponse({
                    'sucesso': True,
                    'resposta_assistente': "Nossa sessão chegou ao fim. Procure o NAPNE se precisar. 💙",
                    'fim_de_sessao': True
                })

            # Salva a resposta
            nova_resposta = Resposta.objects.create(
                texto_resposta=texto_aluno,
                diario=diario_vinculo,
                pergunta=Pergunta.objects.order_by("?").first()
            )

            # IA de Sentimento
            emocao_ptbr = 'neutro'
            try:
                resultado_ia = analisar_e_salvar(nova_resposta)
                emocao_ptbr = resultado_ia["label"] if resultado_ia else "neutro"
            except: pass

            # IA de Chat (Groq)
            try:
                perfil = None
                al = getattr(request.user, 'perfil_aluno', None)
                if al:
                    perfil = {
                        'nome': request.user.username,
                        'tipo_deficiencia': al.get_tipo_deficiencia_display()
                    }
                resposta_bot = gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil)
            except:
                resposta_bot = "Entendo. Me conte mais sobre isso?"

            fim_de_sessao = Resposta.objects.filter(diario=diario_vinculo).count() >= 5

            return JsonResponse({
                'sucesso': True,
                'mensagem_aluno': texto_aluno,
                'emocao_detectada': emocao_ptbr,
                'resposta_assistente': resposta_bot,
                'fim_de_sessao': fim_de_sessao
            })

        except Exception as e:
            return JsonResponse({'erro': str(e)}, status=500)

# --- 3. NAPNE e Estatísticas (Corrigidos para data_criacao) ---
@educador_required
def painel_napne(request):
    hoje = timezone.now().date()
    # Ajustado para data_criacao
    ativos_hoje = SessaoEmocional.objects.filter(data_criacao__date=hoje).values('aluno').distinct().count()
    
    atividade_recente = []
    # Ajustado para data_criacao
    for sessao in SessaoEmocional.objects.select_related('aluno__usuario').order_by('-data_criacao')[:20]:
        atividade_recente.append({
            'sessao': sessao,
            'emoji': EMOCAO_EMOJI.get(sessao.emocao_selecionada, '😐'),
            'precisa_atencao': sessao.emocao_selecionada in EMOCOES_ATENCAO,
            'nome': sessao.aluno.usuario.get_full_name() if sessao.aluno else 'Anônimo',
        })

    return render(request, 'analise/painel_napne.html', {
        'total_alunos': Aluno.objects.count(),
        'ativos_hoje': ativos_hoje,
        'atividade_recente': atividade_recente,
    })

@educador_required
def perfil_aluno_napne(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    # Ajustado para data_criacao
    sessoes_qs = SessaoEmocional.objects.filter(aluno=aluno).order_by('-data_criacao')
    
    historico = []
    for sessao in sessoes_qs:
        diario = getattr(sessao, 'diario', None)
        analises = []
        if diario:
            for resp in Resposta.objects.filter(diario=diario):
                try:
                    an = resp.analiseresposta
                    analises.append({
                        'sentimento': an.sentimento_detectado or 'neutro',
                        'score': round((an.score_sentimento or 0) * 100),
                        'texto': resp.texto_resposta,
                    })
                except: pass

        historico.append({
            'sessao': sessao,
            'analises': analises,
            'emoji': EMOCAO_EMOJI.get(sessao.emocao_selecionada, '😐'),
            'precisa_atencao': sessao.emocao_selecionada in EMOCOES_ATENCAO,
        })

    return render(request, 'analise/perfil_aluno_napne.html', {'aluno': aluno, 'historico': historico})

@educador_required
def listar_alunos(request):
    buscar = request.GET.get('buscar', '')
    todos_alunos = Aluno.objects.select_related('usuario').all().order_by('usuario__first_name')
    if buscar:
        todos_alunos = todos_alunos.filter(usuario__first_name__icontains=buscar)

    alunos_lista = []
    for a in todos_alunos:
        # Ajustado para data_criacao
        ultima = SessaoEmocional.objects.filter(aluno=a).order_by('-data_criacao').first()
        alunos_lista.append({
            'aluno': a,
            'emoji_ultimo': EMOCAO_EMOJI.get(ultima.emocao_selecionada, '😐') if ultima else '',
            'precisa_atencao': ultima.emocao_selecionada in EMOCOES_ATENCAO if ultima else False
        })
    return render(request, 'analise/listar_alunos.html', {'alunos_lista': alunos_lista})

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

@educador_required
def estatisticas_gerais(request):
    trinta_dias = timezone.now() - timedelta(days=30)
    # Ajustado para data_criacao
    sessoes = SessaoEmocional.objects.filter(data_criacao__gte=trinta_dias)
    distribuicao = sessoes.values('emocao_selecionada').annotate(total=Count('id')).order_by('-total')
    
    return render(request, 'analise/estatisticas_gerais.html', {
        'total_registros': sessoes.count(),
        'labels_dist': [item['emocao_selecionada'].capitalize() for item in distribuicao],
        'valores_dist': [item['total'] for item in distribuicao],
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
    return render(request, 'analise/configuracoes_servidor.html')