from __future__ import annotations

import structlog

from job_agent.errors import HumanReviewNeeded

log = structlog.get_logger()

_FIELD_MAP = {
    "name": ["full_name", "name", "applicant_name"],
    "email": ["email", "email_address"],
    "phone": ["phone", "mobile", "contact"],
    "years_exp": ["experience", "years_of_experience", "yoe"],
    "notice_period": ["notice", "notice_period", "availability"],
    "current_salary": ["current_ctc", "current_salary"],
    "expected_salary": ["expected_ctc", "expected_salary", "salary_expectation"],
    "location": ["location", "current_location", "city"],
}


async def fill_and_submit(
    page,
    profile: dict,
    resume_path: str,
    job_id: str,
    llm,
    captcha_solver,
    file_storage,
    application_repo,
    dry_run: bool = False,
) -> dict:
    """Playwright form fill. Returns {status, screenshot_path}."""
    screenshot_path = ""
    try:
        # Fill text fields
        for field_key, selectors in _FIELD_MAP.items():
            value = profile.get(field_key, "")
            if not value:
                continue
            for sel in selectors:
                try:
                    el = await page.query_selector(f"[name='{sel}'], [id='{sel}'], [placeholder*='{sel}']")
                    if el:
                        await el.fill(str(value))
                        break
                except Exception:
                    continue

        # Upload resume
        try:
            file_input = await page.query_selector("input[type='file']")
            if file_input:
                await file_input.set_input_files(resume_path)
        except Exception as exc:
            log.warning("resume_upload_fail", job_id=job_id, reason=str(exc))

        # Handle screening questions via LLM
        await _answer_screening_questions(page, profile, llm)

        # Captcha
        captcha_frame = await page.query_selector("iframe[src*='recaptcha']")
        if captcha_frame:
            site_key = await page.evaluate("document.querySelector('[data-sitekey]')?.dataset.sitekey")
            if site_key:
                token = await captcha_solver.solve(site_key, page.url)
                await page.evaluate(f"document.getElementById('g-recaptcha-response').value = '{token}'")

        # Submit
        if not dry_run:
            submit_btn = await page.query_selector("button[type='submit'], input[type='submit']")
            if submit_btn:
                await submit_btn.click()
                await page.wait_for_load_state("networkidle")

        # Screenshot proof
        from pathlib import Path
        from datetime import datetime
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        screenshot_path = str(Path("logs/screenshots") / f"{ts}_{job_id}_submit.png")
        await page.screenshot(path=screenshot_path)

        return {"status": "submitted" if not dry_run else "dry_run", "screenshot_path": screenshot_path}

    except HumanReviewNeeded:
        raise
    except Exception as exc:
        log.warning("form_fill_fail", job_id=job_id, reason=str(exc))
        try:
            await page.screenshot(path=screenshot_path or "logs/screenshots/error.png")
        except Exception:
            pass
        return {"status": "form_failed", "screenshot_path": screenshot_path, "error": str(exc)}


async def _answer_screening_questions(page, profile: dict, llm) -> None:
    questions = await page.query_selector_all("textarea, select[data-question]")
    for el in questions[:5]:
        q_text = await el.get_attribute("placeholder") or await el.get_attribute("aria-label") or ""
        if not q_text:
            continue
        result = llm.complete(
            "form_screening",
            [{"role": "user", "content": f"Answer this job application question based on my profile.\nQuestion: {q_text}\nProfile: {str(profile)[:300]}\nAnswer (2-3 sentences max):"}],
        )
        if not result.is_err():
            tag = await el.evaluate("el => el.tagName")
            if tag == "TEXTAREA":
                await el.fill(result.unwrap().text[:500])
