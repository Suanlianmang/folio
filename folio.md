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

---

## Step 2 — Check project is initialized

```bash
folio screens list
```

- Works → skip to Step 3.
- Errors → initialize:

```bash
folio init
```

---

## Step 2.5 — Ensure server is running

```bash
curl -s http://localhost:7842/api/status > /dev/null 2>&1 && echo "running" || echo "stopped"
```

- `running` → skip.
- `stopped` → start in background:

```bash
folio serve &
sleep 1
```

Do not tell the user unless the server was just started. If started, say: "Dashboard running at http://localhost:7842"

---

## Step 3 — Orient with tree

```bash
folio tree
```

This gives a complete project overview in one shot. Use it to understand what exists before touching anything. Do not run `screens list` / `components list` / `flows list` separately — `folio tree` replaces all three.

Read `.folio/system.md` for approved decisions and global rules.

---

## Step 4 — Report to user

Brief summary based on `folio tree` output:
- Count by type and status (exploring / approved / finalised)
- Items flagged needs-review
- Items with 2+ variants ready for decision
- Items with no variants yet

Keep it short. User directs next steps.

---

## Before every design iteration — mandatory pre-flight

Before touching any HTML file, run:

```bash
folio context --type screen|component|flow --id N
```

This outputs everything needed in one command: current file, hypothesis, focus area, last 5 changes, variants. **Never** substitute this with `folio screens show` + reading raw HTML + checking system.md separately. `folio context` is the single source of truth for what to work on and why.

Also check for approved components to reuse:

```bash
folio components list
```

Never reimplement a component that already exists as approved.

**First iteration rule:** If no HTML file exists yet for this item — skip context, write the HTML first, then run context on the next pass.

---

## After every design iteration — mandatory recording

After writing or modifying an HTML file, record what changed using the lightweight log command:

```bash
folio log --type screen|component|flow --id N "what changed and why"
```

One line, one string. This feeds `folio suggest` automatically. Use it immediately after every iteration.

For structured delta recording (when you need from/to values or specific change types):

```bash
folio screens change --id N \
  --type layout|copy|color|spacing|interaction|other \
  --target "element name" \
  --from "previous value" \
  --to "new value" \
  --reason "why this change"
```

If the command warns "target was changed N times before", check if this has already been tried and failed before proceeding.

Then take a screenshot and read it:

```bash
folio screenshot --type screen --id N
```

Read the screenshot with the `Read` tool. Never report an iteration as done without seeing the actual output.

---

## When user gives feedback on a result

Record the outcome immediately:

```bash
folio screens record-outcome --delta-id N --outcome "what happened"
```

Find the delta ID from `folio context` output or `folio explain`. Outcomes are the memory of the project — always record them.

---

## Setting hypothesis and focus

When starting work on an item for the first time, or when the user states a goal:

```bash
folio screens set-hypothesis --id N --hypothesis "what we believe and want to test"
folio screens set-focus --id N --area "which part of the design to focus on"
```

Hypothesis = what you're trying to prove. Focus = where Claude should concentrate — prevents drift into unrelated areas.

If hypothesis or focus are missing and there are 2+ variants or changes, ask the user to provide them before continuing.

---

## When stuck or asked for next steps

```bash
folio suggest --type screen --id N
```

Copy the output and paste it into the conversation as a Claude prompt. Do not invent next steps from scratch — use `suggest` to generate options grounded in the actual delta history.

---

## Re-orientation after a gap

If resuming work after a break or the context feels unclear:

```bash
folio explain --type screen --id N
```

This outputs: current state, what's been tried, open questions (changes with no outcome recorded). Use it instead of asking the user to recap.

---

## Approving and finalising

**Approving** — user selects a variant:

```bash
folio screens select-variant --variant-id N        # by ID
folio screens select-variant --id N --file "f.html"  # by filename (when ID unknown)
folio screens set-rationale --id N --rationale "why this variant won"
folio screens set-status --id N --status approved
folio sync-system
```

Rationale is mandatory before `set-status approved`. If missing, ask the user first.

Note: selecting a variant via the dashboard automatically prompts for rationale — no separate CLI call needed in that flow.

**Finalising** — locked, no further changes:

```bash
folio screens set-status --id N --status finalised
folio sync-system
```

Rationale must already exist.

**After any batch of approvals** → always `sync-system`.

---

## Needs-review handoff

When a design needs human judgment before continuing:

```bash
folio screens needs-review --id N
```

The dashboard highlights it. Clear it when resolved:

```bash
folio screens clear-needs-review --id N
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

## CLI Reference

```bash
# Orientation
folio tree
folio context --type screen|component|flow --id N
folio explain --type screen|component|flow --id N
folio suggest --type screen|component|flow --id N

# Screens
folio screens list
folio screens add --name "..." [--description "..."] [--usage "..."]
folio screens show --id N
folio screens set-status --id N --status exploring|approved|finalised
folio screens set-rationale --id N --rationale "..."
folio screens set-parent --id N --parent N
folio screens rename --id N --name "..."
folio screens delete --id N
folio screens set-description --id N --description "..."
folio screens select-variant --variant-id N
folio screens select-variant --id N --file "filename.html"  # alternative: by filename
folio screens remove-variant --variant-id N
folio screens move-variant --variant-id N --to-screen N
folio screens set-hypothesis --id N --hypothesis "..."
folio screens set-focus --id N --area "..."
folio screens needs-review --id N
folio screens clear-needs-review --id N
folio screens change --id N --type T --target "..." --from "..." --to "..." [--reason "..."]
folio screens record-outcome --delta-id N --outcome "..."
folio screens set-variant-rationale --variant-id N --rationale "..."
folio screens flag-variant --variant-id N [--reason "..."]
folio screens unflag-variant --variant-id N

# Components
folio components list
folio components add --name "..."
folio components show --id N
folio components set-status --id N --status approved
folio components set-rationale --id N --rationale "..."
folio components link --id N --screen N
folio components unlink --id N --screen N
folio components select-variant --variant-id N
folio components select-variant --id N --file "filename.html"
folio components set-hypothesis --id N --hypothesis "..."
folio components set-focus --id N --area "..."
folio components needs-review --id N
folio components clear-needs-review --id N
folio components change --id N --type T --target "..." --from "..." --to "..."
folio components record-outcome --delta-id N --outcome "..."

# Flows
folio flows list
folio flows add --name "..."
folio flows show --id N
folio flows set-status --id N --status approved
folio flows set-rationale --id N --rationale "..."
folio flows link --id N --screen N
folio flows unlink --id N --screen N
folio flows select-variant --variant-id N
folio flows select-variant --id N --file "filename.html"
folio flows set-hypothesis --id N --hypothesis "..."
folio flows set-focus --id N --area "..."
folio flows needs-review --id N
folio flows clear-needs-review --id N
folio flows change --id N --type T --target "..." --from "..." --to "..."
folio flows record-outcome --delta-id N --outcome "..."

# Logging (lightweight, preferred over screens change)
folio log --type screen|component|flow --id N "what changed and why"
folio log --type screen|component|flow --id N --variant-id N "what changed and why"  # scoped to a specific variant

# Shared
folio add-variant --type screen|component|flow --id N --file "file.html" [--label "..."] [--rationale "..."]
# Note: --file accepts absolute paths — folio copies the file into .folio/design/ automatically
folio screenshot --type screen|component|flow --id N [--width 1280] [--height 800]
folio sync-system
folio serve [--port N]
folio serve --stop
folio update
```

---

## Iteration loop (summary)

Every design pass follows this exact sequence — no shortcuts:

```
folio context        → read current state
[write / edit HTML]
folio screenshot     → see actual output
folio log            → record what changed and why (add --variant-id N to scope to a variant)
[user gives feedback]
folio record-outcome → capture the result (only if using screens change)
```

If stuck: `folio suggest` → paste prompt → iterate.
If re-orienting: `folio explain` → resume from ground truth.

---

## Dashboard

```bash
folio serve          # starts at http://localhost:7842
folio serve --stop
```

Dashboard features:
- **Flagged** sidebar tab — queue of all variants flagged `needs-revision` across all types
- **Compare ↗** button on any item with 2+ variants — side-by-side iframe view
- Entity rationale shown on card, clickable to edit
- Screen cards show which components are linked to them

---

## Component reuse (server-side include)

Screen variants can reference shared components instead of copy-pasting HTML/CSS/JS. Add to any screen HTML file:

```html
<link rel="folio-component" href="compose.html">
```

The folio server inlines the referenced file at serve time — works in the preview drawer, compare modal, and `folio screenshot`. Components can reference other components (up to 10 levels deep). If the file is not found, an HTML comment is injected and a warning printed to the server log.

When writing new screen variants, always check if approved components exist (`folio components list`) — reference them via `<link rel="folio-component">` instead of reimplementing.

---

## Updating Folio

```bash
folio update
```

To update this skill:

```bash
curl -fsSL https://raw.githubusercontent.com/Suanlianmang/folio/main/skill-install.sh | bash
```
