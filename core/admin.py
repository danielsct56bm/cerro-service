"""
Configuración del admin de Django para la aplicación core
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html, mark_safe
from .models import (
    SystemSetup, Company, Role, User, UserRole, AuthLoginAudit,
    TicketTemplate, TicketTemplateField, TicketCategory, TicketSubcategory,
    WorkSession, Ticket, TicketTurn, Kiosk, KioskRegistrationToken
)

@admin.register(SystemSetup)
class SystemSetupAdmin(admin.ModelAdmin):
    list_display = ['id', 'is_completed', 'completed_at', 'note']
    list_filter = ['is_completed']
    readonly_fields = ['completed_at']
    
    def has_add_permission(self, request):
        # Solo permitir una instancia de SystemSetup
        return not SystemSetup.objects.exists()

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'ruc', 'email', 'phone', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'ruc', 'email']
    readonly_fields = ['created_at', 'updated_at', 'logo_preview']
    ordering = ['name']
    
    def logo_preview(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.logo.url}" width="100" height="100" style="object-fit: cover;" />')
        return "Sin logo"
    logo_preview.short_description = "Vista previa del logo"

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'key', 'company', 'can_access', 'is_system', 'created_at']
    list_filter = ['can_access', 'is_system', 'company', 'created_at']
    search_fields = ['name', 'key', 'company__name']
    readonly_fields = ['created_at']
    ordering = ['company__name', 'name']

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'get_full_name', 'company', 'title', 'department', 'can_access', 'is_active']
    list_filter = ['is_active', 'can_access', 'company', 'department', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'company__name']
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'avatar_preview']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Empresa y Acceso', {
            'fields': ('company', 'can_access', 'must_change_password')
        }),
        ('Información de ServiceNow', {
            'fields': ('title', 'department', 'location', 'sap_id', 'employee_number', 'avatar')
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Empresa y Acceso', {
            'fields': ('company', 'can_access', 'must_change_password')
        }),
        ('Información de ServiceNow', {
            'fields': ('title', 'department', 'location', 'sap_id', 'employee_number', 'avatar')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Nombre Completo'
    
    def avatar_preview(self, obj):
        if obj.avatar:
            return mark_safe(f'<img src="{obj.avatar.url}" width="50" height="50" style="object-fit: cover; border-radius: 50%;" />')
        return "Sin avatar"
    avatar_preview.short_description = "Avatar"

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'get_company']
    list_filter = ['role__company', 'role__key']
    search_fields = ['user__username', 'user__email', 'role__name']
    
    def get_company(self, obj):
        return obj.role.company.name
    get_company.short_description = 'Empresa'

@admin.register(AuthLoginAudit)
class AuthLoginAuditAdmin(admin.ModelAdmin):
    list_display = ['user', 'success', 'ip', 'created_at', 'get_status_display']
    list_filter = ['success', 'created_at', 'user__company']
    search_fields = ['user__username', 'user__email', 'ip']
    readonly_fields = ['user', 'success', 'ip', 'user_agent', 'created_at']
    ordering = ['-created_at']
    
    def get_status_display(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ Exitoso</span>')
        else:
            return format_html('<span style="color: red;">✗ Fallido</span>')
    get_status_display.short_description = 'Estado'
    
    def has_add_permission(self, request):
        # No permitir crear registros manualmente
        return False
    
    def has_change_permission(self, request, obj=None):
        # No permitir editar registros
        return False

# ============================================================================
# ADMIN PARA KIOSKOS Y TICKETS
# ============================================================================

@admin.register(TicketTemplate)
class TicketTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'theme', 'is_active', 'created_at']
    list_filter = ['company', 'theme', 'is_active']
    search_fields = ['name', 'company__name']
    ordering = ['company__name', 'name']


@admin.register(TicketTemplateField)
class TicketTemplateFieldAdmin(admin.ModelAdmin):
    list_display = ['label', 'template', 'field_type', 'required', 'order_no']
    list_filter = ['template', 'field_type', 'required']
    search_fields = ['label', 'template__name']
    ordering = ['template__name', 'order_no']


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'description', 'is_active', 'background_image_preview']
    list_filter = ['company', 'is_active']
    search_fields = ['name', 'company__name']
    ordering = ['company__name', 'name']
    fields = ['company', 'name', 'description', 'icon', 'color', 'background_image', 'is_active', 'template']
    readonly_fields = ['background_image_preview']
    
    def background_image_preview(self, obj):
        if obj.background_image:
            return mark_safe(f'<img src="{obj.background_image.url}" width="50" height="30" style="object-fit: cover;" />')
        return "Sin imagen"
    background_image_preview.short_description = "Imagen de Fondo"


@admin.register(TicketSubcategory)
class TicketSubcategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'description', 'is_active', 'background_image_preview']
    list_filter = ['category__company', 'is_active']
    search_fields = ['name', 'category__name']
    ordering = ['category__name', 'name']
    fields = ['category', 'name', 'description', 'icon', 'color', 'background_image', 'is_active']
    readonly_fields = ['background_image_preview']
    
    def background_image_preview(self, obj):
        if obj.background_image:
            return mark_safe(f'<img src="{obj.background_image.url}" width="50" height="30" style="object-fit: cover;" />')
        return "Sin imagen"
    background_image_preview.short_description = "Imagen de Fondo"


@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'start_time', 'end_time', 'is_active']
    list_filter = ['company', 'is_active']
    search_fields = ['name', 'company__name']
    ordering = ['company__name', 'name']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['code', 'requester', 'category', 'status', 'priority', 'created_at']
    list_filter = ['company', 'status', 'priority', 'category', 'created_at']
    search_fields = ['code', 'requester__username', 'category__name']
    ordering = ['-created_at']
    readonly_fields = ['code', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'requester', 'category', 'assigned_to', 'company'
        )


@admin.register(TicketTurn)
class TicketTurnAdmin(admin.ModelAdmin):
    list_display = ['turn_number', 'ticket', 'is_called', 'created_at']
    list_filter = ['is_called', 'ticket__company', 'created_at']
    search_fields = ['turn_number', 'ticket__code']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(Kiosk)
class KioskAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'user', 'device_type', 'is_active', 'last_heartbeat']
    list_filter = ['company', 'device_type', 'is_active']
    search_fields = ['name', 'mac_address', 'company__name']
    ordering = ['company__name', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(KioskRegistrationToken)
class KioskRegistrationTokenAdmin(admin.ModelAdmin):
    list_display = ['token', 'user', 'is_used', 'expires_at', 'created_at']
    list_filter = ['is_used', 'user__company', 'created_at']
    search_fields = ['token', 'user__username']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'user__company')
