import requests
import logging
from django.conf import settings
from analise.models import AnaliseResposta

# 1. Configuração do Logger em vez de 'print'
logger = logging.getLogger(__name__)

EMOTION_URL = "https://router.huggingface.co/hf-inference/models/j-hartmann/emotion-english-distilroberta-base"

HEADERS = {
    "Authorization": f"Bearer {settings.HF_TOKEN}"
}

def analisar_emocao(texto):
    try:
        # 2. Chamada com Timeout
        response = requests.post(
            EMOTION_URL,
            headers=HEADERS,
            json={"inputs": texto},
            timeout=5  
        )
        
        # 3. Validação de Status HTTP Automática
        response.raise_for_status()
        
        dados = response.json()
        
        # 4. Programação Defensiva: Valida a estrutura da resposta
        if not dados or not isinstance(dados, list) or len(dados) == 0:
            logger.warning(f"Resposta da Hugging Face malformada. Dados: {dados}")
            return None
            
        resultado = dados[0]
        emocao = max(resultado, key=lambda x: x.get("score", 0))

        return {
            "label": emocao.get("label", "unknown"),
            "score": emocao.get("score", 0.0)
        }

    # 5. Captura de Erros Específicos
    except requests.exceptions.Timeout:
        logger.error("Timeout: A Hugging Face demorou mais de 5 segundos para responder.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de conexão com a Hugging Face: {e}")
        return None
    except (ValueError, KeyError, IndexError) as e:
        logger.error(f"Erro ao processar o JSON da Hugging Face: {e}")
        return None


def analisar_e_salvar(resposta_obj):
    resultado = analisar_emocao(resposta_obj.texto_resposta)

    if resultado:
        AnaliseResposta.objects.create(
            resposta=resposta_obj,
            sentimento_detectado=resultado["label"],
            score_sentimento=resultado["score"],
            modelo_ia="j-hartmann/emotion-english-distilroberta-base"
        )
        return resultado

    return None