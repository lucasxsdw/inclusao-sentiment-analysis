from django.db import models
from accounts.models import Aluno


class StatusSessao(models.TextChoices):
    ATIVA = 'ativa', 'Ativa'
    ENCERRADA = 'encerrada', 'Encerrada'
    EXPIRADA = 'expirada', 'Expirada'



class SessaoEmocional(models.Model):
    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        null=True,
        blank=True, db_index=True
    )
    emocao_selecionada = models.CharField(max_length=50, db_index=True)
    data_inicio = models.DateTimeField(auto_now_add=True, db_index=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    status_sessao = models.CharField(max_length=20, choices=StatusSessao.choices, default=StatusSessao.ATIVA)

    def __str__(self):
        return self.emocao_selecionada


class Diario(models.Model):
    sessao_emocional = models.OneToOneField(
        SessaoEmocional,
        on_delete=models.CASCADE
    )
    mensagem_inicial_ia = models.TextField(null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_encerramento = models.DateTimeField(null=True, blank=True)
    total_mensagens = models.IntegerField(default=0)

    def __str__(self):
        return f"Diário da sessão {self.sessao_emocional.id}"


class Pergunta(models.Model):
    emocao_relacionada = models.CharField(max_length=50)
    texto_pergunta = models.TextField()
    ordem = models.IntegerField()
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return self.texto_pergunta


class Resposta(models.Model):
    diario = models.ForeignKey(Diario, on_delete=models.CASCADE)
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    texto_resposta = models.TextField()
    data_resposta = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resposta {self.id}"
