from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    
    TIPO_USUARIO_CHOICES = (
        ('aluno', 'Aluno'),
        ('educador', 'Educador'),
    )

    email = models.EmailField(unique=True) 
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default='aluno'
    )

    def __str__(self):
        return self.username


class Aluno(models.Model):
    TIPO_DEFICIENCIA_CHOICES = [
        ('tea', 'Transtorno do Espectro Autista (TEA)'),
        ('baixa_visao', 'Baixa Visão'),
        ('cegueira', 'Cegueira'),
        ('surdez', 'Surdez'),
        ('surdocegueira', 'Surdocegueira'),
        ('deficiencia_fisica', 'Deficiência Física'),
        ('deficiencia_intelectual', 'Deficiência Intelectual'),
        ('tdah', 'TDAH'),
        ('dislexia', 'Dislexia'),
        ('outro', 'Outro'),
    ]

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil_aluno'
    )
    data_nascimento = models.DateField(null=True, blank=True)
    tipo_deficiencia = models.CharField(max_length=100,  choices=TIPO_DEFICIENCIA_CHOICES,)
    necessidades_especificas = models.TextField(
        null=True,
        blank=True,
        help_text="Descreva as necessidades específicas do aluno para personalizar o atendimento da IA"
    )

    def __str__(self):
        return f"Aluno: {self.usuario.get_full_name()}"


class Educador(models.Model):
    AREA_ATUACAO_CHOICES = [
        ('pedagogia', 'Pedagogia'),
        ('psicologia', 'Psicologia'),
        ('fisioterapia', 'Fisioterapia'),
        ('fonoaudiologia', 'Fonoaudiologia'),
        ('terapia_ocupacional', 'Terapia Ocupacional'),
        ('assistente_social', 'Assistente Social'),
        ('outro', 'Outro'),
    ]
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil_educador'
    )
    area_atuacao = models.CharField(max_length=100, choices=AREA_ATUACAO_CHOICES)

    def __str__(self):
        return f"Educador: {self.usuario.get_full_name()}"