from django.db import models
from accounts.models import Aluno


class SessaoEmocional(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    emocao_selecionada = models.CharField(max_length=50)
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    status_sessao = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.emocao_selecionada} - {self.aluno.usuario.nome}"


class Diario(models.Model):
    sessao_emocional = models.OneToOneField(
        SessaoEmocional,
        on_delete=models.CASCADE
    )
    mensagem_inicial_ia = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_encerramento = models.DateTimeField(null=True, blank=True)


class Pergunta(models.Model):
    emocao_relacionada = models.CharField(max_length=50)
    texto_pergunta = models.TextField()
    ordem = models.IntegerField()
    ativa = models.BooleanField(default=True)


class Resposta(models.Model):
    diario = models.ForeignKey(Diario, on_delete=models.CASCADE)
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    texto_resposta = models.TextField()
    data_resposta = models.DateTimeField(auto_now_add=True)
    sentimento_detectado = models.CharField(max_length=50, null=True, blank=True)
    score_sentimento = models.FloatField(null=True, blank=True)
