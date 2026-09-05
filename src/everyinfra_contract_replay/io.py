from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_CAPTURES = 1_000


class ContractReplayError(ValueError):
    """Raised when fixture input violates the offline analysis contract."""


def read_json(path: str | Path) -> Any:
    source = Path(path)
    size = source.stat().st_size
    if size > MAX_INPUT_BYTES:
        raise ContractReplayError(
            f"input exceeds {MAX_INPUT_BYTES} bytes: {source} ({size} bytes)"
        )
    with source.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_captures(paths: list[str | Path]) -> list[dict[str, Any]]:
    captures: list[dict[str, Any]] = []
    for path in paths:
        payload = read_json(path)
        entries = payload if isinstance(payload, list) else [payload]
        for entry in entries:
            if not isinstance(entry, dict):
                raise ContractReplayError(f"capture must be a JSON object: {path}")
            captures.append(entry)
            if len(captures) > MAX_CAPTURES:
                raise ContractReplayError(
                    f"capture count exceeds command limit of {MAX_CAPTURES}"
                )
    if not captures:
        raise ContractReplayError("at least one capture is required")
    return captures


def write_json_exclusive(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(target, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    except BaseException:
        target.unlink(missing_ok=True)
        raise
