"""Content identity for the fictional application artifact."""

import hashlib
from pathlib import Path


def artifact_identity(path: Path) -> str:
    return f"{path.stem}@sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
