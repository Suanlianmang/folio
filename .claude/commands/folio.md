# /folio — Design Exploration Session

You are helping with a design project tracked by Folio. On every invocation, run through these steps in order.

---

## Step 1 — Check if Folio is installed

Check whether `tools/folio/cli.py` exists.

**If missing**, install it:

```bash
mkdir -p tools
git clone https://github.com/Suanlianmang/folio tools/folio
```

Then add `tools/folio/` and per-project data to the host repo's `.gitignore` (append only if not already present):

```
tools/folio/
tools/design.db
tools/screenshots/
tools/system.md
```

Then install Flask:

```bash
uv pip install flask 2>/dev/null || pip install flask
```

---

## Step 2 — Check if Folio is initialized

```bash
python3 tools/folio/cli.py list
```

- Succeeds → skip to Step 4.
- Errors (DB missing / "Run init first") → continue to Step 3.

---

## Step 3 — Initialize (only if needed)

```bash
python3 tools/folio/cli.py init
```

Creates `tools/design.db`, copies system.md template to `tools/system.md`, seeds any HTML files found in `design/` as items + variants.

---

## Step 4 — Load state

```bash
python3 tools/folio/cli.py list
```

Then read `tools/system.md` for current design system decisions.

---

## Step 5 — Report to user

Short structured summary:

- Total items by status (exploring / approved / finalised)
- Items with no variants (need files)
- Items on `exploring` with 2+ variants (ready for decision)
- Design system state: blank, partial, or populated

Keep it brief. User directs next steps.

---

## Available CLI commands

Run all commands from the host project root.

```bash
# Read
python3 tools/folio/cli.py list
python3 tools/folio/cli.py show --id <n>

# Create
python3 tools/folio/cli.py add-item \
  --type (screen|layout|component|flow) \
  --name "..." \
  --description "..." \
  --usage "..."

python3 tools/folio/cli.py add-variant \
  --item-id <n> \
  --file <filename.html> \
  --label "v1" \
  --ui-description "..."

# Decisions
python3 tools/folio/cli.py select --variant-id <n>
python3 tools/folio/cli.py set-status --id <n> --status (exploring|approved|finalised)
python3 tools/folio/cli.py set-rationale --id <n> --rationale "..."

# Sync design system doc
python3 tools/folio/cli.py sync-system
```

---

## Workflow guide

**Exploring** — variants exist, no selection. Compare options, surface tradeoffs, ask for direction.

**Approving** — user picks direction. Run `select`, `set-status approved`, `set-rationale`. Then `sync-system`.

**Finalising** — design locked. Set `finalised`. Rationale must exist first.

**New work** — user describes a screen/component/flow. Run `add-item`, then `add-variant` per file.

After any batch of approvals → always run `sync-system`.

---

## Dashboard (visual browse)

```bash
python3 tools/folio/server.py
# → http://localhost:5555
```

---

## Notes

- All CLI commands run from host project root, not `tools/folio/`
- `tools/folio/` is gitignored in host repo — updates via `git -C tools/folio pull`
- Only the `<!-- DECISIONS-START -->` / `<!-- DECISIONS-END -->` block in `tools/system.md` is ever overwritten by `sync-system`
