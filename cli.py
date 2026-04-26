"""
cli.py — Folio CLI. Claude-readable plaintext output.

Run from host project root:
    python3 tools/folio/cli.py <command> [args]
"""

import argparse
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — db.py lives in ~/.folio/lib/
# ---------------------------------------------------------------------------

_FOLIO_LIB = str(Path.home() / ".folio" / "lib")
if _FOLIO_LIB not in sys.path:
    sys.path.insert(0, _FOLIO_LIB)

import db

# Configure db paths relative to CWD (host project root)
db.configure(Path.cwd())


# ---------------------------------------------------------------------------
# Output helpers — screens
# ---------------------------------------------------------------------------

def _print_screen_summary(screen: dict) -> None:
    """Print one-line screen summary with indented variants."""
    parent_note = f" (child of #{screen['parent_id']})" if screen.get("parent_id") else ""
    print(f"  #{screen['id']} [screen] {screen['name']} ({screen['status']}){parent_note}")
    for variant in screen.get("variants", []):
        selected_marker = "●" if variant["file"] == screen.get("selected_file") else " "
        label = f" — {variant['label']}" if variant["label"] else ""
        print(f"      {selected_marker} {variant['file']}{label}")


def _print_screen_detail(screen: dict) -> None:
    """Print full screen detail for show command."""
    print(f"#{screen['id']} [screen] {screen['name']}")
    print(f"  Status:      {screen['status']}")
    if screen.get("parent_id"):
        print(f"  Parent:      #{screen['parent_id']}")
    children = screen.get("children", [])
    if children:
        child_ids = ", ".join(f"#{c}" for c in children)
        print(f"  Children:    {child_ids}")
    if screen.get("description"):
        print(f"  Description: {screen['description']}")
    if screen.get("usage"):
        print(f"  Usage:       {screen['usage']}")
    if screen.get("selected_file"):
        print(f"  Selected:    {screen['selected_file']}")
    if screen.get("rationale"):
        print(f"  Rationale:   {screen['rationale']}")
    if screen.get("hypothesis"):
        print(f"  Hypothesis:  {screen['hypothesis']}")
    if screen.get("focus"):
        print(f"  Focus:       {screen['focus']}")
    if screen.get("needs_review"):
        print(f"  Needs review: yes")
    print(f"  Created:     {screen['created_at']}")
    print(f"  Updated:     {screen['updated_at']}")

    variants = screen.get("variants", [])
    if variants:
        print(f"  Variants ({len(variants)}):")
        for v in variants:
            selected_marker = "●" if v["file"] == screen.get("selected_file") else " "
            label           = f" [{v['label']}]" if v["label"] else ""
            print(f"      {selected_marker} #{v['id']} {v['file']}{label}")
            if v.get("ui_description"):
                print(f"          {v['ui_description']}")
            if v.get("notes"):
                print(f"          Notes: {v['notes']}")
            if v.get("rationale"):
                print(f"          Rationale: {v['rationale']}")
            if v.get("flag"):
                reason = f" — {v['flag_reason']}" if v.get("flag_reason") else ""
                print(f"          Flag: {v['flag']}{reason}")
    else:
        print("  Variants: (none)")


# ---------------------------------------------------------------------------
# Output helpers — components
# ---------------------------------------------------------------------------

def _print_component_summary(component: dict) -> None:
    """Print one-line component summary with indented variants."""
    used_in = component.get("used_in", [])
    n_used = len(used_in)
    reuse_tag = f"  ⚠ used in {n_used} screen{'s' if n_used != 1 else ''}" if n_used < 2 else f"  used in {n_used} screens"
    print(f"  #{component['id']} [component] {component['name']} ({component['status']}){reuse_tag}")
    if used_in:
        names = ", ".join(s["name"] for s in used_in)
        print(f"      Used in: {names}")
    for variant in component.get("variants", []):
        selected_marker = "●" if variant["file"] == component.get("selected_file") else " "
        label = f" — {variant['label']}" if variant["label"] else ""
        print(f"      {selected_marker} {variant['file']}{label}")


def _print_component_detail(component: dict) -> None:
    """Print full component detail for show command."""
    print(f"#{component['id']} [component] {component['name']}")
    print(f"  Status:      {component['status']}")
    if component.get("description"):
        print(f"  Description: {component['description']}")
    if component.get("usage"):
        print(f"  Usage:       {component['usage']}")
    if component.get("selected_file"):
        print(f"  Selected:    {component['selected_file']}")
    if component.get("rationale"):
        print(f"  Rationale:   {component['rationale']}")
    if component.get("hypothesis"):
        print(f"  Hypothesis:  {component['hypothesis']}")
    if component.get("focus"):
        print(f"  Focus:       {component['focus']}")
    if component.get("needs_review"):
        print(f"  Needs review: yes")
    used_in = component.get("used_in", [])
    if used_in:
        names = ", ".join(s["name"] for s in used_in)
        print(f"  Used in:     {names}")
    print(f"  Created:     {component['created_at']}")
    print(f"  Updated:     {component['updated_at']}")

    variants = component.get("variants", [])
    if variants:
        print(f"  Variants ({len(variants)}):")
        for v in variants:
            selected_marker = "●" if v["file"] == component.get("selected_file") else " "
            label           = f" [{v['label']}]" if v["label"] else ""
            print(f"      {selected_marker} #{v['id']} {v['file']}{label}")
            if v.get("ui_description"):
                print(f"          {v['ui_description']}")
            if v.get("notes"):
                print(f"          Notes: {v['notes']}")
            if v.get("rationale"):
                print(f"          Rationale: {v['rationale']}")
            if v.get("flag"):
                reason = f" — {v['flag_reason']}" if v.get("flag_reason") else ""
                print(f"          Flag: {v['flag']}{reason}")
    else:
        print("  Variants: (none)")


# ---------------------------------------------------------------------------
# Output helpers — flows
# ---------------------------------------------------------------------------

def _print_flow_summary(flow: dict) -> None:
    """Print one-line flow summary with indented variants."""
    print(f"  #{flow['id']} [flow] {flow['name']} ({flow['status']})")
    screens = flow.get("screens", [])
    if screens:
        names = ", ".join(s["name"] for s in screens)
        print(f"      Screens: {names}")
    for variant in flow.get("variants", []):
        selected_marker = "●" if variant["file"] == flow.get("selected_file") else " "
        label = f" — {variant['label']}" if variant["label"] else ""
        print(f"      {selected_marker} {variant['file']}{label}")


def _print_flow_detail(flow: dict) -> None:
    """Print full flow detail for show command."""
    print(f"#{flow['id']} [flow] {flow['name']}")
    print(f"  Status:      {flow['status']}")
    if flow.get("description"):
        print(f"  Description: {flow['description']}")
    if flow.get("usage"):
        print(f"  Usage:       {flow['usage']}")
    if flow.get("selected_file"):
        print(f"  Selected:    {flow['selected_file']}")
    if flow.get("rationale"):
        print(f"  Rationale:   {flow['rationale']}")
    if flow.get("hypothesis"):
        print(f"  Hypothesis:  {flow['hypothesis']}")
    if flow.get("focus"):
        print(f"  Focus:       {flow['focus']}")
    if flow.get("needs_review"):
        print(f"  Needs review: yes")
    screens = flow.get("screens", [])
    if screens:
        names = ", ".join(s["name"] for s in screens)
        print(f"  Screens:     {names}")
    print(f"  Created:     {flow['created_at']}")
    print(f"  Updated:     {flow['updated_at']}")

    variants = flow.get("variants", [])
    if variants:
        print(f"  Variants ({len(variants)}):")
        for v in variants:
            selected_marker = "●" if v["file"] == flow.get("selected_file") else " "
            label           = f" [{v['label']}]" if v["label"] else ""
            print(f"      {selected_marker} #{v['id']} {v['file']}{label}")
            if v.get("ui_description"):
                print(f"          {v['ui_description']}")
            if v.get("notes"):
                print(f"          Notes: {v['notes']}")
            if v.get("rationale"):
                print(f"          Rationale: {v['rationale']}")
            if v.get("flag"):
                reason = f" — {v['flag_reason']}" if v.get("flag_reason") else ""
                print(f"          Flag: {v['flag']}{reason}")
    else:
        print("  Variants: (none)")


# ---------------------------------------------------------------------------
# Top-level commands
# ---------------------------------------------------------------------------

def _cmd_init(_args: argparse.Namespace) -> None:
    db.init_db()
    print("Initialized: DB schema created, screenshots dir ready.")

    top_level_design = Path.cwd() / "design"
    if top_level_design.is_dir():
        print(
            "Warning: found top-level design/ directory. "
            "Folio serves files from .folio/design/ — move or copy your files there."
        )

    if db.DESIGN_DIR.is_dir():
        count = db.seed_from_design()
        if count > 0:
            print(f"Seeded {count} screen(s) from .folio/design/.")
        else:
            print(".folio/design/ found but no HTML files to seed.")
    else:
        print("No .folio/design/ directory found — skipping seed.")


_CHROME_CANDIDATES = [
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]


def _find_chrome() -> str | None:
    import shutil
    for candidate in _CHROME_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
        if shutil.which(candidate):
            return candidate
    return None


def _cmd_screenshot(args: argparse.Namespace) -> None:
    import subprocess, tempfile, shutil as _shutil

    entity_type = args.type
    entity_id   = args.id

    if entity_type == "screen":
        item = db.get_screen(entity_id)
    elif entity_type == "component":
        item = db.get_component(entity_id)
    else:
        item = db.get_flow(entity_id)

    if not item:
        print(f"Error: {entity_type} #{entity_id} not found.")
        sys.exit(1)

    selected_file = item.get("selected_file")
    if not selected_file:
        print(f"Error: {entity_type} #{entity_id} has no selected file. Select a variant first.")
        sys.exit(1)

    chrome = _find_chrome()
    if not chrome:
        print("Error: Chrome/Chromium not found. Install Google Chrome and retry.")
        sys.exit(1)

    design_file = db.DESIGN_DIR / selected_file
    if not design_file.exists():
        print(f"Error: Design file not found: {design_file}")
        sys.exit(1)

    db.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    width  = getattr(args, "width",  1280)
    height = getattr(args, "height", 800)
    out    = db.SCREENSHOTS_DIR / f"{entity_type}-{entity_id}.png"

    url = design_file.as_uri()
    extra_args: list[str] = []
    js_injection  = getattr(args, "js", None)
    cls_injection = getattr(args, "classes", [])
    if _PID_FILE.exists():
        try:
            pid = int(_PID_FILE.read_text().strip())
            os.kill(pid, 0)
            port = int(os.environ.get("FOLIO_PORT", "7842"))
            base_url = f"http://localhost:{port}/design/{selected_file}"
            from urllib.parse import urlencode, quote
            params: list[tuple[str, str]] = []
            for cls_spec in cls_injection:
                params.append(("class", cls_spec))
            if js_injection:
                params.append(("js", js_injection))
            url = base_url + ("?" + urlencode(params) if params else "")
            extra_args = ["--virtual-time-budget=5000"]
        except (ProcessLookupError, ValueError):
            print("Warning: server not running — component includes will not be inlined.")
    else:
        print("Warning: server not running — component includes will not be inlined.")
    if (js_injection or cls_injection) and url.startswith("file://"):
        print("Error: --js / --class require the folio server to be running.")
        sys.exit(1)

    cmd = [
        chrome,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        f"--window-size={width},{height}",
        f"--screenshot={out}",
        *extra_args,
        url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: Chrome exited {result.returncode}.")
        if result.stderr:
            print(result.stderr[:400])
        sys.exit(1)

    if not out.exists():
        print("Error: Screenshot not created — Chrome may have failed silently.")
        sys.exit(1)

    # Update the selected variant's screenshot field
    variants = item.get("variants", [])
    matched  = next((v for v in variants if v["file"] == selected_file), None)
    if matched:
        if entity_type == "screen":
            db.update_screen_variant_screenshot(matched["id"], str(out))
        elif entity_type == "component":
            db.update_component_variant_screenshot(matched["id"], str(out))
        else:
            db.update_flow_variant_screenshot(matched["id"], str(out))

    print(f"Screenshot saved: {out}")


def _cmd_sync_system(_args: argparse.Namespace) -> None:
    db.sync_system()
    print(f"system.md updated: {db.SYSTEM_MD_PATH}")


def _cmd_context(args: argparse.Namespace) -> None:
    entity_type = args.type
    entity_id   = args.id

    if entity_type == "screen":
        item = db.get_screen(entity_id)
    elif entity_type == "component":
        item = db.get_component(entity_id)
    else:
        item = db.get_flow(entity_id)

    if item is None:
        print(f"Error: {entity_type} #{entity_id} not found.")
        sys.exit(1)

    label = entity_type.capitalize()
    review_label = "yes" if item.get("needs_review") else "no"
    print(f"=== CONTEXT: {label} #{item['id']} — {item['name']} ===")

    # Hypothesis and focus first — they are the active constraints
    if item.get("hypothesis"):
        print(f"HYPOTHESIS: {item['hypothesis']}")
    if item.get("focus"):
        print(f"FOCUS:      {item['focus']}")
    if item.get("hypothesis") or item.get("focus"):
        print()

    print(f"Status: {item['status']}  |  Needs review: {review_label}")
    if item.get("selected_file"):
        print(f"Selected: {item['selected_file']}")

    # Inject global rules from system.md if markers present.
    if db.SYSTEM_MD_PATH.exists():
        content = db.SYSTEM_MD_PATH.read_text(encoding="utf-8")
        start_marker = "<!-- GLOBAL-RULES-START -->"
        end_marker   = "<!-- GLOBAL-RULES-END -->"
        if start_marker in content and end_marker in content:
            start_idx = content.index(start_marker) + len(start_marker)
            end_idx   = content.index(end_marker)
            rules_text = content[start_idx:end_idx].strip()
            if rules_text:
                print()
                print("--- GLOBAL RULES (from system.md) ---")
                print(rules_text)
                print("--------------------------------------")

    deltas = db.list_deltas(entity_type, entity_id, limit=5)
    print()
    print("RECENT CHANGES (last 5):")
    if deltas:
        for delta in deltas:
            date_str = (delta.get("created_at") or "")[:10]
            target   = delta.get("target") or ""
            from_val = delta.get("from_val") or ""
            to_val   = delta.get("to_val") or ""
            reason   = delta.get("reason") or ""
            outcome  = delta.get("outcome") or "not recorded"
            change_str = f"{from_val!r} → {to_val!r}" if (from_val or to_val) else ""
            target_str = f"{target}: {change_str}" if change_str else target
            print(f"  {date_str}  {delta['type']}   {target_str}")
            if reason:
                print(f"              Reason:  {reason}")
            print(f"              Outcome: {outcome}")
    else:
        print("  (none)")

    variants = item.get("variants", [])
    print()
    print(f"VARIANTS ({len(variants)}):")
    if variants:
        for v in variants:
            selected_marker = "●" if v["file"] == item.get("selected_file") else " "
            label_str = f"  [{v['label']}]" if v.get("label") else ""
            flag_str = f"  — {v['flag']}: {v.get('flag_reason') or ''}" if v.get("flag") else ""
            print(f"  {selected_marker} {v['file']}{label_str}{flag_str}")
    else:
        print("  (none)")

    if entity_type == "component":
        print()
        print("Rule: components are late extractions — register only when the same UI is confirmed in 2+ approved/finalised screens.")


def _cmd_tree(args: argparse.Namespace) -> None:
    full       = getattr(args, "full", False)
    screens    = db.list_screens()
    components = db.list_components()
    flows      = db.list_flows()

    print("=== PROJECT TREE ===")

    # ---- screens ----
    roots    = [s for s in screens if not s.get("parent_id")]
    by_parent: dict[int, list[dict]] = {}
    for s in screens:
        pid = s.get("parent_id")
        if pid:
            by_parent.setdefault(pid, []).append(s)

    def _print_screen_node(screen: dict, indent: int) -> None:
        prefix     = "  " * indent
        sub        = "  " * (indent + 1)
        variants   = screen.get("variants", [])
        n_variants = len(variants)
        n_flagged  = sum(1 for v in variants if v.get("flag"))
        file_str   = f"  ● {screen['selected_file']}" if screen.get("selected_file") else ""
        var_str    = ""
        if n_variants:
            var_str = f"  ({n_variants} variant{'s' if n_variants != 1 else ''}"
            var_str += f", {n_flagged} flagged" if n_flagged else ""
            var_str += ")"
        print(f"{prefix}#{screen['id']}  [{screen['status']}]  {screen['name']}{file_str}{var_str}")
        if screen.get("hypothesis"):
            print(f"{sub}Hypothesis: {screen['hypothesis']}")
        if screen.get("focus"):
            print(f"{sub}Focus: {screen['focus']}")
        if screen.get("needs_review"):
            print(f"{sub}needs-review")
        comps = screen.get("components", [])
        if comps:
            comp_str = ", ".join(f"{c['name']} (#{c['id']})" for c in comps)
            print(f"{sub}Components: {comp_str}")
        if full:
            if screen.get("rationale"):
                print(f"{sub}Rationale: {screen['rationale']}")
            for v in variants:
                sel = "●" if v["file"] == screen.get("selected_file") else " "
                lbl = f"  [{v['label']}]" if v.get("label") else ""
                rat = f"  — {v['rationale']}" if v.get("rationale") else ""
                flg = f"  ⚑ {v.get('flag_reason') or 'flagged'}" if v.get("flag") else ""
                print(f"{sub}{sel} {v['file']}{lbl}{rat}{flg}")
            deltas = db.list_deltas("screen", screen["id"], limit=3)
            if deltas:
                print(f"{sub}Recent changes:")
                for d in deltas:
                    date_str = (d.get("created_at") or "")[:10]
                    reason   = d.get("reason") or d.get("target") or d["type"]
                    outcome  = f"  → {d['outcome']}" if d.get("outcome") else ""
                    print(f"{sub}  {date_str}  {reason}{outcome}")
        for child in by_parent.get(screen["id"], []):
            _print_screen_node(child, indent + 1)

    print()
    print(f"SCREENS ({len(screens)})")
    if screens:
        for root in roots:
            _print_screen_node(root, 1)
    else:
        print("  (none)")

    # ---- components ----
    print()
    print(f"COMPONENTS ({len(components)})")
    if components:
        for c in components:
            variants  = c.get("variants", [])
            n_var     = len(variants)
            n_flagged = sum(1 for v in variants if v.get("flag"))
            file_str  = f"  ● {c['selected_file']}" if c.get("selected_file") else ""
            var_str   = ""
            if n_var:
                var_str = f"  ({n_var} variant{'s' if n_var != 1 else ''}"
                var_str += f", {n_flagged} flagged" if n_flagged else ""
                var_str += ")"
            used_in = c.get("used_in", [])
            spec_tag = "  [speculative]" if len(used_in) < 2 else ""
            print(f"  #{c['id']}  [{c['status']}]  {c['name']}{file_str}{var_str}{spec_tag}")
            if c.get("hypothesis"):
                print(f"      Hypothesis: {c['hypothesis']}")
            if c.get("focus"):
                print(f"      Focus: {c['focus']}")
            if c.get("needs_review"):
                print(f"      needs-review")
            if used_in:
                used_str = ", ".join(f"{s['name']} (#{s['id']})" for s in used_in)
                print(f"      Used in: {used_str}")
            if full:
                if c.get("rationale"):
                    print(f"      Rationale: {c['rationale']}")
                for v in variants:
                    sel = "●" if v["file"] == c.get("selected_file") else " "
                    lbl = f"  [{v['label']}]" if v.get("label") else ""
                    rat = f"  — {v['rationale']}" if v.get("rationale") else ""
                    flg = f"  ⚑ {v.get('flag_reason') or 'flagged'}" if v.get("flag") else ""
                    print(f"      {sel} {v['file']}{lbl}{rat}{flg}")
                deltas = db.list_deltas("component", c["id"], limit=3)
                if deltas:
                    print(f"      Recent changes:")
                    for d in deltas:
                        date_str = (d.get("created_at") or "")[:10]
                        reason   = d.get("reason") or d.get("target") or d["type"]
                        outcome  = f"  → {d['outcome']}" if d.get("outcome") else ""
                        print(f"          {date_str}  {reason}{outcome}")
    else:
        print("  (none)")

    # ---- flows ----
    print()
    print(f"FLOWS ({len(flows)})")
    if flows:
        for f in flows:
            variants  = f.get("variants", [])
            n_var     = len(variants)
            n_flagged = sum(1 for v in variants if v.get("flag"))
            file_str  = f"  ● {f['selected_file']}" if f.get("selected_file") else ""
            var_str   = ""
            if n_var:
                var_str = f"  ({n_var} variant{'s' if n_var != 1 else ''}"
                var_str += f", {n_flagged} flagged" if n_flagged else ""
                var_str += ")"
            print(f"  #{f['id']}  [{f['status']}]  {f['name']}{file_str}{var_str}")
            if f.get("hypothesis"):
                print(f"      Hypothesis: {f['hypothesis']}")
            if f.get("focus"):
                print(f"      Focus: {f['focus']}")
            if f.get("needs_review"):
                print(f"      needs-review")
            linked = f.get("screens", [])
            if linked:
                print(f"      Screens: {' → '.join(s['name'] for s in linked)}")
            if full:
                if f.get("rationale"):
                    print(f"      Rationale: {f['rationale']}")
                for v in variants:
                    sel = "●" if v["file"] == f.get("selected_file") else " "
                    lbl = f"  [{v['label']}]" if v.get("label") else ""
                    rat = f"  — {v['rationale']}" if v.get("rationale") else ""
                    flg = f"  ⚑ {v.get('flag_reason') or 'flagged'}" if v.get("flag") else ""
                    print(f"      {sel} {v['file']}{lbl}{rat}{flg}")
                deltas = db.list_deltas("flow", f["id"], limit=3)
                if deltas:
                    print(f"      Recent changes:")
                    for d in deltas:
                        date_str = (d.get("created_at") or "")[:10]
                        reason   = d.get("reason") or d.get("target") or d["type"]
                        outcome  = f"  → {d['outcome']}" if d.get("outcome") else ""
                        print(f"          {date_str}  {reason}{outcome}")
    else:
        print("  (none)")


def _cmd_explain(args: argparse.Namespace) -> None:
    entity_type = args.type
    entity_id   = args.id

    if entity_type == "screen":
        item = db.get_screen(entity_id)
    elif entity_type == "component":
        item = db.get_component(entity_id)
    else:
        item = db.get_flow(entity_id)

    if item is None:
        print(f"Error: {entity_type} #{entity_id} not found.")
        sys.exit(1)

    label = entity_type.capitalize()
    print(f"=== EXPLAIN: {label} #{item['id']} — {item['name']} ===")
    print(f"Status:     {item['status']}")
    print(f"Selected:   {item.get('selected_file') or '(none)'}")
    print(f"Hypothesis: {item.get('hypothesis') or '(not set)'}")
    print(f"Focus:      {item.get('focus') or '(not set)'}")

    deltas = db.list_deltas(entity_type, entity_id)

    print()
    print("WHAT WE'VE TRIED:")
    if deltas:
        for delta in reversed(deltas):
            date_str = (delta.get("created_at") or "")[:10]
            target   = delta.get("target") or ""
            from_val = delta.get("from_val") or ""
            to_val   = delta.get("to_val") or ""
            reason   = delta.get("reason") or ""
            outcome  = delta.get("outcome") or "(none)"
            change_str = f"{from_val!r} → {to_val!r}" if (from_val or to_val) else ""
            target_str = f"{target}: {change_str}" if change_str else target
            print(f"  #{delta['id']}  {date_str}  {delta['type']}  {target_str}")
            if reason:
                print(f"        Reason:  {reason}")
            print(f"        Outcome: {outcome}")
    else:
        print("  (none)")

    variants = item.get("variants", [])
    print()
    print("VARIANTS:")
    if variants:
        for v in variants:
            selected_marker = "●" if v["file"] == item.get("selected_file") else " "
            label_str    = f" [{v['label']}]" if v.get("label") else ""
            rationale_str = f"  rationale: {v['rationale']}" if v.get("rationale") else ""
            flag_str = f"  [needs-revision: {v.get('flag_reason') or ''}]" if v.get("flag") else ""
            print(f"  {selected_marker} {v['file']}{label_str}{rationale_str}{flag_str}")
    else:
        print("  (none)")

    open_questions = [d for d in deltas if not d.get("outcome")]
    print()
    print("OPEN QUESTIONS:")
    if open_questions:
        for delta in open_questions:
            target = delta.get("target") or ""
            print(f"  #{delta['id']}  {delta['type']}  {target} — no outcome recorded")
    else:
        print("  (none)")


def _cmd_suggest(args: argparse.Namespace) -> None:
    entity_type = args.type
    entity_id   = args.id

    if entity_type == "screen":
        item = db.get_screen(entity_id)
    elif entity_type == "component":
        item = db.get_component(entity_id)
    else:
        item = db.get_flow(entity_id)

    if item is None:
        print(f"Error: {entity_type} #{entity_id} not found.")
        sys.exit(1)

    label   = entity_type.capitalize()
    deltas  = db.list_deltas(entity_type, entity_id, limit=5)
    variants = item.get("variants", [])

    print(f"=== SUGGEST PROMPT: {label} #{item['id']} — {item['name']} ===")
    print()
    print("Paste this into your Claude conversation:")
    print()
    print("---")
    print(f"Current {entity_type}: {item['name']} (#{item['id']})")
    print(f"Status: {item['status']}")
    print(f"Hypothesis: {item.get('hypothesis') or '(not set)'}")
    print(f"Focus: {item.get('focus') or '(not set)'}")

    if deltas:
        print()
        print("Recent changes:")
        for delta in reversed(deltas):
            target   = delta.get("target") or ""
            from_val = delta.get("from_val") or ""
            to_val   = delta.get("to_val") or ""
            outcome  = delta.get("outcome") or "no outcome"
            change_str = f"{from_val!r} → {to_val!r}" if (from_val or to_val) else ""
            target_str = f"{target}: {change_str}" if change_str else target
            print(f"  - {delta['type']} on {target_str} (outcome: {outcome})")

    if variants:
        print()
        variant_parts = []
        for v in variants:
            is_selected = v["file"] == item.get("selected_file")
            suffix = " (selected)" if is_selected else ""
            flag   = f" (needs-revision)" if v.get("flag") else ""
            variant_parts.append(f"{v['file']}{suffix}{flag}")
        print(f"Variants: {', '.join(variant_parts)}")

    print()
    if item.get("hypothesis") or item.get("focus"):
        print("CONSTRAINTS (treat these as hard limits, not soft preferences):")
        if item.get("hypothesis"):
            print(f"  Hypothesis: {item['hypothesis']}")
        if item.get("focus"):
            print(f"  Focus: {item['focus']} — only suggest changes within this area")
        print()
    print("Please suggest 1–3 focused next changes to test. Each suggestion must:")
    print("1. Stay within the focus area above (if set)")
    print("2. Directly test or advance the hypothesis above (if set)")
    print("3. Specify: what to change (element + specific change)")
    print("4. Specify: what outcome would confirm or deny the hypothesis")
    print("---")


def _cmd_log(args: argparse.Namespace) -> None:
    entity_type = args.type
    entity_id   = args.id
    message     = args.message
    variant_id  = getattr(args, "variant_id", None)

    if entity_type == "screen":
        item = db.get_screen(entity_id)
    elif entity_type == "component":
        item = db.get_component(entity_id)
    else:
        item = db.get_flow(entity_id)

    if item is None:
        print(f"Error: {entity_type} #{entity_id} not found.")
        sys.exit(1)

    if variant_id is not None:
        variants = item.get("variants", [])
        if not any(v["id"] == variant_id for v in variants):
            print(f"Error: variant #{variant_id} not found on {entity_type} #{entity_id}.")
            sys.exit(1)

    db.add_delta(
        entity_type=entity_type,
        entity_id=entity_id,
        type="other",
        target=None,
        from_val=None,
        to_val=None,
        reason=message,
        variant_id=variant_id,
    )
    if variant_id is not None:
        print(f"Logged on {entity_type} #{entity_id} variant #{variant_id}: {message}")
    else:
        print(f"Logged on {entity_type} #{entity_id}: {message}")


_PID_FILE = Path.home() / ".folio" / "server.pid"


def _cmd_serve(args: argparse.Namespace) -> None:
    import subprocess, signal as _signal

    if getattr(args, "stop", False):
        if not _PID_FILE.exists():
            print("Folio server not running (no PID file).")
            return
        pid = int(_PID_FILE.read_text().strip())
        try:
            os.kill(pid, _signal.SIGTERM)
            _PID_FILE.unlink(missing_ok=True)
            print(f"Stopped Folio server (PID {pid}).")
        except ProcessLookupError:
            _PID_FILE.unlink(missing_ok=True)
            print(f"Process {pid} not found — PID file removed.")
        return

    if getattr(args, "restart", False) and _PID_FILE.exists():
        try:
            pid = int(_PID_FILE.read_text().strip())
            os.kill(pid, _signal.SIGTERM)
            for _ in range(30):
                import time as _time
                _time.sleep(0.1)
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
        except (ProcessLookupError, ValueError):
            pass
        _PID_FILE.unlink(missing_ok=True)

    if _PID_FILE.exists():
        pid = _PID_FILE.read_text().strip()
        print(f"Folio server already running (PID {pid}). Use --stop to stop it.")
        return

    server_path = str(Path.home() / ".folio" / "lib" / "server.py")
    port = getattr(args, "port", 5000)
    os.environ.setdefault("FOLIO_PORT", str(port))
    subprocess.run([sys.executable, server_path])


def _cmd_add_variant(args: argparse.Namespace) -> None:
    import shutil as _shutil

    item_type = args.type
    item_id   = args.id
    label           = getattr(args, "label", None)
    ui_description  = getattr(args, "ui_description", None)
    notes           = getattr(args, "notes", None)
    rationale       = getattr(args, "rationale", None)

    assert item_type in {"screen", "component", "flow"}, f"Unknown type: {item_type!r}"

    src = Path(args.file)
    if src.is_absolute() or src.parent != Path("."):
        # Path has directory components — copy the file into DESIGN_DIR.
        if not src.exists():
            print(f"Error: file not found: {src}")
            sys.exit(1)
        destination = db.DESIGN_DIR / src.name
        if not destination.exists():
            db.DESIGN_DIR.mkdir(parents=True, exist_ok=True)
            _shutil.copy2(src, destination)
            print(f"Copied {src.name} into .folio/design/")
        file = src.name
    else:
        file = args.file
        if not (db.DESIGN_DIR / file).exists():
            print(
                f"Warning: file not found in .folio/design/ — "
                "dashboard will 404. Copy the file there first."
            )

    if item_type == "screen":
        variant = db.create_screen_variant(
            screen_id=item_id, file=file,
            label=label, ui_description=ui_description, notes=notes, rationale=rationale,
        )
    elif item_type == "component":
        variant = db.create_component_variant(
            component_id=item_id, file=file,
            label=label, ui_description=ui_description, notes=notes, rationale=rationale,
        )
    else:
        variant = db.create_flow_variant(
            flow_id=item_id, file=file,
            label=label, ui_description=ui_description, notes=notes, rationale=rationale,
        )

    print(f"Created {item_type} variant #{variant['id']}: {variant['file']}")


# ---------------------------------------------------------------------------
# Screen subcommand handlers
# ---------------------------------------------------------------------------

def _dispatch_screens(args: argparse.Namespace) -> None:
    command = args.command

    if command == "list":
        screens = db.list_screens()
        print(f"=== SCREENS ({len(screens)}) ===")
        for screen in screens:
            _print_screen_summary(screen)

    elif command == "add":
        screen = db.create_screen(
            name=args.name,
            description=getattr(args, "description", None),
            usage=getattr(args, "usage", None),
        )
        print(f"Created screen #{screen['id']}: {screen['name']}")
        first_file = getattr(args, "file", None)
        if first_file:
            variant = db.create_screen_variant(screen_id=screen["id"], file=first_file, label="v1")
            db.select_screen_variant(variant["id"])
            print(f"  Added variant #{variant['id']}: {first_file}")
            print(f"  Selected: {first_file}")

    elif command == "show":
        screen = db.get_screen(args.id)
        if screen is None:
            print(f"Error: Screen {args.id} not found.")
            sys.exit(1)
        _print_screen_detail(screen)

    elif command == "set-status":
        screen = db.update_screen(args.id, status=args.status)
        if screen is None:
            print(f"Error: Screen {args.id} not found.")
            sys.exit(1)
        print(f"Screen #{screen['id']} status → {screen['status']}")

    elif command == "set-rationale":
        screen = db.update_screen(args.id, rationale=args.rationale)
        if screen is None:
            print(f"Error: Screen {args.id} not found.")
            sys.exit(1)
        print(f"Screen #{screen['id']} rationale updated.")

    elif command == "set-parent":
        screen = db.set_screen_parent(args.id, args.parent)
        if screen is None:
            print(f"Error: Screen {args.id} not found.")
            sys.exit(1)
        if args.parent is None:
            print(f"Screen #{screen['id']} parent cleared.")
        else:
            print(f"Screen #{screen['id']} parent → #{args.parent}")

    elif command == "select-variant":
        variant_id = args.variant_id
        if variant_id is None:
            if args.id is None or args.file is None:
                print("Error: Provide --variant-id or both --id and --file.")
                sys.exit(1)
            entity = db.get_screen(args.id)
            if entity is None:
                print(f"Error: Screen {args.id} not found.")
                sys.exit(1)
            match = next((v for v in entity.get("variants", []) if v["file"] == args.file), None)
            if match is None:
                print(f"Error: No variant with file '{args.file}' on screen #{args.id}.")
                sys.exit(1)
            variant_id = match["id"]
        screen = db.select_screen_variant(variant_id)
        if screen is None:
            print(f"Error: Screen variant {variant_id} not found.")
            sys.exit(1)
        print(f"Selected variant {variant_id} on screen #{screen['id']}: {screen['selected_file']}")

    elif command == "set-variant-rationale":
        v = db.update_screen_variant(args.variant_id, rationale=args.rationale)
        if v is None:
            print(f"Error: Screen variant {args.variant_id} not found.")
            sys.exit(1)
        print(f"Screen variant #{v['id']} rationale updated.")

    elif command == "flag-variant":
        v = db.update_screen_variant(
            args.variant_id, flag="needs-revision", flag_reason=getattr(args, "reason", None),
        )
        if v is None:
            print(f"Error: Screen variant {args.variant_id} not found.")
            sys.exit(1)
        print(f"Screen variant #{v['id']} flagged: needs-revision")

    elif command == "unflag-variant":
        v = db.update_screen_variant(args.variant_id, flag=None, flag_reason=None)
        if v is None:
            print(f"Error: Screen variant {args.variant_id} not found.")
            sys.exit(1)
        print(f"Screen variant #{v['id']} unflagged.")

    elif command == "change":
        prior = db.list_deltas("screen", args.id)
        matching = [d for d in prior if d.get("target") == args.target]
        if matching:
            print(
                f"Warning: target \"{args.target}\" was changed {len(matching)} "
                f"time(s) before — check for regressions."
            )
        db.add_delta(
            entity_type="screen",
            entity_id=args.id,
            type=args.type,
            target=args.target,
            from_val=getattr(args, "from_val", None),
            to_val=getattr(args, "to_val", None),
            reason=getattr(args, "reason", None),
        )
        print(f"Recorded change on screen #{args.id}: {args.type} on \"{args.target}\"")

    elif command == "set-hypothesis":
        screen = db.update_screen(args.id, hypothesis=args.hypothesis)
        if screen is None:
            print(f"Error: Screen {args.id} not found.")
            sys.exit(1)
        print(f"Screen #{args.id} hypothesis updated.")

    elif command == "set-focus":
        screen = db.update_screen(args.id, focus=args.area)
        if screen is None:
            print(f"Error: Screen {args.id} not found.")
            sys.exit(1)
        print(f"Screen #{args.id} focus updated.")

    elif command == "needs-review":
        screen = db.update_screen(args.id, needs_review=1)
        if screen is None:
            print(f"Error: Screen {args.id} not found.")
            sys.exit(1)
        print(f"Screen #{args.id} marked for review.")

    elif command == "clear-needs-review":
        screen = db.update_screen(args.id, needs_review=0)
        if screen is None:
            print(f"Error: Screen {args.id} not found.")
            sys.exit(1)
        print(f"Screen #{args.id} review cleared.")

    elif command == "record-outcome":
        delta = db.update_delta_outcome(args.delta_id, args.outcome)
        if delta is None:
            print(f"Error: Delta {args.delta_id} not found.")
            sys.exit(1)
        print(f"Delta #{args.delta_id} outcome recorded.")

    elif command == "rename":
        screen = db.update_screen(args.id, name=args.name)
        if screen is None:
            print(f"Error: Screen {args.id} not found.")
            sys.exit(1)
        print(f"Screen #{screen['id']} renamed to: {screen['name']}")

    elif command == "delete":
        deleted = db.delete_screen(args.id)
        if not deleted:
            print(f"Error: Screen {args.id} not found.")
            sys.exit(1)
        print(f"Screen #{args.id} deleted.")

    elif command == "set-description":
        screen = db.update_screen(args.id, description=args.description)
        if screen is None:
            print(f"Error: Screen {args.id} not found.")
            sys.exit(1)
        print(f"Screen #{screen['id']} description updated.")

    elif command == "remove-variant":
        deleted = db.delete_screen_variant(args.variant_id)
        if not deleted:
            print(f"Error: Screen variant {args.variant_id} not found.")
            sys.exit(1)
        print(f"Screen variant #{args.variant_id} removed.")

    elif command == "move-variant":
        try:
            v = db.move_screen_variant(args.variant_id, args.to_screen)
        except ValueError as exc:
            print(f"Error: {exc}")
            sys.exit(1)
        if v is None:
            print(f"Error: Screen variant {args.variant_id} not found.")
            sys.exit(1)
        print(f"Screen variant #{v['id']} moved to screen #{args.to_screen}.")

    else:
        print(f"Error: Unknown screens command: {command!r}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Component subcommand handlers
# ---------------------------------------------------------------------------

def _dispatch_components(args: argparse.Namespace) -> None:
    command = args.command

    if command == "list":
        components = db.list_components()
        print(f"=== COMPONENTS ({len(components)}) ===")
        for component in components:
            _print_component_summary(component)

    elif command == "add":
        if not getattr(args, "force", False):
            screens = db.list_screens()
            finalized = [s for s in screens if s.get("status") in ("approved", "finalised")]
            if len(finalized) < 2:
                print(
                    "Warning: fewer than 2 approved/finalised screens exist.\n"
                    "Components should be extracted only when the same UI is confirmed in 2+ screens.\n"
                    "Use --force to register anyway."
                )
                sys.exit(1)
        component = db.create_component(
            name=args.name,
            description=getattr(args, "description", None),
            usage=getattr(args, "usage", None),
        )
        print(f"Created component #{component['id']}: {component['name']}")
        first_file = getattr(args, "file", None)
        if first_file:
            variant = db.create_component_variant(
                component_id=component["id"], file=first_file, label="v1"
            )
            db.select_component_variant(variant["id"])
            print(f"  Added variant #{variant['id']}: {first_file}")
            print(f"  Selected: {first_file}")

    elif command == "show":
        component = db.get_component(args.id)
        if component is None:
            print(f"Error: Component {args.id} not found.")
            sys.exit(1)
        _print_component_detail(component)

    elif command == "set-status":
        component = db.update_component(args.id, status=args.status)
        if component is None:
            print(f"Error: Component {args.id} not found.")
            sys.exit(1)
        print(f"Component #{component['id']} status → {component['status']}")

    elif command == "set-rationale":
        component = db.update_component(args.id, rationale=args.rationale)
        if component is None:
            print(f"Error: Component {args.id} not found.")
            sys.exit(1)
        print(f"Component #{component['id']} rationale updated.")

    elif command == "link":
        db.link_component_screen(component_id=args.id, screen_id=args.screen)
        print(f"Linked component #{args.id} to screen #{args.screen}.")

    elif command == "unlink":
        removed = db.unlink_component_screen(component_id=args.id, screen_id=args.screen)
        if not removed:
            print(f"Error: Link between component #{args.id} and screen #{args.screen} not found.")
            sys.exit(1)
        print(f"Unlinked component #{args.id} from screen #{args.screen}.")

    elif command == "select-variant":
        variant_id = args.variant_id
        if variant_id is None:
            if args.id is None or args.file is None:
                print("Error: Provide --variant-id or both --id and --file.")
                sys.exit(1)
            entity = db.get_component(args.id)
            if entity is None:
                print(f"Error: Component {args.id} not found.")
                sys.exit(1)
            match = next((v for v in entity.get("variants", []) if v["file"] == args.file), None)
            if match is None:
                print(f"Error: No variant with file '{args.file}' on component #{args.id}.")
                sys.exit(1)
            variant_id = match["id"]
        component = db.select_component_variant(variant_id)
        if component is None:
            print(f"Error: Component variant {variant_id} not found.")
            sys.exit(1)
        print(
            f"Selected variant {variant_id} on component "
            f"#{component['id']}: {component['selected_file']}"
        )

    elif command == "set-variant-rationale":
        v = db.update_component_variant(args.variant_id, rationale=args.rationale)
        if v is None:
            print(f"Error: Component variant {args.variant_id} not found.")
            sys.exit(1)
        print(f"Component variant #{v['id']} rationale updated.")

    elif command == "flag-variant":
        v = db.update_component_variant(
            args.variant_id, flag="needs-revision", flag_reason=getattr(args, "reason", None),
        )
        if v is None:
            print(f"Error: Component variant {args.variant_id} not found.")
            sys.exit(1)
        print(f"Component variant #{v['id']} flagged: needs-revision")

    elif command == "unflag-variant":
        v = db.update_component_variant(args.variant_id, flag=None, flag_reason=None)
        if v is None:
            print(f"Error: Component variant {args.variant_id} not found.")
            sys.exit(1)
        print(f"Component variant #{v['id']} unflagged.")

    elif command == "change":
        prior = db.list_deltas("component", args.id)
        matching = [d for d in prior if d.get("target") == args.target]
        if matching:
            print(
                f"Warning: target \"{args.target}\" was changed {len(matching)} "
                f"time(s) before — check for regressions."
            )
        db.add_delta(
            entity_type="component",
            entity_id=args.id,
            type=args.type,
            target=args.target,
            from_val=getattr(args, "from_val", None),
            to_val=getattr(args, "to_val", None),
            reason=getattr(args, "reason", None),
        )
        print(f"Recorded change on component #{args.id}: {args.type} on \"{args.target}\"")

    elif command == "set-hypothesis":
        component = db.update_component(args.id, hypothesis=args.hypothesis)
        if component is None:
            print(f"Error: Component {args.id} not found.")
            sys.exit(1)
        print(f"Component #{args.id} hypothesis updated.")

    elif command == "set-focus":
        component = db.update_component(args.id, focus=args.area)
        if component is None:
            print(f"Error: Component {args.id} not found.")
            sys.exit(1)
        print(f"Component #{args.id} focus updated.")

    elif command == "needs-review":
        component = db.update_component(args.id, needs_review=1)
        if component is None:
            print(f"Error: Component {args.id} not found.")
            sys.exit(1)
        print(f"Component #{args.id} marked for review.")

    elif command == "clear-needs-review":
        component = db.update_component(args.id, needs_review=0)
        if component is None:
            print(f"Error: Component {args.id} not found.")
            sys.exit(1)
        print(f"Component #{args.id} review cleared.")

    elif command == "record-outcome":
        delta = db.update_delta_outcome(args.delta_id, args.outcome)
        if delta is None:
            print(f"Error: Delta {args.delta_id} not found.")
            sys.exit(1)
        print(f"Delta #{args.delta_id} outcome recorded.")

    else:
        print(f"Error: Unknown components command: {command!r}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Flow subcommand handlers
# ---------------------------------------------------------------------------

def _dispatch_flows(args: argparse.Namespace) -> None:
    command = args.command

    if command == "list":
        flows = db.list_flows()
        print(f"=== FLOWS ({len(flows)}) ===")
        for flow in flows:
            _print_flow_summary(flow)

    elif command == "add":
        flow = db.create_flow(
            name=args.name,
            description=getattr(args, "description", None),
            usage=getattr(args, "usage", None),
        )
        print(f"Created flow #{flow['id']}: {flow['name']}")
        first_file = getattr(args, "file", None)
        if first_file:
            variant = db.create_flow_variant(flow_id=flow["id"], file=first_file, label="v1")
            db.select_flow_variant(variant["id"])
            print(f"  Added variant #{variant['id']}: {first_file}")
            print(f"  Selected: {first_file}")

    elif command == "show":
        flow = db.get_flow(args.id)
        if flow is None:
            print(f"Error: Flow {args.id} not found.")
            sys.exit(1)
        _print_flow_detail(flow)

    elif command == "set-status":
        flow = db.update_flow(args.id, status=args.status)
        if flow is None:
            print(f"Error: Flow {args.id} not found.")
            sys.exit(1)
        print(f"Flow #{flow['id']} status → {flow['status']}")

    elif command == "set-rationale":
        flow = db.update_flow(args.id, rationale=args.rationale)
        if flow is None:
            print(f"Error: Flow {args.id} not found.")
            sys.exit(1)
        print(f"Flow #{flow['id']} rationale updated.")

    elif command == "link":
        db.link_flow_screen(flow_id=args.id, screen_id=args.screen)
        print(f"Linked flow #{args.id} to screen #{args.screen}.")

    elif command == "unlink":
        removed = db.unlink_flow_screen(flow_id=args.id, screen_id=args.screen)
        if not removed:
            print(f"Error: Link between flow #{args.id} and screen #{args.screen} not found.")
            sys.exit(1)
        print(f"Unlinked flow #{args.id} from screen #{args.screen}.")

    elif command == "select-variant":
        variant_id = args.variant_id
        if variant_id is None:
            if args.id is None or args.file is None:
                print("Error: Provide --variant-id or both --id and --file.")
                sys.exit(1)
            entity = db.get_flow(args.id)
            if entity is None:
                print(f"Error: Flow {args.id} not found.")
                sys.exit(1)
            match = next((v for v in entity.get("variants", []) if v["file"] == args.file), None)
            if match is None:
                print(f"Error: No variant with file '{args.file}' on flow #{args.id}.")
                sys.exit(1)
            variant_id = match["id"]
        flow = db.select_flow_variant(variant_id)
        if flow is None:
            print(f"Error: Flow variant {variant_id} not found.")
            sys.exit(1)
        print(
            f"Selected variant {variant_id} on flow "
            f"#{flow['id']}: {flow['selected_file']}"
        )

    elif command == "set-variant-rationale":
        v = db.update_flow_variant(args.variant_id, rationale=args.rationale)
        if v is None:
            print(f"Error: Flow variant {args.variant_id} not found.")
            sys.exit(1)
        print(f"Flow variant #{v['id']} rationale updated.")

    elif command == "flag-variant":
        v = db.update_flow_variant(
            args.variant_id, flag="needs-revision", flag_reason=getattr(args, "reason", None),
        )
        if v is None:
            print(f"Error: Flow variant {args.variant_id} not found.")
            sys.exit(1)
        print(f"Flow variant #{v['id']} flagged: needs-revision")

    elif command == "unflag-variant":
        v = db.update_flow_variant(args.variant_id, flag=None, flag_reason=None)
        if v is None:
            print(f"Error: Flow variant {args.variant_id} not found.")
            sys.exit(1)
        print(f"Flow variant #{v['id']} unflagged.")

    elif command == "change":
        prior = db.list_deltas("flow", args.id)
        matching = [d for d in prior if d.get("target") == args.target]
        if matching:
            print(
                f"Warning: target \"{args.target}\" was changed {len(matching)} "
                f"time(s) before — check for regressions."
            )
        db.add_delta(
            entity_type="flow",
            entity_id=args.id,
            type=args.type,
            target=args.target,
            from_val=getattr(args, "from_val", None),
            to_val=getattr(args, "to_val", None),
            reason=getattr(args, "reason", None),
        )
        print(f"Recorded change on flow #{args.id}: {args.type} on \"{args.target}\"")

    elif command == "set-hypothesis":
        flow = db.update_flow(args.id, hypothesis=args.hypothesis)
        if flow is None:
            print(f"Error: Flow {args.id} not found.")
            sys.exit(1)
        print(f"Flow #{args.id} hypothesis updated.")

    elif command == "set-focus":
        flow = db.update_flow(args.id, focus=args.area)
        if flow is None:
            print(f"Error: Flow {args.id} not found.")
            sys.exit(1)
        print(f"Flow #{args.id} focus updated.")

    elif command == "needs-review":
        flow = db.update_flow(args.id, needs_review=1)
        if flow is None:
            print(f"Error: Flow {args.id} not found.")
            sys.exit(1)
        print(f"Flow #{args.id} marked for review.")

    elif command == "clear-needs-review":
        flow = db.update_flow(args.id, needs_review=0)
        if flow is None:
            print(f"Error: Flow {args.id} not found.")
            sys.exit(1)
        print(f"Flow #{args.id} review cleared.")

    elif command == "record-outcome":
        delta = db.update_delta_outcome(args.delta_id, args.outcome)
        if delta is None:
            print(f"Error: Delta {args.delta_id} not found.")
            sys.exit(1)
        print(f"Delta #{args.delta_id} outcome recorded.")

    else:
        print(f"Error: Unknown flows command: {command!r}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

def _cmd_update(_args: argparse.Namespace) -> None:
    import subprocess
    base = "https://raw.githubusercontent.com/Suanlianmang/folio/main"

    print("Updating folio CLI...")
    r = subprocess.run(f"curl -fsSL {base}/get.sh | bash", shell=True)
    if r.returncode != 0:
        print("Error: CLI update failed.")
        sys.exit(r.returncode)

    print("Updating folio skill...")
    r = subprocess.run(f"curl -fsSL {base}/skill-install.sh | bash", shell=True)
    if r.returncode != 0:
        print("Error: skill update failed.")
        sys.exit(r.returncode)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="folio",
        description="Folio design exploration tracker CLI",
    )
    sub = parser.add_subparsers(dest="group", required=True)

    # --- screens ---
    p_screens  = sub.add_parser("screens", help="Screen commands")
    screens_sub = p_screens.add_subparsers(dest="command", required=True)

    screens_sub.add_parser("list", help="List all screens")

    p = screens_sub.add_parser("add", help="Create a new screen")
    p.add_argument("--name", required=True)
    p.add_argument("--description")
    p.add_argument("--usage")
    p.add_argument("--file", help="First variant file (optional)")

    p = screens_sub.add_parser("show", help="Show full screen detail")
    p.add_argument("--id", type=int, required=True)

    p = screens_sub.add_parser("set-status", help="Update screen status")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--status", required=True, choices=["exploring", "approved", "finalised"])

    p = screens_sub.add_parser("set-rationale", help="Set screen rationale")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--rationale", required=True)

    p = screens_sub.add_parser("set-parent", help="Set or clear screen parent")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--parent", type=int, default=None, help="Parent screen ID (omit to clear)")

    p = screens_sub.add_parser("select-variant", help="Set variant as selected on parent screen")
    p.add_argument("--variant-id", type=int, default=None, dest="variant_id")
    p.add_argument("--id", type=int, default=None, help="Entity ID (use with --file)")
    p.add_argument("--file", default=None, help="Variant filename (use with --id)")

    p = screens_sub.add_parser("set-variant-rationale", help="Set rationale on a screen variant")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")
    p.add_argument("--rationale", required=True)

    p = screens_sub.add_parser("flag-variant", help="Flag a screen variant as needs-revision")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")
    p.add_argument("--reason", default=None)

    p = screens_sub.add_parser("unflag-variant", help="Clear flag on a screen variant")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")

    p = screens_sub.add_parser("change", help="Record a design change delta on a screen")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--type", required=True, choices=["layout", "copy", "color", "spacing", "interaction", "other"])
    p.add_argument("--target", required=True)
    p.add_argument("--from", dest="from_val", default=None)
    p.add_argument("--to", dest="to_val", default=None)
    p.add_argument("--reason", default=None)

    p = screens_sub.add_parser("set-hypothesis", help="Set working hypothesis on a screen")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--hypothesis", required=True)

    p = screens_sub.add_parser("set-focus", help="Set attention focus area on a screen")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--area", required=True)

    p = screens_sub.add_parser("needs-review", help="Mark screen for human review")
    p.add_argument("--id", type=int, required=True)

    p = screens_sub.add_parser("clear-needs-review", help="Clear review flag on a screen")
    p.add_argument("--id", type=int, required=True)

    p = screens_sub.add_parser("record-outcome", help="Record outcome on a delta")
    p.add_argument("--delta-id", type=int, required=True, dest="delta_id")
    p.add_argument("--outcome", required=True)

    p = screens_sub.add_parser("rename", help="Rename a screen")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--name", required=True)

    p = screens_sub.add_parser("delete", help="Delete a screen and all its variants")
    p.add_argument("--id", type=int, required=True)

    p = screens_sub.add_parser("set-description", help="Update screen description")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--description", required=True)

    p = screens_sub.add_parser("remove-variant", help="Delete a screen variant")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")

    p = screens_sub.add_parser("move-variant", help="Move a screen variant to a different screen")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")
    p.add_argument("--to-screen", type=int, required=True, dest="to_screen")

    # --- components ---
    p_components  = sub.add_parser("components", help="Component commands")
    components_sub = p_components.add_subparsers(dest="command", required=True)

    components_sub.add_parser("list", help="List all components")

    p = components_sub.add_parser("add", help="Create a new component")
    p.add_argument("--name", required=True)
    p.add_argument("--description")
    p.add_argument("--usage")
    p.add_argument("--file", help="First variant file (optional)")
    p.add_argument("--force", action="store_true", help="Skip late-extraction guard")

    p = components_sub.add_parser("show", help="Show full component detail")
    p.add_argument("--id", type=int, required=True)

    p = components_sub.add_parser("set-status", help="Update component status")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--status", required=True, choices=["exploring", "approved", "finalised"])

    p = components_sub.add_parser("set-rationale", help="Set component rationale")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--rationale", required=True)

    p = components_sub.add_parser("link", help="Link component to a screen")
    p.add_argument("--id", type=int, required=True, help="Component ID")
    p.add_argument("--screen", type=int, required=True, help="Screen ID")

    p = components_sub.add_parser("unlink", help="Unlink component from a screen")
    p.add_argument("--id", type=int, required=True, help="Component ID")
    p.add_argument("--screen", type=int, required=True, help="Screen ID")

    p = components_sub.add_parser("select-variant", help="Set variant as selected on parent component")
    p.add_argument("--variant-id", type=int, default=None, dest="variant_id")
    p.add_argument("--id", type=int, default=None, help="Entity ID (use with --file)")
    p.add_argument("--file", default=None, help="Variant filename (use with --id)")

    p = components_sub.add_parser("set-variant-rationale", help="Set rationale on a component variant")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")
    p.add_argument("--rationale", required=True)

    p = components_sub.add_parser("flag-variant", help="Flag a component variant as needs-revision")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")
    p.add_argument("--reason", default=None)

    p = components_sub.add_parser("unflag-variant", help="Clear flag on a component variant")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")

    p = components_sub.add_parser("change", help="Record a design change delta on a component")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--type", required=True, choices=["layout", "copy", "color", "spacing", "interaction", "other"])
    p.add_argument("--target", required=True)
    p.add_argument("--from", dest="from_val", default=None)
    p.add_argument("--to", dest="to_val", default=None)
    p.add_argument("--reason", default=None)

    p = components_sub.add_parser("set-hypothesis", help="Set working hypothesis on a component")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--hypothesis", required=True)

    p = components_sub.add_parser("set-focus", help="Set attention focus area on a component")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--area", required=True)

    p = components_sub.add_parser("needs-review", help="Mark component for human review")
    p.add_argument("--id", type=int, required=True)

    p = components_sub.add_parser("clear-needs-review", help="Clear review flag on a component")
    p.add_argument("--id", type=int, required=True)

    p = components_sub.add_parser("record-outcome", help="Record outcome on a delta")
    p.add_argument("--delta-id", type=int, required=True, dest="delta_id")
    p.add_argument("--outcome", required=True)

    # --- flows ---
    p_flows  = sub.add_parser("flows", help="Flow commands")
    flows_sub = p_flows.add_subparsers(dest="command", required=True)

    flows_sub.add_parser("list", help="List all flows")

    p = flows_sub.add_parser("add", help="Create a new flow")
    p.add_argument("--name", required=True)
    p.add_argument("--description")
    p.add_argument("--usage")
    p.add_argument("--file", help="First variant file (optional)")

    p = flows_sub.add_parser("show", help="Show full flow detail")
    p.add_argument("--id", type=int, required=True)

    p = flows_sub.add_parser("set-status", help="Update flow status")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--status", required=True, choices=["exploring", "approved", "finalised"])

    p = flows_sub.add_parser("set-rationale", help="Set flow rationale")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--rationale", required=True)

    p = flows_sub.add_parser("link", help="Link a screen to a flow")
    p.add_argument("--id", type=int, required=True, help="Flow ID")
    p.add_argument("--screen", type=int, required=True, help="Screen ID")

    p = flows_sub.add_parser("unlink", help="Unlink a screen from a flow")
    p.add_argument("--id", type=int, required=True, help="Flow ID")
    p.add_argument("--screen", type=int, required=True, help="Screen ID")

    p = flows_sub.add_parser("select-variant", help="Set variant as selected on parent flow")
    p.add_argument("--variant-id", type=int, default=None, dest="variant_id")
    p.add_argument("--id", type=int, default=None, help="Entity ID (use with --file)")
    p.add_argument("--file", default=None, help="Variant filename (use with --id)")

    p = flows_sub.add_parser("set-variant-rationale", help="Set rationale on a flow variant")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")
    p.add_argument("--rationale", required=True)

    p = flows_sub.add_parser("flag-variant", help="Flag a flow variant as needs-revision")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")
    p.add_argument("--reason", default=None)

    p = flows_sub.add_parser("unflag-variant", help="Clear flag on a flow variant")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")

    p = flows_sub.add_parser("change", help="Record a design change delta on a flow")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--type", required=True, choices=["layout", "copy", "color", "spacing", "interaction", "other"])
    p.add_argument("--target", required=True)
    p.add_argument("--from", dest="from_val", default=None)
    p.add_argument("--to", dest="to_val", default=None)
    p.add_argument("--reason", default=None)

    p = flows_sub.add_parser("set-hypothesis", help="Set working hypothesis on a flow")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--hypothesis", required=True)

    p = flows_sub.add_parser("set-focus", help="Set attention focus area on a flow")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--area", required=True)

    p = flows_sub.add_parser("needs-review", help="Mark flow for human review")
    p.add_argument("--id", type=int, required=True)

    p = flows_sub.add_parser("clear-needs-review", help="Clear review flag on a flow")
    p.add_argument("--id", type=int, required=True)

    p = flows_sub.add_parser("record-outcome", help="Record outcome on a delta")
    p.add_argument("--delta-id", type=int, required=True, dest="delta_id")
    p.add_argument("--outcome", required=True)

    # --- top-level flat commands ---
    sub.add_parser("init", help="Init DB, copy system.md, seed from design/")
    sub.add_parser("sync-system", help="Write decisions table to system.md")
    sub.add_parser("update", help="Update folio CLI to latest version")

    p_serve = sub.add_parser("serve", help="Start the dashboard server")
    p_serve.add_argument("--port", type=int, default=7842)
    p_serve.add_argument("--stop", action="store_true", help="Stop the running server")
    p_serve.add_argument("--restart", action="store_true", help="Stop running server and restart")

    p_av = sub.add_parser("add-variant", help="Add a variant to any item type")
    p_av.add_argument("--type", required=True, choices=["screen", "component", "flow"])
    p_av.add_argument("--id", type=int, required=True)
    p_av.add_argument("--file", required=True)
    p_av.add_argument("--label")
    p_av.add_argument("--ui-description", dest="ui_description")
    p_av.add_argument("--notes")
    p_av.add_argument("--rationale", default=None)

    p_sc = sub.add_parser("screenshot", help="Screenshot the selected file for an item")
    p_sc.add_argument("--type", required=True, choices=["screen", "component", "flow"])
    p_sc.add_argument("--id", type=int, required=True)
    p_sc.add_argument("--width",  type=int, default=1280)
    p_sc.add_argument("--height", type=int, default=800)
    p_sc.add_argument("--js", dest="js", default=None,
                      help="JS to execute before capture (server must be running)")
    p_sc.add_argument("--class", dest="classes", action="append", default=[],
                      metavar="SELECTOR:CLASS",
                      help="Add class to element before capture, e.g. .list-pane:select-mode (repeatable)")

    p_ctx = sub.add_parser("context", help="Show context for a screen/component/flow")
    p_ctx.add_argument("--type", required=True, choices=["screen", "component", "flow"])
    p_ctx.add_argument("--id", type=int, required=True)

    p_tree = sub.add_parser("tree", help="Show project tree")
    p_tree.add_argument("--full", action="store_true", help="Include rationale, variants, and recent changes per item")

    p_exp = sub.add_parser("explain", help="Show reorientation doc for a screen/component/flow")
    p_exp.add_argument("--type", required=True, choices=["screen", "component", "flow"])
    p_exp.add_argument("--id", type=int, required=True)

    p_sug = sub.add_parser("suggest", help="Generate a Claude suggestion prompt for an item")
    p_sug.add_argument("--type", required=True, choices=["screen", "component", "flow"])
    p_sug.add_argument("--id", type=int, required=True)

    p_log = sub.add_parser("log", help="Log a one-line iteration note on a screen/component/flow")
    p_log.add_argument("--type", required=True, choices=["screen", "component", "flow"])
    p_log.add_argument("--id", type=int, required=True)
    p_log.add_argument("--variant-id", type=int, default=None, dest="variant_id")
    p_log.add_argument("message", help="What changed or what you're testing")

    return parser


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------

def main() -> None:
    parser = _build_parser()
    args   = parser.parse_args()

    try:
        if args.group == "screens":
            _dispatch_screens(args)
        elif args.group == "components":
            _dispatch_components(args)
        elif args.group == "flows":
            _dispatch_flows(args)
        elif args.group == "init":
            _cmd_init(args)
        elif args.group == "sync-system":
            _cmd_sync_system(args)
        elif args.group == "serve":
            _cmd_serve(args)
        elif args.group == "add-variant":
            _cmd_add_variant(args)
        elif args.group == "screenshot":
            _cmd_screenshot(args)
        elif args.group == "update":
            _cmd_update(args)
        elif args.group == "context":
            _cmd_context(args)
        elif args.group == "tree":
            _cmd_tree(args)
        elif args.group == "explain":
            _cmd_explain(args)
        elif args.group == "suggest":
            _cmd_suggest(args)
        elif args.group == "log":
            _cmd_log(args)
        else:
            print(f"Error: Unknown group: {args.group!r}")
            sys.exit(1)
    except FileNotFoundError as exc:
        print(f"Error: {exc} — run 'init' first.")
        sys.exit(1)
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
    except AssertionError as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
