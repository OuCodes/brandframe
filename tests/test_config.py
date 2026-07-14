from pathlib import Path

import pytest

from brandframe.config import (
    CONFIG_ENV_VAR,
    SHARED_CREDENTIALS_ENV_VAR,
    ConfigValidationError,
    default_config_path,
    default_shared_credentials_path,
    load_config,
    resolve_reference,
    resolve_shared_credentials,
    shared_credentials_reference,
    validate_config,
)


def minimal_config() -> dict:
    return {
        "schema_version": 1,
        "project": {"key": "client_ops", "name": "Client Operations"},
        "brand": {"key": "brand_a", "name": "Brand A"},
        "integrations": {
            "meta": {
                "accounts": ["act_123"],
                "credentials": {"shared_ref": "meta.operator_default"},
            }
        },
    }


def test_validate_config_accepts_brand_repository() -> None:
    validate_config(minimal_config())


def test_validate_config_allows_project_without_brand() -> None:
    payload = minimal_config()
    payload.pop("brand")
    validate_config(payload)


@pytest.mark.parametrize("version", [None, 0, 2, "1"])
def test_validate_config_rejects_unsupported_schema(version: object) -> None:
    payload = minimal_config()
    payload["schema_version"] = version
    with pytest.raises(ConfigValidationError, match="schema_version"):
        validate_config(payload)


def test_validate_config_requires_project_identity() -> None:
    payload = minimal_config()
    payload["project"]["key"] = ""
    with pytest.raises(ConfigValidationError, match="project.key"):
        validate_config(payload)


def test_validate_config_rejects_invalid_optional_section() -> None:
    payload = minimal_config()
    payload["reports"] = []
    with pytest.raises(ConfigValidationError, match="reports must be a mapping"):
        validate_config(payload)


def test_validate_config_rejects_local_and_shared_credentials() -> None:
    payload = minimal_config()
    payload["integrations"]["meta"]["credentials"]["local_path"] = "secrets/meta.json"
    with pytest.raises(ConfigValidationError, match="cannot set both"):
        validate_config(payload)


def test_load_config_reads_yaml(tmp_path: Path) -> None:
    path = tmp_path / "brand.yaml"
    path.write_text(
        "schema_version: 1\nproject:\n  key: client_ops\n  name: Client Operations\n",
        encoding="utf-8",
    )
    assert load_config(path)["project"]["key"] == "client_ops"


def test_default_paths_respect_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(CONFIG_ENV_VAR, "~/custom/brand.yaml")
    monkeypatch.setenv(SHARED_CREDENTIALS_ENV_VAR, "~/custom/credentials.yaml")
    assert default_config_path() == Path("~/custom/brand.yaml").expanduser()
    assert default_shared_credentials_path() == Path("~/custom/credentials.yaml").expanduser()


def test_shared_credentials_reference_returns_reference() -> None:
    assert shared_credentials_reference(minimal_config(), "meta") == "meta.operator_default"


def test_resolve_reference_supports_arbitrary_depth() -> None:
    assert resolve_reference(minimal_config(), "integrations.meta.accounts") == ["act_123"]


def test_resolve_reference_rejects_missing_value() -> None:
    with pytest.raises(ConfigValidationError, match="reference not found"):
        resolve_reference(minimal_config(), "brand.domain")


def test_resolve_shared_credentials_requires_mapping() -> None:
    shared = {"meta": {"operator_default": "secret"}}
    with pytest.raises(ConfigValidationError, match="must resolve to a mapping"):
        resolve_shared_credentials(shared, "meta.operator_default")
