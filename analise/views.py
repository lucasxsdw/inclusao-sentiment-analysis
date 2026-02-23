import json
import logging
from django.http import JsonResponse
from django.shortcuts import render
# Importe o seu modelo real que guarda o texto do aluno
from .models import Resposta
from diario.models import Diario
from .services.sentimento_service import analisar_e_salvar
from .services.chat_service import gerar_pergunta_diario



logger = logging.getLogger(__name__)


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

            # Tenta pegar o primeiro diário existente
            diario_vinculo = Diario.objects.first()
            
            # Se o banco estiver vazio, cria um diário genérico de teste na hora!
            if not diario_vinculo:
                diario_vinculo = Diario.objects.create(
                    # Se o seu modelo Diario exigir um título ou algo assim, coloque aqui. 
                    # Exemplo: titulo="Diário de Teste"
                )

            # 2. Salva a mensagem do aluno vinculada a esse diário (agora é 100% garantido que existe)
            nova_resposta = Resposta.objects.create(
                texto_resposta=texto_aluno,
                diario=diario_vinculo 
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