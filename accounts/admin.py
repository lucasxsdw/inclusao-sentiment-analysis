from django.contrib import admin
from .models import Usuario, Aluno, Educador
from django.contrib.auth.admin import UserAdmin


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'tipo_usuario', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Adicionais', {'fields': ('tipo_usuario',)}),
    )   

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'data_nascimento', 'tipo_deficiencia')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')

@admin.register(Educador)
class EducadorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'area_atuacao')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name')  
