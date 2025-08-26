from django.urls import path
from . import views

app_name = 'CPlogin'

urlpatterns = [
    # Autenticación
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    
    # Perfil
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # APIs
    path('api/check-password-strength/', views.check_password_strength, name='check_password_strength'),
]
