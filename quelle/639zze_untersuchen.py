#@ MoveEye – Teil 639zze: «🔍 Untersuchen» – ein Sofortbild der Live-Ansicht (Kopf, Weitwinkel, Wärmebild) oder ein hochgeladenes Foto untersuchen: Personen / Tiere / Fahrzeuge mit der KI, Arten mit BioCLIP (639zzd), Rahmen + Beschriftung über dem Live-Bild, Artinfo-Karte beim Antippen, Ergebnis automatisch im Datentausch-Ordner «Funde». Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Idee 11 des Besitzers (09.11.2026, Entscheide fest):
#   * Auslöser in der Live-Ansicht: Knopf «🔍 Untersuchen» = Sofortbild der aktuellen Ansicht; im Bild antippen (Bereich um den
#     Punkt) oder einen Rahmen ziehen = nur dieser Bereich; wahlweise fährt der Kopf zuerst dorthin (Kopf-Ansicht, Recht «head»;
#     ohne Kopf / Zoom: nur ausschneiden). Zoom: die Kamera am Kopf hat kein optisches Zoom (Camera Module 3) - «Zoom» heisst hier:
#     der Bereich wird aus dem vollen Kamerabild ausgeschnitten (volle Auflösung, nicht das kleine Vorschaubild).
#   * Auswertung: die vorhandene KI (AIDetector, SSD / eigenes YOLO; in der Demo die Demo-Rahmen) für Personen / Tiere /
#     Fahrzeuge, BioCLIP (639zzd, derselbe Rechen-Prozess, derselbe Zwischenspeicher) auf den Tier-Ausschnitten und auf dem
#     Bereich (sonst dem ganzen Bild) für die Art - auch Pflanzen und Pilze, die die KI nicht kennt. Keine freie Bildbeschreibung.
#   * Wärmebild: nur Personen / Tiere (KI + warme Körper der Wärmebild-Erkennung), BioCLIP nie (sagt die Oberfläche).
#   * Anzeige: Rahmen + kleine Beschriftung über dem Live-Bild, antippen = dieselbe Artinfo-Karte wie im Datentausch; bleibt,
#     bis man sie schliesst. Hochladen «📷 Foto untersuchen»: dasselbe für ein Foto vom Handy.
#   * Speichern: Bild + Ergebnis (JSON: Arten / Objekte, Zeit, Ort falls bekannt, Kamera, Bereich) in den Datentausch-Ordner
#     «Funde» («Für alle»; Grenzen und freier Platz wie jeder Upload; fehlt der Speicher, wird nur nicht gespeichert).
#   * Rechte: «live» darf untersuchen; Kopf fahren nur mit «head» (Admin immer). Gäste (Gast-Link): nur Sofortbild / Ausschnitt,
#     nie den Kopf, kein Hochladen. Modelle laden nur der Administrator.
#   * Pi: immer nur eine Untersuchung zugleich (sonst «gleich weiter»), Zeitlimit UNT_TIMEOUT_S, BioCLIP im bestehenden Prozess.
#   * Fenster (Tk): Knopf «🔍 Untersuchen» unter «Mehr» - Kopf-Kamera, ganzes Bild, Ergebnis als Text.
# Tests: werkzeuge/untersuchen_test.py (Demo-Kamera, Ersatz-Modelle, Rechte, Gäste, besetzt, Zeitlimit, Funde, Browser).
# ----------------------------------------------------------------------------
UNT_TIMEOUT_S = 90.0
UNT_UP_MAX = 15 * 1024 * 1024                  # a photo from the phone
UNT_BIO_MAX = 4                                # BioCLIP runs per job (the animals + the region)
UNT_RATE = (20, 60)                            # jobs per 10 minutes: a guest address, a person
UNT_FOLDER = "Funde"
UNT_MARGIN = 0.15                              # around an animal box for BioCLIP
UNT_TAP = 0.30                                 # a tap = a square of 30 % of the shorter side around the point
UNT = {"lock": threading.Lock(), "busy": "", "jobs": {}, "t": 0.0}
UNT_VEH = {"bicycle", "car", "motorcycle", "bus", "train", "truck", "boat"}
UNT_LABELS = {"person": "Person", "bird": "Bird", "cat": "Cat", "dog": "Dog", "horse": "Horse", "sheep": "Sheep", "cow": "Cow",
              "elephant": "Elephant", "bear": "Bear", "zebra": "Zebra", "giraffe": "Giraffe", "animal": "Animal", "bicycle": "Bicycle",
              "car": "Car", "motorcycle": "Motorcycle", "bus": "Bus", "train": "Train", "truck": "Truck", "boat": "Boat",
              "vehicle": "Vehicle", "warm": "Warm body"}

for _p in ("live",):
    PERM_POST[_p] = set(PERM_POST.get(_p, ())) | {"/api/untersuchen", "/api/untersuchen/upload"}
    PERM_GET[_p] = tuple(PERM_GET.get(_p, ())) + ("/api/untersuchen",)


def unt_perms(g_):
    """{"admin", "live", "head", "key", "name"} of the request (None for a guest)"""
    role = getattr(g_, "role", "admin")
    if role == "admin":
        return {"admin": True, "live": True, "head": True, "key": "admin", "name": "Admin"}
    u = user_get(getattr(g_, "user", ""))
    P = set(user_perms(u) if u else ROLE_PERMS.get(ROLE_OLD.get(role, role), ()))
    name = u["name"] if u else str(getattr(g_, "user", "") or "?")
    return {"admin": False, "live": "live" in P, "head": "head" in P, "key": name.lower(), "name": name}


def unt_box(b):
    """a region from the page: [x, y, w, h] 0..1 - clamped; a tap ([x, y] or w/h 0) = a square around the point; None = all"""
    if not isinstance(b, (list, tuple)) or len(b) < 2:
        return None
    try:
        v = [float(x) for x in b[:4]] + [0.0] * (4 - len(b[:4]))
    except (TypeError, ValueError):
        return None
    x, y, w, h = v
    if w < 0.02 or h < 0.02:                                   # a tap
        w = h = UNT_TAP
        x, y = x - w / 2, y - h / 2
    w, h = min(1.0, max(0.02, w)), min(1.0, max(0.02, h))
    x, y = min(1.0 - w, max(0.0, x)), min(1.0 - h, max(0.0, y))
    if w > 0.97 and h > 0.97:
        return None
    return [round(x, 4), round(y, 4), round(w, 4), round(h, 4)]


# ---- the picture of a camera ---------------------------------------------------------------------------------------------------------
def unt_cams():
    """which views exist now (for the page)"""
    w = WATCH_REF.get("w")
    return {"head": w is not None, "wide": bool(view3_wide_cam()), "thermal": THERMAL is not None and THERMAL.frame is not None
            and time.time() - THERMAL.t < 5.0}


def unt_frame(cam):
    """(BGR picture, "") or (None, english reason) - the full camera picture (not the small preview)"""
    if cam == "thermal":
        th = THERMAL
        if th is None or th.frame is None or time.time() - th.t > 5.0:
            return None, "no thermal picture"
        try:
            col, _g = th.color(th.crop(th.frame))
        except Exception as e:
            return None, "thermal picture: " + str(e)[:80]
        return col.copy(), ""
    if cam == "wide":
        c = view3_wide_cam()
        if c is None:
            return None, "no wide-angle camera"
        c.raw_until = time.time() + 15
        for _i in range(40):
            if c.raw is not None:
                return c.raw.copy(), ""
            time.sleep(0.1)
        return None, "no picture of the wide-angle camera"
    w = WATCH_REF.get("w")
    for src in (globals().get("WEB"),):                         # the web stream (640) keeps the raw picture while someone asks
        if src is not None and hasattr(src, "raw_until"):
            src.raw_until = time.time() + 15
            for _i in range(40):
                if src.frame_raw is not None:
                    return src.frame_raw.copy(), ""
                time.sleep(0.1)
    f = getattr(w, "frame_out", None) if w is not None else None
    return (f.copy(), "") if f is not None else (None, "no camera picture yet")


def unt_aim(box, lang=None):
    """drive the head so that the middle of the region is in the middle of the picture; -> (moved pan °, moved tilt °) or None"""
    try:
        hf, vf = cam_fov()
        cx, cy = box[0] + box[2] / 2, box[1] + box[3] / 2
        p0, t0 = servo_pos_deg()
        dp, dt = (cx - 0.5) * float(hf), -(cy - 0.5) * float(vf)
        hp, ht = servo_half("pan"), servo_half("tilt")
        tp = 50.0 + (p0 + dp) / max(1e-6, hp) * 50.0
        tt = 50.0 + (t0 + dt) / max(1e-6, ht) * 50.0
        if not servo_goto(tp, tt, who="untersuchen", wait=True, timeout=8.0):
            return None
        time.sleep(0.6)                                          # let the picture settle (exposure, motion blur)
        p1, t1 = servo_pos_deg()
        return p1 - p0, t1 - t0
    except Exception:
        return None


# ---- detection: persons / animals / vehicles ------------------------------------------------------------------------------------------
def unt_kind(lab):
    if lab == "person":
        return "person"
    if lab in ANIMALS or lab == "animal":
        return "animal"
    if lab in UNT_VEH or lab == "vehicle":
        return "vehicle"
    return ""


def unt_detect(img, thermal=False, warm=True):
    """[{kind, lab, conf, box 0..1}] - the AI of MoveEye (demo: the demo boxes); thermal: also the warm bodies"""
    H, W = img.shape[:2]
    out = []
    boxes, objs = [], []
    try:
        if DEMO.get("on"):
            boxes, objs = demo_ai(img)
        else:
            w = WATCH_REF.get("w")
            ai = getattr(w, "ai", None) if w is not None else None
            if ai is not None and ai.net is not None:
                boxes, objs = ai.infer(img, float(CFG.get("ai_conf", 0.5)), float(CFG.get("object_conf", 0.5)))
    except Exception as e:
        log_event("ai", f"Examine: AI failed: {str(e)[:120]}")
    for b in boxes:
        out.append({"kind": "person", "lab": "person", "conf": round(float(b[4]), 3), "box": [b[0] / W, b[1] / H, b[2] / W, b[3] / H]})
    for b in objs:
        lab = COCO_LABELS.get(int(b[5]), "") if len(b) > 5 else ""
        k = unt_kind(lab)
        if k and (not thermal or k != "vehicle"):
            out.append({"kind": k, "lab": lab, "conf": round(float(b[4]), 3), "box": [b[0] / W, b[1] / H, b[2] / W, b[3] / H]})
    if thermal and warm and THERMAL is not None:
        try:
            for b in THERMAL.detect() or []:                    # warm bodies (230): already 0..1 of the cropped thermal picture
                out.append({"kind": "animal", "lab": "warm", "conf": None, "box": [float(v) for v in b[:4]]})
        except Exception:
            pass
    for o in out:
        o["box"] = [round(max(0.0, min(1.0, v)), 4) for v in o["box"]]
    return out


def unt_bio(img, box, tmpdir):
    """BioCLIP on a part of the picture: the raw result (or None when BioCLIP is not ready)"""
    H, W = img.shape[:2]
    x, y, w, h = box
    x0, y0 = int(max(0, (x - w * UNT_MARGIN) * W)), int(max(0, (y - h * UNT_MARGIN) * H))
    x1, y1 = int(min(W, (x + w * (1 + UNT_MARGIN)) * W)), int(min(H, (y + h * (1 + UNT_MARGIN)) * H))
    if x1 - x0 < 16 or y1 - y0 < 16:
        return None
    p = os.path.join(tmpdir, "c_%d.jpg" % len(os.listdir(tmpdir)))
    cv2.imwrite(p, img[y0:y1, x0:x1], [cv2.IMWRITE_JPEG_QUALITY, 92])
    sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
    c = bio_cache_get(sha)
    if c is not None:
        return c
    ok, err, raw = bio_infer(p)
    if not ok:
        raise RuntimeError(err)
    return bio_cache_put(sha, raw)


# ---- saving into the file exchange: folder «Funde» --------------------------------------------------------------------------------------
def unt_save(who, jpg, result, base):
    """the picture + the result (JSON) into «Für alle / Funde»; -> {"jpg": id, "json": id} or {"error": reason}"""
    if not CFG.get("tausch_on", True):
        return {"error": "the file exchange is switched off"}
    root = _tz_load()
    if root is None:
        return {"error": "the storage (USB stick / SSD) is not there"}
    owner = who or {"key": "guest", "name": "Guest", "is_admin": False}
    sw = {"key": owner["key"], "name": owner["name"], "is_admin": bool(owner.get("admin")), "perms": set(TZ_PERMS)}
    data = json.dumps(result, ensure_ascii=False, indent=1).encode("utf-8")
    err = tausch_room_error(len(jpg) + len(data), sw, "en")
    if err:
        return {"error": err}
    out = {}
    with TZ["lock"]:
        if not any(x["name"] == UNT_FOLDER for x in TZ["folders"]):
            if len(TZ["folders"]) >= TZ_MAX_FOLDERS:
                return {"error": "too many folders"}
            TZ["folders"].append({"name": UNT_FOLDER, "by": "moveeye", "by_name": "MoveEye", "t": int(time.time())})
            TZ["folders"].sort(key=lambda x: x["name"].lower())
            _tz_folders_save(root)
        for ext, b in (("jpg", jpg), ("json", data)):
            name = _tz_unique(base + "." + ext, "all", UNT_FOLDER, sw["key"])
            fid = secrets.token_hex(8)
            m = {"id": fid, "name": name, "area": "all", "folder": UNT_FOLDER, "owner": sw["key"], "owner_name": sw["name"], "size": len(b),
                 "t": int(time.time()), "thumb": None if ext == "jpg" else False}
            try:
                with open(os.path.join(root, "f", fid + ".bin"), "wb") as f:
                    f.write(b)
                _tz_write_json(os.path.join(root, "f", fid + ".json"), m)
            except OSError as e:
                return {"error": "the storage cannot be written to (%s)" % e.__class__.__name__}
            TZ["files"][fid] = m
            out[ext] = fid
    tausch_thumb_queue(out["jpg"])
    return out


# ---- a job: picture -> (aim) -> AI -> BioCLIP -> save ---------------------------------------------------------------------------------
def unt_start(who, cam, box, aim, lang, img=None, src="live"):
    """start one examination (background); -> (ok, english error, job id). who None = guest."""
    cam = cam if cam in ("head", "wide", "thermal") else "head"
    with UNT["lock"]:
        if UNT["busy"]:
            return False, "busy", ""
        jid = secrets.token_hex(8)
        UNT["busy"] = jid
        UNT["jobs"][jid] = {"st": "run", "t": time.time(), "cam": cam, "box": box, "src": src, "step": "picture"}
        for k in sorted(UNT["jobs"], key=lambda k: UNT["jobs"][k]["t"])[:-40]:
            UNT["jobs"].pop(k, None)
    aim = bool(aim and box and cam == "head" and who and who.get("head"))

    def work():
        J = UNT["jobs"][jid]
        t0 = time.time()
        tmp = tempfile.mkdtemp(prefix="mw_unt_")
        try:
            pic = img
            if pic is None:
                pic, why = unt_frame(cam)
                if pic is None:
                    raise RuntimeError(why)
            bx = box
            if aim:
                J["step"] = "aim"
                mv = unt_aim(box)
                if mv is not None:
                    hf, vf = cam_fov()
                    cx = box[0] + box[2] / 2 - mv[0] / max(1e-6, float(hf))
                    cy = box[1] + box[3] / 2 + mv[1] / max(1e-6, float(vf))
                    bx = [min(1 - box[2], max(0.0, cx - box[2] / 2)), min(1 - box[3], max(0.0, cy - box[3] / 2)), box[2], box[3]]
                    bx = [round(v, 4) for v in bx]
                    J["aimed"] = True
                    p2, _w = unt_frame(cam)
                    if p2 is not None:
                        pic = p2
            J.update(step="ai", box=bx)
            H, W = pic.shape[:2]
            region = pic
            if bx:
                x0, y0 = int(bx[0] * W), int(bx[1] * H)
                region = pic[y0:y0 + max(1, int(bx[3] * H)), x0:x0 + max(1, int(bx[2] * W))]
            if DEMO.get("on") and img is None:                   # the demo knows its objects in the whole picture only (210)
                found = [o for o in unt_detect(pic, thermal=cam == "thermal", warm=not bx) if not bx or (
                    bx[0] <= o["box"][0] + o["box"][2] / 2 <= bx[0] + bx[2] and bx[1] <= o["box"][1] + o["box"][3] / 2 <= bx[1] + bx[3])]
            else:
                found = unt_detect(region, thermal=cam == "thermal", warm=not bx)
            if bx and not (DEMO.get("on") and img is None):      # back into the coordinates of the whole picture
                for o in found:
                    b = o["box"]
                    o["box"] = [round(bx[0] + b[0] * bx[2], 4), round(bx[1] + b[1] * bx[3], 4), round(b[2] * bx[2], 4), round(b[3] * bx[3], 4)]
            species, note = [], ""
            if cam == "thermal":
                note = "thermal"
            elif not (bio_runtime() and bio_installed()):
                note = "nobio"
            else:
                J["step"] = "bioclip"
                parts = [o["box"] for o in found if o["kind"] == "animal"][:UNT_BIO_MAX - 1]
                parts.append(bx or [0.0, 0.0, 1.0, 1.0])
                for b in parts:
                    if time.time() - t0 > UNT_TIMEOUT_S:
                        raise TimeoutError("timeout")
                    raw = unt_bio(pic, b, tmp)
                    if raw is not None:
                        species.append({"box": b, "raw": raw, "whole": b == [0.0, 0.0, 1.0, 1.0]})
            if time.time() - t0 > UNT_TIMEOUT_S:
                raise TimeoutError("timeout")
            J.update(found=found, species=species, note=note, size=[W, H])
            # save: the picture (whole, as seen) + the result
            ok, buf = cv2.imencode(".jpg", pic, [cv2.IMWRITE_JPEG_QUALITY, 90])
            jpg = buf.tobytes() if ok else b""
            J["jpg"] = jpg
            gp = None
            try:
                gp = gps_now()
            except Exception:
                gp = None
            res = unt_result_json(J, gp)
            base = time.strftime("Fund_%Y-%m-%d_%H%M%S")
            J["saved"] = unt_save(who, jpg, res, base) if jpg else {"error": "no picture"}
            J.update(st="done", ms=int((time.time() - t0) * 1000))
            log_event("web", f"Examine ({cam}{', region' if bx else ''}{', head moved' if J.get('aimed') else ''}): "
                             f"{len(found)} objects, {len(species)} species checks" + (f", saved in «{UNT_FOLDER}»" if "jpg" in J["saved"] else ""))
        except Exception as e:
            J.update(st="err", err=("timeout" if isinstance(e, TimeoutError) else str(e))[:200])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            with UNT["lock"]:
                if UNT["busy"] == jid:
                    UNT["busy"] = ""
                UNT["t"] = time.time()

    def guard():                                                 # the time limit: the page gets an answer in any case
        th = threading.Thread(target=work, daemon=True, name="unt-job")
        th.start()
        th.join(UNT_TIMEOUT_S + 15)
        J = UNT["jobs"].get(jid) or {}
        if J.get("st") == "run":
            J.update(st="err", err="timeout")
            with UNT["lock"]:
                if UNT["busy"] == jid:
                    UNT["busy"] = ""
    threading.Thread(target=guard, daemon=True, name="unt-guard").start()
    return True, "", jid


def unt_result_json(J, gp):
    """what goes into «Funde» (language-neutral: Latin + German names, no person data)"""
    sp = []
    for s in J.get("species") or []:
        f = bio_format(s["raw"], "de")
        sp.append({"box": s["box"], "whole_picture": s["whole"],
                   "top": [{"sci": t["sci"], "name_de": t["name"], "p": round(t["p"], 4), "group": t["group"]} for t in f["top"]],
                   "sure": {k: f["sure"][k] for k in ("rank", "sci", "name", "p")} if f.get("sure") else None})
    return {"moveeye": APP_VERSION, "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "camera": J.get("cam"), "source": J.get("src"),
            "region": J.get("box"), "head_moved": bool(J.get("aimed")),
            "location": {"lat": round(gp[0], 5), "lon": round(gp[1], 5), "source": gp[2]} if gp else None,
            "objects": [{"kind": o["kind"], "label": o["lab"], "conf": o["conf"], "box": o["box"]} for o in J.get("found") or []],
            "species": sp, "note": J.get("note") or "",
            "bioclip": "BioCLIP 1 (imageomics/bioclip, MIT)" if sp else None}


def unt_state(jid, who, lang):
    """the job for the page (all texts in lang)"""
    L = norm_lang(lang)
    J = UNT["jobs"].get(str(jid or ""))
    if J is None:
        return {"ok": False, "st": "err", "msg": tr("not found", L)}
    if J["st"] == "run":
        return {"ok": True, "st": "run", "step": J.get("step"), "msg": tr({"picture": "Taking the picture …", "aim": "The head turns there …",
                                                                           "ai": "Looking for persons, animals and vehicles …",
                                                                           "bioclip": "Identifying the species (BioCLIP) …"}.get(J.get("step"), "…"), L)}
    if J["st"] == "err":
        e = J.get("err") or ""
        return {"ok": False, "st": "err", "msg": tr("Examining did not work:", L) + " " + tr_err(e, L)}
    items = []
    for o in J.get("found") or []:
        items.append({"kind": o["kind"], "box": o["box"], "label": tr(UNT_LABELS.get(o["lab"], o["lab"]), L),
                      "icon": {"person": "🧍", "animal": "🐾", "vehicle": "🚗"}.get(o["kind"], "•"),
                      "pct": bio_pct(o["conf"], L) if o.get("conf") is not None else ""})
    for s in J.get("species") or []:
        f = bio_format(s["raw"], L)
        t0 = (f.get("top") or [{}])[0]
        lab = (t0.get("name") or t0.get("sci") or "?") if not f.get("unsure") else tr("unsure", L)
        if f.get("sure") and f["top"] and f["top"][0]["p"] < BIO_FALLBACK_BELOW:
            lab = (f["sure"]["name"] or f["sure"]["sci"])
        items.append({"kind": "species", "box": s["box"], "whole": s["whole"], "label": lab, "icon": t0.get("icon", "🌿"),
                      "pct": t0.get("pct", ""), "tox": bool(t0.get("tox")), "res": f})
    sv = J.get("saved") or {}
    note = {"thermal": tr("Thermal picture: only persons and animals - BioCLIP does not work on thermal pictures.", L),
            "nobio": tr("Species: BioCLIP is not loaded yet.", L) + " " + (tr("Load it under Datentausch → 🌿 or here.", L) if who and who.get("admin")
                                                                            else tr("The administrator can load it.", L))}.get(J.get("note") or "", "")
    return {"ok": True, "st": "done", "cam": J["cam"], "box": J.get("box"), "aimed": bool(J.get("aimed")), "items": items, "note": note,
            "nobio": J.get("note") == "nobio", "can_load": bool(who and who.get("admin")), "size": J.get("size"), "ms": J.get("ms"),
            "saved": ({"folder": UNT_FOLDER, "jpg": sv.get("jpg"), "msg": trf("Saved in Datentausch → «{f}»", L, f=UNT_FOLDER)} if sv.get("jpg")
                      else {"msg": tr("Not saved:", L) + " " + tr_err(sv.get("error") or "", L)}),
            "foot": tr(BIO_FOOT, L), "src": J.get("src"),
            "lbl": {k: tr(v, L) for k, v in (("info", "Species info"), ("tox", "☠️ Poisonous"), ("look", "Risk of confusion with:"),
                                             ("art", "Whole article"), ("lic", "Text: Wikipedia, CC BY-SA 4.0, abridged –"), ("auth", "authors"),
                                             ("none", "No species info for this species."), ("wd", "Facts: Wikidata (CC0)"), ("load", "Load species info"))}}


def unt_text(st, lang=None):
    """one result as text (window, log)"""
    if st.get("st") != "done":
        return st.get("msg") or ""
    lines = []
    for it in st.get("items") or []:
        if it["kind"] == "species":
            lines.append("%s %s – %s" % (it["icon"], it["label"], it["pct"]) + ("  ☠️" if it.get("tox") else ""))
        else:
            lines.append("%s %s%s" % (it["icon"], it["label"], (" – " + it["pct"]) if it["pct"] else ""))
    if not lines:
        lines.append(tr("Nothing found.", lang))
    if st.get("note"):
        lines.append("ℹ " + st["note"])
    lines.append((st.get("saved") or {}).get("msg") or "")
    return "\n".join(x for x in lines if x)


def unt_image(jid):
    J = UNT["jobs"].get(str(jid or ""))
    return (J or {}).get("jpg")


# ---- web: /api/untersuchen (+ /upload, /img/<id>.jpg), guests /g/<token>/untersuchen ---------------------------------------------------
_smalltv_routes_639zze = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zze
    _smalltv_routes_639zze(app, reply, body)
    from flask import Response, request, g

    def size_guard():                                    # a too big photo is not even read
        if request.path in ("/api/untersuchen/upload",) and request.method == "POST":
            n = request.content_length
            if n is None or n > UNT_UP_MAX:
                return Response(json.dumps({"ok": False, "st": "err", "msg": "photo too big"}), 413, mimetype="application/json",
                                headers={"Connection": "close"})
        return None
    app.before_request_funcs.setdefault(None, []).insert(0, size_guard)

    def start(who, d, L, rate_key, img=None, src="live"):
        if not tausch_rate(rate_key, "unt", UNT_RATE[0 if who is None else 1]):
            return reply({"ok": False, "st": "err", "msg": tr("Too many requests in a short time - wait a few minutes.", L)}, 429)
        ok, err, jid = unt_start(who, str(d.get("cam") or "head"), unt_box(d.get("box")), bool(d.get("aim")) and who is not None, L, img, src)
        if not ok:
            return reply({"ok": False, "st": "wait" if err == "busy" else "err",
                          "msg": tr("Another examination is running - it continues right after …", L) if err == "busy" else tr_err(err, L)},
                         409 if err == "busy" else 400)
        return reply({"ok": True, "st": "run", "id": jid})

    @app.route("/api/untersuchen", methods=["GET", "POST"])
    def api_untersuchen():
        who = unt_perms(g)
        if request.method == "GET":
            L = norm_lang(request.args.get("lang") or CFG.get("lang"))
            if not who["live"]:
                return reply({"ok": False, "st": "err", "msg": tr("not allowed for your user", L)}, 403)
            if request.args.get("id"):
                return reply(unt_state(request.args.get("id"), who, L))
            return reply({"ok": True, "cams": unt_cams(), "head": who["head"], "busy": bool(UNT["busy"]),
                          "bio": bio_installed() and bio_runtime(), "admin": who["admin"]})
        d = body()
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        if not who["live"]:
            return reply({"ok": False, "st": "err", "msg": tr("not allowed for your user", L)}, 403)
        if d.get("action") == "bio_load":
            if not who["admin"]:
                return reply({"ok": False, "st": "err", "msg": tr("Only the administrator may load models.", L)}, 403)
            ok, err = bio_download()
            return reply({"ok": ok, "st": "loading" if ok else "err", "msg": tr(err, L) if err else ""}, 200 if ok else 400)
        if d.get("aim") and not who["head"]:
            return reply({"ok": False, "st": "err", "msg": tr("You may not move the head.", L)}, 403)
        return start(who, d, L, who["key"])

    @app.route("/api/untersuchen/upload", methods=["POST"])
    def api_untersuchen_upload():
        who = unt_perms(g)
        L = norm_lang(request.args.get("lang") or CFG.get("lang"))
        if not who["live"]:
            return reply({"ok": False, "st": "err", "msg": tr("not allowed for your user", L)}, 403)
        data = request.get_data(cache=False)
        img = None
        if data[:2] == b"\xff\xd8" or data[:8] == b"\x89PNG\r\n\x1a\n" or data[:4] == b"RIFF":
            try:
                img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            except (cv2.error, ValueError):
                img = None
        if img is None or img.size == 0 or img.shape[0] * img.shape[1] > 60_000_000:
            return reply({"ok": False, "st": "err", "msg": tr("This is not a photo MoveEye can read (JPEG, PNG or WebP).", L)}, 400)
        if max(img.shape[:2]) > 2400:                            # enough for the AI and BioCLIP, keeps the Pi fast
            k = 2400.0 / max(img.shape[:2])
            img = cv2.resize(img, (int(img.shape[1] * k), int(img.shape[0] * k)), interpolation=cv2.INTER_AREA)
        return start(who, {"cam": "head", "box": None}, L, who["key"], img, "upload")

    @app.route("/api/untersuchen/img/<jid>.jpg")
    def api_untersuchen_img(jid):
        who = unt_perms(g)
        b = unt_image(jid) if who["live"] else None
        if not b:
            return Response("not found", 404)
        return Response(b, mimetype="image/jpeg", headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})

    def guest_gate(token):
        if not guest_ok(token):
            return False
        return tausch_rate("guest|" + (request.remote_addr or "?"), "g", 2000)

    @app.route("/g/<token>/untersuchen", methods=["GET", "POST"])
    def guest_untersuchen(token):
        if not guest_gate(token):
            return reply({"ok": False}, 404)
        L = sx_req_lang()
        if request.method == "GET":
            if request.args.get("id"):
                return reply(unt_state(request.args.get("id"), None, L))
            return reply({"ok": True, "cams": {"head": True, "wide": False, "thermal": False}, "head": False, "busy": bool(UNT["busy"])})
        d = body()
        d["aim"] = False                                         # guests: never the head
        return start(None, {"cam": "head", "box": d.get("box")}, L, "guest|" + (request.remote_addr or "?"))


# ---- the pages: Live (530) and the guest page (520) -------------------------------------------------------------------------------
UNT_CSS = r"""
/* above the page tips (515 #gd-card 250), below the guided tour (516 #g2-ov 280) */
#lv-tools #lv-b-unt,#lv-tools #lv-b-unt-up{font-size:17px;line-height:1}
.unt-ov{position:absolute;z-index:7;overflow:hidden;pointer-events:none}
.unt-ov.sel{pointer-events:auto;cursor:crosshair;touch-action:none;background:rgba(0,0,0,.18);outline:2px dashed #ffd34d;outline-offset:-2px}
.unt-ov .ub{position:absolute;border:2px solid #3fcf6b;border-radius:4px;box-shadow:0 0 0 1px rgba(0,0,0,.6);box-sizing:border-box}
.unt-ov .ub.person{border-color:#ff9f43}.unt-ov .ub.vehicle{border-color:#8ab4f8}.unt-ov .ub.animal{border-color:#3fcf6b}
.unt-ov .ub.species{border-color:#ffd34d;border-style:dashed}.unt-ov .ub.tox{border-color:#ff4d4d;border-style:solid}
.unt-ov .ub.region{border:2px dashed #ffd34d;background:rgba(255,211,77,.08)}
.unt-ov .ul{position:absolute;left:-2px;top:-24px;max-width:240px;font:700 12px/1.25 system-ui,-apple-system,sans-serif;color:#000;background:#3fcf6b;
  padding:3px 7px;border-radius:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;pointer-events:auto;cursor:pointer;box-shadow:0 1px 4px rgba(0,0,0,.5)}
.unt-ov .ub.person .ul{background:#ff9f43}.unt-ov .ub.vehicle .ul{background:#8ab4f8}.unt-ov .ub.species .ul{background:#ffd34d}
.unt-ov .ub.tox .ul{background:#ff4d4d;color:#fff}.unt-ov .ub.in .ul{top:2px;left:2px}
#unt-bar{position:fixed;z-index:260;left:50%;transform:translateX(-50%);bottom:max(14px,env(safe-area-inset-bottom));width:min(560px,calc(100vw - 20px));
  background:var(--panel,#121821);color:var(--txt,#e8eef5);border:1px solid var(--line,#2a3442);border-radius:14px;padding:10px 12px;
  box-shadow:0 10px 30px rgba(0,0,0,.55);font:14px/1.4 system-ui,-apple-system,sans-serif}
#unt-bar[hidden]{display:none}#unt-bar .t{font-weight:600;margin:0 0 6px}#unt-bar .m{font-size:13px;opacity:.85;margin:0 0 6px}
#unt-bar .r{display:flex;gap:8px;flex-wrap:wrap;align-items:center}#unt-bar button{min-height:40px;padding:6px 12px;border-radius:10px}
#unt-bar label{display:flex;gap:6px;align-items:center;font-size:13.5px;flex:1 1 100%}#unt-bar .bad{color:var(--red,#ff6b6b)}
#unt-bar .x{margin-left:auto}
#unt-host{position:fixed;inset:0;z-index:262;pointer-events:none}#unt-host>.tz-bio{pointer-events:auto}
#unt-up{position:fixed;inset:0;z-index:258;background:rgba(0,0,0,.92);display:flex;flex-direction:column}
#unt-up[hidden]{display:none}#unt-up .bar{display:flex;gap:8px;align-items:center;padding:10px 12px;padding-top:max(10px,env(safe-area-inset-top));color:#fff}
#unt-up .bar b{flex:1}#unt-up .bd{flex:1;position:relative;display:flex;align-items:center;justify-content:center;min-height:0;padding:8px}
#unt-up img{max-width:100%;max-height:100%;object-fit:contain;border-radius:8px}
"""

UNT_JS = r"""
(function () {
  const G = window.UNT_CFG || {};                         // {api, img, tools, guest}
  const T = k => (window.UTX && UTX[k]) || (typeof t === "function" ? t(k) : k);
  const E = (tag, cls, x) => { const e = document.createElement(tag); if (cls) e.className = cls; if (x !== undefined) e.textContent = x; return e; };
  const L = () => (typeof LANG !== "undefined" ? LANG : "");
  const img = () => document.querySelector(G.img);
  const S = {mode: "", box: null, drag: null, res: null, poll: 0, info: null};
  let OV = null, BAR = null, HOST = null;
  async function api(path, opt) {
    try { const r = await fetch(G.api + path, opt); const j = await r.json(); return j; } catch (e) { return {ok: false, st: "err", msg: T("No connection to MoveEye.")}; }
  }
  function cam() {
    if (G.guest) return "head";
    let v = {}; try { v = JSON.parse(localStorage.getItem("mw-view3") || "{}"); } catch (e) {}
    const J = (typeof QSJ !== "undefined" && QSJ) || {}, x = (J.state || {}).extra, w = x && x[0] && x[0].view3;
    if (v.view === "wide" && w && w.wide != null) return "wide";
    if ((J.cfg || {}).thermal_on && (J.cfg || {}).thermal_source) return "thermal";
    return "head";
  }
  function fit(ov, im) {                                  // the layer exactly over the shown picture (object-fit: contain)
    const p = ov.parentNode; if (!p || !im || !im.naturalWidth || !im.getClientRects().length) return false;
    const r = im.getBoundingClientRect(), pr = p.getBoundingClientRect(), nw = im.naturalWidth, nh = im.naturalHeight || 1;
    const k = Math.min(r.width / nw, r.height / nh), w = nw * k, h = nh * k;
    ov.style.left = (r.left - pr.left - (p.clientLeft || 0) + (r.width - w) / 2) + "px"; ov.style.top = (r.top - pr.top - (p.clientTop || 0) + (r.height - h) / 2) + "px";
    ov.style.width = w + "px"; ov.style.height = h + "px"; return true;
  }
  function ensureOv() {
    const im = img(); if (!im) return null;
    if (!OV || !OV.isConnected) { OV = E("div", "unt-ov"); OV.id = "unt-ov"; im.parentNode.appendChild(OV); }
    fit(OV, im); return OV;
  }
  setInterval(() => { if (OV && OV.isConnected && (S.mode || S.res)) fit(OV, img()); }, 400);
  function bar(title, msg, btns, check) {
    if (!BAR) { BAR = E("div"); BAR.id = "unt-bar"; document.body.appendChild(BAR); }
    BAR.hidden = false; BAR.textContent = "";
    BAR.append(E("div", "t", title)); if (msg) BAR.append(E("div", "m" + (msg.bad ? " bad" : ""), msg.text || msg));
    const r = E("div", "r"); if (check) r.append(check); btns.forEach(b => r.append(b)); BAR.append(r);
  }
  const btn = (txt, fn, cls) => { const b = E("button", cls || "", txt); b.type = "button"; b.onclick = e => { e.stopPropagation(); fn(); }; return b; };
  function closeAll() { S.mode = ""; S.box = null; S.res = null; clearTimeout(S.poll); if (OV) { OV.remove(); OV = null; } if (BAR) BAR.hidden = true;
    const h = document.getElementById("unt-host"); if (h) h.textContent = ""; const u = document.getElementById("unt-up"); if (u) u.hidden = true; }
  // ---- choose: tap = a square around the point, drag = a box, or the whole picture ----
  async function choose() {
    if (S.mode === "sel") return closeAll();
    closeAll();
    S.info = G.guest ? {head: false} : await api("?lang=" + L());
    const ov = ensureOv(); if (!ov) return;
    S.mode = "sel"; ov.classList.add("sel"); ov.textContent = "";
    let aimC = null;
    const c = cam();
    if (!G.guest && c === "head" && S.info && S.info.head) { aimC = E("label"); const cb = E("input"); cb.type = "checkbox"; cb.id = "unt-aim"; aimC.append(cb, document.createTextNode(T("🎯 Turn the head there first (pan / tilt)"))); }
    const note = c === "thermal" ? T("Thermal picture: only persons and animals - BioCLIP does not work on thermal pictures.") : "";
    bar("🔍 " + T("Examine") + " · " + T({head: "Head view", wide: "Wide view", thermal: "Thermal view"}[c]),
        (note ? note + " " : "") + T("Tap a spot or drag a box in the picture - or examine the whole picture."),
        [btn("🖼 " + T("Whole picture"), () => go(null)), btn(T("Cancel"), closeAll, "sec x")], aimC);
    ov.onpointerdown = e => { e.preventDefault(); ov.setPointerCapture(e.pointerId); const r = ov.getBoundingClientRect();
      S.drag = {x: (e.clientX - r.left) / r.width, y: (e.clientY - r.top) / r.height, r}; drawSel(S.drag.x, S.drag.y, 0, 0); };
    ov.onpointermove = e => { if (!S.drag) return; const r = S.drag.r, x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      drawSel(Math.min(x, S.drag.x), Math.min(y, S.drag.y), Math.abs(x - S.drag.x), Math.abs(y - S.drag.y)); };
    ov.onpointerup = e => { if (!S.drag) return; const r = S.drag.r, x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      let b = [Math.min(x, S.drag.x), Math.min(y, S.drag.y), Math.abs(x - S.drag.x), Math.abs(y - S.drag.y)]; S.drag = null;
      if (b[2] < 0.03 || b[3] < 0.03) { const a = (img().naturalHeight || 1) / (img().naturalWidth || 1), s = 0.3; const w = Math.min(1, s * Math.min(1, a)), h = Math.min(1, s * Math.min(1, 1 / a));
        b = [Math.max(0, Math.min(1 - w, x - w / 2)), Math.max(0, Math.min(1 - h, y - h / 2)), w, h]; }
      S.box = b.map(v => Math.max(0, Math.min(1, v))); drawSel(...S.box);
      bar("🔍 " + T("Examine this region?"), "", [btn("🔍 " + T("Examine"), () => go(S.box)), btn(T("Other region"), () => { S.box = null; ov.textContent = ""; }, "sec"),
          btn(T("Cancel"), closeAll, "sec x")], aimC); };
  }
  function drawSel(x, y, w, h) {
    OV.textContent = ""; const b = E("div", "ub region"); b.style.left = (x * 100) + "%"; b.style.top = (y * 100) + "%"; b.style.width = (w * 100) + "%"; b.style.height = (h * 100) + "%"; OV.append(b);
  }
  // ---- run ----
  async function go(box, upload) {
    const aimEl = document.getElementById("unt-aim");
    const body = {cam: cam(), box: box, aim: !!(aimEl && aimEl.checked && box), lang: L()};
    if (OV) { OV.classList.remove("sel"); OV.onpointerdown = OV.onpointermove = OV.onpointerup = null; }
    S.mode = "run";
    bar("🔍 " + T("Examine"), "⏳ " + T("Taking the picture …"), [btn(T("Cancel"), closeAll, "sec x")]);
    let r = upload ? await upload() : await api("", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
    while (r && r.st === "wait") { bar("🔍 " + T("Examine"), "⏳ " + (r.msg || ""), [btn(T("Cancel"), closeAll, "sec x")]); await new Promise(z => setTimeout(z, 2500));
      if (S.mode !== "run") return; r = upload ? await upload() : await api("", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)}); }
    if (!r || !r.id) return bar("🔍 " + T("Examine"), {bad: 1, text: (r && r.msg) || T("error")}, [btn(T("Close"), closeAll, "sec x")]);
    const id = r.id;
    const step = async () => {
      if (S.mode !== "run") return;
      const s = await api("?id=" + id + "&lang=" + L());
      if (s.st === "run") { bar("🔍 " + T("Examine"), "⏳ " + (s.msg || "…"), [btn(T("Cancel"), closeAll, "sec x")]); S.poll = setTimeout(step, 700); return; }
      if (s.st !== "done") return bar("🔍 " + T("Examine"), {bad: 1, text: s.msg || T("error")}, [btn(T("Close"), closeAll, "sec x")]);
      S.mode = ""; S.res = s; s.id = id; show(s, !!upload);
    };
    step();
  }
  // ---- the result: boxes + labels over the picture; a label opens the species card ----
  function show(s, upload) {
    let ov;
    if (upload) {                                         // the uploaded photo in its own view
      let u = document.getElementById("unt-up");
      if (!u) { u = E("div"); u.id = "unt-up"; const b = E("div", "bar"), bd = E("div", "bd"); b.append(E("b", "", "📷 " + T("Photo examined")), btn("✕", closeAll, "sec"));
        u.append(b, bd); document.body.appendChild(u); }
      u.hidden = false; const bd = u.querySelector(".bd"); bd.textContent = ""; const im = E("img"); im.alt = ""; im.id = "unt-up-img";
      bd.append(im); ov = E("div", "unt-ov"); ov.id = "unt-ov-up"; bd.append(ov);
      im.onload = () => fit(ov, im); im.src = G.api + "/img/" + s.id + ".jpg"; setTimeout(() => fit(ov, im), 300);
      const keep = setInterval(() => { if (!u.isConnected || u.hidden) return clearInterval(keep); fit(ov, im); }, 500);
    } else { ov = ensureOv(); if (!ov) return; ov.classList.remove("sel"); }
    ov.textContent = "";
    const items = s.items || [];
    items.forEach((it, i) => {
      const b = E("div", "ub " + it.kind + (it.tox ? " tox" : "") + ((it.box[1] < 0.06 || it.whole) ? " in" : ""));
      b.style.left = (it.box[0] * 100) + "%"; b.style.top = (it.box[1] * 100) + "%"; b.style.width = (it.box[2] * 100) + "%"; b.style.height = (it.box[3] * 100) + "%";
      const l = E("div", "ul", (it.tox ? "☠️ " : "") + it.icon + " " + it.label + (it.pct ? " " + it.pct : "")); l.title = it.label;
      l.onclick = e => { e.stopPropagation(); open(it, s); }; b.append(l); ov.append(b);
    });
    const n = items.length;
    const msg = (n ? "" : T("Nothing found.") + " ") + (s.note || "") + " " + ((s.saved || {}).msg || "");
    const btns = [btn(T("Close"), closeAll, "sec x")];
    if (s.nobio && s.can_load) btns.unshift(btn("⬇ " + T("Load BioCLIP"), async () => { const r = await api("", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({action: "bio_load", lang: L()})}); bar("🔍", r.msg || T("Loading BioCLIP …"), [btn(T("Close"), closeAll, "sec x")]); }, ""));
    const sp = items.find(x => x.kind === "species"); if (sp) btns.unshift(btn("📖 " + sp.label, () => open(sp, s), ""));
    bar("🔍 " + (n ? n + " " + T(n === 1 ? "find" : "finds") : T("Examined")), msg.trim(), btns);
    const f = E("div", "m", "⚠️ " + (s.foot || "")); BAR.append(f);
  }
  function open(it, s) {
    if (it.kind !== "species" || !it.res) { if (typeof toast === "function") toast(it.icon + " " + it.label + (it.pct ? " · " + it.pct : "")); return; }
    if (typeof tzBioPanel !== "function") return;
    let h = document.getElementById("unt-host"); if (!h) { h = E("div"); h.id = "unt-host"; document.body.appendChild(h); }
    h.textContent = "";
    tzBioPanel(null, h, null, {}, T, {st: "done", res: Object.assign({lbl: s.lbl, foot: s.foot}, it.res), can_dl: false});
  }
  // ---- upload «📷 Foto untersuchen» ----
  function uploadPick() {
    let inp = document.getElementById("unt-file");
    if (!inp) { inp = E("input"); inp.type = "file"; inp.accept = "image/*"; inp.id = "unt-file"; inp.hidden = true; document.body.appendChild(inp);
      inp.onchange = () => { const f = inp.files && inp.files[0]; inp.value = ""; if (!f) return; closeAll();
        go(null, () => fetch(G.api + "/upload?lang=" + L(), {method: "POST", headers: {"Content-Type": "application/octet-stream"}, body: f}).then(r => r.json()).catch(() => ({st: "err", msg: T("No connection to MoveEye.")}))); }; }
    inp.click();
  }
  window.mwUntersuchen = {choose, upload: uploadPick, close: closeAll};
  function tools() {
    if (G.tools === "live") {
      const tb = document.getElementById("lv-tools"); if (!tb) return setTimeout(tools, 400);
      if (document.getElementById("lv-b-unt")) return;
      const mk = (id, txt, tip, fn) => { const b = E("button", "", txt); b.type = "button"; b.id = id; b.title = T(tip); b.setAttribute("aria-label", T(tip));
        b.onclick = e => { e.stopPropagation(); fn(); }; b.addEventListener("dblclick", e => e.stopPropagation()); return b; };
      const vb = document.getElementById("lv-b-view");
      tb.insertBefore(mk("lv-b-unt", "🔍", "Examine: snapshot, tap a spot or drag a box", choose), vb || null);
      tb.insertBefore(mk("lv-b-unt-up", "📷", "Examine a photo (upload from the phone)", uploadPick), vb || null);
    } else if (G.tools === "guest") {
      const f = document.getElementById("ft"); if (!f || document.getElementById("g-unt")) return;
      const b = E("button", "", "🔍 " + T("Examine")); b.id = "g-unt"; b.type = "button";
      b.style.cssText = "margin:8px auto 0;display:block;background:#1a2433;color:#fff;border:1px solid #2a3442;border-radius:10px;padding:8px 16px;font:inherit";
      b.onclick = choose; f.parentNode.insertBefore(b, f.nextSibling);
    }
  }
  tools();
})();
"""


def unt_live_html():
    return ("<style>" + BIO_CSS + UNT_CSS + "</style><script>\nObject.assign(I18N.de, " + json.dumps(_UNT_DE, ensure_ascii=False) + ");\n"
            + BIO_PANEL_JS + "\nif (document.body.dataset.tab === \"live\") { window.UNT_CFG = {api: \"/api/untersuchen\", img: \"#video\", tools: \"live\"};\n"
            + UNT_JS + "}\n</script>")


if "/*UNT*/" not in WEB_PAGE:
    WEB_PAGE = WEB_PAGE.replace("</body>", "<!--UNT-->/*UNT*/</body>", 1)
_render_page_639zze = render_page


# wraps: render_page
def render_page(page, active):                              # + 639zze: the live page gets «🔍 Untersuchen»
    out = _render_page_639zze(page, active)
    if "<!--UNT-->/*UNT*/" in out:
        out = out.replace("<!--UNT-->/*UNT*/", unt_live_html(), 1)
    return out


_GUEST_UNT = "<style>" + "/*BIOCSS*/" + "</style><script>/*UNTG*/</script>"
if "/*UNTG*/" not in GUEST_PAGE and "\nst();\n" in GUEST_PAGE:
    GUEST_PAGE = GUEST_PAGE.replace("</body>", _GUEST_UNT + "</body>", 1)


def unt_guest_js(lang, token):
    L = norm_lang(lang)
    tx = {k: tr(k, L) for k in _HX_UNT}
    tx.update({k: tr(k, L) for k in BIO_JS_KEYS})
    tx.update({"Head view": tr("Head view", L), "Cancel": tr("Cancel", L), "Close": tr("Close", L), "Nothing found.": tr("Nothing found.", L)})
    return ("window.UTX = " + json.dumps(tx, ensure_ascii=False).replace("</", "<\\/") + ";\n" + BIO_PANEL_JS
            + "\nwindow.UNT_CFG = {api: " + json.dumps("/g/" + token + "/untersuchen") + ", img: \"#v\", tools: \"guest\", guest: true};\n" + UNT_JS)


_smalltv_routes_639zze2 = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zze: the guest page gets the button (only the picture, no head)
    _smalltv_routes_639zze2(app, reply, body)
    from flask import request

    @app.after_request
    def unt_guest_inject(resp):
        try:
            p = request.path
            if (p.startswith("/g/") and p.count("/") == 2 and resp.status_code == 200 and resp.mimetype == "text/html"
                    and not resp.direct_passthrough):
                html = resp.get_data(as_text=True)
                if "/*UNTG*/" in html:
                    tok = p.split("/")[2]
                    html = html.replace("/*BIOCSS*/", BIO_CSS + UNT_CSS, 1).replace("/*UNTG*/", unt_guest_js(sx_req_lang(), tok).replace("</script", "<\\/script"), 1)
                    resp.set_data(html)
        except Exception:
            pass
        return resp


# ---- the window (Tk): «🔍 Untersuchen» under «Mehr» - head camera, whole picture, result as text -------------------------------------
if GUI_OK:
    _unt_tk_more_base = App._tk_more_bar

    def _unt_tk_more_bar(self, parent):
        f = _unt_tk_more_base(self, parent)
        skip = getattr(self, "_fk_more_row", None)
        i = len([w for w in f.grid_slaves() if w is not skip])

        def run():
            def work():
                ok, err, jid = unt_start({"admin": True, "live": True, "head": True, "key": "admin", "name": "Admin"}, "head", None, False, CFG.get("lang"))
                txt = tr_err(err) if not ok else ""
                if ok:
                    end = time.time() + UNT_TIMEOUT_S + 20
                    while time.time() < end and (UNT["jobs"].get(jid) or {}).get("st") == "run":
                        time.sleep(0.3)
                    txt = unt_text(unt_state(jid, {"admin": True}, CFG.get("lang")), CFG.get("lang"))
                try:
                    self.root.after(0, lambda: messagebox.showinfo("🔍 " + tr("Examine"), txt))
                except Exception:
                    pass
            threading.Thread(target=work, daemon=True, name="unt-tk").start()
            try:
                self._status("🔍 " + tr("Taking the picture …"))
            except Exception:
                pass
        self._fbtn(f, "🔍 " + tr("Examine"), run).grid(row=i // 3, column=i % 3, sticky="ew", padx=(0, 6), pady=(0, 6))
        return f

    # wraps: App._tk_more_bar (572, after 639zzc)
    App._tk_more_bar = _unt_tk_more_bar


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_UNT = {
    "Examine": ("Untersuchen", "Examiner", "Esaminare", "Examinar"),
    "Examine: snapshot, tap a spot or drag a box": ("Untersuchen: Sofortbild, Stelle antippen oder Rahmen ziehen", "Examiner : instantané, toucher un endroit ou tracer un cadre",
                                                    "Esaminare: istantanea, tocca un punto o traccia un riquadro", "Examinar: maletg instantan, tutgar in lieu u trair in rom"),
    "Examine a photo (upload from the phone)": ("Foto untersuchen (vom Handy hochladen)", "Examiner une photo (envoyer depuis le téléphone)",
                                                "Esaminare una foto (caricare dal telefono)", "Examinar ina foto (chargiar si dal telefonin)"),
    "Tap a spot or drag a box in the picture - or examine the whole picture.": (
        "Im Bild eine Stelle antippen oder einen Rahmen ziehen – oder das ganze Bild untersuchen.",
        "Touche un endroit ou trace un cadre dans l’image – ou examine toute l’image.",
        "Tocca un punto o traccia un riquadro nell’immagine – o esamina tutta l’immagine.",
        "Tutga in lieu u trai in rom en il maletg – u examinescha l’entir maletg."),
    "Whole picture": ("Ganzes Bild", "Toute l’image", "Tutta l’immagine", "Entir maletg"),
    "Examine this region?": ("Diesen Bereich untersuchen?", "Examiner cette zone ?", "Esaminare quest’area?", "Examinar quest sectur?"),
    "Other region": ("Anderer Bereich", "Autre zone", "Altra area", "Auter sectur"),
    "🎯 Turn the head there first (pan / tilt)": ("🎯 Zuerst den Kopf dorthin drehen (schwenken / neigen)", "🎯 Tourner d’abord la tête vers là (pan / tilt)",
                                                 "🎯 Prima girare la testa lì (pan / tilt)", "🎯 L’emprim volver il chau là (pan / tilt)"),
    "Taking the picture …": ("Bild wird aufgenommen …", "Prise de l’image …", "Scatto dell’immagine …", "Il maletg vegn fatg …"),
    "The head turns there …": ("Der Kopf dreht dorthin …", "La tête tourne vers là …", "La testa gira lì …", "Il chau sa volva là …"),
    "Looking for persons, animals and vehicles …": ("Suche nach Personen, Tieren und Fahrzeugen …", "Recherche de personnes, d’animaux et de véhicules …",
                                                     "Ricerca di persone, animali e veicoli …", "Tschertga da persunas, animals e vehichels …"),
    "Identifying the species (BioCLIP) …": ("Art wird bestimmt (BioCLIP) …", "Identification de l’espèce (BioCLIP) …", "Identificazione della specie (BioCLIP) …",
                                            "La spezia vegn determinada (BioCLIP) …"),
    "Examining did not work:": ("Untersuchen ging nicht:", "L’examen n’a pas marché :", "L’esame non è riuscito:", "Examinar n’ha betg funcziunà:"),
    "Another examination is running - it continues right after …": ("Gerade läuft eine andere Untersuchung – es geht gleich weiter …",
                                                                    "Un autre examen est en cours – ça continue juste après …",
                                                                    "È in corso un altro esame – si continua subito dopo …",
                                                                    "Ussa curra in’autra examinaziun – i cuntinuescha immediat …"),
    "Thermal picture: only persons and animals - BioCLIP does not work on thermal pictures.": (
        "Wärmebild: nur Personen und Tiere – BioCLIP bestimmt keine Arten auf Wärmebildern.",
        "Image thermique : seulement personnes et animaux – BioCLIP ne fonctionne pas sur les images thermiques.",
        "Immagine termica: solo persone e animali – BioCLIP non funziona sulle immagini termiche.",
        "Maletg termic: mo persunas ed animals – BioCLIP na funcziuna betg sin maletgs termics."),
    "Species: BioCLIP is not loaded yet.": ("Arten: BioCLIP ist noch nicht geladen.", "Espèces : BioCLIP n’est pas encore chargé.",
                                            "Specie: BioCLIP non è ancora caricato.", "Spezias: BioCLIP n’è anc betg chargià."),
    "Load it under Datentausch → 🌿 or here.": ("Laden unter Datentausch → 🌿 oder hier.", "Le charger sous Échange de fichiers → 🌿 ou ici.",
                                               "Caricalo in Scambio di file → 🌿 o qui.", "Al chargiar sut Barat da datotecas → 🌿 u qua."),
    "The administrator can load it.": ("Der Administrator kann es laden.", "L’administrateur peut le charger.", "L’amministratore può caricarlo.",
                                       "L’administratur po al chargiar."),
    "Saved in Datentausch → «{f}»": ("Gespeichert im Datentausch → «{f}»", "Enregistré dans l’échange de fichiers → «{f}»",
                                     "Salvato nello scambio di file → «{f}»", "Memorisà en il barat da datotecas → «{f}»"),
    "Not saved:": ("Nicht gespeichert:", "Pas enregistré :", "Non salvato:", "Betg memorisà:"),
    "Photo examined": ("Foto untersucht", "Photo examinée", "Foto esaminata", "Foto examinada"),
    "Examined": ("Untersucht", "Examiné", "Esaminato", "Examinà"),
    "find": ("Fund", "trouvaille", "reperto", "chat"),
    "finds": ("Funde", "trouvailles", "reperti", "chats"),
    "Load BioCLIP": ("BioCLIP laden", "Charger BioCLIP", "Caricare BioCLIP", "Chargiar BioCLIP"),
    "Loading BioCLIP …": ("BioCLIP wird geladen …", "Chargement de BioCLIP …", "Caricamento di BioCLIP …", "BioCLIP vegn chargià …"),
    "Only the administrator may load models.": ("Nur der Administrator darf Modelle laden.", "Seul l’administrateur peut charger des modèles.",
                                                "Solo l’amministratore può caricare modelli.", "Mo l’administratur dastga chargiar models."),
    "You may not move the head.": ("Du darfst den Kopf nicht bewegen.", "Tu ne peux pas bouger la tête.", "Non puoi muovere la testa.",
                                   "Ti na dastas betg mover il chau."),
    "This is not a photo MoveEye can read (JPEG, PNG or WebP).": ("Das ist kein Foto, das MoveEye lesen kann (JPEG, PNG oder WebP).",
                                                                   "Ce n’est pas une photo lisible par MoveEye (JPEG, PNG ou WebP).",
                                                                   "Non è una foto leggibile da MoveEye (JPEG, PNG o WebP).",
                                                                   "Quai n’è nagina foto che MoveEye po leger (JPEG, PNG u WebP)."),
    "unsure": ("unsicher", "incertain", "incerto", "malsegir"),
    "Person": ("Person", "Personne", "Persona", "Persuna"),
    "Bird": ("Vogel", "Oiseau", "Uccello", "Utschè"), "Cat": ("Katze", "Chat", "Gatto", "Giat"), "Dog": ("Hund", "Chien", "Cane", "Chaun"),
    "Horse": ("Pferd", "Cheval", "Cavallo", "Chaval"), "Sheep": ("Schaf", "Mouton", "Pecora", "Nursa"), "Cow": ("Kuh", "Vache", "Mucca", "Vatga"),
    "Elephant": ("Elefant", "Éléphant", "Elefante", "Elefant"), "Bear": ("Bär", "Ours", "Orso", "Urs"), "Zebra": ("Zebra", "Zèbre", "Zebra", "Zebra"),
    "Giraffe": ("Giraffe", "Girafe", "Giraffa", "Giraffa"), "Animal": ("Tier", "Animal", "Animale", "Animal"),
    "Bicycle": ("Velo", "Vélo", "Bicicletta", "Velo"), "Car": ("Auto", "Voiture", "Auto", "Auto"), "Motorcycle": ("Motorrad", "Moto", "Moto", "Moto"),
    "Bus": ("Bus", "Bus", "Autobus", "Bus"), "Train": ("Zug", "Train", "Treno", "Tren"), "Truck": ("Lastwagen", "Camion", "Camion", "Camiun"),
    "Boat": ("Boot", "Bateau", "Barca", "Bartga"), "Vehicle": ("Fahrzeug", "Véhicule", "Veicolo", "Vehichel"),
    "Warm body": ("Warmer Körper", "Corps chaud", "Corpo caldo", "Corp chaud"),
    "Guest": ("Gast", "Invité", "Ospite", "Giast"),
}
for _k, _v in _HX_UNT.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
_UNT_DE = {_k: _v[0] for _k, _v in _HX_UNT.items()}
_UNT_DE.update({k: DE.get(k, k) for k in BIO_JS_KEYS + ("Head view", "Wide view", "Thermal view", "Cancel", "Close")})

# ---- the manual: a section «Untersuchen» after the file exchange ---------------------------------------------------------------------
_HELP_UNT = {
    "de": ('<section id="untersuchen" data-icon="🔍"><h2>Sofortbild untersuchen</h2><ul>'
           '<li><b>🔍 auf dem Live-Bild:</b> Sofortbild der gezeigten Ansicht (Kopf, Weitwinkel oder Wärmebild). Im Bild eine Stelle antippen oder einen Rahmen ziehen = nur dieser Bereich, sonst «Ganzes Bild». '
           'Mit dem Recht «Kopf steuern» kann der Kopf zuerst dorthin drehen («🎯 Zuerst den Kopf dorthin drehen»); ein optisches Zoom hat die Kamera nicht – der Bereich wird aus dem vollen Kamerabild ausgeschnitten.</li>'
           '<li><b>Was MoveEye findet:</b> Personen, Tiere und Fahrzeuge mit der KI, die Art (Pflanze, Tier, Pilz, Insekt) mit BioCLIP – Rahmen und Beschriftung über dem Bild; Beschriftung antippen = Artinfo-Karte wie im Datentausch. '
           'Auf dem <b>Wärmebild</b> nur Personen und Tiere (BioCLIP bestimmt keine Arten auf Wärmebildern). Das Ergebnis bleibt, bis du es schliesst.</li>'
           '<li><b>📷 Foto untersuchen:</b> ein Foto vom Handy hochladen, dieselbe Auswertung.</li>'
           '<li><b>Gespeichert</b> wird jedes Ergebnis automatisch im Datentausch, Ordner <b>«Funde»</b>: das Bild und eine JSON-Datei (Arten / Objekte, Zeit, Ort, falls bekannt).</li>'
           '<li><b>Gäste</b> mit dem Gast-Link können ein Sofortbild oder einen Ausschnitt untersuchen, den Kopf aber nie bewegen. Modelle (BioCLIP) lädt nur der Administrator. Immer nur eine Untersuchung gleichzeitig; alles rechnet auf dem Gerät.</li>'
           '<li>Im Fenster: «Mehr → 🔍 Untersuchen» (Kopf-Kamera, ganzes Bild, Ergebnis als Text).</li></ul></section>\n'),
    "en": ('<section id="untersuchen" data-icon="🔍"><h2>Examine a snapshot</h2><ul>'
           '<li><b>🔍 on the live picture:</b> a snapshot of the shown view (head, wide angle or thermal). Tap a spot or drag a box = only that region, else «Whole picture». '
           'With the right «steer the head» the head can turn there first («🎯 Turn the head there first»); the camera has no optical zoom – the region is cut from the full camera picture.</li>'
           '<li><b>What MoveEye finds:</b> persons, animals and vehicles with the AI, the species (plant, animal, fungus, insect) with BioCLIP – boxes and labels over the picture; tap a label = the species card as in the file exchange. '
           'On the <b>thermal picture</b> only persons and animals (BioCLIP does not identify species on thermal pictures). The result stays until you close it.</li>'
           '<li><b>📷 Examine a photo:</b> upload a photo from the phone, the same analysis.</li>'
           '<li>Every result is <b>saved</b> automatically in the file exchange, folder <b>«Funde»</b>: the picture and a JSON file (species / objects, time, place if known).</li>'
           '<li><b>Guests</b> with the guest link can examine a snapshot or a region but never move the head. Only the administrator loads models (BioCLIP). One examination at a time; everything runs on the device.</li>'
           '<li>In the window: «More → 🔍 Examine» (head camera, whole picture, result as text).</li></ul></section>\n'),
    "fr": ('<section id="untersuchen" data-icon="🔍"><h2>Examiner un instantané</h2><ul><li>🔍 sur l’image en direct : instantané de la vue (tête, grand angle, thermique), toucher un endroit ou tracer un cadre ; '
           'la tête peut d’abord tourner vers là (droit «tête»). Personnes, animaux, véhicules (IA) et espèce (BioCLIP) ; sur l’image thermique seulement personnes et animaux. '
           'Toucher l’étiquette = fiche de l’espèce. 📷 : examiner une photo du téléphone. Enregistré dans l’échange de fichiers, dossier «Funde». Invités : sans bouger la tête.</li></ul></section>\n'),
    "it": ('<section id="untersuchen" data-icon="🔍"><h2>Esaminare un’istantanea</h2><ul><li>🔍 sull’immagine dal vivo: istantanea della vista (testa, grandangolo, termica), tocca un punto o traccia un riquadro; '
           'la testa può prima girare lì (diritto «testa»). Persone, animali, veicoli (IA) e specie (BioCLIP); sull’immagine termica solo persone e animali. '
           'Tocca l’etichetta = scheda della specie. 📷: esaminare una foto del telefono. Salvato nello scambio di file, cartella «Funde». Ospiti: senza muovere la testa.</li></ul></section>\n'),
    "rm": ('<section id="untersuchen" data-icon="🔍"><h2>Examinar in maletg instantan</h2><ul><li>🔍 sin il maletg live: maletg instantan da la vista (chau, grond angul, termic), tutgar in lieu u trair in rom; '
           'il chau po l’emprim sa volver là (dretg «chau»). Persunas, animals, vehichels (IA) e spezia (BioCLIP); sin il maletg termic mo persunas ed animals. '
           'Tutgar l’etichetta = carta da la spezia. 📷: examinar ina foto dal telefonin. Memorisà en il barat da datotecas, ordinatur «Funde». Giasts: senza mover il chau.</li></ul></section>\n'),
}


def _help_unt(doc, lang):
    if 'id="untersuchen"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_UNT[lang] + doc[i:] if i >= 0 else doc


_hp_en_unt = HELP_PAGE.find('<div lang="en">')
if _hp_en_unt > 0:
    HELP_PAGE = _help_unt(HELP_PAGE[:_hp_en_unt], "de") + _help_unt(HELP_PAGE[_hp_en_unt:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_unt(HELP_X[_L], _L)


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def unt_selftest():
    assert unt_box(None) is None and unt_box([0, 0, 1, 1]) is None
    b = unt_box([0.5, 0.5])                                  # a tap: a square around the point
    assert b == [0.35, 0.35, 0.3, 0.3], b
    assert unt_box([0.9, 0.9, 0.5, 0.5]) == [0.5, 0.5, 0.5, 0.5] and unt_box(["x"]) is None
    assert unt_kind("person") == "person" and unt_kind("dog") == "animal" and unt_kind("truck") == "vehicle" and unt_kind("chair") == ""
    J = {"cam": "head", "src": "live", "box": [0.1, 0.1, 0.5, 0.5], "aimed": True,
         "found": [{"kind": "animal", "lab": "dog", "conf": 0.8, "box": [0.2, 0.2, 0.1, 0.1]}], "species": []}
    r = unt_result_json(J, (47.37, 8.54, "fixed"))
    assert r["location"] == {"lat": 47.37, "lon": 8.54, "source": "fixed"} and r["objects"][0]["label"] == "dog" and r["head_moved"]
    assert "/api/untersuchen" in PERM_POST["live"] and role_allows("kid", "/api/untersuchen", "POST", {}) and not role_allows("custom", "/api/untersuchen", "POST", {}, set())
    assert "<!--UNT-->/*UNT*/" in WEB_PAGE and "/*UNTG*/" in GUEST_PAGE and 'id="untersuchen"' in HELP_PAGE
    assert tr("Examine", "de") == "Untersuchen" and tr("Warm body", "fr") == "Corps chaud"
    return "region / tap, kinds, result JSON (place, objects), rights, page hooks, texts"


SELFTEST_EXTRA.append(("Examine a snapshot «🔍 Untersuchen» (639zze)", unt_selftest))
