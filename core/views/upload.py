"""
Vistas para upload de archivos
"""
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from ..serializers import FileUploadSerializer


@extend_schema(tags=["Archivos"], summary="Upload de Archivos", description="Subir archivos (logo o avatar)")
class FileUploadAPIView(APIView):
    """Vista para upload de archivos"""
    permission_classes = [permissions.AllowAny]  # Permitir sin autenticación para setup
    
    @extend_schema(
        request=FileUploadSerializer,
        responses={
            200: {
                'description': 'Archivo subido exitosamente',
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'file_url': {'type': 'string'},
                    'file_name': {'type': 'string'},
                    'file_size': {'type': 'integer'},
                    'file_type': {'type': 'string'}
                }
            },
            400: OpenApiResponse(description="Error en la validación del archivo"),
        },
        examples=[
            OpenApiExample(
                'Upload Logo',
                value={
                    'file': '[archivo de imagen]',
                    'type': 'logo'
                },
                request_only=True
            ),
            OpenApiExample(
                'Upload Avatar',
                value={
                    'file': '[archivo de imagen]',
                    'type': 'avatar'
                },
                request_only=True
            )
        ]
    )
    def post(self, request):
        """Subir archivo"""
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_file = serializer.validated_data['file']
            file_type = serializer.validated_data['type']
            
            # Generar nombre único para el archivo
            import os
            from django.utils import timezone
            
            file_extension = os.path.splitext(uploaded_file.name)[1]
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{file_type}_{timestamp}{file_extension}"
            
            # Determinar directorio según tipo
            if file_type == 'logo':
                upload_path = f'company_logos/{unique_filename}'
            else:  # avatar
                upload_path = f'user_avatars/{unique_filename}'
            
            # Guardar archivo
            from django.core.files.storage import default_storage
            file_path = default_storage.save(upload_path, uploaded_file)
            
            return Response({
                'message': f'Archivo {file_type} subido exitosamente',
                'file_url': f'/media/{file_path}',
                'file_name': unique_filename,
                'file_size': uploaded_file.size,
                'file_type': uploaded_file.content_type
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
