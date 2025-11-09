from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from .models import Room, Message
from .serializers import MessageSerializer
import logging

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        self.room_group_name = f'chat_{self.room_slug}'
        self.user = self.scope['user']
        logger.info(f"🔌 WebSocket connect attempt slug={self.room_slug} user={getattr(self.user, 'username', 'anonymous')}")
        
        if not self.user.is_authenticated:
            logger.warning("❌ WebSocket denied: unauthenticated user")
            await self.close()
            return
        
        room_exists = await self.check_room_exists()
        if not room_exists:
            logger.warning(f"❌ WebSocket denied: room {self.room_slug} not found or inactive")
            await self.close()
            return
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.add_to_presence()
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'user_joined', 'username': self.user.username, 'user_id': self.user.id}
        )
        
        logger.info(f"User {self.user.username} connected to {self.room_slug}")
    
    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.remove_from_presence()
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'user_left', 'username': self.user.username, 'user_id': self.user.id}
            )
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            logger.info(f"User {self.user.username} disconnected from {self.room_slug}")
    
    async def receive_json(self, content):
        try:
            logger.debug(f"📨 Received payload in {self.room_slug}: {content}")
            message_type = content.get('type', 'chat_message')
            if message_type == 'chat_message':
                await self.handle_chat_message(content)
            elif message_type == 'typing':
                await self.handle_typing(content)
        except Exception as e:
            logger.error(f"Error in receive_json for user {self.user.username}: {e}", exc_info=True)
            await self.send_json({'type': 'error', 'message': 'Failed to process message'})
    
    async def handle_chat_message(self, content):
        message_content = content.get('message', '').strip()
        if not message_content:
            return
        message = await self.save_message(message_content)
        if message:
            # ✅ FIX: Convert all UUID fields to strings before sending through Redis
            serialized_message = self.serialize_message(message)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'chat_message', 'message': serialized_message}
            )
    
    async def handle_typing(self, content):
        is_typing = content.get('is_typing', False)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'username': self.user.username,
                'user_id': self.user.id,
                'is_typing': is_typing
            }
        )
    
    def serialize_message(self, message):
        """Convert UUID fields to strings for Redis serialization"""
        if isinstance(message, dict):
            serialized = {}
            for key, value in message.items():
                if hasattr(value, 'hex'):  # Check if it's a UUID
                    serialized[key] = str(value)
                elif isinstance(value, dict):
                    serialized[key] = self.serialize_message(value)
                elif isinstance(value, list):
                    serialized[key] = [
                        self.serialize_message(item) if isinstance(item, dict) else str(item) if hasattr(item, 'hex') else item
                        for item in value
                    ]
                else:
                    serialized[key] = value
            return serialized
        return message
    
    async def chat_message(self, event):
        await self.send_json({'type': 'chat_message', 'message': event['message']})
    
    async def user_joined(self, event):
        online_users = await self.get_presence_list()
        await self.send_json({
            'type': 'user_joined',
            'username': event['username'],
            'user_id': event['user_id'],
            'online_users': online_users
        })
    
    async def user_left(self, event):
        online_users = await self.get_presence_list()
        await self.send_json({
            'type': 'user_left',
            'username': event['username'],
            'user_id': event['user_id'],
            'online_users': online_users
        })
    
    async def typing_indicator(self, event):
        if event['user_id'] != self.user.id:
            await self.send_json({
                'type': 'typing_indicator',
                'username': event['username'],
                'is_typing': event['is_typing']
            })
    
    @database_sync_to_async
    def check_room_exists(self):
        return Room.objects.filter(slug=self.room_slug, is_active=True).exists()
    
    @database_sync_to_async
    def save_message(self, content):
        try:
            room = Room.objects.get(slug=self.room_slug)
            message = Message.objects.create(room=room, user=self.user, content=content)
            serializer = MessageSerializer(message)
            return serializer.data
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None
    
    @database_sync_to_async
    def add_to_presence(self):
        cache_key = f"room_presence:{self.room_slug}"
        online_users = cache.get(cache_key, [])
        user_data = {'id': self.user.id, 'username': self.user.username}
        if user_data not in online_users:
            online_users.append(user_data)
            cache.set(cache_key, online_users, timeout=3600)

    @database_sync_to_async
    def remove_from_presence(self):
        cache_key = f"room_presence:{self.room_slug}"
        online_users = cache.get(cache_key, [])
        online_users = [u for u in online_users if u['id'] != self.user.id]
        if online_users:
            cache.set(cache_key, online_users, timeout=3600)
        else:
            cache.delete(cache_key)

    @database_sync_to_async
    def get_presence_list(self):
        cache_key = f"room_presence:{self.room_slug}"
        return cache.get(cache_key, [])
