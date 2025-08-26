"""
Vistas para setup inicial del sistema
"""
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import SystemSetup, Company, Role, UserRole
from ..serializers import (
    SystemSetupRequestSerializer, SystemSetupResponseSerializer,
    SystemSetupSerializer, CompanySerializer, UserSerializer
)

User = get_user_model()


@extend_schema(
    tags=["1. System Setup"],
    summary="Setup del Sistema",
    description="Configuración inicial del sistema multi-tenant"
)
class SystemSetupAPIView(APIView):
    """Vista para el setup inicial del sistema"""
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Verificar estado del setup",
        description="Obtiene el estado actual de la configuración del sistema",
        responses={
            200: {
                'description': 'Estado del setup',
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'enum': ['completed', 'pending']},
                    'message': {'type': 'string'},
                    'completed_at': {'type': 'string', 'format': 'date-time'},
                    'note': {'type': 'string'}
                }
            }
        }
    )
    def get(self, request):
        """Obtener estado del setup"""
        try:
            setup = SystemSetup.objects.first()
            if setup and setup.is_completed:
                return Response({
                    'status': 'completed',
                    'message': 'El sistema ya está configurado',
                    'completed_at': setup.completed_at,
                    'note': setup.note
                })
            else:
                return Response({
                    'status': 'pending',
                    'message': 'El sistema no está configurado'
                })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        summary="Ejecutar setup del sistema",
        description="Configura el sistema inicial con empresa, roles y usuario administrador",
        request=SystemSetupRequestSerializer,
        responses={
            201: SystemSetupResponseSerializer,
            400: {
                'description': 'Error en la solicitud o sistema ya configurado',
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    )
    def post(self, request):
        """Ejecutar setup del sistema"""
        serializer = SystemSetupRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        force = data.get('force', False)
        
        # Verificar si ya está configurado
        if SystemSetup.objects.filter(is_completed=True).exists() and not force:
            return Response({
                'error': 'El sistema ya está configurado. Use force=true para reconfigurar.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # 1. Crear o actualizar SystemSetup
                setup, created = SystemSetup.objects.get_or_create(
                    id=1,
                    defaults={'is_completed': False}
                )
                
                # 2. Crear empresa
                company_data = data['company']
                company, created = Company.objects.get_or_create(
                    name=company_data['name'],
                    defaults={
                        'ruc': company_data.get('ruc', ''),
                        'email': company_data.get('email', f"info@{company_data['name'].lower().replace(' ', '')}.com"),
                        'phone': company_data.get('phone', ''),
                        'address': company_data.get('address', ''),
                        'logo': company_data.get('logo'),
                        'active': True
                    }
                )
                
                # 3. Crear roles base
                roles_data = [
                    {'key': 'admin', 'name': 'Administrador', 'is_system': True},
                    {'key': 'user', 'name': 'Usuario', 'is_system': True},
                    {'key': 'technician', 'name': 'Técnico', 'is_system': True},
                ]
                
                created_roles = []
                for role_data in roles_data:
                    role, created = Role.objects.get_or_create(
                        company=company,
                        key=role_data['key'],
                        defaults={
                            'name': role_data['name'],
                            'can_access': True,
                            'is_system': role_data['is_system']
                        }
                    )
                    created_roles.append(role)
                
                # 4. Crear usuario administrador
                admin_data = data['admin']
                admin_role = next(r for r in created_roles if r.key == 'admin')
                
                user, created = User.objects.get_or_create(
                    username=admin_data['username'],
                    defaults={
                        'email': admin_data['email'],
                        'company': company,
                        'first_name': admin_data.get('first_name', 'Administrador'),
                        'last_name': admin_data.get('last_name', 'Sistema'),
                        'avatar': admin_data.get('avatar'),
                        'is_active': True,
                        'can_access': True,
                        'must_change_password': True,
                        'is_staff': True,
                        'is_superuser': True
                    }
                )
                
                if created:
                    user.set_password(admin_data['password'])
                    user.save()
                
                # 5. Asignar rol de administrador
                UserRole.objects.get_or_create(user=user, role=admin_role)
                
                # 6. Marcar setup como completado
                setup.is_completed = True
                setup.completed_at = timezone.now()
                setup.note = f'Setup completado el {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
                setup.save()
                
                # Preparar información de roles creados
                roles_info = []
                for role in created_roles:
                    roles_info.append({
                        'id': role.id,
                        'key': role.key,
                        'name': role.name,
                        'is_system': role.is_system,
                        'can_access': role.can_access
                    })
                
                # Resumen del setup
                setup_summary = {
                    'total_roles_created': len(created_roles),
                    'system_roles': [r.key for r in created_roles if r.is_system],
                    'setup_timestamp': timezone.now().isoformat(),
                    'company_configured': company.name,
                    'admin_username': user.username
                }
                
                return Response({
                    'message': 'Setup del sistema completado exitosamente',
                    'company': CompanySerializer(company).data,
                    'admin_user': UserSerializer(user).data,
                    'setup': SystemSetupSerializer(setup).data,
                    'roles_created': roles_info,
                    'setup_summary': setup_summary
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'error': f'Error durante el setup: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=["1. System Setup"],
    summary="Estado del Sistema",
    description="Información del estado actual del sistema"
)
class SystemStatusAPIView(APIView):
    """Vista para obtener estado general del sistema"""
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        summary="Obtener estado del sistema",
        description="Retorna información general del estado del sistema y estadísticas",
        responses={
            200: {
                'description': 'Estado del sistema',
                'type': 'object',
                'properties': {
                    'system_setup': {
                        'type': 'object',
                        'properties': {
                            'is_completed': {'type': 'boolean'},
                            'completed_at': {'type': 'string', 'format': 'date-time'},
                            'status': {'type': 'string'},
                            'status_message': {'type': 'string'},
                            'setup_duration': {'type': 'string'}
                        }
                    },
                    'statistics': {
                        'type': 'object',
                        'properties': {
                            'companies': {'type': 'integer'},
                            'users': {'type': 'integer'},
                            'roles': {'type': 'integer'},
                            'active_users': {'type': 'integer'},
                            'total_user_roles': {'type': 'integer'}
                        }
                    },
                    'status': {'type': 'string', 'enum': ['operational', 'setup_required']},
                    'system_info': {
                        'type': 'object',
                        'properties': {
                            'django_version': {'type': 'string'},
                            'drf_version': {'type': 'string'},
                            'database_engine': {'type': 'string'},
                            'redis_available': {'type': 'boolean'}
                        }
                    }
                }
            }
        }
    )
    def get(self, request):
        """Obtener estado del sistema"""
        try:
            from django import get_version
            from rest_framework import VERSION as drf_version
            from django.conf import settings
            import redis
            
            setup = SystemSetup.objects.first()
            companies_count = Company.objects.count()
            users_count = User.objects.count()
            roles_count = Role.objects.count()
            active_users_count = User.objects.filter(is_active=True, can_access=True).count()
            total_user_roles = UserRole.objects.count()
            
            # Verificar Redis
            redis_available = False
            try:
                r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
                r.ping()
                redis_available = True
            except:
                pass
            
            # Información del setup
            setup_info = {}
            if setup:
                setup_data = SystemSetupSerializer(setup).data
                setup_info = {
                    'is_completed': setup.is_completed,
                    'completed_at': setup.completed_at,
                    'status': setup_data.get('status'),
                    'status_message': setup_data.get('status_message'),
                    'setup_duration': setup_data.get('setup_duration')
                }
            else:
                setup_info = {
                    'is_completed': False,
                    'completed_at': None,
                    'status': 'pending',
                    'status_message': 'Sistema pendiente de configuración',
                    'setup_duration': None
                }
            
            return Response({
                'system_setup': setup_info,
                'statistics': {
                    'companies': companies_count,
                    'users': users_count,
                    'roles': roles_count,
                    'active_users': active_users_count,
                    'total_user_roles': total_user_roles
                },
                'status': 'operational' if setup and setup.is_completed else 'setup_required',
                'system_info': {
                    'django_version': get_version(),
                    'drf_version': drf_version,
                    'database_engine': settings.DATABASES['default']['ENGINE'],
                    'redis_available': redis_available
                }
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
