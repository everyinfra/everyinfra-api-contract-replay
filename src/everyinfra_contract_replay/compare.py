from __future__ import annotations

from collections import Counter
from typing import Any


def _change(
    severity: str,
    kind: str,
    endpoint: str,
    path: str,
    before: Any,
    after: Any,
) -> dict[str, Any]:
    return {
        "severity": severity,
        "kind": kind,
        "endpoint": endpoint,
        "path": path,
        "before": before,
        "after": after,
    }


def _compare_names(
    changes: list[dict[str, Any]],
    endpoint: str,
    path: str,
    before: list[str],
    after: list[str],
) -> None:
    for name in sorted(set(before) - set(after)):
        changes.append(_change("review", "name_removed", endpoint, f"{path}.{name}", name, None))
    for name in sorted(set(after) - set(before)):
        changes.append(_change("review", "name_added", endpoint, f"{path}.{name}", None, name))


def _compare_schema(
    changes: list[dict[str, Any]],
    endpoint: str,
    path: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    response_side: bool,
) -> None:
    if before is None and after is None:
        return
    if before is None:
        severity = "additive" if response_side else "review"
        changes.append(_change(severity, "body_added", endpoint, path, None, after))
        return
    if after is None:
        severity = "breaking_candidate" if response_side else "review"
        changes.append(_change(severity, "body_removed", endpoint, path, before, None))
        return
    before_types = before.get("types", [])
    after_types = after.get("types", [])
    if before_types != after_types:
        severity = "breaking_candidate" if response_side else "review"
        changes.append(_change(severity, "type_changed", endpoint, path, before_types, after_types))

    before_properties = before.get("properties", {})
    after_properties = after.get("properties", {})
    for name in sorted(set(before_properties) - set(after_properties)):
        severity = "breaking_candidate" if response_side else "review"
        changes.append(
            _change(severity, "field_removed", endpoint, f"{path}.{name}", before_properties[name], None)
        )
    for name in sorted(set(after_properties) - set(before_properties)):
        severity = "additive" if response_side else "review"
        changes.append(
            _change(severity, "field_added", endpoint, f"{path}.{name}", None, after_properties[name])
        )
    for name in sorted(set(before_properties) & set(after_properties)):
        _compare_schema(
            changes,
            endpoint,
            f"{path}.{name}",
            before_properties[name],
            after_properties[name],
            response_side,
        )
    if "items" in before or "items" in after:
        _compare_schema(
            changes,
            endpoint,
            f"{path}[]",
            before.get("items"),
            after.get("items"),
            response_side,
        )


def compare_contracts(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    if before.get("kind") != "observed_api_contract" or after.get("kind") != "observed_api_contract":
        raise ValueError("both inputs must be observed_api_contract documents")
    changes: list[dict[str, Any]] = []
    before_endpoints = before.get("endpoints", {})
    after_endpoints = after.get("endpoints", {})

    for endpoint in sorted(set(before_endpoints) - set(after_endpoints)):
        changes.append(_change("breaking_candidate", "endpoint_removed", endpoint, endpoint, True, False))
    for endpoint in sorted(set(after_endpoints) - set(before_endpoints)):
        changes.append(_change("additive", "endpoint_added", endpoint, endpoint, False, True))

    for endpoint in sorted(set(before_endpoints) & set(after_endpoints)):
        left = before_endpoints[endpoint]
        right = after_endpoints[endpoint]
        _compare_names(
            changes,
            endpoint,
            "request.query_keys",
            left["request"]["query_keys"],
            right["request"]["query_keys"],
        )
        _compare_names(
            changes,
            endpoint,
            "request.header_names",
            left["request"]["header_names"],
            right["request"]["header_names"],
        )
        _compare_schema(
            changes,
            endpoint,
            "request.body",
            left["request"]["body"],
            right["request"]["body"],
            False,
        )

        before_statuses = set(left["responses"]["statuses"])
        after_statuses = set(right["responses"]["statuses"])
        for status in sorted(before_statuses - after_statuses):
            severity = "breaking_candidate" if 200 <= status < 300 else "review"
            changes.append(_change(severity, "status_removed", endpoint, f"responses.{status}", status, None))
        for status in sorted(after_statuses - before_statuses):
            severity = "additive" if 200 <= status < 300 else "review"
            changes.append(_change(severity, "status_added", endpoint, f"responses.{status}", None, status))
        for status in sorted(before_statuses & after_statuses):
            left_status = left["responses"]["by_status"][str(status)]
            right_status = right["responses"]["by_status"][str(status)]
            _compare_names(
                changes,
                endpoint,
                f"responses.{status}.header_names",
                left_status["header_names"],
                right_status["header_names"],
            )
            _compare_schema(
                changes,
                endpoint,
                f"responses.{status}.body",
                left_status["body"],
                right_status["body"],
                True,
            )

    severity_counts = Counter(change["severity"] for change in changes)
    return {
        "schema_version": 1,
        "kind": "api_contract_diff",
        "before_evidence_sha256": before.get("evidence_sha256"),
        "after_evidence_sha256": after.get("evidence_sha256"),
        "summary": {
            "total_changes": len(changes),
            "breaking_candidates": severity_counts["breaking_candidate"],
            "additive": severity_counts["additive"],
            "review": severity_counts["review"],
        },
        "changes": changes,
    }


def replay_check(contract: dict[str, Any], captures: list[dict[str, Any]]) -> dict[str, Any]:
    from .contract import build_contract

    observed = build_contract(captures)
    diff = compare_contracts(contract, observed)
    return {
        "schema_version": 1,
        "kind": "offline_replay_check",
        "passed": diff["summary"]["total_changes"] == 0,
        "contract_evidence_sha256": contract.get("evidence_sha256"),
        "observed_evidence_sha256": observed.get("evidence_sha256"),
        "diff": diff,
        "limitations": [
            "Replays fixture structure only and sends no network request.",
            "A passing result covers only the supplied observations.",
        ],
    }
