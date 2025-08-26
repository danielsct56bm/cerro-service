"""
Utilidades para el módulo de usuarios
"""

def apply_dynamic_rules(user_data, rules, column_mapping):
    """Aplicar reglas dinámicas a los datos del usuario"""
    applied_rules = []
    conflicts = []
    
    # Ordenar reglas por prioridad
    sorted_rules = sorted(rules, key=lambda x: x.get('priority', 1))
    
    for rule in sorted_rules:
        field = rule.get('field')
        operator = rule.get('operator')
        value = rule.get('value')
        action_field = rule.get('action_field')
        action_value = rule.get('action_value')
        
        # Verificar si el campo está mapeado
        if field not in column_mapping or field not in user_data:
            continue
            
        field_value = str(user_data[field]).strip()
        should_apply = False
        
        # Evaluar condición según operador
        if operator == 'equals':
            should_apply = field_value.lower() == value.lower()
        elif operator == 'contains':
            should_apply = value.lower() in field_value.lower()
        elif operator == 'starts_with':
            should_apply = field_value.lower().startswith(value.lower())
        elif operator == 'ends_with':
            should_apply = field_value.lower().endswith(value.lower())
        elif operator == 'not_equals':
            should_apply = field_value.lower() != value.lower()
        elif operator == 'not_contains':
            should_apply = value.lower() not in field_value.lower()
        
        if should_apply:
            # Verificar si hay conflicto
            if action_field in user_data:
                conflicts.append({
                    'rule': rule.get('name'),
                    'field': action_field,
                    'old_value': user_data[action_field],
                    'new_value': action_value
                })
            
            # Aplicar la regla
            user_data[action_field] = action_value
            applied_rules.append(rule.get('name'))
    
    return applied_rules, conflicts
