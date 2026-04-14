"""
cli.py — Folio CLI. Claude-readable plaintext output.

Run from host project root:
    python3 tools/folio/cli.py <command> [args]
"""

import argparse
import os
import sys

# ---------------------------------------------------------------------------
# Path setup — db.py lives in the same directory as this file
# ---------------------------------------------------------------------------

_FOLIO_DIR = os.path.dirname(os.path.abspath(__file__))
if _FOLIO_DIR not in sys.path:
    sys.path.insert(0, _FOLIO_DIR)

import db

# Configure db paths relative to CWD (host project root)
db.configure(os.getcwd())


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _print_item_summary(item: dict) -> None:
    """Print one-line item summary with indented variants."""
    print(f"  #{item['id']} [{item['type']}] {item['name']} ({item['status']})")
    for variant in item.get("variants", []):
        selected_marker = "●" if variant["file"] == item.get("selected_file") else " "
        label = f" — {variant['label']}" if variant["label"] else ""
        print(f"      {selected_marker} {variant['file']}{label}")


def _print_item_detail(item: dict) -> None:
    """Print full item detail for show command."""
    print(f"#{item['id']} [{item['type']}] {item['name']}")
    print(f"  Status:      {item['status']}")
    if item.get("description"):
        print(f"  Description: {item['description']}")
    if item.get("usage"):
        print(f"  Usage:       {item['usage']}")
    if item.get("selected_file"):
        print(f"  Selected:    {item['selected_file']}")
    if item.get("rationale"):
        print(f"  Rationale:   {item['rationale']}")
    print(f"  Created:     {item['created_at']}")
    print(f"  Updated:     {item['updated_at']}")

    variants = item.get("variants", [])
    if variants:
        print(f"  Variants ({len(variants)}):")
        for v in variants:
            selected_marker = "●" if v["file"] == item.get("selected_file") else " "
            label           = f" [{v['label']}]" if v["label"] else ""
            print(f"      {selected_marker} #{v['id']} {v['file']}{label}")
            if v.get("ui_description"):
                print(f"          {v['ui_description']}")
            if v.get("notes"):
                print(f"          Notes: {v['notes']}")
    else:
        print("  Variants: (none)")


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def _cmd_init(_args: argparse.Namespace) -> None:
    db.init_db()
    print("Initialized: DB schema created, screenshots dir ready.")

    if os.path.isdir(db.DESIGN_DIR):
        count = db.seed_from_design()
        if count > 0:
            print(f"Seeded {count} item(s) from design/.")
        else:
            print("design/ found but no HTML files to seed.")
    else:
        print("No design/ directory found — skipping seed.")


def _cmd_list(args: argparse.Namespace) -> None:
    type_filter = getattr(args, "type", None)
    items = db.list_items(type_filter=type_filter)
    print(f"=== ITEMS ({len(items)}) ===")
    for item in items:
        _print_item_summary(item)


def _cmd_show(args: argparse.Namespace) -> None:
    item = db.get_item(args.id)
    if item is None:
        print(f"Error: Item {args.id} not found.")
        sys.exit(1)
    _print_item_detail(item)


def _cmd_add_item(args: argparse.Namespace) -> None:
    item = db.create_item(
        type=args.type,
        name=args.name,
        description=getattr(args, "description", None),
        usage=getattr(args, "usage", None),
    )
    print(f"Created item #{item['id']}: {item['name']}")

    first_file = getattr(args, "file", None)
    if first_file:
        variant = db.create_variant(item_id=item["id"], file=first_file, label="v1")
        db.select_variant(variant["id"])
        print(f"  Added variant #{variant['id']}: {first_file}")
        print(f"  Selected: {first_file}")


def _cmd_add_variant(args: argparse.Namespace) -> None:
    variant = db.create_variant(
        item_id=args.item_id,
        file=args.file,
        label=getattr(args, "label", None),
        ui_description=getattr(args, "ui_description", None),
        notes=getattr(args, "notes", None),
    )
    print(f"Created variant #{variant['id']}: {variant['file']}")


def _cmd_select(args: argparse.Namespace) -> None:
    item = db.select_variant(args.variant_id)
    if item is None:
        print(f"Error: Variant {args.variant_id} not found.")
        sys.exit(1)
    print(f"Selected variant {args.variant_id} on item #{item['id']}: {item['selected_file']}")


def _cmd_set_status(args: argparse.Namespace) -> None:
    item = db.update_item(args.id, status=args.status)
    if item is None:
        print(f"Error: Item {args.id} not found.")
        sys.exit(1)
    print(f"Item #{item['id']} status → {item['status']}")


def _cmd_set_rationale(args: argparse.Namespace) -> None:
    item = db.update_item(args.id, rationale=args.rationale)
    if item is None:
        print(f"Error: Item {args.id} not found.")
        sys.exit(1)
    print(f"Item #{item['id']} rationale updated.")


def _cmd_sync_system(_args: argparse.Namespace) -> None:
    db.sync_system()
    print(f"system.md updated: {db.SYSTEM_MD_PATH}")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="folio",
        description="Folio design exploration tracker CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Init DB, copy system.md, seed from design/")

    p_list = sub.add_parser("list", help="List all items")
    p_list.add_argument(
        "--type",
        choices=["screen", "layout", "component", "flow"],
        help="Filter by type",
    )

    p_show = sub.add_parser("show", help="Show full item detail")
    p_show.add_argument("--id", type=int, required=True, help="Item ID")

    p_add_item = sub.add_parser("add-item", help="Create a new item")
    p_add_item.add_argument("--type", required=True, choices=["screen", "layout", "component", "flow"])
    p_add_item.add_argument("--name", required=True)
    p_add_item.add_argument("--description")
    p_add_item.add_argument("--usage")
    p_add_item.add_argument("--file", help="First variant file (optional)")

    p_add_variant = sub.add_parser("add-variant", help="Add a variant to an item")
    p_add_variant.add_argument("--item-id", type=int, required=True, dest="item_id")
    p_add_variant.add_argument("--file", required=True)
    p_add_variant.add_argument("--label")
    p_add_variant.add_argument("--ui-description", dest="ui_description")
    p_add_variant.add_argument("--notes")

    p_select = sub.add_parser("select", help="Set variant as selected on parent item")
    p_select.add_argument("--variant-id", type=int, required=True, dest="variant_id")

    p_set_status = sub.add_parser("set-status", help="Update item status")
    p_set_status.add_argument("--id", type=int, required=True)
    p_set_status.add_argument("--status", required=True, choices=["exploring", "approved", "finalised"])

    p_set_rationale = sub.add_parser("set-rationale", help="Set item rationale")
    p_set_rationale.add_argument("--id", type=int, required=True)
    p_set_rationale.add_argument("--rationale", required=True)

    sub.add_parser("sync-system", help="Write decisions table to system.md")

    return parser


# ---------------------------------------------------------------------------
# Dispatch table
# ---------------------------------------------------------------------------

_COMMANDS = {
    "init":          _cmd_init,
    "list":          _cmd_list,
    "show":          _cmd_show,
    "add-item":      _cmd_add_item,
    "add-variant":   _cmd_add_variant,
    "select":        _cmd_select,
    "set-status":    _cmd_set_status,
    "set-rationale": _cmd_set_rationale,
    "sync-system":   _cmd_sync_system,
}


def main() -> None:
    parser = _build_parser()
    args   = parser.parse_args()

    assert args.command in _COMMANDS, f"Unknown command: {args.command!r}"

    handler = _COMMANDS[args.command]
    try:
        handler(args)
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
