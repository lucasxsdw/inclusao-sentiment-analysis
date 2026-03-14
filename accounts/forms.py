from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario, Aluno

#cada form corresponde a um modelo, nesse caso o modelo Usuario, e os campos que queremos usar para criar um novo usuário. 
# O UserCreationForm já tem os campos de senha e confirmação de senha, então não precisamos adicioná-los manualmente.
class RegisterUserForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ("username", "email", "password1", "password2")


class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ("tipo_deficiencia", "necessidades_especificas")
    