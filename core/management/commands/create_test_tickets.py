"""
Comando para crear tickets de prueba
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import json
from datetime import timedelta

from core.models import Company, User, TicketCategory, TicketSubcategory, Ticket


class Command(BaseCommand):
    help = 'Crea tickets de prueba para verificar el panel admin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='ID de la empresa para la cual crear los tickets'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Número de tickets a crear'
        )

    def handle(self, *args, **options):
        company_id = options['company_id']
        count = options['count']
        
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

        # Obtener usuarios de la empresa
        users = User.objects.filter(company=company, is_active=True)
        if not users.exists():
            self.stdout.write(
                self.style.ERROR('No hay usuarios activos en la empresa.')
            )
            return

        # Obtener categorías y subcategorías
        categories = TicketCategory.objects.filter(company=company, is_active=True)
        if not categories.exists():
            self.stdout.write(
                self.style.ERROR('No hay categorías disponibles. Ejecute setup_ticket_templates primero.')
            )
            return

        self.stdout.write(f'Creando {count} tickets de prueba para empresa: {company.name}')
        
        created_tickets = 0
        
        # Estados y prioridades para variar
        statuses = ['open', 'in_progress', 'resolved', 'closed', 'canceled']
        priorities = ['low', 'normal', 'high', 'urgent']
        
        for i in range(count):
            # Seleccionar usuario aleatorio
            requester = users.order_by('?').first()
            
            # Seleccionar categoría aleatoria
            category = categories.order_by('?').first()
            
            # Seleccionar subcategoría si existe
            subcategory = None
            if category.subcategories.exists():
                subcategory = category.subcategories.filter(is_active=True).order_by('?').first()
            
            # Seleccionar estado y prioridad aleatorios
            status = statuses[i % len(statuses)]
            priority = priorities[i % len(priorities)]
            
            # Crear datos de formulario de ejemplo
            form_data = {
                'motivo': f'Motivo de prueba {i+1}',
                'centro_de_costos': f'CC{i+1:03d}',
                'usuario': requester.get_full_name(),
                'fecha_solicitud': timezone.now().strftime('%Y-%m-%d')
            }
            
            # Crear ticket
            ticket = Ticket.objects.create(
                company=company,
                requester=requester,
                category=category,
                subcategory=subcategory,
                form_data=json.dumps(form_data),
                status=status,
                priority=priority
            )
            
            created_tickets += 1
            self.stdout.write(
                f'  ✓ Ticket creado: {ticket.code} - {category.name} - {status}'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Tickets de prueba creados exitosamente:\n'
                f'  - Tickets creados: {created_tickets}\n'
                f'  - Empresa: {company.name}'
            )
        )
