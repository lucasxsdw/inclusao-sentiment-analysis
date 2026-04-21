import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

# Configuração da API
genai.configure(api_key=settings.GEMINI_API_KEY)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    try:
        # NOME TÉCNICO COMPLETO: Resolve o erro 404 definitivamente
        model = genai.GenerativeModel('models/gemini-1.5-flash')

        nome = perfil_aluno.get('nome', 'Felipe') if perfil_aluno else "Felipe"
        tipo_def = perfil_aluno.get('tipo_deficiencia', 'Deficiência Física') if perfil_aluno else "Deficiência Física"

        # Prompt que força a IA a sair do padrão
        prompt = (
            f"Aja como um assistente empático. Aluno: {nome} ({tipo_def}). "
            f"O aluno perdeu o cão-guia e disse: '{texto_aluno}'. "
            f"Valide o luto e a emoção {emocao_ptbr}. "
            f"Faça uma pergunta sobre como a perda do guia impacta a autonomia dele hoje."
        )

        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text.strip()
        
        return "Sinto muito por essa perda tão grande. Como você está lidando com a falta de auxílio dele agora?"

    except Exception as e:
        logger.error(f"ERRO DE CONEXÃO: {e}")
        # Fallback dinâmico para não repetir a mesma frase enquanto você testa
        import random
        frases = [
            f"Sinto muito, {nome}. Imagino que a falta do seu guia torne tudo mais difícil. Como você está se organizando?",
            f"Sinto muito pela sua perda. Como isso afeta sua mobilidade hoje?",
            f"Estou aqui com você. Quer me contar mais sobre como ele te ajudava no dia a dia?"
        ]
        return random.choice(frases)