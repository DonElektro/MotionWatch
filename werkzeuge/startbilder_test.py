#!/usr/bin/env python3
"""Test «🏞 Startseite: Bilder» (MoveEye Teil 639zzzzf) – eigene Fotos für die Startseite der Homepage, gegen einen falschen
Webspace auf localhost (werkzeuge/homepage_test.py «Webspace») – nie gegen den echten. Nur erzeugte Testbilder, nie Fotos
des Besitzers.

Geprüft (MoveEye im selben Python, Flask-Test-Client):
  * Rechte: Benutzer «Familie» → 403 (Seite, Vorschau, Zustand, Hochladen, Bild, Fokus, Variante), ohne Anmeldung 401, Admin 200.
  * Hochladen JPEG mit EXIF (Kamera, GPS) → WebP ohne EXIF / GPS / XMP, Grösse je Platz (Titel 1600 px, Panorama ≤ 2600 px und
    ≤ 400 KB auch bei «Rauschen», Leiste 360 px hoch), kleine Kopie; kaputt / zu klein / zu gross / unbekannter Platz → 400.
  * Fokuspunkt, Texte (ohne Markup, eigener Text in allen Sprachen), Variante A / B (Seite /startbilder und Karte «Homepage»).
  * Webspace: «Startseite» an + B → index.html mit Startbilder/… (Knöpfe direkt unter dem Titelbild, keine fremden Adressen),
    die Bilder Byte für Byte, Prüfung ohne Probleme (image/webp); Wechsel auf A → B-Bilder gelöscht, A-Bilder hochgeladen,
    Funk/ unberührt; Bild ersetzt → neuer Name, alter gelöscht; alle Bilder weg → schlichte Startseite; «Startseite» aus →
    weder hochgeladen noch gelöscht.
  * --browser: echte MoveEye (--headless --demo) und Chromium bei 390 px: /startbilder (keine waagrechte Bildlaufleiste, keine
    JS-Fehler, Knopf in der Karte «Homepage»), Vorschau A und B; die erste Ansicht (Titel, Satz, 5 Kacheln) passt ohne Scrollen
    bei 1366 × 768, 1536 × 864, 1280 × 720, 1280 × 650, 820 × 1180 und 390 × 844 (22.11.2026); Kapitel-Knöpfe nur mit Sim ≥ HP_GV_KAPITEL; --bilder ORDNER: Bildschirmfotos; --fotos ORDNER: dort die
    Bilder nach Platz-Namen (titel.jpg, pano.jpg, …) hochladen statt erzeugter (z. B. die Fotos des Besitzers, nur lokal).

  python3 werkzeuge/startbilder_test.py [--datei X.py] [--browser] [--bilder ORDNER] [--fotos ORDNER]
"""
import argparse
import base64
import glob
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
sys.path.insert(0, HIER)
import homepage_test as HT  # noqa: E402

FEHLER = []
N = {"ok": 0}
ADMIN_PW = "Admin-" + base64.b16encode(os.urandom(6)).decode().lower()
KEY = "Test-" + base64.b16encode(os.urandom(10)).decode().lower()


def ok(cond, what):
    if cond:
        N["ok"] += 1
    else:
        FEHLER.append(what)
    print(("  ok     " if cond else "  FEHLER ") + what, flush=True)


def foto(w, h, color=(200, 30, 30), noise=False, fmt="JPEG"):
    """a generated photo with EXIF (camera name and GPS) - like a phone photo; left half colored, right half blue"""
    from PIL import Image
    im = Image.effect_noise((w, h), 70).convert("RGB") if noise else Image.new("RGB", (w, h), color)
    if not noise:
        im.paste((30, 40, 200), (w // 2, 0, w, h))
    ex = Image.Exif(); ex[0x010F] = "TestCamFirma"; ex[0x0110] = "TestCamModell"
    ex[0x8825] = {1: "N", 2: (47.0, 3.0, 12.5), 3: "E", 4: (8.0, 18.0, 30.0)}
    b = io.BytesIO(); im.save(b, fmt, quality=90, exif=ex.tobytes())
    return b.getvalue()


def neueste():
    return sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")), key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datei", default="")
    ap.add_argument("--browser", action="store_true")
    ap.add_argument("--bilder", default="")
    ap.add_argument("--fotos", default="", help="Ordner mit Bildern nach Platz-Namen (titel.jpg …) für die Bildschirmfotos")
    a = ap.parse_args()
    datei = os.path.abspath(a.datei or neueste())
    try:
        lauf(datei)
        if a.browser:
            browser(datei, a.bilder, a.fotos)
    finally:
        for h in HT.HOMES:
            shutil.rmtree(h, ignore_errors=True)
    print("\nStartbilder-Test: %d ok, %d Fehler%s" % (N["ok"], len(FEHLER), ("\n  " + "\n  ".join(FEHLER)) if FEHLER else ""))
    return 1 if FEHLER else 0


def lauf(datei):
    from PIL import Image
    ns = HT.laden(datei)
    CFG, HP = ns["CFG"], ns["HP"]
    ns["HP_TEST_HTTP"] = True
    ns["HP_RETRY"][:] = [0.05, 0.1]
    ns["GAMESRV"]["port"] = 1
    ns["sim_manifest_refresh"] = lambda *x, **k: None
    CFG.update(https_extra=False, lang="de", setup_done=True, update_url="")
    assert ns["web_pw_set"](ADMIN_PW)[0]
    okk, err = ns["users_action"]({"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
    assert okk, err
    wst = ns["WebStream"](None)
    wst._serve = lambda app, ctx: None
    wst.start()
    c = wst.app.test_client(use_cookies=False)
    H = {"admin": HT.basic("admin", ADMIN_PW), "Anna": HT.basic("Anna", "anna-pass-1"), "none": {}}
    HT.TYPES["webp"] = "image/webp"
    W = HT.Webspace(KEY)
    base = "http://127.0.0.1:%d" % W.port
    sbd = os.path.join(ns["DATA_DIR"], "startseite")

    def api(d=None, who="admin", q=""):
        if d is None:
            r = c.get("/api/startbilder?lang=de" + q, headers=H[who])
        else:
            r = c.post("/api/startbilder?lang=de" + q, json=d, headers=H[who])
        return r.status_code, r.get_json(silent=True) or {}

    def put(slot, raw, who="admin", fx=50, fy=50):
        r = c.post("/api/startbilder?lang=de&action=set&slot=%s&fx=%s&fy=%s" % (slot, fx, fy), data=raw, headers=dict(H[who], **{"Content-Type": "application/octet-stream"}))
        return r.status_code, r.get_json(silent=True) or {}

    def hp(d=None):
        r = c.post("/api/homepage?lang=de", json=dict(d, lang="de"), headers=H["admin"]) if d else c.get("/api/homepage?lang=de", headers=H["admin"])
        HT.warte(HP)
        return r.status_code, (c.get("/api/homepage?lang=de", headers=H["admin"]).get_json(silent=True) or {})

    def slot(j, k):
        return next((s for s in j.get("slots", []) if s["id"] == k), {})

    print("1) ab Werk, Rechte", flush=True)
    code, j = api()
    ok(code == 200 and j.get("variant") == "B" and CFG["hp_start_variant"] == "B" and ns["DEFAULTS"]["hp_start_variant"] == "B", "ab Werk Variante B (%d)" % code)
    ok([s["id"] for s in j.get("slots", [])] == list(ns["SB_SLOTS"]) and not any(s["custom"] for s in j["slots"]), "13 Plätze, alle leer")
    ok(slot(j, "titel").get("use") == "AB" and slot(j, "pano").get("use") == "B" and slot(j, "lager").get("use") == "A", "Plätze je Variante")
    ok([f["def"] for f in slot(j, "titel").get("fields", [])][:3] == ["Dein Wächter fürs Lager draussen.", "Unterwegs", "Du gehst los – MoveEye kommt mit."],
       "Standardtexte Titel: %s" % [f["def"] for f in slot(j, "titel").get("fields", [])][:3])
    raw = foto(2400, 1800)
    g = [c.get("/startbilder", headers=H["Anna"]).status_code, c.get("/startbilder/vorschau?v=A", headers=H["Anna"]).status_code, api(who="Anna")[0],
         put("titel", raw, "Anna")[0], c.get("/api/startbilder/bild/titel", headers=H["Anna"]).status_code,
         api({"action": "focus", "slot": "titel", "fx": 1, "fy": 1}, "Anna")[0], api({"action": "variant", "v": "A"}, "Anna")[0],
         c.post("/api/homepage", json={"action": "start_variant", "v": "A"}, headers=H["Anna"]).status_code]
    ok(g == [403] * 8 and CFG["hp_start_variant"] == "B" and not os.path.isdir(sbd), "Benutzer «Familie»: alles 403 %s" % g)
    c.post("/api/set", json={"key": "hp_start_variant", "value": "A"}, headers=H["Anna"])
    ok(CFG["hp_start_variant"] == "B", "Familie: /api/set geht nicht")
    ok(api(who="none")[0] == 401 and c.get("/startbilder").status_code == 401, "ohne Anmeldung: 401")
    pg = c.get("/startbilder", headers=H["admin"]).get_data(as_text=True)
    ok("sb-list" in pg and "Startseite: Bilder" in pg and "Keine Personen, Kennzeichen, Hausnummern oder Ortsschilder." in pg, "Seite /startbilder (Deutsch)")
    hpg = c.get("/homepage", headers=H["admin"]).get_data(as_text=True)
    ok('id="hp-sbild" href="/startbilder"' in hpg and 'id="hp-sb-var"' in hpg and hpg.index('id="hp-start"') < hpg.index('id="hp-sbild"'),
       "Karte «Homepage»: Variante und Knopf unter «Startseite»")
    r = c.get("/startbilder/vorschau?v=B", headers=H["admin"])
    pv = r.get_data(as_text=True)                                   # (MoveEye adds its «✕ Zurück» to every page it serves)
    ok(r.status_code == 200 and pv.startswith(ns["hp_index_html"]().split("</body>")[0]) and "/api/startbilder/bild/" not in pv,
       "Vorschau ohne Bilder = schlichte Startseite (%d)" % r.status_code)

    print("2) hochladen, EXIF weg, Grössen", flush=True)
    ok(b"TestCamFirma" in raw, "Testfoto mit EXIF und GPS (%d KB)" % (len(raw) // 1024))
    code, j = put("titel", raw, fx=82, fy=70)
    s = slot(j, "titel")
    ok(code == 200 and s.get("custom") and (s["fx"], s["fy"]) == (82.0, 70.0) and (s["w"], s["h"]) == (1600, 1200), "Titelbild: 1600 × 1200, Fokus 82 / 70 (%d)" % code)
    files = sorted(os.listdir(sbd))
    ok(files == ["bilder.json", "titel-k.webp", "titel.webp"], "gespeichert im Daten-Ordner: %s" % files)
    for n in ("titel.webp", "titel-k.webp"):
        b = open(os.path.join(sbd, n), "rb").read(); im = Image.open(io.BytesIO(b))
        ok(b[:4] == b"RIFF" and b"TestCam" not in b and b"Exif" not in b and b"EXIF" not in b and b"XMP" not in b and not im.getexif(), "%s ohne EXIF / GPS / XMP" % n)
    ok(os.path.getsize(os.path.join(sbd, "titel.webp")) <= 250000 and Image.open(os.path.join(sbd, "titel-k.webp")).size[0] == 900, "Titel ≤ 250 KB, klein 900 px")
    r = c.get("/api/startbilder/bild/titel?k=1", headers=H["admin"])
    ok(r.status_code == 200 and r.mimetype == "image/webp", "Vorschau-Bild (Admin)")
    code, j = put("pano", foto(5000, 1300, noise=True, fmt="PNG"))
    pz = os.path.getsize(os.path.join(sbd, "pano.webp"))
    ok(code == 200 and pz <= 400000 and slot(j, "pano")["w"] <= 2600, "Panorama aus Rauschen: ≤ 400 KB (%d KB, %d px)" % (pz // 1024, slot(j, "pano").get("w", 0)))
    for k in ("leiste1", "leiste2"):
        put(k, foto(1500, 1000))
    code, j = api()
    ok(slot(j, "leiste1").get("h") == 360 and not os.path.exists(os.path.join(sbd, "leiste1-k.webp")), "Leiste: 360 px hoch, keine kleine Kopie")
    code, j = put("lager", b"kein Bild")
    ok(code == 400 and "kann nicht gelesen werden" in j.get("error", ""), "kaputte Datei: 400 «%s»" % j.get("error"))
    code, j = put("lager", foto(500, 400))
    ok(code == 400 and j.get("error") == "Das Bild ist zu klein (mindestens 600 px breit).", "zu klein: «%s»" % j.get("error"))
    code, j = put("hacker", raw)
    ok(code == 400 and not os.path.exists(os.path.join(sbd, "hacker.webp")), "unbekannter Platz: 400")
    big = raw + b"\0" * (26 << 20)
    code, j = put("lager", big)
    ok(code == 400 and "zu gross" in j.get("error", ""), "über 25 MB: 400")

    print("3) Fokus, Texte, Variante", flush=True)
    code, j = api({"action": "focus", "slot": "titel", "fx": 120, "fy": -5})
    ok(code == 200 and (slot(j, "titel")["fx"], slot(j, "titel")["fy"]) == (100.0, 0.0), "Fokus begrenzt auf 0–100")
    api({"action": "focus", "slot": "titel", "fx": 82, "fy": 70})
    code, j = api({"action": "texts", "slot": "titel", "texts": {"line": "Mein <script>Lager</script>", "say": "", "boese": "x"}})
    tf = {f["f"]: f["value"] for f in slot(j, "titel")["fields"]}
    ok(code == 200 and tf["line"] == "Mein scriptLager/script" and tf["say"] == "" and "boese" not in tf, "Texte ohne Markup: %s" % tf)
    api({"action": "texts", "slot": "titel", "texts": {"line": "Mein Lager, mein Wächter."}})
    code, j = api({"action": "variant", "v": "X"})
    ok(code == 400 and CFG["hp_start_variant"] == "B", "unbekannte Variante: 400")

    print("4) Webspace: Startseite B mit eigenen Bildern", flush=True)
    hp({"action": "base", "base": base}); hp({"action": "key", "key": KEY})
    hp({"action": "funk_on", "on": True}); hp({"action": "sim_on", "on": False})
    code, j = hp({"action": "start_on", "on": True})
    code, j = hp({"action": "publish"})
    idx = W.files.get("index.html", b"").decode("utf-8")
    sb = sorted(p for p in W.files if p.startswith("Startbilder/"))
    ok(code == 200 and not j.get("err") and len(sb) == 6, "B: index.html + 6 Bilder (Titel, Panorama je gross + klein, Leiste 2) %s" % sb)
    ok(all(re.fullmatch(r"Startbilder/[a-z0-9-]+-[0-9a-f]{10}\.webp", p) for p in sb), "Namen: Platz + Prüfsumme, genau ein Punkt")
    ok(all(p in idx for p in sb), "index.html nennt jedes hochgeladene Bild")
    ok(idx.index('href="Funk/"') < idx.index('href="Sim/"') < idx.index('id="sc"') < idx.index('class="strip"'), "B: Titelbild, Knöpfe, Panorama, Leiste")
    ok("📡 Handy-Funkgerät" in idx and "Mein Lager, mein Wächter." in idx and "object-position:82.0% 70.0%" in idx, "📡, eigene Titelzeile, Fokuspunkt")
    def links_ok(h_):
        pos_ = [h_.find('href="%s"' % x) for x in ("demo/", "Sim/?grossvater=1", "Funk/", "Sim/", "Info/")]
        return min(pos_) >= 0 and pos_ == sorted(pos_) and "📷 MoveEye" in h_ and "🗺️ Die Karte des Grossvaters" in h_ and "ℹ️ Besucherseite" in h_ \
            and '"btn.i": "ℹ️ Visitor page"' in h_ and '"gv.all": "▶ Jeu complet"' in h_ and h_.count('class="tile t-') == 5 \
            and "La carte du grand-père" in h_ and "La charta dal tat" in h_ and 'class="mweye"' in h_ and "mws-b" in h_ and 'class="mws-p"' in h_
    ok(links_ok(idx), "4.19.1 B: alle Links (MoveEye · Karte des Grossvaters · Funkgerät · Simulator · Besucherseite, 5 Sprachen) und das bewegte Auge")
    ok("kapitel=" not in idx and 'data-t="gv.all"' in idx, "ohne veröffentlichten Browser-Simulator: nur «▶ Ganzes Spiel»")
    m_ = ns["sb_meta"]()
    for ver, want in (("3.77.0", []), ("3.78.0", [1, 2, 3, 4])):
        hk = ns["sb_page_html"]("A", lambda s_, k_: "x.webp", m_, ns["hp_gv_kapitel"](ver))
        got = [int(x) for x in re.findall(r'href="Sim/\?grossvater=1&amp;kapitel=(\d+)"', hk)]
        ok(got == want and (not want or hk.count('class="chip"') == len(want)), "A mit Sim %s: Kapitel-Knöpfe %s" % (ver, got))
    sv = dict(ns["SIM3D_WEB"])
    ns["SIM3D_WEB"].update(version="3.78.0", size=1, sha256="0" * 64)
    ok(ns["hp_gv_kapitel"]() == [1, 2, 3, 4] and "kapitel=4" in ns["hp_fixed_items"]()[0]["get"]().read().decode(),
       "Kapitel nach dem veröffentlichten Browser-Simulator (SIM3D_WEB 3.78.0): 1 · 2 · 3 · 4 auf der Startseite")
    ns["SIM3D_WEB"].clear(); ns["SIM3D_WEB"].update(sv)
    ok(not re.search(r'(?:src|href|srcset)="(?:https?:)?//', idx) and "http://" not in idx and "https://" not in idx, "keine fremden Adressen in der Seite")
    def lokal(p):
        m = re.fullmatch(r"Startbilder/([a-z0-9-]+?)(-k)?-[0-9a-f]{10}\.webp", p)
        return open(os.path.join(sbd, m.group(1).replace("-", "_") + (m.group(2) or "") + ".webp"), "rb").read()
    ok(all(W.files[p] == lokal(p) for p in sb), "Bilder Byte für Byte wie auf MoveEye")
    ok(all(W.files.get("Funk/" + n) for n in ("index.html", "sw.js")), "Funk/ hochgeladen wie bisher")
    code, j = hp({"action": "check"})
    rows = (j.get("check") or {}).get("rows") or []
    srow = [r for r in rows if r["path"].startswith("Startbilder/")]
    ok(len(srow) == 6 and not any(r["probs"] for r in srow) and all(r["type"] == "image/webp" for r in srow),
       "Prüfung: 6 Bilder ohne Problem (image/webp) %s" % [(r["path"], r["type"], r["probs"]) for r in srow][:3])
    ok(j.get("start_variant") == "B" and j.get("start_pics") == 4, "Status: Variante B, 4 eigene Bilder")

    print("5) Wechsel auf A, ersetzen, entfernen", flush=True)
    for k, w, h in (("grat", 2600, 650), ("grat_hoch", 1200, 1600), ("lager", 1600, 1200), ("abend", 1600, 1200), ("nacht", 1600, 1200)):
        put(k, foto(w, h))
    n0 = len(W.log)
    code, j = hp({"action": "start_variant", "v": "A"})
    ok(code == 200 and CFG["hp_start_variant"] == "A", "Variante A über die Karte «Homepage»")
    code, j = hp({"action": "publish"})
    sa = sorted(p for p in W.files if p.startswith("Startbilder/"))
    dels = [x[2] for x in W.log[n0:] if x[0] == "DELETE"]
    ok(len(sa) == 12 and not any("pano" in p or "leiste" in p for p in sa), "A: Titel + 5 Kapitelbilder × 2 = 12 (%d)" % len(sa))
    ok(sorted(dels) == sorted(p for p in sb if "pano" in p or "leiste" in p), "B-Bilder gelöscht, sonst nichts: %s" % dels)
    idx = W.files["index.html"].decode()
    ok(idx.index('href="Funk/"') < idx.index('id="story"') and idx.count('class="band') == 4 and 'media="(orientation:portrait)"' in idx,
       "A: Knöpfe unter dem Titelbild, 4 Kapitel, Hochformat fürs Handy")
    ok(links_ok(idx), "4.19.1 A «Bildgeschichte»: alle Links (MoveEye · Karte des Grossvaters · Funkgerät · Simulator · Besucherseite, 5 Sprachen) und das bewegte Auge")
    ok("prefers-reduced-motion" in idx and all(x in idx for x in ("Über den Grat", "Lagerplatz", "Abend", "Nacht", "Du schläfst. MoveEye wacht.")), "A: Kapitel und Bewegung nur auf Wunsch")
    ok('"titel.line"' not in idx.split("var T=", 1)[1].split(",l=", 1)[0] and '"grat.say"' in idx, "eigener Text in allen Sprachen, andere übersetzt")
    old = [p for p in sa if p.startswith("Startbilder/lager-") and "-k-" not in p][0]
    put("lager", foto(1600, 1200, color=(10, 200, 10)))
    n0 = len(W.log)
    hp({"action": "publish"})
    new = [p for p in W.files if p.startswith("Startbilder/lager-") and "-k-" not in p]
    ok(old not in W.files and len(new) == 1 and new[0] != old and old in [x[2] for x in W.log[n0:] if x[0] == "DELETE"], "Bild ersetzt: neuer Name, alter gelöscht")
    n0 = len(W.uploads())
    hp({"action": "start_on", "on": False}); hp({"action": "publish"})
    for k in ns["SB_SLOTS"]:
        api({"action": "reset", "slot": k})
    hp({"action": "publish"})
    ok(len(W.uploads()) == n0 and any(p.startswith("Startbilder/") for p in W.files), "Startseite aus: nichts hochgeladen, nichts gelöscht")
    hp({"action": "start_on", "on": True})
    code, j = hp({"action": "publish"})
    ok(not any(p.startswith("Startbilder/") for p in W.files) and W.files.get("index.html") == ns["hp_index_html"]().encode(), "alle Bilder entfernt: schlichte Startseite, Startbilder/ gelöscht")
    ok(all(W.files.get("Funk/" + n) for n in ("index.html", "sw.js")), "Funk/ unberührt")
    ok(not [f for f in os.listdir(sbd) if f.endswith(".webp")], "Daten-Ordner ohne Bilder")
    logp = ns["LOG_FILE"]
    log = open(logp, errors="replace").read() if os.path.isfile(logp) else ""
    ok("TestCam" not in log and "47.0" not in log and KEY not in log, "nichts aus dem EXIF und kein Schlüssel im Protokoll")
    t_de = c.get("/i18n/fr.js", headers=H["admin"]).get_data(as_text=True)
    ok("Page d’accueil : images" in t_de, "Französisch auf der Seite (/i18n/fr.js)")


# the shared symbol (part 144) at the title: animation names, colour of the person, its width, two positions 0.6 s apart
SYM_JS = ("async () => { const s = document.querySelector('h1 .mweye svg'); if (!s) return null; const q = c => s.querySelector(c), "
          "an = ['.mws-w', '.mws-f', '.mws-e', '.mws-l1', '.mws-a1', '.mws-lid'].map(c => q(c) ? getComputedStyle(q(c)).animationName : 'fehlt'), "
          "x = () => q('.mws-p').getBoundingClientRect().left, x0 = x(); await new Promise(r => setTimeout(r, 600)); "
          "return [an, getComputedStyle(q('.mws-p')).fill, q('.mws-p').getBoundingClientRect().width, Math.round(x0 * 10), Math.round(x() * 10)]; }")


def browser(datei, bilder, fotos):
    """the real MoveEye (--headless --demo) and Chromium at 390 px"""
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="mw_sbtest_")
    cfg = os.path.join(tmp, "mw"); os.makedirs(cfg)
    st = {"source": "demo", "sim_on": False, "sim_url": "http://127.0.0.1:9", "sim_auto": False, "sim_autostart": False, "sim_autostart_v2": False,
          "sim_autoupd": False, "update_url": "", "lang": "de", "desktop_notice": False, "setup_done": True, "https_extra": False, "news_popup": False,
          "theme": "dark", "detection_on": False, "hp_start_on": True}
    json.dump({"cfg": st}, open(os.path.join(cfg, "motionwatch_settings.json"), "w"))
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    env = dict(os.environ, MOTIONWATCH_HOME=os.path.join(tmp, "home"), NO_PROXY="127.0.0.1,localhost", no_proxy="127.0.0.1,localhost")
    for k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        env[k] = "http://127.0.0.1:9"
    logf = open(os.path.join(tmp, "log.txt"), "w")
    p = subprocess.Popen([sys.executable, datei, "--headless", "--demo", "--port", str(port), "--bind", "127.0.0.1", "--config", cfg, "--web-password", ADMIN_PW],
                         stdout=logf, stderr=subprocess.STDOUT, cwd=tmp, env=env)
    base = "http://127.0.0.1:%d" % port
    op = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    auth = {"Authorization": "Basic " + base64.b64encode(("admin:" + ADMIN_PW).encode()).decode()}

    def post(q, data, ctype):
        r = urllib.request.Request(base + "/api/startbilder?lang=de&" + q, data=data, headers=dict(auth, **{"Content-Type": ctype}), method="POST")
        try:
            with op.open(r, timeout=120) as x:
                return x.status
        except urllib.error.HTTPError as e:
            return e.code
    try:
        for _i in range(240):
            if p.poll() is not None:
                sys.exit("MoveEye beendet:\n" + open(os.path.join(tmp, "log.txt"), errors="replace").read()[-3000:])
            try:
                op.open(base + "/manifest.webmanifest", timeout=2); break
            except Exception:
                time.sleep(1)
        time.sleep(2)
        focus = {"titel": (82, 70)}
        if fotos:
            for f in sorted(os.listdir(fotos)):
                k = os.path.splitext(f)[0]
                k = re.sub(r"^\d+_", "", k)
                if k in ("titel", "grat", "grat_hoch", "lager", "abend", "nacht", "pano") or re.fullmatch(r"leiste[1-6]", k):
                    fx, fy = focus.get(k, (50, 50))
                    ok(post("action=set&slot=%s&fx=%s&fy=%s" % (k, fx, fy), open(os.path.join(fotos, f), "rb").read(), "application/octet-stream") == 200,
                       "Foto «%s» hochgeladen" % k)
        else:
            for k, w, h in (("titel", 2000, 1500), ("pano", 4000, 1000), ("leiste1", 1200, 900), ("leiste2", 2000, 700)):
                post("action=set&slot=%s&fx=82&fy=70" % k, foto(w, h), "application/octet-stream")
        if bilder:
            os.makedirs(bilder, exist_ok=True)
        with sync_playwright() as pw:
            br = pw.chromium.launch(args=["--no-proxy-server"])
            ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, color_scheme="dark",
                                 http_credentials={"username": "admin", "password": ADMIN_PW}, locale="de-CH")
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            hide = ("() => { const g = document.getElementById('gd-card'); if (g) g.style.display = 'none'; "
                    "['g2-ov','g2-spot','g2-bub'].forEach(i => { const e = document.getElementById(i); if (e) e.remove(); }); }")
            pg.goto(base + "/homepage", wait_until="domcontentloaded")
            pg.wait_for_selector("#hp-sbild", timeout=30000); pg.wait_for_timeout(1200); pg.evaluate(hide)
            r = pg.evaluate("() => [document.querySelector('#hp-sbild').textContent.trim(), document.getElementById('hp-sb-var').value, "
                            "document.getElementById('hp-sb-var').options[1].textContent]")
            ok(r == ["🏞 Startseite: Bilder", "B", "A · Bildgeschichte (Tag bis Nacht)"], "Karte «Homepage»: Knopf und Variante %s" % r)
            ok(pg.evaluate("() => document.documentElement.scrollWidth") <= 390, "/homepage: keine waagrechte Bildlaufleiste")
            if bilder:
                pg.locator("section.card", has=pg.locator("#hp-sbild")).screenshot(path=os.path.join(bilder, "homepage_karte.png"))
            pg.goto(base + "/startbilder", wait_until="domcontentloaded")
            pg.wait_for_function("() => document.querySelectorAll('#sb-list .sb-c').length === 13", timeout=30000)
            pg.wait_for_function("() => [...document.querySelectorAll('#sb-list img')].every(i => i.complete && i.naturalWidth > 0)", timeout=60000)
            pg.evaluate(hide); pg.wait_for_timeout(500)
            ok(pg.evaluate("() => document.documentElement.scrollWidth") <= 390, "/startbilder: keine waagrechte Bildlaufleiste")
            names = pg.evaluate("() => [...document.querySelectorAll('#sb-list .sb-b b')].map(b => b.textContent)")
            ok(names[0] == "Titelbild (A und B)" and names[-1] == "B · Bildleiste, Bild 6", "Seite: %s … %s" % (names[:1], names[-1:]))
            if bilder:
                pg.screenshot(path=os.path.join(bilder, "startbilder_390.png"), full_page=False)
                pg.screenshot(path=os.path.join(bilder, "startbilder_390_ganz.png"), full_page=True)
            im = pg.locator("#sb-titel .sb-img img"); bb = im.bounding_box()
            im.click(position={"x": bb["width"] * .3, "y": bb["height"] * .4})
            try:
                pg.wait_for_function("() => (document.querySelector('#sb-titel .sb-b .sb-msg') || {}).textContent === 'Fokuspunkt gespeichert.'", timeout=15000)
                fo = True
            except Exception:
                fo = False
            ok(fo, "Fokuspunkt per Tippen gespeichert (%s)" % pg.evaluate("() => (document.querySelector('#sb-titel .sb-b .sb-msg') || {}).textContent"))
            post("", json.dumps({"action": "focus", "slot": "titel", "fx": 82, "fy": 70}).encode(), "application/json")
            ok(not errs, "keine JS-Fehler auf /startbilder %s" % errs[:2])
            for v, h in (("B", 844), ("A", 844)):
                p2 = ctx.new_page(); e2 = []
                p2.on("pageerror", lambda e: e2.append(str(e)))
                p2.goto(base + "/startbilder/vorschau?v=" + v, wait_until="load"); p2.wait_for_timeout(1500)
                ok(p2.evaluate("() => document.documentElement.scrollWidth") <= 390, "Vorschau %s: keine waagrechte Bildlaufleiste" % v)
                ok(p2.evaluate("() => { const a = document.querySelector('main a'), h = document.querySelector('.hero'); "
                               "return a.getBoundingClientRect().top - h.getBoundingClientRect().bottom; }") < 40, "Vorschau %s: Knöpfe direkt unter dem Titelbild" % v)
                if bilder:
                    p2.screenshot(path=os.path.join(bilder, "vorschau_%s_390.png" % v))
                    p2.evaluate("window.scrollTo(0, %d)" % (h * (1.6 if v == "A" else 1.0))); p2.wait_for_timeout(1500)
                    p2.screenshot(path=os.path.join(bilder, "vorschau_%s_390_weiter.png" % v))
                ey = p2.evaluate("() => { const e = document.querySelector('h1 .mweye'), h = e && e.closest('h1'); if (!e) return null; const r = e.getBoundingClientRect(), "
                                 "s = parseFloat(getComputedStyle(h).fontSize); return [r.width, r.height, s, r.left, getComputedStyle(e.querySelector('.mws-lid')).animationName, "
                                 "[...document.querySelectorAll('main a')].map(a => a.getAttribute('href')), "
                                 "Math.max(...[...document.querySelectorAll('main a')].map(a => a.getBoundingClientRect().right))]; }")
                ok(ey and ey[1] >= ey[2] * 0.9 and ey[1] <= ey[2] * 1.5 and ey[3] < 80 and ey[4] == "mws-b",
                   "Vorschau %s: bewegtes Auge oben links beim Titel (B × H %s, Schrift %s px)" % (v, ey and [round(ey[0]), round(ey[1])], ey and ey[2]))
                ok(ey and ey[5] == ["demo/", "Sim/?grossvater=1", "Funk/", "Sim/", "Info/"] and ey[6] <= 390,
                   "Vorschau %s 390 px: 5 Kacheln in der Reihenfolge, nichts ragt hinaus %s" % (v, ey and ey[5]))
                # 22.11.2026 (Besitzer, «Symbol-Animation»): die rote Person geht in den Ecken, Fächer und Pupille gehen mit
                sy = p2.evaluate(SYM_JS)
                ok(sy and sy[0] == ["mws-w", "mws-f", "mws-e", "mws-s", "mws-s", "mws-b"] and sy[1] == "rgb(224, 36, 43)" and sy[2] > 0 and sy[3] != sy[4],
                   "Vorschau %s: Symbol mit gehender roter Person (Animationen, Farbe, Bewegung %s)" % (v, sy))
                if bilder:
                    p2.evaluate("window.scrollTo(0, 0)"); p2.wait_for_timeout(300)
                    p2.locator("h1 .mweye").screenshot(path=os.path.join(bilder, "symbol_%s_390.png" % v))
                ok(not e2, "Vorschau %s: keine JS-Fehler %s" % (v, e2[:2]))
                p2.close()
            # 22.11.2026 (Besitzer: «Titel oben abgeschnitten, Kacheln unter dem Bildschirm»): die erste Ansicht passt ohne Scrollen
            fit = ("() => { const r = e => e.getBoundingClientRect(), h = r(document.querySelector('h1')), t = [...document.querySelectorAll('main .tile')].map(r), "
                   "l = r(document.querySelector('.cap1 .line')); return [Math.round(h.top), Math.round(Math.max(...t.map(x => x.bottom))), innerHeight, "
                   "document.documentElement.scrollWidth, innerWidth, t.length, Math.round(l.bottom), Math.round(Math.min(...t.map(x => x.top)))]; }")
            for w, h, mob in ((1366, 768, False), (1536, 864, False), (1280, 720, False), (1280, 650, False), (820, 1180, True), (390, 844, True)):
                cf = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1 if not mob else 2, is_mobile=mob, has_touch=mob,
                                    http_credentials={"username": "admin", "password": ADMIN_PW}, locale="de-CH")
                pf = cf.new_page()
                for v in ("A", "B"):
                    pf.goto(base + "/startbilder/vorschau?v=" + v, wait_until="load"); pf.wait_for_timeout(800)
                    pf.evaluate("() => { const b = document.querySelector('.mw-back, #mw-back'); if (b) b.remove(); }")
                    f = pf.evaluate(fit)
                    ok(f[0] >= 0 and f[1] <= f[2] and f[3] <= f[4] and f[5] == 5 and f[6] <= f[7],
                       "Vorschau %s %d × %d: Titel ganz sichtbar (oben %d px), alle 5 Kacheln im Bild (unten %d ≤ %d), Satz über den Kacheln" % (v, w, h, f[0], f[1], f[2]))
                    if bilder:
                        pf.screenshot(path=os.path.join(bilder, "passt_%s_%dx%d.png" % (v, w, h)))
                cf.close()
            ctx3 = br.new_context(viewport={"width": 1024, "height": 1366}, device_scale_factor=2, reduced_motion="reduce",   # iPad, still
                                  http_credentials={"username": "admin", "password": ADMIN_PW}, locale="de-CH")
            p3 = ctx3.new_page(); e3 = []
            p3.on("pageerror", lambda e: e3.append(str(e)))
            for v in ("A", "B"):
                p3.goto(base + "/startbilder/vorschau?v=" + v, wait_until="load"); p3.wait_for_timeout(1200)
                st = p3.evaluate("() => { const s = document.querySelector('h1 .mweye svg'); if (!s) return 'fehlt'; "
                                 "return [...new Set(['.mws-w', '.mws-f', '.mws-e', '.mws-l1', '.mws-a1', '.mws-lid'].map(q => getComputedStyle(s.querySelector(q)).animationName))].join(); }")
                ok(st == "none", "Vorschau %s iPad, «weniger Bewegung»: das Auge steht still (%s)" % (v, st))
                ok(p3.evaluate("() => document.documentElement.scrollWidth") <= 1024, "Vorschau %s iPad: keine waagrechte Bildlaufleiste" % v)
                if bilder:
                    p3.screenshot(path=os.path.join(bilder, "vorschau_%s_ipad.png" % v))
            ok(not e3, "Vorschau iPad: keine JS-Fehler %s" % e3[:2])
            ctx3.close()
            br.close()
    finally:
        p.terminate()
        try:
            p.wait(20)
        except Exception:
            p.kill()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
