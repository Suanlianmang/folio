# Folio — Project Brief

Terminal tool for design exploration tracking. Installed once at `~/.folio/`, used across any project. Two interfaces: Flask dashboard (human) and CLI (Claude). Shared SQLite DB, per-project data gitignored.

---

## Stack

- Python, `uv`, Flask, SQLite (stdlib)
- No other dependencies

---

## Repo structure

```
folio/
  install.sh        — one-time installer, writes to ~/.folio/
  server.py         — Flask dashboard (human-facing)
  cli.py            — CLI tool (Claude-facing)
  db.py             — shared schema + DB operations
  system.md         — design system document template (blank, project fills it)
  pyproject.toml    — uv project config
  .gitignore        — ignores .folio/
```

Installed layout (`~/.folio/`):
```
~/.folio/
  bin/folio         — shell wrapper
  lib/cli.py
  lib/db.py
  lib/server.py
  lib/system.md     — template
```

Per-project data (created by `folio init` in the project root):
```
{project}/
  .folio/
    design.db       — SQLite, project-specific
    screenshots/    — PNGs, project-specific
    system.md       — copied from template, edited per project
```

---

## DB schema

```sql
CREATE TABLE items (
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

CREATE TABLE variants (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id        INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  file           TEXT NOT NULL,
  label          TEXT,
  ui_description TEXT,
  screenshot     TEXT,   -- relative path to PNG in screenshots/
  notes          TEXT,
  created_at     TEXT DEFAULT (datetime('now'))
);
```

---

## Path resolution (db.py)

All paths resolved relative to CWD (the host project root), not folio's own directory.

- DB:          `{CWD}/.folio/design.db`
- Design files:`{CWD}/design/`
- Screenshots: `{CWD}/.folio/screenshots/`
- system.md:   `{CWD}/.folio/system.md`
- Template:    `~/.folio/lib/system.md`

---

## cli.py commands

```bash
folio init                                        # create DB, copy system.md template, seed from design/ if files exist
folio list                                        # dump all items + variants, formatted for Claude to read
folio show --id 2                                 # single item detail
folio add-item --type screen --name "..." --description "..." --usage "..."
folio add-variant --item-id 2 --file x.html --label "v1" --ui-description "..."
folio select --variant-id 4                       # set variant as selected_file on parent item
folio set-status --id 2 --status approved
folio set-rationale --id 2 --rationale "..."
folio sync-system                                 # write decisions from DB into system.md decisions table
folio serve                                       # start Flask dashboard (default port 5000)
folio serve --port 8080
```

Output of `list` and `show` should be clean plaintext — readable by Claude in one pass.

---

## server.py dashboard

Flask app. Run from host project root: `folio serve`

**Routes:**
- `GET /`                          — dashboard HTML (rendered inline, no templates dir)
- `GET /design/<file>`             — serves `../design/<file>` relative to tools/
- `POST /variants/<id>/screenshot` — saves uploaded PNG to screenshots/
- REST API (JSON):
  - `GET    /api/items`
  - `POST   /api/items`
  - `PUT    /api/items/<id>`
  - `DELETE /api/items/<id>`
  - `POST   /api/items/<id>/variants`
  - `PUT    /api/variants/<id>/select`
  - `DELETE /api/variants/<id>`

**Dashboard UI — left sidebar + main:**

Sidebar:
- Project name
- Filter: All / Screens / Layouts / Components / Flows

Main — one card per item:
```
┌──────────────────────────────────────────────────┐
│ Reading View     [screen]     [status ▾]         │
│ Full-screen thread view · Opens from list        │
│                                                  │
│ Variants (3)                                     │
│  ● threads.html      v1           [Preview]      │
│    layout-a.html     Option A  [Preview][Select] │
│    layout-b.html     Option B  [Preview][Select] │
│                                                  │
│ [+ Variant]   [Preview selected]                 │
└──────────────────────────────────────────────────┘
```

- ● dot = currently selected
- Status dropdown updates inline (no save button)
- Preview → opens `/design/<file>` in new tab
- Select → `PUT /api/variants/<id>/select`
- ✕ per variant → delete
- `+ Variant` → modal: file, label, ui_description, notes
- `+ New item` top-right → modal: type, name, description, usage, first file
- "System" tab → renders `tools/system.md` as HTML (use marked.js CDN or simple pre block)

**Design tokens (match host project):**
```css
--bg: #f7f6f4;
--surface: #ffffff;
--border: #e8e6e2;
--text-primary: #1a1a1a;
--text-secondary: #888580;
--text-muted: #c0bdb8;
font: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
```
Monochrome-first. No decorative color. Status chips use subtle tints only.

---

## Installation

```bash
git clone https://github.com/you/folio
cd folio
bash install.sh
```

## Per-project usage

```bash
# In any project root:
folio init              # creates .folio/design.db, .folio/system.md
folio list
folio add-item --type screen --name "Home"
folio serve             # opens dashboard at localhost:5000
folio sync-system
```

---

## Skill (/.claude/commands/design.md)

See skill file. Handles both first-time setup and regular session load.
