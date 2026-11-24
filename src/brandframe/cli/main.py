from __future__ import annotations

import argparse
import json
from importlib.metadata import version
from pathlib import Path
from typing import Any

import yaml

from brandframe.config import (
    default_shared_credentials_path,
    load_config,
    load_yaml_mapping,
    resolve_reference,
    resolve_shared_credentials,
    shared_credentials_reference,
)
from brandframe.guards import assert_account_allowed
from brandframe.redaction import redact_secrets


def _add_config_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Configuration path. Defaults to BRANDFRAME_CONFIG or ./brand.yaml.",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="brandframe",
        description="Configuration and safety tooling for brand repositories.",
    )
    parser.add_argument("--version", action="version", version=version("brandframe"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a brand configuration.")
    _add_config_argument(validate_parser)
    validate_parser.add_argument(
        "--check-shared",
        action="store_true",
        help="Resolve all shared credential references.",
    )
    validate_parser.add_argument(
        "--shared-credentials",
        type=Path,
        default=None,
        help="Shared credentials path. Defaults to the platform config directory.",
    )

    show_parser = subparsers.add_parser("show", help="Show redacted configuration data.")
    _add_config_argument(show_parser)
    show_parser.add_argument(
        "reference", nargs="?", help="Optional dotted reference, such as brand.name."
    )
    show_parser.add_argument("--json", action="store_true", help="Render JSON instead of YAML.")

    guard_parser = subparsers.add_parser("guard-account", help="Verify an account allowlist entry.")
    _add_config_argument(guard_parser)
    guard_parser.add_argument("account_id")
    guard_parser.add_argument("--integration", default="meta")

    return parser


def _shared_references(payload: dict[str, Any]) -> list[tuple[str, str]]:
    integrations = payload.get("integrations", {})
    references: list[tuple[str, str]] = []
    for integration in sorted(integrations):
        reference = shared_credentials_reference(payload, integration)
        if reference:
            references.append((integration, reference))
    return references


def _validate(args: argparse.Namespace) -> None:
    payload = load_config(args.config)
    project = payload["project"]
    print(f"config ok: {project['key']} ({project['name']})")

    references = _shared_references(payload)
    if not args.check_shared:
        if references:
            print(f"shared credential refs: {len(references)}")
        return

    path = args.shared_credentials or default_shared_credentials_path()
    shared = load_yaml_mapping(path)
    for integration, reference in references:
        resolve_shared_credentials(shared, reference)
        print(f"shared credential ok: {integration} -> {reference}")


def _show(args: argparse.Namespace) -> None:
    payload: Any = load_config(args.config)
    if args.reference:
        payload = resolve_reference(payload, args.reference)
    safe_payload = redact_secrets(payload)
    if args.json:
        print(json.dumps(safe_payload, indent=2, sort_keys=True))
        return

    print(yaml.safe_dump(safe_payload, sort_keys=False).rstrip())


def _guard_account(args: argparse.Namespace) -> None:
    payload = load_config(args.config)
    assert_account_allowed(args.account_id, payload, args.integration)
    print(f"account allowed: {args.integration} -> {args.account_id}")


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        _validate(args)
        return
    if args.command == "show":
        _show(args)
        return
    if args.command == "guard-account":
        _guard_account(args)
