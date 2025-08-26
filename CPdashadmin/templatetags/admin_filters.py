from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtener un valor de un diccionario usando una clave"""
    return dictionary.get(key, '')

@register.filter
def split(value, arg):
    """Dividir una cadena en una lista usando un separador"""
    return value.split(arg)

@register.filter
def is_in(value, arg):
    """Verificar si un valor está en una lista"""
    if isinstance(arg, str):
        arg = arg.split(',')
    return value in arg
