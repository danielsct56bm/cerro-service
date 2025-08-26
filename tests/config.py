"""
Configuración simple para testing
"""

# Configuración de base de datos para testing
TEST_DATABASE_CONFIG = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': ':memory:',
}

# Configuración de media para testing
TEST_MEDIA_ROOT = 'test_media'

# Configuración de logging para testing
TEST_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}
