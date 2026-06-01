from job_agent.obs.logging import _scrub_pii


def test_scrubber_strips_email() -> None:
    result = _scrub_pii("Contact john.doe@example.com for details")
    assert "john.doe@example.com" not in result
    assert "[email]" in result


def test_scrubber_strips_phone() -> None:
    result = _scrub_pii("Call +91 98765 43210 now")
    assert "98765" not in result
    assert "[phone]" in result


def test_scrubber_strips_multiple() -> None:
    result = _scrub_pii("Email: hr@company.org, Phone: +1-800-555-0100")
    assert "hr@company.org" not in result
    assert "555-0100" not in result


def test_scrubber_leaves_clean_text() -> None:
    clean = "The build succeeded with 42 warnings"
    assert _scrub_pii(clean) == clean


def test_scrubber_strips_all_pii_inputs() -> None:
    pii_inputs = [
        "user@domain.com",
        "first.last+tag@sub.domain.co.uk",
        "+1 (415) 555-2671",
        "9876543210",
    ]
    for pii in pii_inputs:
        result = _scrub_pii(f"value: {pii} end")
        assert pii not in result, f"PII not scrubbed: {pii}"
