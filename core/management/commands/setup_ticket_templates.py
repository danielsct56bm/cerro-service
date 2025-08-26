"""
Comando para cargar plantillas de tickets desde datos mock
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import json

from core.models import Company, TicketTemplate, TicketTemplateField, TicketCategory, TicketSubcategory


class Command(BaseCommand):
    help = 'Carga plantillas de tickets desde datos mock'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='ID de la empresa para la cual cargar las plantillas'
        )

    def handle(self, *args, **options):
        company_id = options['company_id']
        
        if not company_id:
            # Usar la primera empresa disponible
            company = Company.objects.first()
            if not company:
                self.stdout.write(
                    self.style.ERROR('No hay empresas disponibles. Ejecute setup_system primero.')
                )
                return
            company_id = company.id
        
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Empresa con ID {company_id} no encontrada.')
            )
            return

        # Datos mock proporcionados por el usuario
        ticket_data = {
            "ticket_categories": [
                {
                    "name": "CELULARES",
                    "subcategories": [
                        {
                            "name": "RENOVACIÓN DE CELULAR",
                            "form": [
                                {"label": "Número de teléfono", "type": "number"},
                                {"label": "Modelo de celular actual", "type": "select", "options": None},
                                {"label": "Centro de Costos", "type": "text"},
                                {"label": "Tiempo aproximado de permanencia del celular actual", "type": "date"}
                            ]
                        },
                        {
                            "name": "REASIGNACIÓN DE CELULAR",
                            "form": [
                                {"label": "Reaccionado por", "type": "select", "options": None},
                                {"label": "Modelo de celular", "type": "select", "options": None},
                                {"label": "Centro de Costos", "type": "text"}
                            ]
                        },
                        {
                            "name": "CAMBIO  DE PLAN Y CELULAR",
                            "form": [
                                {"label": "Numero de telefono", "type": "text"},
                                {"label": "Modelo de celular", "type": "select", "options": None},
                                {"label": "Centro de Costos", "type": "text"}
                            ]
                        },
                        {
                            "name": "REPOSICIÓN  DE CELULAR",
                            "form": [
                                {"label": "Numero de telefono", "type": "text"},
                                {"label": "FIC del equipo", "type": "text"},
                                {"label": "Centro de Costos", "type": "text"}
                            ]
                        },
                        {
                            "name": "REVISIÓN DE CELULAR",
                            "form": [
                                {"label": "Modelo de celular", "type": "select", "options": None},
                                {"label": "Numero de lineas", "type": "text"},
                                {"label": "Tiempo aproximado de asignacion", "type": "text"},
                                {"label": "Centro de Costos", "type": "text"}
                            ]
                        },
                        {
                            "name": "SOLICITAR  UN NUEVO CELULAR",
                            "form": [
                                {"label": "Motivo", "type": "text"},
                                {"label": "Uso", "type": "text"},
                                {"label": "Centro de Costos", "type": "text"},
                                {
                                    "label": "Modelo de celular",
                                    "type": "select",
                                    "options": {
                                        "APPLE": ["iPhone7", "iPhone11"],
                                        "android": ["Moto e6e", "SamsungS21 5G"]
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "LAPTOPS",
                    "subcategories": [
                        {
                            "name": "COMPRA DE UN NUEVO EQUIPO",
                            "form": [
                                {"label": "¿Será este un dispositivo compartido?", "type": "select", "options": ["SI", "NO"]},
                                {
                                    "label": "Tipos de equipo",
                                    "type": "select",
                                    "options": [
                                        "Standard Laptop – Para uso de labores administrativas (Costo aprox. 1.2K USD)",
                                        "Engineering Laptop – Para uso de programas robustos y alto procesamiento de datos (Costo aprox. 3.2K USD)",
                                        "Rugged Laptop – Para uso en Campo (Costo aprox. 2.6K USD)"
                                    ]
                                },
                                {"label": "Centro de Costos", "type": "text"}
                            ]
                        },
                        {
                            "name": "PRÉSTAMO DE LAPTOP",
                            "form": [
                                {
                                    "label": "Tipos de equipo",
                                    "type": "select",
                                    "options": [
                                        "Standard Laptop – Para uso de labores administrativas.",
                                        "Engineering Laptop – Para uso de programas robustos y alto procesamiento de datos."
                                    ]
                                },
                                {"label": "Centro de Costos", "type": "text"}
                            ]
                        },
                        {
                            "name": "ASIGNACIÓN DE LAPTOPS",
                            "form": [
                                {"label": "Usuario anterior", "type": "select", "options": None},
                                {"label": "Datos del equipo a asignar", "type": "select", "options": ["Service Tag", "FIC", "Modelo"]}
                            ]
                        },
                        {
                            "name": "Reasignación de laptop",
                            "form": [
                                {"label": "Numero de Serie de la laptop", "type": "text"},
                                {"label": "Numero de FIC", "type": "text"},
                                {"label": "Modelo de laptop", "type": "text"},
                                {"label": "Centro de costos", "type": "text"}
                            ]
                        }
                    ]
                },
                {
                    "name": "RADIOS",
                    "subcategories": [
                        {"name": "RADIO PORTATIL NUEVA"},
                        {"name": "REPARACION DE RADIO PORTATIL"},
                        {"name": "REEMPLAZO DE RADIO PORTATL"},
                        {"name": "ACCESORIOS PARA RAdio portatil"},
                        {"name": "Listado de Accesorios Disponibles"},
                        {"name": "Micrófono PTT (Push-to-Talk)"},
                        {"name": "Batería"},
                        {"name": "Antena"},
                        {"name": "Cargador de radio (con fuente de alimentación)"},
                        {"name": "Cargador de auto / Cargador cenicero"},
                        {"name": "Cargador multiple de radios y baterías"},
                        {"name": "Pechera"},
                        {"name": "Canguro / Riñonera"}
                    ]
                },
                {
                    "name": "TABLETS",
                    "subcategories": [
                        {"name": "TABLET ROBADA O PERDIDA"},
                        {"name": "PROBLEAS CON LA TABLET"},
                        {"name": "NUEVA TABLET O REASIGANACION"},
                        {"name": "CONFIGURACION SAM"},
                        {"name": "CONFIGURACION E-FORMS"}
                    ]
                },
                {
                    "name": "TELÉFONOS SATELITALES",
                    "subcategories": [
                        {"name": "NUEVO EQUIPO"}
                    ]
                },
                {
                    "name": "IMPRESORAS",
                    "subcategories": [
                        {"name": "REPOSICIÓN DE SUMINISTRO: TONER, CONTENEDOR DE RESIDUOS, OTROS"},
                        {"name": "FALLAS TECNICAS EN LA IMPRESORA"},
                        {"name": "SOLICITUD DE IMPRESORA PARA UNA NUEVA UBICACION"}
                    ]
                },
                {
                    "name": "TELEPRESENCIAS",
                    "subcategories": []
                },
                {
                    "name": "CÁMARAS",
                    "subcategories": [
                        {"name": "ACCESOS A LAS CAMARAS"}
                    ]
                },
                {
                    "name": "ACCESORIOS",
                    "subcategories": [
                        {"name": "ANDROID CASE"},
                        {"name": "ANDROID SCREEN PROTECTOR"},
                        {"name": "BACKPACK"},
                        {"name": "ENGINNER DOCKING"},
                        {"name": "iPHONE CASE"}
                    ]
                },
                {"name": "ROBIN", "subcategories": []},
                {"name": "DSL", "subcategories": []},
                {"name": "SISTEMA DE TICKET", "subcategories": []},
                {"name": "ENTERPRISE WORKSPACE", "subcategories": []},
                {"name": "FOTOCHECKS", "subcategories": []},
                {"name": "CIBERSEGURIDAD", "subcategories": []}
            ]
        }

        self.stdout.write(f'Cargando plantillas de tickets para empresa: {company.name}')
        
        created_categories = 0
        created_subcategories = 0
        created_templates = 0
        created_fields = 0

        for category_data in ticket_data['ticket_categories']:
            # Crear categoría
            category, created = TicketCategory.objects.get_or_create(
                company=company,
                name=category_data['name'],
                defaults={
                    'description': f'Categoría para {category_data["name"]}',
                    'icon': 'category',
                    'color': '#1976d2',
                    'is_active': True
                }
            )
            
            if created:
                created_categories += 1
                self.stdout.write(f'  ✓ Categoría creada: {category.name}')

            # Crear subcategorías
            for subcategory_data in category_data.get('subcategories', []):
                subcategory, created = TicketSubcategory.objects.get_or_create(
                    category=category,
                    name=subcategory_data['name'],
                    defaults={
                        'icon': 'subcategory',
                        'color': '#42a5f5',
                        'is_active': True
                    }
                )
                
                if created:
                    created_subcategories += 1
                    self.stdout.write(f'    ✓ Subcategoría creada: {subcategory.name}')

                # Crear plantilla si tiene formulario
                if 'form' in subcategory_data and subcategory_data['form']:
                    template, created = TicketTemplate.objects.get_or_create(
                        company=company,
                        name=f"{category.name} - {subcategory.name}",
                        defaults={
                            'theme': 'default',
                            'settings': json.dumps({
                                'category_id': category.id,
                                'subcategory_id': subcategory.id
                            }),
                            'is_active': True
                        }
                    )
                    
                    if created:
                        created_templates += 1
                        self.stdout.write(f'      ✓ Plantilla creada: {template.name}')

                    # Crear campos del formulario
                    for i, field_data in enumerate(subcategory_data['form']):
                        field_type = field_data.get('type', 'text')
                        if field_type is None:
                            field_type = 'text'
                        
                        options = field_data.get('options')
                        options_json = json.dumps(options) if options else ''
                        
                        field, created = TicketTemplateField.objects.get_or_create(
                            template=template,
                            name=field_data['label'].lower().replace(' ', '_'),
                            defaults={
                                'label': field_data['label'],
                                'field_type': field_type,
                                'required': True,
                                'options': options_json,
                                'order_no': i
                            }
                        )
                        
                        if created:
                            created_fields += 1
                            self.stdout.write(f'        ✓ Campo creado: {field.label} ({field.field_type})')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Carga completada:\n'
                f'  - Categorías: {created_categories}\n'
                f'  - Subcategorías: {created_subcategories}\n'
                f'  - Plantillas: {created_templates}\n'
                f'  - Campos: {created_fields}'
            )
        )
