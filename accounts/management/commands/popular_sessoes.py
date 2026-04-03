import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import Aluno
from diario.models import Diario, SessaoEmocional

class Command(BaseCommand):
    help = 'Popula o banco com sessões emocionais fictícias para testar o Dashboard'

    def handle(self, *args, **kwargs):
        alunos = Aluno.objects.all()
        if not alunos.exists():
            self.stdout.write(self.style.ERROR('Nenhum aluno encontrado. Rode o popular_alunos primeiro.'))
            return

        # Mistura de emoções comuns e emoções de atenção para testar os filtros
        emocoes = ['muito_feliz', 'feliz', 'neutro', 'triste', 'ansioso', 'irritado', 'medo', 'alegria']
        
        self.stdout.write('Gerando histórico emocional no tempo...')

        for aluno in alunos:
            # Sorteia para que alguns alunos tenham mais registros que outros (de 0 a 4)
            qtd_sessoes = random.randint(0, 4)
            
            for _ in range(qtd_sessoes):
                # Sorteia uma data nos últimos 15 dias
                dias_atras = random.randint(0, 15)
                data_simulada = timezone.now() - timedelta(days=dias_atras)
                
                # 1. Cria a sessão PRIMEIRO (o diário depende dela)
                sessao = SessaoEmocional.objects.create(
                    aluno=aluno,
                    emocao_selecionada=random.choice(emocoes)
                )
                
                # 2. Cria o Diário vinculando a sessão que acabou de nascer
                diario = Diario.objects.create(
                    sessao_emocional=sessao
                )
                
                # 3. Truque para burlar o auto_now_add e forçar uma data antiga
                SessaoEmocional.objects.filter(id=sessao.id).update(data_inicio=data_simulada)
        self.stdout.write(self.style.SUCCESS('✅ Sucesso! O histórico emocional foi gerado.'))