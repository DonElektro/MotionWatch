"""Erkennungstest – Fortschritt fürs Testbild des Kiosks (Simulator-PC «HP», simulator3d/beilagen_linux/testbild.py).

erkennungstest.py --fortschritt /run/moveeye-test/fortschritt.json schreibt dorthin (immer ganz, über eine Temp-Datei und
Umbenennen, lesbar für alle): Plan, Zahl der Fälle (aus dem Plan gezählt), laufender Fall mit Soll (was der Simulator
zeigt), Bilanz bisher (Personen erkannt, Tiere / Autos ohne Personen-Alarm, Leerlauf ruhig, Pushes) und den letzten Fall.
Dazu alle ~5 s das Bild, das MoveEye gerade auswertet, mit MoveEyes eigenen Rahmen (/snapshot.jpg: Personen rot mit
Nummer, Bewegung / Tier / Fahrzeug weiss, KI-Objekte farbig mit Name und Prozent), verkleinert als PNG (bild.png höchstens
960 px breit, bild_klein.png 640 px) neben die JSON-Datei, mit «Ist» (was MoveEye in diesem Bild meldet).
Kostet den Test kaum etwas (ein Bild alle 5 s, eigener Faden); jeder Fehler hier wird verschluckt - der Test geht vor.
"""
import json
import os
import threading
import time
import urllib.request

import faelle as F

SOLL = {"person": "Person", "animal": "Tier", "vehicle": "Fahrzeug", "none": "nichts"}
EXTRA_FAELLE = {"blend": 4, "linse": 3, "kopf": 2, "ruhig": 4, "nebenfunde": 5, "real": len(F.REAL)}
EXTRA_JE_LAUF = ("real",)          # diese Sonderfälle gibt es --laeufe mal


def faelle_zaehlen(plaene, schritte_von, laeufe):
    """Zahl der Fälle eines Plans (wie faelle.orte / zimmer / EXTRAS, ohne blinde Flecken)"""
    n = 0
    for p in plaene:
        for schritt in schritte_von(p):
            if schritt[0] != "orte":
                n += sum(EXTRA_FAELLE.get(w, 0) * (laeufe if w in EXTRA_JE_LAUF else 1) for w in schritt[1].split(","))
                continue
            o = schritt[2]
            sel, sel_leer = o.get("sel"), o.get("sel_leer", False)
            for spec in [x for x in schritt[1].split(",") if x]:
                place, only = (spec.split(":", 1) + [""])[:2]
                if place == "schlafzimmer":
                    n += 5
                    continue
                if place not in F.PLAN:
                    continue
                conds = only.split("+") if only else F.PLAN[place][1]
                for c in conds:
                    for e in F.EVENTS:
                        k = "%s|%s|%s" % (place, c, e)
                        if sel is None or k in sel or (e == "leer" and sel_leer):
                            n += laeufe if e in F.PERSON_EVENTS else 1
    return n


def zeilen(pfad):
    try:
        with open(pfad, encoding="utf-8") as f:
            return sum(1 for ln in f if ln.strip())
    except OSError:
        return 0


def ist_von(s):
    """was MoveEye in diesem Moment meldet -> (art, text)"""
    labs = set(s.get("present") or [])
    if int(s.get("persons") or 0) > 0:
        n = int(s.get("persons") or 0)
        return "person", "Person" if n == 1 else "%d Personen" % n
    tier = sorted(labs & F.ANIMAL_LABELS)
    if tier:
        return "tier", "Tier (%s)" % ", ".join(tier[:2])
    fz = sorted(labs & (F.VEH_LABELS - {"bicycle"}))
    if fz:
        return "fahrzeug", "Fahrzeug (%s)" % ", ".join(fz[:2])
    if int(s.get("warm") or 0) > 0:
        return "waerme", "Wärme"
    if labs & {"motion", "prealarm"}:
        return "bewegung", "nur Bewegung"
    return "nichts", "nichts"


class Fortschritt:
    def __init__(self, pfad, plan, plan_text, faelle, start, schon=0, arbeit=""):
        self.pfad = pfad
        self.ordner = os.path.dirname(pfad)
        self.lock = threading.Lock()
        self.d = {"v": 1, "plan": plan, "plan_text": plan_text, "faelle": faelle, "fall": 0, "name": "", "start": int(start),
                  "status": "vorbereitung", "bilanz": {"personen": [0, 0], "ignoriert": [0, 0], "leer": [0, 0], "pushes": 0}}
        if arbeit:
            self.d["arbeit"] = arbeit[:30]                       # Dauerrechnen (3.55.0): welche Arbeit das Testbild zeigt
        self.gezaehlt = schon
        self.laeuft = True
        self._schreiben()

    # ------------------------------------------------ JSON
    def _schreiben(self):
        try:
            tmp = self.pfad + ".neu"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.d, f, ensure_ascii=False)
            os.chmod(tmp, 0o644)
            os.replace(tmp, self.pfad)
        except OSError:
            pass

    def setze(self, **kw):
        with self.lock:
            self.d.update(kw)
            self.d["t"] = int(time.time())
            self._schreiben()

    def fall_beginnt(self, tag, want):
        with self.lock:
            self.d.update(fall=self.gezaehlt + 1, name=tag.replace("_", " · ")[:60], soll=SOLL.get(want, want or ""),
                          status="laeuft", t=int(time.time()))
            self.d["faelle"] = max(self.d["faelle"], self.d["fall"])
            self.d.pop("ist", None)
            self._schreiben()

    def fall_fertig(self, rec):
        with self.lock:
            self.gezaehlt += 1
            b = self.d["bilanz"]
            name = str(rec.get("key", "")).replace("|", " · ")[:60]
            b["pushes"] += len(rec.get("pushes") or [])
            if "false_person_eps" in rec:                        # niemand da: ruhig geblieben?
                ok = not rec.get("false_person_eps")
                b["leer"][1] += 1
                b["leer"][0] += 1 if ok else 0
                txt = "ruhig" if ok else "Fehlalarm: %s× Person" % rec.get("false_person_eps")
            elif "false_person" in rec:                          # Tier / Auto: kein Personen-Alarm?
                ok = not rec.get("false_person")
                b["ignoriert"][1] += 1
                b["ignoriert"][0] += 1 if ok else 0
                txt = ("%s – kein Personen-Alarm" % (rec.get("as") or "Tier/Auto")) if ok else "als Person gemeldet"
            else:                                                # Person: erkannt?
                ok = bool(rec.get("detected"))
                b["personen"][1] += 1
                b["personen"][0] += 1 if ok else 0
                txt = ("Person erkannt" + (" nach %.1f s" % rec["t_detect"] if rec.get("t_detect") is not None else "")) if ok \
                    else "Person NICHT erkannt (%s)" % (rec.get("as") or "–")
            self.d["letzter"] = {"name": name, "ok": ok, "text": txt[:60]}
            self.d["t"] = int(time.time())
            self._schreiben()

    def fertig(self, status="fertig"):
        self.laeuft = False
        self.setze(status=status)

    # ------------------------------------------------ Bild alle 5 s
    def bild_faden(self, mw_url):
        th = threading.Thread(target=self._bilder, args=(mw_url,), daemon=True)
        th.start()
        return th

    def _bilder(self, mw_url):
        try:
            import cv2
            import numpy as np
        except ImportError:
            return
        while self.laeuft:
            t0 = time.time()
            try:
                s = F.mw_state()
                with urllib.request.urlopen(mw_url + "/snapshot.jpg", timeout=6) as r:
                    roh = r.read(8_000_000)
                img = cv2.imdecode(np.frombuffer(roh, np.uint8), cv2.IMREAD_COLOR)
                if img is not None and img.size:
                    for name, breite in (("bild.png", 960), ("bild_klein.png", 640)):
                        h, w = img.shape[:2]
                        k = cv2.resize(img, (breite, max(1, round(h * breite / w))), interpolation=cv2.INTER_AREA) if w > breite else img
                        ok, buf = cv2.imencode(".png", k, [cv2.IMWRITE_PNG_COMPRESSION, 1])
                        if ok:
                            tmp = os.path.join(self.ordner, name + ".neu")
                            with open(tmp, "wb") as f:
                                f.write(buf.tobytes())
                            os.chmod(tmp, 0o644)
                            os.replace(tmp, os.path.join(self.ordner, name))
                    art, txt = ist_von(s)
                    self.setze(ist={"art": art, "text": txt, "fps": float(s.get("fps") or 0)}, bild_t=int(time.time()))
            except Exception:
                pass
            time.sleep(max(1.0, 5.0 - (time.time() - t0)))


def einhaengen(fs):
    """faelle.observe / faelle.save umleiten: Fallbeginn und -ende landen im Fortschritt (sonst ändert sich nichts)"""
    obs, sav = F.observe, F.save

    def observe(secs, tag, want, t_spawn, base, **kw):
        try:
            fs.fall_beginnt(tag, want)
        except Exception:
            pass
        return obs(secs, tag, want, t_spawn, base, **kw)

    def save(rec):
        sav(rec)
        try:
            fs.fall_fertig(rec)
        except Exception:
            pass
    F.observe, F.save = observe, save
