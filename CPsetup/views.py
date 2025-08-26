from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import requests
from core.models import Company, User, SystemSetup, Role, UserRole
import uuid


def setup_check(request):
    """
    Verificar si el sistema ya está configurado
    Si ya existe una empresa, redirigir al login
    """
    if Company.objects.exists():
        messages.warning(request, "El sistema ya está configurado. Redirigiendo al login.")
        return redirect('CPlogin:login')
    
    return redirect('CPsetup:setup_company')


def setup_company(request):
    """
    Paso 1: Configuración de la empresa
    """
    # Verificar si ya existe una empresa configurada
    if Company.objects.exists():
        messages.warning(request, "El sistema ya está configurado. No puede acceder al setup.")
        return redirect('CPlogin:login')
    if request.method == 'POST':
        try:
            data = request.POST
            files = request.FILES
            
            # Crear empresa
            company = Company.objects.create(
                name=data.get('company_name'),
                ruc=data.get('ruc', ''),
                address=data.get('address', ''),
                phone=data.get('phone', ''),
                email=data.get('email', ''),
                active=True
            )
            
            # Subir logo si se proporciona
            if 'logo' in files:
                logo_file = files['logo']
                file_path = f'company_logos/{company.id}_{uuid.uuid4().hex[:8]}_{logo_file.name}'
                saved_path = default_storage.save(file_path, ContentFile(logo_file.read()))
                company.logo = saved_path
                company.save()
            
            # Guardar en sesión para el siguiente paso
            request.session['setup_company_id'] = company.id
            request.session['setup_step'] = 'admin'
            
            messages.success(request, "Empresa configurada exitosamente.")
            return redirect('CPsetup:setup_admin')
            
        except Exception as e:
            messages.error(request, f"Error al configurar la empresa: {str(e)}")
            return render(request, 'CPsetup/setup_company.html')
    
    return render(request, 'CPsetup/setup_company.html')


def setup_admin(request):
    """
    Paso 2: Configuración del administrador
    """
    # Verificar si ya existe una empresa configurada (protección adicional)
    if SystemSetup.objects.filter(is_completed=True).exists():
        messages.warning(request, "El sistema ya está configurado completamente. No puede acceder al setup.")
        return redirect('CPlogin:login')
    
    # Verificar que venimos del paso anterior
    company_id = request.session.get('setup_company_id')
    if not company_id:
        messages.error(request, "Debe configurar la empresa primero.")
        return redirect('CPsetup:setup_company')
    
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        messages.error(request, "Empresa no encontrada.")
        return redirect('CPsetup:setup_company')
    
    if request.method == 'POST':
        try:
            data = request.POST
            files = request.FILES
            
            # Crear usuario administrador
            admin_user = User.objects.create_user(
                username=data.get('username'),
                email=data.get('email'),
                password=data.get('password'),
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                company=company,
                title=data.get('title', ''),
                department=data.get('department', ''),
                location=data.get('location', ''),
                sap_id=data.get('sap_id', ''),
                employee_number=data.get('employee_number', ''),
                can_access=True,
                is_staff=True,
                is_superuser=True
            )
            
            # Manejar avatar
            avatar_type = data.get('avatar_type', 'generated')
            
            if avatar_type == 'upload' and 'avatar' in files:
                # Subir imagen
                avatar_file = files['avatar']
                file_path = f'user_avatars/{admin_user.id}_{uuid.uuid4().hex[:8]}_{avatar_file.name}'
                saved_path = default_storage.save(file_path, ContentFile(avatar_file.read()))
                admin_user.avatar = saved_path
            elif avatar_type == 'generated':
                # Generar avatar con DiceBear
                full_name = f"{admin_user.first_name} {admin_user.last_name}".strip()
                if not full_name:
                    full_name = admin_user.username
                
                # Generar URL del avatar
                avatar_url = f"https://api.dicebear.com/9.x/initials/svg?seed={full_name}"
                
                # Descargar y guardar el avatar
                try:
                    response = requests.get(avatar_url)
                    if response.status_code == 200:
                        file_path = f'user_avatars/{admin_user.id}_{uuid.uuid4().hex[:8]}_generated.svg'
                        saved_path = default_storage.save(file_path, ContentFile(response.content))
                        admin_user.avatar = saved_path
                except Exception as e:
                    # Si falla la descarga, continuar sin avatar
                    pass
            
            admin_user.save()
            
            # Crear roles base del sistema
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
            
            # Asignar rol de administrador al usuario
            admin_role = next(r for r in created_roles if r.key == 'admin')
            UserRole.objects.create(user=admin_user, role=admin_role)
            
            # Marcar setup como completado
            SystemSetup.objects.create(
                is_completed=True,
                note=f"Setup completado para {company.name}"
            )
            
            # Limpiar sesión
            request.session.pop('setup_company_id', None)
            request.session.pop('setup_step', None)
            
            messages.success(request, "Administrador configurado exitosamente. El sistema está listo para usar.")
            return redirect('CPlogin:login')
            
        except Exception as e:
            messages.error(request, f"Error al configurar el administrador: {str(e)}")
    
    context = {
        'company': company,
        'step': 2
    }
    return render(request, 'CPsetup/setup_admin.html', context)


@csrf_exempt
def generate_avatar_preview(request):
    """
    Generar preview del avatar para el nombre ingresado
    """
    # Verificar si el sistema ya está configurado
    if SystemSetup.objects.filter(is_completed=True).exists():
        return JsonResponse({
            'success': False,
            'message': 'El sistema ya está configurado'
        })
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            username = data.get('username', '')
            
            # Usar nombre completo o username como fallback
            seed = f"{first_name} {last_name}".strip()
            if not seed:
                seed = username
            
            if seed:
                avatar_url = f"https://api.dicebear.com/9.x/initials/svg?seed={seed}"
                return JsonResponse({
                    'success': True,
                    'avatar_url': avatar_url
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Se requiere un nombre para generar el avatar'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Datos JSON inválidos'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })


def setup_progress(request):
    """
    Obtener progreso del setup
    """
    # Verificar si el sistema ya está configurado
    if SystemSetup.objects.filter(is_completed=True).exists():
        return JsonResponse({
            'completed': True,
            'message': 'El sistema ya está configurado'
        })
    company_exists = Company.objects.exists()
    setup_completed = SystemSetup.objects.filter(is_completed=True).exists()
    
    return JsonResponse({
        'company_exists': company_exists,
        'setup_completed': setup_completed,
        'current_step': request.session.get('setup_step', 'company')
    })
