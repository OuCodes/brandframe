from __future__ import annotations

from typing import Any

REDACTED = "[REDACTED]"
SENSITIVE_KEY_PARTS = (
    "api_key",
    "access_token",
    "refresh_token",
    "client_secret",
    "password",
    "private_key",
    "secret",
    "token",
)


def is_sensitive_key(key: object) -> bool:
    normalized = str(key).lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: REDACTED if is_sensitive_key(key) else redact_secrets(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [redact_secrets(item) for item in value]

    return value
