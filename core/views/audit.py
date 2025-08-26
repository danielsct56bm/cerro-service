"""
Vistas para auditoría y logs
"""
from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema_view, extend_schema

from ..models import AuthLoginAudit
from ..serializers import AuthLoginAuditSerializer


@extend_schema_view(
    list=extend_schema(summary="Listar logs de acceso", description="Obtiene el historial de logins y logouts", tags=["4. Audit & Logs"]),
    retrieve=extend_schema(summary="Obtener log de acceso", description="Obtiene los detalles de un log de acceso específico", tags=["4. Audit & Logs"])
)
class AuthLoginAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para AuthLoginAudit - Solo lectura"""
    queryset = AuthLoginAudit.objects.all()
    serializer_class = AuthLoginAuditSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['user', 'success', 'created_at']
    search_fields = ['user__username', 'ip', 'user_agent']
    ordering_fields = ['created_at', 'user__username']
    
    def get_view_name(self):
        return "Auth Login Audit"
    
    def get_view_description(self, html=False):
        return "Auditoría de accesos al sistema"
