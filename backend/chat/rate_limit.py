"""
Redis-backed rate limiting middleware
"""
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import time


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limit requests by IP/user"""
    
    # Requests per window
    RATE_LIMITS = {
        'default': (100, 60),  # 100 requests per minute
        'auth': (5, 60),  # 5 login attempts per minute
        'api': (200, 60),  # 200 API calls per minute
    }
    
    def process_request(self, request):
        """Check rate limits before processing request"""
        if request.path.startswith('/admin/'):
            return None  # Skip admin
        
        # Determine limit type
        limit_type = 'default'
        if '/auth/' in request.path:
            limit_type = 'auth'
        elif '/api/' in request.path:
            limit_type = 'api'
        
        # Get client identifier
        client_id = self.get_client_id(request)
        cache_key = f"rate_limit:{limit_type}:{client_id}"
        
        # Check limit
        max_requests, window = self.RATE_LIMITS[limit_type]
        
        current_requests = cache.get(cache_key, [])
        now = time.time()
        
        # Remove old requests outside window
        current_requests = [req_time for req_time in current_requests if now - req_time < window]
        
        if len(current_requests) >= max_requests:
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'retry_after': int(window - (now - current_requests[0]))
            }, status=429)
        
        # Add current request
        current_requests.append(now)
        cache.set(cache_key, current_requests, timeout=window)
        
        return None
    
    def get_client_id(self, request):
        """Get unique client identifier"""
        # Try user ID first
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}"
        
        # Fall back to IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        return f"ip:{ip}"
