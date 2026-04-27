import json
from datetime import timedelta
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.utils import timezone
from diario.models import SessaoEmocional, Diario, Resposta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

# ====================================================================
# 🛡️ REGRAS DE SEGURANÇA
# ====================================================================
def is_aluno(user):
    return user.is_authenticated and user.tipo_usuario == 'aluno'

aluno_required = user_passes_test(is_aluno, login_url='/login/', redirect_field_name=None)

# ====================================================================
# ---------------------------------------------------------
# PÁGINAS PÚBLICAS
# ---------------------------------------------------------
class homePageViews(TemplateView):
    template_name = 'diario/homePage.html'

class sobre(TemplateView):
    template_name = 'diario/sobre.html'

# ---------------------------------------------------------
# PÁGINAS DO ALUNO (Protegidas)
# ---------------------------------------------------------

@method_decorator(login_required, name='dispatch')
@method_decorator(aluno_required, name='dispatch')
class HomeView(TemplateView):
    template_name = 'diario/home.html'

@method_decorator(login_required, name='dispatch')
@method_decorator(aluno_required, name='dispatch')
class EmotionsView(TemplateView):
    template_name = 'diario/emotions.html'

@login_required
@aluno_required
def salvar_emocao(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            emocao = data.get('emocao')
            perfil = getattr(request.user, 'perfil_aluno', None)

            if not emocao:
                return JsonResponse({'status': 'error', 'message': 'Emoção não informada.'}, status=400)

            # Criamos a sessão (data_criacao é automático via auto_now_add no model)
            sessao = SessaoEmocional.objects.create(
                emocao_selecionada=emocao,
                aluno=perfil
            )

            mensagens_iniciais = {
                'muito_feliz': "Que incrível ver que você está muito feliz hoje! Quer me contar o que aconteceu?",
                'feliz': "Que bom que você está se sentindo feliz! Quer compartilhar o motivo?",
                'neutro': "Entendi. Como tem sido o seu dia até agora?",
                'triste': "Notei que você está se sentindo triste hoje. Quer conversar sobre o que está havendo?",
                'muito_triste': "Sinto muito que você esteja se sentindo assim. Estou aqui para te ouvir. O que houve?",
                'ansioso': "Percebi que você está ansioso(a). Quer me contar o que está te deixando assim?",
                'irritado': "Vejo que algo te deixou irritado(a). Quer desabafar sobre isso?",
                'cansado': "Você parece exausto(a). O que tem sugado as suas energias?"
            }
            
            mensagem_personalizada = mensagens_iniciais.get(emocao, "Olá, estou aqui para te ouvir. Como você está?")

            diario = Diario.objects.create(
                sessao_emocional=sessao,
                mensagem_inicial_ia=mensagem_personalizada
            )

            request.session['diario_atual_id'] = diario.id
            request.session.modified = True

            return JsonResponse({'status': 'success', 'diario_id': diario.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método inválido'}, status=405)


@login_required
@aluno_required
def painel_aluno(request):
  
@login_required
@aluno_required
def painel_aluno(request):
    try:
        aluno = request.user.perfil_aluno 
    except Exception:
        return redirect('homePage') 

    # Daqui para baixo, o Python GARANTE que 'aluno' existe
    hoje = timezone.now().date()
    
    sessoes_datas = SessaoEmocional.objects.filter(
        aluno=aluno, 
        data_criacao__date__gte=hoje - timedelta(days=29)
    ).values_list('data_criacao__date', flat=True)
    
    # ... resto do código (streak, heatmap, pendências) ...
    
    datas_com_sessao = set(sessoes_datas)
    # (Continue com a lógica de heatmap e ofensiva enviada anteriormente)

    # Identifica quais dos últimos 7 dias estão sem registro (Pendências)
    dias_pendentes = [data for data in periodo_pendencia if data not in datas_com_sessao]

    # Ofensiva (Streak) - sua lógica está correta aqui
    ofensiva = 0
    dia_cheque = hoje
    if dia_cheque not in datas_com_sessao:
        dia_cheque -= timedelta(days=1)
    while dia_cheque in datas_com_sessao:
        ofensiva += 1
        dia_cheque -= timedelta(days=1)

    # Heatmap (Mapa de calor)
    heatmap_dias = [{'data': hoje - timedelta(days=i), 'preenchido': (hoje - timedelta(days=i)) in datas_com_sessao} for i in range(29, -1, -1)]

    return render(request, 'diario/painel_aluno.html', {
        'ofensiva': ofensiva,
        'heatmap_dias': heatmap_dias,
        'dias_pendentes': dias_pendentes, # AGORA O TEMPLATE VAI RECEBER OS DIAS AUSENTES
    })

@login_required
@aluno_required
def configuracoes_perfil(request):
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
                messages.success(request, 'Senha atualizada com sucesso! 🚀')
                return redirect('configuracoes_perfil')
        else:
            messages.error(request, 'Preencha todos os campos para trocar a senha.')

    return render(request, 'diario/configuracoes.html')