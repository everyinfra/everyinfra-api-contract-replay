from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .compare import compare_contracts, replay_check
from .contract import build_contract
from .io import ContractReplayError, load_captures, read_json, write_json_exclusive
from .redact import sanitize_capture


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="everyinfra-contract",
        description="Offline API contract analysis for sanitized JSON fixtures.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("redact", "build"):
        command = subparsers.add_parser(name)
        command.add_argument("inputs", nargs="+")
        command.add_argument("--output", required=True)

    diff = subparsers.add_parser("diff")
    diff.add_argument("before")
    diff.add_argument("after")
    diff.add_argument("--output", required=True)

    check = subparsers.add_parser("check")
    check.add_argument("contract")
    check.add_argument("inputs", nargs="+")
    check.add_argument("--output", required=True)
    return parser


def _print_summary(payload: object, output: str) -> None:
    if isinstance(payload, list):
        summary = {"kind": "sanitized_captures", "capture_count": len(payload)}
    elif isinstance(payload, dict):
        summary = payload.get("summary") or {
            "kind": payload.get("kind"),
            "capture_count": payload.get("capture_count"),
            "passed": payload.get("passed"),
        }
    else:
        summary = {"kind": type(payload).__name__}
    print(json.dumps({"output": str(Path(output)), "summary": summary}, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command in {"redact", "build"}:
            captures = load_captures(args.inputs)
            if args.command == "redact":
                payload = [sanitize_capture(capture) for capture in captures]
            else:
                payload = build_contract(captures)
        elif args.command == "diff":
            payload = compare_contracts(read_json(args.before), read_json(args.after))
        else:
            contract = read_json(args.contract)
            payload = replay_check(contract, load_captures(args.inputs))

        write_json_exclusive(args.output, payload)
        _print_summary(payload, args.output)
        if args.command == "check" and not payload["passed"]:
            return 2
        return 0
    except (ContractReplayError, ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
