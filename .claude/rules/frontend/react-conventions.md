---
description: React/TypeScript frontend conventions
paths:
  - "frontend/**/*.ts"
  - "frontend/**/*.tsx"
  - "frontend/**/*.css"
---

# React/TypeScript Conventions

## Component Structure

- React 18 functional components with hooks (no class components)
- One component per file, PascalCase naming (e.g., `SearchComponent.tsx`)
- TypeScript strict mode enabled in `tsconfig.json`
- Props: define interfaces, destructure in signature

```typescript
interface SearchProps {
  query: string;
  onResults: (docs: Document[]) => void;
}

export const SearchComponent: React.FC<SearchProps> = ({
  query,
  onResults
}) => {
  // Implementation
};
```

## State Management

- Server state: React Query (`useQuery`, `useMutation`)
- Client state: Zustand stores or React Context
- Never use Redux for this project

## Styling

- Tailwind CSS utility classes only (no inline styles, no CSS modules)
- No hardcoded colors—use Tailwind palette
- Responsive: mobile-first approach with `md:`, `lg:` prefixes

## API Integration

- Centralized: `src/services/api.ts` with typed API calls
- Error handling: standard error format from contracts
- Loading states: manage with React Query

## Accessibility (WCAG 2.1 AA)

- aria-labels on all interactive elements
- Keyboard navigation: Tab order logical
- Color contrast: 4.5:1 minimum for text
- Screen reader: semantic HTML

## Internationalization

- Support Hindi (primary) and English (secondary)
- Use i18n library (e.g., react-i18next)
- Language codes: `hi`, `en` from shared contracts

## Testing

- Unit tests: `*.test.tsx` with React Testing Library
- No snapshot tests (brittle)
- Test user interactions, not implementation

## Build

- Tool: Vite (configured in `vite.config.ts`)
- Output: `dist/`
- Env vars: VITE_* prefix for client-side exposure
