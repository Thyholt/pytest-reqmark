"""Generate simulated executions, then let pytest-xspec assess the saved evidence."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TypedDict, cast
from uuid import uuid4

# The script is also directly runnable from the repository root.
if __package__:
    from .identity import artifact_identity
else:
    from identity import artifact_identity

ROOT = Path(__file__).resolve().parent
SUITES = ("software", "hardware", "system")


class Summary(TypedDict):
    status: str
    verified: bool


class Assessment(TypedDict):
    summary: Summary


def execute(arguments: list[str], cwd: Path, log: Path) -> None:
    environment = dict(os.environ)
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTEST_DISABLE_PLUGIN_AUTOLOAD"):
        environment.pop(name, None)

    result = subprocess.run(
        [sys.executable, *arguments],
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    log.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode not in (0, 1, 5):
        raise RuntimeError(
            f"Command failed with {result.returncode}: {result.stdout}{result.stderr}"
        )


def run_suite(
    label: str,
    application: Path,
    hardware: str,
    suite: str,
    *,
    firmware_version: int = 1,
    deselect_equipment: bool = False,
) -> Path:
    directory = ROOT / "results" / "executions" / f"{label}-{hardware}-{suite}-{uuid4().hex}"
    (directory / "artifacts").mkdir(parents=True)
    firmware = ROOT / "artifacts" / f"fw-{hardware.lower()}-{firmware_version}.toml"
    saved_application = directory / "artifacts" / application.name
    saved_firmware = directory / "artifacts" / firmware.name
    saved_application.write_bytes(application.read_bytes())
    saved_firmware.write_bytes(firmware.read_bytes())
    specification = directory / "specification.toml"
    specification.write_bytes((ROOT / "xspec.toml").read_bytes())
    context = {
        "artifact": artifact_identity(saved_application),
        "hardware": hardware,
        "firmware": firmware.stem,
        "environment": "simulation",
    }
    tables = {
        "context": context,
        "provenance": {
            "adapter": "deterministic-simulator-v1",
            "measurements": str(directory / "measurements.csv"),
            "application": str(saved_application),
            "firmware": str(saved_firmware),
            "flow_observer": "simulated-fluid-sampler-1ms",
        },
        "device": {
            "application": str(saved_application),
            "firmware": str(saved_firmware),
            "assembly": "system" if suite == "system" else "bench",
        },
    }
    content = f"suite = {json.dumps(suite)}\n"
    for name, values in tables.items():
        content += f"\n[{name}]\n" + "".join(
            f"{key} = {json.dumps(value)}\n" for key, value in values.items()
        )

    context_path = directory / "context.toml"
    context_path.write_text(content, encoding="utf-8")
    arguments = [
        "-m",
        "pytest",
        "-s",
        "-q",
        f"--xspec-spec={specification}",
        f"--xspec-context={context_path}",
        f"--xspec-json={directory / 'record.json'}",
    ]
    if deselect_equipment:
        arguments += ["-m", "not equipment"]

    execute(arguments, ROOT / suite, directory / "console.log")
    return directory / "record.json"


def assess(
    name: str,
    application: Path,
    evidence: list[Path],
    *,
    changed_firmware: bool = False,
    reuse: tuple[str, str] | None = None,
    environment: str = "simulation",
) -> dict[str, object]:
    target = ROOT / "results" / f"{name}.target.toml"
    content = (
        f"id = {json.dumps(name)}\n\n[context]\n"
        f"artifact = {json.dumps(artifact_identity(application))}\n"
        f"environment = {json.dumps(environment)}\n"
    )
    if changed_firmware:
        content += '\n[configurations.B]\nfirmware = "fw-b-2"\n'

    if reuse:
        execution, reason = reuse
        content += (
            f'\n[[reuse]]\ntarget = {json.dumps(name)}\nobligation = "SYS-001-B"\n'
            f'execution = {json.dumps(execution)}\nauthor = "Fictional verification engineer"\n'
            f"reason = {json.dumps(reason)}\n"
        )

    target.write_text(content, encoding="utf-8")
    destination = ROOT / "results" / name
    execute(
        [
            "-m",
            "pytest_xspec",
            "assess",
            str(ROOT / "xspec.toml"),
            "--target",
            str(target),
            "--json",
            f"{destination}.json",
            "--markdown",
            f"{destination}.md",
            *map(str, evidence),
        ],
        ROOT,
        Path(f"{destination}.log"),
    )
    # These are the public assessment fields produced by the package command.
    report = cast(Assessment, json.loads(Path(f"{destination}.json").read_text(encoding="utf-8")))
    print(f"{name}: {report['summary']['status']}")
    return {"scenario": name, "status": report["summary"]["status"], "report": f"{name}.json"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=SUITES, help="Run only one independent suite")
    parser.add_argument("--release", choices=("3.1", "3.2", "3.3"), default="3.1")
    parser.add_argument("--hardware", choices=("A", "B"), default="A")
    parser.add_argument(
        "--fix-residual-flow", action="store_true", help="Use a repaired 3.3 fluid path"
    )
    arguments = parser.parse_args()
    (ROOT / "results").mkdir(exist_ok=True)
    print("SIMULATION ONLY. All verification conclusions are computed by pytest-xspec.")
    applications = {
        version: ROOT / "artifacts" / f"app-{version}.toml" for version in ("3.1", "3.2", "3.3")
    }
    if arguments.fix_residual_flow:
        repaired = ROOT / "results" / "app-3.3-repaired.toml"
        repaired.write_text(
            applications["3.3"]
            .read_text(encoding="utf-8")
            .replace("residual_b_ms = 100", "residual_b_ms = 0"),
            encoding="utf-8",
        )
        applications["3.3"] = repaired

    if arguments.suite:
        source = run_suite(
            f"manual-{arguments.release}",
            applications[arguments.release],
            arguments.hardware,
            arguments.suite,
        )
        print(f"Execution record: {source}")
        return

    archive: dict[tuple[str, str, str], Path] = {}
    reports: list[dict[str, object]] = []
    for release, application in applications.items():
        evidence: list[Path] = []
        for hardware in ("A", "B"):
            for suite in SUITES:
                if (release, hardware, suite) == ("3.2", "B", "system"):
                    source = archive["3.1", "B", "system"]
                else:
                    source = run_suite(release, application, hardware, suite)
                    archive[release, hardware, suite] = source

                evidence.append(source)

        reports.append(assess(release, application, evidence))

    baseline = [archive["3.1", hardware, suite] for hardware in ("A", "B") for suite in SUITES]
    equipment = run_suite("equipment", applications["3.1"], "B", "system", deselect_equipment=True)
    reports.append(
        assess("equipment-unavailable", applications["3.1"], [*baseline[:-1], equipment])
    )
    firmware = [
        *baseline[:3],
        run_suite("firmware", applications["3.1"], "B", "software", firmware_version=2),
        run_suite("firmware", applications["3.1"], "B", "hardware", firmware_version=2),
        baseline[-1],
    ]
    reports.append(assess("firmware-change", applications["3.1"], firmware, changed_firmware=True))
    original = json.loads(baseline[-1].read_text(encoding="utf-8"))
    reports.append(
        assess(
            "firmware-reuse",
            applications["3.1"],
            firmware,
            changed_firmware=True,
            reuse=(
                original["execution"]["id"],
                "Demonstration approval: firmware changes diagnostics only. "
                "The simulated motor and fluid behavior is unchanged. "
                "This is not a real engineering approval.",
            ),
        )
    )
    reports.append(
        assess("physical-required", applications["3.1"], baseline, environment="physical")
    )
    (ROOT / "results" / "report.json").write_text(
        json.dumps(reports, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# MediFlow verification results",
        "",
        "SIMULATION ONLY.",
        "",
        "| Scenario | Status | Detail |",
        "| --- | --- | --- |",
    ]
    lines += [
        f"| {row['scenario']} | {row['status']} | [Assessment]({row['scenario']}.md) |"
        for row in reports
    ]
    (ROOT / "results" / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Open examples/medical_verification/results/report.md")


if __name__ == "__main__":
    main()
