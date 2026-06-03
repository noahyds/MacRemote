#!/bin/bash
REPO="https://raw.githubusercontent.com/noahyds/MacRemote/main"
DEST="$HOME/Documents/MacRemote"

clear
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║      Mac Remote — Installerer v4         ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

echo "  [1/6] Sjekker Python..."
if ! command -v python3 &>/dev/null; then
  echo "  ❌ Python3 ikke funnet. Installer fra https://python.org"; exit 1
fi
echo "  ✓ $(python3 --version)"

echo "  [2/6] Sjekker Homebrew..."
if ! command -v brew &>/dev/null; then
  echo "  → Installerer Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  [ -f "/opt/homebrew/bin/brew" ] && eval "$(/opt/homebrew/bin/brew shellenv)"
fi
echo "  ✓ Homebrew klar"

echo "  [3/6] Installerer cliclick..."
command -v cliclick &>/dev/null || brew install cliclick --quiet
command -v cliclick &>/dev/null && echo "  ✓ cliclick klar" || echo "  ⚠️  cliclick ikke tilgjengelig"

echo "  [4/6] Installerer Python-pakker..."
pip3 install flask psutil --quiet --break-system-packages 2>/dev/null || pip3 install flask psutil --quiet 2>/dev/null
python3 -c "import flask,psutil" 2>/dev/null || { echo "  ❌ Installasjon feilet"; exit 1; }
echo "  ✓ Flask og psutil klar"

echo "  [5/6] Laster ned filer..."
mkdir -p "$DEST"
curl -fsSL "$REPO/mac_remote.py"   -o "$DEST/mac_remote.py"
curl -fsSL "$REPO/mac_remote.html" -o "$DEST/mac_remote.html"
[ -f "$DEST/mac_remote.py" ] && [ -f "$DEST/mac_remote.html" ] || { echo "  ❌ Nedlasting feilet"; exit 1; }
echo "  ✓ Filer lastet ned"

echo "  [6/6] Lager starter-app..."
LAUNCHER="$DEST/Start MacRemote.command"
cat > "$LAUNCHER" << 'LAUNCHEREOF'
#!/bin/bash
# Mac Remote — Starter
# Dobbeltklikk for å starte serveren

# Legg til Homebrew i PATH
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

DEST="$HOME/Documents/MacRemote"
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "?")

clear
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║       Mac Remote — Starter               ║"
echo "  ╠══════════════════════════════════════════╣"
echo "  ║  Åpne på mobil:                          ║"
echo "  ║  http://$IP:5055              "
echo "  ║                                          ║"
echo "  ║  Lukk vinduet for å stoppe               ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

python3 "$DEST/mac_remote.py"
LAUNCHEREOF

chmod +x "$LAUNCHER"
# Fjern karantene-flagget så Gatekeeper ikke klager
xattr -d com.apple.quarantine "$LAUNCHER" 2>/dev/null

echo "  ✓ Starter-app laget: $LAUNCHER"

IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "?")
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║  ✅ Mac Remote installert!               ║"
echo "  ╠══════════════════════════════════════════╣"
echo "  ║                                          ║"
echo "  ║  Starter fremover:                       ║"
echo "  ║  Dobbeltklikk «Start MacRemote.command»  ║"
echo "  ║  i ~/Documents/MacRemote/                ║"
echo "  ║                                          ║"
echo "  ║  Tips: dra den til Dock for rask tilgang ║"
echo "  ║                                          ║"
echo "  ║  ⚠️  Gi Terminal tilgang under:          ║"
echo "  ║  Innstillinger → Personvern              ║"
echo "  ║  → Tilgjengelighet (for mus/trackpad)    ║"
echo "  ║                                          ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# Start serveren første gang
python3 "$DEST/mac_remote.py"
