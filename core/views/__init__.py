"""
Vistas organizadas por funcionalidad para mantener archivos pequeños y mantenibles
"""

# Importar todas las vistas para mantener compatibilidad

from .setup import (
    SystemSetupAPIView, SystemStatusAPIView
)

from .companies import CompanyViewSet

from .users import (
    UserViewSet, RoleViewSet, UserRoleViewSet
)

from .audit import AuthLoginAuditViewSet

from .kiosks import (
    KioskViewSet, GenerateKioskUrlAPIView, KioskRegistrationAPIView
)

from .tickets import (
    TicketViewSet, TicketTurnViewSet, KioskTemplatesAPIView, GenerateTicketOrderAPIView
)

from .upload import FileUploadAPIView

from .kiosk import (
    kiosk_view, kiosk_status, kiosk_categories, kiosk_subcategories,
    kiosk_template, kiosk_generate_ticket, kiosk_health
)

# Exportar todas las vistas
__all__ = [
    # Setup
    'SystemSetupAPIView', 'SystemStatusAPIView',
    
    # Companies
    'CompanyViewSet',
    
    # Users
    'UserViewSet', 'RoleViewSet', 'UserRoleViewSet',
    
    # Audit
    'AuthLoginAuditViewSet',
    
    # Kiosks
    'KioskViewSet', 'GenerateKioskUrlAPIView', 'KioskRegistrationAPIView',
    
    # Tickets
    'TicketViewSet', 'TicketTurnViewSet', 'KioskTemplatesAPIView', 'GenerateTicketOrderAPIView',
    
    # Upload
    'FileUploadAPIView',
    'kiosk_view', 'kiosk_status', 'kiosk_categories', 'kiosk_subcategories',
    'kiosk_template', 'kiosk_generate_ticket', 'kiosk_health',
]
