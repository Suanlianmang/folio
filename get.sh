#!/bin/sh
set -e

REPO="https://raw.githubusercontent.com/Suanlianmang/folio/main"
LIB="$HOME/.folio/lib"
BIN="$HOME/.folio/bin"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 not found. Install Python 3 and try again." >&2
    exit 1
fi

mkdir -p "$LIB" "$BIN"

download() {
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$1" -o "$2"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO "$2" "$1"
    else
        echo "Error: curl or wget required." >&2
        exit 1
    fi
}

for file in cli.py db.py server.py main.py system.md; do
    download "$REPO/$file" "$LIB/$file"
done

cat > "$BIN/folio" <<'EOF'
#!/bin/sh
exec python3 "$HOME/.folio/lib/cli.py" "$@"
EOF
chmod +x "$BIN/folio"

RC_FILE=""
case "$SHELL" in
    */zsh)  RC_FILE="$HOME/.zshrc" ;;
    */bash)
        if [ -f "$HOME/.bash_profile" ]; then
            RC_FILE="$HOME/.bash_profile"
        else
            RC_FILE="$HOME/.bashrc"
        fi
        ;;
    *) RC_FILE="$HOME/.profile" ;;
esac

if ! grep -q '\.folio/bin' "$RC_FILE" 2>/dev/null; then
    printf '\nexport PATH="$HOME/.folio/bin:$PATH"\n' >> "$RC_FILE"
fi

echo "folio installed. Restart your shell or run: source ~/$(basename "$RC_FILE")"
