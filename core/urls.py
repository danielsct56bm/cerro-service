"""
URLs para la aplicación core - Organizadas por funcionalidad
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # Kiosks
    KioskViewSet, GenerateKioskUrlAPIView, KioskRegistrationAPIView,
    
    # Tickets
    TicketViewSet, TicketTurnViewSet, KioskTemplatesAPIView, GenerateTicketOrderAPIView,
    
    # Upload
    FileUploadAPIView,
    
    # Kiosk views
    kiosk_view, kiosk_status, kiosk_categories, kiosk_subcategories,
    kiosk_template, kiosk_generate_ticket, kiosk_health,
)

# Router para ViewSets con prefijos organizados
router = DefaultRouter()

# Kioskos y Tickets - Solo endpoints públicos
router.register(r'kiosks', KioskViewSet, basename='kiosk')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'ticket-turns', TicketTurnViewSet, basename='ticket-turn')

# URLs de la API
urlpatterns = [
    # Router de ViewSets
    path('', include(router.urls)),
    
    # Endpoints especiales de kioskos
    path('kiosks/generate-registration-url/', GenerateKioskUrlAPIView.as_view(), name='generate-kiosk-url'),
    path('kiosks/register/<str:token>/', KioskRegistrationAPIView.as_view(), name='kiosk-registration'),
    
    # Endpoints de tickets para kioskos
    path('kiosks/templates/', KioskTemplatesAPIView.as_view(), name='kiosk-templates'),
    path('kiosks/generate-ticket-order/', GenerateTicketOrderAPIView.as_view(), name='generate-ticket-order'),
    
    # Endpoint de upload de archivos
    path('upload/', FileUploadAPIView.as_view(), name='file-upload'),

    # Kiosk URLs
    path('kiosk/', kiosk_view, name='kiosk'),
    path('api/kiosk/status/', kiosk_status, name='kiosk_status'),
    path('api/kiosk/categories/', kiosk_categories, name='kiosk_categories'),
    path('api/kiosk/categories/<int:category_id>/subcategories/', kiosk_subcategories, name='kiosk_subcategories'),
    path('api/kiosk/categories/<int:category_id>/template/', kiosk_template, name='kiosk_template'),
    path('api/kiosk/generate-ticket/', kiosk_generate_ticket, name='kiosk_generate_ticket'),
    path('api/health/', kiosk_health, name='kiosk_health'),
]
