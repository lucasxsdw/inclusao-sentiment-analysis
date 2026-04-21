import logging
from google import genai
from google.genai import types
from django.conf import settings

logger = logging.getLogger(__name__)

# Mudamos para o 1.5-flash: mais cota e mais estabilidade para TCC
MODELO = 'gemini-1.5-flash'

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    try:
        # 1. Extração limpa dos dados do aluno
        nome = "Aluno"
        contexto_deficiencia = "Não informada"
        if perfil_aluno:
            nome = perfil_aluno.get('nome', 'Aluno')
            contexto_deficiencia = f"{perfil_aluno.get('tipo_deficiencia')} com as necessidades: {perfil_aluno.get('necessidades_especificas')}"

        # 2. System Instruction Direta e Curta
        system_prompt = f"""Você é o assistente do 'Diário de Inclusão'.
        ALUNO: {nome}
        DEFICIÊNCIA: {contexto_deficiencia}
        
        MISSÃO:
        - Valide a emoção '{emocao_ptbr}' de forma carinhosa.
        - Relacione o desabafo com a deficiência do aluno de forma sutil.
        - Responda em no máximo 2 frases.
        - Termine com uma pergunta sobre como a deficiência afetou o que ele sentiu."""

        # 3. Chamada da API seguindo o protocolo oficial
        response = client.models.generate_content(
            model=MODELO,
            contents=f"O aluno desabafou: {texto_aluno}",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                safety_settings=[
                    types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                    types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                ],
                temperature=0.7,
                max_output_tokens=150,
            )
        )

        if response and response.text:
            return response.text.strip()
        
        return "Entendo sua dor. Como sua condição influenciou nisso que você me contou?"

    except Exception as e:
        logger.error(f"Erro no Gemini: {e}")
        # Retorna o erro real para o seu teste, mas com fallback se for apenas erro de texto
        raise e