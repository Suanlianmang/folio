# Folio — Implementation TODO

## Phase 1: Data Layer

- [ ] **db.py** — Full data module
  - Path resolution: CWD-based constants (DB_PATH, DESIGN_DIR, SCREENSHOTS_DIR, SYSTEM_MD_PATH, TEMPLATE_PATH)
  - `configure(cwd)` fn to override paths (for testing)
  - `get_db()` → sqlite3.Connection with Row factory, FK pragma, WAL mode
  - `init_db()` → CREATE TABLE IF NOT EXISTS, mkdir screenshots, copy system.md template
  - `seed_from_design()` → scan design/, group files by stem, create items + variants
  - `list_items(type_filter=None)` → list[dict] with nested variants
  - `get_item(item_id)` → dict | None with nested variants
  - `create_item(type, name, description, usage)` → dict
  - `update_item(item_id, **fields)` → dict | None, sets updated_at
  - `delete_item(item_id)` → bool, CASCADE variants
  - `create_variant(item_id, file, label, ui_description, notes)` → dict
  - `delete_variant(variant_id)` → bool
  - `select_variant(variant_id)` → dict | None, sets parent selected_file
  - `update_variant_screenshot(variant_id, screenshot_path)` → bool
  - `sync_system()` → str, writes approved/finalised decisions to system.md between markers

- [ ] **system.md** — Template file shipped with repo
  - Markdown skeleton with `<!-- DECISIONS-START -->` and `<!-- DECISIONS-END -->` markers
  - Decisions table header between markers
  - Space above/below for user custom content

## Phase 2: CLI

- [ ] **cli.py** — All subcommands via argparse
  - Subparsers: init, list, show, add-item, add-variant, select, set-status, set-rationale, sync-system
  - Each subcommand calls db.py, prints plaintext result
  - `list` output: `=== ITEMS (N) ===` then `#id [type] Name (status)` with indented variants
  - `show` output: full detail including description, usage, rationale, variant ui_descriptions
  - Error handling: ValueError → print + exit 1, FileNotFoundError → "Run init first"
  - Entry point: `if __name__ == "__main__": main()`
  - Import db via sys.path adjustment (same directory)

## Phase 3: Dashboard

- [ ] **server.py — API routes** (JSON endpoints only)
  - Flask app setup, sys.path for db import
  - GET /api/items → db.list_items with optional type query param
  - POST /api/items → db.create_item from request.json
  - PUT /api/items/<id> → db.update_item from request.json
  - DELETE /api/items/<id> → db.delete_item
  - POST /api/items/<id>/variants → db.create_variant
  - PUT /api/variants/<id>/select → db.select_variant
  - DELETE /api/variants/<id> → db.delete_variant
  - GET /design/<file> → send_from_directory(DESIGN_DIR)
  - GET /screenshots/<file> → send_from_directory(SCREENSHOTS_DIR)
  - POST /variants/<id>/screenshot → save PNG, update variant
  - GET /system.md → raw text of tools/system.md
  - Error handling: 400 for ValueError, 404 for None, Flask default 500

- [ ] **server.py — DASHBOARD_HTML** (inline HTML/CSS/JS)
  - Single Python string constant, returned on GET /
  - CSS: design tokens as custom properties, sidebar 220px, cards, modal
  - Layout: sidebar (project name, filter tabs) + main (items list, add button)
  - JS state: { items: [], filter: null }
  - JS loadItems() → fetch /api/items, render cards
  - Item card: name, type badge, status dropdown (inline save), variants list
  - Variant row: dot for selected, file, label, Preview/Select/Delete buttons
  - Status dropdown: onchange → PUT /api/items/<id>
  - Modal: reusable shell, innerHTML swapped for new-item vs new-variant forms
  - System tab: fetch /system.md, render with marked.js CDN (<pre> fallback)
  - Project name: window.PROJECT_NAME injected via script tag
  - Port 5555, debug=True, startup banner

## Phase 4: Config Files

- [ ] **pyproject.toml** — Add flask to dependencies array
- [ ] **.gitignore** — Add design.db, screenshots/ lines

## Notes

- All paths relative to CWD (host project root), not folio dir
- CLI run as: `python3 tools/folio/cli.py <cmd>`
- Server run as: `python3 tools/folio/server.py`
- Only external dep: Flask. marked.js via CDN (browser only).
- main.py can be deleted — not part of folio
