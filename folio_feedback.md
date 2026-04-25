# Folio Feedback

Collected from a real session: importing existing screens, registering variants, restructuring screen hierarchy.

---

## Missing CLI Commands

### `folio screens rename --id N --name "..."`
No way to rename a screen without direct DB access. Had to run `sqlite3` and `UPDATE screens SET name = ...`.

### `folio screens delete --id N`
No delete command. Used `DELETE FROM screens WHERE id = N` + manual cleanup of `flow_screens`.

### `folio screens move-variant --variant-id N --to-screen N`
Moving a variant from one screen to another required `UPDATE screen_variants SET screen_id = N`. Common when restructuring.

### `folio screens set-description --id N --description "..."`
Description set at creation only. No way to update it afterward.

### `folio screens remove-variant --variant-id N`
No way to delete a variant from a screen or component. Used `DELETE FROM screen_variants WHERE id = N` directly. Came up when moving thread variants from a screen into a component — had to clean up the old registrations via sqlite3.

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
Five required flags per call (`--type`, `--target`, `--from`, `--to`, `--reason`) makes it too costly to run naturally after every iteration. It gets skipped. Suggest replacing with a single lightweight command:
```
folio log --id N "removed thread strips — testing pure reading focus"
```
One line, one string, attached to current selected variant. Low enough friction to actually use. `suggest` then has real history to work from.

### Rationale — set once, never revisited
Currently used as a free-text field with no prompt. Gets filled once at creation and forgotten. Would get used more if folio prompted for it at the moment of `select-variant` (approval) — "why did this variant win?" That's the natural moment, not a separate command.

### Flag — never used
No review step in the current workflow means flag never gets triggered. Would become useful if the dashboard surfaced "flagged variants" as a distinct queue, making it feel like an action item rather than a label.

### Hypothesis + Focus — set but ignored
Currently pure metadata — setting them doesn't change what folio does or what I focus on. Would become useful if `folio context` prominently displayed them at the top and `folio suggest` used them as constraints when generating next steps.

---

## Core Missing Feature: `folio log`

The iteration loop is: write HTML → screenshot → user reacts. Delta recording sits outside this loop — it's a tax, not a natural step. The fix isn't discipline or automation; it's reducing recording to one command with one argument run immediately after screenshot. `folio screens change` has too many flags. `folio log` would replace it: intent in one sentence, attached to the current variant, feeds `suggest` automatically.

---

## What Worked Well

- `folio tree` — single command, full project overview. Replaced needing `screens list` + `components list` + `flows list`.
- `folio context --type screen --id N` — good single source of truth before iterating.
- Parent-child screen hierarchy — useful for Inbox → Email Detail.
- Flow linking screens together — intuitive once screens are set up.
