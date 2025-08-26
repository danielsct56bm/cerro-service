"""
Tests para la API del setup del sistema
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from core.models import SystemSetup, Company, Role, UserRole

User = get_user_model()


class SetupAPITest(TestCase):
    """Tests para la API del setup"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()
        self.setup_url = '/api/setup/'
        self.status_url = '/api/system-status/'
    
    def test_get_setup_status_pending(self):
        """Test: Obtener estado del setup cuando está pendiente"""
        response = self.client.get(self.setup_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'pending')
        self.assertIn('no está configurado', response.data['message'])
    
    def test_get_setup_status_completed(self):
        """Test: Obtener estado del setup cuando está completado"""
        # Crear setup completado
        SystemSetup.objects.create(is_completed=True)
        
        response = self.client.get(self.setup_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIn('ya está configurado', response.data['message'])
        self.assertIsNotNone(response.data['completed_at'])
    
    def test_post_setup_success(self):
        """Test: Ejecutar setup exitosamente"""
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
        
        response = self.client.post(self.setup_url, setup_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('completado exitosamente', response.data['message'])
        
        # Verificar que se crearon los datos
        self.assertTrue(Company.objects.filter(name='Cerro Verde S.A.A.').exists())
        self.assertTrue(User.objects.filter(username='admin').exists())
        self.assertTrue(SystemSetup.objects.filter(is_completed=True).exists())
        
        # Verificar roles creados
        company = Company.objects.get(name='Cerro Verde S.A.A.')
        self.assertEqual(Role.objects.filter(company=company).count(), 3)
        
        # Verificar rol asignado al admin
        admin_user = User.objects.get(username='admin')
        admin_role = Role.objects.get(company=company, key='admin')
        self.assertTrue(UserRole.objects.filter(user=admin_user, role=admin_role).exists())
    
    def test_post_setup_with_logo(self):
        """Test: Ejecutar setup con logo de empresa"""
        # Crear archivo de logo simulado
        logo_content = b'fake_logo_content'
        logo_file = SimpleUploadedFile(
            name='logo.png',
            content=logo_content,
            content_type='image/png'
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
                'last_name': 'Sistema'
            }
        }
        
        response = self.client.post(self.setup_url, setup_data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que se guardó el logo
        company = Company.objects.get(name='Cerro Verde S.A.A.')
        self.assertIsNotNone(company.logo)
        self.assertTrue(company.logo.name.startswith('company_logos/'))
    
    def test_post_setup_with_avatar(self):
        """Test: Ejecutar setup con avatar de administrador"""
        # Crear archivo de avatar simulado
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
                'email': 'info@cerroverde.com'
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
        
        response = self.client.post(self.setup_url, setup_data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que se guardó el avatar
        admin_user = User.objects.get(username='admin')
        self.assertIsNotNone(admin_user.avatar)
        self.assertTrue(admin_user.avatar.name.startswith('user_avatars/'))
    
    def test_post_setup_already_completed(self):
        """Test: Intentar setup cuando ya está completado"""
        # Crear setup completado
        SystemSetup.objects.create(is_completed=True)
        
        setup_data = {
            'company': {
                'name': 'Otra Empresa',
                'ruc': '20100000001',
                'email': 'info@otraempresa.com'
            },
            'admin': {
                'username': 'admin2',
                'email': 'admin2@otraempresa.com',
                'password': 'Admin123!',
                'first_name': 'Admin',
                'last_name': 'Dos'
            }
        }
        
        response = self.client.post(self.setup_url, setup_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ya está configurado', response.data['error'])
    
    def test_post_setup_force_reconfigure(self):
        """Test: Forzar reconfiguración del setup"""
        # Crear setup completado
        SystemSetup.objects.create(is_completed=True)
        
        setup_data = {
            'company': {
                'name': 'Nueva Empresa',
                'ruc': '20100000002',
                'email': 'info@nuevaempresa.com'
            },
            'admin': {
                'username': 'newadmin',
                'email': 'newadmin@nuevaempresa.com',
                'password': 'Admin123!',
                'first_name': 'Nuevo',
                'last_name': 'Admin'
            },
            'force': True
        }
        
        response = self.client.post(self.setup_url, setup_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('completado exitosamente', response.data['message'])
    
    def test_post_setup_invalid_data(self):
        """Test: Setup con datos inválidos"""
        setup_data = {
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
        
        response = self.client.post(self.setup_url, setup_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company', response.data)
        self.assertIn('admin', response.data)
    
    def test_post_setup_missing_required_fields(self):
        """Test: Setup faltando campos requeridos"""
        setup_data = {
            'company': {
                'name': 'Cerro Verde S.A.A.'
                # Faltan otros campos requeridos
            },
            'admin': {
                'username': 'admin'
                # Faltan otros campos requeridos
            }
        }
        
        response = self.client.post(self.setup_url, setup_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company', response.data)
        self.assertIn('admin', response.data)


class SystemStatusAPITest(TestCase):
    """Tests para la API de estado del sistema"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()
        self.status_url = '/api/system-status/'
    
    def test_get_system_status_pending(self):
        """Test: Obtener estado del sistema cuando está pendiente"""
        response = self.client.get(self.status_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'setup_required')
        self.assertFalse(response.data['system_setup']['is_completed'])
        self.assertEqual(response.data['statistics']['companies'], 0)
        self.assertEqual(response.data['statistics']['users'], 0)
        self.assertEqual(response.data['statistics']['roles'], 0)
    
    def test_get_system_status_operational(self):
        """Test: Obtener estado del sistema cuando está operativo"""
        # Crear datos completos del sistema
        setup = SystemSetup.objects.create(is_completed=True)
        company = Company.objects.create(name="Test Company", active=True)
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            company=company
        )
        role = Role.objects.create(
            company=company, key='admin', name='Administrador'
        )
        UserRole.objects.create(user=user, role=role)
        
        response = self.client.get(self.status_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'operational')
        self.assertTrue(response.data['system_setup']['is_completed'])
        self.assertEqual(response.data['statistics']['companies'], 1)
        self.assertEqual(response.data['statistics']['users'], 1)
        self.assertEqual(response.data['statistics']['roles'], 1)
        self.assertEqual(response.data['statistics']['active_users'], 1)
        self.assertEqual(response.data['statistics']['total_user_roles'], 1)
    
    def test_get_system_status_info(self):
        """Test: Verificar información del sistema"""
        response = self.client.get(self.status_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('django_version', response.data['system_info'])
        self.assertIn('drf_version', response.data['system_info'])
        self.assertIn('database_engine', response.data['system_info'])
        self.assertIn('redis_available', response.data['system_info'])
    
    def test_get_system_status_setup_duration(self):
        """Test: Verificar duración del setup"""
        setup = SystemSetup.objects.create(is_completed=True)
        
        response = self.client.get(self.status_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['system_setup']['completed_at'])
        # Como no tenemos created_at, setup_duration será None
        self.assertIsNone(response.data['system_setup']['setup_duration'])
