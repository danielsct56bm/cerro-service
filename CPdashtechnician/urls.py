from django.urls import path
from . import views

app_name = 'CPdashtechnician'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),
    
    # Gestión de tickets
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('ticket/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    
    # Perfil
    path('profile/', views.profile, name='profile'),
    
    # Reportes
    path('reports/', views.reports, name='reports'),
]
