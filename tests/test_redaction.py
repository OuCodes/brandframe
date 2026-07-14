from brandframe.redaction import REDACTED, redact_secrets


def test_redact_secrets_redacts_nested_sensitive_values() -> None:
    payload = {
        "brand": {"name": "Brand A"},
        "integrations": {
            "service": {
                "api_key": "private",
                "nested": [{"access-token": "private-too"}],
            }
        },
    }
    result = redact_secrets(payload)
    assert result["brand"]["name"] == "Brand A"
    assert result["integrations"]["service"]["api_key"] == REDACTED
    assert result["integrations"]["service"]["nested"][0]["access-token"] == REDACTED


def test_redact_secrets_does_not_mutate_input() -> None:
    payload = {"password": "private"}
    redact_secrets(payload)
    assert payload["password"] == "private"
