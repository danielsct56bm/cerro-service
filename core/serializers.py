"""
Serializers para la API REST del sistema
"""
from rest_framework import serializers
from .models import (
    SystemSetup, Company, Role, User, UserRole, AuthLoginAudit,
    TicketTemplate, TicketTemplateField, TicketCategory, TicketSubcategory,
    WorkSession, Ticket, TicketTurn, Kiosk, KioskRegistrationToken
)

class SystemSetupSerializer(serializers.ModelSerializer):
    """Serializer para SystemSetup"""
    
    class Meta:
        model = SystemSetup
        fields = [
            'id', 'is_completed', 'completed_at', 'note'
        ]
        read_only_fields = ['id']
    
    def to_representation(self, instance):
        """Personalizar la representación del setup"""
        data = super().to_representation(instance)
        
        # Agregar información adicional del estado del sistema
        if instance.is_completed:
            data['status'] = 'completed'
            data['status_message'] = 'Sistema configurado y operativo'
            data['setup_duration'] = None
            # Como no tenemos created_at, no podemos calcular la duración
        else:
            data['status'] = 'pending'
            data['status_message'] = 'Sistema pendiente de configuración'
            data['setup_duration'] = None
        
        return data

class CompanySerializer(serializers.ModelSerializer):
    """Serializer para Company"""
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'ruc', 'address', 'phone', 'email', 'logo',
            'active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class RoleSerializer(serializers.ModelSerializer):
    """Serializer para Role"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Role
        fields = [
            'id', 'company', 'company_name', 'key', 'name', 
            'can_access', 'is_system', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class UserSerializer(serializers.ModelSerializer):
    """Serializer para User"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'company', 'company_name', 'title', 'department', 'location',
            'sap_id', 'employee_number', 'avatar', 'is_active', 'can_access',
            'must_change_password', 'last_login', 'created_at', 'updated_at',
            'roles'
        ]
        read_only_fields = ['id', 'last_login', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def get_roles(self, obj) -> list:
        """Obtener roles del usuario"""
        user_roles = UserRole.objects.filter(user=obj)
        return [{'id': ur.role.id, 'name': ur.role.name, 'key': ur.role.key} for ur in user_roles]

class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios"""
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'company', 'title', 'department', 'location', 'sap_id', 'employee_number', 'avatar'
        ]
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer para UserRole"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    company_name = serializers.CharField(source='role.company.name', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'user_username', 'role', 'role_name', 'company_name']

class AuthLoginAuditSerializer(serializers.ModelSerializer):
    """Serializer para AuthLoginAudit"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    company_name = serializers.CharField(source='user.company.name', read_only=True)
    
    class Meta:
        model = AuthLoginAudit
        fields = [
            'id', 'user', 'user_username', 'company_name', 'success', 
            'ip', 'user_agent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

# Serializers para el setup del sistema
class SetupCompanySerializer(serializers.Serializer):
    """Serializer para el setup de empresa"""
    name = serializers.CharField(max_length=255)
    ruc = serializers.CharField(max_length=32, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    logo = serializers.ImageField(required=False, allow_null=True)

class SetupAdminSerializer(serializers.Serializer):
    """Serializer para el setup del administrador"""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(max_length=255, write_only=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    avatar = serializers.ImageField(required=False, allow_null=True)

class SystemSetupRequestSerializer(serializers.Serializer):
    """Serializer para la solicitud de setup del sistema"""
    company = SetupCompanySerializer()
    admin = SetupAdminSerializer()
    force = serializers.BooleanField(default=False, required=False)

class SystemSetupResponseSerializer(serializers.Serializer):
    """Serializer para la respuesta del setup del sistema"""
    message = serializers.CharField()
    company = CompanySerializer()
    admin_user = UserSerializer()
    setup = SystemSetupSerializer()
    roles_created = serializers.ListField(
        child=serializers.DictField(),
        help_text="Lista de roles creados durante el setup"
    )
    setup_summary = serializers.DictField(
        help_text="Resumen del setup realizado"
    )

class TicketTemplateSerializer(serializers.ModelSerializer):
    """Serializer para TicketTemplate"""
    
    class Meta:
        model = TicketTemplate
        fields = ['id', 'name', 'theme', 'settings', 'is_active', 'created_at']


class TicketTemplateFieldSerializer(serializers.ModelSerializer):
    """Serializer para TicketTemplateField"""
    
    class Meta:
        model = TicketTemplateField
        fields = ['id', 'name', 'label', 'field_type', 'required', 'options', 'order_no']


class TicketCategorySerializer(serializers.ModelSerializer):
    """Serializer para TicketCategory"""
    
    class Meta:
        model = TicketCategory
        fields = ['id', 'name', 'description', 'icon', 'color', 'is_active', 'template']


class TicketSubcategorySerializer(serializers.ModelSerializer):
    """Serializer para TicketSubcategory"""
    
    class Meta:
        model = TicketSubcategory
        fields = ['id', 'name', 'icon', 'color', 'is_active']


class WorkSessionSerializer(serializers.ModelSerializer):
    """Serializer para WorkSession"""
    
    class Meta:
        model = WorkSession
        fields = ['id', 'name', 'start_time', 'end_time', 'is_active', 'created_at']


class TicketSerializer(serializers.ModelSerializer):
    """Serializer para Ticket"""
    category = TicketCategorySerializer(read_only=True)
    subcategory = TicketSubcategorySerializer(read_only=True)
    requester = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'code', 'requester', 'assigned_to', 'category', 'subcategory',
            'template', 'form_data', 'status', 'priority', 'created_at', 'updated_at'
        ]


class TicketCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear tickets"""
    
    class Meta:
        model = Ticket
        fields = ['category', 'subcategory', 'template', 'form_data', 'priority']


class TicketTurnSerializer(serializers.ModelSerializer):
    """Serializer para TicketTurn"""
    ticket = TicketSerializer(read_only=True)
    
    class Meta:
        model = TicketTurn
        fields = ['id', 'turn_number', 'display_message', 'is_called', 'called_at', 'created_at', 'ticket']


class KioskSerializer(serializers.ModelSerializer):
    """Serializer para Kiosk"""
    company = CompanySerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Kiosk
        fields = [
            'id', 'company', 'user', 'name', 'mac_address', 'device_type',
            'is_active', 'last_heartbeat', 'created_at', 'updated_at'
        ]


class KioskCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear kioskos"""
    
    class Meta:
        model = Kiosk
        fields = ['name', 'mac_address', 'device_type']


class KioskRegistrationTokenSerializer(serializers.ModelSerializer):
    """Serializer para KioskRegistrationToken"""
    
    class Meta:
        model = KioskRegistrationToken
        fields = ['id', 'token', 'is_used', 'expires_at', 'created_at']


class GenerateKioskUrlSerializer(serializers.Serializer):
    """Serializer para generar URL de registro de kiosco"""
    user_id = serializers.IntegerField(help_text='ID del usuario que generará la URL')


class KioskRegistrationSerializer(serializers.Serializer):
    """Serializer para registro de kiosco"""
    name = serializers.CharField(max_length=255, help_text='Nombre del kiosco')
    mac_address = serializers.CharField(max_length=17, help_text='Dirección MAC del dispositivo')
    device_type = serializers.ChoiceField(
        choices=Kiosk.DEVICE_TYPES,
        help_text='Tipo de dispositivo'
    )

class LoginSerializer(serializers.Serializer):
    """Serializer para login de usuarios"""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=255, write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            
            if not user:
                raise serializers.ValidationError('Credenciales inválidas.')
            
            if not user.is_active:
                raise serializers.ValidationError('Usuario inactivo.')
            
            if hasattr(user, 'can_access') and not user.can_access:
                raise serializers.ValidationError('Usuario sin acceso al sistema.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Debe proporcionar username y password.')

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para perfil de usuario autenticado"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'company', 'company_name', 'title', 'department', 'location',
            'sap_id', 'employee_number', 'avatar', 'is_active', 'can_access',
            'must_change_password', 'last_login', 'created_at', 'updated_at',
            'roles'
        ]
        read_only_fields = ['id', 'last_login', 'created_at', 'updated_at']
    
    def get_roles(self, obj) -> list:
        """Obtener roles del usuario"""
        user_roles = UserRole.objects.filter(user=obj)
        return [{'id': ur.role.id, 'name': ur.role.name, 'key': ur.role.key} for ur in user_roles]

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña"""
    current_password = serializers.CharField(max_length=255, write_only=True)
    new_password = serializers.CharField(max_length=255, write_only=True)
    confirm_password = serializers.CharField(max_length=255, write_only=True)
    
    def validate(self, attrs):
        current_password = attrs.get('current_password')
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        user = self.context['request'].user
        
        # Verificar contraseña actual
        if not user.check_password(current_password):
            raise serializers.ValidationError('Contraseña actual incorrecta.')
        
        # Verificar que las nuevas contraseñas coincidan
        if new_password != confirm_password:
            raise serializers.ValidationError('Las contraseñas nuevas no coinciden.')
        
        # Validar nueva contraseña
        from django.contrib.auth.password_validation import validate_password
        validate_password(new_password, user)
        
        return attrs

class RefreshSessionSerializer(serializers.Serializer):
    """Serializer para refrescar sesión"""
    
    def validate(self, attrs):
        request = self.context['request']
        user = request.user
        
        if not user.is_authenticated:
            raise serializers.ValidationError('Usuario no autenticado.')
        
        if not user.is_active:
            raise serializers.ValidationError('Usuario inactivo.')
        
        if hasattr(user, 'can_access') and not user.can_access:
            raise serializers.ValidationError('Usuario sin acceso al sistema.')
        
        return attrs

class FileUploadSerializer(serializers.Serializer):
    """Serializer para upload de archivos"""
    file = serializers.FileField()
    type = serializers.ChoiceField(choices=['logo', 'avatar'], help_text="Tipo de archivo a subir")
    
    def validate_file(self, value):
        """Validar el archivo subido"""
        # Verificar tamaño máximo (5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('El archivo no puede ser mayor a 5MB.')
        
        # Verificar tipo de archivo
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if hasattr(value, 'content_type') and value.content_type not in allowed_types:
            raise serializers.ValidationError('Solo se permiten archivos de imagen (JPEG, PNG, GIF, WebP).')
        
        return value
