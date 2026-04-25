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
    print(f"  #{component['id']} [component] {component['name']} ({component['status']})")
    used_in = component.get("used_in", [])
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

    if db.DESIGN_DIR.is_dir():
        count = db.seed_from_design()
        if count > 0:
            print(f"Seeded {count} screen(s) from design/.")
        else:
            print("design/ found but no HTML files to seed.")
    else:
        print("No design/ directory found — skipping seed.")


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

    cmd = [
        chrome,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        f"--window-size={width},{height}",
        f"--screenshot={out}",
        design_file.as_uri(),
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

    if _PID_FILE.exists():
        pid = _PID_FILE.read_text().strip()
        print(f"Folio server already running (PID {pid}). Use --stop to stop it.")
        return

    server_path = str(Path.home() / ".folio" / "lib" / "server.py")
    port = getattr(args, "port", 5000)
    os.environ.setdefault("FOLIO_PORT", str(port))
    subprocess.run([sys.executable, server_path])


def _cmd_add_variant(args: argparse.Namespace) -> None:
    item_type = args.type
    item_id   = args.id
    file      = args.file
    label           = getattr(args, "label", None)
    ui_description  = getattr(args, "ui_description", None)
    notes           = getattr(args, "notes", None)
    rationale       = getattr(args, "rationale", None)

    assert item_type in {"screen", "component", "flow"}, f"Unknown type: {item_type!r}"

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
        screen = db.select_screen_variant(args.variant_id)
        if screen is None:
            print(f"Error: Screen variant {args.variant_id} not found.")
            sys.exit(1)
        print(f"Selected variant {args.variant_id} on screen #{screen['id']}: {screen['selected_file']}")

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
        component = db.select_component_variant(args.variant_id)
        if component is None:
            print(f"Error: Component variant {args.variant_id} not found.")
            sys.exit(1)
        print(
            f"Selected variant {args.variant_id} on component "
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
        flow = db.select_flow_variant(args.variant_id)
        if flow is None:
            print(f"Error: Flow variant {args.variant_id} not found.")
            sys.exit(1)
        print(
            f"Selected variant {args.variant_id} on flow "
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
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")

    p = screens_sub.add_parser("set-variant-rationale", help="Set rationale on a screen variant")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")
    p.add_argument("--rationale", required=True)

    p = screens_sub.add_parser("flag-variant", help="Flag a screen variant as needs-revision")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")
    p.add_argument("--reason", default=None)

    p = screens_sub.add_parser("unflag-variant", help="Clear flag on a screen variant")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")

    # --- components ---
    p_components  = sub.add_parser("components", help="Component commands")
    components_sub = p_components.add_subparsers(dest="command", required=True)

    components_sub.add_parser("list", help="List all components")

    p = components_sub.add_parser("add", help="Create a new component")
    p.add_argument("--name", required=True)
    p.add_argument("--description")
    p.add_argument("--usage")
    p.add_argument("--file", help="First variant file (optional)")

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
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")

    p = components_sub.add_parser("set-variant-rationale", help="Set rationale on a component variant")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")
    p.add_argument("--rationale", required=True)

    p = components_sub.add_parser("flag-variant", help="Flag a component variant as needs-revision")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")
    p.add_argument("--reason", default=None)

    p = components_sub.add_parser("unflag-variant", help="Clear flag on a component variant")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")

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
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")

    p = flows_sub.add_parser("set-variant-rationale", help="Set rationale on a flow variant")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")
    p.add_argument("--rationale", required=True)

    p = flows_sub.add_parser("flag-variant", help="Flag a flow variant as needs-revision")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")
    p.add_argument("--reason", default=None)

    p = flows_sub.add_parser("unflag-variant", help="Clear flag on a flow variant")
    p.add_argument("--variant-id", type=int, required=True, dest="variant_id")

    # --- top-level flat commands ---
    sub.add_parser("init", help="Init DB, copy system.md, seed from design/")
    sub.add_parser("sync-system", help="Write decisions table to system.md")
    sub.add_parser("update", help="Update folio CLI to latest version")

    p_serve = sub.add_parser("serve", help="Start the dashboard server")
    p_serve.add_argument("--port", type=int, default=7842)
    p_serve.add_argument("--stop", action="store_true", help="Stop the running server")

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
