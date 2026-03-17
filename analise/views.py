import json
import logging
from django.http import JsonResponse
from django.shortcuts import render
from diario.models import Diario, Pergunta, Resposta
from accounts.models import Aluno

from .services.sentimento_service import analisar_e_salvar
from .services.chat_service import gerar_pergunta_diario

logger = logging.getLogger(__name__)

def enviar_desabafo(request):
    # --- 1. CARREGAMENTO DA TELA (MÉTODO GET) ---
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

    # --- 2. TROCA DE MENSAGENS NO CHAT (MÉTODO POST) ---
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            texto_aluno = dados.get('texto_resposta', '').strip()

            if not texto_aluno:
                return JsonResponse({'erro': 'O texto não pode estar vazio.'}, status=400)

            diario_id = request.session.get('diario_atual_id')
            if not diario_id:
                return JsonResponse({'erro': 'Sessão expirada. Volte à página inicial.'}, status=400)

            diario_vinculo = Diario.objects.get(id=diario_id)
            pergunta_vinculo = Pergunta.objects.order_by("?").first()
            
            if not pergunta_vinculo:
                return JsonResponse({'erro': 'Nenhuma pergunta cadastrada no sistema.'}, status=500)

            # SALVA A RESPOSTA NO BANCO
            nova_resposta = Resposta.objects.create(
                texto_resposta=texto_aluno,
                diario=diario_vinculo,
                pergunta=pergunta_vinculo 
            )

            # CHAMA A IA DE SENTIMENTO (Hugging Face)
            resultado_ia = analisar_e_salvar(nova_resposta)
            emocao_ptbr = resultado_ia["label"] if resultado_ia else "neutro"

            # BUSCA PERFIL DO ALUNO LOGADO
            perfil_aluno = None
            if request.user.is_authenticated:
                try:
                    aluno = Aluno.objects.get(usuario=request.user)
                    perfil_aluno = {
                        'nome': request.user.get_full_name(),
                        'tipo_deficiencia': aluno.get_tipo_deficiencia_display(),
                        'necessidades_especificas': aluno.necessidades_especificas or 'Não informado'
                    }
                except Aluno.DoesNotExist:
                    pass

            # CONTAGEM DAS 5 MENSAGENS
            total_mensagens = Resposta.objects.filter(diario=diario_vinculo).count()

            if total_mensagens >= 5:
                resposta_bot = "Agradeço muito por compartilhar seus sentimentos comigo hoje. Nossa sessão chegou ao fim. Lembre-se: este chat é um apoio inicial e não substitui o acompanhamento psicológico profissional. Por favor, procure o NAPN ou um profissional de saúde se precisar de mais ajuda. Você é muito importante! 💙"
            else:
                resposta_bot = gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno)

            return JsonResponse({
                'sucesso': True,
                'mensagem_aluno': texto_aluno,
                'emocao_detectada': emocao_ptbr,
                'resposta_assistente': resposta_bot,
                'fim_de_sessao': total_mensagens >= 5
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'erro': 'Formato inválido.'}, status=400)
        except Exception as e:
            logger.error(f"Erro na View: {e}")
            return JsonResponse({'erro': 'Erro interno no servidor.'}, status=500)

    return JsonResponse({'erro': 'Método não permitido.'}, status=405)