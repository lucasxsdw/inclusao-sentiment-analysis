from diario.models import Resposta
from analise.models import AnaliseResposta
from diario.services.ia_service import analisar_sentimento


def analisar_resposta(resposta_obj):
    resultado = analisar_sentimento(resposta_obj.texto)

    AnaliseResposta.objects.create(
        resposta=resposta_obj,
        sentimento_detectado=resultado["label"],
        score_sentimento=resultado["score"],
        modelo_ia="cardiffnlp/twitter-roberta-base-sentiment-latest"
    )
