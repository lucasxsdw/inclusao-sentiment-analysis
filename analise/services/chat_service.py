import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

# Configuração da API antiga/estável
genai.configure(api_key=settings.GEMINI_API_KEY)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        nome = perfil_aluno.get('nome', 'Aluno') if perfil_aluno else "Aluno"
        tipo_def = perfil_aluno.get('tipo_deficiencia', 'Não informada') if perfil_aluno else "Não informada"

        # Prompt mais direto e simples (menos chance de erro)
        prompt = (
            f"Você é um assistente escolar empático. Aluna: {nome} com {tipo_def}. "
            f"Ela disse: '{texto_aluno}'. Valide o sentimento de {emocao_ptbr} e "
            f"faça uma pergunta curta e acolhedora sobre como a {tipo_def} afeta isso."
        )

        response = model.generate_content(prompt)

        if response and response.text:
            return response.text.strip()
        
        return "Sinto muito. Pode me contar mais sobre como você se sente?"

    except Exception as e:
        logger.error(f"ERRO NO SERVIÇO: {e}")
        # AQUI ESTÁ O SEGREDO: Vamos retornar o erro na tela para você ler o que está havendo!
        return f"A IA falhou: {str(e)[:50]}... Mas me diga, Gisiele, como você está?"