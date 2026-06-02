#!/bin/bash

REPO="https://raw.githubusercontent.com/noahyds/MacRemote/main"
DEST="$HOME/Documents/MacRemote"

clear
echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║      Mac Remote — Installerer        ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

# Python
echo "  [1/4] Sjekker Python..."
if ! command -v python3 &>/dev/null; then
  echo "  ❌ Python3 ikke funnet. Installer fra https://python.org"
  exit 1
fi
echo "  ✓ $(python3 --version)"

# Flask
echo "  [2/4] Installerer Flask..."
pip3 install flask --quiet --break-system-packages 2>/dev/null || pip3 install flask --quiet 2>/dev/null
if ! python3 -c "import flask" 2>/dev/null; then
  echo "  ❌ Klarte ikke installere Flask"
  exit 1
fi
echo "  ✓ Flask klar"

# Last ned filer
echo "  [3/4] Laster ned filer..."
mkdir -p "$DEST"
curl -fsSL "$REPO/mac_remote.py" -o "$DEST/mac_remote.py"
curl -fsSL "$REPO/mac_remote.html" -o "$DEST/mac_remote.html"
if [ ! -f "$DEST/mac_remote.py" ] || [ ! -f "$DEST/mac_remote.html" ]; then
  echo "  ❌ Nedlasting feilet. Sjekk internettforbindelsen."
  exit 1
fi
echo "  ✓ Filer lagret i $DEST"

# Start
echo "  [4/4] Starter server..."
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "?")
echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║  ✅ Mac Remote er oppe!              ║"
echo "  ╠══════════════════════════════════════╣"
echo "  ║                                      ║"
echo "  ║  Åpne på mobil:                      ║"
echo "  ║  http://$IP:5055              "
echo "  ║                                      ║"
echo "  ║  Neste gang, kjør:                   ║"
echo "  ║  python3 ~/Documents/MacRemote/mac_remote.py"
echo "  ║                                      ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

python3 "$DEST/mac_remote.py"
