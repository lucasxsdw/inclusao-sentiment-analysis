from django.contrib import messages
from django.views.generic import TemplateView
from django.views.generic.edit import FormView   
from django.contrib.auth.views import LoginView
from .forms import RegisterUserForm, AlunoForm, EducadorForm
from django.urls import reverse_lazy


class Login(LoginView):
    template_name = "accounts/login.html"


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
        usuario = form.save(commit=False)
        usuario.username = form.cleaned_data.get('email')
        usuario.tipo_usuario = 'educador' 
        usuario.save()
      
        messages.success(self.request, 'Cadastro realizado com sucesso! Faça seu login.')
        
        educador_form = EducadorForm(self.request.POST)
        if educador_form.is_valid():
            educador = educador_form.save(commit=False)
            educador.usuario = usuario
            educador.save()
           
    
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['educador_form'] = EducadorForm()
        return context
