# Folio — Claude Context

## Project
Design exploration tracker. Terminal tool installed at `~/.folio/`. Per-project data in `{project}/.folio/` (DB, design files, screenshots, system.md). Zero external deps (stdlib only).

## Key Files
- `db.py` — all DB logic, separate tables: screens / components / flows + variant tables + relation tables
- `cli.py` — namespaced subcommands: `folio screens list`, `folio flows link`, etc.
- `server.py` — stdlib http.server, inline DASHBOARD_HTML, ~2000+ lines
- `install.sh` — copies `*.py` + `system.md` to `~/.folio/lib/`, writes shell wrapper

**After every change to db.py or server.py: run `bash install.sh` if testing via installed path. Dev server runs direct from repo.**

## UI Verification (mandatory)

After ANY change to `server.py` (CSS, JS, HTML):
1. Start server: `cd /tmp/fp2 && python3 /Users/lethil/Desktop/folio/server.py`
2. Use built-in browser preview to screenshot `http://localhost:7842`
3. Navigate to the affected section, take screenshot, verify visually
4. Only report done after confirming the UI looks correct

Do NOT report a UI fix as done without taking a screenshot first.

---

## Planned Features

### Collaboration / Context
- **Variant notes / rationale** — "why" field per variant, visible in tree nodes
- **Constraint spec per screen** — target viewport, device, context attached to each screen
- **Issue flags** — mark variant/screen `needs-revision` + reason, without deleting
- **Side-by-side comparison** — split-pane view of 2 variants
- **Approval with conditions** — approve but attach conditions ("desktop only, mobile TBD")
- **Dependency impact view** — component used in N screens → show affected screens on change
- **Review thread per item** — simple note thread living next to the file

### Visual Feedback for Claude (core problem)
Claude edits UI blind → wrong assumptions → slow iteration. Solutions in priority order:

1. **Screenshots in chat (now)** — user pastes screenshot → Claude reads image → sees actual output
2. **`folio screenshot` command (short term)** — uses Playwright to capture served design file at viewport, saves to `.folio/screenshots/`, marks on variant. Claude reads with `Read` tool.
3. **Playwright MCP (later)** — wire Playwright MCP server → Claude gets `browser_navigate`, `browser_screenshot`, `browser_evaluate` → can open `localhost:7842`, inspect computed CSS, verify layout autonomously without user involvement

### Other
- Responsive/viewport previews (design at multiple sizes)
- Handoff notes attached to approved designs
