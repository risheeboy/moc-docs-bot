### STREAM 9: Frontend — Admin Dashboard

**Agent Goal:** Build the admin dashboard for monitoring, analytics, document management, scrape job management, and system configuration.

**Files to create:**
```
frontend/admin-dashboard/
├── Dockerfile
├── nginx.conf
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── types/
│   │   └── index.ts
│   ├── pages/
│   │   ├── Login.tsx               # Admin login
│   │   ├── Dashboard.tsx           # KPI overview: query vol, response time, sessions
│   │   ├── Analytics.tsx           # Charts: language dist, topic dist, satisfaction
│   │   ├── Documents.tsx           # Upload/manage/delete documents
│   │   ├── ScrapeJobs.tsx          # View/trigger web scraping jobs for 30 sites
│   │   ├── Conversations.tsx       # Browse chat sessions and transcripts
│   │   ├── Feedback.tsx            # Feedback + sentiment analysis trends
│   │   ├── SystemConfig.tsx        # Model settings, thresholds, feature flags
│   │   ├── ModelMonitoring.tsx     # Langfuse-sourced LLM metrics (latency, cost, quality)
│   │   └── AuditLog.tsx            # Searchable audit trail
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── StatsCard.tsx
│   │   ├── ChartWrapper.tsx
│   │   ├── DataTable.tsx
│   │   ├── DocumentUploader.tsx
│   │   └── ProtectedRoute.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   └── useAnalytics.ts
│   ├── services/
│   │   └── api.ts
│   └── styles/
│       └── globals.css
└── tests/
    └── Dashboard.test.tsx
```

**No code dependencies on other streams.**

**Shared Contracts Reference (from `01_Shared_Contracts.md`):**
- §1 Service Registry: API calls go to `/api/v1/*` (NGINX → api-gateway:8000)
- §4 Error Response Format: handle `{"error": {...}}` format from §4
- §10 TypeScript Conventions: `snake_case` fields, no camelCase conversion
- §12 RBAC: dashboard is admin-only; handle 403 responses for unauthorized routes
- §15 Frontend Standards: React 18, TypeScript 5.6+, Vite 6+, Recharts, React Router, TanStack Table

---


---

## Agent Prompt

### Agent 9: Admin Dashboard
```
PREREQUISITE: Read 00_Overview.md and 01_Shared_Contracts.md first.
API base: /api/v1. Use deps from §15, TypeScript conventions from §10.
Build a React 18 + TypeScript admin dashboard with pages for: login,
KPI dashboard (query volume, response time, active sessions, satisfaction),
analytics (language dist, topic trends, model usage via Langfuse),
document management (upload/delete/status), scrape job management
(view/trigger for 30 Ministry websites), conversation browser,
feedback + sentiment trends, system config (model settings, thresholds),
model monitoring (Langfuse-sourced LLM metrics), audit log.
Use Vite + Recharts. JWT authentication.
```

