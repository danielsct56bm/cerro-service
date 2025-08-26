from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from core.models import User, Ticket, Company


def is_other_role(user):
    """
    Verificar si el usuario tiene un rol diferente a admin o technician
    """
    try:
        user_role = user.userrole_set.first()
        if user_role:
            role_key = user_role.role.key
            return user.is_authenticated and role_key not in ['admin', 'technician']
        else:
            return user.is_authenticated and not user.is_superuser
    except:
        return user.is_authenticated and not user.is_superuser


@login_required
def dashboard(request):
    """
    Dashboard principal para otros roles
    """
    # Verificar que no sea admin ni technician
    if not is_other_role(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('CPlogin:login')
    
    user = request.user
    company = user.company
    
    # Obtener tickets creados por el usuario
    my_tickets = Ticket.objects.filter(requester=user).order_by('-created_at')[:10]
    
    # Estadísticas del usuario
    total_created = Ticket.objects.filter(requester=user).count()
    active_tickets = Ticket.objects.filter(requester=user, status__in=['open', 'in_progress']).count()
    closed_tickets = Ticket.objects.filter(requester=user, status='closed').count()
    
    context = {
        'user': user,
        'company': company,
        'my_tickets': my_tickets,
        'total_created': total_created,
        'active_tickets': active_tickets,
        'closed_tickets': closed_tickets,
        'current_time': timezone.now(),
    }
    
    return render(request, 'CPdashother/dashboard.html', context)


@login_required
def my_tickets(request):
    """
    Lista de tickets creados por el usuario
    """
    if not is_other_role(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('CPlogin:login')
    
    tickets = Ticket.objects.filter(requester=request.user).order_by('-created_at')
    
    context = {
        'tickets': tickets,
        'user': request.user,
    }
    
    return render(request, 'CPdashother/my_tickets.html', context)


@login_required
def create_ticket(request):
    """
    Crear nuevo ticket
    """
    if not is_other_role(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('CPlogin:login')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 'medium')
        
        if title and description:
            ticket = Ticket.objects.create(
                title=title,
                description=description,
                priority=priority,
                requester=request.user,
                company=request.user.company,
                status='open'
            )
            
            messages.success(request, "Ticket creado exitosamente.")
            return redirect('CPdashother:my_tickets')
        else:
            messages.error(request, "Por favor complete todos los campos requeridos.")
    
    return render(request, 'CPdashother/create_ticket.html')


@login_required
def profile(request):
    """
    Perfil del usuario
    """
    if not is_other_role(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('CPlogin:login')
    
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
        return redirect('CPdashother:profile')
    
    return render(request, 'CPdashother/profile.html')
