import requests
import logging
from django.conf import settings
from deep_translator import GoogleTranslator
from analise.models import AnaliseResposta

logger = logging.getLogger(__name__)

# modelo estável em inglês (Plano B)
EMOTION_URL = "https://router.huggingface.co/hf-inference/models/j-hartmann/emotion-english-distilroberta-base"
HEADERS = {
    "Authorization": f"Bearer {settings.HF_TOKEN}"
}

def traduzir_pt_para_en(texto):
    try:
        tradutor = GoogleTranslator(source='pt', target='en')
        return tradutor.translate(texto)
    except Exception as e:
        logger.error(f"Erro na tradução: {e}")
        return texto # Retorna original se a tradução falhar


def analisar_emocao(texto_em_ingles):
    try:
        response = requests.post(
            EMOTION_URL,
            headers=HEADERS,
            json={"inputs": texto_em_ingles},
            timeout=10
        )
        
        response.raise_for_status()
        dados = response.json()
        
        if not dados or not isinstance(dados, list) or len(dados) == 0:
            logger.warning(f"Resposta inesperada da HF: {dados}")
            return None
            
        resultado = dados[0]
        emocao = max(resultado, key=lambda x: x.get("score", 0))

        return {
            "label": emocao.get("label", "unknown"),
            "score": emocao.get("score", 0.0)
        }

    except requests.exceptions.Timeout:
        logger.error("Timeout: A Hugging Face demorou para responder.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de conexão com a Hugging Face: {e}")
        return None

def analisar_e_salvar(resposta_obj):
    # 1. Traduz para o inglês
    texto_traduzido = traduzir_pt_para_en(resposta_obj.texto_resposta)
    
    # 2. Analisa a emoção com o texto em inglês
    resultado = analisar_emocao(texto_traduzido)
    if resultado:
        #Dicionario de mapeamento
        mapa_emocoes = {
            "anger": "raiva",
            "disgust": "nojo",
            "fear": "medo",
            "joy": "alegria",
            "neutral": "neutro",
            "sadness": "tristeza",
            "surprise": "surpresa"
        }

        # traduz a emocao com segurança usando o get
        #se a Ia retornar uma label desconhecida, ela será mapeada para "desconhecido"
        emocao_em_portugues = mapa_emocoes.get(resultado["label"], "desconecido")
        # 3. Salva no banco de dados
        AnaliseResposta.objects.create(
            resposta=resposta_obj,
            sentimento_detectado=emocao_em_portugues,
            score_sentimento=resultado["score"],
            modelo_ia="j-hartmann/emotion-english-distilroberta-base"
        )
        return resultado

    return None