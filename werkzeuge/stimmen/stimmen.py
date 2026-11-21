#!/usr/bin/env python3
"""Stimmen für das Abenteuer-Kit (Grossvater K2, Besitzer 21.11.2026): Erzähler und Grossvater/Vater als Ogg, gesprochen mit
Piper (offline, auf dem Runner). Liest die Zeilen aus simulator3d/scripts/kit_k2_daten.gd (wer = erzaehler | grossvater),
setzt die Platzhalter je Rolle ein ({bezug}: Grossvater / Vater, {jahr}: 1974 / 2000), Zeilen mit {name} bleiben ohne Stimme
(der Name ist frei gewählt). Ausgabe: <out>/stimmen/<sha1-12>.ogg + <out>/stimmen/stimmen.json {text: datei} (deutsch).

    python3 werkzeuge/stimmen/stimmen.py <out>      (braucht: piper im PATH oder ./piper/piper, ffmpeg)
Die Stimmen (rhasspy/piper-voices, MIT / CC-Lizenz je Stimme, siehe stimmen.json «lizenz») lädt der Workflow.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATEN = os.path.join(R, "simulator3d", "scripts", "kit_k2_daten.gd")
HF = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/de/de_DE/"
STIMMEN = {   # role -> (voice, speaker speed): narrator calm, the grandfather / father deeper and slower
    "erzaehler": ("thorsten/high/de_DE-thorsten-high", 1.05),
    "grossvater": ("karlsson/low/de_DE-karlsson-low", 1.12),
}
JAHR_SPRECH = {"1974": "neunzehnhundertvierundsiebzig", "2000": "zweitausend"}


def zeilen():
    src = open(DATEN, encoding="utf-8").read()
    out = []
    for m in re.finditer(r'"wer":\s*"(erzaehler|grossvater)",\s*"text":\s*"([^"]+)"', src):
        out.append((m.group(1), m.group(2)))
    for m in re.finditer(r'"sag":\s*"([^"]+)",\s*"wer":\s*"(erzaehler|grossvater)"', src):
        out.append((m.group(2), m.group(1)))
    return out


def varianten(text):
    """the text as the game shows it (German) for both roles: [(shown text, spoken text)]"""
    if "{name}" in text:
        return []
    res = []
    for bezug, jahr, lia in (("Grossvater", "1974", "Enkelin"), ("Vater", "2000", "Tochter")):
        shown = text.replace("{bezug}", bezug).replace("{jahr}", jahr).replace("{lia_bezug}", lia).replace("{jahr_kurz}", jahr[2:])
        spoken = shown
        for j, w in JAHR_SPRECH.items():
            spoken = spoken.replace(j, w)
        spoken = spoken.replace("«", "").replace("»", "").replace("…", ",")
        if (shown, spoken) not in res:
            res.append((shown, spoken))
    return res


def modell(stimme):
    os.makedirs("stimmen_modelle", exist_ok=True)
    p = os.path.join("stimmen_modelle", os.path.basename(stimme) + ".onnx")
    for ext in (".onnx", ".onnx.json"):
        if not os.path.exists(p.replace(".onnx", ext)):
            urllib.request.urlretrieve(HF + stimme + ext, p.replace(".onnx", ext))
    return p


def piper_bin():
    for c in ("./piper/piper", "piper"):
        try:
            subprocess.run([c, "--help"], capture_output=True, timeout=30)
            return c
        except Exception:  # noqa: BLE001
            continue
    raise SystemExit("piper fehlt")


def main():
    out = os.path.join(sys.argv[1], "stimmen")
    os.makedirs(out, exist_ok=True)
    pb = piper_bin()
    for w, (stimme, _t) in STIMMEN.items():                  # the licence of each voice, for the check before it is used
        try:
            urllib.request.urlretrieve(HF + os.path.dirname(stimme) + "/MODEL_CARD", os.path.join(out, "MODEL_CARD_%s.txt" % w))
        except Exception as e:  # noqa: BLE001
            print("MODEL_CARD %s: %s" % (w, e))
    karte = {}
    n = 0
    for wer, text in zeilen():
        stimme, tempo = STIMMEN[wer]
        mp = modell(stimme)
        for shown, spoken in varianten(text):
            key = hashlib.sha1(("%s|%s" % (wer, shown)).encode("utf-8")).hexdigest()[:12]
            wav = os.path.join(out, key + ".wav")
            ogg = os.path.join(out, key + ".ogg")
            subprocess.run([pb, "--model", mp, "--length_scale", str(tempo), "--output_file", wav], input=spoken.encode("utf-8"),
                           check=True, capture_output=True, timeout=120)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af", "loudnorm=I=-16:TP=-1.5", "-ac", "1", "-ar", "22050",
                            "-c:a", "libvorbis", "-q:a", "3", ogg], check=True, timeout=120)
            os.remove(wav)
            karte[shown] = {"datei": key + ".ogg", "wer": wer}
            n += 1
            print(wer, key, shown, flush=True)
    meta = {"_info": "Erzähler und {bezug}: vorgesprochen mit Piper (werkzeuge/stimmen/stimmen.py), nur Deutsch.",
            "stimmen": {w: HF + s for w, (s, _t) in STIMMEN.items()},
            "lizenz": "Piper (MIT); die Lizenz jeder Stimme steht in ihrer MODEL_CARD (hier als MODEL_CARD_<rolle>.txt dabei)",
            "zeilen": karte}
    with open(os.path.join(out, "stimmen.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("Stimmen: %d Dateien" % n)


if __name__ == "__main__":
    main()
