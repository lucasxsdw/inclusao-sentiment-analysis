import logging
from google import genai
from django.conf import settings
from google.genai import types 
logger = logging.getLogger(__name__)

# 1. Configura o cliente com a nova biblioteca e a sua chave
# cliente Gemini
logger = logging.getLogger(__name__)
client = genai.Client(api_key=settings.GEMINI_API_KEY)
def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None, historico_mensagens=None):
    try:
        # Monta o contexto do aluno (Deficiência/Necessidades)
        contexto_perfil = ""
        if perfil_aluno:
            contexto_perfil = f"O aluno se chama {perfil_aluno.get('nome')}, possui {perfil_aluno.get('tipo_deficiencia')} e tem as seguintes necessidades: {perfil_aluno.get('necessidades_especificas')}."

        system_instruction = f"""Você é o assistente empático do 'Diário de Inclusão'.
        CONTEXTO DO ALUNO: {contexto_perfil}
        
        REGRAS DE OURO:
        1. Responda de forma curta (máximo 3 frases), mas EMPÁTICA.
        2. Use o contexto da deficiência do aluno para oferecer um suporte personalizado.
        3. SEMPRE termine com uma pergunta acolhedora e aberta para manter a conversa.
        4. Se o aluno falar de bullying ou fracasso, valide o sentimento antes de perguntar algo."""

        conteudos_historico = []
        if historico_mensagens:
            for msg in historico_mensagens:
                role = "user" if msg['papel'] == "user" else "model"
                conteudos_historico.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.get('texto', '...'))]))

        prompt_final = f"[Emoção: {emocao_ptbr}] {texto_aluno}"
        conteudos_historico.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt_final)]))

        resposta_ia = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=conteudos_historico,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7, # Aumentamos para ela ser menos "travada"
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                ]
            )
        )
        
        if resposta_ia and resposta_ia.text:
            return resposta_ia.text.strip()
        
        return "Sinto muito por isso. Como você está lidando com esse sentimento agora?"

    except Exception as e:
        logger.error(f"Erro Gemini: {e}")
        return "Entendo que as coisas estão difíceis. Quer me contar mais sobre o que aconteceu?"