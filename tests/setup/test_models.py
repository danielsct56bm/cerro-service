"""
Tests unitarios para los modelos del setup del sistema
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import SystemSetup, Company, Role, User, UserRole


class SystemSetupModelTest(TestCase):
    """Tests para el modelo SystemSetup"""
    
    def test_system_setup_creation(self):
        """Test: Crear un SystemSetup básico"""
        setup = SystemSetup.objects.create(
            is_completed=False,
            note="Setup pendiente"
        )
        self.assertIsNotNone(setup.id)
        self.assertFalse(setup.is_completed)
        self.assertIsNone(setup.completed_at)
    
    def test_system_setup_completion(self):
        """Test: Marcar setup como completado"""
        setup = SystemSetup.objects.create(is_completed=False)
        setup.is_completed = True
        setup.save()
        
        self.assertTrue(setup.is_completed)
        self.assertIsNotNone(setup.completed_at)
        self.assertIsInstance(setup.completed_at, timezone.datetime)
    
    def test_system_setup_str_representation(self):
        """Test: Representación string del modelo"""
        setup = SystemSetup.objects.create(is_completed=False)
        self.assertIn('Pendiente', str(setup))
        
        setup.is_completed = True
        setup.save()
        self.assertIn('Completado', str(setup))
    
    def test_system_setup_note_field(self):
        """Test: Campo note del setup"""
        note = "Setup completado para Cerro Verde"
        setup = SystemSetup.objects.create(note=note)
        self.assertEqual(setup.note, note)


class CompanyModelTest(TestCase):
    """Tests para el modelo Company"""
    
    def test_company_creation(self):
        """Test: Crear una empresa básica"""
        company = Company.objects.create(
            name="Cerro Verde S.A.A.",
            active=True
        )
        self.assertIsNotNone(company.id)
        self.assertTrue(company.active)
        self.assertIsNotNone(company.created_at)
        self.assertIsNotNone(company.updated_at)
    
    def test_company_required_fields(self):
        """Test: Campos requeridos de la empresa"""
        company = Company.objects.create(
            name="Cerro Verde S.A.A.",
            active=True
        )
        self.assertEqual(company.name, "Cerro Verde S.A.A.")
        self.assertTrue(company.active)
    
    def test_company_optional_fields(self):
        """Test: Campos opcionales de la empresa"""
        company = Company.objects.create(
            name="Cerro Verde S.A.A.",
            ruc="20100000000",
            email="info@cerroverde.com",
            phone="+51 1 5950000",
            address="Av. Arequipa 4095, Lima, Perú",
            active=True
        )
        self.assertEqual(company.ruc, "20100000000")
        self.assertEqual(company.email, "info@cerroverde.com")
        self.assertEqual(company.phone, "+51 1 5950000")
        self.assertEqual(company.address, "Av. Arequipa 4095, Lima, Perú")
    
    def test_company_str_representation(self):
        """Test: Representación string de la empresa"""
        company = Company.objects.create(name="Cerro Verde S.A.A.")
        self.assertEqual(str(company), "Cerro Verde S.A.A.")
    
    def test_company_logo_upload(self):
        """Test: Subir logo de la empresa"""
        # Crear archivo de imagen simulado
        logo_content = b'fake_logo_content'
        logo_file = SimpleUploadedFile(
            name='logo.png',
            content=logo_content,
            content_type='image/png'
        )
        
        company = Company.objects.create(
            name="Cerro Verde S.A.A.",
            logo=logo_file,
            active=True
        )
        self.assertIsNotNone(company.logo)
        self.assertTrue(company.logo.name.startswith('company_logos/'))


class RoleModelTest(TestCase):
    """Tests para el modelo Role"""
    
    def test_role_creation(self):
        """Test: Crear un rol básico"""
        company = Company.objects.create(name="Cerro Verde S.A.A.")
        role = Role.objects.create(
            company=company,
            key='admin',
            name='Administrador',
            can_access=True,
            is_system=True
        )
        
        self.assertIsNotNone(role.id)
        self.assertEqual(role.company, company)
        self.assertEqual(role.key, 'admin')
        self.assertEqual(role.name, 'Administrador')
        self.assertTrue(role.can_access)
        self.assertTrue(role.is_system)
    
    def test_role_choices(self):
        """Test: Opciones válidas de roles"""
        company = Company.objects.create(name="Cerro Verde S.A.A.")
        
        # Crear roles con todas las opciones válidas
        admin_role = Role.objects.create(
            company=company, key='admin', name='Administrador'
        )
        user_role = Role.objects.create(
            company=company, key='user', name='Usuario'
        )
        technician_role = Role.objects.create(
            company=company, key='technician', name='Técnico'
        )
        
        self.assertEqual(admin_role.name, 'Administrador')
        self.assertEqual(user_role.name, 'Usuario')
        self.assertEqual(technician_role.name, 'Técnico')
    
    def test_role_str_representation(self):
        """Test: Representación string del rol"""
        company = Company.objects.create(name="Cerro Verde")
        role = Role.objects.create(
            company=company, key='admin', name='Administrador'
        )
        str_repr = str(role)
        self.assertIn("Administrador", str_repr)
        self.assertIn("Cerro Verde", str_repr)


class UserModelTest(TestCase):
    """Tests para el modelo User"""
    
    def test_user_creation(self):
        """Test: Crear un usuario básico"""
        company = Company.objects.create(name="Cerro Verde S.A.A.")
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            company=company
        )
        
        self.assertIsNotNone(user.id)
        self.assertEqual(user.company, company)
        self.assertTrue(user.is_active)
        self.assertTrue(user.can_access)
    
    def test_user_required_fields(self):
        """Test: Campos requeridos del usuario"""
        company = Company.objects.create(name="Cerro Verde S.A.A.")
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            company=company
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.company, company)
    
    def test_user_optional_fields(self):
        """Test: Campos opcionales del usuario"""
        company = Company.objects.create(name="Cerro Verde S.A.A.")
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            company=company,
            title="Ingeniero",
            department="IT",
            location="Lima",
            sap_id="SAP123",
            employee_number="EMP001"
        )
        
        self.assertEqual(user.title, "Ingeniero")
        self.assertEqual(user.department, "IT")
        self.assertEqual(user.location, "Lima")
        self.assertEqual(user.sap_id, "SAP123")
        self.assertEqual(user.employee_number, "EMP001")
    
    def test_user_avatar_upload(self):
        """Test: Subir avatar del usuario"""
        company = Company.objects.create(name="Cerro Verde S.A.A.")
        
        # Crear archivo de imagen simulado
        avatar_content = b'fake_avatar_content'
        avatar_file = SimpleUploadedFile(
            name='avatar.jpg',
            content=avatar_content,
            content_type='image/jpeg'
        )
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            company=company,
            avatar=avatar_file
        )
        self.assertIsNotNone(user.avatar)
        self.assertTrue(user.avatar.name.startswith('user_avatars/'))
    
    def test_user_password_setting(self):
        """Test: Establecer contraseña del usuario"""
        company = Company.objects.create(name="Cerro Verde S.A.A.")
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            company=company
        )
        
        # Establecer nueva contraseña
        user.set_password('NewPassword123!')
        user.save()
        
        # Verificar que la contraseña se estableció correctamente
        self.assertTrue(user.check_password('NewPassword123!'))
        self.assertFalse(user.check_password('TestPass123!'))


class UserRoleModelTest(TestCase):
    """Tests para el modelo UserRole"""
    
    def test_user_role_creation(self):
        """Test: Crear relación usuario-rol"""
        company = Company.objects.create(name="Cerro Verde S.A.A.")
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            company=company
        )
        role = Role.objects.create(
            company=company, key='admin', name='Administrador'
        )
        
        user_role = UserRole.objects.create(user=user, role=role)
        
        self.assertIsNotNone(user_role.id)
        self.assertEqual(user_role.user, user)
        self.assertEqual(user_role.role, role)
    
    def test_user_role_str_representation(self):
        """Test: Representación string de UserRole"""
        company = Company.objects.create(name="Cerro Verde")
        user = User.objects.create_user(
            username="admin",
            email='admin@test.com',
            password='TestPass123!',
            company=company
        )
        role = Role.objects.create(
            company=company, key='admin', name='Administrador'
        )
        
        user_role = UserRole.objects.create(user=user, role=role)
        str_repr = str(user_role)
        
        self.assertIn("admin", str_repr)
        self.assertIn("Administrador", str_repr)
        self.assertIn("Cerro Verde", str_repr)
