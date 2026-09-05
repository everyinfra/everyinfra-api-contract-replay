from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from everyinfra_contract_replay.compare import compare_contracts, replay_check
from everyinfra_contract_replay.contract import build_contract
from everyinfra_contract_replay.io import load_captures, write_json_exclusive
from everyinfra_contract_replay.redact import sanitize_capture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)

    baseline_paths = sorted((PROJECT_ROOT / "examples" / "baseline").glob("*.json"))
    current_paths = sorted((PROJECT_ROOT / "examples" / "current").glob("*.json"))
    baseline = load_captures(baseline_paths)
    current = load_captures(current_paths)
    sanitized = [sanitize_capture(capture) for capture in baseline]
    before = build_contract(baseline)
    after = build_contract(current)
    diff = compare_contracts(before, after)
    replay = replay_check(before, current)

    write_json_exclusive(output / "sanitized-baseline.json", sanitized)
    write_json_exclusive(output / "contract-before.json", before)
    write_json_exclusive(output / "contract-after.json", after)
    write_json_exclusive(output / "contract-diff.json", diff)
    write_json_exclusive(output / "offline-replay.json", replay)

    rendered = "\n".join(path.read_text(encoding="utf-8") for path in output.glob("*.json"))
    forbidden = ("synthetic-secret", "another-secret", "operator@example.test", "new-operator@example.test")
    leaked = [value for value in forbidden if value in rendered]
    if leaked:
        raise RuntimeError(f"redaction verification failed: {leaked}")
    if replay["passed"] or diff["summary"]["breaking_candidates"] < 1:
        raise RuntimeError("demo must preserve the intentional breaking change")

    receipt = {
        "kind": "offline_contract_demo_receipt",
        "network_requests": 0,
        "synthetic_fixture_count": len(baseline) + len(current),
        "output_files": sorted(path.name for path in output.glob("*.json")),
        "raw_secret_leaks": 0,
        "diff_summary": diff["summary"],
        "replay_passed": replay["passed"],
        "expected_replay_result": "failed_due_to_intentional_contract_drift",
    }
    write_json_exclusive(output / "demo-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
