"""
Configuración de importación de usuarios
"""
import pandas as pd
import io
from django.contrib import messages
from core.models import Role


def get_column_mapping_suggestions(df):
    """Obtener sugerencias de mapeo de columnas"""
    column_mapping_suggestions = {}
    field_mappings = {
        'username': ['user_name', 'username', 'user', 'login', 'userid', 'id', 'user_id'],
        'email': ['email', 'e-mail', 'mail', 'correo', 'e_mail'],
        'first_name': ['name', 'nombre', 'first_name', 'firstname', 'given_name', 'nombre_completo'],
        'last_name': ['last_name', 'lastname', 'surname', 'apellido'],
        'title': ['title', 'cargo', 'position', 'job_title', 'role', 'puesto'],
        'department': ['department', 'departamento', 'dept', 'division', 'area'],
        'location': ['location', 'ubicacion', 'site', 'office', 'sede'],
        'employee_number': ['employee_number', 'emp_number', 'employee_id', 'emp_id', 'numero_empleado'],
        'sap_id': ['sap_id', 'sap', 'u_sap_id', 'sap_number', 'id_sap'],
        'role': ['role', 'rol', 'user_role', 'type', 'tipo_usuario'],
        'is_active': ['active', 'is_active', 'status', 'enabled', 'activo', 'estado'],
    }
    
    for field, possible_names in field_mappings.items():
        for col in df.columns:
            col_lower = str(col).lower().strip()
            for possible_name in possible_names:
                if possible_name in col_lower or col_lower in possible_name:
                    column_mapping_suggestions[field] = col
                    break
            if field in column_mapping_suggestions:
                break
    
    return column_mapping_suggestions


def get_available_fields():
    """Obtener campos disponibles para reglas dinámicas"""
    return [
        ('department', 'Departamento'),
        ('title', 'Cargo'),
        ('location', 'Ubicación'),
        ('employee_number', 'Número de Empleado'),
        ('sap_id', 'ID SAP'),
    ]


def get_modifiable_fields():
    """Obtener campos que se pueden modificar"""
    return [
        ('role', 'Rol'),
        ('is_active', 'Estado Activo'),
        ('can_access', 'Puede Acceder'),
        ('must_change_password', 'Debe Cambiar Contraseña'),
    ]


def get_comparison_operators():
    """Obtener operadores de comparación"""
    return [
        ('equals', 'Igual a'),
        ('contains', 'Contiene'),
        ('starts_with', 'Empieza con'),
        ('ends_with', 'Termina con'),
        ('not_equals', 'No igual a'),
        ('not_contains', 'No contiene'),
    ]


def get_suggested_rules():
    """Obtener reglas predefinidas como sugerencias"""
    return [
        {
            'name': 'Rol por Departamento',
            'description': 'Asignar rol basado en departamento',
            'field': 'department',
            'operator': 'contains',
            'value': 'TI',
            'action_field': 'role',
            'action_value': 'admin',
            'priority': 1
        },
        {
            'name': 'Estado por Cargo',
            'description': 'Activar usuarios según cargo',
            'field': 'title',
            'operator': 'contains',
            'value': 'Practicante',
            'action_field': 'is_active',
            'action_value': False,
            'priority': 2
        },
        {
            'name': 'Acceso por Ubicación',
            'description': 'Permitir acceso según ubicación',
            'field': 'location',
            'operator': 'equals',
            'value': 'Cerro Verde',
            'action_field': 'can_access',
            'action_value': True,
            'priority': 3
        }
    ]


def get_user_fields():
    """Obtener campos de usuario para mapeo"""
    return [
        ('username', 'Nombre de Usuario'),
        ('email', 'Email'),
        ('first_name', 'Nombre'),
        ('last_name', 'Apellido'),
        ('title', 'Cargo'),
        ('department', 'Departamento'),
        ('location', 'Ubicación'),
        ('employee_number', 'Número de Empleado'),
        ('sap_id', 'ID SAP'),
        ('role', 'Rol'),
        ('is_active', 'Estado Activo'),
    ]


def process_import_config(request, column_mapping):
    """Procesar configuración de importación"""
    # Obtener reglas de interpretación seleccionadas
    selected_rules = []
    custom_rules = []
    
    # Procesar reglas personalizadas
    rule_names = request.POST.getlist('rule_name')
    rule_fields = request.POST.getlist('rule_field')
    rule_operators = request.POST.getlist('rule_operator')
    rule_values = request.POST.getlist('rule_value')
    rule_action_fields = request.POST.getlist('rule_action_field')
    rule_action_values = request.POST.getlist('rule_action_value')
    rule_priorities = request.POST.getlist('rule_priority')
    
    for i in range(len(rule_names)):
        if rule_names[i] and rule_fields[i] and rule_operators[i] and rule_values[i]:
            custom_rules.append({
                'name': rule_names[i],
                'field': rule_fields[i],
                'operator': rule_operators[i],
                'value': rule_values[i],
                'action_field': rule_action_fields[i],
                'action_value': rule_action_values[i],
                'priority': int(rule_priorities[i]) if rule_priorities[i] else 1
            })
    
    # Procesar reglas sugeridas seleccionadas
    for rule_name in request.POST.getlist('suggested_rules'):
        selected_rules.append(rule_name)
    
    return {
        'skip_first_row': False,
        'default_password': request.POST.get('default_password', 'changeme123'),
        'default_role': request.POST.get('default_role', ''),
        'default_is_active': request.POST.get('default_is_active') == 'on',
        'default_can_access': request.POST.get('default_can_access') == 'on',
        'default_must_change_password': request.POST.get('default_must_change_password') == 'on',
        'update_existing': request.POST.get('update_existing') == 'on',
        'delimiter': request.session.get('csv_delimiter', ','),
        'encoding': request.session.get('csv_encoding', 'utf-8'),
        'has_headers': True,
        'selected_rules': selected_rules,
        'custom_rules': custom_rules,
        'column_mapping': column_mapping,
    }


def prepare_step2_context(df, detected_delimiter, encoding, duplicate_columns, problematic_columns):
    """Preparar contexto para el paso 2"""
    # Mapeo inteligente de columnas
    column_mapping_suggestions = get_column_mapping_suggestions(df)
    
    # Convertir DataFrame a una lista de listas para facilitar el acceso en el template
    csv_preview_rows = []
    for _, row in df.head().iterrows():
        row_values = []
        for col in df.columns:
            value = str(row[col]) if pd.notna(row[col]) else ''
            row_values.append(value)
        csv_preview_rows.append(row_values)
    
    return {
        'step': 2,
        'csv_columns': df.columns.tolist(),
        'csv_preview': csv_preview_rows,
        'csv_delimiter': detected_delimiter,
        'csv_encoding': encoding,
        'csv_has_headers': True,
        'column_mapping_suggestions': column_mapping_suggestions,
        'duplicate_columns': duplicate_columns,
        'problematic_columns': problematic_columns,
        'available_fields': get_available_fields(),
        'modifiable_fields': get_modifiable_fields(),
        'comparison_operators': get_comparison_operators(),
        'suggested_rules': get_suggested_rules(),
        'user_fields': get_user_fields(),
    }
