#!/usr/bin/env python3
"""Stimmproben für Lia (Grossvater Phase 2, Besitzer 21.11.2026): weibliche deutsche Piper-Stimmen, je zwei Sätze als Ogg und
MP3, dazu die MODEL_CARD (Lizenz) jeder Stimme. Der Besitzer wählt, ERST danach wird gesprochen (stimmen.py).
    python3 werkzeuge/stimmen/proben.py <out>     (piper im PATH oder ./piper/piper, ffmpeg)"""
import os
import subprocess
import sys
import urllib.request

HF = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/de/de_DE/"
STIMMEN = ["eva_k/x_low/de_DE-eva_k-x_low", "kerstin/low/de_DE-kerstin-low", "ramona/low/de_DE-ramona-low"]
SAETZE = ["Lia. Lia Arnold. Toni war mein Grossvater. Und du: zu langsam.",
          "Er lebt noch, weisst du. Er redet nur nicht gern über damals. Komm, die Sonne wartet nicht auf uns."]


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    pb = "./piper/piper" if os.path.exists("./piper/piper") else "piper"
    for s in STIMMEN:
        name = os.path.basename(s)
        mp = os.path.join(out, name + ".onnx")
        try:
            for ext in (".onnx", ".onnx.json"):
                urllib.request.urlretrieve(HF + s + ext, mp.replace(".onnx", ext))
            urllib.request.urlretrieve(HF + os.path.dirname(s) + "/MODEL_CARD", os.path.join(out, "MODEL_CARD_%s.txt" % name))
            wav = os.path.join(out, name + ".wav")
            subprocess.run([pb, "--model", mp, "--sentence_silence", "0.5", "--output_file", wav], input=" ".join(SAETZE).encode("utf-8"),
                           check=True, capture_output=True, timeout=180)
            for ext, codec in (("ogg", ["-c:a", "libvorbis", "-q:a", "4"]), ("mp3", ["-c:a", "libmp3lame", "-q:a", "4"])):
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af", "loudnorm=I=-16:TP=-1.5", "-ac", "1"] + codec +
                               [os.path.join(out, "lia_probe_%s.%s" % (name, ext))], check=True, timeout=120)
            os.remove(wav)
            print("ok", name, flush=True)
        except Exception as e:  # noqa: BLE001
            print("FEHLT", name, e, flush=True)
        for ext in (".onnx", ".onnx.json"):
            p = mp.replace(".onnx", ext)
            if os.path.exists(p):
                os.remove(p)


if __name__ == "__main__":
    main()
