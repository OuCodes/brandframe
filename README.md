# brandframe

[![CI](https://github.com/OuCodes/brandframe/actions/workflows/ci.yml/badge.svg)](https://github.com/OuCodes/brandframe/actions/workflows/ci.yml)

Configuration and safety tooling for brand repositories.

`brandframe` gives brand-based operations repositories one validated `brand.yaml`, portable credential references, secret-safe inspection, and account allowlist guards.

## Install

```bash
pip install brandframe
```

Python 3.11 or newer is required.

## Quickstart

Create `brand.yaml` in the repository root:

```yaml
schema_version: 1

project:
  key: example_ops
  name: Example Operations

brand:
  key: example
  name: Example Brand

paths:
  data: data
  reports: data/reports

integrations:
  meta:
    accounts:
      - act_123456789
    credentials:
      shared_ref: meta.operator_default
```

Validate it:

```bash
brandframe validate
```

Inspect configuration without printing common secret fields:

```bash
brandframe show brand
brandframe show integrations.meta --json
```

Guard an integration account before a write:

```bash
brandframe guard-account act_123456789
```

## Configuration discovery

The default configuration is `./brand.yaml`. Override it with either:

```bash
brandframe validate --config path/to/brand.yaml
export BRANDFRAME_CONFIG=path/to/brand.yaml
```

Shared credentials default to the platform-specific Brandframe config directory. Override that location with `BRANDFRAME_SHARED_CREDENTIALS` or `--shared-credentials`.

## Shared credential references

Keep secret values outside client repositories:

```yaml
# brand.yaml
integrations:
  meta:
    credentials:
      shared_ref: meta.operator_default
```

```yaml
# ~/.config/brandframe/credentials.yaml on many Unix systems
meta:
  operator_default:
    token_path: ~/.config/example/meta-token
```

Validate every reference:

```bash
brandframe validate --check-shared
```

Brandframe validates that references resolve to mappings. It does not load referenced token files or authenticate with third-party services.

## Python API

```python
from brandframe import assert_account_allowed, load_config

config = load_config()
assert_account_allowed("act_123456789", config, integration="meta")
```

Core public helpers include:

- `load_config()`
- `validate_config()`
- `get_integration_config()`
- `resolve_reference()`
- `resolve_shared_credentials()`
- `redact_secrets()`
- `assert_account_allowed()`

## Schema version 1

Required:

- `schema_version: 1`
- `project.key`
- `project.name`

Optional first-class mapping sections:

- `brand`
- `paths`
- `credentials`
- `integrations`
- `reports`
- `cron`

When `brand` is present, `brand.key` and `brand.name` are required.

An integration credential selector may use either `shared_ref` or `local_path`, never both.

## Security boundaries

- `brandframe show` recursively redacts common secret-bearing keys.
- Shared credential references are validated without printing their values.
- Account guards fail closed when an allowlist is absent.
- `brand.yaml` should contain references and identifiers, not secret values.
- Redaction is defense in depth, not permission to commit secrets.

## Development

```bash
python3.12 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev]"
./.venv/bin/python -m pytest
./.venv/bin/python -m ruff check .
./.venv/bin/python -m build
```

## License

MIT
