from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

def home_view(request):
    """
    Vista principal que redirige según el estado de autenticación
    """
    if request.user.is_authenticated:
        # Si está autenticado, redirigir según su rol
        from CPlogin.views import redirect_user_by_role
        return redirect_user_by_role(request.user)
    else:
        # Si no está autenticado, redirigir al login
        return redirect('CPlogin:login')
