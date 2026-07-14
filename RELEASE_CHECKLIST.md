# Release Checklist

`brandframe` publishes through GitHub Actions trusted publishing.

## One-time setup

Create and verify PyPI and TestPyPI accounts with two-factor authentication enabled.

GitHub repository settings:

- repository: `OuCodes/brandframe`
- environments: `testpypi` and `pypi`
- workflow: `.github/workflows/release.yml`

Configure pending GitHub Actions publishers on both registries:

- project: `brandframe`
- owner: `OuCodes`
- repository: `brandframe`
- workflow: `release.yml`
- environment: `testpypi` on TestPyPI and `pypi` on PyPI

No long-lived package registry token is required.

## Before every release

- update the version in `pyproject.toml`
- move release notes from `Unreleased` into a dated version section
- scan tracked files for client names, identifiers, email addresses, absolute paths, and secrets
- verify README examples and metadata

```bash
./.venv/bin/python -m ruff check .
./.venv/bin/python -m pytest
./.venv/bin/python -m build
./.venv/bin/python -m brandframe --help
```

## TestPyPI

Run the `Release` workflow manually from `main`, then verify:

```bash
python3.12 -m venv /tmp/brandframe-test
/tmp/brandframe-test/bin/python -m pip install --upgrade pip
/tmp/brandframe-test/bin/python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple \
  brandframe
/tmp/brandframe-test/bin/brandframe --help
```

## PyPI

After TestPyPI verification:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Tag pushes publish to real PyPI. Verify with a fresh environment and create a GitHub Release.

## Current wiring

- distribution, import, and CLI: `brandframe`
- GitHub: `OuCodes/brandframe`
- version: `0.1.0`
- Python: `>=3.11`
