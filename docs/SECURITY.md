# Security

## Threat model

| Asset | Threat | Control |
|---|---|---|
| API keys / secrets | Leaked to source control | `.env` via pydantic-settings; `detect-secrets` + `gitleaks` in CI |
| LinkedIn OAuth tokens | Stolen → account takeover | AES-GCM encrypted at rest in `sessions/`; never logged |
| Gmail OAuth tokens | Same | Same; IMAP over TLS only |
| Playwright cookies | Session hijack | AES-GCM encrypted; `sessions/` in `.gitignore` |
| Resume / cover letter PDFs | Privacy leak | Local only; `data/` in `.gitignore`; never cloud-synced |
| Structlog output | PII exposure | PII scrubber strips emails/phones before any log line |
| API endpoint | Unauthorised access | `APP_API_KEY` required on all routes; httpOnly cookie for browser |
| Celery tasks | Replay / duplicate send | Idempotency keys (SHA-256 of payload) stored in Redis |
| Form submissions | Duplicate application | No auto-retry; failure sets `form_failed`, alerts user |

## Key management

- All secrets in `.env` (gitignored). `.env.example` lists keys without values.
- Encryption key: `SECRET_KEY` env var → SHA-256 → 32-byte AES-GCM key.
- Rotate `SECRET_KEY` → re-encrypt all session files (`sessions/`).

## What is never logged

- Email addresses, phone numbers, names (scrubbed by PII processor)
- Email body content
- Message / DM content
- Resume text
- Auth tokens

## Checklist (sign before v1.0)

- [ ] `gitleaks` scan clean on full repo history
- [ ] `pip-audit` zero high-severity findings
- [ ] `npm audit` zero high-severity findings
- [ ] `detect-secrets` baseline committed, CI blocks new secrets
- [ ] All `sessions/` and `data/` entries confirmed gitignored
- [ ] Log scrubber unit tests pass on 10 PII-laden inputs (see `tests/test_logging.py`)
- [ ] CSP header present on dashboard (`next.config.ts`)
- [ ] AES-GCM encryption verified for cookies + LinkedIn token + Gmail token
- [ ] Alembic migrations reviewed — no `DROP TABLE` without explicit intent
