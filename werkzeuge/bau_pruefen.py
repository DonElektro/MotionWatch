#!/usr/bin/env python3
"""Bau-Infos prüfen (real-bauen, Daniels Regel 01.11.2026): passen die Infos zum Selberbauen (hardware/gehaeuse/bau.json →
MoveEye «Bauen» und Simulator «Bauen») noch zum Projektstand? Es wird NICHTS automatisch nachgezogen – nur gewarnt:
«Bau-Infos veraltet: … – nachziehen?».

Geprüft wird:
  1. Pins und Kanäle: jede Verbindung in bau.json «verkabelung» mit «code» hat einen «wert»; derselbe Wert wird hier aus dem
     Code (quelle/) bzw. aus der Übergabe-Doku gelesen (PCA9685-Adresse und -Kanäle, GPIO, I2C-Adressen …). Anders = Warnung.
  2. Gehäuse-Quelle, Doku und Druckdateien: Prüfsummen gegen den festgehaltenen Stand hardware/gehaeuse/bau_abgleich.json
     (Quellcode/*.py, Übergabe / Materialliste / Montage, Einrichtung des Pi, 3MF-Dateien).
  3. Teileliste: jeder Eintrag der Materialliste hat Preis und Händler, jedes Druckteil seine Druckangaben und seine 3MF,
     die Fehlersuche zeigt nur Kennungen aus simulator3d/fehler_katalog.json.

    python3 werkzeuge/bau_pruefen.py               # Bericht (Exit 0, auch mit Warnungen)
    python3 werkzeuge/bau_pruefen.py --ci          # dazu «::warning::»-Zeilen für GitHub Actions
    python3 werkzeuge/bau_pruefen.py --json        # {"warnungen": [...], "werte": {...}} (Selbsttest von MoveEye, Teil 639w)
    python3 werkzeuge/bau_pruefen.py --streng      # Exit 1 bei Warnungen
    python3 werkzeuge/bau_pruefen.py --festhalten  # NACHDEM die Bau-Infos von Hand nachgezogen sind: Stand neu festhalten
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEH = os.path.join(REPO, "hardware", "gehaeuse")
BAU = os.path.join(GEH, "bau.json")
STAND = os.path.join(GEH, "bau_abgleich.json")
Q = os.path.join(REPO, "quelle")
DOKU = ["hardware/gehaeuse/Dokumente/Uebergabe_Gehaeuse_v5.md", "hardware/gehaeuse/Dokumente/Materialliste.md",
        "hardware/gehaeuse/Dokumente/LIESMICH_Montage_v5-1.md", "docs/Einrichtung_Raspberry_Pi.md", "docs/Gehaeuse_Variante2_Weitwinkel.md"]


def lies(rel):
    p = os.path.join(REPO, rel)
    if not os.path.isfile(p):
        return ""
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def quelle_text():
    return "".join(lies(os.path.relpath(p, REPO)) for p in sorted(glob.glob(os.path.join(Q, "*.py"))))


def suche(rx, text, fn=lambda m: m.group(1)):
    m = re.search(rx, text)
    return fn(m) if m else None


def werte():
    """die Prüfwerte aus dem Code und der Übergabe-Doku (Schlüssel = «code» in bau.json verkabelung)"""
    q = quelle_text()
    ue = lies(DOKU[0])
    adr = lambda s: None if s is None else "0x%02X" % int(s, 16) if s.lower().startswith("0x") else s
    w = {
        "pca_address": adr(suche(r'"pca_address":\s*"(0x[0-9a-fA-F]+)"', q)),
        "pca_pan_ch": suche(r'"pca_pan_ch":\s*(\d+)', q),
        "pca_tilt_ch": suche(r'"pca_tilt_ch":\s*(\d+)', q),
        "weit_ir_ch": suche(r"\bWEIT_IR_CH\s*=\s*(\d+)", q),
        "led_ch_rgb": suche(r'"led_ch_r":\s*(\d+),\s*"led_ch_g":\s*(\d+),\s*"led_ch_b":\s*(\d+)', q, lambda m: "/".join(m.groups())),
        "btn_gpio": suche(r'"btn_gpio_protect":\s*"(\d+)",\s*"btn_gpio_ack":\s*"(\d+)"', q, lambda m: "/".join(m.groups())),
        "gpio_relay": suche(r"GPIO_PAN,\s*GPIO_TILT,\s*GPIO_RELAY\s*=\s*\d+,\s*\d+,\s*(\d+)", q),
        "solar_addr": adr(suche(r'"solar_addr":\s*"(0x[0-9a-fA-F]+)"', q)),
        "mover_addr": adr(suche(r'"mover_addr":\s*"(0x[0-9a-fA-F]+)"', q)),
        "ups_e_addr": adr(suche(r"def ups_read_e\(addr=(0x[0-9a-fA-F]+)", q)),
        "doku_licht_weiss": suche(r"Kanal 0 Pan, 1 Tilt, (\d+) Licht weiss", ue),
        "doku_licht_ir": suche(r"Licht weiss, (\d+) Licht IR", ue),
        "doku_pir": suche(r"PIR AS312[^|]*\|[^|]*Ausgang GPIO (\d+)", ue),
        "doku_ds18": suche(r"DS18B20[^|]*\|\s*1-Wire GPIO (\d+)", ue),
    }
    return w


def sha(rel):
    p = os.path.join(REPO, rel)
    if not os.path.isfile(p):
        return None
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def stand_jetzt(bau):
    """was festgehalten wird: Prüfsummen der Quelle, der Doku und der Druckdateien, die Teile und die Prüfwerte"""
    dd = "hardware/gehaeuse/Druckdateien/"
    return {
        "quellcode": {os.path.basename(p): sha(os.path.relpath(p, REPO)) for p in sorted(glob.glob(os.path.join(GEH, "Quellcode", "*.py")))},
        "doku": {d: sha(d) for d in DOKU},
        "druckdateien": {n: sha(dd + n) for n in list(bau.get("druckdateien") or []) + list(bau.get("druckdateien_einzeln") or [])},
        "teile": sorted(t["id"] for t in bau.get("teile") or []),
        "bom": sorted(b["id"] for b in bau.get("bom") or []),
        "werte": werte(),
    }


def pruefen():
    with open(BAU, encoding="utf-8") as f:
        bau = json.load(f)
    W = werte()
    warn = []
    # 1. pins and channels
    for v in (bau.get("verkabelung") or {}).get("verbindungen") or []:
        k = v.get("code")
        if not k:
            continue
        if W.get(k) is None:
            warn.append(f"Prüfwert «{k}» ({v['id']}) im Code / in der Doku nicht mehr gefunden")
        elif str(W[k]).lower() != str(v.get("wert", "")).lower():
            warn.append(f"Verkabeln {v['id']}: Code sagt {W[k]}, Bau-Infos {v.get('wert')}")
    # 2. source, docs, print files against the stand
    st = {}
    if os.path.isfile(STAND):
        with open(STAND, encoding="utf-8") as f:
            st = json.load(f)
    else:
        warn.append("hardware/gehaeuse/bau_abgleich.json fehlt (bau_pruefen.py --festhalten)")
    jetzt = stand_jetzt(bau)
    for grp, name in (("quellcode", "Gehäuse-Quelle"), ("doku", "Doku"), ("druckdateien", "Druckdatei")):
        alt, neu = st.get(grp) or {}, jetzt[grp]
        for k in sorted(set(alt) | set(neu)):
            if alt.get(k) != neu.get(k):
                warn.append(f"{name} {k}: " + ("neu" if k not in alt else "fehlt" if neu.get(k) is None else "geändert"))
    for grp, name in (("teile", "Teile"), ("bom", "Materialliste")):
        a, n = set(st.get(grp) or []), set(jetzt[grp])
        if st and a != n:
            warn.append(f"{name}: " + ", ".join(sorted(["+" + x for x in n - a] + ["−" + x for x in a - n])))
    for k, v in (st.get("werte") or {}).items():
        if st and W.get(k) != v and not any(x.get("code") == k for x in (bau.get("verkabelung") or {}).get("verbindungen") or []):
            warn.append(f"Prüfwert {k}: {v} → {W.get(k)}")
    # 3. completeness of the parts list
    for b in bau.get("bom") or []:
        if not isinstance(b.get("preis"), (int, float)) or b.get("haendler") not in (bau.get("haendler") or {}):
            warn.append(f"Einkauf: {b['id']} ohne Preis-Schätzung oder Händler")
    druck = {p["datei"] for p in (bau.get("druck") or {}).get("teile") or []}
    for t in bau.get("teile") or []:
        if t.get("datei") and t["datei"] not in druck:
            warn.append(f"Drucken: {t['datei']} ohne Druckangaben")
    dd = os.path.join(GEH, "Druckdateien")
    for d in druck:
        if not os.path.isfile(os.path.join(dd, "MoveEye_v5-1_" + d + ".3mf")) and not any(d in n for n in os.listdir(dd)):
            warn.append(f"Drucken: keine 3MF für {d}")
    fk = os.path.join(REPO, "simulator3d", "fehler_katalog.json")
    if os.path.isfile(fk):
        with open(fk, encoding="utf-8") as f:
            ids = {e["id"] for e in json.load(f).get("fehler") or []}
        for i in bau.get("fehlersuche") or []:
            if i not in ids:
                warn.append(f"Fehlersuche: {i} nicht im Fehler-Katalog")
    return warn, W, bau


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ci", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--streng", action="store_true")
    ap.add_argument("--festhalten", action="store_true")
    a = ap.parse_args()
    warn, W, bau = pruefen()
    if a.festhalten:
        st = stand_jetzt(bau)
        st["_hinweis"] = ("Festgehaltener Stand der Bau-Infos (werkzeuge/bau_pruefen.py --festhalten): erst NACH dem Nachziehen von "
                          "hardware/gehaeuse/bau.json neu schreiben. bau_pruefen.py warnt, wenn Quelle, Doku, Druckdateien, Teile oder "
                          "Pins / Kanäle im Code davon abweichen.")
        with open(STAND, "w", encoding="utf-8") as f:
            f.write(json.dumps(dict(sorted(st.items())), ensure_ascii=False, indent=1) + "\n")
        print("festgehalten:", os.path.relpath(STAND, REPO))
        warn, W, bau = pruefen()
    if a.json:
        print(json.dumps({"warnungen": warn, "werte": W}, ensure_ascii=False))
        return 0
    for w in warn:
        print(("::warning title=Bau-Infos::" if a.ci else "WARNUNG: ") + f"Bau-Infos veraltet: {w} – nachziehen?")
    if not warn:
        print("Bau-Infos passen zum Projektstand (" + ", ".join(f"{k}={v}" for k, v in W.items()) + ")")
    return 1 if (a.streng and warn) else 0


if __name__ == "__main__":
    sys.exit(main())
