#@ MoveEye – Teil 639zzx: «Morse-Modus» – einen Text als Morsezeichen senden (Licht, Relais, IR, Status-LED, Lautsprecher) und ein blinkendes Licht im Kamerabild lesen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
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


def morse_decode(ons, gaps):
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
            r = 5 + size // 2
            if any(abs(cx - q["x"]) <= r + q["r"] and abs(cy - q["y"]) <= r + q["r"] for q in self.tracks):
                continue
            if any(abs(cx - gx) <= 6 and abs(cy - gy) <= 6 for gx, gy, _t in self.ignore):
                continue
            tr_ = {"x": cx, "y": cy, "r": min(16, r), "key": MorseKey(), "t0": t, "dec": None, "valid": False, "size": size}
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
        r = min(24, tr_["r"] + grow)
        return max(0, tr_["x"] - r), min(w, tr_["x"] + r + 1), max(0, tr_["y"] - r), min(h, tr_["y"] + r + 1)

    def _track(self, tr_, g, t):
        h, w = g.shape
        key = tr_["key"]
        x0, x1, y0, y1 = self._win(tr_, w, h, int(6.0 * key.dark_for(t)))    # dark for a while: the hand may have moved - look wider
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
            end = self.END_S if not d_ else min(12.0, max(self.END_S, 2.2 * d_["word"]))
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
# ==== MORSE-KERN ENDE ====
