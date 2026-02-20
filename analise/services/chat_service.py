import logging
from google import genai
from django.conf import settings

logger = logging.getLogger(__name__)

# 1. Configura o cliente com a nova biblioteca e a sua chave
client = genai.Client(api_key=settings.GEMINI_API_KEY)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno):
    """
    Gera uma pergunta empática usando a IA do Gemini, baseada na emoção e no texto do aluno.
    """
    try:
        # Usamos o modelo atualizado e gratuito do Google
        modelo = 'gemini-2.5-flash'
        
        # O nosso Prompt de Sistema Sênior
        prompt = f"""Você é o assistente virtual do 'Diário de Inclusão', um ambiente seguro e acolhedor para alunos desabafarem.
        Seu tom é informal, empático e amigável, como um conselheiro escolar jovem.
        
        REGRAS ESTRITAS:
        1. NUNCA dê diagnósticos médicos, psicológicos ou conselhos diretivos sobre o que o aluno deve fazer.
        2. NUNCA minimize o problema do aluno com positividade tóxica (evite frases prontas como 'tudo vai dar certo').
        3. Suas respostas devem ser MUITO curtas, parecidas com mensagens de chat (máximo de 2 frases).
        4. Valide a emoção do aluno e termine sempre com uma única pergunta aberta e suave que o ajude a refletir.
        
        DADOS DO ALUNO:
        Emoção detectada pela IA primária: {emocao_ptbr}
        Desabafo do aluno: "{texto_aluno}"
        
        Escreva sua resposta agora:"""

        # 2. Chama a IA usando a nova sintaxe da biblioteca google-genai
        resposta_ia = client.models.generate_content(
            model=modelo,
            contents=prompt
        )
        
        # 3. Retorna o texto limpo
        return resposta_ia.text.strip()

    except Exception as e:
        logger.error(f"Erro ao gerar pergunta com Gemini: {e}")
        return "Poxa, entendo como você está se sentindo. Quer me contar um pouco mais sobre isso?"