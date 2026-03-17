import logging
from google import genai
from django.conf import settings

logger = logging.getLogger(__name__)

# 1. Configura o cliente com a nova biblioteca e a sua chave
# cliente Gemini
client = genai.Client(api_key=settings.GEMINI_API_KEY)


def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    try:
        modelo = 'gemini-2.5-flash'

        # Monta contexto do perfil se existir
        contexto_perfil = ""
        if perfil_aluno:
            contexto_perfil = f"""
        PERFIL DO ALUNO:
        - Nome: {perfil_aluno.get('nome', 'Não informado')}
        - Tipo de deficiência: {perfil_aluno.get('tipo_deficiencia', 'Não informado')}
        - Necessidades específicas: {perfil_aluno.get('necessidades_especificas', 'Não informado')}
        """

        prompt = f"""Você é o assistente virtual do 'Diário de Inclusão', um ambiente seguro e acolhedor para alunos desabafarem.
        Seu tom é informal, empático e amigável, como um conselheiro escolar jovem.

        REGRAS ESTRITAS:
        1. NUNCA dê diagnósticos médicos, psicológicos ou conselhos diretivos.
        2. NUNCA minimize o problema com positividade tóxica.
        3. Respostas MUITO curtas, máximo 2 frases estilo chat.
        4. Valide a emoção e termine com UMA pergunta aberta e suave.
        5. Se o desabafo do aluno puder estar relacionado à sua deficiência, conecte os dois ativamente na sua pergunta. Por exemplo: se o aluno tem baixa visão e foi mal na prova, pergunte se a deficiência dificultou a realização da prova. Se o aluno tem TEA e está ansioso com interações sociais, conecte isso. Faça essa ligação de forma natural e acolhedora, nunca de forma invasiva.
        6. Adapte sua linguagem às necessidades específicas do aluno.
        {contexto_perfil}
        DADOS DO ALUNO:
        Emoção detectada: {emocao_ptbr}
        Desabafo do aluno: "{texto_aluno}"

        Escreva sua resposta agora:"""

        resposta_ia = client.models.generate_content(
            model=modelo,
            contents=prompt
        )
        
        return resposta_ia.text.strip()

    except Exception as e:
        logger.error(f"Erro ao gerar pergunta com Gemini: {e}")
        return "Poxa, entendo como você está se sentindo. Quer me contar um pouco mais sobre isso?"