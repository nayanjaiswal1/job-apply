FROM python:3.12-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
RUN uv pip install --system --no-cache --extra dev .

FROM python:3.12-slim AS runtime

RUN adduser --system --no-create-home --uid 1001 appuser

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY job_agent/ ./job_agent/
COPY config.yaml .

RUN install -d -o appuser /app/data/resumes /app/data/cover_letters /app/logs/screenshots

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

EXPOSE 8000

CMD ["uvicorn", "job_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
