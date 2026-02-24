from django.contrib import admin
from .models import Diario, Pergunta, SessaoEmocional, Resposta

admin.site.register(Diario)
admin.site.register(SessaoEmocional)
admin.site.register(Pergunta)
admin.site.register(Resposta)
