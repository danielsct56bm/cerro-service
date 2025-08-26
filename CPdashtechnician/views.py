from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from core.models import User, Ticket, Company


def is_technician(user):
    """
    Verificar si el usuario es técnico
    """
    try:
        user_role = user.userrole_set.first()
        return user.is_authenticated and user_role and user_role.role.key == 'technician'
    except:
        return False


@login_required
def dashboard(request):
    """
    Dashboard principal del técnico
    """
    # Verificar que sea técnico
    if not is_technician(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('CPlogin:login')
    
    user = request.user
    company = user.company
    
    # Obtener tickets asignados al técnico
    assigned_tickets = Ticket.objects.filter(assigned_to=user).order_by('-created_at')[:10]
    
    # Estadísticas del técnico
    total_assigned = Ticket.objects.filter(assigned_to=user).count()
    active_tickets = Ticket.objects.filter(assigned_to=user, status__in=['open', 'in_progress']).count()
    completed_tickets = Ticket.objects.filter(assigned_to=user, status='closed').count()
    
    context = {
        'user': user,
        'company': company,
        'assigned_tickets': assigned_tickets,
        'total_assigned': total_assigned,
        'active_tickets': active_tickets,
        'completed_tickets': completed_tickets,
        'current_time': timezone.now(),
    }
    
    return render(request, 'CPdashtechnician/dashboard.html', context)


@login_required
def my_tickets(request):
    """
    Lista de tickets asignados al técnico
    """
    if not is_technician(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('CPlogin:login')
    
    tickets = Ticket.objects.filter(assigned_to=request.user).order_by('-created_at')
    
    context = {
        'tickets': tickets,
        'user': request.user,
    }
    
    return render(request, 'CPdashtechnician/my_tickets.html', context)


@login_required
def profile(request):
    """
    Perfil del técnico
    """
    if not is_technician(request.user):
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
        return redirect('CPdashtechnician:profile')
    
    return render(request, 'CPdashtechnician/profile.html')
