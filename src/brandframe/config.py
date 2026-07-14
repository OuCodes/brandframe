from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from platformdirs import user_config_path

CONFIG_ENV_VAR = "BRANDFRAME_CONFIG"
SHARED_CREDENTIALS_ENV_VAR = "BRANDFRAME_SHARED_CREDENTIALS"
DEFAULT_CONFIG_FILENAME = "brand.yaml"
SUPPORTED_SCHEMA_VERSION = 1
MAPPING_SECTIONS = ("brand", "paths", "credentials", "integrations", "reports", "cron")


class BrandframeError(ValueError):
    """Base error for invalid Brandframe configuration."""


class ConfigValidationError(BrandframeError):
    """Raised when a configuration document violates the schema."""


def default_config_path() -> Path:
    configured = os.environ.get(CONFIG_ENV_VAR, "").strip()
    if configured:
        return Path(configured).expanduser()

    return Path(DEFAULT_CONFIG_FILENAME)


def default_shared_credentials_path() -> Path:
    configured = os.environ.get(SHARED_CREDENTIALS_ENV_VAR, "").strip()
    if configured:
        return Path(configured).expanduser()

    return user_config_path("brandframe") / "credentials.yaml"


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload is None:
        return {}

    if not isinstance(payload, dict):
        raise ConfigValidationError(f"{path} must contain a YAML mapping")

    return payload


def _require_nonempty_string(mapping: dict[str, Any], key: str, label: str) -> None:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigValidationError(f"{label}.{key} is required")


def _validate_credential_selector(integration: str, credentials: Any) -> None:
    if credentials is None:
        return

    if not isinstance(credentials, dict):
        raise ConfigValidationError(f"integrations.{integration}.credentials must be a mapping")

    shared_ref = credentials.get("shared_ref")
    local_path = credentials.get("local_path")
    if shared_ref and local_path:
        raise ConfigValidationError(
            f"integrations.{integration}.credentials cannot set both shared_ref and local_path"
        )

    if shared_ref is not None and (not isinstance(shared_ref, str) or not shared_ref.strip()):
        raise ConfigValidationError(
            f"integrations.{integration}.credentials.shared_ref must be a non-empty string"
        )

    if local_path is not None and (not isinstance(local_path, str) or not local_path.strip()):
        raise ConfigValidationError(
            f"integrations.{integration}.credentials.local_path must be a non-empty string"
        )


def validate_config(payload: dict[str, Any]) -> None:
    version = payload.get("schema_version")
    if version != SUPPORTED_SCHEMA_VERSION:
        raise ConfigValidationError(
            f"schema_version must be {SUPPORTED_SCHEMA_VERSION}, got {version!r}"
        )

    project = payload.get("project")
    if not isinstance(project, dict):
        raise ConfigValidationError("project must be a mapping")
    _require_nonempty_string(project, "key", "project")
    _require_nonempty_string(project, "name", "project")

    for section in MAPPING_SECTIONS:
        value = payload.get(section)
        if value is not None and not isinstance(value, dict):
            raise ConfigValidationError(f"{section} must be a mapping")

    brand = payload.get("brand")
    if isinstance(brand, dict):
        _require_nonempty_string(brand, "key", "brand")
        _require_nonempty_string(brand, "name", "brand")

    integrations = payload.get("integrations", {})
    for name, integration in integrations.items():
        if not isinstance(name, str) or not name.strip():
            raise ConfigValidationError("integration names must be non-empty strings")
        if not isinstance(integration, dict):
            raise ConfigValidationError(f"integrations.{name} must be a mapping")
        _validate_credential_selector(name, integration.get("credentials"))


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or default_config_path()
    payload = load_yaml_mapping(config_path)
    validate_config(payload)
    return payload


def get_integration_config(payload: dict[str, Any], integration: str) -> dict[str, Any]:
    integrations = payload.get("integrations", {})
    if not isinstance(integrations, dict):
        raise ConfigValidationError("integrations must be a mapping")

    value = integrations.get(integration)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigValidationError(f"integrations.{integration} must be a mapping")

    return value


def shared_credentials_reference(payload: dict[str, Any], integration: str) -> str:
    integration_config = get_integration_config(payload, integration)
    credentials = integration_config.get("credentials")
    _validate_credential_selector(integration, credentials)
    if not credentials:
        return ""

    return str(credentials.get("shared_ref") or "").strip()


def resolve_reference(payload: dict[str, Any], reference: str) -> Any:
    if not reference:
        raise ConfigValidationError("reference cannot be empty")

    current: Any = payload
    for segment in reference.split("."):
        if not segment:
            raise ConfigValidationError(f"invalid reference: {reference}")
        if not isinstance(current, dict) or segment not in current:
            raise ConfigValidationError(f"reference not found: {reference}")
        current = current[segment]

    return current


def resolve_shared_credentials(
    shared_credentials: dict[str, Any], reference: str
) -> dict[str, Any]:
    value = resolve_reference(shared_credentials, reference)
    if not isinstance(value, dict):
        raise ConfigValidationError(
            f"shared credential reference must resolve to a mapping: {reference}"
        )

    return value
