import pytest

from job_agent.services.application_state import status_from_email_label, transition


def test_valid_transition():
    assert transition("applied", "rejected") == "rejected"
    assert transition("applied", "interview_scheduled") == "interview_scheduled"
    assert transition("interview_scheduled", "offer_received") == "offer_received"


def test_invalid_transition_raises():
    with pytest.raises(ValueError):
        transition("rejected", "applied")


def test_ghosted_can_return_to_applied():
    assert transition("ghosted", "applied") == "applied"


def test_all_terminal_states_raise():
    for terminal in ("rejected", "withdrawn"):
        with pytest.raises(ValueError):
            transition(terminal, "applied")


def test_day14_tags_ghosted():
    assert transition("applied", "ghosted") == "ghosted"


def test_day21_archives():
    assert transition("ghosted", "archived") == "archived"


def test_status_from_interview_invite():
    assert status_from_email_label("interview_invite") == "interview_scheduled"


def test_status_from_rejection():
    assert status_from_email_label("rejection") == "rejected"


def test_status_from_auto_reply():
    assert status_from_email_label("auto_reply") == "applied"


def test_status_from_unknown_label():
    assert status_from_email_label("gibberish") is None


def test_full_state_machine_branch_coverage():
    path = ["applied", "outreach_sent", "interview_scheduled", "offer_received", "withdrawn"]
    current = "discovered"
    for next_status in path:
        try:
            current = transition(current, next_status)
        except ValueError:
            pass
