from django.db import models
from diario.models import Resposta
from diario.models import SessaoEmocional


class AnaliseResposta(models.Model):
    resposta = models.OneToOneField(Resposta, on_delete=models.CASCADE)
    sentimento_detectado = models.CharField(max_length=50, null=True, blank=True)
    score_sentimento = models.FloatField(null=True, blank=True)
    modelo_ia = models.CharField(max_length=100, null=True, blank=True)
    data_analise = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Análise da Resposta {self.resposta.id}"



class AnaliseSessao(models.Model):
    sessao_emocional = models.OneToOneField(
        SessaoEmocional,
        on_delete=models.CASCADE
    )
    emocao_predominante = models.CharField(max_length=50, null=True, blank=True)
    score_medio = models.FloatField(null=True, blank=True)
    variacao_emocional = models.CharField(max_length=50, null=True, blank=True)
    observacoes_ia = models.TextField(null=True, blank=True)
    data_analise = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Análise da Sessão {self.sessao_emocional.id}"
