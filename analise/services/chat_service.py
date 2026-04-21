import google.generativeai as genai
from django.conf import settings

# Configuração simples
genai.configure(api_key=settings.GEMINI_API_KEY)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    try:
        # Forçamos o modelo estável que está no seu README e requirements
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        nome = perfil_aluno.get('nome', 'Aluno') if perfil_aluno else "Aluno"
        tipo_def = perfil_aluno.get('tipo_deficiencia', 'Dislexia') if perfil_aluno else ""

        # Prompt que força a resposta a ser diferente do fallback
        prompt = (
            f"Você é assistente do NAPNE. Aluno: {nome} ({tipo_def}). "
            f"Desabafo: {texto_aluno}. Responda em 2 frases, valide a emoção "
            f"{emocao_ptbr} e pergunte como a {tipo_def} afeta isso agora."
        )

        response = model.generate_content(prompt)
        return response.text.strip() if response.text else "Conte-me mais sobre isso."

    except Exception as e:
        # Fallback dinâmico para NUNCA repetir a mesma frase
        import random
        frases = ["Como você se sente?", "Pode detalhar melhor?", "Estou te ouvindo."]
        return f"{random.choice(frases)} (Erro técnico: {str(e)[:20]})"