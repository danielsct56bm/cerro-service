"""
Configuración de SQL Server para la aplicación core
"""
from django.db import connection
from django.conf import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Gestor de base de datos SQL Server
    """
    
    @staticmethod
    def execute_query(query, params=None):
        """
        Ejecutar consulta SQL con parámetros
        """
        try:
            with connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if query.strip().upper().startswith('SELECT'):
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                else:
                    connection.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            logger.error(f"Error ejecutando consulta: {e}")
            connection.rollback()
            raise
    
    @staticmethod
    def execute_many(query, params_list):
        """
        Ejecutar la misma consulta con múltiples conjuntos de parámetros
        """
        try:
            with connection.cursor() as cursor:
                cursor.executemany(query, params_list)
                connection.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error ejecutando múltiples consultas: {e}")
            connection.rollback()
            raise
    
    @staticmethod
    def get_table_info(table_name):
        """
        Obtener información de una tabla
        """
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """
        return DatabaseManager.execute_query(query, [table_name])
    
    @staticmethod
    def get_table_count(table_name):
        """
        Obtener número de registros en una tabla
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = DatabaseManager.execute_query(query)
        return result[0]['count'] if result else 0
    
    @staticmethod
    def check_table_exists(table_name):
        """
        Verificar si una tabla existe
        """
        query = """
        SELECT COUNT(*) as count 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_NAME = %s
        """
        result = DatabaseManager.execute_query(query, [table_name])
        return result[0]['count'] > 0 if result else False
    
    @staticmethod
    def get_database_info():
        """
        Obtener información general de la base de datos
        """
        queries = {
            'version': "SELECT @@VERSION as version",
            'database_name': "SELECT DB_NAME() as database_name",
            'server_name': "SELECT @@SERVERNAME as server_name",
            'table_count': "SELECT COUNT(*) as count FROM INFORMATION_SCHEMA.TABLES",
            'user_count': "SELECT COUNT(*) as count FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'",
            'size_info': """
                SELECT 
                    DB_NAME() as database_name,
                    SUM(size * 8 / 1024) as size_mb
                FROM sys.database_files
                GROUP BY type_desc
            """
        }
        
        info = {}
        for key, query in queries.items():
            try:
                result = DatabaseManager.execute_query(query)
                if result:
                    info[key] = result[0]
            except Exception as e:
                logger.warning(f"No se pudo obtener {key}: {e}")
                info[key] = None
        
        return info
    
    @staticmethod
    def health_check():
        """
        Verificar estado de salud de la base de datos
        """
        try:
            # Verificar conexión básica
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Obtener información de la base de datos
            db_info = DatabaseManager.get_database_info()
            
            return {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database_info': db_info
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    @staticmethod
    def backup_database_info():
        """
        Obtener información sobre backups de la base de datos
        """
        query = """
        SELECT 
            database_name,
            backup_start_date,
            backup_finish_date,
            backup_size,
            backup_type
        FROM msdb.dbo.backupset 
        WHERE database_name = DB_NAME()
        ORDER BY backup_start_date DESC
        """
        
        try:
            return DatabaseManager.execute_query(query)
        except Exception as e:
            logger.warning(f"No se pudo obtener información de backups: {e}")
            return []

def get_database_manager():
    """
    Obtener instancia del gestor de base de datos
    """
    return DatabaseManager()
