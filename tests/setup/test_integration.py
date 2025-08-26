"""
Tests de integración para el flujo completo del setup del sistema
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from core.models import SystemSetup, Company, Role, UserRole

User = get_user_model()


class SetupIntegrationTest(TestCase):
    """Tests de integración para el setup"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = Client()
        self.api_client = APIClient()
        self.setup_company_url = reverse('CPsetup:setup_company')
        self.setup_admin_url = reverse('CPsetup:setup_admin')
        self.setup_check_url = reverse('CPsetup:setup_check')
        self.login_url = reverse('CPlogin:login')
        self.api_setup_url = '/api/setup/'
    
    def test_setup_creates_base_roles(self):
        """Test: Verificar que el setup crea los roles base correctos"""
        setup_data = {
            'company': {
                'name': 'Cerro Verde S.A.A.',
                'ruc': '20100000000',
                'email': 'info@cerroverde.com'
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
        
        company = Company.objects.get(name='Cerro Verde S.A.A.')
        
        # Verificar que se crearon los 3 roles base
        roles = Role.objects.filter(company=company)
        self.assertEqual(roles.count(), 3)
        
        # Verificar nombres y claves de roles
        role_keys = [role.key for role in roles]
        role_names = [role.name for role in roles]
        
        self.assertIn('admin', role_keys)
        self.assertIn('user', role_keys)
        self.assertIn('technician', role_keys)
        
        self.assertIn('Administrador', role_names)
        self.assertIn('Usuario', role_names)
        self.assertIn('Técnico', role_names)
        
        # Verificar que todos son roles del sistema
        for role in roles:
            self.assertTrue(role.is_system)
            self.assertTrue(role.can_access)
    
    def test_setup_assigns_admin_role_correctly(self):
        """Test: Verificar que el setup asigna correctamente el rol de administrador"""
        setup_data = {
            'company': {
                'name': 'Cerro Verde S.A.A.',
                'ruc': '20100000000',
                'email': 'info@cerroverde.com'
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
        
        # Verificar que el admin tiene el rol correcto
        admin_user = User.objects.get(username='admin')
        admin_role = Role.objects.get(company=admin_user.company, key='admin')
        
        user_role = UserRole.objects.get(user=admin_user, role=admin_role)
        self.assertIsNotNone(user_role)
        
        # Verificar que solo tiene el rol de admin (no otros roles)
        user_roles = UserRole.objects.filter(user=admin_user)
        self.assertEqual(user_roles.count(), 1)
        self.assertEqual(user_roles.first().role.key, 'admin')
    
    def test_setup_only_once_restriction(self):
        """Test: Verificar que solo se puede hacer setup una vez"""
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
        
        response_1 = self.api_client.post(self.api_setup_url, setup_data_1, format='json')
        self.assertEqual(response_1.status_code, status.HTTP_201_CREATED)
        
        # Intentar segundo setup sin force
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
            }
        }
        
        response_2 = self.api_client.post(self.api_setup_url, setup_data_2, format='json')
        self.assertEqual(response_2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ya está configurado', response_2.data['error'])
        
        # Verificar que solo existe la primera empresa
        self.assertEqual(Company.objects.count(), 1)
        self.assertTrue(Company.objects.filter(name='Primera Empresa').exists())
        self.assertFalse(Company.objects.filter(name='Segunda Empresa').exists())
    
    def test_setup_complete_flow_with_api(self):
        """Test: Flujo completo del setup usando API"""
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
        
        # Verificar que se crearon todos los datos necesarios
        self.assertTrue(Company.objects.filter(name='Cerro Verde S.A.A.').exists())
        self.assertTrue(User.objects.filter(username='admin').exists())
        self.assertTrue(SystemSetup.objects.filter(is_completed=True).exists())
        
        # Verificar roles base creados
        company = Company.objects.get(name='Cerro Verde S.A.A.')
        self.assertEqual(Role.objects.filter(company=company).count(), 3)
        
        # Verificar rol asignado al admin
        admin_user = User.objects.get(username='admin')
        admin_role = Role.objects.get(company=company, key='admin')
        self.assertTrue(UserRole.objects.filter(user=admin_user, role=admin_role).exists())
        
        # Verificar que el admin tiene permisos correctos
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.can_access)
    
    def test_setup_with_logo_and_avatar(self):
        """Test: Setup con logo de empresa y avatar de administrador"""
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
        """Test: Forzar reconfiguración del setup"""
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
    
    def test_setup_data_integrity(self):
        """Test: Integridad de datos después del setup"""
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
