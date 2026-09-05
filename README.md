# EveryInfra API Contract Replay

Offline API contract diff and replay checks for sanitized request and response fixtures.

EveryInfra API Contract Replay turns synthetic or already-authorized, sanitized HTTP observations into deterministic structural contracts. It redacts credentials and contact fields, normalizes resource identifiers, compares field-level changes, and checks later fixtures for contract drift without sending a network request.

This is an original EveryInfra engineering showcase. It is not a third-party reverse-engineering wrapper, traffic interceptor, login tool, signature generator, anti-bot bypass, or complete OpenAPI inference engine.

## What it does

- Removes sensitive header values, all query values, common secret-bearing JSON fields, email addresses and phone values before analysis.
- Replaces UUIDs, long hexadecimal identifiers, integers and common prefixed resource IDs in URL paths with stable templates.
- Builds deterministic contracts for observed methods, origins, paths, query names, request shapes, response statuses and response shapes.
- Reports endpoint, status, field and type changes as `breaking_candidate`, `additive`, or `review`.
- Rebuilds a contract from later fixtures and performs a strict offline replay check. Any structural drift returns a non-zero result.
- Refuses to overwrite an existing output file or demonstration directory.

## What it does not prove

A capture-derived contract only describes the supplied samples. It does not establish field requiredness, every possible status, authorization, rate limits, production compatibility, or ownership of a remote API. Redaction is a defensive filter, not a guarantee that arbitrary input is free of sensitive data; operators must sanitize and minimize fixtures before use.

## Fixture format

Each JSON file contains one object or a list of objects:

```json
{
  "schema_version": 1,
  "capture_id": "get-job-success",
  "request": {
    "method": "GET",
    "url": "https://api.example.test/v1/jobs/job_123456?include=events&token=synthetic-secret",
    "headers": {
      "Accept": "application/json",
      "Authorization": "Bearer synthetic-secret"
    },
    "body": null
  },
  "response": {
    "status": 200,
    "headers": {"Content-Type": "application/json"},
    "body": {"id": "job_123456", "status": "complete"}
  }
}
```

Use reserved domains such as `example.test` for synthetic examples. Do not store real tokens, session cookies, personal data, customer payloads or private endpoints in fixtures.

## Run the deterministic demo

Python 3.12 is sufficient; there are no runtime dependencies.

```bash
PYTHONPATH=src python3 scripts/demo.py --output outputs/demo-001
```

The demo uses only repository fixtures and intentionally introduces a breaking response change. It writes sanitized fixtures, before and after contracts, a field-level diff, and a strict replay report. The script verifies that synthetic secret strings do not appear in the outputs.

## CLI

```bash
PYTHONPATH=src python3 -m everyinfra_contract_replay redact \
  --output outputs/sanitized.json examples/baseline/*.json

PYTHONPATH=src python3 -m everyinfra_contract_replay build \
  --output outputs/contract.json examples/baseline/*.json

PYTHONPATH=src python3 -m everyinfra_contract_replay diff \
  --output outputs/diff.json outputs/before.json outputs/after.json

PYTHONPATH=src python3 -m everyinfra_contract_replay check \
  --output outputs/replay.json outputs/before.json examples/current/*.json
```

`check` returns `0` only when no structural change is observed, `2` when drift is found, and `1` for invalid input or an operational error.

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Tests cover recursive redaction, URL validation, stable path templates, deterministic contracts, breaking/additive classification, strict replay behavior, input size limits, and output overwrite refusal. They do not connect to the internet.

## Security boundary

See [SECURITY.md](SECURITY.md). The tool accepts JSON files, not HAR archives, packet captures or live proxy traffic. It does not execute fixture contents or follow URLs. Inputs are capped at 2 MiB per file and 1,000 captures per command.

## License

EveryInfra's original code is available under the [MIT License](LICENSE). The runtime uses only Python's standard library. Build and development tools retain their own licenses and are not relicensed by this project.
