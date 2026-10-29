#@ Motion Watch – Teil 370: Rückmeldung, Teilen, Abschreckung, Gegensprechen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Feedback to the developer: from the page / the window, anonymous in both directions (no address of the sender, the
#   destination is not shown). Sent by the Pi; without internet it waits and is sent later.
# ----------------------------------------------------------------------------
_FB_DEST = "aHR0cHM6Ly9udGZ5LW1lLmNvbS9tdy1mYi0xYzE3ZTFkMWViNWZhMmFhZTQ5Nw=="
_FB_DEST2 = "aHR0cHM6Ly9udGZ5LnNoL213LWZiLTFjMTdlMWQxZWI1ZmEyYWFlNDk3"      # 2.98.33: the same topic on a second server - sent to both, one is enough
FEEDBACK = {"sent": [], "lock": threading.Lock(), "err": {}, "log_t": {}, "ok_t": 0.0, "test_t": 0.0}


def _fb_file():
    return os.path.join(DATA_DIR, "feedback_outbox.json")


FB_KINDS = {"bug": "Fehler", "idea": "Wunsch", "praise": "Lob", "question": "Frage", "other": "Feedback"}   # 2.98.33: + «Frage»
FB_SHOT_MAX = 350 * 1024               # 2.98.33: a screenshot as ntfy attachment (the ntfy servers allow several MB; small = quick on mobile)


def feedback_send(kind, text, contact="", diag=False, stars=0, page="", shot=None, src="web"):
    """2.98.33 (584): + satisfaction 1-5 stars, the page / place it was written on, the version (always) and an optional
    screenshot (JPEG bytes, faces pixelated by feedback_shot). Anonymous as before: no address, no name unless written."""
    text = str(text or "").strip()[:3000]
    if len(text) < 3:
        return False, "please write a few words"
    now = time.time()
    FEEDBACK["sent"] = [x for x in FEEDBACK["sent"] if now - x < 3600]
    if len(FEEDBACK["sent"]) >= 5:
        return False, "at most 5 messages per hour"
    kind = kind if kind in FB_KINDS else "other"
    try:
        stars = max(0, min(5, int(stars or 0)))
    except (TypeError, ValueError):
        stars = 0
    page = re.sub(r"[^\w ./#:+\-]", "", str(page or ""))[:40]
    src = src if src in ("web", "window", "simulator") else "web"
    body_ = text + (("\n\nKontakt: " + str(contact)[:120]) if contact else "")
    if stars:
        body_ += "\n\nZufriedenheit: " + "★" * stars + "☆" * (5 - stars) + f" ({stars}/5)"
    where = {"web": "Web", "window": "Fenster", "simulator": "3D-Simulator"}[src]
    body_ += f"\n\n— MoveEye {APP_VERSION} · {where}" + (f" · Seite: {page}" if page else "")
    if diag:
        imp = [e for e in STATE["events"] if e.get("imp")][:8]
        body_ += (f"\n\n--- Technik ---\nVersion {APP_VERSION} · Python {sys.version.split()[0]} · {platform_model()} · "
                  f"Sprache {CFG['lang']} · Laufzeit {int((now - START) / 3600)} h\n" + "\n".join(f"{e.get('t', '')} {e.get('text', '')[:140]}" for e in imp))
    msg = {"kind": kind, "body": body_, "t": datetime.now().isoformat(timespec="seconds"), "stars": stars}
    if shot and len(shot) <= FB_SHOT_MAX:
        try:
            os.makedirs(_fb_shot_dir(), exist_ok=True)
            msg["img"] = uuid.uuid4().hex[:12]
            with open(os.path.join(_fb_shot_dir(), msg["img"] + ".jpg"), "wb") as f:
                f.write(shot)
        except OSError:
            msg.pop("img", None)
    FEEDBACK["sent"].append(now)
    with FEEDBACK["lock"]:
        box = _fb_load(); box.append(msg); _fb_save(box[-20:]); _fb_shots_tidy(box[-20:])
    threading.Thread(target=feedback_flush, daemon=True).start()
    log_event("web", "Feedback written - it is sent to the developer (also later, when there is internet)")
    return True, ""


def _fb_shot_dir():
    return os.path.join(DATA_DIR, "feedback_shots")


def _fb_shots_tidy(box):
    """screenshots of messages that are no longer waiting are deleted"""
    keep = {m.get("img") for m in box if m.get("img")}
    try:
        for fn in os.listdir(_fb_shot_dir()):
            if fn[:-4] not in keep:
                os.remove(os.path.join(_fb_shot_dir(), fn))
    except OSError:
        pass


def _fb_load():
    try:
        with open(_fb_file()) as f:
            return [x for x in json.load(f) if isinstance(x, dict)]
    except (OSError, ValueError):
        return []


def _fb_save(box):
    try:
        with open(_fb_file(), "w") as f:
            json.dump(box, f)
    except OSError:
        pass


def _fb_urls():
    import base64
    return [base64.b64decode(x).decode() for x in (_FB_DEST, _FB_DEST2)]


def _fb_host(u):
    return u.split("/")[2] if u.count("/") >= 2 else u


def _fb_req(url, data, headers, method):
    """one request to one server: True / False; the reason of a failure is kept (no topic, no secret) and logged once per hour"""
    host = _fb_host(url)
    try:
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=30 if method == "PUT" else 15) as r:
            if r.status < 300:
                FEEDBACK["err"].pop(host, None); FEEDBACK["ok_t"] = time.time()
                return True
            why = f"HTTP {r.status} {r.reason}"
    except urllib.error.HTTPError as e:
        why = f"HTTP {e.code} {e.reason}"
    except Exception as e:
        why = (type(e).__name__ + ": " + str(getattr(e, "reason", "") or e))[:120]
    FEEDBACK["err"][host] = {"why": why, "t": time.time()}
    if time.time() - FEEDBACK["log_t"].get(host, 0) > 3600:
        FEEDBACK["log_t"][host] = time.time()
        log_event("web", f"Feedback: {host} refused ({why}) - tried again later")
    return False


def feedback_flush():
    """Send what is waiting. Called after writing and every 10 minutes. 2.98.33: to both servers (ntfy-me.com and
    ntfy.sh, same topic); a message counts as sent when one server took it; the picture goes to the same server(s)."""
    with FEEDBACK["lock"]:
        box = _fb_load()
        if not box:
            return
        urls = _fb_urls()
        left = []
        for m in box:
            title = "MoveEye – " + FB_KINDS.get(m.get("kind"), "Feedback") + ((" " + "★" * int(m["stars"])) if m.get("stars") else "")
            tags = {"bug": "bug", "idea": "bulb", "praise": "star", "question": "question"}.get(m.get("kind"), "speech_balloon")
            if not m.get("text_sent"):
                oks = [i for i, u in enumerate(urls) if _fb_req(u, m["body"].encode(), {"Title": _hdr(title), "Tags": tags}, "POST")]
                if not oks:
                    left.append(m); continue
                m["text_sent"] = True; m["dests"] = oks
            if m.get("img"):                             # 2.98.33: the screenshot as a second message with the picture attached
                try:
                    with open(os.path.join(_fb_shot_dir(), m["img"] + ".jpg"), "rb") as f:
                        jpg = f.read()
                except OSError:
                    jpg = b""
                if jpg:
                    h = {"Title": _hdr(title + " · Bildschirmfoto"), "Tags": "camera", "Filename": "moveeye_rueckmeldung.jpg",
                         "Message": _hdr("Bildschirmfoto zur Rückmeldung von " + str(m.get("t", ""))[:16].replace("T", " ")), "Content-Type": "image/jpeg"}
                    if not [i for i in (m.get("dests") or [0, 1]) if i < len(urls) and _fb_req(urls[i], jpg, h, "PUT")]:
                        left.append(m); continue
        _fb_save(left); _fb_shots_tidy(left)
        if len(left) < len(box):
            log_event("web", f"Feedback sent ({len(box) - len(left)})")


def feedback_status():
    """for the dialog: how many messages wait, the last refusal per server (host only)"""
    box = _fb_load()
    errs = [{"host": h, "why": e["why"], "t": e["t"]} for h, e in FEEDBACK["err"].items()]
    return {"waiting": len(box), "errors": errs, "ok_t": FEEDBACK["ok_t"]}


def feedback_test():
    """«Send a test feedback» (developer): one short message to each server, the result per server; not kept"""
    if time.time() - FEEDBACK["test_t"] < 20:
        return False, "wait a moment", []
    FEEDBACK["test_t"] = time.time()
    res = []
    for u in _fb_urls():
        ok = _fb_req(u, f"Test-Feedback von MoveEye {APP_VERSION} ({datetime.now().strftime('%d.%m.%Y %H:%M')})".encode(),
                     {"Title": _hdr("MoveEye – Test-Feedback"), "Tags": "test_tube"}, "POST")
        res.append({"host": _fb_host(u), "ok": ok, "why": "" if ok else FEEDBACK["err"].get(_fb_host(u), {}).get("why", "")})
    return any(r["ok"] for r in res), "", res


def platform_model():
    try:
        with open("/proc/device-tree/model") as f:
            return f.read().strip("\x00 \n")[:60]
    except OSError:
        import platform
        return platform.machine()


def feedback_loop():
    while True:
        time.sleep(600)
        try:
            feedback_flush()
        except Exception:
            pass

# ----------------------------------------------------------------------------
# Sharing with a small logo: pictures (animal diary, snapshots, night report) and videos (recordings, timelapse) get a
#   discreet strip at the bottom right: app icon + "MoveEye" + what / when. Every shared fox picture is a little advert.
# ----------------------------------------------------------------------------
_FONT_CACHE = {}


def _font(size, bold=True):
    key = (size, bold)
    if key not in _FONT_CACHE:
        from PIL import ImageFont
        f = None
        for n in (("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), "LiberationSans-Bold.ttf"):
            for d in ("/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation", "/usr/share/fonts/TTF"):
                try:
                    f = ImageFont.truetype(os.path.join(d, n), size); break
                except OSError:
                    continue
            if f:
                break
        _FONT_CACHE[key] = f or ImageFont.load_default()
    return _FONT_CACHE[key]


def brand_strip(width, caption=""):
    """RGBA picture of the logo strip for a picture / video `width` pixels wide (PIL), or None without PIL."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    hgt = max(26, int(width * 0.045)); pad = max(5, hgt // 5)
    f1, f2 = _font(int(hgt * 0.42)), _font(int(hgt * 0.32), bold=False)
    title = "MoveEye"; cap = str(caption or "")[:60]
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tw = max(tmp.textlength(title, font=f1), tmp.textlength(cap, font=f2) if cap else 0)
    icon = int(hgt - 2 * pad + pad)
    w_ = int(icon + 3 * pad + tw); h_ = hgt
    im = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w_ - 1, h_ - 1), radius=h_ // 3, fill=(10, 14, 20, 165))
    ic = cv2.imdecode(np.frombuffer(app_icon_png(128), np.uint8), cv2.IMREAD_COLOR)
    ic = Image.fromarray(cv2.cvtColor(ic, cv2.COLOR_BGR2RGB)).resize((icon - pad // 2, icon - pad // 2))
    mask = Image.new("L", ic.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, ic.size[0] - 1, ic.size[1] - 1), radius=ic.size[0] // 4, fill=255)
    im.paste(ic, (pad, (h_ - ic.size[1]) // 2), mask)
    x = pad * 2 + ic.size[0]
    if cap:
        d.text((x, int(h_ * 0.08)), title, font=f1, fill=(255, 255, 255, 255))
        d.text((x, int(h_ * 0.55)), cap, font=f2, fill=(255, 190, 140, 255))
    else:
        d.text((x, (h_ - f1.size) // 2 - 1), title, font=f1, fill=(255, 255, 255, 255))
    return im


def brand_image(img_bgr, caption=""):
    """Picture (BGR) with the logo strip at the bottom right. Without PIL: a plain text line (cv2)."""
    h, w = img_bgr.shape[:2]
    strip = brand_strip(w, caption)
    out = img_bgr.copy()
    m = max(6, w // 80)
    if strip is None:
        txt = "MoveEye" + ((" - " + caption.encode("ascii", "replace").decode()) if caption else "")
        cv2.putText(out, txt, (m, h - m), cv2.FONT_HERSHEY_SIMPLEX, max(0.4, w / 1600), (255, 255, 255), max(1, w // 800), cv2.LINE_AA)
        return out
    a = np.array(strip); sh, sw = a.shape[:2]
    if sw + 2 * m > w or sh + 2 * m > h:
        return out
    y0, x0 = h - sh - m, w - sw - m
    rgb = cv2.cvtColor(a[:, :, :3], cv2.COLOR_RGB2BGR).astype(np.float32); al = a[:, :, 3:4].astype(np.float32) / 255.0
    roi = out[y0:y0 + sh, x0:x0 + sw].astype(np.float32)
    out[y0:y0 + sh, x0:x0 + sw] = (rgb * al + roi * (1 - al)).astype(np.uint8)
    return out


def brand_jpg(data, caption="", quality=88):
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return data
    ok, buf = cv2.imencode(".jpg", brand_image(img, caption), [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes() if ok else data


def jpg_without_exif(data):
    """The JPEG without its EXIF blocks (APP1) - that is where the GPS position is; the picture itself stays untouched."""
    if data[:2] != b"\xff\xd8":
        return data
    out, i, n = [data[:2]], 2, len(data)
    while i + 4 <= n and data[i] == 0xFF:
        mk = data[i + 1]
        if mk in (0xD9, 0xDA):                                # end / start of the picture data: the rest as it is
            break
        ln = int.from_bytes(data[i + 2:i + 4], "big")
        if ln < 2 or i + 2 + ln > n:
            return data
        if not (mk == 0xE1 and data[i + 4:i + 10] in (b"Exif\0\0", b"Exif\0\xff")):
            out.append(data[i:i + 2 + ln])
        i += 2 + ln
    out.append(data[i:])
    return b"".join(out)


def share_jpg(data, caption=""):
    """A picture as it leaves the Pi when shared: logo (if on), location only when wanted."""
    g = exif_gps_bytes(data) if CFG["share_gps"] else None
    data = faces_blur_jpg(data)                               # 2.98.14: faces pixelated (375), only in the shared copy
    data = brand_jpg(data, caption) if CFG["share_logo"] else data
    data = jpg_without_exif(data)
    if g:
        data = data[:2] + exif_gps(g[0], g[1]) + data[2:]
    return data


def exif_gps_bytes(data):
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(suffix=".jpg")
        with os.fdopen(fd, "wb") as f:
            f.write(data[:65536])
        return exif_read_gps(tmp)
    except OSError:
        return None
    finally:
        if tmp:
            try:
                os.remove(tmp)
            except OSError:
                pass


def share_video(src, caption=""):
    """A video as it leaves the Pi when shared: logo (if on); the location removed unless wanted. (path, error)"""
    if CFG.get("share_blur_faces", True) and not src.endswith(".faces.mp4"):
        src, err = faces_blur_video(src)                      # 2.98.14: a copy with pixelated faces (375)
        if not src:
            return None, err
    if CFG["share_logo"]:
        return brand_video(src, caption)
    if CFG["share_gps"] or not shutil.which("ffmpeg"):
        return src, ""                                        # without ffmpeg no location was written into it either
    cache = os.path.join(rec_dir(), ".cache"); os.makedirs(cache, exist_ok=True)
    dst = os.path.join(cache, os.path.splitext(os.path.basename(src))[0] + ".nogps.mp4")
    try:
        if os.path.isfile(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            return dst, ""
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-map", "0", "-c", "copy", "-map_metadata", "-1",
                            "-movflags", "+faststart", dst + ".part.mp4"], capture_output=True, timeout=600)
        if r.returncode != 0:
            return None, (r.stderr.decode(errors="replace").strip().splitlines() or ["ffmpeg failed"])[-1][:200]
        os.replace(dst + ".part.mp4", dst)
        return dst, ""
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)[:200]
    finally:
        try:
            os.remove(dst + ".part.mp4")
        except OSError:
            pass


def brand_video(src, caption=""):
    """Copy of a video with the logo strip (ffmpeg overlay), kept in the cache folder. Returns (path, error)."""
    if not shutil.which("ffmpeg"):
        return None, "ffmpeg is missing (sudo apt install ffmpeg)"
    cache = os.path.join(rec_dir(), ".cache"); os.makedirs(cache, exist_ok=True)
    dst = os.path.join(cache, os.path.splitext(os.path.basename(src))[0] + (".share.gps.mp4" if CFG["share_gps"] else ".share.mp4"))
    try:
        if os.path.isfile(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            return dst, ""
    except OSError:
        pass
    cap = cv2.VideoCapture(src); w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280); cap.release()
    strip = brand_strip(w, caption)
    if strip is None:
        CFG_logo = CFG["share_logo"]; CFG["share_logo"] = False
        try:
            return share_video(src, caption)
        finally:
            CFG["share_logo"] = CFG_logo
    png = dst + ".logo.png"; strip.save(png)
    m = max(6, w // 80)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-i", png, "-filter_complex", f"overlay=W-w-{m}:H-h-{m}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-c:a", "copy"]
    cmd += [] if CFG["share_gps"] else ["-map_metadata", "-1"]
    cmd += ["-movflags", "+faststart", dst + ".part.mp4"]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=600)
        if r.returncode != 0:
            return None, (r.stderr.decode(errors="replace").strip().splitlines() or ["ffmpeg failed"])[-1][:200]
        os.replace(dst + ".part.mp4", dst)
        return dst, ""
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)[:200]
    finally:
        for f in (png, dst + ".part.mp4"):
            try:
                os.remove(f)
            except OSError:
                pass

# ----------------------------------------------------------------------------
# Targeted deterrence: what is seen decides the reaction - person, small animal (cat, dog, bird), big animal (bear, cow,
#   horse ...) or a warm body (thermal camera): own sound on the loudspeaker and / or the white light flashing.
#   Only when armed (or always, e.g. to keep animals out of the garden), with a pause between two reactions.
# ----------------------------------------------------------------------------
DETER_GROUPS = (("person", {"person"}), ("big", {"bear", "horse", "cow", "sheep", "elephant", "zebra", "giraffe"}),
                ("small", {"cat", "dog", "bird", "animal"}), ("warm", {"warm"}))     # "animal": own MoveEye model (part 195), size unknown
DETER_ACTS = ("off", "sound", "light", "both")


class Deterrence:
    def __init__(self):
        self.seen = {}; self.last = 0.0; self.last_group = ""

    def check(self, present, t0):
        if not (is_armed() or CFG["deter_always"]):
            self.seen.clear(); return
        hit = None
        for g, labels in DETER_GROUPS:                    # the first group that matches wins (person before animals)
            if present & labels and CFG[f"deter_{g}_act"] != "off":
                hit = g; break
        if hit is None:
            return
        first = self.seen.get(hit)
        if first is None or t0 - first > 4.0:
            self.seen[hit] = t0; return                   # must still be there a moment later (no reaction to one wrong picture)
        if t0 - first < 1.0 or t0 - self.last < float(CFG["deter_pause"]):
            return
        self.react(hit, sorted(present & dict(DETER_GROUPS)[hit])[0] if present & dict(DETER_GROUPS)[hit] else hit)
        self.last = t0; self.seen.pop(hit, None)

    def react(self, group, label):
        act = CFG[f"deter_{group}_act"]; secs = float(CFG["deter_seconds"]); done = []
        if act in ("sound", "both") and out_selected() and not SOUND["playing"] and TALK["proc"] is None:
            ok, _e = sound_play(CFG[f"deter_{group}_sound"], secs, None, reason="deterrence " + label)
            if ok:
                done.append("sound")
        if act in ("light", "both") and CFG["light_white_out"]:
            LIGHTS["strobe_until"] = time.time() + secs; done.append("light")
        log_event("alarm" if group != "small" else "sys", f"Deterrence: {label} -> {' + '.join(done) or 'nothing (no loudspeaker / light connected)'}")
        STATE["deter_last"] = datetime.now().strftime("%H:%M") + " " + tr(label) + " → " + (" + ".join(tr(x) for x in done) or "–")


DETER = Deterrence()

# ---- talking from the phone through the loudspeaker (push to talk) ------------------------------
#   The page records the phone microphone (only allowed on a secure https page), sends 16 kHz / 16 bit pieces every 0.2 s,
#   they are played with aplay. 1.5 s without a piece ends it. While somebody talks, the noise alarm does not listen.
TALK = {"proc": None, "last": 0.0, "who": "", "dev": ""}
_TALK_LOCK = threading.Lock()


def talk_chunk(data, who=""):
    dev = CFG["audio_out"]
    if not out_selected():
        return False, "no loudspeaker selected"
    if not dev.startswith("bt:") and not shutil.which("aplay"):
        return False, "aplay is missing (sudo apt install alsa-utils)"
    if not data or len(data) > 96000:
        return False, "invalid sound data"
    a = np.frombuffer(data[:len(data) // 2 * 2], dtype="<i2").astype(np.float32) * (10.0 ** (float(CFG["talk_gain"]) / 20.0))
    pcm = np.clip(a, -32768, 32767).astype("<i2").tobytes()
    now = time.time()
    with _TALK_LOCK:
        p = TALK["proc"]
        if p is None or p.poll() is not None or TALK["dev"] != dev:
            if SOUND["playing"]:
                sound_stop()                             # the voice wins over a siren that is still playing
            cmd, err = out_cmd(AUDIO_RATE, connect=False)
            if cmd is None:
                return False, err
            try:
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except OSError as e:
                return False, str(e)[:200]
            TALK.update(proc=p, who=who, dev=dev, last=now)
            try:
                p.stdin.write(bytes(int(AUDIO_RATE * 0.15) * 2))     # a little head start: small network gaps do not stutter
            except (BrokenPipeError, OSError):
                pass
            log_event("sys", f"Talking through the loudspeaker ({who or '?'})")
            threading.Thread(target=_talk_watch, args=(p,), daemon=True).start()
        try:
            p.stdin.write(pcm); p.stdin.flush()
        except (BrokenPipeError, OSError):
            TALK["proc"] = None
            return False, "the loudspeaker could not be opened"
        TALK["last"] = now
    if AUDIO is not None:
        AUDIO.mute_until = now + 2.5
    return True, ""


def _talk_watch(p):
    while TALK["proc"] is p:
        if time.time() - TALK["last"] > 1.5:
            talk_stop(); break
        time.sleep(0.25)


def talk_stop():
    with _TALK_LOCK:
        p = TALK["proc"]; TALK["proc"] = None
    if p is None:
        return
    try:
        p.stdin.close()                                  # aplay plays what is left, then ends by itself
    except Exception:
        pass
    def reap():
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
    threading.Thread(target=reap, daemon=True).start()
    if AUDIO is not None:
        AUDIO.mute_until = time.time() + 2.0


