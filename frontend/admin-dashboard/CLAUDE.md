# Admin Dashboard

React 18 + TypeScript + Vite. Admin SPA for system management (10 pages: documents, conversations, feedback, analytics, scraping, models, users, config, audit logs, dashboard). Recharts for analytics, WebSocket for live updates, WCAG 2.1 AA compliant.

## Key Files

- `src/pages/Dashboard.tsx` — Overview, KPIs, health status
- `src/pages/Documents.tsx` — Document CRUD, bulk upload, chunking
- `src/pages/Conversations.tsx` — Conversation browser, export (CSV/JSON)
- `src/pages/Feedback.tsx` — Feedback review, rating, search
- `src/pages/Analytics.tsx` — Recharts visualizations (volume, latency, models)
- `src/pages/Scraping.tsx` — Scrape job management, WebSocket live updates
- `src/pages/ModelManagement.tsx` — Training jobs, evaluation, deployment
- `src/pages/Users.tsx` — User RBAC (admin, editor, viewer)
- `src/pages/Config.tsx` — System config, migrations, service health
- `src/pages/AuditLog.tsx` — Action audit trail with filters
- `src/components/Sidebar.tsx` — Navigation
- `src/hooks/useAuth.ts` — Auth state (JWT)
- `src/services/api.ts` — API client with auth header
- `vite.config.ts` — Build configuration

## Features

- **10 Pages**: Dashboard, Documents, Conversations, Feedback, Analytics, Scraping, Models, Users, Config, Audit Log
- **Role-Based UI**: Admin (full), Editor (docs/convos), Viewer (read-only)
- **React Query**: Server state caching (stale-while-revalidate)
- **Recharts**: Analytics visualizations
- **WebSocket**: Live scrape/training job updates
- **Pagination**: 50 rows per page default

## Authentication

- JWT token (localStorage, XSS risk)
- Role extraction from token
- Protected routes
- Role-based rendering

## Styling

- Tailwind CSS
- Responsive (mobile-first)
- Light/dark mode

## Known Issues

1. **localStorage XSS risk** — Auth tokens in localStorage. Use httpOnly cookies.
2. **Email validation** — User creation doesn't validate email properly.
3. **Export timeout** — Large CSV exports can timeout.
4. **Recharts lag** — Too many data points cause performance issues.
