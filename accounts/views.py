
from django.views.generic.edit import FormView   
from django.contrib.auth.views import LoginView
from .forms import RegisterUserForm, AlunoForm
from django.urls import reverse_lazy


# Create your views here.
class Login(LoginView):
    template_name = "accounts/login.html"


class RegisterUser(FormView):
        template_name = "accounts/register.html"
        form_class = RegisterUserForm 
        success_url = reverse_lazy('login')

        def form_valid(self, form):
                # 1. salva o RegisterUserForm → cria o Usuario
                usuario = form.save()
                
                # 2. pega os dados do AlunoForm do POST
                aluno_form = AlunoForm(self.request.POST)

                # 3. valida o AlunoForm
                if aluno_form.is_valid():
                        # 4. salva o Aluno mas não commita ainda
                        # porque precisa vincular ao usuario primeiro
                        aluno = aluno_form.save(commit=False)
                        aluno.usuario = usuario
                        aluno.save()
                        
                return super().form_valid(form)
        
        # passa o AlunoForm vazio para o template
        def get_context_data(self, **kwargs):
               context = super().get_context_data(**kwargs)
               context['aluno_form'] = AlunoForm()
               return context        