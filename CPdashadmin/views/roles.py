from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from core.models import Role, UserRole


@login_required
def role_management(request):
    """Gestión de roles"""
    # Solo roles de la empresa del usuario actual
    roles = Role.objects.filter(company=request.user.company).annotate(user_count=Count('userrole'))
    
    context = {
        'roles': roles,
    }
    return render(request, 'CPdashadmin/roles/role_management.html', context)


@login_required
def role_create(request):
    """Crear nuevo rol"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        key = request.POST.get('key', 'user')  # Default a 'user'
        
        if Role.objects.filter(company=request.user.company, name=name).exists():
            messages.error(request, 'El nombre del rol ya existe en esta empresa.')
            return render(request, 'CPdashadmin/roles/role_create.html')
        
        role = Role.objects.create(
            company=request.user.company,
            name=name,
            key=key,
            description=description
        )
        messages.success(request, f'Rol {name} creado exitosamente.')
        return redirect('CPdashadmin:role_management')
    
    # Opciones de roles predefinidos
    role_choices = Role.ROLE_CHOICES
    context = {
        'role_choices': role_choices,
    }
    return render(request, 'CPdashadmin/roles/role_create.html', context)


@login_required
def role_detail(request, role_id):
    """Detalle de rol"""
    role = get_object_or_404(Role, id=role_id, company=request.user.company)
    users_with_role = role.userrole_set.select_related('user').all()
    
    context = {
        'role': role,
        'users_with_role': users_with_role,
    }
    return render(request, 'CPdashadmin/roles/role_detail.html', context)


@login_required
def role_edit(request, role_id):
    """Editar rol"""
    role = get_object_or_404(Role, id=role_id, company=request.user.company)
    
    if request.method == 'POST':
        role.name = request.POST.get('name')
        role.description = request.POST.get('description')
        role.save()
        
        messages.success(request, f'Rol {role.name} actualizado exitosamente.')
        return redirect('CPdashadmin:role_detail', role_id=role.id)
    
    context = {
        'role': role,
    }
    return render(request, 'CPdashadmin/roles/role_edit.html', context)


@login_required
def role_delete(request, role_id):
    """Eliminar rol"""
    role = get_object_or_404(Role, id=role_id, company=request.user.company)
    
    if request.method == 'POST':
        name = role.name
        role.delete()
        messages.success(request, f'Rol {name} eliminado exitosamente.')
        return redirect('CPdashadmin:role_management')
    
    context = {
        'role': role,
    }
    return render(request, 'CPdashadmin/roles/role_delete.html', context)
