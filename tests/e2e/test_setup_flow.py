"""
Tests end-to-end para el flujo completo del setup del sistema
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from core.models import SystemSetup, Company, Role, UserRole

User = get_user_model()


class SetupEndToEndTest(TestCase):
    """Tests end-to-end para el setup del sistema"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = Client()
        self.api_client = APIClient()
        self.setup_check_url = reverse('CPsetup:setup_check')
        self.setup_company_url = reverse('CPsetup:setup_company')
        self.setup_admin_url = reverse('CPsetup:setup_admin')
        self.login_url = reverse('CPlogin:login')
        self.api_setup_url = '/api/setup/'
        self.api_status_url = '/api/system-status/'
    
    def test_complete_setup_flow_web_interface(self):
        """Test E2E: Flujo completo del setup usando interfaz web"""
        # Paso 1: Verificar estado inicial
        response = self.client.get(self.setup_check_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('setup_company', response.url)
        
        # Paso 2: Configurar empresa
        company_data = {
            'company_name': 'Cerro Verde S.A.A.',
            'ruc': '20100000000',
            'email': 'info@cerroverde.com',
            'phone': '+51 1 5950000',
            'address': 'Av. Arequipa 4095, Lima, Perú'
        }
        
        response = self.client.post(self.setup_company_url, company_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn('setup_admin', response.url)
        
        # Verificar empresa creada
        self.assertTrue(Company.objects.filter(name='Cerro Verde S.A.A.').exists())
        company = Company.objects.get(name='Cerro Verde S.A.A.')
        
        # Verificar sesión
        self.assertEqual(self.client.session.get('setup_company_id'), company.id)
        self.assertEqual(self.client.session.get('setup_step'), 'admin')
        
        # Paso 3: Configurar administrador
        admin_data = {
            'username': 'admin',
            'email': 'admin@cerroverde.com',
            'password': 'Admin123!',
            'first_name': 'Administrador',
            'last_name': 'Sistema',
            'title': 'Administrador del Sistema',
            'department': 'IT',
            'location': 'Lima',
            'sap_id': 'SAP001',
            'employee_number': 'EMP001',
            'avatar_type': 'generated'
        }
        
        response = self.client.post(self.setup_admin_url, admin_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Verificar datos creados
        self.assertTrue(User.objects.filter(username='admin').exists())
        self.assertTrue(SystemSetup.objects.filter(is_completed=True).exists())
        
        admin_user = User.objects.get(username='admin')
        self.assertEqual(admin_user.company, company)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.can_access)
        
        # Verificar roles creados
        self.assertEqual(Role.objects.filter(company=company).count(), 3)
        admin_role = Role.objects.get(company=company, key='admin')
        self.assertTrue(UserRole.objects.filter(user=admin_user, role=admin_role).exists())
        
        # Verificar sesión limpiada
        self.assertIsNone(self.client.session.get('setup_company_id'))
        self.assertIsNone(self.client.session.get('setup_step'))
        
        # Paso 4: Verificar que no se puede acceder al setup nuevamente
        response = self.client.get(self.setup_check_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_complete_setup_flow_api(self):
        """Test E2E: Flujo completo del setup usando API"""
        # Paso 1: Verificar estado inicial
        response = self.api_client.get(self.api_status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'setup_required')
        self.assertEqual(response.data['statistics']['companies'], 0)
        self.assertEqual(response.data['statistics']['users'], 0)
        
        # Paso 2: Ejecutar setup completo
        setup_data = {
            'company': {
                'name': 'Cerro Verde S.A.A.',
                'ruc': '20100000000',
                'email': 'info@cerroverde.com',
                'phone': '+51 1 5950000',
                'address': 'Av. Arequipa 4095, Lima, Perú'
            },
            'admin': {
                'username': 'admin',
                'email': 'admin@cerroverde.com',
                'password': 'Admin123!',
                'first_name': 'Administrador',
                'last_name': 'Sistema'
            }
        }
        
        response = self.api_client.post(self.api_setup_url, setup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar respuesta de la API
        self.assertIn('completado exitosamente', response.data['message'])
        self.assertIn('company', response.data)
        self.assertIn('admin_user', response.data)
        self.assertIn('setup', response.data)
        self.assertIn('roles_created', response.data)
        self.assertIn('setup_summary', response.data)
        
        # Verificar datos en la base de datos
        self.assertTrue(Company.objects.filter(name='Cerro Verde S.A.A.').exists())
        self.assertTrue(User.objects.filter(username='admin').exists())
        self.assertTrue(SystemSetup.objects.filter(is_completed=True).exists())
        
        company = Company.objects.get(name='Cerro Verde S.A.A.')
        admin_user = User.objects.get(username='admin')
        
        # Verificar roles y permisos
        self.assertEqual(Role.objects.filter(company=company).count(), 3)
        admin_role = Role.objects.get(company=company, key='admin')
        self.assertTrue(UserRole.objects.filter(user=admin_user, role=admin_role).exists())
        
        # Paso 3: Verificar estado final
        response = self.api_client.get(self.api_status_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'operational')
        self.assertEqual(response.data['statistics']['companies'], 1)
        self.assertEqual(response.data['statistics']['users'], 1)
        self.assertEqual(response.data['statistics']['roles'], 3)
        self.assertEqual(response.data['statistics']['active_users'], 1)
        self.assertEqual(response.data['statistics']['total_user_roles'], 1)
        
        # Paso 4: Verificar que no se puede hacer setup nuevamente
        response = self.api_client.post(self.api_setup_url, setup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ya está configurado', response.data['error'])
    
    def test_setup_with_logo_and_avatar(self):
        """Test E2E: Setup con logo de empresa y avatar de administrador"""
        # Crear archivos simulados
        logo_content = b'fake_logo_content'
        logo_file = SimpleUploadedFile(
            name='logo.png',
            content=logo_content,
            content_type='image/png'
        )
        
        avatar_content = b'fake_avatar_content'
        avatar_file = SimpleUploadedFile(
            name='avatar.jpg',
            content=avatar_content,
            content_type='image/jpeg'
        )
        
        setup_data = {
            'company': {
                'name': 'Cerro Verde S.A.A.',
                'ruc': '20100000000',
                'email': 'info@cerroverde.com',
                'logo': logo_file
            },
            'admin': {
                'username': 'admin',
                'email': 'admin@cerroverde.com',
                'password': 'Admin123!',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'avatar': avatar_file
            }
        }
        
        response = self.api_client.post(self.api_setup_url, setup_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar archivos guardados
        company = Company.objects.get(name='Cerro Verde S.A.A.')
        admin_user = User.objects.get(username='admin')
        
        self.assertIsNotNone(company.logo)
        self.assertTrue(company.logo.name.startswith('company_logos/'))
        
        self.assertIsNotNone(admin_user.avatar)
        self.assertTrue(admin_user.avatar.name.startswith('user_avatars/'))
    
    def test_setup_force_reconfigure(self):
        """Test E2E: Forzar reconfiguración del setup"""
        # Primer setup
        setup_data_1 = {
            'company': {
                'name': 'Primera Empresa',
                'ruc': '20100000000',
                'email': 'info@primera.com'
            },
            'admin': {
                'username': 'admin1',
                'email': 'admin1@primera.com',
                'password': 'Admin123!',
                'first_name': 'Admin',
                'last_name': 'Uno'
            }
        }
        
        response = self.api_client.post(self.api_setup_url, setup_data_1, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar primer setup
        self.assertTrue(Company.objects.filter(name='Primera Empresa').exists())
        self.assertTrue(User.objects.filter(username='admin1').exists())
        
        # Segundo setup con force
        setup_data_2 = {
            'company': {
                'name': 'Segunda Empresa',
                'ruc': '20100000001',
                'email': 'info@segunda.com'
            },
            'admin': {
                'username': 'admin2',
                'email': 'admin2@segunda.com',
                'password': 'Admin123!',
                'first_name': 'Admin',
                'last_name': 'Dos'
            },
            'force': True
        }
        
        response = self.api_client.post(self.api_setup_url, setup_data_2, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar segundo setup
        self.assertTrue(Company.objects.filter(name='Segunda Empresa').exists())
        self.assertTrue(User.objects.filter(username='admin2').exists())
        
        # Verificar que el primer setup fue reemplazado
        self.assertFalse(Company.objects.filter(name='Primera Empresa').exists())
        self.assertFalse(User.objects.filter(username='admin1').exists())
    
    def test_setup_error_handling(self):
        """Test E2E: Manejo de errores durante el setup"""
        # Test con datos inválidos
        invalid_setup_data = {
            'company': {
                'name': '',  # Nombre vacío
                'email': 'invalid_email'  # Email inválido
            },
            'admin': {
                'username': '',  # Username vacío
                'email': 'invalid_email',  # Email inválido
                'password': '123'  # Contraseña muy corta
            }
        }
        
        response = self.api_client.post(self.api_setup_url, invalid_setup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verificar que no se crearon datos
        self.assertEqual(Company.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(SystemSetup.objects.count(), 0)
        
        # Test con datos faltantes
        incomplete_setup_data = {
            'company': {
                'name': 'Cerro Verde S.A.A.'
                # Faltan otros campos requeridos
            }
            # Falta sección admin
        }
        
        response = self.api_client.post(self.api_setup_url, incomplete_setup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verificar que no se crearon datos
        self.assertEqual(Company.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(SystemSetup.objects.count(), 0)
    
    def test_setup_data_integrity(self):
        """Test E2E: Integridad de datos después del setup"""
        setup_data = {
            'company': {
                'name': 'Cerro Verde S.A.A.',
                'ruc': '20100000000',
                'email': 'info@cerroverde.com',
                'phone': '+51 1 5950000',
                'address': 'Av. Arequipa 4095, Lima, Perú'
            },
            'admin': {
                'username': 'admin',
                'email': 'admin@cerroverde.com',
                'password': 'Admin123!',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'title': 'Administrador del Sistema',
                'department': 'IT',
                'location': 'Lima',
                'sap_id': 'SAP001',
                'employee_number': 'EMP001'
            }
        }
        
        response = self.api_client.post(self.api_setup_url, setup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar integridad de datos de la empresa
        company = Company.objects.get(name='Cerro Verde S.A.A.')
        self.assertEqual(company.ruc, '20100000000')
        self.assertEqual(company.email, 'info@cerroverde.com')
        self.assertEqual(company.phone, '+51 1 5950000')
        self.assertEqual(company.address, 'Av. Arequipa 4095, Lima, Perú')
        self.assertTrue(company.active)
        self.assertIsNotNone(company.created_at)
        self.assertIsNotNone(company.updated_at)
        
        # Verificar integridad de datos del administrador
        admin_user = User.objects.get(username='admin')
        self.assertEqual(admin_user.email, 'admin@cerroverde.com')
        self.assertEqual(admin_user.first_name, 'Administrador')
        self.assertEqual(admin_user.last_name, 'Sistema')
        self.assertEqual(admin_user.title, 'Administrador del Sistema')
        self.assertEqual(admin_user.department, 'IT')
        self.assertEqual(admin_user.location, 'Lima')
        self.assertEqual(admin_user.sap_id, 'SAP001')
        self.assertEqual(admin_user.employee_number, 'EMP001')
        self.assertEqual(admin_user.company, company)
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.can_access)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.check_password('Admin123!'))
        
        # Verificar integridad del setup
        setup = SystemSetup.objects.get(is_completed=True)
        self.assertTrue(setup.is_completed)
        self.assertIsNotNone(setup.completed_at)
        self.assertIsNotNone(setup.note)
        
        # Verificar integridad de roles
        roles = Role.objects.filter(company=company)
        self.assertEqual(roles.count(), 3)
        
        role_keys = [role.key for role in roles]
        self.assertIn('admin', role_keys)
        self.assertIn('user', role_keys)
        self.assertIn('technician', role_keys)
        
        for role in roles:
            self.assertTrue(role.is_system)
            self.assertTrue(role.can_access)
            self.assertIsNotNone(role.created_at)
        
        # Verificar integridad de UserRole
        admin_role = Role.objects.get(company=company, key='admin')
        user_role = UserRole.objects.get(user=admin_user, role=admin_role)
        self.assertIsNotNone(user_role)
        
        # Verificar que solo hay una relación UserRole para el admin
        admin_user_roles = UserRole.objects.filter(user=admin_user)
        self.assertEqual(admin_user_roles.count(), 1)
        self.assertEqual(admin_user_roles.first().role.key, 'admin')
