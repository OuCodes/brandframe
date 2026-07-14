import pytest

from brandframe.config import ConfigValidationError
from brandframe.guards import assert_account_allowed, normalize_account_id


def config() -> dict:
    return {
        "schema_version": 1,
        "project": {"key": "client_ops", "name": "Client Operations"},
        "brand": {"key": "brand_a", "name": "Brand A"},
        "integrations": {"meta": {"accounts": ["act_123", "456"]}},
    }


def test_normalize_account_id_removes_meta_prefix() -> None:
    assert normalize_account_id(" act_123 ") == "123"


def test_assert_account_allowed_accepts_prefixed_or_plain_id() -> None:
    assert_account_allowed("123", config())
    assert_account_allowed("act_456", config())


def test_assert_account_allowed_blocks_cross_brand_account() -> None:
    with pytest.raises(ConfigValidationError, match="ACCOUNT BLOCKED"):
        assert_account_allowed("act_999", config())


def test_assert_account_allowed_requires_allowlist() -> None:
    payload = config()
    payload["integrations"]["meta"].pop("accounts")
    with pytest.raises(ConfigValidationError, match="must be a non-empty list"):
        assert_account_allowed("123", payload)
