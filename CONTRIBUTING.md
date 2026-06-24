# Contributing to fitrl

Domain rules, CSV schema, stack, and conventions: see [CLAUDE.md](CLAUDE.md).
Project context and pipeline roadmap: see [CONTEXT.md](CONTEXT.md).

## Setup

Requires **Python 3.12+** and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/arthemide/fitrl.git
cd fitrl
make setup-dev                   # uv sync --frozen --group dev
```

Drop your `.fit` files under `data/raw/`.

## Workflow

1. Branch from `main` with a descriptive name:
   - `feat/grpo-reward` - new feature
   - `fix/zone-denominator` - bug fix
   - `docs/csv-schema` - documentation
   - `refactor/session-parser` - refactoring
2. Write code.
3. `make lint` - `ruff check --fix`, `ruff format`, then `ruff check` + `ty check`.
4. Open a PR against `main` - never push directly to `main`.

## Pipeline commands

```bash
make parse                       # parse .fit files → data/processed/output.csv
make annotate                    # interactive session annotation / validation
```

## Code conventions

- **One function per responsibility** (`parse_session`, `parse_zones`).
- **No `print` in business logic** - keep I/O at the edges (CLI entry points use `rich`).
- **Zone thresholds derived from `HR_MAX`** - never hardcode bpm values.
- Typed models via **Pydantic** (`Session`).
- `from __future__ import annotations` in modules.

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `ci:`.
