"""
Vistas de gestión de usuarios - Archivo principal
Este archivo importa todas las vistas desde módulos especializados
"""

# Importar todas las vistas desde los módulos especializados
from .users.user_management import (
    user_management,
    user_detail,
    user_create,
    user_edit,
    user_delete
)

from .users.user_import import (
    user_import,
    user_export
)

from .users.utils import apply_dynamic_rules

# Exportar todas las funciones para mantener compatibilidad
__all__ = [
    'user_management',
    'user_detail',
    'user_create',
    'user_edit',
    'user_delete',
    'user_import',
    'user_export',
    'apply_dynamic_rules'
]
