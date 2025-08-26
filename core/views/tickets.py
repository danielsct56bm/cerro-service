"""
Vistas para gestión de tickets y turnos
"""
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse
from django.utils import timezone
import json

from ..models import Ticket, TicketTurn, TicketCategory, TicketSubcategory, TicketTemplate, TicketTemplateField, WorkSession
from ..serializers import TicketSerializer, TicketTurnSerializer


@extend_schema_view(
    list=extend_schema(summary="Listar tickets", description="Obtiene la lista de tickets del sistema", tags=["5. Kiosks & Tickets"]),
    create=extend_schema(summary="Crear ticket", description="Crea un nuevo ticket", tags=["5. Kiosks & Tickets"]),
    retrieve=extend_schema(summary="Obtener ticket", description="Obtiene los detalles de un ticket específico", tags=["5. Kiosks & Tickets"]),
    update=extend_schema(summary="Actualizar ticket", description="Actualiza los datos de un ticket", tags=["5. Kiosks & Tickets"]),
    destroy=extend_schema(summary="Eliminar ticket", description="Elimina un ticket del sistema", tags=["5. Kiosks & Tickets"])
)
class TicketViewSet(viewsets.ModelViewSet):
    """ViewSet para Ticket"""
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['company', 'status', 'priority', 'category', 'assigned_to']
    search_fields = ['code', 'requester__username', 'assigned_to__username']
    ordering_fields = ['created_at', 'updated_at', 'priority', 'status']
    
    def get_view_name(self):
        return "Tickets"
    
    def get_view_description(self, html=False):
        return "Gestión de tickets de soporte"


@extend_schema_view(
    list=extend_schema(summary="Listar turnos", description="Obtiene la lista de turnos de tickets", tags=["5. Kiosks & Tickets"]),
    create=extend_schema(summary="Crear turno", description="Crea un nuevo turno", tags=["5. Kiosks & Tickets"]),
    retrieve=extend_schema(summary="Obtener turno", description="Obtiene los detalles de un turno específico", tags=["5. Kiosks & Tickets"]),
    update=extend_schema(summary="Actualizar turno", description="Actualiza los datos de un turno", tags=["5. Kiosks & Tickets"]),
    destroy=extend_schema(summary="Eliminar turno", description="Elimina un turno del sistema", tags=["5. Kiosks & Tickets"])
)
class TicketTurnViewSet(viewsets.ModelViewSet):
    """ViewSet para TicketTurn"""
    queryset = TicketTurn.objects.all()
    serializer_class = TicketTurnSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['ticket', 'is_called']
    search_fields = ['ticket__code', 'display_message']
    ordering_fields = ['created_at', 'turn_number', 'called_at']
    
    def get_view_name(self):
        return "Ticket Turns"
    
    def get_view_description(self, html=False):
        return "Gestión de turnos de tickets"


@extend_schema(tags=["5. Kiosks & Tickets"], summary="Obtener Plantillas de Tickets", description="Obtiene las plantillas de tickets disponibles para el kiosko")
class KioskTemplatesAPIView(APIView):
    """Vista para obtener plantillas de tickets para kiosko"""
    permission_classes = []  # Sin autenticación para kiosko
    
    @extend_schema(
        responses={
            200: {
                'description': 'Plantillas de tickets disponibles',
                'type': 'object',
                'properties': {
                    'categories': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'name': {'type': 'string'},
                                'icon': {'type': 'string'},
                                'color': {'type': 'string'},
                                'subcategories': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {'type': 'integer'},
                                            'name': {'type': 'string'},
                                            'icon': {'type': 'string'},
                                            'color': {'type': 'string'},
                                            'template': {
                                                'type': 'object',
                                                'properties': {
                                                    'id': {'type': 'integer'},
                                                    'name': {'type': 'string'},
                                                    'fields': {
                                                        'type': 'array',
                                                        'items': {
                                                            'type': 'object',
                                                            'properties': {
                                                                'id': {'type': 'integer'},
                                                                'name': {'type': 'string'},
                                                                'label': {'type': 'string'},
                                                                'field_type': {'type': 'string'},
                                                                'required': {'type': 'boolean'},
                                                                'options': {'type': 'string'}
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    )
    def get(self, request):
        """Obtener plantillas de tickets para kiosko"""
        from ..models import Company
        
        # Obtener empresa desde parámetro o usar la primera disponible
        company_id = request.GET.get('company_id')
        
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                return Response({
                    'error': 'Empresa no encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            company = Company.objects.first()
            if not company:
                return Response({
                    'error': 'No hay empresas disponibles'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener categorías activas con sus subcategorías y plantillas
        categories = TicketCategory.objects.filter(
            company=company,
            is_active=True
        ).prefetch_related('subcategories', 'subcategories__template', 'subcategories__template__fields')
        
        categories_data = []
        for category in categories:
            category_data = {
                'id': category.id,
                'name': category.name,
                'icon': category.icon,
                'color': category.color,
                'subcategories': []
            }
            
            for subcategory in category.subcategories.filter(is_active=True):
                subcategory_data = {
                    'id': subcategory.id,
                    'name': subcategory.name,
                    'icon': subcategory.icon,
                    'color': subcategory.color,
                    'template': None
                }
                
                # Obtener plantilla si existe
                if hasattr(subcategory, 'template') and subcategory.template:
                    template = subcategory.template
                    template_data = {
                        'id': template.id,
                        'name': template.name,
                        'fields': []
                    }
                    
                    # Obtener campos de la plantilla
                    fields = template.fields.all().order_by('order_no')
                    for field in fields:
                        field_data = {
                            'id': field.id,
                            'name': field.name,
                            'label': field.label,
                            'field_type': field.field_type,
                            'required': field.required,
                            'options': field.options
                        }
                        template_data['fields'].append(field_data)
                    
                    subcategory_data['template'] = template_data
                
                category_data['subcategories'].append(subcategory_data)
            
            categories_data.append(category_data)
        
        return Response({
            'company': {
                'id': company.id,
                'name': company.name
            },
            'categories': categories_data
        }, status=status.HTTP_200_OK)


@extend_schema(tags=["5. Kiosks & Tickets"], summary="Generar Orden de Ticket", description="Genera una orden de ticket desde el kiosko")
class GenerateTicketOrderAPIView(APIView):
    """Vista para generar orden de ticket desde kiosko"""
    permission_classes = []  # Sin autenticación para kiosko
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'category_id': {'type': 'integer'},
                    'subcategory_id': {'type': 'integer'},
                    'form_data': {
                        'type': 'object',
                        'description': 'Datos del formulario completado'
                    },
                    'priority': {
                        'type': 'string',
                        'enum': ['low', 'normal', 'high', 'urgent']
                    }
                },
                'required': ['category_id', 'subcategory_id']
            }
        },
        responses={
            201: {
                'description': 'Orden de ticket generada exitosamente',
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'ticket': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'code': {'type': 'string'},
                            'status': {'type': 'string'},
                            'priority': {'type': 'string'},
                            'created_at': {'type': 'string', 'format': 'date-time'}
                        }
                    },
                    'turn': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'turn_number': {'type': 'integer'},
                            'display_message': {'type': 'string'}
                        }
                    }
                }
            },
            400: OpenApiResponse(description="Datos inválidos"),
            404: OpenApiResponse(description="Categoría o subcategoría no encontrada")
        }
    )
    def post(self, request):
        """Generar orden de ticket desde kiosko"""
        from ..models import Company, User
        
        # Obtener datos de la solicitud
        category_id = request.data.get('category_id')
        subcategory_id = request.data.get('subcategory_id')
        form_data = request.data.get('form_data', {})
        priority = request.data.get('priority', 'normal')
        company_id = request.data.get('company_id')
        
        if not category_id or not subcategory_id:
            return Response({
                'error': 'category_id y subcategory_id son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener empresa
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                return Response({
                    'error': 'Empresa no encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            company = Company.objects.first()
            if not company:
                return Response({
                    'error': 'No hay empresas disponibles'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener categoría y subcategoría
        try:
            category = TicketCategory.objects.get(id=category_id, company=company, is_active=True)
            subcategory = TicketSubcategory.objects.get(id=subcategory_id, category=category, is_active=True)
        except (TicketCategory.DoesNotExist, TicketSubcategory.DoesNotExist):
            return Response({
                'error': 'Categoría o subcategoría no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener usuario anónimo o crear uno temporal
        try:
            requester = User.objects.filter(company=company).first()
            if not requester:
                return Response({
                    'error': 'No hay usuarios disponibles en la empresa'
                }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({
                'error': 'Usuario no encontrado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener sesión de trabajo activa
        current_time = timezone.now().time()
        session = WorkSession.objects.filter(
            company=company,
            is_active=True,
            start_time__lte=current_time,
            end_time__gte=current_time
        ).first()
        
        # Crear ticket
        ticket = Ticket.objects.create(
            company=company,
            requester=requester,
            category=category,
            subcategory=subcategory,
            form_data=json.dumps(form_data),
            status='open',
            priority=priority,
            session=session
        )
        
        # Generar turno
        # Obtener el último turno del día para esta categoría
        today = timezone.now().date()
        last_turn = TicketTurn.objects.filter(
            ticket__category=category,
            ticket__created_at__date=today
        ).order_by('-turn_number').first()
        
        turn_number = 1 if not last_turn else last_turn.turn_number + 1
        
        turn = TicketTurn.objects.create(
            ticket=ticket,
            turn_number=turn_number,
            display_message=f"Turno {turn_number:03d} - {category.name}"
        )
        
        return Response({
            'message': 'Orden de ticket generada exitosamente',
            'ticket': {
                'id': ticket.id,
                'code': ticket.code,
                'status': ticket.status,
                'priority': ticket.priority,
                'created_at': ticket.created_at.isoformat()
            },
            'turn': {
                'id': turn.id,
                'turn_number': turn.turn_number,
                'display_message': turn.display_message
            }
        }, status=status.HTTP_201_CREATED)
