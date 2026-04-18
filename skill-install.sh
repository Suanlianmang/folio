#!/bin/sh
set -e

REPO="https://raw.githubusercontent.com/Suanlianmang/folio/main"
DEST="$HOME/.claude/commands"

if command -v curl >/dev/null 2>&1; then
    dl() { curl -fsSL "$1" -o "$2"; }
elif command -v wget >/dev/null 2>&1; then
    dl() { wget -qO "$2" "$1"; }
else
    echo "Error: curl or wget required." >&2
    exit 1
fi

mkdir -p "$DEST"
dl "$REPO/folio.md" "$DEST/folio.md"

echo "Folio skill installed. Type /folio in Claude Code to start."
echo "Claude will install the folio CLI automatically on first use."
