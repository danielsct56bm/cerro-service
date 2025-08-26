from django.urls import path
from . import views

app_name = 'CPdashtechnician'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),
    
    # Gestión de tickets
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    
    # Perfil
    path('profile/', views.profile, name='profile'),
]
