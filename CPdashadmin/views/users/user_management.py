"""
Vistas básicas de gestión de usuarios
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from core.models import User, Role, UserRole, AuthLoginAudit


@login_required
def user_management(request):
    """Gestión principal de usuarios"""
    # Filtros
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    # Query base - solo usuarios de la empresa del usuario actual
    users = User.objects.filter(company=request.user.company).prefetch_related('userrole_set__role').order_by('username')
    
    # Aplicar filtros
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    if role_filter:
        users = users.filter(userrole_set__role__name=role_filter)
    
    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
    
    # Paginación
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    # Roles disponibles para filtro - solo de la empresa actual
    roles = Role.objects.filter(company=request.user.company)
    
    context = {
        'users': users_page,
        'roles': roles,
        'search': search,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    return render(request, 'CPdashadmin/users/user_management.html', context)


@login_required
def user_detail(request, user_id):
    """Detalle de usuario"""
    user = get_object_or_404(User, id=user_id, company=request.user.company)
    user_roles = user.userrole_set.select_related('role').all()
    recent_activity = AuthLoginAudit.objects.filter(user=user).order_by('-created_at')[:10]
    
    context = {
        'user_detail': user,
        'user_roles': user_roles,
        'recent_activity': recent_activity,
    }
    return render(request, 'CPdashadmin/users/user_detail.html', context)


@login_required
def user_create(request):
    """Crear nuevo usuario"""
    if request.method == 'POST':
        # Lógica para crear usuario
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        role_id = request.POST.get('role')
        
        # Campos adicionales
        title = request.POST.get('title', '')
        department = request.POST.get('department', '')
        location = request.POST.get('location', '')
        employee_number = request.POST.get('employee_number', '')
        sap_id = request.POST.get('sap_id', '')
        
        # Campos de control
        is_active = request.POST.get('is_active') == 'on'
        can_access = request.POST.get('can_access') == 'on'
        must_change_password = request.POST.get('must_change_password') == 'on'
        
        # Validaciones básicas
        if User.objects.filter(username=username).exists():
            messages.error(request, 'El nombre de usuario ya existe.')
            return render(request, 'CPdashadmin/users/user_create.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'El email ya está registrado.')
            return render(request, 'CPdashadmin/users/user_create.html')
        
        # Crear usuario con la empresa del usuario actual
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            company=request.user.company,
            title=title,
            department=department,
            location=location,
            employee_number=employee_number,
            sap_id=sap_id,
            is_active=is_active,
            can_access=can_access,
            must_change_password=must_change_password
        )
        
        # Asignar rol si se proporciona
        if role_id:
            role = get_object_or_404(Role, id=role_id, company=request.user.company)
            UserRole.objects.create(user=user, role=role)
        
        messages.success(request, f'Usuario {username} creado exitosamente.')
        return redirect('CPdashadmin:user_management')
    
    # GET: mostrar formulario
    # Solo roles de la empresa actual
    roles = Role.objects.filter(company=request.user.company)
    context = {
        'roles': roles,
    }
    return render(request, 'CPdashadmin/users/user_create.html', context)


@login_required
def user_edit(request, user_id):
    """Editar usuario"""
    user = get_object_or_404(User, id=user_id, company=request.user.company)
    
    if request.method == 'POST':
        # Lógica para actualizar usuario
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        
        # Campos adicionales
        user.title = request.POST.get('title', '')
        user.department = request.POST.get('department', '')
        user.location = request.POST.get('location', '')
        user.employee_number = request.POST.get('employee_number', '')
        user.sap_id = request.POST.get('sap_id', '')
        
        # Campos de control
        user.is_active = request.POST.get('is_active') == 'on'
        user.can_access = request.POST.get('can_access') == 'on'
        user.must_change_password = request.POST.get('must_change_password') == 'on'
        
        # Actualizar contraseña si se proporciona
        new_password = request.POST.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        user.save()
        
        # Actualizar roles
        role_id = request.POST.get('role')
        user.userrole_set.all().delete()  # Eliminar roles actuales
        if role_id:
            role = get_object_or_404(Role, id=role_id, company=request.user.company)
            UserRole.objects.create(user=user, role=role)
        
        messages.success(request, f'Usuario {user.username} actualizado exitosamente.')
        return redirect('CPdashadmin:user_detail', user_id=user.id)
    
    # GET: mostrar formulario
    roles = Role.objects.filter(company=request.user.company)
    user_roles = user.userrole_set.select_related('role').all()
    
    context = {
        'user_edit': user,
        'roles': roles,
        'user_roles': user_roles,
    }
    return render(request, 'CPdashadmin/users/user_edit.html', context)


@login_required
def user_delete(request, user_id):
    """Eliminar usuario"""
    user = get_object_or_404(User, id=user_id, company=request.user.company)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'Usuario {username} eliminado exitosamente.')
        return redirect('CPdashadmin:user_management')
    
    context = {
        'user_delete': user,
    }
    return render(request, 'CPdashadmin/users/user_delete.html', context)
