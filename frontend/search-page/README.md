# Unified Semantic Search Page

A production-grade React 18 + TypeScript standalone SPA providing AI-powered semantic search across all Ministry of Culture platforms.

## Overview

This is **Stream 11** of the RAG-Based Hindi & English, Search & QA System implementation. It's a full-page search interface (distinct from the chatbot widget in Stream 8) with:

- **AI-generated summaries** of search results (like Google AI Overview)
- **Multimedia results** (images/videos from Ministry websites)
- **Event discovery** (cultural events with dates and venues)
- **Faceted filtering** (source site, language, content type, date range)
- **Language support** for all 23 Indian scheduled languages
- **Voice search** capability
- **WCAG 2.1 AA accessibility**
- **GIGW compliance** (Government Emblem, bilingual header, footer, policies)

## Architecture

```
frontend/search-page/
├── src/
│   ├── main.tsx              # React entry point
│   ├── App.tsx               # Root component
│   ├── pages/
│   │   └── SearchPage.tsx    # Main layout
│   ├── components/           # Reusable UI components
│   ├── hooks/                # Custom React hooks
│   ├── services/             # API clients
│   ├── types/                # TypeScript interfaces
│   ├── i18n/                 # i18next translations
│   ├── styles/               # CSS files
│   └── utils/                # Constants & helpers
├── tests/                    # Unit & integration tests
├── Dockerfile                # Multi-stage build
├── nginx.conf                # Reverse proxy config
├── vite.config.ts            # Vite bundler config
└── package.json
```

## Technologies

- **React 18.3** + **TypeScript 5.6**
- **Vite 6** — Lightning-fast build tool
- **i18next** — Internationalization
- **React Markdown** — Result rendering
- **Vitest** — Unit testing

## Setup

### Prerequisites

- Node.js 20+
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Starts dev server at `http://localhost:5173` with hot reload.

### Build

```bash
npm run build
```

Outputs optimized production build to `dist/`.

### Testing

```bash
npm test
```

Runs Vitest in watch mode.

## API Integration

### Search Endpoint

```
POST /api/v1/search
{
  "query": "Indian heritage sites",
  "language": "en",
  "page": 1,
  "page_size": 20,
  "filters": {
    "source_sites": ["asi.nic.in"],
    "content_type": "webpage",
    "date_from": "2024-01-01",
    "date_to": null,
    "language": null
  }
}
```

**Response:**

```json
{
  "results": [
    {
      "title": "Protected Monuments",
      "url": "https://asi.nic.in/monuments",
      "snippet": "AI-generated summary...",
      "score": 0.91,
      "source_site": "asi.nic.in",
      "language": "en",
      "content_type": "webpage",
      "thumbnail_url": "...",
      "published_date": "2025-06-15"
    }
  ],
  "multimedia": [
    {
      "type": "image",
      "url": "https://asi.nic.in/image.jpg",
      "alt_text": "Monument photo",
      "source_site": "asi.nic.in",
      "thumbnail_url": "..."
    }
  ],
  "events": [
    {
      "title": "National Culture Festival 2026",
      "date": "2026-03-15",
      "venue": "New Delhi",
      "description": "Annual celebration...",
      "source_url": "https://culture.gov.in/events/...",
      "language": "en"
    }
  ],
  "ai_summary": {
    "summary": "Protected monuments in India...",
    "confidence": 0.87,
    "sources": ["asi.nic.in", "culture.gov.in"]
  },
  "total_results": 142,
  "page": 1,
  "page_size": 20,
  "cached": false
}
```

### Suggestions Endpoint

```
GET /api/v1/search/suggest?q=heritage&language=en
```

**Response:**

```json
{
  "suggestions": [
    { "text": "heritage sites", "category": "related", "language": "en" },
    { "text": "heritage monuments", "category": "trending", "language": "en" }
  ]
}
```

### Translation Endpoint

```
POST /api/v1/translate
{
  "text": "Ministry of Culture promotes Indian heritage",
  "source_language": "en",
  "target_language": "hi"
}
```

### Feedback Endpoint

```
POST /api/v1/feedback
{
  "result_id": "https://asi.nic.in/monuments",
  "query": "Indian heritage sites",
  "is_helpful": true,
  "feedback_text": "Very useful information",
  "language": "en"
}
```

## Features

### Search Bar

- **Prominent input field** at page top
- **Voice search** button (auto-detects language)
- **Autocomplete suggestions** (debounced, 300ms)
- **Clear button** for quick reset
- Accessible with ARIA labels

### AI Summary Panel

Displays top-of-results AI-generated answer:

- Summary text synthesized from top sources
- Confidence score (0-100%)
- Source attribution links
- Skeleton loader while fetching

### Result Cards

Each search result displays:

- **Title** (clickable, opens in new tab)
- **URL** (with domain normalization)
- **AI-generated snippet** (500 chars max)
- **Source badge** (site domain + icon)
- **Content type** (webpage/document/event/multimedia)
- **Published date** (localized format)
- **Thumbnail image** (120x120px, lazy-loaded)
- **Feedback widget** (👍 / 👎)

### Multimedia Results

Dedicated grid for images/videos:

- **Image lightbox** — click to enlarge
- **Video player** — HTML5 with controls
- **Alt text** for accessibility
- **Source attribution**

### Event Cards

Cultural events aggregated from Ministry sources:

- **Date & time** (localized format)
- **Venue** information
- **Description** snippet
- **"Learn More"** link

### Faceted Filters

Collapsible sidebar with:

- **Source websites** (checkboxes)
- **Content types** (webpage/document/event/multimedia)
- **Date range** (from/to date pickers)
- **Active filter badge** (count indicator)
- **"Clear Filters"** button

### Language Toggle

Dropdown to switch result language:

- All 23 Indian scheduled languages (ISO 639-1)
- Translates result titles/snippets on-demand
- Falls back to original if translation fails
- Stores preference in localStorage

### Accessibility Features

**WCAG 2.1 AA compliant:**

- Skip-to-content link
- ARIA landmarks (banner, main, contentinfo, region)
- Screen reader announcements (aria-live)
- Keyboard navigation (Tab, Enter, Escape)
- Focus indicators (3px outline)
- Semantic HTML

**Accessibility Controls Panel:**

- 🎨 **High contrast mode**
- 📝 **Large text** (+18px base font)
- 🎬 **Reduce motion** (disables animations)
- 👂 **Screen reader mode** (shows hidden text)
- 📖 **Dyslexic-friendly font** (OpenDyslexic)

Settings persist in localStorage.

### Pagination

- Numbered page buttons (1, 2, 3...)
- Ellipsis for gaps (1, 2, ..., 99, 100)
- "Previous" / "Next" buttons
- Current page highlighted
- Smooth scroll to top on page change

### Related Queries

"People also searched for" suggestions below results:

- Auto-populated from API
- Clickable to perform new search
- Category-based (trending, related, history)

### GIGW Compliance

Mandatory elements per §18 of Shared Contracts:

1. **Government of India Emblem** — prominently displayed in header
2. **Ministry Header** — "Ministry of Culture, Government of India" (English + Hindi)
3. **Language Toggle** — Hindi ↔ English + 21 other languages
4. **Footer Text**:
   - "Website Content Managed by Ministry of Culture"
   - "Designed, Developed and Hosted by NIC"
   - Last Updated date
5. **Footer Links**: Sitemap, Feedback, Terms, Privacy, Copyright, Hyperlinking, Accessibility
6. **Skip-to-content** — keyboard-accessible hidden link
7. **ARIA Landmarks** — role="banner", "main", "contentinfo", "navigation"

## Environment Variables

Create `.env.local`:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

For production Docker build, inject at runtime:

```bash
docker build --build-arg API_BASE_URL=/api/v1 .
```

## Docker Deployment

### Build

```bash
docker build -t rag-search-page:latest .
```

### Run

```bash
docker run -p 80:3000 rag-search-page:latest
```

### Health Check

```bash
curl http://localhost/health
```

Returns `200 OK` with `healthy` body.

## i18n Translations

All UI text in `/src/i18n/`:

- **en.json** — English translations
- **hi.json** — Hindi (हिंदी) translations

Add more languages by:

1. Creating new `.json` file with language code
2. Importing in `i18n/index.ts`
3. Adding to `SUPPORTED_LANGUAGES` in `utils/constants.ts`

## Testing

### Unit Tests

Test files in `/tests/`:

- `SearchPage.test.tsx` — page layout & GIGW elements
- `ResultCard.test.tsx` — result rendering & feedback
- `useSearch.test.ts` — search hook + debouncing

### Run Tests

```bash
npm test                 # Watch mode
npm run test:run         # Single run
npm run test:coverage    # With coverage
```

## Performance

- **Code splitting** via Vite (automatic)
- **Lazy loading** for images (native `loading="lazy"`)
- **Debounced search** (300ms default)
- **Result caching** (API-side, indicated by `cached: true`)
- **Gzip compression** (nginx)
- **Cache headers** for static assets (1-year expiry)

### Lighthouse Targets

- ✅ Performance: 90+
- ✅ Accessibility: 95+
- ✅ Best Practices: 90+
- ✅ SEO: 90+

## Error Handling

All API calls wrapped in try/catch:

```typescript
try {
  const response = await apiClient.search(request)
  setResults(response)
} catch (error) {
  setError(error instanceof Error ? error.message : 'Search failed')
}
```

Error Response Format (§4 of Shared Contracts):

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": {},
    "request_id": "uuid-v4"
  }
}
```

## Embeddable Search Bar

For Drupal header integration, include:

```html
<div id="rag-search-bar"></div>
<script src="https://search.culture.gov.in/embed.js"></script>
```

Lightweight (~5KB), no dependencies.

## Contributing

### Code Style

- TypeScript strict mode enabled
- ESLint + Prettier configured
- No console warnings/errors

### Before Commit

```bash
npm run lint               # Check ESLint
npm test                   # Run tests
npm run build              # Verify production build
```

## License

© Ministry of Culture. All rights reserved.

## Support

For issues or feature requests, contact:

- **Development**: dev-team@culture.gov.in
- **Architecture**: arch-team@culture.gov.in
