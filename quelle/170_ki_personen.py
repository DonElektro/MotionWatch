#@ Motion Watch – Teil 170: KI-Modell laden und herunterladen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# AI person detector (SSD MobileNet V2, COCO class 1 = person)
# ----------------------------------------------------------------------------
AI_MODEL = {"busy": False, "msg": "", "pct": 0}
AI_TGZ_URLS = ("https://storage.googleapis.com/download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz",
               "https://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz")
AI_PBTXT_URL = "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/ssd_mobilenet_v2_coco_2018_03_29.pbtxt"


def ai_model_dirs():
    return [os.path.dirname(os.path.abspath(__file__)), os.path.join(DATA_DIR, "models")]


def ai_model_paths():
    """(pb, pbtxt) of the first folder that has both files - next to the program or in the data folder."""
    for d in ai_model_dirs():
        pb, pbtxt = os.path.join(d, AIDetector.PB), os.path.join(d, AIDetector.PBTXT)
        if os.path.isfile(pb) and os.path.isfile(pbtxt):
            return pb, pbtxt
    return None, None


def _short_net_err(e):
    """A short, readable reason for a failed download."""
    r = getattr(e, "reason", None) or e
    t = str(r)
    if "CERTIFICATE_VERIFY_FAILED" in t:
        return "certificate not valid (check the clock of the Pi)" if "expired" in t or "not yet valid" in t else "certificate not valid"
    if isinstance(r, TimeoutError) or "timed out" in t:
        return "no answer (internet slow or missing)"
    if "Name or service not known" in t or "getaddrinfo" in t or "Temporary failure in name resolution" in t:
        return "no internet (name not found)"
    if "Connection refused" in t or "Network is unreachable" in t:
        return "no internet connection"
    if getattr(e, "code", None):
        return f"server answered {e.code}"
    return t[:80]


def ai_model_download():
    """Fetch the AI model in the background (about 70 MB), check that OpenCV can read it, switch the AI on."""
    if AI_MODEL["busy"]:
        return False, "already running"
    if DEMO["on"]:
        return False, "not in the demo"
    AI_MODEL.update(busy=True, msg="downloading", pct=0)

    def run():
        import tarfile
        dst = os.path.join(DATA_DIR, "models"); os.makedirs(dst, exist_ok=True)
        tgz = os.path.join(dst, "model.tar.gz.part"); pb_tmp = os.path.join(dst, AIDetector.PB + ".part"); tx_tmp = os.path.join(dst, AIDetector.PBTXT + ".part")
        try:
            errs = []
            for url in AI_TGZ_URLS:                               # first address that works (certificates are always checked)
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "MotionWatch/" + APP_VERSION})
                    with urllib.request.urlopen(req, timeout=60) as r, open(tgz, "wb") as f:
                        total = int(r.headers.get("Content-Length") or 0); got = 0
                        while True:
                            b = r.read(256 * 1024)
                            if not b:
                                break
                            f.write(b); got += len(b)
                            AI_MODEL["pct"] = int(got * 90 / total) if total else min(89, got // (800 * 1024))
                    errs = []; break
                except Exception as e:
                    errs.append(_short_net_err(e))
            if errs:
                raise RuntimeError(errs[0])
            with tarfile.open(tgz, "r:gz") as t:                 # only the one file, written by us (no paths from the archive)
                m = next((x for x in t.getmembers() if x.isfile() and x.name.endswith("/" + AIDetector.PB)), None)
                if m is None:
                    raise RuntimeError("model file missing in the archive")
                src = t.extractfile(m)
                with open(pb_tmp, "wb") as f:
                    shutil.copyfileobj(src, f)
            req = urllib.request.Request(AI_PBTXT_URL, headers={"User-Agent": "MotionWatch/" + APP_VERSION})
            with urllib.request.urlopen(req, timeout=60) as r:
                txt = r.read(5 * 1024 * 1024)
            if b"node" not in txt[:4096]:
                raise RuntimeError("the description file is not valid")
            with open(tx_tmp, "wb") as f:
                f.write(txt)
            AI_MODEL["pct"] = 95
            try:
                cv2.dnn.readNetFromTensorflow(pb_tmp, tx_tmp)    # raises if the files are damaged
            except cv2.error:
                raise RuntimeError("the model files are damaged - try again")
            os.replace(pb_tmp, os.path.join(dst, AIDetector.PB)); os.replace(tx_tmp, os.path.join(dst, AIDetector.PBTXT))
            CFG["ai_enabled"] = True; save_settings()
            w = WATCH_REF["w"]
            if w is not None:
                w.ai = AIDetector()
            AI_MODEL.update(msg="ready", pct=100)
            log_event("ai", "AI model downloaded and switched on")
        except Exception as e:
            AI_MODEL.update(msg=f"failed: {tr(str(e))}"[:120], pct=0)
            log_event("ai", f"AI model download failed: {e}"[:200])
        finally:
            AI_MODEL["busy"] = False
            for p_ in (tgz, pb_tmp, tx_tmp):
                try:
                    os.remove(p_)
                except OSError:
                    pass
    threading.Thread(target=run, daemon=True, name="ai-model").start()
    return True, ""


