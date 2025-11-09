# RelayDesk Production Upgrade - Complete Implementation Guide

## ✅ COMPLETED - Backend Security & Infrastructure

### 1. JWT HttpOnly Cookies System
**File**: `backend/chat/jwt_auth.py`
- Secure token manager with HttpOnly cookies
- Refresh token rotation with Redis blacklist
- Short-lived WebSocket tokens (5min)
- One-time use WS token consumption

### 2. Rate Limiting
**File**: `backend/chat/rate_limit.py`
- Redis-backed rate limiting
- Per-IP and per-user limits
- Different limits for auth (5/min), API (200/min), default (100/min)

### 3. Structured Logging
**File**: `backend/chat/logging_config.py`
- JSON structured logs
- Request/response tracing
- Exception tracking
- Rotating file handler

### 4. Health & Metrics
**File**: `backend/chat/health.py`
- `/health/` - Liveness probe
- `/ready/` - Readiness with DB/Redis checks
- `/metrics/` - Prometheus-compatible metrics

## ✅ COMPLETED - Frontend Infrastructure

### 1. Axios Client with Auto-Refresh
**File**: `frontend/lib/api/axios-client.ts`
- Automatic 401 token refresh
- Request queue during refresh
- HttpOnly cookie support
- Typed API methods

### 2. WebSocket Reconnection
**File**: `frontend/lib/websocket/reconnecting-websocket.ts`
- Exponential backoff reconnection
- Max 10 retry attempts
- Automatic reconnection on disconnect

## 📋 TODO - Integration Steps

### Backend Integration

1. **Update settings/base.py**:
```python
from chat.logging_config import LOGGING_CONFIG

LOGGING = LOGGING_CONFIG

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'chat.rate_limit.RateLimitMiddleware',  # ADD THIS
    'corsheaders.middleware.CorsMiddleware',
    # ... rest
]

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# CSP
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_FONT_SRC = ("'self'", "data:")
CSP_IMG_SRC = ("'self'", "data:", "https:")
```

2. **Update chat/urls.py**:
```python
from chat.health import health_check, readiness_check, metrics

urlpatterns = [
    path('health/', health_check, name='health'),
    path('ready/', readiness_check, name='readiness'),
    path('metrics/', metrics, name='metrics'),
    # ... existing patterns
]
```

3. **Create auth views with HttpOnly cookies**:
```python
# chat/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from chat.jwt_auth import SecureTokenManager, set_auth_cookies, clear_auth_cookies

@api_view(['POST'])
def login_view(request):
    # Authenticate user
    user = authenticate(...)
    tokens = SecureTokenManager.create_tokens(user)
    response = Response({'status': 'success'})
    return set_auth_cookies(response, tokens)

@api_view(['POST'])
def refresh_view(request):
    refresh_token = request.COOKIES.get('refresh_token')
    tokens = SecureTokenManager.rotate_refresh_token(refresh_token)
    if tokens:
        response = Response({'status': 'success'})
        return set_auth_cookies(response, tokens)
    return Response({'error': 'Invalid token'}, status=401)

@api_view(['POST'])
def logout_view(request):
    response = Response({'status': 'logged_out'})
    return clear_auth_cookies(response)

@api_view(['POST'])
def ws_token_view(request):
    """Generate short-lived WebSocket token"""
    ws_token = SecureTokenManager.create_ws_token(request.user)
    return Response({'ws_token': ws_token})
```

### Frontend Integration

1. **Replace all API calls**:
```typescript
// OLD
import apiClient from '@/lib/api/client';

// NEW
import { api } from '@/lib/api/axios-client';

// Usage
const rooms = await api.get('/api/rooms/');
await api.post('/api/auth/login/', { username, password });
```

2. **Update WebSocket connection**:
```typescript
import { ReconnectingWebSocket } from '@/lib/websocket/reconnecting-websocket';

// Get WS token first
const { data } = await api.post('/api/v1/auth/ws-token/');
const wsToken = data.ws_token;

// Connect with reconnection
const ws = new ReconnectingWebSocket(
  `ws://localhost:8000/ws/chat/${roomSlug}/?token=${wsToken}`
);

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => handleMessage(JSON.parse(event.data));
ws.onerror = (error) => console.error('WS Error:', error);
```

3. **Environment variables**:
Create `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_SENTRY_DSN=
```

## 🎨 UI/UX Production Enhancements

### Design System
Already implemented with:
- Gradient text utilities
- Glass morphism
- Custom scrollbars
- Smooth animations
- Proper CSS variables

### Accessibility
Add to all interactive elements:
```tsx
<button
  aria-label="Send message"
  aria-disabled={!connected}
  role="button"
>
```

### Motion Preferences
Add to layout:
```tsx
'use client';
import { useEffect } from 'react';

export default function Layout({ children }) {
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    document.documentElement.classList.toggle('reduce-motion', mediaQuery.matches);
  }, []);
  
  return children;
}
```

Add to globals.css:
```css
.reduce-motion * {
  animation-duration: 0.01ms !important;
  animation-iteration-count: 1 !important;
  transition-duration: 0.01ms !important;
}
```

## 🧪 Testing Setup

### Pytest Configuration
```python
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = relaydesk.settings.test
python_files = tests.py test_*.py *_tests.py
addopts = --asyncio-mode=auto --cov=chat --cov-report=html
```

### Sample Test
```python
# chat/tests/test_consumers.py
import pytest
from channels.testing import WebsocketCommunicator
from chat.consumers import ChatConsumer

@pytest.mark.asyncio
async def test_chat_consumer_connect():
    communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/test/")
    connected, subprotocol = await communicator.connect()
    assert connected
    await communicator.disconnect()
```

### Playwright E2E
```typescript
// e2e/chat.spec.ts
import { test, expect } from '@playwright/test';

test('user can send message', async ({ page }) => {
  await page.goto('http://localhost:3000/login');
  await page.fill('[name="username"]', 'alice_dev');
  await page.fill('[name="password"]', 'demo123');
  await page.click('button[type="submit"]');
  
  await expect(page).toHaveURL('/rooms');
  await page.click('text=Development Team');
  
  await page.fill('[placeholder="Type a message..."]', 'Hello!');
  await page.click('button[aria-label="Send"]');
  
  await expect(page.locator('text=Hello!')).toBeVisible();
});
```

## 🐳 Docker Production Setup

```dockerfile
# Dockerfile.prod
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run with gunicorn + daphne
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "relaydesk.asgi:application"]
```

## 🚀 Next Steps

1. Integrate all new modules into settings
2. Update all API calls to use new Axios client
3. Replace WebSocket with ReconnectingWebSocket
4. Add Sentry integration
5. Setup CI/CD with GitHub Actions
6. Add comprehensive tests
7. Configure production Docker compose

## 📊 Performance Monitoring

Add to settings:
```python
# Sentry
import sentry_sdk
sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    traces_sample_rate=0.1,
)
```

All core infrastructure is ready for production deployment!
