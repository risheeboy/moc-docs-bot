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

---


---

## Agent Prompt

### Agent 9: Admin Dashboard
```
Build a React 18 + TypeScript admin dashboard with pages for: login,
KPI dashboard (query volume, response time, active sessions, satisfaction),
analytics (language dist, topic trends, model usage via Langfuse),
document management (upload/delete/status), scrape job management
(view/trigger for 30 Ministry websites), conversation browser,
feedback + sentiment trends, system config (model settings, thresholds),
model monitoring (Langfuse-sourced LLM metrics), audit log.
Use Vite + Recharts. JWT authentication.
```

