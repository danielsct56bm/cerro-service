"""
Consumers para WebSockets con Channels
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Kiosk, Ticket, TicketTurn


class KioskConsumer(AsyncWebsocketConsumer):
    """Consumer para comunicación con kioskos individuales"""
    
    async def connect(self):
        """Conectar al WebSocket"""
        self.kiosk_id = self.scope['url_route']['kwargs']['kiosk_id']
        self.room_group_name = f'kiosk_{self.kiosk_id}'
        
        # Verificar que el kiosco existe
        if await self.kiosk_exists():
            # Unirse al grupo del kiosco
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Actualizar último heartbeat
            await self.update_heartbeat()
            
            await self.accept()
            
            # Enviar mensaje de conexión exitosa
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Conectado al kiosco',
                'kiosk_id': self.kiosk_id
            }))
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        """Desconectar del WebSocket"""
        # Salir del grupo del kiosco
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recibir mensaje del WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'heartbeat':
                # Actualizar heartbeat
                await self.update_heartbeat()
                
                # Confirmar recepción
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat_confirmed',
                    'timestamp': timezone.now().isoformat()
                }))
            
            elif message_type == 'ticket_created':
                # Procesar creación de ticket desde kiosco
                await self.process_ticket_creation(data)
            
            elif message_type == 'status_update':
                # Actualizar estado del kiosco
                await self.update_kiosk_status(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato JSON inválido'
            }))
    
    async def kiosk_message(self, event):
        """Enviar mensaje al kiosco"""
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def kiosk_exists(self):
        """Verificar que el kiosco existe"""
        return Kiosk.objects.filter(id=self.kiosk_id).exists()
    
    @database_sync_to_async
    def update_heartbeat(self):
        """Actualizar último heartbeat del kiosco"""
        try:
            kiosk = Kiosk.objects.get(id=self.kiosk_id)
            kiosk.last_heartbeat = timezone.now()
            kiosk.save()
        except Kiosk.DoesNotExist:
            pass
    
    @database_sync_to_async
    def process_ticket_creation(self, data):
        """Procesar creación de ticket desde kiosco"""
        # TODO: Implementar lógica de creación de ticket
        pass
    
    @database_sync_to_async
    def update_kiosk_status(self, data):
        """Actualizar estado del kiosco"""
        # TODO: Implementar actualización de estado
        pass


class TechniciansConsumer(AsyncWebsocketConsumer):
    """Consumer para notificaciones a técnicos"""
    
    async def connect(self):
        """Conectar al WebSocket"""
        self.company_id = self.scope['url_route']['kwargs']['company_id']
        self.room_group_name = f'technicians_{self.company_id}'
        
        # Unirse al grupo de técnicos
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar mensaje de conexión exitosa
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado como técnico',
            'company_id': self.company_id
        }))
    
    async def disconnect(self, close_code):
        """Desconectar del WebSocket"""
        # Salir del grupo de técnicos
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recibir mensaje del WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'status_update':
                # Actualizar estado del técnico
                await self.update_technician_status(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato JSON inválido'
            }))
    
    async def technician_message(self, event):
        """Enviar mensaje al técnico"""
        await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def update_technician_status(self, data):
        """Actualizar estado del técnico"""
        # TODO: Implementar actualización de estado
        pass


class DisplayConsumer(AsyncWebsocketConsumer):
    """Consumer para pantallas de turnos"""
    
    async def connect(self):
        """Conectar al WebSocket"""
        self.company_id = self.scope['url_route']['kwargs']['company_id']
        self.room_group_name = f'display_{self.company_id}'
        
        # Unirse al grupo de pantallas
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar mensaje de conexión exitosa
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado a pantalla de turnos',
            'company_id': self.company_id
        }))
    
    async def disconnect(self, close_code):
        """Desconectar del WebSocket"""
        # Salir del grupo de pantallas
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recibir mensaje del WebSocket"""
        # Las pantallas solo reciben, no envían
        pass
    
    async def display_message(self, event):
        """Enviar mensaje a la pantalla"""
        await self.send(text_data=json.dumps(event))
