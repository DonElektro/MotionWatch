"""Erkennungstest 2 - neue Sonderfälle (nur Steuer-API des Simulators und Web-API von MoveEye, nichts geändert).
Aufruf: python3 extra.py blend,linse,kopf
  blend : Ferienpark · Stellplatz, Nacht: Auto fährt mit Scheinwerfern direkt auf die Kamera zu (fahrzeuge toward),
          Leerlauf und Person geht; Tag: Sonnen-Blendung in der Linse (cond_glare), Leerlauf und Person geht.
  linse : Camping-Platz, Tag, Wind 55 km/h: Spinnennetz vor der Linse (cond_web), Vogel fliegt vor der Linse (bird_now).
          «Ast direkt vor der Linse» gibt es im Simulator nur in den KI-Trainingsbildern (vielfalt.gd), nicht live.
  kopf  : Camping-Platz, Tag, Kopf-Verfolgung AN (track_person, kopf_on): Schwenk-Winkel 150 s im leeren Bild, dann Person geht.
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import driver as D
from lib import *


def mw_set(key, value):
    try:
        return http_json(MW + "/api/set", {"key": key, "value": value}, timeout=8)
    except Exception as e:
        return {"err": str(e)}


def case(place, ck, ev, want, secs, act, info, done, wind=12, before=None):
    key = "%s|%s|%s" % (place, ck, ev)
    if key in done:
        return
    if load() >= 5.0:
        lw = time.time()
        l = wait_load(5.0, 420)
        log("  Last-Pause %.0f s, Last jetzt %.1f" % (time.time() - lw, l))
    D.clear()
    time.sleep(2)
    if before:
        before()
    ctl(action="set", id="wind", value=wind)
    base = D.baseline(3.0)
    r = act() if act else {"ok": True}
    t_spawn = time.time()
    rec = D.observe(secs, "%s_%s_%s" % (place, ck, ev), want, t_spawn, base)
    rec.update({"key": key, "place": place, "world": D.PLAN[place][0], "cond": ck, "cond_name": NAMES.get(ck, ck), "event": ev,
                "info": info, "spawn_ok": bool((r or {}).get("ok", False)), "secs": secs, "t": time.strftime("%H:%M:%S"), "load": load()})
    ctl(action="set", id="wind", value=12)
    save(rec)
    log(key, "->", rec.get("detected", rec.get("false_person_eps")), rec.get("as", ""), rec.get("t_detect", ""), "fps", rec["fps"],
        "pushes", len(rec["pushes"]))


NAMES = {"nacht_blend": "Nacht, Scheinwerfer direkt in die Kamera", "tag_blend": "Tag, Sonne blendet in die Linse",
         "linse": "Tag, Wind 55 km/h, etwas direkt vor der Linse", "kopf": "Tag, klar, Kopf-Verfolgung AN"}
save = D.save


def toward():
    return ctl(action="fahrzeuge", do="toward")


def walk(dist):
    return lambda: ctl(action="menschen", do="probe", gait="walk", dist=dist)


def blend(done):
    D.goto_place("stellplatz")
    D.set_cond("nacht")
    time.sleep(15)

    def leer_toward():
        r = toward()
        import threading
        threading.Timer(22.0, toward).start()
        return r
    case("stellplatz", "nacht_blend", "leer", "none", 45.0, leer_toward, "2 Autos mit Scheinwerfern direkt auf die Kamera zu, niemand da", done)

    def walk_toward():
        toward()
        time.sleep(3)
        return ctl(action="menschen", do="probe", gait="walk", dist=7.0)
    case("stellplatz", "nacht_blend", "gehen", "person", 22.0, walk_toward, "Auto blendet, dabei geht eine Person quer, 7 m", done)
    D.set_cond("tag")
    ctl(action="set", id="cond_glare", value=True)
    time.sleep(15)
    case("stellplatz", "tag_blend", "leer", "none", 45.0, None, "Sonne blendet (cond_glare), Wind 55 km/h, niemand da", done, wind=55,
         before=lambda: ctl(action="set", id="cond_glare", value=True))
    case("stellplatz", "tag_blend", "gehen", "person", 18.0, walk(10.0), "Sonne blendet, Person geht quer, 10 m", done,
         before=lambda: ctl(action="set", id="cond_glare", value=True))
    ctl(action="set", id="cond_glare", value=False)


def linse(done):
    D.goto_place("camping")
    D.set_cond("tag")
    time.sleep(15)
    case("camping", "linse", "netz", "none", 45.0, None, "Spinnennetz vor der Linse (cond_web), Wind 55 km/h, niemand da", done, wind=55,
         before=lambda: ctl(action="set", id="cond_web", value=True))
    case("camping", "linse", "netz_gehen", "person", 18.0, walk(10.0), "Spinnennetz vor der Linse, Person geht quer, 10 m", done,
         before=lambda: ctl(action="set", id="cond_web", value=True))
    ctl(action="set", id="cond_web", value=False)

    def birds():
        import threading
        r = ctl(action="press", id="bird_now")
        for dt in (12.0, 24.0, 36.0):
            threading.Timer(dt, lambda: ctl(action="press", id="bird_now")).start()
        return r
    case("camping", "linse", "vogel", "none", 45.0, birds, "Vogel fliegt 4× direkt vor der Linse durch, niemand da", done)


def kopf(done):
    key = "camping|kopf|leer"
    D.goto_place("camping")
    D.set_cond("tag")
    a = mw_set("track_person", True)
    b = mw_set("kopf_on", True)
    log("Kopf-Verfolgung an:", a, b)
    time.sleep(5)
    if key not in done:
        wait_load(5.0, 420)
        pans = []
        base = D.baseline(3.0)
        t0 = time.time()
        rec = {}
        import threading
        res = {}
        th = threading.Thread(target=lambda: res.update(D.observe(150.0, "camping_kopf_leer", "none", t0, base)))
        th.start()
        while th.is_alive():
            pans.append([round(time.time() - t0), round(D.pan_deg(), 1)])
            time.sleep(3)
        rec = dict(res)
        st = mw_state()
        rec.update({"key": key, "place": "camping", "world": "camping", "cond": "kopf", "cond_name": NAMES["kopf"], "event": "leer",
                    "info": "Kopf-Verfolgung AN, niemand da, 150 s", "pan": pans, "kopf": st.get("kopf"), "track_what": st.get("track_what"),
                    "secs": 150.0, "t": time.strftime("%H:%M:%S"), "load": load(), "set": [a, b]})
        frame(SHOTS + "/camping_kopf_leer_ende.jpg")
        save(rec)
        log(key, "-> Schwenk", pans[0][1] if pans else "?", "->", pans[-1][1] if pans else "?", "min", min(p[1] for p in pans) if pans else "?",
            "max", max(p[1] for p in pans) if pans else "?", "Personen", rec.get("false_person_eps"), "Pushes", rec.get("false_pushes"))
    key = "camping|kopf|gehen"
    if key not in done:
        pans = []
        D.clear()
        time.sleep(2)
        base = D.baseline(3.0)
        r = ctl(action="menschen", do="probe", gait="walk", dist=10.0)
        t0 = time.time()
        import threading
        res = {}
        th = threading.Thread(target=lambda: res.update(D.observe(25.0, "camping_kopf_gehen", "person", t0, base)))
        th.start()
        while th.is_alive():
            pans.append([round(time.time() - t0, 1), round(D.pan_deg(), 1)])
            time.sleep(1.5)
        rec = dict(res)
        rec.update({"key": key, "place": "camping", "world": "camping", "cond": "kopf", "cond_name": NAMES["kopf"], "event": "gehen",
                    "info": "Kopf-Verfolgung AN, Person geht quer, 10 m", "pan": pans, "spawn_ok": bool(r.get("ok")), "secs": 25.0,
                    "t": time.strftime("%H:%M:%S"), "load": load()})
        save(rec)
        log(key, "->", rec.get("detected"), rec.get("t_detect"), "Schwenk", pans[0][1] if pans else "?", "->", pans[-1][1] if pans else "?")
    log("Kopf-Verfolgung aus:", mw_set("track_person", False), mw_set("kopf_on", False))


if __name__ == "__main__":
    done = D.done_keys()
    for w in sys.argv[1].split(","):
        {"blend": blend, "linse": linse, "kopf": kopf}[w](done)
        os.system("cd /tmp/claude-0/erkt2/tools && python3 sync.py >> ../out/sync.log 2>&1")
    log("extra fertig")
