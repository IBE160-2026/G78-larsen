# G78 — AI & I

Gruppeprosjekt i **IBE160 Programmering med KI** ved Høgskolen i Molde, høsten 2026 (15 studiepoeng).

Repoet inneholder gruppens applikasjon og dokumentasjon av utvikling, testing og kvalitetssikring med KI.

## Medlemmer

- Lisa Katarina Larsen

---

# Booking Platform

A booking platform for saunas. The backend is written in Python; the frontend is JavaScript. Frameworks are chosen in the architecture phase.

## Python tooling: uv

The backend is managed with [uv](https://docs.astral.sh/uv/). It replaces pip, venv, pyenv and poetry, so do not use those here.

| Instead of                          | Use                        |
| ----------------------------------- | -------------------------- |
| `pyenv install` / `pyenv local`     | `.python-version` (uv installs the interpreter on demand) |
| `python -m venv` / `activate`       | `uv sync` (creates `.venv`) |
| `pip install x` / `poetry add x`    | `uv add x`                 |
| `pip install -r requirements.txt`   | `uv sync`                  |
| `poetry run x` / activated venv     | `uv run x`                 |
| `poetry lock`                       | `uv lock`                  |

### Getting started

```sh
uv sync                  # install the pinned Python and all dependencies
uv run booking-platform  # run the backend entry point
```

### Everyday commands

```sh
uv add <package>          # add a runtime dependency
uv add --dev <package>    # add a development dependency (tests, linters)
uv remove <package>       # remove a dependency
uv run pytest             # run a command inside the project environment
uv lock --upgrade         # upgrade locked versions
```

### Rules

- `pyproject.toml` is the single source of truth for dependencies; `uv.lock` pins exact versions. Commit both.
- `.python-version` pins the Python version for everyone. `requires-python` in `pyproject.toml` sets the supported floor.
- Never edit `uv.lock` by hand, and never commit `.venv/`.
- Do not add a `requirements.txt`, `poetry.lock` or `Pipfile`.

## Layout

```
src/booking_platform/   Python package (backend)
pyproject.toml          Project metadata and dependencies
uv.lock                 Locked dependency versions
.docs/                  Planning artifacts (product brief, later PRD and architecture)
_bmad/                  BMad Method configuration
.claude/skills/         BMad skills for Claude Code
```
