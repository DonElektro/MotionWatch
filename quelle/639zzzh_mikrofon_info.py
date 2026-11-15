#@ MoveEye – Teil 639zzzh: kein Mikrofon eingesteckt = ein grauer Hinweis, kein rotes Problem (Besitzer 2026-11) – ausser eine Funktion, die das Mikrofon braucht, ist an. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# arecord meldet «audio open error: No such device» (oder «cannot find card», «Kein solches Gerät» …), wenn das gewählte
# Mikrofon fehlt – z. B. die USB-Kamera mit Mikrofon ist nicht eingesteckt. Bisher: rot «Mikrofon» in der Selbstdiagnose,
# «1 Problem» im Kopf, in der Schutz-Ampel und im Push-Text. Jetzt (Hülle um health_check – alle lesen daraus):
#   - braucht keine eingeschaltete Funktion das Mikrofon: grau (Stufe «off», zählt nicht) «Kein Mikrofon eingesteckt (z. B. USB-Kamera)»
#   - sonst bleibt es rot und nennt die Funktion(en): Geräusch-Alarm, Klatschschalter, «Gesundheit!», Morse- / Funk-Empfang.
# ----------------------------------------------------------------------------
MIC_NONE_RE = re.compile(r"no such device|no such file or directory|kein solches ger|cannot find card|no soundcards found|unknown pcm|"
                         r"no capture device|aucun périphérique|nessun dispositivo", re.I)
_HX_MIC = {
    "No microphone plugged in (e.g. USB camera)": ("Kein Mikrofon eingesteckt (z. B. USB-Kamera)", "Aucun micro branché (p. ex. caméra USB)",
                                                   "Nessun microfono collegato (ad es. telecamera USB)", "Nagin microfon attaschà (p.ex. camera USB)"),
    "No microphone plugged in – needed by": ("Kein Mikrofon eingesteckt – gebraucht von", "Aucun micro branché – nécessaire pour",
                                             "Nessun microfono collegato – serve per", "Nagin microfon attaschà – basegnà da"),
    "Plug in the microphone (or the USB camera) or switch these functions off.": (
        "Mikrofon (oder die USB-Kamera) einstecken oder diese Funktionen ausschalten.", "Branche le micro (ou la caméra USB) ou désactive ces fonctions.",
        "Collega il microfono (o la telecamera USB) o disattiva queste funzioni.", "Attascha il microfon (u la camera USB) u deactivescha questas funcziuns."),
    "Noise alarm": ("Geräusch-Alarm", "Alarme sonore", "Allarme rumore", "Alarm da canera"),
    "Clap switch": ("Klatschschalter", "Interrupteur à claquement", "Interruttore a battito", "Interruptur da clappar"),
    "Bless you": ("«Gesundheit!»", "«À tes souhaits !»", "«Salute!»", "«Viva!»"),
    "Morse / radio receive": ("Morse- / Funk-Empfang", "Réception morse / radio", "Ricezione morse / radio", "Recepziun morse / radio"),
}
for _k, _v in _HX_MIC.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])


def mic_needed_by():
    """the switched-on functions that need the microphone (English names)"""
    out = []
    if CFG.get("noise_alarm"):
        out.append("Noise alarm")
    if CFG.get("clap_on"):
        out.append("Clap switch")
    if CFG.get("sneeze_on"):
        out.append("Bless you")
    try:
        if CFG.get("morse_rx", True) and "morse_on" in globals() and morse_on():
            out.append("Morse / radio receive")
    except Exception:
        pass
    return out


def mic_missing(status):
    """is the microphone status «error: … no such device …» (nothing plugged in)?"""
    s = str(status or "")
    return s.startswith("error") and bool(MIC_NONE_RE.search(s))


def mic_health_fix(h, lang=None):
    """the item «mic» of the self-diagnosis: missing microphone = grey, unless a function needs it (then red, names it)"""
    try:
        items = h.get("items") if isinstance(h, dict) else None
        if not items or not mic_missing((STATE.get("audio") or {}).get("status")):
            return h
        L = norm_lang(lang) if lang else cur_lang()
        need = mic_needed_by()
        for x in items:
            if x.get("id") != "mic":
                continue
            if need:
                x["level"] = "bad"
                x["text"] = tr("No microphone plugged in – needed by", L) + ": " + ", ".join(tr(n, L) for n in need)
                x["tip"] = tr("Plug in the microphone (or the USB camera) or switch these functions off.", L)
            else:
                x["level"] = "off"
                x["text"] = tr("No microphone plugged in (e.g. USB camera)", L)
                x["tip"] = ""
                x.pop("fehler", None)                          # an info: no «Mikrofon stört» / «Beheben» (639u)
            x["mic_none"] = True
        items.sort(key=lambda x: HEALTH_ORDER.index(x["level"]) if x.get("level") in HEALTH_ORDER else 9)
        h["count"] = {k: sum(1 for x in items if x.get("level") == k) for k in HEALTH_ORDER}
    except Exception as e:
        print(f"mic info: {e}")
    return h


_health_check_639zzzh = health_check


# wraps: health_check
def health_check(lang=None):                                   # + 639zzzh: no microphone plugged in = grey, unless needed
    return mic_health_fix(_health_check_639zzzh(lang), lang)


def mic_info_selftest():
    for k in _HX_MIC:
        assert DE.get(k) and all(TRX[L].get(k) for L in ("fr", "it", "rm")), "639zzzh: text " + k
    assert mic_missing("error: arecord: main:850: audio open error: No such device") and mic_missing("error: cannot find card '2'")
    assert not mic_missing("listening") and not mic_missing("error: Device or resource busy") and not mic_missing("off")
    keep = (dict(STATE.get("audio") or {}), {k: CFG.get(k) for k in ("noise_alarm", "clap_on", "sneeze_on")})
    try:
        STATE["audio"] = dict(keep[0], status="error: audio open error: No such device")
        CFG.update(noise_alarm=False, clap_on=False, sneeze_on=False)
        h = mic_health_fix({"items": [{"id": "mic", "level": "bad", "text": "x", "tip": "y"}], "count": {}}, "de")
        assert h["items"][0]["level"] == "off" and "Kein Mikrofon eingesteckt" in h["items"][0]["text"] and h["count"]["bad"] == 0, h
        CFG["noise_alarm"] = True
        h = mic_health_fix({"items": [{"id": "mic", "level": "bad", "text": "x", "tip": "y"}], "count": {}}, "de")
        assert h["items"][0]["level"] == "bad" and "Geräusch-Alarm" in h["items"][0]["text"] and h["count"]["bad"] == 1, h
    finally:
        STATE["audio"] = keep[0]; CFG.update(keep[1])
    return "no microphone plugged in = grey info; red only when a function needs it (and names it)"


SELFTEST_EXTRA.append(("Missing microphone = info, not a problem (639zzzh)", mic_info_selftest))
