import pytest

from ..pump import Observation


@pytest.mark.xspec("SW-001")
def test_occlusion_is_detected(observation: Observation) -> None:
    detected_at = observation.detected_at

    assert detected_at <= 150


@pytest.mark.xspec("SW-002")
def test_stop_command_follows_detection(observation: Observation) -> None:
    delay = observation.commanded_at - observation.detected_at

    assert delay <= 50
