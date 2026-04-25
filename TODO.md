# Folio — Todo

## Tier 1 — Core primitives

- [x] **Structured deltas** (`folio screens change`)
  - Schema: `type`, `target`, `from`, `to`, `reason`, `outcome`
  - Add to `db.py`, `cli.py`
  - Include in `folio context` output

- [x] **Working hypothesis** (`folio screens set-hypothesis`)
  - Field per screen/component/flow
  - Shown in `folio context` output

- [x] **`folio context --screen N`** (prompt builder)
  - Outputs: current variant + last 5 deltas + hypothesis + focus area
  - Replaces reading system.md + show + screenshot separately
  - Add to `folio.md` as mandatory pre-iteration step

- [x] **Attention focus** (`folio focus --screen N --area "header CTA"`)
  - Stored per entity, included in `folio context`
  - Prevents Claude over-editing unrelated areas + regressions

## Tier 2 — High value

- [x] **`folio tree`** — dense text tree for LLM orientation on session start
- [x] **`needs_review` status** — formal human handoff, dashboard highlights it
- [x] **Regression awareness** — query deltas before change: "has this been tried?"
- [x] **`folio explain --screen N`** — Claude generates: what changed, what we're trying, what's unclear. Human re-orientation doc.

## Tier 3 — Lower priority

- [x] Global rules/tokens — injected top of `system.md`
- [x] Auto-generate "pending tasks" section on `sync-system` — zero-cost orientation every session
- [x] `folio suggest --screen N` — Claude proposes 1–3 focused next changes using deltas + hypothesis

## Pending fixes

- [ ] Arrow alignment in flow tree — confirm fix worked (need screenshot)
- [x] Update `folio.md` bootstrap rule: no screenshot on first iteration → write HTML first, screenshot, then iterate
