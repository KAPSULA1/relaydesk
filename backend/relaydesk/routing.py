"""
WebSocket Routing Configuration
Maps WebSocket URLs to consumers
"""
from django.urls import path
from chat.consumers import ChatConsumer

websocket_urlpatterns = [
    path('ws/chat/<slug:room_slug>/', ChatConsumer.as_asgi()),
]
