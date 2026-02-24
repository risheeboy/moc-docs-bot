---
description: Security and compliance rules
paths:
  - "**/*.py"
  - "**/*.ts"
  - "**/*.tsx"
---

# Security & Compliance Rules

## Input Validation

- All user inputs: validated via Pydantic schemas (Python) or TypeScript interfaces
- Never trust untrusted sources (web input, file uploads, API calls)
- Error messages: generic (never leak internal details)

## Database Security

- SQLAlchemy ORM only (never raw SQL)
- No f-strings in queries
- SQL injection prevention: parameterized queries always
- Connection: SSL/TLS required on RDS

## API Security

- CORS: restrict to ALB domain only (fix: speech-service, ocr-service, data-ingestion, llm-service allow_origins=["*"])
- Rate limiting: Redis-backed, per-role limits (admin=120, viewer=30 rpm)
- Authentication: disabled (`AUTH_ENABLED=false`), VPC isolation provides security

## Secrets Management

- No hardcoded secrets in code or config files
- Use: AWS Secrets Manager for credentials
- Env vars: load from Secrets Manager, never commit `.env` with real values
- Example: `.env.example` with dummy values

## Frontend Security

- XSS prevention: React auto-escapes, use DOMPurify for raw HTML
- Token storage: httpOnly cookies (fix: move from localStorage)
- CSRF tokens: on all state-changing forms
- Content-Security-Policy: headers configured

## Data Privacy

- PII handling: Aadhaar, PAN card, phone numbers redacted in LLM output
- Audit logging: all sensitive operations (upload, delete, search, chat)
- Data retention: analytics events 30-day TTL
- Encryption: S3 at-rest, Redis in-transit (SSL), RDS encrypted

## Compliance

- GIGW: Guidelines for Indian Government Websites
- WCAG 2.1 AA: accessibility compliance for all user-facing pages
- No telemetry to third parties without consent

## Checklist Before Commit

- [ ] No hardcoded secrets
- [ ] All user inputs validated
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF tokens on forms
- [ ] Rate limiting on public endpoints
- [ ] SSL/TLS for AWS communication
- [ ] Audit log for sensitive operations
