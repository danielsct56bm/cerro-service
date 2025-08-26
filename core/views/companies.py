"""
Vistas para gestión de empresas
"""
from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema_view, extend_schema

from ..models import Company
from ..serializers import CompanySerializer


@extend_schema_view(
    list=extend_schema(
        summary="Listar empresas",
        description="Obtiene la lista de empresas del sistema",
        tags=["2. Companies"]
    ),
    create=extend_schema(
        summary="Crear empresa",
        description="Crea una nueva empresa en el sistema",
        tags=["2. Companies"]
    ),
    retrieve=extend_schema(
        summary="Obtener empresa",
        description="Obtiene los detalles de una empresa específica",
        tags=["2. Companies"]
    ),
    update=extend_schema(
        summary="Actualizar empresa",
        description="Actualiza los datos de una empresa",
        tags=["2. Companies"]
    ),
    destroy=extend_schema(
        summary="Eliminar empresa",
        description="Elimina una empresa del sistema",
        tags=["2. Companies"]
    )
)
class CompanyViewSet(viewsets.ModelViewSet):
    """ViewSet para Company"""
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['active', 'name']
    search_fields = ['name', 'ruc', 'email']
    ordering_fields = ['name', 'created_at']
    
    def get_view_name(self):
        return "Companies"
    
    def get_view_description(self, html=False):
        return "Gestión de empresas y tenants del sistema"
