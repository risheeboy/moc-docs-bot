# Scope of Work

**Source:** Requirements.pdf pages 5-7

## Project Objective

Development, Implementation, and Maintenance of an AI-powered multilingual chatbot / RAG-based Q&A system for the Ministry of Culture website (culture.gov.in) and its approximately 30 affiliated platforms.

## Two User-Facing Interfaces

1. **Unified AI-Powered Search Interface** — A full-page semantic search experience across all 30 ring-fenced Ministry platforms. Features: AI-generated result summaries, multimedia results (images/videos from source sites), event listings, language toggle, faceted filtering.

2. **Conversational AI Chatbot** — An embeddable chat widget deployed on culture.gov.in (Drupal-based) via `<script>` tag. Features: multi-turn dialogue, voice input/output, source citations, feedback collection, context-aware follow-ups.

Both interfaces share the same backend API Gateway and services, but call different endpoints and render results differently.

## Core AI Features Required

1. **Conversational Chatbot** — Context-aware, multi-turn, with source citation and fallback/escalation
2. **Unified Search** — Semantic search across all 30 platforms with AI-generated summaries
3. **Voice Interaction** — Speech-to-text and text-to-speech in Hindi and English
4. **Content Summarization** — Summarize long documents and pages
5. **Sentiment Analysis** — Analyze user feedback sentiment for analytics
6. **OCR / Document Digitization** — Extract text from scanned documents and images (Hindi + English)
7. **Translation** — Support all 22 scheduled Indian languages
8. **Multimedia Search** — Search across images, videos, and documents from source websites

## Ring-Fenced Websites (Data Sources)

The system must crawl and index content from ~30 Ministry of Culture websites. Explicitly named in the RFP:

1. culture.gov.in (Primary Ministry site)
2. indianculture.gov.in (Indian Culture Portal)
3. mgmd.gov.in (Manuscripts & Graphics)
4. vedicheritage.gov.in (Vedic Heritage)
5. museumsofindia.gov.in (Museums of India)
6. gyanbharatam.com (Knowledge Platform)
7. abhilekh-patal.in (Archival System / Abhilekh Patal)
8. asi.nic.in (Archaeological Survey of India)
9. nationalmuseumindia.gov.in (National Museum)
10. sangeetnatak.gov.in (Sangeet Natak Akademi)
11. sahitya-akademi.gov.in (Sahitya Akademi)
12. ignca.gov.in (Indira Gandhi National Centre for the Arts)
13. nationalarchives.nic.in (National Archives)
14. ngmaindia.gov.in (National Gallery of Modern Art)
15. nmml.nic.in (Nehru Memorial Museum & Library)
16. indiaculture.gov.in
17. ccimindia.org (Centre for Cultural Resources and Training)
18-30. Remaining sites from RFP Annexure (to be provided by Ministry; contact: arit-culture@gov.in)

**Note:** The RFP states "around 30 affiliated platforms" and "+25 more websites maintained by associated departments and organisations under the Ministry" but only explicitly lists ~17 domains. The complete list is to be provided by the Ministry.

## Drupal Integration

The Ministry website (culture.gov.in) runs on **Drupal CMS**. The chatbot widget must be embeddable via a simple `<script>` tag injection into the Drupal site. The search page may be either embedded or linked as a standalone page.

## Content Types to Handle

- HTML web pages (static and JavaScript-rendered SPAs)
- PDF documents (including scanned/image-based PDFs requiring OCR)
- DOCX, TXT files
- Images (with metadata extraction)
- Videos (metadata and transcript extraction where available)
- Structured data (event listings, museum catalogs, archival records)
