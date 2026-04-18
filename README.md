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

Creates `.folio/` with the SQLite database, screenshots directory, and `system.md`. If a `design/` directory exists inside `.folio/`, any HTML files there are automatically seeded as screens.

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

### Dashboard

```sh
folio serve                  # start dashboard at http://localhost:7842
folio serve --port 8080      # custom port
folio serve --stop           # stop the running server
```

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
```

### Components

```sh
folio components list
folio components add --name "Button"
folio components show --id 1
folio components set-status --id 1 --status approved
folio components set-rationale --id 1 --rationale "..."
folio components link --id 1 --screen 2                  # record component used in screen
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

### Variants

Add a variant to any entity type:

```sh
folio add-variant --type screen --id 1 --file "login-v2.html" --label "v2"
folio add-variant --type component --id 1 --file "btn-rounded.html" --label "rounded"
folio add-variant --type flow --id 1 --file "onboarding-short.html"
```

Optional flags: `--label`, `--ui-description`, `--notes`.

### Screenshots

Captures the selected variant file using headless Chrome. Requires Google Chrome or Chromium installed.

```sh
folio screenshot --type screen --id 1
folio screenshot --type screen --id 1 --width 1440 --height 900
```

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

## Project structure

```
.folio/
  design.db        # SQLite database (screens, components, flows, variants)
  design/          # HTML design files (place variant files here)
  screenshots/     # captured PNGs from folio screenshot
  system.md        # decisions table, read by Claude as context
```

Tool installed globally at `~/.folio/` — the `folio` wrapper calls `~/.folio/lib/cli.py`.
