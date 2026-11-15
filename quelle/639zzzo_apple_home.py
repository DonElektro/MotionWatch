#@ MoveEye – Teil 639zzzo: «🏠 Apple Home» – Homebridge auf dem Pi als eigener Dienst: Kamera (Live-Bild aus dem RTSP-Strom, Foto), Bewegungsmelder bei Alarm, Schalter «Schutz», Kopf-Positionen und -Taster, «Patrouille», «Folgen», Licht weiss / Infrarot. Nur der Admin, ab Werk aus. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Auftrag des Besitzers (15.11.2026, freigegeben): MoveEye in der Home-App des iPhones.
#  Beta        vom Besitzer als «Beta» freigegeben (15.11.2026): Abzeichen «Beta» auf der Zeile und auf der Karte, dazu die Zeile
#              «Beta – erstes Einrichten ist der Test; bei Problemen ein Bildschirmfoto schicken» (hk-beta, 5 Sprachen).
#  Karte       «🏠 Apple Home» in Einstellungen → Netz & Zugang (eine Zeile; die Karte ist in sich geschlossen: hkPanel(el) füllt
#              ein beliebiges Element, so kann sie im neuen «Mehr»-Stil (3.97) einfach als Zeile eingesetzt werden). Nur der
#              Admin (Rolle admin, kein App-Schlüssel); Einrichtungscode und QR nur in GET /api/homekit für ihn. Ab Werk aus.
#  Einrichten  «Einrichten» → Frage auf der Seite «Homebridge wird installiert, ca. 150 MB, läuft als eigener Dienst» → im
#              Hintergrund mit denselben Rechten wie Samba (639zzzn: root direkt, sonst «sudo -n», sonst Befehle zum Kopieren):
#              apt nodejs npm (und ffmpeg, falls es fehlt; nur was fehlte, wird gemerkt), Systembenutzer «moveeye-hb» ohne Anmeldung,
#              npm install homebridge + homebridge-camera-ffmpeg (feste Versionen, --ignore-scripts: kein fremdes Installationsskript,
#              kein zweites ffmpeg) nach /opt/moveeye-homebridge, das kleine eigene Plugin «homebridge-moveeye» (Code unten,
#              HK_PLUGIN_JS) nach /opt/moveeye-homebridge/plugins, Speicher /var/lib/moveeye-homebridge (700), Dienst
#              moveeye-homebridge.service (systemd, gehärtet: eigener Benutzer, ProtectSystem=strict, NoNewPrivileges, Nice 5).
#              Nichts davon gehört MoveEye vorher – eine schon vorhandene Homebridge (/var/lib/homebridge) wird nicht angefasst.
#  Netz        HomeKit (HAP) nur auf den LAN-/WLAN-Schnittstellen (bridge.bind, dieselbe Auswahl wie Samba smb_lan: nicht
#              Tailscale, Docker, LTE). Alles andere nur auf 127.0.0.1: Bewegungs-Auslöser des Kamera-Plugins (localhttp),
#              RTSP-Leser «homekit» (RTSP_LOCAL, 420), die Adressen /k/hk/… von MoveEye (prüfen remote_addr, keine Weiterleitung).
#              Fernzugriff (unterwegs) geht über die Steuerzentrale des Besitzers (HomePod / Apple TV / iPad) – kein Port nach aussen.
#  Kamera      «Kamera-Qualität»: «Kopie» (Standard) = homebridge-camera-ffmpeg kopiert MoveEyes H.264 aus dem RTSP-Strom
#              (-vcodec copy, kaum Rechenzeit); MoveEye kodiert dafür das Live-Bild einmal (ffmpeg libx264 ultrafast, 420). Ohne
#              «RTSP für andere Programme» läuft dieser Kodierer nur, solange jemand in der Home-App zuschaut (mediamtx
#              runOnDemand, nur 127.0.0.1). «720p» = das Kamera-Plugin kodiert selbst aus dem MJPEG (auch ohne mediamtx; fehlt
#              mediamtx, gilt das automatisch). Foto: /k/hk/photo.jpg.
#  Bewegung    Bei einem Alarm (push_alert, 020: Person, Wärme, Geräusch – nur wenn scharf, nie in Simulation / Transportmodus)
#              ruft MoveEye http://127.0.0.1:<HK_MOTION_PORT>/motion?<Kamera> auf; der Melder geht nach 30 s von selbst zurück.
#  Schalter    «Schutz»: ein = Wachsam (arm, mit dem normalen Countdown), aus = Aus. Ist eine PIN fürs Ausschalten gesetzt, lehnt
#              MoveEye «aus» aus der Home-App ab (der Schalter springt zurück, die Karte zeigt warum), ausser der Besitzer
#              erlaubt es ausdrücklich auf der Karte (hk_disarm_nopin, ab Werk aus). Die PIN steht nie in Homebridge.
#              Zusatz des Besitzers: «Kopf <Name>» für jede gelernte Position (076) und «Kopf Grundstellung», Taster «Kopf links /
#              rechts / hoch / runter» (Schritt auf der Karte, Standard 15°): ein Druck fährt, nach ~1 s ist der Schalter wieder
#              aus. «Patrouille», «Folgen» (echter Zustand), Lampen «Licht weiss» / «Infrarot» (ein = «an»; aus = zurück auf
#              «Automatisch», wenn sie vorher automatisch war, sonst «aus»; angezeigt wird, ob sie wirklich leuchtet).
#              Gesperrt wie überall: Not-Aus / Störung / Transportmodus (servo_blocked, 072 / 639zzzt), ein laufender Alarm hat
#              den Kopf (kopf_owner «alarm», Gehtest), Spielrunde; höchstens ein Kopf-Befehl pro 0,8 s. Die Liste der Geräte
#              folgt den gelernten Positionen von selbst (das Plugin fragt alle 5 s, dynamische Plattform).
#  Schlüssel   ein eigener App-Schlüssel (573) mit Scope «homekit»: er öffnet NUR /k/hk/state und /k/hk/do von 127.0.0.1 (nicht
#              /api, nicht /k/<key>/…, kein Ändern von Einstellungen), MoveEye speichert nur den Hash. Der Schlüssel selbst steht
#              nur in /var/lib/moveeye-homebridge/config.json (Modus 600, Besitzer moveeye-hb), geschrieben über stdin
#              («install /dev/stdin»), nie in eine Datei von MoveEye, ein Protokoll oder eine Befehlszeile. Das Plugin schickt ihn
#              im Kopf X-MoveEye-Key. Bild / Foto brauchen ein zweites, schwächeres Geheimnis (nur lesen, nur 127.0.0.1;
#              MoveEye kennt nur den sha256), weil ffmpeg es in der Befehlszeile sieht.
#              Ohne Rechte (sudo will ein Passwort): die Datei liegt bis zum Kopieren (höchstens 1 h) als config.pending.json
#              (600) im Ordner von MoveEye, der Befehl zum Kopieren löscht sie danach.
#  Status      läuft / gekoppelt / Fehler: systemctl is-active + das Plugin meldet bei jeder Abfrage (X-HK-Paired), ob die
#              Home-App gekoppelt ist (pairedClients in Homebridges persist). Einrichtungscode XXX-XX-XXX und X-HM://-QR stehen in
#              DATA_DIR/homekit/setup.json (600, nicht in den Einstellungen, nicht im Export) und werden nur gezeigt, solange
#              nicht gekoppelt ist. «Neu koppeln» = neue Kennung + neuer Code, alte Kopplung gelöscht.
#  Aus         «Ausschalten / Deinstallieren» (mit Frage) entfernt nur, was MoveEye eingerichtet hat (hk_st["mine"]): Dienst, Unit,
#              /opt/moveeye-homebridge, /var/lib/moveeye-homebridge, Benutzer moveeye-hb, App-Schlüssel, und die apt-Pakete, die
#              MoveEye installiert hat (kein autoremove).
#  Rechenzeit  siehe HK_CPU (gemessen im Container, für den Pi 5 hochgerechnet) – steht auch auf der Karte.
# Tests: werkzeuge/apple_home_test.py (falsche Installations- / systemd-Schicht, Plugin in Node mit einer falschen Homebridge-API).
# ----------------------------------------------------------------------------
HK_DEF = {"hk_on": False, "hk_quality": "copy", "hk_step": 15, "hk_disarm_nopin": False, "hk_st": {}}
for _k, _v in HK_DEF.items():
    CFG.setdefault(_k, json.loads(json.dumps(_v))); DEFAULTS.setdefault(_k, json.loads(json.dumps(_v)))
    FACTORY_CFG.setdefault(_k, json.loads(json.dumps(_v)))
USER_SETTINGS_DENY.update(HK_DEF)
APPKEY_DENY_KEYS.update(HK_DEF)
APPKEY_DENY_PATHS.add("/api/homekit")
LOCK_DENY_PATHS.add("/api/homekit")

HK_VERSIONS = (("homebridge", "1.8.5"), ("homebridge-camera-ffmpeg", "3.1.4"))
HK_USER = "moveeye-hb"
HK_SVC = "moveeye-homebridge"
HK_PORT = 51836                                           # HAP (not 51826: another Homebridge may use the standard port)
HK_MOTION_PORT = 51837                                    # camera plugin: motion trigger, only 127.0.0.1
HK_KEY_NAME = "Apple Home (Homebridge)"
HK_PKGS = ("nodejs", "npm", "ffmpeg")
HK = {"opt": "/opt/moveeye-homebridge", "var": "/var/lib/moveeye-homebridge", "unit": "/etc/systemd/system/moveeye-homebridge.service",
      "lock": threading.RLock(), "busy": "", "err": "", "cmds": [], "want": False, "seen": 0.0, "paired": None, "active": (0.0, False),
      "log": deque(maxlen=8), "t_head": 0.0, "rl": deque(maxlen=40), "bad": {}, "motion_t": 0.0, "rtsp_h": ""}
HK_CPU = {"copy": "about 1–3 % of one core to copy + 15–25 % for the encoder of MoveEye, only while somebody watches",
          "720p": "about 25–40 % of one core, only while somebody watches", "idle": "about 1 % and 80 MB of memory"}
HK_STEPS_OK = (5, 10, 15, 20, 30, 45)


def hk_sys(cmd, inp=None, timeout=60, root=True):
    """the one door to the system (the test replaces it): as root / «sudo -n» like Samba (639zzzn); secrets only through inp"""
    return smb_sys(cmd, inp, timeout, root)


def hk_step(cmd, why, inp=None, timeout=120):
    rc, out = hk_sys(cmd, inp, timeout)
    if rc == 0:
        return ""
    if _SMB_DENIED.search(out) or rc == 127 and "sudo" in out:
        return "no rights"
    return f"{why}: {(out.splitlines() or ['?'])[-1][:120] if rc != -9 else 'timeout'}"


def _hk_dir():
    d = os.path.join(DATA_DIR, "homekit")
    os.makedirs(d, mode=0o700, exist_ok=True)
    return d


def _hk_write600(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(path, 0o600)


def hk_state():
    return dict(CFG.get("hk_st") or {})


def hk_state_set(**kw):
    st = hk_state()
    st.update(kw)
    CFG["hk_st"] = st
    save_settings()
    return st


# ---- setup code, X-HM:// (the QR of the Home app), identity -----------------------------------------------------------
HK_BAD_CODES = {"00000000", "11111111", "22222222", "33333333", "44444444", "55555555", "66666666", "77777777", "88888888",
                "99999999", "12345678", "87654321"}


def hk_new_code():
    while True:
        c = "".join(secrets.choice("0123456789") for _ in range(8))
        if c not in HK_BAD_CODES:
            return f"{c[:3]}-{c[3:5]}-{c[5:]}"


def hk_new_identity():
    b = [secrets.randbelow(256) for _ in range(6)]
    b[0] = (b[0] & 0xFC) | 0x02                          # a locally administered address
    sid = "".join(secrets.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(4))
    return ":".join(f"{x:02X}" for x in b), sid


def hk_setup_uri(code, sid, category=2):
    """the X-HM:// address of the HomeKit QR code (as HAP-NodeJS Accessory.setupURI: IP accessory, category 2 = bridge)"""
    low = int(str(code).replace("-", "")) | 1 << 28
    if category & 1:
        low |= 1 << 31
    v = (category >> 1) * 0x100000000 + low
    s = ""
    while v:
        v, r = divmod(v, 36)
        s = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[r] + s
    return "X-HM://" + s.rjust(9, "0") + sid


def hk_setup_load():
    try:
        with open(os.path.join(_hk_dir(), "setup.json"), encoding="utf-8") as f:
            d = json.load(f)
        if re.fullmatch(r"\d{3}-\d{2}-\d{3}", d.get("code", "")) and re.fullmatch(r"[0-9A-Z]{4}", d.get("sid", "")):
            return d
    except (OSError, ValueError, AttributeError):
        pass
    return None


def hk_setup_new():
    mac, sid = hk_new_identity()
    d = {"code": hk_new_code(), "sid": sid}
    _hk_write600(os.path.join(_hk_dir(), "setup.json"), json.dumps(d))
    hk_state_set(mac=mac)
    return d


# ---- what Homebridge gets ----------------------------------------------------------------------------------------------
def _hk_hash(x):
    return hashlib.sha256(("mw-hk|" + str(x)).encode()).hexdigest()


def hk_cam_name():
    n = re.sub(r"[^\w ']", " ", str(CFG.get("device_name") or "MoveEye"), flags=re.U)
    n = re.sub(r"\s+", " ", n).strip()[:30]
    return n if n and n[0].isalnum() and n[-1].isalnum() else "MoveEye"


def hk_quality_eff():
    """«copy» needs mediamtx (the RTSP server of 420); without it the camera plugin encodes from the MJPEG"""
    return "copy" if CFG.get("hk_quality") != "720p" and _mediamtx_bin() else "720p"


def hk_base():
    return ("https" if WEB_OPTS.get("https") else "http") + f"://127.0.0.1:{int(CFG['web_port'])}"


def hk_config(key, vpw, setup, lan_if, ffmpeg="/usr/bin/ffmpeg"):
    """the config.json of our Homebridge (dict). key = the app key (scope homekit), vpw = picture secret; never a PIN or password
    of MoveEye"""
    st = hk_state()
    q = hk_quality_eff()
    base = hk_base()
    tls = " -tls_verify 0" if base.startswith("https") else ""
    snap = f"{base}/k/hk/photo.jpg?t={vpw}"
    if q == "copy":
        vc = {"source": f"-rtsp_transport tcp -i rtsp://homekit:{vpw}@127.0.0.1:{int(CFG['rtsp_port'])}/motionwatch", "vcodec": "copy"}
    else:
        vc = {"source": f"-f mjpeg{tls} -i {base}/k/hk/video.mjpg?t={vpw}", "vcodec": "libx264", "maxWidth": 1280, "maxHeight": 720,
              "maxFPS": 15, "maxBitrate": 1500, "forceMax": True, "encoderOptions": "-preset ultrafast -tune zerolatency"}
    vc.update({"stillImageSource": f"{tls.strip()} -i {snap}".strip(), "maxStreams": 2, "audio": False, "packetSize": 1316, "debug": False})
    host = re.sub(r"[^A-Za-z0-9-]", "", socket.gethostname() or "") or "pi"
    return {
        "description": "MoveEye (Apple Home) - written by MoveEye, do not change by hand (MoveEye: Settings -> Network & access -> Apple Home)",
        "bridge": {"name": f"MoveEye {host}"[:30], "username": st.get("mac", ""), "port": HK_PORT, "pin": setup["code"],
                   "setupID": setup["sid"], "bind": list(lan_if), "advertiser": "ciao", "manufacturer": "MoveEye", "model": "MoveEye Bridge"},
        "plugins": ["homebridge-camera-ffmpeg", "homebridge-moveeye"],
        "accessories": [],
        "platforms": [
            {"platform": "Camera-ffmpeg", "name": "Camera FFmpeg", "videoProcessor": ffmpeg, "porthttp": HK_MOTION_PORT, "localhttp": True,
             "cameras": [{"name": hk_cam_name(), "manufacturer": "MoveEye", "model": "MoveEye", "motion": True, "motionTimeout": 30,
                          "switches": False, "motionDoorbell": False, "unbridge": False, "videoConfig": vc}]},
            {"platform": "MoveEye", "name": "MoveEye", "base": base, "key": key, "username": st.get("mac", ""), "poll": 5}]}


HK_UNIT_TEXT = """# MoveEye: Homebridge for Apple Home - written by MoveEye (Settings -> Network & access -> Apple Home)
[Unit]
Description=Homebridge for MoveEye (Apple Home)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={user}
Group={user}
Environment=HOME={var}
Environment=NODE_ENV=production
ExecStart=/usr/bin/node {opt}/node_modules/homebridge/bin/homebridge -U {var} -P {opt}/node_modules -P {opt}/plugins --strict-plugin-resolution -C -Q
Restart=on-failure
RestartSec=10
Nice=5
UMask=0077
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths={var}
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictNamespaces=yes
RestrictSUIDSGID=yes
LockPersonality=yes
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX AF_NETLINK
MemoryMax=400M

[Install]
WantedBy=multi-user.target
"""


def hk_unit_text():
    return HK_UNIT_TEXT.format(user=HK_USER, var=HK["var"], opt=HK["opt"])


HK_PLUGIN_PKG = json.dumps({"name": "homebridge-moveeye", "version": "1.0.0", "description": "MoveEye switches, head and lights (written by MoveEye)",
                            "main": "index.js", "license": "UNLICENSED", "private": True, "keywords": ["homebridge-plugin"],
                            "engines": {"homebridge": ">=1.6.0", "node": ">=18"}}, indent=1)

# the plugin «homebridge-moveeye» (dynamic platform): asks /k/hk/state every 5 s, sends /k/hk/do; the key only in a header
HK_PLUGIN_JS = r"""'use strict';
// homebridge-moveeye - written by MoveEye (Apple Home card). Do not change by hand: MoveEye writes it again.
const http = require('http'), https = require('https'), fs = require('fs'), path = require('path');
const PLUGIN = 'homebridge-moveeye', PLATFORM = 'MoveEye';
module.exports = (api) => { api.registerPlatform(PLUGIN, PLATFORM, MoveEyePlatform); };

class MoveEyePlatform {
  constructor(log, config, api) {
    this.log = log; this.cfg = config || {}; this.api = api; this.hap = api.hap; this.acc = new Map(); this.items = new Map();
    this.base = String(this.cfg.base || 'http://127.0.0.1:5000').replace(/\/+$/, ''); this.key = String(this.cfg.key || '');
    this.every = Math.max(2, Number(this.cfg.poll) || 5) * 1000; this.busy = false; this.fails = 0;
    if (!/^https?:\/\/(127\.0\.0\.1|\[::1\]|localhost)(:\d+)?$/.test(this.base)) { this.log.error('MoveEye: only an address on this Pi is allowed'); return; }
    api.on('didFinishLaunching', () => { this.tick(); this.timer = setInterval(() => this.tick(), this.every); });
    api.on('shutdown', () => clearInterval(this.timer));
  }
  configureAccessory(a) { this.acc.set(a.UUID, a); }
  paired() {
    try {
      const u = String(this.cfg.username || '').replace(/:/g, '').toUpperCase();
      const j = JSON.parse(fs.readFileSync(path.join(this.api.user.persistPath(), 'AccessoryInfo.' + u + '.json'), 'utf8'));
      return Object.keys(j.pairedClients || {}).length > 0;
    } catch (e) { return false; }
  }
  req(action, body) {
    return new Promise((resolve) => {
      const u = new URL(this.base + '/k/hk/' + action), lib = u.protocol === 'https:' ? https : http;
      const data = body ? JSON.stringify(body) : null;
      const r = lib.request(u, {method: data ? 'POST' : 'GET', timeout: 8000, rejectUnauthorized: false,   // only 127.0.0.1 (own certificate)
        headers: Object.assign({'X-MoveEye-Key': this.key, 'X-HK-Paired': this.paired() ? '1' : '0', 'Accept': 'application/json'},
          data ? {'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data)} : {})}, (res) => {
        let b = ''; res.setEncoding('utf8'); res.on('data', c => { if (b.length < 200000) b += c; });
        res.on('end', () => { let j = null; try { j = JSON.parse(b); } catch (e) { j = null; } resolve({code: res.statusCode, j: j || {}}); });
      });
      r.on('timeout', () => r.destroy(new Error('timeout')));
      r.on('error', (e) => resolve({code: 0, j: {ok: false, error: String(e.message || e)}}));
      if (data) r.write(data); r.end();
    });
  }
  async tick() {
    if (this.busy) return; this.busy = true;
    try {
      const {code, j} = await this.req('state');
      if (code !== 200 || !Array.isArray(j.items)) {
        if (this.fails++ % 12 === 0) this.log.warn('MoveEye does not answer (' + code + (j.error ? ': ' + j.error : '') + ')');
        return;
      }
      this.fails = 0; this.sync(j.items);
    } finally { this.busy = false; }
  }
  uuid(id) { return this.hap.uuid.generate('moveeye:' + id); }
  sync(items) {
    const {Service, Characteristic} = this.hap, want = new Set();
    for (const it of items) {
      if (!it || typeof it.id !== 'string' || !it.name) continue;
      const id = this.uuid(it.id); want.add(id); this.items.set(id, it);
      let a = this.acc.get(id);
      const kind = it.type === 'light' ? Service.Lightbulb : Service.Switch;
      if (!a) {
        a = new this.api.platformAccessory(it.name, id); a.context.id = it.id; a.context.type = it.type;
        a.addService(kind, it.name);
        this.api.registerPlatformAccessories(PLUGIN, PLATFORM, [a]); this.acc.set(id, a);
        this.log.info('MoveEye: new in Apple Home: ' + it.name);
      }
      const s = a.getService(kind) || a.addService(kind, it.name);
      const info = a.getService(Service.AccessoryInformation);
      if (info) info.setCharacteristic(Characteristic.Manufacturer, 'MoveEye').setCharacteristic(Characteristic.Model, it.type);
      const ch = s.getCharacteristic(Characteristic.On);
      if (!a.__mw) {
        a.__mw = true;
        ch.onGet(() => { const x = this.items.get(id); return !!(x && x.on); });
        ch.onSet((v) => this.set(id, !!v));
      }
      if (!a.__pending) ch.updateValue(!!it.on);
    }
    const gone = [...this.acc.entries()].filter(([k]) => !want.has(k)).map(([, a]) => a);
    if (gone.length) { this.api.unregisterPlatformAccessories(PLUGIN, PLATFORM, gone); gone.forEach(a => { this.acc.delete(a.UUID); this.items.delete(a.UUID); }); }
  }
  set(id, v) {
    const it = this.items.get(id), a = this.acc.get(id); if (!it || !a) return;
    const ch = (a.getService(this.hap.Service.Lightbulb) || a.getService(this.hap.Service.Switch)).getCharacteristic(this.hap.Characteristic.On);
    if (it.type === 'button' && !v) return;
    a.__pending = true;
    this.req('do', {id: it.id, on: v}).then(({code, j}) => {
      if (!j.ok) this.log.warn('MoveEye: ' + it.name + ': ' + (j.error || ('error ' + code)));
      if (it.type === 'button') { setTimeout(() => { a.__pending = false; ch.updateValue(false); }, 1000); return; }   // a key: off again
      it.on = j.ok ? !!j.on : !!it.on;
      setTimeout(() => { a.__pending = false; ch.updateValue(!!it.on); }, j.ok ? 0 : 400);                    // refused: back
    });
  }
}
"""


# ---- install / apply / remove (one root job at a time, in the background) --------------------------------------------------
def _hk_pkg_have(p):
    rc, out = hk_sys(["dpkg-query", "-W", "-f=${Status}", p], root=False, timeout=20)
    return rc == 0 and "install ok installed" in out


def _hk_node_ok():
    rc, out = hk_sys(["node", "--version"], root=False, timeout=20)
    m = re.match(r"v(\d+)\.", out.strip()) if rc == 0 else None
    return bool(m and int(m.group(1)) >= 18)


def hk_cmds():
    """the commands for a terminal when MoveEye has no rights (sudo wants a password); no secret in them"""
    o, v, u, d = HK["opt"], HK["var"], HK_USER, _hk_dir()
    pk = " ".join(f"{n}@{x}" for n, x in HK_VERSIONS)
    return [f"sudo apt install -y --no-install-recommends {' '.join(HK_PKGS)}",
            f"id {u} || sudo useradd --system --no-create-home --home-dir {v} --shell /usr/sbin/nologin --user-group {u}",
            f"sudo install -d -m 755 {o} {o}/plugins/homebridge-moveeye && sudo install -d -m 700 -o {u} -g {u} {v}",
            f"sudo npm install --prefix {o} --omit=dev --ignore-scripts --no-audit --no-fund --cache {o}/.npm-tmp {pk} && sudo rm -rf {o}/.npm-tmp",
            f"sudo install -m 644 '{d}/plugin/package.json' '{d}/plugin/index.js' {o}/plugins/homebridge-moveeye/",
            f"sudo install -m 600 -o {u} -g {u} '{d}/config.pending.json' {v}/config.json && rm -f '{d}/config.pending.json'",
            f"sudo install -m 644 '{d}/{HK_SVC}.service' {HK['unit']}",
            f"sudo systemctl daemon-reload && sudo systemctl enable --now {HK_SVC}"]


def hk_cmds_off(mine):
    """switching off without rights: only what MoveEye made"""
    c = [f"sudo systemctl disable --now {HK_SVC}"]
    if mine.get("unit"):
        c += [f"sudo rm -f {HK['unit']}", "sudo systemctl daemon-reload"]
    c += [f"sudo rm -rf --one-file-system {mine[k]}" for k in ("opt", "var") if isinstance(mine.get(k), str)]
    if mine.get("user"):
        c.append(f"sudo userdel {HK_USER}")
    if mine.get("pkgs"):
        c.append("sudo apt remove -y " + " ".join(mine["pkgs"]))
    return c


def _hk_files_local():
    """plugin and unit into DATA_DIR/homekit (no secret inside) - the source of the root steps and of the commands"""
    d = _hk_dir()
    os.makedirs(os.path.join(d, "plugin"), exist_ok=True)
    for n, t in (("plugin/package.json", HK_PLUGIN_PKG), ("plugin/index.js", HK_PLUGIN_JS), (HK_SVC + ".service", hk_unit_text())):
        with open(os.path.join(d, n), "w", encoding="utf-8") as f:
            f.write(t)
    return d


def hk_install():
    """apt, user, folders, npm, plugin -> "" or the english reason (records what MoveEye installed in hk_st["mine"])"""
    mine = dict(hk_state().get("mine") or {})
    need = [p for p in HK_PKGS if not _hk_pkg_have(p)]
    if "nodejs" not in need and not _hk_node_ok():
        return "Node.js on this Pi is older than version 18"
    if need:
        apt = shutil.which("apt-get") or "apt-get"
        inst = [apt, "install", "-y", "--no-install-recommends", "-o", "Dpkg::Options::=--force-confold"] + need
        rc, out = hk_sys(inst, timeout=1500)
        if rc != 0 and re.search(r"Unable to locate package|has no installation candidate|Failed to fetch", out):
            if hk_sys([apt, "update"], timeout=600)[0] == 0:
                rc, out = hk_sys(inst, timeout=1500)
        if rc != 0:
            low = out.lower()
            if _SMB_DENIED.search(out):
                return "no rights"
            if "could not get lock" in low or "dpkg frontend lock" in low:
                return "apt is busy right now (another installation or update) - try again in a few minutes"
            if "temporary failure resolving" in low or "could not resolve" in low or "failed to fetch" in low:
                return "no internet for apt - try again with internet"
            return "apt: " + ((out.splitlines() or ["?"])[-1][:120])
        mine["pkgs"] = sorted(set(mine.get("pkgs") or []) | set(need))
        hk_state_set(mine=mine)
        log_event("sys", "Apple Home: installed with apt: " + ", ".join(need))
    import pwd
    try:
        u = pwd.getpwnam(HK_USER)
        if u.pw_uid >= 1000 and not mine.get("user"):
            return f"a user «{HK_USER}» exists already and is not the one of MoveEye"
    except KeyError:
        e = hk_step(["useradd", "--system", "--no-create-home", "--home-dir", HK["var"], "--shell", "/usr/sbin/nologin", "--user-group", HK_USER], "useradd")
        if e:
            return e
        mine["user"] = True
        hk_state_set(mine=mine)
    for ok_ in ("opt", "var"):
        if mine.get(ok_) != HK[ok_] and os.path.exists(HK[ok_]):
            return f"{HK[ok_]} exists already and is not the one of MoveEye"
    e = (hk_step(["install", "-d", "-m", "755", "-o", "root", "-g", "root", HK["opt"], HK["opt"] + "/plugins", HK["opt"] + "/plugins/homebridge-moveeye"], "install -d")
         or hk_step(["install", "-d", "-m", "700", "-o", HK_USER, "-g", HK_USER, HK["var"]], "install -d"))
    if e:
        return e
    mine.update(opt=HK["opt"], var=HK["var"])          # the paths themselves: uninstall removes exactly these
    hk_state_set(mine=mine)
    npm = shutil.which("npm") or "/usr/bin/npm"
    cache = HK["opt"] + "/.npm-tmp"
    rc, out = hk_sys([npm, "install", "--prefix", HK["opt"], "--omit=dev", "--ignore-scripts", "--no-audit", "--no-fund", "--no-update-notifier",
                      "--cache", cache] + [f"{n}@{v}" for n, v in HK_VERSIONS], timeout=1800)
    hk_sys(["rm", "-rf", "--one-file-system", cache], timeout=120)
    if rc != 0:
        if _SMB_DENIED.search(out):
            return "no rights"
        return "npm: " + ((out.splitlines() or ["?"])[-1][:120] if rc != -9 else "timeout")
    d = _hk_files_local()
    e = hk_step(["install", "-m", "644", "-o", "root", "-g", "root", d + "/plugin/package.json", d + "/plugin/index.js",
                 HK["opt"] + "/plugins/homebridge-moveeye/"], "install plugin")
    if e:
        return e
    hk_state_set(installed=int(time.time()), versions=dict(HK_VERSIONS))
    log_event("sys", "Apple Home: Homebridge " + dict(HK_VERSIONS)["homebridge"] + " installed (own service " + HK_SVC + ")")
    return ""


def _hk_key_new():
    """a fresh app key with scope «homekit» (the old one of MoveEye is blocked first) -> key or ""; only in memory"""
    st = hk_state()
    if st.get("key_id"):
        appkey_revoke(st["key_id"], "Apple Home")
    for e in appkey_entries():                                  # a key of an earlier setup with the same name
        if e.get("name") == HK_KEY_NAME:
            appkey_revoke(e["id"], "Apple Home")
    ok, err, key = appkey_create(HK_KEY_NAME, "Apple Home", scope=HOMEKIT_SCOPE)
    if not ok:
        return ""
    hk_state_set(key_id=appkey_find(key, want=HOMEKIT_SCOPE)["id"])
    return key


def hk_rtsp_sync():
    """the RTSP reader «homekit» (420) only while Apple Home wants the copied stream"""
    h = hk_state().get("vh", "")
    want = bool(CFG.get("hk_on") and hk_state().get("installed") and h and hk_quality_eff() == "copy")
    if want:
        import base64
        RTSP_LOCAL["homekit"] = ("- user: homekit\n  pass: sha256:%s\n  ips: ['127.0.0.1/32', '::1/128']\n  permissions:\n  - action: read\n"
                                 "    path: motionwatch\n" % base64.b64encode(bytes.fromhex(h)).decode())
    else:
        RTSP_LOCAL.pop("homekit", None)
    if HK["rtsp_h"] != (RTSP_LOCAL.get("homekit") or ""):
        HK["rtsp_h"] = RTSP_LOCAL.get("homekit") or ""
        try:
            rtsp_restart()
        except Exception as e:
            log_event("sys", f"Apple Home: RTSP: {e}"[:160])


def hk_write_config(new_setup=False):
    """a new app key + picture secret into config.json of Homebridge (stdin -> install -m 600) -> "" or the english reason"""
    lan = smb_lan()
    if not lan:
        return "no home network found (Wi-Fi / LAN)"
    setup = hk_setup_load()
    if setup is None or new_setup:
        setup = hk_setup_new()
    key = _hk_key_new()
    if not key:
        return "no app key could be made (at most 20)"
    vpw = secrets.token_urlsafe(24)
    hk_state_set(vh=hashlib.sha256(vpw.encode()).hexdigest())   # mediamtx compares sha256 (base64), the routes below the same hash
    ff = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
    text = json.dumps(hk_config(key, vpw, setup, sorted({x[0] for x in lan}), ff), indent=1)
    key = vpw = None
    dst = HK["var"] + "/config.json"
    e = hk_step(["install", "-m", "600", "-o", HK_USER, "-g", HK_USER, "/dev/stdin", dst], "install config", inp=text)
    if e == "no rights":
        _hk_write600(os.path.join(_hk_dir(), "config.pending.json"), text)   # until the owner copies it (the command deletes it)
        hk_state_set(pending=int(time.time()))
    text = None
    hk_rtsp_sync()
    return e


def hk_service(on):
    if on:
        d = _hk_files_local()
        e = (hk_step(["install", "-m", "644", "-o", "root", "-g", "root", d + "/" + HK_SVC + ".service", HK["unit"]], "install unit")
             or hk_step(["systemctl", "daemon-reload"], "systemctl daemon-reload")
             or hk_step(["systemctl", "enable", HK_SVC], "systemctl enable")
             or hk_step(["systemctl", "restart", HK_SVC], "systemctl restart"))
        if not e:
            st = hk_state()
            hk_state_set(mine=dict(st.get("mine") or {}, unit=True))
        HK["active"] = (0.0, False)
        return e
    if os.path.exists(HK["unit"]):
        return hk_step(["systemctl", "disable", "--now", HK_SVC], "systemctl disable")
    return ""


def hk_apply(why=""):
    """bring everything to the switch: on = installed, config, service running -> "" or the english reason"""
    with HK["lock"]:
        HK["cmds"] = []
        err = ""
        if CFG.get("hk_on"):
            if not hk_state().get("installed"):
                HK["busy"] = "installing Homebridge … (a few minutes)"
                err = hk_install()
            if not err:
                HK["busy"] = "writing the settings …"
                err = hk_write_config()
            if not err:
                err = hk_service(True)
        if err == "no rights":
            _hk_files_local()
            HK["cmds"] = hk_cmds()
        HK["err"] = err
        hk_rtsp_sync()
        if why:
            log_event("sys", f"Apple Home: {why}" + (f" - not done: {err}" if err else ""))
        return err


def hk_repair():
    """«Neu koppeln»: stop, the old pairing out of persist (only our folder), new identity + code, start"""
    with HK["lock"]:
        e = hk_step(["systemctl", "stop", HK_SVC], "systemctl stop")
        if not e:
            for pat in ("AccessoryInfo.*.json", "IdentifierCache.*.json"):
                e = e or hk_step(["find", HK["var"] + "/persist", "-maxdepth", "1", "-type", "f", "-name", pat, "-delete"], "find")
            e = e or hk_step(["find", HK["var"] + "/accessories", "-maxdepth", "1", "-type", "f", "-name", "cachedAccessories*", "-delete"], "find")
        if not e:
            e = hk_write_config(new_setup=True) or hk_service(True)
        HK.update(paired=None, seen=0.0)
        HK["err"] = e
        if e == "no rights":
            HK["cmds"] = hk_cmds()
        log_event("sys", "Apple Home: paired again (new code)" + (f" - not done: {e}" if e else ""))
        return e


def hk_uninstall():
    """«Ausschalten / Deinstallieren»: only what MoveEye made (hk_st["mine"]) -> "" or the english reason"""
    with HK["lock"]:
        st = hk_state()
        mine = dict(st.get("mine") or {})
        errs = []
        if mine.get("unit") or os.path.exists(HK["unit"]):
            e = hk_step(["systemctl", "disable", "--now", HK_SVC], "systemctl disable")
            if e == "no rights":
                HK.update(err=e, cmds=hk_cmds_off(mine))
                return e
            if e and "not loaded" not in e and "does not exist" not in e:
                errs.append(e)
            if mine.get("unit"):
                errs += [x for x in [hk_step(["rm", "-f", HK["unit"]], "rm unit"), hk_step(["systemctl", "daemon-reload"], "daemon-reload")] if x]
        for k in ("opt", "var"):
            p = mine.get(k)
            if isinstance(p, str) and p == HK[k] and os.path.basename(p) == "moveeye-homebridge":   # never another folder
                e = hk_step(["rm", "-rf", "--one-file-system", p], "rm " + k)
                if e:
                    errs.append(e)
        if mine.get("user"):
            e = hk_step(["userdel", HK_USER], "userdel")
            if e and "does not exist" not in e:
                errs.append(e)
        if mine.get("pkgs"):
            apt = shutil.which("apt-get") or "apt-get"
            e = hk_step([apt, "remove", "-y"] + list(mine["pkgs"]), "apt remove", timeout=900)
            if e:
                errs.append(e)
        if st.get("key_id"):
            appkey_revoke(st["key_id"], "Apple Home")
        for n in ("setup.json", "config.pending.json"):
            try:
                os.remove(os.path.join(_hk_dir(), n))
            except OSError:
                pass
        CFG["hk_on"] = False
        CFG["hk_st"] = {} if not errs else {"mine": mine}
        save_settings()
        RTSP_LOCAL.pop("homekit", None)
        hk_rtsp_sync()
        HK.update(paired=None, seen=0.0, err=errs[0] if errs else "", cmds=[], want=False)
        log_event("sys", "Apple Home: switched off and removed" + (f" - not everything: {errs[0]}" if errs else ""))
        return errs[0] if errs else ""


def hk_bg(label, fn):
    with HK["lock"]:
        if HK["busy"]:
            return False
        HK["busy"] = label

    def run():
        try:
            fn()
        except Exception as e:
            HK["err"] = f"error: {e.__class__.__name__}"
            log_event("sys", f"Apple Home: {e.__class__.__name__}: {e}"[:160])
        finally:
            HK["busy"] = ""
    threading.Thread(target=run, daemon=True, name="apple-home").start()
    return True


def hk_active():
    t, v = HK["active"]
    if time.time() - t < 10:
        return v
    rc, out = hk_sys(["systemctl", "is-active", HK_SVC], root=False, timeout=15)
    v = rc == 0 and out.strip() == "active"
    HK["active"] = (time.time(), v)
    return v


def hk_status(lang=None):
    """for the card (only the administrator gets it): state, code + QR while not paired, the accessories, refused commands"""
    st = hk_state()
    on = bool(CFG.get("hk_on"))
    pend = st.get("pending")
    if pend and (time.time() - pend > 3600 or not on):
        try:
            os.remove(os.path.join(_hk_dir(), "config.pending.json"))
        except OSError:
            pass
        hk_state_set(pending=0)
    if HK["busy"]:
        state, why = "busy", tr(HK["busy"], lang)
    elif not on:
        state, why = "off", ""
    elif HK["err"]:
        e = HK["err"]
        state, why = "err", (tr("MoveEye has no rights for this (sudo asks for a password) - run the commands below once in a terminal.", lang)
                             if e == "no rights" else smb_tr(e, lang))
    elif not hk_active():
        state, why = "err", tr("Homebridge does not run", lang)
    elif HK["paired"]:
        state, why = "paired", ""
    elif HK["seen"] and time.time() - HK["seen"] < 30:
        state, why = "run", ""
    else:
        state, why = "run", tr("starting …", lang)
    out = {"ok": True, "on": on, "state": state, "why": why, "need_confirm": bool(HK["want"]) and not on, "cmds": list(HK["cmds"]),
           "quality": CFG.get("hk_quality", "copy"), "quality_eff": hk_quality_eff(), "mediamtx": bool(_mediamtx_bin()),
           "step": int(CFG.get("hk_step") or 15), "steps": list(HK_STEPS_OK), "pin": bool(CFG.get("protect_pin")),
           "nopin": bool(CFG.get("hk_disarm_nopin")), "cpu": {k: tr(v, lang) for k, v in HK_CPU.items()}, "items": [x["name"] for x in hk_items(lang)] if on else [],
           "log": [{"t": t, "name": n, "why": _hk_why(w, lang)} for t, n, w in HK["log"]], "port": HK_PORT}
    s = hk_setup_load() if on and state == "run" and st.get("installed") else None
    if s:
        uri = hk_setup_uri(s["code"], s["sid"])
        out.update(code=s["code"], uri=uri, qr=qr_svg(uri))
    return out


def hk_action(d):
    """POST /api/homekit -> (ok, english error)"""
    a = str(d.get("action") or "")
    if HK["busy"] and a not in ("quality", "step", "nopin"):
        return False, "busy - try again"
    if a == "setup":
        HK["want"] = True                                     # the page shows the question first
        return True, ""
    if a == "cancel":
        HK["want"] = False
        return True, ""
    if a == "install":
        if not HK["want"] and not CFG.get("hk_on"):
            return False, "Press «Set up» first."
        HK["want"] = False
        CFG["hk_on"] = True
        save_settings()
        hk_bg("installing Homebridge … (a few minutes)", lambda: hk_apply("switched on"))
        return True, ""
    if a == "uninstall":
        hk_bg("removing …", hk_uninstall)
        return True, ""
    if a == "repair":
        if not CFG.get("hk_on"):
            return False, "Switch it on first."
        hk_bg("new pairing …", hk_repair)
        return True, ""
    if a == "retry":
        if not CFG.get("hk_on"):
            return False, "Switch it on first."
        hk_bg("checking …", lambda: hk_apply("try again"))
        return True, ""
    if a == "quality":
        q = str(d.get("value") or "")
        if q not in ("copy", "720p"):
            return False, "invalid value"
        CFG["hk_quality"] = q
        save_settings()
        if CFG.get("hk_on") and hk_state().get("installed"):
            hk_bg("writing the settings …", lambda: hk_apply("camera quality " + q))
        return True, ""
    if a == "step":
        try:
            v = int(d.get("value"))
        except (TypeError, ValueError):
            return False, "invalid value"
        if v not in HK_STEPS_OK:
            return False, "invalid value"
        CFG["hk_step"] = v
        save_settings()
        return True, ""
    if a == "nopin":
        CFG["hk_disarm_nopin"] = bool(d.get("value"))
        save_settings()
        log_event("sys", "Apple Home: switching off from the Home app despite the PIN " + ("ALLOWED by the owner" if CFG["hk_disarm_nopin"] else "refused (standard)"))
        return True, ""
    return False, "unknown action"


# ---- the alarm -> the motion sensor of the camera (020 push_alert) ------------------------------------------------------
def homekit_on_alert(kind):
    """called by push_alert: a real alarm while armed -> the camera plugin's motion trigger on 127.0.0.1 (never raises)"""
    try:
        if not CFG.get("hk_on") or kind not in ("person", "warm", "noise") or not is_armed() or CFG.get("sim_on"):
            return False
        now = time.time()
        if now - HK["motion_t"] < 5:
            return False
        HK["motion_t"] = now
        url = f"http://127.0.0.1:{HK_MOTION_PORT}/motion?" + urllib.parse.quote(hk_cam_name())

        def go():
            try:
                urllib.request.urlopen(urllib.request.Request(url), timeout=3).read(200)
            except Exception as e:
                log_event("sys", f"Apple Home: motion sensor not reached ({e.__class__.__name__})")
        threading.Thread(target=go, daemon=True, name="hk-motion").start()
        return True
    except Exception:
        return False


# ---- what the Home app shows / switches -----------------------------------------------------------------------------------
HK_NAMES = {   # id: (de, en, fr, it, rm) - HomeKit names: letters, digits, spaces (Siri: «Kopf Eingang»)
    "protect": ("Schutz", "Protection", "Protection", "Protezione", "Protecziun"),
    "patrol": ("Patrouille", "Patrol", "Patrouille", "Pattuglia", "Patruglia"),
    "follow": ("Folgen", "Follow", "Suivre", "Segui", "Suandar"),
    "light_white": ("Licht weiss", "White light", "Lumiere blanche", "Luce bianca", "Glisch alva"),
    "light_ir": ("Infrarot", "Infrared", "Infrarouge", "Infrarosso", "Infracotschen"),
    "head_home": ("Kopf Grundstellung", "Head home position", "Tete position de base", "Testa posizione base", "Chau posiziun da basa"),
    "head_left": ("Kopf links", "Head left", "Tete gauche", "Testa sinistra", "Chau sanester"),
    "head_right": ("Kopf rechts", "Head right", "Tete droite", "Testa destra", "Chau dretg"),
    "head_up": ("Kopf hoch", "Head up", "Tete haut", "Testa su", "Chau ensi"),
    "head_down": ("Kopf runter", "Head down", "Tete bas", "Testa giu", "Chau engiu"),
    "head_pt": ("Kopf", "Head", "Tete", "Testa", "Chau"),
}


def _hk_name(i, lang=None):
    L = norm_lang(lang or CFG.get("lang"))
    return HK_NAMES[i][{"de": 0, "en": 1, "fr": 2, "it": 3, "rm": 4}.get(L, 1)]


def _hk_clean(n):
    n = re.sub(r"[^\w ']", " ", str(n), flags=re.U)
    return re.sub(r"\s+", " ", n).strip()[:40]


def _hk_light(n):
    m = CFG.get("light_" + n, "off")
    return m == "on" or m == "auto" and bool((STATE.get("lights") or {}).get(n))


def hk_items(lang=None):
    """[{id, type: switch | light | button, name, on}] - the plugin makes one accessory of each (camera: the camera plugin)"""
    it = [{"id": "protect", "type": "switch", "name": _hk_name("protect", lang), "on": bool(CFG.get("armed"))}]
    head = False
    try:
        head = bool(live_has_head())
    except Exception:
        pass
    if head:
        it += [{"id": "patrol", "type": "switch", "name": _hk_name("patrol", lang), "on": bool(CFG.get("patrol"))},
               {"id": "follow", "type": "switch", "name": _hk_name("follow", lang), "on": bool(CFG.get("track_person") or CFG.get("track_motion"))}]
    for n in ("white", "ir"):
        if CFG.get(f"light_{n}_out") or CFG.get("sim_on"):
            it.append({"id": "light_" + n, "type": "light", "name": _hk_name("light_" + n, lang), "on": _hk_light(n)})
    if head:
        it.append({"id": "head_home", "type": "button", "name": _hk_name("head_home", lang), "on": False})
        seen = {x["name"].lower() for x in it}
        for p in teach_list(lang):
            nm = _hk_clean(p["name"])
            full = _hk_clean(_hk_name("head_pt", lang) + " " + nm) if nm else ""
            if nm and full.lower() not in seen:
                seen.add(full.lower())
                it.append({"id": "pt:" + nm, "type": "button", "name": full, "on": False})
        for dd in ("left", "right", "up", "down"):
            it.append({"id": "head_" + dd, "type": "button", "name": _hk_name("head_" + dd, lang), "on": False})
    return it


HK_SRV_WHY = {"estop": "Emergency stop - press «Release» to move again", "fault": "Servo fault", "inhibit": "Servos stopped",
              "transport": "Transport mode active"}


def _hk_why(w, lang=None):
    """a reason of the list -> text in the language of the page («srv:<code>» = a lock of the servos, 072)"""
    if str(w).startswith("srv:"):
        c = w[4:]
        return ("🧳 " if c == "transport" else "") + tr(HK_SRV_WHY.get(c, c), lang)
    return tr(w, lang)


def hk_head_block(lang=None):
    """'' = the head may move for Apple Home; else why not (english, translated on the card)"""
    b = servo_blocked()
    if b:
        return "srv:" + b
    try:
        cl = kopf_claims()                              # not kopf_owner(): a manual move just before must not hide the alarm
    except NameError:
        cl = set()
    if "alarm" in cl:
        return "an alarm has the head now"
    if "walktest" in cl:
        return "walk test runs"
    try:
        if KOPF.get("game_was") and kopf_game_hand():
            return "game round: only the players move the head"
    except NameError:
        pass
    if time.time() - HK["t_head"] < 0.8:
        return "too fast - one command at a time"
    return ""


def hk_refuse(name, why):
    HK["log"].appendleft((int(time.time()), name, why))
    log_event("web", f"Apple Home: «{name}» refused: {why}"[:200])
    return {"ok": False, "error": _hk_why(why, "en")}


def hk_do(d):
    """POST /k/hk/do {id, on} -> {ok, on} or {ok: False, error} (the switch in the Home app springs back)"""
    i, on = str(d.get("id") or ""), bool(d.get("on"))
    items = {x["id"]: x for x in hk_items()}
    if i not in items:
        return {"ok": False, "error": "unknown accessory"}
    it = items[i]
    nm = it["name"]
    who = "Apple Home"
    if i == "protect":
        if on:
            arm()
        else:
            if CFG.get("protect_pin") and CFG.get("armed") and not CFG.get("hk_disarm_nopin"):
                return dict(hk_refuse(nm, "a PIN for switching off is set - switch off in MoveEye (or allow it on the Apple Home card)"), on=True)
            try:
                protect_cancel_escalation()
                CFG["protect_level"] = "off"
                protect_siren_sync()
            except NameError:
                pass
            disarm()
        log_event("web", f"Apple Home: protection {'on' if on else 'off'}")
        return {"ok": True, "on": bool(CFG.get("armed"))}
    if i in ("patrol", "follow"):
        if on:
            b = servo_blocked()
            if b:
                return dict(hk_refuse(nm, "srv:" + b), on=False)
        if i == "patrol":
            CFG["patrol"] = on
            if on and CFG.get("patrol_mode") not in ("pendulum", "loop"):
                CFG["patrol_mode"] = "pendulum"
            save_settings()
            log_event("patrol", f"Patrol {'ON' if on else 'switched OFF'} ({who})")
        else:
            follow_set(on, who)
        return {"ok": True, "on": hk_items_on(i)}
    if i.startswith("light_"):
        n = i[6:]
        cur = CFG.get("light_" + n, "off")
        prev = dict(hk_state().get("lprev") or {})
        if on:
            if cur != "on":
                prev[n] = cur
            light_set(n, "on")
        else:
            light_set(n, "auto" if prev.get(n) == "auto" else "off")
            prev.pop(n, None)
        hk_state_set(lprev=prev)
        return {"ok": True, "on": _hk_light(n) if not on else True}
    if it["type"] == "button":
        if not on:
            return {"ok": True, "on": False}
        b = hk_head_block()
        if b:
            return hk_refuse(nm, b)
        HK["t_head"] = time.time()
        if i == "head_home":
            hp = tp_pick_home()
            MANUAL["until"] = time.time() + max(10.0, float(CFG.get("manual_hold") or 10))
            servo_driver_note(who, "goto")
            ok = servo_goto(hp[0], hp[1], "teach", wait=False)
            log_event("servo", f"To the home position ({who})")
            return {"ok": bool(ok), "on": False} if ok else hk_refuse(nm, "interrupted")
        if i.startswith("pt:"):
            k = next((p["i"] for p in teach_list() if _hk_clean(p["name"]) == i[3:]), None)
            ok, err = teach_goto(k, who) if k is not None else (False, "no such point")
            return {"ok": True, "on": False} if ok else hk_refuse(nm, err)
        dd = i[5:]
        ax = "pan" if dd in ("left", "right") else "tilt"
        step = float(CFG.get("hk_step") or 15) * kopf_pct_per_deg(ax)
        if not move_camera(dd, step, who):
            return hk_refuse(nm, ("srv:" + servo_blocked()) if servo_blocked() else "refused")
        return {"ok": True, "on": False}
    return {"ok": False, "error": "unknown accessory"}


def hk_items_on(i):
    return next((x["on"] for x in hk_items() if x["id"] == i), False)


# ---- web: /k/hk/… (Homebridge on this Pi) and /api/homekit (the card) --------------------------------------------------------
def _hk_local(req):
    """only a program on this Pi, not something forwarded (Tailscale serve / a tunnel also come from 127.0.0.1)"""
    return req.remote_addr in ("127.0.0.1", "::1") and not any(
        req.headers.get(h) for h in ("X-Forwarded-For", "X-Forwarded-Host", "X-Forwarded-Proto", "Forwarded", "X-Real-Ip", "Tailscale-User-Login"))


def _hk_vpw_ok(t):
    h = hk_state().get("vh", "")
    t = str(t or "")
    if len(t) >= 20 and h and hmac.compare_digest(hashlib.sha256(t.encode()).hexdigest(), h):
        return True
    return len(t) >= 20 and hmac.compare_digest(t, EXT.get("local_tok") or "")


def _hk_rate(ip, bad=False):
    """True = too many: 30 commands in 10 s; 10 wrong keys in 10 min per address"""
    now = time.time()
    if bad:
        rec = [x for x in HK["bad"].get(ip, []) if now - x < 600] + [now]
        HK["bad"][ip] = rec
        return len(rec) > 10
    if len([x for x in HK["bad"].get(ip, []) if now - x < 600]) >= 10:
        return True
    HK["rl"].append(now)
    return len([x for x in HK["rl"] if now - x < 10]) > 30


_smalltv_routes_639zzzo = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzzo
    _smalltv_routes_639zzzo(app, reply, body)
    from flask import request, g, Response

    @app.route("/k/hk/<action>", methods=["GET", "POST"])
    def hk_local_api(action):
        ip = request.remote_addr or "?"
        if not _hk_local(request):
            return Response("not found", 404)
        if action in ("photo.jpg", "video.mjpg"):
            if not CFG.get("hk_on") or not _hk_vpw_ok(request.args.get("t")):
                _hk_rate(ip, True)
                return Response("not found", 404)
            w = WATCH_REF.get("w")
            if action == "photo.jpg":
                f = getattr(w, "frame_out", None)
                if f is None:
                    return Response("no picture yet", 503)
                ok, buf = cv2.imencode(".jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 85])
                return Response(buf.tobytes(), mimetype="image/jpeg", headers={"Cache-Control": "no-store"}) if ok else Response("error", 500)

            def gen():
                last = -1
                if w is None:
                    return
                w.web_viewers += 1; STATE["web_viewers"] = w.web_viewers
                try:
                    while True:
                        jpg, seq = w.jpeg, w.jpeg_seq
                        if jpg and seq != last:
                            last = seq
                            yield b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n"
                        time.sleep(0.03)
                finally:
                    w.web_viewers = max(0, w.web_viewers - 1); STATE["web_viewers"] = w.web_viewers
            return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame", headers={"Cache-Control": "no-store"})
        if action not in ("state", "do"):
            return Response("not found", 404)
        k = request.headers.get("X-MoveEye-Key") or ""
        ke = appkey_find(k, want=HOMEKIT_SCOPE) if CFG.get("hk_on") else None
        if ke is None:
            if _hk_rate(ip, True):
                return reply({"ok": False, "error": "too many wrong keys - wait 10 minutes"}, 429)
            return reply({"ok": False, "error": "unknown key"}, 403)
        if _hk_rate(ip):
            return reply({"ok": False, "error": "too many commands"}, 429)
        appkey_seen(ke, ip)
        HK["seen"] = time.time()
        HK["paired"] = request.headers.get("X-HK-Paired") == "1"
        if action == "state":
            return reply({"ok": True, "items": hk_items(), "device": CFG.get("device_name") or "MoveEye"})
        if request.method != "POST":
            return reply({"ok": False, "error": "POST"}, 405)
        d = request.get_json(force=True, silent=True) or {}
        return reply(hk_do(d if isinstance(d, dict) else {}))

    @app.route("/api/homekit", methods=["GET", "POST"])
    def api_homekit():
        d = body() if request.method == "POST" else {}
        L = norm_lang(request.args.get("lang") or d.get("lang") or CFG.get("lang"))
        if getattr(g, "role", "admin") != "admin" or getattr(g, "appkey", None):
            return reply({"ok": False, "error": tr("only the administrator", L)}, 403)
        if request.method == "POST":
            ok, err = hk_action(d)
            if not ok:
                return reply(dict(hk_status(L), ok=False, error=tr(err, L)), 400)
        return reply(hk_status(L))

    if CFG.get("hk_on"):                                   # after a start: the picture reader for RTSP again (no root step)
        hk_rtsp_sync()


# ---- the card (530 Settings → Network & access) -------------------------------------------------------------------------------
HK_CARD_HTML = ('<details class="card" data-view="applehome" data-vgroup="Panels" data-vlabel="Apple Home">'
                '<summary>🏠 Apple Home</summary><div id="hk-card" class="hk-card"></div></details>\n    ')
HK_PANEL_JS = r"""
<style>
.hk-card .hk-qr{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-top:10px}
.hk-card .hk-qr svg{width:150px;height:150px;border-radius:10px;background:#fff;padding:4px;box-sizing:border-box}
.hk-card .hk-code{font:700 26px/1.2 ui-monospace,Menlo,monospace;letter-spacing:2px}
.hk-card .hk-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.hk-card .hk-li{font-size:13px;margin:2px 0}
.hk-card select{max-width:100%}
.hk-beta{display:inline-block;margin-left:8px;padding:1px 8px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:.3px;
  color:#1a1206;background:#f0b429;vertical-align:middle;text-transform:uppercase}
.hk-card .hk-betaline{font-size:12px;margin:4px 0 6px}
</style>
<script>
(function () {
  try { const D = /*HKDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; I18N.en = I18N.en || {}; Object.assign(I18N.en, /*HKEN*/{}); } catch (e) {}
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const T = x => (typeof t === "function" ? t(x) : x);
  const L = () => (typeof LANG !== "undefined" ? LANG : "en");
  const copy = txt => { try { navigator.clipboard.writeText(txt).then(() => { if (typeof toast === "function") toast("✓ " + T("Copied")); }, () => prompt(T("Copy"), txt)); } catch (e) { prompt(T("Copy"), txt); } };
  const btn = (txt, cls, fn, id) => { const b = E("button", cls || "", txt); b.type = "button"; if (id) b.id = id; b.onclick = fn; return b; };
  window.hkPanel = function (bx) {
    if (!bx || bx.dataset.hk) return; bx.dataset.hk = "1";
    const badge = () => { const s = bx.closest("details.sub") || bx.closest("details"), sm = s && s.querySelector(":scope > summary");   // the row: «Beta»
      if (sm && !sm.querySelector(".hk-beta")) (sm.querySelector(".sn") || sm).appendChild(E("span", "hk-beta", "Beta")); };
    badge(); setTimeout(badge, 1500);
    let timer = null, msg = "", ask = "";
    const sub = () => bx.closest("details.sub") || bx.closest("details");
    const load = async () => { let r = null; try { r = await fetch("/api/homekit?lang=" + L(), {cache: "no-store"}); } catch (e) { return; }
      if (r.status === 403) { const s = sub(); if (s) s.hidden = true; return; } let j = null; try { j = await r.json(); } catch (e) { return; } paint(j); };
    const act = async (a, x) => { const j = await post("/api/homekit", Object.assign({action: a, lang: L()}, x || {})); msg = j.ok ? "" : (j.error || "error"); ask = "";
      if (j.state) paint(j); else load(); return j; };
    function confirmBox(text, okTxt, fn, id) { const c = E("div", "sens-card"); c.id = id; c.style.marginTop = "8px"; c.append(E("div", "", text));
      const r = E("div", "hk-row"); r.append(btn(okTxt, "", fn, id + "-go"), btn(T("Cancel"), "sec", () => { ask = ""; act("cancel"); })); c.append(r); return c; }
    function paint(j) {
      window.HK_ON = !!j.on; bx.textContent = ""; clearTimeout(timer);
      const S = {off: ["mut", "○ " + T("off")], run: ["", "● " + T("running – not paired yet")], paired: ["", "● " + T("running – paired with the Home app")],
                 err: ["err", "⚠ " + T("Error")], busy: ["mut", "⏳ " + T("working …")]}[j.state] || ["mut", j.state];
      const st = E("div", S[0], S[1] + (j.why ? " – " + j.why : "")); st.id = "hk-state"; st.style.fontWeight = "600";
      if (j.state === "run" || j.state === "paired") st.style.color = "#3fb950";
      const bl = E("div", "mut hk-betaline"); bl.id = "hk-beta"; bl.textContent = T("hk-beta"); bl.style.color = "#f0b429";
      bx.append(bl, st);
      if (msg) { const m = E("div", "err", "⚠ " + msg); m.style.marginTop = "4px"; bx.appendChild(m); }
      if (!j.on) {
        bx.appendChild(E("div", "mut", T("hk-intro")));
        if (j.need_confirm) bx.appendChild(confirmBox(T("Homebridge is installed (about 150 MB) and runs as its own service. Continue?"), T("Continue"), () => act("install"), "hk-confirm"));
        else if (j.state !== "busy") { const r = E("div", "hk-row"); r.append(btn(T("Set up"), "", () => act("setup"), "hk-setup")); bx.appendChild(r); }
      }
      if (j.code && j.state !== "paired") {
        const q = E("div", "hk-qr"); q.id = "hk-qr"; const pic = E("div"); pic.innerHTML = j.qr || ""; const tx = E("div");
        tx.append(E("div", "mut", T("HomeKit setup code")), E("div", "hk-code", j.code), E("div", "mut", T("hk-howto")));
        tx.lastChild.style.cssText = "font-size:13px;margin-top:6px;max-width:260px"; q.append(pic, tx); bx.appendChild(q);
      }
      if (j.on && (j.items || []).length) {
        const h = E("div", "mut", T("In the Home app") + ":"); h.style.marginTop = "10px"; bx.appendChild(h);
        bx.appendChild(E("div", "hk-li", "📷 " + T("Camera with live picture and motion sensor")));
        bx.appendChild(E("div", "hk-li", "🔘 " + j.items.join(" · ")));
      }
      if ((j.log || []).length) { const c = E("div", "mut", T("Refused from the Home app:")); c.style.marginTop = "8px"; bx.appendChild(c);
        j.log.forEach(x => { const r = E("div", "mut hk-li", "· " + new Date(x.t * 1000).toLocaleTimeString().slice(0, 5) + " " + x.name + " – " + x.why); bx.appendChild(r); }); }
      if ((j.cmds || []).length) { const c = E("div", "sens-card"); c.style.marginTop = "8px"; c.append(E("div", "", T("Once in a terminal on the Pi:")));
        const pre = E("pre", "", j.cmds.join("\n")); pre.style.cssText = "white-space:pre-wrap;word-break:break-all;font-size:12px;margin:6px 0";
        c.append(pre, btn("⧉ " + T("Copy"), "sec", () => copy(j.cmds.join("\n"))), btn(T("Done – check again"), "sec", () => act("retry"))); bx.appendChild(c); }
      // settings
      const set = E("div"); set.style.marginTop = "10px";
      const qs = E("select"); qs.id = "hk-quality";
      [["copy", T("Copy the stream (little CPU)")], ["720p", T("720p, encoded again (more CPU)")]].forEach(([v, n]) => { const o = E("option", "", n); o.value = v; qs.appendChild(o); });
      qs.value = j.quality; qs.onchange = () => act("quality", {value: qs.value});
      const ql = E("label", "row"); ql.style.cssText = "gap:8px;align-items:center;flex-wrap:wrap"; ql.append(E("span", "", T("Camera quality")), qs); set.appendChild(ql);
      const cpu = E("div", "mut", T("CPU") + ": " + (j.quality === "720p" ? j.cpu["720p"] : j.cpu.copy) + " · Homebridge " + j.cpu.idle);
      cpu.style.fontSize = "12px"; set.appendChild(cpu);
      if (j.quality === "copy" && j.quality_eff !== "copy") { const w = E("div", "mut", "ℹ " + T("mediamtx is missing - the camera is encoded again (720p)")); w.style.fontSize = "12px"; set.appendChild(w); }
      const ss = E("select"); ss.id = "hk-step"; (j.steps || []).forEach(v => { const o = E("option", "", v + "°"); o.value = v; ss.appendChild(o); });
      ss.value = String(j.step); ss.onchange = () => act("step", {value: parseInt(ss.value, 10)});
      const sl = E("label", "row"); sl.style.cssText = "gap:8px;align-items:center;margin-top:6px"; sl.append(E("span", "", T("Head step (left / right / up / down)")), ss); set.appendChild(sl);
      if (j.pin) {
        const r = E("label", "row tg"), cb = E("input"); cb.type = "checkbox"; cb.className = "sw"; cb.id = "hk-nopin"; cb.checked = !!j.nopin;
        cb.onchange = () => { if (cb.checked && !confirm(T("Allow switching off from the Home app without the PIN? Everybody with access to your Home can then switch the protection off."))) { cb.checked = false; return; } act("nopin", {value: cb.checked}); };
        r.append(E("span", "", T("Allow «Schutz» off from the Home app despite the PIN")), cb); r.style.marginTop = "6px"; set.appendChild(r);
        const n = E("div", "mut", j.nopin ? "⚠ " + T("allowed by you") : T("Standard: refused – a PIN for switching off is set.")); n.style.fontSize = "12px"; set.appendChild(n);
      }
      bx.appendChild(set);
      if (j.on && j.state !== "busy") {
        const r = E("div", "hk-row");
        r.append(btn(T("Pair again"), "sec", () => { ask = "repair"; paint(j); }, "hk-repair"), btn(T("Switch off / uninstall"), "red", () => { ask = "uninstall"; paint(j); }, "hk-off"));
        bx.appendChild(r);
        if (ask === "repair") bx.appendChild(confirmBox(T("New code: remove «MoveEye» in the Home app first, then add it again with the new code."), T("Pair again"), () => act("repair"), "hk-ask"));
        if (ask === "uninstall") bx.appendChild(confirmBox(T("Remove Homebridge and everything MoveEye installed for Apple Home? The devices disappear from the Home app."), T("Switch off / uninstall"), () => act("uninstall"), "hk-ask"));
      }
      const nt = E("div", "mut", T("hk-note")); nt.style.cssText = "font-size:12px;margin-top:10px"; bx.appendChild(nt);
      if (j.state === "busy" || (j.state === "run" && j.why)) timer = setTimeout(load, j.state === "busy" ? 1500 : 4000);
    }
    load(); const s = sub(); if (s) s.addEventListener("toggle", () => { if (s.open) load(); });
  };
  const go = () => { const b = document.getElementById("hk-card"); if (b) hkPanel(b); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => setTimeout(go, 0)); else setTimeout(go, 0);
})();
</script>
"""
_hk_g = '{sec: "MQTT / Home Assistant", title: "MQTT / Home Assistant", ic: "🏠"}]},'
_hk_c = '<details class="card" data-view="guest" data-vgroup="Panels" data-vlabel="Guest access">'
_hk_m = '"sec:MQTT / Home Assistant": c => c.mqtt_on,'
if _hk_g in WEB_PAGE and _hk_c in WEB_PAGE and "hkPanel" not in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace(_hk_g, _hk_g[:-3] + ', {card: "applehome", title: "Apple Home", ic: "🏠"}]},', 1)
    WEB_PAGE = WEB_PAGE.replace(_hk_c, HK_CARD_HTML + _hk_c, 1)
    WEB_PAGE = WEB_PAGE.replace(_hk_m, _hk_m + ' "applehome": () => !!window.HK_ON,', 1)
    WEB_PAGE = WEB_PAGE.replace("</body>", HK_PANEL_JS + "</body>", 1)

# english key: (de, fr, it, rm)
_HX_HK = {
    "running – not paired yet": ("läuft – noch nicht gekoppelt", "actif – pas encore couplé", "attivo – non ancora abbinato", "funcziuna – anc betg collià"),
    "running – paired with the Home app": ("läuft – mit der Home-App gekoppelt", "actif – couplé avec l’app Maison", "attivo – abbinato all’app Casa",
                                           "funcziuna – collià cun l’app Chasa"),
    "hk-intro": ("MoveEye in der Home-App von iPhone, iPad und Mac: Kamera mit Live-Bild, Bewegungsmelder bei Alarm, Schalter «Schutz», "
                 "Kopf-Positionen, Patrouille, Folgen und Licht. Dafür richtet MoveEye Homebridge als eigenen Dienst auf dem Pi ein (nur im Heimnetz).",
                 "MoveEye dans l’app Maison de l’iPhone, l’iPad et du Mac : caméra avec image en direct, détecteur de mouvement en cas d’alarme, "
                 "interrupteur «Protection», positions de la tête, patrouille, suivre et lumière. MoveEye installe pour cela Homebridge comme service "
                 "propre sur le Pi (seulement dans le réseau domestique).",
                 "MoveEye nell’app Casa di iPhone, iPad e Mac: videocamera con immagine dal vivo, sensore di movimento in caso di allarme, interruttore "
                 "«Protezione», posizioni della testa, pattuglia, segui e luce. Per questo MoveEye installa Homebridge come servizio proprio sul Pi "
                 "(solo nella rete di casa).",
                 "MoveEye en l’app Chasa dad iPhone, iPad e Mac: camera cun maletg live, sensor da moviment tar in alarm, interruptur «Protecziun», "
                 "posiziuns dal chau, patruglia, suandar e glisch. Per quai endrizza MoveEye Homebridge sco agen servetsch sin il Pi (mo en la rait da chasa)."),
    "Set up": ("Einrichten", "Configurer", "Configura", "Endrizzar"),
    "hk-beta": ("Beta – erstes Einrichten ist der Test; bei Problemen ein Bildschirmfoto schicken",
                "Bêta – la première configuration est le test ; en cas de problème, envoie une capture d’écran",
                "Beta – la prima configurazione è il test; in caso di problemi invia uno screenshot",
                "Beta – l’emprima configuraziun è il test; tar problems trametter in maletg dal visur"),
    "Homebridge is installed (about 150 MB) and runs as its own service. Continue?": (
        "Homebridge wird installiert (ca. 150 MB) und läuft als eigener Dienst. Weiter?",
        "Homebridge sera installé (env. 150 Mo) et tournera comme service propre. Continuer ?",
        "Homebridge viene installato (circa 150 MB) e gira come servizio proprio. Continuare?",
        "Homebridge vegn installà (ca. 150 MB) e funcziuna sco agen servetsch. Vinavant?"),
    "HomeKit setup code": ("HomeKit-Code", "Code de configuration HomeKit", "Codice di configurazione HomeKit", "Code HomeKit"),
    "hk-howto": ("iPhone: Home-App → ＋ → Gerät hinzufügen → diesen QR-Code scannen (oder «Weitere Optionen» und den Code eingeben). "
                 "Die Meldung «Nicht zertifiziertes Gerät» mit «Trotzdem hinzufügen» bestätigen.",
                 "iPhone : app Maison → ＋ → Ajouter un appareil → scanner ce code QR (ou «Plus d’options» et saisir le code). "
                 "Confirmer «Appareil non certifié» avec «Ajouter quand même».",
                 "iPhone: app Casa → ＋ → Aggiungi accessorio → scansiona questo codice QR (o «Altre opzioni» e inserisci il codice). "
                 "Conferma «Accessorio non certificato» con «Aggiungi comunque».",
                 "iPhone: app Chasa → ＋ → Agiuntar apparat → scannar quest code QR (u «Ulteriuras opziuns» ed endatar il code). "
                 "Confermar «Apparat betg certifitgà» cun «Tuttina agiuntar»."),
    "In the Home app": ("In der Home-App", "Dans l’app Maison", "Nell’app Casa", "En l’app Chasa"),
    "Camera with live picture and motion sensor": ("Kamera mit Live-Bild und Bewegungsmelder", "Caméra avec image en direct et détecteur de mouvement",
                                                   "Videocamera con immagine dal vivo e sensore di movimento", "Camera cun maletg live e sensor da moviment"),
    "Refused from the Home app:": ("Aus der Home-App abgelehnt:", "Refusé depuis l’app Maison :", "Rifiutato dall’app Casa:", "Refusà da l’app Chasa:"),
    "Done – check again": ("Erledigt – nochmals prüfen", "Fait – vérifier à nouveau", "Fatto – controlla di nuovo", "Fatg – controllar anc ina giada"),
    "Camera quality": ("Kamera-Qualität", "Qualité de la caméra", "Qualità della videocamera", "Qualitad da la camera"),
    "Copy the stream (little CPU)": ("Videostrom kopieren (wenig Rechenzeit)", "Copier le flux (peu de CPU)", "Copia il flusso (poca CPU)", "Copiar il flux (pauca CPU)"),
    "720p, encoded again (more CPU)": ("720p, neu kodiert (mehr Rechenzeit)", "720p, réencodé (plus de CPU)", "720p, ricodificato (più CPU)",
                                       "720p, codà da nov (dapli CPU)"),
    "CPU": ("Rechenzeit", "CPU", "CPU", "CPU"),
    "mediamtx is missing - the camera is encoded again (720p)": ("mediamtx fehlt – die Kamera wird neu kodiert (720p)",
                                                                 "mediamtx manque – la caméra est réencodée (720p)",
                                                                 "manca mediamtx – la videocamera viene ricodificata (720p)",
                                                                 "mediamtx manca – la camera vegn codada da nov (720p)"),
    "Head step (left / right / up / down)": ("Kopf-Schritt (links / rechts / hoch / runter)", "Pas de la tête (gauche / droite / haut / bas)",
                                             "Passo della testa (sinistra / destra / su / giù)", "Pass dal chau (sanester / dretg / ensi / engiu)"),
    "Allow «Schutz» off from the Home app despite the PIN": ("«Schutz» aus der Home-App trotz PIN ausschalten lassen",
                                                             "Autoriser «Protection» off depuis l’app Maison malgré le PIN",
                                                             "Consenti «Protezione» off dall’app Casa nonostante il PIN",
                                                             "Lubir «Protecziun» off da l’app Chasa malgrà il PIN"),
    "Allow switching off from the Home app without the PIN? Everybody with access to your Home can then switch the protection off.": (
        "Ausschalten aus der Home-App ohne PIN erlauben? Dann kann jeder mit Zugriff auf dein Zuhause den Schutz ausschalten.",
        "Autoriser la désactivation depuis l’app Maison sans PIN ? Toute personne ayant accès à ton domicile pourra alors désactiver la protection.",
        "Consentire lo spegnimento dall’app Casa senza PIN? Chiunque abbia accesso alla tua casa potrà allora spegnere la protezione.",
        "Lubir da deactivar da l’app Chasa senza PIN? Lura po mintgin cun access a tia chasa deactivar la protecziun."),
    "allowed by you": ("von dir erlaubt", "autorisé par toi", "consentito da te", "lubì da tai"),
    "Standard: refused – a PIN for switching off is set.": ("Standard: abgelehnt – eine PIN fürs Ausschalten ist gesetzt.",
                                                            "Par défaut : refusé – un PIN pour désactiver est défini.",
                                                            "Predefinito: rifiutato – è impostato un PIN per spegnere.",
                                                            "Standard: refusà – in PIN per deactivar è fixà."),
    "Pair again": ("Neu koppeln", "Coupler à nouveau", "Abbina di nuovo", "Colliar da nov"),
    "Switch off / uninstall": ("Ausschalten / Deinstallieren", "Désactiver / désinstaller", "Spegni / disinstalla", "Deactivar / deinstallar"),
    "New code: remove «MoveEye» in the Home app first, then add it again with the new code.": (
        "Neuer Code: zuerst «MoveEye» in der Home-App entfernen, dann mit dem neuen Code wieder hinzufügen.",
        "Nouveau code : retire d’abord «MoveEye» dans l’app Maison, puis ajoute-le à nouveau avec le nouveau code.",
        "Nuovo codice: rimuovi prima «MoveEye» nell’app Casa, poi aggiungilo di nuovo con il nuovo codice.",
        "Nov code: l’emprim allontanar «MoveEye» en l’app Chasa, lura agiuntar danovamain cun il nov code."),
    "Remove Homebridge and everything MoveEye installed for Apple Home? The devices disappear from the Home app.": (
        "Homebridge und alles, was MoveEye für Apple Home installiert hat, entfernen? Die Geräte verschwinden aus der Home-App.",
        "Supprimer Homebridge et tout ce que MoveEye a installé pour Apple Home ? Les appareils disparaissent de l’app Maison.",
        "Rimuovere Homebridge e tutto ciò che MoveEye ha installato per Apple Home? Gli accessori spariscono dall’app Casa.",
        "Allontanar Homebridge e tut quai che MoveEye ha installà per Apple Home? Ils apparats svaneschan da l’app Chasa."),
    "hk-note": ("Unterwegs: geht über deine Steuerzentrale (HomePod, Apple TV oder iPad zu Hause) – MoveEye öffnet nichts nach aussen. "
                "Homebridge hört nur im Heimnetz; der Schlüssel für MoveEye steht nur in seiner Einstellungsdatei (nur für Homebridge lesbar).",
                "En déplacement : passe par ton concentrateur (HomePod, Apple TV ou iPad à la maison) – MoveEye n’ouvre rien vers l’extérieur. "
                "Homebridge n’écoute que dans le réseau domestique ; la clé pour MoveEye n’est que dans son fichier de réglages (lisible seulement par Homebridge).",
                "Fuori casa: funziona tramite il tuo hub (HomePod, Apple TV o iPad a casa) – MoveEye non apre nulla verso l’esterno. "
                "Homebridge ascolta solo nella rete di casa; la chiave per MoveEye è solo nel suo file di impostazioni (leggibile solo da Homebridge).",
                "Sin via: va sur tia centrala (HomePod, Apple TV u iPad a chasa) – MoveEye n’avra nagut vers anora. "
                "Homebridge tadla mo en la rait da chasa; la clav per MoveEye è mo en sia datoteca da configuraziun (legibla mo per Homebridge)."),
    "Homebridge does not run": ("Homebridge läuft nicht", "Homebridge ne tourne pas", "Homebridge non è in esecuzione", "Homebridge na funcziuna betg"),
    "starting …": ("startet …", "démarrage …", "avvio …", "cumenza …"),
    "installing Homebridge … (a few minutes)": ("installiere Homebridge … (ein paar Minuten)", "installation de Homebridge … (quelques minutes)",
                                                "installazione di Homebridge … (qualche minuto)", "installescha Homebridge … (in pèr minutas)"),
    "writing the settings …": ("schreibe die Einstellungen …", "écriture des réglages …", "scrittura delle impostazioni …", "scriva las configuraziuns …"),
    "removing …": ("entferne …", "suppression …", "rimozione …", "allontanescha …"),
    "new pairing …": ("neue Kopplung …", "nouveau couplage …", "nuovo abbinamento …", "nov collegament …"),
    "checking …": ("prüfe …", "vérification …", "controllo …", "controllescha …"),
    "Press «Set up» first.": ("Zuerst «Einrichten» drücken.", "Appuie d’abord sur «Configurer».", "Premi prima «Configura».", "L’emprim smatgar «Endrizzar»."),
    "Node.js on this Pi is older than version 18": ("Node.js auf diesem Pi ist älter als Version 18", "Node.js sur ce Pi est plus ancien que la version 18",
                                                    "Node.js su questo Pi è più vecchio della versione 18", "Node.js sin quest Pi è pli vegl che la versiun 18"),
    "no app key could be made (at most 20)": ("kein App-Schlüssel möglich (höchstens 20)", "impossible de créer une clé d’app (20 au plus)",
                                              "impossibile creare una chiave app (al massimo 20)", "nagina clav d’app pussaivla (maximalmain 20)"),
    "a PIN for switching off is set - switch off in MoveEye (or allow it on the Apple Home card)": (
        "eine PIN fürs Ausschalten ist gesetzt – in MoveEye ausschalten (oder auf der Karte Apple Home erlauben)",
        "un PIN pour désactiver est défini – désactive dans MoveEye (ou autorise-le sur la carte Apple Home)",
        "è impostato un PIN per spegnere – spegni in MoveEye (o consentilo nella scheda Apple Home)",
        "in PIN per deactivar è fixà – deactivar en MoveEye (u lubir sin la carta Apple Home)"),
    "an alarm has the head now": ("ein Alarm hat gerade den Kopf", "une alarme a la tête en ce moment", "un allarme ha la testa adesso", "in alarm ha gist il chau"),
    "walk test runs": ("Gehtest läuft", "test de marche en cours", "test di passaggio in corso", "test da chaminar funcziuna"),
    "game round: only the players move the head": ("Spielrunde: nur die Spieler bewegen den Kopf", "partie : seuls les joueurs bougent la tête",
                                                   "partita: solo i giocatori muovono la testa", "runda da gieu: mo ils giugaders movan il chau"),
    "too fast - one command at a time": ("zu schnell – ein Befehl nach dem anderen", "trop rapide – une commande à la fois",
                                         "troppo veloce – un comando alla volta", "memia svelt – in cumond suenter l’auter"),
    "interrupted": ("unterbrochen", "interrompu", "interrotto", "interrut"),
    "no such point": ("diese Position gibt es nicht", "cette position n’existe pas", "questa posizione non esiste", "questa posiziun n’exista betg"),
    "unknown accessory": ("unbekanntes Gerät", "appareil inconnu", "accessorio sconosciuto", "apparat nunenconuschent"),
    "refused": ("abgelehnt", "refusé", "rifiutato", "refusà"),
    "about 1–3 % of one core to copy + 15–25 % for the encoder of MoveEye, only while somebody watches": (
        "ca. 1–3 % eines Kerns fürs Kopieren + 15–25 % für den Kodierer von MoveEye, nur solange jemand zuschaut",
        "env. 1–3 % d’un cœur pour copier + 15–25 % pour l’encodeur de MoveEye, seulement pendant qu’on regarde",
        "circa 1–3 % di un core per copiare + 15–25 % per il codificatore di MoveEye, solo mentre qualcuno guarda",
        "ca. 1–3 % d’in nucleus per copiar + 15–25 % per il codader da MoveEye, mo durant che insatgi guarda"),
    "about 25–40 % of one core, only while somebody watches": ("ca. 25–40 % eines Kerns, nur solange jemand zuschaut",
        "env. 25–40 % d’un cœur, seulement pendant qu’on regarde", "circa 25–40 % di un core, solo mentre qualcuno guarda",
        "ca. 25–40 % d’in nucleus, mo durant che insatgi guarda"),
    "about 1 % and 80 MB of memory": ("ca. 1 % und 80 MB Speicher", "env. 1 % et 80 Mo de mémoire", "circa 1 % e 80 MB di memoria",
                                      "ca. 1 % e 80 MB memoria"),
    "Apple Home: set up in the browser": ("Apple Home: im Browser einrichten", "Apple Home : à configurer dans le navigateur",
                                          "Apple Home: da configurare nel browser", "Apple Home: endrizzar en il navigatur"),
}
HK_EN = {   # English of the note keys (no raw keys in English: MENU_EN for the window / tr, I18N.en for the page)
    "hk-beta": "Beta – setting it up the first time is the test; if something goes wrong, send a screenshot",
    "hk-intro": "MoveEye in the Home app of iPhone, iPad and Mac: camera with live picture, motion sensor at an alarm, switch «Protection», "
                "head positions, patrol, follow and light. For this MoveEye sets up Homebridge as its own service on the Pi (home network only).",
    "hk-howto": "iPhone: Home app → ＋ → Add Accessory → scan this QR code (or «More options» and enter the code). "
                "Confirm «Uncertified Accessory» with «Add Anyway».",
    "hk-note": "Away from home: works through your home hub (HomePod, Apple TV or an iPad at home) – MoveEye opens nothing to the outside. "
               "Homebridge listens only in the home network; the key for MoveEye is only in its settings file (readable only by Homebridge).",
}
MENU_EN.update(HK_EN)
WEB_PAGE = WEB_PAGE.replace("/*HKEN*/{}", json.dumps(HK_EN, ensure_ascii=False), 1)
for _k, _v in _HX_HK.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
WEB_PAGE = WEB_PAGE.replace("/*HKDE*/{}", json.dumps({_k: DE.get(_k, _v[0]) for _k, _v in _HX_HK.items()}, ensure_ascii=False), 1)

# ---- window: a line with the state and a button to the page (the setup is in the browser) -----------------------------------
if GUI_OK:
    _hk_tk_build_section_before = App._build_section

    def _hk_tk_build_section(self, sec, sbody, settings_parent=None):
        _hk_tk_build_section_before(self, sec, sbody, settings_parent)
        if sec != "MQTT / Home Assistant" or CFG.get("lock_on"):
            return
        try:
            s = hk_status()
            txt = {"off": tr("off"), "run": tr("running – not paired yet"), "paired": tr("running – paired with the Home app"),
                   "busy": tr("working …")}.get(s["state"], tr("Error") + " – " + s["why"])
            ttk.Label(sbody, text="🏠 Apple Home: " + txt, style="Mut.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(8, 0))
            ttk.Button(sbody, text=tr("Apple Home: set up in the browser"), command=lambda: self._open_page("/settings")).pack(fill="x", pady=(4, 0))
        except Exception as e:
            log_event("sys", f"Window: Apple Home: {e}"[:160])

    # wraps: App._build_section
    App._build_section = _hk_tk_build_section


# ---- self-test (only for --self-test) ------------------------------------------------------------------------------------------
def apple_home_selftest():
    u = hk_setup_uri("031-45-154", "7OSX")                   # decode it again: 9 signs base 36 + setup ID, IP flag, category 2, code
    v = int(u[7:16], 36)
    assert u.startswith("X-HM://") and u.endswith("7OSX") and len(u) == 20 and v & 0x7FFFFFF == 3145154 and v >> 28 & 1 and v >> 32 == 1, u
    c = hk_new_code()
    assert re.fullmatch(r"\d{3}-\d{2}-\d{3}", c) and c.replace("-", "") not in HK_BAD_CODES
    st0 = dict(CFG.get("hk_st") or {})
    try:
        CFG["hk_st"] = dict(st0, mac="0E:11:22:33:44:55")
        cf = hk_config("me_TESTKEY", "VPW_test_value_long_enough", {"code": "111-22-333", "sid": "AB12"}, ["wlan0"])
    finally:
        CFG["hk_st"] = st0
    t = json.dumps(cf)
    assert cf["bridge"]["bind"] == ["wlan0"] and cf["bridge"]["port"] == HK_PORT and cf["platforms"][0]["localhttp"] is True
    assert cf["platforms"][1]["base"].startswith(("http://127.0.0.1:", "https://127.0.0.1:")) and "/k/hk/photo.jpg?t=" in t
    assert "protect_pin" not in t and "web_password" not in t
    assert "--ignore-scripts" in " ".join(hk_cmds()) and "User=" + HK_USER in hk_unit_text() and "ProtectSystem=strict" in hk_unit_text()
    assert DEFAULTS["hk_on"] is False and "hk_on" in USER_SETTINGS_DENY and "hkPanel" in WEB_PAGE and "/*HKDE*/" not in WEB_PAGE
    assert '{card: "applehome"' in WEB_PAGE.replace(" ", "").replace('{card:"applehome"', '{card: "applehome"')
    assert all(tr(k, "en") == v for k, v in HK_EN.items()) and "/*HKEN*/" not in WEB_PAGE
    for k in _HX_HK:
        assert all(TRX[L].get(k) for L in ("fr", "it", "rm")) and DE.get(k), f"text without translation: {k}"
    assert all(len(v) == 5 for v in HK_NAMES.values())
    return "setup URI, config (LAN bind, local trigger, no PIN), hardened unit, off by default, admin only; 5 languages"


SELFTEST_EXTRA.append(("Apple Home (Homebridge): setup code, config, card (639zzzo)", apple_home_selftest))
