### STREAM 8: Frontend — Conversational Chatbot Widget

**Agent Goal:** Build the React-based conversational chat widget that can be embedded on the Drupal website via a `<script>` tag.

**Files to create:**
```
frontend/chat-widget/
├── Dockerfile                      # node:20-alpine build → nginx:alpine serve
├── nginx.conf
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── public/
│   └── favicon.ico
├── src/
│   ├── main.tsx                    # Entry point
│   ├── App.tsx
│   ├── types/
│   │   ├── index.ts
│   │   ├── chat.ts                 # Message, Session, Source types
│   │   └── api.ts                  # API response types
│   ├── components/
│   │   ├── ChatWidget.tsx          # Floating bubble + expandable panel
│   │   ├── ChatWindow.tsx          # Message list + input area
│   │   ├── MessageBubble.tsx       # User/bot message with markdown + sources
│   │   ├── InputArea.tsx           # Text input + send + voice + language selector
│   │   ├── VoiceButton.tsx         # Push-to-talk voice input
│   │   ├── SourceCard.tsx          # Clickable source citations with links
│   │   ├── FeedbackWidget.tsx      # Thumbs up/down + text feedback form
│   │   ├── LanguageSelector.tsx    # Hindi, English, + other scheduled languages
│   │   ├── TypingIndicator.tsx     # Bot typing animation
│   │   ├── AudioPlayer.tsx         # Play TTS audio response
│   │   ├── FileUpload.tsx          # Upload document for OCR/query
│   │   └── AccessibilityControls.tsx # Font size, contrast, screen reader
│   ├── hooks/
│   │   ├── useChat.ts              # Chat state, multi-turn context, SSE streaming
│   │   ├── useVoice.ts             # Voice recording + STT
│   │   ├── useTTS.ts               # Text-to-speech playback
│   │   └── useAccessibility.ts     # Font size, contrast state
│   ├── services/
│   │   ├── api.ts                  # API client (chat, feedback, voice, translate)
│   │   ├── streaming.ts            # SSE client for streamed responses
│   │   └── audio.ts                # Audio recording/playback
│   ├── styles/
│   │   ├── globals.css
│   │   ├── widget.css
│   │   └── accessibility.css
│   ├── i18n/
│   │   ├── index.ts
│   │   ├── hi.json                 # Hindi UI strings
│   │   └── en.json                 # English UI strings
│   └── utils/
│       ├── markdown.ts
│       └── constants.ts
├── embed.js                        # Standalone embed script for Drupal
└── tests/
    ├── ChatWidget.test.tsx
    ├── MessageBubble.test.tsx
    └── useChat.test.ts
```

**Key requirements:**
- Embeddable as `<script src="embed.js"></script>` on culture.gov.in (Drupal)
- **Shadow DOM** encapsulation to prevent CSS conflicts with host Drupal site
- Multi-turn conversational memory (context window management)
- WCAG 2.1 AA: keyboard nav, ARIA, screen reader, high contrast, font resize
- Streaming responses via SSE
- Voice input/output (STT + TTS)
- Source citations with clickable links
- Hindi/English UI + Devanagari font support
- CORS configured for culture.gov.in origin

**No code dependencies on other streams.**

---

**Shared Contracts Reference (from `01_Shared_Contracts.md`):**
- §1 Service Registry: API calls go to `/api/v1/*` (via NGINX reverse proxy to api-gateway:8000)
- §4 Error Response Format: handle error responses in `{"error": {...}}` format from §4
- §9 Language Codes: language selector must support all 23 codes from §9 (at minimum `hi` and `en` prominently)
- §10 TypeScript Conventions: use `snake_case` field names matching API responses (no camelCase conversion)
- §13 Chatbot Fallback: display exact fallback messages from §13 when API returns fallback
- §15 Frontend Standards: use React 18, TypeScript 5.6+, Vite 6+, i18next, react-markdown, eventsource-parser
- §18 GIGW Elements: implement all 7 mandatory GIGW elements from §18

---

## Agent Prompt

### Agent 8: Conversational Chatbot Widget
```
Build a React 18 + TypeScript CONVERSATIONAL CHATBOT widget embeddable via
<script> tag on culture.gov.in (Drupal).
PREREQUISITE: Read 00_Overview.md and 01_Shared_Contracts.md first.
API base: /api/v1. Use TypeScript conventions from §10, GIGW from §18, deps from §15.

Use Shadow DOM encapsulation to prevent CSS conflicts with host Drupal site.
Features: multi-turn chat with context memory, text + voice input,
SSE streaming responses, markdown rendering, source citations with clickable
links, feedback (thumbs up/down + text), language selector (Hindi/English),
TTS audio playback, file upload for OCR/query.
Accessibility: WCAG 2.1 AA (keyboard nav, ARIA, high contrast, font resize).
GIGW compliance (Guidelines for Indian Government Websites):
  - Government of India Emblem + "Ministry of Culture" header
  - Bilingual interface (Hindi + English) with language toggle prominently placed
  - Screen reader compatible, keyboard navigation, skip-to-content link
  - Standard footer: "Website Content Managed by Ministry of Culture",
    "Designed, Developed and Hosted by NIC", last updated date
  - Sitemap, feedback, terms, privacy policy, copyright, hyperlinking policy links
i18n with Hindi UI strings. Devanagari font support. Use Vite.
This is the CHATBOT interface (not the search page).
```

