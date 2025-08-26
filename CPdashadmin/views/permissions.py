from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from core.models import Role


@login_required
def permission_management(request):
    """Gestión de permisos"""
    # Solo roles de la empresa del usuario actual
    roles = Role.objects.filter(company=request.user.company).annotate(user_count=Count('userrole'))
    
    context = {
        'roles': roles,
    }
    return render(request, 'CPdashadmin/permissions/permission_management.html', context)


@login_required
def permission_create(request):
    """Crear nuevo permiso"""
    messages.info(request, 'La gestión de permisos granular estará disponible próximamente.')
    return redirect('CPdashadmin:permission_management')


@login_required
def permission_edit(request, permission_id):
    """Editar permiso"""
    messages.info(request, 'La gestión de permisos granular estará disponible próximamente.')
    return redirect('CPdashadmin:permission_management')


@login_required
def permission_delete(request, permission_id):
    """Eliminar permiso"""
    messages.info(request, 'La gestión de permisos granular estará disponible próximamente.')
    return redirect('CPdashadmin:permission_management')
