from job_agent.notifications.email_digest import render_digest


def test_digest_renders_html_and_plain():
    stats = {"jobs_found": 12, "applications": 3, "replies": 1, "followups_pending": 2, "interviews": 0}
    html, plain = render_digest(stats)
    assert "12" in html
    assert "12" in plain


def test_digest_plain_has_all_fields():
    stats = {"jobs_found": 5, "applications": 2, "replies": 0, "followups_pending": 1, "interviews": 1}
    _, plain = render_digest(stats)
    assert "Jobs found" in plain
    assert "Applications" in plain
    assert "Interviews" in plain


def test_digest_handles_missing_fields():
    html, plain = render_digest({})
    assert "0" in plain or "Digest" in plain
