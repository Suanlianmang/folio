#!/bin/sh
set -e

# Verify python3 is available.
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 not found. Install Python 3 and try again." >&2
    exit 1
fi

# Create target directories.
mkdir -p "$HOME/.folio/lib"
mkdir -p "$HOME/.folio/bin"

# Copy Python source files and system.md template.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR"/*.py "$HOME/.folio/lib/"
cp "$SCRIPT_DIR/system.md" "$HOME/.folio/lib/system.md"
mkdir -p "$HOME/.folio/lib/ui"
cp "$SCRIPT_DIR"/ui/*.html "$HOME/.folio/lib/ui/"
cp "$SCRIPT_DIR"/ui/*.css  "$HOME/.folio/lib/ui/"
cp "$SCRIPT_DIR"/ui/*.js   "$HOME/.folio/lib/ui/"

# Write the folio wrapper script.
cat > "$HOME/.folio/bin/folio" <<'EOF'
#!/bin/sh
exec python3 "$HOME/.folio/lib/cli.py" "$@"
EOF
chmod +x "$HOME/.folio/bin/folio"

# Detect shell rc file.
RC_FILE=""
case "$SHELL" in
    */zsh)
        RC_FILE="$HOME/.zshrc"
        ;;
    */bash)
        if [ -f "$HOME/.bash_profile" ]; then
            RC_FILE="$HOME/.bash_profile"
        else
            RC_FILE="$HOME/.bashrc"
        fi
        ;;
    *)
        RC_FILE="$HOME/.profile"
        ;;
esac

# Append PATH export only if not already present.
if ! grep -q '\.folio/bin' "$RC_FILE" 2>/dev/null; then
    printf '\nexport PATH="$HOME/.folio/bin:$PATH"\n' >> "$RC_FILE"
fi

RC_NAME="$(basename "$RC_FILE")"
echo "folio installed. Restart your shell or run: source ~/$RC_NAME"
