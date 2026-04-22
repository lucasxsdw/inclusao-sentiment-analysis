import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

# Configuração definitiva para evitar o 404 e usar a cota estável
genai.configure(api_key=settings.GEMINI_API_KEY, transport='rest') 

# Usar 'gemini-1.5-flash-latest' é a forma mais segura para a versão 0.8.3
MODELO = 'gemini-1.5-flash-latest' 

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    try:
        contexto_perfil = ""
        if perfil_aluno and isinstance(perfil_aluno, dict):
            nome = perfil_aluno.get('nome') or 'Não informado'
            tipo_def = perfil_aluno.get('tipo_deficiencia') or 'Não informado'
            necessidades = perfil_aluno.get('necessidades_especificas') or 'Não informado'
            contexto_perfil = f"""
PERFIL DO ALUNO:
- Nome: {nome}
- Deficiência: {tipo_def}
- Necessidades: {necessidades}

INSTRUÇÃO: Conecte o desabafo à deficiência se fizer sentido, de forma acolhedora.
"""

        system_prompt = f"""Você é o assistente do 'Diário de Inclusão'. 
Tom informal, empático e amigável. Máximo 2 frases.
Regras: Sem diagnósticos, sem positividade tóxica, termine com uma pergunta aberta.
{contexto_perfil}
DADOS ATUAIS:
Emoção: {emocao_ptbr}
Desabafo: "{texto_aluno}"
"""

        # Configuração de segurança para não bloquear desabafos sensíveis
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        model = genai.GenerativeModel(
            model_name=MODELO,
            safety_settings=safety_settings
        )

        resposta_ia = model.generate_content(system_prompt)

        # Verificação robusta da resposta
        if resposta_ia and hasattr(resposta_ia, 'text') and resposta_ia.text.strip():
            return resposta_ia.text.strip()

        return "Entendo o que você está sentindo. Quer me contar um pouco mais sobre isso?"

    except Exception as e:
        logger.error(f"Erro Crítico Gemini: {e}")
        # Fallback amigável se a API falhar (cota ou conexão)
        return "Poxa, eu te entendo perfeitamente. O que mais está passando pela sua cabeça agora?"