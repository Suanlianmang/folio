"""
db.py — Folio data layer. All SQL lives here. Paths are CWD-based by default.

Call configure(cwd) to override all path constants before any other function.
"""

import re
import shutil
import sqlite3
from pathlib import Path

# ---------------------------------------------------------------------------
# Path constants — resolved relative to CWD at import time
# ---------------------------------------------------------------------------

_cwd = Path.cwd()

DB_PATH         = _cwd / ".folio" / "design.db"
DESIGN_DIR      = _cwd / ".folio" / "design"
SCREENSHOTS_DIR = _cwd / ".folio" / "screenshots"
SYSTEM_MD_PATH  = _cwd / ".folio" / "system.md"
TEMPLATE_PATH   = Path.home() / ".folio" / "lib" / "system.md"


def configure(cwd: str | Path) -> None:
    """Reset all path constants to be relative to cwd. Call before any other fn."""
    global DB_PATH, DESIGN_DIR, SCREENSHOTS_DIR, SYSTEM_MD_PATH

    cwd = Path(cwd)
    assert cwd.is_absolute(), f"cwd must be absolute: {str(cwd)!r}"

    DB_PATH         = cwd / ".folio" / "design.db"
    DESIGN_DIR      = cwd / ".folio" / "design"
    SCREENSHOTS_DIR = cwd / ".folio" / "screenshots"
    SYSTEM_MD_PATH  = cwd / ".folio" / "system.md"


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
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS screens (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    description   TEXT,
    usage         TEXT,
    parent_id     INTEGER REFERENCES screens(id) ON DELETE SET NULL,
    selected_file TEXT,
    rationale     TEXT,
    status        TEXT NOT NULL DEFAULT 'exploring'
                  CHECK(status IN ('exploring','approved','finalised')),
    created_at    TEXT DEFAULT (datetime('now')),
    updated_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS components (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
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

CREATE TABLE IF NOT EXISTS flows (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
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

CREATE TABLE IF NOT EXISTS screen_variants (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    screen_id      INTEGER NOT NULL REFERENCES screens(id) ON DELETE CASCADE,
    file           TEXT NOT NULL,
    label          TEXT,
    ui_description TEXT,
    screenshot     TEXT,
    notes          TEXT,
    rationale      TEXT,
    flag           TEXT,
    flag_reason    TEXT,
    created_at     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS component_variants (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    component_id   INTEGER NOT NULL REFERENCES components(id) ON DELETE CASCADE,
    file           TEXT NOT NULL,
    label          TEXT,
    ui_description TEXT,
    screenshot     TEXT,
    notes          TEXT,
    rationale      TEXT,
    flag           TEXT,
    flag_reason    TEXT,
    created_at     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS flow_variants (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id        INTEGER NOT NULL REFERENCES flows(id) ON DELETE CASCADE,
    file           TEXT NOT NULL,
    label          TEXT,
    ui_description TEXT,
    screenshot     TEXT,
    notes          TEXT,
    rationale      TEXT,
    flag           TEXT,
    flag_reason    TEXT,
    created_at     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS flow_screens (
    flow_id   INTEGER NOT NULL REFERENCES flows(id) ON DELETE CASCADE,
    screen_id INTEGER NOT NULL REFERENCES screens(id) ON DELETE CASCADE,
    PRIMARY KEY (flow_id, screen_id)
);

CREATE TABLE IF NOT EXISTS component_usage (
    component_id INTEGER NOT NULL REFERENCES components(id) ON DELETE CASCADE,
    screen_id    INTEGER NOT NULL REFERENCES screens(id) ON DELETE CASCADE,
    PRIMARY KEY (component_id, screen_id)
);

CREATE TABLE IF NOT EXISTS deltas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('screen','component','flow')),
    entity_id   INTEGER NOT NULL,
    variant_id  INTEGER,
    type        TEXT NOT NULL,
    target      TEXT,
    from_val    TEXT,
    to_val      TEXT,
    reason      TEXT,
    outcome     TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);
"""


def init_db() -> None:
    """Create DB schema, screenshots dir, and copy system.md template if needed."""
    tools_dir = DB_PATH.parent
    assert tools_dir, "tools_dir must not be empty"

    tools_dir.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    DESIGN_DIR.mkdir(parents=True, exist_ok=True)

    conn = get_db()
    conn.executescript(_SCHEMA)
    _migrate_variants(conn)
    _migrate_entities(conn)
    _migrate_deltas(conn)
    conn.commit()
    conn.close()

    if not SYSTEM_MD_PATH.exists():
        assert TEMPLATE_PATH.exists(), (
            f"system.md template not found at {str(TEMPLATE_PATH)!r}"
        )
        shutil.copy(TEMPLATE_PATH, SYSTEM_MD_PATH)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_VARIANT_TABLES = ("screen_variants", "component_variants", "flow_variants")
_NEW_VARIANT_COLS = (
    ("rationale",   "TEXT"),
    ("flag",        "TEXT"),
    ("flag_reason", "TEXT"),
)


def _migrate_variants(conn: sqlite3.Connection) -> None:
    for table in _VARIANT_TABLES:
        existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for col, decl in _NEW_VARIANT_COLS:
            if col not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")


_ENTITY_TABLES = ("screens", "components", "flows")
_NEW_ENTITY_COLS = (
    ("hypothesis",   "TEXT"),
    ("focus",        "TEXT"),
    ("needs_review", "INTEGER NOT NULL DEFAULT 0"),
)


def _migrate_entities(conn: sqlite3.Connection) -> None:
    for table in _ENTITY_TABLES:
        existing = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        for col, decl in _NEW_ENTITY_COLS:
            if col not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")


_NEW_DELTA_COLS = (
    ("variant_id",   "INTEGER"),
    ("outcome_type", "TEXT"),
)


def _migrate_deltas(conn: sqlite3.Connection) -> None:
    existing = {r["name"] for r in conn.execute("PRAGMA table_info(deltas)").fetchall()}
    for col, decl in _NEW_DELTA_COLS:
        if col not in existing:
            conn.execute(f"ALTER TABLE deltas ADD COLUMN {col} {decl}")


_VALID_STATUSES = {"exploring", "approved", "finalised"}

_VALID_SCREEN_FIELDS    = {"name", "description", "usage", "selected_file", "rationale", "status", "hypothesis", "focus", "needs_review"}
_VALID_COMPONENT_FIELDS = {"name", "description", "usage", "selected_file", "rationale", "status", "hypothesis", "focus", "needs_review"}
_VALID_FLOW_FIELDS      = {"name", "description", "usage", "selected_file", "rationale", "status", "hypothesis", "focus", "needs_review"}

_VALID_VARIANT_FIELDS = {"label", "ui_description", "notes", "rationale", "flag", "flag_reason"}
_VALID_FLAGS = {None, "needs-revision"}


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


def _fetch_screen_variants(conn: sqlite3.Connection, screen_id: int) -> list[dict]:
    """Fetch all variants for a screen, ordered by created_at."""
    cursor = conn.execute(
        "SELECT * FROM screen_variants WHERE screen_id = ? ORDER BY created_at, id",
        (screen_id,),
    )
    return [_row_to_dict(r) for r in cursor.fetchall()]


def _fetch_component_variants(conn: sqlite3.Connection, component_id: int) -> list[dict]:
    """Fetch all variants for a component, ordered by created_at."""
    cursor = conn.execute(
        "SELECT * FROM component_variants WHERE component_id = ? ORDER BY created_at, id",
        (component_id,),
    )
    return [_row_to_dict(r) for r in cursor.fetchall()]


def _fetch_flow_variants(conn: sqlite3.Connection, flow_id: int) -> list[dict]:
    """Fetch all variants for a flow, ordered by created_at."""
    cursor = conn.execute(
        "SELECT * FROM flow_variants WHERE flow_id = ? ORDER BY created_at, id",
        (flow_id,),
    )
    return [_row_to_dict(r) for r in cursor.fetchall()]


def _fetch_screen_children(conn: sqlite3.Connection, screen_id: int) -> list[int]:
    """Return IDs of direct child screens."""
    cursor = conn.execute(
        "SELECT id FROM screens WHERE parent_id = ? ORDER BY created_at, id",
        (screen_id,),
    )
    return [row["id"] for row in cursor.fetchall()]


def _fetch_component_used_in(conn: sqlite3.Connection, component_id: int) -> list[dict]:
    """Return list of {id, name} dicts for screens that use this component."""
    cursor = conn.execute(
        """
        SELECT s.id, s.name
        FROM component_usage cu
        JOIN screens s ON s.id = cu.screen_id
        WHERE cu.component_id = ?
        ORDER BY s.name
        """,
        (component_id,),
    )
    return [_row_to_dict(r) for r in cursor.fetchall()]


def _fetch_screen_components(conn: sqlite3.Connection, screen_id: int) -> list[dict]:
    """Return list of {id, name} dicts for components linked to this screen."""
    cursor = conn.execute(
        """
        SELECT c.id, c.name
        FROM component_usage cu
        JOIN components c ON c.id = cu.component_id
        WHERE cu.screen_id = ?
        ORDER BY c.name
        """,
        (screen_id,),
    )
    return [_row_to_dict(r) for r in cursor.fetchall()]


def _fetch_flow_screens(conn: sqlite3.Connection, flow_id: int) -> list[dict]:
    """Return list of {id, name} dicts for screens linked to a flow."""
    cursor = conn.execute(
        """
        SELECT s.id, s.name, s.parent_id, s.selected_file, s.status
        FROM flow_screens fs
        JOIN screens s ON s.id = fs.screen_id
        WHERE fs.flow_id = ?
        ORDER BY s.name
        """,
        (flow_id,),
    )
    return [_row_to_dict(r) for r in cursor.fetchall()]


# ---------------------------------------------------------------------------
# Screen CRUD
# ---------------------------------------------------------------------------

def list_screens() -> list[dict]:
    """Return all screens, each with variants and children (list of child IDs)."""
    conn = get_db()
    cursor = conn.execute("SELECT * FROM screens ORDER BY created_at, id")
    rows = cursor.fetchall()

    screens = []
    for row in rows:
        screen = _row_to_dict(row)
        screen["variants"]   = _fetch_screen_variants(conn, screen["id"])
        screen["children"]   = _fetch_screen_children(conn, screen["id"])
        screen["components"] = _fetch_screen_components(conn, screen["id"])
        screens.append(screen)

    conn.close()
    return screens


def get_screen(screen_id: int) -> dict | None:
    """Return a single screen with variants and children, or None."""
    assert isinstance(screen_id, int), f"screen_id must be int: {screen_id!r}"
    assert screen_id > 0, f"screen_id must be positive: {screen_id}"

    conn = get_db()
    row = conn.execute("SELECT * FROM screens WHERE id = ?", (screen_id,)).fetchone()
    if row is None:
        conn.close()
        return None

    screen = _row_to_dict(row)
    screen["variants"]   = _fetch_screen_variants(conn, screen_id)
    screen["children"]   = _fetch_screen_children(conn, screen_id)
    screen["components"] = _fetch_screen_components(conn, screen_id)
    conn.close()
    return screen



def get_screen_by_name(name: str) -> dict | None:
    """Find a screen by exact name (case-insensitive)."""
    needle = name.strip().lower()
    for s in list_screens():
        if s["name"].lower() == needle:
            return s
    return None


def get_component_by_name(name: str) -> dict | None:
    """Find a component by exact name (case-insensitive)."""
    needle = name.strip().lower()
    for c in list_components():
        if c["name"].lower() == needle:
            return c
    return None


def get_flow_by_name(name: str) -> dict | None:
    """Find a flow by exact name (case-insensitive)."""
    needle = name.strip().lower()
    for f in list_flows():
        if f["name"].lower() == needle:
            return f
    return None


def create_screen(
    name: str,
    description: str | None = None,
    usage: str | None = None,
) -> dict:
    """Insert a new screen and return it as a dict."""
    assert name and name.strip(), "name must not be empty"

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO screens (name, description, usage) VALUES (?, ?, ?)",
        (name.strip(), description, usage),
    )
    screen_id = cursor.lastrowid
    assert screen_id is not None, "INSERT into screens returned no rowid"

    conn.commit()
    result = get_screen(screen_id)
    conn.close()

    assert result is not None, f"Newly created screen {screen_id} not found"
    return result


def update_screen(screen_id: int, **fields) -> dict | None:
    """Update allowed fields on a screen. Returns updated screen or None if not found."""
    assert isinstance(screen_id, int), f"screen_id must be int: {screen_id!r}"
    assert screen_id > 0, f"screen_id must be positive: {screen_id}"
    assert fields, "At least one field required for update"

    unknown = set(fields) - _VALID_SCREEN_FIELDS
    assert not unknown, f"Unknown screen fields: {unknown}"

    if "status" in fields:
        assert fields["status"] in _VALID_STATUSES, f"Invalid status: {fields['status']!r}"

    assignments = ", ".join(f"{col} = ?" for col in fields)
    values = list(fields.values())
    values.append(screen_id)

    conn = get_db()
    conn.execute(
        f"UPDATE screens SET {assignments}, updated_at = datetime('now') WHERE id = ?",
        values,
    )
    conn.commit()
    result = get_screen(screen_id)
    conn.close()
    return result


def delete_screen(screen_id: int) -> bool:
    """Delete a screen and cascade variants. Returns True if a row was deleted."""
    assert isinstance(screen_id, int), f"screen_id must be int: {screen_id!r}"
    assert screen_id > 0, f"screen_id must be positive: {screen_id}"

    conn = get_db()
    cursor = conn.execute("DELETE FROM screens WHERE id = ?", (screen_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def set_screen_parent(screen_id: int, parent_id: int | None) -> dict | None:
    """Set or clear the parent of a screen. Returns updated screen or None if not found."""
    assert isinstance(screen_id, int), f"screen_id must be int: {screen_id!r}"
    assert screen_id > 0, f"screen_id must be positive: {screen_id}"
    assert parent_id is None or isinstance(parent_id, int), (
        f"parent_id must be int or None: {parent_id!r}"
    )
    assert parent_id != screen_id, "A screen cannot be its own parent"

    conn = get_db()
    exists = conn.execute("SELECT 1 FROM screens WHERE id = ?", (screen_id,)).fetchone()
    if exists is None:
        conn.close()
        return None

    conn.execute(
        "UPDATE screens SET parent_id = ?, updated_at = datetime('now') WHERE id = ?",
        (parent_id, screen_id),
    )
    conn.commit()
    result = get_screen(screen_id)
    conn.close()
    return result


def create_screen_variant(
    screen_id: int,
    file: str,
    label: str | None = None,
    ui_description: str | None = None,
    notes: str | None = None,
    rationale: str | None = None,
) -> dict:
    """Insert a new variant for a screen. Returns the variant as a dict."""
    assert isinstance(screen_id, int), f"screen_id must be int: {screen_id!r}"
    assert screen_id > 0, f"screen_id must be positive: {screen_id}"
    assert file and file.strip(), "file must not be empty"

    conn = get_db()
    exists = conn.execute("SELECT 1 FROM screens WHERE id = ?", (screen_id,)).fetchone()
    if exists is None:
        conn.close()
        raise ValueError(f"Screen {screen_id} not found")

    cursor = conn.execute(
        """
        INSERT INTO screen_variants (screen_id, file, label, ui_description, notes, rationale)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (screen_id, file.strip(), label, ui_description, notes, rationale),
    )
    variant_id = cursor.lastrowid
    assert variant_id is not None, "INSERT into screen_variants returned no rowid"

    conn.commit()
    row = conn.execute(
        "SELECT * FROM screen_variants WHERE id = ?", (variant_id,)
    ).fetchone()
    conn.close()

    assert row is not None, f"Newly created screen_variant {variant_id} not found"
    return _row_to_dict(row)


def select_screen_variant(variant_id: int) -> dict | None:
    """
    Set a screen variant's file as the parent screen's selected_file.
    Returns the updated parent screen dict, or None if variant not found.
    """
    assert isinstance(variant_id, int), f"variant_id must be int: {variant_id!r}"
    assert variant_id > 0, f"variant_id must be positive: {variant_id}"

    conn = get_db()
    row = conn.execute(
        "SELECT screen_id, file FROM screen_variants WHERE id = ?", (variant_id,)
    ).fetchone()

    if row is None:
        conn.close()
        return None

    screen_id = row["screen_id"]
    file      = row["file"]

    assert screen_id is not None, "screen_variant has null screen_id"
    assert file,                  "screen_variant has empty file"

    conn.execute(
        "UPDATE screens SET selected_file = ?, updated_at = datetime('now') WHERE id = ?",
        (file, screen_id),
    )
    conn.commit()
    result = get_screen(screen_id)
    conn.close()
    return result


def delete_screen_variant(variant_id: int) -> bool:
    """Delete a screen variant by id. Returns True if a row was deleted."""
    assert isinstance(variant_id, int), f"variant_id must be int: {variant_id!r}"
    assert variant_id > 0, f"variant_id must be positive: {variant_id}"

    conn = get_db()
    cursor = conn.execute("DELETE FROM screen_variants WHERE id = ?", (variant_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def move_screen_variant(variant_id: int, to_screen_id: int) -> dict | None:
    """Move a screen variant to a different screen. Returns updated variant or None if not found."""
    assert isinstance(variant_id, int) and variant_id > 0
    assert isinstance(to_screen_id, int) and to_screen_id > 0

    conn = get_db()
    exists = conn.execute("SELECT 1 FROM screens WHERE id = ?", (to_screen_id,)).fetchone()
    if exists is None:
        conn.close()
        raise ValueError(f"Screen {to_screen_id} not found")

    cursor = conn.execute(
        "UPDATE screen_variants SET screen_id = ? WHERE id = ?",
        (to_screen_id, variant_id),
    )
    if cursor.rowcount == 0:
        conn.close()
        return None
    conn.commit()
    row = conn.execute("SELECT * FROM screen_variants WHERE id = ?", (variant_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def update_variant_screenshot(variant_id: int, screenshot_path: str) -> bool:
    """Update screenshot on any variant type. Tries all three tables."""
    conn = get_db()
    for table in ("screen_variants", "component_variants", "flow_variants"):
        cursor = conn.execute(
            f"UPDATE {table} SET screenshot = ? WHERE id = ?",
            (screenshot_path, variant_id),
        )
        if cursor.rowcount > 0:
            conn.commit()
            conn.close()
            return True
    conn.close()
    return False


def update_screen_variant_screenshot(variant_id: int, screenshot_path: str) -> bool:
    conn = get_db()
    cursor = conn.execute(
        "UPDATE screen_variants SET screenshot = ? WHERE id = ?",
        (screenshot_path, variant_id),
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def update_screen_variant(variant_id: int, **fields) -> dict | None:
    """Update allowed fields on a screen variant. Returns updated variant or None if not found."""
    assert isinstance(variant_id, int) and variant_id > 0
    assert fields, "at least one field required"
    unknown = set(fields) - _VALID_VARIANT_FIELDS
    assert not unknown, f"unknown variant fields: {unknown}"
    if "flag" in fields:
        assert fields["flag"] in _VALID_FLAGS, f"invalid flag: {fields['flag']!r}"

    assignments = ", ".join(f"{c} = ?" for c in fields)
    values = list(fields.values()) + [variant_id]

    conn = get_db()
    cursor = conn.execute(
        f"UPDATE screen_variants SET {assignments} WHERE id = ?", values,
    )
    if cursor.rowcount == 0:
        conn.close()
        return None
    conn.commit()
    row = conn.execute("SELECT * FROM screen_variants WHERE id = ?", (variant_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def update_component_variant(variant_id: int, **fields) -> dict | None:
    """Update allowed fields on a component variant. Returns updated variant or None if not found."""
    assert isinstance(variant_id, int) and variant_id > 0
    assert fields, "at least one field required"
    unknown = set(fields) - _VALID_VARIANT_FIELDS
    assert not unknown, f"unknown variant fields: {unknown}"
    if "flag" in fields:
        assert fields["flag"] in _VALID_FLAGS, f"invalid flag: {fields['flag']!r}"

    assignments = ", ".join(f"{c} = ?" for c in fields)
    values = list(fields.values()) + [variant_id]

    conn = get_db()
    cursor = conn.execute(
        f"UPDATE component_variants SET {assignments} WHERE id = ?", values,
    )
    if cursor.rowcount == 0:
        conn.close()
        return None
    conn.commit()
    row = conn.execute("SELECT * FROM component_variants WHERE id = ?", (variant_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def update_flow_variant(variant_id: int, **fields) -> dict | None:
    """Update allowed fields on a flow variant. Returns updated variant or None if not found."""
    assert isinstance(variant_id, int) and variant_id > 0
    assert fields, "at least one field required"
    unknown = set(fields) - _VALID_VARIANT_FIELDS
    assert not unknown, f"unknown variant fields: {unknown}"
    if "flag" in fields:
        assert fields["flag"] in _VALID_FLAGS, f"invalid flag: {fields['flag']!r}"

    assignments = ", ".join(f"{c} = ?" for c in fields)
    values = list(fields.values()) + [variant_id]

    conn = get_db()
    cursor = conn.execute(
        f"UPDATE flow_variants SET {assignments} WHERE id = ?", values,
    )
    if cursor.rowcount == 0:
        conn.close()
        return None
    conn.commit()
    row = conn.execute("SELECT * FROM flow_variants WHERE id = ?", (variant_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def get_screen_tree() -> list[dict]:
    """
    Return root screens (parent_id IS NULL), each with nested 'children' list recursively.
    Builds the tree in Python using an adjacency list — no recursive SQL.
    """
    conn = get_db()
    cursor = conn.execute("SELECT * FROM screens ORDER BY created_at, id")
    all_rows = [_row_to_dict(r) for r in cursor.fetchall()]
    conn.close()

    # Build adjacency list: parent_id → [child_row, ...]
    children_by_parent: dict[int | None, list[dict]] = {}
    for screen in all_rows:
        parent_id = screen["parent_id"]
        children_by_parent.setdefault(parent_id, []).append(screen)

    def _attach_children(node: dict) -> dict:
        """Recursively attach children to a node dict."""
        node_id = node["id"]
        child_rows = children_by_parent.get(node_id, [])
        node["children"] = [_attach_children(c) for c in child_rows]
        return node

    roots = children_by_parent.get(None, [])
    return [_attach_children(r) for r in roots]


# ---------------------------------------------------------------------------
# Component CRUD
# ---------------------------------------------------------------------------

def list_components() -> list[dict]:
    """Return all components, each with variants and used_in (screen id+name pairs)."""
    conn = get_db()
    cursor = conn.execute("SELECT * FROM components ORDER BY created_at, id")
    rows = cursor.fetchall()

    components = []
    for row in rows:
        component = _row_to_dict(row)
        component["variants"] = _fetch_component_variants(conn, component["id"])
        component["used_in"]  = _fetch_component_used_in(conn, component["id"])
        components.append(component)

    conn.close()
    return components


def get_component(component_id: int) -> dict | None:
    """Return a single component with variants and used_in, or None."""
    assert isinstance(component_id, int), f"component_id must be int: {component_id!r}"
    assert component_id > 0, f"component_id must be positive: {component_id}"

    conn = get_db()
    row = conn.execute(
        "SELECT * FROM components WHERE id = ?", (component_id,)
    ).fetchone()
    if row is None:
        conn.close()
        return None

    component = _row_to_dict(row)
    component["variants"] = _fetch_component_variants(conn, component_id)
    component["used_in"]  = _fetch_component_used_in(conn, component_id)
    conn.close()
    return component


def create_component(
    name: str,
    description: str | None = None,
    usage: str | None = None,
) -> dict:
    """Insert a new component and return it as a dict."""
    assert name and name.strip(), "name must not be empty"

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO components (name, description, usage) VALUES (?, ?, ?)",
        (name.strip(), description, usage),
    )
    component_id = cursor.lastrowid
    assert component_id is not None, "INSERT into components returned no rowid"

    conn.commit()
    result = get_component(component_id)
    conn.close()

    assert result is not None, f"Newly created component {component_id} not found"
    return result


def update_component(component_id: int, **fields) -> dict | None:
    """Update allowed fields on a component. Returns updated component or None if not found."""
    assert isinstance(component_id, int), f"component_id must be int: {component_id!r}"
    assert component_id > 0, f"component_id must be positive: {component_id}"
    assert fields, "At least one field required for update"

    unknown = set(fields) - _VALID_COMPONENT_FIELDS
    assert not unknown, f"Unknown component fields: {unknown}"

    if "status" in fields:
        assert fields["status"] in _VALID_STATUSES, f"Invalid status: {fields['status']!r}"

    assignments = ", ".join(f"{col} = ?" for col in fields)
    values = list(fields.values())
    values.append(component_id)

    conn = get_db()
    conn.execute(
        f"UPDATE components SET {assignments}, updated_at = datetime('now') WHERE id = ?",
        values,
    )
    conn.commit()
    result = get_component(component_id)
    conn.close()
    return result


def delete_component(component_id: int) -> bool:
    """Delete a component and cascade variants. Returns True if a row was deleted."""
    assert isinstance(component_id, int), f"component_id must be int: {component_id!r}"
    assert component_id > 0, f"component_id must be positive: {component_id}"

    conn = get_db()
    cursor = conn.execute("DELETE FROM components WHERE id = ?", (component_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def create_component_variant(
    component_id: int,
    file: str,
    label: str | None = None,
    ui_description: str | None = None,
    notes: str | None = None,
    rationale: str | None = None,
) -> dict:
    """Insert a new variant for a component. Returns the variant as a dict."""
    assert isinstance(component_id, int), f"component_id must be int: {component_id!r}"
    assert component_id > 0, f"component_id must be positive: {component_id}"
    assert file and file.strip(), "file must not be empty"

    conn = get_db()
    exists = conn.execute(
        "SELECT 1 FROM components WHERE id = ?", (component_id,)
    ).fetchone()
    if exists is None:
        conn.close()
        raise ValueError(f"Component {component_id} not found")

    cursor = conn.execute(
        """
        INSERT INTO component_variants (component_id, file, label, ui_description, notes, rationale)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (component_id, file.strip(), label, ui_description, notes, rationale),
    )
    variant_id = cursor.lastrowid
    assert variant_id is not None, "INSERT into component_variants returned no rowid"

    conn.commit()
    row = conn.execute(
        "SELECT * FROM component_variants WHERE id = ?", (variant_id,)
    ).fetchone()
    conn.close()

    assert row is not None, f"Newly created component_variant {variant_id} not found"
    return _row_to_dict(row)


def select_component_variant(variant_id: int) -> dict | None:
    """
    Set a component variant's file as the parent component's selected_file.
    Returns the updated parent component dict, or None if variant not found.
    """
    assert isinstance(variant_id, int), f"variant_id must be int: {variant_id!r}"
    assert variant_id > 0, f"variant_id must be positive: {variant_id}"

    conn = get_db()
    row = conn.execute(
        "SELECT component_id, file FROM component_variants WHERE id = ?", (variant_id,)
    ).fetchone()

    if row is None:
        conn.close()
        return None

    component_id = row["component_id"]
    file         = row["file"]

    assert component_id is not None, "component_variant has null component_id"
    assert file,                     "component_variant has empty file"

    conn.execute(
        "UPDATE components SET selected_file = ?, updated_at = datetime('now') WHERE id = ?",
        (file, component_id),
    )
    conn.commit()
    result = get_component(component_id)
    conn.close()
    return result


def delete_component_variant(variant_id: int) -> bool:
    """Delete a component variant by id. Returns True if a row was deleted."""
    assert isinstance(variant_id, int), f"variant_id must be int: {variant_id!r}"
    assert variant_id > 0, f"variant_id must be positive: {variant_id}"

    conn = get_db()
    cursor = conn.execute("DELETE FROM component_variants WHERE id = ?", (variant_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def update_component_variant_screenshot(variant_id: int, screenshot_path: str) -> bool:
    conn = get_db()
    cursor = conn.execute(
        "UPDATE component_variants SET screenshot = ? WHERE id = ?",
        (screenshot_path, variant_id),
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def link_component_screen(component_id: int, screen_id: int) -> bool:
    """Link a component to a screen. INSERT OR IGNORE — always returns True."""
    assert isinstance(component_id, int), f"component_id must be int: {component_id!r}"
    assert component_id > 0, f"component_id must be positive: {component_id}"
    assert isinstance(screen_id, int), f"screen_id must be int: {screen_id!r}"
    assert screen_id > 0, f"screen_id must be positive: {screen_id}"

    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO component_usage (component_id, screen_id) VALUES (?, ?)",
        (component_id, screen_id),
    )
    conn.commit()
    conn.close()
    return True


def unlink_component_screen(component_id: int, screen_id: int) -> bool:
    """Unlink a component from a screen. Returns True if a row was deleted."""
    assert isinstance(component_id, int), f"component_id must be int: {component_id!r}"
    assert component_id > 0, f"component_id must be positive: {component_id}"
    assert isinstance(screen_id, int), f"screen_id must be int: {screen_id!r}"
    assert screen_id > 0, f"screen_id must be positive: {screen_id}"

    conn = get_db()
    cursor = conn.execute(
        "DELETE FROM component_usage WHERE component_id = ? AND screen_id = ?",
        (component_id, screen_id),
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ---------------------------------------------------------------------------
# Flow CRUD
# ---------------------------------------------------------------------------

def list_flows() -> list[dict]:
    """Return all flows, each with variants and screens (linked screen id+name pairs)."""
    conn = get_db()
    cursor = conn.execute("SELECT * FROM flows ORDER BY created_at, id")
    rows = cursor.fetchall()

    flows = []
    for row in rows:
        flow = _row_to_dict(row)
        flow["variants"] = _fetch_flow_variants(conn, flow["id"])
        flow["screens"]  = _fetch_flow_screens(conn, flow["id"])
        flows.append(flow)

    conn.close()
    return flows


def get_flow(flow_id: int) -> dict | None:
    """Return a single flow with variants and linked screens, or None."""
    assert isinstance(flow_id, int), f"flow_id must be int: {flow_id!r}"
    assert flow_id > 0, f"flow_id must be positive: {flow_id}"

    conn = get_db()
    row = conn.execute("SELECT * FROM flows WHERE id = ?", (flow_id,)).fetchone()
    if row is None:
        conn.close()
        return None

    flow = _row_to_dict(row)
    flow["variants"] = _fetch_flow_variants(conn, flow_id)
    flow["screens"]  = _fetch_flow_screens(conn, flow_id)
    conn.close()
    return flow


def create_flow(
    name: str,
    description: str | None = None,
    usage: str | None = None,
) -> dict:
    """Insert a new flow and return it as a dict."""
    assert name and name.strip(), "name must not be empty"

    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO flows (name, description, usage) VALUES (?, ?, ?)",
        (name.strip(), description, usage),
    )
    flow_id = cursor.lastrowid
    assert flow_id is not None, "INSERT into flows returned no rowid"

    conn.commit()
    result = get_flow(flow_id)
    conn.close()

    assert result is not None, f"Newly created flow {flow_id} not found"
    return result


def update_flow(flow_id: int, **fields) -> dict | None:
    """Update allowed fields on a flow. Returns updated flow or None if not found."""
    assert isinstance(flow_id, int), f"flow_id must be int: {flow_id!r}"
    assert flow_id > 0, f"flow_id must be positive: {flow_id}"
    assert fields, "At least one field required for update"

    unknown = set(fields) - _VALID_FLOW_FIELDS
    assert not unknown, f"Unknown flow fields: {unknown}"

    if "status" in fields:
        assert fields["status"] in _VALID_STATUSES, f"Invalid status: {fields['status']!r}"

    assignments = ", ".join(f"{col} = ?" for col in fields)
    values = list(fields.values())
    values.append(flow_id)

    conn = get_db()
    conn.execute(
        f"UPDATE flows SET {assignments}, updated_at = datetime('now') WHERE id = ?",
        values,
    )
    conn.commit()
    result = get_flow(flow_id)
    conn.close()
    return result


def delete_flow(flow_id: int) -> bool:
    """Delete a flow and cascade variants. Returns True if a row was deleted."""
    assert isinstance(flow_id, int), f"flow_id must be int: {flow_id!r}"
    assert flow_id > 0, f"flow_id must be positive: {flow_id}"

    conn = get_db()
    cursor = conn.execute("DELETE FROM flows WHERE id = ?", (flow_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def create_flow_variant(
    flow_id: int,
    file: str,
    label: str | None = None,
    ui_description: str | None = None,
    notes: str | None = None,
    rationale: str | None = None,
) -> dict:
    """Insert a new variant for a flow. Returns the variant as a dict."""
    assert isinstance(flow_id, int), f"flow_id must be int: {flow_id!r}"
    assert flow_id > 0, f"flow_id must be positive: {flow_id}"
    assert file and file.strip(), "file must not be empty"

    conn = get_db()
    exists = conn.execute("SELECT 1 FROM flows WHERE id = ?", (flow_id,)).fetchone()
    if exists is None:
        conn.close()
        raise ValueError(f"Flow {flow_id} not found")

    cursor = conn.execute(
        """
        INSERT INTO flow_variants (flow_id, file, label, ui_description, notes, rationale)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (flow_id, file.strip(), label, ui_description, notes, rationale),
    )
    variant_id = cursor.lastrowid
    assert variant_id is not None, "INSERT into flow_variants returned no rowid"

    conn.commit()
    row = conn.execute(
        "SELECT * FROM flow_variants WHERE id = ?", (variant_id,)
    ).fetchone()
    conn.close()

    assert row is not None, f"Newly created flow_variant {variant_id} not found"
    return _row_to_dict(row)


def select_flow_variant(variant_id: int) -> dict | None:
    """
    Set a flow variant's file as the parent flow's selected_file.
    Returns the updated parent flow dict, or None if variant not found.
    """
    assert isinstance(variant_id, int), f"variant_id must be int: {variant_id!r}"
    assert variant_id > 0, f"variant_id must be positive: {variant_id}"

    conn = get_db()
    row = conn.execute(
        "SELECT flow_id, file FROM flow_variants WHERE id = ?", (variant_id,)
    ).fetchone()

    if row is None:
        conn.close()
        return None

    flow_id = row["flow_id"]
    file    = row["file"]

    assert flow_id is not None, "flow_variant has null flow_id"
    assert file,                "flow_variant has empty file"

    conn.execute(
        "UPDATE flows SET selected_file = ?, updated_at = datetime('now') WHERE id = ?",
        (file, flow_id),
    )
    conn.commit()
    result = get_flow(flow_id)
    conn.close()
    return result


def delete_flow_variant(variant_id: int) -> bool:
    """Delete a flow variant by id. Returns True if a row was deleted."""
    assert isinstance(variant_id, int), f"variant_id must be int: {variant_id!r}"
    assert variant_id > 0, f"variant_id must be positive: {variant_id}"

    conn = get_db()
    cursor = conn.execute("DELETE FROM flow_variants WHERE id = ?", (variant_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def update_flow_variant_screenshot(variant_id: int, screenshot_path: str) -> bool:
    conn = get_db()
    cursor = conn.execute(
        "UPDATE flow_variants SET screenshot = ? WHERE id = ?",
        (screenshot_path, variant_id),
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def link_flow_screen(flow_id: int, screen_id: int) -> bool:
    """Link a screen to a flow. INSERT OR IGNORE — always returns True."""
    assert isinstance(flow_id, int), f"flow_id must be int: {flow_id!r}"
    assert flow_id > 0, f"flow_id must be positive: {flow_id}"
    assert isinstance(screen_id, int), f"screen_id must be int: {screen_id!r}"
    assert screen_id > 0, f"screen_id must be positive: {screen_id}"

    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO flow_screens (flow_id, screen_id) VALUES (?, ?)",
        (flow_id, screen_id),
    )
    conn.commit()
    conn.close()
    return True


def unlink_flow_screen(flow_id: int, screen_id: int) -> bool:
    """Unlink a screen from a flow. Returns True if a row was deleted."""
    assert isinstance(flow_id, int), f"flow_id must be int: {flow_id!r}"
    assert flow_id > 0, f"flow_id must be positive: {flow_id}"
    assert isinstance(screen_id, int), f"screen_id must be int: {screen_id!r}"
    assert screen_id > 0, f"screen_id must be positive: {screen_id}"

    conn = get_db()
    cursor = conn.execute(
        "DELETE FROM flow_screens WHERE flow_id = ? AND screen_id = ?",
        (flow_id, screen_id),
    )
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ---------------------------------------------------------------------------
# Delta CRUD
# ---------------------------------------------------------------------------

_VALID_ENTITY_TYPES = {"screen", "component", "flow"}
_VALID_DELTA_TYPES  = {"layout", "copy", "color", "spacing", "interaction", "other"}


_VALID_OUTCOME_TYPES = {"accepted", "rejected", "revised"}


def add_delta(
    entity_type: str,
    entity_id: int,
    type: str,
    target: str | None = None,
    from_val: str | None = None,
    to_val: str | None = None,
    reason: str | None = None,
    variant_id: int | None = None,
    outcome_type: str | None = None,
) -> dict:
    """Insert a new delta and return it as a dict."""
    assert entity_type in _VALID_ENTITY_TYPES, f"Invalid entity_type: {entity_type!r}"
    assert isinstance(entity_id, int), f"entity_id must be int: {entity_id!r}"
    assert entity_id > 0, f"entity_id must be positive: {entity_id}"
    assert type in _VALID_DELTA_TYPES, f"Invalid delta type: {type!r}"
    assert variant_id is None or (isinstance(variant_id, int) and variant_id > 0), \
        f"variant_id must be positive int or None: {variant_id!r}"
    assert outcome_type is None or outcome_type in _VALID_OUTCOME_TYPES, \
        f"outcome_type must be one of {sorted(_VALID_OUTCOME_TYPES)} or None: {outcome_type!r}"

    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO deltas (entity_type, entity_id, variant_id, type, target, from_val, to_val, reason, outcome_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (entity_type, entity_id, variant_id, type, target, from_val, to_val, reason, outcome_type),
    )
    delta_id = cursor.lastrowid
    assert delta_id is not None, "INSERT into deltas returned no rowid"

    conn.commit()
    row = conn.execute("SELECT * FROM deltas WHERE id = ?", (delta_id,)).fetchone()
    conn.close()

    assert row is not None, f"Newly created delta {delta_id} not found"
    return _row_to_dict(row)


def list_deltas(entity_type: str, entity_id: int, limit: int | None = None) -> list[dict]:
    """Return deltas for an entity, newest first. Optionally limit count."""
    assert entity_type in _VALID_ENTITY_TYPES, f"Invalid entity_type: {entity_type!r}"
    assert isinstance(entity_id, int), f"entity_id must be int: {entity_id!r}"
    assert entity_id > 0, f"entity_id must be positive: {entity_id}"

    sql = (
        "SELECT * FROM deltas WHERE entity_type = ? AND entity_id = ? "
        "ORDER BY created_at DESC, id DESC"
    )
    conn = get_db()
    if limit is not None:
        assert isinstance(limit, int) and limit > 0, f"limit must be positive int: {limit!r}"
        rows = conn.execute(sql + " LIMIT ?", (entity_type, entity_id, limit)).fetchall()
    else:
        rows = conn.execute(sql, (entity_type, entity_id)).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def list_recent_outcome_deltas(
    outcome_type: str,
    days: int,
    limit: int,
) -> list[dict]:
    """Return deltas with the given outcome_type created within the last N days, newest first."""
    assert outcome_type in _VALID_OUTCOME_TYPES, f"Invalid outcome_type: {outcome_type!r}"
    assert isinstance(days, int) and days > 0, f"days must be positive int: {days!r}"
    assert isinstance(limit, int) and limit > 0, f"limit must be positive int: {limit!r}"

    conn = get_db()
    rows = conn.execute(
        """
        SELECT * FROM deltas
        WHERE outcome_type = ?
          AND created_at >= datetime('now', ? || ' days')
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (outcome_type, f"-{days}", limit),
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def update_delta_outcome(delta_id: int, outcome: str) -> dict | None:
    """Set the outcome on a delta. Returns updated delta or None if not found."""
    assert isinstance(delta_id, int), f"delta_id must be int: {delta_id!r}"
    assert delta_id > 0, f"delta_id must be positive: {delta_id}"
    assert isinstance(outcome, str), f"outcome must be str: {outcome!r}"

    conn = get_db()
    cursor = conn.execute(
        "UPDATE deltas SET outcome = ? WHERE id = ?",
        (outcome, delta_id),
    )
    if cursor.rowcount == 0:
        conn.close()
        return None
    conn.commit()
    row = conn.execute("SELECT * FROM deltas WHERE id = ?", (delta_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


# ---------------------------------------------------------------------------
# Seed from design directory
# ---------------------------------------------------------------------------

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
    Creates one screen per group and one screen_variant per file.
    Returns count of screens created.
    """
    if not DESIGN_DIR.is_dir():
        return 0

    html_files = sorted(
        p.name for p in DESIGN_DIR.iterdir() if p.name.lower().endswith(".html")
    )

    if not html_files:
        return 0

    # Map base_stem → [filename, ...]
    groups: dict[str, list[str]] = {}
    for filename in html_files:
        raw_stem  = Path(filename).stem
        base_stem = _VARIANT_SUFFIX_PATTERN.sub("", raw_stem)
        groups.setdefault(base_stem, []).append(filename)

    conn = get_db()
    screens_created = 0

    for base_stem, files in groups.items():
        name   = _stem_to_name(base_stem)
        cursor = conn.execute(
            "INSERT INTO screens (name) VALUES (?)",
            (name,),
        )
        screen_id = cursor.lastrowid
        assert screen_id is not None, "INSERT into screens returned no rowid"

        for index, filename in enumerate(files):
            label = f"v{index + 1}"
            conn.execute(
                "INSERT INTO screen_variants (screen_id, file, label) VALUES (?, ?, ?)",
                (screen_id, filename, label),
            )

        # First file becomes selected_file
        conn.execute(
            "UPDATE screens SET selected_file = ? WHERE id = ?",
            (files[0], screen_id),
        )
        screens_created += 1

    conn.commit()
    conn.close()
    return screens_created


# ---------------------------------------------------------------------------
# System doc sync
# ---------------------------------------------------------------------------

_DECISIONS_START = "<!-- DECISIONS-START -->"
_DECISIONS_END   = "<!-- DECISIONS-END -->"
_PENDING_START   = "<!-- PENDING-START -->"
_PENDING_END     = "<!-- PENDING-END -->"


def sync_system() -> str:
    """
    Write decisions table and pending table into system.md marker sections.
    Returns the final file content.
    """
    assert SYSTEM_MD_PATH.exists(), (
        f"system.md not found at {str(SYSTEM_MD_PATH)!r} — run init first"
    )

    conn = get_db()

    screen_rows = [
        _row_to_dict(r) for r in conn.execute(
            """
            SELECT id, name, status, rationale, selected_file
            FROM screens
            WHERE status IN ('approved', 'finalised')
            ORDER BY name
            """
        ).fetchall()
    ]

    component_rows = [
        _row_to_dict(r) for r in conn.execute(
            """
            SELECT id, name, status, rationale, selected_file
            FROM components
            WHERE status IN ('approved', 'finalised')
            ORDER BY name
            """
        ).fetchall()
    ]

    flow_rows = [
        _row_to_dict(r) for r in conn.execute(
            """
            SELECT id, name, status, rationale, selected_file
            FROM flows
            WHERE status IN ('approved', 'finalised')
            ORDER BY name
            """
        ).fetchall()
    ]

    # Query pending (exploring) items with variant counts.
    pending_screen_rows = [
        _row_to_dict(r) for r in conn.execute(
            """
            SELECT s.id, s.name, s.hypothesis,
                   COUNT(sv.id) AS variant_count
            FROM screens s
            LEFT JOIN screen_variants sv ON sv.screen_id = s.id
            WHERE s.status = 'exploring'
            GROUP BY s.id
            ORDER BY s.name
            """
        ).fetchall()
    ]

    pending_component_rows = [
        _row_to_dict(r) for r in conn.execute(
            """
            SELECT c.id, c.name, c.hypothesis,
                   COUNT(cv.id) AS variant_count
            FROM components c
            LEFT JOIN component_variants cv ON cv.component_id = c.id
            WHERE c.status = 'exploring'
            GROUP BY c.id
            ORDER BY c.name
            """
        ).fetchall()
    ]

    pending_flow_rows = [
        _row_to_dict(r) for r in conn.execute(
            """
            SELECT f.id, f.name, f.hypothesis,
                   COUNT(fv.id) AS variant_count
            FROM flows f
            LEFT JOIN flow_variants fv ON fv.flow_id = f.id
            WHERE f.status = 'exploring'
            GROUP BY f.id
            ORDER BY f.name
            """
        ).fetchall()
    ]

    conn.close()

    # Build decisions table.
    decided_items: list[dict] = []
    for row in screen_rows:
        row["type"] = "screen"
        decided_items.append(row)
    for row in component_rows:
        row["type"] = "component"
        decided_items.append(row)
    for row in flow_rows:
        row["type"] = "flow"
        decided_items.append(row)

    decided_items.sort(key=lambda r: (r["type"], r["name"]))

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

    working_content = (
        content[:start_index]
        + table_block
        + content[end_index:]
    )

    # Update PENDING section if markers exist — skip silently if absent.
    if _PENDING_START in working_content and _PENDING_END in working_content:
        pending_items: list[dict] = []
        for row in pending_screen_rows:
            row["type"] = "screen"
            pending_items.append(row)
        for row in pending_component_rows:
            row["type"] = "component"
            pending_items.append(row)
        for row in pending_flow_rows:
            row["type"] = "flow"
            pending_items.append(row)

        pending_lines: list[str] = []
        pending_lines.append("")
        pending_lines.append("| # | Type | Name | Variants | Hypothesis |")
        pending_lines.append("|---|------|------|----------|------------|")

        for item in pending_items:
            hyp = (item.get("hypothesis") or "").replace("|", "\\|")
            pending_lines.append(
                f"| {item['id']} | {item['type']} | {item['name']} "
                f"| {item['variant_count']} | {hyp} |"
            )

        pending_lines.append("")
        pending_block = "\n".join(pending_lines)

        ps_idx = working_content.index(_PENDING_START) + len(_PENDING_START)
        pe_idx = working_content.index(_PENDING_END)

        assert ps_idx < pe_idx, "PENDING-START appears after PENDING-END"

        working_content = (
            working_content[:ps_idx]
            + pending_block
            + working_content[pe_idx:]
        )

    with open(SYSTEM_MD_PATH, "w", encoding="utf-8") as f:
        f.write(working_content)

    return working_content
