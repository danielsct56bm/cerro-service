"""
Tests para las vistas web del setup del sistema
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import SystemSetup, Company, Role, UserRole

User = get_user_model()


class SetupViewsTest(TestCase):
    """Tests para las vistas del setup"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = Client()
        self.setup_company_url = reverse('CPsetup:setup_company')
        self.setup_admin_url = reverse('CPsetup:setup_admin')
        self.setup_check_url = reverse('CPsetup:setup_check')
        self.login_url = reverse('CPlogin:login')
    
    def test_setup_check_redirects_to_company_when_no_company_exists(self):
        """Test: Verificar setup redirige a configuración de empresa cuando no existe empresa"""
        response = self.client.get(self.setup_check_url)
        
        # Debería redirigir a setup_company
        self.assertEqual(response.status_code, 302)
        self.assertIn('setup_company', response.url)
    
    def test_setup_check_redirects_to_login_when_company_exists(self):
        """Test: Verificar setup redirige a login cuando ya existe empresa"""
        # Crear empresa
        Company.objects.create(name="Test Company", active=True)
        
        response = self.client.get(self.setup_check_url)
        
        # Debería redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_setup_company_form_submission(self):
        """Test: Envío del formulario de configuración de empresa"""
        company_data = {
            'company_name': 'Cerro Verde S.A.A.',
            'ruc': '20100000000',
            'email': 'info@cerroverde.com',
            'phone': '+51 1 5950000',
            'address': 'Av. Arequipa 4095, Lima, Perú'
        }
        
        response = self.client.post(self.setup_company_url, company_data)
        
        # Debería redirigir a setup_admin
        self.assertEqual(response.status_code, 302)
        self.assertIn('setup_admin', response.url)
        
        # Verificar que se creó la empresa
        self.assertTrue(Company.objects.filter(name='Cerro Verde S.A.A.').exists())
        
        # Verificar que se guardó en sesión
        self.assertIsNotNone(self.client.session.get('setup_company_id'))
        self.assertEqual(self.client.session.get('setup_step'), 'admin')
    
    def test_setup_company_with_logo(self):
        """Test: Configuración de empresa con logo"""
        # Crear archivo de logo simulado
        logo_content = b'fake_logo_content'
        logo_file = SimpleUploadedFile(
            name='logo.png',
            content=logo_content,
            content_type='image/png'
        )
        
        company_data = {
            'company_name': 'Cerro Verde S.A.A.',
            'ruc': '20100000000',
            'email': 'info@cerroverde.com',
            'logo': logo_file
        }
        
        response = self.client.post(self.setup_company_url, company_data)
        
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se guardó el logo
        company = Company.objects.get(name='Cerro Verde S.A.A.')
        self.assertIsNotNone(company.logo)
        self.assertTrue(company.logo.name.startswith('company_logos/'))
    
    def test_setup_admin_form_submission(self):
        """Test: Envío del formulario de configuración de administrador"""
        # Crear empresa primero
        company = Company.objects.create(name="Test Company", active=True)
        self.client.session['setup_company_id'] = company.id
        self.client.session['setup_step'] = 'admin'
        self.client.session.save()
        
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
            'employee_number': 'EMP001'
        }
        
        response = self.client.post(self.setup_admin_url, admin_data)
        
        # Debería redirigir a login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Verificar que se creó el usuario administrador
        self.assertTrue(User.objects.filter(username='admin').exists())
        
        # Verificar que se marcó el setup como completado
        self.assertTrue(SystemSetup.objects.filter(is_completed=True).exists())
        
        # Verificar que se limpió la sesión
        self.assertIsNone(self.client.session.get('setup_company_id'))
        self.assertIsNone(self.client.session.get('setup_step'))
    
    def test_setup_admin_with_generated_avatar(self):
        """Test: Configuración de administrador con avatar generado"""
        # Crear empresa primero
        company = Company.objects.create(name="Test Company", active=True)
        self.client.session['setup_company_id'] = company.id
        self.client.session['setup_step'] = 'admin'
        self.client.session.save()
        
        admin_data = {
            'username': 'admin',
            'email': 'admin@cerroverde.com',
            'password': 'Admin123!',
            'first_name': 'Administrador',
            'last_name': 'Sistema',
            'avatar_type': 'generated'
        }
        
        response = self.client.post(self.setup_admin_url, admin_data)
        
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se generó el avatar
        admin_user = User.objects.get(username='admin')
        self.assertIsNotNone(admin_user.avatar)
        self.assertTrue(admin_user.avatar.name.startswith('user_avatars/'))
    
    def test_setup_admin_with_uploaded_avatar(self):
        """Test: Configuración de administrador con avatar subido"""
        # Crear empresa primero
        company = Company.objects.create(name="Test Company", active=True)
        self.client.session['setup_company_id'] = company.id
        self.client.session['setup_step'] = 'admin'
        self.client.session.save()
        
        # Crear archivo de avatar simulado
        avatar_content = b'fake_avatar_content'
        avatar_file = SimpleUploadedFile(
            name='avatar.jpg',
            content=avatar_content,
            content_type='image/jpeg'
        )
        
        admin_data = {
            'username': 'admin',
            'email': 'admin@cerroverde.com',
            'password': 'Admin123!',
            'first_name': 'Administrador',
            'last_name': 'Sistema',
            'avatar_type': 'upload',
            'avatar': avatar_file
        }
        
        response = self.client.post(self.setup_admin_url, admin_data)
        
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se guardó el avatar
        admin_user = User.objects.get(username='admin')
        self.assertIsNotNone(admin_user.avatar)
        self.assertTrue(admin_user.avatar.name.startswith('user_avatars/'))
    
    def test_setup_admin_without_company_session(self):
        """Test: Intentar configurar admin sin sesión de empresa"""
        admin_data = {
            'username': 'admin',
            'email': 'admin@cerroverde.com',
            'password': 'Admin123!',
            'first_name': 'Administrador',
            'last_name': 'Sistema'
        }
        
        response = self.client.post(self.setup_admin_url, admin_data)
        
        # Debería redirigir a setup_company
        self.assertEqual(response.status_code, 302)
        self.assertIn('setup_company', response.url)
    
    def test_setup_company_form_validation(self):
        """Test: Validación del formulario de empresa"""
        # Test con datos inválidos
        invalid_data = {
            'company_name': '',  # Nombre vacío
            'email': 'invalid_email'  # Email inválido
        }
        
        response = self.client.post(self.setup_company_url, invalid_data)
        
        # Debería mostrar errores
        self.assertEqual(response.status_code, 200)  # No redirige
        self.assertIn('company_name', response.context['form'].errors)
    
    def test_setup_admin_form_validation(self):
        """Test: Validación del formulario de administrador"""
        # Crear empresa primero
        company = Company.objects.create(name="Test Company", active=True)
        self.client.session['setup_company_id'] = company.id
        self.client.session['setup_step'] = 'admin'
        self.client.session.save()
        
        # Test con datos inválidos
        invalid_data = {
            'username': '',  # Username vacío
            'email': 'invalid_email',  # Email inválido
            'password': '123'  # Contraseña muy corta
        }
        
        response = self.client.post(self.setup_admin_url, invalid_data)
        
        # Debería mostrar errores
        self.assertEqual(response.status_code, 200)  # No redirige
        self.assertIn('username', response.context['form'].errors)
    
    def test_setup_complete_flow(self):
        """Test: Flujo completo del setup"""
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
