# Importar todas las vistas para mantener compatibilidad
from .dashboard import dashboard
from .users import (
    user_management, user_detail, user_create, user_edit, 
    user_delete, user_import, user_export
)
from .roles import (
    role_management, role_create, role_detail, role_edit, role_delete
)
from .permissions import (
    permission_management, permission_create, permission_edit, permission_delete
)
from .services import (
    ticket_management, create_ticket, get_subcategories, 
    ticket_categories_management, create_ticket_category, 
    create_ticket_subcategory, create_ticket_template,
    view_ticket_category, edit_ticket_category, delete_ticket_category,
    manage_category_templates,
    kiosk_management, display_management,
    system_settings, reports,
    save_network_settings, save_kiosk_settings, save_general_settings, detect_local_ip
)

__all__ = [
    'dashboard',
    'user_management', 'user_detail', 'user_create', 'user_edit', 
    'user_delete', 'user_import', 'user_export',
    'role_management', 'role_create', 'role_detail', 'role_edit', 'role_delete',
    'permission_management', 'permission_create', 'permission_edit', 'permission_delete',
    'ticket_management', 'create_ticket', 'get_subcategories',
    'ticket_categories_management', 'create_ticket_category',
    'create_ticket_subcategory', 'create_ticket_template',
    'view_ticket_category', 'edit_ticket_category', 'delete_ticket_category',
    'manage_category_templates',
    'kiosk_management', 'display_management',
    'system_settings', 'reports',
    'save_network_settings', 'save_kiosk_settings', 'save_general_settings', 'detect_local_ip'
]
