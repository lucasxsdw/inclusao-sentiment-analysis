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
        # 1. Garante que o texto do aluno não seja nulo
        texto_aluno = texto_aluno if texto_aluno else "Estou aqui para conversar."
        
        system_instruction = """Você é o assistente do 'Diário de Inclusão'. 
        REGRAS:
        1. Máximo 200 caracteres. Seja breve.
        2. Não dê conselhos longos. Valide o sentimento.
        3. Nunca termine com perguntas abertas."""

        # 2. Montagem SEGURA do histórico
        conteudos_historico = []
        if historico_mensagens:
            for msg in historico_mensagens:
                # Garante que 'texto' nunca seja vazio ou None
                txt = msg.get('texto', '').strip()
                if not txt:
                    txt = "..." # Valor padrão para não quebrar a API
                
                role = "user" if msg['papel'] == "user" else "model"
                conteudos_historico.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=txt)])
                )

        # 3. Adiciona a mensagem ATUAL do aluno
        prompt_final = f"[Contexto Emocional: {emocao_ptbr}] {texto_aluno}"
        conteudos_historico.append(
            types.Content(role="user", parts=[types.Part.from_text(text=prompt_final)])
        )

        # 4. Chamada da API com o modelo correto e sem filtros
        resposta_ia = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=conteudos_historico,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                ]
            )
        )
        
        # 5. Verifica se a resposta veio de fato
        if resposta_ia and hasattr(resposta_ia, 'text') and resposta_ia.text:
            return resposta_ia.text.strip()
        
        return "Entendo perfeitamente o que você está sentindo. Me conte mais."

    except Exception as e:
        logger.error(f"ERRO CRÍTICO NO GEMINI: {e}", exc_info=True)
        # Se tudo der errado, retorne uma frase neutra em vez da frase de erro técnica
        return "Entendo. Sinto muito que as coisas estejam difíceis na faculdade hoje."