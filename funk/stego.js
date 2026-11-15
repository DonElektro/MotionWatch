/* MoveEye – «Botschaft im Bild» (Steganographie) – ein eigenständiges Modul, das im Browser (WebCrypto,
   Canvas) und in node (crypto.subtle, zlib) gleich rechnet. Es wird im «Digitalen Rucksack» eingebaut und
   läuft auch offline auf der Seite «Handy-Funkgerät». Für den Besitzer von MoveEye gemacht.

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
