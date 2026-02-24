# Search Page

React 18 + TypeScript + Vite. Standalone semantic search SPA with AI summaries, multimedia results, faceted filtering, event cards, WCAG 2.1 AA compliant.

## Key Files

- `src/components/SearchBar.tsx` — Search input with autocomplete, language selector
- `src/components/ResultsList.tsx` — Search results display
- `src/components/ResultCard.tsx` — Individual card (text, image, video)
- `src/components/EventCard.tsx` — Cultural event card with metadata
- `src/components/SummaryPanel.tsx` — AI-generated summary section
- `src/components/Filters.tsx` — Faceted filter sidebar
- `src/hooks/useSearch.ts` — Search state, caching, history
- `src/hooks/useFilters.ts` — Filter state, URL persistence
- `src/hooks/useResults.ts` — Result formatting, term highlighting
- `src/pages/SearchPage.tsx` — Main page layout
- `vite.config.ts` — Vite configuration

## Features

- **Semantic Search**: `/search` endpoint with query string, language, filters
- **Result Types**: Text excerpts, images, videos, cultural events
- **Faceted Filters**: Language, content type, category, date range, source
- **AI Summaries**: Bullet-point summaries from top N results
- **Event Cards**: Title, date, location, category, register link
- **Pagination**: Client-side, 20 results per page

## API Integration

- Endpoint: `POST /search`
- Filters: content_type, date_range, category, source, language
- Response: results array, facet counts, summary, total count

## Performance

- Debouncing: 300ms delay
- Virtualization: Large result sets
- Lazy loading: Images
- Caching: Recent searches in localStorage

## Accessibility

- WCAG 2.1 AA (contrast, focus, keyboard nav)
- GIGW (RTL, Indian languages)
- Screen reader announcements
- Focus management on updates

## Styling

- Responsive (mobile-first)
- Tailwind CSS + theme variables
- Light/dark mode toggle
- Print-friendly

## Known Issues

None critical. Page is stable.
