#!/bin/bash

REPO="https://raw.githubusercontent.com/noahyds/MacRemote/main"
DEST="$HOME/Documents/MacRemote"

clear
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║      Mac Remote — Installerer v3         ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# ── Python ──
echo "  [1/5] Sjekker Python..."
if ! command -v python3 &>/dev/null; then
  echo "  ❌ Python3 ikke funnet. Installer fra https://python.org"
  exit 1
fi
echo "  ✓ $(python3 --version)"

# ── Homebrew ──
echo "  [2/5] Sjekker Homebrew..."
if ! command -v brew &>/dev/null; then
  echo "  → Installerer Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Legg til i PATH for Apple Silicon
  if [ -f "/opt/homebrew/bin/brew" ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi
fi
echo "  ✓ Homebrew klar"

# ── cliclick ──
echo "  [3/5] Installerer cliclick (trackpad-støtte)..."
if ! command -v cliclick &>/dev/null; then
  brew install cliclick --quiet
fi
if command -v cliclick &>/dev/null; then
  echo "  ✓ cliclick klar"
else
  echo "  ⚠️  cliclick ikke tilgjengelig — trackpad fungerer likevel, men tregere"
fi

# ── Flask ──
echo "  [4/5] Installerer Flask..."
pip3 install flask --quiet --break-system-packages 2>/dev/null || pip3 install flask --quiet 2>/dev/null
if ! python3 -c "import flask" 2>/dev/null; then
  echo "  ❌ Klarte ikke installere Flask"
  exit 1
fi
echo "  ✓ Flask klar"

# ── Last ned filer ──
echo "  [5/5] Laster ned filer fra GitHub..."
mkdir -p "$DEST"
curl -fsSL "$REPO/mac_remote.py"   -o "$DEST/mac_remote.py"
curl -fsSL "$REPO/mac_remote.html" -o "$DEST/mac_remote.html"

if [ ! -f "$DEST/mac_remote.py" ] || [ ! -f "$DEST/mac_remote.html" ]; then
  echo "  ❌ Nedlasting feilet. Sjekk internett og at repoet er public."
  exit 1
fi
echo "  ✓ Filer lagret i $DEST"

IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "?")
PORT=5055

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║  ✅ Mac Remote er klar!                  ║"
echo "  ╠══════════════════════════════════════════╣"
echo "  ║                                          ║"
echo "  ║  Åpne på mobil:                          ║"
echo "  ║  http://$IP:$PORT                 "
echo "  ║                                          ║"
echo "  ║  Husk: mobil og Mac må være på           ║"
echo "  ║  samme Wi-Fi nettverk                    ║"
echo "  ║                                          ║"
echo "  ║  Neste gang: kjør bare                   ║"
echo "  ║  python3 ~/Documents/MacRemote/mac_remote.py"
echo "  ║                                          ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""
echo "  ⚠️  NB: Gi Terminal tilgang under"
echo "     Systeminnstillinger → Personvern"
echo "     → Tilgjengelighet (for trackpad/mus)"
echo ""

python3 "$DEST/mac_remote.py"
