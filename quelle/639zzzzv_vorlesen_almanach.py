#@ MoveEye – Teil 639zzzzv_vorlesen_almanach: 🔊 im Überlebens-Almanach liest mit der Piper-Stimme («meine KI-Stimme») wie das Vorlesen im Digitalen Rucksack – derselbe Spieler, Laden-Anzeige, Stopp, Sprache der Seite; ohne Piper oder bei einem Fehler die Browser-Stimme mit kurzem Hinweis. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Idee #31 (Besitzer, freigegeben 28.11.2026): «Der 🔊-Knopf im Almanach liest heute mit der Browser-Stimme – umstellen auf meine
# KI-Stimme, genau wie das Vorlesen im Rucksack.»
#  Wiederverwendet (keine Doppelung): Sätze vl_saetze / vl_sentence, Stimme vl_synth (Teil 639zzzzv, hier mit old=False: nur Piper,
#            nie die alte Stimme - die Browser-Stimme ist der Rückfall), der Spieler des Browsers window.mwReadP (VL_PLAYER_JS:
#            Laden, Pause bei Alarm, Radio-Ausschluss, Sperrbildschirm) mit der Option {url} statt einer Rucksack-Datei, Piper-
#            Schlüssel piper_key / piper_voice_for / piper_ready / piper_warm (639zzb), Aussehen der Leiste wie .vl-dock.
#  Adressen  /almanach/vorlesen?i=<Artikel>&lang=<Sprache der Seite> -> {ok, ch, n, piper, hint, tx} (das «Buch» eines Artikels: Titel +
#            Absätze, Listenpunkte je ein Absatz), ohne i nur die Texte · /almanach/vorlesen/ton?i&s&lang -> WAV eines Satzes (503 +
#            fallback, wenn Piper fehlt oder nicht antwortet). Wie der ganze Almanach ohne Anmeldung offen (Gäste im WLAN): nur feste
#            Texte des Almanachs, kein freier Text; Ton unter DATA_DIR/piper/almanach (höchstens ALM_VL_N Dateien / ALM_VL_MB).
#  Rückfall  keine Piper-Stimme der Sprache, Laufzeit fehlt, Fehler oder keine Verbindung: Browser-Stimme (wie bisher, de-CH) ab dem
#            Satz, der gerade dran war, und ein Hinweis unten (#x-tip). Schalter «Stimme» (MW_VOICE, 639q) gilt weiter für beide.
# Test: werkzeuge/almanach_vorlesen_test.py (Adressen, Gäste, Rückfall ohne Piper, Browser 390 px: Knopf holt den Ton von Piper,
# Leiste mit Laden / Stopp, ohne Piper Browser-Stimme mit Hinweis).
# ----------------------------------------------------------------------------
ALM_VL = {"books": {}, "lock": threading.Lock(), "q": deque(), "run": False}
ALM_VL_N, ALM_VL_MB = 1500, 120
ALM_VL_LANG = "de"                                         # the almanac is written in German (630: «nur auf Deutsch»)


def alm_vl_arts():
    return [(a[0], a[1]) for c in ALMANAC for a in c[3]]


def alm_vl_book(i):
    """the «book» of article i for the player of the backpack: {title, lang, ch: [{t, p: [[sentence]]}], n} (same shape as vl_book)"""
    arts = alm_vl_arts()
    if not 0 <= int(i) < len(arts):
        raise LookupError("unknown article")
    t, x = arts[int(i)]
    with ALM_VL["lock"]:
        b = ALM_VL["books"].get(t)
        if b is not None:
            return b
    ps = [vl_saetze(t)]
    for blk in str(x).split("\n\n"):
        ls = blk.split("\n")
        if all(l_.startswith("- ") for l_ in ls):
            ps += [vl_saetze(l_[2:]) for l_ in ls]
        else:
            ps.append(vl_saetze(" ".join(ls)))
    ps = [p for p in ps if p]
    b = {"title": t, "lang": ALM_VL_LANG, "ch": [{"t": t, "p": ps}], "n": [sum(len(p) for p in ps)]}
    with ALM_VL["lock"]:
        if len(ALM_VL["books"]) > 400:
            ALM_VL["books"].clear()
        ALM_VL["books"][t] = b
    return b


def alm_vl_ready(lang):
    return VL["synth"] is not None or piper_ready(lang)


def alm_vl_dir():
    return os.path.join(piper_dir(), "almanach")


def alm_vl_trim(d):
    try:
        fs = sorted((e.stat().st_mtime, e.stat().st_size, e.path) for e in os.scandir(d) if e.name.endswith(".wav"))
    except OSError:
        return
    tot = sum(x[1] for x in fs)
    while fs and (len(fs) > ALM_VL_N or tot > ALM_VL_MB * 1024 * 1024):
        _t, sz, p_ = fs.pop(0)
        try:
            os.remove(p_); tot -= sz
        except OSError:
            pass


def alm_vl_ton(i, s, lang):
    """(path of the WAV of sentence s of article i, error) - only Piper, computed once"""
    b = alm_vl_book(i)
    text, _end = vl_sentence(b, 0, int(s)) if 0 <= int(s) < b["n"][0] else ("", True)
    if not text:
        return "", "unknown sentence"
    if not alm_vl_ready(lang):
        return "", "no voice"
    d = alm_vl_dir()
    p_ = os.path.join(d, piper_key("alm", piper_voice_for(lang) if VL["synth"] is None else "test", 1.0, lang + "|" + text) + ".wav")
    if os.path.isfile(p_) and os.path.getsize(p_) > 100:
        return p_, ""
    tmp = p_ + f".{threading.get_ident()}.tmp.wav"
    try:
        os.makedirs(d, exist_ok=True)
        ok, err = vl_synth(re.sub(r"[\x00-\x1f]", " ", text), lang, 1.0, tmp, old=False)
        if not ok or not os.path.isfile(tmp) or os.path.getsize(tmp) <= 100:
            return "", err or "no voice"
        os.replace(tmp, p_)
    except OSError as e:
        return "", str(e)[:120]
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    alm_vl_trim(d)
    return p_, ""


def alm_vl_ahead(i, s, lang, n=2):
    """the next sentences in the background (one worker, a short queue)"""
    b = alm_vl_book(i)
    with ALM_VL["lock"]:
        for k in range(1, n + 1):
            if s + k < b["n"][0] and (i, s + k, lang) not in ALM_VL["q"]:
                ALM_VL["q"].append((i, s + k, lang))
        while len(ALM_VL["q"]) > 6:
            ALM_VL["q"].popleft()
        if ALM_VL["run"] or not ALM_VL["q"]:
            return
        ALM_VL["run"] = True

    def work():
        try:
            while True:
                with ALM_VL["lock"]:
                    if not ALM_VL["q"]:
                        return
                    job = ALM_VL["q"].popleft()
                try:
                    alm_vl_ton(*job)
                except Exception:
                    pass
        finally:
            ALM_VL["run"] = False
    threading.Thread(target=work, daemon=True, name="alm-vl-ahead").start()


_ALM_VL_TX = ("Read aloud", "Pause", "Stop", "loading …", "My AI voice", "Browser voice", "No AI voice loaded - the browser voice reads.",
              "The AI voice does not answer - the browser voice reads on.")


def alm_vl_info(i, lang, ui):
    d = {"ok": True, "tx": {k: tr(k, ui) for k in _ALM_VL_TX}}
    if i is None:
        return d
    b = alm_vl_book(i)
    ready = alm_vl_ready(lang)
    if ready:
        piper_warm(lang)
    d.update(i=int(i), title=b["title"], lang=lang, ch=b["ch"], n=b["n"], piper=ready,
             hint="" if ready else tr("No AI voice loaded - the browser voice reads.", ui))
    return d


_smalltv_routes_almvl = smalltv_routes


# wraps: smalltv_routes
def smalltv_routes(app, reply, body):                        # + 639zzzzv_vorlesen_almanach: /almanach/vorlesen, /almanach/vorlesen/ton
    _smalltv_routes_almvl(app, reply, body)
    from flask import request, send_file

    def args():
        a = request.args
        return norm_lang(a.get("lang") or ALM_VL_LANG), norm_lang(CFG.get("lang"))

    @app.route("/almanach/vorlesen")
    def alm_vl_route():
        L, ui = args()
        try:
            i = request.args.get("i")
            r = reply(alm_vl_info(None if i in (None, "") else int(i), L, ui))
        except (TypeError, ValueError, LookupError):
            return reply({"ok": False, "error": tr("invalid value", ui)}, 400)
        r.headers["Cache-Control"] = "no-store"
        return r

    @app.route("/almanach/vorlesen/ton")
    def alm_vl_ton_route():
        L, ui = args()
        try:
            i, s = int(request.args.get("i") or 0), int(request.args.get("s") or 0)
            p_, err = alm_vl_ton(i, s, L)
        except (TypeError, ValueError, LookupError):
            return reply({"ok": False, "error": tr("invalid value", ui)}, 400)
        if not p_:
            return reply({"ok": False, "fallback": True, "error": tr("The AI voice does not answer - the browser voice reads on.", ui)}, 503)
        try:
            alm_vl_ahead(i, s, L)
        except Exception:
            pass
        r = send_file(p_, mimetype="audio/wav", conditional=True, max_age=0)
        r.headers["Cache-Control"] = "private, max-age=3600"
        r.headers["X-Content-Type-Options"] = "nosniff"
        r.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        return r


# ---- the page: the player of the backpack + a bar like .vl-dock (round ▶ / ⏸, ⏹ Stopp, loading, the voice) --------------------------
ALM_VL_JS = r"""<style>
#alm-rd{position:fixed;left:0;right:0;bottom:0;z-index:8;background:var(--panel);border-top:1px solid var(--line);padding:8px 16px;padding-bottom:max(10px,env(safe-area-inset-bottom));font-family:system-ui,sans-serif}
#alm-rd[hidden]{display:none}body.rd-on main{padding-bottom:110px}body.rd-on #x-tip{bottom:calc(96px + env(safe-area-inset-bottom,0px))}
.rd-ctl{display:flex;align-items:center;gap:12px;max-width:720px;margin:0 auto}
.rd-go{width:56px;height:56px;min-width:56px;border-radius:50%;font-size:24px;background:var(--acc);color:#fff;border:0;padding:0}
.rd-tx{flex:1;min-width:0;line-height:1.3}.rd-tx b{display:block;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.rd-tx small{display:block;color:var(--mut);font-size:12.5px}
.rd-x{min-width:54px;min-height:48px;padding:2px 6px;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1.05;font-size:19px}.rd-x small{font-size:10px;color:var(--mut);margin-top:2px}
.rd-sp{display:inline-block;width:11px;height:11px;border:2px solid var(--line);border-top-color:var(--acc);border-radius:50%;animation:rd-sp .9s linear infinite;vertical-align:-1px;margin-right:6px}
@keyframes rd-sp{to{transform:rotate(360deg)}}@media(prefers-reduced-motion:reduce){.rd-sp{animation:none}}
@media print{#alm-rd{display:none!important}}
</style>
<div id="alm-rd" hidden><div class="rd-ctl"><button type="button" class="rd-go" id="rd-go">⏸</button><div class="rd-tx"><b id="rd-ti"></b><small id="rd-st"></small></div>
<button type="button" class="rd-x" id="rd-x">⏹<small id="rd-xl"></small></button></div></div>
<script>
/*VLPLAYER*/
(function () {
  const P = window.mwReadP; if (!P) return;
  const $ = id => document.getElementById(id), LG = document.documentElement.lang || "de";
  let TX = {}, mode = "", cur = -1, gen = 0, pending = false, heard = false, bT = 0;    // mode: "" | "piper" | "browser"
  const T = k => TX[k] || ({"Read aloud": "Vorlesen", "Pause": "Pause", "Stop": "Stopp", "loading …": "lädt …", "My AI voice": "Meine KI-Stimme", "Browser voice": "Browser-Stimme"})[k] || k;
  const BK = {};
  const info = i => fetch("/almanach/vorlesen?i=" + i + "&lang=" + LG, {cache: "no-store"}).then(r => r.json()).then(j => { if (j && j.ok) { BK[i] = j; if (j.tx) TX = j.tx; } return j; }).catch(() => null);
  fetch("/almanach/vorlesen?lang=" + LG).then(r => r.json()).then(j => { if (j && j.tx) { TX = j.tx; P.tx = {"Read aloud": T("Read aloud")}; paint(); } }).catch(() => {});
  function tip(t) { const x = $("x-tip"); if (!x || !t) return; x.textContent = t; x.hidden = false; clearTimeout(tip.t); tip.t = setTimeout(() => { x.hidden = true; }, 5000); }
  function rest(J, s) { const o = []; let k = 0; for (const p of J.ch[0].p) for (const x of p) { if (k++ >= s) o.push(x); } return o.join(" "); }
  function fallback(i, why, s) {                           // the browser voice from sentence s on
    gen++; mode = ""; pending = false; if (P.S.on) P.stop();
    const J = BK[i]; mode = window.almBrowser && almBrowser(i, J && s ? rest(J, s) : "") ? "browser" : ""; cur = mode ? i : -1; bT = Date.now();
    tip(why); paint();
  }
  window.almStop = function () { gen++; pending = false; const m0 = mode; mode = ""; cur = -1;
    if (m0 === "piper" && P.S.on) P.stop(); if (m0 === "browser" && window.speechSynthesis) speechSynthesis.cancel(); paint(); };
  window.almRead = async function (i) {
    if (mode && cur === i) { almStop(); return; }          // a second tap on 🔊 stops (as before)
    almStop();
    const g = gen; cur = i; mode = "piper"; heard = false;
    let J = BK[i];
    if (!J) { pending = true; paint(); J = await info(i); pending = false; if (g !== gen) return; }
    if (!J || !J.ok) { fallback(i, T("The AI voice does not answer - the browser voice reads on."), 0); return; }
    if (!J.piper) { fallback(i, J.hint || T("No AI voice loaded - the browser voice reads."), 0); return; }
    P.speed(1); P.play("alm" + i, 0, 0, J, {url: (c, s) => "/almanach/vorlesen/ton?i=" + i + "&s=" + s + "&lang=" + LG,
      nopoll: !(typeof PLUS !== "undefined" && PLUS.heim)});              // alarm = pause only for a known device (a guest may not ask /api/vorlesen)
    paint();
  };
  function settle() {                                      // the player stopped: at the end, by Stopp, or with an error
    if (mode !== "piper" || P.S.on || pending) return;
    if (P.S.st === "error") { fallback(cur, T("The AI voice does not answer - the browser voice reads on."), P.S.s); return; }
    mode = ""; cur = -1; paint();
  }
  function paint() {
    const S = P.S, d = $("alm-rd");
    if (mode === "piper" && !S.on && !pending) { setTimeout(settle, 0); }
    d.hidden = !mode; document.body.classList.toggle("rd-on", !!mode); $("b-read").classList.toggle("on", !!mode);
    $("b-read").title = mode ? T("Stop") : T("Read aloud"); $("rd-xl").textContent = T("Stop");
    if (!mode) return;
    if (S.st === "playing") heard = true;
    const a = all[cur]; $("rd-ti").textContent = "🔊 " + (a ? a.t : "");
    const st = $("rd-st"), go = $("rd-go"); st.textContent = "";
    let paused = false;
    if (mode === "piper") {
      paused = !!(S.paused || S.hold);
      if (pending || (S.st === "loading" && !heard)) { const sp = document.createElement("span"); sp.className = "rd-sp"; st.append(sp, T("loading …")); }
      else st.textContent = (paused ? "⏸ " + (S.hold || T("Pause")) : "🗣 " + T("My AI voice")) + " · " + (S.s + 1) + " / " + ((S.n && S.n[0]) || 1);
    } else { paused = !!(window.speechSynthesis && speechSynthesis.paused); st.textContent = (paused ? "⏸ " : "🗣 ") + T("Browser voice"); }
    go.textContent = paused ? "▶" : "⏸"; go.title = paused ? T("Read aloud") : T("Pause");
  }
  P.cb = paint;
  $("rd-go").onclick = () => {
    if (mode === "piper") { if (P.S.paused) P.resume(); else P.pause(); }
    else if (mode === "browser" && window.speechSynthesis) { if (speechSynthesis.paused) speechSynthesis.resume(); else speechSynthesis.pause(); paint(); }
  };
  $("rd-x").onclick = () => almStop();
  setInterval(() => { if (mode === "browser" && Date.now() - bT > 1500 && window.speechSynthesis && !speechSynthesis.speaking && !speechSynthesis.paused) { mode = ""; cur = -1; paint(); } }, 600);
  const sh = window.show;                                  // the article on the screen: its sentences ready before the tap (iPhone: sound only in the tap)
  if (typeof sh === "function") window.show = function (i) { const r = sh.apply(this, arguments); if (!BK[i]) info(i); return r; };
  setTimeout(() => { try { const i = window.cur ?? tipIdx(); if (!BK[i]) info(i); } catch (e) {} }, 300);
})();
</script>"""

ALM_PAGE = ALM_PAGE.replace("</body>", ALM_VL_JS.replace("/*VLPLAYER*/", VL_PLAYER_JS, 1) + "</body>", 1)

# ---- texts (English key: Deutsch, Français, Italiano, Rumantsch) -----------------------------------------------------------------------
_HX_ALMVL = {
    "My AI voice": ("Meine KI-Stimme", "Ma voix IA", "La mia voce IA", "Mia vusch IA"),
    "Browser voice": ("Browser-Stimme", "Voix du navigateur", "Voce del browser", "Vusch dal navigatur"),
    "No AI voice loaded - the browser voice reads.": ("Keine KI-Stimme geladen – es liest die Browser-Stimme.", "Aucune voix IA chargée – la voix du navigateur lit.",
                                                      "Nessuna voce IA caricata – legge la voce del browser.", "Nagina vusch IA chargiada – la vusch dal navigatur legia."),
    "The AI voice does not answer - the browser voice reads on.": ("Die KI-Stimme antwortet nicht – die Browser-Stimme liest weiter.",
                                                                   "La voix IA ne répond pas – la voix du navigateur continue.",
                                                                   "La voce IA non risponde – continua la voce del browser.",
                                                                   "La vusch IA na respunda betg – la vusch dal navigatur legia vinavant."),
}
for _k, _v in _HX_ALMVL.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])

# ---- the manual: one point in «Vorlesen und Datei-Ansicht» -------------------------------------------------------------------------------
_HELP_ALMVL = {
    "de": "<li><b>Almanach:</b> 🔊 im Überlebens-Almanach liest den Artikel mit derselben Piper-Stimme (Leiste unten: ⏸ / ▶, ⏹ Stopp). "
          "Ist keine deutsche Piper-Stimme geladen oder antwortet sie nicht, liest die Browser-Stimme (mit Hinweis).</li>",
    "en": "<li><b>Almanac:</b> 🔊 in the survival almanac reads the article with the same Piper voice (bar at the bottom: ⏸ / ▶, ⏹ Stop). "
          "Without a German Piper voice, or when it does not answer, the browser voice reads (with a hint).</li>",
    "fr": "<li><b>Almanach :</b> 🔊 dans l’almanach de survie lit l’article avec la même voix Piper (barre en bas : ⏸ / ▶, ⏹ Stop). "
          "Sans voix Piper allemande, ou si elle ne répond pas, la voix du navigateur lit (avec un avis).</li>",
    "it": "<li><b>Almanacco:</b> 🔊 nell’almanacco di sopravvivenza legge l’articolo con la stessa voce Piper (barra in basso: ⏸ / ▶, ⏹ Stop). "
          "Senza una voce Piper tedesca, o se non risponde, legge la voce del browser (con un avviso).</li>",
    "rm": "<li><b>Almanac:</b> 🔊 en l’almanac da survivenza legia l’artitgel cun la medema vusch Piper (trav sutvart: ⏸ / ▶, ⏹ Stop). "
          "Senza vusch Piper tudestga, u sch’ella na respunda betg, legia la vusch dal navigatur (cun ina indicaziun).</li>",
}


def _help_almvl(doc, lang):
    i = doc.find('<section id="vorlesen"')
    if i < 0 or "<b>Almanach:</b>" in doc or "<b>Almanac:</b>" in doc or "<b>Almanach :</b>" in doc or "<b>Almanacco:</b>" in doc:
        return doc
    j = doc.find("</ul></section>", i)
    return doc[:j] + _HELP_ALMVL[lang] + doc[j:] if j > 0 else doc


_hp_en_almvl = HELP_PAGE.find('<div lang="en">')
if _hp_en_almvl > 0:
    HELP_PAGE = _help_almvl(HELP_PAGE[:_hp_en_almvl], "de") + _help_almvl(HELP_PAGE[_hp_en_almvl:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_almvl(HELP_X[_L], _L)


def alm_vl_selftest():
    b = alm_vl_book(0)
    assert b["n"][0] == sum(len(p) for p in b["ch"][0]["p"]) and b["ch"][0]["p"][0] == [alm_vl_arts()[0][0]], "title = first sentence"
    assert all(not x.startswith("- ") for p in b["ch"][0]["p"] for x in p), "list items without «- »"
    s0 = VL["synth"]
    try:
        VL["synth"] = None
        if not piper_ready(ALM_VL_LANG):
            assert alm_vl_ton(0, 0, ALM_VL_LANG) == ("", "no voice"), "without Piper no sound (the browser voice reads)"
            assert alm_vl_info(0, ALM_VL_LANG, "de")["piper"] is False
    finally:
        VL["synth"] = s0
    assert alm_vl_ton(0, 10 ** 6, ALM_VL_LANG)[1] == "unknown sentence"
    if "<script>" in ALM_PAGE:                               # with the additional data (the pages are there)
        assert "window.mwReadP = " in ALM_PAGE and "window.almRead" in ALM_PAGE and "almBrowser" in ALM_PAGE
    return f"{len(alm_vl_arts())} articles, Piper {'ready' if piper_ready(ALM_VL_LANG) else 'missing - browser voice'}"


SELFTEST_EXTRA.append(("Almanac reads aloud with the Piper voice, browser voice as fallback (639zzzzv_vorlesen_almanach)", alm_vl_selftest))
