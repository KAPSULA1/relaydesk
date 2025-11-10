"""
ASGI config for relaydesk project.
Handles both HTTP and WebSocket connections with JWT authentication.
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

# Set default settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'relaydesk.settings')

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# Import routing and JWT middleware after Django setup
from relaydesk.routing import websocket_urlpatterns
from chat.middleware import JwtAuthMiddlewareStack

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # TEMPORARY: Removed AllowedHostsOriginValidator to test if it's blocking connections
    # The validator was rejecting WebSocket connections from Vercel frontend
    "websocket": JwtAuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),

    # ORIGINAL (commented out for testing):
    # "websocket": AllowedHostsOriginValidator(
    #     JwtAuthMiddlewareStack(
    #         URLRouter(websocket_urlpatterns)
    #     )
    # ),
})
