"""
Comando para configurar sesiones de trabajo por defecto
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import time

from core.models import Company, WorkSession


class Command(BaseCommand):
    help = 'Configura sesiones de trabajo por defecto para las empresas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-id',
            type=int,
            help='ID de la empresa para la cual configurar las sesiones'
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

        # Sesiones de trabajo por defecto
        sessions_data = [
            {
                'name': 'Mañana',
                'start_time': time(8, 0),  # 8:00 AM
                'end_time': time(12, 0),   # 12:00 PM
            },
            {
                'name': 'Tarde',
                'start_time': time(13, 0), # 1:00 PM
                'end_time': time(17, 0),   # 5:00 PM
            },
            {
                'name': 'Noche',
                'start_time': time(18, 0), # 6:00 PM
                'end_time': time(22, 0),   # 10:00 PM
            },
            {
                'name': '24/7',
                'start_time': time(0, 0),  # 12:00 AM
                'end_time': time(23, 59),  # 11:59 PM
            }
        ]

        self.stdout.write(f'Configurando sesiones de trabajo para empresa: {company.name}')
        
        created_sessions = 0
        
        for session_data in sessions_data:
            session, created = WorkSession.objects.get_or_create(
                company=company,
                name=session_data['name'],
                defaults={
                    'start_time': session_data['start_time'],
                    'end_time': session_data['end_time'],
                    'is_active': True
                }
            )
            
            if created:
                created_sessions += 1
                self.stdout.write(
                    f'  ✓ Sesión creada: {session.name} ({session.start_time} - {session.end_time})'
                )
            else:
                self.stdout.write(
                    f'  - Sesión existente: {session.name} ({session.start_time} - {session.end_time})'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Configuración completada:\n'
                f'  - Sesiones configuradas: {created_sessions}'
            )
        )
