import json
import logging
from datetime import timedelta
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db.models import Avg, Count

# Imports dos seus Apps
from diario.models import SessaoEmocional, Diario, Resposta, Pergunta
from accounts.models import Aluno
from analise.models import AnaliseResposta
from .services.sentimento_service import analisar_e_salvar
from .services.chat_service import gerar_pergunta_diario

logger = logging.getLogger(__name__)

# ====================================================================
# 🛡️ REGRAS DE SEGURANÇA
# ====================================================================
def is_aluno(user):
    return user.is_authenticated and user.tipo_usuario == 'aluno'

def is_educador(user):
    return user.is_authenticated and user.tipo_usuario == 'educador'

aluno_required = user_passes_test(is_aluno, login_url='/login/', redirect_field_name=None)
educador_required = user_passes_test(is_educador, login_url='/login/', redirect_field_name=None)

# Mapeamentos de Emoção
EMOCOES_ATENCAO = ['triste', 'muito_triste', 'ansioso', 'irritado', 'tristeza', 'medo', 'raiva']
EMOCAO_EMOJI = {
    'muito_feliz': '😄', 'feliz': '😊', 'neutro': '😐',
    'triste': '😢', 'muito_triste': '😭', 'ansioso': '😰',
    'irritado': '😠', 'cansado': '😴', 'alegria': '😊',
    'tristeza': '😢', 'medo': '😨', 'raiva': '😠',
    'surpresa': '😲', 'nojo': '🤢',
}

# ---------------------------------------------------------
# PÁGINAS PÚBLICAS E BÁSICAS
# ---------------------------------------------------------
class homePageViews(TemplateView):
    template_name = 'diario/homePage.html'

class sobre(TemplateView):
    template_name = 'diario/sobre.html'

@method_decorator(aluno_required, name='dispatch')
class HomeView(TemplateView):
    template_name = 'diario/home.html'

@method_decorator(aluno_required, name='dispatch')
class EmotionsView(TemplateView):
    template_name = 'diario/emotions.html'

# ---------------------------------------------------------
# LÓGICA DO ALUNO
# ---------------------------------------------------------

@aluno_required
def salvar_emocao(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            emocao = data.get('emocao')
            perfil = getattr(request.user, 'perfil_aluno', None)

            if not emocao:
                return JsonResponse({'status': 'error', 'message': 'Emoção não informada.'}, status=400)

            # Criamos a sessão (data_criacao é automático via auto_now_add)
            sessao = SessaoEmocional.objects.create(
                emocao_selecionada=emocao,
                aluno=perfil
            )

            mensagens_iniciais = {
                'muito_feliz': "Que incrível ver você feliz! O que aconteceu?",
                'feliz': "Que bom que você está bem! Quer contar o motivo?",
                'neutro': "Como tem sido o seu dia até agora?",
                'triste': "Sinto muito que esteja triste. Quer conversar?",
                'muito_triste': "Estou aqui para te ouvir. O que houve?",
                'ansioso': "Percebi sua ansiedade. Quer desabafar?",
                'irritado': "Algo te deixou irritado? Pode falar aqui.",
                'cansado': "O que tem sugado as suas energias?"
            }
            
            msg = mensagens_iniciais.get(emocao, "Olá, estou aqui para te ouvir.")

            diario = Diario.objects.create(
                sessao_emocional=sessao,
                mensagem_inicial_ia=msg
            )

            request.session['diario_atual_id'] = diario.id
            request.session.modified = True 

            return JsonResponse({'status': 'success', 'diario_id': diario.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método inválido'}, status=405)

@aluno_required
def painel_aluno(request):
    try:
        aluno = request.user.perfil_aluno 
    except:
        return redirect('homePage')

    hoje = timezone.now().date()
    # Buscamos as datas usando data_criacao
    sessoes_datas = SessaoEmocional.objects.filter(
        aluno=aluno, 
        data_criacao__date__gte=hoje - timedelta(days=29)
    ).values_list('data_criacao__date', flat=True)
    
    datas_com_sessao = set(sessoes_datas)

    ofensiva = 0
    dia_cheque = hoje
    if dia_cheque not in datas_com_sessao:
        dia_cheque -= timedelta(days=1)
    while dia_cheque in datas_com_sessao:
        ofensiva += 1
        dia_cheque -= timedelta(days=1)

    heatmap_dias = [{'data': hoje - timedelta(days=i), 'preenchido': (hoje - timedelta(days=i)) in datas_com_sessao} for i in range(29, -1, -1)]

    return render(request, 'diario/painel_aluno.html', {
        'ofensiva': ofensiva,
        'heatmap_dias': heatmap_dias,
    })

@aluno_required
def enviar_desabafo(request):
    if request.method == "GET":
        diario_id = request.session.get('diario_atual_id')
        mensagem = "Olá! Como você está se sentindo?"
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

            # Perfil do aluno para a IA
            perfil = None
            al = getattr(request.user, 'perfil_aluno', None)
            if al:
                perfil = {'nome': request.user.username, 'tipo_deficiencia': al.get_tipo_deficiencia_display()}

            # Salva Resposta
            resp = Resposta.objects.create(texto_resposta=texto, diario=diario, pergunta=Pergunta.objects.order_by("?").first())
            
            # IA Sentimento e Chat (Groq)
            emocao = 'neutro'
            try:
                res_ia = analisar_e_salvar(resp)
                emocao = res_ia["label"] if res_ia else "neutro"
            except: pass

            try:
                bot_msg = gerar_pergunta_diario(emocao, texto, perfil)
            except:
                bot_msg = "Entendo. Quer me contar mais?"

            total = Resposta.objects.filter(diario=diario).count()
            fim = total >= 5
            if fim: bot_msg = "Sessão finalizada. Procure o NAPNE se precisar. 💙"

            return JsonResponse({'sucesso': True, 'resposta_assistente': bot_msg, 'fim_de_sessao': fim})
        except Exception as e:
            return JsonResponse({'erro': str(e)}, status=500)

# ---------------------------------------------------------
# LÓGICA DO EDUCADOR (NAPNE) - CAMPO data_criacao AJUSTADO
# ---------------------------------------------------------

@educador_required
def painel_napne(request):
    hoje = timezone.now().date()
    # Ajustado de data_inicio para data_criacao
    ativos_hoje = SessaoEmocional.objects.filter(data_criacao__date=hoje).values('aluno').distinct().count()
    total_alunos = Aluno.objects.count()
    
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
        'total_alunos': total_alunos,
        'ativos_hoje': ativos_hoje,
        'atividade_recente': atividade_recente,
    })

@educador_required
def estatisticas_gerais(request):
    hoje = timezone.now()
    trinta_dias = hoje - timedelta(days=30)
    # Ajustado para data_criacao
    sessoes = SessaoEmocional.objects.filter(data_criacao__gte=trinta_dias)
    
    distribuicao = sessoes.values('emocao_selecionada').annotate(total=Count('id')).order_by('-total')
    labels = [item['emocao_selecionada'].capitalize() for item in distribuicao]
    valores = [item['total'] for item in distribuicao]

    return render(request, 'analise/estatisticas_gerais.html', {
        'total_registros': sessoes.count(),
        'labels_dist': labels,
        'valores_dist': valores,
    })

@login_required
def configuracoes_perfil(request):
    if request.method == 'POST':
        nova = request.POST.get('nova_senha')
        if nova and len(nova) >= 8:
            request.user.set_password(nova)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Senha atualizada!')
        else:
            messages.error(request, 'Erro na senha.')
    return render(request, 'diario/configuracoes.html')