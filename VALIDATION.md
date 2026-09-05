# Validation and evidence boundaries

This page separates implemented behavior, local evidence, and claims that remain unverified. All current examples are synthetic and use reserved `example.test` domains. The application sends no network request.

## Current local evidence

Validated on 2026-09-05 with Python 3.12.11 and macOS arm64:

- Thirteen unit, CLI and subprocess tests pass in one run. They cover recursive redaction without input mutation, query masking, URL userinfo rejection, path templating, deterministic contracts, secret absence, change classification, pass/fail replay behavior, output overwrite refusal, the 1,000-capture limit, the `redact` CLI, and the complete demonstration.
- The demonstration consumes four synthetic fixtures and records `network_requests=0`. The generated evidence contains no raw synthetic key or contact string. Its intentional current-version changes produce five findings: two `breaking_candidate`, two `additive`, and one `review`; strict offline replay therefore correctly reports `passed=false`.
- The runtime has no third-party dependency. `uv.lock` resolves only the local project. Six exact isolated build-tool versions are fixed with distribution hashes; the 2026-09-05 OSV query returned six results with no listed vulnerabilities. That sample does not cover Python, macOS, native libraries, CI images or future versions.
- Two final hash-constrained wheel builds are byte-identical with SHA-256 `b4e49a6fed451b96761a2a3b4a7a542f3e19e34744f03fb655498e943107b3b7`. The wheel contains seven source modules plus five metadata/license files. CRC, RECORD membership and hashes, source bytes, package identity, empty dependency metadata, MIT expression and license bytes pass the project verifier.
- The final wheel installs without dependencies into a fresh Python 3.12 environment. `uv pip check` passes and the installed `everyinfra-contract redact` command creates one sanitized capture without the raw synthetic key or email.

These observations are evidence for the named local samples. They are not a claim of complete secret detection, OpenAPI equivalence, production traffic compatibility, external API authorization, or security certification.

## Reproduce the core checks

```bash
uv sync --locked --python 3.12
PYTHONDONTWRITEBYTECODE=1 uv run --locked python -m unittest discover -s tests -v
uv run --locked python scripts/demo.py --output outputs/demo-new-name
uv build --wheel --build-constraints build-constraints.txt --require-hashes --out-dir outputs/build-a
uv build --wheel --build-constraints build-constraints.txt --require-hashes --out-dir outputs/build-b
uv run --locked python scripts/verify_wheel.py outputs/build-a/*.whl outputs/build-b/*.whl --output outputs/wheel-verification.json
```

Every output file and demonstration directory must be new. The test suite and demo do not follow fixture URLs.

## Not yet verified

- Linux, Windows, Intel macOS or Python versions outside 3.12
- A universal redaction guarantee or application-specific secret dictionaries
- HAR, packet capture, streaming bodies, multipart forms, binary data or live HTTP replay
- Contract requiredness, unobserved status codes, semantic value constraints or OpenAPI generation
- Production workload, concurrency, long-duration or memory boundaries
- A GitHub Release, package upload, deployment, search indexing, AI mention, citation, traffic or conversion outcome. Public repository contents and hosted CI require separate GitHub-side evidence after the source push.

See [SECURITY.md](SECURITY.md) for the input and data-sharing boundary, [THIRD_PARTY.md](THIRD_PARTY.md) for build-tool ownership, and [PUBLIC_RELEASE.md](PUBLIC_RELEASE.md) for the candidate source boundary.
