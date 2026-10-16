import pytest

from ..pump import Observation


@pytest.mark.xspec("SYS-001")
@pytest.mark.equipment
def test_fluid_delivery_stops(observation: Observation) -> None:
    stopped_at = observation.flow_stopped_at

    assert stopped_at <= 300, f"Fluid delivery continued until {stopped_at} ms"
