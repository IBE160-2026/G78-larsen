"""DR-3, AD-17: every file in `frontend/public/` has a row in `ASSETS.md`, and the check names a file that has none.

A row names the file by its path under `frontend/public/` in backticks, for example `fonts/finlandica-variable.woff2`.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "frontend" / "public"
ASSETS = ROOT / "ASSETS.md"


def rows(assets_text: str) -> list[str]:
    """The table rows of ASSETS.md (lines that start with `|`)."""
    return [line for line in assets_text.splitlines() if line.lstrip().startswith("|")]


def missing_rows(public: Path, assets_text: str) -> list[str]:
    """Files under `public` (as paths relative to it) that no table row of ASSETS.md names in backticks."""
    table = rows(assets_text)
    missing = []
    for f in sorted(p for p in public.rglob("*") if p.is_file()):
        rel = f.relative_to(public).as_posix()
        if not any(f"`{rel}`" in row for row in table):
            missing.append(rel)
    return missing


def test_every_public_file_has_a_row_in_assets_md():
    assert PUBLIC.is_dir()
    missing = missing_rows(PUBLIC, ASSETS.read_text(encoding="utf-8"))
    assert not missing, f"files in frontend/public/ without a row in ASSETS.md: {', '.join(missing)}"


def test_a_file_without_a_row_is_named(tmp_path):
    (tmp_path / "fonts").mkdir()
    (tmp_path / "fonts" / "listed.woff2").write_bytes(b"x")
    (tmp_path / "unlisted.jpg").write_bytes(b"x")
    text = "| File | Source |\n|---|---|\n| `fonts/listed.woff2` | somewhere |\n\nProse naming `unlisted.jpg` is no row.\n"
    assert missing_rows(tmp_path, text) == ["unlisted.jpg"]
