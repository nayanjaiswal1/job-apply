from __future__ import annotations

import re
import statistics

import structlog

log = structlog.get_logger()

_BANNED_VERBS = {
    "spearheaded", "leveraged", "orchestrated", "championed", "fostered",
    "utilized", "facilitated", "streamlined", "synergized", "revolutionized",
}
_EM_DASH_RE = re.compile(r"—")
_BULLET_RE = re.compile(r"^[•\-\*·]\s+(.+)", re.MULTILINE)


def _pattern_score(text: str) -> float:
    """Internal pattern-based AI signal (0.0–1.0). Always runs — no API needed."""
    signals = 0.0
    total = 0.0

    # Banned verb presence
    total += 1.0
    text_lower = text.lower()
    banned_count = sum(1 for v in _BANNED_VERBS if v in text_lower)
    signals += min(banned_count / 3.0, 1.0)

    # Em-dash density (LLM tell)
    total += 1.0
    em_dashes = len(_EM_DASH_RE.findall(text))
    signals += min(em_dashes / 5.0, 1.0)

    # Bullet length uniformity (all same length = AI signal)
    bullets = _BULLET_RE.findall(text)
    if len(bullets) >= 4:
        total += 1.0
        lengths = [len(b.split()) for b in bullets]
        variance = statistics.stdev(lengths) if len(lengths) >= 2 else 0.0
        signals += 1.0 if variance < 1.5 else 0.0

    return signals / total if total > 0 else 0.0


async def score(text: str) -> float:
    """Returns AI probability 0.0–1.0. GPTZero primary, pattern fallback."""
    pattern = _pattern_score(text)

    try:
        import gptzero  # type: ignore[import]
        result = gptzero.score(text)
        api_score = float(result.get("completely_generated_prob", pattern))
        log.info("ai_detector_api", score=api_score, pattern_score=pattern)
        return api_score
    except Exception as exc:
        log.warning("ai_detector_api_fail", reason=str(exc), fallback="pattern_only")
        return pattern
