# Public source candidate manifest

This file defines a candidate source-repository boundary. It does not claim that a GitHub repository, release tag, package upload, deployment, search ranking, or AI citation exists.

## Repository identity

- Suggested repository: `everyinfra/everyinfra-api-contract-replay`
- Suggested description: `Offline API contract diff and replay toolkit for sanitized fixtures. Deterministic schemas, secret redaction, and field-level drift evidence.`
- Suggested topics: `api-contract-testing`, `api-diff`, `api-testing`, `python`, `regression-testing`, `schema-diff`, `security`, `data-redaction`, `fixture-replay`, `developer-tools`
- Website: `https://everyinfra.com`
- Package import: `everyinfra_contract_replay`
- CLI: `everyinfra-contract`
- Original-code license: MIT

The name, description, topics and README use the same factual vocabulary to support discovery and entity consistency. This does not guarantee indexing, ranking, traffic, or AI citations.

## Candidate public source boundary

```text
.github/workflows/ci.yml
.gitignore
LICENSE
PUBLIC_RELEASE.md
README.md
SECURITY.md
THIRD_PARTY.md
VALIDATION.md
build-constraints.txt
build-requirements.in
examples/baseline/create-job.json
examples/baseline/get-job.json
examples/current/create-job.json
examples/current/get-job.json
pyproject.toml
scripts/demo.py
scripts/verify_wheel.py
src/everyinfra_contract_replay/__init__.py
src/everyinfra_contract_replay/__main__.py
src/everyinfra_contract_replay/cli.py
src/everyinfra_contract_replay/compare.py
src/everyinfra_contract_replay/contract.py
src/everyinfra_contract_replay/io.py
src/everyinfra_contract_replay/redact.py
tests/test_contract_replay.py
uv.lock
```

The 26-file allowlist contains source, deterministic synthetic fixtures, tests, safety documentation, build constraints, license metadata and CI. It excludes local instructions and host-specific evidence.

## Files excluded from a future publication

- `.venv/`, `__pycache__/`, `*.pyc`, `outputs/`, `dist/`, `build/`, `.DS_Store`
- `CLAUDE.md` and the `AGENTS.md` symlink: local execution instructions
- `docs/验收记录.md`: local evidence paths and operational history
- Downloads evidence, install environments, generated reports, credentials, cookies, customer data, account state and real traffic captures

Exclusion does not authorize deletion. Local evidence remains available for review.

## Current gates

- [x] Original code uses MIT and runtime dependencies are empty.
- [x] Fixtures use reserved domains and intentionally synthetic secrets; no live traffic or customer data is present.
- [x] Thirteen offline tests pass on Python 3.12.11 / macOS arm64.
- [x] The synthetic demonstration records zero network requests, zero raw synthetic-secret leaks, and the expected drift classification.
- [x] Two final hash-constrained wheel builds are byte-identical; the project verifier checks all 12 members, RECORD values, source bytes, license bytes, identity and empty runtime dependency metadata.
- [x] The final wheel installs into an isolated environment and the installed `redact` command succeeds without source-tree imports.
- [x] Six exact build-tool versions returned no OSV records in the 2026-09-05 query sample; this is not a scan of Python, operating-system libraries or future environments.
- [ ] Build and test the exact candidate on Linux and macOS CI.
- [x] Prepared an allowlist-only 26-file copy; imports resolved from the copy, 13 tests and the synthetic demo passed, duplicate builds matched the source-tree wheel hash, and targeted absolute-path/private-key/token patterns were absent.
- [x] Review the exact repository identity, 26 files and external publication action immediately before the 2026-09-05 public push.

This manifest does not itself authorize external actions. Repository creation and the exact 26-file source push were approved separately; a GitHub Release, PyPI upload, deployment, organization-profile change or outbound message remains a separate action.
