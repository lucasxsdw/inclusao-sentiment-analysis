import json
import logging
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count

# Imports dos Models
from diario.models import Diario, Pergunta, Resposta, SessaoEmocional
from accounts.models import Aluno
from analise.models import AnaliseResposta

# Services
from .services.sentimento_service import analisar_e_salvar
from .services.chat_service import gerar_pergunta_diario

logger = logging.getLogger(__name__)

# --- Regras de Acesso ---
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

# --- Função que o Render estava pedindo ---
@educador_required
def perfil_aluno_napne(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    sessoes_qs = SessaoEmocional.objects.filter(aluno=aluno).order_by('-data_criacao')
    
    historico = []
    for sessao in sessoes_qs:
        diario = getattr(sessao, 'diario', None)
        analises = []
        if diario:
            respostas = Resposta.objects.filter(diario=diario).prefetch_related('analiseresposta')
            for resp in respostas:
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

    return render(request, 'analise/perfil_aluno_napne.html', {
        'aluno': aluno,
        'historico': historico,
        'total_sessoes': len(historico),
    })

# --- Chat/Desabafo ---
@aluno_required
def enviar_desabafo(request):
    if request.method == "GET":
        diario_id = request.session.get('diario_atual_id')
        mensagem = "Olá! Como você está hoje?"
        if diario_id:
            d = Diario.objects.filter(id=diario_id).first()
            if d and d.mensagem_inicial_ia: mensagem = d.mensagem_inicial_ia
        return render(request, 'analise/chat.html', {'mensagem_inicial': mensagem})

    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            texto = dados.get('texto_resposta', '').strip()
            diario_id = request.session.get('diario_atual_id')
            diario = get_object_or_404(Diario, id=diario_id)

            resp = Resposta.objects.create(texto_resposta=texto, diario=diario, pergunta=Pergunta.objects.order_by("?").first())
            
            emocao = 'neutro'
            try:
                res_ia = analisar_e_salvar(resp)
                emocao = res_ia["label"] if res_ia else "neutro"
            except: pass

            try:
                perfil = {'nome': request.user.username}
                al = getattr(request.user, 'perfil_aluno', None)
                if al: perfil['tipo_deficiencia'] = al.get_tipo_deficiencia_display()
                bot_msg = gerar_pergunta_diario(emocao, texto, perfil)
            except: bot_msg = "Entendo. Me conte mais."

            total = Resposta.objects.filter(diario=diario).count()
            fim = total >= 5
            if fim: bot_msg = "Sessão encerrada. Procure o NAPNE se precisar. 💙"

            return JsonResponse({'sucesso': True, 'resposta_assistente': bot_msg, 'fim_de_sessao': fim})
        except Exception as e:
            return JsonResponse({'erro': str(e)}, status=500)

# --- Outras Views do Educador ---
@educador_required
def painel_napne(request):
    hoje = timezone.now().date()
    ativos = SessaoEmocional.objects.filter(data_criacao__date=hoje).values('aluno').distinct().count()
    recente = SessaoEmocional.objects.select_related('aluno__usuario').order_by('-data_criacao')[:20]
    return render(request, 'analise/painel_napne.html', {'ativos_hoje': ativos, 'atividade_recente': recente, 'total_alunos': Aluno.objects.count()})

@educador_required
def listar_alunos(request):
    alunos = Aluno.objects.select_related('usuario').all().order_by('usuario__first_name')
    # Lógica simplificada para não dar erro
    return render(request, 'analise/listar_alunos.html', {'alunos_lista': [{'aluno': a} for a in alunos]})