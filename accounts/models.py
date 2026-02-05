from django.db import models


class Usuario(models.Model):
    TIPO_USUARIO_CHOICES = (
        ('aluno', 'Aluno'),
        ('educador', 'Educador'),
    )

    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=128)
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


class Aluno(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True
    )
    data_nascimento = models.DateField()
    tipo_deficiencia = models.CharField(max_length=50)

    def __str__(self):
        return f"Aluno: {self.usuario.nome}"


class Educador(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True
    )
    area_atuacao = models.CharField(max_length=50)

    def __str__(self):
        return f"Educador: {self.usuario.nome}"
