#@ MoveEye – Teil 639zzzzk_blinki_wissen: «Blinki fragen» – Wissen: Suche in der Anleitung und in der Hilfe der Einstellungen (BM25, ohne zweites Modell), «Öffnen»-Ziele, Fehlersuche aus Protokoll + Selbstdiagnose (nur lesen), Vorschläge nur mit OK. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Frag MoveEye  Die Frage sucht in der Anleitung (HELP_PAGE Deutsch / Englisch, HELP_X fr / it / rm, je Abschnitt in Stücke
#               von ~90 Wörtern) und in der Hilfe der Einstellungen (Name + SET_HELP + Empfehlung) mit BM25 (Wortstämme grob,
#               Umlaute gleich). Die besten 3 Stücke (~600 Wörter-Stücke) gehen mit einer festen Vorgabe an das Modell. Die
#               «Öffnen»-Knöpfe kommen NICHT vom Modell, sondern aus den gefundenen Stücken: Abschnitt → /help#id,
#               Einstellung → news_href (/settings?setting=K, Teil 137) - so führt kein erfundener Link irgendwohin.
#               Ohne Daten-ZIP ist die Anleitung leer: dann nur die Einstellungen (keine Ausnahme).
# Fehlersuche   liest nur: Selbstdiagnose (health_check, mit Fehler-Katalog 639u), die letzten Protokoll-Zeilen
#               (STATE events, Adressen gekürzt wie im Diagnose-Paket: _scrub_text), CPU, Temperatur, Speicher, Strom.
#               Vorschläge = die Behebungen des Fehler-Katalogs (fx_run, 639u) – nur Knopf «Vorschlag», ausgeführt erst nach
#               einem eigenen OK (POST mit ok:true, nur Administrator). Keine Behebung schaltet den Schutz aus (BLINKI_FIX_DENY).
# ----------------------------------------------------------------------------
# Der Programmtext dieses Teils steht in EINEM Literal (Besitzer / Koordinator 15.11.2026: Hauptdatei klein): werkzeuge/bauen.py
# legt es in die Zusatz-ZIP, beim Start läuft es hier an seinem Platz (exec in den gemeinsamen Namen). Ohne ZIP gibt es
# «Blinki fragen» nicht - es gehört nicht zu Start, Schutz oder Alarm. Die ZIP ist über ZD_SHA256 (Teil 012) mit signiert.
BLINKI_WISSEN_PY = r'''BLINKI_IDX = {}
BLINKI_FIX_DENY = re.compile(r"protect|schutz|arm|alarm_off|disarm|aus$", re.I)
_BLINKI_STOP = set("der die das und oder ein eine einen einem eines ist sind wie was wo wann warum ich du er sie es wir ihr mit "
                   "von zu im in am an auf aus bei für fur nicht kann muss soll wird den dem des the a an and or is are how what "
                   "where when why i you it to of in on for with not can do does le la les et ou un une est il elle pour avec "
                   "il lo la e o un una è per con non ch che".split())
_BLINKI_WORD = re.compile(r"[a-zà-ÿ0-9]{2,}")
_BLINKI_UML = str.maketrans({"ä": "a", "ö": "o", "ü": "u", "ß": "ss", "é": "e", "è": "e", "à": "a", "ò": "o", "ì": "i", "ù": "u"})


def blinki_words(text):
    """the search words of a text: lower case, umlauts plain, rough stems (German / French / Italian / English endings)"""
    out = []
    for w in _BLINKI_WORD.findall(str(text or "").lower().translate(_BLINKI_UML)):
        if w in _BLINKI_STOP:
            continue
        for suf in ("ungen", "ung", "en", "er", "es", "e", "n", "s"):
            if len(w) > len(suf) + 3 and w.endswith(suf):
                w = w[:-len(suf)]; break
        out.append(w)
    return out


def _blinki_plain(html):
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S | re.I)
    t = re.sub(r"<br\s*/?>|</(p|li|h\d|div|tr)>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    import html as _h
    t = _h.unescape(t)
    return re.sub(r"[ \t\r\f\v]+", " ", re.sub(r"\n\s*\n+", "\n", t)).strip()


def _blinki_help_html(L):
    """the manual in one language: de / en from HELP_PAGE, fr / it / rm from HELP_X (else English)"""
    hp = HELP_PAGE if isinstance(HELP_PAGE, str) else ""
    i = hp.find('<div lang="en">')
    if L == "de":
        return hp[:i] if i > 0 else hp
    if L in ("fr", "it", "rm") and isinstance(globals().get("HELP_X"), dict) and HELP_X.get(L):
        return HELP_X[L]
    return hp[i:] if i > 0 else ""


def blinki_chunks(L):
    """[{kind, id, title, text, href}] of the manual and of the settings in language L"""
    out = []
    for m in re.finditer(r'<section id="([A-Za-z0-9_-]+)"[^>]*>(.*?)</section>', _blinki_help_html(L), re.S):
        sid, body = m.group(1), m.group(2)
        h = re.search(r"<h2[^>]*>(.*?)</h2>", body, re.S)
        title = _blinki_plain(h.group(1)) if h else sid
        words = _blinki_plain(body[h.end():] if h else body).split()
        for k in range(0, max(1, len(words)), 80):
            piece = " ".join(words[max(0, k - 10):k + 90])
            if piece:
                out.append({"kind": "help", "id": sid, "title": title, "text": piece, "href": "/help#" + sid})
    seen = set()
    for row in list(TOGGLES) + list(SLIDERS) + list(TEXTS):
        try:
            sec, key, label = row[0], row[1], row[2]
        except (IndexError, TypeError):
            continue
        if key in seen or key not in CFG:                    # only names and help texts, never a value
            continue
        seen.add(key)
        hlp = SET_HELP.get(key) if isinstance(SET_HELP.get(key), (list, tuple)) else ()
        txt = tr(label, L) + ". " + " ".join(tr(x, L) for x in hlp[:2] if isinstance(x, str))
        href = news_href({"einstellung": key}) if "news_href" in globals() else "/settings?setting=" + key
        out.append({"kind": "set", "id": key, "title": tr(sec, L) + " → " + tr(label, L), "text": txt, "href": href})
    return out


def blinki_index(L):
    """the search index of one language (made once, again when the manual changes)"""
    L = norm_lang(L)
    sig = (len(HELP_PAGE) if isinstance(HELP_PAGE, str) else 0, len(TOGGLES), len(SET_HELP))
    ix = BLINKI_IDX.get(L)
    if ix and ix["sig"] == sig:
        return ix
    import math
    ch = blinki_chunks(L)
    docs = [blinki_words(c["title"] + " " + c["title"] + " " + c["text"]) for c in ch]
    df = {}
    for d in docs:
        for w in set(d):
            df[w] = df.get(w, 0) + 1
    n = len(docs) or 1
    ix = {"sig": sig, "chunks": ch, "docs": [{w: d.count(w) for w in set(d)} for d in docs], "len": [len(d) for d in docs],
          "avg": (sum(len(d) for d in docs) / n) or 1.0, "idf": {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}}
    BLINKI_IDX[L] = ix
    return ix


def blinki_search(q, L, k=3):
    """the k best pieces for a question (BM25; a word that only starts like an indexed word counts half - compounds)"""
    ix = blinki_index(L)
    qw = blinki_words(q)
    if not qw or not ix["chunks"]:
        return []
    k1, b = 1.4, 0.75
    vocab = ix["idf"]
    terms = []
    for w in set(qw):
        if w in vocab:
            terms.append((w, 1.0))
        elif len(w) >= 5:
            terms += [(v, 0.5) for v in vocab if v.startswith(w) or (len(v) >= 5 and w.startswith(v))][:6]
    res = []
    for i, tf in enumerate(ix["docs"]):
        s = 0.0
        for w, wt in terms:
            f = tf.get(w)
            if f:
                s += wt * vocab[w] * f * (k1 + 1) / (f + k1 * (1 - b + b * ix["len"][i] / ix["avg"]))
        if s > 0:
            res.append((s, i))
    res.sort(reverse=True)
    out, ids = [], set()
    for s, i in res:
        c = ix["chunks"][i]
        if (c["kind"], c["id"]) in ids and len(out) >= 2:
            continue
        ids.add((c["kind"], c["id"]))
        out.append(dict(c, score=round(s, 2)))
        if len(out) >= k:
            break
    return out


_BLINKI_LANG_NAME = {"de": "German (Swiss spelling: always «ss», never «ß»)", "fr": "French", "it": "Italian",
                     "rm": "Romansh (Rumantsch Grischun; if unsure, German)", "en": "English"}
BLINKI_RULES = ("You are Blinki, the friendly eye of MoveEye, a camera guard (Raspberry Pi) for camping, house and garden. "
                "Answer in {lang}. Keep it short: at most 6 sentences or a short numbered list. Use ONLY the facts below; "
                "if they do not answer the question, say so and suggest the manual. Never invent menu names, buttons or numbers. "
                "Never suggest to switch the protection, the alarm or the camera off. You cannot change settings yourself.")


def blinki_messages(mode, q, L, prev=None, extra=None):
    """(messages, sources, links, fixes) for one question"""
    L = norm_lang(L)
    if mode in BLINKI_EXTRA_MODES:
        return blinki_messages_more(mode, q, L, prev, extra or {})
    rules = BLINKI_RULES.format(lang=_BLINKI_LANG_NAME.get(L, "English"))
    sources, links, fixes = [], [], []
    if mode == "fehler":
        q = q or tr("Does my MoveEye have a problem? Please check it.", L)
        facts, fixes = blinki_diag_facts(L)
        sys_ = rules + " Task: explain the likely cause of the problem in plain words and what the user can check. " \
            "The facts are the self-check and the log of the device right now.\n\nFACTS:\n" + facts
        sources = [{"title": tr("Self-check", L), "href": "/hilfe/fehler/"}, {"title": tr("Log", L), "href": "/log"}]
        for fx in fixes:
            if fx.get("help"):
                links.append({"title": fx["title"], "href": fx["help"]})
    else:
        hits = blinki_search(q, L, 3)
        facts = "\n\n".join("[%s] %s" % (h["title"], h["text"]) for h in hits) or "(nothing found in the manual)"
        sys_ = rules + "\n\nFACTS FROM THE MANUAL:\n" + facts
        seen = set()
        for h in hits:
            if h["href"] not in seen:
                seen.add(h["href"]); links.append({"title": h["title"], "href": h["href"], "kind": h["kind"]})
        sources = [{"title": h["title"], "href": h["href"]} for h in hits]
    msgs = [{"role": "system", "content": sys_}]
    if isinstance(prev, (list, tuple)) and len(prev) == 2 and all(isinstance(x, str) for x in prev):
        msgs += [{"role": "user", "content": prev[0][:400]}, {"role": "assistant", "content": prev[1][:600]}]
    msgs.append({"role": "user", "content": str(q)[:600]})
    return msgs, sources, links[:3], fixes


def blinki_diag_facts(L):
    """the self-check, the log and some values as plain text for the model (read only); and the fixes it may suggest"""
    lines, fixes = [], []
    try:
        h = health_check(L) or {}
    except Exception:
        h = {}
    for x in (h.get("items") or [])[:30]:
        lv = x.get("level")
        if lv in ("ok", "off"):
            continue
        lines.append("- [%s] %s: %s %s" % (lv, x.get("title", ""), _scrub_text(x.get("text", ""))[:140], x.get("tip", "")[:120]))
        fe = x.get("fehler") or {}
        if fe.get("id"):
            e = fx_entry(fe["id"]) if "fx_entry" in globals() else None
            act = (e or {}).get("aktion") or ""
            fixes.append({"fid": fe["id"], "title": fe.get("title") or x.get("title", ""), "fix": fe.get("fix") or "",
                          "act": act if act and not BLINKI_FIX_DENY.search(act) else "", "help": fe.get("path") or ""})
    if not lines:
        lines.append("- the self-check finds no problem right now")
    oks = [x.get("title", "") for x in (h.get("items") or []) if x.get("level") == "ok"]
    if oks:
        lines.append("- in order: " + ", ".join(oks[:12]))
    st = []
    for k, f in (("fps", "camera pictures per second: %.1f"), ("cpu", "CPU load: %.0f %%"), ("cpu_temp", "CPU temperature: %.0f °C")):
        v = STATE.get(k)
        if isinstance(v, (int, float)):
            st.append(f % v)
    d = STATE.get("disk") or {}
    if d.get("free_mb") is not None:
        st.append("free on the memory card: %d MB" % d["free_mb"])
    sp = STATE.get("supply") or {}
    if sp.get("uv_now") or sp.get("throttled"):
        st.append("power supply: too low voltage / throttled")
    st.append("protection state: %s" % STATE.get("arm_state", ""))
    ev = (STATE.get("events") or [])[:25]                 # the newest first (as in the diagnosis package)
    log = ["%s [%s] %s" % (str(e.get("t", ""))[-8:], e.get("kind", ""), _scrub_text(str(e.get("text", "")))[:110]) for e in ev]
    txt = "SELF-CHECK:\n" + "\n".join(lines) + "\n\nVALUES:\n- " + "\n- ".join(st) + "\n\nLOG (newest first):\n" + "\n".join(log)
    return txt[:5000], fixes[:4]


def blinki_fix(fid, ok, who="web"):
    """run the fix of the error catalogue that Blinki suggested - only with ok=True (the own OK of the user)"""
    if ok is not True:
        return False, "needs your OK"
    e = fx_entry(fid) if "fx_entry" in globals() else None
    act = (e or {}).get("aktion") or ""
    if not act or BLINKI_FIX_DENY.search(act):
        return False, "not allowed"
    if not any(x.get("fehler", {}).get("id") == fid for x in (health_check().get("items") or [])):
        return False, "this problem is not there any more"
    log_event("sys", f"Blinki: suggestion «{act}» confirmed by {who}")
    return fx_run(act, "Blinki / " + who)


# ---- one question: the model when it is there, else the found places of the manual (no model needed) ----------------------------
BLINKI_MODES = ("frag", "fehler")
BLINKI_WAIT_MAX = 4                     # questions waiting at the same time (more: «Blinki is busy»)


def blinki_offline_ok():
    """the model of this device can answer (engine + checked model)"""
    return bool(blinki_engine()) and blinki_model_ok()


def blinki_engine_for(mode):
    """'offline' | 'cloud' | '' (no model: the manual only); 639zzzzk_blinki_cloud adds the cloud"""
    return "offline" if blinki_offline_ok() else ""


def blinki_fallback(mode, L, sources, links, facts=""):
    """the answer without a model: the places of the manual / the self-check, as they are"""
    if mode in BLINKI_EXTRA_MODES:
        return tr("For this Blinki needs the language model on the device (or the cloud). The administrator sets it up here.", L)
    if mode == "fehler":
        bad = [ln[2:] for ln in facts.split("\n") if ln.startswith("- [")][:6]
        return tr("Without the language model Blinki can only show what the self-check finds:", L) + "\n" + (
            "\n".join("• " + x for x in bad) if bad else "• " + tr("the self-check finds no problem right now", L))
    if not sources:
        return tr("I found nothing about this in the manual. Try other words - or open the manual.", L)
    return tr("Blinki cannot answer freely yet (the language model is missing). These places of the manual fit best:", L)


def blinki_ask(mode, q, lang=None, prev=None, who="web", client="", extra=None):
    """a new question -> (job, '') or (None, English reason)"""
    L = norm_lang(lang)
    mode = mode if mode in BLINKI_MODES or mode in BLINKI_EXTRA_MODES else ""
    q = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", str(q or "")).strip()[:600]
    if not mode:
        return None, "unknown action"
    if not q and mode not in BLINKI_NOQ_MODES:
        return None, "the text is empty"
    if mode == "fehler" and not q:
        q = tr("Does my MoveEye have a problem? Please check it.", L)
    with BLINKI["lock"]:
        for j in BLINKI["jobs"].values():                 # a new question of the same page ends its old one
            if client and j.get("client") == client and j["state"] in ("wait", "think", "write"):
                j["stop"] = True
        waiting = sum(1 for j in BLINKI["jobs"].values() if j["state"] in ("wait", "think", "write") and not j["stop"])
    if waiting >= BLINKI_WAIT_MAX:
        return None, "Blinki is busy - try again in a minute"
    msgs, sources, links, fixes = blinki_messages(mode, q, L, prev, extra)
    eng = blinki_engine_for(mode)
    x = {"sources": sources, "links": links, "fixes": fixes, "engine": eng or "manual", "client": client, "who": who}
    x.update({k: v for k, v in (extra or {}).items() if k in ("kid", "place", "speak", "quiz", "image", "max_tokens", "temp")})
    if not eng:
        import queue as _q
        jid = os.urandom(6).hex()
        txt = blinki_fallback(mode, L, sources, links, msgs[0]["content"] if mode == "fehler" else "")
        j = {"id": jid, "t": time.time(), "mode": mode, "q": q, "lang": L, "messages": [], "text": txt, "state": "done", "err": "",
             "stop": False, "t_first": time.time(), "t_end": time.time(), "n_tok": 0}
        j.update(x)
        with BLINKI["lock"]:
            BLINKI["jobs"][jid] = j; BLINKI["order"].append(jid)
            while len(BLINKI["order"]) > 30:
                BLINKI["jobs"].pop(BLINKI["order"].pop(0), None)
        return j, ""
    j = blinki_job_new(mode, q, L, msgs, x)
    log_event("sys", f"Blinki: question ({mode}, {eng}) by {who}")
    return j, ""


BLINKI_EXTRA_MODES = ()                 # 639zzzzk_blinki_mehr: stories, nature guide, quiz
BLINKI_NOQ_MODES = ("fehler",)          # modes that work without a typed text
'''
if BLINKI_WISSEN_PY:
    exec(compile(BLINKI_WISSEN_PY, '<639zzzzk_blinki_wissen>', "exec"), globals())
