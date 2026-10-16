import pytest

from ..pump import Observation


@pytest.mark.xspec("HW-001")
def test_controller_bench_stops_delivery(observation: Observation) -> None:
    delay = observation.flow_stopped_at - observation.commanded_at

    assert delay <= 100
