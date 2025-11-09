# RelayDesk Production Refactor - Execution Plan

## Phase 1: Backend Security & Architecture (EXECUTING NOW)
- JWT → HttpOnly cookies with refresh rotation
- Redis-backed token blacklist
- Rate limiting middleware
- CORS/CSRF/CSP/HSTS hardening
- /api/v1/auth/ws-token/ endpoint
- Structured logging + Sentry
- Health/readiness endpoints
- N+1 query optimization

## Phase 2: Frontend Architecture (EXECUTING NOW)
- Axios client with interceptors
- WebSocket reconnection/backoff/heartbeats
- Environment variable extraction
- Design system with CSS tokens
- Accessibility (WCAG 2.2 AA)
- Motion preferences respect

## Phase 3: Testing & CI/CD (EXECUTING NOW)
- pytest + pytest-asyncio
- Playwright E2E
- Multi-stage Dockerfiles
- GitHub Actions workflows

## Phase 4: UI Polish (EXECUTING NOW)
- Discord/Linear-grade design system
- Perfect typography hierarchy
- Professional spacing/shadows
- Smooth animations
- Responsive layout
