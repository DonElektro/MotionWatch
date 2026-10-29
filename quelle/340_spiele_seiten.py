#@ Motion Watch – Teil 340: Extras: Seiten der Spielecke und des Spieleabends. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
SPIELE_PAGE = """<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Spielecke</title><link rel="icon" href="/icon-192.png"><style>
body{margin:0;background:#0E1621;color:#E8EEF5;font-family:system-ui,sans-serif}main{max-width:720px;margin:0 auto;padding:20px 16px}
h1{font-size:26px;margin:6px 0 4px}p{color:#9FB0C3;margin:4px 0 16px}.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
a.c{display:block;background:#16263A;border-radius:14px;padding:14px;color:inherit;text-decoration:none}a.c:active{transform:scale(.98)}
.i{font-size:34px}.n{font-weight:700;margin:6px 0 2px}.d{font-size:13px;color:#9FB0C3}.big{background:#E9A23B;color:#0E1621;font-weight:700;
display:block;text-align:center;padding:14px;border-radius:14px;text-decoration:none;margin:0 0 18px}</style></head><body><main>
<h1>🎲 Spielecke</h1>__PARTY__<p>__NOTE__</p><div class="g">__GAMES__</div></main></body></html>"""


GAMESRV = {"port": 0, "msg": ""}
STREAMS = {"n": 0, "ip": {}, "lock": threading.Lock()}


def games_server_start():
    """2.95.35: the browser games come from their own port (web port + 2). For the browser that is another «origin»:
    game code can neither read the pages of MoveEye nor send commands with the login of the administrator.
    Only for devices in the own network."""
    import http.server, socketserver, mimetypes
    port = int(CFG["web_port"]) + 2                      # + 1 is the https page

    class H(http.server.BaseHTTPRequestHandler):
        server_version = "MotionWatchGames"
        def log_message(self, *a):
            pass

        def do_GET(self):
            if not lan_guest_ip(self.client_address[0], self.headers.get("X-Forwarded-For", "")):
                self.send_error(403, "only in the own Wi-Fi"); return
            from urllib.parse import unquote, urlsplit
            path = unquote(urlsplit(self.path).path)
            m = re.fullmatch(r"/g/([A-Za-z0-9_\-]{1,40})/?(.*)", path)
            p_ = games_file(m.group(1), m.group(2)) if m else None
            if not p_:
                self.send_error(404); return
            if m.group(2) == "" and not path.endswith("/"):
                self.send_response(301); self.send_header("Location", path + "/"); self.end_headers(); return
            try:
                with open(p_, "rb") as f:
                    data = f.read()
            except OSError:
                self.send_error(404); return
            ct = mimetypes.guess_type(p_)[0] or "application/octet-stream"
            if ct == "text/html":
                h_ = (self.headers.get("Host") or "").rsplit(":", 1)[0]
                data = games_inject_back(data, f"http://{h_}:{CFG['web_port']}/spiele" if h_ else "/")
            self.send_response(200)
            self.send_header("Content-Type", ct + ("; charset=utf-8" if ct.startswith("text/") or ct.endswith("javascript") else ""))
            self.send_header("Content-Length", str(len(data))); self.send_header("Cache-Control", "max-age=3600")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers(); self.wfile.write(data)

    class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True
    try:
        srv = S(("0.0.0.0", port), H)
    except OSError as e:
        GAMESRV.update(port=0, msg=f"port {port}: {e}"[:120])
        return
    GAMESRV.update(port=port, msg="")
    threading.Thread(target=srv.serve_forever, daemon=True, name="games").start()


GAME_BACK = """<div id="mw-back" style="position:fixed;bottom:10px;left:10px;opacity:.85;z-index:2147483647;font:600 15px system-ui,sans-serif">
<a href="__BACK__" onclick="if(history.length>1){history.back();return false}try{window.close()}catch(e){}" style="display:inline-block;
background:rgba(14,22,33,.85);color:#fff;text-decoration:none;padding:8px 13px;border-radius:12px;border:1px solid rgba(255,255,255,.25)">✕ Zurück</a></div>"""


# 2.95.56: every page without its own way back gets a «✕ Zurück» button. On the phone MoveEye often runs as an app from
# the home screen (no address bar, no back button): a page like the almanac then could not be closed any more.
PAGE_EXIT = """<script>(function () {
  if (window.__mwExit) return; window.__mwExit = 1;
  var HOME = __HOME__, d = document;
  function go(ev) {
    if (ev) { ev.preventDefault(); ev.stopImmediatePropagation(); }
    var fs = d.fullscreenElement || d.webkitFullscreenElement;
    if (fs) { (d.exitFullscreen || d.webkitExitFullscreen).call(d); return; }
    var left = false; addEventListener("pagehide", function () { left = true; });
    function rest() {
      if (left) return;
      if (HOME && location.pathname !== HOME) { location.href = HOME; return; }
      try { window.close(); } catch (e) {}
      setTimeout(function () { var t = d.getElementById("mw-exit-t"); if (!left && t) { t.hidden = false; setTimeout(function () { t.hidden = true; }, 4000); } }, 300);
    }
    if (history.length > 1) { history.back(); setTimeout(rest, 700); } else rest();   // back where it came from - or home
  }
  function setup() {
    var own = d.querySelector("[data-mw-exit]");
    if (own) { own.addEventListener("click", go, true); return; }          // the page has its own button: it now always works
    if (d.getElementById("mw-back") || d.querySelector("nav.nav")) return;  // games have one, the pages of the app have the tabs
    var en = (d.documentElement.lang || "de").slice(0, 2) !== "de";
    var w = d.createElement("div");
    w.style.cssText = "position:fixed;left:10px;bottom:calc(10px + env(safe-area-inset-bottom,0px));z-index:2147483647;font:600 15px system-ui,sans-serif";
    w.innerHTML = '<button type="button" id="mw-exit" style="background:rgba(14,22,33,.88);color:#fff;border:1px solid rgba(255,255,255,.3);border-radius:12px;padding:9px 14px;font:inherit;cursor:pointer;min-height:40px">✕ ' + (en ? "Back" : "Zurück") + '</button>'
      + '<div id="mw-exit-t" hidden style="margin-top:6px;background:#eef3fa;color:#0b1220;border-radius:10px;padding:8px 11px;max-width:260px;font-weight:600">' + (en ? "Close this tab or swipe the app away." : "Diesen Tab schliessen oder die App wegwischen.") + '</div>';
    d.body.appendChild(w); d.getElementById("mw-exit").addEventListener("click", go);
  }
  if (d.body) setup(); else d.addEventListener("DOMContentLoaded", setup);
  addEventListener("keydown", function (e) { if (e.key === "Escape" && (d.fullscreenElement || d.webkitFullscreenElement)) go(); });
})();</script>"""
PAGE_EXIT_GUEST = ("/x/", "/k/", "/p/", "/spiele", "/nt/", "/info", "/almanach")


def page_exit_inject(path, txt):
    """2.95.56: add the «✕ Zurück» button to an HTML page (not the main page, not the TV, not the games themselves)"""
    if path == "/" or path.startswith(("/tv/", "/api/", "/g/")) or "window.__mwExit" in txt:
        return None
    home = "" if path.startswith(PAGE_EXIT_GUEST) else "/"    # guests may not open the main page: there they close the tab
    btn = PAGE_EXIT.replace("__HOME__", json.dumps(home))
    i = txt.lower().rfind("</body>")
    return txt[:i] + btn + txt[i:] if i >= 0 else txt + btn


def games_inject_back(data, back):
    """2.95.36: every game page gets a «✕ Zurück» button (to the game collection) - the games themselves have none"""
    try:
        txt = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    btn = GAME_BACK.replace("__BACK__", html_escape(back, quote=True))
    i = txt.lower().rfind("</body>")
    txt = txt[:i] + btn + txt[i:] if i >= 0 else txt + btn
    return txt.encode("utf-8")


def games_url(game, fn="", host=""):
    """where a game is opened: the games port when it runs, otherwise the same server as before"""
    if GAMESRV["port"] and host:
        h = host.rsplit(":", 1)[0] if host.count(":") == 1 or host.startswith("[") and "]:" in host else host
        return f"http://{h}:{GAMESRV['port']}/g/{game}/{fn}"
    return ""


GAME_GROUPS = {"touch": "👆 Für Handy und Tablet (Touch)", "buttons": "🎮 Mit Bildschirm-Tasten (am PC mit der Tastatur)"}   # 2.95.54


def spiele_page(host=""):
    from html import escape as _e
    gl = games_list()
    cards = ""
    for grp in (["touch", "buttons"] if any(x.get("input") for x in gl) else [None]):     # 2.95.54: touch games first
        part = [x for x in gl if grp is None or x.get("input", "touch") == grp]
        if not part:
            continue
        if grp:
            cards += f'<div style="grid-column:1/-1;font-weight:700;margin:14px 0 2px">{_e(GAME_GROUPS[grp])}</div>'
        cards += "".join(f'<a class="c" href="{_e(games_url(x["dir"], x.get("start", "index.html"), host) or "/spiele/g/" + x["dir"] + "/" + x.get("start", "index.html"))}"><div class="i">{_e(x.get("icon", "🎮"))}</div>'
                         f'<div class="n">{_e(x.get("name", x["dir"]))}</div><div class="d">{_e(x.get("desc", ""))}</div></a>' for x in part)
    party = (f'<a class="big" href="/p/{PARTY["key"]}/">👥 Zum Spieleabend (Quiz, Werwolf, Malen, 4 gewinnt)</a>' if party_on()
             else '<p>Der Spieleabend (Quiz, Werwolf, Malen …) ist gerade zu – öffnen kann ihn, wer MoveEye verwaltet.</p>')
    note = "Einzelspiele – laufen direkt im Browser:" if gl else "Die Spielesammlung ist noch nicht installiert (MoveEye → Reiter Spielecke)."
    return SPIELE_PAGE.replace("__PARTY__", party).replace("__NOTE__", note).replace("__GAMES__", cards)


def games_list():
    try:
        with open(os.path.join(games_dir(), "games.json")) as f:
            d = json.load(f)
        return [g_ for g_ in d.get("games", []) if isinstance(g_, dict) and os.path.isfile(os.path.join(games_dir(), g_.get("dir", "-"), g_.get("start", "index.html")))]
    except (OSError, ValueError):
        return []


def games_installed_version():
    try:
        with open(os.path.join(games_dir(), "games.json")) as f:
            return json.load(f).get("version", "")
    except (OSError, ValueError):
        return ""


def games_install():
    """the collection of free browser games: from GitHub (checksum checked) into the data folder"""
    if GAMES_DL["running"]:
        return
    GAMES_DL.update(running=True, msg="downloading …", got=0)
    try:
        import hashlib, io
        src = CFG["update_url"].strip()
        base = src.rsplit("/", 1)[0] + "/" if src.startswith("https://") else SIM3D_BASE
        h = hashlib.sha256(); buf = io.BytesIO()
        with urllib.request.urlopen(_upd_request(base + GAMES_PKG["file"]), timeout=60) as r:
            while True:
                b = r.read(1 << 16)
                if not b:
                    break
                h.update(b); buf.write(b); GAMES_DL["got"] = buf.tell()
                if GAMES_PKG["size"] and buf.tell() > GAMES_PKG["size"] + 1024:
                    raise ValueError("file too large")
        if h.hexdigest() != GAMES_PKG["sha256"]:
            raise ValueError("checksum wrong")
        tmp = games_dir() + ".new"
        shutil.rmtree(tmp, ignore_errors=True)
        with zipfile.ZipFile(buf) as z:
            for n in z.namelist():
                if n.startswith("/") or ".." in n.split("/"):
                    raise ValueError("bad file name in the package")
            z.extractall(tmp)
        shutil.rmtree(games_dir(), ignore_errors=True)
        os.replace(tmp, games_dir())
        GAMES_DL["msg"] = "installed"
        log_event("sys", f"Game collection {GAMES_PKG['version']} installed")
    except Exception as e:
        GAMES_DL["msg"] = "error: " + str(e)[:120]
        log_event("sys", f"Game collection: {e}"[:160])
    finally:
        GAMES_DL["running"] = False


def games_file(game, fn):
    """a file of an installed game (only inside its folder)"""
    gl = {g_["dir"]: g_ for g_ in games_list()}
    if game not in gl:
        return None
    base = os.path.realpath(os.path.join(games_dir(), game))
    p_ = os.path.realpath(os.path.join(base, fn or gl[game].get("start", "index.html")))
    if not (p_ == base or p_.startswith(base + os.sep)) or not os.path.isfile(p_):
        return None
    return p_


PARTY_PAGE = r"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0e1621"><title>Spielecke</title>
<style>
:root{--bg:#0e1621;--panel:#16212f;--line:#24324a;--txt:#e8eef6;--mut:#8ea0b6;--acc:#3b8cff;--teal:#5ed6c1;--amber:#e9a23b;--red:#ff5a5f;--grn:#3fcf6b}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--txt);font:16px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif}
body{padding:calc(10px + env(safe-area-inset-top)) 12px calc(20px + env(safe-area-inset-bottom))}
header{display:flex;align-items:center;gap:10px;margin-bottom:12px}header img{width:34px;height:34px;border-radius:9px}
header h1{font-size:19px;margin:0;flex:1}header .me{font-size:13px;color:var(--mut);text-align:right}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px;margin-bottom:12px}
h2{font-size:17px;margin:0 0 10px}.mut{color:var(--mut);font-size:14px}
button{font:inherit;border:0;border-radius:12px;padding:12px 14px;background:var(--acc);color:#fff;font-weight:600;cursor:pointer;touch-action:manipulation}
button.sec{background:#24324a;color:var(--txt)}button.red{background:var(--red)}button.grn{background:var(--grn);color:#062}button:disabled{opacity:.45}
input,select{font:inherit;padding:11px 12px;border-radius:12px;border:1px solid var(--line);background:#0b121c;color:var(--txt);width:100%}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.row>*{flex:1 1 auto}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}
.gbtn{display:flex;flex-direction:column;align-items:flex-start;gap:4px;text-align:left;background:#1c2a3d;border:1px solid var(--line);color:var(--txt);min-height:86px}
.gbtn b{font-size:16px}.gbtn span{font-size:12px;color:var(--mut);font-weight:400}.gbtn.on{border-color:var(--acc);box-shadow:0 0 0 2px var(--acc) inset}
.pl{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid var(--line)}.pl:last-child{border:0}
.pl .n{flex:1}.pl .s{font-weight:700;min-width:36px;text-align:right}.off{opacity:.45}
.buzz{width:min(72vw,300px);height:min(72vw,300px);border-radius:50%;font-size:34px;display:block;margin:12px auto;background:radial-gradient(circle at 35% 30%,#ff8a8d,#e0262c);box-shadow:0 10px 0 #8d1418,0 14px 30px rgba(0,0,0,.5)}
.buzz:active{transform:translateY(6px);box-shadow:0 4px 0 #8d1418}
.big{font-size:22px;font-weight:700;text-align:center;margin:10px 0}
.role{font-size:28px;text-align:center;padding:26px;border-radius:16px;background:#0b121c;border:1px dashed var(--line);user-select:none}
canvas{width:100%;aspect-ratio:4/3;background:#fff;border-radius:12px;touch-action:none;display:block}
.cols{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}.cols button{width:36px;height:36px;padding:0;border-radius:50%;border:2px solid #fff3}
.cols button.on{border-color:#fff}
.log{max-height:150px;overflow:auto;font-size:14px;margin-top:8px}.log div{padding:2px 0}
.c4{display:grid;grid-template-columns:repeat(7,1fr);gap:5px;background:#1d4fbf;padding:6px;border-radius:14px;max-width:420px;margin:8px auto}
.c4 div{aspect-ratio:1;border-radius:50%;background:#0b121c}.c4 .p0{background:#ff5a5f}.c4 .p1{background:#ffd23f}.c4 .w{box-shadow:0 0 0 3px #fff inset}
.c4b{display:grid;grid-template-columns:repeat(7,1fr);gap:5px;max-width:420px;margin:0 auto}.c4b button{padding:8px 0;font-size:18px}
.dice{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:10px 0}.dice div{width:58px;height:58px;border-radius:12px;background:#fff;color:#111;font-size:30px;font-weight:800;display:flex;align-items:center;justify-content:center}
.timer{font-size:46px;font-weight:800;text-align:center;font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:3px 10px;border-radius:999px;background:#24324a;font-size:13px;margin:2px}
a.gl{display:flex;gap:10px;align-items:center;text-decoration:none;color:var(--txt);background:#1c2a3d;border:1px solid var(--line);border-radius:12px;padding:10px}
a.gl img{width:44px;height:44px;border-radius:10px;object-fit:cover;background:#0b121c}a.gl b{display:block}a.gl span{font-size:12px;color:var(--mut)}
.hidden{display:none!important}
</style></head><body>
<header><img src="/icon-192.png" alt=""><h1>🎲 Spielecke</h1><div class="me" id="me"></div><button class="sec" id="quit" style="padding:8px 12px" title="Spielecke verlassen">🚪 Verlassen</button></header>
<div id="join" class="card hidden"><h2>Mitspielen</h2><div class="row"><input id="nm" maxlength="20" placeholder="Dein Name" autocomplete="nickname"><button id="go">Los!</button></div></div>
<div id="app" class="hidden">
  <div id="gamebox"></div>
  <div class="card" id="toolscard"><h2>🎲 Würfel und ⏳ Sanduhr</h2>
    <div id="dice" class="dice"></div><div class="mut" id="dicewho" style="text-align:center"></div>
    <div class="row" style="margin-top:8px"><select id="dn"><option value="1">1 Würfel</option><option value="2" selected>2 Würfel</option><option value="3">3 Würfel</option><option value="4">4 Würfel</option><option value="5">5 Würfel</option></select>
      <select id="ds"><option value="6">W6</option><option value="4">W4</option><option value="8">W8</option><option value="10">W10</option><option value="12">W12</option><option value="20">W20</option></select>
      <button id="roll">Würfeln</button></div>
    <div class="timer" id="timer" style="margin-top:12px">–</div>
    <div class="row"><button class="sec" data-s="30">30 s</button><button class="sec" data-s="60">1 min</button><button class="sec" data-s="120">2 min</button><button class="sec" data-s="300">5 min</button><button class="sec" data-s="0">Stopp</button></div>
  </div>
  <div class="card"><h2>🏆 Punkte</h2><div id="players"></div><div id="hostbox" class="hidden" style="margin-top:8px"><button class="sec" id="resetsc">Punkte auf 0</button></div></div>
  <div class="card hidden" id="simcard"><h2>🎯 Team gegen MoveEye (3D-Simulator)</h2><p class="mut" id="simtxt"></p>
    <a id="simgo" href="#" target="_blank" rel="noopener" style="display:block;text-align:center;text-decoration:none;background:var(--amber);color:#0e1621;font-weight:700;padding:13px;border-radius:12px">🏃 Mitspielen</a></div>
  <div class="card" id="collcard"><h2>🕹 Spielesammlung (für dich allein)</h2><div id="coll" class="grid"></div></div>
</div>
<script>
const KEY = "__KEY__", BASE = "/p/" + KEY;
const $ = s => document.querySelector(s);
let PID = "", V = null, SEQ = -1, busy = false, drawing = null, myColor = "#111111", myWidth = 5, pending = [], lastBeep = 0;
try { PID = localStorage.getItem("mwp-" + KEY) || ""; } catch (e) {}
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
async function act(a, extra) { const r = await fetch(BASE + "/a", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({pid: PID, a: a}, extra || {}))}).then(x => x.json()).catch(() => ({ok: false, error: "keine Verbindung"}));
  if (!r.ok && r.error) toast(r.error); if (r.v) { r.v._skew = (r.v.now || Date.now() / 1000) - Date.now() / 1000; V = r.v; render(); } return r; }
function toast(t) { let e = $("#toast"); if (!e) { e = document.createElement("div"); e.id = "toast"; e.style.cssText = "position:fixed;left:50%;bottom:24px;transform:translateX(-50%);background:#000c;padding:10px 16px;border-radius:12px;z-index:9"; document.body.appendChild(e); }
  e.textContent = t; e.hidden = false; clearTimeout(e._t); e._t = setTimeout(() => e.hidden = true, 2500); }
function beep(f, d) { try { const ac = beep.ac || (beep.ac = new (window.AudioContext || window.webkitAudioContext)()); const o = ac.createOscillator(), g = ac.createGain(); o.frequency.value = f || 880; g.gain.value = .2; o.connect(g); g.connect(ac.destination); o.start(); o.stop(ac.currentTime + (d || .15)); } catch (e) {} }
function speak(t) { try { speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(t); u.lang = "de-CH"; u.rate = .95; speechSynthesis.speak(u); } catch (e) {} }
async function join() { const name = $("#nm").value.trim(); if (!name) return;
  const r = await fetch(BASE + "/join", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({pid: PID, name: name})}).then(x => x.json()).catch(() => ({}));
  if (r.pid) { PID = r.pid; try { localStorage.setItem("mwp-" + KEY, PID); localStorage.setItem("mwp-name", name); } catch (e) {} SEQ = -1; poll(); } else toast(r.error || "Beitreten ging nicht"); }
$("#quit").onclick = async () => {                 // 2.95.36: leave the game corner (also from inside a game)
  if (V && V.me && !confirm("Spielecke verlassen? Deine Punkte gehen verloren.")) return;
  if (V && V.me) { try { await act("quit"); } catch (e) {} }
  try { localStorage.removeItem("mwp-" + KEY); } catch (e) {}
  location.href = "/spiele";
};
$("#go").onclick = join; $("#nm").onkeydown = e => { if (e.key === "Enter") join(); };
try { $("#nm").value = localStorage.getItem("mwp-name") || ""; } catch (e) {}
async function poll() {
  if (busy) return; busy = true;
  const askedPid = PID;
  try { const r = await fetch(BASE + "/s?pid=" + encodeURIComponent(PID) + "&seq=" + SEQ, {cache: "no-store"});
    if (r.status === 404) { document.body.innerHTML = "<div class='card' style='margin:20px'><h2>Die Spielecke ist geschlossen.</h2><p class='mut'>Frag den Gastgeber nach dem neuen QR-Code.</p></div>"; return; }
    const j = await r.json();
    if (askedPid !== PID) { busy = false; SEQ = -1; setTimeout(poll, 0); return; }   // joined meanwhile: ask again at once (2.95.36)
    V = j; V._skew = (j.now || Date.now() / 1000) - Date.now() / 1000; SEQ = j.seq; render(); } catch (e) { await new Promise(r => setTimeout(r, 1500)); }
  busy = false; setTimeout(poll, 50);
}
const GAMES = [["lobby", "🏠 Lobby", "Alle sammeln"], ["quiz", "🔔 Quiz mit Buzzer", "Wer zuerst drückt, antwortet"], ["wolf", "🐺 Werwolf", "Der Erzähler führt durch die Nacht"],
  ["draw", "🎨 Montagsmaler", "Einer zeichnet, alle raten"], ["c4", "🔴 Vier gewinnt", "Zwei spielen, alle schauen zu"],
  ["slf", "🏙 Stadt-Land-Fluss", "Buchstabe ziehen, schnell schreiben"], ["guess", "📏 Schätzfrage", "Wer am nächsten liegt, gewinnt"],
  ["taboo", "🗣 Begriffe erklären", "Erklären ohne verbotene Wörter"], ["whoami", "🤔 Wer bin ich?", "Alle sehen deinen Begriff – nur du nicht"],
  ["react", "⚡ Reaktion", "Wer tippt am schnellsten?"], ["ships", "🚢 Schiffe versenken", "Zwei gegeneinander"]];
function render() {
  if (!V) return;
  if (!V.me) { $("#join").classList.remove("hidden"); $("#app").classList.add("hidden"); return; }
  $("#join").classList.add("hidden"); $("#app").classList.remove("hidden");
  if (V.nt && V.nt !== render.nt && typeof ntMeasure === "function") {      // 2.95.52: the network check measures by itself
    render.nt = V.nt; const me = (V.players.find(p => p.id === V.me) || {}).name || "";
    toast("📶 Netz-Check läuft …");
    ntMeasure(me, () => {}, "party").then(r => toast("📶 " + ({good: "Gute Verbindung", fair: "Verbindung geht so", weak: "Schwache Verbindung"}[r.grade] || "gemessen")
      + (r.down != null ? " · " + (+r.down).toFixed(1) + " Mbit/s" : "") + (r.rtt != null ? " · " + Math.round(r.rtt) + " ms" : "")));
  }
  const me = V.players.find(p => p.id === V.me) || {};
  $("#me").innerHTML = esc(me.name) + (V.host ? " · 👑 Gastgeber" : "") + "<br>" + me.score + " Punkte";
  // players
  $("#players").innerHTML = V.players.map(p => `<div class="pl ${p.on ? "" : "off"}"><span class="n">${p.host ? "👑 " : ""}${esc(p.name)}</span>`
    + (V.host ? `<button class="sec" style="padding:6px 10px" onclick="act('score',{id:'${p.id}',n:-1})">−</button> <button class="sec" style="padding:6px 10px" onclick="act('score',{id:'${p.id}',n:1})">+</button> ${p.host ? "" : `<button class="sec" style="padding:6px 8px;font-size:12px" onclick="act('makehost',{id:'${p.id}'})">👑</button>`}` : "")
    + `<span class="s">${p.score}</span></div>`).join("");
  $("#hostbox").classList.toggle("hidden", !V.host);
  // tools
  const D = V.tools.dice; $("#dice").innerHTML = D ? D.vals.map(x => `<div>${x}</div>`).join("") : "";
  $("#dicewho").textContent = D ? D.by + " hat gewürfelt (W" + D.sides + ")" + (D.vals.length > 1 ? " · Summe " + D.vals.reduce((a, b) => a + b, 0) : "") : "";
  if (D && D.t !== render.lastDice) { render.lastDice = D.t; beep(660, .08); }
  // 2.98.7: the game of the 3D simulator (opened together with the game corner)
  const SG = V.sim; $("#simcard").classList.toggle("hidden", !SG);
  if (SG) { $("#simgo").href = SG.url; $("#simtxt").textContent = "Schleich mit dem Handy unentdeckt an der Kamera vorbei zum Ziel. "
    + (SG.runners >= SG.max ? "Alle " + SG.max + " Läuferplätze sind besetzt – du schaust zuerst durch die Kamera zu." : (SG.max - SG.runners) + " von " + SG.max + " Läuferplätzen frei.")
    + (SG.round === "play" ? " Eine Runde läuft gerade." : ""); }
  // collection
  const GG = {touch: "👆 Für Handy und Tablet (Touch)", buttons: "🎮 Mit Bildschirm-Tasten"};        // 2.95.54: touch games first
  const gsorted = (V.games || []).slice().sort((a, b) => (a.input === "buttons") - (b.input === "buttons"));
  let gprev = null;
  $("#coll").innerHTML = gsorted.length ? gsorted.map(g => { const hd = g.input && g.input !== gprev ? `<div style="font-weight:700;margin:12px 0 4px;grid-column:1/-1">${GG[g.input] || ""}</div>` : ""; gprev = g.input; return hd + `<a class="gl" href="${BASE}/g/${g.dir}/" target="_blank">${/\./.test(g.icon || "") ? `<img src="${BASE}/g/${g.dir}/${g.icon}" alt="" onerror="this.style.visibility='hidden'">` : `<span style="font-size:30px;width:44px;text-align:center;flex:0 0 44px">${esc(g.icon || "🎮")}</span>`}<div><b>${esc(g.name)}</b><span>${esc(g.desc || "")}</span></div></a>`; }).join("")
    : "<div class='mut'>Die Spielesammlung ist auf diesem Gerät noch nicht installiert (MoveEye → Reiter Spielecke).</div>";
  renderGame();
}
function gameChooser() {
  return `<div class="card"><h2>Was spielen wir?</h2><div class="grid">${GAMES.map(g => `<button class="gbtn ${V.game === g[0] ? "on" : ""}" onclick="act('game',{game:'${g[0]}'})"><b>${g[1]}</b><span>${g[2]}</span></button>`).join("")}</div></div>`;
}
function renderGame() {
  const box = $("#gamebox"); let h = "";
  if (V.host && V.game === "lobby") h += gameChooser();
  if (V.game === "lobby") h += `<div class="card"><h2>🏠 Lobby</h2><div class="mut">${V.host ? "Du bist Gastgeber: wähle oben ein Spiel." : "Warte, bis " + esc(V.hostname || "der Gastgeber") + " ein Spiel wählt."}</div>
      <div style="margin-top:8px">${V.players.map(p => `<span class="pill">${esc(p.name)}</span>`).join("")}</div></div>`;
  if (V.game !== "lobby") h += `<div class="row" style="margin-bottom:10px"><span class="mut">${(GAMES.find(g => g[0] === V.game) || [])[1] || ""}</span>${V.host ? `<button class="sec" style="flex:0 0 auto" onclick="act('game',{game:'lobby'})">↩ Andere Spiele</button>` : `<span class="mut" style="flex:0 0 auto">Spiel wechseln: ${esc(V.hostname || "Gastgeber")}</span>`}</div>`;
  if (V.game === "quiz") h += quizHtml();
  if (V.game === "wolf") h += wolfHtml();
  if (V.game === "draw") h += drawHtml();
  if (V.game === "c4") h += c4Html();
  if (V.game === "slf") h += slfHtml();
  if (V.game === "guess") h += guessHtml();
  if (V.game === "taboo") h += tabooHtml();
  if (V.game === "ships") h += shipsHtml();
  if (V.game === "react") h += reactHtml();
  if (V.game === "whoami") h += whoHtml();
  const G_ = V[V.game] || {}, stage = V.game + "|" + (G_.phase || "") + "|" + (G_.round || G_.n || "");
  if (box.dataset.h !== h || V.game === "draw") {
    if (V.game === "draw" && box.querySelector("canvas") && box.dataset.g === "draw" && box.dataset.drawer === V.draw.drawer) { drawUpdate(); return; }
    // keep what is being typed (the page is drawn new when something changes)
    const keep = {}, fe = document.activeElement, fid = fe && box.contains(fe) && fe.id ? fe.id : "";
    if (box.dataset.stage === stage) box.querySelectorAll("input[id]:not([type=checkbox]):not([type=number])").forEach(x => keep[x.id] = x.value);
    box.innerHTML = h; box.dataset.h = h; box.dataset.g = V.game; box.dataset.drawer = V.draw ? V.draw.drawer : ""; box.dataset.stage = stage;
    for (const id in keep) { const x = document.getElementById(id); if (x && x.value !== keep[id]) { x.value = keep[id]; x._sent = undefined; } }
    if (fid) { const f = document.getElementById(fid); if (f) { f.focus(); try { f.setSelectionRange(f.value.length, f.value.length); } catch (e) {} } }
    if (V.game === "draw") drawSetup();
  }
  if (V.game === "react") reactArm();
}
// ---- quiz ----
function quizHtml() { const Q = V.quiz, first = Q.order[0];
  if (V.host) return `<div class="card"><h2>🔔 Quiz · Frage ${Q.n}</h2><div class="big" style="font-size:19px">${esc(Q.q)}</div><div class="mut" style="text-align:center">Antwort: <b>${esc(Q.a)}</b></div>
    <div class="row" style="margin-top:10px"><button class="sec" onclick="act('showq')">👁 Frage allen zeigen</button><button class="sec" onclick="act('nextq')">⏭ Andere Frage</button></div>
    <div class="big">${Q.phase === "wait" ? "Bereit?" : Q.phase === "open" ? "Buzzer sind frei …" : "🔔 " + esc(first ? first.name : "")}</div>
    ${Q.order.length > 1 ? `<div class="mut" style="text-align:center">danach: ${Q.order.slice(1).map(x => esc(x.name)).join(", ")}</div>` : ""}
    <div class="row" style="margin-top:8px">${Q.phase === "locked" ? `<button class="grn" onclick="act('right')">✓ Richtig (+1)</button><button class="red" onclick="act('wrong')">✗ Falsch</button>` : `<button onclick="act('open')">🔓 Buzzer freigeben</button>`}</div>
    <div class="mut" style="margin-top:8px">Tipp: Du kannst auch eigene Fragen vorlesen – einfach «Buzzer freigeben».</div></div>`;
  const mine = Q.order.findIndex(x => x.id === V.me);
  if (Q.phase === "locked" && first && first.id === V.me && render.lastBuzz !== Q.order.length) { render.lastBuzz = Q.order.length; beep(988, .3); }
  return `<div class="card"><h2>🔔 Quiz · Frage ${Q.n}</h2>${Q.q ? `<div class="big" style="font-size:19px">${esc(Q.q)}</div>` : ""}
    <button class="buzz" ${Q.phase !== "open" || mine >= 0 ? "disabled" : ""} onclick="act('buzz');navigator.vibrate&&navigator.vibrate(80)">BUZZ</button>
    <div class="big">${Q.phase === "wait" ? "Warte auf die Frage …" : Q.phase === "open" ? (mine >= 0 ? "Gedrückt!" : "Jetzt drücken!") : first && first.id === V.me ? "🎤 Du bist dran!" : "🔔 " + esc(first ? first.name : "")}</div></div>`;
}
// ---- werewolf ----
function wolfHtml() { const W = V.wolf;
  if (V.host) {
    if (W.phase === "setup") return `<div class="card"><h2>🐺 Werwolf · du bist Erzähler</h2><div class="mut">Mitspieler (ohne dich): ${V.players.length - 1}. Rollen:</div>
      <div class="row" style="margin-top:8px"><label>🐺 Werwölfe<input type="number" min="1" max="6" value="${W.cfg.wolf || 1}" onchange="act('cfg',{wolf:+this.value})"></label>
      <label>🔮 Seherin<input type="number" min="0" max="1" value="${W.cfg.seer || 0}" onchange="act('cfg',{seer:+this.value})"></label>
      <label>🧪 Hexe<input type="number" min="0" max="1" value="${W.cfg.witch || 0}" onchange="act('cfg',{witch:+this.value})"></label></div>
      <button style="margin-top:10px;width:100%" onclick="act('start')">Rollen verteilen und Nacht beginnen</button></div>`;
    return `<div class="card"><h2>${W.phase === "night" ? "🌙 Nacht" : "☀️ Tag"}</h2><div class="big" style="font-size:18px">${esc(W.text)}</div>
      <div class="row"><button class="sec" onclick="speak(${JSON.stringify(W.text).replace(/"/g, "&quot;")})">🔊 Vorlesen</button><button onclick="act('next').then(()=>speak(V.wolf.text))">Weiter ▶</button></div>
      ${W.winner ? `<div class="big">${esc(W.winner)}</div>` : ""}
      <h2 style="margin-top:14px">Spieler (antippen = tot / lebendig)</h2>${W.roles.map(r => `<div class="pl ${r.alive ? "" : "off"}"><span class="n">${r.alive ? "" : "💀 "}${esc(r.name)}</span><span class="mut">${esc(r.role)}</span></div>`).join("")}
      <div class="row" style="margin-top:6px">${W.alive.map(p => `<button class="sec" style="flex:0 0 auto;padding:6px 10px" onclick="act('kill',{id:'${p.id}'})">${p.alive ? "☠ " : "↺ "}${esc(p.name)}</button>`).join("")}</div>
      <h2 style="margin-top:14px">Abstimmung</h2><div class="row">${W.voting ? `<button class="red" onclick="act('voteclose')">Abstimmung beenden (${W.votes})</button>` : `<button onclick="act('voteopen')">🗳 Abstimmung starten</button>`}</div>
      ${(W.tally || []).map(x => `<div class="pl"><span class="n">${esc(x.name)}</span><b>${x.n}</b><button class="sec" style="flex:0 0 auto;padding:6px 10px;margin-left:8px" onclick="act('kill',{id:'${x.id}'})">☠</button></div>`).join("")}
      <button class="sec" style="margin-top:10px" onclick="act('game',{game:'wolf'})">Neues Spiel</button></div>`;
  }
  if (W.phase === "setup") return `<div class="card"><h2>🐺 Werwolf</h2><div class="mut">${esc(V.hostname)} ist Erzähler und verteilt gleich die Rollen.</div></div>`;
  const alive = (W.alive.find(p => p.id === V.me) || {}).alive !== false;
  return `<div class="card"><h2>${W.phase === "night" ? "🌙 Nacht" : "☀️ Tag"}${alive ? "" : " · 💀 du bist tot"}</h2>
    <div class="role" onpointerdown="this.textContent=${JSON.stringify(W.role).replace(/"/g, "&quot;")}" onpointerup="this.textContent='👆 Gedrückt halten: deine Rolle'" onpointerleave="this.textContent='👆 Gedrückt halten: deine Rolle'">👆 Gedrückt halten: deine Rolle</div>
    ${W.winner ? `<div class="big">${esc(W.winner)}</div>` : ""}
    ${W.voting && alive ? `<h2 style="margin-top:12px">🗳 Wer ist der Werwolf?</h2><div class="grid">${W.alive.filter(p => p.alive && p.id !== V.me).map(p => `<button class="${W.myvote === p.id ? "" : "sec"}" onclick="act('vote',{id:'${p.id}'})">${esc(p.name)}</button>`).join("")}</div>` : ""}
    </div>`;
}
// ---- drawing ----
function drawHtml() { const D = V.draw, mine = D.drawer === V.me;
  return `<div class="card"><h2>🎨 Montagsmaler · Runde ${D.round} · ⏳ <span id="dleft">${D.left}</span> s</h2>
    <div class="big" id="dword" style="font-size:20px">${mine ? "Zeichne: " + esc(D.word) : esc(D.drawername) + " zeichnet · " + esc(D.hint)}</div>
    <canvas id="cv" width="800" height="600"></canvas>
    ${mine ? `<div class="cols">${["#111111", "#e0262c", "#1d6fe0", "#2a9d3a", "#f2b705", "#8b4513", "#9b59b6", "#ffffff"].map(c => `<button style="background:${c}" data-c="${c}"></button>`).join("")}
      <button class="sec" style="width:auto;border-radius:12px;padding:0 12px" id="thick">✏️ dick</button></div>
      <div class="row"><button class="sec" onclick="act('clear')">🗑 Leeren</button><button class="sec" onclick="act('skip')">⏭ Anderes Wort</button></div>`
    : `<div class="row" style="margin-top:8px"><input id="gs" placeholder="${D.iguessed ? "Erraten! ✅" : "Dein Tipp …"}" ${D.iguessed ? "disabled" : ""} autocomplete="off"><button id="gsb" ${D.iguessed ? "disabled" : ""}>Raten</button></div>`}
    <div class="log" id="dlog"></div>${D.last ? `<div class="mut">Letztes Wort: ${esc(D.last)}</div>` : ""}</div>`;
}
function drawSetup() { const cv = $("#cv"); if (!cv) return; const ctx = cv.getContext("2d"); const D = V.draw;
  if (D.drawer === V.me) {
    document.querySelectorAll(".cols [data-c]").forEach(b => { b.onclick = () => { myColor = b.dataset.c; document.querySelectorAll(".cols [data-c]").forEach(x => x.classList.toggle("on", x === b)); }; });
    $("#thick").onclick = () => { myWidth = myWidth === 5 ? 14 : 5; $("#thick").textContent = myWidth === 5 ? "✏️ dick" : "✏️ dünn"; };
    const pos = e => { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height]; };
    cv.onpointerdown = e => { cv.setPointerCapture(e.pointerId); drawing = {p: [pos(e)], c: myColor, w: myWidth}; };
    cv.onpointermove = e => { if (!drawing) return; const p = pos(e); const l = drawing.p[drawing.p.length - 1]; drawing.p.push(p); seg(ctx, l, p, drawing.c, drawing.w);
      if (drawing.p.length >= 30) { pending.push(drawing); drawing = {p: [p], c: drawing.c, w: drawing.w}; flush(); } };
    cv.onpointerup = cv.onpointercancel = () => { if (drawing) { pending.push(drawing); drawing = null; flush(); } };
  } else {
    const send = () => { const t = $("#gs").value.trim(); if (t) { act("guess", {t: t}); $("#gs").value = ""; } };
    if ($("#gsb")) { $("#gsb").onclick = send; $("#gs").onkeydown = e => { if (e.key === "Enter") send(); }; }
  }
  drawUpdate(true);
}
function seg(ctx, a, b, c, w) { ctx.strokeStyle = c; ctx.lineWidth = w; ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.beginPath(); ctx.moveTo(a[0] * 800, a[1] * 600); ctx.lineTo(b[0] * 800, b[1] * 600); ctx.stroke(); }
async function flush() { if (flush.busy) return; flush.busy = true; while (pending.length) { const s = pending.shift(); await act("stroke", {p: s.p, c: s.c, w: s.w}); } flush.busy = false; }
function drawUpdate(full) { const cv = $("#cv"); if (!cv) return; const D = V.draw, ctx = cv.getContext("2d");
  if (full || (cv._n || 0) > D.strokes.length) { ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, 800, 600); cv._n = 0; }
  if (!(D.drawer === V.me && drawing)) for (let i = cv._n || 0; i < D.strokes.length; i++) { const s = D.strokes[i]; for (let k = 1; k < s.p.length; k++) seg(ctx, s.p[k - 1], s.p[k], s.c, s.w); }
  cv._n = D.strokes.length;
  if ($("#dleft")) $("#dleft").textContent = D.left;
  $("#dlog").innerHTML = D.log.slice().reverse().map(x => `<div><b>${esc(x.n)}</b> ${esc(x.t)}</div>`).join("");
  if ($("#gs") && D.iguessed) { $("#gs").disabled = true; $("#gs").placeholder = "Erraten! ✅"; $("#gsb").disabled = true; }
  const w = $("#dword"); if (w) w.textContent = D.drawer === V.me ? "Zeichne: " + D.word : D.drawername + " zeichnet · " + D.hint;
}
// ---- connect four ----
function c4Html() { const C = V.c4, seat = C.seats.findIndex(s => s && s.id === V.me), my = seat >= 0 && C.turn === seat && C.win < 0 && C.seats[0] && C.seats[1];
  const lw = new Set((C.line || []).map(x => x[0] * 7 + x[1]));
  const st = C.win === 2 ? "Unentschieden!" : C.win >= 0 ? "🏆 " + esc(C.seats[C.win].name) + " gewinnt!" : !(C.seats[0] && C.seats[1]) ? "Zwei Spieler setzen sich hin" : my ? "Du bist dran!" : esc(C.seats[C.turn].name) + " ist dran";
  return `<div class="card"><h2>🔴 Vier gewinnt</h2><div class="row">${[0, 1].map(i => C.seats[i] ? `<span class="pill">${i ? "🟡" : "🔴"} ${esc(C.seats[i].name)}</span>` : `<button class="sec" onclick="act('sit',{seat:${i}})">${i ? "🟡" : "🔴"} Hinsetzen</button>`).join("")}</div>
    <div class="big">${st}</div>
    ${my ? `<div class="c4b">${[0, 1, 2, 3, 4, 5, 6].map(c => `<button onclick="act('drop',{col:${c}})">⬇</button>`).join("")}</div>` : ""}
    <div class="c4">${C.board.map((r, ri) => r.map((x, ci) => `<div class="${x >= 0 ? "p" + x : ""} ${lw.has(ri * 7 + ci) ? "w" : ""}"></div>`).join("")).join("")}</div>
    <div class="row">${C.win >= 0 ? `<button onclick="act('reset',{swap:1})">Nochmal (Farben tauschen)</button>` : ""}${seat >= 0 ? `<button class="sec" onclick="act('leave')">Aufstehen</button>` : ""}</div></div>`;
}
// ---- more games (2.95.32) ----
function slfHtml() { const S = V.slf, cats = S.cats || [];
  let h = `<div class="card"><h2>🏙 Stadt-Land-Fluss${S.round ? " · Runde " + S.round : ""}</h2>`;
  if (S.phase === "setup") {
    h += V.host ? `<div class="mut">Kategorien (mit Komma getrennt):</div><input id="slfcats" value="${esc(cats.join(", "))}" onchange="act('cats',{t:this.value})">
      <button style="width:100%;margin-top:10px" onclick="act('start')">🎲 Buchstabe ziehen und los!</button>` : `<div class="mut">Gleich zieht ${esc(V.hostname)} einen Buchstaben. Kategorien: ${esc(cats.join(", "))}</div>`;
    return h + "</div>";
  }
  if (S.phase === "play") {
    h += `<div class="big" style="font-size:54px;margin:4px 0">${esc(S.letter)}</div>`
      + (S.stop_left >= 0 ? `<div class="big" style="color:var(--red)">⛔ ${esc(S.stop_by)} ruft STOPP! Noch <span class="slfleft" data-end="${Date.now() / 1000 + S.stop_left}">${Math.ceil(S.stop_left)}</span> s</div>` : "")
      + cats.map((c, i) => `<label class="mut" style="display:block;margin-top:8px">${esc(c)}<input id="slf${i}" data-i="${i}" class="slfin" autocomplete="off" autocapitalize="words" value="${esc((S.mine || {})[i] || "")}"></label>`).join("")
      + `<div class="row" style="margin-top:12px"><button class="red" onclick="slfSave();act('stop')">✋ STOPP!</button>${V.host ? `<button class="sec" onclick="slfSave();act('end')">Runde beenden</button>` : ""}</div>`
      + `<div class="mut" style="margin-top:6px">Fertig: <span id="slfdone">${S.done.map(esc).join(", ") || "–"}</span></div>`;
    return h + "</div>";
  }
  // review
  h += `<div class="mut">Buchstabe <b>${esc(S.letter)}</b> · 20 = als Einzige(r) in der Kategorie, 10 = eigene Antwort, 5 = gleich wie jemand · ${V.host ? "Antippen = ungültig/gültig" : "Der Gastgeber kann Antworten streichen"}</div>
    <div style="overflow-x:auto;margin-top:8px"><table style="border-collapse:collapse;width:100%;font-size:14px"><tr><th style="text-align:left">Spieler</th>${cats.map(c => `<th style="text-align:left;padding:4px">${esc(c)}</th>`).join("")}<th>Σ</th></tr>`
    + (S.table || []).map(r => `<tr style="border-top:1px solid var(--line)"><td style="padding:4px"><b>${esc(r.name)}</b></td>${r.ans.map((a, i) => `<td style="padding:4px;${r.veto[i] ? "text-decoration:line-through;opacity:.5" : ""}" ${V.host ? `onclick="act('veto',{id:'${r.id}',i:${i}})"` : ""}>${esc(a) || "–"} <span class="mut">${r.pts[i]}</span></td>`).join("")}<td style="padding:4px"><b>${r.pts.reduce((a, b) => a + b, 0)}</b></td></tr>`).join("")
    + `</table></div>` + (V.host ? `<button class="grn" style="width:100%;margin-top:10px" onclick="act('award')">✓ Punkte gutschreiben (5 = 1 Punkt) und nächste Runde</button>` : "");
  return h + "</div>";
}
function slfSave() { document.querySelectorAll(".slfin").forEach(x => { if (x.value !== x._sent) { x._sent = x.value; act("ans", {i: +x.dataset.i, t: x.value}); } }); }
document.addEventListener("input", e => { if (e.target.classList && e.target.classList.contains("slfin")) { clearTimeout(e.target._t); e.target._t = setTimeout(slfSave, 600); } });
function guessHtml() { const G = V.guess;
  if (G.phase === "setup") return `<div class="card"><h2>📏 Schätzfrage</h2><div class="mut">Wer am nächsten dran ist, bekommt einen Punkt.</div>${V.host ? `<button style="width:100%;margin-top:10px" onclick="act('next')">Erste Frage</button>` : ""}</div>`;
  let h = `<div class="card"><h2>📏 Schätzfrage ${G.n}</h2><div class="big" style="font-size:19px">${esc(G.q)}</div>`;
  if (G.phase === "ask") {
    if (V.host) h += `<div class="mut" style="text-align:center">Antwort: <b>${fmtN(G.answer)} ${esc(G.unit)}</b> · ${G.count} Schätzungen</div><button style="width:100%;margin-top:10px" onclick="act('reveal')">🎯 Auflösen</button>`;
    else h += `<div class="row"><input id="gsn" inputmode="decimal" placeholder="Deine Schätzung${G.unit ? " (" + esc(G.unit) + ")" : ""}" autocomplete="off"><button onclick="if($('#gsn').value.trim())act('guess',{n:$('#gsn').value})">Abgeben</button></div>`
      + `<div class="mut" style="margin-top:6px">${G.mine != null ? "Deine Schätzung: <b>" + fmtN(G.mine) + "</b> (du kannst sie noch ändern)" : "Noch keine Schätzung abgegeben"} · ${G.count} haben geschätzt</div>`;
  } else {
    h += `<div class="big">${fmtN(G.answer)} ${esc(G.unit)}</div>` + G.list.map(r => `<div class="pl"><span class="n">${r.win ? "🏆 " : ""}${esc(r.name)}</span><span>${fmtN(r.v)}</span><span class="mut" style="margin-left:10px">±${fmtN(r.d)}</span></div>`).join("")
      + (V.host ? `<button style="width:100%;margin-top:10px" onclick="act('next')">Nächste Frage</button>` : "");
  }
  return h + "</div>";
}
function fmtN(x) { return x == null ? "" : Number(x).toLocaleString("de-CH", {maximumFractionDigits: 2}); }
function tabooHtml() { const T = V.taboo, mine = T.explainer === V.me;
  let h = `<div class="card"><h2>🗣 Begriffe erklären${T.round ? " · Runde " + T.round : ""}</h2>`;
  if (T.phase !== "turn") {
    h += `<div class="mut">Eine Person erklärt Begriffe, ohne die verbotenen Wörter zu sagen. Die anderen rufen laut. Pro erratenem Begriff gibt es je einen Punkt für den Erklärer und für den, der es erraten hat.</div>`
      + (V.host ? `<div class="row" style="margin-top:8px"><span class="mut">Zeit pro Runde</span><select onchange="act('secs',{s:+this.value})">${[45, 60, 90, 120].map(s => `<option value="${s}" ${T.secs === s ? "selected" : ""}>${s} s</option>`).join("")}</select></div>` : "")
      + `<div class="big">Als Nächstes erklärt: ${esc(T.nextname)}</div>`
      + (V.host || T.next === V.me ? `<button style="width:100%" onclick="act('start')">▶ Runde starten</button>` : "");
  } else if (mine) {
    h += `<div class="mut" style="text-align:center">⏳ <span class="tbleft" data-end="${Date.now() / 1000 + T.left}">${T.left}</span> s · ${T.n} erklärt</div>
      <div style="background:#fff;color:#111;border-radius:14px;padding:14px;text-align:center;margin:8px 0"><div style="font-size:28px;font-weight:800">${esc(T.word)}</div>
      <div style="border-top:2px solid #e0262c;margin-top:8px;padding-top:6px;color:#b0181d;font-weight:700">${T.forbidden.map(esc).join("<br>")}</div></div>
      <div class="mut">Wer hat es erraten?</div><div class="row">${V.players.filter(p => p.id !== V.me).map(p => `<button class="grn" style="flex:0 0 auto" onclick="act('ok',{by:'${p.id}'})">✓ ${esc(p.name)}</button>`).join("")}</div>
      <div class="row" style="margin-top:8px"><button class="red" onclick="act('taboo')">🚫 Tabu gesagt</button><button class="sec" onclick="act('skip')">⏭ Weiter</button></div>`;
  } else {
    h += `<div class="big">🗣 ${esc(T.explainername)} erklärt</div><div class="timer"><span class="tbleft" data-end="${Date.now() / 1000 + T.left}">${T.left}</span></div><div class="mut" style="text-align:center">Laut raten! ${T.n} erraten</div>`;
  }
  if (T.log.length) h += `<div class="log">${T.log.slice().reverse().map(x => `<div>${esc(x)}</div>`).join("")}</div>`;
  return h + "</div>";
}
function shipsHtml() { const S = V.ships, me = S.seat, both = S.seats[0] && S.seats[1], go = both && S.ready[0] && S.ready[1];
  const cell = (v, own) => ["", own ? "background:#5b6b82" : "", "background:#1d6fe0", "background:#e9a23b", "background:#e0262c"][v] || "";
  const sym = v => ["", "", "•", "✸", "✖"][v];
  const grid = (b, own, shoot) => `<div style="display:grid;grid-template-columns:repeat(8,1fr);gap:3px;background:#0b2a4a;padding:5px;border-radius:10px;max-width:360px;margin:6px auto">${b.map((r, y) => r.map((v, x) => `<div style="aspect-ratio:1;border-radius:4px;background:#103c66;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:800;${cell(v, own)};${shoot && v < 2 ? "cursor:pointer" : ""}" ${shoot && v < 2 ? `onclick="act('shoot',{x:${x},y:${y}})"` : ""}>${sym(v)}</div>`).join("")).join("")}</div>`;
  const st = S.win >= 0 ? "🏆 " + esc(S.seats[S.win].name) + " gewinnt!" : !both ? "Zwei Spieler setzen sich hin" : !go ? "Schiffe verteilen, dann «Bereit»" : me === S.turn ? "🎯 Du bist dran – schiess aufs Feld oben!" : esc(S.seats[S.turn].name) + " ist dran";
  let h = `<div class="card"><h2>🚢 Schiffe versenken</h2><div class="row">${[0, 1].map(i => S.seats[i] ? `<span class="pill">${i ? "🟡" : "🔴"} ${esc(S.seats[i].name)} ${S.ready[i] ? "✓" : ""} · ${S.left[i]} Schiffe</span>` : `<button class="sec" onclick="act('sit',{seat:${i}})">${i ? "🟡" : "🔴"} Hinsetzen</button>`).join("")}</div><div class="big">${st}</div>`;
  if (S.last && go) h += `<div class="mut" style="text-align:center">Letzter Schuss: ${esc(S.seats[S.last.by].name)} → ${"ABCDEFGH"[S.last.x]}${S.last.y + 1}: ${S.last.sunk ? "versenkt! 💥" : S.last.hit ? "Treffer!" : "Wasser"}</div>`;
  if (me >= 0) {
    h += `<div class="mut" style="text-align:center;margin-top:8px">Gegner</div>${grid(S.boards[1 - me], false, go && S.turn === me && S.win < 0)}<div class="mut" style="text-align:center">Deine Flotte</div>${grid(S.boards[me], true, false)}`;
    if (!go && S.win < 0) h += `<div class="row"><button class="sec" onclick="act('shuffle')">🔀 Neu verteilen</button>${S.ready[me] ? "" : `<button class="grn" onclick="act('ready')">✓ Bereit</button>`}</div>`;
  } else if (both) h += [0, 1].map(i => `<div class="mut" style="text-align:center;margin-top:8px">Flotte von ${esc(S.seats[i].name)}</div>${grid(S.boards[i], false, false)}`).join("");
  h += `<div class="row" style="margin-top:8px">${S.win >= 0 ? `<button onclick="act('reset')">Nochmal (Seiten tauschen)</button>` : ""}${me >= 0 ? `<button class="sec" onclick="act('leave')">Aufstehen</button>` : ""}</div>`;
  return h + "</div>";
}
function reactHtml() { const R = V.react, plays = !V.host || R.hostplays;
  let h = `<div class="card"><h2>⚡ Reaktion${R.round ? " · Runde " + R.round : ""}</h2>`;
  if (R.phase === "wait") {
    h += plays ? `<button id="rbtn" class="rbtn" style="width:100%;height:46vh;font-size:30px;border-radius:20px;background:#e0262c" data-go="${R.go_at}">${R.mine != null ? (R.mine < 0 ? "Zu früh! 😬" : Math.round(R.mine) + " ms") : "Warten …<br><span style='font-size:16px;font-weight:400'>Tippen, sobald es GRÜN wird</span>"}</button>`
      : `<div class="big">Gleich wird es grün …</div>`;
  } else {
    h += `<div class="mut">Alle warten, bis der Knopf grün wird – dann so schnell wie möglich tippen. Wer zu früh tippt, scheidet aus.</div>`;
    if (R.phase === "done") h += `<div class="big">${R.winner ? "🏆 " + esc(R.winner) : "Niemand gültig"}</div>` + R.res.map(r => `<div class="pl"><span class="n">${r.me ? "<b>" + esc(r.name) + "</b>" : esc(r.name)}</span><span>${r.ms < 0 ? "zu früh" : Math.round(r.ms) + " ms"}</span></div>`).join("");
  }
  if (V.host && R.phase !== "wait") h += `<button style="width:100%;margin-top:10px" onclick="act('start')">▶ ${R.round ? "Nochmal" : "Start"}</button><label class="mut" style="display:flex;gap:8px;align-items:center;margin-top:8px"><input type="checkbox" style="width:auto" ${R.hostplays ? "checked" : ""} onchange="act('hostplays')"> Ich spiele auch mit</label>`;
  return h + "</div>";
}
function reactArm() { const b = $("#rbtn"); if (!b || b._armed === b.dataset.go || V.react.mine != null) return; b._armed = b.dataset.go;
  const goLocal = (+b.dataset.go - (V._skew || 0)) * 1000; let green = false;
  clearTimeout(reactArm.t); reactArm.t = setTimeout(() => { green = true; b.style.background = "#2fbf5b"; b.innerHTML = "JETZT!"; }, Math.max(0, goLocal - Date.now()));
  b.onpointerdown = e => { e.preventDefault(); if (b._done) return; b._done = true; clearTimeout(reactArm.t); const ms = green ? Date.now() - goLocal : -1;
    b.innerHTML = ms < 0 ? "Zu früh! 😬" : Math.round(ms) + " ms"; b.style.background = ms < 0 ? "#7a1d20" : "#1d6fe0"; act("tap", {ms}); };
}
function whoHtml() { const W = V.whoami;
  let h = `<div class="card"><h2>🤔 Wer bin ich?${W.round ? " · Runde " + W.round : ""}</h2>`;
  if (!W.round) return h + `<div class="mut">Jede Person bekommt einen Begriff (Tier, Beruf, Märchenfigur …), den alle anderen sehen – nur sie selbst nicht. Mit Ja/Nein-Fragen herausfinden, wer man ist!</div>${V.host ? `<button style="width:100%;margin-top:10px" onclick="act('start')">Begriffe verteilen</button>` : ""}</div>`;
  h += W.have ? (W.solved ? `<div class="big">Du bist: ${esc(W.mine)} ✅</div>` : `<div class="role">❓ Wer bin ich?</div><button class="grn" style="width:100%;margin-top:10px" onclick="if(confirm('Wirklich erraten? Erst bestätigen, wenn die anderen Ja sagen.'))act('solved')">🎉 Ich habe es erraten!</button>`) : `<div class="mut">Du bist erst nach dem Verteilen dazugekommen – du kannst trotzdem mitraten.</div>`;
  h += `<h2 style="margin-top:14px">Die anderen</h2>` + W.others.map(o => `<div class="pl"><span class="n">${esc(o.name)}</span><b style="font-size:18px">${esc(o.word)}</b>${o.solved ? " ✅" : ""}</div>`).join("");
  if (W.order.length) h += `<div class="mut" style="margin-top:8px">Erraten: ${W.order.map((n, i) => (i + 1) + ". " + esc(n)).join(" · ")} (3/2/1 Punkte)</div>`;
  if (V.host) h += `<button class="sec" style="width:100%;margin-top:10px" onclick="if(confirm('Neue Begriffe verteilen?'))act('start')">Neue Runde</button>`;
  return h + "</div>";
}
setInterval(() => { document.querySelectorAll(".slfleft,.tbleft").forEach(e => { e.textContent = Math.max(0, Math.ceil(+e.dataset.end - Date.now() / 1000)); }); }, 500);
// tools
$("#roll").onclick = () => act("dice", {n: +$("#dn").value, sides: +$("#ds").value});
document.querySelectorAll("[data-s]").forEach(b => b.onclick = () => act("timer", {s: +b.dataset.s}));
$("#resetsc").onclick = () => { if (confirm("Alle Punkte auf 0?")) act("resetscores"); };
setInterval(() => { if (!V) return; const T = V.tools.timer;
  if (T && T.end) { const left = Math.max(0, Math.round(T.end - Date.now() / 1000 - (V._skew || 0))); $("#timer").textContent = Math.floor(left / 60) + ":" + ("0" + left % 60).slice(-2);
    if (left === 0 && lastBeep !== T.end) { lastBeep = T.end; beep(880, .5); setTimeout(() => beep(660, .5), 600); navigator.vibrate && navigator.vibrate([300, 100, 300]); } }
  else $("#timer").textContent = "–";
  if (V.game === "draw" && $("#dleft")) $("#dleft").textContent = Math.max(0, (+$("#dleft").textContent || 0) - 1);
}, 1000);
poll();
__NTJS__
</script></body></html>
"""


SIMGAME = {"t": 0.0, "busy": False, "g": None}   # the game in the simulator, fetched now and then (2.95.22: «Team gegen MoveEye»)


def _simgame_fetch():
    try:
        r = sim_control({"action": "game_info"})
        if isinstance(r, dict) and r.get("ok") and r.get("open"):
            SIMGAME["g"] = {"round": r.get("round"), "mode": r.get("mode"), "left": r.get("left"), "cd": r.get("cd"),
                            "mwg": r.get("mwg"), "task": r.get("task") or "", "url": r.get("url") or "", "max": r.get("max"),
                            "runners": r.get("runners")}
        else:
            SIMGAME["g"] = None
    except Exception:
        SIMGAME["g"] = None
    finally:
        SIMGAME["busy"] = False


def sim_game():
    if not (CFG["sim_on"] and SIM["ok"]):
        SIMGAME["g"] = None
        return None
    if time.time() - SIMGAME["t"] > 2.5 and not SIMGAME["busy"]:
        SIMGAME["t"] = time.time(); SIMGAME["busy"] = True
        threading.Thread(target=_simgame_fetch, daemon=True).start()
    return SIMGAME["g"]


def sim_picture_ok():
    """2.95.93: the pictures of the simulator really arrive (not only its answers): a picture of the simulator camera was
    processed in the last 6 s. «connected» is only shown when this is true as well."""
    if not str(CFG["source"]).startswith("sim:"):
        return True
    w = WATCH_REF.get("w")
    try:
        return w is not None and STATE.get("source_status") == "connected" and time.time() - float(getattr(w, "_last_t0", 0) or 0) < 6.0
    except (TypeError, ValueError):
        return False


def sim_live():
    """2.95.93: the simulation is on AND really connected (answers and pictures) - only then the menus show it green"""
    return bool(CFG["sim_on"] and SIM["ok"] and time.time() - SIM["t"] < 5 and sim_picture_ok())


def sim_status():
    return {"game": sim_game(), "found": sim_found(), "auto": bool(CFG.get("sim_auto")), "autostart": bool(CFG.get("sim_autostart")), "auto_on": bool(CFG.get("sim_auto_on")), "autoupd": bool(CFG.get("sim_autoupd", True)), "stats": sim_stats(), "eco": bool(CFG.get("sim_eco")), "fps": int(CFG.get("sim_fps") or 6),
            "sim3d": {"version": SIM3D["version"], "size_mb": round(SIM3D["size"] / 1e6), "ready": sim3d_ready()},
            "simpy": {"version": SIMPY["version"], "size_kb": round(SIMPY["size"] / 1e3), "ready": sim3d_ready(SIMPY)},
            "view": bool(((SIM.get("info") or {}).get("view") or {}).get("input")) if CFG["sim_on"] else False,
            "versions": sim_versions() if CFG["sim_on"] and SIM["ok"] else None,
            "scan": {k: v for k, v in SIMSCAN.items()}, "installed": os.path.isfile(os.path.join(sim_dir(), "motionwatch_simulator.py")), "running": sim_running(), "on": bool(CFG["sim_on"]), "tunnel": {"active": tunnel_active()}, "ok": SIM["ok"] and time.time() - SIM["t"] < 5, "pic": sim_picture_ok(), "msg": SIM["msg"], "url": sim_base(),
            "dark": SIM["dark"], "ambient": SIM["ambient"], "sent": SIM["sent"]}


# ---- 2.95.86: the simulation has its own settings. Switching it on puts the real settings aside (and brings back the ones
# of the last simulation); switching back restores the real ones and asks which changes of the simulation to take over.
SIMPROF = {"q": None, "start": None}                               # the open question: {"t", "changes": [{key, label, real, sim}]}
_SIMPROF_SKIP_KEYS = {"source", "thermal_source"}          # 2.95.93: switched by the simulation itself (sim_set), never asked
_SIMPROF_AUTO_KEYS = {"min_area", "sensitivity", "speed_consistency", "walk_frames",   # the auto-tuner sets them: kept apart, not asked
                      "pan", "tilt"}                        # 2.96.10: where the head looks - restored, never asked
_SIMPROF_SKIP_SECTIONS = {"Simulator", "Updates", "Wi-Fi / hotspot", "Setup", "Web stream", "Guest access", "MQTT / Home Assistant", "Backup", "SMS (LTE stick)"}


def simprof_keys():
    """the settings that belong to the profile: switches, sliders and texts of the settings - without the simulator itself,
    network, access, updates and anything secret"""
    out = {}
    for lst in (TOGGLES, SLIDERS, TEXTS):
        for t_ in lst:
            sec, key, label = t_[0], t_[1], t_[2]
            if sec in _SIMPROF_SKIP_SECTIONS or key not in CFG or key.startswith("sim_") or key in _SIMPROF_SKIP_KEYS:
                continue
            if len(t_) > 3 and t_[3] == "secret" or any(w in key for w in ("password", "token", "secret", "topic", "_key", "user", "pin")):
                continue
            out.setdefault(key, label)
    return out


def _simprof_file(which):
    return os.path.join(DATA_DIR, f"settings_{which}.json")


def _simprof_save(which, vals):
    try:
        with open(_simprof_file(which), "w", encoding="utf-8") as f:
            json.dump(vals, f)
    except OSError:
        pass


def _simprof_load(which):
    try:
        with open(_simprof_file(which), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def simprof_on():
    """simulation on: the real settings aside, the ones of the last simulation back"""
    if not CFG.get("sim_separate", True):
        return
    keys = simprof_keys()
    _simprof_save("real", {k: CFG[k] for k in keys})
    SIMPROF["q"] = None
    for k, v in _simprof_load("sim").items():
        if k in keys and type(v) == type(CFG[k]):
            CFG[k] = v
    SIMPROF["start"] = {k: CFG[k] for k in keys}             # 2.95.93: only changes of this simulation are asked about
    _simprof_save("start", SIMPROF["start"])                  # also after a restart of MoveEye during the simulation


def simprof_off():
    """simulation off: remember its settings, the real ones back, the question which changes to take over"""
    if not CFG.get("sim_separate", True):
        return
    keys = simprof_keys()
    real = _simprof_load("real")
    if not real:
        return
    simv = {k: CFG[k] for k in keys}
    _simprof_save("sim", simv)
    ch = []
    start = SIMPROF.get("start") or _simprof_load("start")
    for k, label in keys.items():
        if k in real and real[k] != simv[k]:
            # 2.95.93: asked only when changed during this simulation (not by the auto-tuner, not already at its start)
            opt = CFG.get("simprof_opt") or {}
            if k in opt and k not in ("pan", "tilt"):           # 2.97.0: found by the optimisation in the simulation - always asked
                ch.append({"key": k, "label": label + " (" + tr("optimisation") + ")", "real": real[k], "sim": simv[k], "opt": True})
            elif k not in _SIMPROF_AUTO_KEYS and k not in (CFG.get("simprof_ignore") or []) and (k not in start or start[k] != simv[k]):
                ch.append({"key": k, "label": label, "real": real[k], "sim": simv[k]})
            CFG[k] = real[k]
    CFG["simprof_opt"] = {}
    SIMPROF["q"] = {"t": time.time(), "changes": ch[:80]} if ch else None
    if ch:
        log_event("sys", f"Simulation off: {len(ch)} settings of the simulation not taken over yet (question on the page)")


def simprof_ignore(keys, reset=False):
    """2.96.10: settings the question leaves out from now on (the real value always comes back)"""
    cur = [] if reset else list(CFG.get("simprof_ignore") or [])
    for k in keys:
        if isinstance(k, str) and k in CFG and k not in cur:
            cur.append(k)
    CFG["simprof_ignore"] = cur[:200]
    save_settings()


def simprof_answer(take):
    """the answer: these keys get the value of the simulation (an empty list: keep the real settings)"""
    q = SIMPROF["q"]
    if not q:
        return 0
    n = 0
    for c in q["changes"]:
        if c["key"] in take and c["key"] in CFG:
            CFG[c["key"]] = c["sim"]; n += 1
    SIMPROF["q"] = None
    save_settings()
    if n:
        log_event("sys", f"{n} settings of the simulation taken over")
    return n


def simprof_state(lang=None):
    q = SIMPROF["q"]
    if not q:
        return None
    lg = lang or CFG.get("lang", "de")
    return {"t": q["t"], "changes": [dict(c, label=tr(c["label"], lg)) for c in q["changes"]], "ignored": len(CFG.get("simprof_ignore") or [])}


def sim_set(on, who="web", confirm=False):
    """The one switch: real hardware <-> simulator.
    2.97.0: armed, the simulation would make the real device blind - only with confirm=True (then disarmed first)."""
    on = bool(on)
    if on == bool(CFG["sim_on"]):
        return True, ""
    if on and CFG["armed"]:
        if not confirm:
            return False, "armed"
        disarm()
        log_event("sys", f"Disarmed for the simulation ({who}) - the real camera is not watched now")
    if not str(who).startswith("automatic"):            # by hand: the automatic does not switch it back (2.95.25)
        CFG["sim_auto_on"] = False
        if not on:
            _SIMGONE["block"] = True
    w = WATCH_REF["w"]
    if on:
        CFG["sim_prev_source"] = CFG["source"] if not str(CFG["source"]).startswith("sim:") else "auto"
        CFG["sim_prev_thermal"] = CFG["thermal_source"] if not str(CFG["thermal_source"]).startswith("sim:") else ""
        simprof_on()                                    # 2.95.86: own settings for the simulation
        CFG["sim_on"] = True; CFG["source"] = "sim:0"; CFG["thermal_source"] = "sim:thermal"
        if "sim:1" not in CFG["extra_cams"] and len(CFG["extra_cams"]) < MAX_EXTRA:
            CFG["extra_cams"] = CFG["extra_cams"] + ["sim:1"]
        SIM.update(t=0.0, ok=False, msg="connecting …", seen_event=0)
        log_event("sys", f"SIMULATION ON ({who}) - {sim_base()}")
    else:
        CFG["sim_on"] = False
        simprof_off()                                   # 2.95.86: the real settings back, question about the changes
        CFG["source"] = CFG["sim_prev_source"] or "auto"; CFG["thermal_source"] = CFG["sim_prev_thermal"] or ""
        CFG["extra_cams"] = [x for x in CFG["extra_cams"] if not x.startswith("sim:")]
        CFG["sensors"] = [x for x in CFG["sensors"] if not x["src"].startswith("sim:")]
        SIM.update(ok=False, msg="off", off_t=time.time())
        QUICK["rec_until"] = 0.0                            # forget what happened in the simulation
        if w is not None:
            w.last_person_time = 0; w.last_warm = 0.0; w.preroll.clear()
        if AUDIO is not None:
            AUDIO.last_noise = 0.0
        log_event("sys", f"SIMULATION OFF ({who}) - back to the real hardware")
    save_settings()
    try:
        cams_apply()
    except Exception:
        pass
    if w is not None:
        w.request_source(CFG["source"])
    return True, ""


