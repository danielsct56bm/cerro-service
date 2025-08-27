from django.urls import path
from . import views

app_name = 'CPdashadmin'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Usuarios
    path('users/', views.user_management, name='user_management'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/import/', views.user_import, name='user_import'),
    path('users/export/', views.user_export, name='user_export'),
    
    # Roles
    path('roles/', views.role_management, name='role_management'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/<int:role_id>/', views.role_detail, name='role_detail'),
    path('roles/<int:role_id>/edit/', views.role_edit, name='role_edit'),
    path('roles/<int:role_id>/delete/', views.role_delete, name='role_delete'),
    
    # Permisos
    path('permissions/', views.permission_management, name='permission_management'),
    
    # Tickets (URLs directas)
    path('tickets/', views.ticket_management, name='ticket_management'),
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/get-subcategories/<int:category_id>/', views.get_subcategories, name='get_subcategories'),
    
    # Gestión de Categorías de Tickets
    path('tickets/categories/', views.ticket_categories_management, name='ticket_categories_management'),
    path('tickets/categories/create/', views.create_ticket_category, name='create_ticket_category'),
    path('tickets/categories/<int:category_id>/', views.view_ticket_category, name='view_ticket_category'),
    path('tickets/categories/<int:category_id>/edit/', views.edit_ticket_category, name='edit_ticket_category'),
    path('tickets/categories/<int:category_id>/delete/', views.delete_ticket_category, name='delete_ticket_category'),
    path('tickets/categories/<int:category_id>/templates/', views.manage_category_templates, name='manage_category_templates'),
    path('tickets/subcategories/create/', views.create_ticket_subcategory, name='create_ticket_subcategory'),
    path('tickets/subcategories/<int:subcategory_id>/', views.view_ticket_subcategory, name='view_ticket_subcategory'),
    path('tickets/subcategories/<int:subcategory_id>/edit/', views.edit_ticket_subcategory, name='edit_ticket_subcategory'),
    path('tickets/subcategories/<int:subcategory_id>/delete/', views.delete_ticket_subcategory, name='delete_ticket_subcategory'),
    path('tickets/subcategories/', views.subcategories_management, name='subcategories_management'),
    path('tickets/templates/create/', views.create_ticket_template, name='create_ticket_template'),
    
    # Servicios
    path('services/tickets/', views.ticket_management, name='ticket_management_services'),
    path('services/tickets/create/', views.create_ticket, name='create_ticket_services'),
    path('services/tickets/get-subcategories/<int:category_id>/', views.get_subcategories, name='get_subcategories_services'),
    path('services/kiosks/', views.kiosk_management, name='kiosk_management'),
    path('services/displays/', views.display_management, name='display_management'),
    
    # Configuración
    path('settings/', views.system_settings, name='system_settings'),
    path('settings/network/save/', views.save_network_settings, name='save_network_settings'),
    path('settings/kiosk/save/', views.save_kiosk_settings, name='save_kiosk_settings'),
    path('settings/general/save/', views.save_general_settings, name='save_general_settings'),
    path('settings/detect-ip/', views.detect_local_ip, name='detect_local_ip'),
    
    # Reportes
    path('reports/', views.reports, name='reports'),
]
