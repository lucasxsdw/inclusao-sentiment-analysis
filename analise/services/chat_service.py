import logging
from groq import Groq
from django.conf import settings

logger = logging.getLogger(__name__)

# Inicializa o cliente Groq
# Certifique-se de ter GROQ_API_KEY no seu settings.py apontando para o .env/Render
client = Groq(api_key=settings.GROQ_API_KEY)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    try:
        contexto_perfil = ""
        if perfil_aluno and isinstance(perfil_aluno, dict):
            nome = perfil_aluno.get('nome', 'Aluno')
            tipo_def = perfil_aluno.get('tipo_deficiencia', 'Não informado')
            necessidades = perfil_aluno.get('necessidades_especificas', 'Não informado')
            contexto_perfil = f"\nALUNO: {nome}\nDEFICIÊNCIA: {tipo_def}\nNECESSIDADES: {necessidades}"

        system_prompt = f"""Você é o assistente empático do 'Diário de Inclusão'.
Responda de forma curta (máximo 2 frases), informal e muito acolhedora.
NÃO dê diagnósticos ou conselhos médicos. Termine sempre com uma pergunta aberta.
{contexto_perfil}
DADOS DO DESABAFO:
Emoção detectada: {emocao_ptbr}
Texto do aluno: "{texto_aluno}" """

        # Chamada ao modelo Llama 3.1 (Sucessor oficial e muito mais rápido)
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", # <--- O NOME NOVO É ESTE
            messages=[
                {"role": "system", "content": "Você é um assistente de apoio emocional escolar."},
                {"role": "user", "content": system_prompt}
            ],
            temperature=0.7,
            max_tokens=150,
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Erro no serviço Groq: {e}")
        return "Sinto muito que você esteja passando por isso. Quer me contar um pouco mais sobre o que aconteceu?"