#!/bin/bash
REPO="https://raw.githubusercontent.com/noahyds/MacRemote/main"
DEST="$HOME/Documents/MacRemote"

clear
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║      Mac Remote — Installerer v4         ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

echo "  [1/5] Sjekker Python..."
if ! command -v python3 &>/dev/null; then
  echo "  ❌ Python3 ikke funnet. Installer fra https://python.org"; exit 1
fi
echo "  ✓ $(python3 --version)"

echo "  [2/5] Sjekker Homebrew..."
if ! command -v brew &>/dev/null; then
  echo "  → Installerer Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  [ -f "/opt/homebrew/bin/brew" ] && eval "$(/opt/homebrew/bin/brew shellenv)"
fi
echo "  ✓ Homebrew klar"

echo "  [3/5] Installerer cliclick..."
command -v cliclick &>/dev/null || brew install cliclick --quiet
command -v cliclick &>/dev/null && echo "  ✓ cliclick klar" || echo "  ⚠️  cliclick ikke tilgjengelig"

echo "  [4/5] Installerer Python-pakker..."
pip3 install flask psutil --quiet --break-system-packages 2>/dev/null || pip3 install flask psutil --quiet 2>/dev/null
python3 -c "import flask,psutil" 2>/dev/null || { echo "  ❌ Installasjon feilet"; exit 1; }
echo "  ✓ Flask og psutil klar"

echo "  [5/5] Laster ned filer..."
mkdir -p "$DEST"
curl -fsSL "$REPO/mac_remote.py"   -o "$DEST/mac_remote.py"
curl -fsSL "$REPO/mac_remote.html" -o "$DEST/mac_remote.html"
[ -f "$DEST/mac_remote.py" ] && [ -f "$DEST/mac_remote.html" ] || { echo "  ❌ Nedlasting feilet"; exit 1; }
echo "  ✓ Filer lagret i $DEST"

IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "?")
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║  ✅ Mac Remote er klar!                  ║"
echo "  ╠══════════════════════════════════════════╣"
echo "  ║  Åpne på mobil: http://$IP:5055   "
echo "  ║                                          ║"
echo "  ║  ⚠️  Gi Terminal tilgang under:          ║"
echo "  ║  Innstillinger → Personvern              ║"
echo "  ║  → Tilgjengelighet (for mus/trackpad)    ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

python3 "$DEST/mac_remote.py"
