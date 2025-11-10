"""
Custom Middleware for RelayDesk
"""
from django.utils.deprecation import MiddlewareMixin


class DisableCSRFForAPIMiddleware(MiddlewareMixin):
    """
    Disable CSRF protection for API endpoints that use JWT authentication.
    This middleware should be placed after CsrfViewMiddleware in settings.
    """
    def process_request(self, request):
        # Exempt all /api/ endpoints from CSRF verification
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None
