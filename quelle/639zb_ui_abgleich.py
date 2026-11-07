#@ MoveEye – Teil 639zb: Abgleich der Ansicht MoveEye ↔ Simulator (P2 «totale Integration»: Feld «ui» mit Revision, letzte Änderung gewinnt, MoveEye führt bei Gleichstand und nach dem Neuverbinden), eine Einfach/Experte-Wahl und eine Sprache (P3), Zustand Aus / Wachsam / Voll, Push-Vorschau, Diagnose gegenseitig, Versions-Paar und Bedienermodus im Simulator (★ review_integration2). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Besitzer (31.10. / 01.11.2026): «In MoveEye umschalten, und der Simulator zieht sofort mit, und umgekehrt» - ohne eigenen Schalter.
#   * Geteilt (ui_gemeinsam.json «shared», UIS_KEYS): Einfach/Experte, Symbole farbig/schlicht, Sprache, Bewegung reduzieren,
#     Stimme, Rundgang, Blinki, «Neu in …». Hell/Dunkel/Rotlicht bleibt pro Gerät («local»).
#   * Protokoll (simulator3d/schnittstelle.json): MoveEye schickt im 10-Hz-Zustand (POST /state) «ui» = {"rev", "took", "v": {…}}.
#     Der Simulator antwortet nur bei einer eigenen Änderung mit «ui» = {"n": laufende Nummer, "base": rev, "set": {…}}.
#     MoveEye zählt die Revision: jede eigene Änderung und jede übernommene Änderung des Simulators = rev + 1. «took» sagt dem
#     Simulator, bis zu welcher Nummer seine Änderungen angekommen sind (danach gelten wieder die Werte von MoveEye).
#   * Letzte Änderung gewinnt (gemessen an der Ankunft bei MoveEye, keine Uhren). Im selben Takt geändert: MoveEye gewinnt.
#     Nach dem Neuverbinden (Pause > 3 s, anderer Leiter, rev kleiner) führt MoveEye - der Simulator übernimmt alles.
#   * Nur das MoveEye, das den Simulator steuert (Leiter), gleicht ab (ein zuschauendes bekommt «follower»). Ohne Verbindung
#     arbeitet jede Seite mit ihren eigenen Werten weiter. Ältere Simulatoren ignorieren «ui» (Feld «features» in /info: ui1).
#   * P3: Einfach/Experte gilt überall (früher pro Seite, Teil 586 «mw-page-mode»: einmal übernommen, Experte gewinnt, damit
#     nichts verschwindet; der alte Wert bleibt in den Einstellungen liegen). Eine Sprache: web_ui «mw-lang» = CFG lang.
#   * ★1 «level» (Aus / Wachsam / Voll / Gehtest + Farbe der Status-LED), ★2 «push» (die letzte Meldung, für das Kärtchen im
#     Simulator), ★3 «diag» (alle 15 s die Selbstdiagnose von MoveEye) und hier umgekehrt die des Simulators (health_check,
#     diag_zip), ★4 Versions-Paar «MoveEye 3.x · Sim 3.x ✓», ★6 «lock» (Bedienermodus; Entsperren mit der PIN von MoveEye,
#     geprüft nur hier: lock_set, 5 Fehlversuche = 5 Minuten Pause).
#   * Offene Web-Seiten: kleiner Hinweis «Ansicht im Simulator geändert – neu laden» (kein Neuladen von selbst).
# ----------------------------------------------------------------------------
UIS_KEYS = ("simple", "icons", "lang", "motion", "voice", "tours", "blinki", "news", "news_links")
UIS_ENUM = {"icons": ("color", "plain"), "lang": LANGS, "motion": ("auto", "on", "off"), "voice": ("on", "off", "subtitles"),
            "news_links": ("auto", "on", "off")}   # Links zu Neuerungen (639zc)
UIS = {"rev": 1, "last": None, "mine": set(), "took": 0, "lang_seen": None, "from_sim": [], "from_sim_t": 0.0,
       "lock_n": 0, "lock_msg": "", "upd_n": 0, "upd_msg": "", "diag_t": 0.0, "sim_diag": None, "sim_diag_t": 0.0, "sim_diag_busy": False}
UIS_LOCK = threading.Lock()
for _k, _v in (("ui_mode_merged", False),):
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v)

# key = English text: (Deutsch, Français, Italiano, Rumantsch)
_HX_UIS = {
    'View changed in the simulator': ('Ansicht im Simulator geändert', 'Vue modifiée dans le simulateur', 'Vista modificata nel simulatore',
                                      'Vista midada en il simulatur'),
    'Reload': ('Neu laden', 'Recharger', 'Ricarica', 'Chargiar da nov'),
    'Versions': ('Versionen', 'Versions', 'Versioni', 'Versiuns'),
    'Simulator older': ('Simulator älter', 'Simulateur plus ancien', 'Simulatore più vecchio', 'Simulatur pli vegl'),
    'MoveEye older': ('MoveEye älter', 'MoveEye plus ancien', 'MoveEye più vecchio', 'MoveEye pli vegl'),
    'Update the simulator': ('Simulator aktualisieren', 'Mettre à jour le simulateur', 'Aggiorna il simulatore', 'Actualisar il simulatur'),
    'Update MoveEye': ('MoveEye aktualisieren', 'Mettre à jour MoveEye', 'Aggiorna MoveEye', 'Actualisar MoveEye'),
    'The numbers may differ, but one program is older than the other one needs.':
        ('Die Nummern dürfen verschieden sein, aber ein Programm ist älter, als das andere braucht.',
         'Les numéros peuvent différer, mais un programme est plus ancien que ce dont l’autre a besoin.',
         'I numeri possono essere diversi, ma un programma è più vecchio di quanto serve all’altro.',
         'Ils numers dastgan esser differents, ma in program è pli vegl che quai che l’auter dovra.'),
    'Simulator': ('Simulator', 'Simulateur', 'Simulatore', 'Simulatur'),
    'MoveEye gets only {f} pictures/s from the simulator - it hardly detects anything (from about 3/s on it works)':
        ('MoveEye bekommt nur {f} Bilder/s vom Simulator – so erkennt es kaum etwas (ab etwa 3/s geht es)',
         'MoveEye ne reçoit que {f} images/s du simulateur – il ne détecte presque rien (à partir d’env. 3/s cela fonctionne)',
         'MoveEye riceve solo {f} immagini/s dal simulatore – non rileva quasi nulla (da circa 3/s funziona)',
         'MoveEye survegn mo {f} maletgs/s dal simulatur – uschia na renconuscha el quasi nagut (a partir da var 3/s funcziunescha)'),
    'Pictures from the simulator': ('Bilder vom Simulator', 'Images du simulateur', 'Immagini dal simulatore', 'Maletgs dal simulatur'),
    'Make the simulator lighter (System → Graphics: Lite) or close other programs on the PC.':
        ('Simulator leichter stellen (System → Grafik: Lite) oder andere Programme auf dem PC schliessen.',
         'Alléger le simulateur (Système → Graphisme : Lite) ou fermer d’autres programmes sur le PC.',
         'Alleggerire il simulatore (Sistema → Grafica: Lite) o chiudere altri programmi sul PC.',
         'Far il simulatur pli levs (Sistem → Grafica: Lite) u serrar auters programs sin il PC.'),
}
for _k, _v in _HX_UIS.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(('fr', 'it', 'rm')):
        TRX[_L].setdefault(_k, _v[_i + 1])


# ---- the shared values -------------------------------------------------------------------------------------------------
def ui_norm(k, v):
    """a value from the other side, checked: None = not usable"""
    if k in ("simple", "tours", "blinki", "news"):
        return v if isinstance(v, bool) else None
    if k in UIS_ENUM:
        v = str(v or "").lower()
        return v if v in UIS_ENUM[k] else None
    return None


def ui_lang_unify():
    """P3 (E2): ONE language - the web choice (web_ui «mw-lang», all browsers) and the device language (CFG lang) are the same.
    Changed on one side (language menu of a page, Pi window, settings, simulator): the other follows. First time: the web
    choice is taken over (it is the one the user saw last)."""
    wu = CFG.get("web_ui") or {}
    wl, cl = str(wu.get("mw-lang") or ""), cur_lang()
    seen = UIS["lang_seen"]
    if wl in LANGS and wl != cl:
        if seen is None or seen == cl:                    # the web choice changed (or first time)
            CFG["lang"] = wl; cl = wl
        else:                                             # the device language changed
            CFG["web_ui"] = dict(wu, **{"mw-lang": cl})
    elif not wl and seen is not None and wu:
        CFG["web_ui"] = dict(wu, **{"mw-lang": cl})
    UIS["lang_seen"] = cl
    return cl


def ui_values():
    """the shared values of MoveEye now (names of ui_gemeinsam.json «shared»)"""
    cl = ui_lang_unify()
    wu = CFG.get("web_ui") or {}
    rm = str(CFG.get("reduce_motion") or "auto")
    vm = str(CFG.get("voice_mode") or "on")
    return {"simple": bool(CFG.get("ui_simple", True)), "icons": "plain" if wu.get("mw-icons") == "plain" else "color",
            "lang": cl, "motion": rm if rm in UIS_ENUM["motion"] else "auto", "voice": vm if vm in UIS_ENUM["voice"] else "on",
            "tours": bool(CFG.get("tours_auto", True)), "blinki": bool(CFG.get("blinki_on", True)), "news": bool(CFG.get("news_popup", True)),
            "news_links": str(CFG.get("news_links") or "auto") if str(CFG.get("news_links") or "auto") in UIS_ENUM["news_links"] else "auto"}


def ui_apply(vals, who="simulator"):
    """set shared values that came from the other side; returns the keys that really changed"""
    cur = ui_values()
    ch = []
    for k, v in (vals or {}).items():
        v = ui_norm(k, v) if k in UIS_KEYS else None
        if v is None or cur.get(k) == v:
            continue
        ch.append(k)
        if k == "simple":
            CFG["ui_simple"] = v
        elif k == "icons":
            CFG["web_ui"] = dict(CFG.get("web_ui") or {}, **{"mw-icons": v})
        elif k == "lang":
            CFG["lang"] = v; CFG["web_ui"] = dict(CFG.get("web_ui") or {}, **{"mw-lang": v}); UIS["lang_seen"] = v
        elif k == "motion":
            CFG["reduce_motion"] = v
        elif k == "voice":
            CFG["voice_mode"] = v
        elif k == "tours":
            CFG["tours_auto"] = v
        elif k == "blinki":
            CFG["blinki_on"] = v
        elif k == "news":
            CFG["news_popup"] = v
        elif k == "news_links":
            CFG["news_links"] = v
    if ch:
        _save_settings_639zb()
        UIS["from_sim"] = ch; UIS["from_sim_t"] = time.time()
        log_event("sys", f"View taken over from the {who}: " + ", ".join(f"{k} = {ui_values()[k]}" for k in ch))
    return ch


def ui_tick():
    """once per packet to the simulator: an own change since the last packet = rev + 1 (its keys: «mine» for this packet)"""
    with UIS_LOCK:
        cur = ui_values()
        last = UIS["last"]
        UIS["mine"] = {k for k in UIS_KEYS if last is not None and cur[k] != last[k]}
        if UIS["mine"]:
            UIS["rev"] += 1
        UIS["last"] = cur
        return cur


def ui_take(u):
    """world_reply «ui» of the simulator: its own changes (set), the PIN of the operator mode (unlock), «update MoveEye»"""
    if not isinstance(u, dict):
        return
    with UIS_LOCK:
        n = int(u.get("n") or 0)
        s = u.get("set")
        if isinstance(s, dict) and n > UIS["took"]:
            UIS["took"] = n
            keep = {k: v for k, v in s.items() if k in UIS_KEYS and k not in UIS["mine"]}   # same packet: MoveEye wins
            ui_apply(keep)
            UIS["last"] = ui_values()
            UIS["rev"] += 1
    ul = u.get("unlock")
    if isinstance(ul, dict) and int(ul.get("n") or 0) > UIS["lock_n"]:
        UIS["lock_n"] = int(ul.get("n") or 0)
        if CFG.get("lock_on"):
            ok, err = lock_set("unlock", str(ul.get("pin") or "")[:12], source="simulator")
            UIS["lock_msg"] = "ok" if ok else err
        else:
            UIS["lock_msg"] = "ok"
    up = u.get("update_mw")
    if isinstance(up, dict) and int(up.get("n") or 0) > UIS["upd_n"]:
        UIS["upd_n"] = int(up.get("n") or 0)
        ui_update_mw(str(up.get("ver") or ""), "simulator")


def ui_update_mw(ver, who="web"):
    """★4: MoveEye to the number of the simulator (only a signed version of the update source, never in operator mode)"""
    if CFG.get("lock_on"):
        UIS["upd_msg"] = "locked"
        return False

    def run():
        try:
            items = update_check()
            lst = items[0] if isinstance(items, tuple) else items
            vs = [str(x.get("version")) for x in (lst or []) if isinstance(x, dict)]
            want = ver if ver in vs else ""
            if not want:
                UIS["upd_msg"] = "not found: " + ver
                return
            ok, err = update_install(want)
            UIS["upd_msg"] = "installing " + want if ok else str(err)
            log_event("sys", f"Update to {want} asked for by the {who}" + ("" if ok else f" - {err}"))
        except Exception as e:
            UIS["upd_msg"] = str(e)[:120]
    threading.Thread(target=run, daemon=True, name="uisupd").start()
    return True


# ---- what else goes to the simulator ------------------------------------------------------------------------------------
def ui_level():
    """★1: the state in the words and colours of MoveEye: off | watch | full | walktest (+ colour of the status LED)"""
    try:
        lv = protect_level()
    except NameError:
        lv = "watch" if CFG.get("armed") else "off"
    arming = STATE.get("arm_state") == "arming"
    wt = False
    try:
        wt = bool(lv != "off" and walktest_on())
    except NameError:
        pass
    try:
        col = LED_HEX.get(led_colour("led_col_" + lv), "#888888")
    except NameError:
        col = {"off": "#2fd35a", "watch": "#ff8a1f", "full": "#ff2a2a"}.get(lv, "#888888")
    return {"id": "walktest" if wt else lv, "col": "#3b7bff" if wt else col, "arming": arming}


def ui_push_last():
    """★2: the newest message of the list «Nachrichten» (test inbox or real push), for the little card in the simulator"""
    try:
        with MSGLOG["lock"]:
            items = list(_msglog_load()[-1:])
    except Exception:
        return None
    if not items:
        return None
    x = items[0]
    t = float(x.get("t") or 0.0)
    return {"id": str(x.get("id", "")), "t": round(t, 1), "hm": time.strftime("%H:%M", time.localtime(t)) if t else "",
            "title": str(x.get("title") or "")[:120], "where": str(x.get("where") or "")[:60], "status": str(x.get("status") or "")}


def ui_diag_items():
    """★3: the self-diagnosis of MoveEye for the simulator (without the simulator's own lines; with the warning about too few
    pictures per second from the simulator)"""
    try:
        its = _health_check_639zb(cur_lang()) + [x for x in ui_pair_items(cur_lang()) if x["id"] == "sim:fps"]
        return [dict(x, id="mw:" + str(x.get("id"))) for x in its][:30]
    except Exception:
        return []


_sim_state_639zb = sim_state


def sim_state():                                          # + 639zb: ui, features, level, lock, push (and every 15 s diag)
    d = _sim_state_639zb()
    d["features"] = ["ui1", "level1", "push1", "diag1", "lock1", "ver1"]
    d["sim_min"] = SIM_MIN                                # 3 tracks: the oldest simulator this MoveEye works with (545)
    cur = ui_tick()
    if not SIM.get("follower"):                           # only the leading MoveEye shares the view
        d["ui"] = {"rev": UIS["rev"], "took": UIS["took"], "v": cur}
    d["level"] = ui_level()
    d["lock"] = {"on": bool(CFG.get("lock_on")), "n": UIS["lock_n"], "msg": UIS["lock_msg"], "pin": bool(CFG.get("lock_pin"))}
    d["push"] = ui_push_last()
    if time.time() - UIS["diag_t"] > 15.0:
        UIS["diag_t"] = time.time()
        d["diag"] = ui_diag_items()
    if time.time() - UIS["sim_diag_t"] > 20.0 and not UIS["sim_diag_busy"] and SIM.get("ok") and "diag1" in sim_features():
        UIS["sim_diag_busy"] = True
        threading.Thread(target=ui_sim_diag_fetch, daemon=True, name="simdiag").start()
    return d


_simvals_take_639zb = simvals_take


def simvals_take(rep_):                                   # + 639zb: «ui» of the answer (the simulator's own view changes)
    _simvals_take_639zb(rep_)
    if not rep_.get("follower"):
        ui_take(rep_.get("ui"))


def ui_sim_diag_fetch():
    """★3: the self-diagnosis of the simulator (same format: id, icon, title, level, text, tip), cached for 20 s"""
    try:
        r = sim_control({"action": "mehr", "do": "diag"})
        its = [x for x in (r.get("items") or []) if isinstance(x, dict) and not str(x.get("id", "")).startswith("mw:")]
        UIS["sim_diag"] = its
    except Exception:
        UIS["sim_diag"] = None
    finally:
        UIS["sim_diag_t"] = time.time(); UIS["sim_diag_busy"] = False


# ---- ★4 the version pair ------------------------------------------------------------------------------------------------
def ui_vnum(v):
    """«3.34.0», «MoveEye Sim 3.34.0», «3D-5.34.0» -> (3, 34, 0); None = no number"""
    try:
        return sim_vkey(v)
    except NameError:
        m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", str(v or ""))
        return tuple(int(x or 0) for x in m.groups()) if m else None


def ui_ver_pair(lang=None):
    """{"mw", "sim", "same", "older": "" | "sim" | "mw", "text"} - «MoveEye 3.34.0 · Sim 3.34.0 ✓» or «⚠ Simulator older …».
    3 tracks (Besitzer 03.11.2026): the numbers differ on purpose; «same» = the pair works together (each side at least the
    minimum of the other: SIM_MIN of MoveEye 545, «mw_min» of the simulator in /info), «older» = the side below that minimum."""
    info = SIM.get("info") or {}
    sv = str(info.get("ver") or info.get("version") or "")
    if not re.match(r"^\d+\.\d+\.\d+$", sv):
        m = re.search(r"\d+\.\d+\.\d+", str(info.get("name") or ""))
        sv = m.group(0) if m else sv
    a, b = ui_vnum(APP_VERSION), ui_vnum(sv)
    smin, mmin = ui_vnum(SIM_MIN), ui_vnum(str(info.get("mw_min") or "")) or (0, 0, 0)
    out = {"mw": APP_VERSION, "sim": sv, "same": bool(a and b and b >= smin and a >= mmin), "older": ""}
    if a and b and not out["same"]:
        out["older"] = "sim" if b < smin else "mw"
        out["need"] = SIM_MIN if out["older"] == "sim" else str(info.get("mw_min"))
    txt = f"MoveEye {APP_VERSION} · Sim {sv or '?'}"
    if out["same"]:
        txt += " ✓"
    elif out["older"]:
        txt = "⚠ " + tr("Simulator older" if out["older"] == "sim" else "MoveEye older", lang) + ": " + txt
    out["text"] = txt
    return out


_sim_status_639zb = sim_status


def sim_status():                                         # + 639zb: the version pair for the page «Simulator» (470 verPaint)
    r = _sim_status_639zb()
    try:
        if CFG.get("sim_on") and SIM.get("ok"):
            r["pair"] = dict(ui_ver_pair(cur_lang()), btn=tr("Update MoveEye", cur_lang()))
    except Exception:
        pass
    return r


# ---- ★3 diagnosis both ways ---------------------------------------------------------------------------------------------
_health_check_639zb = health_check


def health_check(lang=None):                              # + 639zb: the lines of the simulator, the version pair, pictures/s
    out = _health_check_639zb(lang)
    if not (CFG.get("sim_on") and SIM.get("ok") and time.time() - float(SIM.get("t") or 0) < 5):
        return out
    L = norm_lang(lang) if lang else cur_lang()
    out += ui_pair_items(L)
    for x in UIS["sim_diag"] or []:
        out.append({"id": "sim:" + str(x.get("id", "")), "icon": "🎮", "title": tr("Simulator", L) + ": " + str(x.get("title", "")),
                    "level": str(x.get("level", "off")), "text": str(x.get("text", "")), "tip": str(x.get("tip", ""))})
    return out


def ui_pair_items(L):
    """the version pair and the warning «too few pictures per second» (both sides show them)"""
    out = []
    vp = ui_ver_pair(L)
    out.append({"id": "sim:ver", "icon": "🔢", "title": tr("Versions", L), "level": "ok" if vp["same"] else "warn", "text": vp["text"],
                "tip": "" if vp["same"] else tr("The numbers may differ, but one program is older than the other one needs.", L)
                + " → " + tr("Update the simulator" if vp["older"] == "sim" else "Update MoveEye", L)})
    if str(CFG.get("source") or "").startswith("sim:"):
        f = float(STATE.get("fps") or 0)
        if 0 < f < 3.0:
            out.append({"id": "sim:fps", "icon": "🎞", "title": tr("Pictures from the simulator", L), "level": "warn",
                        "text": trf("MoveEye gets only {f} pictures/s from the simulator - it hardly detects anything (from about 3/s on it works)", L, f=f"{f:.1f}"),
                        "tip": tr("Make the simulator lighter (System → Graphics: Lite) or close other programs on the PC.", L)})
    return out


_diag_zip_639zb = diag_zip


def diag_zip():                                           # + 639zb: sim_diagnose.json and sim_protokoll.txt into the package
    raw = _diag_zip_639zb()
    if not (CFG.get("sim_on") and SIM.get("ok")):
        return raw
    import io as _io
    add = {}
    try:
        add["sim_diagnose.json"] = json.dumps({"pair": ui_ver_pair(), "items": (sim_control({"action": "mehr", "do": "diag"}) or {}).get("items")},
                                              indent=1, ensure_ascii=False, default=str)
    except Exception as e:
        add["sim_diagnose.json"] = json.dumps({"error": str(e)[:200]})
    try:
        add["sim_protokoll.txt"] = _scrub_text(str((sim_control({"action": "mehr", "do": "log"}) or {}).get("text") or ""))[-400000:]
    except Exception as e:
        add["sim_protokoll.txt"] = "error: " + str(e)[:200]
    buf = _io.BytesIO(raw)
    with zipfile.ZipFile(buf, "a", zipfile.ZIP_DEFLATED) as z:
        for k, v in add.items():
            z.writestr(k, v)
    return buf.getvalue()


# ---- P3: one language, one Simple / Expert --------------------------------------------------------------------------------
_save_settings_639zb = save_settings


def save_settings(*a, **k):                               # + 639zb: after a change of CFG lang the web follows (one language)
    try:
        ui_lang_unify()
    except Exception:
        pass
    return _save_settings_639zb(*a, **k)


_web_ui_update_639zb = web_ui_update


def web_ui_update(changes, removes=()):                   # + 639zb: «mw-lang» of a page = the device language
    r = _web_ui_update_639zb(changes, removes)
    if isinstance(changes, dict) and str(changes.get("mw-lang") or "") in LANGS and changes["mw-lang"] != cur_lang():
        CFG["lang"] = changes["mw-lang"]; UIS["lang_seen"] = CFG["lang"]
        _save_settings_639zb()
    return r


# wraps: page_modes
def page_modes():                                         # + 639zb (P3, E1): one Simple / Expert for everything - no page has its own
    return {}


def ui_mode_merge():
    """once: who had chosen Simple / Expert per page (586 «mw-page-mode») gets ONE choice - Expert if a page was on Expert
    (nothing disappears); the old entry stays in the settings (not deleted)"""
    if CFG.get("ui_mode_merged"):
        return None
    CFG["ui_mode_merged"] = True
    try:
        m = json.loads((CFG.get("web_ui") or {}).get("mw-page-mode") or "{}")
    except (TypeError, ValueError):
        m = {}
    vals = [v for v in (m.values() if isinstance(m, dict) else []) if v in ("simple", "expert")]
    if vals and "expert" in vals and CFG.get("ui_simple", True):
        CFG["ui_simple"] = False
        log_event("sys", "Simple / Expert now applies everywhere: Expert (a page was on Expert before)")
    return CFG["ui_simple"]


_load_settings_639zb = load_settings


def load_settings(*a, **k):                               # + 639zb: one Simple / Expert (taken over once), one language
    r = _load_settings_639zb(*a, **k)
    try:
        ui_mode_merge(); ui_lang_unify()
    except Exception as e:
        print(f"639zb: {e}")
    return r


# ---- the web: a small hint when the simulator changed the view, the version pair --------------------------------------------
def ui_sync_info(lang=None):
    vals = ui_values()
    return {"rev": UIS["rev"], "v": vals, "from_sim": UIS["from_sim"], "from_sim_t": UIS["from_sim_t"],
            "sim": bool(CFG.get("sim_on") and SIM.get("ok") and time.time() - float(SIM.get("t") or 0) < 5),
            "pair": ui_ver_pair(lang), "upd_msg": UIS["upd_msg"], "lock": bool(CFG.get("lock_on"))}


UIS_JS = r"""<script id="uis-js">(function(){
// 639zb: the view (Simple / Expert, symbols, language …) was changed in the simulator - a small hint instead of reloading by itself
var TX=/*TX*/{}, R=null, L=function(){try{return (typeof LANG!=="undefined"&&LANG)||localStorage.getItem("mw-lang")||"de";}catch(e){return "de";}};
function t(k){var d=TX[L()]||{};return d[k]||k;}
function hint(){if(document.getElementById("uis-hint"))return;var b=document.createElement("div");b.id="uis-hint";b.setAttribute("role","status");
 b.style.cssText="position:fixed;left:50%;transform:translateX(-50%);bottom:4.2rem;z-index:80;background:var(--panel,#1b222c);color:var(--txt,#e6edf3);border:1px solid var(--line,#334);border-radius:99px;padding:.35rem .5rem .35rem .9rem;font-size:.85rem;box-shadow:0 4px 16px #0006;display:flex;gap:.6rem;align-items:center;max-width:calc(100vw - 32px)";
 var s=document.createElement("span");s.textContent="🎮 "+t("View changed in the simulator");var k=document.createElement("button");k.type="button";k.textContent="↻ "+t("Reload");
 k.style.cssText="padding:.25rem .7rem;border-radius:99px";k.onclick=function(){location.reload();};b.append(s,k);document.body.appendChild(b);}
function poll(){if(document.hidden)return;fetch("/api/ui_sync",{cache:"no-store"}).then(function(x){return x.json();}).then(function(j){
 if(!j||j.rev==null)return;if(R===null){R=j.rev;return;}if(j.rev!==R){R=j.rev;
  try{var pl=j.v&&j.v.icons==="plain";localStorage.setItem("mw-icons",pl?"plain":"color");document.body.classList.toggle("icplain",pl);}catch(e){}
  if(j.from_sim&&j.from_sim.some(function(k){return k!=="icons";})&&Date.now()/1000-j.from_sim_t<30)hint();}}).catch(function(){});}
setInterval(poll,8000);setTimeout(poll,1500);})();</script>"""


def ui_tx():
    keys = ("View changed in the simulator", "Reload")
    out = {"de": {k: DE.get(k, k) for k in keys}, "en": {k: k for k in keys}}
    for L in ("fr", "it", "rm"):
        out[L] = {k: TRX[L].get(k) or k for k in keys}
    return out


_render_page_639zb = render_page


def render_page(page, active):                            # + 639zb: the hint on every page with tabs
    out = _render_page_639zb(page, active)
    if '<nav class="nav">' not in out or 'id="uis-js"' in out:
        return out
    i = out.rfind("</body>")
    tag = UIS_JS.replace("/*TX*/{}", json.dumps(ui_tx(), ensure_ascii=False).replace("</", "<\\/"))
    return out[:i] + tag + out[i:] if i >= 0 else out + tag


_smalltv_routes_639zb = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zb: /api/ui_sync (GET: rev, values, version pair; POST: update)
    _smalltv_routes_639zb(app, reply, body)
    from flask import request as _rq

    @app.route("/api/ui_sync", methods=["GET", "POST"])
    def ui_sync_api_():
        if _rq.method == "POST":
            d = body()
            do = str(d.get("do") or "")
            if do == "update_sim":
                try:
                    sim_control({"action": "press", "id": "update_now"})
                    return reply({"ok": True})
                except Exception as e:
                    return reply({"ok": False, "error": str(e)[:120]})
            if do == "update_mw":
                return reply({"ok": ui_update_mw(ui_ver_pair()["sim"], "web")})
            return reply({"ok": False, "error": "unknown"})
        return reply(ui_sync_info(_rq.args.get("lang")))


# ---- the manual (HELP_PAGE of 540): one paragraph in «Tipps & Tricks», German and English (fr / it / rm: HELP_X falls back)
for _a, _b in (('<section id="tips" data-icon="🧭" class="tips"><h2>Tipps &amp; Tricks</h2>',
                "<p><b>🎮 MoveEye und Simulator zeigen dasselbe:</b> Einfach / Experte (eine Wahl für alle Seiten, das Pi-Fenster und den "
                "Simulator), Symbole farbig / schlicht, die Sprache (eine für Web und Gerät), «Bewegung reduzieren», «Stimme», Rundgang, Blinki "
                "und «Neu in …» gleichen sich von selbst ab – die letzte Änderung gilt, sonst MoveEye. Hell / Dunkel / Rotlicht bleibt pro Gerät. "
                "Der Simulator zeigt dazu den Zustand Aus / Wachsam / Voll in den Farben der Status-LED, die letzte Push-Meldung, das "
                "Versions-Paar «MoveEye 3.x · Sim 3.x ✓» und im Bedienermodus nur die Hauptschalter (Entsperren mit der PIN von MoveEye). "
                "Die Selbstdiagnose und das Diagnose-Paket enthalten auch die Werte des Simulators.</p>"),
               ('<section id="tips" data-icon="🧭" class="tips"><h2>Tips &amp; tricks</h2>',
                "<p><b>🎮 MoveEye and the simulator show the same:</b> Simple / Expert (one choice for every page, the Pi window and the "
                "simulator), symbols coloured / plain, the language (one for the web and the device), «Reduce motion», «Voice», tour, Blinki "
                "and «New in …» are shared by themselves – the last change counts, otherwise MoveEye. Light / dark / red light stays per device. "
                "The simulator also shows the state Off / Watchful / Full in the colours of the status LED, the last push message, the "
                "version pair «MoveEye 3.x · Sim 3.x ✓» and, in operator mode, only the main switches (unlock with the PIN of MoveEye). "
                "The self-diagnosis and the diagnosis package contain the values of the simulator too.</p>")):
    if _a in HELP_PAGE:
        HELP_PAGE = HELP_PAGE.replace(_a, _a + _b, 1)


# ---- self-test ------------------------------------------------------------------------------------------------------------
def ui_sync_selftest():
    """a value changed on one side appears on the other (without picture): MoveEye -> simulator (rev), simulator -> MoveEye
    (set), same packet (MoveEye wins), unlock with the PIN, one language, one Simple / Expert, level, version pair"""
    keep = {k: json.loads(json.dumps(CFG.get(k))) for k in ("ui_simple", "web_ui", "lang", "reduce_motion", "voice_mode", "tours_auto",
                                                              "blinki_on", "news_popup", "news_links", "lock_on", "lock_pin", "lock_snap", "ui_mode_merged")}
    keepu = dict(UIS); keepu["mine"] = set(UIS["mine"])
    sim_keep = {k: SIM.get(k) for k in ("follower", "info")}
    try:
        CFG["ui_simple"] = True; CFG["lang"] = "de"; CFG["web_ui"] = {"mw-lang": "de"}; UIS["lang_seen"] = "de"; UIS["last"] = None
        SIM["follower"] = False
        d = sim_state()
        assert d["ui"]["v"]["simple"] is True and d["ui"]["v"]["lang"] == "de", "639zb: ui missing"
        r0 = d["ui"]["rev"]
        CFG["ui_simple"] = False                             # MoveEye changes -> rev + 1, the value goes out
        d = sim_state()
        assert d["ui"]["rev"] == r0 + 1 and d["ui"]["v"]["simple"] is False, "639zb: own change not counted"
        n0 = UIS["took"]
        simvals_take_ui = {"ui": {"n": n0 + 1, "base": d["ui"]["rev"], "set": {"icons": "plain", "voice": "subtitles", "bad": 1, "lang": "xx"}}}
        ui_take(simvals_take_ui["ui"])                        # the simulator changes -> MoveEye takes it over
        assert ui_values()["icons"] == "plain" and CFG["voice_mode"] == "subtitles" and CFG["lang"] == "de", "639zb: change of the simulator lost"
        d = sim_state()
        assert d["ui"]["took"] == n0 + 1 and d["ui"]["v"]["icons"] == "plain", "639zb: took / value not sent back"
        ui_take({"n": n0 + 1, "set": {"icons": "color"}})     # the same number again: ignored (no ping-pong)
        assert ui_values()["icons"] == "plain", "639zb: old change taken twice"
        CFG["tours_auto"] = False; sim_state()                # same packet: MoveEye wins
        ui_take({"n": n0 + 2, "set": {"tours": True, "news": False}})
        assert CFG["tours_auto"] is False and CFG["news_popup"] is False, "639zb: same packet - MoveEye must win (and the other key counts)"
        ui_take({"n": n0 + 3, "set": {"news_links": "off"}})       # Links zu Neuerungen (639zc): the simulator switches them off
        assert CFG["news_links"] == "off" and ui_values()["news_links"] == "off", "639zb: «Links zu Neuerungen» from the simulator"
        ui_take({"n": n0 + 4, "set": {"news_links": "bad"}})
        assert CFG["news_links"] == "off", "639zb: a bad value of «Links zu Neuerungen» must be ignored"
        SIM["follower"] = True                                # only the leading MoveEye
        assert "ui" not in sim_state(), "639zb: a watching MoveEye must not share the view"
        SIM["follower"] = False
        web_ui_update({"mw-lang": "fr"})                     # one language: web -> device and device -> web
        assert CFG["lang"] == "fr", "639zb: web language did not reach the device"
        CFG["lang"] = "it"; ui_values()
        assert CFG["web_ui"]["mw-lang"] == "it", "639zb: device language did not reach the web"
        CFG["ui_mode_merged"] = False; CFG["ui_simple"] = True
        CFG["web_ui"] = dict(CFG["web_ui"], **{"mw-page-mode": json.dumps({"live": "simple", "settings": "expert"})})
        assert ui_mode_merge() is False and page_simple("live") is False and "mw-page-mode" in CFG["web_ui"], "639zb: one Simple / Expert"
        CFG["lock_pin"] = _pin_hash("4321"); CFG["lock_on"] = True; CFG["lock_snap"] = {}
        ui_take({"unlock": {"n": UIS["lock_n"] + 1, "pin": "1111"}})
        assert CFG["lock_on"] and UIS["lock_msg"] == "wrong PIN", "639zb: wrong PIN must not unlock"
        assert sim_state()["lock"]["on"] is True
        ui_take({"unlock": {"n": UIS["lock_n"] + 1, "pin": "4321"}})
        assert not CFG["lock_on"] and UIS["lock_msg"] == "ok", "639zb: unlocking with the PIN of MoveEye"
        assert ui_level()["id"] in ("off", "watch", "full", "walktest") and ui_level()["col"].startswith("#"), "639zb: level"
        SIM["info"] = {"version": APP_VERSION}
        assert ui_ver_pair("de")["same"] and ui_ver_pair("de")["text"].endswith("✓"), "639zb: version pair"
        SIM["info"] = {"version": "3.0.1"}
        assert ui_ver_pair("de")["older"] == "sim" and ui_ver_pair("de")["text"].startswith("⚠"), "639zb: older simulator"
        SIM["info"] = {"version": SIM_MIN}                # 3 tracks: another number, but new enough = ✓
        assert ui_ver_pair("de")["same"] and ui_ver_pair("de")["older"] == "", "639zb: 3 tracks, different numbers that fit"
        SIM["info"] = {"version": "99.0.0", "mw_min": "99.0.0"}
        assert ui_ver_pair("de")["older"] == "mw" and ui_ver_pair("de")["need"] == "99.0.0", "639zb: the simulator needs a newer MoveEye"
        assert "sim_min" in sim_state() and sim_state()["sim_min"] == SIM_MIN, "639zb: sim_min in the state"
        js = render_page("<html><head></head><body><header><h1>MoveEye</h1><!--NAV--></header><main></main></body></html>", "live")
        assert js.count('id="uis-js"') == 1 and "Ansicht im Simulator" in js, "639zb: hint script"
        sh = UI_GEMEINSAM.get("shared") or {}
        assert all(k in sh for k in UIS_KEYS) and "theme" in (UI_GEMEINSAM.get("local") or []), "639zb: ui_gemeinsam.json «shared» / «local»"
        assert all(TRX[L].get(k) for L in ("fr", "it", "rm") for k in _HX_UIS), "639zb: texts"
        assert "MoveEye und Simulator zeigen dasselbe" in HELP_PAGE and "MoveEye and the simulator show the same" in HELP_PAGE, "639zb: manual"
    finally:
        CFG.update(keep); UIS.clear(); UIS.update(keepu); SIM.update(sim_keep)
    return "view shared both ways (" + ", ".join(UIS_KEYS) + "), MoveEye wins the same packet, PIN, one language, one Simple / Expert"


def ui_more_selftest():
    """★5: the entries of «Mehr» both programs have - same order (ui_gemeinsam.json «more_order»), names in 5 languages"""
    U = UI_GEMEINSAM
    order = U.get("more_order") or []
    items = {m["id"]: m for m in U.get("more") or []}
    assert order and all(i in items for i in order), "639zb: more_order / more"
    marks = {"help": 'href="/help"', "case": 'href="/case"', "build": 'href="/build"', "feedback": 'id="m-fb"', "about": 'id="m-about"', "werk": 'id="g2-sys"'}
    pos = [MORE_PAGE.find(marks.get(i, "\0")) for i in order]
    assert all(p >= 0 for p in pos) and pos == sorted(pos), f"639zb: «Mehr» of MoveEye not in the order {order}: {pos}"
    for i in order:
        mw = items[i].get("mw") or {}
        for lg in UI_GEM_LANGS:
            want = (mw.get("names") or {}).get(lg)
            assert not want or ui_gem_tr(mw["key"], lg) == want, f"639zb: «Mehr» {i} ({lg}): «{ui_gem_tr(mw['key'], lg)}» instead of «{want}»"
    gd = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulator3d", "scripts", "mehr.gd")
    if os.path.isfile(gd):
        with open(gd, encoding="utf-8") as f:
            m = re.search(r"\nconst ITEMS := \[(.*?)\]\]\n", f.read(), re.S)
        rows = re.findall(r'\["(\w+)", "\w+", "([^"]*)"', m.group(1) + "]]") if m else []
        ids = [r[0] for r in rows]
        sp = [ids.index((items[i].get("sim") or {}).get("row", "?")) if (items[i].get("sim") or {}).get("row") in ids else -1 for i in order]
        assert all(p >= 0 for p in sp) and sp == sorted(sp), f"639zb: «Mehr» of the simulator not in the order {order}: {sp}"
        for i in order:
            sm = items[i].get("sim") or {}
            assert dict(rows).get(sm.get("row")) == sm.get("key"), f"639zb: «Mehr» {i}: simulator name «{dict(rows).get(sm.get('row'))}» instead of «{sm.get('key')}»"
    return f"{len(order)} entries of «Mehr» in both programs in the same order: " + " · ".join(order)


SELFTEST_EXTRA.append(("View shared with the simulator (ui, 639zb)", ui_sync_selftest))
SELFTEST_EXTRA.append(("«Mehr» in the same order MoveEye ↔ simulator (ui_gemeinsam.json «more», 639zb)", ui_more_selftest))
