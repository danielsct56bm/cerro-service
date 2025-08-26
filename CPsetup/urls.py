from django.urls import path
from . import views

app_name = 'CPsetup'

urlpatterns = [
    # Verificación inicial del setup
    path('check/', views.setup_check, name='setup_check'),
    
    # Flujo de setup
    path('company/', views.setup_company, name='setup_company'),
    path('admin/', views.setup_admin, name='setup_admin'),
    
    # APIs auxiliares
    path('api/generate-avatar/', views.generate_avatar_preview, name='generate_avatar_preview'),
    path('api/progress/', views.setup_progress, name='setup_progress'),
]
