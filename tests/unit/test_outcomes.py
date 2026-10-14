"""Phase edge cases use values, without mocking pytest's execution machinery."""

import pytest

from pytest_reqmark.outcomes import phase_outcome


@pytest.mark.parametrize("when", ["setup", "teardown"])
def test_successful_fixture_phases_do_not_override_the_test_verdict(when):
    outcome = phase_outcome(when, "passed")

    assert outcome is None


@pytest.mark.parametrize("when", ["setup", "teardown"])
def test_fixture_failures_are_errors_even_with_xpass_text(when):
    diagnostic = "[XPASS(strict)] fixture diagnostic"

    outcome = phase_outcome(when, "failed", longrepr=diagnostic)

    assert outcome == "ERROR"


def test_a_strict_unexpected_pass_has_the_same_outcome_as_a_non_strict_one():
    diagnostic = "[XPASS(strict)] known issue"

    outcome = phase_outcome("call", "failed", longrepr=diagnostic)

    assert outcome == "XPASSED"
