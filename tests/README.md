# 🧪 Testing - ServiceNow Cerro Verde

## 📁 Estructura
```
tests/
├── __init__.py
├── setup/                    # Tests del módulo setup
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_api.py
│   └── test_integration.py
├── login/                    # Tests del módulo login (futuro)
├── admin/                    # Tests del módulo admin (futuro)
└── e2e/                      # Tests end-to-end
    └── test_setup_flow.py
```

## 🚀 Comandos

```bash
# Todos los tests
python manage.py test

# Tests específicos
python manage.py test tests.setup
python manage.py test tests.e2e

# Con verbosidad
python manage.py test -v 2
```

## 📊 Cobertura

```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 🎯 Módulos Testeados

| Módulo | Status | Tests | Cobertura |
|--------|--------|-------|-----------|
| Setup | ✅ | 25 | 95% |
| Login | ⏳ | - | - |
| Admin | ⏳ | - | - |
| E2E | ✅ | 8 | 90% |

## 📝 Notas
- Usa Django unittest nativo
- Base de datos: SQLite en memoria
- Media: `test_media/` temporal
