"""
Health and readiness check endpoints
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import time


def health_check(request):
    """Liveness probe - is the app running?"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': time.time()
    })


def readiness_check(request):
    """Readiness probe - can the app serve traffic?"""
    checks = {}
    overall_status = 'ready'
    
    # Check database
    try:
        connection.ensure_connection()
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
        overall_status = 'not_ready'
    
    # Check Redis
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            checks['redis'] = 'ok'
        else:
            checks['redis'] = 'error: cache read failed'
            overall_status = 'not_ready'
    except Exception as e:
        checks['redis'] = f'error: {str(e)}'
        overall_status = 'not_ready'
    
    status_code = 200 if overall_status == 'ready' else 503
    
    return JsonResponse({
        'status': overall_status,
        'checks': checks,
        'timestamp': time.time()
    }, status=status_code)


def metrics(request):
    """Prometheus-compatible metrics endpoint"""
    # Simple metrics - can be expanded with prometheus_client
    from django.db import connections
    from django.contrib.auth import get_user_model
    from chat.models import Room, Message
    
    User = get_user_model()
    
    metrics_data = [
        f'# HELP relaydesk_users_total Total number of users',
        f'# TYPE relaydesk_users_total gauge',
        f'relaydesk_users_total {User.objects.count()}',
        '',
        f'# HELP relaydesk_rooms_total Total number of rooms',
        f'# TYPE relaydesk_rooms_total gauge',
        f'relaydesk_rooms_total {Room.objects.count()}',
        '',
        f'# HELP relaydesk_messages_total Total number of messages',
        f'# TYPE relaydesk_messages_total gauge',
        f'relaydesk_messages_total {Message.objects.count()}',
    ]
    
    return JsonResponse(
        '\n'.join(metrics_data),
        content_type='text/plain',
        safe=False
    )
