# Folio TODO

## Pending fixes (from session 2 feedback)

### Broken behavior
- [x] `add-variant --file /absolute/path` stores path verbatim → 404. Fixed: copies to `.folio/design/`, stores filename only.
- [x] `folio init` seeds only from `.folio/design/`, warns about top-level `design/`.
- [x] Warning emitted when variant file missing from `.folio/design/` at `add-variant` time.

### CLI gaps
- [x] `select-variant --file <filename>` — add `--id` + `--file` as alternative to `--variant-id` (all three entity types).
- [x] `folio log --variant-id N` — logs now attach to a specific variant. `deltas` table gains `variant_id` column (migration included).

### Dashboard gaps
- [x] Rationale renders in dashboard cards (`entityRationaleHtml` wired in all three card renderers).
- [x] Compare modal (`Compare ↗` button + `openCompareModal`) implemented in `dashboard.js`.
- [x] Screen components shown on screen cards via `screenComponentsHtml`.

---

## Component Reuse (server-side include) ✓

`<link rel="folio-component" href="compose.html">` in any screen HTML → server inlines the referenced file at serve time. Recursive (depth limit 10). Non-HTML files pass through unchanged. No DB/CLI changes needed.
