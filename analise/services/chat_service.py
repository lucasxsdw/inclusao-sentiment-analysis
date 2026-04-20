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
        # 1. NOME DO MODELO (O 2.5 não existe, use 2.0-flash)
        modelo_nome = 'gemini-2.0-flash' 
        
        # 2. CONSTRUÇÃO DO PROMPT DINÂMICO
        contexto = ""
        if perfil_aluno:
            contexto = f"Aluno: {perfil_aluno.get('nome')}, Deficiência: {perfil_aluno.get('tipo_deficiencia')}. "

        system_instruction = f"""Você é o assistente do 'Diário de Inclusão'. {contexto}
        REGRAS:
        1. Responda de forma curta e empática (máximo 3 frases).
        2. SEMPRE termine com uma pergunta acolhedora sobre o que o aluno sentiu.
        3. Valide o sofrimento do aluno sem julgamentos.
        4. Use o contexto da deficiência dele apenas se for relevante para o suporte."""

        # 3. LIMPEZA DO HISTÓRICO (Vital para não dar erro de conexão)
        # 2. Montagem ULTRA SEGURA do histórico
        conteudos_historico = []
        if historico_mensagens:
            ultimo_papel = None
            for msg in historico_mensagens:
                papel_atual = "user" if msg['papel'] == "user" else "model"
                texto = msg.get('texto', '').strip()

                # REGRA DE OURO: Só adiciona se o texto existir e NÃO repetir o papel anterior
                if texto and papel_atual != ultimo_papel:
                    conteudos_historico.append(
                        types.Content(role=papel_atual, parts=[types.Part.from_text(text=texto)])
                    )
                    ultimo_papel = papel_atual

        # REGRA DE OURO 2: O Gemini SEMPRE exige que a última mensagem antes da resposta seja do USER
        # Se a última do histórico foi USER, a gente remove ela para colocar a ATUAL
        if conteudos_historico and conteudos_historico[-1].role == "user":
            conteudos_historico.pop()

        # 3. Adiciona a mensagem ATUAL do aluno (Garantindo que seja USER)
        prompt_final = f"[Contexto: {emocao_ptbr}] {texto_aluno}"
        conteudos_historico.append(
            types.Content(role="user", parts=[types.Part.from_text(text=prompt_final)])
        )

        # 5. CHAMADA BLINDADA
        resposta_ia = client.models.generate_content(
            model=modelo_nome,
            contents=conteudos_historico,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                # DESATIVA TODOS OS FILTROS (Indispensável para TCC de inclusão)
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                ]
            )
        )
        
        if resposta_ia and resposta_ia.text:
            return resposta_ia.text.strip()
        
        return "Sinto muito por isso. Quer me contar como está se sentindo agora?"

    except Exception as e:
        logger.error(f"ERRO GEMINI: {e}")
        # Se a IA falhar, o aluno recebe isso e o sistema não parece quebrado
        return "Sinto muito por isso. É um peso grande para carregar, mas estou aqui ouvindo você. Quer me contar mais?"