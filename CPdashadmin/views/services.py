from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import socket
import requests
from django.views.decorators.csrf import csrf_exempt

from core.models import User, Kiosk, Ticket, Company, Role, TicketCategory, TicketSubcategory, TicketTemplate, TicketTemplateField
from core.serializers import TicketSerializer


@login_required
def ticket_management(request):
    """Gestión de tickets"""
    company = request.user.company
    
    # Obtener parámetros de filtrado
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    category_filter = request.GET.get('category', '')
    page = request.GET.get('page', 1)
    
    # Query base
    tickets = Ticket.objects.filter(company=company).select_related(
        'requester', 'assigned_to', 'category', 'subcategory'
    )
    
    # Aplicar filtros
    if search:
        tickets = tickets.filter(
            Q(code__icontains=search) |
            Q(requester__first_name__icontains=search) |
            Q(requester__last_name__icontains=search) |
            Q(requester__username__icontains=search) |
            Q(category__name__icontains=search) |
            Q(subcategory__name__icontains=search)
        )
    
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    
    if category_filter:
        tickets = tickets.filter(category_id=category_filter)
    
    # Ordenar por fecha de creación (más recientes primero)
    tickets = tickets.order_by('-created_at')
    
    # Paginación
    paginator = Paginator(tickets, 20)  # 20 tickets por página
    tickets_page = paginator.get_page(page)
    
    # Estadísticas
    total_tickets = Ticket.objects.filter(company=company).count()
    open_tickets = Ticket.objects.filter(company=company, status='open').count()
    in_progress_tickets = Ticket.objects.filter(company=company, status='in_progress').count()
    closed_tickets = Ticket.objects.filter(company=company, status='closed').count()
    resolved_tickets = Ticket.objects.filter(company=company, status='resolved').count()
    
    # Categorías para filtro
    categories = TicketCategory.objects.filter(company=company, is_active=True)
    
    context = {
        'tickets': tickets_page,
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'in_progress_tickets': in_progress_tickets,
        'closed_tickets': closed_tickets,
        'resolved_tickets': resolved_tickets,
        'categories': categories,
        'search': search,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'category_filter': category_filter,
    }
    return render(request, 'CPdashadmin/services/tickets/ticket_management.html', context)


@login_required
def ticket_categories_management(request):
    """Gestión de categorías de tickets"""
    company = request.user.company
    
    # Obtener parámetros de filtrado
    search = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    
    # Query base
    categories = TicketCategory.objects.filter(company=company).prefetch_related('subcategories')
    
    # Aplicar filtros
    if search:
        categories = categories.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Ordenar por nombre
    categories = categories.order_by('name')
    
    # Paginación
    paginator = Paginator(categories, 20)
    categories_page = paginator.get_page(page)
    
    # Estadísticas
    total_categories = TicketCategory.objects.filter(company=company).count()
    active_categories = TicketCategory.objects.filter(company=company, is_active=True).count()
    total_subcategories = TicketSubcategory.objects.filter(category__company=company).count()
    total_templates = TicketTemplate.objects.filter(company=company).count()
    
    context = {
        'categories': categories_page,
        'total_categories': total_categories,
        'active_categories': active_categories,
        'total_subcategories': total_subcategories,
        'total_templates': total_templates,
        'search': search,
    }
    return render(request, 'CPdashadmin/services/tickets/categories_management.html', context)


@login_required
def view_ticket_category(request, category_id):
    """Ver detalles de una categoría"""
    company = request.user.company
    
    try:
        category = get_object_or_404(TicketCategory, id=category_id, company=company)
        
        # Obtener subcategorías
        subcategories = TicketSubcategory.objects.filter(category=category, is_active=True)
        
        # Obtener plantillas
        templates = TicketTemplate.objects.filter(company=company, is_active=True)
        
        # Obtener tickets de esta categoría
        tickets = Ticket.objects.filter(category=category).select_related('requester', 'assigned_to').order_by('-created_at')[:10]
        
        # Estadísticas de la categoría
        total_tickets = Ticket.objects.filter(category=category).count()
        open_tickets = Ticket.objects.filter(category=category, status='open').count()
        in_progress_tickets = Ticket.objects.filter(category=category, status='in_progress').count()
        closed_tickets = Ticket.objects.filter(category=category, status='closed').count()
        
        context = {
            'category': category,
            'subcategories': subcategories,
            'templates': templates,
            'tickets': tickets,
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'in_progress_tickets': in_progress_tickets,
            'closed_tickets': closed_tickets,
        }
        return render(request, 'CPdashadmin/services/tickets/view_category.html', context)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener categoría: {str(e)}'
        }, status=400)


@login_required
def edit_ticket_category(request, category_id):
    """Editar una categoría"""
    company = request.user.company
    
    try:
        category = get_object_or_404(TicketCategory, id=category_id, company=company)
        
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                name = data.get('name')
                description = data.get('description', '')
                icon = data.get('icon', 'folder')
                color = data.get('color', '#1976d2')
                is_active = data.get('is_active', True)
                
                if not name:
                    return JsonResponse({
                        'success': False,
                        'message': 'El nombre de la categoría es requerido'
                    }, status=400)
                
                # Verificar si ya existe otra categoría con ese nombre
                if TicketCategory.objects.filter(company=company, name=name).exclude(id=category_id).exists():
                    return JsonResponse({
                        'success': False,
                        'message': 'Ya existe otra categoría con ese nombre'
                    }, status=400)
                
                # Actualizar categoría
                category.name = name
                category.description = description
                category.icon = icon
                category.color = color
                category.is_active = is_active
                category.updated_at = timezone.now()
                category.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Categoría actualizada exitosamente',
                    'category': {
                        'id': category.id,
                        'name': category.name,
                        'description': category.description,
                        'icon': category.icon,
                        'color': category.color,
                        'is_active': category.is_active,
                        'updated_at': category.updated_at.isoformat()
                    }
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error al actualizar categoría: {str(e)}'
                }, status=400)
        
        # GET - Mostrar formulario de edición
        context = {
            'category': category,
        }
        return render(request, 'CPdashadmin/services/tickets/edit_category.html', context)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener categoría: {str(e)}'
        }, status=400)


@login_required
def delete_ticket_category(request, category_id):
    """Eliminar una categoría"""
    company = request.user.company
    
    try:
        category = get_object_or_404(TicketCategory, id=category_id, company=company)
        
        # Verificar si tiene tickets asociados
        tickets_count = Ticket.objects.filter(category=category).count()
        if tickets_count > 0:
            return JsonResponse({
                'success': False,
                'message': f'No se puede eliminar la categoría porque tiene {tickets_count} tickets asociados'
            }, status=400)
        
        # Verificar si tiene subcategorías
        subcategories_count = TicketSubcategory.objects.filter(category=category).count()
        if subcategories_count > 0:
            return JsonResponse({
                'success': False,
                'message': f'No se puede eliminar la categoría porque tiene {subcategories_count} subcategorías asociadas'
            }, status=400)
        
        # Eliminar categoría
        category_name = category.name
        category.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Categoría "{category_name}" eliminada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar categoría: {str(e)}'
        }, status=400)


@login_required
def manage_category_templates(request, category_id):
    """Gestionar plantillas de una categoría"""
    company = request.user.company
    
    try:
        category = get_object_or_404(TicketCategory, id=category_id, company=company)
        
        # Obtener plantillas asociadas a esta categoría
        templates = TicketTemplate.objects.filter(company=company, is_active=True)
        
        # Filtrar plantillas que pertenecen a esta categoría
        category_templates = []
        for template in templates:
            try:
                settings = json.loads(template.settings)
                if settings.get('category_id') == category_id:
                    category_templates.append(template)
            except:
                continue
        
        context = {
            'category': category,
            'templates': category_templates,
            'all_templates': templates,
        }
        return render(request, 'CPdashadmin/services/tickets/manage_templates.html', context)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al gestionar plantillas: {str(e)}'
        }, status=400)


@login_required
def create_ticket_category(request):
    """Crear nueva categoría de tickets"""
    company = request.user.company
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            description = data.get('description', '')
            icon = data.get('icon', 'category')
            color = data.get('color', '#1976d2')
            
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre de la categoría es requerido'
                }, status=400)
            
            # Verificar si ya existe una categoría con ese nombre
            if TicketCategory.objects.filter(company=company, name=name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe una categoría con ese nombre'
                }, status=400)
            
            # Crear categoría
            category = TicketCategory.objects.create(
                company=company,
                name=name,
                description=description,
                icon=icon,
                color=color,
                is_active=True
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Categoría creada exitosamente',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'icon': category.icon,
                    'color': category.color,
                    'is_active': category.is_active,
                    'created_at': category.created_at.isoformat()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al crear categoría: {str(e)}'
            }, status=400)
    
    # GET - Mostrar formulario
    context = {}
    return render(request, 'CPdashadmin/services/tickets/create_category.html', context)


@login_required
def create_ticket_subcategory(request):
    """Crear nueva subcategoría de tickets"""
    company = request.user.company
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            category_id = data.get('category_id')
            name = data.get('name')
            icon = data.get('icon', 'subcategory')
            color = data.get('color', '#42a5f5')
            
            if not category_id or not name:
                return JsonResponse({
                    'success': False,
                    'message': 'La categoría y el nombre son requeridos'
                }, status=400)
            
            # Obtener categoría
            category = get_object_or_404(TicketCategory, id=category_id, company=company)
            
            # Verificar si ya existe una subcategoría con ese nombre en la categoría
            if TicketSubcategory.objects.filter(category=category, name=name).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Ya existe una subcategoría con ese nombre en esta categoría'
                }, status=400)
            
            # Crear subcategoría
            subcategory = TicketSubcategory.objects.create(
                category=category,
                name=name,
                icon=icon,
                color=color,
                is_active=True
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Subcategoría creada exitosamente',
                'subcategory': {
                    'id': subcategory.id,
                    'name': subcategory.name,
                    'icon': subcategory.icon,
                    'color': subcategory.color,
                    'is_active': subcategory.is_active,
                    'category_name': category.name,
                    'created_at': subcategory.created_at.isoformat()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al crear subcategoría: {str(e)}'
            }, status=400)
    
    # GET - Mostrar formulario
    categories = TicketCategory.objects.filter(company=company, is_active=True)
    context = {
        'categories': categories,
    }
    return render(request, 'CPdashadmin/services/tickets/create_subcategory.html', context)


@login_required
def create_ticket_template(request):
    """Crear nueva plantilla de tickets"""
    company = request.user.company
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            category_id = data.get('category_id')
            subcategory_id = data.get('subcategory_id')
            theme = data.get('theme', 'default')
            fields = data.get('fields', [])
            
            if not name or not category_id:
                return JsonResponse({
                    'success': False,
                    'message': 'El nombre y la categoría son requeridos'
                }, status=400)
            
            # Obtener categoría y subcategoría
            category = get_object_or_404(TicketCategory, id=category_id, company=company)
            subcategory = None
            if subcategory_id:
                subcategory = get_object_or_404(TicketSubcategory, id=subcategory_id, category=category)
            
            # Crear plantilla
            template = TicketTemplate.objects.create(
                company=company,
                name=name,
                theme=theme,
                settings=json.dumps({
                    'category_id': category.id,
                    'subcategory_id': subcategory.id if subcategory else None
                }),
                is_active=True
            )
            
            # Crear campos de la plantilla
            for i, field_data in enumerate(fields):
                TicketTemplateField.objects.create(
                    template=template,
                    name=field_data.get('name', f'field_{i}'),
                    label=field_data.get('label', ''),
                    field_type=field_data.get('field_type', 'text'),
                    required=field_data.get('required', False),
                    options=json.dumps(field_data.get('options', [])),
                    order_no=i
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Plantilla creada exitosamente',
                'template': {
                    'id': template.id,
                    'name': template.name,
                    'theme': template.theme,
                    'is_active': template.is_active,
                    'created_at': template.created_at.isoformat()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al crear plantilla: {str(e)}'
            }, status=400)
    
    # GET - Mostrar formulario
    categories = TicketCategory.objects.filter(company=company, is_active=True)
    context = {
        'categories': categories,
    }
    return render(request, 'CPdashadmin/services/tickets/create_template.html', context)


@login_required
def create_ticket(request):
    """Crear nuevo ticket"""
    company = request.user.company
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            category_id = data.get('category_id')
            subcategory_id = data.get('subcategory_id')
            form_data = data.get('form_data', {})
            priority = data.get('priority', 'normal')
            
            # Obtener categoría y subcategoría
            category = get_object_or_404(TicketCategory, id=category_id, company=company, is_active=True)
            subcategory = None
            if subcategory_id:
                subcategory = get_object_or_404(TicketSubcategory, id=subcategory_id, category=category, is_active=True)
            
            # Crear ticket
            ticket = Ticket.objects.create(
                company=company,
                requester=request.user,
                category=category,
                subcategory=subcategory,
                form_data=json.dumps(form_data),
                status='open',
                priority=priority
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Ticket creado exitosamente',
                'ticket': {
                    'id': ticket.id,
                    'code': ticket.code,
                    'status': ticket.status,
                    'priority': ticket.priority,
                    'created_at': ticket.created_at.isoformat()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al crear ticket: {str(e)}'
            }, status=400)
    
    # GET - Mostrar formulario
    categories = TicketCategory.objects.filter(company=company, is_active=True)
    
    context = {
        'categories': categories,
    }
    return render(request, 'CPdashadmin/services/tickets/create_ticket.html', context)


@login_required
def get_subcategories(request, category_id):
    """Obtener subcategorías de una categoría"""
    company = request.user.company
    
    try:
        category = get_object_or_404(TicketCategory, id=category_id, company=company, is_active=True)
        subcategories = TicketSubcategory.objects.filter(category=category, is_active=True)
        
        subcategories_data = []
        for subcategory in subcategories:
            subcategory_data = {
                'id': subcategory.id,
                'name': subcategory.name,
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
            
            subcategories_data.append(subcategory_data)
        
        return JsonResponse({
            'success': True,
            'subcategories': subcategories_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener subcategorías: {str(e)}'
        }, status=400)


@login_required
def kiosk_management(request):
    """Gestión de kiosks"""
    kiosks = Kiosk.objects.filter(company=request.user.company, is_active=True).all()
    
    context = {
        'kiosks': kiosks,
    }
    return render(request, 'CPdashadmin/services/kiosks/kiosk_management.html', context)


@login_required
def display_management(request):
    """Gestión de displays"""
    # Placeholder - implementar cuando se tenga el modelo Display
    displays = []
    
    context = {
        'displays': displays,
    }
    return render(request, 'CPdashadmin/services/displays/display_management.html', context)


@login_required
def system_settings(request):
    """Configuración del sistema"""
    company = request.user.company
    
    # Obtener configuración actual del sistema
    settings = get_system_settings(company)
    
    context = {
        'company': company,
        'settings': settings,
    }
    return render(request, 'CPdashadmin/settings/system_settings.html', context)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def save_network_settings(request):
    """Guardar configuración de red"""
    try:
        data = json.loads(request.body)
        company = request.user.company
        
        # Guardar configuración en la base de datos o archivo de configuración
        settings = get_system_settings(company)
        settings.update({
            'local_ip': data.get('local_ip', ''),
            'public_ip': data.get('public_ip', ''),
            'port': data.get('port', '8000'),
            'detection_mode': data.get('detection_mode', 'auto'),
            'last_updated': timezone.now().isoformat()
        })
        
        save_system_settings(company, settings)
        
        return JsonResponse({
            'success': True,
            'message': 'Configuración de red guardada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar configuración: {str(e)}'
        }, status=400)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def save_kiosk_settings(request):
    """Guardar configuración de kioskos"""
    try:
        data = json.loads(request.body)
        company = request.user.company
        
        settings = get_system_settings(company)
        settings.update({
            'kiosk_auto_refresh': data.get('kiosk_auto_refresh', False),
            'kiosk_refresh_interval': data.get('kiosk_refresh_interval', '30'),
            'kiosk_sound_notifications': data.get('kiosk_sound_notifications', False),
            'kiosk_welcome_message': data.get('kiosk_welcome_message', ''),
            'last_updated': timezone.now().isoformat()
        })
        
        save_system_settings(company, settings)
        
        return JsonResponse({
            'success': True,
            'message': 'Configuración de kioskos guardada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar configuración: {str(e)}'
        }, status=400)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def save_general_settings(request):
    """Guardar configuración general"""
    try:
        data = json.loads(request.body)
        company = request.user.company
        
        settings = get_system_settings(company)
        settings.update({
            'maintenance_mode': data.get('maintenance_mode', False),
            'maintenance_message': data.get('maintenance_message', ''),
            'last_updated': timezone.now().isoformat()
        })
        
        save_system_settings(company, settings)
        
        return JsonResponse({
            'success': True,
            'message': 'Configuración general guardada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al guardar configuración: {str(e)}'
        }, status=400)

@login_required
def detect_local_ip(request):
    """Detectar IP local del servidor"""
    try:
        # Obtener IP local del servidor
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Verificar si es una IP válida
        if local_ip and local_ip != '127.0.0.1':
            return JsonResponse({
                'success': True,
                'local_ip': f'{local_ip}:8000'
            })
        else:
            # Intentar obtener IP desde una conexión externa
            try:
                response = requests.get('https://api.ipify.org', timeout=5)
                if response.status_code == 200:
                    return JsonResponse({
                        'success': True,
                        'local_ip': f'{response.text}:8000'
                    })
            except:
                pass
            
            return JsonResponse({
                'success': False,
                'message': 'No se pudo detectar la IP local'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al detectar IP: {str(e)}'
        }, status=400)

def get_system_settings(company):
    """Obtener configuración del sistema para una empresa"""
    # Por ahora, usar configuración por defecto
    # En producción, esto debería leer desde la base de datos o archivo de configuración
    return {
        'local_ip': '',
        'public_ip': '',
        'port': '8000',
        'detection_mode': 'auto',
        'kiosk_auto_refresh': True,
        'kiosk_refresh_interval': '30',
        'kiosk_sound_notifications': True,
        'kiosk_welcome_message': 'Bienvenido al sistema de tickets',
        'maintenance_mode': False,
        'maintenance_message': 'Sistema en mantenimiento. Volveremos pronto.',
        'installation_date': timezone.now().isoformat(),
        'last_check': timezone.now().isoformat(),
        'active_kiosks': Kiosk.objects.filter(company=company, is_active=True).count(),
        'tickets_today': Ticket.objects.filter(
            company=company, 
            created_at__date=timezone.now().date()
        ).count(),
        'last_updated': timezone.now().isoformat()
    }

def save_system_settings(company, settings):
    """Guardar configuración del sistema para una empresa"""
    # Por ahora, solo actualizar el diccionario en memoria
    # En producción, esto debería guardar en la base de datos o archivo de configuración
    settings['last_updated'] = timezone.now().isoformat()
    return True


@login_required
def reports(request):
    """Reportes y estadísticas"""
    # Estadísticas para reportes - solo de la empresa actual
    total_users = User.objects.filter(company=request.user.company, is_active=True).count()
    total_kiosks = Kiosk.objects.filter(company=request.user.company, is_active=True).count()
    total_tickets = Ticket.objects.filter(company=request.user.company).count()
    
    # Usuarios por rol - solo de la empresa actual
    users_by_role = Role.objects.filter(company=request.user.company).annotate(user_count=Count('userrole')).values('name', 'user_count')
    
    # Tickets por estado - solo de la empresa actual
    tickets_by_status = Ticket.objects.filter(company=request.user.company).values('status').annotate(count=Count('id'))
    
    context = {
        'total_users': total_users,
        'total_kiosks': total_kiosks,
        'total_tickets': total_tickets,
        'users_by_role': list(users_by_role),
        'tickets_by_status': list(tickets_by_status),
    }
    return render(request, 'CPdashadmin/reports/reports.html', context)
