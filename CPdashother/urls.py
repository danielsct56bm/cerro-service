from django.urls import path
from . import views

app_name = 'CPdashother'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),
    
    # Gestión de tickets
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('create-ticket/', views.create_ticket, name='create_ticket'),
    
    # Perfil
    path('profile/', views.profile, name='profile'),
]
