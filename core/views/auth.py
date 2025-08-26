"""
Vistas de autenticación y gestión de usuarios
"""
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import AuthLoginAudit
from ..serializers import (
    LoginSerializer, UserProfileSerializer, ChangePasswordSerializer, 
    RefreshSessionSerializer
)

User = get_user_model()



class LoginAPIView(APIView):
    """Vista para login de usuarios"""
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        request=LoginSerializer,
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(description="Credenciales inválidas"),
        },
        examples=[
            OpenApiExample(
                'Login Exitoso',
                value={
                    'username': 'admin',
                    'password': 'password123'
                },
                request_only=True
            )
        ]
    )
    def post(self, request):
        """Login de usuario"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Actualizar último login
            user.last_login = timezone.now()
            user.save()
            
            # Registrar auditoría de login exitoso
            AuthLoginAudit.objects.create(
                user=user,
                success=True,
                ip=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Login del usuario
            from django.contrib.auth import login
            login(request, user)
            
            return Response({
                'message': 'Login exitoso',
                'user': UserProfileSerializer(user, context={'request': request}).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LogoutAPIView(APIView):
    """Vista para logout de usuarios"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None
    

    def post(self, request):
        """Logout de usuario"""
        # Registrar auditoría de logout
        AuthLoginAudit.objects.create(
            user=request.user,
            success=True,
            ip=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            note="Logout exitoso"
        )
        
        # Logout del usuario
        from django.contrib.auth import logout
        logout(request)
        
        return Response({
            'message': 'Logout exitoso'
        }, status=status.HTTP_200_OK)



class UserProfileAPIView(APIView):
    """Vista para obtener perfil del usuario autenticado"""
    permission_classes = [permissions.IsAuthenticated]
    

    def get(self, request):
        """Obtener perfil del usuario autenticado"""
        return Response(
            UserProfileSerializer(request.user, context={'request': request}).data,
            status=status.HTTP_200_OK
        )



class ChangePasswordAPIView(APIView):
    """Vista para cambiar contraseña"""
    permission_classes = [permissions.IsAuthenticated]
    

    def post(self, request):
        """Cambiar contraseña del usuario"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            new_password = serializer.validated_data['new_password']
            
            # Cambiar contraseña
            user.set_password(new_password)
            user.must_change_password = False
            user.save()
            
            return Response({
                'message': 'Contraseña cambiada exitosamente'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class RefreshSessionAPIView(APIView):
    """Vista para refrescar sesión de usuario"""
    permission_classes = [permissions.IsAuthenticated]
    

    def post(self, request):
        """Refrescar sesión del usuario"""
        serializer = RefreshSessionSerializer(data={}, context={'request': request})
        if serializer.is_valid():
            user = request.user
            
            # Actualizar último login (actividad)
            user.last_login = timezone.now()
            user.save()
            
            # Registrar auditoría de refresh
            AuthLoginAudit.objects.create(
                user=user,
                success=True,
                ip=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                note="Sesión refrescada"
            )
            
            return Response({
                'message': 'Sesión refrescada exitosamente',
                'user': UserProfileSerializer(user, context={'request': request}).data,
                'session_refreshed_at': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
