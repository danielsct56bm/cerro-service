from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinLengthValidator
import uuid

class SystemSetup(models.Model):
    """
    Control del setup inicial del sistema
    Solo se puede crear una instancia
    """
    id = models.AutoField(primary_key=True)
    is_completed = models.BooleanField(default=False, verbose_name="Setup Completado")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Completado")
    note = models.TextField(blank=True, verbose_name="Notas del Setup")
    
    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuración del Sistema"
        db_table = 'system_setup'
    
    def __str__(self):
        return f"Setup del Sistema - {'Completado' if self.is_completed else 'Pendiente'}"
    
    def save(self, *args, **kwargs):
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

class Company(models.Model):
    """
    Empresas/Tenants del sistema
    """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name="Nombre de la Empresa")
    ruc = models.CharField(max_length=32, blank=True, verbose_name="RUC")
    address = models.TextField(blank=True, verbose_name="Dirección")
    phone = models.CharField(max_length=32, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True, verbose_name="Logo de la Empresa")
    active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        db_table = 'companies'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return self.name

class Role(models.Model):
    """
    Roles del sistema por empresa (multi-tenant)
    """
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('user', 'Usuario'),
        ('technician', 'Técnico'),
    ]
    
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Empresa")
    key = models.CharField(max_length=50, choices=ROLE_CHOICES, verbose_name="Clave del Rol")
    name = models.CharField(max_length=100, verbose_name="Nombre del Rol")
    can_access = models.BooleanField(default=True, verbose_name="Puede Acceder")
    is_system = models.BooleanField(default=False, verbose_name="Es Rol del Sistema")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    
    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        db_table = 'roles'
        unique_together = ['company', 'key']
        indexes = [
            models.Index(fields=['company', 'key']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.company.name})"

class User(AbstractUser):
    """
    Usuarios del sistema con soporte multi-tenant
    Extiende el modelo User de Django
    """
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Campos adicionales para ServiceNow
    title = models.CharField(max_length=100, blank=True, verbose_name="Cargo")
    department = models.CharField(max_length=100, blank=True, verbose_name="Departamento")
    location = models.CharField(max_length=100, blank=True, verbose_name="Ubicación")
    sap_id = models.CharField(max_length=50, blank=True, verbose_name="ID SAP")
    employee_number = models.CharField(max_length=50, blank=True, verbose_name="Número de Empleado")
    avatar = models.ImageField(upload_to='user_avatars/', blank=True, null=True, verbose_name="Avatar del Usuario")
    
    # Campos de control
    must_change_password = models.BooleanField(default=False, verbose_name="Debe Cambiar Contraseña")
    can_access = models.BooleanField(default=False, verbose_name="Puede Acceder al Sistema")
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['company']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username}) - {self.company.name}"
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

class UserRole(models.Model):
    """
    Relación muchos a muchos entre usuarios y roles
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name="Rol")
    
    class Meta:
        verbose_name = "Rol de Usuario"
        verbose_name_plural = "Roles de Usuario"
        db_table = 'user_roles'
        unique_together = ['user', 'role']
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

class AuthLoginAudit(models.Model):
    """
    Auditoría de intentos de login
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Usuario")
    success = models.BooleanField(verbose_name="Login Exitoso")
    ip = models.GenericIPAddressField(verbose_name="Dirección IP")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Intento")
    
    class Meta:
        verbose_name = "Auditoría de Login"
        verbose_name_plural = "Auditoría de Logins"
        db_table = 'auth_login_audit'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['success']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        status = "Exitoso" if self.success else "Fallido"
        user_info = self.user.username if self.user else "Usuario Desconocido"
        return f"{user_info} - {status} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

class TicketTemplate(models.Model):
    """Plantilla de formulario para tickets"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='ticket_templates')
    name = models.CharField(max_length=255)
    theme = models.CharField(max_length=50, default='default')
    settings = models.TextField(blank=True, help_text='Configuración JSON de la plantilla')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ticket_templates'
        unique_together = ['company', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"


class TicketTemplateField(models.Model):
    """Campos de formulario para plantillas de tickets"""
    FIELD_TYPES = [
        ('text', 'Texto'),
        ('select', 'Selección'),
        ('toggle', 'Toggle/Checkbox'),
        ('email', 'Email'),
        ('phone', 'Teléfono'),
        ('number', 'Número'),
        ('date', 'Fecha'),
        ('textarea', 'Área de texto'),
    ]
    
    template = models.ForeignKey(TicketTemplate, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=100)
    label = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    options = models.TextField(blank=True, help_text='Opciones JSON para campos select')
    order_no = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'ticket_template_fields'
        ordering = ['order_no']
    
    def __str__(self):
        return f"{self.label} ({self.template.name})"


class TicketCategory(models.Model):
    """Categorías de tickets"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='ticket_categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=10, blank=True)
    background_image = models.ImageField(upload_to='category_backgrounds/', blank=True, null=True, verbose_name="Imagen de Fondo")
    is_active = models.BooleanField(default=True)
    template = models.ForeignKey(TicketTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ticket_categories'
        verbose_name_plural = 'Ticket Categories'
        unique_together = ['company', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"


class TicketSubcategory(models.Model):
    """Subcategorías de tickets"""
    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=10, blank=True)
    background_image = models.ImageField(upload_to='subcategory_backgrounds/', blank=True, null=True, verbose_name="Imagen de Fondo")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ticket_subcategories'
        verbose_name_plural = 'Ticket Subcategories'
        unique_together = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.category.name}"


class WorkSession(models.Model):
    """Sesiones de trabajo para turnos"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='work_sessions')
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'work_sessions'
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"


class Ticket(models.Model):
    """Tickets del sistema"""
    STATUS_CHOICES = [
        ('open', 'Abierto'),
        ('in_progress', 'En Progreso'),
        ('resolved', 'Resuelto'),
        ('closed', 'Cerrado'),
        ('canceled', 'Cancelado'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tickets')
    code = models.CharField(max_length=50, unique=True)
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_tickets')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE, related_name='tickets')
    subcategory = models.ForeignKey(TicketSubcategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets')
    template = models.ForeignKey(TicketTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    form_data = models.TextField(blank=True, help_text='Datos del formulario en JSON')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    session = models.ForeignKey(WorkSession, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'tickets'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Ticket {self.code} - {self.requester.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.code:
            # Generar código único automáticamente
            self.code = self.generate_ticket_code()
        super().save(*args, **kwargs)
    
    def generate_ticket_code(self):
        """Generar código único de ticket"""
        import random
        import string
        from datetime import datetime
        
        # Formato: YYYYMMDD-XXXX
        date_part = datetime.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        code = f"{date_part}-{random_part}"
        
        # Verificar que no exista
        while Ticket.objects.filter(code=code).exists():
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            code = f"{date_part}-{random_part}"
        
        return code


class TicketTurn(models.Model):
    """Turnos generados por tickets"""
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='turn')
    turn_number = models.IntegerField()
    display_message = models.CharField(max_length=255, blank=True)
    is_called = models.BooleanField(default=False)
    called_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ticket_turns'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Turno {self.turn_number} - Ticket {self.ticket.code}"
    
    def call_turn(self):
        """Marcar turno como llamado"""
        from django.utils import timezone
        self.is_called = True
        self.called_at = timezone.now()
        self.save()


class Kiosk(models.Model):
    """Kioskos de tickets"""
    DEVICE_TYPES = [
        ('windows', 'Windows'),
        ('android', 'Android'),
        ('web', 'Web'),
        ('ios', 'iOS'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='kiosks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kiosks')
    name = models.CharField(max_length=255)
    mac_address = models.CharField(max_length=17, unique=True)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    is_active = models.BooleanField(default=True)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'kiosks'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.mac_address}"
    
    def get_websocket_channel(self):
        """Obtener canal WebSocket específico para este kiosco"""
        return f"kiosk_{self.id}_{self.company.id}"


class KioskRegistrationToken(models.Model):
    """Tokens para registro de kioskos"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kiosk_tokens')
    token = models.CharField(max_length=64, unique=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'kiosk_registration_tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token {self.token[:8]}... - {self.user.username}"
    
    def is_expired(self):
        """Verificar si el token ha expirado"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def mark_as_used(self):
        """Marcar token como usado"""
        self.is_used = True
        self.save()
