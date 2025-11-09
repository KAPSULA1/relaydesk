"""
Production-grade JWT authentication with HttpOnly cookies
Implements refresh token rotation and Redis-backed blacklist
"""
from datetime import timedelta
from django.conf import settings
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
import uuid


class SecureTokenManager:
    """Manages JWT tokens with HttpOnly cookies and rotation"""
    
    ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
    REFRESH_TOKEN_LIFETIME = timedelta(days=7)
    WS_TOKEN_LIFETIME = timedelta(minutes=5)
    
    BLACKLIST_PREFIX = "token:blacklist:"
    REFRESH_PREFIX = "token:refresh:"
    WS_TOKEN_PREFIX = "token:ws:"
    
    @classmethod
    def create_tokens(cls, user):
        """Create access and refresh tokens for user"""
        refresh = RefreshToken.for_user(user)
        refresh['user_id'] = user.id
        refresh['username'] = user.username
        refresh['jti'] = str(uuid.uuid4())
        
        # Store refresh token in Redis
        cache.set(
            f"{cls.REFRESH_PREFIX}{refresh['jti']}",
            str(refresh),
            timeout=int(cls.REFRESH_TOKEN_LIFETIME.total_seconds())
        )
        
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'access_expires': cls.ACCESS_TOKEN_LIFETIME.total_seconds(),
            'refresh_expires': cls.REFRESH_TOKEN_LIFETIME.total_seconds(),
        }
    
    @classmethod
    def create_ws_token(cls, user):
        """Create short-lived token for WebSocket authentication"""
        token_id = str(uuid.uuid4())
        token_data = {
            'user_id': user.id,
            'username': user.username,
            'type': 'websocket'
        }
        
        cache.set(
            f"{cls.WS_TOKEN_PREFIX}{token_id}",
            token_data,
            timeout=int(cls.WS_TOKEN_LIFETIME.total_seconds())
        )
        
        return token_id
    
    @classmethod
    def verify_ws_token(cls, token_id):
        """Verify and consume WebSocket token (one-time use)"""
        cache_key = f"{cls.WS_TOKEN_PREFIX}{token_id}"
        token_data = cache.get(cache_key)
        
        if token_data:
            cache.delete(cache_key)  # One-time use
            return token_data
        return None
    
    @classmethod
    def blacklist_token(cls, jti):
        """Add token to blacklist"""
        cache.set(
            f"{cls.BLACKLIST_PREFIX}{jti}",
            True,
            timeout=int(cls.REFRESH_TOKEN_LIFETIME.total_seconds())
        )
    
    @classmethod
    def is_blacklisted(cls, jti):
        """Check if token is blacklisted"""
        return cache.get(f"{cls.BLACKLIST_PREFIX}{jti}") is not None
    
    @classmethod
    def rotate_refresh_token(cls, old_refresh_token):
        """Rotate refresh token and blacklist old one"""
        try:
            token = RefreshToken(old_refresh_token)
            jti = token.get('jti')
            
            # Blacklist old token
            cls.blacklist_token(jti)
            
            # Create new tokens
            user_id = token.get('user_id')
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            
            return cls.create_tokens(user)
        except (TokenError, Exception):
            return None


def set_auth_cookies(response, tokens):
    """Set secure HttpOnly cookies for tokens"""
    # Access token cookie
    response.set_cookie(
        key='access_token',
        value=tokens['access'],
        max_age=int(tokens['access_expires']),
        httponly=True,
        secure=settings.SECURE_SSL_REDIRECT,
        samesite='Lax',
        domain=settings.SESSION_COOKIE_DOMAIN
    )
    
    # Refresh token cookie
    response.set_cookie(
        key='refresh_token',
        value=tokens['refresh'],
        max_age=int(tokens['refresh_expires']),
        httponly=True,
        secure=settings.SECURE_SSL_REDIRECT,
        samesite='Lax',
        domain=settings.SESSION_COOKIE_DOMAIN
    )
    
    return response


def clear_auth_cookies(response):
    """Clear authentication cookies"""
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response
