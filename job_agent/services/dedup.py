from __future__ import annotations

import hashlib

import structlog

from job_agent.ports.scraper import Job

log = structlog.get_logger()

_FUZZY_THRESHOLD = 0.92


def job_id(title: str, company: str, location: str) -> str:
    """SHA-256(title+company+location) — canonical job dedup key."""
    raw = f"{title.lower().strip()}|{company.lower().strip()}|{location.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()


class DedupService:
    """Exact (SHA-256) + fuzzy (cosine > 0.92) deduplication for job listings."""

    def __init__(self, embedder=None) -> None:  # type: ignore[type-arg]
        self._embedder = embedder

    async def is_duplicate(
        self,
        job: Job,
        existing_ids: set[str],
        existing_embeddings: list[tuple[str, list[float]]] | None = None,
    ) -> bool:
        if job.id in existing_ids:
            log.info("dedup_exact_match", job_id=job.id)
            return True

        if self._embedder and existing_embeddings:
            jd_text = job.jd_text or f"{job.title} {job.company}"
            vec = await self._embedder.embed(jd_text)
            for eid, evec in existing_embeddings:
                sim = self._embedder.cosine_similarity(vec, evec)
                if sim > _FUZZY_THRESHOLD:
                    log.info("dedup_fuzzy_match", job_id=job.id, matched=eid, similarity=sim)
                    return True
        return False
