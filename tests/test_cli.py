from pathlib import Path

import pytest

from brandframe.cli.main import main


def write_config(path: Path) -> None:
    path.write_text(
        """
schema_version: 1
project:
  key: client_ops
  name: Client Operations
brand:
  key: brand_a
  name: Brand A
integrations:
  meta:
    accounts:
      - act_123
    credentials:
      shared_ref: meta.operator_default
  service:
    api_key: do-not-print
""".strip(),
        encoding="utf-8",
    )


def test_validate_command_reports_project(tmp_path: Path, capsys) -> None:
    path = tmp_path / "brand.yaml"
    write_config(path)
    main(["validate", "--config", str(path)])
    output = capsys.readouterr().out
    assert "config ok: client_ops (Client Operations)" in output
    assert "shared credential refs: 1" in output


def test_validate_command_checks_shared_references(tmp_path: Path, capsys) -> None:
    path = tmp_path / "brand.yaml"
    shared = tmp_path / "credentials.yaml"
    write_config(path)
    shared.write_text(
        "meta:\n  operator_default:\n    token_path: ~/.config/token\n", encoding="utf-8"
    )
    main(
        [
            "validate",
            "--config",
            str(path),
            "--check-shared",
            "--shared-credentials",
            str(shared),
        ]
    )
    assert "shared credential ok: meta -> meta.operator_default" in capsys.readouterr().out


def test_show_command_redacts_secrets(tmp_path: Path, capsys) -> None:
    path = tmp_path / "brand.yaml"
    write_config(path)
    main(["show", "--config", str(path), "integrations.service", "--json"])
    output = capsys.readouterr().out
    assert "do-not-print" not in output
    assert "[REDACTED]" in output


def test_guard_account_command_accepts_allowlisted_account(tmp_path: Path, capsys) -> None:
    path = tmp_path / "brand.yaml"
    write_config(path)
    main(["guard-account", "--config", str(path), "123"])
    assert "account allowed: meta -> 123" in capsys.readouterr().out


def test_invalid_command_reports_argparse_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["unknown"])

    assert exc.value.code == 2
    assert "argument command: invalid choice: 'unknown'" in capsys.readouterr().err
