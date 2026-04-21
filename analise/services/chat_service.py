import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

# Configura a API com a sua nova chave
genai.configure(api_key=settings.GEMINI_API_KEY)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    try:
        # Usando o modelo que você já confirmou que funciona!
        model = genai.GenerativeModel('gemini-1.5-flash')

        nome = perfil_aluno.get('nome', 'Felipe') if perfil_aluno else "Felipe"
        tipo_def = perfil_aluno.get('tipo_deficiencia', 'Deficiência Física') if perfil_aluno else ""

        # Um prompt mais livre para a IA não ficar presa
        prompt = (
            f"Você é um assistente escolar empático. Aluno(a): {nome}. "
            f"Contexto: {tipo_def}. O aluno desabafou: '{texto_aluno}'. "
            f"Valide o sentimento de {emocao_ptbr} e faça uma pergunta "
            f"curta e profunda sobre o que ele acabou de dizer."
        )

        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        
        return "Estou te ouvindo com atenção. O que mais você gostaria de compartilhar?"

    except Exception as e:
        logger.error(f"ERRO: {e}")
        # Fallback genérico para não viciar a conversa
        return "Entendo perfeitamente. Como você está lidando com tudo isso hoje?"