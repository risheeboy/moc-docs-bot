# Technical Requirements

**Source:** Requirements.pdf pages 7-10

## AI / ML Requirements

### Models — Open Source Only
- All AI/ML models must be **open-source** (no proprietary API calls like OpenAI, Google, etc.)
- Models must run **on-premise** — no data leaves the hosting environment
- Must support **Hindi as primary language** with English as secondary

### Specific AI Capabilities

| Capability | Requirement |
|---|---|
| Conversational AI | Multi-turn, context-aware chatbot with source citations |
| Search | Semantic search with AI-generated summaries across 30 sites |
| Voice | Speech-to-text + Text-to-speech (Hindi + English) |
| Summarization | Summarize long documents and web pages |
| Sentiment Analysis | Analyze feedback text to determine sentiment (positive/negative/neutral) |
| OCR | Extract text from scanned documents and images (Hindi + English) |
| Translation | All 22 scheduled Indian languages |
| Multimodal | Search across text, images, videos |

### Chatbot Specific Requirements
- **Multi-turn conversations** with context retention
- **Source citations** — every response must cite the source document/URL
- **Fallback mechanism** — when confidence is low, provide graceful fallback: "I'm unable to find an answer. Please contact the Ministry helpline at [number] or email [address]."
- **Feedback collection** — thumbs up/down + optional text feedback on every response
- **Session management** — session timeout, context window management, session resumption

## Security Requirements

### Authentication & Authorization
- **Role-Based Access Control (RBAC)** with minimum roles:
  - Admin: full system access
  - Editor: manage documents, view analytics, trigger scrapes
  - Viewer: read-only analytics and conversation browser
  - API Consumer: chatbot + search API access only (for embedded widget)
- **JWT-based authentication** for API access
- **API key management** for external integrations

### Data Security
- **Encryption at rest** — all stored data must be encrypted (AES-256 or equivalent)
- **Encryption in transit** — all communications over TLS/HTTPS
- **Input sanitization** — protect against XSS, SQL injection, prompt injection
- **PII handling** — detect and redact personally identifiable information (Aadhaar numbers, phone numbers, etc.)
- **Audit trail** — log every API request with user, timestamp, action, IP address

### Rate Limiting
- API rate limiting to prevent abuse
- Configurable per-role rate limits

## Accessibility Requirements
- **WCAG 2.1 Level AA** compliance for all user-facing interfaces
- Keyboard navigation
- Screen reader compatibility
- Skip-to-content links
- Sufficient color contrast
- Font scaling support

## GIGW Compliance (Guidelines for Indian Government Websites)
Both user-facing interfaces must comply with GIGW:
- Government of India branding (National Emblem, "Ministry of Culture" header)
- Bilingual interface (Hindi + English) with language toggle prominently placed
- Standard footer: "Website Content Managed by Ministry of Culture", "Designed, Developed and Hosted by NIC", last updated date
- Mandatory links: Sitemap, Feedback, Terms & Conditions, Privacy Policy, Copyright Policy, Hyperlinking Policy
- S3WaaS (Secure, Scalable & Sugamya Website as a Service) alignment if applicable

## Data Handling
- **Data sovereignty** — all data must remain within India
- **No external API calls** — system must be fully self-contained
- **Data retention policy** — configurable retention periods for conversations, feedback, audit logs
- **Backup & Recovery** — automated daily backups with disaster recovery plan
