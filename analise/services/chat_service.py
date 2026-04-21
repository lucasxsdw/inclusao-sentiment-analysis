import logging
import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)

# Configuração da biblioteca estável
# Certifique-se que GEMINI_API_KEY está correta no Render
genai.configure(api_key=settings.GEMINI_API_KEY)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None):
    """
    Gera resposta empática conectando o desabafo com a deficiência do aluno.
    Utiliza a biblioteca google-generativeai (estável).
    """
    try:
        # Uso do nome técnico completo para evitar Erro 404
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

        # extração segura dos dados do perfil
        nome = "Aluno"
        tipo_def = "Não informada"
        necessidades = ""

        if perfil_aluno and isinstance(perfil_aluno, dict):
            nome = perfil_aluno.get('nome', 'Aluno')
            tipo_def = perfil_aluno.get('tipo_deficiencia', 'Não informada')
            necessidades = perfil_aluno.get('necessidades_especificas', '')

        # Prompt otimizado para a versão 1.5 Flash
        system_prompt = (
            f"Você é o assistente empático do 'Diário de Inclusão'. "
            f"Sua missão é apoiar a aluna {nome}, que possui {tipo_def}. "
            f"REGRAS: 1. Responda em no máximo 2 frases. "
            f"2. Valide a emoção '{emocao_ptbr}' de forma carinhosa. "
            f"3. Conecte o desabafo com a deficiência ({tipo_def}) de forma sutil. "
            f"4. Termine com uma pergunta acolhedora."
        )

        # Chamada da API
        response = model.generate_content(
            f"{system_prompt}\n\nO aluno desabafou: {texto_aluno}",
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=150,
            ),
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            ]
        )

        # Verificação de resposta
        if response and response.text:
            return response.text.strip()
        
        # Caso a IA retorne vazio por algum filtro de segurança do Google
        return f"Entendo seu sentimento, {nome}. Como você acha que a {tipo_def} influencia nisso que você me contou?"

    except Exception as e:
        # Log do erro para depuração no Render
        logger.error(f"ERRO CRÍTICO GEMINI: {e}")
        
        # Fallback inteligente: Se a API falhar (cota ou rede), 
        # o sistema responde usando os dados do aluno para não parecer erro.
        return f"Poxa, imagino como deve ser difícil lidar com esse momento e com a {tipo_def} ao mesmo tempo. Quer me contar mais sobre o que você está sentindo?"