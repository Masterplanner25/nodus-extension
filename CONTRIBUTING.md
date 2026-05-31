# Contributing to nodus-extension

## Setup

```bash
git clone https://github.com/Masterplanner25/nodus-extension.git
cd nodus-extension
pip install -e ".[dev]"
```

Tests require `nodus-lang` source on the path:

```bash
PYTHONPATH="src:C:/dev/Coding Language/src" pytest tests/ -q
```

## Running tests

```bash
# With nodus-lang source
PYTHONPATH="src:C:/dev/Coding Language/src" pytest tests/ -q

# Coverage
PYTHONPATH="src:C:/dev/Coding Language/src" pytest tests/ --cov=nodus_extension -q
```

## Code style

- Python 3.11+
- Pydantic v2 for manifest models
- Extension args are always JSON strings (not dicts) — keep this invariant
- Subprocess sandbox is tier 1 (insecure-dev); OCI/VM are v0.2+ tiers

## Test fixtures

Extension fixtures live in `tests/fixtures/`. Each fixture is a minimal
extension directory with `nodus-extension.json` and `extension.py`.

## Submitting changes

1. Fork the repo and create a branch from `main`
2. Add tests for any new behaviour
3. Ensure tests pass
4. Open a pull request with a description of what changes and why
