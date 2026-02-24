### STREAM 11: Frontend — Unified Semantic Search Page (**NEW**)

**Agent Goal:** Build the **full-page semantic search interface** — a standalone SPA that provides AI-powered search across all 30 Ministry of Culture ring-fenced platforms. This is a **separate interface from the chatbot**.

**Files to create:**
```
frontend/search-page/
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
│   │   ├── index.ts
│   │   ├── search.ts               # SearchResult, MultimediaResult, EventResult
│   │   └── api.ts
│   ├── pages/
│   │   └── SearchPage.tsx           # Main search page layout
│   ├── components/
│   │   ├── SearchBar.tsx            # Prominent search input + voice search button
│   │   ├── SearchResults.tsx        # Results list container
│   │   ├── ResultCard.tsx           # Individual result: title, AI summary, source link, thumbnail
│   │   ├── MultimediaResult.tsx     # Image/video result card (from source websites)
│   │   ├── EventCard.tsx            # Cultural event listing card (date, venue, description)
│   │   ├── AISummaryPanel.tsx       # AI-generated answer summary at top of results
│   │   ├── FacetFilters.tsx         # Filter by: source site, language, content type, date range
│   │   ├── LanguageToggle.tsx       # Switch result language (Hindi ↔ English ↔ other)
│   │   ├── Pagination.tsx           # Result pagination
│   │   ├── VoiceSearchButton.tsx    # Voice input for search query
│   │   ├── RelatedQueries.tsx       # "People also searched for" suggestions
│   │   ├── SourceBadge.tsx          # Badge showing originating website
│   │   └── AccessibilityControls.tsx
│   ├── hooks/
│   │   ├── useSearch.ts             # Search state, debounced query, result fetching
│   │   ├── useFilters.ts            # Facet filter state management
│   │   ├── useVoiceSearch.ts        # Voice input for search
│   │   └── useAccessibility.ts
│   ├── services/
│   │   ├── api.ts                   # Search API client (/api/v1/search, /api/v1/search/suggest)
│   │   └── audio.ts
│   ├── styles/
│   │   ├── globals.css
│   │   ├── search.css               # Search-specific styles
│   │   └── accessibility.css
│   ├── i18n/
│   │   ├── index.ts
│   │   ├── hi.json
│   │   └── en.json
│   └── utils/
│       └── constants.ts
├── embed.js                         # Optional: embed search bar on Drupal pages
└── tests/
    ├── SearchPage.test.tsx
    ├── ResultCard.test.tsx
    └── useSearch.test.ts
```

**Key features (from Requirements):**
- Prominent search bar with voice search capability
- **AI-generated summary** at top of results (like Google's AI Overview)
- Individual result cards with: title, AI-generated snippet, source link, thumbnail image
- **Multimedia results** — images and videos from originating Ministry websites
- **Event discovery** — cultural events aggregated from connected sites
- **Faceted filtering** — by source website, language, content type (document/event/media), date range
- **Language toggle** — view results translated into any scheduled Indian language
- "Related queries" / "People also searched" suggestions
- WCAG 2.1 AA accessible
- Embeddable search bar component for Drupal header integration

**No code dependencies on other streams** — calls `/api/v1/search` and `/api/v1/translate` endpoints.

**Shared Contracts Reference (from `01_Shared_Contracts.md`):**
- §1 Service Registry: API calls go to `/api/v1/search`, `/api/v1/search/suggest`, `/api/v1/translate`, `/api/v1/feedback`
- §4 Error Response Format: handle `{"error": {...}}` format from §4
- §8.1 Search API Response: TypeScript interfaces must match the `/search` response schema from §8.1 (results, multimedia, events arrays)
- §9 Language Codes: language toggle must support all 23 codes from §9
- §10 TypeScript Conventions: `snake_case` fields, no camelCase conversion
- §15 Frontend Standards: React 18, TypeScript 5.6+, Vite 6+, i18next, react-markdown, eventsource-parser
- §18 GIGW Elements: implement all 7 mandatory GIGW elements from §18

---


---

## Agent Prompt

### Agent 11: Unified Semantic Search Page (**NEW**)
```
PREREQUISITE: Read 00_Overview.md and 01_Shared_Contracts.md first.
API: /api/v1/search. TypeScript interfaces must match §8.1 search response schema.
Use GIGW from §18, deps from §15, language codes from §9.
Build a React 18 + TypeScript UNIFIED SEMANTIC SEARCH PAGE as a standalone SPA.
This is a SEPARATE interface from the chatbot — a full-page search experience.
Features:
- Prominent search bar with voice search capability
- AI-generated answer summary at top of results (like Google AI Overview)
- Result cards: title, AI snippet, source website badge, thumbnail image
- Multimedia results: images and videos from Ministry source websites
- Event discovery cards: cultural events with dates, venues, descriptions
- Faceted filters: source site, language, content type, date range
- Language toggle: translate results into any Indian scheduled language
- "Related queries" / auto-suggestions
- Pagination
- Feedback widget on search results (thumbs up/down)
- WCAG 2.1 AA accessible, Devanagari font support
- GIGW compliance (same as Agent 8): Government Emblem, Ministry header,
  bilingual toggle, standard footer, sitemap, policy links
- i18n (Hindi/English UI), Use Vite
Calls: /api/v1/search, /api/v1/search/suggest, /api/v1/translate, /api/v1/feedback
This is NOT the chatbot. This is the search results page.
```

