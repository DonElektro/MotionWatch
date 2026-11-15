#!/usr/bin/env python3
"""Test «📶 Mein Handy-Hotspot bevorzugen» (MoveEye Teil 639zzzzf) – mit erfundenem nmcli / iw / ip, nie mit dem echten Netz.

  Ein Ordner mit eigenen Programmen `nmcli`, `iw`, `ip` steht vorne im PATH; sie lesen und schreiben einen erfundenen Zustand
  (gespeicherte Netze, aktive Verbindung, sichtbare Netze, Geräte im eigenen WLAN, Fehler beim Verbinden) und schreiben jeden
  Aufruf mit. Das Internet nach dem Wechsel ist erfunden (hspref_online ersetzt).

  A) im eigenen Prozess (gebaute Datei geladen): Schalter aus = nichts passiert (kein nmcli, alte Netz-Automatik unverändert),
     aus einem anderen WLAN, aus dem eigenen WLAN (mit Liste und ohne Liste = kurzer Blick), ohne Netz, Geräte im eigenen
     WLAN = warten, Alarm / Update / Sicherung / Homepage = warten, Fehler = zurück + Pause 2 / 5 / 10 min, kein Internet =
     zurück, bald wieder weg = Fehler (kein Hin und Her), von Hand umgeschaltet = Ruhe, Name nie in Push, nie ein Passwort im
     Protokoll, Texte in 5 Sprachen.
  B) --browser: MoveEye (Demo, eigener Daten-Ordner, erfundenes nmcli) – Karte «WLAN / Hotspot» 390 px dunkel, Bild nach --bilder.

  python3 werkzeuge/hotspot_bevorzugen_test.py [--datei X.py] [--browser] [--bilder ORDNER]
"""
import argparse
import base64
import glob
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
FEHLER = []

# ---- the made-up network tools (one script, three names) ---------------------------------------------------------------------
FAKE = r'''#!/usr/bin/env python3
import json, os, sys
P = os.environ["MW_FAKE_NET"]
st = json.load(open(P))
me = os.path.basename(sys.argv[0]); a = sys.argv[1:]
st["calls"].append(me + " " + " ".join(a))
out, code = "", 0
AP = "MotionWatch-Hotspot"
def save():
    json.dump(st, open(P, "w"))
def esc(s):
    return s.replace("\\", "\\\\").replace(":", "\\:")
byid = {c["uuid"]: c for c in st["saved"]}
apon = "u-ap" in st["active"]
if me == "nmcli":
    if "--wait" in a:
        i = a.index("--wait"); a = a[:i] + a[i + 2:]
    if a[:4] == ["-t", "-f", "RUNNING", "general"]:
        out = "running\n"
    elif a[:2] == ["-t", "-f"] and a[3:5] == ["connection", "show"] and "--active" in a:
        f = a[2].split(",")
        for u in st["active"]:
            c = byid[u]; row = {"NAME": c["name"], "UUID": u, "TYPE": "802-11-wireless", "DEVICE": "wlan0"}
            out += ":".join(esc(row[k]) for k in f) + "\n"
    elif a[:2] == ["-t", "-f"] and a[3:5] == ["connection", "show"]:
        f = a[2].split(",")
        for c in st["saved"]:
            row = {"NAME": c["name"], "UUID": c["uuid"], "TYPE": "802-11-wireless", "AUTOCONNECT": "yes", "AUTOCONNECT-PRIORITY": str(c.get("prio", 0)),
                   "ACTIVE": "yes" if c["uuid"] in st["active"] else "no"}
            out += ":".join(esc(row[k]) for k in f) + "\n"
    elif a[:3] == ["-t", "-g", "802-11-wireless.ssid,802-11-wireless.mode"]:
        c = byid.get(a[-1]); out = (c["ssid"] + "\n" + c.get("mode", "infrastructure") + "\n") if c else ""
    elif a[:4] == ["-t", "-f", "SSID,SIGNAL", "device"]:
        r = a[a.index("--rescan") + 1]
        st["rescans"].append(r)
        if apon and not st.get("dual") and not st.get("scan_in_ap"):
            out = ""                                    # NetworkManager in AP mode: no list
        else:
            vis = dict(st["visible"])
            if apon:
                vis["MoveEye"] = 99
            out = "".join(esc(s) + ":" + str(v) + "\n" for s, v in vis.items())
    elif a[:2] == ["connection", "up"]:
        u = a[3] if a[2] == "uuid" else next(c["uuid"] for c in st["saved"] if c["name"] == a[3])
        c = byid[u]
        if u != "u-ap" and (u in st["up_fail"] or c["ssid"] not in st["visible"]):
            code, out = 4, "Error: Connection activation failed: (7) Secrets were required, but not provided."
        else:
            keep = [x for x in st["active"] if x == "u-ap" and st.get("dual")] if u != "u-ap" else ([x for x in st["active"] if st.get("dual")])
            st["active"] = [x for x in keep if x != u] + [u]
    elif a[:2] == ["connection", "down"]:
        u = a[3] if a[2] == "uuid" else next(c["uuid"] for c in st["saved"] if c["name"] == a[3])
        if u in st["active"]:
            st["active"].remove(u)
        else:
            code, out = 10, "Error: 'x' is not an active connection."
    elif a[:2] == ["connection", "modify"] or a[:2] == ["connection", "add"] or a[:2] == ["device", "set"]:
        pass
    else:
        pass
elif me == "iw":
    if a[2:] == ["station", "dump"]:
        out = "".join("Station aa:bb:cc:dd:ee:%02x (on wlan0)\n\tsignal: -50\n" % i for i in range(st["clients"] if apon else 0))
    elif a[2:] == ["link"]:
        u = next((x for x in st["active"] if x != "u-ap"), None)
        out = ("Connected to 11:22:33:44:55:66 (on wlan0)\n\tSSID: %s\n\tsignal: -55 dBm\n\ttx bitrate: 72.2 MBit/s\n" % byid[u]["ssid"]) if u else "Not connected.\n"
elif me == "ip":
    if a[:3] == ["-4", "-o", "addr"]:
        if apon and not st.get("dual"):
            out = "3: wlan0    inet 10.42.0.1/24 brd 10.42.0.255 scope global wlan0\n"
        elif any(x != "u-ap" for x in st["active"]):
            out = "3: wlan0    inet 192.168.77.23/24 brd 192.168.77.255 scope global wlan0\n"
save()
sys.stdout.write(out if code == 0 else "")
sys.stderr.write(out if code else "")
sys.exit(code)
'''


def fake_bin(tmp, net):
    b = os.path.join(tmp, "fakebin"); os.makedirs(b, exist_ok=True)
    for n in ("nmcli", "iw", "ip"):
        p = os.path.join(b, n)
        with open(p, "w") as f:
            f.write(FAKE.replace("#!/usr/bin/env python3", "#!" + sys.executable, 1))
        os.chmod(p, 0o755)
    json.dump(net, open(os.path.join(tmp, "net.json"), "w"))
    return b


def netz(**kw):
    n = {"saved": [{"name": "Zuhause", "uuid": "u-home", "ssid": "Zuhause", "prio": 20},
                   {"name": "Elektros iPhone", "uuid": "u-phone", "ssid": "Elektros iPhone"},
                   {"name": "MotionWatch-Hotspot", "uuid": "u-ap", "ssid": "MoveEye", "mode": "ap"}],
         "active": ["u-home"], "visible": {"Zuhause": 70, "Elektros iPhone": 55}, "up_fail": [], "clients": 0, "dual": False,
         "scan_in_ap": False, "calls": [], "rescans": []}
    n.update(kw)
    return n


TEIL_A = r'''
import json, os, sys, threading, time
ns = {"__name__": "mw_hsp_test", "__file__": os.path.abspath(sys.argv[1])}
exec(compile(open(sys.argv[1], encoding="utf-8").read(), sys.argv[1], "exec"), ns)
P = os.environ["MW_FAKE_NET"]
C, S, H, W = ns["CFG"], ns["STATE"], ns["HSPREF"], ns["WIFI"]
out = {}
logs, pushes = [], []
_le = ns["log_event"]
ns["log_event"] = lambda kind, text, *a, **k: logs.append(text)
ns["save_settings"] = lambda *a, **k: None
class N:
    def info(self, *a, **k): pushes.append(a)
    def alert(self, *a, **k): pushes.append(a)
class WW:
    notifier = N(); writer = None
ns["WATCH_REF"]["w"] = WW()
NET = {"inet": {}}
ns["hspref_online"] = lambda secs=40: NET["inet"].get(cur_ssid(), True)
C.update(lang="de", net_mode="auto", camping=False, hotspot_ssid="MoveEye", hotspot_password="geheim-pw-123", hs_prefer=False, hs_prefer_ssid="")
S.update(persons=0, tracking=False, recording=False)
W["backend"] = None; W["iface"] = "wlan0"
ns["NETAUTO"]["paused"] = False
def net(**kw):
    st = json.load(open(P)); st.update(kw); json.dump(st, open(P, "w"))
def st():
    return json.load(open(P))
def cur_ssid():
    s = st(); u = next((x for x in s["active"] if x != "u-ap"), None)
    return next((c["ssid"] for c in s["saved"] if c["uuid"] == u), "")
def tick():
    net(calls=[], rescans=[]); H["tick"] = 0.0; H["saved_t"] = -1e9
    r = ns["hspref_tick"](True)
    return r
def ups():
    return [c for c in st()["calls"] if "connection up uuid u-phone" in c]
def reset(**kw):
    H.update(fails=0, next=0.0, on_since=0.0, peek=0.0, hand=-1e9, rescan=0.0)
    base = json.load(open(P + ".start")); base.update(kw); json.dump(base, open(P, "w"))
    W.update(busy=False, hs_busy=False, job="", job_ok=None)
    ns["NETAUTO"]["paused"] = False
    logs.clear()
json.dump(st(), open(P + ".start", "w"))
de = lambda: ns["hspref_text"]("de")
# 0 switch off: old behaviour, no nmcli at all from the preference; the network automatic still runs its own step
reset()
r = tick(); out["off"] = [r, st()["calls"], de()]
na = ns["NetAuto"].__new__(ns["NetAuto"]); na.lost_since = None; na.next_retry = None
S["hotspot"] = {"on": False, "clients": 0}; S["wifi"] = {"connected": True, "ssid": "Zuhause"}
net(calls=[]); na.step(); out["off_netauto"] = [S.get("netauto"), [c for c in st()["calls"] if "SSID,SIGNAL" in c or "connection up" in c]]
C.update(hs_prefer=True, hs_prefer_ssid="")
out["none"] = [tick(), de()]
# 1 from another Wi-Fi (home) -> the phone hotspot
C["hs_prefer_ssid"] = "Elektros iPhone"
reset()
r = tick(); out["home"] = [r, st()["active"], ups(), de(), list(logs), st()["rescans"]]
r = tick(); out["home_again"] = [r, ups()]
# 2 own Wi-Fi (AP), a device connected -> wait; nobody -> switch (NetworkManager has no list in AP mode: short look)
reset(active=["u-ap"], clients=1)
r = tick(); out["ap_dev"] = [r, de(), ups(), st()["active"]]
net(clients=2); r = tick(); out["ap_dev2"] = de()
net(clients=0)
r = tick(); out["ap_peek"] = [r, st()["active"], ups(), st()["rescans"], list(logs)]
r = tick(); out["ap_peek_ok"] = [r, de()]
# 2b own Wi-Fi, the phone is not there: the look takes the own Wi-Fi back, the next look waits 5 min
reset(active=["u-ap"], visible={"Zuhause": 70})
r = tick(); out["ap_away"] = [r, st()["active"], [c for c in st()["calls"] if "MotionWatch-Hotspot" in c]]
r = tick(); out["ap_wait5"] = [r, de(), st()["calls"].count("nmcli connection down id MotionWatch-Hotspot")]
# 2c own Wi-Fi where the adapter can list (scan_in_ap): direct switch, but not with a device
reset(active=["u-ap"], scan_in_ap=True)
r = tick(); out["ap_list"] = [r, st()["active"], [c for c in st()["calls"] if "--rescan yes" in c]]
# 2d second adapter (repeater): devices in the own Wi-Fi do not block, the own Wi-Fi stays on
reset(active=["u-ap", "u-home"], dual=True, clients=3)
ns["DUAL"].update(on=True, up="wlan1", ap="wlan0")
r = tick(); out["dual"] = [r, st()["active"], ups()]
ns["DUAL"].update(on=False, up="", ap="")
# 3 no network at all
reset(active=[])
r = tick(); out["none_net"] = [r, st()["active"], st()["rescans"]]
# 4 alarm / update / backup / homepage: wait, then switch
for k, on, off in (("alarm", lambda: S.update(persons=1), lambda: S.update(persons=0)),
                   ("track", lambda: S.update(tracking=True), lambda: S.update(tracking=False)),
                   ("theft", lambda: ns["GPSMOD"].update(alarm_t=time.time()), lambda: ns["GPSMOD"].update(alarm_t=0.0)),
                   ("rec", lambda: setattr(WW, "writer", object()), lambda: setattr(WW, "writer", None)),
                   ("update", lambda: ns["UPD_PROG"].update(phase="download"), lambda: ns["UPD_PROG"].update(phase="")),
                   ("backup", lambda: ns.__setitem__("BACKUP", type("B", (), {"busy": "/x/a.mp4"})()), lambda: ns.__setitem__("BACKUP", None)),
                   ("homepage", lambda: ns["HP"].update(busy="uploading"), lambda: ns["HP"].update(busy=""))):
    reset(); on()
    r = tick(); a = [r, de(), ups()]
    off(); r = tick(); out["blk_" + k] = a + [r]
# 5 failure: back to home, pause 2 / 5 / 10 / 10 min, nothing in between
reset(up_fail=["u-phone"])
seq = []
for i in range(4):
    H["next"] = 0.0
    r = tick(); s = st(); seq.append([r, H["n"], s["active"], len(ups()), round((H["next"] - time.monotonic()) / 60)])
    r2 = tick(); seq[-1] += [r2, len(ups())]
out["fail_seq"] = seq; out["fail_log"] = list(logs); out["fail_job"] = W["job"]
# 5b from the own Wi-Fi: failure -> the own Wi-Fi comes back
reset(active=["u-ap"], up_fail=["u-phone"])
r = tick(); out["fail_ap"] = [r, st()["active"], W["job"]]
# 5c connected, but no internet: down again, back home
reset(); NET["inet"] = {"Elektros iPhone": False}
r = tick(); out["noinet"] = [r, st()["active"], [c for c in st()["calls"] if "connection down uuid u-phone" in c], list(logs)]
NET["inet"] = {}
# 6 no flapping: switched, gone again after a moment -> counts as failure, no immediate return
reset()
r = tick(); a = [r, st()["active"]]
net(active=["u-home"])                              # NetworkManager fell back to home (phone went away)
r = tick(); out["flap"] = a + [r, ups(), round((H["next"] - time.monotonic()) / 60)]
H["next"] = 0.0; H["on_since"] = time.monotonic() - 700        # stayed 11+ min: a drop later is no failure
net(active=["u-phone"]); H["fails"] = 2
r = tick(); out["stable"] = [r, H["fails"]]
# 7 switched by hand: quiet
reset(); ns["netauto_pause"]()
r = tick(); out["hand"] = [r, de(), ups()]
reset(); C["camping"] = True; r = tick(); out["camping"] = [r, ups()]; C["camping"] = False
# 8 the setting, the page data, privacy
reset()
out["set_bad"] = list(ns["hspref_set"](True, "Nachbar-WLAN"))
out["set_ok"] = [list(ns["hspref_set"](True, "Elektros iPhone")), C["hs_prefer_ssid"], C["hs_prefer"]]
out["status"] = ns["wifi_status"]()["hsp"]
out["push_ssids"] = ns["push_ssids"]()
p = ns["push_no_ssid"]({"event": "info", "text": "Elektros iPhone weg", "info_title": "x"})
out["push_clean"] = p["text"]
out["pushes"] = [str(x) for x in pushes]
out["pw_in_log"] = any("geheim-pw-123" in str(x) for x in logs)
out["txt"] = {}
for L in ("de", "en", "fr", "it", "rm"):
    H.update(state=ns["HSP_DEV1"], n=1); a = ns["hspref_text"](L)
    H.update(state=ns["HSP_AWAY"], n=0); b = ns["hspref_text"](L)
    H.update(state=ns["HSP_OK"]); c = ns["hspref_text"](L)
    out["txt"][L] = [a, b, c, ns["tr"]("Prefer my phone hotspot", L)]
out["selftest"] = ns["hspref_selftest"]()
print("ERG " + json.dumps(out, ensure_ascii=False, default=str))
os._exit(0)
'''


def ok(bed, text):
    print(("  ok     " if bed else "  FEHLER ") + text, flush=True)
    if not bed:
        FEHLER.append(text)


def teil_a(datei, tmp):
    print("A) Logik im eigenen Prozess (erfundenes nmcli / iw / ip)", flush=True)
    home = os.path.join(tmp, "a"); os.makedirs(home)
    b = fake_bin(tmp, netz())
    env = dict(os.environ, MOTIONWATCH_HOME=home, MW_FAKE_NET=os.path.join(tmp, "net.json"), PATH=b + os.pathsep + os.environ.get("PATH", ""))
    r = subprocess.run([sys.executable, "-c", TEIL_A, datei], capture_output=True, text=True, timeout=900, env=env, cwd=tmp)
    e = next((json.loads(ln[4:]) for ln in r.stdout.splitlines() if ln.startswith("ERG ")), None)
    if e is None:
        print((r.stdout + r.stderr)[-4000:])
        ok(False, "Teil A lief nicht durch")
        return
    ok(e["off"][0] == "off" and e["off"][1] == [] and e["off"][2] == "", "Schalter aus: nichts, kein nmcli-Aufruf (%s)" % e["off"][1][:3])
    ok(e["off_netauto"][1] == [] and e["off_netauto"][0], "Schalter aus: Netz-Automatik wie bisher (%s)" % e["off_netauto"][0])
    ok(e["none"][0].startswith("choose a saved") and "gespeichertes Netz" in e["none"][1], "an ohne Netz: «%s»" % e["none"][1])
    h = e["home"]
    ok(h[0] == "connected" and h[1] == ["u-phone"] and len(h[2]) == 1 and "uuid u-phone" in h[2][0], "aus dem Heim-WLAN zum Handy-Hotspot (%s)" % h[2])
    ok(h[3] == "📶 Hotspot «Elektros iPhone»: verbunden", "Anzeige «%s»" % h[3])
    ok(any("switching (from «Zuhause»)" in x for x in h[4]) and any("connected, internet works" in x for x in h[4]), "Protokoll: %s" % h[4][:2])
    ok(h[5] == ["auto", "no"] or h[5][:1] == ["auto"], "Suche: einmal neu, NetworkManager-Liste (%s)" % h[5])
    ok(e["home_again"][0] == "connected" and e["home_again"][1] == [], "verbunden: kein neuer Wechsel")
    a = e["ap_dev"]
    ok(a[0].startswith("waiting, because") and a[1] == "📶 Hotspot «Elektros iPhone»: wartet, weil 1 Gerät verbunden ist" and a[2] == [] and a[3] == ["u-ap"],
       "eigenes WLAN + 1 Gerät: «%s»" % a[1])
    ok(e["ap_dev2"].endswith("wartet, weil 2 Geräte verbunden sind"), "2 Geräte: «%s»" % e["ap_dev2"])
    a = e["ap_peek"]
    ok(a[0] == "connected" and a[1] == ["u-phone"] and "yes" in a[3], "eigenes WLAN, niemand verbunden: kurzer Blick, dann gewechselt (%s, %s)" % (a[1], a[3]))
    ok(any("switching (from the own Wi-Fi)" in x for x in a[4]), "Protokoll aus dem eigenen WLAN")
    a = e["ap_away"]
    ok(a[0] == "not in range" and a[1] == ["u-ap"] and any("down id" in c for c in a[2]) and any("up id" in c for c in a[2]),
       "Hotspot nicht da: eigenes WLAN wieder an (%s)" % a[2])
    ok(e["ap_wait5"][1].endswith("eigenes WLAN: nächster Blick in 5 min") and e["ap_wait5"][2] == 0, "nächster Blick erst in 5 min: «%s»" % e["ap_wait5"][1])
    ok(e["ap_list"][0] == "connected" and e["ap_list"][1] == ["u-phone"] and e["ap_list"][2] == [], "eigenes WLAN mit Liste: direkt gewechselt")
    ok(e["dual"][0] == "connected" and e["dual"][1] == ["u-ap", "u-phone"] and "ifname wlan1" in (e["dual"][2] or [""])[0],
       "zweiter Adapter: Geräte bremsen nicht, eigenes WLAN bleibt (%s)" % e["dual"][1])
    ok(e["none_net"][0] == "connected" and e["none_net"][1] == ["u-phone"], "ohne Netz: verbunden (%s)" % e["none_net"][1])
    for k in ("alarm", "track", "theft", "rec", "update", "backup", "homepage"):
        b_ = e["blk_" + k]
        ok(b_[0].startswith("found - waiting") and b_[2] == [] and b_[3] == "connected", "%s: wartet («%s»), danach verbunden" % (k, b_[1]))
    s = e["fail_seq"]
    ok([x[4] for x in s] == [2, 5, 10, 10] and all(x[2] == ["u-home"] and x[3] == 1 and x[6] == 0 for x in s),
       "Fehler: zurück ins Heim-WLAN, Pause 2 / 5 / 10 / 10 min, dazwischen kein Versuch (%s)" % [x[4] for x in s])
    ok(s[0][5].startswith("after a failure") and "back on «Zuhause»" in e["fail_job"], "Anzeige / Auftrag: %s · %s" % (s[0][5], e["fail_job"]))
    ok(e["fail_ap"][1] == ["u-ap"] and "own Wi-Fi on" in e["fail_ap"][2], "Fehler aus dem eigenen WLAN: eigenes WLAN wieder an (%s)" % e["fail_ap"][2])
    n = e["noinet"]
    ok(n[0].startswith("after a failure") and n[1] == ["u-home"] and n[2] and any("no internet" in x for x in n[3]), "kein Internet: getrennt, zurück (%s)" % n[1])
    f = e["flap"]
    ok(f[0] == "connected" and f[2].startswith("after a failure") and f[3] == [] and f[4] == 2, "bald wieder weg: Fehler, kein sofortiger Wechsel (%s)" % f[2])
    ok(e["stable"] == ["connected", 0], "10 min stabil: Zähler wieder 0 (%s)" % e["stable"])
    ok(e["hand"][0] == "paused (switched by hand)" and e["hand"][2] == [] and "von Hand" in e["hand"][1], "von Hand umgeschaltet: «%s»" % e["hand"][1])
    ok(e["camping"][0] == "paused (switched by hand)" and e["camping"][1] == [], "Camping-Profil: Ruhe")
    ok(e["set_bad"][0] is False and e["set_ok"] == [[True, ""], "Elektros iPhone", True], "Wahl nur aus gespeicherten Netzen (%s)" % e["set_bad"])
    ok(e["status"]["ssid"] == "Elektros iPhone" and "state" in e["status"], "/api/wifi zeigt hsp (%s)" % e["status"])
    ok("Elektros iPhone" in e["push_ssids"] and "Elektros iPhone" not in e["push_clean"], "Name nie in Push: «%s»" % e["push_clean"])
    ok(e["pushes"] == [], "keine eigene Push-Nachricht (%s)" % e["pushes"][:2])
    ok(not e["pw_in_log"], "kein Passwort im Protokoll")
    for L, (a_, b_, c_, sw) in e["txt"].items():
        ok("Elektros iPhone" in a_ and "1" in a_ and "{" not in a_ + b_ + c_ and (L == "en" or a_ != e["txt"]["en"][0]), "%s: «%s» · «%s» · «%s» · %s" % (L, a_, b_, c_, sw))
    ok(e["selftest"] is True, "Selbsttest-Funktion")


WRAP = r'''
import json, os, sys, time, threading
D = sys.argv[1]
src = open(D, encoding="utf-8").read()
i = src.rfind('\nif __name__ == "__main__":')
patch = """
hspref_online = lambda secs=40: True
# the demo blocks /api/wifi (210); here nmcli / iw / ip are invented (PATH), so the test lets it through
DEMO_BLOCK = tuple(x for x in DEMO_BLOCK if x != "/api/wifi")
def _hsp_test_loop():                                # the demo has no network automatic: the test runs the look itself
    while True:
        try:
            hspref_tick()
        except Exception as e:
            print("hsp", e)
        time.sleep(1)
threading.Thread(target=_hsp_test_loop, daemon=True).start()
"""
src = src[:i] + patch + src[i:]
sys.argv = [D] + sys.argv[2:]
exec(compile(src, D, "exec"), {"__name__": "__main__", "__file__": D})
'''
PW = "hsp-test-pw-1"


def teil_b(datei, tmp, bilder):
    print("B) Karte «WLAN / Hotspot» 390 px dunkel (MoveEye Demo, erfundenes nmcli)", flush=True)
    from playwright.sync_api import sync_playwright
    os.makedirs(bilder, exist_ok=True)
    tb = os.path.join(tmp, "b"); os.makedirs(tb)
    b = fake_bin(tb, netz(active=["u-ap"], clients=1))
    cfg = os.path.join(tb, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "news_popup": False,
          "theme": "dark", "detection_on": False, "track_person": False, "track_motion": False, "patrol": False, "net_mode": "client"}
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    wrap = os.path.join(tb, "wrap.py"); open(wrap, "w").write(WRAP)
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    logf = open(os.path.join(tb, "log.txt"), "w")
    env = dict(os.environ, MW_FAKE_NET=os.path.join(tb, "net.json"), PATH=b + os.pathsep + os.environ.get("PATH", ""), MOTIONWATCH_HOME=cfg)
    p = subprocess.Popen([sys.executable, wrap, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg,
                          "--web-password", PW], stdout=logf, stderr=subprocess.STDOUT, cwd=tb, env=env)
    base = "http://127.0.0.1:%d" % port
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    auth = {"Authorization": "Basic " + base64.b64encode(("admin:" + PW).encode()).decode()}

    def api(data=None):
        r = urllib.request.Request(base + "/api/wifi", data=json.dumps(data).encode() if data is not None else None,
                                   headers=dict(auth, **{"Content-Type": "application/json"}))
        try:
            with op.open(r, timeout=60) as x:
                return json.loads(x.read())
        except urllib.error.HTTPError as e:
            return json.loads(e.read())
    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tb, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        r = api({"action": "prefer", "on": True, "ssid": "Elektros iPhone"})
        ok(r.get("ok") and r["hsp"]["ssid"] == "Elektros iPhone", "API: Hotspot gewählt und eingeschaltet (%s)" % r.get("hsp"))
        for _i in range(30):
            h = api()["hsp"]
            if h["state"].startswith("waiting"):
                break
            time.sleep(1)
        ok(h["state"] == "waiting, because {n} device is connected" and h["n"] == 1, "MoveEye wartet (1 Gerät im eigenen WLAN): %s" % h)
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
                                 color_scheme="dark", http_credentials={"username": "admin", "password": PW}, locale="de-CH")
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(base + "/settings?open=wifi", wait_until="domcontentloaded")
            pg.wait_for_timeout(2500)

            def weg():
                pg.evaluate("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; ['g2-ov', 'g2-spot', 'g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")
            weg()
            pg.evaluate("() => { const c = document.getElementById('wf-card'); if (c) { c.classList.remove('l-hide'); c.hidden = false; c.style.display = ''; c.open = true; c.dispatchEvent(new Event('toggle')); } }")
            pg.wait_for_selector("#hsp-st", timeout=30000)
            pg.wait_for_function("() => (document.getElementById('hsp-st') || {}).textContent.includes('wartet')", timeout=30000)
            txt = pg.locator("#hsp-st").inner_text()
            ok(txt == "📶 Hotspot «Elektros iPhone»: wartet, weil 1 Gerät verbunden ist", "Karte: «%s»" % txt)
            mark = pg.locator("#wf-saved .hsp-b.on").count()
            tag = pg.locator("#wf-saved .hsp-tag").inner_text() if pg.locator("#wf-saved .hsp-tag").count() else ""
            ok(mark == 1 and "Mein Handy-Hotspot" in tag, "Liste: 📶 markiert (%d, «%s»)" % (mark, tag))
            weg()
            card = pg.locator("#wf-card")
            card.scroll_into_view_if_needed(); pg.wait_for_timeout(500)
            card.screenshot(path=os.path.join(bilder, "hotspot_karte_wartet.png"))
            # nobody connected any more -> it switches; the card says «verbunden»
            s = json.load(open(os.path.join(tb, "net.json"))); s["clients"] = 0; s["scan_in_ap"] = True
            json.dump(s, open(os.path.join(tb, "net.json"), "w"))
            # («wartet, weil 1 Gerät verbunden ist» also contains «verbunden»: wait for the end of the text)
            try:
                pg.wait_for_function("() => /: verbunden$/.test(((document.getElementById('hsp-st') || {}).textContent || '').trim())", timeout=70000)
            except Exception:
                pass
            weg(); card.screenshot(path=os.path.join(bilder, "hotspot_karte_verbunden.png"))
            txt = pg.locator("#hsp-st").inner_text()
            h = api()["hsp"]
            ok(txt == "📶 Hotspot «Elektros iPhone»: verbunden" and h["state"] == "connected", "Karte nach dem Wechsel: «%s» (%s)" % (txt, h["state"]))
            # switch off from the page
            pg.locator("#hsp-on").click(force=True)
            pg.wait_for_function("() => !document.getElementById('hsp-st')", timeout=20000)
            ok(api()["hsp"]["on"] is False, "Schalter auf der Seite: aus")
            w = pg.evaluate("() => document.documentElement.scrollWidth")
            ok(w <= 390, "keine waagrechte Bildlaufleiste bei 390 px (%d)" % w)
            for L, word in (("fr", "Préférer le point d'accès"), ("it", "Preferire l'hotspot"), ("rm", "Preferir il hotspot"), ("en", "Prefer my phone hotspot")):
                pg.evaluate("async l => { try { localStorage.setItem('mw-lang', l); } catch (e) {} await fetch('/api/ui', {method: 'POST', "
                            "headers: {'Content-Type': 'application/json'}, body: JSON.stringify({set: {'mw-lang': l}})}); }", L)
                pg.goto(base + "/settings?open=wifi", wait_until="domcontentloaded")
                pg.wait_for_timeout(1500)
                pg.evaluate("() => { const c = document.getElementById('wf-card'); if (c) { c.open = true; c.dispatchEvent(new Event('toggle')); } }")
                try:
                    pg.wait_for_function("w => (document.getElementById('hsp-box') || {}).textContent.includes(w)", arg=word, timeout=30000)
                    ok(True, "%s: «%s»" % (L, word))
                except Exception:
                    ok(False, "%s: «%s» fehlt (%s)" % (L, word, pg.evaluate("() => (document.getElementById('hsp-box')||{}).textContent")[:160]))
            ok(not errs, "keine JS-Fehler %s" % errs[:3])
            br.close()
    finally:
        p.terminate()
        try:
            p.wait(10)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default=os.path.join(tempfile.gettempdir(), "hotspot_bilder"))
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                                               key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1])
    print("Handy-Hotspot-Test · " + os.path.basename(datei), flush=True)
    tmp = tempfile.mkdtemp(prefix="mw_hsp_")
    try:
        teil_a(datei, tmp)
        if a.browser:
            teil_b(datei, tmp, a.bilder)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("Handy-Hotspot-Test: " + ("OK" if not FEHLER else "%d FEHLER" % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == "__main__":
    sys.exit(main())
