#@ MoveEye – Teil 639zzf: Bildgrösse aus dem Dateikopf (vor cv2.imdecode bei hochgeladenen Bildern – Schutz vor Pixelbomben). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 3.68.1 (Härtung): a tiny file can declare a huge picture (e.g. 65 000 × 65 000 px in a 300-byte PNG). cv2.imdecode
# allocates the full picture before anything else can check it. Every place that decodes pictures from users or from
# the network therefore reads width × height from the file head first and refuses the file without decoding when
#   * the head cannot be read (unknown or damaged format), or
#   * width × height > IMG_MP_MAX (60 MP) or one side > IMG_SIDE_MAX, or a side is 0.
# Formats: JPEG (first SOF marker), PNG (IHDR), WebP (VP8 / VP8L / VP8X), GIF, BMP, TIFF (first IFD).
# Used by: the upload of «🔍 Untersuchen» (639zze), the previews of the Datentausch (639zzc, tausch_img_dims) and the
# AI helper on the PC (180, /helper/detect).
# ----------------------------------------------------------------------------
import io as _io_bk
import struct as _struct_bk

IMG_MP_MAX = 60_000_000
IMG_SIDE_MAX = 20_000


def img_head(src):
    """(format, width, height) from the head of a picture - bytes or an open binary file - or None"""
    f = _io_bk.BytesIO(src) if isinstance(src, (bytes, bytearray, memoryview)) else src
    try:
        f.seek(0)
        h = f.read(32)
        if h.startswith(b"\x89PNG\r\n\x1a\n"):
            if h[12:16] != b"IHDR" or len(h) < 24:
                return None
            w, hh = _struct_bk.unpack(">II", h[16:24])
            return "png", w, hh
        if h[:6] in (b"GIF87a", b"GIF89a") and len(h) >= 10:
            w, hh = _struct_bk.unpack("<HH", h[6:10])
            return "gif", w, hh
        if h[:2] == b"BM" and len(h) >= 26:
            w, hh = _struct_bk.unpack("<ii", h[18:26])
            return "bmp", abs(w), abs(hh)
        if h[:4] == b"RIFF" and h[8:12] == b"WEBP":
            c = h[12:32] + f.read(10)
            if c[:4] == b"VP8 " and len(c) >= 18:
                if c[11:14] != b"\x9d\x01\x2a":                  # start code of a VP8 key frame
                    return None
                w, hh = _struct_bk.unpack("<HH", c[14:18])
                return "webp", w & 0x3fff, hh & 0x3fff
            if c[:4] == b"VP8L" and len(c) >= 13:
                if c[8] != 0x2f:
                    return None
                b = int.from_bytes(c[9:13], "little")
                return "webp", (b & 0x3fff) + 1, ((b >> 14) & 0x3fff) + 1
            if c[:4] == b"VP8X" and len(c) >= 18:
                return "webp", 1 + int.from_bytes(c[12:15], "little"), 1 + int.from_bytes(c[15:18], "little")
            return None
        if h[:4] in (b"II*\x00", b"MM\x00*"):
            e = "<" if h[:2] == b"II" else ">"
            f.seek(_struct_bk.unpack(e + "I", h[4:8])[0])
            n = _struct_bk.unpack(e + "H", f.read(2))[0]
            w = hh = None
            for _i in range(min(n, 500)):
                tag, typ, _cnt = _struct_bk.unpack(e + "HHI", f.read(8))
                v = f.read(4)
                val = _struct_bk.unpack(e + "H", v[:2])[0] if typ == 3 else _struct_bk.unpack(e + "I", v)[0] if typ == 4 else None
                if tag == 256:
                    w = val
                elif tag == 257:
                    hh = val
            return ("tiff", w, hh) if w is not None and hh is not None else None
        if h[:2] == b"\xff\xd8":
            f.seek(2)
            for _i in range(1000):
                m = f.read(2)
                while m[:1] == b"\xff" and m[1:2] == b"\xff":     # fill bytes
                    m = m[1:] + f.read(1)
                if len(m) < 2 or m[0] != 0xFF:
                    return None
                mk = m[1]
                if mk == 0x01 or 0xD0 <= mk <= 0xD7:               # markers without length
                    continue
                if mk in (0xD8, 0xD9, 0xDA):                       # second SOI / end / picture data before a SOF: broken
                    return None
                ln = _struct_bk.unpack(">H", f.read(2))[0]
                if ln < 2:
                    return None
                if 0xC0 <= mk <= 0xCF and mk not in (0xC4, 0xC8, 0xCC):
                    d = f.read(5)
                    hh, w = _struct_bk.unpack(">HH", d[1:5])
                    return "jpeg", w, hh
                f.seek(ln - 2, 1)
            return None
    except (OSError, _struct_bk.error, ValueError, IndexError, TypeError):
        return None
    return None


def img_head_ok(src, formats=None):
    """(True, (w, h)) when the picture may be decoded, else (False, reason) - nothing is decoded here"""
    r = img_head(src)
    if r is None:
        return False, "head unreadable"
    fmt, w, hh = r
    if formats and fmt not in formats:
        return False, "format " + fmt
    if w <= 0 or hh <= 0:
        return False, "empty"
    if w > IMG_SIDE_MAX or hh > IMG_SIDE_MAX or w * hh > IMG_MP_MAX:
        return False, "too big %dx%d" % (w, hh)
    return True, (w, hh)


def img_decode_checked(data, flag=None, formats=None):
    """cv2.imdecode only after the head check; None when refused or not readable"""
    if not img_head_ok(data, formats)[0]:
        return None
    try:
        return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR if flag is None else flag)
    except (cv2.error, ValueError, MemoryError):
        return None


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def _bk_bomb(fmt, w, hh):
    """a few bytes that only declare w × h (no picture data)"""
    if fmt == "png":
        return b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR" + _struct_bk.pack(">II", w, hh) + b"\x08\x02\x00\x00\x00" + b"\x00" * 4
    if fmt == "jpeg":
        return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\xff\xc0\x00\x11\x08" + _struct_bk.pack(">HH", hh, w) + b"\x03" + b"\x00" * 9
    if fmt == "vp8x":
        return b"RIFF\x00\x00\x00\x00WEBPVP8X\x0a\x00\x00\x00\x00\x00\x00\x00" + (w - 1).to_bytes(3, "little") + (hh - 1).to_bytes(3, "little")
    if fmt == "vp8l":
        return b"RIFF\x00\x00\x00\x00WEBPVP8L\x05\x00\x00\x00\x2f" + ((w - 1) | ((hh - 1) << 14)).to_bytes(4, "little")
    if fmt == "vp8":
        return b"RIFF\x00\x00\x00\x00WEBPVP8 \x0a\x00\x00\x00\x00\x00\x00\x9d\x01\x2a" + _struct_bk.pack("<HH", w, hh)
    raise ValueError(fmt)


def bk_selftest():
    for fmt in ("png", "jpeg"):
        assert img_head(_bk_bomb(fmt, 65000, 65000))[1:] == (65000, 65000), fmt
        assert not img_head_ok(_bk_bomb(fmt, 65000, 65000))[0] and not img_head_ok(_bk_bomb(fmt, 30000, 100))[0], fmt
        assert img_head_ok(_bk_bomb(fmt, 4000, 3000)) == (True, (4000, 3000)), fmt
    assert img_head(_bk_bomb("vp8x", 16384, 16384))[1:] == (16384, 16384) and not img_head_ok(_bk_bomb("vp8x", 16384, 16384))[0]
    assert img_head(_bk_bomb("vp8l", 16384, 16000))[1:] == (16384, 16000) and not img_head_ok(_bk_bomb("vp8l", 16384, 16000))[0]
    assert img_head(_bk_bomb("vp8", 16383, 16383))[1:] == (16383, 16383) and not img_head_ok(_bk_bomb("vp8", 16383, 16383))[0]
    seen, imd = [], cv2.imdecode                              # refused WITHOUT decoding: cv2.imdecode is never called
    try:
        cv2.imdecode = lambda *a: seen.append(1)
        for b in (_bk_bomb("png", 65000, 65000), _bk_bomb("jpeg", 9000, 9000), _bk_bomb("vp8x", 16384, 16384), b"no picture"):
            assert img_decode_checked(b) is None
    finally:
        cv2.imdecode = imd
    assert not seen, "decoded although refused"
    for fmt, ext in (("jpeg", ".jpg"), ("png", ".png"), ("webp", ".webp")):
        ok, buf = cv2.imencode(ext, np.full((30, 40, 3), 128, np.uint8))
        if ok:                                                   # a real picture: same size as the decoder says
            assert img_head(buf.tobytes()) == (fmt, 40, 30), (fmt, img_head(buf.tobytes()))
            im = img_decode_checked(buf.tobytes(), formats=("jpeg", "png", "webp"))
            assert im is not None and im.shape[:2] == (30, 40), fmt
    assert img_head(b"\xff\xd8\xff\xda\x00\x02") is None and img_head(b"\x89PNG\r\n\x1a\n") is None and img_head(b"RIFF\x00\x00\x00\x00WEBPVP8 ") is None
    assert not img_head_ok(_bk_bomb("png", 0, 10))[0] and img_head_ok(_bk_bomb("png", 100, 100), formats=("jpeg",))[0] is False
    return "JPEG SOF / PNG IHDR / WebP VP8 VP8L VP8X read from the head; bombs (> 60 MP, > %d px a side, unreadable) refused without decoding" % IMG_SIDE_MAX


SELFTEST_EXTRA.append(("Picture size from the file head (639zzf)", bk_selftest))
