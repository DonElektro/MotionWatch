#@ MoveEye – Teil 639zzzzk_blinki_y_mehr: «Blinki fragen» Stufe 2 – 🔥 Lagerfeuer-Geschichten (Kinder / Erwachsene, Orte vom eigenen Platz), 🦌 Naturführer (zu dem, was MoveEye gesehen hat), 🎤 Quizmaster (neue Fragen für die Spielecke, Teil 320). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Geschichten   etwa 250 Wörter; «Kinder» (für Kinder-Benutzer immer): freundlich, nichts Gruseliges, keine Gewalt, gutes Ende;
#               ein Wortfilter prüft den Text, solange er kommt - trifft er, bricht Blinki ab und sagt es freundlich.
#               Orte: eigene Namen der Orte im Verlauf (places.json), Punkte des Kopfes (Teach-in) und Zonen - nie Koordinaten.
# Naturführer   die Sichtungen der letzten 7 Tage (Art, Zeit, Dauer; 090 / 425) als Fakten; Wissen über die Art darf das Modell
#               dazugeben. Ein Bild nur mit Cloud und Einzel-OK (639zzzzk_blinki_y_cloud). Recht: Aufnahmen («rec»).
# Quizmaster    neue Fragen als JSON [{q, a}], geprüft (Länge, doppelt, höchstens 10); «In die Spielecke» hängt sie an QUIZ an
#               (gemerkt in CFG blinki_quiz, höchstens 200) - Recht: Spiele («games»).
# ----------------------------------------------------------------------------
# Der Programmtext dieses Teils steht in EINEM Literal (Besitzer / Koordinator 15.11.2026: Hauptdatei klein): werkzeuge/bauen.py
# legt es in die Zusatz-ZIP, beim Start läuft es hier an seinem Platz (zd_exec, Teil 639zzzzk_blinki_kern). Ohne ZIP gibt es
# «Blinki fragen» nicht - es gehört nicht zu Start, Schutz oder Alarm. Die ZIP ist über ZD_SHA256 (Teil 012) mit signiert.
BLINKI_MEHR_PY = r'''BLINKI_MODE_NEED.update({"geschichte": "", "natur": "rec", "quiz": "games"})
BLINKI_MODE_ICON.update({"geschichte": ("🔥", "Campfire stories"), "natur": ("🦌", "Nature guide"), "quiz": ("🎤", "Quizmaster")})
BLINKI_KID_MODES.add("geschichte")
BLINKI_EXTRA_MODES = ("geschichte", "natur", "quiz")
BLINKI_NOQ_MODES = ("fehler", "geschichte", "natur", "quiz")
BLINKI_QUIZ_MAX = 200
CFG.setdefault("blinki_quiz", []); DEFAULTS.setdefault("blinki_quiz", [])
USER_SETTINGS_DENY.add("blinki_quiz")
BLINKI_KID_BAD = re.compile(r"\b(tot|töte|tötet|getötet|blut|mord|leiche|waffe|messer|gewehr|pistole|sterb|gestorben|horror|kill|dead|blood|murder|weapon|gun|knife|"
                            r"sang|mort|tuer|arme|couteau|sangue|morto|uccid|coltello|pistola|sex)", re.I)


def blinki_places():
    """names of the own site (never coordinates): own place names, points of the head, zones"""
    out = []
    try:
        for v in (places_names() or {}).values():
            if isinstance(v, dict) and v.get("own"):
                out.append(str(v["own"]))
    except Exception:
        pass
    try:
        out += [wp_name(w) for w in WAYPOINTS]
    except Exception:
        pass
    try:
        out += [str(z.get("name") or "").strip() for z in ZONES if not str(z.get("name") or "").startswith("Zone ")]
    except Exception:
        pass
    seen, res = set(), []
    for x in out:
        x = re.sub(r"[\x00-\x1f<>]", "", str(x)).strip()[:40]
        if x and x.lower() not in seen:
            seen.add(x.lower()); res.append(x)
    return res[:12]


def blinki_seen(L, days=7):
    """what MoveEye saw in the last days (sightings), as lines for the model"""
    try:
        b = datetime.now(); a = b - timedelta(days=days)
        lst = _tl_sightings(a, b, L)
    except Exception:
        lst = []
    lines, count = [], {}
    for e in sorted(lst, key=lambda x: -x["t"])[:25]:
        nm = str(e.get("name") or e.get("label") or "")
        count[nm] = count.get(nm, 0) + 1
        lines.append("- %s: %s%s" % (datetime.fromtimestamp(e["t"]).strftime("%a %d.%m. %H:%M"), nm,
                                    (" (%d s)" % int(e["dur"])) if isinstance(e.get("dur"), (int, float)) else ""))
    return lines, count


def blinki_messages_more(mode, q, L, prev, extra):
    """(messages, sources, links, fixes) of the modes of stage 2"""
    lang = _BLINKI_LANG_NAME.get(L, "English")
    sources, links = [], []
    if mode == "geschichte":
        kid = bool(extra.get("kid"))
        place = str(extra.get("place") or "")
        place = place if place in blinki_places() else ""
        _lines, cnt = blinki_seen(L)
        sys_ = ("You are Blinki, the friendly eye of MoveEye, telling a campfire story in %s. About 250 words, short paragraphs, a title in the first line. " % lang
                + ("For children aged 5 to 10: warm, funny, a little exciting but never scary, no violence, no weapons, no death, no blood, a happy end. "
                   if kid else "For adults: cosy and a little spooky is fine, but no gore, nothing cruel, nothing sexual. ")
                + "Blinki may appear in the story as a little eye that watches the camp. "
                + ("The story happens here: %s. " % place if place else "")
                + ("Animals seen near the camp recently: %s. " % ", ".join(list(cnt)[:5]) if cnt else ""))
        user = q or tr("Tell a campfire story.", L)
        extra_job = {"max_tokens": 650, "temp": 0.8, "kid": kid}
    elif mode == "natur":
        lines, cnt = blinki_seen(L)
        sys_ = ("You are Blinki, a nature guide for campers, in %s. Explain the animals MoveEye saw near the camp: how they live, when they are active, "
                "how to watch them without disturbing them and what to keep in mind (food, safety). Keep it short (at most 10 sentences). "
                "What MoveEye saw is ONLY what is listed below; do not invent sightings. If nothing was seen, say so and give two tips. "
                "General knowledge about a species is fine. Never suggest to switch the protection off.\n\nSEEN BY MOVEEYE (last 7 days):\n" % lang
                + ("\n".join(lines) if lines else "(nothing)"))
        user = q or tr("What did MoveEye see, and what should I know about these animals?", L)
        sources = [{"title": tr("Sightings", L) + " (7 d)", "href": "/diary"}]
        links = [{"title": tr("History", L), "href": "/recordings"}]
        extra_job = {"max_tokens": 450}
    else:
        n = max(3, min(10, int(extra.get("n") or 8))) if str(extra.get("n") or "8").isdigit() else 8
        sys_ = ("You are Blinki, the quizmaster of a campfire quiz in %s. Write %d NEW quiz questions with short answers for a mixed group "
                "(families, children from 10). Topics: nature, animals, Switzerland, camping, weather, stars, everyday knowledge. Only facts you are sure of. "
                "Reply ONLY with a JSON array like [{\"q\": \"question\", \"a\": \"answer\"}] - no other text." % (lang, n))
        user = q or tr("New questions, please.", L)
        extra_job = {"max_tokens": 700, "temp": 0.7}
    extra.update(extra_job)
    msgs = [{"role": "system", "content": sys_}, {"role": "user", "content": str(user)[:600]}]
    return msgs, sources, links, []


_blinki_ask_mehr = blinki_ask


# wraps: blinki_ask
def blinki_ask(mode, q, lang=None, prev=None, who="web", client="", extra=None):   # + 639zzzzk_blinki_y_mehr: the job settings of the modes
    extra = dict(extra or {})
    for k in ("max_tokens", "temp", "quiz"):
        extra.pop(k, None)                                  # never from a page
    if mode == "quiz":
        extra["n"] = extra.get("n") or 8
    j, err = _blinki_ask_mehr(mode, q, lang, None if mode in BLINKI_EXTRA_MODES else prev, who, client, extra)
    if j is not None and mode in BLINKI_EXTRA_MODES:
        j.update({k: extra[k] for k in ("max_tokens", "temp", "kid") if k in extra})
    return j, err


def blinki_quiz_parse(text):
    """the questions of an answer of the quizmaster: [{q, a}] (checked), [] when nothing usable"""
    m = re.search(r"\[.*\]", str(text or ""), re.S)
    if not m:
        return []
    try:
        lst = json.loads(m.group(0))
    except ValueError:
        return []
    have = {re.sub(r"\W+", "", q_.lower()) for q_, _a in QUIZ}
    out = []
    for x in lst if isinstance(lst, list) else []:
        if not isinstance(x, dict):
            continue
        q_ = re.sub(r"[\x00-\x1f<>]", " ", str(x.get("q") or "")).strip()
        a_ = re.sub(r"[\x00-\x1f<>]", " ", str(x.get("a") or "")).strip()
        k = re.sub(r"\W+", "", q_.lower())
        if 8 <= len(q_) <= 180 and 1 <= len(a_) <= 90 and k not in have:
            have.add(k); out.append({"q": q_, "a": a_})
        if len(out) >= 10:
            break
    return out


def blinki_quiz_take(jid, idx=None, who="web"):
    """put the questions of a quiz answer into the game corner (QUIZ + CFG blinki_quiz) -> (ok, reason, n)"""
    j = BLINKI["jobs"].get(str(jid or ""))
    if j is None or j.get("mode") != "quiz" or j["state"] != "done":
        return False, "unknown action", 0
    lst = blinki_quiz_parse(j["text"])
    if isinstance(idx, list):
        lst = [x for i, x in enumerate(lst) if i in idx]
    if not lst:
        return False, "no usable questions", 0
    saved = [x for x in CFG.get("blinki_quiz") or [] if isinstance(x, dict)]
    saved = (saved + lst)[-BLINKI_QUIZ_MAX:]
    CFG["blinki_quiz"] = saved
    save_settings()
    QUIZ.extend((x["q"], x["a"]) for x in lst)
    j["taken"] = True
    log_event("sys", f"Blinki: {len(lst)} quiz questions into the game corner ({who})")
    return True, "", len(lst)


for _x in CFG.get("blinki_quiz") or []:                       # the questions of before (after a restart)
    if isinstance(_x, dict) and _x.get("q") and _x.get("a") and (_x["q"], _x["a"]) not in QUIZ:
        QUIZ.append((str(_x["q"])[:180], str(_x["a"])[:90]))

_blinki_job_view_mehr = blinki_job_view


# wraps: blinki_job_view
def blinki_job_view(j, start=0):                                # + 639zzzzk_blinki_y_mehr: children's filter, quiz questions
    if j.get("kid") and not j.get("replaced") and BLINKI_KID_BAD.search(j["text"]):
        j["stop"] = True
        j.update(replaced=True, text=tr("Hmm, this story went the wrong way - Blinki tells you another one. Tap 🔥 again!", j.get("lang")))
    if j.get("replaced"):
        start = 0
    v = _blinki_job_view_mehr(j, start)
    v["full"] = bool(j.get("replaced"))
    if j.get("replaced") and v["state"] == "stopped":
        v["state"] = "done"
    if j.get("mode") == "quiz" and v["state"] == "done":
        v["quiz"] = blinki_quiz_parse(j["text"]); v["taken"] = bool(j.get("taken"))
    v["image"] = bool(j.get("sent_image"))
    return v


_blinki_state_mehr = blinki_state


# wraps: blinki_state
def blinki_state():                                             # + 639zzzzk_blinki_y_mehr: places for the stories
    st = _blinki_state_mehr()
    st["places"] = blinki_places()
    st["quiz_n"] = len(CFG.get("blinki_quiz") or [])
    return st


_role_allows_mehr = role_allows


# wraps: role_allows
def role_allows(role, path, method, d, perms=None):           # + 639zzzzk_blinki_y_mehr: quiz questions into the game corner = right «games»
    if path == "/api/ki/quiz" and method == "POST" and role != "admin":
        P = set(perms) if perms is not None else set(ROLE_PERMS.get(ROLE_OLD.get(role, role), ()))
        return "games" in P
    return _role_allows_mehr(role, path, method, d, perms)


_smalltv_routes_mehr = smalltv_routes


def smalltv_routes(app, reply, body):                          # + 639zzzzk_blinki_y_mehr: POST /api/ki/quiz
    _smalltv_routes_mehr(app, reply, body)
    from flask import g

    @app.route("/api/ki/quiz", methods=["POST"])
    def blinki_api_quiz():
        d = body(); L = norm_lang(d.get("lang"))
        ok_, err, n = blinki_quiz_take(d.get("id"), d.get("take") if isinstance(d.get("take"), list) else None, getattr(g, "user", "") or "admin")
        return reply({"ok": ok_, "error": None if ok_ else tr_err(err, L), "n": n}, 200 if ok_ else 400)
'''
zd_exec(BLINKI_MEHR_PY, '639zzzzk_blinki_y_mehr.py')
