from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from core.models import User, Kiosk, Ticket, AuthLoginAudit


@login_required
def dashboard(request):
    """Dashboard principal del admin"""
    # Estadísticas generales - solo de la empresa actual
    total_users = User.objects.filter(company=request.user.company, is_active=True).count()
    total_kiosks = Kiosk.objects.filter(company=request.user.company, is_active=True).count()
    total_tickets = Ticket.objects.filter(company=request.user.company).count()
    recent_logins = AuthLoginAudit.objects.filter(
        user__company=request.user.company
    ).select_related('user').order_by('-created_at')[:5]
    
    context = {
        'total_users': total_users,
        'total_kiosks': total_kiosks,
        'total_tickets': total_tickets,
        'recent_logins': recent_logins,
    }
    return render(request, 'CPdashadmin/dashboard.html', context)
