import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Aluno
from faker import Faker

# Pega o seu modelo de usuário configurado
Usuario = get_user_model()

class Command(BaseCommand):
    help = 'Popula o banco de dados com alunos de teste para o TCC'

    def add_arguments(self, parser):
        # Permite escolher quantos alunos criar rodando: python manage.py popular_alunos 15
        parser.add_argument('quantidade', type=int, help='Número de alunos a serem criados')

    def handle(self, *args, **kwargs):
        quantidade = kwargs['quantidade']
        fake = Faker('pt_BR') # Gera dados no padrão brasileiro!

        # Lista de deficiências baseada nos choices do seu modelo (adapte se necessário)
        tipos_deficiencia = ['visual', 'auditiva', 'intelectual', 'fisica', 'multipla', 'tea']

        self.stdout.write('Iniciando a criação de alunos...')

        for _ in range(quantidade):
            nome = fake.first_name()
            sobrenome = fake.last_name()
            
            # Cria um e-mail limpo sem acentos
            email_falso = f"{nome.lower()}.{sobrenome.lower()}@teste.edu.br"

            try:
                # 1. Cria o Usuário Base (Aquele esquema de "pausar e carimbar")
                usuario = Usuario(
                    first_name=nome,
                    last_name=sobrenome,
                    email=email_falso,
                    username=email_falso # Usa o email como username conforme sua view de cadastro
                )
                usuario.set_password('SenhaSegura123!') # Define uma senha padrão para todos
                usuario.tipo_usuario = 'aluno' # O carimbo de segurança!
                usuario.save()

                # 2. Cria o Perfil do Aluno vinculado ao usuário
                Aluno.objects.create(
                    usuario=usuario,
                    tipo_deficiencia=random.choice(tipos_deficiencia),
                    necessidades_especificas=fake.text(max_nb_chars=80)
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erro ao criar {nome}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'✅ Sucesso! {quantidade} alunos fictícios criados com perfeição.'))