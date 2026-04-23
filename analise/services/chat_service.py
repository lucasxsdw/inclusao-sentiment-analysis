import logging
from groq import Groq
from django.conf import settings
from diario.models import Resposta

logger = logging.getLogger(__name__)
client = Groq(api_key=settings.GROQ_API_KEY)

def gerar_pergunta_diario(emocao_ptbr, texto_aluno, perfil_aluno=None, diario_id=None):
    try:
        # 1. Recuperar o histórico recente para a IA não "esquecer" o que foi dito
        historico_texto = ""
        if diario_id:
            mensagens_anteriores = Resposta.objects.filter(diario_id=diario_id).order_by('-id')[:3]
            for m in reversed(mensagens_anteriores):
                historico_texto += f"Aluno: {m.texto_resposta}\n"

        # 2. Preparar o contexto da deficiência
        contexto_deficiencia = "Não informado"
        if perfil_aluno:
            contexto_deficiencia = f"{perfil_aluno.get('tipo_deficiencia', 'Não informado')}. Necessidades: {perfil_aluno.get('necessidades_especificas', 'Não informado')}"

        # 3. System Prompt "Turbinado"
        system_prompt = f"""
        Você é o assistente empático do 'Diário de Inclusão'.
        OBJETIVO: Apoiar alunos com deficiência (PCD) do IF Baiano.
        
        PERFIL DO ALUNO: {perfil_aluno.get('nome', 'Aluno')}
        DEFICIÊNCIA: {contexto_deficiencia}
        
        REGRAS CRÍTICAS:
        1. Se o aluno responder de forma curta (Ex: "sim", "bastante", "não"), NÃO reinicie a conversa. Use o HISTÓRICO abaixo para continuar o assunto.
        2. Tente ligar o desabafo com a DEFICIÊNCIA dele (Ex: se ele está cansado e tem deficiência física, pergunte sobre a acessibilidade no trajeto).
        3. Responda em no máximo 2 frases curtas.
        4. Termine SEMPRE com uma pergunta aberta.

        HISTÓRICO RECENTE:
        {historico_texto}
        
        DADOS ATUAIS:
        Emoção detectada agora: {emocao_ptbr}
        Última fala do aluno: "{texto_aluno}"
        """

        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Você é um mentor de apoio emocional escolar especializado em inclusão."},
                {"role": "user", "content": system_prompt}
            ],
            temperature=0.6, # Menor temperatura para ser menos "viajado"
            max_tokens=150,
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Erro no Groq: {e}")
        return "Entendo que isso te afeta. Como sua rotina na escola tem lidado com essa situação?"