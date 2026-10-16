"""Command-line assessment of saved pytest-xspec execution reports."""

import argparse
import json
import sys
from pathlib import Path

from pytest_xspec.assessment import assess
from pytest_xspec.assessment_io import load_plan, load_runs, load_target
from pytest_xspec.assessment_reporting import markdown, terminal


class Arguments(argparse.Namespace):
    command: str
    specification: Path
    target: Path
    reports: list[Path]
    json: Path | None
    markdown: Path | None


def _validate_destinations(arguments: Arguments) -> None:
    inputs = {
        path.resolve() for path in [arguments.specification, arguments.target, *arguments.reports]
    }
    outputs = [path.resolve() for path in (arguments.json, arguments.markdown) if path is not None]
    aliases = any(
        output.exists() and other.exists() and output.samefile(other)
        for index, output in enumerate(outputs)
        for other in [*inputs, *outputs[:index]]
    )
    if len(set(outputs)) != len(outputs) or inputs.intersection(outputs) or aliases:
        raise ValueError("assessment output must not overwrite an input or another output")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pytest-xspec")
    parser.add_argument("command", choices=["assess"])
    parser.add_argument("specification", type=Path)
    parser.add_argument("reports", type=Path, nargs="*")
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--json", type=Path, help="Write the structured assessment")
    parser.add_argument("--markdown", type=Path, help="Write a readable assessment")
    arguments = Arguments()
    parser.parse_intermixed_args(argv, namespace=arguments)
    try:
        _validate_destinations(arguments)
        plan = load_plan(arguments.specification)
        target = load_target(arguments.target, plan)
        report = assess(plan, target, load_runs(arguments.reports, plan))
        if arguments.json is not None:
            arguments.json.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

        if arguments.markdown is not None:
            arguments.markdown.write_text(markdown(report, arguments.markdown), encoding="utf-8")

    except (OSError, ValueError) as error:
        print(f"pytest-xspec: {error}", file=sys.stderr)
        return 4

    print(terminal(report))
    return 0 if report["summary"]["verified"] else 1
