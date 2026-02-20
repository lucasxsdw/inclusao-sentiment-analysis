import json
from django.http import JsonResponse
from django.views.generic import TemplateView
from diario.models import SessaoEmocional, Diario
from diario.models import Resposta, Pergunta
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

            # 2️⃣ Criar diário automaticamente
            diario = Diario.objects.create(
                sessao_emocional=sessao,
                mensagem_inicial_ia="Olá, estou aqui para te ouvir."
            )

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


