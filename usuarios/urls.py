# usuarios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # O name='login' é usado em LOGIN_URL e redirects
    path('login/', views.user_login, name='login'),
    # O name='logout' é usado no link de sair
    path('logout/', views.user_logout, name='logout'),
    # URL para editar perfil
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]
