import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # ESSA É A CHAVE PARA DESBLOQUEAR:
        # Configuramos para não bloquear quase nada (BLOCK_NONE)
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        prompt = (
            f"Você é um tutor de apoio escolar. O aluno desabafou: '{texto_aluno}'. "
            f"Ele está sentindo {emocao_ptbr}. Valide o sentimento dele com empatia "
            f"e faça uma pergunta curta para ele continuar o desabafo."
        )

        # Passamos as configurações de segurança aqui
        response = model.generate_content(prompt, safety_settings=safety_settings)
        
        # Verificamos se a IA gerou texto ou se foi bloqueada
        if response and response.candidates and response.candidates[0].content.parts:
            return response.text.strip()
        
        return "Sinto muito que esteja passando por isso. Pode me contar mais detalhes?"

    except Exception as e:
        logger.error(f"Erro no Gemini: {e}")
        return "Estou aqui para te ouvir. Como isso tem afetado seu dia?"