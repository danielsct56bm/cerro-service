"""
Procesamiento de datos de usuarios para importación
"""
from django.contrib import messages
from core.models import User, Role, UserRole
from .utils import apply_dynamic_rules
import pandas as pd
import io


def generate_preview_data(df, column_mapping, import_config):
    """Generar datos de preview"""
    preview_data = []
    for index, row in df.head(10).iterrows():
        user_data = extract_user_data_from_row(row, column_mapping, import_config)
        
        # Aplicar reglas de interpretación
        applied_rules, rule_conflicts = apply_interpretation_rules(user_data, import_config, column_mapping)
        
        # Agregar información de reglas aplicadas
        user_data['_applied_rules'] = applied_rules
        user_data['_rule_conflicts'] = rule_conflicts
        
        # Agregar configuraciones por defecto
        add_default_configurations(user_data, import_config)
        
        preview_data.append(user_data)
    
    return preview_data


def extract_user_data_from_row(row, column_mapping, import_config):
    """Extraer datos de usuario desde la fila CSV"""
    user_data = {}
    for field_name, csv_column in column_mapping.items():
        value = str(row.get(csv_column, '')).strip()
        
        # Procesamiento especial para campos específicos
        if field_name == 'is_active':
            user_data[field_name] = convert_boolean_value(value, import_config['default_is_active'])
        elif field_name == 'first_name' and 'name' in column_mapping:
            user_data = process_full_name(row, column_mapping, field_name, value)
        else:
            user_data[field_name] = value
    
    return user_data


def convert_boolean_value(value, default_value):
    """Convertir valor a booleano"""
    if value.lower() in ['true', 'verdadero', '1', 'yes', 'si']:
        return True
    elif value.lower() in ['false', 'falso', '0', 'no']:
        return False
    else:
        return default_value


def process_full_name(row, column_mapping, field_name, value):
    """Procesar nombre completo"""
    user_data = {}
    full_name = str(row.get(column_mapping.get('name', ''), '')).strip()
    
    if full_name and ' ' in full_name:
        parts = full_name.split(' ', 1)
        user_data['first_name'] = parts[0]
        user_data['last_name'] = parts[1] if len(parts) > 1 else ''
    else:
        user_data[field_name] = value
    
    return user_data


def apply_interpretation_rules(user_data, import_config, column_mapping):
    """Aplicar reglas de interpretación"""
    applied_rules = []
    rule_conflicts = []
    
    # Aplicar reglas sugeridas seleccionadas
    if import_config['selected_rules']:
        suggested_applied, suggested_conflicts = apply_suggested_rules(
            user_data, import_config, column_mapping
        )
        applied_rules.extend(suggested_applied)
        rule_conflicts.extend(suggested_conflicts)
    
    # Aplicar reglas personalizadas
    custom_applied, custom_conflicts = apply_dynamic_rules(
        user_data, 
        import_config.get('custom_rules', []), 
        column_mapping
    )
    applied_rules.extend(custom_applied)
    rule_conflicts.extend(custom_conflicts)
    
    return applied_rules, rule_conflicts


def apply_suggested_rules(user_data, import_config, column_mapping):
    """Aplicar reglas sugeridas"""
    applied_rules = []
    rule_conflicts = []
    
    for rule_name in import_config['selected_rules']:
        # Buscar la regla sugerida correspondiente
        for suggested_rule in import_config.get('suggested_rules', []):
            if suggested_rule['name'] == rule_name:
                # Verificar si el campo está mapeado
                if suggested_rule['field'] in column_mapping:
                    field_value = str(user_data.get(suggested_rule['field'], '')).strip()
                    should_apply = evaluate_rule_condition(
                        field_value, suggested_rule['operator'], suggested_rule['value']
                    )
                    
                    if should_apply:
                        # Verificar conflicto
                        if suggested_rule['action_field'] in user_data:
                            rule_conflicts.append({
                                'rule': rule_name,
                                'field': suggested_rule['action_field'],
                                'old_value': user_data[suggested_rule['action_field']],
                                'new_value': suggested_rule['action_value']
                            })
                        
                        user_data[suggested_rule['action_field']] = suggested_rule['action_value']
                        applied_rules.append(rule_name)
                break
    
    return applied_rules, rule_conflicts


def evaluate_rule_condition(field_value, operator, value):
    """Evaluar condición de regla"""
    if operator == 'contains':
        return value.lower() in field_value.lower()
    elif operator == 'equals':
        return field_value.lower() == value.lower()
    elif operator == 'starts_with':
        return field_value.lower().startswith(value.lower())
    elif operator == 'ends_with':
        return field_value.lower().endswith(value.lower())
    elif operator == 'not_equals':
        return field_value.lower() != value.lower()
    elif operator == 'not_contains':
        return value.lower() not in field_value.lower()
    return False


def add_default_configurations(user_data, import_config):
    """Agregar configuraciones por defecto"""
    user_data['password'] = import_config['default_password']
    if 'is_active' not in user_data:
        user_data['is_active'] = import_config['default_is_active']
    if 'can_access' not in user_data:
        user_data['can_access'] = import_config['default_can_access']
    user_data['must_change_password'] = import_config['default_must_change_password']


def process_import_data(df, column_mapping, import_config, request):
    """Procesar los datos de importación"""
    success_count = 0
    error_count = 0
    errors = []
    conflicts = []
    
    for index, row in df.iterrows():
        try:
            # Extraer datos según mapeo
            user_data = extract_user_data_from_row(row, column_mapping, import_config)
            
            # Aplicar reglas de interpretación
            applied_rules, rule_conflicts = apply_interpretation_rules(user_data, import_config, column_mapping)
            
            # Validar datos requeridos
            if not user_data.get('username') or not user_data.get('email'):
                errors.append(f'Fila {index + 1}: Username y email son obligatorios')
                error_count += 1
                continue
            
            # Verificar si usuario existe
            existing_user = User.objects.filter(username=user_data['username']).first()
            if existing_user and not import_config['update_existing']:
                conflicts.append(f'Fila {index + 1}: Usuario {user_data["username"]} ya existe')
                error_count += 1
                continue
            
            # Crear o actualizar usuario
            user = create_or_update_user(user_data, existing_user, import_config, request)
            
            # Asignar rol si se especifica
            if user_data.get('role'):
                assign_user_role(user, user_data['role'], request, errors, index)
            
            success_count += 1
            
        except Exception as e:
            errors.append(f'Fila {index + 1}: {str(e)}')
            error_count += 1
    
    return success_count, error_count, errors, conflicts


def create_or_update_user(user_data, existing_user, import_config, request):
    """Crear o actualizar usuario"""
    if existing_user and import_config['update_existing']:
        user = existing_user
        update_user_fields(user, user_data, import_config)
        user.save()
    else:
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            password=import_config['default_password'],
            company=request.user.company,
            title=user_data.get('title', ''),
            department=user_data.get('department', ''),
            location=user_data.get('location', ''),
            employee_number=user_data.get('employee_number', ''),
            sap_id=user_data.get('sap_id', ''),
            is_active=user_data.get('is_active', import_config['default_is_active']),
            can_access=user_data.get('can_access', import_config['default_can_access']),
            must_change_password=import_config['default_must_change_password']
        )
    
    return user


def update_user_fields(user, user_data, import_config):
    """Actualizar campos del usuario"""
    user.first_name = user_data.get('first_name', '')
    user.last_name = user_data.get('last_name', '')
    user.email = user_data.get('email', '')
    user.title = user_data.get('title', '')
    user.department = user_data.get('department', '')
    user.location = user_data.get('location', '')
    user.employee_number = user_data.get('employee_number', '')
    user.sap_id = user_data.get('sap_id', '')
    user.is_active = user_data.get('is_active', import_config['default_is_active'])
    user.can_access = user_data.get('can_access', import_config['default_can_access'])
    user.must_change_password = import_config['default_must_change_password']


def assign_user_role(user, role_name, request, errors, index):
    """Asignar rol al usuario"""
    role = Role.objects.filter(company=request.user.company, name=role_name).first()
    if role:
        # Eliminar roles existentes
        user.userrole_set.all().delete()
        UserRole.objects.create(user=user, role=role)
    else:
        # Si el rol no existe, crear un warning
        errors.append(f'Fila {index + 1}: Rol "{role_name}" no encontrado')
