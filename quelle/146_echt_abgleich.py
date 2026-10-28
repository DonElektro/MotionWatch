#@ MoveEye – Teil 146: Echt-Abgleich für den Simulator (2.98.6) – das Aussehen der echten Bilder messen und dem Simulator schicken. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# The simulator (3D-3.94, realism.gd) makes its pictures look like the real ones of THIS MoveEye: brightness, contrast,
# saturation, colour cast (red / blue to green), sharpness and grain - day and night separately. The real pictures are the
# diary pictures and the alarm pictures (never taken in the simulation). Measured the same way as realism.gd.stats():
# 160 x 90 bilinear, luminance 0.299 / 0.587 / 0.114. Only picture data leaves MoveEye (no map data, no picture itself).
# ----------------------------------------------------------------------------
REAL_LOOK = {"t": 0.0, "v": None, "busy": False}


def real_look_stats(img):
    s = cv2.resize(img, (160, 90), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0
    b, g, r = s[:, :, 0], s[:, :, 1], s[:, :, 2]
    L = 0.299 * r + 0.587 * g + 0.114 * b
    mean = float(L.mean())
    sat = float((s.max(axis=2) - s.min(axis=2)).mean())
    inner = L[1:89, 1:159]
    sharp = float(np.abs(inner - L[1:89, 0:158]).mean())
    noise = float(np.abs(inner - (L[1:89, 0:158] + L[1:89, 2:160] + L[0:88, 1:159] + L[2:90, 1:159]) * 0.25).mean())
    gm = max(0.001, float(g.mean()))
    return {"mean": mean, "std": float(L.std()), "sat": sat, "r": float(r.mean()) / gm, "b": float(b.mean()) / gm, "sharp": sharp, "noise": noise}


def _real_look_files():
    out = []
    for d, pat in ((diary_dir(), None), (rec_dir(), "person_")):
        try:
            for f in os.listdir(d):
                if f.lower().endswith(".jpg") and (pat is None or f.startswith(pat)):
                    p = os.path.join(d, f)
                    out.append((os.path.getmtime(p), p))
        except OSError:
            pass
    out.sort(reverse=True)
    return [p for _t, p in out[:80]]


def real_look_build():
    acc = {"day": [], "night": []}
    for p in _real_look_files():
        img = cv2.imread(p)
        if img is None or img.shape[0] < 90:
            continue
        st = real_look_stats(img)
        acc["night" if st["mean"] < 0.18 or st["sat"] < 0.03 else "day"].append(st)
    res = {}
    for k, lst in acc.items():
        if lst:
            res[k] = {key: round(float(np.median([x[key] for x in lst])), 4) for key in lst[0]}
            res[k]["n"] = len(lst)
    return res


def real_look():
    """for the simulator state: the look of the real pictures (computed in the background, at most every 6 h)"""
    if not REAL_LOOK["busy"] and time.time() - REAL_LOOK["t"] > 6 * 3600:
        REAL_LOOK["busy"] = True

        def run():
            try:
                REAL_LOOK["v"] = real_look_build()
                log_event("sys", "Real look for the simulator: " + ", ".join(f"{k} {v['n']} picture(s)" for k, v in (REAL_LOOK["v"] or {}).items()))
            except Exception as e:
                log_event("sys", f"Real look: {e}"[:120])
            REAL_LOOK["t"] = time.time()
            REAL_LOOK["busy"] = False
        threading.Thread(target=run, daemon=True, name="reallook").start()
    return REAL_LOOK["v"] or None
