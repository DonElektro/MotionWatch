#@ MoveEye – Teil 375: Gesichter verpixeln beim Teilen (nur die geteilte Kopie, das Original bleibt). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.14 (Wunsch Daniel): wenn ein Bild oder Video geteilt wird (Aufnahmen, Tagebuch – alles, was über share_jpg /
# share_video in 370 geht), werden Gesichter von selbst unkenntlich gemacht (verpixelt). Einstellung «Gesichter verpixeln
# beim Teilen» (share_blur_faces, Standard ein). Nur die geteilte Kopie wird verändert, das Original bleibt wie es ist.
# Erkennung, der Reihe nach:
#   1. Gesichter: Haar-Kaskade von OpenCV (haarcascade_frontalface_default.xml, wird mit opencv-python bzw. python3-opencv
#      mitgeliefert: cv2.data.haarcascades oder /usr/share/opencv4/haarcascades), dazu die Profil-Kaskade, wenn vorhanden.
#   2. Kein Gesicht gefunden oder keine Kaskade: Personen suchen (HOG-Personenerkennung von OpenCV, sonst das KI-Modell
#      SSD MobileNet von MoveEye) und den oberen Teil jeder Person (Kopf) verpixeln.
# Videos: Bild für Bild (Kopie im Ordner .cache, wird wiederverwendet, solange das Original gleich bleibt).
# ----------------------------------------------------------------------------
FACEBLUR = {"lock": threading.Lock(), "casc": None, "prof": None, "hog": None, "net": None, "tried": False,
            "how": "", "last": {}, "busy": set()}
FACE_CASCADE_DIRS = ["/usr/share/opencv4/haarcascades", "/usr/share/opencv/haarcascades", "/usr/local/share/opencv4/haarcascades",
                     "/usr/local/share/opencv/haarcascades"]


def _faceblur_init():
    """load the detectors once (whatever this OpenCV has)"""
    if FACEBLUR["tried"]:
        return
    FACEBLUR["tried"] = True
    dirs = []
    try:
        dirs.append(cv2.data.haarcascades)
    except AttributeError:
        pass
    dirs += FACE_CASCADE_DIRS + [os.path.join(DATA_DIR, "models"), os.path.dirname(os.path.abspath(__file__))]
    CC = getattr(cv2, "CascadeClassifier", None)
    if CC is not None:
        for nm, key in (("haarcascade_frontalface_default.xml", "casc"), ("haarcascade_frontalface_alt.xml", "casc"),
                        ("haarcascade_profileface.xml", "prof")):
            if FACEBLUR[key] is not None:
                continue
            for d in dirs:
                p = os.path.join(d or "", nm)
                if d and os.path.isfile(p):
                    try:
                        c = CC(p)
                        if not c.empty():
                            FACEBLUR[key] = c
                            break
                    except cv2.error:
                        pass
    if getattr(cv2, "HOGDescriptor", None) is not None:
        try:
            h = cv2.HOGDescriptor()
            h.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            FACEBLUR["hog"] = h
        except (cv2.error, AttributeError):
            pass
    try:
        pb, pbtxt = ai_model_paths()
        if pb:
            FACEBLUR["net"] = cv2.dnn.readNetFromTensorflow(pb, pbtxt)    # an own copy: the detection keeps its own net
    except Exception:
        pass
    FACEBLUR["how"] = ("faces" if FACEBLUR["casc"] is not None else "") + \
                      ("+persons" if (FACEBLUR["hog"] is not None or FACEBLUR["net"] is not None) else "")
    if not FACEBLUR["how"]:
        log_event("sys", "Blur faces when sharing: this OpenCV has no face or person detector - pictures are shared without blurring")


def faceblur_state():
    _faceblur_init()
    return {"on": bool(CFG.get("share_blur_faces", True)), "faces": FACEBLUR["casc"] is not None,
            "persons": FACEBLUR["hog"] is not None or FACEBLUR["net"] is not None, "last": FACEBLUR["last"]}


def _persons_find(img):
    """person boxes (x, y, w, h) - HOG, else the SSD model"""
    out = []
    h, w = img.shape[:2]
    if FACEBLUR["net"] is not None:
        try:
            blob = cv2.dnn.blobFromImage(img, size=(300, 300), swapRB=True, crop=False)
            FACEBLUR["net"].setInput(blob)
            det = FACEBLUR["net"].forward()
            for i in range(det.shape[2]):
                if int(det[0, 0, i, 1]) == 1 and float(det[0, 0, i, 2]) >= 0.35:
                    x1, y1, x2, y2 = (det[0, 0, i, 3:7] * np.array([w, h, w, h])).astype(int)
                    if x2 > x1 and y2 > y1:
                        out.append((max(0, x1), max(0, y1), x2 - x1, y2 - y1))
        except cv2.error:
            pass
    if not out and FACEBLUR["hog"] is not None:
        try:
            s = min(1.0, 800.0 / max(1, w))
            small = cv2.resize(img, (int(w * s), int(h * s))) if s < 1 else img
            rects, _ = FACEBLUR["hog"].detectMultiScale(small, winStride=(8, 8), padding=(8, 8), scale=1.05)
            out = [(int(x / s), int(y / s), int(rw / s), int(rh / s)) for (x, y, rw, rh) in rects]
        except cv2.error:
            pass
    return out


def faces_find(img):
    """[(x, y, w, h)] of the regions to make unrecognisable: faces, otherwise the heads of persons"""
    _faceblur_init()
    if img is None or img.size == 0:
        return []
    H, W = img.shape[:2]
    boxes = []
    with FACEBLUR["lock"]:
        if FACEBLUR["casc"] is not None:
            s = min(1.0, 960.0 / max(1, W))
            g = cv2.cvtColor(img if s >= 1 else cv2.resize(img, (int(W * s), int(H * s))), cv2.COLOR_BGR2GRAY)
            g = cv2.equalizeHist(g)
            mn = max(16, int(min(g.shape[:2]) * 0.03))
            for c, flip in ((FACEBLUR["casc"], False), (FACEBLUR["prof"], False), (FACEBLUR["prof"], True)):
                if c is None:
                    continue
                src = cv2.flip(g, 1) if flip else g
                try:
                    r = c.detectMultiScale(src, scaleFactor=1.1, minNeighbors=5, minSize=(mn, mn))
                except cv2.error:
                    continue
                for (x, y, w, h) in (r if len(r) else []):
                    if flip:
                        x = g.shape[1] - x - w
                    boxes.append((int(x / s), int(y / s), int(w / s), int(h / s)))
        if not boxes:
            for (x, y, w, h) in _persons_find(img):
                hh = max(8, int(h * 0.24)); hw = max(8, int(min(w, hh * 1.1)))       # the head: top quarter, middle
                boxes.append((x + (w - hw) // 2, y, hw, hh))
    return boxes


def faces_pixelate(img, boxes, pad=0.25):
    """the regions as coarse blocks (plus a soft blur, so no detail is left); returns the number of regions"""
    H, W = img.shape[:2]
    n = 0
    for (x, y, w, h) in boxes:
        px, py = int(w * pad), int(h * pad)
        x0, y0, x1, y1 = max(0, x - px), max(0, y - py), min(W, x + w + px), min(H, y + h + py)
        if x1 - x0 < 2 or y1 - y0 < 2:
            continue
        roi = img[y0:y1, x0:x1]
        bs = max(6, min(x1 - x0, y1 - y0) // 7)                  # about 7 blocks across a face
        sm = cv2.resize(roi, (max(1, (x1 - x0) // bs), max(1, (y1 - y0) // bs)), interpolation=cv2.INTER_AREA)
        big = cv2.resize(sm, (x1 - x0, y1 - y0), interpolation=cv2.INTER_NEAREST)
        k = max(3, (bs // 2) * 2 + 1)
        img[y0:y1, x0:x1] = cv2.GaussianBlur(big, (k, k), 0)
        n += 1
    return n


def faces_blur_image(img):
    """the picture (BGR, changed in place) with the faces pixelated; returns the number of regions"""
    boxes = faces_find(img)
    n = faces_pixelate(img, boxes) if boxes else 0
    FACEBLUR["last"] = {"t": time.time(), "n": n, "kind": "image"}
    return n


def faces_blur_jpg(data, quality=90):
    """JPEG bytes -> JPEG bytes with pixelated faces (the original data is not changed)"""
    if not CFG.get("share_blur_faces", True):
        return data
    try:
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return data
        if not faces_blur_image(img):
            return data
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return buf.tobytes() if ok else data
    except Exception as e:
        log_event("sys", f"Blur faces: {e}"[:160])
        return data


def faces_blur_video(src):
    """a copy of the video with pixelated faces (cache folder). Returns (path, error). The original stays untouched."""
    if not CFG.get("share_blur_faces", True) or src.endswith(".faces.mp4"):
        return src, ""
    _faceblur_init()
    if not FACEBLUR["how"]:
        return src, ""                                          # nothing to find faces with (logged once)
    cache = os.path.join(rec_dir(), ".cache"); os.makedirs(cache, exist_ok=True)
    dst = os.path.join(cache, os.path.splitext(os.path.basename(src))[0] + ".faces.mp4")
    try:
        if os.path.isfile(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            return dst, ""
    except OSError:
        pass
    with FACEBLUR["lock"]:
        if dst in FACEBLUR["busy"]:
            return None, "the video is being prepared - try again in a moment"
        FACEBLUR["busy"].add(dst)
    part = dst + ".part.mp4"
    cap = cv2.VideoCapture(src)
    proc = writer = None
    try:
        if not cap.isOpened():
            return None, "video cannot be read"
        fps = cap.get(cv2.CAP_PROP_FPS) or 10.0
        fps = fps if 1 <= fps <= 120 else 10.0
        recent, i, n_reg = [], 0, 0
        while True:
            ok, fr = cap.read()
            if not ok or fr is None:
                break
            if i % 2 == 0:                                       # every 2nd picture: look again; the boxes stay 3 pictures
                recent = ([faces_find(fr)] + recent)[:2]
            boxes = [b for bl in recent for b in bl]
            n_reg += faces_pixelate(fr, boxes) if boxes else 0
            if proc is None and writer is None:
                h, w = fr.shape[:2]
                if shutil.which("ffmpeg"):
                    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
                           "-framerate", f"{fps:.2f}", "-i", "-", "-an", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-map_metadata", "-1", "-movflags", "+faststart", part]
                    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                else:
                    for cc in ("avc1", "mp4v"):
                        writer = cv2.VideoWriter(part, cv2.VideoWriter_fourcc(*cc), fps, (w, h))
                        if writer.isOpened():
                            break
                        writer.release(); writer = None
                    if writer is None:
                        return None, "no video encoder (install ffmpeg)"
            if proc is not None:
                proc.stdin.write(fr.tobytes())
            else:
                writer.write(fr)
            i += 1
        if i == 0:
            return None, "video cannot be read"
        if proc is not None:
            proc.stdin.close()
            err = proc.stderr.read().decode(errors="replace").strip()
            if proc.wait(timeout=600) != 0:
                return None, (err.splitlines() or ["ffmpeg failed"])[-1][:200]
        else:
            writer.release(); writer = None
        os.replace(part, dst)
        FACEBLUR["last"] = {"t": time.time(), "n": n_reg, "kind": "video", "frames": i}
        log_event("rec", f"Shared video: faces made unrecognisable ({n_reg} regions in {i} pictures)")
        return dst, ""
    except (OSError, subprocess.SubprocessError, cv2.error, ValueError) as e:
        return None, str(e)[:200]
    finally:
        cap.release()
        if writer is not None:
            writer.release()
        if proc is not None and proc.poll() is None:
            proc.kill()
        try:
            os.remove(part)
        except OSError:
            pass
        with FACEBLUR["lock"]:
            FACEBLUR["busy"].discard(dst)


def faceblur_selftest():
    """pixelating works (a synthetic «face» loses its detail) and the original bytes stay the same"""
    img = np.zeros((240, 320, 3), np.uint8)
    for k in range(0, 80, 4):
        cv2.line(img, (100 + k, 60), (100 + k, 140), (255, 255, 255), 1)       # fine stripes = detail
    before = img[60:140, 100:180].std()
    n = faces_pixelate(img, [(100, 60, 80, 80)])
    after = img[70:130, 110:170].astype(np.float32)
    assert n == 1 and after.std() < before * 0.6, "pixelating must remove the detail"
    ok, buf = cv2.imencode(".jpg", np.full((60, 80, 3), 128, np.uint8))
    data = buf.tobytes(); copy = bytes(data)
    faces_blur_jpg(data)
    assert data == copy
    _faceblur_init()
    return "detector: " + (FACEBLUR["how"] or "none in this OpenCV")
