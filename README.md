# Folio

A terminal tool for tracking design exploration alongside AI coding sessions. Keeps screens, components, and flows — each with multiple variants — moving through an explicit lifecycle: **exploring → approved → finalised**. Produces a `system.md` that gives Claude a ground-truth record of what was decided and why.

## Install

Requires Python 3. No external dependencies.

```sh
curl -fsSL https://raw.githubusercontent.com/Suanlianmang/folio/main/get.sh | bash
```

Restart your shell (or source your rc file) after install. Re-running the same command updates an existing install.

## Setup

Run once per project, from the project root:

```sh
folio init
```

Creates `.folio/` with the SQLite database, screenshots directory, and `system.md`. If `.folio/design/` contains HTML files, they are automatically seeded as screens. Folio warns if a top-level `design/` directory exists to prevent path confusion.

Add `.folio/` to your `.gitignore` — it contains local state, not source.

## Concepts

**Screens, components, and flows** are the three tracked entity types. Each holds multiple **variants** — HTML files representing different design attempts. One variant can be marked as selected (the current working version).

**Status** moves in one direction:
- `exploring` — variants exist, no decision made
- `approved` — a variant selected, rationale recorded
- `finalised` — locked; no further changes expected

**`system.md`** is a markdown file inside `.folio/` that Claude reads as context. Run `sync-system` after any approval to update it with the decisions table.

## Commands

### Init and sync

```sh
folio init                   # create .folio/, seed from design/ if present
folio sync-system            # write approved/finalised decisions into .folio/system.md
```

### Orientation

```sh
folio tree                   # project overview — screens, components, flows with status
folio tree --full            # full context: rationale, all variants, last 3 changes per item
```

`folio tree --full` is the single command to orient Claude at the start of a session. It replaces running `folio context` per item.

### Dashboard

```sh
folio serve                  # start dashboard at http://localhost:7842
folio serve --port 8080      # custom port
folio serve --stop           # stop the running server
folio serve --restart        # stop running server and restart (picks up folio update)
```

The dashboard now includes:
- **Flagged queue** — sidebar "Flagged" tab lists all variants marked `needs-revision` across all entity types
- **Compare mode** — items with 2+ variants show a "Compare ↗" button; opens side-by-side iframe view
- **Entity rationale** — shown on every card, clickable to edit inline
- **Screen components** — screen cards show which components are linked to them
- **Select-variant prompt** — selecting a variant via the dashboard prompts for rationale immediately

### Inter-screen navigation

Screen HTML files can link to other screens by ID using the `/screen/<id>` route served by the folio dashboard.

```html
<a href="/screen/2">← Inbox</a>
<button onclick="location.href='/screen/5'">Review →</button>
```

The server resolves the ID to whichever variant is currently selected. Requires `folio serve` to be running.

### Screens

```sh
folio screens list
folio screens add --name "Login"
folio screens add --name "Login" --file "login-v1.html"   # add with first variant
folio screens show --id 1
folio screens set-status --id 1 --status exploring|approved|finalised
folio screens set-rationale --id 1 --rationale "Chose this layout for scan order"
folio screens set-parent --id 2 --parent 1               # nest screen under another
folio screens select-variant --variant-id 3              # mark variant as selected
folio screens rename --id 1 --name "New Name"
folio screens delete --id 1
folio screens set-description --id 1 --description "..."
folio screens remove-variant --variant-id 3
folio screens move-variant --variant-id 3 --to-screen 2
```

### Components

Components are **late extractions** — register one only after the same UI pattern is confirmed in 2+ approved or finalised screens. `folio components add` enforces this and exits with a warning if fewer than 2 approved/finalised screens exist. Use `--force` to bypass.

`folio tree` flags components with fewer than 2 linked screens as `[speculative]`.

```sh
folio components list
folio components add --name "Button"           # blocked if <2 approved/finalised screens
folio components add --name "Button" --force   # bypass guard
folio components show --id 1
folio components set-status --id 1 --status approved
folio components set-rationale --id 1 --rationale "..."
folio components link --id 1 --screen 2        # record component used in screen
folio components unlink --id 1 --screen 2
folio components select-variant --variant-id 4
```

### Flows

```sh
folio flows list
folio flows add --name "Onboarding"
folio flows show --id 1
folio flows set-status --id 1 --status approved
folio flows set-rationale --id 1 --rationale "..."
folio flows link --id 1 --screen 2                       # add screen to flow
folio flows unlink --id 1 --screen 2
folio flows select-variant --variant-id 5
```

### Logging

One-line iteration notes attached to any entity. Feeds `folio suggest` automatically. Preferred over `screens change` for quick recording.

```sh
folio log --type screen --id 1 "removed thread strips — testing reading focus"
folio log --type screen --id 1 --variant-id 3 "scoped note on a specific variant"
folio log --type component --id 2 "tightened padding to 12px"
```

### Variants

Add a variant to any entity type:

```sh
folio add-variant --type screen --id 1 --file "login-v2.html" --label "v2"
folio add-variant --type component --id 1 --file "btn-rounded.html" --label "rounded"
folio add-variant --type flow --id 1 --file "onboarding-short.html"
```

Optional flags: `--label`, `--ui-description`, `--notes`, `--rationale`. Accepts absolute paths — folio copies the file into `.folio/design/` automatically.

### Screenshots

Captures the selected variant file using headless Chrome. Requires Google Chrome or Chromium installed.

```sh
folio screenshot --type screen --id 1
folio screenshot --type screen --id 1 --width 1440 --height 900
```

When the folio server is running, screenshots are taken via `http://localhost:7842/design/…` so `<link rel="folio-component">` includes are inlined correctly. If the server is not running, folio falls back to a `file://` URI and warns that component includes will be missing.

**Capturing dynamic states** — add classes or inject JS before capture without touching the HTML file. Requires the server to be running.

```sh
# Add one or more classes
folio screenshot --type screen --id 1 \
  --class ".list-pane:select-mode" \
  --class ".bulk-bar:active"

# Inject arbitrary JS
folio screenshot --type screen --id 1 \
  --js "document.querySelector('#header').style.display='none'"
```

JS executes after all page scripts have loaded (`DOMContentLoaded` timing), so it can safely call functions defined in the design file's own scripts.

Screenshot saved to `.folio/screenshots/` and recorded on the variant.

## Typical workflow

```sh
# Start a new project
folio init

# Track a new screen
folio screens add --name "Dashboard"
folio add-variant --type screen --id 1 --file "dashboard-v1.html" --label "v1"
folio add-variant --type screen --id 1 --file "dashboard-v2.html" --label "v2"

# Review, decide, record rationale
folio screens select-variant --variant-id 2
folio screens set-status --id 1 --status approved
folio screens set-rationale --id 1 --rationale "v2 reduces cognitive load above the fold"

# Update system.md so Claude knows what was decided
folio sync-system

# Open dashboard to review all items
folio serve
```

## Component reuse

Screen variants can reference shared components instead of copy-pasting HTML/CSS/JS:

```html
<link rel="folio-component" href="compose.html">
```

The folio server inlines the referenced file at serve time — works in the preview drawer, compare modal, and `folio screenshot`. Components can reference other components (up to 10 levels deep).

Only use this after the pattern is confirmed in 2+ finalised screens — not speculatively.

## Project structure

```
.folio/
  design.db        # SQLite database (screens, components, flows, variants)
  design/          # HTML design files (place variant files here)
  screenshots/     # captured PNGs from folio screenshot
  system.md        # decisions table, read by Claude as context
```

Tool installed globally at `~/.folio/` — the `folio` wrapper calls `~/.folio/lib/cli.py`.
