"""
Vistas para gestión de kioskos
"""
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from django.utils import timezone
import secrets
import hashlib

from ..models import Kiosk, KioskRegistrationToken
from ..serializers import KioskSerializer, KioskRegistrationTokenSerializer


@extend_schema_view(
    list=extend_schema(summary="Listar kioskos", description="Obtiene la lista de kioskos registrados", tags=["5. Kiosks & Tickets"]),
    create=extend_schema(summary="Crear kiosko", description="Crea un nuevo kiosko", tags=["5. Kiosks & Tickets"]),
    retrieve=extend_schema(summary="Obtener kiosko", description="Obtiene los detalles de un kiosko específico", tags=["5. Kiosks & Tickets"]),
    update=extend_schema(summary="Actualizar kiosko", description="Actualiza los datos de un kiosko", tags=["5. Kiosks & Tickets"]),
    destroy=extend_schema(summary="Eliminar kiosko", description="Elimina un kiosko del sistema", tags=["5. Kiosks & Tickets"])
)
class KioskViewSet(viewsets.ModelViewSet):
    """ViewSet para Kiosk"""
    queryset = Kiosk.objects.all()
    serializer_class = KioskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['company', 'is_active', 'device_type']
    search_fields = ['name', 'mac_address', 'company__name']
    ordering_fields = ['name', 'created_at', 'last_activity']
    
    def get_view_name(self):
        return "Kiosks"
    
    def get_view_description(self, html=False):
        return "Gestión de kioskos de tickets"


@extend_schema(tags=["5. Kiosks & Tickets"], summary="Generar URL de Registro", description="Genera URL única para registro de kiosko")
class GenerateKioskUrlAPIView(APIView):
    """Vista para generar URL de registro de kiosko"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None
    
    @extend_schema(
        responses={
            200: {
                'description': 'URL de registro generada',
                'type': 'object',
                'properties': {
                    'registration_url': {'type': 'string'},
                    'token': {'type': 'string'},
                    'expires_at': {'type': 'string', 'format': 'date-time'},
                    'user_id': {'type': 'integer'}
                }
            }
        }
    )
    def post(self, request):
        """Generar URL de registro para kiosko"""
        # Generar token único
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Crear token de registro
        registration_token = KioskRegistrationToken.objects.create(
            token_hash=token_hash,
            requester=request.user,
            expires_at=timezone.now() + timezone.timedelta(hours=24)
        )
        
        # Construir URL de registro
        registration_url = f"{request.build_absolute_uri('/')}api/kiosks/register/{token}/"
        
        return Response({
            'registration_url': registration_url,
            'token': token,
            'expires_at': registration_token.expires_at.isoformat(),
            'user_id': request.user.id
        }, status=status.HTTP_200_OK)


@extend_schema(tags=["5. Kiosks & Tickets"], summary="Registro de Kiosko", description="Registra un kiosko usando token de seguridad")
class KioskRegistrationAPIView(APIView):
    """Vista para registro de kiosko"""
    permission_classes = []  # Sin autenticación para registro
    serializer_class = None
    
    @extend_schema(
        responses={
            200: KioskSerializer,
            400: OpenApiResponse(description="Token inválido o expirado"),
            404: OpenApiResponse(description="Token no encontrado")
        }
    )
    def post(self, request, token):
        """Registrar kiosko usando token"""
        # Verificar token
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        try:
            registration_token = KioskRegistrationToken.objects.get(
                token_hash=token_hash,
                is_used=False,
                expires_at__gt=timezone.now()
            )
        except KioskRegistrationToken.DoesNotExist:
            return Response({
                'error': 'Token inválido o expirado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener datos del kiosko
        kiosk_data = request.data
        name = kiosk_data.get('name')
        mac_address = kiosk_data.get('mac_address')
        device_type = kiosk_data.get('device_type', 'web')
        
        if not name or not mac_address:
            return Response({
                'error': 'Nombre y dirección MAC son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si el kiosko ya existe
        existing_kiosk = Kiosk.objects.filter(mac_address=mac_address).first()
        if existing_kiosk:
            # Actualizar kiosko existente
            existing_kiosk.name = name
            existing_kiosk.device_type = device_type
            existing_kiosk.last_activity = timezone.now()
            existing_kiosk.save()
            
            # Marcar token como usado
            registration_token.is_used = True
            registration_token.used_at = timezone.now()
            registration_token.save()
            
            return Response({
                'message': 'Kiosko actualizado exitosamente',
                'kiosk': KioskSerializer(existing_kiosk).data,
                'websocket_url': f"ws://{request.get_host()}/ws/kiosk/{existing_kiosk.id}/"
            }, status=status.HTTP_200_OK)
        
        # Crear nuevo kiosko
        kiosk = Kiosk.objects.create(
            name=name,
            mac_address=mac_address,
            device_type=device_type,
            company=registration_token.requester.company,
            is_active=True
        )
        
        # Marcar token como usado
        registration_token.is_used = True
        registration_token.used_at = timezone.now()
        registration_token.save()
        
        return Response({
            'message': 'Kiosko registrado exitosamente',
            'kiosk': KioskSerializer(kiosk).data,
            'websocket_url': f"ws://{request.get_host()}/ws/kiosk/{kiosk.id}/"
        }, status=status.HTTP_201_CREATED)
