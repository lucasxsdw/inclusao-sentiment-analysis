import json
from django.http import JsonResponse
from django.views.generic import TemplateView
from diario.models import SessaoEmocional, Diario
from diario.models import Resposta
from analise.services.sentimento_service import analisar_e_salvar



class HomeView(TemplateView):
    template_name = 'diario/home.html'  

    
class EmotionsView(TemplateView):
    template_name = 'diario/emotions.html'


def salvar_emocao(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        emocao = data.get('emocao')

        if emocao:
            # 1️⃣ Criar sessão
            sessao = SessaoEmocional.objects.create(
                emocao_selecionada=emocao,
                status_sessao='ativa'
            )

            # 💡 NOVIDADE: Mapeando a emoção para a primeira mensagem personalizada!
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
            # Se a emoção não for achada, usa um texto padrão
            mensagem_personalizada = mensagens_iniciais.get(emocao, "Olá, estou aqui para te ouvir. Como você está?")

            # 2️⃣ Criar diário automaticamente com a mensagem dinâmica
            diario = Diario.objects.create(
                sessao_emocional=sessao,
                mensagem_inicial_ia=mensagem_personalizada
            )

            # 3️⃣ A MÁGICA DA SESSÃO: Guardar na "memória" do navegador para o Chat ler depois!
            request.session['diario_atual_id'] = diario.id
            request.session['emocao_inicial'] = emocao
            request.session['contagem_mensagens'] = 0  # Já preparando o seu limite de 5 perguntas!

            return JsonResponse({
                'status': 'success',
                'sessao_id': sessao.id,
                'diario_id': diario.id
            })

        return JsonResponse({'status': 'error'}, status=400)

    return JsonResponse({'status': 'error'}, status=405)




def salvar_resposta(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        diario_id = data.get('diario_id')
        pergunta_id = data.get('pergunta_id')
        texto = data.get('texto')

        if diario_id and pergunta_id and texto:

            resposta = Resposta.objects.create(
                diario_id=diario_id,
                pergunta_id=pergunta_id,
                texto_resposta=texto
            )

            # 🔥 Roda IA automaticamente
            resultado = analisar_e_salvar(resposta)

            return JsonResponse({
                'status': 'success',
                'sentimento_detectado': resultado['label'],
                'score': resultado['score']
            })

        return JsonResponse({'status': 'error'}, status=400)

    return JsonResponse({'status': 'error'}, status=405)



class homePageViews(TemplateView):
    template_name = 'diario/homePage.html'