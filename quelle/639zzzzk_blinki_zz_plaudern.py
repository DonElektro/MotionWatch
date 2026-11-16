#@ MoveEye – Teil 639zzzzk_blinki_zz_plaudern: «Blinki fragen» – 💬 Plaudern: Blinki beantwortet beliebige Fragen (nicht nur zu MoveEye), getippt oder gesprochen, mit kurzem Verlauf nur im Speicher. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (16.11.2026): eine Art «💬 Plaudern» neben den anderen auf /blinki – fragen, was man will.
#  Vorgabe    eigene Vorgabe (BLINKI_CHAT_RULES): freundlich, kurz (höchstens 8 Sätze), in der Sprache des Benutzers; sagt ehrlich,
#             wenn es unsicher ist; nichts über aktuelle Ereignisse; offline «kein Internet», mit Cloud «kann nicht im Netz suchen»;
#             nie eine Anleitung, Schutz / Alarm / Kamera auszuschalten; keine Arzt-, Rechts- oder Geldberatung über Allgemeines
#             hinaus; familientauglich ab 10 Jahren (Spielecke), Erwachsenen- oder gefährliche Themen höflich ablehnen.
#  Hinweis    offline zeigt jede Antwort eine feste Zeile «kleines Modell, kann sich irren – mit der Cloud besser» (vom Server,
#             nicht vom Modell; wird nicht vorgelesen).
#  Verlauf    die letzten BLINKI_CHAT_TURNS Fragen + Antworten pro Gespräch (Seite: Benutzer + Seiten-Kennung; Gerät: «device»;
#             Fenster: «tk»), NUR im Speicher: nach BLINKI_CHAT_IDLE_S ohne Frage oder mit «Neu» weg (samt den Antworten in
#             BLINKI["jobs"]). Nichts davon geht ins Protokoll oder auf die Karte (nur die Zeile «Blinki: question (plaudern, …)»).
#  Motor      offline das Modell auf dem Gerät, mit dem Cloud-Schalter die Cloud (wie die anderen Arten). Pausen wie bisher
#             (Kern: SIGSTOP bei Alarm / Bewegung / Hitze); mit der Cloud beginnt eine Antwort erst, wenn kein Alarm läuft.
#  Sprechen   🎙 auf dem Handy wie bei «Frag MoveEye»; am Gerät wählt der Administrator, welche Art der Auslöser fragt
#             (blinki_listen_mode: frag | plaudern, ab Werk «plaudern» – Besitzer 16.11.2026).
#  Rechte     wie «Frag MoveEye»: alle angemeldeten Benutzer ausser Kindern.
# ----------------------------------------------------------------------------
# Der Programmtext dieses Teils steht in EINEM Literal (Hauptdatei klein): werkzeuge/bauen.py legt es in die Zusatz-ZIP, beim
# Start läuft es hier an seinem Platz (zd_exec, Teil 639zzzzk_blinki_kern). Ohne ZIP gibt es «Blinki fragen» nicht.
BLINKI_PLAUDERN_PY = r'''BLINKI_CHAT_TURNS = 4                   # question + answer pairs that the model sees again
BLINKI_CHAT_IDLE_S = 15 * 60
BLINKI_CHAT = {"lock": threading.Lock(), "conv": {}, "sweeper": None}
_bk_need = dict(BLINKI_MODE_NEED)                         # «💬 Plaudern» right after «💬 Frag MoveEye»
BLINKI_MODE_NEED.clear()
for _m, _n in _bk_need.items():
    BLINKI_MODE_NEED[_m] = _n
    if _m == "frag":
        BLINKI_MODE_NEED["plaudern"] = ""
BLINKI_MODE_NEED.setdefault("plaudern", "")
BLINKI_MODE_ICON["plaudern"] = ("💬", "Chat freely")
BLINKI_EXTRA_MODES = BLINKI_EXTRA_MODES + ("plaudern",)
BLINKI_USER_POST = BLINKI_USER_POST + ("/api/ki/new",)
CFG.setdefault("blinki_listen_mode", "plaudern"); DEFAULTS.setdefault("blinki_listen_mode", "plaudern")
USER_SETTINGS_DENY.add("blinki_listen_mode"); APPKEY_DENY_KEYS.add("blinki_listen_mode")
BLINKI_SET["blinki_listen_mode"] = lambda v: (True, v) if v in ("frag", "plaudern") else (False, "invalid value")
BLINKI_CHAT_RULES = (
    "You are Blinki, the friendly eye of MoveEye (a small camera guard for camping, house and garden), chatting with the user. "
    "Answer in {lang}; if the user clearly writes in another language, answer in that language. "
    "The user may ask about anything. Be friendly and short: at most 8 sentences, no long lists. "
    "If you are not sure, say so honestly - never invent facts, names, numbers or sources. {engine} "
    "You know nothing about current events: no news, prices, weather, sport results or what happened recently - say so instead of guessing. "
    "Never give instructions to switch off, weaken or get around the protection, the alarm, the siren or the camera of MoveEye or of any other "
    "alarm system. Health, law and money: only general information, never a diagnosis, dosage or personal advice - suggest a doctor, "
    "pharmacist, lawyer or bank. Stay family-friendly: children from 10 may read along. Politely refuse adult, sexual, cruel or hateful "
    "topics and anything dangerous (weapons, drugs, explosives, self-harm, risky experiments) and suggest something else. "
    "If someone seems to be in danger or talks about hurting themselves, answer kindly and tell them to talk to a trusted person now "
    "or to call 143 (Die Dargebotene Hand), 147 for children and young people, or 112 in an emergency. "
    "For questions about using MoveEye, say that the mode «{frag}» answers from the manual. Today is {date}.")
BLINKI_CHAT_ENGINE = {"offline": "You are a small language model running offline on this device without any internet, so you can easily be wrong.",
                      "cloud": "You run on a cloud service, but you cannot browse the web or read the news; your knowledge stops at some date."}
BLINKI_CHAT_NOTE = "Small offline model - it can be wrong. The cloud gives better answers."


def blinki_chat_key(who, client):
    """the conversation: the device and the window have one each, a page one per user + page"""
    client = str(client or "")
    return client if client in ("device", "tk") else "web|%s|%s" % (str(who or "")[:40], client[:40])


def blinki_chat_turns(key):
    """the last turns of a conversation [(question, answer)], [] after the idle time"""
    with BLINKI_CHAT["lock"]:
        c = BLINKI_CHAT["conv"].get(key)
        if c and time.time() - c["t"] > BLINKI_CHAT_IDLE_S:
            BLINKI_CHAT["conv"].pop(key, None); c = None
        return list(c["turns"]) if c else []


def blinki_chat_add(key, q, a):
    a = str(a or "").strip()
    if not key or not a:
        return
    with BLINKI_CHAT["lock"]:
        c = BLINKI_CHAT["conv"].setdefault(key, {"t": 0.0, "turns": []})
        c["turns"] = (c["turns"] + [(str(q or "")[:400], a[:700])])[-BLINKI_CHAT_TURNS:]
        c["t"] = time.time()
        if BLINKI_CHAT["sweeper"] is None or not BLINKI_CHAT["sweeper"].is_alive():
            BLINKI_CHAT["sweeper"] = threading.Thread(target=_blinki_chat_sweep, daemon=True, name="blinki-chat")
            BLINKI_CHAT["sweeper"].start()


def blinki_chat_forget(key=None, idle_only=False):
    """«Neu» (one conversation) or the idle time (all old ones): the turns and their answers in BLINKI["jobs"] are gone"""
    now = time.time()
    with BLINKI_CHAT["lock"]:
        keys = [k for k, c in BLINKI_CHAT["conv"].items() if (k == key if key else True) and (not idle_only or now - c["t"] > BLINKI_CHAT_IDLE_S)]
        for k in keys:
            BLINKI_CHAT["conv"].pop(k, None)
    with BLINKI["lock"]:
        for jid in list(BLINKI["order"]):
            j = BLINKI["jobs"].get(jid)
            if j is None or j.get("mode") != "plaudern" or j["state"] in ("wait", "think", "write"):
                continue
            if (key and j.get("chat") == key) or (not key and now - (j.get("t_end") or j["t"]) > BLINKI_CHAT_IDLE_S):
                BLINKI["jobs"].pop(jid, None); BLINKI["order"].remove(jid)
    return len(keys)


def _blinki_chat_sweep():
    while True:
        time.sleep(30)
        try:
            blinki_chat_forget(None, True)
            with BLINKI_CHAT["lock"]:
                if not BLINKI_CHAT["conv"] and not any(j.get("mode") == "plaudern" for j in BLINKI["jobs"].values()):
                    BLINKI_CHAT["sweeper"] = None
                    return
        except Exception:
            pass


def blinki_chat_messages(q, L, extra):
    """(messages, sources, links, fixes) of «💬 Plaudern»: the own rules, the last turns, the question"""
    eng = blinki_engine_for("plaudern") or "offline"
    sys_ = BLINKI_CHAT_RULES.format(lang=_BLINKI_LANG_NAME.get(L, "English"), engine=BLINKI_CHAT_ENGINE.get(eng, BLINKI_CHAT_ENGINE["offline"]),
                                    frag=tr("Ask MoveEye", L), date=datetime.now().strftime("%Y-%m-%d"))
    msgs = [{"role": "system", "content": sys_}]
    for uq, ua in blinki_chat_turns(extra.get("chat") or ""):
        msgs += [{"role": "user", "content": uq}, {"role": "assistant", "content": ua}]
    msgs.append({"role": "user", "content": str(q)[:600]})
    extra.update(max_tokens=420, temp=0.6)
    return msgs, [], [], []


_blinki_messages_more_chat = blinki_messages_more


# wraps: blinki_messages_more
def blinki_messages_more(mode, q, L, prev, extra):             # + 639zzzzk_blinki_zz_plaudern
    if mode == "plaudern":
        return blinki_chat_messages(q, L, extra)
    return _blinki_messages_more_chat(mode, q, L, prev, extra)


_blinki_ask_chat = blinki_ask


# wraps: blinki_ask
def blinki_ask(mode, q, lang=None, prev=None, who="web", client="", extra=None):   # + 639zzzzk_blinki_zz_plaudern: the conversation
    extra = dict(extra or {})
    extra.pop("chat", None)
    if mode == "plaudern":
        extra["chat"] = blinki_chat_key(who, client)
    return _blinki_ask_chat(mode, q, lang, prev, who, client, extra)


_blinki_answer_chat = blinki_answer


# wraps: blinki_answer
def blinki_answer(j):                                           # + 639zzzzk_blinki_zz_plaudern: the turn into the conversation
    if j.get("mode") != "plaudern":
        return _blinki_answer_chat(j)
    if j.get("engine") == "cloud":                              # the cloud does not compute here - still no answer during an alarm
        while BLINKI["held"] == "alarm" and not j["stop"]:
            j["state"] = "wait"; time.sleep(0.3)
    _blinki_answer_chat(j)
    if j["state"] in ("think", "write") and not j["stop"] and j["text"].strip():
        blinki_chat_add(j.get("chat"), j["q"], j["text"])


_blinki_job_view_chat = blinki_job_view


# wraps: blinki_job_view
def blinki_job_view(j, start=0):                                # + 639zzzzk_blinki_zz_plaudern: the hint of the small model
    v = _blinki_job_view_chat(j, start)
    if j.get("mode") == "plaudern":
        v["note"] = tr(BLINKI_CHAT_NOTE, j.get("lang")) if v["engine"] == "offline" else ""
        v["turns"] = len(blinki_chat_turns(j.get("chat") or ""))
    return v


_blinki_state_chat = blinki_state


# wraps: blinki_state
def blinki_state():                                             # + 639zzzzk_blinki_zz_plaudern
    st = _blinki_state_chat()
    st["chat"] = {"turns": BLINKI_CHAT_TURNS, "idle_min": BLINKI_CHAT_IDLE_S // 60, "listen_mode": CFG.get("blinki_listen_mode") or "plaudern"}
    return st


_smalltv_routes_chat = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                          # + 639zzzzk_blinki_zz_plaudern: POST /api/ki/new («Neu»)
    _smalltv_routes_chat(app, reply, body)
    from flask import g

    @app.route("/api/ki/new", methods=["POST"])
    def blinki_api_new():
        d = body()
        blinki_chat_forget(blinki_chat_key(getattr(g, "user", "") or getattr(g, "role", "admin"), str(d.get("client") or "")[:40]))
        return reply({"ok": True})
'''
zd_exec(BLINKI_PLAUDERN_PY, '639zzzzk_blinki_zz_plaudern.py')
