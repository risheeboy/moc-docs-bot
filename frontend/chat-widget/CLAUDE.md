# Chat Widget

React 18 + TypeScript + Vite. Embeddable chat widget with Shadow DOM isolation, SSE streaming, voice I/O, WCAG 2.1 AA compliant.

## Key Files

- `src/components/ChatWindow.tsx` — Main widget container
- `src/components/MessageList.tsx` — Message rendering with Markdown
- `src/components/InputBar.tsx` — Text input + Send button
- `src/components/VoiceButton.tsx` — STT/TTS controls
- `src/hooks/useChat.ts` — Chat state, API, stream handling
- `src/hooks/useVoice.ts` — Web Audio microphone + playback
- `src/hooks/useAccessibility.ts` — WCAG helpers (ARIA, focus, screen reader)
- `src/services/api.ts` — Centralized API client
- `src/services/streaming.ts` — SSE stream handling
- `src/embed.js` — Widget embed script
- `vite.config.ts` — Vite configuration

## Architecture

- **Shadow DOM**: Style isolation from host page
- **SSE Streaming**: Server-Sent Events for real-time responses
- **Voice**: Web Audio API for STT/TTS
- **Accessibility**: WCAG 2.1 AA, ARIA labels, keyboard nav, screen reader support
- **Theming**: CSS variables (light/dark mode)

## API Integration

- Endpoint: `/chat` (API Gateway)
- Format: JSON request, SSE response stream
- Payload: `{ message: string, language: string, session_id?: string }`

## Styling

- Tailwind CSS + CSS variables
- Variables: `--primary-color`, `--text-color`, `--bg-color`, `--border-color`
- Light/dark mode toggle

## Build

- Tool: Vite
- Output: `dist/`
- Code splitting via dynamic imports

## Known Issues

1. **embed.js placeholder** — Doesn't load React app. Needs implementation.
2. **useChat race condition** — Stream handling uses setTimeout(100) instead of proper async/await.
3. **No reconnect logic** — Doesn't retry on network failure.
4. **localStorage for history** — Should use backend persistence.
