"""
Middleware para controlar el acceso al sistema según el setup inicial
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from .models import SystemSetup

class SystemSetupMiddleware(MiddlewareMixin):
    """
    Middleware que verifica si el sistema está configurado
    """
    
    def process_request(self, request):
        # URLs que siempre están permitidas
        allowed_urls = [
            '/admin/',
            '/admin/login/',
            '/setup/',
            '/api/schema/',
            '/api/docs/',
        ]
        
        # Verificar si la URL actual está permitida
        current_path = request.path
        is_allowed = any(current_path.startswith(url) for url in allowed_urls)
        
        if is_allowed:
            return None
        
        # Verificar si el sistema está configurado
        try:
            setup = SystemSetup.objects.first()
            if not setup or not setup.is_completed:
                # Sistema no configurado, redirigir al setup
                if not current_path.startswith('/setup/'):
                    messages.warning(
                        request, 
                        'El sistema no está configurado. Complete la configuración inicial.'
                    )
                    return redirect('CPsetup:setup_check')
        except Exception:
            # Error al verificar setup, permitir acceso al admin
            if not current_path.startswith('/admin/'):
                return redirect('admin:login')
        
        return None

class CompanyAccessMiddleware(MiddlewareMixin):
    """
    Middleware para controlar acceso multi-tenant
    """
    
    def process_request(self, request):
        # URLs que siempre están permitidas (admin de Django)
        admin_urls = [
            '/admin/',
            '/admin/login/',
            '/admin/password_change/',
            '/admin/logout/',
        ]
        
        # Si es una URL del admin de Django, no aplicar restricciones
        current_path = request.path
        is_admin_url = any(current_path.startswith(url) for url in admin_urls)
        
        if is_admin_url:
            return None
        
        if not request.user.is_authenticated:
            return None
        
        # Verificar si el usuario puede acceder al sistema
        if hasattr(request.user, 'can_access') and not request.user.can_access:
            messages.error(
                request, 
                'Su cuenta no tiene acceso al sistema. Contacte al administrador.'
            )
            return redirect('CPlogin:logout')
        
        # Verificar si debe cambiar contraseña
        if hasattr(request.user, 'must_change_password') and request.user.must_change_password:
            current_path = request.path
            if not current_path.startswith('/login/change-password/'):
                messages.warning(
                    request, 
                    'Debe cambiar su contraseña antes de continuar.'
                )
                return redirect('CPlogin:change_password')
        
        return None
