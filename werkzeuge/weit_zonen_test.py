#!/usr/bin/env python3
"""Test «Weitwinkel-KI» (Teil 639zw, Paket Weitwinkel-KI vom 14.11.2026) über die echte Web-Schnittstelle, ohne Simulator:

  1  Update eines bestehenden Geräts: eine alte Einstellungsdatei (Wärmebild-Bestätigung aus, alte Liste kopf_ov_zones)
     -> die Bestätigung ist nachts einmal an, «Neu in …» zeigt den Hinweis (mit «nachts»), nach «gesehen» nicht mehr.
  2  Zonen im Weitwinkelbild: die alte Liste gilt für die feste Montage weiter (mit allen drei Zielen), speichern mit Zielen,
     wieder lesen; Familie (Recht «arm») darf lesen, aber nicht ändern; ohne Anmeldung nichts.
  3  /api/wache: Ziele Person / Tier / Fahrzeug ab Werk, Zeitfenster 4 s und Spielraum 8°, Zähler.
  4  Seiten: Kameras hat die Karte «Zonen im Weitwinkelbild», der Zonen-Editor die Ziele pro Zone.

  python3 werkzeuge/weit_zonen_test.py [--datei X.py]
"""
import argparse
import glob
import json
import os
import re
import shutil
import socket
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
from rechte_schutz_test import Geraet, REPO  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Weitwinkel-KI: Zonen, Ziele, Wärmebild-Bestätigung")
    ap.add_argument("--datei", default="")
    ap.add_argument("--port", type=int, default=5147)
    a = ap.parse_args()
    datei = os.path.abspath(a.datei) if a.datei else sorted(glob.glob(os.path.join(REPO, "webcam_bewegung_*.py")),
                              key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]
    with socket.socket() as sk:
        try:
            sk.bind(("127.0.0.1", a.port))
        except OSError:
            sk.bind(("127.0.0.1", 0)); a.port = sk.getsockname()[1]
    G = Geraet(datei, a.port)
    fehler = []

    def pruef(ok, text):
        print(("  ok    " if ok else "  FEHLER ") + text, flush=True)
        if not ok:
            fehler.append(text)

    alt = [{"id": "0a0b0c0d", "name": "Zelt", "mode": "trigger", "points": [[0.1, 0.4], [0.6, 0.4], [0.6, 1.0], [0.1, 1.0]]}]
    G.einst_aendern(lambda c: c.update(alarm_heat_fusion=False, kopf_ov_zones=alt, news_seen_web="3.0.0", news_seen_tk="3.0.0"))
    try:
        G.start()
        c, j = G.req("/api/users", {"action": "add", "name": "Anna", "password": "anna-pass-1", "role": "family"})
        pruef(c == 200 and j.get("ok"), "Benutzerin Anna (Familie) angelegt")
        print("== 1: Update - Wärmebild-Bestätigung nachts einmal an, Hinweis", flush=True)
        c, w = G.req("/api/wache?lang=de")
        pruef(c == 200 and w["fusion"]["on"] is True, "Bestätigung nach dem Update an (war aus)")
        c, n = G.req("/api/news?lang=de&who=web")
        txt = json.dumps(n, ensure_ascii=False)
        pruef(c == 200 and n.get("show") and "nachts" in txt.lower() and "alarm_heat_fusion" in txt, "«Neu in …» zeigt den Hinweis mit «nachts» (%d)" % c)
        c, n = G.req("/api/news?lang=de&who=web", {})
        c, n = G.req("/api/news?lang=de&who=web")
        pruef(c == 200 and "Wärmebild" not in json.dumps(n, ensure_ascii=False), "nach «gesehen» nicht mehr im Browser")
        c, n = G.req("/api/news?lang=de&who=tk")
        pruef(c == 200 and "Wärmebild" in json.dumps(n, ensure_ascii=False), "im Fenster noch einmal")
        print("== 2: Zonen im Weitwinkelbild", flush=True)
        c, z = G.req("/api/weit/zones")
        zs = z.get("zones") or [] if isinstance(z, dict) else []
        pruef(c == 200 and z.get("key") == "fixed" and len(zs) == 1 and zs[0]["targets"] == ["person", "animal", "vehicle"],
              "alte Liste gilt für die feste Montage, alle drei Ziele (%s)" % (zs[:1],))
        neu = [{"name": "Zelt", "mode": "trigger", "targets": ["person"], "points": [[0.1, 0.4], [0.6, 0.4], [0.6, 1.0], [0.1, 1.0]]},
               {"name": "Strasse", "mode": "ignore", "targets": ["vehicle", "animal"], "points": [[0.0, 0.0], [1.0, 0.0], [1.0, 0.3]]}]
        c, r = G.req("/api/weit/zones", {"zones": neu, "lang": "de"}, wer="Anna")
        pruef(c == 403, "Familie darf die Zonen nicht ändern (%d)" % c)
        c, r = G.req("/api/weit/zones", wer="Anna")
        pruef(c == 200, "Familie darf sie sehen (%d)" % c)
        c, r = G.req("/api/weit/zones", wer=None)
        pruef(c in (401, 403), "ohne Anmeldung nichts (%d)" % c)
        c, r = G.req("/api/weit/zones", {"zones": neu, "lang": "de"})
        pruef(c == 200 and r.get("ok"), "Administrator speichert zwei Zonen")
        c, z = G.req("/api/weit/zones")
        zs = z.get("zones") or []
        pruef([(x["mode"], x["targets"]) for x in zs] == [("trigger", ["person"]), ("ignore", ["animal", "vehicle"])],
              "gelesen wie gespeichert: Art und Ziele (%s)" % [(x["mode"], x["targets"]) for x in zs])
        c, r = G.req("/api/weit/zones", {"zones": "x"})
        pruef(c == 400, "ungültige Zonen: 400 (%d)" % c)
        print("== 3: /api/wache", flush=True)
        c, w = G.req("/api/wache?lang=de")
        f = w.get("fusion") or {}
        pruef(sorted(w.get("classes") or []) == ["animal", "person", "vehicle"], "Ziele ab Werk: Person, Tier, Fahrzeug (%s)" % w.get("classes"))
        pruef(f.get("window") == 4.0 and f.get("tol") == 8.0 and "fault" in f and "last" in f, "Zeitfenster 4 s, Spielraum 8°, Zähler")
        print("== 4: Seiten", flush=True)
        c, p = G.req("/cams", roh=True)
        pruef(c == 200 and b"wk-cams" in p, "Kameras: Karte «Zonen im Weitwinkelbild»")
        c, p = G.req("/zones?cam=weit", roh=True)
        pruef(c == 200 and b"function wkTargets" in p and b"WKHEAD" in p, "Zonen-Editor: Ziele pro Zone, Kopfstellung beim Speichern")
        c, t = G.req("/api/timeline?lang=de")
        pruef(c == 200, "Zeitleiste antwortet (%d)" % c)
        G.stop()
        st = G.einst()
        pruef(st.get("alarm_heat_fusion") is True and st.get("heat_fus_mig") is True, "gespeichert: an, Umstellung erledigt")
        pruef(st.get("kopf_ov_zone_sets", {}).get("fixed") and st.get("kopf_ov_zones") == st["kopf_ov_zone_sets"]["fixed"],
              "pro Montage gespeichert, alte Liste gleich nachgeführt")
    finally:
        G.stop()
        log = G.log()
        if "Traceback (most recent call last)" in log:
            print(log[-3000:]); fehler.append("Traceback im Protokoll")
        shutil.rmtree(G.tmp, ignore_errors=True)
    print("Weitwinkel-Zonen-Test " + ("OK" if not fehler else "FEHLGESCHLAGEN (%d)" % len(fehler)))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
