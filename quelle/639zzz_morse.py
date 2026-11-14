#@ MoveEye – Teil 639zzz: «Morse-Modus» – einen Text als Morsezeichen senden (Licht, Relais, IR, Status-LED, Lautsprecher) und ein blinkendes Licht im Kamerabild lesen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (12.11.2026, Schritt 1 von 2). Ab Werk aus; nichts ändert sich, bis der Administrator den Modus öffnet.
#
#  Der Modus    «Morse-Modus» läuft eine gewählte Zeit (ab Werk 10 Minuten, höchstens MORSE_MODE_MAX_MIN) und endet von selbst.
#               Solange er läuft, ist der Schutz PAUSIERT - auf demselben Weg wie beim Gehtest (415): is_armed() sagt «nein»,
#               damit gibt es keine Alarme, Pushes, Sirene, Alarm-Licht, Relais-Auslöser und keine Abschreckung. Dazu ruhen
#               die Bewegungs-Maske, die KI, der Sabotage-Wächter («abgedeckt / verdreht»), die Linsen-Prüfung und die
#               Umschaltung Tag / Nacht - ein blinkendes Licht ist keine Bewegung und keine Blendung.
#               NICHTS wird dafür in den Einstellungen umgestellt: der Zustand steht nur im Speicher (MORSE). Fällt der Strom
#               aus oder startet das Programm neu, ist der Modus einfach aus und der Schutz genau wie vorher - es gibt nichts
#               zurückzustellen, also auch nichts, das hängen bleiben kann.
#  Senden       Text -> Zeichen (morse_encode) -> Zeitplan (morse_timeline: dit = 1, dah = 3, Pausen 1 / 3 / 7 Einheiten,
#               Farnsworth wahlweise) -> die gewählten Ausgänge tasten im 50-Hz-Takt der Hardware-Schleife (080):
#                 weisses Licht / IR-Licht   über lights_tick (070) - derselbe Weg wie die SOS-Lampe (639zzt)
#                 Relais                     über Hardware._lights: der GPIO des Relais
#                 Status-LED                 über led_frame (163a)
#                 Lautsprecher               ein Ton aus dem Zeitplan gerechnet (morse_beep_samples)
#               Nach dem Ende (fertig, Stopp, Fehler, Modus-Ende, Ausschalten) wird nichts mehr überschrieben: jeder Ausgang
#               macht wieder, was er ohne Morsen machen würde. Die SOS-Lampe (639zzt) geht immer vor.
#               Tempo-Grenzen pro Ausgang (MORSE_OUT_HZ, Schaltspiele pro Sekunde; WPM = 2.4 × Hz):
#                 sichtbares Licht (weiss, Relais)   höchstens 3 Blitze / s (wie Disco-Licht und Abschreckung, 070) = 7 WPM
#                 mechanisches Relais (ab Werk)      2 / s = 4 WPM (Kontakte, Lebensdauer); als «Halbleiter-Relais» 3 / s
#                 Status-LED (klein)                 4.5 / s = 10 WPM (unter 5 Hz), Hinweis ab 3 / s
#                 IR-Licht (unsichtbar)              8.3 / s = 20 WPM (der 50-Hz-Takt taktet nicht genauer)
#                 Lautsprecher                       25 WPM
#               Gesendet wird mit dem langsamsten gewählten Ausgang - es gibt keinen Weg, einen Ausgang schneller zu tasten.
#  Empfangen    MorseRx: sucht im verkleinerten Helligkeitsbild (160 Felder breit, Maximum pro Feld) Stellen, die in den
#               letzten Sekunden hell UND dunkel waren (nicht die hellste Stelle), verfolgt sie, schwellt mit Hysterese,
#               schätzt die Länge eines dit aus dem Signal und entschlüsselt mit Wortpausen (morse_decode). Gleichmässiges
#               Blinken (Blinker eines Autos) ist kein Text. Gemessen mit werkzeuge/morse_test.py --messen.
#               Der empfangene Text ist FREMDE EINGABE: nur Zeichen aus der Morse-Tabelle, gekürzt, nie als Befehl gelesen,
#               nie als HTML ausgegeben (Live-Bild: in die Pixel gezeichnet; Seite: textContent).
#  Schritt 2    (nicht gebaut) Ton über das Mikrofon und IR zwischen zwei MoveEye: eine weitere Quelle ruft dieselbe
#               Entschlüsselung (MorseKey.edge + morse_decode) und meldet über morse_rx_text(text, quelle) - siehe MORSE_SOURCES.
# Texte in 5 Sprachen: _HX_MORSE. Seite /morse (nur Administrator), /api/morse. Test: werkzeuge/morse_test.py.
# ----------------------------------------------------------------------------

# ==== MORSE-KERN ANFANG (läuft auch allein: werkzeuge/morse_test.py --quelle; braucht nur math, time, numpy, cv2) ====
MORSE_CODE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-",
    "L": ".-..", "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-", "U": "..-", "V": "...-",
    "W": ".--", "X": "-..-", "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.", "!": "-.-.--", "/": "-..-.", "(": "-.--.", ")": "-.--.-", "&": ".-...",
    ":": "---...", ";": "-.-.-.", "=": "-...-", "+": ".-.-.", "-": "-....-", "_": "..--.-", '"': ".-..-.", "$": "...-..-", "@": ".--.-.",
    "Ä": ".-.-", "Ö": "---.", "Ü": "..--", "CH": "----", "ß": "...--..", "É": "..-..", "È": ".-..-", "À": ".--.-", "Ñ": "--.--",
}
# prosigns: sent as ONE sign (no pause inside). <AR> = «+», <BT> = «=», <KN> = «(» are the same signs as those characters.
MORSE_PROSIGNS = {"SOS": "...---...", "AR": ".-.-.", "SK": "...-.-", "KA": "-.-.-", "BT": "-...-", "HH": "........", "SN": "...-.", "KN": "-.--."}
MORSE_DECODE = {v: k for k, v in MORSE_CODE.items()}
for _k, _v in MORSE_PROSIGNS.items():
    MORSE_DECODE.setdefault(_v, "<" + _k + ">")
MORSE_UNKNOWN = "#"                    # a sign that is in no table (never a Morse character itself)
MORSE_TEXT_MAX = 200                   # characters of a text to send
MORSE_RX_TEXT_MAX = 240                # characters of a received message
MORSE_WPM_MIN, MORSE_WPM_MAX = 3, 25


def morse_upper(text):
    """upper case for Morse: «ß» stays (Python makes «SS» of it), the accents of the table stay, the others lose theirs"""
    out = []
    for c in str(text or ""):
        if c == "ß":
            out.append(c); continue
        u = c.upper()
        if len(u) == 1 and u not in MORSE_CODE and ord(u) > 127:
            import unicodedata
            d = unicodedata.normalize("NFKD", u)
            u = d[0] if d and d[0].isascii() else u
        out.append(u)
    return "".join(out)


def morse_encode(text):
    """text -> (signs, skipped): signs = list of ("code", shown) and (" ", " ") for a word gap; skipped = the characters
    that have no Morse sign (left out). «CH» is one sign, «<SOS>» / «<AR>» ... are prosigns."""
    s = morse_upper(str(text or "")[:MORSE_TEXT_MAX * 4])
    signs, skipped = [], []
    i, n = 0, len(s)
    while i < n and len(signs) < MORSE_TEXT_MAX * 2:
        c = s[i]
        if c.isspace():
            if signs and signs[-1][0] != " ":
                signs.append((" ", " "))
            i += 1; continue
        if c == "<":
            j = s.find(">", i + 1, i + 6)
            if j > 0 and s[i + 1:j] in MORSE_PROSIGNS:
                signs.append((MORSE_PROSIGNS[s[i + 1:j]], s[i:j + 1])); i = j + 1; continue
        if s[i:i + 2] == "CH":
            signs.append((MORSE_CODE["CH"], "CH")); i += 2; continue
        if c in MORSE_CODE:
            signs.append((MORSE_CODE[c], c))
        else:
            skipped.append(c)
        i += 1
    while signs and signs[-1][0] == " ":
        signs.pop()
    return signs, skipped


def morse_unit(wpm):
    """seconds of one dit at this speed (the word PARIS = 50 units)"""
    return 1.2 / max(0.5, float(wpm))


def morse_timeline(signs, wpm, farnsworth=0):
    """signs -> [(seconds, on)] alternating, starts with ON. Standard timing: dit 1, dah 3, between the elements of a sign 1,
    between signs 3, between words 7 units. Farnsworth (0 = off, else the overall speed, slower than wpm): the signs keep
    the speed wpm, only the pauses between signs and words get longer (ARRL: t_a = (60 c - 37.2 s) / (s c))."""
    u = morse_unit(wpm)
    cg, wg = 3.0 * u, 7.0 * u
    fw = float(farnsworth or 0)
    if 0 < fw < float(wpm):
        ta = (60.0 * float(wpm) - 37.2 * fw) / (fw * float(wpm))
        cg, wg = 3.0 * ta / 19.0, 7.0 * ta / 19.0
    out = []
    gap = 0.0
    for code, _shown in signs:
        if code == " ":
            gap = wg if out else 0.0
            continue
        if out:
            out.append((gap or cg, False))
        gap = 0.0
        for k, e in enumerate(code):
            if k:
                out.append((u, False))
            out.append((u if e == "." else 3.0 * u, True))
    return out


def morse_edges(timeline):
    """[(seconds, on)] -> the times of the switches [t0 = 0 on, t1 off, t2 on ...] and the whole length"""
    ts, t = [], 0.0
    for d, _on in timeline:
        ts.append(t); t += d
    return ts, t


def morse_on_at(ts, total, dt):
    """is the key down dt seconds after the start? (ts from morse_edges; binary search)"""
    if dt < 0.0 or dt >= total or not ts:
        return False
    lo, hi = 0, len(ts) - 1
    while lo < hi:
        m = (lo + hi + 1) // 2
        if ts[m] <= dt:
            lo = m
        else:
            hi = m - 1
    return lo % 2 == 0


def _morse_split(vals, ratio):
    """sorted values -> index of the best split into a low and a high group whose medians differ at least by `ratio`,
    or 0 (one group). The split with the widest relative jump wins."""
    best, bi = 0.0, 0
    n = len(vals)
    for i in range(1, n):
        lo, hi = vals[i - 1], vals[i]
        if lo <= 0:
            continue
        j = hi / lo
        if j > best:
            best, bi = j, i
    if bi and vals[(bi + n) // 2] / max(1e-9, vals[bi // 2]) >= ratio and best >= 1.25:
        return bi
    return 0


def morse_decode(ons, gaps, _fair=False):
    """ons[i] = seconds the light was on, gaps[i] = seconds dark after it (the last may be None = still open).
    -> {"text", "unit" (s per dit), "wpm", "mixed" (short and long seen), "periodic" (even blinking - no text), "q" (0..1 fit),
        "n" (elements), "unknown" (signs not in the table), "word" (s: a gap from here on is a new word)}
    The length of a dit comes from the signal itself: the short and the long group of the ON times (dah / dit about 3) -
    with only one group the short pauses decide (ON about as long as the pause = dits, three times = dahs)."""
    n = len(ons)
    res = {"text": "", "unit": 0.0, "wpm": 0.0, "periodic": False, "mixed": False, "q": 0.0, "n": n, "unknown": 0, "word": 0.0}
    if n == 0:
        return res
    so = sorted(max(1e-4, float(x)) for x in ons)
    gl = [max(1e-4, float(g)) for g in gaps[:n] if g is not None]
    sg = sorted(gl)
    k = _morse_split(so, 2.2)
    if k and len(sg) >= 2 and not _fair:
        # the way shifts the lengths: a radio opens late (ON shorter, pauses longer), a lamp glows on (the other way round).
        # A dit and the pause inside a sign are sent equally long - so half their difference is taken back from every length.
        dit_, short_ = so[k // 2], sg[len(sg) // 4]
        if 0.42 * dit_ <= short_ <= 2.4 * dit_ and abs(short_ - dit_) > 0.12 * dit_:
            dl = 0.5 * (short_ - dit_)
            return morse_decode([max(1e-3, float(o) + dl) for o in ons], [None if g is None else max(1e-3, float(g) - dl) for g in gaps], True)
    if k:
        dit, dah = so[k // 2], so[(k + n) // 2]
        u = (dit * k + dah / 3.0 * (n - k)) / n
        thr_on = 1.6 * u
    else:
        med = so[n // 2]
        short = sg[len(sg) // 4] if sg else med          # a short pause (between the elements of a sign)
        if n >= 2 and sg and med > 1.9 * short and (len(sg) < 2 or sg[0] * 1.9 < med):
            u = med / 3.0                                # all long: dahs
        else:
            u = med
        thr_on = 1.6 * u
    u = max(1e-3, u)
    g1 = 1.6 * u                                         # ±40 % by hand: a dit / a short pause up to 1.4, a dah / a pause between signs from 1.8
    long_g = [g for g in sg if g >= g1]
    word = 5.0 * u
    kg = _morse_split(long_g, 1.7) if len(long_g) >= 2 else 0
    if kg:                                               # two groups of long pauses: between signs and between words
        word = max(g1 * 1.2, math.sqrt(long_g[kg // 2] * long_g[(kg + len(long_g)) // 2]))   # (Farnsworth: both are longer)
    # even blinking: all ON times alike and all pauses alike (a car indicator, a beacon, «EEEE», «TTTT») is no text
    res["mixed"] = bool(k) or (len(long_g) > 0 and len(long_g) < len(sg))
    res["periodic"] = n >= 5 and not res["mixed"]
    txt, cur, unknown, good = [], [], 0, 0
    for i in range(n):
        o = float(ons[i])
        dah_ = o >= thr_on
        cur.append("-" if dah_ else ".")
        r = o / (3.0 * u if dah_ else u)
        if 0.55 <= r <= 1.7:
            good += 1
        g = gaps[i] if i < len(gaps) else None
        if g is None or g >= g1 or len(cur) >= 10:
            ch = MORSE_DECODE.get("".join(cur))
            if ch is None:
                ch = MORSE_UNKNOWN; unknown += 1
            txt.append(ch); cur = []
            if g is not None and g >= word and i < n - 1:
                txt.append(" ")
    res.update(text="".join(txt)[:MORSE_RX_TEXT_MAX], unit=round(u, 4), wpm=round(1.2 / u, 1), q=round(good / float(n), 3),
               unknown=unknown, word=round(word, 3))
    return res


class MorseKey:
    """from a level (0..255, light on = high) per picture to elements: Schmitt trigger between the dark and the bright
    level of the last seconds, the time of a switch interpolated between two pictures. Also the entry for step 2 (sound,
    IR): feed levels with level(), or switches directly with edge()."""
    EL_MAX = 600                        # elements of one message (then it is closed)

    def __init__(self):
        self.t = []; self.v = []        # the last levels (for the dark / bright level)
        self.on = False; self.t_on = 0.0; self.t_off = 0.0; self.t_last = 0.0
        self.lo = 0.0; self.hi = 0.0
        self.ons = []; self.gaps = []
        self.pv = None; self.pt = 0.0; self.n = 0

    def levels(self):
        if len(self.v) >= 12 and self.n % 4 == 0:
            s = sorted(self.v)
            self.lo, self.hi = float(s[len(s) // 10]), float(s[-1 - len(s) // 50])
        return self.lo, self.hi

    def prime(self, vals):
        """the dark and the bright level from a first series (so the first element is not lost while they are learnt)"""
        s = sorted(float(v) for v in vals)
        if len(s) >= 6:
            self.lo, self.hi = s[len(s) // 10], s[-1 - len(s) // 50]

    def level(self, v, t, keep_s=6.0, min_swing=20.0):
        """one picture: the level v at the time t. Returns True when an element or a pause was closed."""
        v = float(v); t = float(t)
        self.n += 1
        self.t.append(t); self.v.append(v)
        if len(self.v) > 400 or (len(self.t) > 8 and t - self.t[0] > keep_s):
            k = 1
            while k < len(self.t) - 8 and t - self.t[k] > keep_s:
                k += 1
            del self.t[:k], self.v[:k]
        lo, hi = self.levels()
        if v > hi:
            hi = self.hi = v                              # brighter than ever: at once (the first element must not be lost)
        elif v < lo:
            lo = self.lo = v
        sw = hi - lo
        ch = False
        if sw >= min_swing and self.pv is not None:
            mid = lo + 0.5 * sw
            if not self.on and v > lo + 0.62 * sw:
                ch = self.edge(True, self._cross(mid, v, t))
            elif self.on and v < lo + 0.38 * sw:
                ch = self.edge(False, self._cross(mid, v, t))
        self.pv, self.pt, self.t_last = v, t, t
        return ch

    def _cross(self, mid, v, t):
        dv = v - self.pv
        if abs(dv) < 1e-6 or not (min(self.pv, v) <= mid <= max(self.pv, v)):
            return t
        return self.pt + (mid - self.pv) / dv * (t - self.pt)

    def edge(self, on, t):
        """the key went down (on) / up at the time t"""
        if on == self.on:
            return False
        self.on = on
        if on:
            if self.ons and self.gaps and self.gaps[-1] is None:
                self.gaps[-1] = max(0.0, t - self.t_off)
            self.t_on = t
            return bool(self.ons)
        self.t_off = t
        if len(self.ons) < self.EL_MAX:
            self.ons.append(max(0.0, t - self.t_on)); self.gaps.append(None)
        return True

    def dark_for(self, t):
        """seconds since the last element ended (0 while the light is on or nothing was seen yet)"""
        return 0.0 if (self.on or not self.ons) else max(0.0, t - self.t_off)


def morse_valid(d, fps=0.0):
    """is this decode a Morse text worth showing? At least 3 elements, short and long ones, the lengths fit, few unknown
    signs, and a dit is at least 1.5 pictures long (else the camera is too slow for this speed)."""
    if not d or d["n"] < 3 or d["periodic"] or not d["mixed"] or d["q"] < 0.7 or not d["text"].strip():
        return False
    if fps and d["unit"] * fps < 1.5:
        return False
    return d["unknown"] * 3 <= max(1, len(d["text"].replace(" ", "")))


class MorseRx:
    """Finds blinking lights in the camera picture and decodes them. feed(gray, t) once per picture; cheap:
    one dilate + one small copy per picture, every few pictures a minimum / maximum over the last seconds.
    Memory is fixed: BUF pictures of 160 × 90 bytes, at most TRACKS lights, EL_MAX elements each."""
    W = 160                             # fields across (the picture is made this small, the brightest pixel of a field counts)
    BUF = 192                           # pictures kept (the last seconds)
    SPAN_S = 6.0                        # s: a field must have been dark and bright within this time
    TRACKS = 3
    MIN_SWING = 24                      # grey levels between dark and bright
    AREA_MAX = 0.12                     # a blinking area bigger than this part of the picture is no lamp (the whole scene flickers)
    END_S = 3.0                         # s of dark that end a message (longer for slow keying: 2.2 word gaps)
    IGNORE_S = 20.0                     # s an even blinker is left alone before it is looked at again

    def __init__(self, on_message=None):
        self.on_message = on_message
        self.reset()

    def reset(self):
        self.buf = None; self.tb = None; self.i = 0; self.nf = 0
        self.mn = None; self.tracks = []; self.ignore = []
        self.active = None; self.live = None
        self.done = []
        self.stats = {"frames": 0, "fps": 0.0, "msgs": 0, "dropped": 0, "periodic": 0, "fast": 0, "fast_t": 0.0, "ms": 0.0, "tracks": 0}
        self._t_prev = 0.0; self._dts = []

    def _order(self):
        """indices of the buffered pictures, oldest first"""
        n = min(self.nf, self.BUF)
        return [(self.i - n + j) % self.BUF for j in range(n)]

    def feed(self, gray, t):
        """gray: uint8 picture (any size, 2 dimensions); t: its time in seconds. Returns the live state (dict) or None."""
        c0 = time.perf_counter()
        t = float(t)
        if t != t or abs(t) == float("inf"):
            return self.live
        H, W = gray.shape[:2]
        k = max(1, W // self.W)
        if k > 1:
            g = cv2.dilate(gray, np.ones((k, k), np.uint8))[k // 2::k, k // 2::k]
        else:
            g = gray
        if self.buf is None or self.buf.shape[1:] != g.shape:
            self.reset()
            self.buf = np.zeros((self.BUF,) + g.shape, np.uint8); self.tb = np.zeros(self.BUF, np.float64)
        if self._t_prev and 0 < t - self._t_prev < 2.0:
            self._dts.append(t - self._t_prev); del self._dts[:-30]
            self.stats["fps"] = round(len(self._dts) / max(1e-6, sum(self._dts)), 1)
        elif self._t_prev and not (t > self._t_prev) and not (self._t_prev - t > 2.0):
            return self.live                                         # a picture out of order (or without a time): left out
        elif self._t_prev:
            keep = self.stats; self.reset(); self.stats = keep       # the clock jumped or the camera was away: start again
            self.buf = np.zeros((self.BUF,) + g.shape, np.uint8); self.tb = np.zeros(self.BUF, np.float64)
        self._t_prev = t
        self.buf[self.i] = g; self.tb[self.i] = t
        self.i = (self.i + 1) % self.BUF; self.nf += 1
        fps = self.stats["fps"] or 10.0
        every = max(3, int(fps / 3.0))
        if self.nf % every == 0 and self.nf >= 6:
            self._scan(t)
        for tr_ in list(self.tracks):
            self._track(tr_, g, t)
        self._close(t)
        self.stats["frames"] += 1; self.stats["tracks"] = len(self.tracks)
        self.stats["ms"] = round(0.95 * self.stats["ms"] + 0.05 * (time.perf_counter() - c0) * 1000.0, 3)
        return self.live

    # ---- where does something blink? ----
    def _scan(self, t):
        idx = [j for j in self._order() if t - self.tb[j] <= self.SPAN_S]
        if len(idx) < 6:
            return
        sub = self.buf[idx]
        mn = sub.min(axis=0); mx = sub.max(axis=0)
        self.mn = mn
        rng = cv2.subtract(mx, mn)
        thr = max(float(self.MIN_SWING), 3.0 * float(np.percentile(rng, 75)))
        mask = (rng > thr).astype(np.uint8)
        if not mask.any() or len(self.tracks) >= self.TRACKS:
            return
        nl, _lab, st, cen = cv2.connectedComponentsWithStats(mask, connectivity=8)
        h, w = mask.shape
        cand = []
        for li in range(1, min(nl, 40)):
            x, y, bw, bh, area = [int(v) for v in st[li]]
            if area > self.AREA_MAX * h * w:
                continue
            peak = int(rng[y:y + bh, x:x + bw].max())
            cand.append((peak, x + bw // 2, y + bh // 2, max(bw, bh)))
        cand.sort(reverse=True)
        self.ignore = [g_ for g_ in self.ignore if t - g_[2] < self.IGNORE_S]
        self.done = [g_ for g_ in self.done if t - g_[2] < self.SPAN_S + 2.0]
        for peak, cx, cy, size in cand[:6]:
            if len(self.tracks) >= self.TRACKS:
                break
            r = min(8, 4 + size // 2)                       # a small window: a person walking past must not cover a lamp nearby
            if any(abs(cx - q["x"]) <= r + q["r"] and abs(cy - q["y"]) <= r + q["r"] for q in self.tracks):
                continue
            if any(abs(cx - gx) <= 6 and abs(cy - gy) <= 6 for gx, gy, _t in self.ignore):
                continue
            tr_ = {"x": cx, "y": cy, "r": r, "key": MorseKey(), "t0": t, "dec": None, "valid": False, "size": size}
            x0, x1, y0, y1 = self._win(tr_, w, h)
            lv = (sub[:, y0:y1, x0:x1].astype(np.int16) - mn[y0:y1, x0:x1].astype(np.int16)).reshape(len(idx), -1).max(axis=1)
            after = max([0.0] + [te for dx, dy, te in self.done if abs(cx - dx) <= 12 and abs(cy - dy) <= 12])
            tr_["key"].prime(lv)
            for j, v in zip(idx, lv):                     # the last seconds once more for this place (not a message already read)
                if self.tb[j] > after:
                    tr_["key"].level(v, self.tb[j], self.SPAN_S, self.MIN_SWING)
            self.tracks.append(tr_)

    @staticmethod
    def _win(tr_, w, h, grow=0):
        r = min(tr_["r"] + 12, tr_["r"] + grow)
        return max(0, tr_["x"] - r), min(w, tr_["x"] + r + 1), max(0, tr_["y"] - r), min(h, tr_["y"] + r + 1)

    def _track(self, tr_, g, t):
        h, w = g.shape
        key = tr_["key"]
        # dark for a while: the hand may have moved - look wider. Only for a place that has shown Morse already: anything else
        # that moves (a person walking past) keeps its small window and cannot take up a lamp nearby.
        x0, x1, y0, y1 = self._win(tr_, w, h, int(6.0 * key.dark_for(t)) if tr_["valid"] else 0)
        if self.mn is None or x1 <= x0 or y1 <= y0:
            return
        d = cv2.subtract(g[y0:y1, x0:x1], self.mn[y0:y1, x0:x1])
        _mn, v, _p, pos = cv2.minMaxLoc(d)
        if key.level(v, t, self.SPAN_S, self.MIN_SWING):
            tr_["dec"] = morse_decode(key.ons, key.gaps)
            d_ = tr_["dec"]
            tr_["valid"] = morse_valid(d_, self.stats["fps"])
            if d_["periodic"] and d_["n"] >= 12:           # an even blinker: leave this place alone for a while
                self.stats["periodic"] += 1
                self.ignore.append((tr_["x"], tr_["y"], t)); del self.ignore[:-8]
                self._drop(tr_); return
        if key.on and v > key.lo + 0.62 * (key.hi - key.lo):   # follow the light (a torch in a hand moves)
            tr_["x"] = int(round(0.5 * tr_["x"] + 0.5 * (x0 + pos[0]))); tr_["y"] = int(round(0.5 * tr_["y"] + 0.5 * (y0 + pos[1])))
        if self.active is None and tr_["valid"]:
            self.active = tr_
        if tr_ is self.active:
            self.live = {"text": tr_["dec"]["text"], "wpm": tr_["dec"]["wpm"], "x": tr_["x"] / float(w), "y": tr_["y"] / float(h),
                         "r": tr_["r"] / float(w), "on": key.on, "t": t, "valid": tr_["valid"]}

    def _drop(self, tr_):
        if tr_ in self.tracks:
            self.tracks.remove(tr_)
        if tr_ is self.active:
            self.active = None; self.live = None

    def _close(self, t):
        for tr_ in list(self.tracks):
            key = tr_["key"]
            d_ = tr_["dec"]
            # (one or two elements alone say nothing about the speed: a bright thing that passed must not keep the place open)
            end = self.END_S if not d_ or d_["n"] < 3 else min(12.0, max(self.END_S, 2.2 * d_["word"]))
            full = len(key.ons) >= key.EL_MAX or (d_ is not None and len(d_["text"]) >= MORSE_RX_TEXT_MAX)
            if key.on and t - key.t_on > 8.0:               # on for good: a lamp, no key
                self._drop(tr_); continue
            if (key.ons and key.dark_for(t) >= end) or full:
                if key.gaps and key.gaps[-1] is not None:
                    key.gaps[-1] = None
                d_ = morse_decode(key.ons, key.gaps)
                ok = morse_valid(d_, self.stats["fps"])
                if d_["n"] >= 3 and d_["mixed"] and self.stats["fps"] and d_["unit"] * self.stats["fps"] < 1.5:
                    self.stats["fast"] += 1; self.stats["fast_t"] = t
                self.done.append((tr_["x"], tr_["y"], key.t_off)); del self.done[:-8]
                if ok and (self.active is None or tr_ is self.active):
                    self.stats["msgs"] += 1
                    if self.on_message is not None:
                        self.on_message(d_["text"].strip(), dict(d_, x=tr_["x"] / float(self.buf.shape[2]), y=tr_["y"] / float(self.buf.shape[1]), t=t))
                else:
                    self.stats["dropped"] += 1
                self._drop(tr_)
            elif not key.ons and not key.on and t - tr_["t0"] > self.SPAN_S + 2.0:
                self._drop(tr_)                             # nothing came of it


class MorseAudio:
    """Morse by sound: a keyed tone or a whistle in the microphone signal (16 kHz mono). feed(samples) with every piece of
    sound; cheap: one small FFT per 8 ms. Looks for ONE narrow tone that was there AND not there in the last seconds
    (a steady tone, hiss, a bang or the wind are no key), follows it, and decodes with MorseKey / morse_decode like the
    light. Nothing of the sound is kept: only the levels of 44 frequency fields of the last seconds (no speech can be made
    of them), fixed memory."""
    RATE = 16000
    HOP, WIN = 128, 256                 # 8 ms steps, 16 ms window = fields of 62.5 Hz
    LO, HI = 300.0, 3000.0              # Hz: the band of a voice radio, a whistle, the tone of MoveEye (660 Hz)
    SPAN_S = 6.0
    MIN_SWING = 9.0                     # dB a tone must stand out of the hiss
    END_S = 3.0
    IGNORE_S = 20.0

    def __init__(self, on_message=None):
        self.on_message = on_message
        self.win = np.hanning(self.WIN).astype(np.float32)
        self.b0 = int(round(self.LO * self.WIN / self.RATE)); self.b1 = int(round(self.HI * self.WIN / self.RATE)) + 1
        self.fps = self.RATE / float(self.HOP)
        self.N = int(self.SPAN_S * self.fps)
        self.reset()

    def reset(self):
        self.tail = np.zeros(0, np.float32)
        self.hist = np.zeros((self.N, self.b1 - self.b0), np.float32); self.i = 0; self.n = 0
        self.t = 0.0; self.prev = None
        self.key = None; self.bin = -1; self.dec = None; self.valid = False; self.t0 = 0.0
        self.ignore = []; self.done = []; self.live = None
        self.stats = {"frames": 0, "msgs": 0, "dropped": 0, "periodic": 0, "ms": 0.0, "hz": 0, "db": 0.0}

    def _order(self):
        n = min(self.n, self.N)
        return [(self.i - n + j) % self.N for j in range(n)]

    def _lev(self, rows, b):
        return rows[:, max(0, b - 2):b + 3].max(axis=1)        # ±125 Hz: a whistle is never quite steady

    def feed(self, pcm):
        """pcm: the next samples (any number), int16 scale. Returns the live state (dict) or None."""
        c0 = time.perf_counter()
        x = np.asarray(pcm, np.float32).ravel()
        if x.size > self.RATE * 2:
            x = x[-self.RATE * 2:]                              # never more than 2 s at once
        if not np.all(np.isfinite(x)):
            return self.live
        x = np.concatenate((self.tail, x)) if self.tail.size else x
        nfr = (x.size - self.WIN) // self.HOP + 1
        if nfr <= 0:
            self.tail = x
            return self.live
        idx = np.arange(self.WIN)[None, :] + self.HOP * np.arange(nfr)[:, None]
        X = np.abs(np.fft.rfft(x[idx] * self.win, axis=1))[:, self.b0:self.b1]
        self.tail = x[nfr * self.HOP:]
        med = np.median(X, axis=1)[:, None] + 1.0
        c = np.clip(20.0 * np.log10(X / med + 1e-6), 0.0, 60.0).astype(np.float32)   # dB above the hiss of this moment
        for r in range(nfr):
            row = c[r] if self.prev is None else 0.55 * c[r] + 0.45 * self.prev
            self.prev = row
            self.hist[self.i] = row; self.i = (self.i + 1) % self.N; self.n += 1
            self.t += self.HOP / float(self.RATE)
            if self.key is not None:
                v = float(row[max(0, self.bin - 2):self.bin + 3].max())
                if self.key.level(v, self.t, self.SPAN_S, self.MIN_SWING):
                    self._decoded()
                if self.key is not None:
                    self._close()
            if self.n % 40 == 0 and self.n >= 60:
                self._scan()
        self.stats["frames"] += nfr
        self.stats["ms"] = round(0.9 * self.stats["ms"] + 0.1 * (time.perf_counter() - c0) * 1000.0, 3)
        return self.live

    def _scan(self):
        rows = self.hist[self._order()]
        lo = np.percentile(rows, 15, axis=0); hi = np.percentile(rows, 97, axis=0)
        sw = hi - lo
        self.ignore = [g for g in self.ignore if self.t - g[1] < self.IGNORE_S]
        self.done = [g for g in self.done if self.t - g[1] < self.SPAN_S + 2.0]
        for b, _t in self.ignore:
            sw[max(0, b - 3):b + 4] = 0.0
        if self.key is not None:                                # follow a tone that drifts (a whistle, a radio off tune)
            a, e = max(0, self.bin - 3), min(sw.size, self.bin + 4)
            b = a + int(np.argmax(sw[a:e]))
            if sw[b] > sw[self.bin] + 3.0:
                self.bin = b
            self.stats["hz"] = int(round((self.b0 + self.bin) * self.RATE / float(self.WIN)))
            return
        b = int(np.argmax(sw))
        if sw[b] < self.MIN_SWING + 3.0:
            return
        lv = self._lev(rows, b)
        mid = float(lo[b]) + 0.5 * float(sw[b])
        duty = float((lv > mid).mean())
        if not 0.03 <= duty <= 0.85:
            return
        self.key = MorseKey(); self.bin = b; self.dec = None; self.valid = False; self.t0 = self.t
        self.stats["hz"] = int(round((self.b0 + b) * self.RATE / float(self.WIN))); self.stats["db"] = round(float(sw[b]), 1)
        after = max([0.0] + [te for db_, te in self.done if abs(db_ - b) <= 4])
        n = lv.size
        self.key.prime(lv)
        for j in range(n):                                      # the last seconds once more for this tone
            tj = self.t - (n - 1 - j) * self.HOP / float(self.RATE)
            if tj > after:
                self.key.level(float(lv[j]), tj, self.SPAN_S, self.MIN_SWING)
        if self.key.ons:
            self._decoded()

    def _decoded(self):
        key = self.key
        self.dec = d = morse_decode(key.ons, key.gaps)
        self.valid = morse_valid(d, self.fps)
        if d["periodic"] and d["n"] >= 12:                      # an even beep (a reversing lorry, an alarm clock): no text
            self.stats["periodic"] += 1
            self.ignore.append((self.bin, self.t)); del self.ignore[:-8]
            self._drop(); return
        self.live = {"text": d["text"], "wpm": d["wpm"], "hz": self.stats["hz"], "on": key.on, "t": self.t, "valid": self.valid}

    def _drop(self):
        self.key = None; self.bin = -1; self.dec = None; self.valid = False; self.live = None

    def _close(self):
        key, d = self.key, self.dec
        end = self.END_S if not d or d["n"] < 3 else min(12.0, max(self.END_S, 2.2 * d["word"]))
        full = len(key.ons) >= key.EL_MAX or (d is not None and len(d["text"]) >= MORSE_RX_TEXT_MAX)
        if key.on and self.t - key.t_on > 8.0:                  # a tone that stays: no key
            self._drop(); return
        if (key.ons and key.dark_for(self.t) >= end) or full:
            if key.gaps and key.gaps[-1] is not None:
                key.gaps[-1] = None
            d = morse_decode(key.ons, key.gaps)
            self.done.append((self.bin, key.t_off)); del self.done[:-8]
            if morse_valid(d, self.fps):
                self.stats["msgs"] += 1
                if self.on_message is not None:
                    self.on_message(d["text"].strip(), dict(d, hz=self.stats["hz"], t=self.t))
            else:
                self.stats["dropped"] += 1
            self._drop()
        elif not key.ons and not key.on and self.t - self.t0 > self.SPAN_S + 2.0:
            self._drop()
# ==== MORSE-KERN ENDE ====


# ---- the mode, the settings -------------------------------------------------------------------------------------------------------
MORSE_MODE_MAX_MIN = 30                # hard maximum of one session (start + every «longer»), minutes
MORSE_TX_MAX_S = 600.0                 # a transmission never lasts longer
MORSE_TX_PER_MIN = 6                   # starts of a transmission per minute
MORSE_PUSH_GAP_S, MORSE_PUSH_PER_H = 20.0, 10
MORSE_SAY_GAP_S = 10.0
MORSE_LIMIT_K = 0.4                    # reading limit shown: WPM = 0.4 × pictures per second (a dit = 3 pictures; docs/Morse_Messung.md)
# switching cycles per second an output may do; a row of dits blinks with 1 / (2 dit) -> WPM = 2.4 × Hz
MORSE_OUT_HZ = {"white": 3.0, "relay": 2.0, "relay_ssr": 3.0, "led": 4.5, "ir": 25.0 / 3.0, "beep": 25.0 / 2.4}
MORSE_FLASH_NOTE_HZ = 3.0              # visible flashing from here on: the page shows the note about flashing light
MORSE_SOURCES = ("camera", "sound")    # camera: a light, also the infrared light of another MoveEye; sound: the microphone
MORSE_TEST_TEXT = "VVV TEST"           # «Gegenstelle testen»: what one MoveEye sends by infrared and the other one looks for
MORSE_SOUND_WPM = 20                   # reading by sound: shown limit (measured: docs/Morse_Messung_Ton.md)
MORSE_OWN_S = 1.5                      # s after an own transmission in which the own light / tone is not read (no echo)
MORSE_DEF = {"morse_minutes": 10, "morse_wpm": 5, "morse_fw": 0, "morse_outs": ["white"], "morse_ssr": [], "morse_rx": True,
             "morse_rx_live": True, "morse_rx_hist": True, "morse_rx_push": False, "morse_rx_say": False, "morse_rx_sound": False}
for _k, _v in MORSE_DEF.items():
    CFG.setdefault(_k, json.loads(json.dumps(_v))); DEFAULTS.setdefault(_k, json.loads(json.dumps(_v)))
    FACTORY_CFG.setdefault(_k, json.loads(json.dumps(_v)))
USER_SETTINGS_DENY.update(MORSE_DEF)   # only the administrator (never a user with «settings», never an app key, not in operator mode)
APPKEY_DENY_KEYS.update(MORSE_DEF)
APPKEY_DENY_PATHS.update({"/api/morse", "/morse"})
LOCK_DENY_PATHS.add("/api/morse")
_IMP["sys"] = re.compile(_IMP["sys"].pattern + r"|Morse mode")       # «Morse-Modus ein / aus» counts as important in the log

MORSE = {"until": 0.0, "t0": 0.0, "by": "", "tx": None, "rx": None, "arx": None, "alive": None, "a_t": 0.0, "own_light": 0.0, "own_sound": 0.0,
         "own_rst": [False, False], "peer": None, "msgs": deque(maxlen=20), "live": None, "last": None, "relearn": False,
         "lock": threading.RLock(), "tx_starts": [], "push_t": [], "push_held": 0, "say_t": 0.0, "out_n": 0, "lab": {}, "err_t": 0.0, "seq": 0}


def morse_on():
    """does the Morse mode run? (ends it when its time is over - whoever asks first)"""
    u = MORSE["until"]
    if not u:
        return False
    if time.time() < u and not PAUSING["on"]:
        return True
    morse_end("the time is over" if not PAUSING["on"] else "the program stops")
    return False


def morse_end(why="button", who=""):
    with MORSE["lock"]:
        if not MORSE["until"]:
            return False
        MORSE["until"] = 0.0
        morse_tx_stop(why)
        MORSE["live"] = None; MORSE["alive"] = None; MORSE["relearn"] = True
        for k in ("rx", "arx"):
            if MORSE[k] is not None:
                MORSE[k].reset()                             # nothing of the sound or the pictures stays behind
    try:                                                   # the sabotage guard and the lens check learn the scene again (no alarm
        if TAMPER is not None:                             # because a lamp was on a moment ago)
            TAMPER.ref = None; TAMPER.settle = time.time() + 10
    except Exception:
        pass
    log_event("sys", f"Morse mode off ({why}{', ' + who if who else ''}) - the protection is as before: {protect_level()}"[:200])
    return True


def morse_start(minutes, who="web", more=False):
    """start the mode (more=False) or make a running one longer (more=True) -> (ok, English error). Every start and every
    «longer» is an own request of the administrator; all together never more than MORSE_MODE_MAX_MIN after the start."""
    try:
        m = int(minutes)
    except (TypeError, ValueError):
        return False, "not a number"
    if not 1 <= m <= MORSE_MODE_MAX_MIN:
        return False, "not a number"
    now = time.time()
    with MORSE["lock"]:
        on = morse_on()
        if more:
            if not on:
                return False, "the Morse mode is not running"
            cap = MORSE["t0"] + MORSE_MODE_MAX_MIN * 60.0
            if MORSE["until"] >= cap - 1.0:
                return False, "the Morse mode cannot run longer - start it again when it has ended"
            MORSE["until"] = min(cap, MORSE["until"] + m * 60.0)
            log_event("sys", f"Morse mode longer ({who}): until {datetime.fromtimestamp(MORSE['until']).strftime('%H:%M:%S')}"[:200])
            return True, ""
        if on:
            return False, "the Morse mode is already running"
        if toolmode_on() or RESTART.get("pending"):
            return False, "not now - the camera rests"
        if MORSE["rx"] is None:
            MORSE["rx"] = MorseRx(lambda text, info: morse_rx_text(text, "camera", info))
        MORSE["rx"].reset()
        if MORSE["arx"] is None:
            MORSE["arx"] = MorseAudio(lambda text, info: morse_rx_text(text, "sound", info))
        MORSE["arx"].reset()
        MORSE.update(alive=None, peer=None, own_light=0.0, own_sound=0.0)
        MORSE.update(until=now + m * 60.0, t0=now, by=str(who)[:40], live=None, last=None)
    try:
        protect_cancel_escalation()
    except Exception:
        pass
    log_event("sys", f"Morse mode on ({who}) for {m} min - the protection is PAUSED until "
                     f"{datetime.fromtimestamp(MORSE['until']).strftime('%H:%M:%S')} (was: {protect_level_cfg()})"[:200])
    return True, ""


def protect_level_cfg():
    """the level the settings say (is_armed() says «no» while the mode runs)"""
    try:
        return protect_level()
    except Exception:
        return "?"


_is_armed_morse = is_armed


# wraps: is_armed
def is_armed():                                              # + 639zzz: no alarms while the Morse mode runs (like the walk test)
    if MORSE["until"] and morse_on():
        return False
    return _is_armed_morse()


_protect_label_morse = protect_label


# wraps: protect_label
def protect_label(arm_state, left=0, lang=None):             # + 639zzz: the state everywhere says «Morse-Modus», not «Wachsam»
    if MORSE["until"] and arm_state in ("armed", "arming") and morse_on():
        return "⏸ " + tr("Morse mode", lang)
    return _protect_label_morse(arm_state, left, lang)


_protect_status_morse = protect_status


# wraps: protect_status
def protect_status(lang=None, force=False):                  # + 639zzz: the pages show «Morse-Modus» instead of «Wachsam» / «Voll»
    v = _protect_status_morse(lang, force)
    if MORSE["until"] and morse_on():
        v = dict(v, morse=True, morse_rest=max(0, int(MORSE["until"] - time.time())))
    return v


# the main page (530): the badge in the header and the card «Schutz» say «Morse-Modus» while it runs (like «Gehtest»)
for _a, _b in (
        ('  if ((s.protect || {}).walk && (s.arm_state === "armed" || s.arm_state === "arming")) return ["🚶 " + t("Walk test"), "yel"];',
         '  if ((s.protect || {}).morse && (s.arm_state === "armed" || s.arm_state === "arming")) return ["⏸ " + t("Morse mode"), "yel"];   // 639zzz\n'),
        ('  const walk = !!P.walk && P.level !== "off";', '  const morse = !!P.morse && P.level !== "off";   // 639zzz\n'),
        ('    if (walk && P.level === k) { ic = "🚶"; n = t("Walk test"); }', '    if (morse && P.level === k) { ic = "⏸"; n = t("Morse mode"); }\n')):
    if _a in WEB_PAGE and _b.strip() not in WEB_PAGE:
        WEB_PAGE = WEB_PAGE.replace(_a, _b + _a, 1)
for _a, _b in (('walk ? "🚶 " + t("Walk test running: no alarms until it ends (afterwards the protection is as before).") :',
                'morse ? "⏸ " + t("Morse mode is running – the protection is PAUSED") : '),
               ("P.forecast, P.walk", "P.morse, ")):
    if _a in WEB_PAGE and _b + _a not in WEB_PAGE:
        WEB_PAGE = WEB_PAGE.replace(_a, _b + _a, 1)

_web_disarms_morse = web_disarms


# wraps: web_disarms
def web_disarms(path, d):                                    # + 639zzz: starting / prolonging the mode pauses the protection -> PIN
    if path == "/api/morse" and isinstance(d, dict) and CFG.get("armed"):
        return d.get("action") in ("start", "more")
    return _web_disarms_morse(path, d)


_kopf_claims_morse = kopf_claims


# wraps: kopf_claims
def kopf_claims():                                           # + 639zzz: the head stands still while the mode runs (rank of the walk
    c = _kopf_claims_morse()                                 # test, 162: no round, no glance, no parking; the hand still steers)
    if MORSE["until"] and morse_on():
        c.add("walktest")
    return c


# ---- quiet while the mode runs: a blinking light is no movement, no sabotage, no day -------------------------------------------------
_morse_foreground_410 = MotionWatch.foreground
_morse_lowlight_410 = MotionWatch._lowlight_decide
_morse_eco_410 = MotionWatch._eco
_morse_tamper_feed_060 = TamperGuard.feed
_morse_lens_feed_060 = LensCheck.feed
_morse_ai_detect_180 = AIDetector.detect
_morse_fog_twi_frame = fog_twi_frame
_morse_batt_save_pace = batt_save_pace


def _morse_foreground(self, gray, small, rain_mode, wind_boost):
    if MORSE["until"] or MORSE["relearn"]:
        MORSE["relearn"] = False
        if not MORSE["until"] or morse_on():
            self.bg.apply(gray, learningRate=1.0)          # the picture of now is the background
            self.color_bg = None
            return np.zeros_like(gray)
    return _morse_foreground_410(self, gray, small, rain_mode, wind_boost)


def _morse_lowlight(self, bright, t0):
    if MORSE["until"] and morse_on():
        return bool(STATE.get("lowlight"))                  # a torch is neither day nor night: the mode stays
    return _morse_lowlight_410(self, bright, t0)


def _morse_eco(self, present, t0):
    if MORSE["until"] and morse_on():
        self.eco_wake_t = t0                                # reading needs every picture: no «few pictures (all quiet)»
    return _morse_eco_410(self, present, t0)


def _morse_tamper_feed(self, small, t0):
    if MORSE["until"] and morse_on():
        self.ref = None; self.settle = t0 + 10; self.n_cov = self.n_mov = 0
        return None
    return _morse_tamper_feed_060(self, small, t0)


def _morse_lens_feed(self, small, t0):
    if MORSE["until"] and morse_on():
        return None
    return _morse_lens_feed_060(self, small, t0)


def _morse_ai_detect(self, frame):
    if MORSE["until"] and morse_on():
        self.objects = []                                   # the protection is paused: the computer is free for a high frame rate
        return []
    return _morse_ai_detect_180(self, frame)


# wraps: fog_twi_frame
def fog_twi_frame(w, small, gray, bright, lowlight, t0):     # + 639zzz: every picture of the camera loop to the Morse reader
    if MORSE["until"]:
        try:
            if morse_on() and CFG.get("morse_rx") and MORSE["rx"] is not None:
                if time.time() - MORSE["own_light"] < MORSE_OWN_S:   # the own lamp lights the scene: that is no message
                    if not MORSE["own_rst"][0]:
                        MORSE["own_rst"][0] = True; MORSE["rx"].reset(); MORSE["live"] = None
                else:
                    MORSE["own_rst"][0] = False
                    MORSE["live"] = MORSE["rx"].feed(gray, t0)
        except Exception as e:
            if t0 - MORSE["err_t"] > 60:
                MORSE["err_t"] = t0; log_event("sys", f"Morse reader: {type(e).__name__}: {e}"[:160])
            try:
                MORSE["rx"].reset()
            except Exception:
                pass
    return _morse_fog_twi_frame(w, small, gray, bright, lowlight, t0)


_morse_audio_chunk_250 = AudioMonitor._chunk


def _morse_audio_chunk(self, data):                          # + 639zzz step 2: the sound of the microphone to the Morse reader -
    _morse_audio_chunk_250(self, data)                       # only while the mode runs and «by sound» is chosen; nothing is stored
    if MORSE["until"] and CFG.get("morse_rx_sound"):
        try:
            if morse_on() and MORSE["arx"] is not None:
                now = time.time()
                if now < self.mute_until or SOUND["playing"] or now - MORSE["own_sound"] < MORSE_OWN_S:
                    if not MORSE["own_rst"][1]:              # MoveEye plays a sound itself: not read
                        MORSE["own_rst"][1] = True; MORSE["arx"].reset(); MORSE["alive"] = None
                else:
                    MORSE["own_rst"][1] = False
                    MORSE["alive"] = MORSE["arx"].feed(np.frombuffer(data, dtype="<i2"))
                    MORSE["a_t"] = now
        except Exception as e:
            if time.time() - MORSE["err_t"] > 60:
                MORSE["err_t"] = time.time(); log_event("sys", f"Morse by sound: {type(e).__name__}: {e}"[:160])
            try:
                MORSE["arx"].reset()
            except Exception:
                pass


# wraps: AudioMonitor._chunk
AudioMonitor._chunk = _morse_audio_chunk


# wraps: batt_save_pace
def batt_save_pace(watch, t0, present):                      # + 639zzz: the battery saver does not slow the pictures in the mode
    if MORSE["until"] and morse_on():
        return None
    return _morse_batt_save_pace(watch, t0, present)


# wraps: MotionWatch.foreground
MotionWatch.foreground = _morse_foreground
# wraps: MotionWatch._lowlight_decide
MotionWatch._lowlight_decide = _morse_lowlight
# wraps: MotionWatch._eco
MotionWatch._eco = _morse_eco
# wraps: TamperGuard.feed
TamperGuard.feed = _morse_tamper_feed
# wraps: LensCheck.feed
LensCheck.feed = _morse_lens_feed
# wraps: AIDetector.detect
AIDetector.detect = _morse_ai_detect


# ---- sending ----------------------------------------------------------------------------------------------------------------------
def morse_out_wpm(kind):
    """the fastest speed of an output kind (whole WPM)"""
    return int(math.floor(2.4 * MORSE_OUT_HZ[kind] + 1e-6))


def morse_outputs(lang=None):
    """the outputs the administrator can choose: [{"id", "name", "kind", "ok", "wpm", "hz", "vis", "why"}]"""
    sim = bool(CFG.get("sim_on"))
    out = []

    def add(oid, name, kind, ok, vis, why=""):
        out.append({"id": oid, "name": name, "kind": kind, "ok": bool(ok), "wpm": morse_out_wpm(kind), "hz": round(MORSE_OUT_HZ[kind], 1),
                    "vis": vis, "why": "" if ok else tr(why, lang)})
    add("white", tr("White light", lang), "white", CFG.get("light_white_out") or sim, True, "not connected")
    add("ir", tr("Infrared light", lang), "ir", CFG.get("light_ir_out") or sim, False, "not connected")
    led_ok = bool(CFG.get("led_on", True)) and (LED.get("hw") in ("pca", "sim") or LED.get("sim"))
    add("led", tr("Status LED", lang), "led", led_ok, True, "not connected")
    try:
        sp = out_selected() and not sim_speaker_only("test")
    except Exception:
        sp = False
    add("beep", tr("Loudspeaker (tone)", lang), "beep", sp, False, "no loudspeaker selected")
    ssr = set(CFG.get("morse_ssr") or [])
    with LOCK:
        rel = [dict(r) for r in RELAYS]
    for r in rel:
        g = int(r["gpio"])
        kind = "relay_ssr" if g in ssr else "relay"
        add(f"relay:{g}", f"{r['name']} (GPIO {g})", kind, True, True)
        out[-1]["ssr"] = g in ssr
    return out


def morse_plan(text, outs, wpm, fw=0, lang=None):
    """what a transmission would be -> (plan, English error). plan = {"signs", "shown", "skipped", "wpm" (really used),
    "asked", "slow" (name of the output that limits), "fw", "tl", "secs", "outs", "relays", "flash_hz", "note"}"""
    signs, skipped = morse_encode(text)
    if len(str(text or "")) > MORSE_TEXT_MAX:
        return None, "the text is too long"
    if not any(c != " " for c, _s in signs):
        return None, "the text is empty" if not skipped else "no character of this text has a Morse sign"
    avail = {o["id"]: o for o in morse_outputs(lang)}
    ids = [o for o in dict.fromkeys(str(x) for x in (outs or [])) if o in avail][:12]
    if not ids:
        return None, "choose at least one output"
    bad = [avail[o]["name"] for o in ids if not avail[o]["ok"]]
    if bad:
        return None, "an output you chose is not connected"
    try:
        asked = float(wpm)
        fwv = float(fw or 0)
    except (TypeError, ValueError):
        return None, "not a number"
    if not (asked == asked and fwv == fwv):
        return None, "not a number"
    asked = max(MORSE_WPM_MIN, min(MORSE_WPM_MAX, asked))
    slow = min(ids, key=lambda o: avail[o]["wpm"])
    eff = min(asked, float(avail[slow]["wpm"]))             # the ONE place the speed is decided: never above the slowest output
    fwv = fwv if MORSE_WPM_MIN <= fwv < eff else 0
    tl = morse_timeline(signs, eff, fwv)
    secs = sum(d for d, _on in tl)
    if secs > MORSE_TX_MAX_S:
        return None, "this takes too long - a shorter text or faster"
    hz = 1.0 / (2.0 * morse_unit(eff))
    vis = [o for o in ids if avail[o]["vis"]]
    return {"signs": signs, "shown": "".join(s for _c, s in signs), "skipped": skipped[:40], "wpm": eff, "asked": asked,
            "slow": avail[slow]["name"] if eff < asked else "", "fw": fwv, "tl": tl, "secs": round(secs, 1), "outs": ids,
            "relays": {int(o[6:]): next((bool(r["active_low"]) for r in RELAYS if int(r["gpio"]) == int(o[6:])), False) for o in ids if o.startswith("relay:")},
            "flash_hz": round(hz, 2), "note": bool(vis) and hz >= MORSE_FLASH_NOTE_HZ - 1e-6, "vis": bool(vis)}, ""


def morse_tx_start(text, outs, wpm, fw=0, who="web"):
    """-> (ok, English error or "", plan). One transmission at a time, only while the mode runs."""
    now = time.time()
    with MORSE["lock"]:
        if not morse_on():
            return False, "the Morse mode is not running", None
        if MORSE["tx"] is not None:
            return False, "a transmission is running", None
        MORSE["tx_starts"] = [t for t in MORSE["tx_starts"] if now - t < 60.0]
        if len(MORSE["tx_starts"]) >= MORSE_TX_PER_MIN:
            return False, "too many transmissions - wait a minute", None
        plan, err = morse_plan(text, outs, wpm, fw)
        if plan is None:
            return False, err, None
        if "white" in plan["outs"] and ALM_SOS.get("on"):
            return False, "the SOS lamp is flashing - it goes first", None
        if now + 0.6 + plan["secs"] > MORSE["until"]:
            return False, "the Morse mode ends before this text is sent - make it longer first", None
        ts, total = morse_edges(plan["tl"])
        MORSE["tx_starts"].append(now)
        MORSE["seq"] += 1
        MORSE["tx"] = {"ts": ts, "total": total, "t0": now + 0.6, "outs": set(plan["outs"]), "relays": plan["relays"], "shown": plan["shown"],
                       "skipped": plan["skipped"], "wpm": plan["wpm"], "fw": plan["fw"], "by": str(who)[:40], "seq": MORSE["seq"], "tl": plan["tl"]}
    log_event("relay", f"Morse: sending {len(plan['shown'])} characters at {plan['wpm']:g} WPM on {', '.join(plan['outs'])} ({who})"[:200])
    if "beep" in plan["outs"]:
        morse_beep_play(MORSE["tx"])
    return True, "", plan


def morse_tx_stop(why="button"):
    with MORSE["lock"]:
        tx = MORSE["tx"]
        MORSE["tx"] = None
    if tx is None:
        return False
    if "beep" in tx["outs"] and why != "done":
        try:
            sound_stop()
        except Exception:
            pass
    log_event("relay", f"Morse: transmission {'finished' if why == 'done' else 'stopped (' + str(why) + ')'} - every output is as before"[:200])
    return True


def morse_tx_key(now=None):
    """None = nothing is sent (the outputs are left alone), else True / False = the key is down / up"""
    tx = MORSE["tx"]
    if tx is None:
        return None
    now = time.time() if now is None else now
    if PAUSING["on"] or now >= MORSE["until"] or now - tx["t0"] >= tx["total"]:
        morse_tx_stop("done" if now - tx["t0"] >= tx["total"] else "the mode ended")
        return None
    if "beep" in tx["outs"]:                                 # the own tone / the own light is not read back (639zzz step 2)
        MORSE["own_sound"] = now
    if len(tx["outs"]) > ("beep" in tx["outs"]):
        MORSE["own_light"] = now
    return morse_on_at(tx["ts"], tx["total"], now - tx["t0"])


_lights_tick_morse = lights_tick


# wraps: lights_tick
def lights_tick():                                           # + 639zzz: Morse with the white / infrared light (the way of the SOS lamp, 639zzt)
    L = STATE.get("lights")
    if isinstance(L, dict) and L.get("morse"):               # the light rules (070) compare with their own last result, not with
        L = dict(L); L.update(L.pop("morse")); STATE["lights"] = L       # the keying: no «White light ON / OFF» per dit
    res = _lights_tick_morse()
    tx = MORSE["tx"]
    if tx is None:
        return res
    try:
        on = morse_tx_key()
        if on is None:
            return res
        base = {}
        for n in ("white", "ir"):
            if n not in tx["outs"] or not (CFG.get(f"light_{n}_out") or CFG.get("sim_on")):
                continue
            if n == "white" and ALM_SOS.get("on"):
                continue                                     # the SOS lamp goes first
            base[n] = bool(res.get(n)); res[n] = on
        if base:
            STATE["lights"] = dict(STATE.get("lights") or {}, morse=base, **{n: res[n] for n in base})
    except Exception as e:
        MORSE["tx"] = None                                   # an error ends the transmission: the lights do what the rules say
        log_event("sys", f"Morse: light: {type(e).__name__}: {e}"[:160])
    return res


_morse_hw_lights = Hardware._lights


def _morse_hw_lights_wrap(self, wanted):
    _morse_hw_lights(self, wanted)
    tx = MORSE["tx"]
    if tx is None or not tx["relays"]:
        return
    try:
        on = morse_tx_key()
        if on is None:
            return
        for g, al in tx["relays"].items():
            if g in wanted:                                  # only a relay that exists: the hardware loop writes it (080)
                wanted[g] = (on, al)
    except Exception as e:
        MORSE["tx"] = None
        log_event("sys", f"Morse: relay: {type(e).__name__}: {e}"[:160])


# wraps: Hardware._lights
Hardware._lights = _morse_hw_lights_wrap
_led_frame_morse = led_frame
LED_LAYER_NAMES["morse"] = "Morse"


# wraps: led_frame
def led_frame(now, level="off", arming=False, dark=False):   # + 639zzz: Morse with the status LED (white, on / off)
    fr = _led_frame_morse(now, level, arming, dark)
    tx = MORSE["tx"]
    if tx is None or "led" not in tx["outs"] or not CFG.get("led_on", True):
        return fr
    try:
        on = morse_tx_key()
        if on is None:
            return fr
        br = max(0.5, _led_int("led_bright", 1, 100) / 100.0)
        return {"col": "white" if on else "off", "rgb": (1.0, 1.0, 1.0) if on else (0.0, 0.0, 0.0), "br": br if on else 0.0, "layer": "morse"}
    except Exception:
        MORSE["tx"] = None
        return fr


MORSE_BEEP_HZ = 660.0


def morse_beep_chunks(tl, rate, lead=0.6):
    """the tone of a timeline as pieces of float32 samples (5 ms ramps: no clicks)"""
    yield np.zeros(int(lead * rate), np.float32)
    ramp = max(1, int(0.005 * rate))
    for d, on in tl:
        n = max(1, int(round(d * rate)))
        if not on:
            yield np.zeros(n, np.float32); continue
        y = np.sin(2.0 * np.pi * MORSE_BEEP_HZ * np.arange(n) / rate).astype(np.float32)
        r = min(ramp, n // 2)
        if r:
            y[:r] *= np.linspace(0, 1, r, dtype=np.float32); y[-r:] *= np.linspace(1, 0, r, dtype=np.float32)
        yield y


def morse_beep_play(tx):
    """the tone on the loudspeaker in the background (the way of sound_play, 250: «sound_stop» ends it)"""
    try:
        vol = max(0.0, min(100.0, float(CFG.get("clap_volume", 60)))) / 100.0
        sound_stop(); talk_stop()
        with _SOUND_LOCK:
            SOUND["gen"] += 1; gen = SOUND["gen"]
            SOUND["playing"] = True; SOUND["msg"] = ""
            SOUND.update(kind="morse", virt=False, vol=vol * 100.0)
    except Exception as e:
        log_event("sys", f"Morse: tone: {e}"[:160]); return False

    def work():
        p = None
        try:
            cmd, err = out_cmd(OUT_RATE)
            if cmd is None:
                raise RuntimeError(err)
            with _SOUND_LOCK:
                if gen != SOUND["gen"]:
                    return
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                SOUND["proc"] = p
            if AUDIO is not None:
                AUDIO.mute_until = time.time() + tx["total"] + 3.0
            for y in morse_beep_chunks(tx["tl"], OUT_RATE, max(0.0, tx["t0"] - time.time())):
                if gen != SOUND["gen"] or MORSE["tx"] is not tx:
                    break
                p.stdin.write((np.clip(y * (vol ** 2), -1, 1) * 32767).astype("<i2").tobytes())
            p.stdin.close()
            p.wait(timeout=tx["total"] + 30)
        except (BrokenPipeError, OSError, RuntimeError, subprocess.SubprocessError) as e:
            log_event("sys", f"Morse: tone: {e}"[:160])
        finally:
            if p is not None and p.poll() is None:
                try:
                    p.kill()
                except Exception:
                    pass
            with _SOUND_LOCK:
                if gen == SOUND["gen"]:
                    SOUND["playing"] = False; SOUND["proc"] = None
            if AUDIO is not None:
                AUDIO.mute_until = time.time() + 2.0
    threading.Thread(target=work, daemon=True, name="morse-tone").start()
    return True


# ---- received text: foreign input ---------------------------------------------------------------------------------------------------
_MORSE_RX_OK = frozenset("".join(MORSE_DECODE.values()) + " " + MORSE_UNKNOWN)


def morse_clean(text):
    """a received text: only characters of the Morse table, one line, at most MORSE_RX_TEXT_MAX"""
    return " ".join("".join(c for c in str(text or "") if c in _MORSE_RX_OK).split())[:MORSE_RX_TEXT_MAX]


def morse_rx_text(text, source="camera", info=None):
    """a message is complete (from the camera; step 2: from the microphone / another MoveEye). The text is NEVER a command."""
    txt = morse_clean(text)
    if not txt or source not in MORSE_SOURCES or not morse_on():
        return False
    now = time.time()
    info = info if isinstance(info, dict) else {}
    m = {"t": datetime.now().strftime("%H:%M:%S"), "ts": now, "text": txt, "src": source, "wpm": float(info.get("wpm") or 0.0),
         "x": info.get("x"), "y": info.get("y"), "push": "", "pic": False, "test": False}
    MORSE["msgs"].appendleft(m); MORSE["last"] = m
    log_event("sys", f"Morse received ({source}, {m['wpm']:g} WPM): «{txt[:120]}»")
    if MORSE_TEST_TEXT in txt or (len(txt) <= 16 and ("TEST" in txt.split() or "VVV" in txt.split() or (len(txt) >= 4 and txt in MORSE_TEST_TEXT))):
        m["test"] = True                                     # «Gegenstelle testen»: shown on the page, no push, nothing read aloud
        MORSE["peer"] = {"t": m["t"], "ts": now, "wpm": m["wpm"], "src": source, "full": MORSE_TEST_TEXT in txt}
        return True
    if MORSE["out_n"] >= 3:
        return True                                          # the outputs are busy: the text is in the list and in the log
    MORSE["out_n"] += 1
    w = WATCH_REF.get("w")
    img = None
    try:
        if CFG.get("morse_rx_hist") and w is not None and w.frame_out is not None:
            img = w.frame_out.copy()
    except Exception:
        img = None
    threading.Thread(target=_morse_rx_out, args=(m, img), daemon=True, name="morse-rx").start()
    return True


def _morse_rx_out(m, img):
    try:
        L = norm_lang(CFG.get("lang"))
        now = m["ts"]
        if img is not None and not CFG.get("sim_on"):        # History -> Recordings: the picture with the note (like a QR card)
            try:
                d = rec_dir(); os.makedirs(d, exist_ok=True)
                name = f"morse_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{MORSE['seq'] % 1000:03d}{len(MORSE['msgs']) % 10}.jpg"
                if cv2.imwrite(os.path.join(d, name), img, [cv2.IMWRITE_JPEG_QUALITY, 88]):
                    _write_sidecar(name, {"source": "Morse", "note": "📡 " + m["text"]})
                    m["pic"] = True
            except OSError as e:
                log_event("sys", f"Morse: picture: {e}"[:160])
        if CFG.get("morse_rx_push"):                         # one push per message, text only (060 _dispatch: never a Wi-Fi name)
            MORSE["push_t"] = [t for t in MORSE["push_t"] if now - t < 3600.0]
            if (MORSE["push_t"] and now - MORSE["push_t"][-1] < MORSE_PUSH_GAP_S) or len(MORSE["push_t"]) >= MORSE_PUSH_PER_H:
                MORSE["push_held"] += 1; m["push"] = "held"
            else:
                w = WATCH_REF.get("w")
                n = getattr(w, "notifier", None) if w is not None else None
                if n is not None:
                    MORSE["push_t"].append(now)
                    p = {"event": "info", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "text": m["text"],
                         "info_title": "{name}: 📡 " + tr("Morse received", L), "obj_ic": "📡", "obj_title": tr("Morse received", L), "obj_ev": "morse",
                         "snapshot": None, "rain": False, "wind": "", "source": "", "link": ""}
                    n._dispatch(p, None, "")
                    m["push"] = "sent" if n.configured() else "list"
        if CFG.get("morse_rx_say") and now - MORSE["say_t"] >= MORSE_SAY_GAP_S and MORSE["tx"] is None:
            MORSE["say_t"] = now
            say = re.sub(r"[<>#]", " ", m["text"]).strip()[:200]
            if say:
                tts_say(say, L)
    except Exception as e:
        log_event("sys", f"Morse: output: {type(e).__name__}: {e}"[:160])
    finally:
        MORSE["out_n"] = max(0, MORSE["out_n"] - 1)


# ---- the live picture: «Morse-Modus» is unmistakable, the frame around the light, the characters as they arrive ---------------------
def _morse_label(key, text, col, hgt):
    c = MORSE["lab"].get(key)
    if c is None or c[0] != (text, hgt):
        b, a = _qrk_label_img(text, col, hgt)
        c = ((text, hgt), b, a); MORSE["lab"][key] = c
    return c[1], c[2]


def _morse_paste(frame, b, a, x, y):
    H, W = frame.shape[:2]
    lh, lw = b.shape[:2]
    if lw > W or lh > H:
        b, a = b[:H, :W], a[:H, :W]; lh, lw = b.shape[:2]
    x, y = max(0, min(W - lw, int(x))), max(0, min(H - lh, int(y)))
    roi = frame[y:y + lh, x:x + lw]
    frame[y:y + lh, x:x + lw] = (roi * (1 - a) + b * a).astype(np.uint8)


def morse_draw(frame):
    if frame is None:
        return
    try:
        H, W = frame.shape[:2]
        L = norm_lang(CFG.get("lang"))
        hgt = max(24, H // 16)
        end = datetime.fromtimestamp(MORSE["until"]).strftime("%H:%M")
        b, a = _morse_label("mode", tr("MORSE MODE – protection paused until", L) + " " + end, (40, 160, 245), hgt)
        _morse_paste(frame, b, a, 8, 42)
        if not CFG.get("morse_rx_live"):
            return
        lv, last = MORSE["live"], MORSE["last"]
        now = time.time()
        txt, pos, col = "", None, (80, 220, 90)
        if lv and lv.get("valid") and lv.get("text"):
            txt, pos = lv["text"], (lv["x"], lv["y"], lv["r"])
        elif MORSE["alive"] and MORSE["alive"].get("valid") and MORSE["alive"].get("text") and now - MORSE["a_t"] < 2.0:
            txt = "♪ " + MORSE["alive"]["text"]                # by sound: no place in the picture
        elif last and now - last["ts"] < 8.0:
            txt, pos = ("♪ " if last["src"] == "sound" else "") + last["text"], ((last["x"], last["y"], 0.03) if last.get("x") is not None else None)
        if pos:
            cx, cy, r = int(pos[0] * W), int(pos[1] * H), max(14, int(pos[2] * W))
            cv2.rectangle(frame, (cx - r, cy - r), (cx + r, cy + r), (0, 0, 0), 5, cv2.LINE_AA)
            cv2.rectangle(frame, (cx - r, cy - r), (cx + r, cy + r), col, 2, cv2.LINE_AA)
        if txt:
            b, a = _morse_label("text", ("Morse (" + tr("sound", L) + "): " if txt[:1] == "♪" else "Morse: ") + morse_clean(txt)[-40:], col, hgt)   # (no symbols: the font of the Pi may lack them)
            _morse_paste(frame, b, a, W - b.shape[1] - 8, H - b.shape[0] - 10)   # bottom right (left: the marks «LIVE» of the page)
    except (cv2.error, ValueError, TypeError, IndexError, KeyError):
        pass


_walktest_draw_morse = walktest_draw


# wraps: walktest_draw
def walktest_draw(frame):                                    # + 639zzz: the banner of the mode and the received characters
    _walktest_draw_morse(frame)
    if MORSE["until"] and morse_on():
        morse_draw(frame)


# ---- state for the page -------------------------------------------------------------------------------------------------------------
def morse_state(lang=None):
    L = norm_lang(lang or CFG.get("lang"))
    on = morse_on()
    now = time.time()
    tx = MORSE["tx"]
    rx = MORSE["rx"]
    fps = float((rx.stats if rx is not None else {}).get("fps") or 0.0) if on else float(STATE.get("fps") or 0.0)
    st = {"on": on, "rest": max(0, int(MORSE["until"] - now)) if on else 0, "until": datetime.fromtimestamp(MORSE["until"]).strftime("%H:%M:%S") if on else "",
          "by": MORSE["by"] if on else "", "max_min": MORSE_MODE_MAX_MIN, "more": on and MORSE["until"] < MORSE["t0"] + MORSE_MODE_MAX_MIN * 60.0 - 1.0,
          "armed": bool(CFG.get("armed")), "level": tr(LED_STATE_NAMES.get(protect_level_cfg(), "Off"), L), "pin": bool(CFG.get("protect_pin")) and bool(CFG.get("armed")),
          "sos": bool(ALM_SOS.get("on")), "outs": morse_outputs(L), "text_max": MORSE_TEXT_MAX, "wpm_min": MORSE_WPM_MIN, "wpm_max": MORSE_WPM_MAX,
          "note_hz": MORSE_FLASH_NOTE_HZ,
          "prefs": {k[6:]: CFG.get(k) for k in MORSE_DEF},
          "tx": None if tx is None else {"shown": tx["shown"], "wpm": tx["wpm"], "fw": tx["fw"], "outs": sorted(tx["outs"]), "total": round(tx["total"], 1),
                                        "pos": round(max(0.0, min(tx["total"], now - tx["t0"])), 1), "skipped": tx["skipped"], "by": tx["by"]},
          "rx": {"on": bool(CFG.get("morse_rx")), "fps": round(fps, 1), "limit": round(MORSE_LIMIT_K * fps, 1), "k": MORSE_LIMIT_K,
                 "sound": morse_sound_state(on, now), "peer": MORSE["peer"] if on else None, "test_text": MORSE_TEST_TEXT,
                 "live": (MORSE["live"] or {}).get("text", "") if on and (MORSE["live"] or {}).get("valid") else "",
                 "live_wpm": (MORSE["live"] or {}).get("wpm", 0) if on else 0,
                 "fast": bool(rx is not None and on and now - float(rx.stats.get("fast_t") or 0.0) < 15.0 and rx.stats.get("fast")),
                 "blink": int(rx.stats.get("periodic", 0)) if rx is not None else 0, "ms": (rx.stats.get("ms") if rx is not None else None),
                 "push_held": MORSE["push_held"],
                 "msgs": [{"t": m["t"], "text": m["text"], "wpm": m["wpm"], "src": m["src"], "pic": m["pic"], "push": m["push"], "test": bool(m.get("test"))} for m in list(MORSE["msgs"])]}}
    return st


def morse_sound_state(on, now):
    """reading by sound for the page: is there a microphone, does it deliver, the tone that is followed, the live text"""
    au = STATE.get("audio") or {}
    a, al = MORSE["arx"], MORSE["alive"] or {}
    fresh = on and now - MORSE["a_t"] < 2.0
    return {"on": bool(CFG.get("morse_rx_sound")), "mic": bool(au.get("mic")), "status": str(au.get("status") or "off")[:40], "run": bool(fresh),
            "own": bool(on and (MORSE["own_rst"][1])), "hz": int(a.stats.get("hz") or 0) if (a is not None and fresh and a.key is not None) else 0,
            "live": al.get("text", "") if fresh and al.get("valid") else "", "live_wpm": al.get("wpm", 0) if fresh else 0,
            "limit": MORSE_SOUND_WPM, "blink": int(a.stats.get("periodic", 0)) if a is not None else 0}


def morse_prefs(d):
    """the choices of the page (validated) -> saved"""
    def num(k, lo, hi, cast=int):
        if k in d:
            try:
                v = cast(float(d[k]))
            except (TypeError, ValueError):
                return
            if v == v:
                CFG["morse_" + k] = max(lo, min(hi, v))
    num("minutes", 1, MORSE_MODE_MAX_MIN); num("wpm", MORSE_WPM_MIN, MORSE_WPM_MAX); num("fw", 0, MORSE_WPM_MAX)
    for k in ("rx", "rx_live", "rx_hist", "rx_push", "rx_say", "rx_sound"):
        if k in d:
            CFG["morse_" + k] = bool(d[k])
    ids = {o["id"] for o in morse_outputs()}
    if isinstance(d.get("outs"), list):
        CFG["morse_outs"] = [o for o in dict.fromkeys(str(x) for x in d["outs"][:20]) if o in ids]
    if isinstance(d.get("ssr"), list):
        gp = {int(r["gpio"]) for r in RELAYS}
        CFG["morse_ssr"] = sorted({int(x) for x in d["ssr"][:20] if isinstance(x, int) and not isinstance(x, bool) and x in gp})
    save_settings()
    return True


# ---- ONE entry for the web API and the window: who may, the PIN, the actions ------------------------------------------------------------
def morse_may(role="admin", appkey=None, change=True):
    """only the administrator (never an app key); changing never in operator mode (390 - the web server says so as well)"""
    return role == "admin" and not appkey and not (change and CFG.get("lock_on"))


def morse_do(d, who, role="admin", appkey=None, pin=None, pin_checked=False, lang=None):
    """an action of the page or of the window -> (HTTP code, answer). pin_checked: the web server has asked for the PIN
    already (pin_guard 550 with web_disarms); the window hands the PIN over and it is checked here - the same rule:
    starting / prolonging the mode while the protection is on needs the PIN for «Aus»."""
    d = d if isinstance(d, dict) else {}
    L = norm_lang(lang or d.get("lang") or CFG.get("lang"))
    if not morse_may(role, appkey):
        return 403, {"ok": False, "error": tr("Only for the administrator", L)}
    a = str(d.get("action") or "")
    who = str(who or tr("the administrator", "en"))[:40]

    def out(ok, err="", code=None, **kw):
        return code or (200 if ok else 400), dict({"ok": ok, "error": tr_err(err, L) if err else None, "state": morse_state(L)}, **kw)
    if a in ("start", "more"):
        if not pin_checked and web_disarms("/api/morse", d) and CFG.get("protect_pin"):
            ok, err = protect_pin_check(pin, "window Morse")
            if not ok:
                return 403, {"ok": False, "error": tr(err, L), "need_pin": True}
        ok, err = morse_start(d.get("minutes"), who, more=(a == "more"))
        return out(ok, err, None if ok else 409)
    if a == "stop":
        morse_end("button", who)
        return out(True)
    if a == "prefs":
        morse_prefs(d)
        return out(True)
    if a in ("send", "plan"):
        text = d.get("text")
        if not isinstance(text, str):
            return out(False, "the text is empty")
        if a == "plan":
            plan, err = morse_plan(text, d.get("outs"), d.get("wpm"), d.get("fw"), L)
        else:
            ok, err, plan = morse_tx_start(text, d.get("outs"), d.get("wpm"), d.get("fw"), who)
        if plan is None:
            return out(False, err, 429 if err.startswith("too many") else (409 if "running" in err or "SOS" in err or "ends before" in err else 400))
        return out(True, plan={k: plan[k] for k in ("shown", "skipped", "wpm", "asked", "slow", "fw", "secs", "flash_hz", "note", "vis")})
    if a == "test":                                          # «Gegenstelle testen»: the fixed text by infrared, at most 20 WPM
        ok, err, plan = morse_tx_start(MORSE_TEST_TEXT, ["ir"], d.get("wpm") or CFG.get("morse_wpm"), 0, who)
        if plan is None:
            return out(False, err, 409 if "running" in err or "ends before" in err else (429 if err.startswith("too many") else 400))
        return out(True, plan={k: plan[k] for k in ("shown", "skipped", "wpm", "asked", "slow", "fw", "secs", "flash_hz", "note", "vis")})
    if a == "tx_stop":
        morse_tx_stop("button")
        return out(True)
    return 400, {"ok": False, "error": "unknown action"}


# ---- the web: /morse and /api/morse (only the administrator) ------------------------------------------------------------------------
_smalltv_routes_morse = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                        # + 639zzz: the Morse page and its API (only the administrator)
    _smalltv_routes_morse(app, reply, body)
    from flask import Response, request, g

    def nope():
        if not morse_may(getattr(g, "role", "admin"), getattr(g, "appkey", None), change=False):
            return reply({"ok": False, "error": tr("Only for the administrator", norm_lang(request.args.get("lang")))}, 403)
        return None

    @app.route("/api/morse", methods=["GET", "POST"])
    def api_morse():
        n = nope()
        if n is not None:
            return n
        if request.method == "GET":
            return reply({"ok": True, "state": morse_state(request.args.get("lang"))})
        code, ans = morse_do(body(), getattr(g, "user", "") or "", getattr(g, "role", "admin"), getattr(g, "appkey", None), pin_checked=True)
        return reply(ans, code)

    @app.route("/morse")
    def morse_page():
        n = nope()
        if n is not None:
            return n
        return Response(render_page(MORSE_PAGE, "more"), mimetype="text/html", headers={"Cache-Control": "no-store"})


# ---- the window (Tk): Mehr -> «Morse-Modus» - start (with the PIN), end, the time left, send with the saved choices, the received text --
if GUI_OK:
    def _morse_tk_win(self):
        w = getattr(self, "_morse_top", None)
        if w is not None and w.winfo_exists():
            w.lift(); return
        w = self._morse_top = tk.Toplevel(self.root); w.title("MoveEye – " + tr("Morse mode")); w.configure(bg=C["bg"]); w.geometry("560x520")
        st = tk.Label(w, text="", bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 11, "bold"), wraplength=520, justify="left", anchor="w")
        st.pack(fill="x", padx=12, pady=(10, 2))
        tk.Label(w, text=tr("Starting it pauses the protection for the chosen time. Nothing is watched meanwhile."), bg=C["bg"], fg=C["mut"],
                 font=("DejaVu Sans", 9), wraplength=520, justify="left", anchor="w").pack(fill="x", padx=12)
        bf = tk.Frame(w, bg=C["bg"]); bf.pack(fill="x", padx=12, pady=8)
        msg = tk.Label(w, text="", bg=C["bg"], fg=C.get("yel", "#ffd60a"), font=("DejaVu Sans", 9), wraplength=520, justify="left", anchor="w")

        def do(d, ask_pin=False):
            pin = None
            if ask_pin and CFG.get("protect_pin") and web_disarms("/api/morse", d):
                from tkinter import simpledialog
                pin = simpledialog.askstring("MoveEye", tr("PIN for switching off"), show="*", parent=w)
                if pin is None:
                    return
            code, ans = morse_do(d, "window", pin=pin)      # the same entry as the web page: rights, PIN, limits
            msg.config(text="" if ans.get("ok") else "⚠ " + str(ans.get("error") or ""))
            if ans.get("ok") and ans.get("plan"):
                p_ = ans["plan"]
                msg.config(text=f"«{p_['shown']}» · {p_['wpm']:g} WPM · {int(p_['secs'])} s" + (" · " + tr("slowed down by:") + " " + p_["slow"] if p_["slow"] else ""))
            tick(False)
        b_go = self._fbtn(bf, "▶ " + tr("Start the Morse mode"), lambda: do({"action": "start", "minutes": CFG.get("morse_minutes", 10)}, True), primary=True)
        b_go.pack(side="left", padx=(0, 6))
        self._fbtn(bf, "+ 5 min", lambda: do({"action": "more", "minutes": 5}, True)).pack(side="left", padx=(0, 6))
        self._fbtn(bf, "⏹ " + tr("End the Morse mode"), lambda: do({"action": "stop"})).pack(side="left")
        sf = tk.Frame(w, bg=C["bg"]); sf.pack(fill="x", padx=12)
        ent = tk.Entry(sf, font=("DejaVu Sans", 11)); ent.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._fbtn(sf, "📡 " + tr("Send"), lambda: do({"action": "send", "text": ent.get()[:MORSE_TEXT_MAX], "outs": CFG.get("morse_outs"),
                                                      "wpm": CFG.get("morse_wpm"), "fw": CFG.get("morse_fw")})).pack(side="left", padx=(0, 6))
        self._fbtn(sf, "⏹ " + tr("Stop"), lambda: do({"action": "tx_stop"})).pack(side="left")
        msg.pack(fill="x", padx=12, pady=(6, 0))
        self._fbtn(w, "🌐 " + tr("Outputs, speed, what happens with received text (browser)"), lambda: self._open_page("/morse")).pack(anchor="w", padx=12, pady=8)
        txt = tk.Text(w, bg=C["panel"], fg=C["txt"], font=("DejaVu Sans Mono", 11), wrap="word", bd=0, padx=10, pady=8, height=8)
        txt.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        def tick(again=True):
            try:
                if not w.winfo_exists():
                    return
                s = morse_state()
                if s["on"]:
                    st.config(text="⏸ " + tr("Morse mode is running – the protection is PAUSED") + f"  ·  {s['rest'] // 60}:{s['rest'] % 60:02d}", fg=C.get("org", "#ff9f0a"))
                else:
                    st.config(text=tr("The Morse mode is off.") + ("  ·  " + tr("Only for the administrator") if not morse_may() else ""), fg=C["txt"])
                r = s["rx"]
                body = ((r["live"] + "  (" + str(r["live_wpm"]) + " WPM)\n\n") if r["live"] else "") + "\n".join(f"{m['t']}  {m['text']}" for m in r["msgs"])
                if s["tx"]:
                    body = "📡 " + s["tx"]["shown"] + f"  {s['tx']['pos']:.0f} / {s['tx']['total']:.0f} s\n\n" + body
                if body != getattr(txt, "_last", None):
                    txt._last = body
                    txt.config(state="normal"); txt.delete("1.0", "end"); txt.insert("end", body); txt.config(state="disabled")   # plain text only
                if again:
                    w.after(1000, tick)
            except Exception:
                pass
        tick()

    App._morse_win = _morse_tk_win
    _morse_tk_more_base = App._tk_more_bar

    def _morse_tk_more_bar(self, parent):
        f = _morse_tk_more_base(self, parent)
        row = max([int(x.grid_info().get("row", 0)) for x in f.grid_slaves()] + [-1]) + 1     # under everything that is there
        self._fbtn(f, "📡 " + tr("Morse mode"), self._morse_win).grid(row=row, column=0, sticky="ew", padx=(0, 6), pady=(0, 6))
        return f

    # wraps: App._tk_more_bar (572, after 639w «Bauen» and 639zj)
    App._tk_more_bar = _morse_tk_more_bar


MORSE_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="no-referrer">
<title>MoveEye - Morse mode</title>
<style>
/*BASECSS*/
main{padding:16px;max-width:820px;margin:0 auto;box-sizing:border-box}
.mo-back{display:inline-flex;align-items:center;min-height:40px;gap:6px;text-decoration:none;color:var(--acc);font-weight:600;margin:0 0 6px}
.mo-top{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:0 0 6px}.mo-top h2{margin:0;flex:1 1 200px;font-size:20px}
.mo-st{border:2px solid var(--line);border-radius:14px;background:var(--panel);padding:12px;margin:0 0 14px;display:flex;flex-direction:column;gap:8px}
.mo-st.on{border-color:var(--org)}.mo-st .big{font-size:17px;font-weight:700;overflow-wrap:anywhere}.mo-st.on .big{color:var(--org)}
.mo-cd{font-size:30px;font-weight:700;font-variant-numeric:tabular-nums}
.mo-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.mo-row>button,.mo-row>select{min-height:44px;flex:1 1 130px;font:inherit;font-size:16px}
.mo-f{display:flex;flex-direction:column;gap:10px}.mo-f textarea{font:inherit;font-size:16px;min-height:84px;width:100%;box-sizing:border-box;resize:vertical;
background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:8px 10px}
.mo-outs{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:6px}
.mo-o{display:flex;flex-direction:column;gap:2px;border:1px solid var(--line);border-radius:10px;padding:6px 10px;min-width:0}
.mo-o.off{opacity:.55}.mo-o label{display:flex;align-items:center;gap:8px;min-height:36px;overflow-wrap:anywhere}.mo-o small{color:var(--mut);font-size:12px;overflow-wrap:anywhere}
.mo-o label.sub{font-size:13px;color:var(--mut);min-height:30px}
.mo-sl{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:center}.mo-sl input[type=range]{width:100%;min-height:40px}
.mo-sl b{font-variant-numeric:tabular-nums;white-space:nowrap}
.mo-hint{font-size:13px;color:var(--mut);overflow-wrap:anywhere}.mo-hint.bad{color:var(--red)}.mo-hint.warn{color:var(--yel)}.mo-hint.ok{color:var(--grn)}
.mo-warn{border:1px solid var(--yel);border-radius:10px;padding:8px 10px;font-size:13px}
.mo-bar{height:10px;border-radius:999px;background:var(--line);overflow:hidden}.mo-bar i{display:block;height:100%;width:0;background:var(--acc)}
.mo-chk{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:2px 12px}.mo-chk label{display:flex;align-items:center;gap:8px;min-height:40px}
.mo-live{font:600 18px/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;border:1px solid var(--line);border-radius:10px;padding:10px;min-height:48px;
overflow-wrap:anywhere;white-space:pre-wrap;background:var(--field)}
.mo-msgs{display:flex;flex-direction:column;gap:6px;margin:0;padding:0;list-style:none}.mo-msgs li{border:1px solid var(--line);border-radius:10px;padding:8px 10px}
.mo-msgs b{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;overflow-wrap:anywhere;white-space:pre-wrap;display:block}.mo-msgs small{color:var(--mut)}
section.card h3{margin:0 0 10px}details.card>summary{cursor:pointer;font-weight:600;min-height:32px}
</style></head><body>
<header>
  <h1>MoveEye</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main>
  <a class="mo-back" href="/more" id="mo-back">‹ More</a>
  <div class="mo-top"><h2 id="mo-title">📡 Morse mode</h2></div>
  <div class="mut" id="mo-intro" style="margin:0 0 12px"></div>
  <div class="mo-st" id="mo-st">…</div>
  <section class="card" id="mo-send"><h3 id="mo-send-t">Send</h3>
    <div class="mo-f">
      <textarea id="mo-text" maxlength="200" autocomplete="off" autocapitalize="characters" spellcheck="false"></textarea>
      <div class="mo-hint" id="mo-l-outs"></div>
      <div class="mo-outs" id="mo-outs"></div>
      <div class="mo-sl"><input type="range" id="mo-wpm" min="3" max="25" step="1"><b id="mo-wpm-v"></b></div>
      <div class="mo-row"><label for="mo-fw" id="mo-l-fw" class="mo-hint" style="flex:1 1 180px"></label><select id="mo-fw"></select></div>
      <div class="mo-hint" id="mo-plan"></div>
      <div class="mo-warn" id="mo-flash" hidden></div>
      <div class="mo-warn" id="mo-wear" hidden></div>
      <div id="mo-prog" hidden><div class="mo-live" id="mo-shown"></div><div class="mo-bar" style="margin-top:8px"><i id="mo-bar"></i></div></div>
      <div class="mo-row"><button type="button" id="mo-go">📡 Send</button><button type="button" class="sec" id="mo-halt" hidden>⏹ Stop</button></div>
      <div class="mo-hint bad" id="mo-err"></div>
    </div>
  </section>
  <section class="card" id="mo-recv"><h3 id="mo-recv-t">Receive</h3>
    <div class="mo-f">
      <div class="mo-chk" id="mo-chk"></div>
      <div class="mo-hint" id="mo-fps"></div>
      <div class="mo-live" id="mo-live"></div>
      <div class="mo-hint warn" id="mo-fast" hidden></div>
      <div class="mo-hint" id="mo-snd"></div>
      <ul class="mo-msgs" id="mo-msgs"></ul>
    </div>
  </section>
  <details class="card" id="mo-peer"><summary id="mo-peer-s">Test the other MoveEye (infrared)</summary>
    <ol id="mo-peer-how" class="mut"></ol>
    <div class="mo-row"><button type="button" id="mo-peer-go">Send the test signal by infrared</button></div>
    <div class="mo-hint" id="mo-peer-r"></div>
  </details>
  <details class="card"><summary id="mo-how-s">How it works</summary><ul id="mo-how" class="mut"></ul></details>
</main>
<script>
/*COMMON*/
/*MORSEDE*/
(async function () {
  try { await initAppearance(); } catch (e) {}
  const $i = id => document.getElementById(id);
  const E = (tag, cls, txt) => { const x = document.createElement(tag); if (cls) x.className = cls; if (txt != null) x.textContent = txt; return x; };
  const L = () => { try { return LANG || "de"; } catch (e) { return "de"; } };
  const api = async (b) => { try { const r = await fetch("/api/morse", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: L()}, b || {}))});
    return await r.json(); } catch (e) { return {ok: false, error: t("No connection to MoveEye.")}; } };
  document.title = "MoveEye – " + t("Morse mode");
  $i("mo-back").textContent = "‹ " + t("More");
  $i("mo-title").textContent = "📡 " + t("Morse mode");
  $i("mo-intro").textContent = t("Send a text as Morse code with a light, a relay or the loudspeaker - and read a blinking light with the camera.");
  $i("mo-send-t").textContent = t("Send"); $i("mo-recv-t").textContent = t("Receive"); $i("mo-how-s").textContent = t("How it works");
  $i("mo-l-outs").textContent = t("Outputs (several at once are possible):");
  $i("mo-l-fw").textContent = t("Longer pauses between the signs (Farnsworth):");
  $i("mo-text").placeholder = t("Text to send, e.g. SOS or <SOS>");
  $i("mo-go").textContent = "📡 " + t("Send"); $i("mo-halt").textContent = "⏹ " + t("Stop");
  ["While the Morse mode runs the protection is paused: no alarms, no push messages, no siren. It ends by itself and the protection is exactly as before - also after a power cut.",
   "Sending: dit = 1 unit, dah = 3, pauses 1 / 3 / 7. Ä Ö Ü, CH and the sharp s have their own signs. <SOS> in angle brackets is sent as one sign. Characters without a Morse sign are left out and shown.",
   "Every output has a top speed: white light and relays at most 3 flashes a second (7 WPM), a mechanical relay 4 WPM, the status LED 10 WPM, infrared 20 WPM, the tone 25 WPM. Several outputs send at the speed of the slowest.",
   "Receiving: aim a torch or a lamp at the camera and key slowly and evenly. The camera reads up to about 0.4 × its pictures per second in WPM. By hand, lengths may vary by about a third.",
   "By day a weak lamp is not read: the light must be clearly brighter than what is behind it. At night a small torch is enough.",
   "Even blinking (a car indicator) is no text. That is why a message of only E or only T («EEEE») is thrown away.",
   "By sound: a tone or a whistle near the microphone is read like a light, up to about 20 WPM. The microphone is only listened to while the Morse mode runs and «with the microphone» is chosen. No sound is stored - only the decoded text.",
   "The received text is only shown, saved, sent and read aloud - it is never carried out as a command."].forEach(s => $i("mo-how").appendChild(E("li", "", t(s))));
  $i("mo-peer-s").textContent = t("Test the other MoveEye (infrared)"); $i("mo-peer-go").textContent = "📡 " + t("Send the test signal by infrared");
  ["Two MoveEye see each other at night: each one must have the infrared light of the other in its picture.",
   "Start the Morse mode on both. On the other MoveEye the page shows «reads up to about … WPM» - set the speed here no higher.",
   "Tap «Send the test signal by infrared» here. The other MoveEye shows «Test signal of the other MoveEye read». Then swap the roles.",
   "While a MoveEye sends with a light it does not read its own light."].forEach(x => $i("mo-peer-how").appendChild(E("li", "", t(x))));
  $i("mo-peer-go").onclick = async () => { $i("mo-err").textContent = ""; const j = await api({action: "test", wpm: +$i("mo-wpm").value});
    if (j.state) J = j; if (!j.ok) $i("mo-err").textContent = j.error || ""; else { P = j; paintPlan(); } paint(); };
  let J = null, P = null, tm = 0, dirty = false, planTm = 0, busy = false;
  const fmt = s => Math.floor(s / 60) + ":" + String(Math.floor(s % 60)).padStart(2, "0");
  const outsSel = () => Array.from(document.querySelectorAll("#mo-outs input[data-o]")).filter(c => c.checked && !c.disabled).map(c => c.dataset.o);
  const ssrSel = () => Array.from(document.querySelectorAll("#mo-outs input[data-ssr]")).filter(c => c.checked).map(c => +c.dataset.ssr);
  const savePrefs = extra => api(Object.assign({action: "prefs", outs: outsSel(), ssr: ssrSel(), wpm: +$i("mo-wpm").value, fw: +$i("mo-fw").value}, extra || {}));
  function paintMode() {
    const s = J.state, b = $i("mo-st"); b.textContent = ""; b.classList.toggle("on", s.on);
    if (s.on) {
      b.appendChild(E("div", "big", "⏸ " + t("Morse mode is running – the protection is PAUSED")));
      b.appendChild(E("div", "mo-cd", fmt(s.rest)));
      b.appendChild(E("div", "mo-hint", t("Ends by itself at") + " " + s.until + " · " + t("started by") + " " + s.by + " · " + t("then the protection is again:") + " " + s.level));
      const r = E("div", "mo-row"), x = E("button", "", "⏹ " + t("End the Morse mode")), m = E("button", "sec", "+ 5 min");
      x.type = m.type = "button";
      x.onclick = async () => { x.disabled = true; J = await api({action: "stop"}); paint(); };
      m.disabled = !s.more; m.title = s.more ? "" : t("The longest time is reached.");
      m.onclick = async () => { m.disabled = true; const j = await api({action: "more", minutes: 5}); if (j.state) J = j; $i("mo-err").textContent = j.ok ? "" : (j.error || ""); paint(); };
      r.append(x, m); b.appendChild(r);
    } else {
      b.appendChild(E("div", "big", t("The Morse mode is off.")));
      b.appendChild(E("div", "mo-hint", t("Starting it pauses the protection for the chosen time. Nothing is watched meanwhile.") + (s.armed ? " " + t("Now:") + " " + s.level + "." : "")));
      const r = E("div", "mo-row"), sel = E("select"), go = E("button", "", "▶ " + t("Start the Morse mode"));
      [2, 5, 10, 15, 20, 30].filter(m => m <= s.max_min).forEach(m => { const o = E("option", "", m + " min"); o.value = m; if (m === s.prefs.minutes) o.selected = true; sel.appendChild(o); });
      sel.id = "mo-min"; sel.setAttribute("aria-label", t("Minutes")); go.type = "button";
      go.onclick = async () => { go.disabled = true; const j = await api({action: "start", minutes: +sel.value}); go.disabled = false;
        if (j.state) J = j; $i("mo-err").textContent = j.ok ? "" : (j.error || ""); if (j.ok) api({action: "prefs", minutes: +sel.value}); paint(); };
      r.append(sel, go); b.appendChild(r);
    }
  }
  function paintOuts() {
    const box = $i("mo-outs"), s = J.state; if (box.childElementCount && dirty) return; box.textContent = "";
    s.outs.forEach(o => { const d = E("div", "mo-o" + (o.ok ? "" : " off")), lab = E("label"), cb = E("input"); cb.type = "checkbox"; cb.dataset.o = o.id;
      cb.disabled = !o.ok; cb.checked = o.ok && (s.prefs.outs || []).indexOf(o.id) >= 0; cb.onchange = () => { dirty = true; savePrefs(); plan(); };
      lab.append(cb, E("span", "", o.name)); d.appendChild(lab);
      d.appendChild(E("small", "", o.ok ? t("up to") + " " + o.wpm + " WPM (" + o.hz + " " + t("flashes a second") + ")" : o.why));
      if (o.kind.indexOf("relay") === 0) { const l2 = E("label", "sub"), c2 = E("input"); c2.type = "checkbox"; c2.dataset.ssr = o.id.slice(6); c2.checked = !!o.ssr;
        c2.onchange = async () => { J = await savePrefs(); dirty = false; paintOuts(); plan(); }; l2.append(c2, E("span", "", t("solid-state relay (no contacts)"))); d.appendChild(l2); }
      box.appendChild(d); });
  }
  function paintTx() {
    const s = J.state, tx = s.tx;
    $i("mo-prog").hidden = !tx; $i("mo-halt").hidden = !tx; $i("mo-go").disabled = !s.on || !!tx || busy;
    $i("mo-go").title = s.on ? "" : t("Start the Morse mode first.");
    if (tx) { $i("mo-shown").textContent = tx.shown + "  ·  " + tx.wpm + " WPM  ·  " + fmt(tx.pos) + " / " + fmt(tx.total); $i("mo-bar").style.width = Math.min(100, 100 * tx.pos / Math.max(1, tx.total)) + "%"; }
  }
  function paintRx() {
    const s = J.state, r = s.rx, box = $i("mo-chk");
    if (!box.childElementCount) [["rx", "Read a blinking light with the camera"], ["rx_live", "Show in the live picture"], ["rx_hist", "Save in the history with a picture"],
      ["rx_push", "Push message to the phone (text only)"], ["rx_say", "Read aloud on the loudspeaker"],
      ["rx_sound", "Read a tone or a whistle with the microphone"]].forEach(([k, txt]) => { const lab = E("label"), cb = E("input"); cb.type = "checkbox";
        cb.dataset.k = k; cb.checked = !!s.prefs[k]; cb.onchange = async () => { const b = {action: "prefs"}; b[k] = cb.checked; const j = await api(b); if (j.state) J = j; paintRx(); }; lab.append(cb, E("span", "", t(txt))); box.appendChild(lab); });
    $i("mo-fps").textContent = !r.on ? t("Reading is switched off.") : !s.on ? t("Reading runs only while the Morse mode is on.")
      : t("The camera now delivers") + " " + r.fps + " " + t("pictures a second - it reads up to about") + " " + Math.max(1, Math.floor(r.limit)) + " WPM.";
    $i("mo-live").textContent = r.live ? r.live + "  (" + r.live_wpm + " WPM)" : (s.on && r.on ? "… " + t("waiting for a blinking light") : "–");
    $i("mo-fast").hidden = !r.fast; $i("mo-fast").textContent = t("A light blinks too fast for the camera - key more slowly.");
    const sd = r.sound, se = $i("mo-snd");                     // step 2: by sound
    se.textContent = !sd.on ? "" : "🎤 " + (!sd.mic ? t("No microphone is chosen (Settings → Sound).") : !s.on ? t("Reading runs only while the Morse mode is on.")
      : sd.own ? t("MoveEye plays a sound itself - not listening meanwhile.") : !sd.run ? t("The microphone delivers no sound.") + " (" + sd.status + ")"
      : (sd.live ? sd.live + "  (" + sd.live_wpm + " WPM, " + sd.hz + " Hz)" : sd.hz ? t("a tone at") + " " + sd.hz + " Hz …" : t("listening for a tone or a whistle"))
        + " · " + t("reads up to about") + " " + sd.limit + " WPM. " + t("No sound is stored - only the decoded text."));
    const pe = $i("mo-peer-r"), p = r.peer;
    pe.textContent = !p ? (s.on ? t("No test signal of the other MoveEye read yet.") : "") : (p.full ? "✓ " + t("Test signal of the other MoveEye read") : "◐ " + t("Test signal read only in part - send more slowly or aim better"))
      + " · " + p.t + " · " + p.wpm + " WPM";
    pe.className = "mo-hint" + (p && p.full ? " ok" : p ? " warn" : "");
    $i("mo-peer-go").disabled = !s.on || !!s.tx || !(s.outs.find(o => o.id === "ir") || {}).ok;
    const ul = $i("mo-msgs"); ul.textContent = "";
    r.msgs.forEach(m => { const li = E("li"); li.appendChild(E("b", "", m.text));
      li.appendChild(E("small", "", (m.src === "sound" ? "🎤 " : "💡 ") + m.t + " · " + m.wpm + " WPM" + (m.test ? " · " + t("test signal") : "") + (m.pic ? " · 🖼 " + t("in the history") : "") + (m.push === "sent" ? " · 📲 " + t("push sent") : m.push === "held" ? " · " + t("push held back (too many)") : ""))); ul.appendChild(li); });
  }
  function paintPlan() {
    const el = $i("mo-plan"), f = $i("mo-flash"), w = $i("mo-wear"); f.hidden = true; w.hidden = true;
    if (!P) { el.textContent = ""; return; }
    if (!P.ok) { el.textContent = P.error || ""; el.className = "mo-hint bad"; return; }
    const p = P.plan; el.className = "mo-hint";
    el.textContent = "«" + p.shown + "» · " + p.wpm + " WPM · " + fmt(p.secs) + (p.slow ? " · " + t("slowed down by:") + " " + p.slow : "")
      + (p.skipped.length ? " · " + t("left out (no Morse sign):") + " " + p.skipped.join(" ") : "");
    if (p.vis) { f.hidden = false; f.textContent = "⚠ " + (p.note ? t("Flashing light, about 3 flashes a second: it can trigger seizures in people with photosensitive epilepsy. Do not aim it at people.")
      : t("Flashing light: do not aim it at people or at the road.")); }
    if (outsSel().some(o => o.indexOf("relay:") === 0) && ssrSel().length < outsSel().filter(o => o.indexOf("relay:") === 0).length) { w.hidden = false;
      w.textContent = "⚙ " + t("A mechanical relay wears: this text switches it about") + " " + Math.round(p.shown.replace(/ /g, "").length * 2.6) + " " + t("times."); }
  }
  function plan() {
    clearTimeout(planTm);
    planTm = setTimeout(async () => { const txt = $i("mo-text").value; if (!txt.trim()) { P = null; paintPlan(); return; }
      P = await api({action: "plan", text: txt, outs: outsSel(), wpm: +$i("mo-wpm").value, fw: +$i("mo-fw").value}); paintPlan(); }, 250);
  }
  function paint() { if (!J || !J.state) return; paintMode(); paintOuts(); paintTx(); paintRx(); }
  async function load() {
    clearTimeout(tm);
    let j = null; try { j = await (await fetch("/api/morse?lang=" + encodeURIComponent(L()), {cache: "no-store"})).json(); } catch (e) {}
    if (j && j.ok) { J = j; paint(); } else if (!J) { $i("mo-st").textContent = "⚠ " + ((j && j.error) || t("Only for the administrator")); }
    tm = setTimeout(load, J && J.state && J.state.on ? 1000 : 5000);          // asking never makes the mode longer
  }
  try { J = await (await fetch("/api/morse?lang=" + encodeURIComponent(L()), {cache: "no-store"})).json(); } catch (e) { J = null; }
  if (!J || !J.ok) { $i("mo-st").textContent = "⚠ " + ((J && J.error) || t("Only for the administrator")); return; }
  const s0 = J.state, wp = $i("mo-wpm"), fw = $i("mo-fw");
  wp.min = s0.wpm_min; wp.max = s0.wpm_max; wp.value = s0.prefs.wpm; wp.setAttribute("aria-label", "WPM"); $i("mo-text").maxLength = s0.text_max;
  const wv = () => { $i("mo-wpm-v").textContent = wp.value + " WPM"; };
  wv(); wp.oninput = () => { wv(); plan(); }; wp.onchange = () => savePrefs();
  [0, 3, 4, 5, 6, 8, 10].forEach(v => { const o = E("option", "", v ? t("like") + " " + v + " WPM" : t("off")); o.value = v; if (v === s0.prefs.fw) o.selected = true; fw.appendChild(o); });
  fw.onchange = () => { savePrefs(); plan(); };
  $i("mo-text").oninput = plan;
  $i("mo-go").onclick = async () => { busy = true; $i("mo-go").disabled = true; $i("mo-err").textContent = "";
    const j = await api({action: "send", text: $i("mo-text").value, outs: outsSel(), wpm: +wp.value, fw: +fw.value}); busy = false;
    if (j.state) J = j; if (!j.ok) $i("mo-err").textContent = j.error || ""; else { P = j; paintPlan(); } paint(); };
  $i("mo-halt").onclick = async () => { const j = await api({action: "tx_stop"}); if (j.state) J = j; paint(); };
  paint(); tm = setTimeout(load, 1000);
})();
</script>
</body></html>
"""

MORSE_MORE_ITEM = ('<a class="mi" href="/morse" id="m-morse"><i>📡</i><span><b data-i18n="Morse mode">Morse mode</b>'
                   '<small data-i18n="Send and read Morse code with light and sound">Send and read Morse code with light and sound</small></span><span class="ar">›</span></a>\n  ')

_render_page_morse = render_page


# wraps: render_page
def render_page(page, active):                               # + 639zzz: the German texts of the Morse page, its item under «Mehr» (administrator)
    out = _render_page_morse(page, active)
    if "/*MORSEDE*/" in out:
        out = out.replace("/*MORSEDE*/", "Object.assign(I18N.de, " + json.dumps(_MORSE_DE, ensure_ascii=False).replace("</", "<\\/") + ");", 1)
    if active == "more" and 'href="/morse"' not in out and '<a class="mi" href="/tools">' in out:
        try:
            from flask import g as _g
            admin = qrk_admin_ok(_g)
        except Exception:
            admin = False
        if admin:
            i = out.find('<a class="mi" href="/tools">')
            out = (out[:i] + MORSE_MORE_ITEM + out[i:]).replace("</body>", "<script>Object.assign(I18N.de, " + json.dumps(
                {k: _MORSE_DE[k] for k in ("Morse mode", "Send and read Morse code with light and sound")}, ensure_ascii=False) + ");</script></body>", 1)
    return out


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
# ---- texts (English key: Deutsch, français, italiano, rumantsch) ----
# texts the program itself shows (banner in the live picture, state, push, outputs)
_HX_MORSE = {
    "Morse mode": ("Morse-Modus", "Mode morse", "Modalità Morse", "Modus da morse"),
    "the administrator": ("dem Administrator", "l’administrateur", "l’amministratore", "l’administratur"),
    "White light": ("Weisses Licht", "Lumière blanche", "Luce bianca", "Glisch alva"),
    "Infrared light": ("Infrarot-Licht", "Lumière infrarouge", "Luce a infrarossi", "Glisch infracotschna"),
    "Status LED": ("Status-LED", "LED d’état", "LED di stato", "LED da status"),
    "Loudspeaker (tone)": ("Lautsprecher (Ton)", "Haut-parleur (son)", "Altoparlante (suono)", "Autpledader (tun)"),
    "not connected": ("nicht angeschlossen", "non connecté", "non collegato", "betg collià"),
    "no loudspeaker selected": ("kein Lautsprecher gewählt", "aucun haut-parleur choisi", "nessun altoparlante scelto", "nagin autpledader tschernì"),
    "MORSE MODE – protection paused until": ("MORSE-MODUS – Schutz pausiert bis", "MODE MORSE – protection en pause jusqu’à", "MODALITÀ MORSE – protezione in pausa fino alle", "MODUS DA MORSE – protecziun en pausa fin"),
    "Outputs, speed, what happens with received text (browser)": ("Ausgänge, Tempo, was mit empfangenem Text geschieht (Browser)", "Sorties, vitesse, que faire du texte reçu (navigateur)", "Uscite, velocità, cosa fare del testo ricevuto (browser)", "Sortidas, tempo, tge che capita cun il text retschavì (browser)"),
    "Morse received": ("Morse empfangen", "Morse reçu", "Morse ricevuto", "Morse retschavì"),
    "Only for the administrator": ("Nur für den Administrator", "Réservé à l’administrateur", "Solo per l’amministratore", "Mo per l’administratur"),
    "Start the Morse mode": ("Morse-Modus starten", "Démarrer le mode morse", "Avviare la modalità Morse", "Aviar il modus da morse"),
    "End the Morse mode": ("Morse-Modus beenden", "Terminer le mode morse", "Terminare la modalità Morse", "Finir il modus da morse"),
    "The Morse mode is off.": ("Der Morse-Modus ist aus.", "Le mode morse est désactivé.", "La modalità Morse è spenta.", "Il modus da morse è ora."),
    "Morse mode is running – the protection is PAUSED": ("Morse-Modus läuft – der Schutz ist PAUSIERT", "Le mode morse est actif – la protection est EN PAUSE", "La modalità Morse è attiva – la protezione è IN PAUSA", "Il modus da morse è activ – la protecziun è EN PAUSA"),
    "Starting it pauses the protection for the chosen time. Nothing is watched meanwhile.": ("Beim Starten wird der Schutz für die gewählte Zeit pausiert. In dieser Zeit wird nichts bewacht.", "Au démarrage, la protection est mise en pause pour la durée choisie. Rien n’est surveillé pendant ce temps.", "All’avvio la protezione va in pausa per il tempo scelto. Nel frattempo non viene sorvegliato nulla.", "Cun aviar vegn la protecziun messa en pausa per il temp tschernì. En quel temp na vegn surveglià nagut."),
    "slowed down by:": ("gebremst durch:", "ralenti par :", "rallentato da:", "franà da:"),
    "Send": ("Senden", "Envoyer", "Inviare", "Trametter"),
    "Stop": ("Stopp", "Stop", "Stop", "Stop"),
}
# the texts of the page /morse and the answers of /api/morse - with the page in the data file
MORSE_PAGE_TEXTS = {
    "Send and read Morse code with light and sound": ("Morsezeichen senden und lesen, mit Licht und Ton", "Envoyer et lire du morse, avec lumière et son", "Inviare e leggere il Morse, con luce e suono", "Trametter e leger morse, cun glisch e tun"),
    "Send a text as Morse code with a light, a relay or the loudspeaker - and read a blinking light with the camera.": ("Einen Text als Morsezeichen senden, mit einem Licht, einem Relais oder dem Lautsprecher – und ein blinkendes Licht mit der Kamera lesen.", "Envoyer un texte en morse avec une lumière, un relais ou le haut-parleur – et lire une lumière clignotante avec la caméra.", "Inviare un testo in Morse con una luce, un relè o l’altoparlante – e leggere una luce lampeggiante con la telecamera.", "Trametter in text en morse cun ina glisch, in relais u l’autpledader – e leger ina glisch che traglischa cun la camera."),
    "Receive": ("Empfangen", "Recevoir", "Ricevere", "Retschaiver"),
    "More": ("Mehr", "Plus", "Altro", "Dapli"),
    "Minutes": ("Minuten", "Minutes", "Minuti", "Minutas"),
    "How it works": ("So funktioniert es", "Comment ça marche", "Come funziona", "Uschia funcziuni"),
    "off": ("aus", "désactivé", "spento", "ora"),
    "like": ("wie", "comme", "come", "sco"),
    "up to": ("bis", "jusqu’à", "fino a", "fin"),
    "times.": ("mal.", "fois.", "volte.", "giadas."),
    "Now:": ("Jetzt:", "Maintenant :", "Adesso:", "Ussa:"),
    "started by": ("gestartet von", "démarré par", "avviata da", "avià da"),
    "flashes a second": ("Blitze pro Sekunde", "éclairs par seconde", "lampi al secondo", "chametgs per secunda"),
    "solid-state relay (no contacts)": ("Halbleiter-Relais (ohne Kontakte)", "relais statique (sans contacts)", "relè a stato solido (senza contatti)", "relais electronic (senza contacts)"),
    "Outputs (several at once are possible):": ("Ausgänge (mehrere zugleich sind möglich):", "Sorties (plusieurs à la fois possibles) :", "Uscite (anche più insieme):", "Sortidas (pliras a medem temp pussaivel):"),
    "Longer pauses between the signs (Farnsworth):": ("Längere Pausen zwischen den Zeichen (Farnsworth):", "Pauses plus longues entre les signes (Farnsworth) :", "Pause più lunghe tra i segni (Farnsworth):", "Pausas pli lungas tranter ils segns (Farnsworth):"),
    "Text to send, e.g. SOS or <SOS>": ("Text zum Senden, z. B. SOS oder <SOS>", "Texte à envoyer, p. ex. SOS ou <SOS>", "Testo da inviare, p. es. SOS o <SOS>", "Text per trametter, p. ex. SOS u <SOS>"),
    "left out (no Morse sign):": ("ausgelassen (kein Morsezeichen):", "omis (pas de signe morse) :", "omessi (nessun segno Morse):", "laschà ora (nagin segn da morse):"),
    "Flashing light, about 3 flashes a second: it can trigger seizures in people with photosensitive epilepsy. Do not aim it at people.": ("Blinklicht, rund 3 Blitze pro Sekunde: es kann bei Menschen mit lichtempfindlicher Epilepsie Anfälle auslösen. Nicht auf Menschen richten.", "Lumière clignotante, environ 3 éclairs par seconde : elle peut provoquer des crises chez les personnes épileptiques photosensibles. Ne pas la diriger vers des personnes.", "Luce lampeggiante, circa 3 lampi al secondo: può provocare crisi nelle persone con epilessia fotosensibile. Non puntarla sulle persone.", "Glisch che traglischa, circa 3 chametgs per secunda: ella po chaschunar attatgas tar persunas cun epilepsia fotosensibla. Betg drizzar sin persunas."),
    "Flashing light: do not aim it at people or at the road.": ("Blinklicht: nicht auf Menschen oder auf die Strasse richten.", "Lumière clignotante : ne pas la diriger vers des personnes ni vers la route.", "Luce lampeggiante: non puntarla sulle persone o sulla strada.", "Glisch che traglischa: betg drizzar sin persunas u sin la via."),
    "A mechanical relay wears: this text switches it about": ("Ein mechanisches Relais nützt sich ab: dieser Text schaltet es etwa", "Un relais mécanique s’use : ce texte le commute environ", "Un relè meccanico si consuma: questo testo lo commuta circa", "In relais mecanic sa disfa: quest text al commutescha circa"),
    "Ends by itself at": ("Endet von selbst um", "Se termine automatiquement à", "Termina da sola alle", "Finescha da sasez a las"),
    "then the protection is again:": ("danach ist der Schutz wieder:", "ensuite la protection est de nouveau :", "poi la protezione è di nuovo:", "suenter è la protecziun puspè:"),
    "Start the Morse mode first.": ("Zuerst den Morse-Modus starten.", "Démarrez d’abord le mode morse.", "Avvia prima la modalità Morse.", "Avia l’emprim il modus da morse."),
    "The longest time is reached.": ("Die längste Zeit ist erreicht.", "La durée maximale est atteinte.", "La durata massima è raggiunta.", "Il temp maximal è cuntanschì."),
    "Read a blinking light with the camera": ("Ein blinkendes Licht mit der Kamera lesen", "Lire une lumière clignotante avec la caméra", "Leggere una luce lampeggiante con la telecamera", "Leger ina glisch che traglischa cun la camera"),
    "Show in the live picture": ("Im Live-Bild zeigen", "Afficher dans l’image en direct", "Mostrare nell’immagine live", "Mussar en il maletg live"),
    "Save in the history with a picture": ("Im Verlauf speichern, mit Bild", "Enregistrer dans l’historique, avec image", "Salvare nella cronologia, con immagine", "Memorisar en la cronologia, cun maletg"),
    "Push message to the phone (text only)": ("Push-Nachricht aufs Handy (nur Text)", "Notification push sur le portable (texte seul)", "Notifica push sul telefono (solo testo)", "Push sin il telefonin (mo text)"),
    "Read aloud on the loudspeaker": ("Über den Lautsprecher vorlesen", "Lire à voix haute sur le haut-parleur", "Leggere ad alta voce dall’altoparlante", "Preleger sur l’autpledader"),
    "Reading is switched off.": ("Das Lesen ist ausgeschaltet.", "La lecture est désactivée.", "La lettura è spenta.", "Il leger è ora."),
    "Reading runs only while the Morse mode is on.": ("Gelesen wird nur, solange der Morse-Modus läuft.", "La lecture ne fonctionne que pendant le mode morse.", "La lettura funziona solo con la modalità Morse attiva.", "Legì vegn mo durant il modus da morse."),
    "The camera now delivers": ("Die Kamera liefert jetzt", "La caméra fournit actuellement", "La telecamera fornisce ora", "La camera furnescha ussa"),
    "pictures a second - it reads up to about": ("Bilder pro Sekunde – sie liest bis etwa", "images par seconde – elle lit jusqu’à environ", "immagini al secondo – legge fino a circa", "maletgs per secunda – ella legia fin circa"),
    "waiting for a blinking light": ("wartet auf ein blinkendes Licht", "en attente d’une lumière clignotante", "in attesa di una luce lampeggiante", "spetga ina glisch che traglischa"),
    "A light blinks too fast for the camera - key more slowly.": ("Ein Licht blinkt zu schnell für die Kamera – langsamer tasten.", "Une lumière clignote trop vite pour la caméra – manipulez plus lentement.", "Una luce lampeggia troppo in fretta per la telecamera – battere più lentamente.", "Ina glisch traglischa memia svelt per la camera – tastar pli plaun."),
    "in the history": ("im Verlauf", "dans l’historique", "nella cronologia", "en la cronologia"),
    "push sent": ("Push gesendet", "push envoyé", "push inviato", "push tramess"),
    "push held back (too many)": ("Push zurückgehalten (zu viele)", "push retenu (trop nombreux)", "push trattenuto (troppi)", "push retegnì (memia blers)"),
    "No connection to MoveEye.": ("Keine Verbindung zu MoveEye.", "Pas de connexion à MoveEye.", "Nessuna connessione con MoveEye.", "Nagina colliaziun cun MoveEye."),
    "While the Morse mode runs the protection is paused: no alarms, no push messages, no siren. It ends by itself and the protection is exactly as before - also after a power cut.": ("Solange der Morse-Modus läuft, ist der Schutz pausiert: keine Alarme, keine Push-Nachrichten, keine Sirene. Er endet von selbst, und der Schutz ist genau wie vorher – auch nach einem Stromausfall.", "Tant que le mode morse est actif, la protection est en pause : pas d’alarmes, pas de notifications, pas de sirène. Il se termine tout seul et la protection est exactement comme avant – aussi après une coupure de courant.", "Finché la modalità Morse è attiva la protezione è in pausa: niente allarmi, niente notifiche, niente sirena. Termina da sola e la protezione è esattamente come prima – anche dopo un’interruzione di corrente.", "Uschè ditg ch’il modus da morse è activ, è la protecziun en pausa: nagins alarms, nagins push, nagina sirena. El finescha da sasez e la protecziun è exact sco avant – er suenter in’interrupziun da current."),
    "Sending: dit = 1 unit, dah = 3, pauses 1 / 3 / 7. Ä Ö Ü, CH and the sharp s have their own signs. <SOS> in angle brackets is sent as one sign. Characters without a Morse sign are left out and shown.": ("Senden: dit = 1 Einheit, dah = 3, Pausen 1 / 3 / 7. Ä Ö Ü, CH und das Eszett haben eigene Zeichen. <SOS> in spitzen Klammern wird als ein Zeichen gesendet. Zeichen ohne Morsezeichen werden ausgelassen und angezeigt.", "Envoi : point = 1 unité, trait = 3, pauses 1 / 3 / 7. Ä Ö Ü, CH et l’eszett ont leurs propres signes. <SOS> entre chevrons est envoyé comme un seul signe. Les caractères sans signe morse sont omis et indiqués.", "Invio: punto = 1 unità, linea = 3, pause 1 / 3 / 7. Ä Ö Ü, CH e l’eszett hanno segni propri. <SOS> tra parentesi angolari è inviato come un solo segno. I caratteri senza segno Morse sono omessi e indicati.", "Trametter: punct = 1 unitad, stritg = 3, pausas 1 / 3 / 7. Ä Ö Ü, CH e l’eszett han agens segns. <SOS> en parantesas agüzzas vegn tramess sco in segn. Caracters senza segn da morse vegnan laschads ora e mussads."),
    "Every output has a top speed: white light and relays at most 3 flashes a second (7 WPM), a mechanical relay 4 WPM, the status LED 10 WPM, infrared 20 WPM, the tone 25 WPM. Several outputs send at the speed of the slowest.": ("Jeder Ausgang hat ein Höchsttempo: weisses Licht und Relais höchstens 3 Blitze pro Sekunde (7 WPM), ein mechanisches Relais 4 WPM, die Status-LED 10 WPM, Infrarot 20 WPM, der Ton 25 WPM. Mehrere Ausgänge senden im Tempo des langsamsten.", "Chaque sortie a une vitesse maximale : lumière blanche et relais au plus 3 éclairs par seconde (7 WPM), un relais mécanique 4 WPM, la LED d’état 10 WPM, l’infrarouge 20 WPM, le son 25 WPM. Plusieurs sorties émettent à la vitesse de la plus lente.", "Ogni uscita ha una velocità massima: luce bianca e relè al massimo 3 lampi al secondo (7 WPM), un relè meccanico 4 WPM, il LED di stato 10 WPM, l’infrarosso 20 WPM, il suono 25 WPM. Più uscite trasmettono alla velocità della più lenta.", "Mintga sortida ha in tempo maximal: glisch alva e relais maximalmain 3 chametgs per secunda (7 WPM), in relais mecanic 4 WPM, la LED da status 10 WPM, infracotschen 20 WPM, il tun 25 WPM. Pliras sortidas tramettan en il tempo da la pli plauna."),
    "Receiving: aim a torch or a lamp at the camera and key slowly and evenly. The camera reads up to about 0.4 × its pictures per second in WPM. By hand, lengths may vary by about a third.": ("Empfangen: eine Taschenlampe oder Lampe auf die Kamera richten und langsam und gleichmässig tasten. Die Kamera liest bis etwa 0.4 × ihre Bilder pro Sekunde in WPM. Von Hand dürfen die Längen um etwa ein Drittel schwanken.", "Réception : dirigez une lampe de poche ou une lampe vers la caméra et manipulez lentement et régulièrement. La caméra lit jusqu’à environ 0,4 × ses images par seconde en WPM. À la main, les durées peuvent varier d’environ un tiers.", "Ricezione: punta una torcia o una lampada verso la telecamera e batti lentamente e in modo regolare. La telecamera legge fino a circa 0,4 × le sue immagini al secondo in WPM. A mano le durate possono variare di circa un terzo.", "Retschaiver: drizzar ina lampa da giaglioffa u ina lampa sin la camera e tastar plaun e regularmain. La camera legia fin circa 0,4 × ses maletgs per secunda en WPM. A maun pon las lunghezzas variar per circa in terz."),
    "By day a weak lamp is not read: the light must be clearly brighter than what is behind it. At night a small torch is enough.": ("Am Tag wird eine schwache Lampe nicht gelesen: das Licht muss deutlich heller sein als das, was dahinter ist. In der Nacht genügt eine kleine Taschenlampe.", "De jour, une lampe faible n’est pas lue : la lumière doit être nettement plus claire que l’arrière-plan. La nuit, une petite lampe de poche suffit.", "Di giorno una lampada debole non viene letta: la luce deve essere nettamente più chiara dello sfondo. Di notte basta una piccola torcia.", "Da di na vegn ina lampa flaivla betg legida: la glisch sto esser cleramain pli clera che quai ch’è davos. La notg basta ina pitschna lampa da giaglioffa."),
    "Even blinking (a car indicator) is no text. That is why a message of only E or only T («EEEE») is thrown away.": ("Gleichmässiges Blinken (der Blinker eines Autos) ist kein Text. Darum wird eine Nachricht nur aus E oder nur aus T («EEEE») verworfen.", "Un clignotement régulier (le clignotant d’une voiture) n’est pas un texte. C’est pourquoi un message composé uniquement de E ou de T («EEEE») est rejeté.", "Un lampeggio regolare (la freccia di un’auto) non è un testo. Per questo un messaggio di sole E o sole T («EEEE») viene scartato.", "In traglischar regular (il blinker d’in auto) n’è nagin text. Perquai vegn in messadi mo cun E u mo cun T («EEEE») sbittà."),
    "The received text is only shown, saved, sent and read aloud - it is never carried out as a command.": ("Der empfangene Text wird nur angezeigt, gespeichert, gesendet und vorgelesen – er wird nie als Befehl ausgeführt.", "Le texte reçu est seulement affiché, enregistré, envoyé et lu – il n’est jamais exécuté comme une commande.", "Il testo ricevuto viene solo mostrato, salvato, inviato e letto – non viene mai eseguito come comando.", "Il text retschavì vegn mo mussà, memorisà, tramess e prelegì – el na vegn mai exequì sco cumond."),
    "not a number": ("keine Zahl", "pas un nombre", "non è un numero", "nagin dumber"),
    "the Morse mode is not running": ("der Morse-Modus läuft nicht", "le mode morse n’est pas actif", "la modalità Morse non è attiva", "il modus da morse n’è betg activ"),
    "the Morse mode is already running": ("der Morse-Modus läuft schon", "le mode morse est déjà actif", "la modalità Morse è già attiva", "il modus da morse è gia activ"),
    "the Morse mode cannot run longer - start it again when it has ended": ("der Morse-Modus kann nicht länger laufen – nach dem Ende neu starten", "le mode morse ne peut pas durer plus longtemps – redémarrez-le après la fin", "la modalità Morse non può durare di più – riavviala quando è terminata", "il modus da morse na po betg durar pli ditg – aviar danovamain suenter la fin"),
    "not now - the camera rests": ("jetzt nicht – die Kamera ruht", "pas maintenant – la caméra est au repos", "non ora – la telecamera è a riposo", "betg ussa – la camera paussa"),
    "the text is too long": ("der Text ist zu lang", "le texte est trop long", "il testo è troppo lungo", "il text è memia lung"),
    "the text is empty": ("der Text ist leer", "le texte est vide", "il testo è vuoto", "il text è vid"),
    "no character of this text has a Morse sign": ("kein Zeichen dieses Textes hat ein Morsezeichen", "aucun caractère de ce texte n’a de signe morse", "nessun carattere di questo testo ha un segno Morse", "nagin caracter da quest text ha in segn da morse"),
    "choose at least one output": ("mindestens einen Ausgang wählen", "choisissez au moins une sortie", "scegli almeno un’uscita", "tscherna almain ina sortida"),
    "an output you chose is not connected": ("ein gewählter Ausgang ist nicht angeschlossen", "une sortie choisie n’est pas connectée", "un’uscita scelta non è collegata", "ina sortida tschernida n’è betg colliada"),
    "this takes too long - a shorter text or faster": ("das dauert zu lange – kürzerer Text oder schneller", "c’est trop long – texte plus court ou plus rapide", "dura troppo – testo più corto o più veloce", "quai dura memia ditg – text pli curt u pli svelt"),
    "a transmission is running": ("eine Sendung läuft", "une émission est en cours", "una trasmissione è in corso", "ina transmissiun è en curs"),
    "too many transmissions - wait a minute": ("zu viele Sendungen – eine Minute warten", "trop d’émissions – attendez une minute", "troppe trasmissioni – attendi un minuto", "memia bleras transmissiuns – spetgar ina minuta"),
    "the SOS lamp is flashing - it goes first": ("die SOS-Lampe blinkt – sie geht vor", "la lampe SOS clignote – elle a la priorité", "la lampada SOS lampeggia – ha la precedenza", "la lampa SOS traglischa – ella ha la precedenza"),
    "the Morse mode ends before this text is sent - make it longer first": ("der Morse-Modus endet, bevor dieser Text gesendet ist – zuerst verlängern", "le mode morse se termine avant la fin de ce texte – prolongez-le d’abord", "la modalità Morse termina prima che il testo sia inviato – prima prolungala", "il modus da morse finescha avant che quest text è tramess – l’emprim prolungar"),
    "Read a tone or a whistle with the microphone": ("Einen Ton oder Pfiff mit dem Mikrofon lesen", "Lire un son ou un sifflement avec le microphone", "Leggere un suono o un fischio con il microfono", "Leger in tun u in tschivel cun il microfon"),
    "No microphone is chosen (Settings → Sound).": ("Kein Mikrofon gewählt (Einstellungen → Ton).", "Aucun microphone choisi (Réglages → Son).", "Nessun microfono scelto (Impostazioni → Suono).", "Nagin microfon tschernì (Parameters → Tun)."),
    "MoveEye plays a sound itself - not listening meanwhile.": ("MoveEye spielt selbst einen Ton – solange wird nicht mitgehört.", "MoveEye joue lui-même un son – pas d’écoute pendant ce temps.", "MoveEye sta riproducendo un suono – nel frattempo non ascolta.", "MoveEye suna sez in tun – uschè ditg na vegn betg tadlà."),
    "The microphone delivers no sound.": ("Das Mikrofon liefert keinen Ton.", "Le microphone ne fournit aucun son.", "Il microfono non fornisce alcun suono.", "Il microfon na furnescha nagin tun."),
    "a tone at": ("ein Ton bei", "un son à", "un suono a", "in tun tar"),
    "listening for a tone or a whistle": ("wartet auf einen Ton oder Pfiff", "en attente d’un son ou d’un sifflement", "in attesa di un suono o di un fischio", "spetga in tun u in tschivel"),
    "reads up to about": ("liest bis etwa", "lit jusqu’à environ", "legge fino a circa", "legia fin circa"),
    "No sound is stored - only the decoded text.": ("Es wird kein Ton gespeichert – nur der entschlüsselte Text.", "Aucun son n’est enregistré – seulement le texte décodé.", "Nessun suono viene salvato – solo il testo decodificato.", "I na vegn memorisà nagin tun – mo il text decodà."),
    "No test signal of the other MoveEye read yet.": ("Noch kein Testsignal der Gegenstelle gelesen.", "Aucun signal de test de l’autre MoveEye lu pour l’instant.", "Nessun segnale di prova dell’altro MoveEye letto finora.", "Anc nagin signal da test da l’auter MoveEye legì."),
    "Test signal of the other MoveEye read": ("Testsignal der Gegenstelle gelesen", "Signal de test de l’autre MoveEye lu", "Segnale di prova dell’altro MoveEye letto", "Signal da test da l’auter MoveEye legì"),
    "Test signal read only in part - send more slowly or aim better": ("Testsignal nur teilweise gelesen – langsamer senden oder besser zielen", "Signal de test lu en partie seulement – envoyer plus lentement ou mieux viser", "Segnale di prova letto solo in parte – inviare più lentamente o puntare meglio", "Signal da test legì mo per part – trametter pli plaun u drizzar meglier"),
    "test signal": ("Testsignal", "signal de test", "segnale di prova", "signal da test"),
    "Test the other MoveEye (infrared)": ("Gegenstelle testen (Infrarot)", "Tester l’autre MoveEye (infrarouge)", "Provare l’altro MoveEye (infrarosso)", "Testar l’auter MoveEye (infracotschen)"),
    "Send the test signal by infrared": ("Testsignal per Infrarot senden", "Envoyer le signal de test par infrarouge", "Inviare il segnale di prova a infrarossi", "Trametter il signal da test per infracotschen"),
    "Two MoveEye see each other at night: each one must have the infrared light of the other in its picture.": ("Zwei MoveEye sehen sich in der Nacht: jedes muss das Infrarot-Licht des anderen im Bild haben.", "Deux MoveEye se voient la nuit : chacun doit avoir la lumière infrarouge de l’autre dans son image.", "Due MoveEye si vedono di notte: ognuno deve avere la luce a infrarossi dell’altro nell’immagine.", "Dus MoveEye sa vesan la notg: mintgin sto avair la glisch infracotschna da l’auter en ses maletg."),
    "Start the Morse mode on both. On the other MoveEye the page shows «reads up to about … WPM» - set the speed here no higher.": ("Auf beiden den Morse-Modus starten. Auf der Gegenstelle zeigt die Seite «liest bis etwa … WPM» – hier das Tempo nicht höher stellen.", "Démarrez le mode morse sur les deux. Sur l’autre MoveEye, la page indique «lit jusqu’à environ … WPM» – ne réglez pas ici une vitesse plus élevée.", "Avvia la modalità Morse su entrambi. Sull’altro MoveEye la pagina mostra «legge fino a circa … WPM» – qui non impostare una velocità maggiore.", "Aviar il modus da morse sin tuts dus. Sin l’auter MoveEye mussa la pagina «legia fin circa … WPM» – qua betg tscherner in tempo pli aut."),
    "Tap «Send the test signal by infrared» here. The other MoveEye shows «Test signal of the other MoveEye read». Then swap the roles.": ("Hier «Testsignal per Infrarot senden» antippen. Die Gegenstelle zeigt «Testsignal der Gegenstelle gelesen». Danach die Rollen tauschen.", "Touchez ici «Envoyer le signal de test par infrarouge». L’autre MoveEye affiche «Signal de test de l’autre MoveEye lu». Ensuite, échangez les rôles.", "Tocca qui «Inviare il segnale di prova a infrarossi». L’altro MoveEye mostra «Segnale di prova dell’altro MoveEye letto». Poi scambia i ruoli.", "Tutgar qua «Trametter il signal da test per infracotschen». L’auter MoveEye mussa «Signal da test da l’auter MoveEye legì». Suenter barattar las rollas."),
    "While a MoveEye sends with a light it does not read its own light.": ("Solange ein MoveEye mit einem Licht sendet, liest es das eigene Licht nicht.", "Tant qu’un MoveEye émet avec une lumière, il ne lit pas sa propre lumière.", "Mentre un MoveEye trasmette con una luce non legge la propria luce.", "Uschè ditg ch’in MoveEye trametta cun ina glisch, na legia el betg l’atgna glisch."),
    "By sound: a tone or a whistle near the microphone is read like a light, up to about 20 WPM. The microphone is only listened to while the Morse mode runs and «with the microphone» is chosen. No sound is stored - only the decoded text.": ("Mit Ton: ein Ton oder Pfiff nahe am Mikrofon wird gelesen wie ein Licht, bis etwa 20 WPM. Das Mikrofon wird nur mitgehört, solange der Morse-Modus läuft und «mit dem Mikrofon» gewählt ist. Es wird kein Ton gespeichert – nur der entschlüsselte Text.", "Par le son : un son ou un sifflement près du microphone est lu comme une lumière, jusqu’à environ 20 WPM. Le microphone n’est écouté que pendant le mode morse et si «avec le microphone» est choisi. Aucun son n’est enregistré – seulement le texte décodé.", "Con il suono: un suono o un fischio vicino al microfono viene letto come una luce, fino a circa 20 WPM. Il microfono viene ascoltato solo con la modalità Morse attiva e se è scelto «con il microfono». Nessun suono viene salvato – solo il testo decodificato.", "Cun tun: in tun u in tschivel datiers dal microfon vegn legì sco ina glisch, fin circa 20 WPM. Il microfon vegn tadlà mo durant il modus da morse e sche «cun il microfon» è tschernì. I na vegn memorisà nagin tun – mo il text decodà."),
}
for _k, _v in list(_HX_MORSE.items()) + list(MORSE_PAGE_TEXTS.items()):
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_MORSE_DE = {_k: DE.get(_k, _v[0]) for _k, _v in list(_HX_MORSE.items()) + list(MORSE_PAGE_TEXTS.items())}

# ---- the manual: a section «Morse-Modus» --------------------------------------------------------------------------------------------
_HELP_MORSE = {
    "de": ('<section id="morse" data-icon="📡"><h2>Morse-Modus</h2><ul>'
           '<li><b>Was:</b> Mehr → «📡 Morse-Modus» (nur der Administrator). Einen Text als Morsezeichen senden – mit dem weissen Licht, einem Relais, dem IR-Licht, '
           'der Status-LED oder als Ton – und ein blinkendes Licht (Taschenlampe, Scheinwerfer) mit der Kamera lesen.</li>'
           '<li><b>Der Schutz ist solange pausiert:</b> keine Alarme, keine Push-Nachrichten, keine Sirene. Im Live-Bild und beim Schutz-Zustand steht «Morse-Modus». '
           'Der Modus endet von selbst (ab Werk 10 Minuten, höchstens 30); danach ist der Schutz genau wie vorher, auch nach einem Stromausfall oder Neustart. '
           'Mit einer PIN für «Aus» braucht auch der Start die PIN.</li>'
           '<li><b>Tempo:</b> weisses Licht und Relais höchstens 3 Blitze pro Sekunde = 7 WPM (Blinklicht kann Anfälle auslösen), mechanisches Relais 4 WPM, '
           'Status-LED 10 WPM, IR 20 WPM, Ton 25 WPM. Mehrere Ausgänge senden im Tempo des langsamsten.</li>'
           '<li><b>Lesen:</b> langsam und gleichmässig tasten; die Kamera liest bis etwa 0.4 × Bilder pro Sekunde in WPM (die Seite zeigt den Wert). '
           'Von Hand dürfen die Längen um etwa ein Drittel schwanken. Am Tag wird eine schwache Lampe nicht gelesen – das Licht muss deutlich heller sein als der Hintergrund. '
           'Gleichmässiges Blinken (Auto-Blinker) ist kein Text; darum wird auch eine Nachricht nur aus E oder nur aus T («EEEE») verworfen.</li>'
           '<li><b>Empfangener Text:</b> im Live-Bild, im Verlauf mit Bild, als Push (nur Text) und vorgelesen – jedes einzeln wählbar. Er wird nie als Befehl ausgeführt.</li>'
           '<li><b>Mit Ton (Mikrofon):</b> ein Ton oder Pfiff nahe am Mikrofon wird gelesen wie ein Licht, bis etwa 20 WPM (ab Werk aus). Das Mikrofon wird dafür nur mitgehört, solange der Morse-Modus läuft und «mit dem Mikrofon» gewählt ist; <b>es wird kein Ton gespeichert</b>, nur der entschlüsselte Text. Ein gleichmässiges Piepen ist kein Text.</li><li><b>Zwei MoveEye mit Infrarot:</b> nachts sendet eines mit dem IR-Licht, das andere liest mit der Kamera. Unter «Gegenstelle testen» schickt eines ein Testsignal, das andere zeigt, ob es gelesen wurde. Solange ein MoveEye selbst mit Licht sendet, liest es das eigene Licht nicht.</li>'
           '</ul></section>\n'),
    "en": ('<section id="morse" data-icon="📡"><h2>Morse mode</h2><ul>'
           '<li><b>What:</b> More → «📡 Morse mode» (administrator only). Send a text as Morse code - with the white light, a relay, the infrared light, the status LED '
           'or as a tone - and read a blinking light (torch, spotlight) with the camera.</li>'
           '<li><b>The protection is paused meanwhile:</b> no alarms, no push messages, no siren. The live picture and the protection state say «Morse mode». '
           'The mode ends by itself (10 minutes by default, 30 at most); then the protection is exactly as before, also after a power cut or restart. '
           'With a PIN for «Off» the start needs the PIN too.</li>'
           '<li><b>Speed:</b> white light and relays at most 3 flashes a second = 7 WPM (flashing light can trigger seizures), mechanical relay 4 WPM, status LED 10 WPM, '
           'infrared 20 WPM, tone 25 WPM. Several outputs send at the speed of the slowest.</li>'
           '<li><b>Reading:</b> key slowly and evenly; the camera reads up to about 0.4 × pictures per second in WPM (the page shows the value). By hand, lengths may vary '
           'by about a third. By day a weak lamp is not read - the light must be clearly brighter than the background. Even blinking (a car indicator) is no text; '
           'that is why a message of only E or only T («EEEE») is thrown away.</li>'
           '<li><b>Received text:</b> in the live picture, in the history with a picture, as a push (text only) and read aloud - each can be chosen. It is never carried out as a command.</li>'
           '<li><b>By sound (microphone):</b> a tone or a whistle near the microphone is read like a light, up to about 20 WPM (off by default). The microphone is only listened to while the Morse mode runs and «with the microphone» is chosen; <b>no sound is stored</b>, only the decoded text. An even beep is no text.</li><li><b>Two MoveEye by infrared:</b> at night one sends with the infrared light, the other reads with the camera. Under «Test the other MoveEye» one sends a test signal, the other shows whether it was read. While a MoveEye sends with a light it does not read its own light.</li>'
           '</ul></section>\n'),
    "fr": ('<section id="morse" data-icon="📡"><h2>Mode morse</h2><ul>'
           '<li>Plus → «📡 Mode morse» (administrateur uniquement) : envoyer un texte en morse (lumière blanche, relais, infrarouge, LED d’état, son) et lire une lumière clignotante avec la caméra.</li>'
           '<li>Pendant ce temps la protection est en pause ; le mode se termine tout seul (10 minutes, 30 au plus), ensuite la protection est comme avant, aussi après une coupure de courant.</li>'
           '<li>Vitesse : lumière blanche et relais au plus 3 éclairs par seconde = 7 WPM, relais mécanique 4 WPM, LED d’état 10 WPM, infrarouge 20 WPM, son 25 WPM.</li>'
           '<li>Par le son (microphone, désactivé d’origine) : un son ou un sifflement est lu jusqu’à environ 20 WPM, uniquement pendant le mode morse ; <b>aucun son n’est enregistré</b>, seulement le texte décodé. Deux MoveEye par infrarouge : «Tester l’autre MoveEye» envoie un signal de test que l’autre affiche.</li>'
           '<li>Lecture : jusqu’à environ 0,4 × images par seconde en WPM ; de jour, une lampe faible n’est pas lue ; un clignotement régulier (ou «EEEE») n’est pas un texte. '
           'Le texte reçu n’est jamais exécuté comme une commande.</li></ul></section>\n'),
    "it": ('<section id="morse" data-icon="📡"><h2>Modalità Morse</h2><ul>'
           '<li>Altro → «📡 Modalità Morse» (solo amministratore): inviare un testo in Morse (luce bianca, relè, infrarosso, LED di stato, suono) e leggere una luce lampeggiante con la telecamera.</li>'
           '<li>Nel frattempo la protezione è in pausa; la modalità termina da sola (10 minuti, al massimo 30), poi la protezione è come prima, anche dopo un’interruzione di corrente.</li>'
           '<li>Velocità: luce bianca e relè al massimo 3 lampi al secondo = 7 WPM, relè meccanico 4 WPM, LED di stato 10 WPM, infrarosso 20 WPM, suono 25 WPM.</li>'
           '<li>Con il suono (microfono, spento di fabbrica): un suono o un fischio viene letto fino a circa 20 WPM, solo con la modalità Morse attiva; <b>nessun suono viene salvato</b>, solo il testo decodificato. Due MoveEye a infrarossi: «Provare l’altro MoveEye» invia un segnale di prova che l’altro mostra.</li>'
           '<li>Lettura: fino a circa 0,4 × immagini al secondo in WPM; di giorno una lampada debole non viene letta; un lampeggio regolare (o «EEEE») non è un testo. '
           'Il testo ricevuto non viene mai eseguito come comando.</li></ul></section>\n'),
    "rm": ('<section id="morse" data-icon="📡"><h2>Modus da morse</h2><ul>'
           '<li>Dapli → «📡 Modus da morse» (mo l’administratur): trametter in text en morse (glisch alva, relais, infracotschen, LED da status, tun) e leger ina glisch che traglischa cun la camera.</li>'
           '<li>En quel temp è la protecziun en pausa; il modus finescha da sasez (10 minutas, maximalmain 30), suenter è la protecziun sco avant, er suenter in’interrupziun da current.</li>'
           '<li>Tempo: glisch alva e relais maximalmain 3 chametgs per secunda = 7 WPM, relais mecanic 4 WPM, LED da status 10 WPM, infracotschen 20 WPM, tun 25 WPM.</li>'
           '<li>Cun tun (microfon, ora da fabrica): in tun u in tschivel vegn legì fin circa 20 WPM, mo durant il modus da morse; <b>i na vegn memorisà nagin tun</b>, mo il text decodà. Dus MoveEye cun infracotschen: «Testar l’auter MoveEye» trametta in signal da test che l’auter mussa.</li>'
           '<li>Leger: fin circa 0,4 × maletgs per secunda en WPM; da di na vegn ina lampa flaivla betg legida; in traglischar regular (u «EEEE») n’è nagin text. '
           'Il text retschavì na vegn mai exequì sco cumond.</li></ul></section>\n'),
}


def _help_morse(doc, lang):
    if 'id="morse"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_MORSE[lang] + doc[i:] if i >= 0 else doc


_hp_en_morse = HELP_PAGE.find('<div lang="en">')
if _hp_en_morse > 0:
    HELP_PAGE = _help_morse(HELP_PAGE[:_hp_en_morse], "de") + _help_morse(HELP_PAGE[_hp_en_morse:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_morse(HELP_X[_L], _L)


# ---- self-test --------------------------------------------------------------------------------------------------------------------------
def morse_selftest():
    assert len(set(MORSE_CODE.values())) == len(MORSE_CODE), "a Morse sign twice"
    for txt in ("SOS", "GRÜßE AUS ZÜRICH", "CQ DE MOVEEYE 73"):
        tl = morse_timeline(morse_encode(txt)[0], 8)
        d = [x for x, _on in tl]
        r = morse_decode(d[0::2], d[1::2] + [None])
        assert r["text"] == txt and abs(r["wpm"] - 8) < 0.3, (txt, r)
    assert morse_encode("a€b")[1] == ["€"] and morse_encode("<SOS>")[0] == [("...---...", "<SOS>")]
    assert morse_out_wpm("white") == 7 and morse_out_wpm("relay") == 4 and morse_out_wpm("led") == 10 and morse_out_wpm("ir") == 20 and morse_out_wpm("beep") == 25
    assert all(1.0 / (2.0 * morse_unit(morse_out_wpm(k))) <= MORSE_OUT_HZ[k] + 1e-9 for k in MORSE_OUT_HZ), "an output faster than its limit"
    assert MORSE_OUT_HZ["white"] <= 3.0 and MORSE_OUT_HZ["relay_ssr"] <= 3.0 and MORSE_OUT_HZ["led"] < 5.0, "visible light in the range 5 - 30 Hz"
    keep = {k: json.loads(json.dumps(CFG.get(k))) for k in list(MORSE_DEF) + ["light_white_out", "light_ir_out", "sim_on", "armed", "protect_level"]}
    keepm = dict(MORSE, msgs=deque(MORSE["msgs"], maxlen=20), tx_starts=list(MORSE["tx_starts"]))
    sv, lg, ws = save_settings, log_event, STATE.get("lights")
    logs = []
    try:
        globals()["save_settings"] = lambda *a, **k: None
        globals()["log_event"] = lambda k, t: logs.append(t)
        CFG.update(light_white_out="gpio:17", light_ir_out="", sim_on=False, armed=True, protect_level="watch")
        ARM["at"] = 0.0
        MORSE.update(until=0.0, tx=None, tx_starts=[])
        assert _is_armed_morse() and is_armed(), "armed before the mode"
        plan, err = morse_plan("SOS", ["white", "ir"], 20)
        assert plan is None and "not connected" in err, (plan, err)
        plan, err = morse_plan("SOS", ["white"], 20)
        assert plan and plan["wpm"] == 7 and plan["slow"] and plan["flash_hz"] <= 3.0 and plan["vis"] and not plan["note"], plan
        assert morse_plan("SOS", ["white"], float("nan"))[0] is None and morse_plan("€", ["white"], 5)[0] is None and morse_plan("E" * 300, ["white"], 5)[0] is None
        assert morse_tx_start("SOS", ["white"], 5)[1] == "the Morse mode is not running"
        assert morse_start(0)[0] is False and morse_start(MORSE_MODE_MAX_MIN + 1)[0] is False and morse_start("x")[0] is False
        assert morse_start(10, "self-test") == (True, "") and morse_on() and not is_armed() and CFG["armed"] is True, "the mode pauses, the setting stays"
        assert protect_label("armed") == "⏸ " + tr("Morse mode") and web_disarms("/api/morse", {"action": "start"}) and not web_disarms("/api/morse", {"action": "send"})
        assert morse_start(10)[1] == "the Morse mode is already running"
        t0 = MORSE["t0"]
        for _i in range(12):
            morse_start(MORSE_MODE_MAX_MIN, more=True)
        assert MORSE["until"] <= t0 + MORSE_MODE_MAX_MIN * 60.0 + 1e-6, "the mode can be made longer without end"
        ok_, err, plan = morse_tx_start("E T", ["white"], 7, 0, "self-test")
        assert ok_ and MORSE["tx"] is not None and morse_tx_start("E", ["white"], 7)[1] == "a transmission is running", err
        tx = MORSE["tx"]
        assert morse_tx_key(tx["t0"] - 0.1) is False and morse_tx_key(tx["t0"] + 0.01) is True and morse_tx_key(tx["t0"] + morse_unit(7) * 1.5) is False
        STATE["lights"] = {"white": False, "ir": False}
        tx["t0"] = time.time() - 0.01
        r = lights_tick()
        assert r["white"] is True and STATE["lights"].get("morse") == {"white": False}, (r, STATE["lights"])
        assert morse_tx_key(tx["t0"] + tx["total"] + 0.1) is None and MORSE["tx"] is None, "the transmission ends by itself"
        r = lights_tick()
        assert r["white"] is False and "morse" not in STATE["lights"], "after the end the light is as the rules say"
        assert not any("White light O" in x for x in logs), "no «White light ON / OFF» per dit"
        # the ONE entry of the web page and the window: rights, operator mode, PIN
        assert morse_do({"action": "stop"}, "x", role="family")[0] == 403 and morse_do({"action": "send", "text": "E"}, "x", role="kid")[0] == 403
        assert morse_do({"action": "stop"}, "x", appkey="k1")[0] == 403 and not morse_may("admin", "k1") and morse_may("admin")
        lk = CFG.get("lock_on")
        try:
            CFG["lock_on"] = True
            assert morse_do({"action": "start", "minutes": 5}, "x")[0] == 403 and morse_may("admin", None, change=False), "operator mode: no start"
        finally:
            CFG["lock_on"] = lk
        assert morse_do({"action": "nonsense"}, "x")[0] == 400 and morse_do(None, "x")[0] == 400 and morse_do({"action": "send", "text": 5}, "x")[0] == 400
        MORSE["tx_starts"] = [time.time()] * MORSE_TX_PER_MIN
        assert morse_tx_start("E", ["white"], 7)[1].startswith("too many")
        assert set(morse_clean("a<b onclick=x>\x00\x1b[0m\nÄ<SOS> ok🙂")) <= _MORSE_RX_OK and "\n" not in morse_clean("A\nB") and len(morse_clean("E" * 999)) == MORSE_RX_TEXT_MAX
        CFG.update(morse_rx_hist=False, morse_rx_push=False, morse_rx_say=False)
        assert morse_rx_text("SOS <SOS>", "camera", {"wpm": 5}) and MORSE["msgs"][0]["text"] == "SOS <SOS>" and not morse_rx_text("X", "other")
        MORSE["until"] = time.time() - 1.0
        assert not morse_on() and is_armed() and MORSE["until"] == 0.0 and any("Morse mode off" in x for x in logs), "the mode ends by itself, the protection is back"
        # step 2: by sound, the test signal of the other MoveEye, the own light is not read
        assert morse_start(5, "self-test")[0] and morse_rx_text("OK", "sound", {"wpm": 12, "hz": 660}) and MORSE["msgs"][0]["src"] == "sound"
        assert isinstance(MORSE["arx"], MorseAudio) and MORSE["arx"].feed(np.zeros(1600, np.int16)) is None
        MORSE["push_t"] = []
        assert morse_rx_text(MORSE_TEST_TEXT, "camera", {"wpm": 6}) and MORSE["peer"]["full"] and MORSE["msgs"][0]["test"] and not MORSE["push_t"]
        assert morse_rx_text("V TEST", "camera") and not MORSE["peer"]["full"] and MORSE["msgs"][0]["test"], "the test signal read in part"
        assert morse_rx_text("T UVV TEST", "camera") and not MORSE["peer"]["full"] and MORSE["msgs"][0]["test"], "garbled at the start: in part"
        assert morse_rx_text("TESTE DAS", "camera") and not MORSE["msgs"][0]["test"], "another text is no test signal"
        MORSE["tx_starts"] = []; CFG["light_ir_out"] = "gpio:27"
        c_, a_ = morse_do({"action": "test", "wpm": 99}, "self-test")
        assert (a_.get("ok") and MORSE["tx"]["outs"] == {"ir"} and MORSE["tx"]["wpm"] <= 20), (c_, a_)
        if MORSE["tx"] is not None:
            MORSE["tx"]["t0"] = time.time() - 0.01
            morse_tx_key()
            assert time.time() - MORSE["own_light"] < MORSE_OWN_S and MORSE["own_sound"] == 0.0, "the own light is marked"
            morse_tx_stop("self-test")
        morse_prefs({"rx_sound": True})
        assert CFG["morse_rx_sound"] is True and morse_sound_state(True, time.time())["on"]
        morse_end("self-test")
        assert MORSE["arx"].n == 0 and MORSE["alive"] is None, "nothing of the sound stays after the mode"
        assert not morse_rx_text("SOS", "camera"), "no text is taken while the mode is off"
        pin0, fails0 = CFG.get("protect_pin"), list(PROTECT["pin_fails"])
        try:                                                 # the window: start and «longer» need the PIN for «Aus», like the web page
            CFG["protect_pin"] = _pin_hash("2468"); PROTECT["pin_fails"] = []
            c_, a_ = morse_do({"action": "start", "minutes": 5}, "window")
            assert c_ == 403 and a_.get("need_pin") and not morse_on(), "start without the PIN"
            assert morse_do({"action": "start", "minutes": 5}, "window", pin="2468")[0] == 200 and morse_on(), "start with the PIN"
            assert morse_do({"action": "more", "minutes": 5}, "window")[0] == 403 and morse_do({"action": "more", "minutes": 5}, "window", pin="2468")[0] == 200
            assert morse_do({"action": "stop"}, "window")[0] == 200 and not morse_on() and is_armed(), "ending needs no PIN"
        finally:
            CFG["protect_pin"] = pin0; PROTECT["pin_fails"] = fails0
    finally:
        globals()["save_settings"], globals()["log_event"] = sv, lg
        CFG.update(keep); STATE["lights"] = ws
        MORSE.update(keepm); MORSE["until"] = 0.0; MORSE["tx"] = None; MORSE["relearn"] = False
    assert "No sound is stored" in MORSE_PAGE and "mo-peer-go" in MORSE_PAGE, "the page: privacy sentence, test of the other MoveEye"
    assert "/*MORSEDE*/" in MORSE_PAGE and 'href="/more"' in MORSE_PAGE and "innerHTML" not in MORSE_PAGE, "the page: way back, texts, no innerHTML"
    return "table, timing, speed limits per output, one entry for web and window (rights, PIN), mode pauses and ends by itself (never longer than the maximum), one transmission, light as before, received text cleaned, by sound, test signal of the other MoveEye"


SELFTEST_EXTRA.append(("Morse mode: send, read, pause of the protection (639zzz)", morse_selftest))
