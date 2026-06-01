# Deploy

## Prerequisites

- Docker + Docker Compose
- Python 3.12 + uv
- Node 20+
- `.env` file populated from `.env.example`

## First-time setup

```bash
git clone <repo>
cd job-agent
cp .env.example .env
# Edit .env — fill in API keys

docker-compose up -d
uv sync
uv run alembic upgrade head

cd ui && npm install && npm run gen:api
```

Open `http://localhost:8000/docs` to verify API, `http://localhost:3000` for the dashboard.

## Tagging v1.0

```bash
uv run pytest --cov                              # must be green
uv run ruff check . && uv run mypy .             # must be clean
cd ui && npm run build                           # must succeed
git tag v1.0
```

## Rollback procedure

See `docs/RUNBOOK.md` → Rollback section.

## Cost estimate (--minimize mode, 6h run)

| Task | Model | Est. tokens/run | Est. cost |
|---|---|---|---|
| Job scoring (100 jobs) | gpt-4o-mini | 50K in / 5K out | ~$0.01 |
| Resume rewrite (3 apps) | ollama/llama3.1:8b | local | $0 |
| Cover letter (3) | ollama/mistral:7b | local | $0 |
| Mail classify (10) | groq/llama3-8b | ~5K in | ~$0.001 |
| **Total** | | | **~$0.01/day** |

Normal mode (cloud models): ~$0.50–$2/day depending on volume.
