#@ MoveEye – Teil 639zzzi: «Mehrton» (MFSK) als dritter Weg neben Morse und «Eigenes Protokoll (2 Töne)» – nur über den Ton: Vorlagen 4 / 8 / 16 Töne und ein Baukasten, Rahmen (Vorspann, Kopf, Nutzdaten, CRC-16), Fehlerkorrektur aus / leicht / stark (Faltungscode K=7 mit Viterbi, weiche Entscheidungen, Verschachtelung), Schlüssel wie V2 auf Bytes; dieselbe Rechnung auf der Seite «Handy-Funkgerät» (Block MFSK in FUNK_PAGE). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Besitzer (14.11.2026): Mehrton als neue Art neben Morse und dem eigenen Protokoll, auf der Seite und in MoveEye (nur Ton).
# Spezifikation (Bit für Bit gleich in der Seite, geprüft von werkzeuge/funk_test.py Teil M, Testvektoren MFSK_VEKTOREN):
#   * Töne: Vorlage 1 = 4 Töne 800 + i·250 Hz, Symbol 40 ms, Schutz 6 ms; 2 = 8 Töne 650 + i·200 Hz, 50 ms / 8 ms;
#     3 = 16 Töne 500 + i·150 Hz, 64 ms / 8 ms; 0 = Baukasten (2-32 Töne, Start + Abstand oder Liste, Symbol, Schutz frei).
#     Symbol = ein Ton für T ms (Phase läuft durch); der Empfänger misst nur [Start + Schutz, Start + T) mit Hann-Fenster.
#     Daten nutzen die ersten 2^k Töne (k = floor(log2 n) Bit pro Symbol), Gray-Code: Wert v -> Ton v ^ (v >> 1).
#   * Rahmen: Vorspann 0.3 s (Ton 0 und Ton n-1 abwechselnd: Rauschsperre, Lautstärke-Regelung), Sync 12 Symbole
#     (Ton = MFSK_SYNC_A[j] · n // 16), Kopf 5 Bytes [0x10 | Vorlage, Fehlerkorrektur | Schlüssel << 2 | gepackt << 3, Länge,
#     Prüfwert des Baukastens (CRC-8 der Einstellungen) oder 0, CRC-8 der vier] immer mit Faltungscode 1/2 (92 Bit),
#     dann Nutzdaten + CRC-16/CCITT-FALSE (über die 4 Kopf-Bytes + Nutzdaten) mit der gewählten Fehlerkorrektur,
#     verschachtelt (Block, Spalten = ceil(sqrt(n))), auf k Bit aufgefüllt, dann 3 Symbole Ton 0 (Nachlauf).
#   * Fehlerkorrektur: aus = roh; leicht = Faltungscode K=7 (171, 133 oktal) punktiert auf 3/4 (Muster 110110);
#     stark = derselbe Code mit Rate 1/2. Viterbi mit weichen Entscheidungen aus den Ton-Energien.
#   * Text: nur die 39 Zeichen des Protokolls -> gepackt (3 Zeichen in 2 Bytes), sonst UTF-8 (Gross / klein, Umlaute).
#   * Schlüssel (V2 auf Bytes): dieselben Schlüssel (funk_v2_keys), Nonce 4 Bytes, Strom HMAC-SHA256(kE, "M" ‖ Nonce ‖ Zähler
#     4 Bytes) XOR, Prüfung HMAC-SHA256(kM, 0x03 ‖ Kopf 4 Bytes ‖ Nonce ‖ Geheimtext)[0:4]. Nutzdaten = Nonce ‖ Geheimtext ‖ Prüfung.
#   * Empfang: Goertzel / DFT pro Ton in Schritten von T/8, Sync durch Korrelation, Takt nachgeführt (früh / spät), alle
#     Vorlagen und der Baukasten gleichzeitig. Kopf falsch -> weitersuchen; CRC-16 falsch -> «gestört»; Prüfung falsch ->
#     «falscher Schlüssel oder gestört»; Baukasten mit anderem Prüfwert -> «andere Baukasten-Einstellungen».

# ==== MFSK-KERN ANFANG ====
MFSK_PRESETS = {1: {"n": 4, "f0": 800.0, "df": 250.0, "T": 40.0, "g": 6.0},
                2: {"n": 8, "f0": 650.0, "df": 200.0, "T": 50.0, "g": 8.0},
                3: {"n": 16, "f0": 500.0, "df": 150.0, "T": 64.0, "g": 8.0}}
MFSK_SYNC_A = (0, 15, 5, 10, 3, 12, 8, 1, 14, 6, 11, 2)
MFSK_LEAD_S = 0.3
MFSK_TAIL = 3
MFSK_FECS = ("aus", "leicht", "stark")
MFSK_HDR_BITS = 92
MFSK_MAX_DATA = 255
MFSK_TEXT_MAX = 200
MFSK_BAND = (300.0, 3000.0)
MFSK_G1, MFSK_G2 = 0o171, 0o133
MFSK_PUNCT = (1, 1, 0, 1, 1, 0)


def _mf_rnd(x):
    """round half up (like Math.round in the page - Python's round() rounds half to even)"""
    return int(math.floor(x + 0.5))


def mfsk_tones(s):
    """the frequencies of a setting (list, or start + i · spacing)"""
    if s.get("list"):
        return [float(f) for f in s["list"]]
    return [float(s["f0"]) + i * float(s["df"]) for i in range(int(s["n"]))]


def mfsk_k(s):
    n = len(mfsk_tones(s))
    return max(1, n.bit_length() - 1)


def mfsk_check(s):
    """a Baukasten setting -> (clean setting or None, errors, warnings, the least spacing in Hz) - English texts (tr in the pages)"""
    err, warn = [], []
    try:
        T = _mf_rnd(float(s.get("T", 50)) * 2) / 2.0; g = _mf_rnd(float(s.get("g", 0)) * 2) / 2.0
        if s.get("list"):
            tones = sorted(set(_mf_rnd(float(f) * 10) / 10.0 for f in s["list"]))
            c = {"n": len(tones), "list": tones, "T": T, "g": g}
        else:
            c = {"n": _mf_rnd(float(s.get("n", 8))), "f0": _mf_rnd(float(s.get("f0", 600)) * 10) / 10.0, "df": _mf_rnd(float(s.get("df", 200)) * 10) / 10.0, "T": T, "g": g}
    except (TypeError, ValueError, OverflowError):
        return None, ["not a number"], [], 0
    if not all(v == v and abs(v) < 1e6 for v in [c["T"], c["g"]] + mfsk_tones(c)):
        return None, ["not a number"], [], 0
    tones = mfsk_tones(c)
    if not 2 <= len(tones) <= 32:
        err.append("2 to 32 tones")
    if not 10 <= c["T"] <= 500:
        err.append("a symbol lasts 10 to 500 ms")
    if not 0 <= c["g"] <= c["T"] / 2.0:
        err.append("the guard time is 0 to half the symbol")
    if tones and (min(tones) < MFSK_BAND[0] or max(tones) > MFSK_BAND[1]):
        err.append("all tones between 300 and 3000 Hz (the band of a radio)")
    need = 0
    if not err:
        w = (c["T"] - c["g"]) / 1000.0
        need = int(math.ceil(2.0 / w))
        gap = min(b - a for a, b in zip(tones, tones[1:]))
        if gap < 1.0 / w:
            err.append("the tones are too close for this symbol length")
        elif gap < 2.0 / w:
            warn.append("the tones are close for this symbol length - more space is better")
        if len(tones) & (len(tones) - 1):
            warn.append("only a power of 2 of the tones carries data")
        if c["T"] - c["g"] < 15:
            warn.append("very short symbols: a radio and its squelch may smear them")
    return (None if err else c), err, warn, need


def mfsk_crc8(data):
    c = 0
    for b in data:
        c ^= b
        for _ in range(8):
            c = ((c << 1) ^ 0x07) & 0xFF if c & 0x80 else (c << 1) & 0xFF
    return c


def mfsk_crc16(data):
    c = 0xFFFF
    for b in data:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c


def mfsk_hash(s):
    """the check value of a Baukasten setting (in the header: both sides must have the same)"""
    t = "%d|%s|%d|%d" % (len(mfsk_tones(s)), ";".join(str(_mf_rnd(f * 10)) for f in mfsk_tones(s)), _mf_rnd(s["T"] * 10), _mf_rnd(s["g"] * 10))
    return mfsk_crc8(t.encode("ascii"))


def mfsk_pack(text):
    """-> (bytes, packed): only the 39 signs -> 3 signs in 2 bytes; otherwise UTF-8"""
    if text and all(c in FUNK_ALPHA for c in text):
        ix = [FUNK_ALPHA.index(c) for c in text]
        out = bytearray()
        i = 0
        while i + 3 <= len(ix):
            v = ix[i] * 1521 + ix[i + 1] * 39 + ix[i + 2]; out += bytes((v >> 8, v & 255)); i += 3
        if len(ix) - i == 2:
            v = 59319 + ix[i] * 39 + ix[i + 1]; out += bytes((v >> 8, v & 255))
        elif len(ix) - i == 1:
            out.append(ix[i])
        return bytes(out), True
    return text.encode("utf-8"), False


def mfsk_unpack(b, packed):
    if not packed:
        return b.decode("utf-8", "replace")
    out = []
    n = len(b) - (len(b) % 2)
    for i in range(0, n, 2):
        v = (b[i] << 8) | b[i + 1]
        if v >= 59319:
            v -= 59319
            out += [FUNK_ALPHA[(v // 39) % 39], FUNK_ALPHA[v % 39]]
        else:
            out += [FUNK_ALPHA[(v // 1521) % 39], FUNK_ALPHA[(v // 39) % 39], FUNK_ALPHA[v % 39]]
    if len(b) % 2:
        out.append(FUNK_ALPHA[b[-1] % 39])
    return "".join(out)


def _mfsk_par(x):
    return bin(x).count("1") & 1


def mfsk_conv(bits):
    """K=7 rate 1/2 (171, 133), 6 zero bits at the end"""
    r, out = 0, []
    for b in list(bits) + [0] * 6:
        r = ((r << 1) | b) & 0x7F
        out += [_mfsk_par(r & MFSK_G1), _mfsk_par(r & MFSK_G2)]
    return out


def mfsk_coded_len(nbits, fec):
    if fec == 0:
        return nbits
    n2 = 2 * (nbits + 6)
    return n2 if fec == 2 else sum(MFSK_PUNCT[i % 6] for i in range(n2))


def mfsk_fec_enc(bits, fec):
    if fec == 0:
        return list(bits)
    c = mfsk_conv(bits)
    return c if fec == 2 else [x for i, x in enumerate(c) if MFSK_PUNCT[i % 6]]


_MFSK_TR = None


def _mfsk_trellis():
    global _MFSK_TR
    if _MFSK_TR is None:
        o = np.zeros((64, 2, 2))                 # [next state][which predecessor][output 1 / 2] as ±1
        for ns in range(64):
            b = ns & 1
            for h in range(2):
                p = (ns >> 1) | (h << 5)
                r = ((p << 1) | b) & 0x7F
                o[ns, h, 0] = 2 * _mfsk_par(r & MFSK_G1) - 1; o[ns, h, 1] = 2 * _mfsk_par(r & MFSK_G2) - 1
        _MFSK_TR = o
    return _MFSK_TR


def mfsk_viterbi(llr, nbits):
    """soft Viterbi (llr > 0 = bit 1), rate 1/2 pairs incl. the tail -> nbits bits. Ties: the first predecessor"""
    o = _mfsk_trellis()
    nst = nbits + 6
    pa = np.arange(64) >> 1
    pb = pa | 32
    m = np.full(64, -1e18); m[0] = 0.0
    dec = np.zeros((nst, 64), np.uint8)
    for t in range(nst):
        l1, l2 = float(llr[2 * t]), float(llr[2 * t + 1])
        a = m[pa] + (o[:, 0, 0] * l1 + o[:, 0, 1] * l2)
        b = m[pb] + (o[:, 1, 0] * l1 + o[:, 1, 1] * l2)
        d = b > a
        dec[t] = d
        m = np.where(d, b, a)
    s, out = 0, [0] * nst
    for t in range(nst - 1, -1, -1):
        out[t] = s & 1
        s = (s >> 1) | (int(dec[t, s]) << 5)
    return out[:nbits]


def mfsk_fec_dec(llr, nbits, fec):
    if fec == 0:
        return [1 if v > 0 else 0 for v in llr[:nbits]]
    if fec == 1:
        full, j = [], 0
        for i in range(2 * (nbits + 6)):
            if MFSK_PUNCT[i % 6]:
                full.append(llr[j]); j += 1
            else:
                full.append(0.0)
        llr = full
    return mfsk_viterbi(llr, nbits)


def mfsk_ilv_order(n):
    cols = max(1, int(math.ceil(math.sqrt(n))))
    rows = (n + cols - 1) // cols
    return [r * cols + c for c in range(cols) for r in range(rows) if r * cols + c < n]


def _mfsk_bits(data):
    return [(b >> (7 - i)) & 1 for b in data for i in range(8)]


def _mfsk_bytes(bits):
    return bytes(sum(bits[i + j] << (7 - j) for j in range(8)) for i in range(0, len(bits) - 7, 8))


def mfsk_key_stream(kE, nonce, n):
    import hmac
    out, c = bytearray(), 0
    while len(out) < n:
        out += hmac.new(kE, b"M" + nonce + c.to_bytes(4, "big"), hashlib.sha256).digest(); c += 1
    return bytes(out[:n])


def mfsk_frame(text, pid, s, fec, key="", nonce=None):
    """text -> (symbols: tone indices of the whole transmission, English error)"""
    import hmac
    text = " ".join(str(text or "").split())
    if not text:
        return None, "the text is empty"
    if len(text) > MFSK_TEXT_MAX:                                # (code points - the page counts the same)
        return None, "the text is too long"
    data, packed = mfsk_pack(text)
    hdr = [0x10 | (pid & 15), (fec & 3) | (4 if key else 0) | (8 if packed else 0), 0, mfsk_hash(s) if pid == 0 else 0]
    if key:
        nonce = nonce if nonce is not None else secrets.token_bytes(4)
        kE, kM = funk_v2_keys(key)
        ct = bytes(a ^ b for a, b in zip(data, mfsk_key_stream(kE, nonce, len(data))))
        hdr[2] = len(data) + 8
        data = nonce + ct + hmac.new(kM, b"\x03" + bytes(hdr) + nonce + ct, hashlib.sha256).digest()[:4]
    else:
        hdr[2] = len(data)
    if len(data) > MFSK_MAX_DATA:
        return None, "the text is too long"
    hb = bytes(hdr)
    crc = mfsk_crc16(hb + data)
    bits = mfsk_conv(_mfsk_bits(hb + bytes([mfsk_crc8(hb)])))
    pay = mfsk_fec_enc(_mfsk_bits(data + bytes((crc >> 8, crc & 255))), fec)
    if fec:
        pay = [pay[i] for i in mfsk_ilv_order(len(pay))]
    bits += pay
    k = mfsk_k(s)
    bits += [0] * ((-len(bits)) % k)
    n = len(mfsk_tones(s))
    lead = max(2, _mf_rnd(MFSK_LEAD_S * 1000.0 / s["T"]))
    sym = [(0 if i % 2 == 0 else n - 1) for i in range(lead)] + [a * n // 16 for a in MFSK_SYNC_A]
    for i in range(0, len(bits), k):
        v = 0
        for b in bits[i:i + k]:
            v = (v << 1) | b
        sym.append(v ^ (v >> 1))
    return sym + [0] * MFSK_TAIL, ""


def mfsk_render(sym, s, rate, vol=0.8):
    """the tones, phase running through, symbol borders at round(j · T · rate), 3 ms ramps at the very start and end"""
    tones = mfsk_tones(s)
    T = s["T"] / 1000.0
    n = _mf_rnd(len(sym) * T * rate)
    f = np.empty(n)
    for j, t in enumerate(sym):
        f[_mf_rnd(j * T * rate):_mf_rnd((j + 1) * T * rate)] = tones[t]
    ph = np.concatenate(([0.0], np.cumsum(2.0 * np.pi * f / rate)[:-1]))
    y = vol * np.sin(ph)
    r = min(n // 2, int(0.003 * rate))
    if r:
        y[:r] *= np.arange(r) / float(r); y[-r:] *= np.arange(r, 0, -1) / float(r)
    return y.astype(np.float32)


class MfskDet:
    """one tone set (a preset or the Baukasten): energies every T/8, sync, symbols, header, payload"""

    def __init__(self, rate, pid, s, emit, key_fn):
        self.rate, self.pid, self.s, self.emit, self.key_fn = rate, pid, s, emit, key_fn
        self.tones = mfsk_tones(s); self.n = len(self.tones); self.k = mfsk_k(s); self.nd = 1 << self.k
        self.h = _mf_rnd(s["T"] * rate / 8000.0); self.go = _mf_rnd(s["g"] * rate / 1000.0)
        self.W = _mf_rnd((s["T"] - s["g"]) * rate / 1000.0)
        i = np.arange(self.W)
        win = 0.5 - 0.5 * np.cos(2 * np.pi * i / (self.W - 1))
        self.tab = (np.exp(-2j * np.pi * np.outer(i, self.tones) / rate) * win[:, None])
        self.sync = [a * self.n // 16 for a in MFSK_SYNC_A]
        self.thr = 1.0 / self.n + 0.35 * (1.0 - 1.0 / self.n)
        self.hash = mfsk_hash(s) if pid == 0 else 0
        gi = [t ^ (t >> 1) ^ (t >> 2) ^ (t >> 3) ^ (t >> 4) for t in range(self.nd)]       # tone -> value (Gray back)
        self.bsel = [(np.array([(gi[t] >> (self.k - 1 - b)) & 1 for t in range(self.nd)]) == 1) for b in range(self.k)]
        self.reset()

    def reset(self):
        self.buf = np.zeros(0); self.b0 = 0; self.hop = 0
        self.E = {}; self.state = 0; self.best = None; self.live = None; self.floor = None

    def feed(self, x):
        self.buf = np.concatenate((self.buf, x))
        last = self.b0 + self.buf.size
        nh = (last - self.go - self.W) // self.h - self.hop + 1
        if nh > 0:
            st = self.hop * self.h + self.go - self.b0
            idx = st + np.arange(nh)[:, None] * self.h + np.arange(self.W)[None, :]
            P = np.abs(self.buf[idx] @ self.tab) ** 2
            for j in range(nh):
                self.E[self.hop + j] = P[j]
                tot = float(P[j].sum())                   # the noise floor: fast down, slowly up (time constant ~ 1000 hops)
                self.floor = tot if self.floor is None or tot < self.floor else self.floor + (tot - self.floor) * 0.001
                self.step(self.hop + j)
            self.hop += nh
        keep = self.hop * self.h - self.b0
        if keep > 0:
            self.buf = self.buf[keep:]; self.b0 += keep
        lo = self.hop - 16 * 8 if self.state == 0 else self.q - 4
        for i in [i for i in self.E if i < lo]:
            del self.E[i]

    def step(self, i):
        if self.state == 0:
            c = i - 11 * 8
            if c - 1 not in self.E:
                return
            sc, lo = 0.0, 1e300                           # every sync symbol counts the same; all of them above 1.5 × the floor
            for j, t in enumerate(self.sync):
                e = self.E[c + 8 * j]; tot = float(e.sum())
                sc += float(e[t]) / (tot + 1e-30); lo = min(lo, tot)
            sc /= 12.0
            if sc >= self.thr and lo > 1.5 * self.floor and (self.best is None or sc > self.best[1]):
                self.best = (c, sc)
            if self.best is not None and c >= self.best[0] + 8:
                self.lock(self.best[0]); self.best = None
            return
        while self.state and self.q + 1 <= i:
            self.symbol()

    def lock(self, c):
        self.state = 1; self.base = c + 12 * 8; self.adj = 0; self.dacc = 0.0; self.j = 0; self.llr = []
        self.q = self.base; self.need = int(math.ceil(MFSK_HDR_BITS / float(self.k))); self.hdr = None
        self.live = {"pid": self.pid, "n": self.n, "got": 0, "of": 0}

    def symbol(self):
        e = self.E[self.q][:self.nd]
        a = np.sqrt(e)
        m = int(np.argmax(a))
        ee, el = self.E[self.q - 1][m], self.E[self.q + 1][m]
        self.dacc += (el - ee) / (el + ee + 1e-30)
        mx = float(a.max()) + 1e-30
        for sel in self.bsel:
            self.llr.append(float((a[sel].max() - a[~sel].max()) / mx))
        self.j += 1
        if self.dacc > 1.5:
            self.adj += 1; self.dacc = 0.0
        elif self.dacc < -1.5:
            self.adj -= 1; self.dacc = 0.0
        self.q = self.base + self.j * 8 + self.adj
        if self.live:
            self.live["got"] = self.j
        if self.j == self.need:
            if self.hdr is None:
                self.header()
            else:
                self.payload()

    def header(self):
        bits = mfsk_viterbi(self.llr[:MFSK_HDR_BITS], 40)
        hb = _mfsk_bytes(bits)
        if mfsk_crc8(hb[:4]) != hb[4] or hb[0] >> 4 != 1 or (hb[0] & 15) != self.pid or (hb[1] & 3) == 3:
            self.state = 0; self.live = None; return
        self.hdr = hb[:4]
        fec = hb[1] & 3
        self.nb = (hb[2] + 2) * 8
        self.lc = mfsk_coded_len(self.nb, fec)
        self.need = int(math.ceil((MFSK_HDR_BITS + self.lc) / float(self.k)))
        if self.live:
            self.live["of"] = self.need
        if self.need <= self.j:
            self.payload()

    def payload(self):
        import hmac
        hb = self.hdr
        fec, key_on, packed = hb[1] & 3, bool(hb[1] & 4), bool(hb[1] & 8)
        llr = self.llr[MFSK_HDR_BITS:MFSK_HDR_BITS + self.lc]
        if fec:
            d = [0.0] * self.lc
            for j, p in enumerate(mfsk_ilv_order(self.lc)):
                d[p] = llr[j]
            llr = d
        b = _mfsk_bytes(mfsk_fec_dec(llr, self.nb, fec))
        data, crc = b[:-2], (b[-2] << 8) | b[-1]
        res = {"pid": self.pid, "fec": MFSK_FECS[fec], "key": False, "bad": "", "text": "", "n": self.n}
        self.state = 0; self.live = None
        if mfsk_crc16(hb + data) != crc:
            res["bad"] = "crc"
        elif self.pid == 0 and hb[3] != self.hash:
            res["bad"] = "settings"
        elif key_on:
            key = self.key_fn() if self.key_fn else ""
            if not key:
                res["bad"] = "nokey"
            elif len(data) < 8:
                res["bad"] = "bad"
            else:
                kE, kM = funk_v2_keys(key)
                nonce, ct, tag = data[:4], data[4:-4], data[-4:]
                if not hmac.compare_digest(hmac.new(kM, b"\x03" + bytes(hb) + nonce + ct, hashlib.sha256).digest()[:4], tag):
                    res["bad"] = "bad"
                else:
                    res["key"] = True
                    res["text"] = mfsk_unpack(bytes(a ^ b_ for a, b_ in zip(ct, mfsk_key_stream(kE, nonce, len(ct)))), packed)
        else:
            res["text"] = mfsk_unpack(data, packed)
        self.emit(res)


class MfskRx:
    """all presets and (if set) the Baukasten at once. feed(samples) any number, int16 scale or -1..1"""

    def __init__(self, rate=16000, custom=None, on_message=None, key_fn=None):
        self.rate = rate
        self.dets = [MfskDet(rate, p, s, self._emit, key_fn) for p, s in sorted(MFSK_PRESETS.items())]
        if custom:
            self.dets.append(MfskDet(rate, 0, custom, self._emit, key_fn))
        self.on_message = on_message
        self.got = []

    def _emit(self, res):
        self.got.append(res)
        if self.on_message is not None:
            self.on_message(res)

    def live(self):
        return next((d.live for d in self.dets if d.live), None)

    def reset(self):
        for d in self.dets:
            d.reset()

    def feed(self, pcm):
        x = np.asarray(pcm, np.float64).ravel()
        if not x.size or not np.all(np.isfinite(x)) or x.size > self.rate * 610:
            return
        if np.asarray(pcm).dtype.kind in "iu":
            x = x / 32768.0
        for d in self.dets:
            d.feed(x)


def mfsk_clean(text):
    """a received MFSK text (UTF-8, any case): one line, no control characters, at most MORSE_RX_TEXT_MAX"""
    return " ".join("".join(ch for ch in str(text or "") if ch.isprintable()).split())[:240]
# ==== MFSK-KERN ENDE ====


# ---- in MoveEye: the format «Mehrton» in the Morse mode (only the loudspeaker sends it, the microphone reads it) ----------------
MFSK_DEF = {"morse_mf_pid": 2, "morse_mf_fec": 1, "morse_mf_custom": {"n": 8, "f0": 600.0, "df": 200.0, "T": 50.0, "g": 8.0}}
for _k, _v in MFSK_DEF.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)
MFSK = {"rx": None, "t": 0.0, "of": None}


class MfskTL(list):
    """a timeline [(seconds, Hz)] of Mehrton - morse_beep_chunks renders it with the phase running through"""
    sym = None
    s = None


def mfsk_on():
    return CFG.get("morse_fmt") == "mfsk"


def mfsk_custom():
    c, _e, _w, _n = mfsk_check(CFG.get("morse_mf_custom") or MFSK_DEF["morse_mf_custom"])
    return c


def mfsk_setting():
    """(preset id, setting, FEC 0-2) of the saved choice; the Baukasten only if it is valid"""
    pid = int(CFG.get("morse_mf_pid") or 0)
    fec = max(0, min(2, int(CFG.get("morse_mf_fec") if CFG.get("morse_mf_fec") is not None else 1)))
    if pid in MFSK_PRESETS:
        return pid, MFSK_PRESETS[pid], fec
    c = mfsk_custom()
    return (0, c, fec) if c else (2, MFSK_PRESETS[2], fec)


def mfsk_tl(text):
    """text -> (MfskTL, English error)"""
    pid, s, fec = mfsk_setting()
    sym, err = mfsk_frame(text, pid, s, fec, str(CFG.get("morse_key") or ""))
    if err:
        return None, err
    tl = MfskTL((s["T"] / 1000.0, mfsk_tones(s)[t]) for t in sym)
    tl.sym, tl.s = sym, s
    return tl, ""


_morse_plan_mfsk = morse_plan


# wraps: morse_plan (639zzzf)
def morse_plan(text, outs, wpm, fw=0, lang=None):              # + 639zzzi: «Mehrton» - only with the loudspeaker
    ids = [str(x) for x in (outs or [])] if isinstance(outs, (list, tuple)) else []
    if not mfsk_on() or "beep" not in ids:
        return _morse_plan_mfsk(text, outs, wpm, fw, lang)
    avail = {o["id"]: o for o in morse_outputs(lang)}
    if not (avail.get("beep") or {}).get("ok"):
        return None, "an output you chose is not connected"
    tl, err = mfsk_tl(text)
    if err:
        return None, err
    secs = sum(d for d, _f in tl)
    if secs > MORSE_TX_MAX_S:
        return None, "this takes too long - a shorter text or faster"
    pid, s, fec = mfsk_setting()
    return {"signs": [], "shown": " ".join(str(text).split()), "skipped": [], "wpm": 0, "asked": 0, "slow": "", "fw": 0, "tl": tl,
            "secs": round(secs, 1), "outs": ["beep"], "relays": {}, "flash_hz": 0.0, "note": False, "vis": False, "fmt": "mfsk",
            "key": bool(CFG.get("morse_key")), "mf": {"pid": pid, "n": len(mfsk_tones(s)), "fec": MFSK_FECS[fec]},
            "ignored": [avail[o]["name"] for o in ids if o != "beep" and o in avail]}, ""


_morse_beep_chunks_mfsk = morse_beep_chunks


# wraps: morse_beep_chunks (639zzzf)
def morse_beep_chunks(tl, rate, lead=0.6):                      # + 639zzzi: Mehrton with the phase running through
    if not isinstance(tl, MfskTL):
        yield from _morse_beep_chunks_mfsk(tl, rate, lead); return
    yield np.zeros(int(lead * rate), np.float32)
    yield mfsk_render(tl.sym, tl.s, rate, 1.0)


def mfsk_rx_message(res):
    """a Mehrton frame is complete -> the Morse list (never a command)"""
    t = MORSE_UNKNOWN if res.get("bad") else res.get("text", "")
    morse_rx_text(t, "sound", {"fmt": "mfsk", "key": res.get("key"), "bad": res.get("bad", ""), "wpm": 0})


_mfsk_audio_chunk_prev = AudioMonitor._chunk


def _mfsk_audio_chunk(self, data):                            # + 639zzzi: the microphone to the Mehrton readers (in the mode)
    if not mfsk_on():
        return _mfsk_audio_chunk_prev(self, data)
    _morse_audio_chunk_250(self, data)                        # (the sound monitor as always; no Morse reader meanwhile)
    if not (MORSE["until"] and CFG.get("morse_rx_sound")):
        return
    try:
        if not morse_on():
            return
        cu = mfsk_custom() if int(CFG.get("morse_mf_pid") or 0) == 0 else None
        if MFSK["rx"] is None or MFSK["of"] != json.dumps(cu):
            MFSK["rx"] = MfskRx(16000, cu, mfsk_rx_message, lambda: str(CFG.get("morse_key") or "")); MFSK["of"] = json.dumps(cu)
        now = time.time()
        if now < self.mute_until or SOUND["playing"] or now - MORSE["own_sound"] < MORSE_OWN_S:
            MFSK["rx"].reset()                                # (its own sound is not read)
        else:
            MFSK["rx"].feed(np.frombuffer(data, dtype="<i2"))
        MFSK["t"] = now
    except Exception as e:
        if time.time() - MORSE["err_t"] > 60:
            MORSE["err_t"] = time.time(); log_event("sys", f"Mehrton: {type(e).__name__}: {e}"[:160])
        try:
            MFSK["rx"].reset()
        except Exception:
            pass


# wraps: AudioMonitor._chunk (639zzzf wrapper)
AudioMonitor._chunk = _mfsk_audio_chunk

_morse_state_mfsk = morse_state


# wraps: morse_state (639zzzf)
def morse_state(lang=None):                                     # + 639zzzi: the Mehrton choice and what the reader is at
    st = _morse_state_mfsk(lang)
    pid, s, fec = mfsk_setting()
    cu = CFG.get("morse_mf_custom") or MFSK_DEF["morse_mf_custom"]
    _c, err, warn, need = mfsk_check(cu)
    rx = MFSK["rx"]
    fresh = st["on"] and mfsk_on() and rx is not None and time.time() - MFSK["t"] < 2.0
    lv = rx.live() if fresh else None
    st["funk"]["mf"] = {"pid": int(CFG.get("morse_mf_pid") or 0), "fec": fec, "custom": cu, "err": [tr_err(x, lang) for x in err],
                        "warn": [tr_err(x, lang) for x in warn], "need": need, "used": pid,
                        "presets": {str(k): dict(v) for k, v in MFSK_PRESETS.items()},
                        "bps": round(mfsk_k(s) * 1000.0 / s["T"] * (1.0, 0.75, 0.5)[fec], 1), "run": bool(fresh),
                        "live": ({"n": lv["n"], "got": lv["got"], "of": lv["of"]} if lv else None)}
    return st


_morse_do_mfsk = morse_do


# wraps: morse_do (639zzzf)
def morse_do(d, who, role="admin", appkey=None, pin=None, pin_checked=False, lang=None):   # + 639zzzi: format «mfsk», its settings
    d = d if isinstance(d, dict) else {}
    if str(d.get("action") or "") != "funk" or not (d.get("fmt") == "mfsk" or isinstance(d.get("mf"), dict)):
        return _morse_do_mfsk(d, who, role, appkey, pin, pin_checked, lang)
    L = norm_lang(lang or d.get("lang") or CFG.get("lang"))
    if not morse_may(role, appkey):
        return 403, {"ok": False, "error": tr("Only for the administrator", L)}

    def out(ok, err=""):
        return (200 if ok else 400), {"ok": ok, "error": tr_err(err, L) if err else None, "state": morse_state(L)}
    if d.get("fmt") == "mfsk":
        if MORSE["tx"] is not None:
            return out(False, "a transmission is running")
        CFG["morse_fmt"] = "mfsk"
    mf = d.get("mf") if isinstance(d.get("mf"), dict) else {}
    try:
        if "pid" in mf:
            p = int(mf["pid"])
            if p not in (0, 1, 2, 3):
                return out(False, "unknown choice")
            CFG["morse_mf_pid"] = p
        if "fec" in mf:
            f = int(mf["fec"])
            if f not in (0, 1, 2):
                return out(False, "unknown choice")
            CFG["morse_mf_fec"] = f
    except (TypeError, ValueError):
        return out(False, "not a number")
    if isinstance(mf.get("custom"), dict):
        cu = dict(mf["custom"])
        if isinstance(cu.get("list"), str):
            cu["list"] = [x for x in re.split(r"[\s,;]+", cu["list"]) if x]
        if not cu.get("list"):
            cu.pop("list", None)
        c, err, _w, _n = mfsk_check(cu)
        if err:
            save_settings()
            return out(False, err[0])
        CFG["morse_mf_custom"] = c
    MFSK["rx"] = None
    save_settings()
    return out(True)


_funk_wav_bytes_mfsk = funk_wav_bytes


# wraps: funk_wav_bytes (639zzzf)
def funk_wav_bytes(text, wpm, fw=0):                            # + 639zzzi: Mehrton as WAV (16 kHz: every symbol whole samples)
    if not mfsk_on():
        return _funk_wav_bytes_mfsk(text, wpm, fw)
    import io
    import wave
    tl, err = mfsk_tl(text)
    if err:
        return None, "", err
    y = np.concatenate([np.zeros(3200, np.float32), mfsk_render(tl.sym, tl.s, 16000, 0.8), np.zeros(4800, np.float32)])
    b = io.BytesIO()
    with wave.open(b, "wb") as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(16000)
        wv.writeframes((np.clip(y, -1.0, 1.0) * 32767).astype("<i2").tobytes())
    return b.getvalue(), "MoveEye_Mehrton" + datetime.now().strftime("_%Y%m%d_%H%M%S") + ".wav", ""


_funk_audio_read_mfsk = funk_audio_read


# wraps: funk_audio_read (639zzzf)
def funk_audio_read(data, lang=None):                           # + 639zzzi: a Mehrton recording
    if not mfsk_on():
        return _funk_audio_read_mfsk(data, lang)
    if FUNK_FILE["busy"]:
        return [], "another file is being read"
    if not data:
        return [], FUNK_FILE_ERR
    if len(data) > FUNK_AUDIO_MAX_B:
        return [], "the file is too big"
    FUNK_FILE["busy"] = True
    try:
        try:
            pcm = funk_audio_pcm(data)
        except ValueError as e:
            return [], str(e)
        cu = mfsk_custom() if int(CFG.get("morse_mf_pid") or 0) == 0 else None
        rx = MfskRx(16000, cu, None, lambda: str(CFG.get("morse_key") or ""))
        for i in range(0, pcm.size, 16000):
            rx.feed(pcm[i:i + 16000])
        rx.feed(np.zeros(16000, np.int16))
        out = []
        for r in rx.got:
            m = funk_file_msg(MORSE_UNKNOWN if r["bad"] else r["text"], {"fmt": "mfsk", "key": r["key"], "bad": r["bad"], "wpm": 0})
            if m:
                out.append(mfsk_bad_text(r["bad"], lang) if r["bad"] else m["text"])
        return out, ""
    finally:
        FUNK_FILE["busy"] = False


def mfsk_bad_text(bad, lang=None):
    return tr({"nokey": "encrypted - no key is set here", "bad": "wrong key or disturbed", "crc": "disturbed - the check sum is wrong",
               "settings": "other Baukasten settings than here"}.get(bad, "wrong key or disturbed"), lang)


_HX_MFSK = {
    "Multi-tone": ("Mehrton", "Multi-tons", "Multitono", "Plirs tuns"),
    "Multi-tone (MFSK): many tones, each carries several bits - faster and sturdier than two tones. The other side needs the same tones (a preset is found by itself; the Baukasten must be the same on both sides). Only the loudspeaker sends it.": (
        "Mehrton (MFSK): viele Töne, jeder trägt mehrere Bits – schneller und robuster als zwei Töne. Die Gegenseite braucht dieselben Töne (eine Vorlage findet sie selbst; den Baukasten auf beiden Seiten gleich einstellen). Nur der Lautsprecher sendet es.",
        "Multi-tons (MFSK) : beaucoup de sons, chacun porte plusieurs bits – plus rapide et plus robuste que deux sons. L’autre côté a besoin des mêmes sons (un modèle est trouvé tout seul ; le Baukasten doit être identique des deux côtés). Seul le haut-parleur l’envoie.",
        "Multitono (MFSK): molti suoni, ognuno porta più bit – più veloce e più robusto di due suoni. L’altra parte ha bisogno degli stessi suoni (un modello viene trovato da sé; il Baukasten deve essere uguale sui due lati). Lo invia solo l’altoparlante.",
        "Plirs tuns (MFSK): blers tuns, mintgin porta plirs bits – pli svelt e pli robust che dus tuns. L’autra vart dovra ils medems tuns (in model vegn chattà sez; il Baukasten sto esser il medem sin omaduas varts). Mo il autpledader al trametta."),
    "Tones": ("Töne", "Sons", "Suoni", "Tuns"),
    "tones": ("Töne", "sons", "suoni", "tuns"),
    "Error correction": ("Fehlerkorrektur", "Correction d’erreurs", "Correzione degli errori", "Correctura da sbagls"),
    "off": ("aus", "désactivée", "spenta", "deactivà"),
    "light": ("leicht", "légère", "leggera", "levga"),
    "strong": ("stark", "forte", "forte", "ferma"),
    "Number of tones": ("Anzahl Töne", "Nombre de sons", "Numero di suoni", "Dumber da tuns"),
    "First tone (Hz)": ("Erster Ton (Hz)", "Premier son (Hz)", "Primo suono (Hz)", "Emprim tun (Hz)"),
    "Spacing (Hz)": ("Abstand (Hz)", "Écart (Hz)", "Distanza (Hz)", "Distanza (Hz)"),
    "Symbol (ms)": ("Symbol (ms)", "Symbole (ms)", "Simbolo (ms)", "Simbol (ms)"),
    "Guard time (ms)": ("Schutzzeit (ms)", "Temps de garde (ms)", "Tempo di guardia (ms)", "Temp da protecziun (ms)"),
    "Or a list of tones (Hz, with commas):": ("Oder eine Liste der Töne (Hz, mit Kommas):", "Ou une liste de sons (Hz, avec des virgules) :",
                                              "Oppure un elenco di suoni (Hz, con virgole):", "U ina glista dals tuns (Hz, cun commas):"),
    "Baukasten (own settings)": ("Baukasten (eigene Einstellungen)", "Baukasten (réglages propres)", "Baukasten (impostazioni proprie)", "Baukasten (agens parameters)"),
    "The Baukasten settings do not work - the 8 tones are used.": ("Die Baukasten-Einstellungen gehen nicht – es gelten die 8 Töne.",
                                                                   "Les réglages du Baukasten ne fonctionnent pas – les 8 sons sont utilisés.",
                                                                   "Le impostazioni del Baukasten non funzionano – si usano gli 8 suoni.",
                                                                   "Ils parameters dal Baukasten na funcziunan betg – i valan ils 8 tuns."),
    "at least": ("mindestens", "au moins", "almeno", "almain"),
    "Multi-tone: only the loudspeaker sends it - light and infrared send Morse.": ("Mehrton: nur der Lautsprecher sendet es – Licht und Infrarot senden Morse.",
                                                                                  "Multi-tons : seul le haut-parleur l’envoie – la lumière et l’infrarouge envoient du morse.",
                                                                                  "Multitono: lo invia solo l’altoparlante – luce e infrarosso inviano Morse.",
                                                                                  "Plirs tuns: mo il autpledader al trametta – glisch ed infracotschen tramettan morse."),
    "a frame is coming": ("ein Rahmen kommt", "une trame arrive", "arriva una trama", "in rom arriva"),
    "listening for multi-tone": ("wartet auf Mehrton", "en attente de multi-tons", "in attesa del multitono", "spetga plirs tuns"),
    "disturbed - the check sum is wrong": ("gestört – die Prüfsumme stimmt nicht", "perturbé – la somme de contrôle est fausse",
                                           "disturbato – la somma di controllo è sbagliata", "disturbà – la summa da controlla è sbagliada"),
    "other Baukasten settings than here": ("andere Baukasten-Einstellungen als hier", "autres réglages du Baukasten qu’ici",
                                           "altre impostazioni del Baukasten che qui", "auters parameters dal Baukasten che qua"),
    "2 to 32 tones": ("2 bis 32 Töne", "2 à 32 sons", "da 2 a 32 suoni", "2 fin 32 tuns"),
    "a symbol lasts 10 to 500 ms": ("ein Symbol dauert 10 bis 500 ms", "un symbole dure 10 à 500 ms", "un simbolo dura da 10 a 500 ms", "in simbol cuzza 10 fin 500 ms"),
    "the guard time is 0 to half the symbol": ("die Schutzzeit ist 0 bis zur Hälfte des Symbols", "le temps de garde va de 0 à la moitié du symbole",
                                               "il tempo di guardia va da 0 a metà del simbolo", "il temp da protecziun è 0 fin la mesadad dal simbol"),
    "all tones between 300 and 3000 Hz (the band of a radio)": ("alle Töne zwischen 300 und 3000 Hz (das Band eines Funkgeräts)",
                                                                "tous les sons entre 300 et 3000 Hz (la bande d’une radio)",
                                                                "tutti i suoni tra 300 e 3000 Hz (la banda di una radio)",
                                                                "tut ils tuns tranter 300 e 3000 Hz (la banda d’in radio)"),
    "the tones are too close for this symbol length": ("die Töne liegen zu nah für diese Symbol-Länge", "les sons sont trop proches pour cette durée de symbole",
                                                       "i suoni sono troppo vicini per questa durata del simbolo", "ils tuns èn memia datiers per questa lunghezza dal simbol"),
    "the tones are close for this symbol length - more space is better": ("die Töne liegen nah für diese Symbol-Länge – mehr Abstand ist besser",
                                                                          "les sons sont proches pour cette durée de symbole – plus d’écart est mieux",
                                                                          "i suoni sono vicini per questa durata del simbolo – più distanza è meglio",
                                                                          "ils tuns èn datiers per questa lunghezza dal simbol – dapli distanza è meglier"),
    "only a power of 2 of the tones carries data": ("nur eine Zweierpotenz der Töne trägt Daten", "seule une puissance de 2 des sons porte des données",
                                                    "solo una potenza di 2 dei suoni porta dati", "mo ina potenza da 2 dals tuns porta datas"),
    "very short symbols: a radio and its squelch may smear them": ("sehr kurze Symbole: Funkgerät und Rauschsperre können sie verschmieren",
                                                                   "symboles très courts : la radio et son squelch peuvent les étaler",
                                                                   "simboli molto corti: la radio e lo squelch possono sbavarli",
                                                                   "simbols fitg curts: il radio e la serra da canera als pon sfarlattar"),
}
for _k, _v in _HX_MFSK.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_MORSE_DE.update({_k: DE.get(_k, _v[0]) for _k in _HX_MFSK})

_HELP_MFSK = {
    "de": '<li><b>📶 Mehrton (MFSK):</b> Format «Mehrton»: 4, 8 oder 16 Töne (2–4 Bit pro Ton) oder ein Baukasten (2–32 Töne, Abstand, Symbol- und Schutzzeit frei); Rahmen mit Vorspann, Kopf und CRC-16; Fehlerkorrektur aus / leicht / stark (Faltungscode mit Viterbi). Eine Vorlage erkennt die Gegenseite selbst, den Baukasten auf beiden Seiten gleich einstellen. Gross- / Kleinbuchstaben und Umlaute gehen mit. Mit Schlüssel wie V2. Messung: docs/Funk_Protokoll.md.</li>',
    "en": '<li><b>📶 Multi-tone (MFSK):</b> format «Multi-tone»: 4, 8 or 16 tones (2–4 bits per tone) or a Baukasten (2–32 tones, spacing, symbol and guard time free); frames with preamble, header and CRC-16; error correction off / light / strong (convolutional code with Viterbi). A preset is found by the other side itself, set the Baukasten the same on both sides. Upper / lower case and umlauts go along. With a key like V2. Measured: docs/Funk_Protokoll.md.</li>',
    "fr": '<li><b>📶 Multi-tons (MFSK) :</b> 4, 8 ou 16 sons ou un Baukasten ; trames avec CRC-16 ; correction d’erreurs désactivée / légère / forte. Un modèle est reconnu tout seul, le Baukasten doit être identique des deux côtés.</li>',
    "it": '<li><b>📶 Multitono (MFSK):</b> 4, 8 o 16 suoni o un Baukasten; trame con CRC-16; correzione degli errori spenta / leggera / forte. Un modello viene riconosciuto da sé, il Baukasten deve essere uguale sui due lati.</li>',
    "rm": '<li><b>📶 Plirs tuns (MFSK):</b> 4, 8 u 16 tuns u in Baukasten; roms cun CRC-16; correctura da sbagls deactivada / levga / ferma. In model vegn enconuschì sez, il Baukasten sto esser il medem sin omaduas varts.</li>',
}
funk_help_add(_HELP_MFSK)                                   # (into the finished manual too - see 639zzzf)

# test vectors (the same in werkzeuge/funk_test.py: page in node = MoveEye): text, preset, FEC, key, nonce (hex) -> the first 16 hex
# signs of SHA-256 of the symbols written as "3,0,15,…"
MFSK_VEKTOREN = (("HALLO WELT 73?", 1, 0, "", "", "27cc5c2e5d0db79f"), ("Grüsse aus Zürich!", 2, 2, "", "", "d60e08619c32fd1c"),
                 ("TREFFEN UM 15 UHR", 3, 1, "geheim", "01020304", "ee2d506088e5d8b3"),
                 ("ÄÖÜ äöü ß € 😀", 2, 1, "Zürich 2026!", "a0b1c2d3", "732df6e58ff31ddb"))


def mfsk_selftest():
    """Mehrton: CRC, packing, code + Viterbi, the fixed vectors, a frame through the reader for every preset and FEC (with
    and without key, wrong key, the Baukasten and its check value), noise is no frame, the settings check"""
    assert _HELP_MFSK["de"] in HELP_PAGE, "the paragraph on Mehrton is in the manual"
    assert mfsk_crc16(b"123456789") == 0x29B1 and mfsk_crc8(b"123456789") == 0xF4, "CRC-16/CCITT-FALSE, CRC-8"
    for t in ("A", "AB", "ABC", "HALLO WELT 73?", "Grüsse aus Zürich!"):
        b, pk = mfsk_pack(t)
        assert mfsk_unpack(b, pk) == t and pk == all(c in FUNK_ALPHA for c in t)
    bits = [int(c) for c in "1011001110001011010011"]
    for fec in (1, 2):
        c = mfsk_fec_enc(bits, fec)
        assert len(c) == mfsk_coded_len(len(bits), fec) and mfsk_fec_dec([1.0 if x else -1.0 for x in c], len(bits), fec) == bits
    for text, pid, fec, key, nonce, h in MFSK_VEKTOREN:
        sym, _e = mfsk_frame(text, pid, MFSK_PRESETS[pid], fec, key, bytes.fromhex(nonce) if nonce else None)
        assert hashlib.sha256(",".join(map(str, sym)).encode()).hexdigest()[:16] == h, (text, pid, fec)
    cu, err, _w, _n = mfsk_check({"n": 6, "f0": 700, "df": 220, "T": 45, "g": 7})
    assert cu and not err and mfsk_check({"n": 8, "f0": 700, "df": 10, "T": 20, "g": 5})[1] and mfsk_check({"n": 4, "f0": 2900, "df": 300, "T": 40, "g": 5})[1]
    rng = np.random.default_rng(5)
    cases = [(p, f, k) for p in (1, 2, 3) for f in (0, 1, 2) for k in ("", "geheim")][::3] + [(0, 2, "geheim")]
    for pid, fec, key in cases:
        s = MFSK_PRESETS.get(pid) or cu
        sym, err = mfsk_frame("Grüsse 15 Uhr!", pid, s, fec, key)
        y = np.concatenate([np.zeros(4000), mfsk_render(sym, s, 16000), np.zeros(8000)])
        y = y + rng.normal(0, 0.05, y.size)
        for kk, want in ((key, ("Grüsse 15 Uhr!", "")), ("falsch" if key else "", ("", "bad") if key else ("Grüsse 15 Uhr!", ""))):
            rx = MfskRx(16000, cu if pid == 0 else None, None, lambda kk=kk: kk)
            rx.feed(y)
            assert [(r["text"], r["bad"]) for r in rx.got] == [want], (pid, fec, key, kk, rx.got)
    rx = MfskRx(16000, mfsk_check({"n": 6, "f0": 700, "df": 220, "T": 45, "g": 7.5})[0], None, None)
    s = cu
    sym, _e = mfsk_frame("X", 0, s, 2)
    rx.feed(np.concatenate([np.zeros(4000), mfsk_render(sym, s, 16000), np.zeros(8000)]))
    assert [r["bad"] for r in rx.got] in ([], ["settings"]), rx.got
    rx = MfskRx(16000)
    rx.feed(rng.normal(0, 0.3, 16000 * 8))
    assert not rx.got, "noise is no frame"
    return "CRC, packing, Viterbi, vectors, every preset / FEC with and without key, wrong key, Baukasten, noise"


SELFTEST_EXTRA.append(("Mehrton (MFSK): frames, error correction, key, Baukasten (639zzzi)", mfsk_selftest))
