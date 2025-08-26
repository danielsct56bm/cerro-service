"""
Manejadores específicos para la importación de usuarios desde CSV
"""
from django.shortcuts import render, redirect
from django.contrib import messages
import pandas as pd
import io
import chardet


def handle_csv_upload(request):
    """Manejar la carga del archivo CSV"""
    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        messages.error(request, 'Por favor seleccione un archivo CSV.')
        return redirect('CPdashadmin:user_import')
    
    if not csv_file.name.lower().endswith(('.csv', '.txt')):
        messages.error(request, 'El archivo debe ser un CSV o TXT.')
        return redirect('CPdashadmin:user_import')
    
    try:
        # Leer el contenido del archivo
        file_content = csv_file.read()
        
        # Detectar codificación
        detected = chardet.detect(file_content)
        encoding = detected['encoding'] if detected['confidence'] > 0.7 else 'utf-8'
        
        # Intentar decodificar con la codificación detectada
        try:
            decoded_content = file_content.decode(encoding)
        except UnicodeDecodeError:
            # Fallback a UTF-8
            decoded_content = file_content.decode('utf-8', errors='ignore')
        
        # Detectar delimitador
        detected_delimiter = detect_delimiter(decoded_content)
        
        # Leer CSV con parámetros detectados
        df = pd.read_csv(
            io.StringIO(decoded_content), 
            delimiter=detected_delimiter,
            nrows=10,
            encoding=encoding,
            header=0
        )
        
        # Verificar problemas en el CSV
        duplicate_columns = df.columns[df.columns.duplicated()].tolist()
        problematic_columns = detect_problematic_columns(df)
        
        if duplicate_columns:
            messages.warning(request, f'Columnas duplicadas detectadas: {", ".join(duplicate_columns)}. Esto puede causar problemas.')
        
        if problematic_columns:
            messages.warning(request, f'Columnas problemáticas detectadas: {", ".join(problematic_columns)}')
        
        # Guardar en sesión para el siguiente paso
        save_csv_session_data(request, decoded_content, df, detected_delimiter, encoding, duplicate_columns, problematic_columns)
        
        return df, detected_delimiter, encoding, duplicate_columns, problematic_columns
        
    except Exception as e:
        messages.error(request, f'Error al leer el archivo CSV: {str(e)}')
        return None, None, None, None, None


def detect_delimiter(content):
    """Detectar el delimitador del CSV"""
    delimiters = [',', ';', '\t', '|']
    detected_delimiter = ','
    
    for delimiter in delimiters:
        try:
            df_test = pd.read_csv(io.StringIO(content), delimiter=delimiter, nrows=1)
            if len(df_test.columns) > 1:
                detected_delimiter = delimiter
                break
        except:
            continue
    
    return detected_delimiter


def detect_problematic_columns(df):
    """Detectar columnas problemáticas en el CSV"""
    problematic_columns = []
    for col in df.columns:
        if pd.isna(col) or str(col).strip() == '':
            problematic_columns.append(f'Columna sin nombre en posición {list(df.columns).index(col) + 1}')
        elif str(col).startswith('Unnamed:'):
            problematic_columns.append(f'Columna sin nombre: {col}')
    
    return problematic_columns


def save_csv_session_data(request, decoded_content, df, delimiter, encoding, duplicate_columns, problematic_columns):
    """Guardar datos del CSV en la sesión"""
    request.session['csv_data'] = decoded_content
    request.session['csv_columns'] = df.columns.tolist()
    request.session['csv_preview'] = df.head().to_dict('records')
    request.session['csv_delimiter'] = delimiter
    request.session['csv_encoding'] = encoding
    request.session['csv_has_headers'] = True
    request.session['duplicate_columns'] = duplicate_columns
    request.session['problematic_columns'] = problematic_columns


def handle_column_mapping(request):
    """Manejar el mapeo de columnas"""
    csv_data = request.session.get('csv_data')
    if not csv_data:
        messages.error(request, 'No hay datos CSV cargados.')
        return redirect('CPdashadmin:user_import')
    
    # Obtener mapeo de columnas
    column_mapping = extract_column_mapping(request)
    
    # Validar campos requeridos
    missing_fields = validate_required_fields(column_mapping)
    if missing_fields:
        messages.error(request, f'Los siguientes campos son obligatorios: {", ".join(missing_fields)}')
        return redirect('CPdashadmin:user_import')
    
    return column_mapping


def extract_column_mapping(request):
    """Extraer el mapeo de columnas del formulario"""
    column_mapping = {}
    field_names = ['username', 'email', 'first_name', 'last_name', 'title', 'department', 'location', 'employee_number', 'sap_id', 'role', 'is_active']
    
    for field_name in field_names:
        csv_column = request.POST.get(f'map_{field_name}')
        if csv_column:
            column_mapping[field_name] = csv_column
    
    return column_mapping


def validate_required_fields(column_mapping):
    """Validar campos requeridos"""
    required_fields = ['username', 'email']
    missing_fields = [field for field in required_fields if field not in column_mapping]
    return missing_fields


def handle_import_confirmation(request):
    """Manejar la confirmación de importación"""
    csv_data = request.session.get('csv_data')
    column_mapping = request.session.get('column_mapping')
    import_config = request.session.get('import_config')
    
    if not all([csv_data, column_mapping, import_config]):
        messages.error(request, 'Datos de importación incompletos.')
        return redirect('CPdashadmin:user_import')
    
    try:
        df = pd.read_csv(
            io.StringIO(csv_data),
            delimiter=import_config['delimiter'],
            encoding=import_config['encoding'],
            header=0
        )
        
        return df
        
    except Exception as e:
        messages.error(request, f'Error durante la importación: {str(e)}')
        return None


def cleanup_import_session(request):
    """Limpiar datos de sesión de importación"""
    session_keys = [
        'csv_data', 'csv_columns', 'csv_preview', 'column_mapping', 
        'import_config', 'csv_delimiter', 'csv_encoding', 'csv_has_headers', 
        'duplicate_columns', 'problematic_columns'
    ]
    
    for key in session_keys:
        request.session.pop(key, None)
