import requests
from django.conf import settings

from analise.models import AnaliseResposta

EMOTION_URL = "https://router.huggingface.co/hf-inference/models/j-hartmann/emotion-english-distilroberta-base"

HEADERS = {
    "Authorization": f"Bearer {settings.HF_TOKEN}"
}


def analisar_emocao(texto):
    response = requests.post(
        EMOTION_URL,
        headers=HEADERS,
        json={"inputs": texto}
    )

    if response.status_code != 200:
        print("Erro HF:", response.text)
        return None

    resultado = response.json()[0]

    emocao = max(resultado, key=lambda x: x["score"])

    return {
        "label": emocao["label"],
        "score": emocao["score"]
    }


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