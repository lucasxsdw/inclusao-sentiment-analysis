import json
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
# Importe o seu modelo real que guarda o texto do aluno
from .models import Resposta 
from .services.sentimento_service import analisar_e_salvar
from .services.chat_service import gerar_pergunta_diario



logger = logging.getLogger(__name__)

@csrf_exempt # Usamos csrf_exempt temporariamente para facilitar os testes via Postman/Shell
def enviar_desabafo(request):
    if request.method == "GET":
        return render(request, 'analise/chat.html')
    """
    Recebe a mensagem do aluno, analisa a emoção, gera a resposta da IA e devolve para o chat.
    """
    if request.method == 'POST':
        try:
            # 1. Recebe os dados em JSON (enviados pelo frontend)
            dados = json.loads(request.body)
            texto_aluno = dados.get('texto_resposta', '').strip()

            if not texto_aluno:
                return JsonResponse({'erro': 'O texto não pode estar vazio.'}, status=400)

            # 2. Salva a mensagem do aluno no banco de dados
            # NOTA: Ajuste os campos abaixo conforme a estrutura do seu TCC (ex: linkar com o aluno logado)
            nova_resposta = Resposta.objects.create(
                texto_resposta=texto_aluno
                # aluno=request.user # Se você já tiver sistema de login
            )

            # 3. Chama o Cérebro: Analisa a emoção e salva o sentimento no banco
            resultado_ia = analisar_e_salvar(nova_resposta)
            
            # Se a IA falhar (Plano B), assumimos "neutro" para o chat não travar
            emocao_ptbr = resultado_ia["label"] if resultado_ia else "neutro"

            # 4. Chama a Voz: Gera a resposta empática do conselheiro
            resposta_bot = gerar_pergunta_diario(emocao_ptbr, texto_aluno)

            # 5. Devolve o pacote completo para a tela do aluno
            return JsonResponse({
                'sucesso': True,
                'mensagem_aluno': texto_aluno,
                'emocao_detectada': emocao_ptbr,
                'resposta_assistente': resposta_bot
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'erro': 'Formato de dado inválido. Envie um JSON.'}, status=400)
        except Exception as e:
            logger.error(f"Erro na View enviar_desabafo: {e}")
            return JsonResponse({'erro': 'Erro interno no servidor.'}, status=500)

    # Se tentarem acessar a URL direto pelo navegador (método GET)
    return JsonResponse({'erro': 'Método não permitido. Use POST.'}, status=405)