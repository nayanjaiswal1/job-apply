# Runbook

## Start the stack

```bash
docker-compose up -d
uv run alembic upgrade head
uv run uvicorn job_agent.api.main:app --reload   # dev
cd ui && npm run dev                              # dev UI
```

## Common errors

### `/health` returns 503

Check which dep is down:
```bash
curl http://localhost:8000/health
# {"db":"fail","redis":"ok","chroma":"ok"}
docker-compose ps
docker-compose logs db
```

### Alembic `can't locate revision`

```bash
uv run alembic history
uv run alembic current
uv run alembic upgrade head
```

### Celery tasks not running

```bash
docker-compose logs redis
# Start worker:
uv run celery -A job_agent.queue.tasks worker --loglevel=info
```

### LinkedIn OAuth token expired

Token lives in `sessions/linkedin_token.json`. Delete it and re-run the OAuth flow:
```bash
rm sessions/linkedin_token.json
uv run python -m job_agent.graph --agent job_search
# Follow the printed auth URL
```

### DLQ entries accumulating

```bash
curl http://localhost:8000/api/v1/approvals/queue/dlq
```
Investigate the `error` field. Fix root cause, then clear:
```python
from job_agent.queue.dlq import DeadLetterQueue
import asyncio
dlq = DeadLetterQueue("redis://localhost:6379/0")
asyncio.run(dlq.clear())
```

### Manual state fix (application stuck)

```python
import asyncio
from job_agent.db.session import get_session
from job_agent.db.repositories.application_repo import ApplicationRepository

async def fix():
    async with get_session() as s:
        repo = ApplicationRepository(s)
        await repo.update_status("APP_ID_HERE", "withdrawn")

asyncio.run(fix())
```

## Backup

```bash
# Postgres dump
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Chroma snapshot (stop chromadb container first)
docker-compose stop chromadb
tar -czf chroma_$(date +%Y%m%d).tar.gz ./chroma_data
docker-compose start chromadb

# Resumes
rsync -av data/resumes/ ~/resumes_backup/
```

Keep 7 daily backups. Rotate with:
```bash
find ~/backups/ -name "*.sql" -mtime +7 -delete
```

## Rollback

1. `docker-compose down`
2. Restore Postgres: `psql $DATABASE_URL < backup_YYYYMMDD.sql`
3. Checkout previous tag: `git checkout v0.9`
4. `docker-compose up -d && uv run alembic upgrade head`
