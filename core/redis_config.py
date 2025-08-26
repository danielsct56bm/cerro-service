"""
Configuración avanzada de Redis para la aplicación core
"""
import redis
from django.conf import settings
from django.core.cache import cache
import json
import logging

logger = logging.getLogger(__name__)

class RedisManager:
    """
    Gestor avanzado de Redis para operaciones complejas
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    def set_with_expiry(self, key, value, expiry=3600):
        """
        Establecer valor con tiempo de expiración
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.redis_client.setex(key, expiry, value)
        except Exception as e:
            logger.error(f"Error al establecer valor en Redis: {e}")
            return False
    
    def get_json(self, key):
        """
        Obtener valor JSON de Redis
        """
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except json.JSONDecodeError:
            logger.warning(f"Valor en Redis no es JSON válido para key: {key}")
            return None
        except Exception as e:
            logger.error(f"Error al obtener valor de Redis: {e}")
            return None
    
    def set_hash(self, hash_name, mapping, expiry=None):
        """
        Establecer hash en Redis
        """
        try:
            result = self.redis_client.hset(hash_name, mapping=mapping)
            if expiry:
                self.redis_client.expire(hash_name, expiry)
            return result
        except Exception as e:
            logger.error(f"Error al establecer hash en Redis: {e}")
            return False
    
    def get_hash(self, hash_name):
        """
        Obtener hash completo de Redis
        """
        try:
            return self.redis_client.hgetall(hash_name)
        except Exception as e:
            logger.error(f"Error al obtener hash de Redis: {e}")
            return {}
    
    def delete_pattern(self, pattern):
        """
        Eliminar todas las claves que coincidan con un patrón
        """
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error al eliminar patrón de Redis: {e}")
            return 0
    
    def increment_counter(self, key, amount=1, expiry=None):
        """
        Incrementar contador en Redis
        """
        try:
            result = self.redis_client.incr(key, amount)
            if expiry:
                self.redis_client.expire(key, expiry)
            return result
        except Exception as e:
            logger.error(f"Error al incrementar contador en Redis: {e}")
            return None
    
    def add_to_set(self, set_name, *values, expiry=None):
        """
        Agregar valores a un set en Redis
        """
        try:
            result = self.redis_client.sadd(set_name, *values)
            if expiry:
                self.redis_client.expire(set_name, expiry)
            return result
        except Exception as e:
            logger.error(f"Error al agregar a set en Redis: {e}")
            return False
    
    def get_set_members(self, set_name):
        """
        Obtener todos los miembros de un set
        """
        try:
            return self.redis_client.smembers(set_name)
        except Exception as e:
            logger.error(f"Error al obtener miembros del set: {e}")
            return set()
    
    def health_check(self):
        """
        Verificar estado de salud de Redis
        """
        try:
            self.redis_client.ping()
            info = self.redis_client.info()
            return {
                'status': 'healthy',
                'version': info.get('redis_version', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', 'N/A'),
                'uptime': info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

# Instancia global del gestor de Redis
redis_manager = RedisManager()

def get_redis_manager():
    """
    Obtener instancia del gestor de Redis
    """
    return redis_manager
