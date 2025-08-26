"""
Configuración de rutas para WebSockets
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Canal para kioskos individuales
    re_path(r'ws/kiosk/(?P<kiosk_id>\w+)/$', consumers.KioskConsumer.as_asgi()),
    
    # Canal para técnicos (notificaciones de tickets)
    re_path(r'ws/technicians/(?P<company_id>\w+)/$', consumers.TechniciansConsumer.as_asgi()),
    
    # Canal para pantallas de turnos
    re_path(r'ws/display/(?P<company_id>\w+)/$', consumers.DisplayConsumer.as_asgi()),
]
