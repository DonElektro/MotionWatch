#@ MoveEye – Teil 418: Feste Fehl-Personen lernen (ein Personen-Kasten, der sich über Minuten nicht bewegt = Gegenstand) und Tier vor Person (Spur-Klasse). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# real-erk-e1 (Erkennungstest 31.10.2026, Schwachstellen 2, 6, 7):
# 1) «Feste Fehl-Person»: the AI calls a small spruce on a stone base, a tree trunk in the infrared light ... a person, all the
#    time. The head turned after it (−30° → −71°) and a push «Person, ca. 2 m» came for a trunk. Now a person box of the AI that
#    does not move for minutes is remembered as a THING («spot», in degrees: it stays on its place when the head turns):
#    - it never walked there: no moving track (a person walking in) was at that place shortly before or when it appeared,
#    - it stands still: middle within FIX_STILL of its height, height within FIX_SIZE (a few jumps of the AI box are allowed),
#    - for FIX_LEARN_S (3 min) - or only FIX_LEARN_START_S when it was there already at the start (camera / scene new),
#    - it is not warm like a body (only with a thermal camera in °C).
#    A learned spot: its AI box and a person track standing on it are no person (no push, the head does not follow, drawn
#    grey «OBJECT?»). It is a person again at once when the box moves clearly or another person comes onto it. A card on
#    the Live / Schutz page shows the picture: «Hier steht etwas, das wie eine Person aussieht – ignorieren?» → a mask
#    (anchored ignore zone for persons, like «Platz einrichten») / «Ist eine Person» (never learnt there again) / «Später».
# 2) «Tier vor Person»: once the AI saw an animal (dog, cat, sheep, bird, cow, horse, bear …) on a track, the track keeps that
#    class: no person from the movement (also not «sticky» from before), no «Person?» and no thermal person on it. A new track
#    where an animal was a moment ago inherits it. Only the AI itself saying «person» over FIX_ANIMAL_AI_S (and no animal in
#    that time) makes it a person again («im Zweifel Person» when the AI is sure).
# Gegenprobe (Daniel): a person who walked in and then stands still for a long time is NEVER learnt (walked = for good).
# ----------------------------------------------------------------------------
FIX_LEARN_S = 180.0         # «über Minuten»: 3 min without moving. A visitor standing that long in front of a camera without
                            # having walked there (the case «walked» is never learnt) is very rare; a tree stands for ever.
FIX_LEARN_START_S = 45.0    # there already when the camera / scene started (MoveEye put up, «Einrichten»): the false persons of
                            # the test were there from the first picture; 45 s ≈ 20 AI runs at the 2 fps of the simulator.
FIX_START_WIN_S = 90.0      # «at the start»: a spot first seen in the first 90 s after the camera / scene started
FIX_HEAD_STILL_S = 2.0      # learn only while the head stood still 2 s (the planned servo position is ahead of the picture)
FIX_MATCH = 0.35            # the same spot: middle within 0.35 × its size (degrees) and height ratio 0.6 … 1.67 (the AI box
FIX_MATCH_H = 1.67          # of a tree jumps 10 … 25 % from run to run; a person 2 steps away is outside)
FIX_STILL = 0.25            # «stands still»: middle within 0.25 × its height of where it was first seen, height within FIX_SIZE
FIX_SIZE = 1.33             # (3 pictures in a row outside = it moved: the learning starts again)
FIX_GAP_S = 25.0            # not seen for 25 s while learning: forgotten (the AI misses a thing now and then, not for that long)
FIX_KEEP_S = 1800.0         # a learnt spot not seen for 30 min is forgotten (light changed, head somewhere else)
FIX_WALK_LOOK_S = 60.0      # «walked in»: a moving track at that place in the last 60 s before the spot appeared (or 5 s after) -
                            # the AI may find a person only after it stopped; a minute covers a slow AI and a short pause
FIX_WALK_AFTER_S = 5.0
FIX_ANIMAL_MEM_S = 4.0      # an animal of the AI is remembered 4 s on its place (the AI runs only now and then; a new track there inherits it)
FIX_ANIMAL_AI_S = 1.5       # an animal track becomes a person only when the AI says «person» on it for 1.5 s (≥ 2 runs) and no animal
FIXP = {"spots": [], "moving": deque(maxlen=1000), "animals": deque(maxlen=60), "start_t": 0.0, "head": None, "head_t": 0.0,
        "offers": [], "next": 1, "learned_n": 0, "suppressed": 0}


def fixp_reset(t0=None):
    """new camera / scene (410 reset_scene): the spots are forgotten (another picture), the start window begins again"""
    FIXP["spots"] = []; FIXP["moving"].clear(); FIXP["animals"].clear()
    FIXP["start_t"] = time.time() if t0 is None else t0


def _fixp_ang(b, pw, ph, head=None):
    """box in working pixels -> (azimuth, elevation, width, height) in degrees (the head position + the field of view)"""
    hf, vf = cam_fov()
    pa, ta = servo_pos_deg() if head is None else head
    x, y, w, h = [float(v) for v in b[:4]]
    return (pa + ((x + w / 2.0) / pw - 0.5) * hf, ta - ((y + h / 2.0) / ph - 0.5) * vf, max(0.05, w / pw * hf), max(0.05, h / ph * vf))


def _fixp_match(s, a):
    """a (angle box) is the same thing as the spot s"""
    sz = max(s["a"][2], s["a"][3])
    if math.hypot(a[0] - s["a"][0], a[1] - s["a"][1]) > FIX_MATCH * sz:
        return False
    r = a[3] / max(1e-6, s["a"][3])
    return 1.0 / FIX_MATCH_H <= r <= FIX_MATCH_H


def _fixp_ov(a, b):
    """overlap of two angle boxes (middle, size): intersection / smaller area"""
    ix = max(0.0, min(a[0] + a[2] / 2, b[0] + b[2] / 2) - max(a[0] - a[2] / 2, b[0] - b[2] / 2))
    iy = max(0.0, min(a[1] + a[3] / 2, b[1] + b[3] / 2) - max(a[1] - a[3] / 2, b[1] - b[3] / 2))
    return ix * iy / max(1e-9, min(a[2] * a[3], b[2] * b[3]))


def _fixp_walked(a, t_from, t_to):
    """a moving track (a person walking in) was at this place in the time window"""
    area = a[2] * a[3]
    return any(t_from <= m[0] <= t_to and _fixp_ov(a, m[1]) > 0.2 and m[1][2] * m[1][3] >= 0.2 * area for m in FIXP["moving"])


def _fixp_warm(b, pw, ph):
    """the box is warm like a body in the thermal picture (only a camera in °C; never for a tree) - then it is not learnt"""
    try:
        tt = _thermal_temps((b[0] / pw, b[1] / ph, b[2] / pw, b[3] / ph)) if THERMAL is not None else None
    except Exception:
        tt = None
    return bool(tt and tt[0] - tt[1] >= 3.0 and 25.0 <= tt[0] <= 42.0)


def fixp_spot_step(s, a, t0, start_t, walked, warm=False):
    """one observation a (angle box) of the spot s at t0 - the decision without the camera (self-test). Returns "learned" when
    the spot just became a thing, "moved" when a learned spot moved (a person again), else None."""
    if walked:
        s["walked"] = True                                   # walked in: for good never a thing
    if warm:
        s["warm"] = True
    s["last"] = t0; s["n"] += 1
    still = (math.hypot(a[0] - s["a0"][0], a[1] - s["a0"][1]) <= FIX_STILL * s["a0"][3]
             and 1.0 / FIX_SIZE <= a[3] / max(1e-6, s["a0"][3]) <= FIX_SIZE)
    s["out"] = 0 if still else s["out"] + 1
    s["a"] = tuple(0.8 * p + 0.2 * q for p, q in zip(s["a"], a))      # the AI box jitters: a slow average
    if s["out"] >= 3:                                        # it moved (not one jump of the AI box)
        was = s["learned"]
        s.update(a0=tuple(a), first=t0, out=0, learned=False, at_start=False)
        return "moved" if was else None
    need = FIX_LEARN_START_S if s["at_start"] else FIX_LEARN_S
    if not s["learned"] and not s["walked"] and not s["warm"] and not s["never"] and t0 - s["first"] >= need:
        s["learned"] = True
        return "learned"
    return None


def fixp_new_spot(a, t0, start_t):
    s = {"id": FIXP["next"], "a": tuple(a), "a0": tuple(a), "first": t0, "last": t0, "n": 0, "out": 0, "learned": False,
         "walked": False, "warm": False, "never": False, "at_start": t0 - start_t <= FIX_START_WIN_S, "offered": False}
    FIXP["next"] += 1
    return s


def fixp_filter_ai(ai_boxes, pw, ph, t0, small=None):
    """410, before the AI persons become tracks: learn the spots from the AI person boxes and drop the boxes on learnt spots.
    Returns the AI person boxes that stay persons."""
    if not FIXP["start_t"]:
        FIXP["start_t"] = t0
    head = servo_pos_deg()
    if FIXP["head"] is None or abs(head[0] - FIXP["head"][0]) > 0.3 or abs(head[1] - FIXP["head"][1]) > 0.3:
        FIXP["head"] = head; FIXP["head_t"] = t0
    still = t0 - FIXP["head_t"] >= FIX_HEAD_STILL_S and not manual_active()
    spots = FIXP["spots"]
    out = []
    for b in ai_boxes:
        a = _fixp_ang(b, pw, ph, head)
        s = next((s for s in spots if _fixp_match(s, a)), None)
        if s is None:
            for o in spots:                                  # a person box on a learnt spot that is not the thing itself:
                if o["learned"] and _fixp_ov(a, o["a"]) > 0.3 and _fixp_walked(a, t0 - 5.0, t0):   # another person came onto it
                    o.update(learned=False, first=t0, a0=o["a"], out=0, at_start=False)     # -> a person again
                    log_event("person", f"Still object #{o['id']}: a person comes onto it - a person again")
            if still and len(spots) < 12:
                s = fixp_new_spot(a, t0, FIXP["start_t"])
                s["walked"] = _fixp_walked(a, t0 - FIX_WALK_LOOK_S, t0)
                spots.append(s)
            out.append(b); continue
        if still or s["learned"]:
            walked = t0 - s["first"] <= FIX_WALK_AFTER_S and _fixp_walked(a, s["first"], t0)
            r = fixp_spot_step(s, a, t0, FIXP["start_t"], walked, _fixp_warm(b, pw, ph) if not s["learned"] else False) if still else None
            if r == "learned":
                FIXP["learned_n"] += 1
                log_event("person", f"Still object #{s['id']}: a «person» that has not moved for {int(t0 - s['first'])} s and did not walk "
                                    f"there - from now on a thing (no alarm, the head does not follow)")
                _fixp_offer(s, b, small, pw, ph, t0)
            elif r == "moved":
                log_event("person", f"Still object #{s['id']} moved - a person again")
        if s["learned"]:
            FIXP["suppressed"] += 1; continue
        out.append(b)
    FIXP["spots"] = [s for s in spots if t0 - s["last"] <= (FIX_KEEP_S if s["learned"] else FIX_GAP_S)]
    while FIXP["animals"] and t0 - FIXP["animals"][0][0] > FIX_ANIMAL_MEM_S:
        FIXP["animals"].popleft()
    while FIXP["moving"] and t0 - FIXP["moving"][0][0] > FIX_WALK_LOOK_S + FIX_WALK_AFTER_S:
        FIXP["moving"].popleft()
    return out


def fixp_head_still(t0):
    """seconds the head has stood still (set by fixp_filter_ai every picture; 232 uses it: no speed of warm bodies while it turns)"""
    return t0 - FIXP["head_t"] if FIXP["head"] is not None else 0.0


def fixp_track(t, pw, ph, t0):
    """410, after classify, for every track: remember moving tracks (a person walking in) and take the person away from a
    track that stands on a learnt spot (the AI box is gone, «sticky» kept it a person)"""
    head = FIXP["head"] or servo_pos_deg()
    still = t0 - FIXP["head_t"] >= FIX_HEAD_STILL_S
    learned = [s for s in FIXP["spots"] if s["learned"]]
    if t.lost:
        return
    x, y, w, h = t.box
    net = math.hypot(t.center()[0] - t.start[0], t.center()[1] - t.start[1])
    a = None
    if (still and len(t.hist) >= 3 and t0 - getattr(t, "_fx_t", 0.0) >= 0.4 and net >= max(10.0, 0.5 * max(w, h))
            and (t.is_person or t.steadiness() >= CFG["speed_consistency"])):
        a = _fixp_ang(t.box, pw, ph, head); t._fx_t = t0
        FIXP["moving"].append((t0, a))                   # goes somewhere (no branch swinging to and fro), 2-3 times a second
    sup = False
    if (t.is_person or getattr(t, "fixp", False)) and learned and net < max(10.0, 0.5 * max(w, h)):
        a = a or _fixp_ang(t.box, pw, ph, head)
        sup = any(_fixp_match(s, a) for s in learned)
    if sup:
        t.is_person = False                              # 410 classify: no person from the movement while fixp is set
    t.fixp = sup


def fixp_animal_note(boxes, pw, ph, t0):
    """the animals of the AI in this picture (x, y, w, h, conf, cls) -> remembered FIX_ANIMAL_MEM_S on their place"""
    for o in boxes:
        FIXP["animals"].append((t0, tuple(o[:4]), COCO_LABELS.get(o[5], "animal") if len(o) > 5 else "animal"))


def fixp_animal_of(box, t0, same=False):
    """an animal of the AI (now or a moment ago) lies on this box -> its class, else None. same = it must be the same thing
    (IoU > 0.5: for a track the AI calls a person - a dog walking next to its owner does not make the owner an animal)"""
    for tt, b, cls in reversed(FIXP["animals"]):
        if t0 - tt <= FIX_ANIMAL_MEM_S and (iou(box, b) > 0.5 if same else (iou(box, b) > 0.15 or _ov(box, b) > 0.5)):
            return cls
    return None


VEHICLE_LABELS = ("car", "truck", "bus", "motorcycle", "train")


def fixp_veto(tracks, ai_objs, pw, ph, t0):
    """for «Person?» and the thermal person (232): where the camera / AI sees an animal or a vehicle - boxes 0..1 with the kind
    [(x, y, w, h, "animal" | "vehicle")]"""
    out = [(b[0] / pw, b[1] / ph, b[2] / pw, b[3] / ph, "animal") for tt, b, _c in FIXP["animals"] if t0 - tt <= FIX_ANIMAL_MEM_S]
    for t in tracks:
        if t.lost or t.is_person:
            continue
        k = "animal" if getattr(t, "animal_like", False) else ("vehicle" if t.is_vehicle else None)
        if k:
            out.append((t.box[0] / pw, t.box[1] / ph, t.box[2] / pw, t.box[3] / ph, k))
    for o in ai_objs:
        if COCO_LABELS.get(o[5]) in VEHICLE_LABELS:
            out.append((o[0] / pw, o[1] / ph, o[2] / pw, o[3] / ph, "vehicle"))
    return out


def animal_track_decide(t, ai_person, animal_cls, t0):
    """Tier vor Person for one track (410 classify): -> True when the track is an animal (no person from movement / sticky).
    ai_person = the AI calls it a person now; animal_cls = an animal of the AI lies on it now (or a moment ago)."""
    if animal_cls:
        t.animal_like = True; t.animal_cls = animal_cls; t.animal_t = t0; t.ai_p_since = 0.0
    if not getattr(t, "animal_like", False):
        return False
    if ai_person and not animal_cls:
        if not getattr(t, "ai_p_since", 0.0):
            t.ai_p_since = t0
        if t0 - t.ai_p_since >= FIX_ANIMAL_AI_S:             # the AI says «person» on it again and again: a person after all
            t.animal_like = False; t.animal_cls = None
            return False
    elif not ai_person:
        t.ai_p_since = 0.0
    return True


def _fixp_offer(s, b, small, pw, ph, t0):
    """the card «Hier steht etwas, das wie eine Person aussieht – ignorieren?» with the picture of the spot"""
    if s["offered"] or any(o["sid"] == s["id"] for o in FIXP["offers"]):
        return
    s["offered"] = True
    jpg = None
    if small is not None:
        try:
            x, y, w, h = [int(v) for v in b[:4]]
            m = int(max(w, h) * 0.6) + 10
            x0, y0 = max(0, x - m), max(0, y - m); x1, y1 = min(small.shape[1], x + w + m), min(small.shape[0], y + h + m)
            crop = small[y0:y1, x0:x1].copy()
            cv2.rectangle(crop, (x - x0, y - y0), (x - x0 + w, y - y0 + h), (0, 200, 255), 2)
            if crop.shape[0] < 160:
                f_ = 160.0 / crop.shape[0]; crop = cv2.resize(crop, (int(crop.shape[1] * f_), 160))
            ok, buf = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 80])
            jpg = buf.tobytes() if ok else None
        except (cv2.error, ValueError):
            jpg = None
    FIXP["offers"].append({"id": uuid.uuid4().hex[:10], "sid": s["id"], "t": t0, "jpg": jpg, "state": ""})
    FIXP["offers"] = FIXP["offers"][-5:]


def fixp_state():
    now = time.time()
    return {"ok": True, "learned": sum(1 for s in FIXP["spots"] if s["learned"]), "learning": sum(1 for s in FIXP["spots"] if not s["learned"]),
            "offers": [{"id": o["id"], "age": int(now - o["t"]), "pic": bool(o["jpg"])} for o in FIXP["offers"]
                       if not o["state"] and any(s["id"] == o["sid"] and s["learned"] for s in FIXP["spots"])]}


def fixp_answer(oid, op):
    """«mask» = an anchored ignore zone for persons over the spot (stays when the head turns, editable in the zone editor),
    «person» = it is a person: never learnt there again, «later» = the card goes away (the spot stays a thing for now)"""
    o = next((o for o in FIXP["offers"] if o["id"] == oid), None)
    if o is None:
        return False, "gone"
    s = next((s for s in FIXP["spots"] if s["id"] == o["sid"]), None)
    o["state"] = op
    if op == "person":
        if s:
            s.update(learned=False, never=True)
        log_event("person", "Still object: «it is a person» - not learnt there again")
        return True, ""
    if op != "mask" or s is None:
        return True, ""
    if len(ZONES) >= MAX_ZONES:
        return False, "at most 12 zones"
    a, e, w, h = s["a"]
    mg = 1.0                                                 # 1° more on every side (the servo and the field of view are not exact)
    ang = [[a - w / 2 - mg, e + h / 2 + mg], [a + w / 2 + mg, e + h / 2 + mg], [a + w / 2 + mg, e - h / 2 - mg], [a - w / 2 - mg, e - h / 2 - mg]]
    pts = [[round(min(1.0, max(0.0, x)), 4), round(min(1.0, max(0.0, y)), 4)] for x, y in sleep_project(ang)[::8]]
    z = {"mode": "ignore", "kinds": "person", "name": "🌲 " + tr("Looks like a person"), "points": pts, "ang": ang,
         "anchor": True, "id": uuid.uuid4().hex[:8]}
    ok, err = zones_set([dict(z_) for z_ in ZONES] + [z])
    if ok:
        log_event("person", "Still object: taken as a mask (ignore zone for persons)")
    return ok, err


def fixp_draw(frame, sx, sy, pw, ph):
    """the learnt spots in the live picture: thin grey box «OBJECT?» (only those in the picture now)"""
    if not FIXP["spots"]:
        return
    hf, vf = cam_fov(); pa, ta = servo_pos_deg(); now = time.time()
    for s in FIXP["spots"]:
        if not s["learned"] or now - s["last"] > 3.0:
            continue
        a, e, w, h = s["a"]
        cx = ((a - pa) / hf + 0.5) * pw; cy = (0.5 - (e - ta) / vf) * ph; bw = w / hf * pw; bh = h / vf * ph
        x0, y0 = int((cx - bw / 2) * sx), int((cy - bh / 2) * sy); x1, y1 = int((cx + bw / 2) * sx), int((cy + bh / 2) * sy)
        cv2.rectangle(frame, (x0, y0), (x1, y1), (160, 160, 160), 1)
        cv2.putText(frame, "OBJECT? (ignored)", (x0, max(14, y0 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1, cv2.LINE_AA)


def fixp_routes(app, reply, body):
    """/api/fixp (state, answer) and /api/fixp/pic/<id> (the picture of the card) - called once by the web server (550)"""
    from flask import Response, g, request

    @app.route("/api/fixp", methods=["GET", "POST"])
    def api_fixp():
        if request.method == "GET":
            return reply(fixp_state())
        if getattr(g, "role", "admin") != "admin":
            return reply({"ok": False, "error": "not allowed"}, 403)
        d = body()
        op = str(d.get("op") or "")
        if op not in ("mask", "person", "later"):
            return reply({"ok": False, "error": "op"}, 400)
        ok, err = fixp_answer(str(d.get("id") or ""), op)
        return reply({"ok": ok, "error": tr(err) if err else None}, 200 if ok else 400)

    @app.route("/api/fixp/pic/<oid>")
    def api_fixp_pic(oid):
        o = next((o for o in FIXP["offers"] if o["id"] == oid and o["jpg"]), None)
        if o is None:
            return Response(b"", status=404)
        return Response(o["jpg"], mimetype="image/jpeg", headers={"Cache-Control": "no-store"})


# the card on the Live / Schutz page (main page 530); German texts by 639k
FIXP_MAIN_JS = r"""
<script>
(function () {
  try { const D = /*FXDE*/{}; for (const k in D) if (!(k in I18N.de)) I18N.de[k] = D[k]; } catch (e) {}
  const T = x => (typeof t === "function" ? t(x) : x);
  const E = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };
  const tab = () => document.body.getAttribute("data-tab") || "";
  let S = null;
  function show() {
    let o = document.getElementById("fx-offer");
    const f = S && S.offers && S.offers[0];
    const want = f && (tab() === "protect" || tab() === "live");
    if (!want) { if (o) o.remove(); return; }
    if (o && o.dataset.id === f.id) return;
    if (o) o.remove();
    o = E("div", "card"); o.id = "fx-offer"; o.dataset.id = f.id; o.style.cssText = "border:2px solid var(--acc);margin:0 0 12px";
    o.appendChild(E("b", "", "🌲 " + T("Something here looks like a person - ignore it?")));
    if (f.pic) { const im = E("img"); im.src = "/api/fixp/pic/" + f.id; im.alt = ""; im.style.cssText = "display:block;max-width:100%;max-height:220px;margin:8px 0;border-radius:8px"; o.appendChild(im); }
    o.appendChild(E("div", "mut", T("It has not moved for minutes. MoveEye treats it as a thing for now (no alarm, the head does not follow); a mask keeps it so.")));
    const r = E("div", "btns");
    const ans = async op => { try { await post("/api/fixp", {op: op, id: f.id}); } catch (e) {} o.remove(); if (op === "mask") toast("✓ " + T("Mask made")); };
    const a = E("button", "", T("Ignore (make a mask)")); a.type = "button"; a.onclick = () => ans("mask");
    const p = E("button", "sec", T("It is a person")); p.type = "button"; p.onclick = () => ans("person");
    const x = E("button", "sec", T("Later")); x.type = "button"; x.onclick = () => ans("later");
    r.append(a, p, x); o.appendChild(r);
    const m = document.querySelector("main"); if (m) m.prepend(o);
  }
  async function poll() {
    try { const r = await fetch("/api/fixp", {cache: "no-store"}); if (r.ok) S = await r.json(); } catch (e) {}
    try { show(); } catch (e) {}
    setTimeout(poll, 15000);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => setTimeout(poll, 900)); else setTimeout(poll, 900);
})();
</script>
"""
FIXP_MAIN_KEYS = ["Something here looks like a person - ignore it?",
                  "It has not moved for minutes. MoveEye treats it as a thing for now (no alarm, the head does not follow); a mask keeps it so.",
                  "Ignore (make a mask)", "It is a person", "Later", "Mask made"]


def fixp_main_js():
    return FIXP_MAIN_JS.replace("/*FXDE*/{}", json.dumps({k: DE.get(k, k) for k in FIXP_MAIN_KEYS}, ensure_ascii=False))


def fixp_selftest():
    """a spruce there from the start becomes a thing after 45 s, one appearing later after 3 min; a person who walked in and
    then stands still for 10 min never does; a learnt thing that moves is a person again; animal tracks keep their class"""
    # 1) the spruce: there from the start, the AI box jitters ±10 %
    s = fixp_new_spot((10.0, 2.0, 4.0, 9.0), 100.0, 100.0)
    res = []
    for i in range(1, 60):
        j = 0.1 * (1 if i % 2 else -1)
        res.append(fixp_spot_step(s, (10.0 + j, 2.0, 4.0, 9.0 * (1 + j)), 100.0 + i, 100.0, False))
    assert "learned" in res and res.index("learned") + 1 == int(FIX_LEARN_START_S), res.index("learned") if "learned" in res else res
    # 2) a thing that appears later (patrol looks there): only after FIX_LEARN_S
    s2 = fixp_new_spot((-20.0, 1.0, 3.0, 8.0), 1000.0, 100.0)
    assert not s2["at_start"]
    r2 = [fixp_spot_step(s2, (-20.0, 1.0, 3.0, 8.0), 1000.0 + i * 2, 100.0, False) for i in range(1, 100)]
    assert r2.index("learned") * 2 + 2 >= FIX_LEARN_S
    # 3) Gegenprobe: a person walked in, then stands still 10 min - never a thing (also at the start)
    s3 = fixp_new_spot((5.0, 0.0, 2.0, 7.0), 100.0, 100.0)
    r3 = [fixp_spot_step(s3, (5.0, 0.0, 2.0, 7.0), 100.0 + i, 100.0, i == 1) for i in range(1, 600)]
    assert "learned" not in r3 and s3["walked"]
    # 4) warm like a body (thermal camera in °C): never learnt
    s4 = fixp_new_spot((5.0, 0.0, 2.0, 7.0), 100.0, 100.0)
    assert "learned" not in [fixp_spot_step(s4, (5.0, 0.0, 2.0, 7.0), 100.0 + i, 100.0, False, i == 3) for i in range(1, 200)]
    # 5) the learnt spruce moves clearly (it was a person after all): a person again; one jump of the AI box is not enough
    assert fixp_spot_step(s, (13.0, 2.0, 4.0, 9.0), 200.0, 100.0, False) is None and s["learned"]
    assert fixp_spot_step(s, (10.0, 2.0, 4.0, 9.0), 201.0, 100.0, False) is None and s["learned"]
    out = [fixp_spot_step(s, (14.0, 2.0, 4.0, 9.0), 202.0 + i, 100.0, False) for i in range(3)]
    assert out[-1] == "moved" and not s["learned"]
    # 6) matching: same place / size yes, two steps away or half the height no
    sp = {"a": (0.0, 0.0, 3.0, 8.0)}
    assert _fixp_match(sp, (0.5, 0.3, 3.0, 8.5)) and not _fixp_match(sp, (5.0, 0.0, 3.0, 8.0)) and not _fixp_match(sp, (0.0, 0.0, 3.0, 4.0))

    # 7) Tier vor Person: a dog track stays an animal; the AI saying «person» once does not change it, 1.5 s of it does
    class _T:
        pass
    t = _T()
    assert animal_track_decide(t, False, None, 0.0) is False
    assert animal_track_decide(t, False, "dog", 1.0) is True
    assert animal_track_decide(t, False, None, 15.0) is True             # 14 s later, no animal in this picture: still the dog
    assert animal_track_decide(t, True, None, 15.5) is True              # the AI says «person» once
    assert animal_track_decide(t, True, "dog", 16.0) is True             # and dog again: the clock starts again
    assert animal_track_decide(t, True, None, 16.5) is True and animal_track_decide(t, True, None, 18.1) is False   # 1.6 s person: a person
    FIXP["animals"].clear()
    fixp_animal_note([(10, 10, 40, 20, 0.6, 18)], 320, 240, 50.0)
    assert fixp_animal_of((12, 12, 38, 22), 52.0) == "dog" and fixp_animal_of((12, 12, 38, 22), 60.0) is None
    assert fixp_animal_of((200, 100, 30, 60), 52.0) is None
    FIXP["animals"].clear()

    # 8) thermal picture (232): a car on 20 m (pieces) is a vehicle, walking / running persons stay persons
    hf, vf, asp = 66.0, 41.0, 9 / 16.0
    th, tv = math.tan(math.radians(hf) / 2.0), math.tan(math.radians(vf) / 2.0)

    def go(dist, height, width, speed, n=8, fps=4.0, start=0.2):
        TVEH.update(chains=[], veh=[], ts=0.0)
        h = height / (2.0 * dist * tv); w = width / (2.0 * dist * th); vx = speed / (2.0 * dist * th); r = []
        for i in range(n):
            ts = 500.0 + i / fps
            r = thermal_vehicle_step([(start + vx * (ts - 500.0), 0.5, w, h)], ts, hf, vf, asp)
        return bool(r)
    assert go(20.0, 0.6, 0.5, 8.3)                       # a tyre / grille piece of a car at 30 km/h
    assert go(20.0, 1.5, 4.5, 8.3)                       # the whole car, wide and (8-bit picture) hot
    assert go(20.0, 1.5, 4.5, 2.0, n=12) is False        # slowly parking: speed alone no vehicle (the AI / camera may say it)
    assert not go(10.0, 1.7, 0.5, 1.4) and not go(6.0, 1.75, 0.5, 5.0)     # walking and running persons
    assert not go(8.0, 0.85, 0.5, 4.0)                   # half hidden (only the upper half warm), running
    assert not go(10.0, 1.7, 1.2, 1.5)                   # two persons side by side
    TVEH.update(chains=[], veh=[], ts=0.0)
    return True


SELFTEST_EXTRA.append(("Still «person» = thing, a person who walked in stays one, animal before person (418)", fixp_selftest))
