#!/usr/bin/env python3
"""Mac Remote Control Server v4"""

from flask import Flask, request, jsonify, send_from_directory, Response, send_file
import subprocess, os, socket, platform, random, json, base64, mimetypes, psutil

app = Flask(__name__)

ADJECTIVES = ["Gepard","Ulv","Ørn","Tiger","Bjørn","Rev","Gaupe","Elg","Sel","Hval","Ravn","Hare","Bison","Løve","Irbis"]
NOUNS = ["Fjord","Skog","Topp","Dal","Mark","Kyst","Bre","Eng","Foss","Vann","Heim","Berg"]
TOKEN = random.choice(ADJECTIVES) + random.choice(NOUNS) + str(random.randint(10,99))

def check_auth(req):
    t = req.headers.get("X-Auth-Token") or req.args.get("token")
    return t == TOKEN

def run(cmd, shell=True):
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=15)
        return {"ok": True, "out": result.stdout.strip(), "err": result.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "err": "Tidsavbrudd"}
    except Exception as e:
        return {"ok": False, "err": str(e)}

def osascript(script):
    return run(["osascript", "-e", script], shell=False)

def has_cliclick():
    r = subprocess.run("which cliclick", shell=True, capture_output=True)
    return r.returncode == 0

@app.route("/")
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "mac_remote.html")

@app.route("/manifest.json")
def manifest():
    data = {"name":"Mac Remote","short_name":"MacRemote","start_url":"/",
            "display":"standalone","background_color":"#111213","theme_color":"#111213",
            "icons":[{"src":"/icon.png","sizes":"512x512","type":"image/png"}]}
    return Response(json.dumps(data), mimetype="application/json")

@app.route("/icon.png")
def icon():
    px = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
    return Response(px, mimetype="image/png")

# ── INFO ──
@app.route("/api/info")
def info():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    vol = run("osascript -e 'output volume of (get volume settings)'")
    muted = run("osascript -e 'output muted of (get volume settings)'")
    battery = run("pmset -g batt | grep -o '[0-9]*%' | head -1")
    wifi = run("networksetup -getairportnetwork en0 | awk -F': ' '{print $2}'")
    return jsonify({
        "hostname": socket.gethostname(),
        "os": platform.mac_ver()[0],
        "volume": vol.get("out","?"),
        "muted": muted.get("out","false"),
        "battery": battery.get("out","?"),
        "wifi": wifi.get("out","?"),
    })

# ── CPU / RAM ──
@app.route("/api/system/stats")
def system_stats():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    temps = {}
    try:
        t = psutil.sensors_temperatures()
        if t:
            for name, entries in t.items():
                if entries:
                    temps[name] = round(entries[0].current, 1)
    except: pass
    net = psutil.net_io_counters()
    return jsonify({
        "cpu": round(cpu, 1),
        "ram_used": round(mem.used / 1024**3, 1),
        "ram_total": round(mem.total / 1024**3, 1),
        "ram_pct": mem.percent,
        "disk_used": round(disk.used / 1024**3, 1),
        "disk_total": round(disk.total / 1024**3, 1),
        "disk_pct": round(disk.used / disk.total * 100, 1),
        "net_sent": round(net.bytes_sent / 1024**2, 1),
        "net_recv": round(net.bytes_recv / 1024**2, 1),
        "temps": temps,
    })

@app.route("/api/system/processes")
def system_processes():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    procs = []
    for p in sorted(psutil.process_iter(['pid','name','cpu_percent','memory_percent']), key=lambda x: x.info['cpu_percent'] or 0, reverse=True)[:20]:
        procs.append({
            "pid": p.info['pid'],
            "name": p.info['name'],
            "cpu": round(p.info['cpu_percent'] or 0, 1),
            "mem": round(p.info['memory_percent'] or 0, 1),
        })
    return jsonify({"processes": procs})

# ── LYD ──
@app.route("/api/volume/set/<int:level>")
def volume_set(level):
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(osascript(f"set volume output volume {max(0,min(100,level))}"))

@app.route("/api/volume/togglemute")
def volume_togglemute():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    r = run("osascript -e 'output muted of (get volume settings)'")
    currently_muted = r.get("out","false").strip().lower() == "true"
    if currently_muted:
        osascript("set volume without output muted")
        return jsonify({"ok": True, "muted": False})
    else:
        osascript("set volume with output muted")
        return jsonify({"ok": True, "muted": True})

# ── MEDIA ──
@app.route("/api/media/<action>")
def media(action):
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    keys = {"play":"key code 49","next":"key code 124 using {command down}","prev":"key code 123 using {command down}"}
    if action not in keys: return jsonify({"ok":False,"err":"Ukjent"})
    return jsonify(osascript(f'tell application "System Events" to {keys[action]}'))

# ── SKJERM ──
@app.route("/api/display/sleep")
def display_sleep():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(run("pmset displaysleepnow"))

@app.route("/api/display/wake")
def display_wake():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(run("caffeinate -u -t 1"))

@app.route("/api/display/screenshot")
def screenshot():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    path = "/tmp/mac_remote_screenshot.jpg"
    r = run(f"screencapture -x -t jpg -o {path}")
    if not os.path.exists(path):
        return jsonify({"ok": False, "err": "Klarte ikke ta skjermshot"})
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    os.remove(path)
    return jsonify({"ok": True, "image": data})

# ── SYSTEM ──
@app.route("/api/system/sleep")
def system_sleep():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(osascript('tell application "System Events" to sleep'))

@app.route("/api/system/lock")
def system_lock():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(run("pmset sleepnow"))

@app.route("/api/system/screensaver")
def screensaver():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify(run("open -a ScreenSaverEngine"))

@app.route("/api/system/notification", methods=["POST"])
def notification():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    title = data.get("title","Mac Remote").replace('"','')
    msg = data.get("message","").replace('"','')
    return jsonify(osascript(f'display notification "{msg}" with title "{title}"'))

@app.route("/api/system/say", methods=["POST"])
def say():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    text = data.get("text","").replace('"','').replace("'",'')[:200]
    return jsonify(run(f'say "{text}"'))

# ── APPER ──
@app.route("/api/app/open/<appname>")
def app_open(appname):
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    safe = appname.replace('"','').replace(';','').replace('&','').replace('|','')
    return jsonify(run(["open","-a",safe], shell=False))

@app.route("/api/apps/installed")
def apps_installed():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    r = run("ls /Applications/ | grep '.app' | sed 's/.app//'")
    apps = sorted([a.strip() for a in r.get("out","").split("\n") if a.strip()])
    return jsonify({"apps": apps})

@app.route("/api/apps/running")
def apps_running():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    r = run("osascript -e 'tell application \"System Events\" to get name of every application process whose background only is false'")
    apps = [a.strip() for a in r.get("out","").split(",") if a.strip()]
    return jsonify({"apps": apps})

# ── TERMINAL ──
@app.route("/api/terminal", methods=["POST"])
def terminal():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    cmd = data.get("cmd","").strip()
    if not cmd: return jsonify({"ok":False,"err":"Tom kommando"})
    # Blokkerte kommandoer
    blocked = ["rm -rf /","sudo rm","mkfs","dd if=",":(){ :|:","shutdown","reboot"]
    for b in blocked:
        if b in cmd:
            return jsonify({"ok":False,"err":f"Blokkert kommando"})
    r = run(cmd)
    return jsonify({"ok": True, "out": r.get("out",""), "err": r.get("err","")})

# ── FIL-BROWSER ──
@app.route("/api/files/list")
def files_list():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    path = request.args.get("path", os.path.expanduser("~"))
    path = os.path.normpath(path)
    # Sikkerhet: ikke gå utenfor hjemmemappe
    home = os.path.expanduser("~")
    if not path.startswith(home) and path != "/":
        path = home
    try:
        entries = []
        for name in sorted(os.listdir(path)):
            if name.startswith("."): continue
            full = os.path.join(path, name)
            try:
                stat = os.stat(full)
                is_dir = os.path.isdir(full)
                entries.append({
                    "name": name,
                    "path": full,
                    "is_dir": is_dir,
                    "size": stat.st_size if not is_dir else 0,
                })
            except: continue
        return jsonify({"ok":True, "path": path, "entries": entries, "parent": os.path.dirname(path)})
    except Exception as e:
        return jsonify({"ok":False, "err":str(e)})

@app.route("/api/files/download")
def files_download():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    path = request.args.get("path","")
    home = os.path.expanduser("~")
    if not os.path.isfile(path) or not path.startswith(home):
        return jsonify({"error":"Ikke tillatt"}), 403
    return send_file(path, as_attachment=True)

# ── TASTATUR / MUS ──
@app.route("/api/type", methods=["POST"])
def type_text():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    text = data.get("text","").replace('"','\\"')
    return jsonify(osascript(f'tell application "System Events" to keystroke "{text}"'))

@app.route("/api/key", methods=["POST"])
def key_press():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    key = data.get("key","")
    safe_keys = {
        "return":"key code 36","delete":"key code 51","escape":"key code 53",
        "tab":"key code 48","space":"key code 49","up":"key code 126",
        "down":"key code 125","left":"key code 123","right":"key code 124",
        "cmd_c":'keystroke "c" using command down',
        "cmd_v":'keystroke "v" using command down',
        "cmd_z":'keystroke "z" using command down',
        "cmd_tab":'keystroke tab using command down',
    }
    if key not in safe_keys: return jsonify({"ok":False,"err":"Ukjent tast"})
    return jsonify(osascript(f'tell application "System Events" to {safe_keys[key]}'))

@app.route("/api/mouse/move", methods=["POST"])
def mouse_move():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    dx = float(data.get("dx",0)); dy = float(data.get("dy",0))
    if has_cliclick():
        return jsonify(run(f"cliclick m:+{int(dx)},+{int(dy)}"))
    script = f'''tell application "System Events"
    set cp to position of mouse
    set nx to (item 1 of cp) + {dx}
    set ny to (item 2 of cp) + {dy}
    set position of mouse to {{nx, ny}}
end tell'''
    return jsonify(osascript(script))

@app.route("/api/mouse/click", methods=["POST"])
def mouse_click():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    btn = data.get("button","left")
    if has_cliclick():
        flag = {"right":"r","double":"dc","left":"c"}.get(btn,"c")
        return jsonify(run(f"cliclick {flag}:."))
    if btn == "right":
        return jsonify(osascript('tell application "System Events" to secondary click at (position of mouse)'))
    return jsonify(osascript('tell application "System Events" to click at (position of mouse)'))

@app.route("/api/mouse/scroll", methods=["POST"])
def mouse_scroll():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    dy = int(data.get("dy",0))
    if has_cliclick():
        direction = "d" if dy > 0 else "u"
        return jsonify(run(f"cliclick {direction}:."))
    script = f'tell application "System Events" to scroll {abs(dy)} {"down" if dy>0 else "up"}'
    return jsonify(osascript(script))

@app.route("/api/clipboard/set", methods=["POST"])
def clipboard_set():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    data = request.json or {}
    p = subprocess.run("pbcopy", input=data.get("text","").encode(), capture_output=True)
    return jsonify({"ok": p.returncode==0})

@app.route("/api/clipboard/get")
def clipboard_get():
    if not check_auth(request): return jsonify({"error": "Ugyldig token"}), 401
    return jsonify({"text": run("pbpaste").get("out","")})

if __name__ == "__main__":
    try:
        ip = subprocess.run("ipconfig getifaddr en0", shell=True, capture_output=True, text=True).stdout.strip()
        if not ip:
            ip = subprocess.run("ipconfig getifaddr en1", shell=True, capture_output=True, text=True).stdout.strip()
        if not ip:
            ip = socket.gethostbyname(socket.gethostname())
    except: ip = "?"
    port = 5055
    print(f"""
╔══════════════════════════════════════════════╗
║       Mac Remote Control Server v4          ║
╠══════════════════════════════════════════════╣
║                                              ║
║  Åpne på mobil:                              ║
║  http://{ip}:{port}
║                                              ║
║  Token:  {TOKEN}
║                                              ║
╚══════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=port, debug=False)
