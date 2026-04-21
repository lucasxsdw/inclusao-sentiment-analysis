import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

# Configura a chave
genai.configure(api_key=settings.GEMINI_API_KEY)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    try:
        # MUDANÇA VITAL: O nome 'gemini-1.5-flash-001' é o endereço estável.
        # Ele resolve o erro 404 de "not found for v1beta".
        model = genai.GenerativeModel('gemini-1.5-flash-001')

        nome = perfil_aluno.get('nome', 'Gisiele') if perfil_aluno else "Gisiele"
        tipo_def = perfil_aluno.get('tipo_deficiencia', 'Dislexia') if perfil_aluno else "Dislexia"

        # Prompt otimizado para gerar respostas variadas
        prompt = (
            f"Você é assistente do Diário de Inclusão. Aluna: {nome} ({tipo_def}). "
            f"Ela desabafou: '{texto_aluno}'. Valide o sentimento de {emocao_ptbr}. "
            f"Faça uma pergunta acolhedora e inédita focada em como a {tipo_def} se relaciona com isso."
        )

        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        
        return "Sinto muito que esteja passando por isso. Quer me contar mais?"

    except Exception as e:
        logger.error(f"ERRO GEMINI: {e}")
        # Fallback inteligente para não repetir sempre a mesma coisa
        import random
        frases = [
            f"Entendo, {nome}. Como você sente que a {tipo_def} afeta esse seu momento?",
            f"Poxa, imagino o peso disso. Como a {tipo_def} influencia o que você está sentindo agora?",
            f"Estou aqui te ouvindo, {nome}. Você acha que isso tem a ver com a {tipo_def}?"
        ]
        return random.choice(frases)