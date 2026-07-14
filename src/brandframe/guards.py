from __future__ import annotations

from typing import Any

from brandframe.config import ConfigValidationError, get_integration_config


def normalize_account_id(account_id: str) -> str:
    normalized = str(account_id).strip()
    if normalized.startswith("act_"):
        return normalized[4:]
    return normalized


def allowed_accounts(payload: dict[str, Any], integration: str) -> set[str]:
    integration_config = get_integration_config(payload, integration)
    accounts = integration_config.get("accounts")
    if not isinstance(accounts, list) or not accounts:
        raise ConfigValidationError(f"integrations.{integration}.accounts must be a non-empty list")

    normalized = {normalize_account_id(value) for value in accounts if str(value).strip()}
    if not normalized:
        raise ConfigValidationError(f"integrations.{integration}.accounts cannot be empty")

    return normalized


def assert_account_allowed(
    account_id: str,
    payload: dict[str, Any],
    integration: str = "meta",
) -> None:
    normalized = normalize_account_id(account_id)
    if not normalized:
        raise ConfigValidationError("account_id cannot be empty")

    allowed = allowed_accounts(payload, integration)
    if normalized in allowed:
        return

    brand = payload.get("brand") or payload["project"]
    identity = brand.get("key") or brand.get("name")
    raise ConfigValidationError(
        f"ACCOUNT BLOCKED: {account_id} is not allowed for {identity!r} "
        f"in integrations.{integration}.accounts"
    )
