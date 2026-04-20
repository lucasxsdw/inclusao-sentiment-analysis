import json
from datetime import timedelta
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.utils import timezone
from diario.models import SessaoEmocional, Diario, Resposta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator # <-- NOVO: Para proteger classes
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

# ====================================================================
# 🛡️ REGRAS DE SEGURANÇA (O "CRÁCHA" DO ALUNO)
# ====================================================================
def is_aluno(user):
    return user.is_authenticated and user.tipo_usuario == 'aluno'

aluno_required = user_passes_test(is_aluno, login_url='/login/', redirect_field_name=None)
# ====================================================================

# ---------------------------------------------------------
# PÁGINAS PÚBLICAS (Qualquer um pode ver)
# ---------------------------------------------------------
class homePageViews(TemplateView):
    template_name = 'diario/homePage.html'

class sobre(TemplateView):
    template_name = 'diario/sobre.html'

# ---------------------------------------------------------
# PÁGINAS DO ALUNO (Protegidas)
# ---------------------------------------------------------

# Para proteger uma Class-Based View, usamos o @method_decorator
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

            # Tenta pegar o perfil, se não existir, evita o erro 500
            try:
                perfil = request.user.perfil_aluno
            except Exception:
                return JsonResponse({'status': 'error', 'message': 'Usuário não possui perfil de aluno cadastrado.'}, status=400)

            if emocao:
                sessao = SessaoEmocional.objects.create(
                    emocao_selecionada=emocao,
                    status_sessao='ativa',
                    aluno=perfil 
                )

                mensagens_iniciais = {
                    'muito_feliz': "Que incrível ver que você está muito feliz hoje! Quer me contar o que aconteceu?",
                    'feliz': "Que bom que você está se sentindo feliz! Quer compartilhar o motivo?",
                    'neutro': "Entendi. Como tem sido o seu dia até agora?",
                    'triste': "Notei que você está se sentindo triste hoje. Quer conversar sobre o que está havendo?",
                    'muito_triste': "Sinto muito que você esteja se sentindo assim. Estou aqui para te ouvir, no seu tempo. O que houve?",
                    'ansioso': "Percebi que você está ansioso(a). Respire fundo... Quer me contar o que está te deixando assim?",
                    'irritado': "Vejo que algo te deixou irritado(a). Quer desabafar sobre isso?",
                    'cansado': "Você parece exausto(a). O que tem sugado as suas energias ultimamente?"
                }
                
                mensagem_personalizada = mensagens_iniciais.get(emocao, "Olá, estou aqui para te ouvir. Como você está?")

                diario = Diario.objects.create(
                    sessao_emocional=sessao,
                    mensagem_inicial_ia=mensagem_personalizada
                )

                request.session['diario_atual_id'] = diario.id
                request.session['emocao_inicial'] = emocao
                request.session['contagem_mensagens'] = 0  

                return JsonResponse({
                    'status': 'success',
                    'sessao_id': sessao.id,
                    'diario_id': diario.id
                })

            return JsonResponse({'status': 'error', 'message': 'Emoção não informada.'}, status=400)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error'}, status=405)
@aluno_required
def painel_aluno(request):
    aluno = request.user.perfil_aluno 

    hoje = timezone.now().date()
    trinta_dias_atras = hoje - timedelta(days=29)

    sessoes = SessaoEmocional.objects.filter(
        aluno=aluno, 
        data_inicio__date__gte=trinta_dias_atras
    ).values_list('data_inicio__date', flat=True)
    
    datas_com_sessao = set(sessoes)

    ofensiva = 0
    dia_cheque = hoje
    
    if dia_cheque not in datas_com_sessao:
        dia_cheque -= timedelta(days=1)

    while dia_cheque in datas_com_sessao:
        ofensiva += 1
        dia_cheque -= timedelta(days=1)

    heatmap_dias = []
    for i in range(29, -1, -1):
        dia_atual = hoje - timedelta(days=i)
        heatmap_dias.append({
            'data': dia_atual,
            'preenchido': dia_atual in datas_com_sessao
        })

    dias_pendentes = []
    data_criacao_conta = request.user.date_joined.date() 

    for i in range(1, 8):
        dia_atual = hoje - timedelta(days=i)
        if dia_atual >= data_criacao_conta and dia_atual not in datas_com_sessao:
            dias_pendentes.append(dia_atual)

    return render(request, 'diario/painel_aluno.html', {
        'ofensiva': ofensiva,
        'heatmap_dias': heatmap_dias,
        'dias_pendentes': dias_pendentes,
    })


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