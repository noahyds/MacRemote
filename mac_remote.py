#!/usr/bin/env python3
"""
Mac Remote Control Server v2
Krever: pip3 install flask
"""

from flask import Flask, request, jsonify, send_from_directory
import subprocess, os, socket, platform, base64, threading, time

app = Flask(__name__)
SECRET = "minmac123"

def check_auth(req):
    token = req.headers.get("X-Auth-Token") or req.args.get("token")
    return token == SECRET

def run(cmd, shell=True):
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=10)
        return {"ok": True, "out": result.stdout.strip(), "err": result.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "err": "Tidsavbrudd"}
    except Exception as e:
        return {"ok": False, "err": str(e)}

def osascript(script):
    return run(["osascript", "-e", script], shell=False)

@app.route("/")
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "mac_remote.html")

@app.route("/api/info")
def info():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    vol = run("osascript -e 'output volume of (get volume settings)'")
    battery = run("pmset -g batt | grep -o '[0-9]*%' | head -1")
    wifi = run("networksetup -getairportnetwork en0 | awk -F': ' '{print $2}'")
    return jsonify({
        "hostname": socket.gethostname(),
        "os": platform.mac_ver()[0],
        "volume": vol.get("out", "?"),
        "battery": battery.get("out", "?"),
        "wifi": wifi.get("out", "?"),
    })

@app.route("/api/volume/set/<int:level>")
def volume_set(level):
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(osascript(f"set volume output volume {max(0,min(100,level))}"))

@app.route("/api/media/<action>")
def media(action):
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    keys = {"play": "key code 49", "next": "key code 124 using {command down}", "prev": "key code 123 using {command down}"}
    if action not in keys: return jsonify({"ok": False, "err": "Ukjent"})
    return jsonify(osascript(f'tell application "System Events" to {keys[action]}'))

@app.route("/api/display/sleep")
def display_sleep():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(run("pmset displaysleepnow"))

@app.route("/api/display/wake")
def display_wake():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(run("caffeinate -u -t 1"))

@app.route("/api/system/sleep")
def system_sleep():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(osascript('tell application "System Events" to sleep'))

@app.route("/api/system/lock")
def system_lock():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(run("/System/Library/CoreServices/Menu\\ Extras/User.menu/Contents/Resources/CGSession -suspend"))

@app.route("/api/system/screensaver")
def screensaver():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(run("open -a ScreenSaverEngine"))

@app.route("/api/system/notification", methods=["POST"])
def notification():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    title = data.get("title", "Mac Remote").replace('"', '')
    msg = data.get("message", "").replace('"', '')
    return jsonify(osascript(f'display notification "{msg}" with title "{title}"'))

@app.route("/api/app/open/<appname>")
def app_open(appname):
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    safe = appname.replace('"','').replace(';','').replace('&','').replace('|','')
    return jsonify(run(["open", "-a", safe], shell=False))

@app.route("/api/app/quit/<appname>")
def app_quit(appname):
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    safe = appname.replace('"','').replace(';','').replace('&','').replace('|','')
    return jsonify(osascript(f'tell application "{safe}" to quit'))

@app.route("/api/apps/installed")
def apps_installed():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    r = run("ls /Applications/ | grep '.app' | sed 's/.app//'")
    apps = [a.strip() for a in r.get("out","").split("\n") if a.strip()]
    return jsonify({"apps": apps})

@app.route("/api/apps/running")
def apps_running():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    r = run("osascript -e 'tell application \"System Events\" to get name of every application process whose background only is false'")
    apps = [a.strip() for a in r.get("out","").split(",") if a.strip()]
    return jsonify({"apps": apps})

@app.route("/api/type", methods=["POST"])
def type_text():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    text = data.get("text", "").replace('"', '\\"')
    return jsonify(osascript(f'tell application "System Events" to keystroke "{text}"'))

@app.route("/api/key", methods=["POST"])
def key_press():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    key = data.get("key", "")
    safe_keys = {
        "return": "key code 36",
        "delete": "key code 51",
        "escape": "key code 53",
        "tab": "key code 48",
        "space": "key code 49",
        "up": "key code 126",
        "down": "key code 125",
        "left": "key code 123",
        "right": "key code 124",
        "cmd_c": "keystroke \"c\" using command down",
        "cmd_v": "keystroke \"v\" using command down",
        "cmd_z": "keystroke \"z\" using command down",
        "cmd_tab": "keystroke tab using command down",
    }
    if key not in safe_keys: return jsonify({"ok": False, "err": "Ukjent tast"})
    return jsonify(osascript(f'tell application "System Events" to {safe_keys[key]}'))

@app.route("/api/mouse/move", methods=["POST"])
def mouse_move():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    dx = float(data.get("dx", 0))
    dy = float(data.get("dy", 0))
    script = f'''
tell application "System Events"
    set pos to position of mouse
    set x to (item 1 of pos) + {dx}
    set y to (item 2 of pos) + {dy}
    set position of mouse to {{x, y}}
end tell'''
    return jsonify(osascript(script))

@app.route("/api/mouse/click", methods=["POST"])
def mouse_click():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    btn = data.get("button", "left")
    if btn == "right":
        script = 'tell application "System Events" to set position of mouse to position of mouse\ntell application "System Events" to click at position of mouse using right button'
    else:
        script = 'tell application "System Events" to click at position of mouse'
    return jsonify(osascript(script))

@app.route("/api/mouse/scroll", methods=["POST"])
def mouse_scroll():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    dy = int(data.get("dy", 0))
    script = f'tell application "System Events" to scroll {abs(dy)} {"down" if dy > 0 else "up"}'
    return jsonify(osascript(script))

@app.route("/api/clipboard/set", methods=["POST"])
def clipboard_set():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    text = data.get("text", "")
    p = subprocess.run("pbcopy", input=text.encode(), capture_output=True)
    return jsonify({"ok": p.returncode == 0})

@app.route("/api/clipboard/get")
def clipboard_get():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify({"text": run("pbpaste").get("out", "")})

@app.route("/api/wifi/on")
def wifi_on():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(run("networksetup -setairportpower en0 on"))

@app.route("/api/wifi/off")
def wifi_off():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(run("networksetup -setairportpower en0 off"))

if __name__ == "__main__":
    try:
        ip = subprocess.run("ipconfig getifaddr en0", shell=True, capture_output=True, text=True).stdout.strip()
        if not ip:
            ip = socket.gethostbyname(socket.gethostname())
    except:
        ip = "?"
    port = 5055
    print(f"""
╔══════════════════════════════════════════╗
║     Mac Remote Control Server v2        ║
╠══════════════════════════════════════════╣
║  Åpne på mobil:                         ║
║  http://{ip}:{port}
║                                          ║
║  Token: {SECRET}
╚══════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=port, debug=False)
