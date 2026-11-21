"""DR-3, AD-17: every file in `frontend/public/` has a row in `ASSETS.md`, every image and font row names a file that
exists and gives its source as a link, and each check names what it finds wrong.

A row names the file by its path under `frontend/public/` in backticks, for example `fonts/finlandica-variable.woff2`.
"""

from __future__ import annotations

import re
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


def asset_rows(assets_text: str) -> list[tuple[str, str]]:
    """(path, row) for each table row whose first cell is an image or font path in backticks."""
    found = []
    for row in rows(assets_text):
        first = row.strip().strip("|").split("|")[0].strip()
        m = re.fullmatch(r"`((?:images|fonts)/[^`]+)`", first)
        if m:
            found.append((m.group(1), row))
    return found


def missing_files(public: Path, assets_text: str) -> list[str]:
    """Image and font rows whose file is not under `public`, or whose row gives no source link."""
    wrong = []
    # exact case, as the Linux container serves it (Windows' `is_file` ignores case)
    files = {p.relative_to(public).as_posix() for p in public.rglob("*") if p.is_file()}
    for path, row in asset_rows(assets_text):
        if path not in files:
            wrong.append(f"{path} (no such file)")
        elif not re.search(r"\]\(https?://", row):
            wrong.append(f"{path} (no source link)")
    return wrong


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


def test_every_image_and_font_row_points_to_a_file_with_a_source():
    text = ASSETS.read_text(encoding="utf-8")
    assert asset_rows(text), "ASSETS.md has no image or font rows"
    wrong = missing_files(PUBLIC, text)
    assert not wrong, f"rows in ASSETS.md that do not hold: {', '.join(wrong)}"


def test_a_row_without_a_file_or_a_source_is_named(tmp_path):
    (tmp_path / "images").mkdir()
    (tmp_path / "images" / "here.jpg").write_bytes(b"x")
    (tmp_path / "images" / "unsourced.jpg").write_bytes(b"x")
    text = ("| File | Source |\n|---|---|\n| `images/here.jpg` | [photo](https://example.org/p) |\n"
            "| `images/gone.jpg` | [photo](https://example.org/q) |\n| `images/unsourced.jpg` | taken by us |\n")
    assert missing_files(tmp_path, text) == ["images/gone.jpg (no such file)", "images/unsourced.jpg (no source link)"]
