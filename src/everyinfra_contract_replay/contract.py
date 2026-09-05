from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from .redact import sanitize_capture

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
HEX_RE = re.compile(r"^[0-9a-fA-F]{16,}$")
INTEGER_RE = re.compile(r"^[0-9]+$")
PREFIXED_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*_[A-Za-z0-9_-]{4,}$")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def path_template(path: str) -> str:
    segments = []
    for segment in path.split("/"):
        if UUID_RE.fullmatch(segment):
            segments.append("{uuid}")
        elif HEX_RE.fullmatch(segment):
            segments.append("{hex}")
        elif INTEGER_RE.fullmatch(segment):
            segments.append("{int}")
        elif PREFIXED_ID_RE.fullmatch(segment) and not re.fullmatch(r"v[0-9]+", segment, re.I):
            segments.append("{id}")
        else:
            segments.append(segment)
    normalized = "/".join(segments)
    return normalized or "/"


def value_schema(value: Any) -> dict[str, Any]:
    if value is None:
        return {"types": ["null"]}
    if isinstance(value, bool):
        return {"types": ["boolean"]}
    if isinstance(value, int):
        return {"types": ["integer"]}
    if isinstance(value, float):
        return {"types": ["number"]}
    if isinstance(value, str):
        return {"types": ["string"]}
    if isinstance(value, dict):
        return {
            "types": ["object"],
            "properties": {
                str(key): value_schema(item)
                for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            },
        }
    if isinstance(value, list):
        item_schema: dict[str, Any] = {"types": ["unknown"]}
        if value:
            item_schema = value_schema(value[0])
            for item in value[1:]:
                item_schema = merge_schema(item_schema, value_schema(item))
        return {"types": ["array"], "items": item_schema}
    return {"types": [type(value).__name__]}


def merge_schema(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {"types": sorted(set(left.get("types", [])) | set(right.get("types", [])))}
    left_properties = left.get("properties", {})
    right_properties = right.get("properties", {})
    if left_properties or right_properties:
        properties: dict[str, Any] = {}
        for key in sorted(set(left_properties) | set(right_properties)):
            if key in left_properties and key in right_properties:
                properties[key] = merge_schema(left_properties[key], right_properties[key])
            else:
                properties[key] = left_properties.get(key, right_properties.get(key))
        merged["properties"] = properties
    if "items" in left or "items" in right:
        if "items" in left and "items" in right:
            merged["items"] = merge_schema(left["items"], right["items"])
        else:
            merged["items"] = left.get("items", right.get("items"))
    return merged


def _merge_optional_schema(existing: dict[str, Any] | None, value: Any) -> dict[str, Any]:
    incoming = value_schema(value)
    return incoming if existing is None else merge_schema(existing, incoming)


def build_contract(captures: list[dict[str, Any]]) -> dict[str, Any]:
    sanitized = [sanitize_capture(capture) for capture in captures]
    sanitized.sort(key=canonical_json)
    endpoints: dict[str, dict[str, Any]] = {}

    for capture in sanitized:
        request = capture["request"]
        response = capture["response"]
        parsed = urlsplit(request["url"])
        origin = f"{parsed.scheme}://{parsed.netloc}"
        template = path_template(parsed.path)
        endpoint_key = f"{request['method']} {origin}{template}"
        endpoint = endpoints.setdefault(
            endpoint_key,
            {
                "method": request["method"],
                "origin": origin,
                "path_template": template,
                "observations": 0,
                "request": {"query_keys": [], "header_names": [], "body": None},
                "responses": {"statuses": [], "by_status": {}},
            },
        )
        endpoint["observations"] += 1
        endpoint["request"]["query_keys"] = sorted(
            set(endpoint["request"]["query_keys"])
            | {key for key, _value in parse_qsl(parsed.query, keep_blank_values=True)}
        )
        endpoint["request"]["header_names"] = sorted(
            set(endpoint["request"]["header_names"])
            | {name.lower() for name in request["headers"]}
        )
        endpoint["request"]["body"] = _merge_optional_schema(
            endpoint["request"]["body"], request["body"]
        )

        status = response["status"]
        endpoint["responses"]["statuses"] = sorted(
            set(endpoint["responses"]["statuses"]) | {status}
        )
        status_key = str(status)
        status_contract = endpoint["responses"]["by_status"].setdefault(
            status_key, {"observations": 0, "header_names": [], "body": None}
        )
        status_contract["observations"] += 1
        status_contract["header_names"] = sorted(
            set(status_contract["header_names"])
            | {name.lower() for name in response["headers"]}
        )
        status_contract["body"] = _merge_optional_schema(
            status_contract["body"], response["body"]
        )

    evidence = canonical_json(sanitized).encode("utf-8")
    return {
        "schema_version": 1,
        "kind": "observed_api_contract",
        "capture_count": len(sanitized),
        "evidence_sha256": hashlib.sha256(evidence).hexdigest(),
        "limitations": [
            "Describes supplied observations only.",
            "Does not infer field requiredness or unobserved behavior.",
            "Does not establish authorization, ownership, or production compatibility.",
        ],
        "endpoints": {key: endpoints[key] for key in sorted(endpoints)},
    }
