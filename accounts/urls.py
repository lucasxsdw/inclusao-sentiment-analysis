from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import Login, RegisterUser, RegisterServ, TipoUser

app_name = 'accounts'
urlpatterns = [
    path('login/', Login.as_view(), name='login'),
    path('register/', RegisterUser.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('tipoUser/', TipoUser.as_view(), name="tipoUser"),
    path('registerServ/', RegisterServ.as_view(), name="registerServ")
]
