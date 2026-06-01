from __future__ import annotations

import re


_SECTION_WEIGHTS = {
    "experience": 0.5,
    "skills": 0.3,
    "education": 0.1,
    "summary": 0.1,
}


def score(resume_txt: str, jd_txt: str) -> float:
    """ATS keyword overlap score 0–100. Fast, no LLM."""
    jd_keywords = _extract_keywords(jd_txt)
    if not jd_keywords:
        return 0.0
    resume_words = set(_extract_keywords(resume_txt))
    overlap = jd_keywords & resume_words
    base = len(overlap) / len(jd_keywords) * 100

    # Bonus: section coverage (does resume have standard ATS sections?)
    section_bonus = 0.0
    for section in ("experience", "education", "skills", "summary", "objective"):
        if re.search(rf"\b{section}\b", resume_txt, re.I):
            section_bonus += 2.0

    return min(base + section_bonus, 100.0)


def _extract_keywords(text: str) -> set[str]:
    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#\-\.]{2,}\b", text.lower())
    stopwords = {
        "the", "and", "for", "with", "that", "this", "have", "will", "are",
        "you", "our", "your", "from", "not", "but", "all", "can", "been",
        "their", "they", "also", "more", "than", "when", "what", "some",
    }
    return {w for w in words if w not in stopwords}
