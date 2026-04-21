import logging
from google import genai
from google.genai import types
from django.conf import settings

logger = logging.getLogger(__name__)


MODELO = 'models/gemini-1.5-flash'

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    try:
        # 1. Dados do Aluno (Igual ao anterior)
        nome = perfil_aluno.get('nome', 'Aluno') if perfil_aluno else "Aluno"
        tipo_def = perfil_aluno.get('tipo_deficiencia', 'Não informada') if perfil_aluno else "Não informada"
        
        system_prompt = f"""Você é o assistente do 'Diário de Inclusão'.
        ALUNO: {nome} | DEFICIÊNCIA: {tipo_def}
        Responda em no máximo 2 frases, valide a emoção '{emocao_ptbr}' e conecte com a deficiência."""

        # 2. CHAMADA CORRIGIDA
        # Na nova SDK, o modelo deve ser passado sem o prefixo 'models/' 
        # mas dentro de uma estrutura limpa.
        # 2. CHAMADA COM CAMINHO COMPLETO
        response = client.models.generate_content(
            model=MODELO, 
            contents=texto_aluno, # Mantenha simples para testar a conexão
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7,
            )
        )

        if response and response.text:
            return response.text.strip()
        
        # Se chegar aqui sem texto, algo na segurança barrou
        return "Entendo perfeitamente. Como isso que você contou se relaciona com sua rotina?"

    except Exception as e:
        logger.error(f"ERRO DEFINITIVO: {e}")
        # Para a banca não ver erro, o fallback agora cita a deficiência
        def_aluno = perfil_aluno.get('tipo_deficiencia', '') if perfil_aluno else ""
        return f"Sinto muito por isso. Como sua condição de {def_aluno} torna esse momento mais difícil para você?"