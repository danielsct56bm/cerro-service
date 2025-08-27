from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator
from core.models import User, Ticket, Company, TicketCategory, TicketSubcategory


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
    Dashboard principal del técnico con datos reales
    """
    # Verificar que sea técnico
    if not is_technician(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('CPlogin:login')
    
    user = request.user
    company = user.company
    
    # Obtener tickets asignados al técnico
    assigned_tickets = Ticket.objects.filter(assigned_to=user).order_by('-created_at')[:5]
    
    # Estadísticas reales del técnico
    total_assigned = Ticket.objects.filter(assigned_to=user).count()
    active_tickets = Ticket.objects.filter(assigned_to=user, status__in=['open', 'in_progress']).count()
    completed_tickets = Ticket.objects.filter(assigned_to=user, status='closed').count()
    
    # Calcular tasa de satisfacción (si hay tickets completados)
    satisfaction_rate = 0
    if completed_tickets > 0:
        # Aquí podrías calcular basado en ratings reales si los tienes
        satisfaction_rate = 95  # Placeholder - implementar lógica real
    
    # Tickets por estado
    tickets_by_status = Ticket.objects.filter(assigned_to=user).values('status').annotate(
        count=Count('id')
    )
    
    # Tickets recientes para la tabla
    recent_tickets = Ticket.objects.filter(assigned_to=user).order_by('-created_at')[:3]
    
    context = {
        'user': user,
        'company': company,
        'assigned_tickets': assigned_tickets,
        'total_assigned': total_assigned,
        'active_tickets': active_tickets,
        'completed_tickets': completed_tickets,
        'satisfaction_rate': satisfaction_rate,
        'tickets_by_status': tickets_by_status,
        'recent_tickets': recent_tickets,
        'current_time': timezone.now(),
    }
    
    return render(request, 'CPdashtechnician/dashboard.html', context)


@login_required
def my_tickets(request):
    """
    Lista de tickets asignados al técnico con filtros reales
    """
    if not is_technician(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('CPlogin:login')
    
    # Obtener parámetros de filtro
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('search', '')
    
    # Query base
    tickets = Ticket.objects.filter(assigned_to=request.user)
    
    # Aplicar filtros
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    
    if category_filter:
        tickets = tickets.filter(category__id=category_filter)
    
    if search_query:
        tickets = tickets.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Ordenar por fecha de creación (más recientes primero)
    tickets = tickets.order_by('-created_at')
    
    # Paginación
    paginator = Paginator(tickets, 10)  # 10 tickets por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener categorías para el filtro
    categories = TicketCategory.objects.all()
    
    context = {
        'tickets': page_obj,
        'user': request.user,
        'categories': categories,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
        'search_query': search_query,
        'total_tickets': tickets.count(),
    }
    
    return render(request, 'CPdashtechnician/my_tickets.html', context)


@login_required
def profile(request):
    """
    Perfil del técnico con funcionalidad real
    """
    if not is_technician(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('CPlogin:login')
    
    user = request.user
    
    if request.method == 'POST':
        # Actualizar información básica
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.employee_number = request.POST.get('employee_number', user.employee_number)
        user.sap_id = request.POST.get('sap_id', user.sap_id)
        user.phone = request.POST.get('phone', user.phone)
        user.department = request.POST.get('department', user.department)
        user.bio = request.POST.get('bio', user.bio)
        
        # Manejar avatar si se subió
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        
        try:
            user.save()
            messages.success(request, "Perfil actualizado exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al actualizar perfil: {str(e)}")
        
        return redirect('CPdashtechnician:profile')
    
    # Obtener estadísticas reales para el perfil
    total_tickets = Ticket.objects.filter(assigned_to=user).count()
    completed_tickets = Ticket.objects.filter(assigned_to=user, status='closed').count()
    satisfaction_rate = 95 if completed_tickets > 0 else 0  # Placeholder
    
    context = {
        'user': user,
        'total_tickets': total_tickets,
        'completed_tickets': completed_tickets,
        'satisfaction_rate': satisfaction_rate,
    }
    
    return render(request, 'CPdashtechnician/profile.html', context)


@login_required
def ticket_detail(request, ticket_id):
    """
    Detalle de un ticket específico
    """
    if not is_technician(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('CPlogin:login')
    
    ticket = get_object_or_404(Ticket, id=ticket_id, assigned_to=request.user)
    
    if request.method == 'POST':
        # Actualizar estado del ticket
        new_status = request.POST.get('status')
        if new_status in ['open', 'in_progress', 'closed']:
            ticket.status = new_status
            ticket.save()
            messages.success(request, f"Ticket #{ticket.id} actualizado a {new_status}")
            return redirect('CPdashtechnician:ticket_detail', ticket_id=ticket.id)
    
    context = {
        'ticket': ticket,
        'user': request.user,
    }
    
    return render(request, 'CPdashtechnician/ticket_detail.html', context)


@login_required
def reports(request):
    """
    Reportes del técnico
    """
    if not is_technician(request.user):
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect('CPlogin:login')
    
    user = request.user
    
    # Estadísticas por mes
    from datetime import datetime, timedelta
    now = timezone.now()
    last_month = now - timedelta(days=30)
    
    monthly_stats = Ticket.objects.filter(
        assigned_to=user,
        created_at__gte=last_month
    ).values('status').annotate(count=Count('id'))
    
    # Tickets por categoría
    category_stats = Ticket.objects.filter(
        assigned_to=user
    ).values('category__name').annotate(count=Count('id'))
    
    # Tickets por prioridad
    priority_stats = Ticket.objects.filter(
        assigned_to=user
    ).values('priority').annotate(count=Count('id'))
    
    context = {
        'user': user,
        'monthly_stats': monthly_stats,
        'category_stats': category_stats,
        'priority_stats': priority_stats,
    }
    
    return render(request, 'CPdashtechnician/reports.html', context)
