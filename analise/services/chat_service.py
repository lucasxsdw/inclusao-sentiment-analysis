import logging
from google import genai
from django.conf import settings
from google.genai import types 
logger = logging.getLogger(__name__)

# 1. Configura o cliente com a nova biblioteca e a sua chave
# cliente Gemini
logger = logging.getLogger(__name__)
client = genai.Client(api_key=settings.GEMINI_API_KEY)


def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None, historico_mensagens=None):
    try:
        modelo = 'gemini-2.5-flash'
        # ... (seu código de montar o contexto_perfil e system_instruction continua igual) ...
        
        system_instruction = f"""Você é o assistente virtual do 'Diário de Inclusão'... (resto do seu prompt)"""

        conteudos_historico = []
        if historico_mensagens:
            for msg in historico_mensagens:
                role = "user" if msg['papel'] == "user" else "model"
                conteudos_historico.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=msg['texto'])])
                )

        prompt_nova_mensagem = f"[Emoção declarada: {emocao_ptbr}]\n{texto_aluno}"
        conteudos_historico.append(
            types.Content(role="user", parts=[types.Part.from_text(text=prompt_nova_mensagem)])
        )

        # --- A MÁGICA DOS FILTROS ACONTECE AQUI NA CONFIGURAÇÃO ---
        # ... seu código anterior ...
        resposta_ia = client.models.generate_content(
            model=modelo,
            contents=conteudos_historico,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.4, # Abaixamos a temperatura para ser mais direto
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                ]
            )
        )
        
        # VERIFICAÇÃO DE BLOQUEIO:
        if not resposta_ia.candidates or not resposta_ia.candidates[0].content.parts:
            return "Sinto muito que esteja passando por isso. Estou aqui para te ouvir."

        return resposta_ia.text.strip()
        

    except Exception as e:
        logger.error(f"Erro ao gerar pergunta com Gemini: {e}", exc_info=True)
        return "Desculpe, tive um probleminha técnico por aqui. Quer tentar me contar de novo?"