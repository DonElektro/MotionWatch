#@ MoveEye – Teil 639zzzf: «Eigenes Protokoll (2 Töne)» des Besitzers im Morse-Modus (senden über den Lautsprecher, lesen über das Mikrofon, Schlüssel nur für den Administrator) und die Seite «📻 Handy-Funkgerät» (/morse/funk, dieselbe Seite als PWA in funk/). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Besitzer (14.11.2026): seine Seite «Morse-Funk» (Handy-Lautsprecher / Mikrofon über ein Handfunkgerät) soll mit MoveEye reden.
# Sein Protokoll, Bit für Bit gleich wie seine Seite:
#   * Ton A (800 Hz) = Daten: kurz = Punkt, lang = Strich (Längen wie Morse, 1 Einheit = 1.2 s / WPM).
#   * Ton B (1400 Hz): kurz (1 Einheit) = Zeichenende, lang (3 Einheiten) = Start / Ende der Nachricht.
#   * 39 Zeichen FUNK_ALPHA = A-Z 0-9 Leerzeichen . ?   (Leerzeichen hat den Code «..--»; die übrigen = Morse).
#   * Zeitplan (seine Funktion transmit): B lang, 3 Pause; je Zeichen: Elemente mit 1 Pause, 1 Pause, B kurz, 2 Pause;
#     am Ende 1 Pause, B lang.
#   * Schlüssel (freiwillig): Schlüsselstrom = SHA-256(Schlüssel + "|" + Block 0, 1, …), Bytes < 234 -> Byte mod 39, 4096 Werte;
#     Zeichen i einer Nachricht (ab 0, jede Nachricht neu) wird um Wert i verschoben. Das VERSCHLEIERT nur (jede Nachricht hat
#     denselben Strom) - keine starke Verschlüsselung; im Amateurfunk sind verschlüsselte Übertragungen verboten.
#   * Später (nicht jetzt, Besitzer): echte Verschlüsselung. Platz dafür, ohne das jetzige Protokoll zu brechen: eine Nachricht,
#     deren ERSTES Zeichen den Code FUNK_VERSION_CODE («.-.-», kommt in den 39 Zeichen nicht vor) hat, ist ein neueres Format -
#     seine Seite zeigt dann «□» und Unsinn (kein Absturz), MoveEye sagt «neueres Format» statt Unsinn zu zeigen.
# Der Empfänger ist seine Funktion makeDecoder (Goertzel ±40 Hz, Hysterese, Tempo aus dem Signal) nach Python übertragen
# (FunkRx) - gleiche Regeln, gleiche Zeiten; dazu die Regeln von MoveEye für fremde Eingabe (nur mit Start-Ton, Länge, «EEEE»).
# Prüfung der Verträglichkeit: werkzeuge/funk_test.py lässt SEINEN Decoder (zwischen /*DECODER-START*/ und /*DECODER-END*/,
# unverändert in funk/index.html, Prüfsumme) in node gegen MoveEyes Ton laufen und MoveEye gegen den Ton seiner Funktion
# transmit - mit und ohne Schlüssel, direkt und über den nachgebauten Funkkanal (docs/Funk_Protokoll.md).

# ==== FUNK-KERN ANFANG ====
FUNK_ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .?"
FUNK_NA = len(FUNK_ALPHA)
FUNK_VERSION_CODE = ".-.-"              # reserved: first sign of a message in a newer format (later: real encryption)
# the Morse table of his page (not the one of MoveEye: no umlauts, other punctuation) - for his «Morse» mode
FUNK_MORSE = {"A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
              "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
              "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--", "Z": "--..", "0": "-----", "1": ".----", "2": "..---",
              "3": "...--", "4": "....-", "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.", ".": ".-.-.-",
              ",": "--..--", "?": "..--..", "/": "-..-.", "-": "-....-", "=": "-...-", ":": "---...", "@": ".--.-.", "+": ".-.-.",
              "!": "-.-.--", "(": "-.--.", ")": "-.--.-", "'": ".----.", '"': ".-..-."}
FUNK_MORSE_REV = {v: k for k, v in FUNK_MORSE.items()}
FUNK_PCODE = {c: ("..--" if c == " " else FUNK_MORSE[c]) for c in FUNK_ALPHA}
FUNK_PREV = {v: FUNK_ALPHA.index(c) for c, v in FUNK_PCODE.items()}
FUNK_KS_LEN = 4096
FUNK_UNKNOWN = "□"


def funk_norm(s):
    """his normText: upper case, Ä Ö Ü -> AE OE UE, ß -> SS, white space -> one space"""
    t = str(s or "").upper().replace("Ä", "AE").replace("Ö", "OE").replace("Ü", "UE").replace("ß", "SS")
    return re.sub(r"\s+", " ", t)


def funk_keystream(key, n=FUNK_KS_LEN):
    """his makeKeystream: SHA-256(key + "|" + block), bytes < 234 -> byte mod 39. No key -> None"""
    if not key:
        return None
    import hashlib
    out, block = [], 0
    while len(out) < n:
        for b in hashlib.sha256((str(key) + "|" + str(block)).encode("utf-8")).digest():
            if b < 234:
                out.append(b % FUNK_NA)
            if len(out) >= n:
                break
        block += 1
    return out


def funk_prep(text, ks=None, mode="prot"):
    """his prepTx -> (plain, codes). prot: only the 39 characters, shifted by the key stream from position 0; morse: his table"""
    t = funk_norm(text)
    if mode == "prot":
        plain = "".join(c for c in t if c in FUNK_ALPHA)
        out = [FUNK_ALPHA[(FUNK_ALPHA.index(c) + (ks[i % len(ks)] if ks else 0)) % FUNK_NA] for i, c in enumerate(plain)]
        return plain, [FUNK_PCODE[c] for c in out]
    plain = "".join(c for c in t if c == " " or c in FUNK_MORSE).strip()
    return plain, [" " if c == " " else FUNK_MORSE[c] for c in plain]


def funk_timeline(codes, wpm, fa=800.0, fb=1400.0, mode="prot"):
    """his transmit as a timeline [(seconds, frequency or 0)] (without his 0.15 s lead)"""
    u = 1.2 / float(wpm)
    tl = []

    def beep(f, d):
        tl.append((d, float(f)))

    def gap(n):
        if tl and tl[-1][1] == 0:
            tl[-1] = (tl[-1][0] + n * u, 0)
        else:
            tl.append((n * u, 0))
    if mode == "prot":
        beep(fb, 3 * u); gap(3)
        for code in codes:
            for j, el in enumerate(code):
                if j:
                    gap(1)
                beep(fa, 3 * u if el == "-" else u)
            gap(1); beep(fb, u); gap(2)
        gap(1); beep(fb, 3 * u)
    else:
        for i, code in enumerate(codes):
            if code == " ":
                gap(7); continue
            if i and codes[i - 1] != " ":
                gap(3)
            for j, el in enumerate(code):
                if j:
                    gap(1)
                beep(fa, 3 * u if el == "-" else u)
    return tl


class FunkRx:
    """his makeDecoder in Python: feed(samples) with the sound (any rate, int16 or float scale); frames of about 10.7 ms (512 at
    48 kHz, 171 at 16 kHz), Goertzel at the tone ±40 Hz, hysteresis, the same state machine and times. cfg(): {"mode": "prot" |
    "morse", "fA", "fB", "wpm", "auto", "sens"}. on_message(text, info) for every finished message. strict=True (MoveEye): a
    message counts only after the long start tone, not «EEEE», at most max_len characters; the reserved first sign -> newer."""

    def __init__(self, rate=16000, cfg=None, on_message=None, strict=True, max_len=240, scale=None):
        self.rate = int(rate)
        self.N = max(64, int(round(512 * self.rate / 48000.0)))
        self.dt = self.N / float(self.rate) * 1000.0
        self.cfg = cfg or (lambda: {"mode": "prot", "fA": 800, "fB": 1400, "wpm": 12, "auto": True, "sens": 10})
        self.on_message = on_message
        self.strict, self.max_len, self.scale = strict, int(max_len), scale
        i = np.arange(self.N)
        self.win = (0.5 - 0.5 * np.cos(2 * np.pi * i / (self.N - 1))).astype(np.float64)
        self._ex = {}
        self.ks = None
        self.reset()

    def reset(self):
        c = self.cfg()
        self.tail = np.zeros(0, np.float64)
        self.TA = {"floor": None, "on": False}; self.TB = {"floor": None, "on": False}
        self.state = 0; self.cand = 0; self.candN = 0; self.dur = 0.0
        self.unit = 1200.0 / float(c["wpm"]); self.sym = ""; self.live = ""; self.ended = True; self.pos = 0
        self.fired = {"c": False, "w": False, "m": False}; self.level = 0.0; self.recent = []
        self.started = False; self.newer = False
        self.stats = {"frames": 0, "msgs": 0, "dropped": 0, "a": False, "b": False}

    def _exp(self, f):
        e = self._ex.get(f)
        if e is None:
            e = self._ex[f] = np.exp(-2j * np.pi * f * np.arange(self.N) / self.rate)
        return e

    def _tone(self, x, f, E):
        P = max(float(abs(np.dot(x, self._exp(f + df))) ** 2) for df in (-40.0, 0.0, 40.0))   # = his Goertzel power
        return 10.0 * math.log10(P + 1e-12), 3.0 * P / (self.N * E + 1e-20)

    @staticmethod
    def _hyst(t, db, frac, sens):
        if t["floor"] is None:
            t["floor"] = db
        if t["on"]:
            if not (db > t["floor"] + sens - 5 and frac > 0.07):
                t["on"] = False
        elif db > t["floor"] + sens and frac > 0.15:
            t["on"] = True
        if db < t["floor"]:
            t["floor"] += (db - t["floor"]) * 0.2
        elif not t["on"]:
            t["floor"] += (db - t["floor"]) * 0.01
        return t["on"]

    def _classify(self, ms):
        c = self.cfg()
        if not c.get("auto"):
            self.unit = 1200.0 / float(c["wpm"]); return "-" if ms >= 2 * self.unit else "."
        self.recent.append(ms); del self.recent[:-16]
        mn, mx = min(self.recent), max(self.recent)
        if len(self.recent) >= 4 and mx / mn >= 2:
            c1, c2 = mn, mx
            for _ in range(5):
                th = (c1 + c2) / 2.0
                lo = [r for r in self.recent if r < th]; hi = [r for r in self.recent if r >= th]
                if lo:
                    c1 = sum(lo) / len(lo)
                if hi:
                    c2 = sum(hi) / len(hi)
            u = (c1 + c2 / 3.0) / 2.0
            self.unit = min(300.0, max(30.0, self.unit * 0.5 + u * 0.5))
            return "-" if ms >= (c1 + c2) / 2.0 else "."
        dash = ms >= 2 * self.unit
        self.unit = min(300.0, max(30.0, self.unit * 0.85 + (ms / 3.0 if dash else ms) * 0.15))
        return "-" if dash else "."

    def _new_text(self):
        if self.ended:
            self.live = ""; self.pos = 0; self.ended = False; self.started = False; self.newer = False

    def _flush(self):
        if not self.sym:
            return
        c = self.cfg(); self._new_text()
        if c["mode"] == "prot":
            if self.pos == 0 and self.sym == FUNK_VERSION_CODE:
                self.newer = True
            idx = FUNK_PREV.get(self.sym)
            if idx is None:
                self.live += FUNK_UNKNOWN
            else:
                k = self.ks[self.pos % len(self.ks)] if self.ks else 0
                self.live += FUNK_ALPHA[(idx - k + FUNK_NA * 2) % FUNK_NA]
            self.pos += 1
        else:
            self.live += FUNK_MORSE_REV.get(self.sym, FUNK_UNKNOWN)
        self.sym = ""
        if self.strict and len(self.live) >= self.max_len:
            self._end()                                   # (MoveEye) no endless message

    def _end(self):
        self._flush()
        t = self.live.strip()
        if t and not self.ended:
            self._deliver(t)
        self.ended = True

    def _deliver(self, t):
        c = self.cfg()
        info = {"mode": c["mode"], "wpm": round(1200.0 / self.unit, 1), "key": bool(self.ks) and c["mode"] == "prot",
                "started": self.started, "newer": self.newer}
        if self.strict:
            plain = t.replace(" ", "")
            if c["mode"] == "prot" and not self.started:
                self.stats["dropped"] += 1; return            # no long start tone: a beep nearby, not the protocol
            if not self.newer and len(plain) >= 4 and len(set(plain)) == 1:
                self.stats["dropped"] += 1; return            # «EEEE» / «TTTT»: even beeping, no text
            if not self.newer and len(plain) >= 6 and sum(ch in "ET" for ch in plain) >= 0.6 * len(plain):
                self.stats["dropped"] += 1; return            # mostly the one-element signs: tones at random (text has ~25 % E / T)
        self.stats["msgs"] += 1
        if self.on_message is not None:
            self.on_message(t, info)

    def _end_seg(self, s, ms):
        if ms < 12:
            return
        c = self.cfg()
        if s == 1:
            self.sym = (self.sym + self._classify(ms))[-8:]
        elif s == 2 and c["mode"] == "prot":
            if ms < 2 * self.unit:
                self._flush()
            elif not self.ended and (self.live or self.sym):
                self._end()
            else:
                self.live = ""; self.pos = 0; self.ended = False; self.sym = ""; self.started = True; self.newer = False

    def _silence(self, ms):
        c = self.cfg(); u = self.unit
        if c["mode"] == "morse":
            if ms > 2.5 * u and self.sym:
                self._flush()
            if ms > 5 * u and not self.fired["w"] and self.live and not self.ended and not self.live.endswith(" "):
                self.live += " "; self.fired["w"] = True
        elif ms > 4 * u and self.sym:
            self._flush()
        if ms > 8000 and not self.fired["m"] and not self.ended and (self.live.strip() or self.sym):
            self._end(); self.fired["m"] = True

    def frame(self, x, muted=False):
        c = self.cfg()
        y = x * self.win
        E = float(np.dot(y, y))
        self.level = math.sqrt(E / self.N)
        raw = 0
        if not muted:
            adb, afr = self._tone(y, float(c["fA"]), E); bdb, bfr = self._tone(y, float(c["fB"]), E)
            oa = self._hyst(self.TA, adb, afr, c["sens"]); ob = self._hyst(self.TB, bdb, bfr, c["sens"])
            raw = 1 if (oa and (not ob or adb >= bdb)) else (2 if ob else 0)
            self.stats["a"], self.stats["b"] = oa, ob
        dt = self.dt
        if raw != self.state:
            if raw == self.cand:
                self.candN += 1
            else:
                self.cand = raw; self.candN = 1
            if self.candN >= 2:
                self._end_seg(self.state, self.dur - dt); self.state = raw; self.dur = 2 * dt
                self.fired = {"c": False, "w": False, "m": False}; self.candN = 0
            else:
                self.dur += dt
        else:
            self.candN = 0; self.dur += dt
        if self.state == 0:
            self._silence(self.dur)
        self.stats["frames"] += 1

    def feed(self, pcm, muted=False):
        """the next samples (any number). int16 scale is made -1..1 (his page works with -1..1)"""
        x = np.asarray(pcm, np.float64).ravel()
        if x.size > self.rate * 610:
            return                                          # (the microphone brings 0.1 s at a time: this is no sound)
        if x.size and not np.all(np.isfinite(x)):
            return
        sc = self.scale if self.scale is not None else (1.0 / 32768.0 if np.asarray(pcm).dtype.kind in "iu" else 1.0)
        x = np.concatenate((self.tail, x * sc)) if self.tail.size else x * sc
        n = x.size // self.N
        for i in range(n):
            self.frame(x[i * self.N:(i + 1) * self.N], muted)
        self.tail = x[n * self.N:]
# ==== FUNK-KERN ENDE ====


# ---- the page «Handy-Funkgerät»: his page (decoder, prepTx, transmit unchanged), five languages, way back, PWA for GitHub Pages ----
FUNK_PAGE = r"""<!DOCTYPE html>
<!-- Handy-Funkgerät (MoveEye) – beruht auf der Seite «Morse-Funk», die für den Besitzer von MoveEye gemacht wurde (sein Protokoll
     mit zwei Tönen, sein Decoder unverändert zwischen DECODER-START und DECODER-END, seine Funktionen prepTx und transmit).
     Eine Datei, keine Anfragen nach aussen; der Schlüssel bleibt nur im Speicher dieses Handys. Quelle: quelle/639zzzf_funk.py -->
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Funk">
<meta name="theme-color" content="#111418">
<meta name="referrer" content="no-referrer">
<!--PWA--><link rel="manifest" href="manifest.webmanifest"><link rel="apple-touch-icon" href="apple-touch-icon.png"><link rel="icon" href="icon-192.png"><!--/PWA-->
<title>Handy-Funkgerät</title>
<style>
:root{--bg:#111418;--card:#191D23;--line:#2A3038;--text:#EDEFF2;--muted:#9AA3AD;--a:#F2A33A;--b:#5AA9FF;--acc:#5AA9FF}
*{box-sizing:border-box}
html,body{margin:0;min-height:100%;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"SF Pro Text",Inter,"DejaVu Sans",system-ui,sans-serif;-webkit-tap-highlight-color:transparent}
body{display:flex;justify-content:center}
.app{width:100%;max-width:480px;min-height:100vh;display:flex;flex-direction:column;gap:16px;padding:calc(env(safe-area-inset-top) + 14px) 16px calc(env(safe-area-inset-bottom) + 20px)}
.back{display:inline-flex;align-items:center;min-height:40px;color:var(--acc);font-weight:600;text-decoration:none;align-self:flex-start}
[hidden]{display:none!important}
.ttl{margin:0;font-size:20px;display:flex;align-items:center;gap:8px}
.top{display:flex;justify-content:space-between;align-items:center;gap:8px}
.pill{min-height:44px;padding:0 14px;border-radius:22px;border:1px solid var(--line);background:var(--card);color:var(--text);font:500 15px inherit;font-family:inherit;display:flex;align-items:center;gap:8px;min-width:0}
.pill span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pill.on{border-color:#5a3d12}
.icon{width:44px;height:44px;flex:0 0 44px;border-radius:22px;border:1px solid var(--line);background:var(--card);display:flex;align-items:center;justify-content:center;padding:0}
.label{font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;overflow-wrap:anywhere}
.rx{flex:1;display:flex;flex-direction:column;gap:10px;min-height:140px}
#live{font-size:30px;font-weight:700;line-height:1.2;overflow-wrap:anywhere;min-height:40px}
#live.empty{color:#6A737D;font-weight:500;font-size:22px}
#sym{font-family:ui-monospace,Menlo,"DejaVu Sans Mono",monospace;font-size:20px;color:var(--a);letter-spacing:3px;min-height:26px}
.track{background:var(--card);border-radius:14px;padding:12px;display:flex;flex-direction:column;gap:8px}
.track canvas{width:100%;height:36px;display:block}
.meta{display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px 10px;font-size:13px;color:var(--muted)}
.dot{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:4px;vertical-align:-1px}
.big{align-self:center;width:180px;height:180px;border-radius:50%;border:6px solid #3A2A12;background:var(--a);color:#111418;font:700 22px inherit;font-family:inherit;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px}
.big.live{background:#111418;color:var(--a);border-color:var(--a);animation:pulse 1.6s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(242,163,58,.45)}70%{box-shadow:0 0 0 22px rgba(242,163,58,0)}100%{box-shadow:0 0 0 0 rgba(242,163,58,0)}}
.bottom{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.btn{min-height:52px;border-radius:14px;border:1px solid var(--line);background:var(--card);color:var(--text);font:600 16px inherit;font-family:inherit;padding:6px 10px}
.btn.primary{background:var(--a);border-color:var(--a);color:#111418}
.btn.danger{color:#FF8A80}
#msg{font-size:14px;color:#FF8A80;min-height:0;overflow-wrap:anywhere}
#msg a{color:var(--acc)}
.sheet{position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;align-items:flex-end;justify-content:center;z-index:5}
.sheet.open{display:flex}
.panel{width:100%;max-width:480px;max-height:92%;overflow:auto;background:#161A20;border-radius:20px 20px 0 0;padding:20px 16px calc(env(safe-area-inset-bottom) + 20px);display:flex;flex-direction:column;gap:14px}
.panel h2{margin:0;font-size:22px;display:flex;justify-content:space-between;align-items:center;gap:8px}
.close{background:none;border:0;color:var(--acc);font:600 16px inherit;font-family:inherit;min-height:44px;padding:0 4px}
label.f{display:flex;flex-direction:column;gap:6px;font-size:14px;color:var(--muted)}
input[type=text],input[type=password],input[type=number],textarea,select{width:100%;background:var(--bg);border:1px solid var(--line);border-radius:12px;color:var(--text);font:16px inherit;font-family:inherit;padding:12px}
textarea{min-height:110px;resize:vertical}
.row{display:flex;justify-content:space-between;align-items:center;gap:10px;font-size:16px;min-height:44px}
.row input[type=checkbox]{width:24px;height:24px;flex:0 0 24px;accent-color:var(--a)}
input[type=range]{width:100%;accent-color:var(--a)}
.seg{display:grid;grid-template-columns:1fr 1fr;gap:6px;background:var(--bg);padding:4px;border-radius:12px}
.seg button{min-height:42px;border:0;border-radius:9px;background:none;color:var(--muted);font:600 15px inherit;font-family:inherit}
.seg button.sel{background:var(--card);color:var(--text)}
.hint{font-size:13px;color:var(--muted);line-height:1.4;overflow-wrap:anywhere}
.warn{font-size:13px;line-height:1.4;border:1px solid #6b5313;border-radius:10px;padding:8px 10px;color:#F2D58A}
.hist{display:flex;flex-direction:column}
.hist div{padding:12px 0;border-bottom:1px solid var(--line);display:flex;flex-direction:column;gap:4px}
.hist span{overflow-wrap:anywhere}
.hist small{color:var(--muted)}
.prev{font-family:ui-monospace,Menlo,"DejaVu Sans Mono",monospace;font-size:14px;color:var(--a);overflow-wrap:anywhere}
</style>
</head>
<body>
<div class="app">
  <a class="back" id="mw-back" href="/morse" hidden>‹ Morse</a>
  <h1 class="ttl"><span aria-hidden="true">📻</span><span id="ttl">Handy-Funkgerät</span></h1>
  <div class="top">
    <button class="pill" id="keyBtn" aria-label="Schlüssel einstellen">
      <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3"/></svg>
      <span id="keyTxt">Kein Schlüssel</span>
    </button>
    <button class="icon" id="setBtn" aria-label="Einstellungen">
      <svg aria-hidden="true" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#EDEFF2" stroke-width="2" stroke-linecap="round"><path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/></svg>
    </button>
  </div>

  <div class="rx">
    <div class="label" id="modeLbl">Empfangen · Eigenes Protokoll</div>
    <div id="live" class="empty">Tippe auf «Hören»</div>
    <div id="sym"></div>
  </div>

  <div class="track">
    <canvas id="cv" aria-hidden="true"></canvas>
    <div class="meta">
      <span><span class="dot" style="background:var(--a)"></span>A <span id="fAl">800</span> Hz &nbsp;<span class="dot" style="background:var(--b)"></span>B <span id="fBl">1400</span> Hz</span>
      <span id="wpm">– WPM</span>
    </div>
  </div>
  <div id="msg" role="status"></div>

  <button class="big" id="listen">
    <svg aria-hidden="true" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>
    <span id="listenTxt">Hören</span>
  </button>

  <div class="bottom">
    <button class="btn" id="histBtn">Verlauf</button>
    <button class="btn" id="sendBtn">Senden</button>
  </div>
  <div class="hint" id="install" hidden></div>
</div>

<!-- Senden -->
<div class="sheet" id="shSend"><div class="panel">
  <h2><span data-t="send">Senden</span> <button class="close" data-close data-t="close">Schliessen</button></h2>
  <label class="f"><span data-t="text">Text</span><textarea id="txIn" placeholder="z. B. Treffen um 15 Uhr"></textarea></label>
  <div class="hint"><span data-t="sentAs">Wird gesendet als:</span> <span class="prev" id="txPrev">–</span></div>
  <div class="hint" data-t="hold">Handy-Lautsprecher ans Mikrofon des Funkgeräts halten, dann Sendetaste drücken.</div>
  <button class="btn primary" id="txGo">Senden</button>
  <button class="btn" id="txStop" data-t="cancel">Abbrechen</button>
</div></div>

<!-- Schlüssel -->
<div class="sheet" id="shKey"><div class="panel">
  <h2><span data-t="key">Schlüssel</span> <button class="close" data-close data-t="close">Schliessen</button></h2>
  <label class="f"><span data-t="keySame">Schlüssel (gleich wie beim Gegenüber)</span><input type="password" id="keyIn" autocomplete="off" autocapitalize="off" spellcheck="false"></label>
  <div class="row"><span data-t="remember">Auf diesem Gerät merken</span> <input type="checkbox" id="keyRem"></div>
  <div class="hint" data-t="keyLocal">Der Schlüssel bleibt nur auf diesem Gerät. Ohne «merken» ist er nach dem Schliessen der App weg.</div>
  <div class="warn" data-t="keyWarn">Der Schlüssel verschleiert nur.</div>
  <div class="warn" data-t="legal">Amateurfunk: keine Verschlüsselung.</div>
  <button class="btn primary" id="keySave" data-t="apply">Übernehmen</button>
  <button class="btn danger" id="keyDel" data-t="keyDel">Schlüssel löschen</button>
</div></div>

<!-- Einstellungen -->
<div class="sheet" id="shSet"><div class="panel">
  <h2><span data-t="settings">Einstellungen</span> <button class="close" data-close data-t="close">Schliessen</button></h2>
  <label class="f"><span data-t="lang">Sprache</span><select id="sL"><option value="de">Deutsch</option><option value="en">English</option><option value="fr">Français</option><option value="it">Italiano</option><option value="rm">Rumantsch</option></select></label>
  <div class="seg" role="group" aria-label="Modus">
    <button id="mProt" data-t="prot">Eigenes Protokoll</button>
    <button id="mMorse" data-t="morse">Morse</button>
  </div>
  <label class="f"><span data-t="toneA">Ton A – Daten (Hz)</span><input type="number" id="sFA" inputmode="numeric" min="300" max="3000"></label>
  <label class="f"><span data-t="toneB">Ton B – Steuerung (Hz)</span><input type="number" id="sFB" inputmode="numeric" min="300" max="3000"></label>
  <label class="f"><span><span data-t="speed">Tempo</span>: <span id="sWv"></span> WPM</span><input type="range" id="sW" min="5" max="35" step="1"></label>
  <div class="row"><span data-t="auto">Tempo automatisch erkennen</span> <input type="checkbox" id="sAuto"></div>
  <label class="f"><span><span data-t="sens">Empfindlichkeit</span>: <span id="sSv"></span></span><input type="range" id="sS" min="3" max="15" step="1"></label>
  <label class="f"><span data-t="vol">Sende-Lautstärke</span><input type="range" id="sV" min="0.1" max="1" step="0.05"></label>
  <div class="hint" data-t="help">Protokoll</div>
  <div class="hint" data-t="mwMorse">MoveEye</div>
</div></div>

<!-- Verlauf -->
<div class="sheet" id="shHist"><div class="panel">
  <h2><span data-t="hist">Verlauf</span> <button class="close" data-close data-t="close">Schliessen</button></h2>
  <div class="hist" id="histList"></div>
  <button class="btn danger" id="histClr" data-t="histClr">Verlauf löschen</button>
</div></div>

<script>
/*MWFUNK*/
/*DECODER-START*/
const MORSE={A:'.-',B:'-...',C:'-.-.',D:'-..',E:'.',F:'..-.',G:'--.',H:'....',I:'..',J:'.---',K:'-.-',L:'.-..',M:'--',N:'-.',O:'---',P:'.--.',Q:'--.-',R:'.-.',S:'...',T:'-',U:'..-',V:'...-',W:'.--',X:'-..-',Y:'-.--',Z:'--..',
'0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....','6':'-....','7':'--...','8':'---..','9':'----.',
'.':'.-.-.-',',':'--..--','?':'..--..','/':'-..-.','-':'-....-','=':'-...-',':':'---...','@':'.--.-.','+':'.-.-.','!':'-.-.--','(':'-.--.',')':'-.--.-',"'":'.----.','"':'.-..-.'};
const MORSE_REV={};for(const k in MORSE)MORSE_REV[MORSE[k]]=k;
// Eigenes Protokoll: 39 Zeichen, Leerzeichen hat einen eigenen Code
const ALPHA='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .?';
const PCODE={};for(const c of ALPHA)PCODE[c]=(c===' ')?'..--':MORSE[c];
const PREV={};for(const c of ALPHA)PREV[PCODE[c]]=ALPHA.indexOf(c);
const NA=ALPHA.length;

function normText(s){return s.toUpperCase().replace(/Ä/g,'AE').replace(/Ö/g,'OE').replace(/Ü/g,'UE').replace(/ß/g,'SS').replace(/\s+/g,' ');}

async function makeKeystream(key,len){
  if(!key)return null;
  const out=[];let block=0;const enc=new TextEncoder();
  while(out.length<len){
    const h=new Uint8Array(await crypto.subtle.digest('SHA-256',enc.encode(key+'|'+block++)));
    for(const b of h){if(b<234)out.push(b%NA);if(out.length>=len)break;}
  }
  return out;
}

function makeDecoder(opt){
  // opt: {sr, N, getCfg(), onUpdate(d), onMessage(text,mode)}
  const N=opt.N,sr=opt.sr,dt=N/sr*1000;
  const win=new Float32Array(N);for(let i=0;i<N;i++)win[i]=0.5-0.5*Math.cos(2*Math.PI*i/(N-1));
  const wb=new Float32Array(N);
  const T={A:{floor:null,on:false},B:{floor:null,on:false}};
  const d={state:0,cand:0,candN:0,dur:0,unit:1200/opt.getCfg().wpm,sym:'',live:'',ended:true,pos:0,fired:{c:false,w:false,m:false},level:0,track:[],ks:null};
  function goertzel(x,f){const k=2*Math.cos(2*Math.PI*f/sr);let s1=0,s2=0;for(let i=0;i<N;i++){const s0=x[i]+k*s1-s2;s2=s1;s1=s0;}return s1*s1+s2*s2-k*s1*s2;}
  function tone(x,f,E){let P=0;for(const df of [-40,0,40])P=Math.max(P,goertzel(x,f+df));return {db:10*Math.log10(P+1e-12),frac:3*P/(N*E+1e-20)};}
  function hyst(t,m,sens){
    if(t.floor===null)t.floor=m.db;
    if(t.on){ if(!(m.db>t.floor+sens-5&&m.frac>0.07))t.on=false; }
    else { if(m.db>t.floor+sens&&m.frac>0.15)t.on=true; }
    if(m.db<t.floor)t.floor+=(m.db-t.floor)*0.2; else if(!t.on)t.floor+=(m.db-t.floor)*0.01;
    return t.on;
  }
  const recent=[];
  function classify(ms){
    const cfg=opt.getCfg();
    if(!cfg.auto){d.unit=1200/cfg.wpm;return ms>=2*d.unit?'-':'.';}
    recent.push(ms);if(recent.length>16)recent.shift();
    const mn=Math.min(...recent),mx=Math.max(...recent);
    if(recent.length>=4&&mx/mn>=2){
      // zwei Gruppen (kurz/lang) bilden
      let c1=mn,c2=mx;
      for(let it=0;it<5;it++){let s1=0,n1=0,s2=0,n2=0;const th=(c1+c2)/2;for(const r of recent){if(r<th){s1+=r;n1++;}else{s2+=r;n2++;}}if(n1)c1=s1/n1;if(n2)c2=s2/n2;}
      const u=(c1+c2/3)/2;d.unit=Math.min(300,Math.max(30,d.unit*0.5+u*0.5));
      return ms>=(c1+c2)/2?'-':'.';
    }
    const dash=ms>=2*d.unit;
    d.unit=Math.min(300,Math.max(30,d.unit*0.85+(dash?ms/3:ms)*0.15));
    return dash?'-':'.';
  }
  function newText(){ if(d.ended){d.live='';d.pos=0;d.ended=false;} }
  function flushChar(){
    if(!d.sym)return;
    const cfg=opt.getCfg();newText();
    if(cfg.mode==='prot'){
      const idx=PREV[d.sym];
      if(idx===undefined)d.live+='□';
      else{const k=d.ks?d.ks[d.pos%d.ks.length]:0;d.live+=ALPHA[(idx-k+NA*2)%NA];}
      d.pos++;
    }else d.live+=MORSE_REV[d.sym]||'□';
    d.sym='';
  }
  function endMessage(){
    flushChar();
    const t=d.live.trim();
    if(t&&!d.ended)opt.onMessage(t,opt.getCfg().mode);
    d.ended=true;
  }
  function endSeg(s,ms){
    if(ms<12)return;
    const cfg=opt.getCfg();
    if(s===1){ d.sym+=classify(ms); if(d.sym.length>8)d.sym=d.sym.slice(-8); }
    else if(s===2&&cfg.mode==='prot'){
      const long=ms>=2*d.unit;
      if(!long)flushChar();
      else if(!d.ended&&(d.live||d.sym))endMessage();
      else {d.live='';d.pos=0;d.ended=false;d.sym='';}
    }
  }
  function silence(ms){
    const cfg=opt.getCfg(),u=d.unit;
    if(cfg.mode==='morse'){
      if(ms>2.5*u&&d.sym)flushChar();
      if(ms>5*u&&!d.fired.w&&d.live&&!d.ended&&!d.live.endsWith(' ')){d.live+=' ';d.fired.w=true;}
    }else if(ms>4*u&&d.sym)flushChar();
    if(ms>8000&&!d.fired.m&&!d.ended&&(d.live.trim()||d.sym)){endMessage();d.fired.m=true;}
  }
  d.frame=function(x,muted){
    const cfg=opt.getCfg();
    let E=0;for(let i=0;i<N;i++){const y=x[i]*win[i];wb[i]=y;E+=y*y;}
    d.level=Math.sqrt(E/N);
    let raw=0;
    if(!muted){
      const a=tone(wb,cfg.fA,E),b=tone(wb,cfg.fB,E);
      const oa=hyst(T.A,a,cfg.sens),ob=hyst(T.B,b,cfg.sens);
      raw=oa&&(!ob||a.db>=b.db)?1:(ob?2:0);
    }
    d.track.push(raw);if(d.track.length>Math.round(5000/dt))d.track.shift();
    if(raw!==d.state){
      if(raw===d.cand)d.candN++;else{d.cand=raw;d.candN=1;}
      if(d.candN>=2){endSeg(d.state,d.dur-dt);d.state=raw;d.dur=2*dt;d.fired={c:false,w:false,m:false};d.candN=0;}
      else d.dur+=dt;
    }else{d.candN=0;d.dur+=dt;}
    if(d.state===0)silence(d.dur);
    opt.onUpdate(d);
  };
  d.reset=function(){d.sym='';d.live='';d.ended=true;d.pos=0;T.A.floor=T.B.floor=null;T.A.on=T.B.on=false;};
  return d;
}
/*DECODER-END*/

// ---------- Sprache (MoveEye: fünf Sprachen) ----------
const TXT={
de:{title:'Handy-Funkgerät',back:'‹ Morse-Modus',keyAria:'Schlüssel einstellen',noKey:'Kein Schlüssel',keyOn:'Schlüssel aktiv',morseNoKey:'Morse · ohne Schlüssel',settings:'Einstellungen',recv:'Empfangen',prot:'Eigenes Protokoll',morse:'Morse',tap:'Tippe auf «Hören»',wait:'Warte auf Signal …',listen:'Hören',stop:'Stopp',hist:'Verlauf',send:'Senden',close:'Schliessen',text:'Text',ph:'z. B. Treffen um 15 Uhr',sentAs:'Wird gesendet als:',hold:'Handy-Lautsprecher ans Mikrofon des Funkgeräts halten, dann Sendetaste drücken.',cancel:'Abbrechen',key:'Schlüssel',keySame:'Schlüssel (gleich wie beim Gegenüber)',remember:'Auf diesem Gerät merken',keyLocal:'Der Schlüssel bleibt nur auf diesem Gerät. Ohne «merken» ist er nach dem Schliessen der App weg.',keyWarn:'Der Schlüssel verschleiert nur: jede Nachricht verschiebt die Zeichen mit derselben Folge. Das ist keine starke Verschlüsselung – wer mehrere Nachrichten hört, kann sie entschlüsseln.',legal:'Im Amateurfunk ist Verschlüsselung verboten (ITU-Vollzugsordnung Funk Nr. 25.2A; BAKOM: digitale Übertragungen nur unverschlüsselt). Mit Schlüssel nie über Amateurfunk senden; für andere Funkgeräte (z. B. PMR446) die Regeln des BAKOM beachten.',apply:'Übernehmen',keyDel:'Schlüssel löschen',lang:'Sprache',toneA:'Ton A – Daten (Hz)',toneB:'Ton B – Steuerung (Hz)',speed:'Tempo',auto:'Tempo automatisch erkennen',sens:'Empfindlichkeit',vol:'Sende-Lautstärke',help:'Protokoll: Ton A kurz = Punkt, lang = Strich. Ton B kurz = Zeichenende, lang = Start/Ende der Nachricht. Mehr Empfindlichkeit erkennt leise Töne, reagiert aber eher auf Rauschen.',mwMorse:'Morse von MoveEye kommt mit 660 Hz: für «Morse» hier Ton A auf 660 stellen. Das eigene Protokoll von MoveEye nutzt dieselben Töne wie diese Seite.',histClr:'Verlauf löschen',nothing:'Noch nichts empfangen.',hProt:'Protokoll',hMorse:'Morse',withKey:'mit Schlüssel',sending:'Sende …',micErr:'Kein Zugriff aufs Mikrofon. In Safari erlauben (aA › Website-Einstellungen › Mikrofon). Fehler:',insecure:'Das Mikrofon geht nur auf einer sicheren Seite (https).',openSecure:'Sichere Seite öffnen',cert:'Der Browser warnt einmal, dass dem Zertifikat nicht vertraut wird: MoveEye hat es selbst gemacht. «Erweitert» → «Weiter» wählen (iPhone: «Details einblenden» → «diese Website besuchen»).',install:'iPhone: Teilen → «Zum Home-Bildschirm». Nach dem ersten Laden geht die Seite auch ohne Internet.'},
en:{title:'Phone radio',back:'‹ Morse mode',keyAria:'Set the key',noKey:'No key',keyOn:'Key active',morseNoKey:'Morse · without key',settings:'Settings',recv:'Receiving',prot:'Own protocol',morse:'Morse',tap:'Tap «Listen»',wait:'Waiting for a signal …',listen:'Listen',stop:'Stop',hist:'History',send:'Send',close:'Close',text:'Text',ph:'e.g. Meet at 3 pm',sentAs:'Sent as:',hold:'Hold the phone loudspeaker to the microphone of the radio, then press the talk button.',cancel:'Cancel',key:'Key',keySame:'Key (the same as the other side)',remember:'Remember on this device',keyLocal:'The key stays on this device only. Without «remember» it is gone when the app is closed.',keyWarn:'The key only obscures: every message shifts the characters with the same sequence. This is no strong encryption – whoever hears several messages can decode them.',legal:'Encryption is forbidden in amateur radio (ITU Radio Regulations No. 25.2A; OFCOM: digital transmissions only unencrypted). Never send with a key over amateur radio; for other radios (e.g. PMR446) follow the rules of OFCOM (BAKOM).',apply:'Apply',keyDel:'Delete the key',lang:'Language',toneA:'Tone A – data (Hz)',toneB:'Tone B – control (Hz)',speed:'Speed',auto:'Detect the speed by itself',sens:'Sensitivity',vol:'Sending volume',help:'Protocol: tone A short = dot, long = dash. Tone B short = end of a character, long = start / end of the message. More sensitivity hears quiet tones but reacts more to noise.',mwMorse:'Morse from MoveEye comes at 660 Hz: for «Morse» set tone A to 660 here. The own protocol of MoveEye uses the same tones as this page.',histClr:'Delete the history',nothing:'Nothing received yet.',hProt:'Protocol',hMorse:'Morse',withKey:'with key',sending:'Sending …',micErr:'No access to the microphone. Allow it in Safari (aA › Website Settings › Microphone). Error:',insecure:'The microphone only works on a secure page (https).',openSecure:'Open the secure page',cert:'The browser will warn once that the certificate is not trusted: MoveEye made it itself. Choose «Advanced» → «Continue» (iPhone: «Show details» → «visit this website»).',install:'iPhone: Share → «Add to Home Screen». After the first load the page also works without internet.'},
fr:{title:'Radio du téléphone',back:'‹ Mode morse',keyAria:'Régler la clé',noKey:'Pas de clé',keyOn:'Clé active',morseNoKey:'Morse · sans clé',settings:'Réglages',recv:'Réception',prot:'Protocole propre',morse:'Morse',tap:'Touchez «Écouter»',wait:'En attente d’un signal …',listen:'Écouter',stop:'Arrêt',hist:'Historique',send:'Envoyer',close:'Fermer',text:'Texte',ph:'p. ex. Rendez-vous à 15 h',sentAs:'Envoyé comme :',hold:'Tenez le haut-parleur du téléphone contre le microphone de la radio, puis appuyez sur la touche d’émission.',cancel:'Annuler',key:'Clé',keySame:'Clé (la même que de l’autre côté)',remember:'Mémoriser sur cet appareil',keyLocal:'La clé reste uniquement sur cet appareil. Sans «mémoriser», elle disparaît à la fermeture de l’app.',keyWarn:'La clé ne fait que masquer : chaque message décale les caractères avec la même suite. Ce n’est pas un chiffrement fort – qui entend plusieurs messages peut les décoder.',legal:'Le chiffrement est interdit en radioamateur (Règlement des radiocommunications de l’UIT n° 25.2A ; OFCOM : transmissions numériques uniquement non chiffrées). Ne jamais émettre avec une clé en radioamateur ; pour d’autres radios (p. ex. PMR446), respecter les règles de l’OFCOM.',apply:'Appliquer',keyDel:'Supprimer la clé',lang:'Langue',toneA:'Son A – données (Hz)',toneB:'Son B – commande (Hz)',speed:'Vitesse',auto:'Détecter la vitesse automatiquement',sens:'Sensibilité',vol:'Volume d’émission',help:'Protocole : son A court = point, long = trait. Son B court = fin d’un caractère, long = début / fin du message. Plus de sensibilité capte les sons faibles mais réagit plus au bruit.',mwMorse:'Le morse de MoveEye arrive à 660 Hz : pour «Morse», réglez ici le son A sur 660. Le protocole propre de MoveEye utilise les mêmes sons que cette page.',histClr:'Effacer l’historique',nothing:'Encore rien reçu.',hProt:'Protocole',hMorse:'Morse',withKey:'avec clé',sending:'Envoi …',micErr:'Pas d’accès au microphone. L’autoriser dans Safari (aA › Réglages du site web › Microphone). Erreur :',insecure:'Le microphone ne fonctionne que sur une page sécurisée (https).',openSecure:'Ouvrir la page sécurisée',cert:'Le navigateur avertit une fois que le certificat n’est pas fiable : MoveEye l’a créé lui-même. Choisir «Paramètres avancés» → «Continuer» (iPhone : «Afficher les détails» → «visiter ce site web»).',install:'iPhone : Partager → «Sur l’écran d’accueil». Après le premier chargement, la page fonctionne aussi sans internet.'},
it:{title:'Radio del telefono',back:'‹ Modalità Morse',keyAria:'Impostare la chiave',noKey:'Nessuna chiave',keyOn:'Chiave attiva',morseNoKey:'Morse · senza chiave',settings:'Impostazioni',recv:'Ricezione',prot:'Protocollo proprio',morse:'Morse',tap:'Tocca «Ascolta»',wait:'In attesa di un segnale …',listen:'Ascolta',stop:'Stop',hist:'Cronologia',send:'Invia',close:'Chiudi',text:'Testo',ph:'p. es. Ritrovo alle 15',sentAs:'Inviato come:',hold:'Tieni l’altoparlante del telefono vicino al microfono della radio, poi premi il tasto di trasmissione.',cancel:'Annulla',key:'Chiave',keySame:'Chiave (la stessa dell’altra parte)',remember:'Ricordare su questo apparecchio',keyLocal:'La chiave resta solo su questo apparecchio. Senza «ricordare» sparisce chiudendo l’app.',keyWarn:'La chiave nasconde soltanto: ogni messaggio sposta i caratteri con la stessa sequenza. Non è una cifratura forte – chi ascolta più messaggi può decifrarli.',legal:'Nel radioamatorismo la cifratura è vietata (Regolamento delle radiocomunicazioni UIT n. 25.2A; UFCOM: trasmissioni digitali solo non cifrate). Non trasmettere mai con una chiave via radioamatori; per altre radio (p. es. PMR446) rispettare le regole dell’UFCOM.',apply:'Applica',keyDel:'Cancellare la chiave',lang:'Lingua',toneA:'Suono A – dati (Hz)',toneB:'Suono B – controllo (Hz)',speed:'Velocità',auto:'Riconoscere la velocità da sé',sens:'Sensibilità',vol:'Volume di trasmissione',help:'Protocollo: suono A corto = punto, lungo = linea. Suono B corto = fine del carattere, lungo = inizio / fine del messaggio. Più sensibilità sente i suoni deboli ma reagisce di più al rumore.',mwMorse:'Il Morse di MoveEye arriva a 660 Hz: per «Morse» qui impostare il suono A su 660. Il protocollo proprio di MoveEye usa gli stessi suoni di questa pagina.',histClr:'Cancellare la cronologia',nothing:'Ancora niente ricevuto.',hProt:'Protocollo',hMorse:'Morse',withKey:'con chiave',sending:'Invio …',micErr:'Nessun accesso al microfono. Permetterlo in Safari (aA › Impostazioni sito web › Microfono). Errore:',insecure:'Il microfono funziona solo su una pagina sicura (https).',openSecure:'Aprire la pagina sicura',cert:'Il browser avvisa una volta che il certificato non è attendibile: l’ha creato MoveEye stesso. Scegliere «Avanzate» → «Procedi» (iPhone: «Mostra dettagli» → «visita questo sito web»).',install:'iPhone: Condividi → «Aggiungi alla schermata Home». Dopo il primo caricamento la pagina funziona anche senza internet.'},
rm:{title:'Radio dal telefonin',back:'‹ Modus da morse',keyAria:'Definir la clav',noKey:'Nagina clav',keyOn:'Clav activa',morseNoKey:'Morse · senza clav',settings:'Parameters',recv:'Retschaiver',prot:'Agen protocol',morse:'Morse',tap:'Tutga «Tadlar»',wait:'Spetga in signal …',listen:'Tadlar',stop:'Stop',hist:'Cronologia',send:'Trametter',close:'Serrar',text:'Text',ph:'p. ex. Sentupada a las 15',sentAs:'Vegn tramess sco:',hold:'Tegnair il autpledader dal telefonin vi dal microfon dal radio, lura smatgar la tasta da trametter.',cancel:'Interrumper',key:'Clav',keySame:'Clav (la medema sco tar l’auter)',remember:'Memorisar sin quest apparat',keyLocal:'La clav resta mo sin quest apparat. Senza «memorisar» è ella davent suenter avair serrà l’app.',keyWarn:'La clav zuppenta mo: mintga messadi spustescha ils caracters cun la medema successiun. Quai n’è nagin criptadi ferm – tgi che auda plirs messadis, als po decodar.',legal:'En il radioamatur è il criptadi scumandà (Reglament da radiocommunicaziun UIT nr. 25.2A; UFCOM: transmissiuns digitalas mo betg criptadas). Mai trametter cun clav via radioamatur; per auters radios (p. ex. PMR446) observar las reglas da l’UFCOM.',apply:'Applitgar',keyDel:'Stizzar la clav',lang:'Lingua',toneA:'Tun A – datas (Hz)',toneB:'Tun B – controlla (Hz)',speed:'Tempo',auto:'Enconuscher il tempo sez',sens:'Sensibilitad',vol:'Volumen da trametter',help:'Protocol: tun A curt = punct, lung = lingia. Tun B curt = fin dal caracter, lung = cumenzament / fin dal messadi. Dapli sensibilitad auda tuns flaivels, ma reagescha pli fitg sin canera.',mwMorse:'Il morse da MoveEye vegn cun 660 Hz: per «Morse» qua metter il tun A sin 660. L’agen protocol da MoveEye dovra ils medems tuns sco questa pagina.',histClr:'Stizzar la cronologia',nothing:'Anc nagut retschavì.',hProt:'Protocol',hMorse:'Morse',withKey:'cun clav',sending:'Trametta …',micErr:'Nagin access al microfon. Permetter en Safari (aA › Parameters da la website › Microfon). Errur:',insecure:'Il microfon funcziuna mo sin ina pagina segira (https).',openSecure:'Avrir la pagina segira',cert:'Il navigatur avertescha ina giada ch’il certificat na saja betg fidà: MoveEye l’ha fatg sez. Tscherner «Avanzà» → «Cuntinuar» (iPhone: «Mussar detagls» → «visitar questa website»).',install:'iPhone: Parter → «Agiuntar al visur da partenza». Suenter l’emprima chargiada funcziuna la pagina er senza internet.'}};
const MW=window.MW_FUNK||null;
const LOC={de:'de-CH',en:'en-GB',fr:'fr-CH',it:'it-CH',rm:'rm-CH'};
function pickLang(){
  let l=null;try{l=JSON.parse(localStorage.getItem('morsefunk.lang'));}catch(e){}
  if(!l&&MW&&MW.lang)l=MW.lang;
  if(!l){const n=(navigator.language||'de').slice(0,2).toLowerCase();l=TXT[n]?n:'de';}
  return TXT[l]?l:'de';
}
let LG=pickLang();
const T=k=>(TXT[LG]&&TXT[LG][k])||TXT.de[k]||k;
function applyLang(){
  document.documentElement.lang=LG;document.title=(MW?'MoveEye – ':'')+T('title');
  document.querySelectorAll('[data-t]').forEach(e=>{e.textContent=T(e.getAttribute('data-t'));});
  $('ttl').textContent=T('title');$('keyBtn').setAttribute('aria-label',T('keyAria'));$('setBtn').setAttribute('aria-label',T('settings'));
  $('txIn').placeholder=T('ph');$('txGo').textContent=T('send');$('histBtn').textContent=T('hist');$('sendBtn').textContent=T('send');
  $('listenTxt').textContent=listening?T('stop'):T('listen');$('sL').value=LG;
  if(MW){$('mw-back').hidden=false;$('mw-back').href=MW.back||'/morse';$('mw-back').textContent=T('back');}   // (id mw-back: MoveEye adds no «✕ Zurück» on top)
  else{const i=$('install');i.hidden=!(location.protocol==='https:');i.textContent=T('install');}
  renderTop();dirty=true;
}

// ---------- App ----------
const $=id=>document.getElementById(id);
const store={get(k,def){try{const v=localStorage.getItem('morsefunk.'+k);return v===null?def:JSON.parse(v);}catch(e){return def;}},
  set(k,v){try{localStorage.setItem('morsefunk.'+k,JSON.stringify(v));}catch(e){}},del(k){try{localStorage.removeItem('morsefunk.'+k);}catch(e){}}};
const cfg=Object.assign({mode:'prot',fA:800,fB:1400,wpm:12,auto:true,sens:10,vol:0.8},store.get('cfg',{}));
let key=store.get('key','')||'';let ks=null;
let history=store.get('hist',[]);
let ctx=null,stream=null,proc=null,src=null,dec=null,listening=false,sendingUntil=0,sendNodes=[];
let dirty=false;

function saveCfg(){store.set('cfg',cfg);}
async function applyKey(){ks=await makeKeystream(key,4096);if(dec)dec.ks=ks;renderTop();}

function renderTop(){
  const k=$('keyBtn');
  if(cfg.mode==='morse'){$('keyTxt').textContent=T('morseNoKey');k.classList.remove('on');k.style.color='var(--muted)';}
  else if(key){$('keyTxt').textContent=T('keyOn');k.classList.add('on');k.style.color='var(--a)';}
  else{$('keyTxt').textContent=T('noKey');k.classList.remove('on');k.style.color='var(--text)';}
  $('modeLbl').textContent=T('recv')+' · '+(cfg.mode==='prot'?T('prot'):T('morse'));
  $('fAl').textContent=cfg.fA;$('fBl').textContent=cfg.fB;
}

function render(){
  dirty=false;
  const L=$('live');
  if(dec&&dec.live){L.textContent=dec.live;L.classList.remove('empty');}
  else{L.textContent=listening?T('wait'):T('tap');L.classList.add('empty');}
  if(dec){
    $('sym').textContent=dec.sym.replace(/\./g,'·').replace(/-/g,'–');
    $('wpm').textContent=Math.round(1200/dec.unit)+' WPM'+(cfg.auto?' (auto)':'');
  }
  drawTrack();
}
function drawTrack(){
  const c=$('cv'),r=c.getBoundingClientRect(),dpr=window.devicePixelRatio||1;
  if(c.width!==Math.round(r.width*dpr)){c.width=Math.round(r.width*dpr);c.height=Math.round(r.height*dpr);}
  const g=c.getContext('2d');g.clearRect(0,0,c.width,c.height);
  g.fillStyle='#232830';g.fillRect(0,c.height/2-1,c.width,2);
  if(!dec)return;
  const tr=dec.track,n=Math.max(tr.length,1),max=Math.round(5000/(512/(ctx?ctx.sampleRate:48000)*1000));
  const w=c.width/max,off=c.width-n*w;
  for(let i=0;i<tr.length;i++){if(!tr[i])continue;g.fillStyle=tr[i]===1?'#F2A33A':'#5AA9FF';g.fillRect(off+i*w,c.height*0.2,Math.ceil(w),c.height*0.6);}
  const lv=Math.min(1,dec.level*20);g.fillStyle='#3A4048';g.fillRect(0,c.height-3*dpr,c.width*lv,3*dpr);
}
function loop(){if(dirty||listening)render();requestAnimationFrame(loop);}

function showMsg(t){$('msg').textContent=t||'';}
function insecureMsg(){
  // the microphone needs https: MoveEye has a second, secure address (its own certificate - the browser asks once)
  const m=$('msg');m.textContent=T('insecure')+' ';
  if(MW&&MW.https_port){const a=document.createElement('a');a.href='https://'+location.hostname+':'+MW.https_port+location.pathname;a.textContent=T('openSecure');
    m.append(a,document.createElement('br'),document.createTextNode(T('cert')));}
}

async function ensureCtx(){
  if(!ctx){const AC=window.AudioContext||window.webkitAudioContext;ctx=new AC();}
  if(ctx.state==='suspended')await ctx.resume();
}

async function startListen(){
  showMsg('');
  if(!window.isSecureContext||!navigator.mediaDevices){insecureMsg();return;}
  try{
    await ensureCtx();
    stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:false,noiseSuppression:false,autoGainControl:false}});
  }catch(e){showMsg(T('micErr')+' '+(e.name||e));return;}
  const prevLive=dec?{live:dec.live,ended:true}:null;
  dec=makeDecoder({sr:ctx.sampleRate,N:512,getCfg:()=>cfg,onUpdate:()=>{dirty=true;},onMessage:addHistory});
  dec.ks=ks;if(prevLive&&prevLive.live){dec.live=prevLive.live;}
  src=ctx.createMediaStreamSource(stream);
  proc=ctx.createScriptProcessor(512,1,1);
  const sink=ctx.createGain();sink.gain.value=0;
  proc.onaudioprocess=e=>dec.frame(e.inputBuffer.getChannelData(0),ctx.currentTime<sendingUntil);
  src.connect(proc);proc.connect(sink);sink.connect(ctx.destination);
  listening=true;$('listen').classList.add('live');$('listenTxt').textContent=T('stop');
}
function stopListen(){
  if(dec&&!dec.ended&&(dec.live.trim()||dec.sym)){dec.frame(new Float32Array(512),true);/* flush */}
  if(dec){const t=dec.live.trim();if(!dec.ended&&t){addHistory(t,cfg.mode);dec.ended=true;}}
  try{proc&&proc.disconnect();src&&src.disconnect();}catch(e){}
  if(stream)stream.getTracks().forEach(t=>t.stop());
  stream=proc=src=null;listening=false;
  $('listen').classList.remove('live');$('listenTxt').textContent=T('listen');dirty=true;
}

function addHistory(text,mode){
  history.unshift({t:Date.now(),text,mode,key:mode==='prot'&&!!key});history=history.slice(0,200);store.set('hist',history);
}
function renderHist(){
  const L=$('histList');L.textContent='';
  if(!history.length){const d=document.createElement('div'),s=document.createElement('small');s.textContent=T('nothing');d.append(s);L.append(d);return;}
  for(const h of history){
    const d=document.createElement('div');const s=document.createElement('span');s.textContent=h.text;
    const m=document.createElement('small');m.textContent=new Date(h.t).toLocaleString(LOC[LG]||'de-CH')+' · '+(h.mode==='prot'?T('hProt'):T('hMorse'))+(h.key?' · 🔑 '+T('withKey'):'');
    d.append(s,m);L.append(d);
  }
}

// ---------- Senden ----------
function prepTx(text){
  const t=normText(text);
  if(cfg.mode==='prot'){
    const plain=[...t].filter(c=>ALPHA.includes(c)).join('');
    const out=[];for(let i=0;i<plain.length;i++){const k=ks?ks[i%ks.length]:0;out.push(ALPHA[(ALPHA.indexOf(plain[i])+k)%NA]);}
    return {plain,codes:out.map(c=>PCODE[c])};
  }
  const plain=[...t].filter(c=>c===' '||MORSE[c]).join('').trim();
  return {plain,codes:[...plain].map(c=>c===' '?' ':MORSE[c])};
}
function updPrev(){
  const p=prepTx($('txIn').value);
  $('txPrev').textContent=p.plain?(p.plain+(cfg.mode==='prot'&&key?'  (🔑 '+T('withKey')+')':'')):'–';
}
async function transmit(){
  const p=prepTx($('txIn').value);if(!p.plain)return;
  await ensureCtx();
  const u=1.2/cfg.wpm;let t=ctx.currentTime+0.15;
  const beep=(f,len)=>{const o=ctx.createOscillator(),g=ctx.createGain();o.frequency.value=f;o.type='sine';
    g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(cfg.vol,t+0.005);g.gain.setValueAtTime(cfg.vol,t+len-0.005);g.gain.linearRampToValueAtTime(0,t+len);
    o.connect(g);g.connect(ctx.destination);o.start(t);o.stop(t+len+0.02);sendNodes.push(o);t+=len;};
  const gap=n=>{t+=n*u;};
  if(cfg.mode==='prot'){
    beep(cfg.fB,3*u);gap(3);
    for(const code of p.codes){for(let j=0;j<code.length;j++){if(j)gap(1);beep(cfg.fA,code[j]==='-'?3*u:u);}gap(1);beep(cfg.fB,u);gap(2);}
    gap(1);beep(cfg.fB,3*u);
  }else{
    p.codes.forEach((code,i)=>{if(code===' '){gap(7);return;}if(i&&p.codes[i-1]!==' ')gap(3);for(let j=0;j<code.length;j++){if(j)gap(1);beep(cfg.fA,code[j]==='-'?3*u:u);}});
  }
  sendingUntil=t+0.3;
  const total=t-ctx.currentTime;$('txGo').textContent='Sende … '+total.toFixed(1)+' s';$('txGo').disabled=true;
  setTimeout(()=>{$('txGo').textContent='Senden';$('txGo').disabled=false;sendNodes=[];},total*1000+300);
}
async function transmitUI(){
  // his transmit stays as it is (it writes «Sende …» / «Senden»): afterwards the button in the language of the page
  await transmit();
  const left=ctx?Math.max(0,sendingUntil-0.3-ctx.currentTime):0;
  if($('txGo').disabled)$('txGo').textContent=T('sending')+' '+left.toFixed(1)+' s';
  setTimeout(()=>{if(!$('txGo').disabled)$('txGo').textContent=T('send');},left*1000+400);
}
function stopTx(){for(const o of sendNodes){try{o.stop();}catch(e){}}sendNodes=[];sendingUntil=0;$('txGo').textContent=T('send');$('txGo').disabled=false;}

// ---------- UI-Verdrahtung ----------
function open(id){$(id).classList.add('open');}
document.querySelectorAll('.sheet').forEach(s=>{s.addEventListener('click',e=>{if(e.target===s||e.target.hasAttribute('data-close'))s.classList.remove('open');});});
$('listen').onclick=()=>listening?stopListen():startListen();
$('sendBtn').onclick=()=>{updPrev();open('shSend');};
$('txIn').oninput=updPrev;$('txGo').onclick=transmitUI;$('txStop').onclick=stopTx;
$('keyBtn').onclick=()=>{$('keyIn').value=key;$('keyRem').checked=!!store.get('key','');open('shKey');};
$('keySave').onclick=async()=>{key=$('keyIn').value;if($('keyRem').checked&&key)store.set('key',key);else store.del('key');await applyKey();$('shKey').classList.remove('open');};
$('keyDel').onclick=async()=>{key='';store.del('key');$('keyIn').value='';await applyKey();$('shKey').classList.remove('open');};
$('histBtn').onclick=()=>{renderHist();open('shHist');};
$('histClr').onclick=()=>{history=[];store.set('hist',history);renderHist();};
function syncSet(){
  $('mProt').classList.toggle('sel',cfg.mode==='prot');$('mMorse').classList.toggle('sel',cfg.mode==='morse');
  $('sFA').value=cfg.fA;$('sFB').value=cfg.fB;$('sW').value=cfg.wpm;$('sWv').textContent=cfg.wpm;$('sAuto').checked=cfg.auto;
  $('sS').value=21-cfg.sens;$('sSv').textContent=(21-cfg.sens)+' / 15';$('sV').value=cfg.vol;renderTop();
}
$('setBtn').onclick=()=>{syncSet();open('shSet');};
$('mProt').onclick=()=>{cfg.mode='prot';saveCfg();syncSet();};
$('mMorse').onclick=()=>{cfg.mode='morse';saveCfg();syncSet();};
$('sFA').onchange=e=>{const v=+e.target.value;if(v>=300&&v<=3000)cfg.fA=v;saveCfg();syncSet();};
$('sFB').onchange=e=>{const v=+e.target.value;if(v>=300&&v<=3000)cfg.fB=v;saveCfg();syncSet();};
$('sW').oninput=e=>{cfg.wpm=+e.target.value;if(dec)dec.unit=1200/cfg.wpm;saveCfg();syncSet();};
$('sAuto').onchange=e=>{cfg.auto=e.target.checked;saveCfg();syncSet();};
$('sS').oninput=e=>{cfg.sens=21-(+e.target.value);saveCfg();syncSet();};
$('sV').oninput=e=>{cfg.vol=+e.target.value;saveCfg();};
$('sL').onchange=e=>{LG=TXT[e.target.value]?e.target.value:'de';store.set('lang',LG);applyLang();};

applyLang();applyKey();dirty=true;loop();
if(!window.isSecureContext)insecureMsg();
if(!MW&&'serviceWorker' in navigator&&location.protocol==='https:'){navigator.serviceWorker.register('sw.js').catch(()=>{});}
</script>
</body>
</html>
"""


# ---- in MoveEye: settings (the key is a secret: never in «prefs», the log, the history, a push, app keys, «own settings») --------
FUNK_DEF = {"morse_fmt": "morse", "morse_fa": 800, "morse_fb": 1400, "morse_key": ""}
for _k, _v in FUNK_DEF.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)
USER_SETTINGS_DENY.add("morse_key")
APPKEY_DENY_KEYS.add("morse_key")
APPKEY_DENY_PATHS.update({"/morse/funk", "/morse/funk.html"})
FUNK_WPM = (5, 25)                     # his page 5 - 35 WPM; the loudspeaker of MoveEye at most 25 (MORSE_OUT_HZ «beep»)
FUNK_KEY_MAX = 200
FUNK_PAGES_URL = "https://donelektro.github.io/MotionWatch/funk/"     # the same page for a phone without MoveEye (GitHub Pages)
FUNK = {"rx": None, "t": 0.0, "ks": None, "ks_of": None, "own": False}


def funk_ks():
    """the key stream of the saved key (made once per key)"""
    k = str(CFG.get("morse_key") or "")
    h = hash(k)
    if FUNK["ks_of"] != h:
        FUNK["ks"] = funk_keystream(k) if k else None; FUNK["ks_of"] = h
    return FUNK["ks"]


def funk_cfg():
    return {"mode": "prot", "fA": int(CFG.get("morse_fa") or 800), "fB": int(CFG.get("morse_fb") or 1400),
            "wpm": max(FUNK_WPM[0], min(FUNK_WPM[1], int(CFG.get("morse_wpm") or 12))), "auto": True, "sens": 10}


def funk_on():
    return CFG.get("morse_fmt") == "prot"


_morse_plan_funk = morse_plan


# wraps: morse_plan (639zzz)
def morse_plan(text, outs, wpm, fw=0, lang=None):              # + 639zzzf: «own protocol» - only with the loudspeaker, light / IR stay Morse
    ids = [str(x) for x in (outs or [])] if isinstance(outs, (list, tuple)) else []
    if not funk_on() or "beep" not in ids:
        return _morse_plan_funk(text, outs, wpm, fw, lang)
    if len(str(text or "")) > MORSE_TEXT_MAX:
        return None, "the text is too long"
    ks = funk_ks()
    plain, codes = funk_prep(text, ks)
    norm = funk_norm(text)
    skipped = list(dict.fromkeys(c for c in norm if c not in FUNK_ALPHA))[:40]
    if not plain.strip():
        return None, "no character of this text is in the protocol (A-Z, 0-9, space . ?)"
    avail = {o["id"]: o for o in morse_outputs(lang)}
    if not (avail.get("beep") or {}).get("ok"):
        return None, "an output you chose is not connected"
    try:
        asked = float(wpm)
    except (TypeError, ValueError):
        return None, "not a number"
    if asked != asked:
        return None, "not a number"
    eff = max(FUNK_WPM[0], min(FUNK_WPM[1], asked, float(avail["beep"]["wpm"])))
    tl = funk_timeline(codes, eff, int(CFG.get("morse_fa") or 800), int(CFG.get("morse_fb") or 1400))
    secs = sum(d for d, _f in tl)
    if secs > MORSE_TX_MAX_S:
        return None, "this takes too long - a shorter text or faster"
    other = [avail[o]["name"] for o in ids if o != "beep" and o in avail]
    return {"signs": [], "shown": plain, "skipped": skipped, "wpm": eff, "asked": asked, "slow": avail["beep"]["name"] if eff < asked else "",
            "fw": 0, "tl": tl, "secs": round(secs, 1), "outs": ["beep"], "relays": {}, "flash_hz": 0.0, "note": False, "vis": False,
            "fmt": "prot", "key": bool(ks), "ignored": other}, ""


_morse_beep_chunks_funk = morse_beep_chunks


# wraps: morse_beep_chunks (639zzz)
def morse_beep_chunks(tl, rate, lead=0.6):                      # + 639zzzf: a timeline with a frequency per tone (two tones A / B)
    if all(on is True or not on for _d, on in tl):
        yield from _morse_beep_chunks_funk(tl, rate, lead); return
    yield np.zeros(int(lead * rate), np.float32)
    ramp = max(1, int(0.005 * rate))
    for d, on in tl:
        n = max(1, int(round(d * rate)))
        if not on:
            yield np.zeros(n, np.float32); continue
        f = MORSE_BEEP_HZ if on is True else float(on)
        y = np.sin(2.0 * np.pi * f * np.arange(n) / rate).astype(np.float32)
        r = min(ramp, n // 2)
        if r:
            y[:r] *= np.linspace(0, 1, r, dtype=np.float32); y[-r:] *= np.linspace(1, 0, r, dtype=np.float32)
        yield y


def funk_rx_message(text, info):
    """a message of the protocol is complete -> the Morse list (like every received text: never a command)"""
    if info.get("newer"):
        text = MORSE_UNKNOWN                                  # a newer format (later: real encryption) - no nonsense on the page
    else:
        text = text.replace(FUNK_UNKNOWN, MORSE_UNKNOWN)
    morse_rx_text(text, "sound", {"wpm": info.get("wpm"), "fmt": "prot", "key": info.get("key"), "newer": info.get("newer")})


def _funk_audio_chunk(self, data):                            # + 639zzzf: the microphone to the protocol (only in the mode, «by sound» on)
    if not funk_on():
        return _morse_audio_chunk(self, data)                 # Morse: as before (639zzz step 2)
    _morse_audio_chunk_250(self, data)
    if not (MORSE["until"] and CFG.get("morse_rx_sound")):
        return
    try:
        if not morse_on():
            return
        if FUNK["rx"] is None:
            FUNK["rx"] = FunkRx(16000, funk_cfg, funk_rx_message, strict=True, max_len=MORSE_RX_TEXT_MAX)
        rx = FUNK["rx"]
        rx.ks = funk_ks()
        now = time.time()
        own = now < self.mute_until or SOUND["playing"] or now - MORSE["own_sound"] < MORSE_OWN_S
        FUNK["own"] = bool(own)
        rx.feed(np.frombuffer(data, dtype="<i2"), muted=own)  # (his page: while it sends, the frames count as silence)
        FUNK["t"] = now
    except Exception as e:
        if time.time() - MORSE["err_t"] > 60:
            MORSE["err_t"] = time.time(); log_event("sys", f"Morse protocol: {type(e).__name__}: {e}"[:160])
        try:
            FUNK["rx"].reset()
        except Exception:
            pass


# wraps: AudioMonitor._chunk (639zzz wrapper)
AudioMonitor._chunk = _funk_audio_chunk

_morse_end_funk = morse_end


# wraps: morse_end (639zzz)
def morse_end(why="button", who=""):                            # + 639zzzf: nothing of the protocol stays after the mode
    r = _morse_end_funk(why, who)
    if FUNK["rx"] is not None and not MORSE["until"]:
        FUNK["rx"].reset()
    return r


_morse_state_funk = morse_state


# wraps: morse_state (639zzz)
def morse_state(lang=None):                                     # + 639zzzf: the format, the tones, «a key is set» (never the key)
    st = _morse_state_funk(lang)
    rx, now = FUNK["rx"], time.time()
    fresh = st["on"] and funk_on() and rx is not None and now - FUNK["t"] < 2.0
    st["funk"] = {"fmt": CFG.get("morse_fmt") or "morse", "fa": int(CFG.get("morse_fa") or 800), "fb": int(CFG.get("morse_fb") or 1400),
                  "key": bool(CFG.get("morse_key")), "wpm_min": FUNK_WPM[0], "wpm_max": FUNK_WPM[1], "run": bool(fresh), "own": bool(fresh and FUNK["own"]),
                  "live": (rx.live if fresh and not rx.ended else ""), "sym": (rx.sym if fresh else ""),
                  "wpm": round(1200.0 / rx.unit, 1) if fresh else 0, "a": bool(fresh and rx.stats.get("a")), "b": bool(fresh and rx.stats.get("b")),
                  "page": "/morse/funk", "file": "/morse/funk.html", "pages": FUNK_PAGES_URL, "https_port": STATE.get("https_port")}
    return st


_morse_do_funk = morse_do


# wraps: morse_do (639zzz)
def morse_do(d, who, role="admin", appkey=None, pin=None, pin_checked=False, lang=None):   # + 639zzzf: format, tones, key
    d = d if isinstance(d, dict) else {}
    a = str(d.get("action") or "")
    if a not in ("funk", "key"):
        return _morse_do_funk(d, who, role, appkey, pin, pin_checked, lang)
    L = norm_lang(lang or d.get("lang") or CFG.get("lang"))
    if not morse_may(role, appkey):
        return 403, {"ok": False, "error": tr("Only for the administrator", L)}

    def out(ok, err=""):
        return (200 if ok else 400), {"ok": ok, "error": tr_err(err, L) if err else None, "state": morse_state(L)}
    if a == "key":                                           # the key: only set or delete, never read back
        if d.get("clear"):
            CFG["morse_key"] = ""; save_settings()
            log_event("sys", "Morse protocol: key deleted")
            return out(True)
        k = d.get("key")
        if not isinstance(k, str) or not k or len(k) > FUNK_KEY_MAX or any(ord(c) < 32 for c in k):
            return out(False, "the key must be 1 to 200 characters")
        CFG["morse_key"] = k; save_settings()
        log_event("sys", "Morse protocol: key set")            # (never the key itself)
        return out(True)
    if "fmt" in d:
        if d["fmt"] not in ("morse", "prot"):
            return out(False, "unknown choice")
        if MORSE["tx"] is not None:
            return out(False, "a transmission is running")
        CFG["morse_fmt"] = d["fmt"]
    fa, fb = int(CFG.get("morse_fa") or 800), int(CFG.get("morse_fb") or 1400)
    try:
        if "fa" in d:
            fa = int(float(d["fa"]))
        if "fb" in d:
            fb = int(float(d["fb"]))
    except (TypeError, ValueError):
        return out(False, "not a number")
    if not (300 <= fa <= 3000 and 300 <= fb <= 3000) or abs(fa - fb) < 200:
        return out(False, "tones between 300 and 3000 Hz, at least 200 Hz apart")
    CFG["morse_fa"], CFG["morse_fb"] = fa, fb
    if FUNK["rx"] is not None:
        FUNK["rx"].reset()
    save_settings()
    return out(True)


def funk_page(variant="mw", lang=None, https_port=None):
    """the page «Handy-Funkgerät»: mw = in MoveEye (way back, its language, the secure address), pwa = GitHub Pages (manifest,
    offline), file = a file for another phone (no manifest; iPhone: no microphone for files - use the Pages address)"""
    p = FUNK_PAGE
    if variant != "pwa":
        a, e = p.find("<!--PWA-->"), p.find("<!--/PWA-->")
        if a >= 0 and e > a:
            p = p[:a] + p[e + len("<!--/PWA-->"):]
    if variant == "mw":
        mw = {"lang": norm_lang(lang or CFG.get("lang")), "back": "/morse", "https_port": https_port}
        p = p.replace("/*MWFUNK*/", "window.MW_FUNK=" + json.dumps(mw).replace("</", "<\\/") + ";", 1)
    return p


_smalltv_routes_funk = smalltv_routes


# wraps: smalltv_routes (639zzz)
def smalltv_routes(app, reply, body):                         # + 639zzzf: /morse/funk (the page), /morse/funk.html (as a file)
    _smalltv_routes_funk(app, reply, body)
    from flask import Response, request, g

    def nope():
        if not morse_may(getattr(g, "role", "admin"), getattr(g, "appkey", None), change=False):
            return reply({"ok": False, "error": tr("Only for the administrator", norm_lang(request.args.get("lang")))}, 403)
        return None

    @app.route("/morse/funk")
    def funk_page_mw():
        n = nope()
        if n is not None:
            return n
        return Response(funk_page("mw", request.args.get("lang"), STATE.get("https_port")), mimetype="text/html",
                        headers={"Cache-Control": "no-store", "Permissions-Policy": "microphone=(self)"})

    @app.route("/morse/funk.html")
    def funk_page_file():
        n = nope()
        if n is not None:
            return n
        return Response(funk_page("file"), mimetype="text/html",
                        headers={"Cache-Control": "no-store", "Content-Disposition": 'attachment; filename="Handy-Funkgeraet.html"'})


_HX_FUNK = {
    "no character of this text is in the protocol (A-Z, 0-9, space . ?)": (
        "kein Zeichen dieses Textes ist im Protokoll (A–Z, 0–9, Leerzeichen . ?)", "aucun caractère de ce texte n’est dans le protocole (A–Z, 0–9, espace . ?)",
        "nessun carattere di questo testo è nel protocollo (A–Z, 0–9, spazio . ?)", "nagin caracter da quest text è en il protocol (A–Z, 0–9, spazi . ?)"),
    "the key must be 1 to 200 characters": ("der Schlüssel muss 1 bis 200 Zeichen lang sein", "la clé doit avoir 1 à 200 caractères",
                                            "la chiave deve avere da 1 a 200 caratteri", "la clav sto avair 1 fin 200 caracters"),
    "tones between 300 and 3000 Hz, at least 200 Hz apart": ("Töne zwischen 300 und 3000 Hz, mindestens 200 Hz auseinander",
                                                              "sons entre 300 et 3000 Hz, à au moins 200 Hz l’un de l’autre",
                                                              "suoni tra 300 e 3000 Hz, ad almeno 200 Hz di distanza", "tuns tranter 300 e 3000 Hz, almain 200 Hz da distanza"),
    "decrypted with the key": ("entschlüsselt mit Schlüssel", "déchiffré avec la clé", "decifrato con la chiave", "decriptà cun la clav"),
    "Own protocol (2 tones)": ("Eigenes Protokoll (2 Töne)", "Protocole propre (2 sons)", "Protocollo proprio (2 suoni)", "Agen protocol (2 tuns)"),
    "newer format - this MoveEye cannot read it": ("neueres Format – dieses MoveEye kann es nicht lesen", "format plus récent – ce MoveEye ne peut pas le lire",
                                                   "formato più recente – questo MoveEye non può leggerlo", "format pli nov – quest MoveEye na po betg al leger"),
}
for _k, _v in _HX_FUNK.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_MORSE_DE.update({_k: DE.get(_k, _v[0]) for _k, _v in _HX_FUNK.items()})

# ---- the manual: in the section «Morse-Modus» ----------------------------------------------------------------------------------------
_HELP_FUNK = {
    "de": ('<li><b>📻 Eigenes Protokoll (2 Töne) und Handy-Funkgerät:</b> im Morse-Modus «Format» → «Eigenes Protokoll (2 Töne)»: Ton A (800 Hz) '
           'trägt Punkt und Strich, Ton B (1400 Hz) kurz = Zeichenende, lang = Start / Ende der Nachricht; 39 Zeichen (A–Z, 0–9, Leerzeichen . ?). '
           'Gesendet wird nur über den Lautsprecher (Licht und IR senden weiter Morse), gelesen über das Mikrofon («mit dem Mikrofon» an). '
           'Gleich wie die Seite «Handy-Funkgerät» (Morse-Modus → «📻 Handy-Funkgerät»; für ein Handy ohne MoveEye: '
           '<code>' + FUNK_PAGES_URL + '</code>, «Zum Home-Bildschirm», geht danach ohne Internet). Am iPhone braucht das Mikrofon die sichere '
           'Seite (https, Port + 1): einmal die Zertifikatswarnung bestätigen. <b>Schlüssel</b> (nur Administrator): verschleiert nur – jede Nachricht '
           'nutzt dieselbe Folge, keine starke Verschlüsselung. Im Amateurfunk ist Verschlüsselung verboten (ITU Nr. 25.2A, BAKOM); für PMR446 & Co. die '
           'Regeln des BAKOM beachten. Der Schlüssel steht nie im Protokoll, im Verlauf oder in einer Push; im Verlauf steht nur «entschlüsselt mit Schlüssel».</li>'),
    "en": ('<li><b>📻 Own protocol (2 tones) and phone radio:</b> in the Morse mode «Format» → «Own protocol (2 tones)»: tone A (800 Hz) carries dot '
           'and dash, tone B (1400 Hz) short = end of a character, long = start / end of the message; 39 characters (A–Z, 0–9, space . ?). It is sent only '
           'with the loudspeaker (light and IR keep sending Morse) and read with the microphone («with the microphone» on). The same as the page «Phone radio» '
           '(Morse mode → «📻 Phone radio»; for a phone without MoveEye: <code>' + FUNK_PAGES_URL + '</code>, «Add to Home Screen», then it works without '
           'internet). On an iPhone the microphone needs the secure page (https, port + 1): accept the certificate warning once. <b>Key</b> (administrator only): '
           'it only obscures - every message uses the same sequence, no strong encryption. Encryption is forbidden in amateur radio (ITU No. 25.2A, OFCOM); '
           'for PMR446 & co. follow the rules of OFCOM. The key is never in the log, the history or a push; the history only says «decrypted with the key».</li>'),
    "fr": ('<li><b>📻 Protocole propre (2 sons) et radio du téléphone :</b> mode morse «Format» → «Protocole propre (2 sons)» : son A (800 Hz) = point et '
           'trait, son B (1400 Hz) court = fin du caractère, long = début / fin ; 39 caractères. Envoyé seulement par le haut-parleur, lu par le microphone. '
           'Téléphone sans MoveEye : <code>' + FUNK_PAGES_URL + '</code>. iPhone : page sécurisée (https). <b>Clé</b> (administrateur) : ne fait que masquer, '
           'pas de chiffrement fort ; chiffrement interdit en radioamateur (UIT n° 25.2A, OFCOM). La clé n’apparaît jamais dans le journal, l’historique ou un push.</li>'),
    "it": ('<li><b>📻 Protocollo proprio (2 suoni) e radio del telefono:</b> modalità Morse «Formato» → «Protocollo proprio (2 suoni)»: suono A (800 Hz) = '
           'punto e linea, suono B (1400 Hz) corto = fine del carattere, lungo = inizio / fine; 39 caratteri. Inviato solo con l’altoparlante, letto con il '
           'microfono. Telefono senza MoveEye: <code>' + FUNK_PAGES_URL + '</code>. iPhone: pagina sicura (https). <b>Chiave</b> (amministratore): nasconde '
           'soltanto, nessuna cifratura forte; cifratura vietata nel radioamatorismo (UIT n. 25.2A, UFCOM). La chiave non appare mai nel registro, nella cronologia o in un push.</li>'),
    "rm": ('<li><b>📻 Agen protocol (2 tuns) e radio dal telefonin:</b> modus da morse «Format» → «Agen protocol (2 tuns)»: tun A (800 Hz) = punct e '
           'lingia, tun B (1400 Hz) curt = fin dal caracter, lung = cumenzament / fin; 39 caracters. Tramess mo cun il autpledader, legì cun il microfon. '
           'Telefonin senza MoveEye: <code>' + FUNK_PAGES_URL + '</code>. iPhone: pagina segira (https). <b>Clav</b> (administratur): zuppenta mo, nagin '
           'criptadi ferm; criptadi scumandà en il radioamatur (UIT nr. 25.2A, UFCOM). La clav na cumpara mai en il protocol, la cronologia u in push.</li>'),
}
for _L, _li in _HELP_FUNK.items():
    if _L in _HELP_MORSE and "</ul></section>" in _HELP_MORSE[_L]:
        _HELP_MORSE[_L] = _HELP_MORSE[_L].replace("</ul></section>", _li + "</ul></section>", 1)


def funk_selftest():
    """the protocol: table, key stream (known values), encode -> decode for every character with and without key, a newer format,
    hostile input; the page keeps his decoder; the key never in the state"""
    assert len(FUNK_ALPHA) == 39 and len(set(FUNK_PCODE.values())) == 39 and FUNK_VERSION_CODE not in FUNK_PREV, "39 different signs, the version sign free"
    ks = funk_keystream("geheim", 8)
    assert ks == funk_keystream("geheim", 8) and all(0 <= k < 39 for k in ks) and funk_keystream("") is None
    for key in ("", "geheim"):
        k_ = funk_keystream(key)
        got = []
        rx = FunkRx(16000, lambda: {"mode": "prot", "fA": 800, "fB": 1400, "wpm": 15, "auto": True, "sens": 10}, lambda t, i: got.append((t, i)))
        rx.ks = k_
        txt = "TREFFEN 15 UHR. OK? " + FUNK_ALPHA.replace(" ", "")
        _p, codes = funk_prep(txt, k_)
        y = np.concatenate([np.zeros(1600)] + [np.sin(2 * np.pi * f * np.arange(int(d * 16000)) / 16000.0) * 0.5 if f else np.zeros(int(d * 16000))
                                              for d, f in funk_timeline(codes, 15)] + [np.zeros(4000)])
        rx.feed((y * 32767).astype(np.int16))
        assert got and got[0][0] == txt.strip() and got[0][1]["key"] == bool(key) and got[0][1]["started"], (key, got)
    got = []
    rx = FunkRx(16000, None, lambda t, i: got.append((t, i)))
    rx.feed(np.random.default_rng(3).normal(0, 3000, 16000 * 5).astype(np.int16)); rx.feed(np.full(1000, np.nan))
    assert not got, "noise is no message"
    a, e = FUNK_PAGE.index("/*DECODER-START*/"), FUNK_PAGE.index("/*DECODER-END*/")
    assert "makeDecoder" in FUNK_PAGE[a:e] and "innerHTML" not in FUNK_PAGE and "http://" not in FUNK_PAGE.replace("http://www.w3.org/2000/svg", "")
    assert "window.MW_FUNK=" in funk_page("mw", "de") and "manifest" not in funk_page("file") and "manifest.webmanifest" in funk_page("pwa")
    keep = CFG.get("morse_key")
    try:
        CFG["morse_key"] = "selbsttest-geheim"
        st = json.dumps(morse_state("de"))
        assert "selbsttest-geheim" not in st and '"key": true' in st, "the key is never in the state"
    finally:
        CFG["morse_key"] = keep
    return "39 signs, key stream, every character with and without key, noise, his decoder in the page, key never in the state"


SELFTEST_EXTRA.append(("Morse: own protocol of the owner, phone radio (639zzzf)", funk_selftest))
