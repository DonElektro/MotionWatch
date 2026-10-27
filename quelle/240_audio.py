#@ Motion Watch – Teil 240: Mikrofon, Geräusch-Alarm. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Audio: microphone (noise alarm, live listening in the browser, sound in the recordings) + loudspeaker of the Pi (siren)
#   One "arecord" process reads the microphone (16 kHz mono) and feeds everything else: a USB microphone can only be
#   opened by one program at a time. The loudspeaker plays generated sounds (siren, two-tone, beeps, horn) or own sound
#   files from <settings folder>/sounds via "aplay". While the Pi plays a sound, the noise alarm does not listen.
# ----------------------------------------------------------------------------
AUDIO_RATE = 16000                     # microphone: 16 kHz mono 16 bit = 32 kB/s (fine over a phone hotspot)
AUDIO_CHUNK = AUDIO_RATE // 10         # 0.1 s
OUT_RATE = 22050                       # loudspeaker
AUDIO_DEV_RE = re.compile(r"^(default|(plug)?hw:CARD=[A-Za-z0-9_\-]{1,40},DEV=\d{1,2})$")
AUDIO_DEVS = {"in": [], "out": [], "time": 0.0, "err": ""}
SOUND_KINDS = ("siren", "two-tone", "beeps", "horn", "whistle", "bangs")
SIREN_ON = ("off", "person", "alarm", "all")
SOUND_EXT = (".wav", ".mp3", ".ogg", ".flac", ".m4a")
SOUND_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.\-()]{0,80}$")
_ALSA_RE = re.compile(r"^card (\d+): (\S+) \[(.*?)\], device (\d+): (.*?) \[(.*?)\]")
AUDIO = None                           # AudioMonitor, created together with the camera loop


def sounds_dir():
    return os.path.join(DATA_DIR, "sounds")


def own_sounds():
    try:
        return sorted(f for f in os.listdir(sounds_dir()) if f.lower().endswith(SOUND_EXT) and SOUND_NAME_RE.match(f))[:40]
    except OSError:
        return []


def _alsa_scan(cmd):
    """Sound cards from "arecord -l" / "aplay -l". The id uses the card NAME (plughw:CARD=Device,DEV=0): the number of a USB
    card can change after a reboot, the name stays. plughw converts the sample rate (many USB microphones only do 48 kHz)."""
    if not shutil.which(cmd):
        return [], f"{cmd} is missing (sudo apt install alsa-utils)"
    rc, out, err = _run([cmd, "-l"], timeout=10)
    items = []
    for line in (out or "").splitlines():
        m = _ALSA_RE.match(line.strip())
        if not m:
            continue
        _n, cid, cname, dev, _dn, dname = m.groups()
        dev_id = f"plughw:CARD={cid},DEV={dev}"
        if not AUDIO_DEV_RE.match(dev_id) or any(i["id"] == dev_id for i in items):
            continue
        label = cname if (not dname or dname == cname or dname.startswith("USB Audio")) else f"{cname} - {dname}"
        items.append({"id": dev_id, "name": label})
    return items, ("" if rc == 0 or items else (err or "")[:200])


def audio_scan():
    """Look for microphones and loudspeakers (also called from the page: "Search devices")."""
    ins, e1 = _alsa_scan("arecord")
    outs, e2 = _alsa_scan("aplay")
    AUDIO_DEVS.update({"in": ins, "out": outs, "time": time.time(), "err": e1 or e2})
    return ins, outs


def audio_choice_pairs(kind):
    """[(value, label)] for the microphone / loudspeaker selection. A saved device that is not plugged in stays selectable."""
    pairs = [("", "– " + tr("none") + " –"), ("default", tr("System default"))]
    pairs += [(d["id"], d["name"]) for d in AUDIO_DEVS[kind]]
    if kind == "out":
        pairs += [("bt:" + d["mac"], "Bluetooth: " + d["name"]) for d in BT["devices"] if d["paired"] and d["audio"]]
    cur = CFG["audio_in" if kind == "in" else "audio_out"]
    if cur and cur not in [p[0] for p in pairs]:
        pairs.append((cur, ("Bluetooth " + cur[3:]) if cur.startswith("bt:") else cur.replace("plughw:CARD=", "").split(",")[0] + " (" + tr("not connected") + ")"))
    return pairs


def sound_choice_pairs():
    names = {"siren": "Siren (rising and falling)", "two-tone": "Two-tone horn", "beeps": "Fast beeps", "horn": "Horn",
             "whistle": "High whistle (animals)", "bangs": "Bangs / claps (animals)"}
    return [(k, tr(names[k])) for k in SOUND_KINDS] + [("file:" + f, "♪ " + f) for f in own_sounds()]


def _db(rms):
    return round(20.0 * math.log10(max(rms, 1.0) / 32768.0), 1)


