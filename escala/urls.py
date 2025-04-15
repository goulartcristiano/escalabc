# escala/urls.py
from django.urls import path
from . import views

app_name = 'escala' # Namespace para as URLs (útil em templates: {% url 'escala:nome_da_url' %})

urlpatterns = [
    # URL principal para gerenciar a escala
    path('', views.gerenciar_escala, name='gerenciar_escala'),
    path('excluir/<int:pk>/', views.excluir_escala, name='excluir_escala'),
]
