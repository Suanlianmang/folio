# /folio — Design Exploration Session

Run through these steps in order on every invocation.

---

## Step 1 — Check Folio CLI is installed

```bash
folio --help
```

- Works → skip to Step 2.
- `command not found` or any error → install automatically:

```bash
curl -fsSL https://raw.githubusercontent.com/Suanlianmang/folio/main/get.sh | bash
source ~/.zshrc 2>/dev/null || source ~/.bashrc 2>/dev/null || true
```

Tell the user: "Folio CLI installed. Continuing setup."

To update an existing install, run the same command.

---

## Step 2 — Check project is initialized

```bash
folio screens list
```

- Works → skip to Step 3.
- Errors with "run init first" or similar → initialize:

```bash
folio init
```

---

## Step 3 — Load state

```bash
folio screens list
folio components list
folio flows list
```

Read `.folio/system.md` for current decisions.

---

## Step 4 — Report to user

Brief summary:
- Count by type and status (exploring / approved / finalised)
- Items with no variants
- Items with 2+ variants ready for decision
- system.md state: blank / partial / populated

Keep it short. User directs next steps.

---

## CLI Reference

```bash
# Screens
folio screens list
folio screens add --name "..." [--description "..."] [--usage "..."]
folio screens show --id N
folio screens set-status --id N --status exploring|approved|finalised
folio screens set-rationale --id N --rationale "..."
folio screens set-parent --id N --parent N
folio screens select-variant --variant-id N

# Components
folio components list
folio components add --name "..."
folio components show --id N
folio components set-status --id N --status approved
folio components set-rationale --id N --rationale "..."
folio components link --id N --screen N
folio components unlink --id N --screen N
folio components select-variant --variant-id N

# Flows
folio flows list
folio flows add --name "..."
folio flows show --id N
folio flows set-status --id N --status approved
folio flows set-rationale --id N --rationale "..."
folio flows link --id N --screen N
folio flows unlink --id N --screen N
folio flows select-variant --variant-id N

# Shared
folio add-variant --type screen|component|flow --id N --file "file.html" [--label "..."]
folio screenshot --type screen|component|flow --id N [--width 1280] [--height 800]
folio sync-system
folio serve [--port N]
folio serve --stop
folio update
```

---

## UI Verification (mandatory)

After ANY change to `server.py` (CSS, JS, HTML):

1. Start server: `folio serve`
2. Take a browser screenshot of `http://localhost:7842`
3. Navigate to the affected section, verify visually
4. Only report done after screenshot confirms it looks correct

Never report a UI fix as done without a screenshot.

---

## Workflow

**Exploring** — variants exist, no selection. Compare, surface tradeoffs, ask user for direction.

**Approving** — user picks. Run `select-variant`, `set-status approved`, `set-rationale`. Then `sync-system`.

**Finalising** — locked. Set `finalised`. Rationale must exist first.

**New work** — user describes screen/component/flow. `add`, then `add-variant` per file.

After any batch of approvals → always `sync-system`.

---

## Dashboard

```bash
folio serve          # starts at http://localhost:7842
folio serve --stop
```

---

## Updating Folio

To update the CLI to the latest version:

```bash
folio update
```

To update this skill:

```bash
curl -fsSL https://raw.githubusercontent.com/Suanlianmang/folio/main/skill-install.sh | bash
```
