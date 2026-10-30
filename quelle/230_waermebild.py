#@ Motion Watch – Teil 230: Wärmebild-Überlagerung, Nachtsicht, Easter Egg (Herz). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Thermal camera: a second camera with the same view. Its picture is coloured and laid over the normal picture
# (blend, or "hot mode": only the warmest areas are shown). Detection always works on the normal picture.
# ----------------------------------------------------------------------------
class ThermalCam:
    """Keeps the chosen thermal source open in the background and always holds its newest picture."""
    def __init__(self):
        self.src = None; self.spec = ""; self.frame = None; self.t = 0.0; self.fails = 0
        self.retry_at = 0.0; self.opening = False; self.cache = (None, None)
        self.bgsub = None; self.bg_shape = None; self.hits = deque(maxlen=5); self.det_t = 0.0; self.boxes = []; self.lo = self.hi = None
        threading.Thread(target=self.loop, daemon=True).start()

    def wanted(self):
        spec = CFG["thermal_source"] if (CFG["thermal_on"] or CFG["thermal_alarm"] or CFG["nightvision"] or CFG["nightvision_auto"]
                                         or thermal_person_active()) else ""
        if spec and spec == STATE["source_id"]:
            return ""                                          # that camera is the main camera already
        return spec

    def _close(self):
        src, self.src, self.frame = self.src, None, None
        if src is not None:
            src.release()

    def _open(self, spec):
        self.opening = True
        try:
            res = open_source(spec, thermal=True)
            if res[0] is None:
                STATE["thermal"] = "no picture: " + res[3]
                log_event("sys", f"Thermal camera '{res[2]}' not available: {res[3]}")
                self.retry_at = time.time() + 5.0
            elif self.wanted() != spec:
                res[0].release()
            else:
                self.src = res[0]; self.spec = spec; self.fails = 0
                size = getattr(res[0], "size", None)
                STATE["thermal_res"] = f"{size[0]}x{size[1]}" if size else ""
                log_event("sys", f"Thermal camera: {res[2]}" + (f" ({STATE['thermal_res']})" if size else ""))
        finally:
            self.opening = False

    def loop(self):
        while True:
            try:
                want = self.wanted()
                if self.src is not None and (want != self.spec):
                    self._close()
                if self.src is None:
                    if not want:
                        STATE["thermal"] = "off" if not (CFG["thermal_on"] or CFG["thermal_alarm"]) else ("same camera as the main picture" if CFG["thermal_source"] else "no thermal camera selected")
                        time.sleep(0.5); continue
                    if time.time() >= self.retry_at and not self.opening:
                        STATE["thermal"] = "connecting…"
                        self._open(want)
                    else:
                        time.sleep(0.3)
                    continue
                ok, fr = self.src.read()
                w_ = WATCH_REF["w"]
                if w_ is not None and w_.eco_slow:
                    time.sleep(max(0.0, 1.0 / max(1.0, float(CFG["eco_fps"])) - 0.05))     # power saving
                if ok and fr is not None:
                    self.frame = fr; self.t = time.time(); self.fails = 0
                    STATE["thermal"] = "connected"
                else:
                    self.fails += 1
                    if self.fails >= 30:
                        STATE["thermal"] = "connection lost - reconnecting"
                        self._close(); self.retry_at = time.time() + 3.0
                    time.sleep(0.05)
            except Exception as e:
                STATE["thermal"] = "error: " + str(e)[:80]
                self._close(); self.retry_at = time.time() + 5.0; time.sleep(1.0)

    main_aspect = 9 / 16.0                           # height / width of the camera picture (set by the overlay)

    @classmethod
    def crop(cls, fr):
        """The part of the (wider) thermal picture that the normal camera sees: zoom + shift (thermal camera settings)."""
        g = cls.sim_geom()
        if g is not None:                            # 2.95.88: simulator - fit by the field of view of both cameras
            return cls.fit(fr, *g)
        z = max(0.3, min(1.0, float(CFG["thermal_zoom"]) / 100.0))
        dx, dy = float(CFG["thermal_dx"]) / 100.0, float(CFG["thermal_dy"]) / 100.0
        if z >= 0.999 and not dx and not dy:
            return fr
        H, W = fr.shape[:2]
        w = W * z; h = min(float(H), w * cls.main_aspect)
        x0 = max(0.0, min(W - w, W * (0.5 + dx) - w / 2)); y0 = max(0.0, min(H - h, H * (0.5 - dy) - h / 2))
        out = fr[int(round(y0)):int(round(y0 + h)), int(round(x0)):int(round(x0 + w))]
        return out if out.size else fr

    @staticmethod
    def sim_geom():
        """In the simulation the field of view of the head camera and of the thermal camera is known (/info): which part
        of the main picture the thermal picture covers (fx, fy; < 1 = it covers less, it is put in the middle). None outside."""
        try:
            if not (CFG.get("sim_on") and str(CFG["thermal_source"]) == "sim:thermal" and str(CFG["source"]).startswith("sim:")):
                return None
            info = SIM.get("info") or {}
            th = info.get("thermal") or {}
            cam = next((c for c in info.get("cameras") or [] if str(c.get("id")) == str(CFG["source"])[4:]), None)
            if not th or not cam or not (th.get("on_head") and cam.get("on_head")):
                return None
            if CFG.get("thermal_align_own"):
                return None                              # 557: the assistant «Wärmebild ausrichten» measured it (zoom / shift)
            fx = math.tan(math.radians(float(th["fov_h"])) / 2) / math.tan(math.radians(float(cam["fov_h"])) / 2)
            fy = fx * (float(th["h"]) / float(th["w"])) / (float(cam["h"]) / float(cam["w"]))
            if th.get("fov_v") and cam.get("fov_v"):     # 557: Thermal-90 has 90° × 67° (the pixels are not square)
                fy = math.tan(math.radians(float(th["fov_v"])) / 2) / math.tan(math.radians(float(cam["fov_v"])) / 2)
            return fx, fy
        except (KeyError, ValueError, TypeError, ZeroDivisionError):
            return None

    @staticmethod
    def fit(fr, fx, fy):
        """The thermal picture as the field of the main picture: bigger field = cut out the middle, smaller = put it in the middle
        and fill the rest with the median (no picture there, so no warm edges)."""
        H, W = fr.shape[:2]
        oW, oH = max(2, int(round(W / fx))), max(2, int(round(H / fy)))
        x0, y0 = (oW - W) // 2, (oH - H) // 2
        fill = np.median(fr.reshape(H * W, -1), axis=0).astype(fr.dtype)
        out = np.empty((oH, oW) + fr.shape[2:], fr.dtype); out[...] = fill
        sx0, sy0 = max(0, -x0), max(0, -y0)
        dx0, dy0 = max(0, x0), max(0, y0)
        w, h = min(W - sx0, oW - dx0), min(H - sy0, oH - dy0)
        out[dy0:dy0 + h, dx0:dx0 + w] = fr[sy0:sy0 + h, sx0:sx0 + w]
        return out

    @staticmethod
    def to_gray8(fr):
        """Any thermal frame -> 8 bit intensity (hot = bright) with the contrast stretched to what is in the picture."""
        if fr.ndim == 3:
            if fr.shape[2] == 1:
                fr = fr[:, :, 0]
            else:
                fr = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY) if fr.dtype == np.uint8 else fr.mean(axis=2)
        f = fr.astype(np.float32)
        small = f[::max(1, f.shape[0] // 60), ::max(1, f.shape[1] // 80)]
        lo, hi = np.percentile(small, (1, 99))
        if hi - lo < 1e-3:
            return np.zeros(f.shape, np.uint8)
        return np.clip((f - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)

    @staticmethod
    def is_plain_gray(fr):
        if fr.ndim == 2 or fr.shape[2] == 1:
            return True
        if fr.dtype != np.uint8:
            return True
        s = fr[::8, ::8].astype(np.int16)
        return int(np.abs(s[:, :, 0] - s[:, :, 1]).max()) < 6 and int(np.abs(s[:, :, 1] - s[:, :, 2]).max()) < 6

    def color(self, fr):
        """-> (colour picture, intensity). A camera that already delivers false colours keeps its own colours."""
        gray = self.to_gray8(fr)
        cmap = THERMAL_MAPS.get(CFG["thermal_map"], cv2.COLORMAP_INFERNO)
        if self.is_plain_gray(fr):
            col = cv2.applyColorMap(gray, cmap) if cmap is not None else cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        else:
            col = fr if fr.dtype == np.uint8 and fr.ndim == 3 and fr.shape[2] == 3 else cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return col, gray

    def detect(self):
        """Warm bodies in the thermal picture: clearly warmer than the scene (thermal_delta), moving (unless switched off,
        so sun-warmed stones or an engine do not alarm), big enough, inside the zones, seen in 3 of the last 5 pictures."""
        fr, t = self.frame, self.t
        if fr is None or time.time() - t > 3.0:
            self.hits.clear(); self.boxes = []; return []
        if t == self.det_t:
            return self.boxes
        self.det_t = t
        f = self.crop(fr).astype(np.float32)
        if f.ndim == 3:
            f = f.mean(axis=2)
        if f.shape[1] > 160:
            f = cv2.resize(f, (160, max(1, int(f.shape[0] * 160 / f.shape[1]))), interpolation=cv2.INTER_AREA)
        lo, hi = np.percentile(f, (2, 99.5))
        if self.lo is None:
            self.lo, self.hi = float(lo), float(hi)
        else:                                            # slow: an animal walking in must not re-scale the whole picture
            self.lo += 0.05 * (lo - self.lo); self.hi += 0.05 * (max(hi, self.lo + 1e-3) - self.hi)
        g = np.clip((f - self.lo) * 255.0 / max(1e-3, self.hi - self.lo), 0, 255).astype(np.uint8)
        med = float(np.median(g))
        # 2.98.x (Prüfstand: clear nights 0 thermal persons): the clear night sky is very cold (-20 °C and colder) and sets
        # the bottom of the scale - the ground then sits at ~210 of 255 and «median + 30 %» was above 255: nothing could
        # ever be warm. The step is now measured on the warm side only (twice the room above the median, at most the old
        # full scale), with a camera in °C at least 10 °C, else at least a quarter of the scale.
        span = min(255.0, 2.0 * (255.0 - med))
        if fr.dtype != np.uint8:
            span = max(span, min(255.0, 10.0 * 255.0 / max(1e-3, self.hi - self.lo)))
        else:
            span = max(span, 64.0)
        warm = ((g.astype(np.float32) > med + CFG["thermal_delta"] / 100.0 * span).astype(np.uint8)) * 255
        if CFG["thermal_need_motion"]:
            if self.bgsub is None or self.bg_shape != g.shape:
                self.bgsub = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=12, detectShadows=False); self.bg_shape = g.shape
            mov = cv2.dilate(self.bgsub.apply(g), np.ones((3, 3), np.uint8), iterations=2)
            warm = cv2.bitwise_and(warm, mov)
        warm = cv2.morphologyEx(warm, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        cnts, _ = cv2.findContours(warm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        H, W = g.shape
        min_a = max(2.0, CFG["thermal_min_area"] / 100.0 * W * H)
        boxes = []
        for c in cnts:
            if cv2.contourArea(c) < min_a:
                continue
            x, y, w, h = cv2.boundingRect(c)
            nb = (x / W, y / H, w / W, h / H)
            if zone_allows(nb[0] + nb[2] / 2.0, nb[1] + nb[3] * 0.85):
                boxes.append(nb)
        self.hits.append(bool(boxes))
        self.boxes = boxes if sum(self.hits) >= 3 else []
        return self.boxes

    def overlay(self, frame):
        fr = self.frame
        if fr is None or time.time() - self.t > 3.0:
            return frame
        try:
            H, W = frame.shape[:2]
            ThermalCam.main_aspect = H / float(W)
            col, gray = self.color(self.crop(fr))
            col = cv2.resize(col, (W, H), interpolation=cv2.INTER_CUBIC)
            a = float(max(0.05, min(1.0, CFG["thermal_alpha"])))
            if CFG["thermal_hot"]:
                gray = cv2.resize(gray, (W, H), interpolation=cv2.INTER_LINEAR)
                thr = float(np.percentile(gray[::4, ::4], CFG["thermal_hot_pct"]))
                m = cv2.GaussianBlur((gray > thr).astype(np.float32), (0, 0), max(2.0, W / 200.0))[:, :, None] * a
                return (frame * (1.0 - m) + col * m).astype(np.uint8)
            return cv2.addWeighted(frame, 1.0 - a, col, a, 0)
        except cv2.error:
            return frame


THERMAL = None            # created together with the camera loop


_BELLY = "25:fe87bfc14c106eb2ebb75df5dba6aaec172507faaafe006700ce29179083c51cf8728e897041b1972f895c703f641812f524ff98ff0049463f8eab9055117ba9afa5d29fbee9fec505c09efe89178"     # a little pattern for the marmot (easter egg)


def belly_matrix():
    n, hx = _BELLY.split(":"); n = int(n)
    bits = bin(int(hx, 16))[2:].zfill(len(hx) * 4)
    return [[bits[r * n + c] == "1" for c in range(n)] for r in range(n)]


def _rdp(P, eps):
    """Ramer-Douglas-Peucker: the corners of a drawn line."""
    if len(P) < 3:
        return list(P)
    (ax, ay), (bx, by) = P[0], P[-1]; L = math.hypot(bx - ax, by - ay) or 1e-9
    dmax, idx = -1.0, 0
    for i in range(1, len(P) - 1):
        d = abs((bx - ax) * (ay - P[i][1]) - (ax - P[i][0]) * (by - ay)) / L if L > 1e-6 else math.hypot(P[i][0] - ax, P[i][1] - ay)
        if d > dmax:
            dmax, idx = d, i
    if dmax <= eps:
        return [P[0], P[-1]]
    return _rdp(P[:idx + 1], eps)[:-1] + _rdp(P[idx:], eps)


def cw_triangle(P):
    """True when the points (screen coordinates, y down) are a closed triangle drawn clockwise."""
    if len(P) < 8:
        return False
    xs = [p[0] for p in P]; ys = [p[1] for p in P]
    w, h = max(xs) - min(xs), max(ys) - min(ys); size = max(w, h)
    if size < 40 or min(w, h) < size * 0.3 or math.hypot(P[0][0] - P[-1][0], P[0][1] - P[-1][1]) > size * 0.35:
        return False
    area = sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P))) / 2
    if area <= 0 or not (0.25 <= area / (w * h) <= 0.68):          # y down: positive = clockwise; a triangle fills about half
        return False
    V = _rdp(list(P) + [P[0]], size * 0.12)[:-1]
    changed = True
    while changed and len(V) > 3:                                      # drop corners that are nearly straight
        changed = False
        for i in range(len(V)):
            a, b, c = V[i - 1], V[i], V[(i + 1) % len(V)]
            u, v = (a[0] - b[0], a[1] - b[1]), (c[0] - b[0], c[1] - b[1])
            nu, nv = math.hypot(*u), math.hypot(*v)
            if nu < size * 0.12 or nv < size * 0.12 or (u[0] * v[0] + u[1] * v[1]) / (nu * nv) < -0.88:
                del V[i]; changed = True; break
    return len(V) == 3


def ccw_heart(P, min_size=90):
    """2.95.61: True when the points (screen coordinates, y down) are a big closed heart drawn counter-clockwise:
    two round lobes at the top, a dip in the middle between them, a point at the bottom."""
    if len(P) < 12:
        return False
    xs = [p[0] for p in P]; ys = [p[1] for p in P]
    left, right, top, bot = min(xs), max(xs), min(ys), max(ys)
    w, h = right - left, bot - top; size = max(w, h)
    if size < min_size or not (0.6 <= w / max(h, 1e-6) <= 1.6) or math.hypot(P[0][0] - P[-1][0], P[0][1] - P[-1][1]) > size * 0.3:
        return False
    area = sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P))) / 2
    if area >= 0 or not (0.4 <= -area / (w * h) <= 0.88):          # y down: negative = counter-clockwise on the screen
        return False
    cx = (left + right) / 2
    D = []                                                           # more points on long, fast strokes
    for i in range(len(P)):
        a_, b_ = P[i], P[(i + 1) % len(P)]; k_ = max(1, int(math.hypot(b_[0] - a_[0], b_[1] - a_[1]) / (size / 80)))
        D += [(a_[0] + (b_[0] - a_[0]) * j / k_, a_[1] + (b_[1] - a_[1]) * j / k_) for j in range(k_)]
    P = D
    tip = max(P, key=lambda p: p[1])
    if abs(tip[0] - cx) > 0.22 * w:                                  # the point at the bottom, in the middle
        return False
    low = [p[0] for p in P if p[1] > top + 0.8 * h]
    if low and max(low) - min(low) > 0.55 * w:                       # it gets narrow towards the point
        return False
    mid = [p[1] for p in P if abs(p[0] - cx) < 0.07 * w and p[1] < top + 0.6 * h]
    if not mid or min(mid) < top + 0.07 * h:                         # the dip between the lobes
        return False
    lt = [p[1] for p in P if p[0] < cx - 0.15 * w]; rt = [p[1] for p in P if p[0] > cx + 0.15 * w]
    return bool(lt and rt and min(lt) <= top + 0.15 * h and min(rt) <= top + 0.15 * h)     # two lobes up high


def heart_points(cx, cy, s, n=48, scale_x=1.0):
    """the outline of a heart around (cx, cy), s = half the width (screen: y down)"""
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3; y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        out.append((cx + x / 16 * s * scale_x, cy + (y + 2.5) / 16 * s))
    return out


class NightVision:
    """Night vision look: the picture brightened and tinted green like an image intensifier (a little grain, dark
    corners); a thermal camera adds glowing outlines of warm bodies and - with the Thermal-90 - their temperature."""
    def __init__(self):
        self.vig = None; self.vig_size = None; self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        self.rng = np.random.default_rng(3)

    def active(self):
        return bool(CFG["nightvision"] or (CFG["nightvision_auto"] and LIGHTS.get("dark")))

    def apply(self, frame):
        try:
            H, W = frame.shape[:2]
            g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            g = self.clahe.apply(g)
            m = float(g.mean())
            if m < 110:                                        # lift dark scenes (gamma)
                gm = max(0.35, math.log(120.0 / 255.0) / math.log(max(m, 2.0) / 255.0))
                g = (255.0 * (g / 255.0) ** gm).astype(np.uint8)
            if self.vig_size != (W, H):
                yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
                r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
                self.vig = np.clip(1.15 - 0.55 * r ** 2, 0.25, 1.0).astype(np.float32); self.vig_size = (W, H)
            noise = self.rng.normal(0, 9, (H // 2 + 1, W // 2 + 1)).astype(np.float32)
            noise = cv2.resize(noise, (W, H), interpolation=cv2.INTER_NEAREST)
            v = np.clip((g.astype(np.float32) + noise) * self.vig, 0, 255)
            out = np.dstack([v * 0.22, v, v * 0.38]).astype(np.uint8)          # B, G, R: phosphor green
            th = THERMAL
            if th is not None and th.frame is not None and time.time() - th.t < 3.0:
                self._thermal(out, th, W, H)
            cv2.putText(out, "NV", (W - 42, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (120, 255, 150), 2, cv2.LINE_AA)
            return out
        except (cv2.error, ValueError):
            return frame

    def _thermal(self, out, th, W, H):
        fr = ThermalCam.crop(th.frame)
        celsius = fr.ndim == 2 and fr.dtype.kind == "f"
        f = fr.astype(np.float32) if celsius else ThermalCam.to_gray8(fr).astype(np.float32)
        f = cv2.resize(f, (W, H), interpolation=cv2.INTER_LINEAR)
        thr = float(np.percentile(f[::4, ::4], 96))
        if celsius:
            thr = max(thr, float(np.median(f[::4, ::4])) + 4.0)          # at least 4 °C warmer than the surroundings
        mask = (f > thr).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted((c for c in cnts if cv2.contourArea(c) > W * H * 0.002), key=cv2.contourArea, reverse=True)[:4]
        glow = np.zeros_like(out)
        cv2.drawContours(glow, cnts, -1, (170, 255, 200), 3)
        glow = cv2.GaussianBlur(glow, (0, 0), 3)
        np.maximum(out, glow, out=out)
        cv2.drawContours(out, cnts, -1, (210, 255, 225), 1, cv2.LINE_AA)
        if celsius:
            for c in cnts:
                x, y, w, h = cv2.boundingRect(c)
                t = float(f[y:y + h, x:x + w].max())
                num, F, col = f"{t:.0f}", cv2.FONT_HERSHEY_SIMPLEX, (190, 255, 205)
                (nw, th_), _ = cv2.getTextSize(num, F, 0.55, 2); (cw, _h), _ = cv2.getTextSize("C", F, 0.55, 2)
                tw = nw + 7 + cw
                tx, ty = int(min(max(2, x + w / 2 - tw / 2), W - tw - 4)), int(max(th_ + 4, y - 6))
                cv2.rectangle(out, (tx - 4, ty - th_ - 4), (tx + tw + 4, ty + 4), (20, 60, 25), -1)
                cv2.putText(out, num, (tx, ty), F, 0.55, col, 2, cv2.LINE_AA)
                cv2.circle(out, (tx + nw + 3, ty - th_ + 2), 2, col, 1, cv2.LINE_AA)          # degree sign
                cv2.putText(out, "C", (tx + nw + 7, ty), F, 0.55, col, 2, cv2.LINE_AA)


NIGHTVISION = NightVision()


