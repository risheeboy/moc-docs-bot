# Admin Dashboard - Ministry of Culture RAG System

A production-quality React 18 + TypeScript admin dashboard for managing the Hindi QA RAG system.

## Overview

The admin dashboard provides comprehensive monitoring, analytics, document management, and system configuration for the Ministry of Culture's AI-powered Q&A platform.

## Key Features

### Dashboard & Analytics
- **Real-time KPIs**: Query volume, response time, active sessions, user satisfaction
- **Charts & Analytics**: Language distribution, topic trends, model usage, satisfaction trends
- **Period Selection**: 24 hours, 7 days, 30 days, 90 days

### Document Management
- **Upload Interface**: Drag-and-drop document upload with progress tracking
- **Document Status**: Track processing status (pending, processing, completed, failed)
- **Bulk Operations**: View and manage all ingested documents

### Web Scraping
- **Job Management**: Trigger scrape jobs for 30 Ministry websites
- **Progress Tracking**: Real-time progress monitoring for crawls
- **Job History**: View status of all previous scrape jobs

### Conversation Browser
- **Session Browsing**: Search and filter user conversations
- **Transcript View**: Complete conversation history with timestamps
- **User Feedback**: Linked feedback and ratings

### Feedback & Sentiment Analysis
- **Sentiment Distribution**: Pie charts of positive/negative/neutral feedback
- **Rating Distribution**: Bar charts by star rating
- **Trends**: Sentiment trends over time

### System Configuration
- **RAG Settings**: Confidence threshold, top-k results, cache TTL
- **LLM Settings**: Temperature, max tokens
- **Session Timeout**: Idle timeout and max turns
- **Feature Flags**: Voice input, translation, OCR, sentiment analysis

### Model Monitoring (Langfuse Integration)
- **Per-Model Metrics**: Request volume, latency, token usage, cost
- **Performance Charts**: Visualizations of model performance
- **Cost Analysis**: Track per-model costs

### Audit Log
- **Activity Tracking**: All administrative actions logged
- **Searchable**: Filter by user, action, resource type
- **Security**: IP address logging, success/failure tracking

## Architecture

### Tech Stack
- **Frontend**: React 18, TypeScript 5.6+
- **UI Library**: Recharts for charts, TanStack React Table for data tables
- **Build Tool**: Vite 6
- **Styling**: CSS (no CSS-in-JS, vanilla CSS with CSS modules)
- **HTTP Client**: Axios with request/response interceptors
- **Routing**: React Router v7
- **Package Manager**: npm

### Project Structure

```
frontend/admin-dashboard/
├── src/
│   ├── pages/             # Full-page components
│   ├── components/        # Reusable UI components
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API client
│   ├── types/             # TypeScript interfaces
│   ├── styles/            # CSS files
│   ├── App.tsx            # Root component
│   └── main.tsx           # Entry point
├── tests/                 # Unit tests
├── Dockerfile             # Production Docker image
├── nginx.conf             # Nginx configuration
├── vite.config.ts         # Vite configuration
├── tsconfig.json          # TypeScript configuration
└── package.json           # Dependencies
```

## Getting Started

### Development

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API base URL
   ```

3. **Start development server**:
   ```bash
   npm run dev
   ```
   Opens at http://localhost:5173

4. **Build for production**:
   ```bash
   npm run build
   ```

### Docker Deployment

1. **Build image**:
   ```bash
   docker build -t admin-dashboard:1.0.0 .
   ```

2. **Run container**:
   ```bash
   docker run -p 80:80 \
     -e VITE_API_BASE_URL=/api/v1 \
     admin-dashboard:1.0.0
   ```

## API Integration

The dashboard communicates with the backend API Gateway at `/api/v1/`.

### Key Endpoints

**Authentication**:
- `POST /auth/login` - Login

**Dashboard**:
- `GET /admin/dashboard/metrics` - KPI metrics

**Analytics**:
- `GET /admin/analytics?period=7d` - Analytics data

**Documents**:
- `GET /admin/documents?page=1&page_size=20` - List documents
- `POST /admin/documents/upload` - Upload document
- `DELETE /admin/documents/{id}` - Delete document

**Scrape Jobs**:
- `GET /admin/scrape-jobs?page=1` - List jobs
- `POST /admin/scrape-jobs/trigger` - Trigger new job
- `GET /admin/scrape-jobs/{job_id}` - Get job status

**Conversations**:
- `GET /admin/conversations?page=1` - List conversations
- `GET /admin/conversations/{session_id}` - Get conversation detail

**Feedback**:
- `GET /admin/feedback?page=1` - List feedback
- `GET /admin/feedback/sentiment-summary?period=30d` - Sentiment summary

**System Config**:
- `GET /admin/config` - Get current config
- `PUT /admin/config` - Update config

**Model Monitoring**:
- `GET /admin/model-monitoring?period=7d` - Model metrics (from Langfuse)

**Audit Log**:
- `GET /admin/audit-log?page=1` - List audit entries with optional filters

## Authentication

Uses JWT tokens stored in localStorage. The API client automatically includes the `Authorization: Bearer {token}` header in all requests.

## Data Types

All API responses use `snake_case` field names. See `src/types/index.ts` for complete TypeScript interfaces.

## Styling

Global styles in `src/styles/globals.css` with page-specific overrides. Uses CSS variables for theming.

**Color Scheme**:
- Primary: #1f2937 (Dark slate)
- Accent: #3b82f6 (Blue)
- Success: #10b981 (Green)
- Danger: #ef4444 (Red)
- Warning: #f59e0b (Amber)

## Performance

- **Code Splitting**: Separate chunks for vendor, charts, and table libraries
- **Caching**: Browser caching for static assets (JS, CSS, images) with 1-year TTL
- **Compression**: Gzip compression enabled in Nginx
- **Lazy Loading**: Route-based code splitting via React Router

## Error Handling

All API errors follow the standard format:
```typescript
{
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id?: string;
  }
}
```

Errors are displayed in alert banners and logged to console.

## Testing

Run unit tests:
```bash
npm test
```

Tests use Vitest + React Testing Library.

## Security

- **HTTPS**: Enforced at NGINX layer (via reverse proxy)
- **CORS**: Configured for same-origin requests only
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, etc.
- **No Sensitive Data**: JWT tokens cleared on 401 responses
- **CSP**: Content Security Policy headers configured

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Deployment Notes

1. **Environment Variables**: Set `VITE_API_BASE_URL` at build time or runtime via Nginx
2. **Health Check**: `/health` endpoint returns 200 OK
3. **Static Assets**: Cached for 1 year with `Cache-Control: immutable`
4. **SPA Routing**: All non-file requests redirected to `index.html`

## Troubleshooting

### CORS Errors
- Ensure API Gateway is configured to accept requests from admin dashboard origin
- Check `CORS_ALLOWED_ORIGINS` in backend .env

### 401 Unauthorized
- Token may be expired. User will be redirected to login page
- Check token in browser localStorage

### API Calls Timing Out
- Increase timeout in `src/services/api.ts`
- Check API Gateway is healthy and reachable

## Contributing

1. Follow TypeScript strict mode
2. Add unit tests for new features
3. Use snake_case for API response fields
4. Document component prop types
5. Test on mobile (responsive design)

## License

Government of India - Ministry of Culture

## Contact

For support: arit-culture@gov.in
