# Vistas de gestión de usuarios
from .user_management import user_management, user_detail, user_create, user_edit, user_delete
from .user_import import user_import, user_export
from .utils import apply_dynamic_rules

# Importar funciones de los módulos factorizados para acceso directo si es necesario
from .import_handlers import (
    handle_csv_upload,
    handle_column_mapping,
    handle_import_confirmation,
    cleanup_import_session
)
from .import_config import (
    process_import_config,
    prepare_step2_context,
    get_column_mapping_suggestions,
    get_available_fields,
    get_modifiable_fields,
    get_comparison_operators,
    get_suggested_rules,
    get_user_fields
)
from .data_processor import (
    generate_preview_data,
    process_import_data,
    extract_user_data_from_row,
    apply_interpretation_rules
)

__all__ = [
    # Vistas principales
    'user_management',
    'user_detail', 
    'user_create',
    'user_edit',
    'user_delete',
    'user_import',
    'user_export',
    'apply_dynamic_rules',
    
    # Funciones de importación factorizadas
    'handle_csv_upload',
    'handle_column_mapping',
    'handle_import_confirmation',
    'cleanup_import_session',
    'process_import_config',
    'prepare_step2_context',
    'get_column_mapping_suggestions',
    'get_available_fields',
    'get_modifiable_fields',
    'get_comparison_operators',
    'get_suggested_rules',
    'get_user_fields',
    'generate_preview_data',
    'process_import_data',
    'extract_user_data_from_row',
    'apply_interpretation_rules'
]
