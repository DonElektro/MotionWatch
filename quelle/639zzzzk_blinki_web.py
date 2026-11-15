#@ MoveEye – Teil 639zzzzk_blinki_web: «Blinki fragen» – Seite /blinki (Chat mit Blinki als Gesicht, Text Stück für Stück, Vorlesen mit Piper), API /api/ki/…, Zeile unter Mehr → Übersicht, Rechte, Pi-Fenster (Mehr → «💬 Blinki fragen»). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Seite     /blinki: oben Blinki (Figur aus Teil 589, MWBlinki.make) + Zustand (offline / pausiert / Modell fehlt), darunter die
#           Arten als Chips (💬 Frag MoveEye, 🔧 Fehlersuche; Stufe 2 mehr), der Verlauf als Sprechblasen und unten das Eingabefeld.
#           Der Text kommt Stück für Stück: die Seite fragt alle 0.4 s /api/ki/job/<id>?from=n (kein Server-Sent-Events nötig, geht
#           durch jeden Tunnel). «Öffnen»-Knöpfe und Quellen kommen vom Server (aus den gefundenen Stellen, nie vom Modell).
#           Ohne Modell: Karte «Blinki einrichten» (Administrator: «Modell laden» mit Fortschritt, «Motor einrichten»); Fragen
#           gehen trotzdem - Blinki zeigt dann die passenden Stellen der Anleitung (blinki_fallback).
# Vorlesen  🔊 pro Antwort: im Browser (Piper-WAV Satz für Satz über /api/ki/voice/<id>.wav) oder am Lautsprecher des Geräts
#           (tts_say; Recht «Gegensprechen»). «Antworten vorlesen» merkt sich der Browser.
# Rechte    ansehen + 💬 Frag MoveEye: jeder angemeldete Benutzer ausser Kindern; 🔧 Fehlersuche, Vorschläge ausführen, Modell,
#           Motor und Einstellungen: nur der Administrator (nie mit App-Schlüssel, nicht im Bedienermodus).
# ----------------------------------------------------------------------------
# Der Programmtext dieses Teils steht in EINEM Literal (Besitzer / Koordinator 15.11.2026: Hauptdatei klein): werkzeuge/bauen.py
# legt es in die Zusatz-ZIP, beim Start läuft es hier an seinem Platz (zd_exec, Teil 639zzzzk_blinki_kern). Ohne ZIP gibt es
# «Blinki fragen» nicht - es gehört nicht zu Start, Schutz oder Alarm. Die ZIP ist über ZD_SHA256 (Teil 012) mit signiert.
BLINKI_WEB_PY = r'''VIEW_GET_PAGES.add("/blinki")
VIEW_GET = VIEW_GET + ("/api/ki/state", "/api/ki/job/", "/api/ki/voice/")
APPKEY_DENY_PATHS.update({"/api/ki/set", "/api/ki/model", "/api/ki/fix"})
LOCK_DENY_PATHS.update({"/api/ki/set", "/api/ki/model", "/api/ki/fix"})
BLINKI_MODE_NEED = {"frag": "", "fehler": "admin"}       # mode -> right ('' = every user, «admin» = only the administrator)
BLINKI_KID_MODES = set()                                 # 639zzzzk_blinki_mehr: children may only listen to stories
BLINKI_USER_POST = ("/api/ki/ask", "/api/ki/stop", "/api/ki/say", "/api/ki/stt")
BLINKI_SET = {"blinki_speak": "bool", "blinki_threads": (1, 4)}     # what /api/ki/set may change (more in the later stages)
BLINKI_MODE_ICON = {"frag": ("💬", "Ask MoveEye"), "fehler": ("🔧", "Troubleshooting")}
BLINKI["voices"] = deque(maxlen=60)                      # the read-aloud pieces of Blinki (only these are served)


def blinki_mode_ok(mode, role="admin", perms=None):
    if role == "admin":
        return mode in BLINKI_MODE_NEED
    P = set(perms) if perms is not None else set(ROLE_PERMS.get(ROLE_OLD.get(role, role), ()))
    need = BLINKI_MODE_NEED.get(mode)
    if need is None or need == "admin":
        return False
    if role == "kid":
        return mode in BLINKI_KID_MODES
    return not need or need in P


_role_allows_blinki = role_allows


# wraps: role_allows
def role_allows(role, path, method, d, perms=None):           # + 639zzzzk_blinki_web: who may ask Blinki what
    if method not in ("GET", "HEAD") and path in BLINKI_USER_POST and role != "admin":
        d = d if isinstance(d, dict) else {}
        P = set(perms) if perms is not None else set(ROLE_PERMS.get(ROLE_OLD.get(role, role), ()))
        if path in ("/api/ki/ask", "/api/ki/stt"):
            return blinki_mode_ok(str(d.get("mode") or "frag"), role, perms)
        if path == "/api/ki/say" and d.get("where") == "pi":
            return "talk" in P
        return role != "kid" or bool(BLINKI_KID_MODES)
    return _role_allows_blinki(role, path, method, d, perms)


def blinki_modes(role="admin", perms=None, lang=None):
    L = norm_lang(lang)
    return [{"m": m, "icon": BLINKI_MODE_ICON[m][0], "label": tr(BLINKI_MODE_ICON[m][1], L)} for m in BLINKI_MODE_NEED
            if m in BLINKI_MODE_ICON and blinki_mode_ok(m, role, perms)]


def blinki_page_state(lang=None, role="admin", perms=None):
    L = norm_lang(lang)
    st = blinki_state()
    st.update(admin=role == "admin", kid_only=role == "kid", modes=blinki_modes(role, perms, L), offline_ok=blinki_offline_ok(),
              talk=role == "admin" or "talk" in (set(perms) if perms is not None else set(ROLE_PERMS.get(ROLE_OLD.get(role, role), ()))),
              held_t=tr(BLINKI_HELD_TXT.get(st["held"], ""), L) if st["held"] else "",
              err_t=tr_err(st["err"], L) if st["err"] else "", dl_t=tr_err(st["dl"]["msg"], L) if st["dl"]["msg"] else "",
              install_t=tr_err(st["engine"]["install"][8:], L) if st["engine"]["install"].startswith("failed: ") else "")
    return st


BLINKI_HELD_TXT = {"alarm": "Blinki waits: alarm - the protection goes first", "motion": "Blinki waits: MoveEye follows a movement",
                   "heat": "Blinki waits: the processor is too hot (over 80 °C)"}


def blinki_set(key, value):
    """one setting of Blinki (only the administrator) -> (ok, English reason)"""
    kind = BLINKI_SET.get(key)
    if kind is None:
        return False, "unknown setting"
    if kind == "bool":
        v = bool(value) if isinstance(value, bool) else str(value).lower() in ("1", "true", "on")
    elif isinstance(kind, tuple):
        try:
            v = max(kind[0], min(kind[1], int(value)))
        except (TypeError, ValueError):
            return False, "invalid value"
    elif callable(kind):
        ok, v = kind(value)
        if not ok:
            return False, v
    else:
        return False, "unknown setting"
    CFG[key] = v
    save_settings()
    log_event("sys", f"Blinki: setting {key} changed")
    if key == "blinki_threads" and BLINKI["proc"] is not None:
        blinki_stop("new number of cores")
    return True, ""


def blinki_plain_text(t):
    """the answer without the marks of the model (for the voice)"""
    t = re.sub(r"\*\*|__|`|#+ ", "", str(t or ""))
    return re.sub(r"\s+", " ", t).strip()


def blinki_pieces(t, n=180):
    """sentences of at most n characters (tts_say takes 200)"""
    out, cur = [], ""
    for s in re.split(r"(?<=[.!?:;])\s+", blinki_plain_text(t)):
        while len(s) > n:
            k = s.rfind(" ", 0, n)
            k = k if k > 40 else n
            if cur:
                out.append(cur); cur = ""
            out.append(s[:k]); s = s[k:].strip()
        if cur and len(cur) + len(s) + 1 > n:
            out.append(cur); cur = ""
        cur = (cur + " " + s).strip()
    if cur:
        out.append(cur)
    return [x for x in out if x][:12]


def blinki_say(jid, where="browser", n=0, lang=None):
    """read an answer aloud: «pi» = the loudspeaker of the device (all pieces, in the background); «browser» = piece n as a WAV
    of Piper (/api/ki/voice/<id>.wav) -> (ok, reason, {sid, more})"""
    j = BLINKI["jobs"].get(str(jid or ""))
    if j is None or not j["text"]:
        return False, "unknown action", {}
    L = norm_lang(lang or j.get("lang"))
    parts = blinki_pieces(j["text"])
    if where == "pi":
        if not parts:
            return False, "the text is empty", {}

        def run():
            for p in parts:
                ok, _e = tts_say(p, L)
                if not ok:
                    break
                t0 = time.time()
                while SOUND.get("playing") and time.time() - t0 < 30:
                    time.sleep(0.2)
        threading.Thread(target=run, daemon=True, name="blinki-say").start()
        return True, "", {"n": len(parts)}
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 0
    if not 0 <= n < len(parts):
        return False, "the text is empty", {}
    tmp = os.path.join(blinki_dir(), "say.wav")
    os.makedirs(blinki_dir(), exist_ok=True)
    ok, err = tts_make(parts[n], L, tmp)
    sid = str(TTS.get("id") or "")
    if not ok or not re.fullmatch(r"[0-9a-f]{20}", sid) or not os.path.isfile(piper_cache_path(sid)):
        return False, err or "speech failed", {}
    BLINKI["voices"].append(sid)
    return True, "", {"sid": sid, "more": n + 1 < len(parts), "n": len(parts)}


_smalltv_routes_blinki = smalltv_routes


def smalltv_routes(app, reply, body):                        # + 639zzzzk_blinki_web: the page /blinki and /api/ki/…
    _smalltv_routes_blinki(app, reply, body)
    from flask import Response, request, g, send_file

    def who_():
        role = getattr(g, "role", "admin")
        return role, (None if role == "admin" else user_req_perms(g))

    def lang_(d=None):
        return norm_lang((d or {}).get("lang") or request.args.get("lang"))

    def answer(ok, err, L, extra=None, code=None):
        out = {"ok": ok, "error": None if ok else tr_err(err, L)}
        out.update(extra or {})
        return reply(out, code or (200 if ok else 400))

    @app.route("/blinki")
    def blinki_page():
        return Response(render_page(BLINKI_PAGE, "more"), mimetype="text/html", headers={"Cache-Control": "no-store"})

    @app.route("/api/ki/state")
    def blinki_api_state():
        role, perms = who_()
        return reply({"ok": True, "state": blinki_page_state(lang_(), role, perms)})

    @app.route("/api/ki/job/<jid>")
    def blinki_api_job(jid):
        j = BLINKI["jobs"].get(jid) if _BLINKI_ID.match(jid or "") else None
        if j is None:
            return reply({"ok": False, "error": "unknown"}, 404)
        try:
            start = max(0, int(request.args.get("from") or 0))
        except ValueError:
            start = 0
        v = blinki_job_view(j, start)
        L = norm_lang(j.get("lang"))
        if v["err"]:
            v["err"] = tr_err(v["err"], L)
        if v["held"]:
            v["held"] = tr(BLINKI_HELD_TXT.get(v["held"], ""), L)
        return reply({"ok": True, "job": v})

    @app.route("/api/ki/voice/<name>")
    def blinki_api_voice(name):
        m = re.fullmatch(r"([0-9a-f]{20})\.wav", name or "")
        if not m or m.group(1) not in BLINKI["voices"] or not os.path.isfile(piper_cache_path(m.group(1))):
            return Response("not found", 404)
        return send_file(piper_cache_path(m.group(1)), mimetype="audio/wav", max_age=600)

    @app.route("/api/ki/ask", methods=["POST"])
    def blinki_api_ask():
        d = body(); L = lang_(d)
        role, perms = who_()
        prev = d.get("prev") if isinstance(d.get("prev"), list) else None
        extra = {k: d.get(k) for k in ("kid", "place", "image_ok") if k in d}
        if role == "kid":
            extra["kid"] = True                                 # children: always the children's version
        j, err = blinki_ask(str(d.get("mode") or "frag"), d.get("q"), L, prev, getattr(g, "user", "") or role, str(d.get("client") or "")[:40], extra)
        if j is None:
            return answer(False, err, L)
        return answer(True, "", L, {"id": j["id"], "job": blinki_job_view(j)})

    @app.route("/api/ki/stop", methods=["POST"])
    def blinki_api_stop():
        d = body()
        j = BLINKI["jobs"].get(str(d.get("id") or ""))
        if j is not None:
            j["stop"] = True
        return reply({"ok": True})

    @app.route("/api/ki/say", methods=["POST"])
    def blinki_api_say():
        d = body(); L = lang_(d)
        ok, err, x = blinki_say(d.get("id"), "pi" if d.get("where") == "pi" else "browser", d.get("n") or 0, L)
        return answer(ok, err, L, x)

    @app.route("/api/ki/fix", methods=["POST"])
    def blinki_api_fix():
        d = body(); L = lang_(d)
        ok, msg = blinki_fix(str(d.get("fid") or ""), d.get("ok"), getattr(g, "user", "") or "admin")
        return answer(ok, msg, L, {"msg": tr_err(msg, L) if ok and msg else ""})

    @app.route("/api/ki/model", methods=["POST"])
    def blinki_api_model():
        d = body(); L = lang_(d); a = str(d.get("action") or "")
        if a == "load":
            ok, err = blinki_download()
        elif a == "cancel":
            BLINKI_DL["stop"] = True; ok, err = True, ""
        elif a == "delete":
            ok, err = blinki_delete()
        elif a == "engine":
            ok, err = blinki_install()
        elif a == "stop":
            blinki_stop("button"); ok, err = True, ""
        else:
            ok, err = False, "unknown action"
        return answer(ok, err, L, {"state": blinki_page_state(L)})

    @app.route("/api/ki/set", methods=["POST"])
    def blinki_api_set():
        d = body(); L = lang_(d)
        ok, err = blinki_set(str(d.get("key") or ""), d.get("value"))
        return answer(ok, err, L, {"state": blinki_page_state(L)})


# ---- Mehr → Übersicht: one row; the German texts of the page --------------------------------------------------------------------
BLINKI_MORE_ROW = ('  <a class="mi" href="/blinki" id="m-blinki"><i>💬</i><span><b data-i18n="Ask Blinki">Ask Blinki</b><small data-i18n="Questions about MoveEye, troubleshooting">'
                   'Questions about MoveEye, troubleshooting</small></span><span class="ar">›</span></a>\n')
_bk_anchor = '  <a class="mi" href="/help">'
if 'href="/blinki"' not in MORE_PAGE and MORE_PAGE.count(_bk_anchor) == 1:
    MORE_PAGE = MORE_PAGE.replace(_bk_anchor, BLINKI_MORE_ROW + _bk_anchor, 1)

_render_page_blinki = render_page


# wraps: render_page
def render_page(page, active):                               # + 639zzzzk_blinki_web: German texts and the figure of the page /blinki
    out = _render_page_blinki(page, active)
    if "/*BLINKIDE*/" in out:
        out = out.replace("/*BLINKIDE*/", "Object.assign(I18N.de, " + json.dumps(_BKFRAG_DE, ensure_ascii=False).replace("</", "<\\/") + ");\n"
                          + blinki_js("de"), 1)
    return out


# ---- the window (Tk): Mehr -> «💬 Blinki fragen» -----------------------------------------------------------------------------------
if GUI_OK:
    def _blinki_tk_win(self):
        w = getattr(self, "_blinki_top", None)
        if w is not None and w.winfo_exists():
            w.lift(); return
        w = self._blinki_top = tk.Toplevel(self.root); w.title("MoveEye – " + tr("Ask Blinki")); w.configure(bg=C["bg"]); w.geometry("520x560")
        top = tk.Frame(w, bg=C["bg"]); top.pack(fill="x", padx=12, pady=(10, 4))
        try:
            blinki_tk_label(top, 56, "point", C["bg"]).pack(side="left", padx=(0, 10))
        except Exception:
            pass
        st = tk.Label(top, text="", bg=C["bg"], fg=C["mut"], font=("DejaVu Sans", 9), wraplength=400, justify="left", anchor="w")
        tk.Label(top, text=tr("Ask Blinki"), bg=C["bg"], fg=C["txt"], font=("DejaVu Sans", 13, "bold"), anchor="w").pack(fill="x")
        st.pack(fill="x")
        mode = tk.StringVar(value="frag")
        mf = tk.Frame(w, bg=C["bg"]); mf.pack(fill="x", padx=12)
        for m in BLINKI_MODE_NEED:
            if m in BLINKI_MODE_ICON:
                tk.Radiobutton(mf, text=BLINKI_MODE_ICON[m][0] + " " + tr(BLINKI_MODE_ICON[m][1]), variable=mode, value=m, bg=C["bg"], fg=C["txt"],
                               selectcolor=C["panel"], activebackground=C["bg"], font=("DejaVu Sans", 10), anchor="w").pack(side="left", padx=(0, 8))
        out = tk.Text(w, bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 11), wrap="word", height=14, bd=0, padx=8, pady=6)
        out.pack(fill="both", expand=True, padx=12, pady=8)
        ef = tk.Frame(w, bg=C["bg"]); ef.pack(fill="x", padx=12)
        ent = tk.Entry(ef, bg=C["field"], fg=C["txt"], insertbackground=C["txt"], font=("DejaVu Sans", 11))
        ent.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=4)
        cur = {"id": "", "n": 0}

        def ask(_e=None):
            q = ent.get().strip()
            if not q and mode.get() not in BLINKI_NOQ_MODES:
                return
            j, err = blinki_ask(mode.get(), q, CFG.get("lang"), None, "window", "tk")
            if j is None:
                st.config(text="⚠ " + tr_err(err)); return
            ent.delete(0, "end")
            out.insert("end", ("\n" if out.index("end-1c") != "1.0" else "") + "🙂 " + (q or j["q"]) + "\n👁 ")
            cur.update(id=j["id"], n=0)
            tick()
        ent.bind("<Return>", ask)
        self._fbtn(ef, "➤ " + tr("Ask"), ask, primary=True).pack(side="left")
        bf = tk.Frame(w, bg=C["bg"]); bf.pack(fill="x", padx=12, pady=6)
        self._fbtn(bf, "⏹ " + tr("Stop"), lambda: BLINKI["jobs"].get(cur["id"], {}).update(stop=True)).pack(side="left", padx=(0, 6))
        self._fbtn(bf, "🔊 " + tr("Read aloud"), lambda: blinki_say(cur["id"], "pi")).pack(side="left", padx=(0, 6))
        self._fbtn(bf, "🌐 " + tr("Open in the browser"), lambda: self._open_page("/blinki")).pack(side="left")
        self._fbtn(w, tr("Close"), w.destroy, primary=True).pack(side="bottom", anchor="e", padx=12, pady=(0, 10))

        def tick():
            try:
                if not w.winfo_exists():
                    return
                s = blinki_state()
                st.config(text=(tr(BLINKI_HELD_TXT.get(s["held"], "")) if s["held"] else
                                (tr("offline on this device") + " · " + s["model"]["name"]) if blinki_offline_ok() else
                                tr("The language model is missing - set it up in the browser (Mehr → Blinki fragen).")))
                j = BLINKI["jobs"].get(cur["id"])
                if j is not None:
                    new = j["text"][cur["n"]:]
                    if new:
                        out.insert("end", new); out.see("end"); cur["n"] += len(new)
                    if j["state"] in ("done", "error", "stopped"):
                        links = [x.get("title", "") for x in (j.get("links") or [])]
                        out.insert("end", ("\n⚠ " + tr_err(j["err"]) if j["err"] else "") + ("\n📖 " + " · ".join(links) if links else "") + "\n")
                        cur["id"] = ""
                w.after(400 if cur["id"] else 2000, tick)
            except Exception:
                pass
        tick()

    App._blinki_win = _blinki_tk_win
    _blinki_tk_more_base = App._tk_more_bar

    def _blinki_tk_more_bar(self, parent):
        f = _blinki_tk_more_base(self, parent)
        row = max([int(x.grid_info().get("row", 0)) for x in f.grid_slaves()] + [-1]) + 1
        self._fbtn(f, "💬 " + tr("Ask Blinki"), self._blinki_win).grid(row=row, column=0, sticky="ew", padx=(0, 6), pady=(0, 6))
        return f

    # wraps: App._tk_more_bar (572, after 639zzzzd «Radio»)
    App._tk_more_bar = _blinki_tk_more_bar
'''
zd_exec(BLINKI_WEB_PY, '639zzzzk_blinki_web.py')
