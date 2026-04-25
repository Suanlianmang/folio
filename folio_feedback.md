# Folio Feedback

Collected from a real session: importing existing screens, registering variants, restructuring screen hierarchy.

---

## New (Session 2)

### `folio screens select-variant --file "filename.html"`
Variant IDs are unpredictable — after registering a file you don't know if it's variant #8 or #10 without checking. `select-variant` requires the ID. Should accept `--file` as an alternative so you can select by filename, which is always known.

### `folio log --variant-id N "..."`
Logs currently attach to the screen/component, not a specific variant. With 3 variants in exploration, there's no way to know which log entry belongs to which. Should be able to log against a variant directly.

---

## Completed ✓

### `folio screens rename --id N --name "..."`  ✓
### `folio screens delete --id N`  ✓
### `folio screens set-description --id N --description "..."`  ✓
### `folio screens remove-variant --variant-id N`  ✓
### `folio screens move-variant --variant-id N --to-screen N`  ✓
### `folio log` top-level command  ✓

---

## Missing CLI Commands

### `folio screens move-variant --variant-id N --to-screen N`
Moving a variant from one screen to another required `UPDATE screen_variants SET screen_id = N`. Common when restructuring.

---

## Broken Behavior

### `add-variant --file /absolute/path` stores the path as-is
When passing an absolute path, folio stores it verbatim in the DB. The server then 404s because it resolves paths relative to `.folio/design/`. Expected behavior: copy file into `.folio/design/` and store filename only. Required 3 manual steps to fix (update 5 DB rows via sqlite3).

### `folio init` seeds from `design/` (top-level), not `.folio/design/`
Creates split ownership confusion. Files exist in `design/`, folio expects them in `.folio/design/`. No warning emitted.

### No warning when variant file is outside `.folio/design/`
Silent failure → 404 in dashboard. Should warn at `add-variant` time.

---

## No Tooling For

- **Splitting a multi-section HTML into separate variants** — had a single file with 3 options side-by-side (A/B/C columns). Had to manually extract each into its own file, then register 3 variants.
- **Migrating an existing `design/system.md`** — no import or merge command. Manually copied tokens, components, decisions into `.folio/system.md`.

---

## Dashboard Missing

### Rationale not displayed anywhere
`folio components set-rationale` saves to DB but the dashboard never surfaces it — not on the component card, not in the detail view. Same likely true for screens and flows. Rationale is useless if it's invisible.

### No way to view all variants at once
Variants are only viewable one at a time — click to switch. No side-by-side or grid view. For exploration (e.g. thread A vs B vs C) you have to mentally compare across clicks. A "compare variants" mode or thumbnail grid would make diverging directions much easier to evaluate.

### Components linked to a screen not shown on screen detail
`folio components link --id N --screen N` records the relationship but the screen detail view doesn't list which components it uses. To know what's linked you have to run `folio components show --id N` and infer from there. Should be visible on the screen itself.

---

## Underused Features & How to Fix That

### `folio screens change` + `record-outcome` — too much ceremony, never used
Five required flags per call (`--type`, `--target`, `--from`, `--to`, `--reason`) makes it too costly to run naturally after every iteration. It gets skipped. Replaced by `folio log` — but `log` needs `--variant-id` support to be fully useful.

### Rationale — set once, never revisited
Would get used more if folio prompted for it at the moment of `select-variant` — "why did this variant win?" That's the natural moment, not a separate command.

### Flag — never used
No review step in the current workflow means flag never gets triggered. Would become useful if the dashboard surfaced flagged variants as a distinct queue.

### Hypothesis + Focus — set but ignored
Would become useful if `folio context` prominently displayed them at the top and `folio suggest` used them as constraints when generating next steps.

---

## Core Missing Feature: `folio log` (now shipped — needs variant-level support)

`folio log` shipped and is the right pattern — one line, low friction, fits naturally after screenshot. Missing piece: logs attach to the item, not the variant. With multiple variants in flight, the log is ambiguous. `--variant-id` would complete it.

---

## Architecture Suggestion: Component Reuse

Every screen variant currently copy-pastes the same CSS and JS — compose box, action buttons, popover, pin button, thread strips. Hundreds of lines repeated per file. This means:
- Reading a screen variant costs full context every time
- Fixing a component (e.g. compose box) requires editing every file that uses it
- Variants are hard to compare because they're bloated with shared boilerplate

**Suggestion:** folio should support a simple include system for approved components. Could be as lightweight as a `<link rel="component" href="../components/compose.html">` convention that the folio server resolves at serve time. Screen variants then only contain what's unique to them — layout, structure, the decisions being tested. Approved components are referenced, not duplicated.

This would make variants smaller, comparisons faster, and component changes propagate automatically.

---

## What Worked Well

- `folio tree` — single command, full project overview.
- `folio context --type screen --id N` — good single source of truth before iterating.
- `folio log` — right friction level, now part of the natural loop.
- `sync-system` auto-generates Pending table — good signal of what's left exploring.
- Parent-child screen hierarchy — useful for Inbox → Email Detail.
- Flow linking screens together — intuitive once screens are set up.
