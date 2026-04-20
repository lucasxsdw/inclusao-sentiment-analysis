import logging
from google import genai
from google.genai import types
from django.conf import settings

logger = logging.getLogger(__name__)

# Problema 4 corrigido: nome correto do modelo
MODELO = 'gemini-2.0-flash'

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    """
    Gera resposta empática usando Gemini.
    Corrigido: protocolo de papéis, filtros de segurança, contexto de perfil e nome do modelo.
    """
    try:
        # Problema 3 corrigido: contexto do perfil sempre montado corretamente
        contexto_perfil = ""
        if perfil_aluno and isinstance(perfil_aluno, dict):
            nome = perfil_aluno.get('nome') or 'Não informado'
            tipo_def = perfil_aluno.get('tipo_deficiencia') or 'Não informado'
            necessidades = perfil_aluno.get('necessidades_especificas') or 'Não informado'

            contexto_perfil = f"""
PERFIL DO ALUNO (USE PARA PERSONALIZAR SUA RESPOSTA):
- Nome: {nome}
- Tipo de deficiência: {tipo_def}
- Necessidades específicas: {necessidades}

INSTRUÇÃO ESPECIAL: Se o desabafo do aluno puder estar relacionado à sua deficiência,
conecte os dois de forma natural e acolhedora na sua pergunta.
Por exemplo: se tem baixa visão e foi mal na prova, pergunte se a deficiência dificultou.
Se tem TEA e está ansioso com interações sociais, conecte isso ao desabafo.
"""

        system_prompt = f"""Você é o assistente virtual do 'Diário de Inclusão', um ambiente seguro e acolhedor para alunos desabafarem.
Seu tom é informal, empático e amigável, como um conselheiro escolar jovem.

REGRAS ESTRITAS:
1. NUNCA dê diagnósticos médicos, psicológicos ou conselhos diretivos.
2. NUNCA minimize o problema com positividade tóxica (evite 'tudo vai dar certo').
3. Respostas MUITO curtas — máximo 2 frases estilo chat.
4. Valide a emoção e termine com UMA pergunta aberta e suave.
5. Adapte sua linguagem às necessidades específicas do aluno.
{contexto_perfil}"""

        # Problema 1 corrigido: estrutura correta User->Model sem conflito de papéis
        # Problema 2 corrigido: BLOCK_NONE para palavras sensíveis do contexto emocional
        safety_settings = [
            types.SafetySetting(
                category='HARM_CATEGORY_HARASSMENT',
                threshold='BLOCK_NONE'
            ),
            types.SafetySetting(
                category='HARM_CATEGORY_HATE_SPEECH',
                threshold='BLOCK_NONE'
            ),
            types.SafetySetting(
                category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
                threshold='BLOCK_NONE'
            ),
            types.SafetySetting(
                category='HARM_CATEGORY_DANGEROUS_CONTENT',
                threshold='BLOCK_NONE'
            ),
        ]

        mensagem_usuario = f"Emoção detectada: {emocao_ptbr}\nDesabafo do aluno: \"{texto_aluno}\"\n\nEscreva sua resposta agora:"

        resposta_ia = client.models.generate_content(
            model=MODELO,
            contents=mensagem_usuario,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                safety_settings=safety_settings,
                max_output_tokens=200,
                temperature=0.7,
            )
        )

        # Verifica se a resposta tem conteúdo válido
        if resposta_ia and resposta_ia.text and resposta_ia.text.strip():
            return resposta_ia.text.strip()

        logger.warning("Gemini retornou resposta vazia ou bloqueada.")
        return "Entendo o que você está sentindo. Quer me contar um pouco mais sobre isso?"

    except Exception as e:
        logger.error(f"Erro ao gerar resposta com Gemini: {e}")
        return "Poxa, entendo como você está se sentindo. Quer me contar um pouco mais sobre isso?"