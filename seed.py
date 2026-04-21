import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from diario.models import Pergunta

def popular_perguntas():
    perguntas = [
        {'emocao': 'feliz', 'texto': 'Que notícia boa! O que aconteceu de especial hoje?'},
        {'emocao': 'triste', 'texto': 'Sinto muito. Gostaria de me contar o que te deixou assim?'},
        {'emocao': 'muito_triste', 'texto': 'Percebo que hoje está sendo um dia difícil. Quer desabafar?'},
        {'emocao': 'raiva', 'texto': 'Entendo sua frustração. O que causou esse sentimento?'},
        {'emocao': 'neutro', 'texto': 'Como foi sua rotina hoje na escola?'},
    ]

    for p in perguntas:
        Pergunta.objects.get_or_create(
            emocao_relacionada=p['emocao'],
            texto_pergunta=p['texto'],
            defaults={'ordem': 1, 'ativa': True}
        )
    print("✅ Perguntas cadastradas com sucesso!")

if __name__ == "__main__":
    popular_perguntas()