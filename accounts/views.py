from django.contrib import messages
from django.views.generic import TemplateView
from django.views.generic.edit import FormView   
from django.contrib.auth.views import LoginView

from config import settings
from .forms import RegisterUserForm, AlunoForm, EducadorForm
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView


from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

# --- 1. Regras de quem é quem ---
def is_aluno(user):
    return user.is_authenticated and user.tipo_usuario == 'aluno'

def is_educador(user):
    return user.is_authenticated and user.tipo_usuario == 'educador'

# --- 2. Os Decorators (Os "Seguranças") ---
# Se não for aluno, bloqueia.
aluno_required = user_passes_test(is_aluno, login_url='/login/', redirect_field_name=None)

# Se não for educador, bloqueia.
educador_required = user_passes_test(is_educador, login_url='/login/', redirect_field_name=None)



class Login(LoginView):
    template_name = "accounts/login.html"

    def get_success_url(self):
        user = self.request.user
        if user.tipo_usuario == 'educador':
            return '/analise/painel/'
        return '/diario/home/'


class TipoUser(TemplateView):
    template_name = "accounts/tipoUser.html"

class RegisterUser(FormView):
    template_name = "accounts/register.html"
    form_class = RegisterUserForm 
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        usuario = form.save(commit=False)
        usuario.username = form.cleaned_data.get('email')
        usuario.save()
        
        messages.success(self.request, 'Cadastro realizado com sucesso! Faça seu login.')

        aluno_form = AlunoForm(self.request.POST)
        if aluno_form.is_valid():
            aluno = aluno_form.save(commit=False)
            aluno.usuario = usuario
            aluno.save()
            
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['aluno_form'] = AlunoForm()
        return context
    

class RegisterServ(FormView):
    template_name = "accounts/registerServ.html"
    form_class = RegisterUserForm
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        # 1. PEGA O CÓDIGO E FAZ A VERIFICAÇÃO AQUI
        codigo_digitado = self.request.POST.get('codigo_acesso')
        CHAVE_SECRETA = settings.CHAVE_ACESSO_NAPNE

        if codigo_digitado != CHAVE_SECRETA:
            # Mostra o erro na tela e interrompe o salvamento
            messages.error(self.request, "Código de autorização inválido! Verifique a chave com a instituição.")
            return self.form_invalid(form) # Retorna para a página sem salvar nada

        # =======================================================
        # 2. SE O CÓDIGO ESTIVER CERTO, CONTINUA O SALVAMENTO
        # =======================================================
        usuario = form.save(commit=False)
        usuario.username = form.cleaned_data.get('email')
        usuario.tipo_usuario = 'educador' 
        usuario.save()
      
        educador_form = EducadorForm(self.request.POST)
        if educador_form.is_valid():
            educador = educador_form.save(commit=False)
            educador.usuario = usuario
            educador.save()
            
        # Movi a mensagem de sucesso para cá, para garantir que só 
        # apareça se tudo (inclusive o educador) for salvo.
        messages.success(self.request, 'Cadastro de Servidor realizado com sucesso! Faça seu login.')
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['educador_form'] = EducadorForm()
        return context
