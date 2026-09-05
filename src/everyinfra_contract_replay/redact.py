from __future__ import annotations

import copy
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .io import ContractReplayError

SECRET_HEADER_NAMES = {
    "authorization",
    "cookie",
    "proxy-authorization",
    "set-cookie",
    "x-api-key",
}
SECRET_KEY_PARTS = (
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "password",
    "passwd",
    "refresh_token",
    "secret",
    "session",
    "token",
)
CONTACT_KEY_PARTS = ("email", "phone", "telephone")
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)\+?[0-9][0-9 ()-]{6,}[0-9](?!\w)")
BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
TOKEN_RE = re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{8,}\b")


def _normalized_key(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_")


def _key_matches(key: Any, parts: tuple[str, ...]) -> bool:
    normalized = _normalized_key(key)
    return any(part in normalized for part in parts)


def redact_text(value: str) -> str:
    value = BEARER_RE.sub("Bearer [REDACTED]", value)
    value = TOKEN_RE.sub("[REDACTED_TOKEN]", value)
    value = EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    return PHONE_RE.sub("[REDACTED_PHONE]", value)


def redact_value(value: Any, parent_key: Any = "") -> Any:
    if _key_matches(parent_key, SECRET_KEY_PARTS):
        return "[REDACTED]"
    if _key_matches(parent_key, CONTACT_KEY_PARTS):
        return "[REDACTED_CONTACT]"
    if isinstance(value, dict):
        return {
            str(key): redact_value(item, key)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def redact_headers(headers: Any) -> dict[str, Any]:
    if headers is None:
        return {}
    if not isinstance(headers, dict):
        raise ContractReplayError("headers must be a JSON object")
    sanitized: dict[str, Any] = {}
    for name, value in sorted(headers.items(), key=lambda pair: str(pair[0]).lower()):
        header_name = str(name)
        if header_name.lower() in SECRET_HEADER_NAMES:
            sanitized[header_name] = "[REDACTED]"
        else:
            sanitized[header_name] = redact_value(value, header_name)
    return sanitized


def redact_url(raw_url: Any) -> str:
    if not isinstance(raw_url, str):
        raise ContractReplayError("request.url must be a string")
    parsed = urlsplit(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ContractReplayError("request.url must be an absolute http or https URL")
    if parsed.username is not None or parsed.password is not None:
        raise ContractReplayError("request.url must not contain username or password")
    masked_query = []
    for key, _value in parse_qsl(parsed.query, keep_blank_values=True):
        replacement = "[REDACTED]" if _key_matches(key, SECRET_KEY_PARTS + CONTACT_KEY_PARTS) else "[VALUE]"
        masked_query.append((key, replacement))
    return urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", urlencode(masked_query), "")
    )


def sanitize_capture(capture: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(capture, dict):
        raise ContractReplayError("capture must be a JSON object")
    request = capture.get("request")
    response = capture.get("response")
    if not isinstance(request, dict) or not isinstance(response, dict):
        raise ContractReplayError("capture requires request and response objects")

    method = request.get("method")
    if not isinstance(method, str) or not method.strip():
        raise ContractReplayError("request.method must be a non-empty string")
    status = response.get("status")
    if isinstance(status, bool) or not isinstance(status, int) or not 100 <= status <= 599:
        raise ContractReplayError("response.status must be an integer from 100 to 599")

    sanitized = {
        "schema_version": 1,
        "capture_id": redact_text(str(capture.get("capture_id", "unnamed"))),
        "request": {
            "method": method.strip().upper(),
            "url": redact_url(request.get("url")),
            "headers": redact_headers(request.get("headers")),
            "body": redact_value(copy.deepcopy(request.get("body"))),
        },
        "response": {
            "status": status,
            "headers": redact_headers(response.get("headers")),
            "body": redact_value(copy.deepcopy(response.get("body"))),
        },
    }
    return sanitized
