"""Fictional controller and fluid path, advancing in deterministic 1 ms ticks."""

from dataclasses import dataclass


@dataclass
class Pump:
    detection_delay_ms: int
    command_delay_ms: int
    coast_ms: int
    residual_ms: int
    detected_at: int | None = None
    commanded_at: int | None = None
    motor_stopped_at: int | None = None
    flow_ul: int = 1

    def tick(self, time_ms: int) -> None:
        if time_ms >= self.detection_delay_ms and self.detected_at is None:
            self.detected_at = time_ms

        if (
            self.detected_at is not None
            and time_ms >= self.detected_at + self.command_delay_ms
            and self.commanded_at is None
        ):
            self.commanded_at = time_ms

        if (
            self.commanded_at is not None
            and time_ms >= self.commanded_at + self.coast_ms
            and self.motor_stopped_at is None
        ):
            self.motor_stopped_at = time_ms

        if (
            self.motor_stopped_at is not None
            and time_ms >= self.motor_stopped_at + self.residual_ms
        ):
            self.flow_ul = 0


@dataclass(frozen=True)
class Observation:
    detected_at: int
    commanded_at: int
    motor_stopped_at: int
    flow_stopped_at: int


def observe(pump: Pump) -> tuple[Observation, list[tuple[int, int]]]:
    """The observer samples delivered fluid, never the motor's stop signal."""
    samples: list[tuple[int, int]] = []
    for time_ms in range(1000):
        pump.tick(time_ms)
        samples.append((time_ms, pump.flow_ul))
        if pump.flow_ul == 0:
            break

    if pump.detected_at is None or pump.commanded_at is None or pump.motor_stopped_at is None:
        raise RuntimeError("The simulated controller did not complete its stop sequence")

    stopped_at = next(time for time, volume in samples if volume == 0)
    return Observation(
        pump.detected_at, pump.commanded_at, pump.motor_stopped_at, stopped_at
    ), samples
