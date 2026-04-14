"""
db.py — Folio data layer. All SQL lives here. Paths are CWD-based by default.

Call configure(cwd) to override all path constants before any other function.
"""

import os
import re
import shutil
import sqlite3

# ---------------------------------------------------------------------------
# Path constants — resolved relative to CWD at import time
# ---------------------------------------------------------------------------

_cwd = os.getcwd()

DB_PATH         = os.path.join(_cwd, "tools", "design.db")
DESIGN_DIR      = os.path.join(_cwd, "design")
SCREENSHOTS_DIR = os.path.join(_cwd, "tools", "screenshots")
SYSTEM_MD_PATH  = os.path.join(_cwd, "tools", "system.md")
TEMPLATE_PATH   = os.path.join(os.path.dirname(__file__), "system.md")


def configure(cwd: str) -> None:
    """Reset all path constants to be relative to cwd. Call before any other fn."""
    global DB_PATH, DESIGN_DIR, SCREENSHOTS_DIR, SYSTEM_MD_PATH

    assert os.path.isabs(cwd), f"cwd must be absolute: {cwd!r}"

    DB_PATH         = os.path.join(cwd, "tools", "design.db")
    DESIGN_DIR      = os.path.join(cwd, "design")
    SCREENSHOTS_DIR = os.path.join(cwd, "tools", "screenshots")
    SYSTEM_MD_PATH  = os.path.join(cwd, "tools", "system.md")


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Return a connection with Row factory, FK enforcement, and WAL mode."""
    assert DB_PATH, "DB_PATH must not be empty"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


# ---------------------------------------------------------------------------
# Schema init + seeding
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    type          TEXT NOT NULL CHECK(type IN ('screen','layout','component','flow')),
    name          TEXT NOT NULL,
    description   TEXT,
    usage         TEXT,
    selected_file TEXT,
    rationale     TEXT,
    status        TEXT NOT NULL DEFAULT 'exploring'
                  CHECK(status IN ('exploring','approved','finalised')),
    created_at    TEXT DEFAULT (datetime('now')),
    updated_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS variants (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id        INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    file           TEXT NOT NULL,
    label          TEXT,
    ui_description TEXT,
    screenshot     TEXT,
    notes          TEXT,
    created_at     TEXT DEFAULT (datetime('now'))
);
"""


def init_db() -> None:
    """Create DB schema, screenshots dir, and copy system.md template if needed."""
    tools_dir = os.path.dirname(DB_PATH)
    assert tools_dir, "tools_dir must not be empty"

    os.makedirs(tools_dir, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    conn = get_db()
    conn.executescript(_SCHEMA)
    conn.commit()
    conn.close()

    if not os.path.exists(SYSTEM_MD_PATH):
        assert os.path.exists(TEMPLATE_PATH), (
            f"system.md template not found at {TEMPLATE_PATH!r}"
        )
        shutil.copy(TEMPLATE_PATH, SYSTEM_MD_PATH)


# Suffixes to strip when grouping design files into items.
_VARIANT_SUFFIX_PATTERN = re.compile(
    r"(-v\d+|_alt\d*|-option-[^.]+)$",
    re.IGNORECASE,
)


def _stem_to_name(stem: str) -> str:
    """Convert a filename stem like 'reading-view' into 'Reading View'."""
    return stem.replace("-", " ").replace("_", " ").title()


def seed_from_design() -> int:
    """
    Scan DESIGN_DIR for HTML files. Group by stem (stripping variant suffixes).
    Creates one item per group and one variant per file. Returns count of items created.
    """
    if not os.path.isdir(DESIGN_DIR):
        return 0

    html_files = sorted(
        f for f in os.listdir(DESIGN_DIR) if f.lower().endswith(".html")
    )

    if not html_files:
        return 0

    # Map base_stem → [filename, ...]
    groups: dict[str, list[str]] = {}
    for filename in html_files:
        raw_stem = os.path.splitext(filename)[0]
        base_stem = _VARIANT_SUFFIX_PATTERN.sub("", raw_stem)
        groups.setdefault(base_stem, []).append(filename)

    conn = get_db()
    items_created = 0

    for base_stem, files in groups.items():
        name = _stem_to_name(base_stem)
        cursor = conn.execute(
            "INSERT INTO items (type, name) VALUES (?, ?)",
            ("screen", name),
        )
        item_id = cursor.lastrowid
        assert item_id is not None, "INSERT into items returned no rowid"

        for index, filename in enumerate(files):
            label = f"v{index + 1}"
            conn.execute(
                "INSERT INTO variants (item_id, file, label) VALUES (?, ?, ?)",
                (item_id, filename, label),
            )

        # First file becomes selected_file
        conn.execute(
            "UPDATE items SET selected_file = ? WHERE id = ?",
            (files[0], item_id),
        )
        items_created += 1

    conn.commit()
    conn.close()
    return items_created


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


def _fetch_variants(conn: sqlite3.Connection, item_id: int) -> list[dict]:
    """Fetch all variants for an item, ordered by created_at."""
    cursor = conn.execute(
        "SELECT * FROM variants WHERE item_id = ? ORDER BY created_at, id",
        (item_id,),
    )
    return [_row_to_dict(r) for r in cursor.fetchall()]


def _fetch_item_with_variants(conn: sqlite3.Connection, item_id: int) -> dict | None:
    """Return item dict with nested 'variants' list, or None if not found."""
    cursor = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    item = _row_to_dict(row)
    item["variants"] = _fetch_variants(conn, item_id)
    return item


# ---------------------------------------------------------------------------
# Item CRUD
# ---------------------------------------------------------------------------

_VALID_TYPES    = {"screen", "layout", "component", "flow"}
_VALID_STATUSES = {"exploring", "approved", "finalised"}
_VALID_ITEM_FIELDS = {
    "type", "name", "description", "usage",
    "selected_file", "rationale", "status",
}


def list_items(type_filter: str | None = None) -> list[dict]:
    """Return all items with nested variants. Optionally filter by type."""
    assert type_filter is None or type_filter in _VALID_TYPES, (
        f"Invalid type_filter: {type_filter!r}"
    )

    conn = get_db()
    if type_filter is None:
        cursor = conn.execute("SELECT * FROM items ORDER BY created_at, id")
    else:
        cursor = conn.execute(
            "SELECT * FROM items WHERE type = ? ORDER BY created_at, id",
            (type_filter,),
        )

    rows = cursor.fetchall()
    items = []
    for row in rows:
        item = _row_to_dict(row)
        item["variants"] = _fetch_variants(conn, item["id"])
        items.append(item)

    conn.close()
    return items


def get_item(item_id: int) -> dict | None:
    """Return a single item with nested variants, or None."""
    assert isinstance(item_id, int), f"item_id must be int: {item_id!r}"
    assert item_id > 0, f"item_id must be positive: {item_id}"

    conn = get_db()
    result = _fetch_item_with_variants(conn, item_id)
    conn.close()
    return result


def create_item(
    type: str,
    name: str,
    description: str | None = None,
    usage: str | None = None,
) -> dict:
    """Insert a new item and return it as a dict."""
    assert type in _VALID_TYPES, f"Invalid type: {type!r}"
    assert name and name.strip(), "name must not be empty"

    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO items (type, name, description, usage)
        VALUES (?, ?, ?, ?)
        """,
        (type, name.strip(), description, usage),
    )
    item_id = cursor.lastrowid
    assert item_id is not None, "INSERT into items returned no rowid"

    conn.commit()
    result = _fetch_item_with_variants(conn, item_id)
    conn.close()

    assert result is not None, f"Newly created item {item_id} not found"
    return result


def update_item(item_id: int, **fields) -> dict | None:
    """Update allowed fields on an item. Returns updated item or None if not found."""
    assert isinstance(item_id, int), f"item_id must be int: {item_id!r}"
    assert item_id > 0, f"item_id must be positive: {item_id}"
    assert fields, "At least one field required for update"

    unknown = set(fields) - _VALID_ITEM_FIELDS
    assert not unknown, f"Unknown item fields: {unknown}"

    if "type" in fields:
        assert fields["type"] in _VALID_TYPES, f"Invalid type: {fields['type']!r}"
    if "status" in fields:
        assert fields["status"] in _VALID_STATUSES, f"Invalid status: {fields['status']!r}"

    assignments = ", ".join(f"{col} = ?" for col in fields)
    values = list(fields.values())
    values.append(item_id)

    conn = get_db()
    conn.execute(
        f"UPDATE items SET {assignments}, updated_at = datetime('now') WHERE id = ?",
        values,
    )
    conn.commit()
    result = _fetch_item_with_variants(conn, item_id)
    conn.close()
    return result


def delete_item(item_id: int) -> bool:
    """Delete item and cascade variants. Returns True if a row was deleted."""
    assert isinstance(item_id, int), f"item_id must be int: {item_id!r}"
    assert item_id > 0, f"item_id must be positive: {item_id}"

    conn = get_db()
    cursor = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ---------------------------------------------------------------------------
# Variant CRUD
# ---------------------------------------------------------------------------

def create_variant(
    item_id: int,
    file: str,
    label: str | None = None,
    ui_description: str | None = None,
    notes: str | None = None,
) -> dict:
    """Insert a new variant for an item. Returns the variant as a dict."""
    assert isinstance(item_id, int), f"item_id must be int: {item_id!r}"
    assert item_id > 0, f"item_id must be positive: {item_id}"
    assert file and file.strip(), "file must not be empty"

    conn = get_db()

    # Validate item exists before inserting
    exists = conn.execute("SELECT 1 FROM items WHERE id = ?", (item_id,)).fetchone()
    if exists is None:
        conn.close()
        raise ValueError(f"Item {item_id} not found")

    cursor = conn.execute(
        """
        INSERT INTO variants (item_id, file, label, ui_description, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (item_id, file.strip(), label, ui_description, notes),
    )
    variant_id = cursor.lastrowid
    assert variant_id is not None, "INSERT into variants returned no rowid"

    conn.commit()
    row = conn.execute("SELECT * FROM variants WHERE id = ?", (variant_id,)).fetchone()
    conn.close()

    assert row is not None, f"Newly created variant {variant_id} not found"
    return _row_to_dict(row)


def delete_variant(variant_id: int) -> bool:
    """Delete a variant by id. Returns True if a row was deleted."""
    assert isinstance(variant_id, int), f"variant_id must be int: {variant_id!r}"
    assert variant_id > 0, f"variant_id must be positive: {variant_id}"

    conn = get_db()
    cursor = conn.execute("DELETE FROM variants WHERE id = ?", (variant_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def select_variant(variant_id: int) -> dict | None:
    """
    Set a variant's file as the parent item's selected_file.
    Returns the updated parent item dict, or None if variant not found.
    """
    assert isinstance(variant_id, int), f"variant_id must be int: {variant_id!r}"
    assert variant_id > 0, f"variant_id must be positive: {variant_id}"

    conn = get_db()
    row = conn.execute(
        "SELECT item_id, file FROM variants WHERE id = ?", (variant_id,)
    ).fetchone()

    if row is None:
        conn.close()
        return None

    item_id = row["item_id"]
    file    = row["file"]

    assert item_id is not None, "variant has null item_id"
    assert file,                "variant has empty file"

    conn.execute(
        "UPDATE items SET selected_file = ?, updated_at = datetime('now') WHERE id = ?",
        (file, item_id),
    )
    conn.commit()
    result = _fetch_item_with_variants(conn, item_id)
    conn.close()
    return result


def update_variant_screenshot(variant_id: int, screenshot_path: str) -> bool:
    """Store a relative screenshot path on a variant. Returns True on success."""
    assert isinstance(variant_id, int), f"variant_id must be int: {variant_id!r}"
    assert variant_id > 0, f"variant_id must be positive: {variant_id}"
    assert screenshot_path and screenshot_path.strip(), "screenshot_path must not be empty"

    conn = get_db()
    cursor = conn.execute(
        "UPDATE variants SET screenshot = ? WHERE id = ?",
        (screenshot_path.strip(), variant_id),
    )
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


# ---------------------------------------------------------------------------
# System doc sync
# ---------------------------------------------------------------------------

_DECISIONS_START = "<!-- DECISIONS-START -->"
_DECISIONS_END   = "<!-- DECISIONS-END -->"


def sync_system() -> str:
    """
    Read approved/finalised items from DB and write a decisions table
    between the marker comments in system.md. Returns the new file content.
    """
    assert os.path.exists(SYSTEM_MD_PATH), (
        f"system.md not found at {SYSTEM_MD_PATH!r} — run init first"
    )

    conn = get_db()
    cursor = conn.execute(
        """
        SELECT id, type, name, status, rationale, selected_file
        FROM items
        WHERE status IN ('approved', 'finalised')
        ORDER BY type, name
        """,
    )
    decided_items = [_row_to_dict(r) for r in cursor.fetchall()]
    conn.close()

    # Build decisions table
    lines: list[str] = []
    lines.append("")
    lines.append("| # | Type | Name | Status | Selected File | Rationale |")
    lines.append("|---|------|------|--------|--------------|-----------|")

    for item in decided_items:
        rationale     = (item["rationale"] or "").replace("|", "\\|")
        selected_file = item["selected_file"] or ""
        lines.append(
            f"| {item['id']} | {item['type']} | {item['name']} "
            f"| {item['status']} | {selected_file} | {rationale} |"
        )

    lines.append("")
    table_block = "\n".join(lines)

    with open(SYSTEM_MD_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert _DECISIONS_START in content, (
        f"Marker {_DECISIONS_START!r} not found in {SYSTEM_MD_PATH!r}"
    )
    assert _DECISIONS_END in content, (
        f"Marker {_DECISIONS_END!r} not found in {SYSTEM_MD_PATH!r}"
    )

    start_index = content.index(_DECISIONS_START) + len(_DECISIONS_START)
    end_index   = content.index(_DECISIONS_END)

    assert start_index < end_index, "DECISIONS-START appears after DECISIONS-END"

    new_content = (
        content[:start_index]
        + table_block
        + content[end_index:]
    )

    with open(SYSTEM_MD_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    return new_content
