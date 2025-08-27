from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from core.models import Company, User, AuthLoginAudit, UserRole
import json


def redirect_user_by_role(user):
    """
    Redirigir al usuario según su rol
    """
    # Obtener el rol principal del usuario
    try:
        user_role = user.userrole_set.first()
        if user_role:
            role_key = user_role.role.key
        else:
            # Si no tiene rol asignado, verificar si es superuser
            role_key = 'admin' if user.is_superuser else 'user'
    except:
        role_key = 'user'
    
    # Redirigir según el rol
    if role_key == 'admin':
        return redirect('CPdashadmin:dashboard')
    elif role_key == 'technician':
        return redirect('CPdashtechnician:dashboard')
    else:
        # Para cualquier otro rol (user, etc.)
        return redirect('CPdashother:dashboard')


def login_view(request):
    """
    Vista de login personalizada
    """
    # Si ya está autenticado, redirigir según su rol
    if request.user.is_authenticated:
        return redirect_user_by_role(request.user)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            # Intentar autenticar
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Verificar si el usuario puede acceder al sistema
                if hasattr(user, 'can_access') and not user.can_access:
                    messages.error(request, "Su cuenta no tiene acceso al sistema. Contacte al administrador.")
                    # Registrar intento fallido
                    AuthLoginAudit.objects.create(
                        user=user,
                        success=False,
                        ip=request.META.get('REMOTE_ADDR', ''),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        note="Usuario sin acceso al sistema"
                    )
                    return render(request, 'CPlogin/login.html')
                
                # Login exitoso
                login(request, user)
                
                # Registrar login exitoso
                AuthLoginAudit.objects.create(
                    user=user,
                    success=True,
                    ip=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # Verificar si debe cambiar contraseña
                if hasattr(user, 'must_change_password') and user.must_change_password:
                    messages.warning(request, "Debe cambiar su contraseña antes de continuar.")
                    return redirect('CPlogin:change_password')
                
                # Redirigir según el rol
                messages.success(request, f"Bienvenido, {user.get_full_name() or user.username}!")
                return redirect_user_by_role(user)
            else:
                # Login fallido
                messages.error(request, "Usuario o contraseña incorrectos.")
                
                # Intentar encontrar el usuario para registrar el intento fallido
                try:
                    user = User.objects.get(username=username)
                    AuthLoginAudit.objects.create(
                        user=user,
                        success=False,
                        ip=request.META.get('REMOTE_ADDR', ''),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        note="Contraseña incorrecta"
                    )
                except User.DoesNotExist:
                    # Usuario no existe
                    AuthLoginAudit.objects.create(
                        user=None,
                        success=False,
                        ip=request.META.get('REMOTE_ADDR', ''),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        note=f"Usuario '{username}' no existe"
                    )
        else:
            messages.error(request, "Por favor complete todos los campos.")
    
    return render(request, 'CPlogin/login.html')


@login_required
def logout_view(request):
    """
    Vista de logout
    """
    logout(request)
    messages.success(request, "Ha cerrado sesión exitosamente.")
    return redirect('CPlogin:login')


@login_required
def change_password(request):
    """
    Cambio de contraseña obligatorio
    """
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Preparar contexto para errores
        context = {
            'user': request.user,
            'company': request.user.company if hasattr(request.user, 'company') else None,
        }
        
        # Verificar que todos los campos estén completos
        if not current_password or not new_password or not confirm_password:
            messages.error(request, "Por favor complete todos los campos.")
            return render(request, 'CPlogin/change_password.html', context)
        
        # Verificar contraseña actual
        if not request.user.check_password(current_password):
            messages.error(request, "La contraseña actual es incorrecta.")
            return render(request, 'CPlogin/change_password.html', context)
        
        # Verificar que las nuevas contraseñas coincidan
        if new_password != confirm_password:
            messages.error(request, "Las nuevas contraseñas no coinciden.")
            return render(request, 'CPlogin/change_password.html', context)
        
        # Verificar fortaleza de la contraseña
        if len(new_password) < 8:
            messages.error(request, "La nueva contraseña debe tener al menos 8 caracteres.")
            return render(request, 'CPlogin/change_password.html', context)
        
        # Cambiar contraseña
        request.user.set_password(new_password)
        request.user.must_change_password = False
        request.user.save()
        
        # Re-autenticar al usuario
        user = authenticate(request, username=request.user.username, password=new_password)
        if user:
            login(request, user)
        
        messages.success(request, "Contraseña cambiada exitosamente.")
        return redirect_user_by_role(user)
    
    # Pasar información del usuario al contexto
    context = {
        'user': request.user,
        'company': request.user.company if hasattr(request.user, 'company') else None,
    }
    return render(request, 'CPlogin/change_password.html', context)


@login_required
def profile(request):
    """
    Perfil del usuario
    """
    if request.method == 'POST':
        user = request.user
        
        # Actualizar información básica
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.title = request.POST.get('title', user.title)
        user.department = request.POST.get('department', user.department)
        user.location = request.POST.get('location', user.location)
        
        user.save()
        
        messages.success(request, "Perfil actualizado exitosamente.")
        return redirect('CPlogin:profile')
    
    return render(request, 'CPlogin/profile.html')


@csrf_exempt
def check_password_strength(request):
    """
    API para verificar fortaleza de contraseña
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            password = data.get('password', '')
            
            strength = 0
            feedback = []
            
            if len(password) >= 8:
                strength += 1
            else:
                feedback.append("Al menos 8 caracteres")
            
            if any(c.islower() for c in password):
                strength += 1
            else:
                feedback.append("Al menos una letra minúscula")
            
            if any(c.isupper() for c in password):
                strength += 1
            else:
                feedback.append("Al menos una letra mayúscula")
            
            if any(c.isdigit() for c in password):
                strength += 1
            else:
                feedback.append("Al menos un número")
            
            if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
                strength += 1
            else:
                feedback.append("Al menos un carácter especial")
            
            if strength < 3:
                level = "débil"
                color = "danger"
            elif strength < 5:
                level = "media"
                color = "warning"
            else:
                level = "fuerte"
                color = "success"
            
            return JsonResponse({
                'strength': strength,
                'level': level,
                'color': color,
                'feedback': feedback,
                'max_strength': 5
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Datos JSON inválidos'
            }, status=400)
    
    return JsonResponse({
        'error': 'Método no permitido'
    }, status=405)


def forgot_password(request):
    """
    Vista para recuperar contraseña (placeholder)
    """
    messages.info(request, "Funcionalidad de recuperación de contraseña en desarrollo.")
    return redirect('CPlogin:login')
