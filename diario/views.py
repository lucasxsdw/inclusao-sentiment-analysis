import json
from datetime import timedelta
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

# Importação dos models locais
from .models import SessaoEmocional, Diario, Resposta

# Regra de acesso
def is_aluno(user):
    return user.is_authenticated and user.tipo_usuario == 'aluno'

aluno_required = user_passes_test(is_aluno, login_url='/login/', redirect_field_name=None)

# Views de navegação
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

@aluno_required
def salvar_emocao(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            emocao = data.get('emocao')
            perfil = getattr(request.user, 'perfil_aluno', None)

            if not emocao:
                return JsonResponse({'status': 'error', 'message': 'Emoção não informada.'}, status=400)

            sessao = SessaoEmocional.objects.create(
                emocao_selecionada=emocao,
                aluno=perfil
            )

            mensagens = {
                'muito_feliz': "Que incrível ver você feliz! O que aconteceu?",
                'feliz': "Que bom que você está se sentindo bem! Quer contar?",
                'neutro': "Como tem sido o seu dia?",
                'triste': "Sinto muito que esteja triste. Quer conversar?",
                'muito_triste': "Estou aqui para te ouvir. O que houve?",
                'ansioso': "Percebi sua ansiedade. Quer desabafar?",
                'irritado': "Algo te deixou irritado? Pode falar aqui.",
                'cansado': "O que tem sugado as suas energias?"
            }
            
            msg = mensagens.get(emocao, "Olá, estou aqui para te ouvir.")

            diario = Diario.objects.create(
                sessao_emocional=sessao,
                mensagem_inicial_ia=msg
            )

            request.session['diario_atual_id'] = diario.id
            request.session.modified = True

            return JsonResponse({'status': 'success', 'diario_id': diario.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error'}, status=405)

@aluno_required
def painel_aluno(request):
    try:
        aluno = request.user.perfil_aluno
    except:
        return redirect('homePage')

    hoje = timezone.now().date()
    # Busca por data_criacao (o campo que criamos)
    sessoes_datas = SessaoEmocional.objects.filter(
        aluno=aluno,
        data_criacao__date__gte=hoje - timedelta(days=29)
    ).values_list('data_criacao__date', flat=True)
    
    datas_com_sessao = set(sessoes_datas)
    ofensiva = 0
    dia_cheque = hoje
    if dia_cheque not in datas_com_sessao: dia_cheque -= timedelta(days=1)
    while dia_cheque in datas_com_sessao:
        ofensiva += 1
        dia_cheque -= timedelta(days=1)

    heatmap = [{'data': hoje - timedelta(days=i), 'preenchido': (hoje - timedelta(days=i)) in datas_com_sessao} for i in range(29, -1, -1)]

    return render(request, 'diario/painel_aluno.html', {'ofensiva': ofensiva, 'heatmap_dias': heatmap})

@aluno_required
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