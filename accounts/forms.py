from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Usuario, Aluno, Educador

#cada form corresponde a um modelo, nesse caso o modelo Usuario, e os campos que queremos usar para criar um novo usuário. 
# O UserCreationForm já tem os campos de senha e confirmação de senha, então não precisamos adicioná-los manualmente.
class RegisterUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(
    required=True,
    label="Nome completo",
    max_length=150
)

    class Meta:
        model = Usuario
        fields = ("first_name", "email", "password1", "password2")


class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ("tipo_deficiencia", "necessidades_especificas")
    
class EducadorForm(forms.ModelForm):
    class Meta:
        model = Educador
        fields = ("area_atuacao",)
            