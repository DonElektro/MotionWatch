#@ MoveEye – Teil 639zzzzc: «🔏 Botschaft im Bild» im «Digitalen Rucksack» – Steganographie: einen geheimen Text in ein Foto legen (verschlüsselt, als LSB in den RGB-Kanälen, Pixel-Reihenfolge vom Schlüssel abhängig). Gleiche Rechnung wie das Modul funk/stego.js. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Paket des Besitzers (freigegeben 14.11.2026, erweitert 15.11.2026). Zwei Dinge:
#   1. «🔏 Botschaft im Bild»: ein Foto bekommt «🔏 Botschaft verstecken» (Text + Schlüssel eingeben → eine NEUE Datei
#      «<name>_b.png», das Original bleibt). «🔎 Botschaft lesen»: Bild wählen, Schlüssel eingeben, der Text erscheint
#      (wird nie protokolliert). Nur Text (UTF-8); die Seite zeigt, wie viele Zeichen noch passen.
#   2. Die Seite /tausch wird eine Übersicht mit Zeilen (wie «Mehr»): 🎒 oben, dann die Zeilen «📋 Packlisten»,
#      «📁 Dateien» (der ganze Datei-Bereich öffnet sich als Unterseite mit «‹ Zurück») und «🔏 Botschaft im Bild».
#   Verschlüsselt wird ZUERST: PBKDF2-HMAC-SHA256 (200000 Runden, fester Salz «MoveEye-Bild-v1» + 16 Byte Zufalls-Salz),
#   dann AES-256-GCM (im Browser WebCrypto, in Python das Paket «cryptography») – oder, wo kein AES ist, ein
#   HMAC-SHA256-Schlüsselstrom mit Encrypt-then-MAC. Der Kopf (Version, Länge) ist mitverschlüsselt, ohne Schlüssel
#   ist nichts mehr als Rauschen zu sehen. Falscher Schlüssel / beschädigtes Bild → «keine Botschaft gefunden oder
#   falscher Schlüssel» (mit Absicht nicht zu unterscheiden). JPEG wird dekodiert, Ausgabe ist immer PNG.
#   Der Schlüssel und der Text bleiben im Browser (WebCrypto); der Server bekommt sie nie, nichts davon wird
#   protokolliert. Das Modul funk/stego.js braucht kein Netz; die Seite «Handy-Funkgerät» lädt es erst ab Phase 2.
# Der Python-Kern unten ist bitgleich zu funk/stego.js (gemeinsamer Test-Vektor, werkzeuge/stego_test.py). Er steht
# für die Prüfung auf dem Gerät und als zweiter Weg bereit (der Browser rechnet im Normalfall selbst).
# Tests: werkzeuge/stego_test.py (Python↔node, mehrere Grössen, Grenze, falscher Schlüssel, geänderter Bereich,
#   JPEG→PNG, Original unverändert, nichts Geheimes im Protokoll, Browser-Test der Seite bei 390 px). Selbsttest unten.
# ----------------------------------------------------------------------------
import hashlib as _bild_hashlib
import hmac as _bild_hmac
import struct as _bild_struct

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _BildAESGCM
    _BILD_HAS_AES = True
except Exception:                                          # pragma: no cover
    _BildAESGCM = None
    _BILD_HAS_AES = False

_BILD_SALT_FIX = b"MoveEye-Bild-v1"
_BILD_PERM_FIX = b"MoveEye-Bild-v1-perm"
_BILD_SALT_LEN, _BILD_NONCE_LEN, _BILD_TAG_LEN, _BILD_HDR_LEN = 16, 12, 16, 5
_BILD_OVERHEAD = _BILD_SALT_LEN + _BILD_NONCE_LEN + (_BILD_HDR_LEN + _BILD_TAG_LEN) + _BILD_TAG_LEN   # 65


class BildCapacity(Exception):
    def __init__(self, cap, need):
        super().__init__("too big")
        self.capacity = cap
        self.need = need


def _bild_pbkdf2(pw, salt):
    return _bild_hashlib.pbkdf2_hmac("sha256", pw, _BILD_SALT_FIX + salt, 200000, 32)


def _bild_sub_nonce(nonce, tag):
    return _bild_hashlib.sha256(nonce + tag).digest()[:_BILD_NONCE_LEN]


def _bild_mac_keys(k):
    return _bild_hashlib.sha256(k + b"enc").digest(), _bild_hashlib.sha256(k + b"mac").digest()


def _bild_keystream(ke, nonce, n):
    out, blk = bytearray(), 0
    while len(out) < n:
        out += _bild_hmac.new(ke, nonce + _bild_struct.pack(">I", blk), _bild_hashlib.sha256).digest()
        blk += 1
    return bytes(out[:n])


def _bild_hmac_enc(k, nonce, pt):
    ke, km = _bild_mac_keys(k)
    ks = _bild_keystream(ke, nonce, len(pt))
    ct = bytes(a ^ b for a, b in zip(pt, ks))
    return ct + _bild_hmac.new(km, nonce + ct, _bild_hashlib.sha256).digest()[:_BILD_TAG_LEN]


def _bild_hmac_dec(k, nonce, blob):
    if len(blob) < _BILD_TAG_LEN:
        raise ValueError("x")
    ke, km = _bild_mac_keys(k)
    ct, tag = blob[:-_BILD_TAG_LEN], blob[-_BILD_TAG_LEN:]
    if not _bild_hmac.compare_digest(_bild_hmac.new(km, nonce + ct, _bild_hashlib.sha256).digest()[:_BILD_TAG_LEN], tag):
        raise ValueError("tag")
    ks = _bild_keystream(ke, nonce, len(ct))
    return bytes(a ^ b for a, b in zip(ct, ks))


def _bild_pack(pw, text, salt=None, nonce=None, force_hmac=False):
    if isinstance(pw, str):
        pw = pw.encode("utf-8")
    msg = text.encode("utf-8") if isinstance(text, str) else text
    salt = salt if salt is not None else os.urandom(_BILD_SALT_LEN)
    nonce = nonce if nonce is not None else os.urandom(_BILD_NONCE_LEN)
    k = _bild_pbkdf2(pw, salt)
    nH, nB = _bild_sub_nonce(nonce, b"H"), _bild_sub_nonce(nonce, b"B")
    hdr = bytes([1]) + _bild_struct.pack(">I", len(msg))
    if _BILD_HAS_AES and not force_hmac:
        hdrct, bodyct = _BildAESGCM(k).encrypt(nH, hdr, None), _BildAESGCM(k).encrypt(nB, msg, None)
    else:
        hdrct, bodyct = _bild_hmac_enc(k, nH, hdr), _bild_hmac_enc(k, nB, msg)
    return salt + nonce + hdrct + bodyct


def _bild_unpack(pw, read_bytes, total):
    if isinstance(pw, str):
        pw = pw.encode("utf-8")
    salt, nonce = read_bytes(0, _BILD_SALT_LEN), read_bytes(_BILD_SALT_LEN, _BILD_NONCE_LEN)
    k = _bild_pbkdf2(pw, salt)
    nH, nB = _bild_sub_nonce(nonce, b"H"), _bild_sub_nonce(nonce, b"B")
    off = _BILD_SALT_LEN + _BILD_NONCE_LEN
    hdrct = read_bytes(off, _BILD_HDR_LEN + _BILD_TAG_LEN)
    hdr = None
    if _BILD_HAS_AES:
        try:
            hdr = _BildAESGCM(k).decrypt(nH, hdrct, None)
        except Exception:
            hdr = None
    if hdr is None:
        try:
            hdr = _bild_hmac_dec(k, nH, hdrct)
        except Exception:
            hdr = None
    if not hdr or len(hdr) != _BILD_HDR_LEN or hdr[0] != 1:
        raise ValueError("no message")
    length = _bild_struct.unpack(">I", hdr[1:5])[0]
    if _BILD_OVERHEAD + length > total:
        raise ValueError("no message")
    bodyct = read_bytes(off + _BILD_HDR_LEN + _BILD_TAG_LEN, length + _BILD_TAG_LEN)
    body = None
    if _BILD_HAS_AES:
        try:
            body = _BildAESGCM(k).decrypt(nB, bodyct, None)
        except Exception:
            body = None
    if body is None:
        try:
            body = _bild_hmac_dec(k, nB, bodyct)
        except Exception:
            body = None
    if body is None:
        raise ValueError("no message")
    return body.decode("utf-8")


class _BildPrng:
    def __init__(self, seed):
        self.seed, self.buf, self.pos, self.ctr = seed, b"", 8, 0

    def word(self):
        if self.pos >= 8:
            self.buf = _bild_hashlib.sha256(self.seed + _bild_struct.pack("<Q", self.ctr)).digest()
            self.ctr += 1
            self.pos = 0
        o = self.pos * 4
        self.pos += 1
        return _bild_struct.unpack_from("<I", self.buf, o)[0]

    def below(self, n):
        if n <= 0:
            return 0
        limit = (0x100000000 // n) * n
        while True:
            x = self.word()
            if x < limit:
                return x % n


def _bild_positions(pw, total, m):
    if isinstance(pw, str):
        pw = pw.encode("utf-8")
    pr = _BildPrng(_bild_hashlib.sha256(_BILD_PERM_FIX + pw).digest())
    state, out = {}, [0] * m
    for i in range(m):
        j = i + pr.below(total - i)
        vi, vj = state.get(i, i), state.get(j, j)
        out[i] = vj
        state[j] = vi
        if j != i:
            state[i] = vj
    return out


def _bild_slot_count(w, h):
    return w * h * 3


def bild_capacity(w, h):
    return max(0, _bild_slot_count(w, h) // 8 - _BILD_OVERHEAD)


def _bild_embed(rgba, w, h, pw, payload):
    total, nbits = _bild_slot_count(w, h), len(payload) * 8
    if nbits > total:
        raise ValueError("too big")
    pos = _bild_positions(pw, total, nbits)
    for i in range(nbits):
        slot = pos[i]
        idx = (slot // 3) * 4 + (slot % 3)
        rgba[idx] = (rgba[idx] & 0xFE) | ((payload[i >> 3] >> (7 - (i & 7))) & 1)


def _bild_reader(rgba, w, h, pw):
    total, cache = _bild_slot_count(w, h), {"pos": []}

    def read(byte_off, nbytes):
        need = (byte_off + nbytes) * 8
        if len(cache["pos"]) < need:
            cache["pos"] = _bild_positions(pw, total, min(total, max(need, len(cache["pos"]))))
        pos, out = cache["pos"], bytearray(nbytes)
        for i in range(nbytes * 8):
            slot = pos[byte_off * 8 + i]
            idx = (slot // 3) * 4 + (slot % 3)
            out[i >> 3] |= (rgba[idx] & 1) << (7 - (i & 7))
        return bytes(out)

    return read


def _bild_load_rgba(image_bytes):
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    w, h = im.size
    return bytearray(im.tobytes()), w, h


def _bild_save_png(rgba, w, h):
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.frombytes("RGBA", (w, h), bytes(rgba)).save(buf, format="PNG", compress_level=6)
    return buf.getvalue()


def bild_hide_image(image_bytes, text, pw, salt=None, nonce=None, force_hmac=False):
    """embed the text and return new PNG bytes; raises BildCapacity if it does not fit. The Besitzer's key never logged."""
    rgba, w, h = _bild_load_rgba(image_bytes)
    need = len(text.encode("utf-8")) if isinstance(text, str) else len(text)
    cap = bild_capacity(w, h)
    if need > cap:
        raise BildCapacity(cap, need)
    _bild_embed(rgba, w, h, pw, _bild_pack(pw, text, salt=salt, nonce=nonce, force_hmac=force_hmac))
    return _bild_save_png(rgba, w, h)


def bild_reveal_image(image_bytes, pw):
    """the hidden text, or None for a wrong key / a damaged picture (not to be told apart). Never logged."""
    if not pw:
        return None
    try:
        rgba, w, h = _bild_load_rgba(image_bytes)
    except Exception:
        return None
    total = _bild_slot_count(w, h)
    if total < _BILD_OVERHEAD * 8:
        return None
    try:
        return _bild_unpack(pw, _bild_reader(rgba, w, h, pw), total)
    except Exception:
        return None


# ---- das Modul für den Browser (wortgetreu funk/stego.js; bauen.py legt dieses grosse Literal in die Zusatzdatei) ----
STEGO_JS = r"""/* MoveEye – «Botschaft im Bild» (Steganographie) – ein eigenständiges Modul, das im Browser (WebCrypto,
   Canvas) und in node (crypto.subtle, zlib) gleich rechnet. Es wird im «Digitalen Rucksack» eingebaut und
   braucht kein Netz; auf der Seite «Handy-Funkgerät» lädt es erst Phase 2. Für den Besitzer von MoveEye gemacht.

   Format (bitgleich zur Python-Seite quelle/639zzzzc_bild_stego.py):
     Schlüssel k = PBKDF2-HMAC-SHA256(Passwort, "MoveEye-Bild-v1"+salt, 200000, 32 Byte)
     danach AES-256-GCM (WebCrypto / cryptography) – oder, wenn kein AES da ist, ein HMAC-SHA256-
     Schlüsselstrom mit Encrypt-then-MAC (verschlüsseln, dann prüfen). Der Kopf (Version, Länge) ist
     mitverschlüsselt. Die Bytes liegen als LSB in den RGB-Kanälen, die Reihenfolge der Pixel ist eine
     vom Passwort abgeleitete Zufallsordnung: ohne Schlüssel sieht nichts anders aus als Rauschen.
   Nichts wird protokolliert. Text ist UTF-8. Ausgabe ist immer PNG. */
(function (root, factory) {
  var mod = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = mod;
  if (root) root.MWStego = mod;
})(typeof self !== "undefined" ? self : (typeof globalThis !== "undefined" ? globalThis : this), function () {
  "use strict";

  // ---- die Umgebung: WebCrypto im Browser und in node (crypto.subtle), zlib nur in node ----------------
  var g = (typeof self !== "undefined") ? self : (typeof globalThis !== "undefined" ? globalThis : {});
  var subtle = (g.crypto && g.crypto.subtle) ? g.crypto.subtle : null;
  var nodeCrypto = null, zlib = null, isNode = false;
  if (typeof process !== "undefined" && process.versions && process.versions.node) {
    isNode = true;
    try { nodeCrypto = require("crypto"); } catch (e) {}
    try { zlib = require("zlib"); } catch (e) {}
    if (!subtle && nodeCrypto && nodeCrypto.webcrypto) subtle = nodeCrypto.webcrypto.subtle;
  }

  var SALT_FIX = utf8("MoveEye-Bild-v1");
  var PERM_FIX = utf8("MoveEye-Bild-v1-perm");
  var SALT_LEN = 16, NONCE_LEN = 12, TAG_LEN = 16, HDR_LEN = 5;   // ver(1)+len(4)
  var OVERHEAD = SALT_LEN + NONCE_LEN + (HDR_LEN + TAG_LEN) + TAG_LEN;   // 16+12+21+16 = 65

  // ---- kleine Helfer -----------------------------------------------------------------------------------
  function utf8(s) { return new TextEncoder().encode(s); }
  function fromUtf8(b) { return new TextDecoder("utf-8", {fatal: true}).decode(b); }
  function cat() { var n = 0, i; for (i = 0; i < arguments.length; i++) n += arguments[i].length;
    var o = new Uint8Array(n), p = 0; for (i = 0; i < arguments.length; i++) { o.set(arguments[i], p); p += arguments[i].length; } return o; }
  function u32be(n) { return new Uint8Array([(n >>> 24) & 255, (n >>> 16) & 255, (n >>> 8) & 255, n & 255]); }
  function eq(a, b) { if (a.length !== b.length) return false; var d = 0; for (var i = 0; i < a.length; i++) d |= a[i] ^ b[i]; return d === 0; }

  // SHA-256 (eigene, synchrone Umsetzung – gleich im Browser und in node, auch für den PRNG und HMAC) -----
  function sha256(msg) {
    var K = sha256.K || (sha256.K = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
      0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,
      0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,
      0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,
      0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,
      0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]);
    var H = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    var l = msg.length, bl = ((l + 8) >> 6) + 1, M = new Uint8Array(bl * 64);
    M.set(msg); M[l] = 0x80;
    var bits = l * 8; M[bl * 64 - 4] = (bits >>> 24) & 255; M[bl * 64 - 3] = (bits >>> 16) & 255; M[bl * 64 - 2] = (bits >>> 8) & 255; M[bl * 64 - 1] = bits & 255;
    var w = new Int32Array(64), i, j, a, b, c, d, e, f, gg, h, t1, t2;
    var rotr = function (x, n) { return (x >>> n) | (x << (32 - n)); };
    for (i = 0; i < bl; i++) {
      for (j = 0; j < 16; j++) { var o = i * 64 + j * 4; w[j] = (M[o] << 24) | (M[o + 1] << 16) | (M[o + 2] << 8) | M[o + 3]; }
      for (j = 16; j < 64; j++) { var s0 = rotr(w[j-15],7) ^ rotr(w[j-15],18) ^ (w[j-15] >>> 3); var s1 = rotr(w[j-2],17) ^ rotr(w[j-2],19) ^ (w[j-2] >>> 10); w[j] = (w[j-16] + s0 + w[j-7] + s1) | 0; }
      a = H[0]; b = H[1]; c = H[2]; d = H[3]; e = H[4]; f = H[5]; gg = H[6]; h = H[7];
      for (j = 0; j < 64; j++) { var S1 = rotr(e,6) ^ rotr(e,11) ^ rotr(e,25); var ch = (e & f) ^ (~e & gg);
        t1 = (h + S1 + ch + K[j] + w[j]) | 0; var S0 = rotr(a,2) ^ rotr(a,13) ^ rotr(a,22); var maj = (a & b) ^ (a & c) ^ (b & c); t2 = (S0 + maj) | 0;
        h = gg; gg = f; f = e; e = (d + t1) | 0; d = c; c = b; b = a; a = (t1 + t2) | 0; }
      H[0]=(H[0]+a)|0;H[1]=(H[1]+b)|0;H[2]=(H[2]+c)|0;H[3]=(H[3]+d)|0;H[4]=(H[4]+e)|0;H[5]=(H[5]+f)|0;H[6]=(H[6]+gg)|0;H[7]=(H[7]+h)|0;
    }
    var out = new Uint8Array(32);
    for (i = 0; i < 8; i++) { out[i*4] = (H[i] >>> 24) & 255; out[i*4+1] = (H[i] >>> 16) & 255; out[i*4+2] = (H[i] >>> 8) & 255; out[i*4+3] = H[i] & 255; }
    return out;
  }
  function hmac256(key, msg) {
    var bk = key.length > 64 ? sha256(key) : key, k = new Uint8Array(64); k.set(bk);
    var ip = new Uint8Array(64), op = new Uint8Array(64), i;
    for (i = 0; i < 64; i++) { ip[i] = k[i] ^ 0x36; op[i] = k[i] ^ 0x5c; }
    return sha256(cat(op, sha256(cat(ip, msg))));
  }
  function pbkdf2(pass, salt, iter, dkLen) {
    // PBKDF2-HMAC-SHA256 (synchron, mit der eigenen hmac256 – gleich auf beiden Seiten)
    var out = new Uint8Array(dkLen), blocks = Math.ceil(dkLen / 32), off = 0, bi;
    for (bi = 1; bi <= blocks; bi++) {
      var u = hmac256(pass, cat(salt, u32be(bi))), t = u.slice(0), j, c;
      for (c = 1; c < iter; c++) { u = hmac256(pass, u); for (j = 0; j < 32; j++) t[j] ^= u[j]; }
      var take = Math.min(32, dkLen - off); out.set(t.subarray(0, take), off); off += take;
    }
    return out;
  }

  // ---- der PRNG und die Pixel-Reihenfolge --------------------------------------------------------------
  // Zähler-Strom aus SHA-256(seed || zähler), 8 Wörter je 32 Bit (little-endian in den 4 Bytes) – gleich in Python.
  function Prng(seed) { this.seed = seed; this.buf = null; this.pos = 8; this.ctr = 0; }
  Prng.prototype.word = function () {
    if (this.pos >= 8) {
      var c = new Uint8Array(8), n = this.ctr++;
      for (var i = 0; i < 8; i++) { c[i] = n & 255; n = Math.floor(n / 256); }   // 64 Bit little-endian
      this.buf = sha256(cat(this.seed, c)); this.pos = 0;
    }
    var o = this.pos * 4; this.pos++;
    return ((this.buf[o]) | (this.buf[o+1] << 8) | (this.buf[o+2] << 16) | (this.buf[o+3] << 24)) >>> 0;   // little-endian
  };
  Prng.prototype.below = function (n) {                        // gleichverteilt in [0, n) ohne Verzerrung
    if (n <= 0) return 0;
    var limit = Math.floor(0x100000000 / n) * n, x;
    do { x = this.word(); } while (x >= limit);
    return x % n;
  };
  // die ersten m Plätze einer Zufalls-Permutation von [0, total) (sparsames Fisher-Yates) ----------------
  function positions(pass, total, m) {
    if (typeof pass === "string") pass = utf8(pass);
    var pr = new Prng(sha256(cat(PERM_FIX, pass))), state = new Map(), out = new Int32Array(m), i;
    var getv = function (k) { return state.has(k) ? state.get(k) : k; };
    for (i = 0; i < m; i++) {
      var j = i + pr.below(total - i), vi = getv(i), vj = getv(j);
      out[i] = vj; state.set(j, vi); if (j !== i) state.set(i, vj);
    }
    return out;
  }

  // ---- AES-256-GCM (WebCrypto) und der HMAC-Ersatz -----------------------------------------------------
  function subNonce(nonce, tag) { return sha256(cat(nonce, utf8(tag))).subarray(0, NONCE_LEN); }
  async function aesEnc(k, nonce, pt) {
    var key = await subtle.importKey("raw", k, {name: "AES-GCM"}, false, ["encrypt"]);
    var ct = await subtle.encrypt({name: "AES-GCM", iv: nonce, tagLength: 128}, key, pt);
    return new Uint8Array(ct);
  }
  async function aesDec(k, nonce, ct) {
    var key = await subtle.importKey("raw", k, {name: "AES-GCM"}, false, ["decrypt"]);
    var pt = await subtle.decrypt({name: "AES-GCM", iv: nonce, tagLength: 128}, key, ct);
    return new Uint8Array(pt);
  }
  function macKeys(k) { return {e: sha256(cat(k, utf8("enc"))).slice(0, 32), m: sha256(cat(k, utf8("mac"))).slice(0, 32)}; }
  function keystream(ke, nonce, n) {
    var out = new Uint8Array(n), i = 0, blk = 0;
    while (i < n) { var ks = hmac256(ke, cat(nonce, u32be(blk++))); for (var j = 0; j < 32 && i < n; j++) out[i++] = ks[j]; }
    return out;
  }
  function hmacEnc(k, nonce, pt) {
    var mk = macKeys(k), ks = keystream(mk.e, nonce, pt.length), ct = new Uint8Array(pt.length), i;
    for (i = 0; i < pt.length; i++) ct[i] = pt[i] ^ ks[i];
    var tag = hmac256(mk.m, cat(nonce, ct)).subarray(0, TAG_LEN);
    return cat(ct, tag);
  }
  function hmacDec(k, nonce, blob) {
    if (blob.length < TAG_LEN) throw new Error("x");
    var mk = macKeys(k), ct = blob.subarray(0, blob.length - TAG_LEN), tag = blob.subarray(blob.length - TAG_LEN);
    if (!eq(hmac256(mk.m, cat(nonce, ct)).subarray(0, TAG_LEN), tag)) throw new Error("tag");
    var ks = keystream(mk.e, nonce, ct.length), pt = new Uint8Array(ct.length), i;
    for (i = 0; i < ct.length; i++) pt[i] = ct[i] ^ ks[i];
    return pt;
  }

  // ---- den Container bauen und lesen (reine Bytes, ohne Bild) -------------------------------------------
  async function pack(pass, text) {
    var msg = utf8(text), pw = utf8(pass);
    var salt = rand(SALT_LEN), nonce = rand(NONCE_LEN);
    var k = pbkdf2(pw, cat(SALT_FIX, salt), 200000, 32);
    var nH = subNonce(nonce, "H"), nB = subNonce(nonce, "B");
    var hdr = cat(new Uint8Array([1]), u32be(msg.length));
    var hdrct, bodyct;
    if (subtle) { hdrct = await aesEnc(k, nH, hdr); bodyct = await aesEnc(k, nB, msg); }
    else { hdrct = hmacEnc(k, nH, hdr); bodyct = hmacEnc(k, nB, msg); }
    return cat(salt, nonce, hdrct, bodyct);
  }
  // liest die Plätze bei Bedarf: salt, nonce, Kopf, Körper
  async function unpack(pass, readBytes, total) {
    var pw = utf8(pass);
    var salt = readBytes(0, SALT_LEN), nonce = readBytes(SALT_LEN, NONCE_LEN);
    var k = pbkdf2(pw, cat(SALT_FIX, salt), 200000, 32);
    var nH = subNonce(nonce, "H"), nB = subNonce(nonce, "B");
    var off = SALT_LEN + NONCE_LEN, hdrct = readBytes(off, HDR_LEN + TAG_LEN);
    var hdr = null;
    if (subtle) { try { hdr = await aesDec(k, nH, hdrct); } catch (e) {} }
    if (!hdr) { try { hdr = hmacDec(k, nH, hdrct); } catch (e) {} }
    if (!hdr || hdr.length !== HDR_LEN || hdr[0] !== 1) throw new Error("no message");
    var len = ((hdr[1] << 24) | (hdr[2] << 16) | (hdr[3] << 8) | hdr[4]) >>> 0;
    if (OVERHEAD + len > total) throw new Error("no message");
    var bodyct = readBytes(off + HDR_LEN + TAG_LEN, len + TAG_LEN), body = null;
    if (subtle) { try { body = await aesDec(k, nB, bodyct); } catch (e) {} }
    if (!body) { try { body = hmacDec(k, nB, bodyct); } catch (e) {} }
    if (!body) throw new Error("no message");
    return fromUtf8(body);
  }
  function rand(n) {
    var b = new Uint8Array(n);
    if (g.crypto && g.crypto.getRandomValues) g.crypto.getRandomValues(b);
    else if (nodeCrypto) b.set(nodeCrypto.randomBytes(n));
    else throw new Error("no random source");
    return b;
  }

  // ---- LSB in den RGB-Kanälen (Alpha bleibt unberührt) -------------------------------------------------
  // slots: pro Pixel 3 Plätze (R,G,B). slotToIndex(i) -> Position im RGBA-Puffer.
  function slotCount(w, h) { return w * h * 3; }
  function capacityChars(w, h) { return Math.max(0, Math.floor(slotCount(w, h) / 8) - OVERHEAD); }
  function embedBits(rgba, w, h, pass, payload) {
    var total = slotCount(w, h), nbits = payload.length * 8;
    if (nbits > total) throw new Error("too big");
    var pos = positions(pass, total, nbits), i;
    for (i = 0; i < nbits; i++) {
      var slot = pos[i], px = (slot / 3) | 0, ch = slot % 3, idx = px * 4 + ch;   // RGBA, Alpha übersprungen
      var bit = (payload[i >> 3] >> (7 - (i & 7))) & 1;                            // MSB zuerst
      rgba[idx] = (rgba[idx] & 0xfe) | bit;
    }
  }
  function makeReader(rgba, w, h, pass) {
    var total = slotCount(w, h), cache = [];   // cache[i] = Position von Rang i (lazy, aber positions() rechnet in einem Zug)
    return function (byteOff, nbytes) {
      var need = (byteOff + nbytes) * 8, out = new Uint8Array(nbytes), i;
      if (cache.length < need) cache = positions(pass, total, Math.min(total, Math.max(need, cache.length)));
      for (i = 0; i < nbytes * 8; i++) {
        var rank = byteOff * 8 + i, slot = cache[rank], px = (slot / 3) | 0, ch = slot % 3, idx = px * 4 + ch;
        var bit = rgba[idx] & 1; out[i >> 3] |= bit << (7 - (i & 7));
      }
      return out;
    };
  }

  // ---- PNG lesen / schreiben: in node mit zlib, im Browser mit Canvas ----------------------------------
  function crc32(buf) {
    var t = crc32.t; if (!t) { t = crc32.t = new Int32Array(256); for (var n = 0; n < 256; n++) { var c = n; for (var kk = 0; kk < 8; kk++) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1); t[n] = c; } }
    var crc = -1; for (var i = 0; i < buf.length; i++) crc = (crc >>> 8) ^ t[(crc ^ buf[i]) & 255]; return (crc ^ -1) >>> 0;
  }
  function pngEncodeNode(rgba, w, h) {
    var stride = w * 4, raw = new Uint8Array((stride + 1) * h), y;
    for (y = 0; y < h; y++) { raw[y * (stride + 1)] = 0; raw.set(rgba.subarray(y * stride, y * stride + stride), y * (stride + 1) + 1); }
    var comp = zlib.deflateSync(Buffer.from(raw.buffer, raw.byteOffset, raw.byteLength), {level: 6});
    var chunks = [];
    chunks.push(new Uint8Array([137,80,78,71,13,10,26,10]));
    var ihdr = new Uint8Array(13); var dv = new DataView(ihdr.buffer);
    dv.setUint32(0, w); dv.setUint32(4, h); ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;   // 8-bit RGBA
    chunks.push(chunkNode("IHDR", ihdr));
    chunks.push(chunkNode("IDAT", new Uint8Array(comp.buffer, comp.byteOffset, comp.byteLength)));
    chunks.push(chunkNode("IEND", new Uint8Array(0)));
    return cat.apply(null, chunks);
  }
  function chunkNode(type, data) {
    var tb = utf8(type), len = new Uint8Array(4), dv = new DataView(len.buffer); dv.setUint32(0, data.length);
    var body = cat(tb, data), crc = new Uint8Array(4); new DataView(crc.buffer).setUint32(0, crc32(body));
    return cat(len, body, crc);
  }
  function pngDecodeNode(bytes) {
    var p = 8, idat = [], w = 0, h = 0, ct = 0, bd = 0;
    while (p < bytes.length) {
      var len = (bytes[p] << 24 | bytes[p+1] << 16 | bytes[p+2] << 8 | bytes[p+3]) >>> 0;
      var type = fromUtf8(bytes.subarray(p + 4, p + 8)), d = bytes.subarray(p + 8, p + 8 + len);
      if (type === "IHDR") { w = (d[0]<<24|d[1]<<16|d[2]<<8|d[3])>>>0; h = (d[4]<<24|d[5]<<16|d[6]<<8|d[7])>>>0; bd = d[8]; ct = d[9]; if (d[12] !== 0) throw new Error("interlaced"); }
      else if (type === "IDAT") idat.push(d.slice(0));
      else if (type === "IEND") break;
      p += 12 + len;
    }
    if (bd !== 8 || (ct !== 2 && ct !== 6)) throw new Error("unsupported PNG");
    var raw = new Uint8Array(zlib.inflateSync(Buffer.concat(idat.map(function (u) { return Buffer.from(u.buffer, u.byteOffset, u.byteLength); }))));
    var chn = ct === 6 ? 4 : 3, stride = w * chn, rgba = new Uint8Array(w * h * 4), prev = new Uint8Array(stride), y, x, c;
    for (y = 0; y < h; y++) {
      var f = raw[y * (stride + 1)], line = raw.subarray(y * (stride + 1) + 1, y * (stride + 1) + 1 + stride), cur = new Uint8Array(stride);
      for (x = 0; x < stride; x++) {
        var a = x >= chn ? cur[x - chn] : 0, b = prev[x], cc = x >= chn ? prev[x - chn] : 0, v = line[x];
        if (f === 1) v = (v + a) & 255; else if (f === 2) v = (v + b) & 255; else if (f === 3) v = (v + ((a + b) >> 1)) & 255;
        else if (f === 4) { var pp = a + b - cc, pa = Math.abs(pp - a), pb = Math.abs(pp - b), pc = Math.abs(pp - cc), pr = (pa <= pb && pa <= pc) ? a : (pb <= pc ? b : cc); v = (v + pr) & 255; }
        cur[x] = v;
      }
      for (x = 0; x < w; x++) { var o = (y * w + x) * 4, s = x * chn; rgba[o] = cur[s]; rgba[o+1] = cur[s+1]; rgba[o+2] = cur[s+2]; rgba[o+3] = chn === 4 ? cur[s+3] : 255; }
      prev = cur;
    }
    return {width: w, height: h, data: rgba};
  }
  // Browser: ein beliebiges Bild (PNG/JPEG) -> RGBA über Canvas; RGBA -> PNG-Blob -----------------------
  async function decodeBrowser(bytes) {
    var blob = new Blob([bytes]), url = URL.createObjectURL(blob);
    try {
      var img = await new Promise(function (res, rej) { var im = new Image(); im.onload = function () { res(im); }; im.onerror = function () { rej(new Error("image")); }; im.src = url; });
      var cv = document.createElement("canvas"); cv.width = img.naturalWidth; cv.height = img.naturalHeight;
      var cx = cv.getContext("2d", {willReadFrequently: true}); cx.drawImage(img, 0, 0);
      var id = cx.getImageData(0, 0, cv.width, cv.height);
      return {width: cv.width, height: cv.height, data: new Uint8Array(id.data.buffer.slice(0))};
    } finally { URL.revokeObjectURL(url); }
  }
  async function encodeBrowser(rgba, w, h) {
    var cv = document.createElement("canvas"); cv.width = w; cv.height = h;
    var cx = cv.getContext("2d"); var id = cx.createImageData(w, h); id.data.set(rgba); cx.putImageData(id, 0, 0);
    var blob = await new Promise(function (res) { cv.toBlob(function (b) { res(b); }, "image/png"); });
    return new Uint8Array(await blob.arrayBuffer());
  }
  function decode(bytes) { return isNode ? Promise.resolve(pngDecodeNode(bytes)) : decodeBrowser(bytes); }
  function encode(rgba, w, h) { return isNode ? Promise.resolve(pngEncodeNode(rgba, w, h)) : encodeBrowser(rgba, w, h); }

  // ---- die beiden Aufgaben --------------------------------------------------------------------------------
  async function hide(imageBytes, text, pass) {
    if (!pass) throw new Error("key");
    var img = await decode(imageBytes);
    var cap = capacityChars(img.width, img.height), need = utf8(text).length;
    if (need > cap) { var err = new Error("too big"); err.capacity = cap; err.need = need; throw err; }
    var payload = await pack(pass, text);
    embedBits(img.data, img.width, img.height, pass, payload);
    return encode(img.data, img.width, img.height);   // immer PNG
  }
  async function reveal(imageBytes, pass) {
    if (!pass) return null;
    var img;
    try { img = await decode(imageBytes); } catch (e) { return null; }
    try {
      var total = slotCount(img.width, img.height);
      if (total < OVERHEAD * 8) return null;
      var reader = makeReader(img.data, img.width, img.height, pass);
      return await unpack(pass, reader, total);
    } catch (e) { return null; }   // falscher Schlüssel / beschädigt: nicht zu unterscheiden
  }
  function capacity(w, h) { return capacityChars(w, h); }

  return {hide: hide, reveal: reveal, capacity: capacity, OVERHEAD: OVERHEAD,
          _internal: {sha256: sha256, hmac256: hmac256, pbkdf2: pbkdf2, positions: positions, pack: pack, unpack: unpack,
                      pngDecodeNode: isNode ? pngDecodeNode : null, pngEncodeNode: isNode ? pngEncodeNode : null, hasAES: !!subtle}};
});
"""

# ---- die zusätzlichen Stile der Übersichts-Zeilen und der Unterseiten (wie «Mehr») ----------------------------------
STEGO_CSS = r"""
.tz-hub{display:flex;flex-direction:column;gap:10px;margin:0 0 12px}
.tz-row{display:flex;align-items:center;gap:12px;text-decoration:none;color:inherit;min-height:60px;cursor:pointer;border:1px solid var(--line);border-radius:var(--r);background:var(--panel);padding:12px 14px;box-shadow:var(--shadow)}
.tz-row .ri{font-size:28px;width:34px;text-align:center;flex:none}
.tz-row .rt{flex:1;min-width:0}.tz-row .rt b{display:block}.tz-row .rt small{color:var(--mut);display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tz-row .rc{color:var(--mut);font-size:20px;flex:none}
.tz-back{display:flex;align-items:center;gap:10px;margin:0 0 12px}
.tz-back a{color:var(--acc2);text-decoration:none;font-weight:600;min-height:40px;display:inline-flex;align-items:center}
.tz-back b{flex:1;min-width:0;font-size:18px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sg-card{border:1px solid var(--line);border-radius:var(--r);background:var(--panel);padding:14px;margin:0 0 12px;box-shadow:var(--shadow)}
.sg-card h3{margin:0 0 10px;font-size:16px}
.sg-f{display:flex;flex-direction:column;gap:6px;margin:0 0 10px}.sg-f>span{font-size:13px;color:var(--mut)}
.sg-f textarea,.sg-f input[type=text],.sg-f input[type=password]{background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:10px;font:inherit;width:100%;box-sizing:border-box}
.sg-f textarea{min-height:96px;resize:vertical}
.sg-cap{font-size:12.5px;color:var(--mut)}.sg-cap.bad{color:var(--red)}
.sg-row{display:flex;align-items:center;gap:8px;font-size:14px;min-height:40px}
.sg-btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}.sg-btns button{min-height:42px}
.sg-note{font-size:12.5px;color:var(--mut);line-height:1.45;margin:8px 0 0;border-left:3px solid var(--line);padding:2px 0 2px 10px}
.sg-out{border:1px solid var(--grn);border-radius:10px;padding:10px 12px;margin:10px 0 0;font-size:14px}
.sg-out.bad{border-color:var(--red)}
.sg-read{white-space:pre-wrap;overflow-wrap:anywhere;background:var(--field);border:1px solid var(--line);border-radius:10px;padding:12px;margin:8px 0 0;font-size:15px;line-height:1.5;-webkit-user-select:text;user-select:text}
.sg-thumb{max-width:120px;max-height:120px;border-radius:8px;border:1px solid var(--line);display:block;margin:4px 0}
.tz-it .ac .sg-b{flex:none;min-width:40px}
"""

# ---- die Übersicht und die Dialoge (läuft nach COMMON_JS und nach dem Datei-IIFE von 639zzc) -----------------------
STEGO_UI = r"""
(function () {
  var main = document.getElementById("tz"), S = window.MWStego;
  if (!main || !S) return;
  var $ = function (s) { return document.querySelector(s); };
  var enc = new TextEncoder();
  var inBag = location.pathname.indexOf("/tausch") === 0;   // im Rucksack (dann auch «in den Rucksack»), sonst offline
  function key(k) { return (typeof t === "function" && t(k) !== k) ? t(k) : k; }
  // --- die Teile des Datei-Bereichs in eine Unterseite verschieben ---
  var quota = $("#tz-quota"), msg = $("#tz-msg"), tabs = main.querySelector(".tz-tabs"), crumb = $("#tz-crumb"),
      tool = main.querySelector(".tz-tool"), hint = $("#tz-hint"), up = $("#tz-up"), bodyEl = $("#tz-body"),
      pack = $("#tz-pack"), tzh = main.querySelector(".tz-h"), store = $("#tz-store");
  var hub = document.createElement("div"); hub.className = "tz-hub"; hub.id = "tz-hub";
  var subFiles = document.createElement("div"); subFiles.id = "tz-sub-files"; subFiles.hidden = true;
  var subMsg = document.createElement("div"); subMsg.id = "tz-sub-msg"; subMsg.hidden = true;
  function backBar(title) { var b = document.createElement("div"); b.className = "tz-back";
    var a = document.createElement("a"); a.href = "#"; a.textContent = "‹ " + key("Back"); a.onclick = function (e) { e.preventDefault(); go(""); };
    var t2 = document.createElement("b"); t2.textContent = title; b.append(a, t2); return b; }
  function row(icon, title, sub, fn) { var r = document.createElement("div"); r.className = "tz-row"; r.setAttribute("role", "button"); r.tabIndex = 0;
    var i = document.createElement("span"); i.className = "ri"; i.textContent = icon;
    var tx = document.createElement("span"); tx.className = "rt"; var b = document.createElement("b"); b.textContent = title;
    var s = document.createElement("small"); s.textContent = sub; tx.append(b, s);
    var c = document.createElement("span"); c.className = "rc"; c.textContent = "›"; r.append(i, tx, c);
    r.onclick = fn; r.onkeydown = function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fn(); } };
    r._sub = s; return r; }
  var rowFiles = row("📁", key("Files"), key("Share photos, videos and documents - for everyone or only for you"), function () { go("dateien"); });
  var rowMsg = row("🔏", key("Message in a picture"), key("Hide a secret text in a photo - only openable with the key"), function () { go("botschaft"); });
  // Zeilen einhängen: Packlisten (falls da), Dateien, Botschaft
  if (pack) { pack.remove(); pack.classList.add("tz-row-keep"); hub.appendChild(pack); }
  hub.appendChild(rowFiles); hub.appendChild(rowMsg);
  // Datei-Teile in die Unterseite
  subFiles.appendChild(backBar(key("Files")));
  [quota, msg, tabs, crumb, tool, hint, up, bodyEl].forEach(function (n) { if (n) subFiles.appendChild(n); });
  tzh.insertAdjacentElement("afterend", hub);
  hub.insertAdjacentElement("afterend", subFiles);
  subFiles.insertAdjacentElement("afterend", subMsg);
  if (store) tzh.appendChild(store);
  // Nutzung in die graue Zeile der «Dateien» spiegeln
  function fmtShort(n) { n = +n || 0; var u = n >= 1073741824 ? [n / 1073741824, " GB"] : n >= 1048576 ? [n / 1048576, " MB"] : [Math.max(n ? 1 : 0, n / 1024), " KB"];
    var s = u[0].toFixed(u[0] < 10 && u[1] !== " KB" ? 1 : 0).replace(/\.0$/, ""); return (typeof LANG !== "undefined" && LANG !== "en" ? s.replace(".", ",") : s) + u[1]; }
  if (window.MutationObserver) new MutationObserver(function () {
    var q1 = $("#tz-qt1"); if (q1 && q1.textContent && q1.textContent !== "…") rowFiles._sub.textContent = q1.textContent;
  }).observe(subFiles, {subtree: true, childList: true, characterData: true});
  // --- Ansichten umschalten (Hash hält alte Tiefenlinks am Leben) ---
  function show(v) { hub.hidden = v !== ""; subFiles.hidden = v !== "dateien"; subMsg.hidden = v !== "botschaft";
    try { window.scrollTo(0, 0); } catch (e) {} }
  function go(v) { if ((location.hash.slice(1) || "") === v) show(v); else location.hash = v ? "#" + v : "#"; }
  function applyHash() { var v = (location.hash || "").replace(/^#/, ""); show(v === "dateien" || v === "botschaft" ? v : ""); }
  window.addEventListener("hashchange", applyHash);
  // beim Ziehen von Dateien automatisch zur Unterseite «Dateien»
  ["dragenter", "dragover"].forEach(function (ev) { window.addEventListener(ev, function () { if (subFiles.hidden) go("dateien"); }); });
  // --- die Seite «🔏 Botschaft im Bild» ---
  subMsg.appendChild(backBar("🔏 " + key("Message in a picture")));
  var hideCard = buildHide();
  subMsg.appendChild(hideCard);
  subMsg.appendChild(buildRead());
  applyHash();

  function fileToBytes(file) { return new Promise(function (res, rej) { var r = new FileReader();
    r.onload = function () { res(new Uint8Array(r.result)); }; r.onerror = function () { rej(new Error("read")); }; r.readAsArrayBuffer(file); }); }
  function dims(file) { return new Promise(function (res) { var u = URL.createObjectURL(file), im = new Image();
    im.onload = function () { res([im.naturalWidth, im.naturalHeight]); URL.revokeObjectURL(u); };
    im.onerror = function () { res([0, 0]); URL.revokeObjectURL(u); }; im.src = u; }); }
  function remember(k) { try { return localStorage.getItem("mw-stego-key") || ""; } catch (e) { return ""; } }
  function setRemember(on, v) { try { if (on && v) localStorage.setItem("mw-stego-key", v); else localStorage.removeItem("mw-stego-key"); } catch (e) {} }

  function buildHide() {
    var c = document.createElement("div"); c.className = "sg-card";
    c.innerHTML = '<h3>🔏 ' + esc(key("Hide a message")) + '</h3>';
    var pick = field(key("Choose a picture")); var fi = document.createElement("input"); fi.type = "file"; fi.accept = "image/*"; pick.appendChild(fi);
    var thumb = document.createElement("img"); thumb.className = "sg-thumb"; thumb.hidden = true; pick.appendChild(thumb);
    var cap = document.createElement("div"); cap.className = "sg-cap"; pick.appendChild(cap);
    var mf = field(key("Message")); var ta = document.createElement("textarea"); ta.maxLength = 200000; mf.appendChild(ta);
    var kf = field(key("Key")); var ki = document.createElement("input"); ki.type = "password"; ki.autocomplete = "off"; ki.value = remember(); kf.appendChild(ki);
    var rem = document.createElement("label"); rem.className = "sg-row";
    var cb = document.createElement("input"); cb.type = "checkbox"; cb.checked = !!remember(); rem.append(cb, document.createTextNode(" " + key("Remember on this device")));
    var btns = document.createElement("div"); btns.className = "sg-btns";
    var go2 = document.createElement("button"); go2.type = "button"; go2.textContent = "🔏 " + key("Hide in the picture"); go2.disabled = true;
    btns.appendChild(go2);
    var note = document.createElement("div"); note.className = "sg-note"; note.textContent = key("Send as a file (AirDrop, mail, Signal/WhatsApp «as document»). Sent as a photo, WhatsApp & co. destroy the message.");
    var out = document.createElement("div"); out.className = "sg-out"; out.hidden = true;
    c.append(pick, mf, kf, rem, btns, note, out);
    var curDims = [0, 0], curCap = 0, pre = null;   // pre: ein Bild aus dem Rucksack ({bytes, name})
    function updCap() {
      if (!curDims[0]) { cap.textContent = ""; go2.disabled = true; return; }
      var used = enc.encode(ta.value).length, left = curCap - used;
      cap.classList.toggle("bad", left < 0);
      cap.textContent = left >= 0 ? key("fits about {n} characters").replace("{n}", left) : key("{n} characters too many").replace("{n}", -left);
      go2.disabled = !(pre || (fi.files && fi.files[0])) || left < 0 || !ta.value.length;
    }
    async function useBlobLike(blob, name) { thumb.src = URL.createObjectURL(blob); thumb.hidden = false;
      curDims = await dims(blob); curCap = S.capacity(curDims[0], curDims[1]); updCap(); }
    fi.onchange = async function () { out.hidden = true; pre = null; var f = fi.files && fi.files[0];
      if (!f) { thumb.hidden = true; curDims = [0, 0]; updCap(); return; } await useBlobLike(f, f.name); };
    c.loadPrefill = async function (bytes, name) { out.hidden = true; fi.value = ""; pre = {bytes: bytes, name: name};
      await useBlobLike(new Blob([bytes], {type: "image/png"}), name); };
    ta.oninput = updCap;
    go2.onclick = async function () {
      var f = fi.files && fi.files[0]; if (!pre && !f) return;
      if (!ki.value) { return showOut(out, key("Enter a key."), true); }
      setRemember(cb.checked, ki.value);
      go2.disabled = true; showOut(out, "… " + key("Working …"), false);
      try {
        var src = pre ? pre.bytes : await fileToBytes(f), nm = pre ? pre.name : (f.name || "bild");
        var png = await S.hide(src, ta.value, ki.value);
        var base = nm.replace(/\.[^.]+$/, "") + "_b.png";
        var blob = new Blob([png], {type: "image/png"});
        deliver(out, blob, base);
      } catch (e) {
        if (e && e.capacity !== undefined) showOut(out, key("The message is too long for this picture (about {n} characters fit).").replace("{n}", e.capacity), true);
        else showOut(out, key("The picture could not be processed."), true);
      }
      go2.disabled = false;
    };
    return c;
  }

  function deliver(out, blob, name) {
    out.className = "sg-out"; out.hidden = false; out.textContent = "";
    out.appendChild(document.createTextNode("✓ " + key("Hidden ✓ – the new picture «{f}» is ready.").replace("{f}", name) + " "));
    var btns = document.createElement("div"); btns.className = "sg-btns";
    var file = (window.File && typeof File === "function") ? new File([blob], name, {type: "image/png"}) : null;
    if (navigator.share && file && navigator.canShare && navigator.canShare({files: [file]})) {
      var sh = document.createElement("button"); sh.type = "button"; sh.textContent = "📤 " + key("Share as a file");
      sh.onclick = function () { navigator.share({files: [file], title: name}).catch(function () {}); }; btns.appendChild(sh);
    }
    var dl = document.createElement("a"); dl.className = "btn"; dl.textContent = "⬇ " + key("Download"); dl.href = URL.createObjectURL(blob); dl.download = name; btns.appendChild(dl);
    if (inBag && window.MW_BAG_UP !== false) {
      var sv = document.createElement("button"); sv.type = "button"; sv.className = "sec"; sv.textContent = "🎒 " + key("Save in the backpack");
      sv.onclick = function () { sv.disabled = true; uploadBlob(name, blob).then(function (ok) {
        showOut(out, ok ? "✓ " + key("Saved in the backpack: {f}").replace("{f}", name) : "⚠ " + key("Could not save in the backpack."), !ok);
      }); }; btns.appendChild(sv);
    }
    out.appendChild(btns);
  }

  function buildRead() {
    var c = document.createElement("div"); c.className = "sg-card";
    c.innerHTML = '<h3>🔎 ' + esc(key("Read a message")) + '</h3>';
    var pick = field(key("Choose a picture")); var fi = document.createElement("input"); fi.type = "file"; fi.accept = "image/*"; pick.appendChild(fi);
    var kf = field(key("Key")); var ki = document.createElement("input"); ki.type = "password"; ki.autocomplete = "off"; ki.value = remember(); kf.appendChild(ki);
    var btns = document.createElement("div"); btns.className = "sg-btns";
    var go2 = document.createElement("button"); go2.type = "button"; go2.textContent = "🔎 " + key("Read the message"); btns.appendChild(go2);
    var out = document.createElement("div"); out.className = "sg-out"; out.hidden = true;
    var read = document.createElement("div"); read.className = "sg-read"; read.hidden = true;
    c.append(pick, kf, btns, out, read);
    go2.onclick = async function () {
      read.hidden = true; var f = fi.files && fi.files[0];
      if (!f) return showOut(out, key("Choose a picture."), true);
      if (!ki.value) return showOut(out, key("Enter a key."), true);
      go2.disabled = true; showOut(out, "… " + key("Reading …"), false);
      var txt = null;
      try { txt = await S.reveal(await fileToBytes(f), ki.value); } catch (e) { txt = null; }
      go2.disabled = false;
      if (txt === null || txt === undefined) { showOut(out, "🚫 " + key("no message found or wrong key"), true); return; }
      out.hidden = true; read.hidden = false; read.textContent = txt;   // nur anzeigen, nie speichern
    };
    return c;
  }

  // --- in jeder Bild-Kachel des Datei-Bereichs eine kleine 🔏-Aktion ---
  if (bodyEl && window.MutationObserver) {
    var grid = bodyEl.querySelector("#tz-grid") || bodyEl;
    new MutationObserver(function () {
      grid.querySelectorAll(".tz-it").forEach(function (it) {
        if (it._sgDone) return; it._sgDone = true;
        var dl = it.querySelector('a[href^="/tausch/dl/"]'); var img = it.querySelector(".th img");
        if (!dl || !img) return;   // nur echte Bilder
        var ac = it.querySelector(".ac"); if (!ac) { ac = document.createElement("div"); ac.className = "ac"; it.appendChild(ac); }
        var b = document.createElement("button"); b.type = "button"; b.className = "sec sg-b"; b.title = key("Hide a message"); b.textContent = "🔏";
        b.onclick = async function (e) { e.stopPropagation();
          try { var bytes = new Uint8Array(await (await fetch(dl.getAttribute("href"), {cache: "no-store"})).arrayBuffer());
            prefillHide(bytes, (it.querySelector(".nm") && it.querySelector(".nm").textContent) || "bild"); } catch (err) {} };
        ac.insertBefore(b, ac.firstChild);
      });
    }).observe(grid, {childList: true, subtree: true});
  }
  function prefillHide(bytes, name) { go("botschaft");
    if (hideCard.loadPrefill) hideCard.loadPrefill(bytes, name);
    hideCard.scrollIntoView({block: "start"}); }

  function field(label) { var f = document.createElement("label"); f.className = "sg-f"; var s = document.createElement("span"); s.textContent = label; f.appendChild(s); return f; }
  function esc(s) { var d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
  function showOut(out, txt, bad) { out.hidden = false; out.className = "sg-out" + (bad ? " bad" : ""); out.textContent = txt; }

  async function uploadBlob(name, blob) {
    try {
      var st = await post("/api/tausch", {action: "start", name: name, size: blob.size, area: "all", folder: "", lang: (typeof LANG !== "undefined" ? LANG : "de")});
      if (!st || !st.ok || !st.id) return false;
      var id = st.id, chunk = st.chunk || 1048576, off = st.have || 0, buf = new Uint8Array(await blob.arrayBuffer());
      while (off < buf.length) {
        var end = Math.min(buf.length, off + chunk);
        var r = await fetch("/api/tausch/chunk?id=" + encodeURIComponent(id) + "&off=" + off, {method: "POST", body: buf.subarray(off, end)});
        var j = await r.json(); if (!j.ok) return false; off = j.have;
      }
      var fin = await post("/api/tausch", {action: "finish", id: id, lang: (typeof LANG !== "undefined" ? LANG : "de")});
      return !!(fin && fin.ok);
    } catch (e) { return false; }
  }
})();
"""

# ---- die Übersetzungen (englischer Schlüssel: Deutsch, français, italiano, rumantsch) -------------------------------
_HX_STEGO = {
    'Back': ('Zurück', 'Retour', 'Indietro', 'Enavos'),
    'Files': ('Dateien', 'Fichiers', 'File', 'Datotecas'),
    'Message in a picture': ('Botschaft im Bild', 'Message dans une image', 'Messaggio nell’immagine', 'Messadi en ina maletg'),
    'Hide a secret text in a photo - only openable with the key': ('Einen geheimen Text in ein Foto legen – nur mit dem Schlüssel lesbar', 'Cacher un texte secret dans une photo – lisible seulement avec la clé', 'Nascondere un testo segreto in una foto – leggibile solo con la chiave', 'Zuppar in text secret en ina foto – legibel mo cun la clav'),
    'Hide a message': ('Botschaft verstecken', 'Cacher un message', 'Nascondere un messaggio', 'Zuppar in messadi'),
    'Read a message': ('Botschaft lesen', 'Lire un message', 'Leggere un messaggio', 'Leger in messadi'),
    'Choose a picture': ('Bild wählen', 'Choisir une image', 'Scegliere un’immagine', 'Tscherner ina maletg'),
    'Choose a picture.': ('Wähle ein Bild.', 'Choisis une image.', 'Scegli un’immagine.', 'Tscherna ina maletg.'),
    'Message': ('Nachricht', 'Message', 'Messaggio', 'Messadi'),
    'Key': ('Schlüssel', 'Clé', 'Chiave', 'Clav'),
    'fits about {n} characters': ('passt noch ca. {n} Zeichen', 'encore env. {n} caractères', 'ancora circa {n} caratteri', 'anc var. {n} caracters'),
    '{n} characters too many': ('{n} Zeichen zu viel', '{n} caractères de trop', '{n} caratteri di troppo', '{n} caracters memia bler'),
    'The message is too long for this picture (about {n} characters fit).': ('Die Botschaft ist zu lang für dieses Bild (es passen ca. {n} Zeichen).', 'Le message est trop long pour cette image (env. {n} caractères possibles).', 'Il messaggio è troppo lungo per questa immagine (ci stanno circa {n} caratteri).', 'Il messadi è memia lung per questa maletg (anc var. {n} caracters).'),
    'Remember on this device': ('Auf diesem Gerät merken', 'Retenir sur cet appareil', 'Ricorda su questo dispositivo', 'Memorisar sin quest apparat'),
    'Hide in the picture': ('Im Bild verstecken', 'Cacher dans l’image', 'Nascondi nell’immagine', 'Zuppar en la maletg'),
    'Read the message': ('Botschaft lesen', 'Lire le message', 'Leggi il messaggio', 'Leger il messadi'),
    'Enter a key.': ('Gib einen Schlüssel ein.', 'Saisis une clé.', 'Inserisci una chiave.', 'Dai en ina clav.'),
    'Working …': ('Arbeite …', 'Travail en cours …', 'Elaborazione …', 'Lavur en curs …'),
    'Reading …': ('Lese …', 'Lecture …', 'Lettura …', 'Leger …'),
    'Hidden ✓ – the new picture «{f}» is ready.': ('Versteckt ✓ – das neue Bild «{f}» ist fertig.', 'Caché ✓ – la nouvelle image «{f}» est prête.', 'Nascosto ✓ – la nuova immagine «{f}» è pronta.', 'Zuppà ✓ – la nova maletg «{f}» è pronta.'),
    'Share as a file': ('Als Datei teilen', 'Partager comme fichier', 'Condividi come file', 'Parter sco datoteca'),
    'Save in the backpack': ('In den Rucksack', 'Dans le sac à dos', 'Nello zaino', 'En il satgados'),
    'Saved in the backpack: {f}': ('Im Rucksack gespeichert: {f}', 'Enregistré dans le sac à dos : {f}', 'Salvato nello zaino: {f}', 'Memorisà en il satgados: {f}'),
    'Could not save in the backpack.': ('Konnte nicht im Rucksack gespeichert werden.', 'Impossible d’enregistrer dans le sac à dos.', 'Impossibile salvare nello zaino.', 'Betg pussaivel da memorisar en il satgados.'),
    'no message found or wrong key': ('keine Botschaft gefunden oder falscher Schlüssel', 'aucun message trouvé ou mauvaise clé', 'nessun messaggio trovato o chiave errata', 'nagin messadi chattà u clav faussa'),
    'The picture could not be processed.': ('Das Bild konnte nicht verarbeitet werden.', 'L’image n’a pas pu être traitée.', 'Impossibile elaborare l’immagine.', 'La maletg na pudeva betg vegnir elaborada.'),
    'The picture could not be opened.': ('Das Bild konnte nicht geöffnet werden.', 'L’image n’a pas pu être ouverte.', 'Impossibile aprire l’immagine.', 'La maletg na pudeva betg vegnir averta.'),
    'Send as a file (AirDrop, mail, Signal/WhatsApp «as document»). Sent as a photo, WhatsApp & co. destroy the message.': ('Als Datei verschicken (AirDrop, Mail, Signal/WhatsApp «als Dokument»). Als Foto verschickt, zerstören WhatsApp & Co. die Botschaft.', 'Envoyer comme fichier (AirDrop, mail, Signal/WhatsApp « en document »). Envoyé comme photo, WhatsApp et cie détruisent le message.', 'Inviare come file (AirDrop, mail, Signal/WhatsApp « come documento »). Inviato come foto, WhatsApp e simili distruggono il messaggio.', 'Trametter sco datoteca (AirDrop, mail, Signal/WhatsApp « sco document »). Tramess sco foto, destrueschan WhatsApp & co. il messadi.'),
}

for _k, _v in _HX_STEGO.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_STEGO_DE = {_k: _v[0] for _k, _v in _HX_STEGO.items()}
_STEGO_DE["Share photos, videos and documents - for everyone or only for you"] = DE.get(
    "Share photos, videos and documents - for everyone or only for you", "")

# ---- Seite /tausch umbauen: Symbol 🎒, Packlisten-Symbol 📋, Modul + Übersicht einbauen ----------------------------
TAUSCH_PAGE = TAUSCH_PAGE.replace('<h2>\U0001F4C1 <span data-i18n="File exchange">', '<h2>\U0001F392 <span data-i18n="File exchange">', 1)
TAUSCH_PAGE = TAUSCH_PAGE.replace('<span style="font-size:28px">\U0001F392</span><span style="flex:1;min-width:0"><b data-i18n="Packing lists">',
                                  '<span style="font-size:28px">\U0001F4CB</span><span style="flex:1;min-width:0"><b data-i18n="Packing lists">', 1)

_STEGO_BLOCK = ("<style>" + STEGO_CSS + "</style>\n<script>\n" + STEGO_JS + "\n</script>\n<script>\n"
                + "try{Object.assign(I18N.de, " + json.dumps(_STEGO_DE, ensure_ascii=False) + ");}catch(e){}\n"
                + STEGO_UI + "\n</script>")
if "MWStego" not in TAUSCH_PAGE:
    TAUSCH_PAGE = TAUSCH_PAGE.replace("</script>\n</body></html>", "</script>\n" + _STEGO_BLOCK + "\n</body></html>", 1)


def bild_selftest():
    # 1. die Zahlen und ein Rundlauf (Python-Kern, bitgleich zum Browser-Modul)
    assert _BILD_OVERHEAD == 65
    assert bild_capacity(200, 150) == 200 * 150 * 3 // 8 - 65
    from PIL import Image
    import io as _io
    _b = _io.BytesIO(); Image.new("RGBA", (120, 90), (12, 34, 56, 255)).save(_b, "PNG"); _base = _b.getvalue()
    _txt = "Besitzer-Test: Grüße 😀 – Treffpunkt 07:00."
    _png = bild_hide_image(_base, _txt, "schlüssel!")
    assert bild_reveal_image(_png, "schlüssel!") == _txt, "round trip"
    assert bild_reveal_image(_png, "falsch") is None, "wrong key must not read"
    assert _png[:8] == b"\x89PNG\r\n\x1a\n", "output is PNG"
    # 2. der gemeinsame Test-Vektor (bitgleich Python ↔ funk/stego.js, siehe werkzeuge/stego_test.py)
    _cont = bytes.fromhex('000102030405060708090a0b0c0d0e0f6465666768696a6b6c6d6e6f78e90763b1ef059fb32e046820d56215b87d9864e68804b21dc36c8371f3a1ddfccc58fc35921671a6856f08b9ff62bb75d7c0f83c5007ad7ccb12098c4a16baee220f213b8a31336144f2c90e24ecc4ba28efcf32b27a9e')
    assert _bild_unpack('MoveEye-Vektor-1', lambda o, n: _cont[o:o + n], 10 ** 7) == 'Treffen 06:30 am Brunnen. Schlüssel: grün-7. 🏔', "test vector"
    # 3. der Fallback-Weg (HMAC-Schlüsselstrom, wo kein AES ist) rechnet ebenso
    _h2 = bild_hide_image(_base, "nur HMAC", "k", force_hmac=True)
    assert bild_reveal_image(_h2, "k") == "nur HMAC", "hmac fallback"
    # 4. das Modul und die drei Zeilen stecken in der Seite, nichts Geheimes wird je protokolliert
    if STEGO_JS and STEGO_UI:                               # (ohne Zusatzdatei sind die grossen Literale leer)
        for _m in ("MWStego", "tz-row", "Message in a picture", "tz-sub-files", "tz-sub-msg"):
            assert _m.replace(" ", "") in (STEGO_JS + STEGO_UI).replace(" ", ""), "page missing: " + _m
        assert "console.log" not in STEGO_JS and "console.log" not in STEGO_UI, "no logging of secrets"
    return "«Botschaft im Bild»: Verstecken/Lesen (AES-256-GCM, LSB, schlüssel-abhängige Ordnung), 5 Sprachen, Python↔JS bitgleich"


SELFTEST_EXTRA.append(("Botschaft im Bild: hide/read, encryption, capacity, wrong key, Python↔JS vector (639zzzzc)", bild_selftest))
