# Importar todas las vistas desde los módulos modularizados
from .views.dashboard import dashboard
from .views.users import (
    user_management, user_detail, user_create, user_edit, 
    user_delete, user_import, user_export
)
from .views.roles import (
    role_management, role_create, role_detail, role_edit, role_delete
)
from .views.permissions import (
    permission_management, permission_create, permission_edit, permission_delete
)
from .views.services import (
    ticket_management, kiosk_management, display_management,
    system_settings, reports
)

# Mantener compatibilidad con imports existentes
__all__ = [
    'dashboard',
    'user_management', 'user_detail', 'user_create', 'user_edit', 
    'user_delete', 'user_import', 'user_export',
    'role_management', 'role_create', 'role_detail', 'role_edit', 'role_delete',
    'permission_management', 'permission_create', 'permission_edit', 'permission_delete',
    'ticket_management', 'kiosk_management', 'display_management',
    'system_settings', 'reports'
]
