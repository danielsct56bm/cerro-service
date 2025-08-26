"""
Vistas para gestión de usuarios y roles
"""
from rest_framework import viewsets, permissions
from django.db import models
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import Role, UserRole
from ..serializers import (
    UserSerializer, UserCreateSerializer, RoleSerializer, UserRoleSerializer
)

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        summary="Listar usuarios",
        description="Obtiene la lista de usuarios del sistema con búsqueda y filtros avanzados",
        tags=["3. Users & Roles"],
        parameters=[
            OpenApiParameter(name='search', type=str, description='Búsqueda general'),
            OpenApiParameter(name='full_name', type=str, description='Buscar por nombre completo'),
            OpenApiParameter(name='employee_number', type=str, description='Buscar por número de empleado'),
            OpenApiParameter(name='sap_id', type=str, description='Buscar por SAP ID'),
            OpenApiParameter(name='title', type=str, description='Buscar por título/cargo'),
            OpenApiParameter(name='department', type=str, description='Filtrar por departamento'),
            OpenApiParameter(name='location', type=str, description='Filtrar por ubicación'),
            OpenApiParameter(name='company', type=int, description='Filtrar por ID de empresa'),
            OpenApiParameter(name='is_active', type=bool, description='Filtrar por estado activo'),
            OpenApiParameter(name='can_access', type=bool, description='Filtrar por permiso de acceso'),
            OpenApiParameter(name='access_status', type=str, enum=['active', 'inactive', 'blocked'], description='Filtrar por estado de acceso combinado'),
            OpenApiParameter(name='created_after', type=str, description='Usuarios creados después de esta fecha (YYYY-MM-DD)'),
            OpenApiParameter(name='created_before', type=str, description='Usuarios creados antes de esta fecha (YYYY-MM-DD)'),
            OpenApiParameter(name='last_login_after', type=str, description='Último login después de esta fecha (YYYY-MM-DD)'),
            OpenApiParameter(name='ordering', type=str, description='Ordenar por: username, company__name, created_at, last_login, first_name, last_name, employee_number'),
        ]
    ),
    create=extend_schema(summary="Crear usuario", description="Crea un nuevo usuario en el sistema", tags=["3. Users & Roles"]),
    retrieve=extend_schema(summary="Obtener usuario", description="Obtiene los detalles de un usuario específico", tags=["3. Users & Roles"]),
    update=extend_schema(summary="Actualizar usuario", description="Actualiza los datos de un usuario", tags=["3. Users & Roles"]),
    destroy=extend_schema(summary="Eliminar usuario", description="Elimina un usuario del sistema", tags=["3. Users & Roles"])
)
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para User"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['company', 'is_active', 'can_access', 'department', 'location']
    search_fields = [
        'username', 'email', 'first_name', 'last_name', 'company__name',
        'employee_number', 'u_sap_id', 'title'
    ]
    ordering_fields = [
        'username', 'company__name', 'created_at', 'last_login',
        'first_name', 'last_name', 'employee_number'
    ]
    
    def get_view_name(self):
        return "Users"
    
    def get_view_description(self, html=False):
        return "Gestión de usuarios del sistema multi-tenant"
    
    def get_queryset(self):
        """Mejorar queryset con prefetch y select_related para optimizar consultas"""
        return User.objects.select_related('company').prefetch_related('userrole_set__role')
    
    def get_serializer_class(self):
        """Usar serializer diferente para crear"""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def filter_queryset(self, queryset):
        """Filtrado personalizado para búsquedas avanzadas"""
        queryset = super().filter_queryset(queryset)
        
        # Búsqueda por nombre completo (first_name + last_name)
        full_name = self.request.query_params.get('full_name', None)
        if full_name:
            queryset = queryset.filter(
                models.Q(first_name__icontains=full_name) |
                models.Q(last_name__icontains=full_name) |
                models.Q(first_name__icontains=full_name.split()[0]) |
                models.Q(last_name__icontains=full_name.split()[-1])
            )
        
        # Búsqueda por número de empleado
        employee_number = self.request.query_params.get('employee_number', None)
        if employee_number:
            queryset = queryset.filter(employee_number__icontains=employee_number)
        
        # Búsqueda por SAP ID
        sap_id = self.request.query_params.get('sap_id', None)
        if sap_id:
            queryset = queryset.filter(u_sap_id__icontains=sap_id)
        
        # Búsqueda por título/cargo
        title = self.request.query_params.get('title', None)
        if title:
            queryset = queryset.filter(title__icontains=title)
        
        # Búsqueda por departamento
        department = self.request.query_params.get('department', None)
        if department:
            queryset = queryset.filter(department__icontains=department)
        
        # Búsqueda por ubicación
        location = self.request.query_params.get('location', None)
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Filtro por estado de acceso
        access_status = self.request.query_params.get('access_status', None)
        if access_status:
            if access_status == 'active':
                queryset = queryset.filter(can_access=True, is_active=True)
            elif access_status == 'inactive':
                queryset = queryset.filter(can_access=False)
            elif access_status == 'blocked':
                queryset = queryset.filter(is_active=False)
        
        # Filtro por fecha de creación
        created_after = self.request.query_params.get('created_after', None)
        if created_after:
            try:
                date = timezone.datetime.strptime(created_after, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date)
            except ValueError:
                pass
        
        created_before = self.request.query_params.get('created_before', None)
        if created_before:
            try:
                date = timezone.datetime.strptime(created_before, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date)
            except ValueError:
                pass
        
        # Filtro por último login
        last_login_after = self.request.query_params.get('last_login_after', None)
        if last_login_after:
            try:
                date = timezone.datetime.strptime(last_login_after, '%Y-%m-%d').date()
                queryset = queryset.filter(last_login__date__gte=date)
            except ValueError:
                pass
        
        return queryset


@extend_schema_view(
    list=extend_schema(summary="Listar roles", description="Obtiene la lista de roles del sistema", tags=["3. Users & Roles"]),
    create=extend_schema(summary="Crear rol", description="Crea un nuevo rol en el sistema", tags=["3. Users & Roles"]),
    retrieve=extend_schema(summary="Obtener rol", description="Obtiene los detalles de un rol específico", tags=["3. Users & Roles"]),
    update=extend_schema(summary="Actualizar rol", description="Actualiza los datos de un rol", tags=["3. Users & Roles"]),
    destroy=extend_schema(summary="Eliminar rol", description="Elimina un rol del sistema", tags=["3. Users & Roles"])
)
class RoleViewSet(viewsets.ModelViewSet):
    """ViewSet para Role"""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['company', 'can_access', 'is_system']
    search_fields = ['name', 'key', 'company__name']
    ordering_fields = ['company__name', 'name']
    
    def get_view_name(self):
        return "Roles"
    
    def get_view_description(self, html=False):
        return "Gestión de roles y permisos por empresa"


@extend_schema_view(
    list=extend_schema(summary="Listar asignaciones de roles", description="Obtiene la lista de asignaciones de roles a usuarios", tags=["3. Users & Roles"]),
    create=extend_schema(summary="Asignar rol a usuario", description="Asigna un rol a un usuario específico", tags=["3. Users & Roles"]),
    retrieve=extend_schema(summary="Obtener asignación de roles", description="Obtiene los detalles de una asignación de rol específica", tags=["3. Users & Roles"]),
    update=extend_schema(summary="Actualizar asignación de rol", description="Actualiza la asignación de rol a un usuario", tags=["3. Users & Roles"]),
    destroy=extend_schema(summary="Remover rol de usuario", description="Remueve un rol asignado a un usuario", tags=["3. Users & Roles"])
)
class UserRoleViewSet(viewsets.ModelViewSet):
    """ViewSet para UserRole"""
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['user', 'role', 'role__company']
    search_fields = ['user__username', 'role__name', 'role__company__name']
