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
        modelo = 'gemini-2.0-flash' # Verifique se não está '2.5' no seu código
        
        system_instruction = """Você é o assistente do 'Diário de Inclusão'. 
        REGRAS CRÍTICAS:
        1. Responda em no máximo 200 caracteres (curto e direto).
        2. Seja empático, mas não dê conselhos longos.
        3. NUNCA faça perguntas abertas no final.
        4. Se o usuário falar de bullying ou sofrimento, valide o sentimento de forma breve e acolhedora."""

        # ... (montagem do histórico continua igual) ...

        resposta_ia = client.models.generate_content(
            model='gemini-2.0-flash', # Certifique-se de que a versão está correta
            contents=conteudos_historico,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
                # Isso impede que a IA trave ao ler palavras tristes
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                ]
            )
        )
        
        # Se a IA for bloqueada mesmo assim, evite o erro genérico
        if not resposta_ia.candidates or not resposta_ia.candidates[0].content.parts:
            return "Entendo como isso é difícil para você. Saiba que não está sozinho e eu estou aqui para te ouvir."

        return resposta_ia.text.strip()

    except Exception as e:
        logger.error(f"Erro: {e}")
        return "Desculpe, tive um probleminha técnico por aqui. Quer tentar me contar de novo?"