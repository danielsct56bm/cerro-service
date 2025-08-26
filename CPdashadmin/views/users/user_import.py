"""
Vistas de importación y exportación de usuarios - Archivo principal refactorizado
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from core.models import Role
from .import_handlers import (
    handle_csv_upload,
    handle_column_mapping,
    handle_import_confirmation,
    cleanup_import_session
)
from .import_config import (
    process_import_config,
    prepare_step2_context
)
from .data_processor import (
    generate_preview_data,
    process_import_data
)
import csv


@login_required
def user_import(request):
    """Importar usuarios desde CSV"""
    if request.method == 'POST':
        if 'upload_csv' in request.POST:
            return _handle_csv_upload_step(request)
        elif 'map_columns' in request.POST:
            return _handle_column_mapping_step(request)
        elif 'confirm_import' in request.POST:
            return _handle_import_confirmation_step(request)
    
    # GET: mostrar formulario inicial
    context = {
        'step': 1,
        'roles': Role.objects.filter(company=request.user.company),
    }
    return render(request, 'CPdashadmin/users/user_import.html', context)


def _handle_csv_upload_step(request):
    """Manejar el paso 1: Carga de CSV"""
    result = handle_csv_upload(request)
    if result[0] is None:  # Error en la carga
        return result[1]  # Redirect
    
    df, detected_delimiter, encoding, duplicate_columns, problematic_columns = result
    
    # Preparar contexto para el paso 2
    context = prepare_step2_context(df, detected_delimiter, encoding, duplicate_columns, problematic_columns)
    return render(request, 'CPdashadmin/users/user_import.html', context)


def _handle_column_mapping_step(request):
    """Manejar el paso 2: Mapeo de columnas"""
    column_mapping = handle_column_mapping(request)
    if isinstance(column_mapping, type(redirect('CPdashadmin:user_import'))):
        return column_mapping  # Error, redirect
    
    # Procesar reglas y configuraciones
    import_config = process_import_config(request, column_mapping)
    
    # Guardar en sesión
    request.session['column_mapping'] = column_mapping
    request.session['import_config'] = import_config
    
    # Procesar CSV para preview de importación
    try:
        import pandas as pd
        import io
        
        csv_data = request.session.get('csv_data')
        df = pd.read_csv(
            io.StringIO(csv_data),
            delimiter=import_config['delimiter'],
            encoding=import_config['encoding'],
            header=0
        )
        
        # Generar preview
        preview_data = generate_preview_data(df, column_mapping, import_config)
        
        # Roles disponibles
        roles = Role.objects.filter(company=request.user.company)
        if not roles.exists():
            messages.warning(request, 'No hay roles configurados en la empresa. Se crearán usuarios sin rol.')
        
        context = {
            'step': 3,
            'preview_data': preview_data,
            'total_rows': len(df),
            'roles': roles,
            'column_mapping': column_mapping,
            'import_config': import_config,
            'selected_rules': import_config['selected_rules'],
        }
        return render(request, 'CPdashadmin/users/user_import.html', context)
        
    except Exception as e:
        messages.error(request, f'Error al procesar el CSV: {str(e)}')
        return redirect('CPdashadmin:user_import')


def _handle_import_confirmation_step(request):
    """Manejar el paso 3: Confirmación de importación"""
    df = handle_import_confirmation(request)
    if df is None:  # Error
        return redirect('CPdashadmin:user_import')
    
    # Obtener datos de sesión
    column_mapping = request.session.get('column_mapping')
    import_config = request.session.get('import_config')
    
    # Procesar importación
    success_count, error_count, errors, conflicts = process_import_data(
        df, column_mapping, import_config, request
    )
    
    # Limpiar sesión
    cleanup_import_session(request)
    
    # Mostrar resultados
    if success_count > 0:
        messages.success(request, f'Importación completada: {success_count} usuarios procesados exitosamente.')
    if conflicts:
        messages.warning(request, f'{len(conflicts)} conflictos detectados (usuarios ya existentes).')
    if error_count > 0:
        messages.warning(request, f'{error_count} errores durante la importación.')
    
    return redirect('CPdashadmin:user_management')


@login_required
def user_export(request):
    """Exportar usuarios a CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="usuarios.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Username', 'Email', 'Nombre', 'Apellido', 'Cargo', 'Departamento', 
        'Ubicación', 'Número de Empleado', 'ID SAP', 'Rol', 'Estado', 
        'Acceso', 'Último Acceso', 'Fecha de Creación'
    ])
    
    # Solo usuarios de la empresa actual
    from core.models import User
    users = User.objects.filter(company=request.user.company).prefetch_related('userrole_set__role')
    
    for user in users:
        roles = ', '.join([ur.role.name for ur in user.userrole_set.all()])
        writer.writerow([
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            user.title or '',
            user.department or '',
            user.location or '',
            user.employee_number or '',
            user.sap_id or '',
            roles,
            'Activo' if user.is_active else 'Inactivo',
            'Permitido' if user.can_access else 'Denegado',
            user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else 'Nunca',
            user.date_joined.strftime('%d/%m/%Y %H:%M')
        ])
    
    return response
