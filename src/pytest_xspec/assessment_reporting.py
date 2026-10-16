"""Readable generic views of a saved-results assessment."""

import html
import json
import os
from pathlib import Path
from urllib.parse import quote

from pytest_xspec.assessment import Assessment


def _text(value: str) -> str:
    escaped = html.escape(value).replace("\\", "\\\\").replace("\n", " ").replace("\r", " ")
    for punctuation in "|`*[]_":
        escaped = escaped.replace(punctuation, "\\" + punctuation)

    return escaped


def terminal(report: Assessment) -> str:
    lines = [f"{report['target']}: {report['summary']['status']}"]
    for row in report["obligations"]:
        lines.append(f"{row['id']}  {row['status']}")
        if row["status"] != "PASSED":
            if not row["tests"]:
                lines.append("  No execution supplied for this obligation.")

            for test in row["tests"]:
                if test["applicable"]:
                    lines.append(f"  {test['nodeid']}: {test['outcome']} ({test['execution']})")
                else:
                    for key, mismatch in test["mismatches"].items():
                        lines.append(
                            f"  {key}: expected {mismatch['expected']!r}, "
                            f"actual {mismatch['actual']!r}"
                        )

    summary = report["summary"]
    lines.append(f"Verified obligations: {summary['passed']}/{summary['obligations']}")
    lines.append(f"Collection errors: {summary['collection_errors']}")
    return "\n".join(lines)


def markdown(report: Assessment, destination: Path) -> str:
    summary = report["summary"]
    lines = [
        f"# Verification: {_text(report['target'])}",
        "",
        f"**{summary['status']}**",
        "",
        f"Verified obligations: {summary['passed']}/{summary['obligations']}. "
        f"Coverage: {summary['coverage']:.1f}%. Collection errors: {summary['collection_errors']}.",
        "",
        "This verdict evaluates the declared verification plan against supplied pytest executions.",
        "It does not establish product safety or authorize a release.",
        "",
        "## Obligations",
        "",
        "| Obligation | Requirement | Configuration | Suite | Status |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        "| "
        + " | ".join(
            _text(row[key])
            for key in (
                "id",
                "requirement",
                "configuration",
                "suite",
                "status",
            )
        )
        + " |"
        for row in report["obligations"]
    )

    lines += ["", "## Execution evidence", ""]
    for row in report["obligations"]:
        lines += [
            f"### {_text(row['id'])}: {row['status']}",
            "",
            "Expected context:",
            "",
            "```json",
            json.dumps(row["expected"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]
        if not row["tests"]:
            lines += ["No execution was supplied for this obligation.", ""]

        for test in row["tests"]:
            relative = os.path.relpath(Path(test["source"]).resolve(), destination.parent.resolve())
            link = quote(relative, safe="/")
            applicability = "applicable" if test["applicable"] else "INAPPLICABLE"
            lines += [
                f"- **{test['outcome']}**, {applicability}: {_text(test['nodeid'])}.",
                f"  Execution {_text(test['execution'])}, suite {_text(test['suite'])}.",
                f"  [{_text(Path(test['source']).name)}]({link}).",
                f"  Started {_text(test['started_at'])}, finished {_text(test['finished_at'])}.",
            ]
            for key, mismatch in test["mismatches"].items():
                actual = json.dumps(mismatch["actual"], ensure_ascii=False)
                expected = json.dumps(mismatch["expected"], ensure_ascii=False)
                lines.append(
                    f"  Mismatch {_text(key)}: expected {_text(expected)}, actual {_text(actual)}."
                )

            if test["reuse"] is not None:
                decision = test["reuse"]
                lines.append(
                    f"  **Explicit reuse**, approved by {_text(decision['author'])}: "
                    f"{_text(decision['reason'])}"
                )

            lines += [
                "",
                "```json",
                json.dumps(
                    {
                        "context": test["context"],
                        "provenance": test["provenance"],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                "```",
                "",
            ]

    lines += [
        "## Supplied executions",
        "",
        "| Execution | Suite | Collection errors | Source |",
        "| --- | --- | --- | --- |",
    ]
    for source in report["executions"]:
        execution = source["execution"]
        relative = os.path.relpath(Path(source["source"]).resolve(), destination.parent.resolve())
        link = quote(relative, safe="/")
        lines.append(
            f"| {_text(execution['id'])} | {_text(execution['suite'])} | "
            f"{source['collection_errors']} | [Record]({link}) |"
        )

    return "\n".join(lines) + "\n"
