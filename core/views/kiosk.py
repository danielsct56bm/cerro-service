from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import socket
import requests

from core.models import TicketCategory, TicketSubcategory, TicketTemplate, TicketTemplateField, Ticket, Company
from CPdashadmin.views.services import get_system_settings

def kiosk_view(request):
    """Vista principal del kiosko"""
    # Detectar la empresa basada en la IP o configuración
    company = detect_company(request)
    
    if not company:
        return JsonResponse({
            'error': 'No se pudo identificar la empresa'
        }, status=400)
    
    # Obtener configuración del sistema
    settings = get_system_settings(company)
    
    # Verificar modo de mantenimiento
    if settings.get('maintenance_mode', False):
        return render(request, 'kiosk_maintenance.html', {
            'company': company,
            'settings': settings,
            'maintenance_message': settings.get('maintenance_message', 'Sistema en mantenimiento')
        })
    
    # Obtener categorías activas
    categories = TicketCategory.objects.filter(
        company=company,
        is_active=True
    ).order_by('name')
    
    context = {
        'company': company,
        'categories': categories,
        'settings': settings,
    }
    
    return render(request, 'kiosk.html', context)

def detect_company(request):
    """Detectar la empresa basada en la IP del cliente"""
    # Obtener IP del cliente
    client_ip = get_client_ip(request)
    
    # Por ahora, usar la primera empresa disponible
    # En producción, esto debería usar una lógica más sofisticada
    try:
        company = Company.objects.first()
        return company
    except Company.DoesNotExist:
        return None

def get_client_ip(request):
    """Obtener la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@csrf_exempt
@require_http_methods(["GET"])
def kiosk_status(request):
    """Endpoint para verificar el estado del kiosko"""
    company = detect_company(request)
    
    if not company:
        return JsonResponse({
            'maintenance_mode': True,
            'maintenance_message': 'Sistema no disponible'
        })
    
    settings = get_system_settings(company)
    
    return JsonResponse({
        'maintenance_mode': settings.get('maintenance_mode', False),
        'maintenance_message': settings.get('maintenance_message', ''),
        'auto_refresh': settings.get('kiosk_auto_refresh', True),
        'refresh_interval': settings.get('kiosk_refresh_interval', 30),
        'sound_notifications': settings.get('kiosk_sound_notifications', True)
    })

@csrf_exempt
@require_http_methods(["GET"])
def kiosk_categories(request):
    """Endpoint para obtener categorías del kiosko"""
    company = detect_company(request)
    
    if not company:
        return JsonResponse({'error': 'Empresa no encontrada'}, status=400)
    
    categories = TicketCategory.objects.filter(
        company=company,
        is_active=True
    ).values('id', 'name', 'description', 'icon', 'color')
    
    return JsonResponse({
        'categories': list(categories)
    })

@csrf_exempt
@require_http_methods(["GET"])
def kiosk_subcategories(request, category_id):
    """Endpoint para obtener subcategorías de una categoría"""
    company = detect_company(request)
    
    if not company:
        return JsonResponse({'error': 'Empresa no encontrada'}, status=400)
    
    try:
        category = TicketCategory.objects.get(id=category_id, company=company)
        subcategories = TicketSubcategory.objects.filter(
            category=category,
            is_active=True
        ).values('id', 'name', 'description')
        
        return JsonResponse({
            'subcategories': list(subcategories)
        })
    except TicketCategory.DoesNotExist:
        return JsonResponse({'error': 'Categoría no encontrada'}, status=404)

@csrf_exempt
@require_http_methods(["GET"])
def kiosk_template(request, category_id):
    """Endpoint para obtener la plantilla de una categoría"""
    company = detect_company(request)
    
    if not company:
        return JsonResponse({'error': 'Empresa no encontrada'}, status=400)
    
    try:
        category = TicketCategory.objects.get(id=category_id, company=company)
        
        # Buscar plantilla asociada a la categoría
        template = None
        if category.template:
            template = category.template
        else:
            # Buscar plantilla en settings JSON
            templates = TicketTemplate.objects.filter(company=company, is_active=True)
            for t in templates:
                try:
                    settings = json.loads(t.settings)
                    if settings.get('category_id') == category_id:
                        template = t
                        break
                except (json.JSONDecodeError, TypeError):
                    continue
        
        if template:
            fields = TicketTemplateField.objects.filter(
                template=template,
                is_active=True
            ).values('name', 'label', 'type', 'required', 'placeholder', 'icon', 'options')
            
            # Procesar opciones JSON
            for field in fields:
                if field['options']:
                    try:
                        field['options'] = json.loads(field['options'])
                    except (json.JSONDecodeError, TypeError):
                        field['options'] = []
                else:
                    field['options'] = []
            
            return JsonResponse({
                'template_id': template.id,
                'template_name': template.name,
                'fields': list(fields)
            })
        else:
            return JsonResponse({
                'template_id': None,
                'template_name': None,
                'fields': []
            })
            
    except TicketCategory.DoesNotExist:
        return JsonResponse({'error': 'Categoría no encontrada'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
def kiosk_generate_ticket(request):
    """Endpoint para generar un ticket desde el kiosko"""
    company = detect_company(request)
    
    if not company:
        return JsonResponse({'error': 'Empresa no encontrada'}, status=400)
    
    try:
        data = json.loads(request.body)
        
        # Validar datos requeridos
        category_id = data.get('category_id')
        priority = data.get('priority')
        
        if not category_id or not priority:
            return JsonResponse({
                'success': False,
                'message': 'Categoría y prioridad son requeridos'
            }, status=400)
        
        # Obtener categoría
        try:
            category = TicketCategory.objects.get(id=category_id, company=company)
        except TicketCategory.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Categoría no encontrada'
            }, status=404)
        
        # Obtener subcategoría si se proporciona
        subcategory = None
        subcategory_id = data.get('subcategory_id')
        if subcategory_id:
            try:
                subcategory = TicketSubcategory.objects.get(id=subcategory_id, category=category)
            except TicketSubcategory.DoesNotExist:
                pass
        
        # Crear el ticket
        ticket = Ticket.objects.create(
            company=company,
            category=category,
            subcategory=subcategory,
            priority=priority,
            status='open',
            title=f"Ticket {category.name}",
            description=data.get('description', ''),
            created_by=None,  # Anónimo desde kiosko
            created_at=timezone.now()
        )
        
        # Generar número de ticket
        ticket.number = f"T-{ticket.id:04d}"
        ticket.save()
        
        # Procesar campos dinámicos si existen
        dynamic_fields = {}
        for key, value in data.items():
            if key not in ['category_id', 'subcategory_id', 'priority', 'description']:
                dynamic_fields[key] = value
        
        if dynamic_fields:
            ticket.form_data = json.dumps(dynamic_fields)
            ticket.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Ticket generado exitosamente',
            'ticket': {
                'id': ticket.id,
                'number': ticket.number,
                'category': category.name,
                'subcategory': subcategory.name if subcategory else None,
                'priority': ticket.get_priority_display(),
                'status': ticket.get_status_display(),
                'created_at': ticket.created_at.isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Datos JSON inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al generar ticket: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def kiosk_health(request):
    """Endpoint de salud para el kiosko"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })
