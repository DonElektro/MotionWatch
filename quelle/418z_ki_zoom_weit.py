#@ MoveEye – Teil 418z: KI-Zoom für weite Bewegung (Reichweite im Wald). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# real-erk-e3 (31.10.2026, grosser Erkennungstest REAL_ERKENNUNG.md, Schwachstelle 8): im Schattwald fand MoveEye stehende /
# gehende Personen nur auf 5 von 15 Plätzen, nie über 10 m (offener Stellplatz: 13 von 14 bis 25 m). Drei Gründe im Code:
#   1. Die KI sah nur das kleine Arbeitsbild (proc_width, ab Werk 480 px). Das eigene YOLO-Modell (Eingang 640 px) bekam es
#      VERGRÖSSERT (480 -> 640: keine Einzelheit mehr), die «KI-Lupe» (2.98.13) schnitt ihre Kachel aus demselben 480-px-Bild.
#      Jetzt nehmen beide das Kamerabild selbst (Kopfkamera des Simulators 960 x 540, Camera Module 3 je nach Einstellung):
#      ai_view gibt dem YOLO-Modell das ganze Kamerabild (es verkleinert selbst auf seinen Eingang: 960 -> 640 = 1.33 x mehr
#      Pixel pro Person als vorher, gleiche Rechenzeit), die Lupe schneidet ihre Kachel aus dem Kamerabild (2 x mehr Pixel).
#      Das Standardmodell SSD (300 x 300) bekommt wie bisher das Arbeitsbild (mehr Pixel bringen ihm nichts), aber auch seine
#      Lupe-Kachel aus dem Kamerabild.
#   2. Eine Person ab ~12 m bewegt im Wald (Stämme, Schatten) nur kleine Flecken, kleiner als die Mindestfläche einer Spur
#      (min_area, mit Empfindlichkeit / Wind): keine Spur -> kein Hinweis -> keine Lupe. Jetzt ist auch kleine Bewegung ein
#      Hinweis («weit»), wenn sie am selben Ort wiederkommt (ZOOM_FAR_N in ZOOM_FAR_S) und noch kein KI-Kasten dort ist.
#   3. Die Lupe nahm immer den GRÖSSTEN Hinweis - im Wald mit Wind ist das fast immer ein Ast. Jetzt kommen die Hinweise der
#      Reihe nach dran (der am längsten nicht angeschaute zuerst), ein offener Treffer (Bestätigung) hat Vorrang.
# Gegen Fehlalarme (leerer Wald mit Wind): eine Person der Lupe auf einem «weiten» Hinweis (ohne Spur) zählt erst, wenn ein
# zweiter Lupe-Lauf sie am selben Ort wieder findet (ZOOM_CONFIRM_S), und nur aufrecht (ZOOM_UPRIGHT, weit weg geht oder steht
# eine Person); bei starkem Wind / Sturm (Wind-Messung 190) gibt es keine «weiten» Hinweise (da bewegt sich alles - so viel wie
# vorher, nicht weniger: vorher gab es sie gar nicht). Hinweise aus Spuren zählen wie bisher sofort.
# Leistung (Pi 5): weiterhin höchstens EIN zusätzlicher KI-Lauf pro KI-Lauf, nur wenn es einen Hinweis gibt; «weite» Hinweise
# nur bei jedem ZOOM_FAR_EVERY-ten KI-Lauf. Mit dem YOLO-Modell kommen bis zu 4 Kacheln in EINEN Lauf (2 x 2, je 320 px).
# Der Takt der KI (180: Pause = 2 x Laufzeit, heiss / Akku langsamer) enthält die Lupe, die Kamera-Schleife bleibt geschützt.
#
# Grössere KI-Eingabe (960 px) geprüft - NICHT eingebaut, nur der Zoom:
#   - Das ONNX-Modell hat einen festen Eingang (ki_training/trainieren.py: export dynamic=False, imgsz 320; Testmodell 640).
#     960 px hiesse ein eigenes Modell, das mit --imgsz 960 trainiert / exportiert wird (Einstellung gäbe es dafür keine).
#   - Rechenzeit: YOLOv8n 8.7 GFLOPs bei 640 px, bei 960 px 2.25 x so viel (19.6). Gemessen mit OpenCV-DNN (cv2 5.0, wie am
#     Pi): 640 px 325 ms auf diesem Entwicklungsrechner (2 Kerne, Last ~5). Ultralytics «Raspberry Pi 5» Benchmark YOLOv8n
#     640 px ONNX ~120-130 ms (onnxruntime, 4 Kerne); OpenCV-DNN ist erfahrungsgemäss 1.5-2 x langsamer -> Pi 5 ~200-250 ms
#     bei 640, ~450-560 ms bei 960. Die KI läuft in der Kamera-Schleife: ein Lauf von 0.5 s hält das Bild eine halbe Sekunde
#     an - bei 10-15 Bildern/s (66-100 ms pro Bild) fehlen dann 5-8 Bilder pro KI-Lauf, die Bewegungs-Erkennung (Spuren,
#     Voralarm) leidet. Darum: kein 960-Modell, sondern die Lupe mit den echten Kamera-Pixeln (Kachel 110 px Arbeitsbild =
#     220 px Kamerabild -> 640 px Eingang: 2.9 x vergrössert, wie ein 1800-px-Modell an dieser Stelle).
# Schalter: der bestehende «KI-Lupe» (ai_zoom, KI-Erkennung) - kein neuer Regler. Selbsttest: zoom_selftest.
# ----------------------------------------------------------------------------
ZOOM_FAR_MIN = 0.00025   # kleinste Bewegung als Hinweis (Anteil am Arbeitsbild; 480 x 270: 32 px², z. B. 4 x 8 px). Eine
                         # Person auf 25 m ist mit der Kopfkamera (41° hoch) ~24 x 7 px gross; Rauschen einzelner Pixel ist kleiner.
ZOOM_FAR_N, ZOOM_FAR_S = 3, 2.0    # «kommt am selben Ort wieder»: 3 Bilder mit Bewegung in derselben Zelle in 2 s (bei 2 Bildern/s
                         # im Simulator 3 von 4 Bildern; ein einzelnes Flackern / Rauschen kommt nicht 3 x an denselben Ort)
ZOOM_GRID = (16, 9)      # Zellen des Arbeitsbilds für «am selben Ort» (480 x 270: 30 x 30 px = auf 20 m etwa 1.5 m)
ZOOM_FAR_MAX = 8         # höchstens so viele «weite» Hinweise auf einmal (Wind: viele - es kommen ohnehin nur 4 pro Lauf dran)
ZOOM_FAR_EVERY = 2       # «weite» Hinweise nur bei jedem 2. KI-Lauf: höchstens +50 % KI-Zeit im Mittel (Hinweise aus Spuren wie bisher)
ZOOM_CONFIRM_S = 5.0     # ein Lupe-Treffer auf einem «weiten» Hinweis zählt erst, wenn ein zweiter Lauf ihn in 5 s am selben Ort findet
                         # (eine gehende Person auf 20 m legt in 5 s ~7 m zurück = ~100 px - darum «am selben Ort» grosszügig, s. unten)
ZOOM_UPRIGHT = 1.2       # weit weg: nur ein aufrechter Kasten (Höhe >= 1.2 x Breite) - gehend ~2.5, stehend ~3.5; Äste / Büsche quer
ZOOM_TILES_YOLO = 4      # mit dem eigenen YOLO-Modell: bis 4 Kacheln in einem Lauf (2 x 2), mit SSD (300 px) nur eine
ZOOM = {"seen": {}, "far": [], "looked": {}, "pend": [], "runs": 0, "far_hits": 0, "pend_n": 0}


def ai_view(ai, frame):
    """(picture for the main AI run, scale picture / working picture): the own YOLO model gets the camera picture itself when it
    is bigger than the working picture (it letterboxes to its input anyway), SSD the working picture as before"""
    full = getattr(ai, "full", None)
    if ai.kind != "yolo" or full is None or full.shape[1] <= frame.shape[1]:
        return frame, 1.0
    return full, full.shape[1] / float(frame.shape[1])


def ai_unscale(boxes, k, n=4):
    """boxes of the camera picture back into the working picture (the first n values are x, y, w, h)"""
    if k == 1.0:
        return boxes
    return [tuple(int(round(v / k)) if i < 4 else v for i, v in enumerate(b)) for b in boxes]


def _zcell(b, pw, ph):
    return (int((b[0] + b[2] / 2.0) * ZOOM_GRID[0] / max(1, pw)), int((b[1] + b[3] / 2.0) * ZOOM_GRID[1] / max(1, ph)))


def zoom_far_feed(ai, boxes, small_area, tracks, pw, ph, t0, wind_level="calm"):
    """410, every picture: movement boxes (x, y, w, h of the working picture) smaller than a track that come back at the same
    place become «far» hints of the Lupe (ai.far). Not in strong wind / storm, not where a track or an AI box already is."""
    seen = ZOOM["seen"]
    if wind_level in ("strong", "storm"):
        seen.clear(); ai.far = []; return []
    amin = ZOOM_FAR_MIN * pw * ph
    taken = [t.box for t in tracks if not getattr(t, "lost", 0)] + [b[:4] for b in getattr(ai, "boxes", []) or []]
    for b in boxes:
        a = b[2] * b[3]
        if a < amin or a >= small_area or any(iou(b, tb) > 0.05 for tb in taken):
            continue
        c = _zcell(b, pw, ph)
        dq = seen.get(c)
        if dq is None:
            dq = seen[c] = deque(maxlen=12)
        dq.append((t0, tuple(int(v) for v in b[:4])))
    for c in list(seen):
        dq = seen[c]
        while dq and t0 - dq[0][0] > ZOOM_FAR_S:
            dq.popleft()
        if not dq:
            del seen[c]
    # a cell and its 8 neighbours together (a far person walks from cell to cell: ~25 px/s at 20 m, a cell is 30 px);
    # the strongest place first, its neighbours are then the same place
    tot = {c: sum(len(seen.get((c[0] + dx, c[1] + dy), ())) for dx in (-1, 0, 1) for dy in (-1, 0, 1)) for c in seen}
    out, used = [], []
    for c in sorted(tot, key=lambda c: (-tot[c], -seen[c][-1][0])):
        if tot[c] < ZOOM_FAR_N or any(abs(c[0] - u[0]) <= 1 and abs(c[1] - u[1]) <= 1 for u in used):
            continue
        used.append(c); out.append((tot[c], seen[c][-1][1]))
    ai.far = [b for _n, b in sorted(out, key=lambda o: -o[0])[:ZOOM_FAR_MAX]]
    return ai.far


def zoom_pick(track_hints, far_hints, boxes, now, k_max, far_ok):
    """the hints for this Lupe run: [(box, kind)] - open far hits (to confirm) first, then the track hints (biggest first, as
    before), then the far hints, each in turn by «looked at longest ago»; never where the AI already has a person box"""
    cand = []
    ZOOM["pend"] = [p for p in ZOOM["pend"] if now - p[0] <= ZOOM_CONFIRM_S]
    for p in ZOOM["pend"]:
        cand.append((p[1], "far"))
    for hb in sorted(track_hints, key=lambda b: -b[2] * b[3]):
        cand.append((tuple(hb[:4]), "track"))
    if far_ok:
        lk = ZOOM["looked"]
        for hb in sorted(far_hints, key=lambda b: lk.get((b[0] // 24, b[1] // 24), 0.0)):
            cand.append((tuple(hb[:4]), "far"))
    out = []
    for hb, kind in cand:
        if any(iou(hb, b[:4]) > 0.1 for b in boxes) or any(iou(hb, o[0]) > 0.3 for o in out):
            continue
        out.append((hb, kind))
        if len(out) >= k_max:
            break
    for hb, kind in out:
        ZOOM["looked"][(hb[0] // 24, hb[1] // 24)] = now
    if len(ZOOM["looked"]) > 400:
        ZOOM["looked"] = {k: v for k, v in ZOOM["looked"].items() if now - v < 30.0}
    return out


def zoom_tile(hb, w, h):
    """the square tile (x0, y0, side) around a hint in the working picture (w x h): 3.2 x its height, at least 110 px (2.98.13)"""
    side = int(min(min(w, h), max(110, 3.2 * hb[3])))
    cx, cy = hb[0] + hb[2] // 2, hb[1] + hb[3] // 2
    return max(0, min(w - side, cx - side // 2)), max(0, min(h - side, cy - side // 2)), side


def zoom_accept(bx, kind, now, side, wh):
    """a person box of the Lupe (working picture): True = counts now. Track hints at once (as before); far hints only upright
    and when a second run finds it at the same place (the first hit waits in ZOOM["pend"] and is looked at first next time)"""
    if bx[3] >= 0.6 * side and side > 0.8 * wh:
        return False                                     # the whole tile as one «person»: not trusted (2.98.13)
    if kind != "far":
        return True
    if bx[3] < ZOOM_UPRIGHT * bx[2]:
        return False
    cx, cy = bx[0] + bx[2] / 2.0, bx[1] + bx[3] / 2.0
    for p in ZOOM["pend"]:
        q = p[2]
        if now - p[0] <= ZOOM_CONFIRM_S and now - p[0] > 0.05 and abs(cx - (q[0] + q[2] / 2.0)) < max(side * 0.6, 3 * q[2]) \
                and abs(cy - (q[1] + q[3] / 2.0)) < max(side * 0.4, q[3]):
            ZOOM["pend"].remove(p)
            ZOOM["far_hits"] += 1
            return True
    ZOOM["pend"].append((now, (int(cx - side / 2), int(cy - side / 2), side, side), tuple(bx[:4])))
    ZOOM["pend_n"] += 1
    return False


def ai_zoom_run(ai, frame, boxes, w, h, now=None):
    """the «KI-Lupe» (2.98.13, extended real-erk-e3): look at the hints once more, enlarged, with the pixels of the camera
    picture. Adds the persons found to boxes (working picture) and returns boxes."""
    if not CFG.get("ai_zoom", True):
        return boxes
    now = time.time() if now is None else now
    ZOOM["runs"] += 1
    full = getattr(ai, "full", None)
    if full is None or full.shape[1] < w:
        full = frame
    k = full.shape[1] / float(w)
    yolo = ai.kind == "yolo"
    picks = zoom_pick(getattr(ai, "hints", []) or [], getattr(ai, "far", []) or [], boxes, now,
                      ZOOM_TILES_YOLO if yolo else 1, ZOOM["runs"] % ZOOM_FAR_EVERY == 0 or bool(ZOOM["pend"]))
    if not picks:
        return boxes
    tiles = []
    for hb, kind in picks:
        x0, y0, side = zoom_tile(hb, w, h)
        fx0, fy0, fs = int(x0 * k), int(y0 * k), int(side * k)
        crop = full[fy0:fy0 + fs, fx0:fx0 + fs]
        if crop.size:
            tiles.append((x0, y0, side, crop, kind))
    if not tiles:
        return boxes
    found = []                                           # (x, y, w, h, conf) of the working picture, kind, side
    if yolo and len(tiles) > 1:                          # 2 x 2 in one run: each tile 320 px of the 640 px input
        n = int(ai.meta["input"]); q = n // 2
        mos = np.full((n, n, 3), 114, np.uint8)
        for i, (x0, y0, side, crop, kind) in enumerate(tiles):
            mos[(i // 2) * q:(i // 2) * q + q, (i % 2) * q:(i % 2) * q + q] = cv2.resize(crop, (q, q), interpolation=cv2.INTER_LINEAR)
        for a1, b1, bw, bh, conf in ai.infer(mos, CFG["ai_conf"], 2.0)[0]:      # only persons
            i = int(b1 + bh / 2.0) // q * 2 + int(a1 + bw / 2.0) // q
            if i >= len(tiles):
                continue
            ox, oy = (i % 2) * q, (i // 2) * q
            if a1 < ox - 4 or b1 < oy - 4 or a1 + bw > ox + q + 4 or b1 + bh > oy + q + 4:
                continue                                 # crosses the border of its tile: half of two pictures
            x0, y0, side, _c, kind = tiles[i]
            s = side / float(q)
            found.append(((x0 + (a1 - ox) * s, y0 + (b1 - oy) * s, max(1, bw * s), max(1, bh * s), conf), kind, side))
    else:
        for x0, y0, side, crop, kind in tiles:
            s = side / float(crop.shape[1])
            for a1, b1, bw, bh, conf in ai.infer(crop, CFG["ai_conf"], 2.0)[0]:
                found.append(((x0 + a1 * s, y0 + b1 * s, max(1, bw * s), max(1, bh * s), conf), kind, side))
    for bx, kind, side in found:
        bx = (int(bx[0]), int(bx[1]), max(1, int(bx[2])), max(1, int(bx[3])), bx[4])
        if any(iou(bx[:4], b[:4]) > 0.3 for b in boxes):
            continue
        if zoom_accept(bx, kind, now, side, min(w, h)):
            boxes.append(bx); STATE["ai_zoom_hits"] = STATE.get("ai_zoom_hits", 0) + 1
    STATE["ai_zoom"] = {"tiles": len(tiles), "far": len(getattr(ai, "far", []) or []), "far_hits": ZOOM["far_hits"], "open": len(ZOOM["pend"])}
    return boxes


def zoom_selftest():
    """far hints (small movement that comes back), their order, the confirmation of far hits and the 2 x 2 tiles"""
    class _T:
        def __init__(self, b):
            self.box = b; self.lost = 0

    class _AI:
        kind = "yolo"; meta = {"input": 640}; boxes = []; hints = []; far = []; full = None

        def __init__(self, hits):
            self.hits = hits; self.calls = []

        def infer(self, img, cp, co):
            self.calls.append(img.shape)
            return list(self.hits), []
    try:
        ZOOM.update(seen={}, far=[], looked={}, pend=[], runs=0, far_hits=0, pend_n=0)
        ai = _AI([])
        pw, ph = 480, 270
        for i in range(3):                                # a small thing (10 x 24 px) three times at the same place
            zoom_far_feed(ai, [(300 + i, 100, 10, 24)], 1125, [], pw, ph, 10.0 + 0.5 * i)
        assert len(ai.far) == 1, ai.far
        assert zoom_far_feed(ai, [(300, 100, 10, 24)], 1125, [], pw, ph, 11.5, "strong") == []     # strong wind: no far hints
        ZOOM["seen"].clear(); ai.far = []
        zoom_far_feed(ai, [(50, 50, 10, 24)], 1125, [], pw, ph, 20.0)
        assert ai.far == []                               # once only: no hint
        for i in range(3):                                # under a track: no far hint (the track is a hint itself)
            zoom_far_feed(ai, [(200, 150, 10, 24)], 1125, [_T((195, 145, 30, 40))], pw, ph, 30.0 + 0.3 * i)
        assert ai.far == [], ai.far
        for i in range(3):                                # big enough for a track: not a far hint
            zoom_far_feed(ai, [(100, 100, 40, 60)], 1125, [], pw, ph, 40.0 + 0.3 * i)
        assert ai.far == []
        # order: the far hint looked at longest ago comes first
        ZOOM["looked"] = {(10, 4): 5.0, (2, 4): 1.0}
        p = zoom_pick([], [(240, 100, 10, 24), (48, 100, 10, 24)], [], 50.0, 1, True)
        assert p and p[0][0][0] == 48, p
        assert zoom_pick([], [(240, 100, 10, 24)], [], 50.0, 1, False) == []           # not this run (every 2nd)
        assert zoom_pick([], [(240, 100, 10, 24)], [(238, 95, 16, 34, 0.9)], 50.0, 1, True) == []   # the AI has it already
        # confirmation: a far hit counts only the second time at about the same place, and only upright
        ZOOM["pend"] = []
        assert not zoom_accept((300, 100, 10, 26, 0.6), "far", 60.0, 110, 270)
        assert len(ZOOM["pend"]) == 1
        assert zoom_pick([], [], [], 61.0, 1, False)[0][1] == "far"                   # the open hit is looked at again first
        assert zoom_accept((306, 101, 10, 25, 0.6), "far", 61.0, 110, 270)            # second run, a few px on: counts
        assert not zoom_accept((300, 100, 30, 12, 0.7), "far", 62.0, 110, 270)        # lying / a branch across: never
        assert zoom_accept((300, 100, 30, 12, 0.7), "track", 62.0, 110, 270)          # track hints as before: at once
        assert not zoom_accept((0, 0, 200, 250, 0.9), "track", 62.0, 260, 270)        # the whole tile: not trusted
        ZOOM["pend"] = []
        assert not zoom_accept((300, 100, 10, 26, 0.6), "far", 70.0, 110, 270)
        assert not zoom_accept((300, 100, 10, 26, 0.6), "far", 76.0, 110, 270)        # 6 s later: too late, a new first hit
        # 2 x 2 tiles in one run (YOLO), boxes back in the working picture; camera picture 2 x bigger
        ZOOM.update(pend=[], looked={}, runs=1)
        frame = np.zeros((270, 480, 3), np.uint8); full = np.zeros((540, 960, 3), np.uint8)
        ai = _AI([(320 + 100, 50, 20, 60, 0.8)])           # a person in the 2nd tile (top right), 320 px tile
        ai.full = full; ai.hints = [(40, 40, 10, 24), (300, 120, 10, 24)]
        out = ai_zoom_run(ai, frame, [], 480, 270, 80.0)
        assert ai.calls == [(640, 640, 3)], ai.calls       # one run for both tiles
        assert len(out) == 1 and 250 < out[0][0] + out[0][2] / 2 < 360 and out[0][3] < 40, out
        ai = _AI([(5, 5, 30, 300, 0.8)])                   # one tile alone: the crop itself, from the camera picture (220 px)
        ai.full = full; ai.hints = [(40, 40, 10, 24)]
        ZOOM.update(pend=[], looked={})
        ai_zoom_run(ai, frame, [], 480, 270, 90.0)
        assert ai.calls == [(220, 220, 3)], ai.calls
        assert ai_unscale([(100, 50, 20, 40, 0.7)], 2.0) == [(50, 25, 10, 20, 0.7)]
        v, k = ai_view(ai, frame)
        assert v is full and k == 2.0
        ai.kind = "ssd"
        assert ai_view(ai, frame)[0] is frame              # SSD: the working picture as before
    finally:
        ZOOM.update(seen={}, far=[], looked={}, pend=[], runs=0, far_hits=0, pend_n=0)
    return True


SELFTEST_EXTRA.append(("AI magnifier: far movement, camera pixels, 2 x 2 tiles (418z)", zoom_selftest))
