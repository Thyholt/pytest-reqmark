"""User-owned simulation adapter and measurements, outside pytest-xspec."""

import csv
import sys
from importlib import import_module
from pathlib import Path
from typing import cast

import pytest

from .identity import artifact_identity
from .pump import Observation, Pump, observe


def read_toml(path: Path) -> dict[str, object]:
    toml = import_module("tomllib" if sys.version_info >= (3, 11) else "tomli")
    with path.open("rb") as stream:
        return cast(dict[str, object], toml.load(stream))


@pytest.fixture
def observation(pytestconfig: pytest.Config, request: pytest.FixtureRequest) -> Observation:
    run = read_toml(Path(pytestconfig.getoption("xspec_context")))
    # These local simulator tables are created by run.py with a known schema.
    device = cast(dict[str, str], run["device"])
    context = cast(dict[str, str], run["context"])
    provenance = cast(dict[str, str], run["provenance"])
    application = Path(device["application"])
    firmware = read_toml(Path(device["firmware"]))
    software = read_toml(application)
    if (
        context["artifact"] != artifact_identity(application)
        or context["firmware"] != firmware["id"]
    ):
        raise ValueError("Recorded context does not identify the configured simulator")

    residual = int(str(software["residual_b_ms"])) if context["hardware"] == "B" else 0
    pump = Pump(
        int(str(software["detection_ms"])),
        int(str(software["command_ms"])),
        int(str(firmware["coast_ms"])),
        residual if device["assembly"] == "system" else 0,
    )

    result, samples = observe(pump)

    measurements = Path(provenance["measurements"])
    new_file = not measurements.exists()
    with measurements.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        if new_file:
            writer.writerow(("test_nodeid", "time_ms", "delivered_ul"))

        writer.writerows((request.node.nodeid, time, volume) for time, volume in samples)

    print(f"SIMULATED_EXECUTION {context['artifact']} {context['hardware']} {context['firmware']}")
    print(
        f"FLOW_STOPPED_AT {result.flow_stopped_at} ms, "
        f"MOTOR_STOPPED_AT {result.motor_stopped_at} ms"
    )
    return result
