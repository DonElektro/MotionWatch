#@ MoveEye – Teil 148: Fehlalarme aus den Spielen prüfen, bevor sie als «keine Person» ins Training gehen (falearn). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.38: In jeder Spielrunde meldete der Simulator (gamelearn.gd) rund 20 «Fehlalarme» pro Minute – auch Rahmen um Spieler,
# weil er MoveEyes Rahmen (aus einem Bild von vor 1–3 s) mit den Spielern von JETZT verglich. Diese Ausschnitte kamen als
# «keine Person» nach fa_learn/ und hätten der KI Falsches beigebracht. Darum hier ein Sicherheitsnetz:
#  - das richtige Bild: MoveEye merkt sich während einer Spielrunde die letzten Bilder mit ihren Personen-Rahmen
#    (fa_ring_note, aus 410) und schneidet den Ausschnitt aus dem Bild, in dem es den Rahmen wirklich gesehen hat
#  - die Wahrheit vom Simulator (ab 3D-4.13, «info.v» 2): keine Person / kein Spieler in der Nähe des Rahmens, der Rahmen
#    nicht viel grösser als eine stehende Person an dieser Stelle («pmax»), der Kopf hat sich nicht gedreht
#  - sonst kommt der Ausschnitt nach fa_learn/zweifel/ (label «doubtful», use false – nicht fürs Training)
#  - «Lernbilder prüfen» (Web: Simulator → Lernen → Fehlalarm-Lernen; Fenster: Simulator): prüft die vorhandenen
#    Spiel-Bilder in fa_learn/ nochmals mit den gespeicherten Angaben; alte Spiel-Bilder ohne diese Angaben gehen nach zweifel/.
# ----------------------------------------------------------------------------
FA_DOUBT_DIR = "zweifel"
FA_RING = {"q": deque(maxlen=48)}          # (time, picture, [[x, y, w, h] 0..1, …]) of the last seconds
FACHECK = {"last": None, "count": None, "count_t": 0.0}


def fa_ring_note(frame, boxes):
    """410: a picture with persons during a game round (frame_raw is a fresh copy per picture - only the reference is kept)"""
    try:
        q = FA_RING["q"]
        now = time.time()
        q.append((now, frame, [list(b) for b in boxes]))
        while q and now - q[0][0] > 5.0:
            q.popleft()
    except Exception:
        pass


def fa_ring_find(box):
    """(picture, "ring") in which MoveEye reported exactly this box, newest first - or (None, "")"""
    try:
        for t_, f_, bs in reversed(list(FA_RING["q"])):
            if time.time() - t_ > 5.0:
                break
            for b in bs:
                if all(abs(float(b[i]) - float(box[i])) <= 0.0015 for i in range(4)):
                    return f_, "ring"
    except Exception:
        pass
    return None, ""


def fa_near(m, t):
    """a box and a truth box mean the same thing (like gamelearn.gd «near»): the truth box grows by a margin; a quarter
    of the box in it, or the centre of one in the other"""
    try:
        m = [float(v) for v in m[:4]]
        t = [float(v) for v in t[:4]]
    except (TypeError, ValueError, IndexError):
        return False
    mx, my = 0.04 + 0.25 * t[2], 0.04 + 0.15 * t[3]
    e = [t[0] - mx, t[1] - my, t[2] + 2 * mx, t[3] + 2 * my]
    ix = max(0.0, min(m[0] + m[2], e[0] + e[2]) - max(m[0], e[0]))
    iy = max(0.0, min(m[1] + m[3], e[1] + e[3]) - max(m[1], e[1]))
    if m[2] * m[3] > 0 and ix * iy / (m[2] * m[3]) >= 0.25:
        return True
    cx, cy = m[0] + m[2] / 2, m[1] + m[3] / 2
    if e[0] <= cx <= e[0] + e[2] and e[1] <= cy <= e[1] + e[3]:
        return True
    tx, ty = t[0] + t[2] / 2, t[1] + t[3] / 2
    return m[0] <= tx <= m[0] + m[2] and m[1] <= ty <= m[1] + m[3]


def fa_box_check(box, info, how, H=0):
    """(ok, [reasons]) - may this box be kept as «no person»? Every doubt is a reason."""
    why = []
    try:
        x, y, w_, h_ = [float(v) for v in (box or [])[:4]]
    except (TypeError, ValueError):
        return False, ["no box"]
    if w_ * h_ > 0.2 or w_ > 0.6 or h_ > 0.8:
        why.append("very big")
    if not isinstance(info, dict) or int(info.get("v") or 0) < 2:
        why.append("no truth from the simulator")
    else:
        tru = info.get("truth") if isinstance(info.get("truth"), list) else []
        if any(isinstance(t, (list, tuple)) and len(t) >= 4 and fa_near([x, y, w_, h_], t) for t in tru[:32]):
            why.append("person near")
        try:
            pm = float(info.get("pmax") or -1)
        except (TypeError, ValueError):
            pm = -1.0
        if pm > 0.005 and (h_ > 1.3 * pm or w_ > 1.0 * pm):     # a person is about a third as wide as high
            why.append("bigger than a person there")
        if info.get("steady") is False:
            why.append("head turned")
    if how != "ring":
        why.append("picture not found")
    try:
        e = size_expected([x, y, w_, h_], 1.0)             # 417: how big a person is at this place (learned by MoveEye)
        if e and h_ > 2.5 * e and "bigger than a person there" not in why:
            why.append("bigger than a person there")
    except Exception:
        pass
    return not why, why


def fa_check_meta(info, how, H=0):
    """what is kept next to the picture so «Lernbilder prüfen» can check it again later"""
    m = {"v": 2 if isinstance(info, dict) and int(info.get("v") or 0) >= 2 else 1, "frame": how, "h": int(H or 0)}
    if isinstance(info, dict):
        tru = []
        for t in (info.get("truth") if isinstance(info.get("truth"), list) else [])[:16]:
            try:
                tru.append([round(float(v), 3) for v in t[:4]])
            except (TypeError, ValueError, IndexError):
                pass
        m["truth"] = tru
        try:
            m["pmax"] = round(float(info.get("pmax")), 3)
        except (TypeError, ValueError):
            m["pmax"] = -1
        if isinstance(info.get("steady"), bool):
            m["steady"] = info["steady"]
    return m


def fa_next_number(d):
    n = 0
    try:
        for fn in os.listdir(d):
            m_ = re.match(r"^(\d+)\.jpg$", fn)
            if m_:
                n = max(n, int(m_.group(1)))
    except OSError:
        pass
    return n + 1


def _fa_is_game_dir(dn, d):
    if dn.endswith("_spiel"):
        return True
    try:
        with open(os.path.join(d, "info.json")) as f:
            i = json.load(f)
        return i.get("cause") == "game" or i.get("from") == "simulator game"
    except (OSError, ValueError, AttributeError):
        return False


def fa_counts():
    """(game pictures for the training, doubtful pictures) - cached for 30 s"""
    if FACHECK["count"] is not None and time.time() - FACHECK["count_t"] < 30:
        return FACHECK["count"]
    base = os.path.join(DATA_DIR, "fa_learn")
    g = z = 0
    try:
        for dn in os.listdir(base):
            d = os.path.join(base, dn)
            if not os.path.isdir(d):
                continue
            if dn == FA_DOUBT_DIR:
                for r_, _ds, fs in os.walk(d):
                    z += sum(1 for f in fs if f.endswith(".jpg"))
            elif _fa_is_game_dir(dn, d):
                g += sum(1 for f in os.listdir(d) if f.endswith(".jpg"))
    except OSError:
        pass
    FACHECK.update(count=(g, z), count_t=time.time())
    return g, z


def fa_review():
    """«Lernbilder prüfen»: every game picture in fa_learn/ again - with the saved truth if there is one; game pictures
    without it (before 2.98.38) go to fa_learn/zweifel/. The pictures of real false alarms (👎) are not touched."""
    base = os.path.join(DATA_DIR, "fa_learn")
    res = {"t": time.time(), "checked": 0, "kept": 0, "moved": 0}
    try:
        names = sorted(os.listdir(base))
    except OSError:
        names = []
    for dn in names:
        d = os.path.join(base, dn)
        if dn == FA_DOUBT_DIR or not os.path.isdir(d) or not _fa_is_game_dir(dn, d):
            continue
        zd = os.path.join(base, FA_DOUBT_DIR, dn)
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".jpg"):
                continue
            res["checked"] += 1
            jp = os.path.join(d, fn[:-4] + ".json")
            meta = {}
            try:
                with open(jp) as f:
                    meta = json.load(f)
            except (OSError, ValueError):
                meta = {}
            chk = meta.get("check") if isinstance(meta, dict) else None
            if isinstance(chk, dict) and int(chk.get("v") or 0) >= 2:
                ok, why = fa_box_check(meta.get("box"), dict(chk, v=2), chk.get("frame"), chk.get("h") or 0)
            else:
                ok, why = False, ["old game picture without truth"]
            if ok:
                res["kept"] += 1
                continue
            try:
                os.makedirs(zd, exist_ok=True)
                n = fa_next_number(zd)
                shutil.move(os.path.join(d, fn), os.path.join(zd, "%02d.jpg" % n))
                meta = meta if isinstance(meta, dict) else {}
                meta.update(label="doubtful", moved_from=dn + "/" + fn, check=dict(chk if isinstance(chk, dict) else {}, ok=False, why=why))
                with open(os.path.join(zd, "%02d.json" % n), "w") as f:
                    json.dump(meta, f)
                if os.path.isfile(jp):
                    os.remove(jp)
                res["moved"] += 1
            except OSError as e:
                log_event("sys", f"Check learning pictures: {e}"[:120])
        try:                                            # nothing left but info.json: the folder goes too
            rest = [f for f in os.listdir(d) if f != "info.json"]
            if not rest:
                if os.path.isdir(zd) and not os.path.exists(os.path.join(zd, "info.json")) and os.path.isfile(os.path.join(d, "info.json")):
                    shutil.copy(os.path.join(d, "info.json"), os.path.join(zd, "info.json"))
                shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass
    if res["moved"]:                                    # the doubtful folders say so themselves (a training tool walking fa_learn/)
        for r_, ds, _fs in os.walk(os.path.join(base, FA_DOUBT_DIR)):
            for x in ds + [""]:
                p_ = os.path.join(r_, x, "info.json")
                try:
                    with open(p_, "w") as f:
                        json.dump({"label": "doubtful", "use": False, "from": "simulator game", "note": "not for the training"}, f)
                except OSError:
                    pass
            break
    FACHECK["last"] = res
    FACHECK["count"] = None
    log_event("sys", f"Learning pictures checked: {res['checked']} checked, {res['kept']} kept, {res['moved']} moved to «doubtful»")
    return res


def facheck_state():
    g, z = fa_counts()
    return {"last": FACHECK["last"], "game": g, "doubt": z}


def falearn_tk_build(app, sbody):
    """the window (section Simulator): «Lernbilder prüfen» - like the web (139, sheet «Fehlalarm-Lernen»)"""
    from tkinter import ttk
    def run():
        def go():
            r = fa_review()
            g, z = fa_counts()
            app._status("Simulator", "✓ " + tr("Learning pictures checked") + f": {r['checked']} · {tr('kept')} {r['kept']} · "
                        + f"{tr('moved to «doubtful»')} {r['moved']} · {tr('Game pictures for the training')} {g} · {tr('doubtful (not used)')} {z}")
        threading.Thread(target=go, daemon=True, name="facheck").start()
    ttk.Button(sbody, text="🔍 " + tr("Check learning pictures"), command=run).pack(fill="x", pady=(4, 0))
