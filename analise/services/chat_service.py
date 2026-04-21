import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

# Configura a chave que está no seu .env
genai.configure(api_key=settings.GEMINI_API_KEY)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    try:
        # NOME SIMPLES: Sem 'models/' e sem '-latest' para evitar o 404 nesta versão
        model = genai.GenerativeModel('gemini-1.5-flash')

        nome = perfil_aluno.get('nome', 'Gisiele') if perfil_aluno else "Gisiele"
        tipo_def = perfil_aluno.get('tipo_deficiencia', 'Dislexia') if perfil_aluno else "Dislexia"

        # Prompt direto para garantir que a IA responda algo novo
        prompt = (
            f"Você é o assistente do Diário de Inclusão. Aluna: {nome} ({tipo_def}). "
            f"Ela disse: '{texto_aluno}'. Valide o sentimento de {emocao_ptbr} e "
            f"faça uma pergunta curta e diferente sobre como a {tipo_def} afeta isso."
        )

        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        
        return "Estou te ouvindo. Pode me contar mais?"

    except Exception as e:
        logger.error(f"ERRO: {e}")
        # Fallback que usa os dados do aluno para não parecer erro
        return f"Entendo, {nome}. Como você acha que a {tipo_def} torna esse momento mais difícil?"