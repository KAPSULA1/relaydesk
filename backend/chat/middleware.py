"""
JWT Authentication Middleware for Django Channels
Extracts and validates JWT tokens from WebSocket connections
"""
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken, AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class JwtAuthMiddleware(BaseMiddleware):
    """
    Custom middleware for JWT authentication in WebSocket connections.

    Supports token extraction from:
    1. Sec-WebSocket-Protocol header: Bearer, <jwt> (RECOMMENDED - more secure)
    2. Query string: ?token=<jwt> (FALLBACK - less secure)

    Sets scope['user'] to authenticated user or AnonymousUser.
    """

    async def __call__(self, scope, receive, send):
        token = self.get_token_from_scope(scope)

        path = scope.get("path", "unknown")
        client = scope.get("client")
        logger.info(f"🔐 WebSocket auth attempt path={path} client={client}")

        if token:
            user = await self.get_user_from_token(token)
            scope['user'] = user

            if user.is_authenticated:
                logger.info(f"✅ WebSocket auth success: {user.username} (ID: {user.id})")
            else:
                logger.warning("⚠️ WebSocket auth failed: invalid token")
        else:
            scope['user'] = AnonymousUser()
            logger.warning("⚠️ WebSocket connection attempted without token")

        return await super().__call__(scope, receive, send)

    def get_token_from_scope(self, scope):
        """
        Extract JWT token from WebSocket scope.

        Primary source: query string (?token=...)
        Fallback: Sec-WebSocket-Protocol header (legacy)
        """
        query_string = scope.get('query_string', b'').decode('utf-8')
        if query_string:
            query_params = parse_qs(query_string)
            token_list = query_params.get('token', [])
            if token_list:
                logger.debug("Token extracted from query string")
                return token_list[0]

        headers = dict(scope.get('headers', []))
        protocol_header = headers.get(b'sec-websocket-protocol', b'').decode('utf-8')
        if protocol_header:
            parts = [p.strip() for p in protocol_header.split(',')]
            for part in parts:
                if part.lower() != 'bearer' and len(part) > 20:
                    logger.debug("Token extracted from Sec-WebSocket-Protocol header")
                    return part

        return None

    @database_sync_to_async
    def get_user_from_token(self, token):
        """
        Validate JWT token and return associated user.

        Args:
            token: JWT token string

        Returns:
            User: Authenticated user object or AnonymousUser if validation fails
        """
        try:
            # Step 1: Validate token structure and signature
            UntypedToken(token)

            # Step 2: Decode token to get user_id
            access_token = AccessToken(token)
            user_id = access_token['user_id']

            # Step 3: Fetch user from database
            user = User.objects.get(id=user_id)

            logger.debug(f"User {user.username} authenticated via JWT token")
            return user

        except (InvalidToken, TokenError) as e:
            logger.warning(f"JWT token validation failed: {e}")
            return AnonymousUser()
        except User.DoesNotExist:
            logger.warning(f"JWT token valid but user not found (user_id: {user_id})")
            return AnonymousUser()
        except Exception as e:
            logger.error(f"Unexpected error during JWT authentication: {e}")
            return AnonymousUser()


def JwtAuthMiddlewareStack(inner):
    """
    Helper function to apply JWT middleware (similar to AuthMiddlewareStack).

    Usage:
        from chat.middleware import JwtAuthMiddlewareStack

        application = ProtocolTypeRouter({
            "websocket": JwtAuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            ),
        })

    Args:
        inner: The inner ASGI application (typically URLRouter)

    Returns:
        JwtAuthMiddleware wrapped application
    """
    return JwtAuthMiddleware(inner)
