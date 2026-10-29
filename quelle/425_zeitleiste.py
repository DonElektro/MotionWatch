#@ MoveEye – Teil 425: Zeitleiste der Nacht – alles einer Nacht auf einer Zeitachse (Aufnahmen, Nachrichten, Tiere, Alarme, Akku, Temperatur, Wetter). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# 2.98.14 (Wunsch Daniel): Reiter Verlauf → «Zeitleiste». Eine Nacht (Standard: letzte Nacht 18:00–09:00, Tag wählbar) oder
# ein ganzer Tag, alles auf einer Zeitachse. Die Daten kommen aus den bestehenden Quellen – nichts wird doppelt gespeichert:
#   Aufnahmen        list_recordings (430)            Nachrichten   msglog_list (065)
#   Tierbesuche      SIGHT / Tagebuch (090)           Alarme, Log   Protokoll-Dateien (390, nur die wichtigen Zeilen)
#   Akku, Temperatur climate_day (060, alle 10 Min.)  Wetter        weather_day (060, Open-Meteo, stündlich)
# Eine Adresse: /api/timeline?day=JJJJ-MM-TT&mode=night|day. Seite TL_PAGE (523), Fenster: einfache Liste (575).
# ----------------------------------------------------------------------------
TL_ALARM_KINDS = ("person", "alarm", "tamper")


def timeline_window(day=None, mode="night"):
    """(start, end) of a night (the evening before the given morning 18:00 until 09:00) or a whole day"""
    try:
        d = datetime.strptime(str(day or "")[:10], "%Y-%m-%d")
    except ValueError:
        d = datetime.now()
    d = d.replace(hour=0, minute=0, second=0, microsecond=0)
    if mode == "day":
        return d, d + timedelta(days=1)
    return d - timedelta(hours=6), d + timedelta(hours=9)


def _tl_days(a, b):
    out, d = [], a.replace(hour=0, minute=0, second=0, microsecond=0)
    while d < b:
        out.append(d.strftime("%Y-%m-%d")); d += timedelta(days=1)
    return out


def _tl_log(a, b, limit=400):
    """the important log lines between a and b (archive days + today's file), oldest first"""
    import gzip
    files = []
    for day in _tl_days(a, b):
        try:
            files += sorted(os.path.join(log_dir(), f) for f in os.listdir(log_dir())
                            if LOG_NAME_RE.match(f) and f[12:22] == day)
        except OSError:
            pass
    if os.path.isfile(LOG_FILE):
        files.append(LOG_FILE)
    sa, sb = a.strftime("%Y-%m-%d %H:%M:%S"), b.strftime("%Y-%m-%d %H:%M:%S")
    out, seen, rep_ = [], set(), {}
    for p in files:
        try:
            if p.endswith(".gz"):
                with gzip.open(p, "rt", encoding="utf-8", errors="replace") as f:
                    lines = f.read().splitlines()
            else:
                with open(p, "rb") as f:
                    f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 6 * 1024 * 1024))
                    lines = f.read().decode("utf-8", "replace").splitlines()
        except OSError:
            continue
        for ln in lines:
            m = LOG_LINE_RE.match(ln)
            if not m:
                continue
            ts = m.group(1) + " " + m.group(2)
            if not (sa <= ts < sb):
                continue
            kind, text = m.group(3), m.group(4)
            if kind == "status" or text.startswith(("Diary: ", "Recording started")):   # noise / shown as visit or recording
                continue
            if not (kind in TL_ALARM_KINDS or log_important(kind, text)):
                continue
            key = (ts, kind, text)
            if key in seen:
                continue
            seen.add(key)
            try:
                t = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").timestamp()
            except ValueError:
                continue
            first = rep_.get((kind, text))
            if first is not None and kind not in TL_ALARM_KINDS:   # the same warning again and again: one entry with a count
                first["n"] = first.get("n", 1) + 1; first["t_last"] = t
                continue
            e = {"t": t, "type": "log", "kind": kind, "text": text[:300], "alarm": kind in TL_ALARM_KINDS}
            rep_[(kind, text)] = e
            out.append(e)
    out.sort(key=lambda x: x["t"])
    return out[-limit:]


def _tl_recordings(a, b):
    out, off = [], 0
    args = {"from": a.strftime("%Y-%m-%d"), "to": (b - timedelta(seconds=1)).strftime("%Y-%m-%d"), "sort": "old", "limit": 200}
    while off < 1000:
        args["offset"] = off
        try:
            r = list_recordings(args, WATCH_REF.get("w"))
        except Exception as e:
            log_event("sys", f"Timeline: recordings {e}"[:160])
            break
        for it in r.get("items") or []:
            if it.get("timelapse"):
                continue
            try:
                t = datetime.strptime(it["time"], "%Y-%m-%d %H:%M:%S")
            except (KeyError, ValueError):
                continue
            if a <= t < b:
                out.append({"t": t.timestamp(), "type": "rec", "name": it["name"], "kind": it["kind"], "snap": it.get("snap"),
                            "dur": it.get("duration"), "persons": it.get("persons"), "false": it.get("false"), "fav": it.get("fav"),
                            "src": it.get("source") or "", "live": bool(it.get("recording"))})
        off += 200
        if off >= int(r.get("total") or 0):
            break
    return out


def _tl_sightings(a, b, lang):
    sight_load()
    sa, sb = a.isoformat(timespec="seconds"), b.isoformat(timespec="seconds")
    with SIGHT_LOCK:
        lst = [dict(e) for e in SIGHT["list"] if sa <= e.get("start", "") < sb]
    out = []
    for e in lst:
        try:
            t = datetime.fromisoformat(e["start"]).timestamp()
        except ValueError:
            continue
        out.append({"t": t, "type": "sight", "id": e.get("id"), "label": e.get("label"), "name": tr_trigger(e.get("label", ""), lang),
                    "kind": e.get("kind"), "dur": e.get("dur"), "img": e.get("img") or "", "conf": e.get("conf")})
    return out


def _tl_messages(a, b):
    ta, tb = a.timestamp(), b.timestamp()
    out = []
    for m in msglog_list(MSGLOG_MAX):
        t = float(m.get("t") or 0)
        if ta <= t < tb:
            out.append({"t": t, "type": "msg", "id": m.get("id"), "ev": m.get("ev"), "title": m.get("title"), "text": m.get("text"),
                        "status": m.get("status"), "img": bool(m.get("img"))})
    return out


def _tl_series(a, b):
    """climate (every 10 min: temperature, humidity, CPU, battery) and weather (every hour) between a and b"""
    clim, wx = [], []
    for day in _tl_days(a, b):
        for row in climate_day(day):
            try:
                t = datetime.strptime(day + " " + str(row[0]), "%Y-%m-%d %H:%M")
            except (ValueError, TypeError, IndexError):
                continue
            if a <= t < b:
                r = list(row) + [None] * 6
                clim.append({"t": t.timestamp(), "temp": r[1], "hum": r[2], "cpu": r[4], "bat": r[5]})
        w = weather_day(day) or {}
        for hh, v in sorted((w.get("hourly") or {}).items()):
            try:
                t = datetime.strptime(day + " " + hh, "%Y-%m-%d %H")
            except ValueError:
                continue
            if a <= t < b and isinstance(v, list):
                v = list(v) + [None] * 5
                ic = ""
                try:
                    ic = wmo_text(v[3])[0] if v[3] is not None else ""
                except Exception:
                    pass
                wx.append({"t": t.timestamp(), "temp": v[0], "rain": v[1], "hum": v[2], "code": v[3], "gust": v[4], "icon": ic})
    return clim, wx


def timeline_build(day=None, mode="night", lang=None):
    L = norm_lang(lang) if lang else cur_lang()
    mode = "day" if mode == "day" else "night"
    a, b = timeline_window(day, mode)
    items = []
    for fn in (lambda: _tl_recordings(a, b), lambda: _tl_messages(a, b), lambda: _tl_sightings(a, b, L), lambda: _tl_log(a, b)):
        try:
            items += fn()
        except Exception as e:
            log_event("sys", f"Timeline: {type(e).__name__}: {e}"[:160])
    items.sort(key=lambda x: x["t"])
    try:
        clim, wx = _tl_series(a, b)
    except Exception:
        clim, wx = [], []
    cnt = {"rec": 0, "msg": 0, "sight": 0, "log": 0, "alarm": 0, "animal": 0, "false": 0}
    for it in items:
        cnt[it["type"]] += 1
        if it["type"] == "log" and it.get("alarm"):
            cnt["alarm"] += 1
        if it["type"] == "sight" and it.get("kind") == "animal":
            cnt["animal"] += 1
        if it["type"] == "rec" and it.get("false"):
            cnt["false"] += 1
    bats = [c["bat"] for c in clim if c.get("bat") is not None]
    temps = [c["temp"] for c in clim if c.get("temp") is not None] or [w["temp"] for w in wx if w.get("temp") is not None]
    return {"ok": True, "mode": mode, "day": a.strftime("%Y-%m-%d") if mode == "day" else (a + timedelta(hours=6)).strftime("%Y-%m-%d"),
            "start": a.timestamp(), "end": b.timestamp(), "now": time.time(), "items": items[-1500:], "climate": clim, "weather": wx,
            "count": cnt, "bat": {"first": bats[0], "last": bats[-1], "min": min(bats)} if bats else None,
            "temp": {"min": min(temps), "max": max(temps)} if temps else None,
            "env": bool(CFG.get("env_on")), "weather_on": bool(CFG.get("weather_on"))}


def timeline_text(tl, lang=None):
    """the timeline as plain lines (window, tests): [(time 'HH:MM', symbol, text, item)]"""
    L = norm_lang(lang) if lang else cur_lang()
    out = []
    for it in tl["items"]:
        hm = datetime.fromtimestamp(it["t"]).strftime("%H:%M")
        ty = it["type"]
        if ty == "rec":
            s = ("🎬 " if it["kind"] == "video" else "📷 ") + tr("Recording", L) + (f" · {it['dur']:.0f} s" if it.get("dur") else "")
            if it.get("false"):
                s += " · " + tr("false alarm", L)
            out.append((hm, "rec", s, it))
        elif ty == "msg":
            out.append((hm, "msg", "✉ " + (it.get("title") or "MoveEye") + " – " + str(it.get("text") or "")[:120], it))
        elif ty == "sight":
            out.append((hm, "sight", ("🦊 " if it.get("kind") == "animal" else "👤 ") + str(it.get("name") or it.get("label")) +
                        (f" · {it['dur']} s" if it.get("dur") else ""), it))
        else:
            out.append((hm, "alarm" if it.get("alarm") else "log", ("🚨 " if it.get("alarm") else "• ") + it["text"] +
                        (f" (× {it['n']})" if it.get("n", 1) > 1 else ""), it))
    return out
