"""
Comando para el setup inicial del sistema
Crea la primera empresa, roles base y usuario administrador
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from core.models import SystemSetup, Company, Role, UserRole

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup inicial del sistema: empresa, roles y usuario admin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company-name',
            type=str,
            default='Mi Empresa',
            help='Nombre de la empresa principal'
        )
        parser.add_argument(
            '--company-ruc',
            type=str,
            default='',
            help='RUC de la empresa'
        )
        parser.add_argument(
            '--admin-username',
            type=str,
            default='admin',
            help='Username del usuario administrador'
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            default='admin@empresa.com',
            help='Email del usuario administrador'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='Admin123!',
            help='Contraseña del usuario administrador'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar setup aunque ya esté completado'
        )

    def handle(self, *args, **options):
        # Verificar si ya existe setup
        if SystemSetup.objects.filter(is_completed=True).exists() and not options['force']:
            self.stdout.write(
                self.style.WARNING('El sistema ya está configurado. Usa --force para reconfigurar.')
            )
            return

        try:
            with transaction.atomic():
                # 1. Crear o actualizar SystemSetup
                setup, created = SystemSetup.objects.get_or_create(
                    id=1,
                    defaults={'is_completed': False}
                )
                
                if created:
                    self.stdout.write('✓ SystemSetup creado')
                else:
                    self.stdout.write('✓ SystemSetup existente encontrado')

                # 2. Crear empresa principal
                company, created = Company.objects.get_or_create(
                    name=options['company_name'],
                    defaults={
                        'ruc': options['company_ruc'],
                        'email': f'info@{options["company_name"].lower().replace(" ", "")}.com',
                        'active': True
                    }
                )
                
                if created:
                    self.stdout.write(f'✓ Empresa "{company.name}" creada')
                else:
                    self.stdout.write(f'✓ Empresa "{company.name}" existente encontrada')

                # 3. Crear roles base del sistema
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
                    
                    if created:
                        self.stdout.write(f'✓ Rol "{role.name}" creado')
                    else:
                        self.stdout.write(f'✓ Rol "{role.name}" existente encontrado')

                # 4. Crear usuario administrador
                admin_role = next(r for r in created_roles if r.key == 'admin')
                
                user, created = User.objects.get_or_create(
                    username=options['admin_username'],
                    defaults={
                        'email': options['admin_email'],
                        'company': company,
                        'first_name': 'Administrador',
                        'last_name': 'Sistema',
                        'is_active': True,
                        'can_access': True,
                        'must_change_password': True,
                        'is_staff': True,
                        'is_superuser': True
                    }
                )
                
                if created:
                    user.set_password(options['admin_password'])
                    user.save()
                    self.stdout.write(f'✓ Usuario admin "{user.username}" creado')
                else:
                    self.stdout.write(f'✓ Usuario admin "{user.username}" existente encontrado')

                # 5. Asignar rol de administrador
                user_role, created = UserRole.objects.get_or_create(
                    user=user,
                    role=admin_role
                )
                
                if created:
                    self.stdout.write(f'✓ Rol de administrador asignado a {user.username}')
                else:
                    self.stdout.write(f'✓ Rol de administrador ya asignado a {user.username}')

                # 6. Marcar setup como completado
                setup.is_completed = True
                setup.completed_at = timezone.now()
                setup.note = f'Setup completado el {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'
                setup.save()
                
                self.stdout.write('✓ Setup del sistema marcado como completado')

                # 7. Resumen final
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n🎉 Setup del sistema completado exitosamente!\n'
                        f'📋 Empresa: {company.name}\n'
                        f'👤 Usuario Admin: {user.username}\n'
                        f'🔑 Contraseña: {options["admin_password"]}\n'
                        f'🔗 Panel Admin: /admin/\n'
                        f'⚠️  IMPORTANTE: Cambia la contraseña en el primer login'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante el setup: {str(e)}')
            )
            raise
