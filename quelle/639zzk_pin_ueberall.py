#@ MoveEye – Teil 639zzk: «PIN überall im Browser» – die PIN-Frage auf jeder Seite für alles, was den Schutz ausschaltet, und der Selbsttest der Korrekturen «Rechte / Schutz» (Prüfung 10.11.2026)
# ----------------------------------------------------------------------------
# Prüfung vom 10.11.2026 (Besitzer: alle Punkte korrigieren). Die Logik steht dort, wo sie hingehört:
#   2  Rechte-Tabelle genau statt «beginnt mit» (040 view_get_ok / perm_get_ok), /api/factory nur Administrator (586)
#   5  Recht «arm» darf /api/protect (Stand, Stufe, «Schutz testen»; PIN / Eskalation / Anwesenheit: Administrator) (040)
#   6  POST /api/tunnel nur Administrator (040, 550)
#   4  PIN für alles, was der Browser ausschaltet: web_disarms / web_pin_guard (135), pin_guard (550)
#   3  Die Stufe bestimmt die Sirene: protect_siren_sync (135), von jedem Einschalten gerufen (130 arm_level_sync)
#   11 Ein / Aus sofort speichern (040 save_settings_flush), «von Hand» eines Zeitplans übersteht den Neustart (030)
# Hier: die PIN-Frage im Browser. Verlangt der Server die PIN (403 mit "need_pin"), zeigt JEDE Seite dieselbe Frage wie bei
# «Aus» auf der Seite «Schutz» (Feld «PIN», «Ausschalten», ✕) und schickt die Anfrage mit der PIN noch einmal (Kopfzeile
# X-MW-PIN). So braucht keine Seite eigenen Code: Modus «Transport», «Camping aus», «Alle aus» bei mehreren Geräten,
# «Simulation an» (schaltet den Schutz aus) … Die Seite «Schutz» fragt bei «Aus» wie bisher selbst (sie schickt "pin" mit).
# Test: werkzeuge/rechte_schutz_test.py (Benutzer Kind / Familie / ohne Rechte, PIN, Stufen, Zeitplan nach Neustart).
# ----------------------------------------------------------------------------
_HX_PIN = {   # English (key): Deutsch, Français, Italiano, Rumantsch
    "PIN needed": ("PIN nötig", "PIN requis", "PIN necessario", "PIN necessari"),
    "This switches the protection off. Enter the PIN.": (
        "Das schaltet den Schutz aus. Gib die PIN ein.", "Cela désactive la protection. Saisis le PIN.",
        "Questo spegne la protezione. Inserisci il PIN.", "Quai stizza la protecziun. Endatescha il PIN."),
    "Switch off": ("Ausschalten", "Désactiver", "Spegni", "Stizzar"),
    "Cancel": ("Abbrechen", "Annuler", "Annulla", "Interrumper"),
}
for _k, _v in _HX_PIN.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])

PIN_ASK_JS = r"""<script id="mw-pin-ask">
(function () {                                       // 639zzk: the PIN question for every request the server answers with need_pin
  if (window.mwPinAsk || !window.fetch) return;
  const TX = /*PINTX*/{};
  const F = window.fetch.bind(window);
  function T(k) { let l = "de"; try { l = (typeof LANG !== "undefined" && LANG) || document.documentElement.lang || "de"; } catch (e) {}
    const i = ["de", "fr", "it", "rm"].indexOf(String(l).slice(0, 2)); return i < 0 || !TX[k] ? k : TX[k][i]; }
  let busy = null;
  function ask(msg) {                                // the same as «Aus» on the page «Schutz»: field «PIN», «Ausschalten», ✕
    if (busy) return busy;
    busy = new Promise(done => {
      const bg = document.createElement("div"); bg.id = "mw-pin-dlg"; bg.setAttribute("role", "dialog"); bg.setAttribute("aria-modal", "true");
      bg.style.cssText = "position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;padding:16px";
      const box = document.createElement("div");
      box.style.cssText = "background:var(--panel,#111822);color:var(--txt,#e8eef5);border:1px solid var(--line,#1f2b3a);border-radius:14px;padding:16px;max-width:340px;width:100%;box-shadow:0 10px 28px rgba(0,0,0,.4)";
      const h = document.createElement("div"); h.style.cssText = "font-weight:600;margin-bottom:6px"; h.textContent = "🔢 PIN";
      const p = document.createElement("div"); p.id = "mw-pin-msg"; p.style.cssText = "font-size:14px;margin-bottom:10px";
      p.textContent = T("This switches the protection off. Enter the PIN.") + (msg && msg !== T("PIN needed") ? " ⚠ " + msg : "");
      const row = document.createElement("div"); row.style.cssText = "display:flex;gap:6px";
      const i = document.createElement("input"); i.type = "password"; i.inputMode = "numeric"; i.placeholder = "PIN"; i.autocomplete = "off"; i.id = "mw-pin-in";
      i.style.cssText = "flex:1;min-width:0"; i.setAttribute("aria-label", "PIN");
      const ok = document.createElement("button"); ok.type = "button"; ok.id = "mw-pin-ok"; ok.textContent = T("Switch off");
      const no = document.createElement("button"); no.type = "button"; no.id = "mw-pin-no"; no.className = "sec"; no.textContent = "✕"; no.setAttribute("aria-label", T("Cancel"));
      const end = v => { bg.remove(); busy = null; done(v); };
      ok.onclick = () => { if (i.value.trim()) end(i.value.trim()); else i.focus(); };
      no.onclick = () => end(null);
      i.onkeydown = e => { if (e.key === "Enter") ok.click(); else if (e.key === "Escape") end(null); };
      row.append(i, ok, no); box.append(h, p, row); bg.appendChild(box); document.body.appendChild(bg);
      setTimeout(() => i.focus(), 50);
    });
    return busy;
  }
  window.mwPinAsk = ask;
  window.fetch = async function (input, init) {
    const r = await F(input, init);
    try {
      if (r.status !== 403 || typeof input !== "string" || !init || String(init.method || "").toUpperCase() !== "POST") return r;
      let j = await r.clone().json();
      if (!j || !j.need_pin) return r;
      if (typeof init.body === "string" && /"pin"\s*:/.test(init.body)) return r;   // the page asks itself (Schutz → Aus)
      for (let n = 0; n < 5; n++) {
        const pin = await ask(j.error || "");
        if (pin == null) return r;
        const h = new Headers(init.headers || {}); h.set("X-MW-PIN", pin);
        const r2 = await F(input, Object.assign({}, init, {headers: h}));
        if (r2.status !== 403) return r2;
        j = await r2.clone().json().catch(() => null);
        if (!j || !j.need_pin) return r2;
      }
    } catch (e) {}
    return r;
  };
})();
</script>"""
PIN_ASK_JS = PIN_ASK_JS.replace("/*PINTX*/{}", json.dumps({_k: list(_v) for _k, _v in _HX_PIN.items()}, ensure_ascii=False), 1)

_render_page_before_pin = render_page


def render_page(page, active):
    """+ 639zzk: every page can ask for the PIN (before the other scripts run, so their requests go through it)"""
    out = _render_page_before_pin(page, active)
    if 'id="mw-pin-ask"' in out:
        return out
    i = out.find("<body")
    j = out.find(">", i) if i >= 0 else -1
    return out[:j + 1] + PIN_ASK_JS + out[j + 1:] if j >= 0 else out + PIN_ASK_JS


# ---- self-test ------------------------------------------------------------------------------------------------------------
def rechte_schutz_selftest():
    """the corrections of the check of 10.11.2026 without a web server: rights table, PIN list, level -> siren, schedule note"""
    # 2 / 5 / 6: the rights table
    for r_ in ("kid", "friend", "family", "view"):
        for p_ in ("/api/factory", "/api/factory/backup/motionwatch_settings.before_reset_20260101-000000.json", "/api/fax", "/api/statex",
                   "/api/settings/export", "/api/users"):
            assert not role_allows(r_, p_, "GET", {}), (r_, p_)
        assert role_allows(r_, "/api/fa", "GET", {}) and role_allows(r_, "/api/state", "GET", {}) and role_allows(r_, "/i18n/de.js", "GET", {}), r_
        assert role_allows(r_, "/api/ui", "GET", {}) and role_allows(r_, "/api/ui_simple", "GET", {}) and role_allows(r_, "/api/ui_sync", "GET", {}), r_
        assert not role_allows(r_, "/api/tunnel", "POST", {"on": True}) and role_allows(r_, "/api/tunnel", "GET", {}), r_
        assert not role_allows(r_, "/api/factory", "POST", {}), r_
    assert not role_allows("custom", "/api/audio/live", "GET", {}, set()) and role_allows("custom", "/api/audio/live", "GET", {}, {"live"})
    assert role_allows("custom", "/api/audio", "GET", {}, set()), "the state of the sound stays for everybody"
    assert role_allows("view", "/api/recordings/stats", "GET", {}) and not role_allows("view", "/api/recordingsx", "GET", {})
    assert role_allows("family", "/api/protect", "GET", {}) and role_allows("family", "/api/protect", "POST", {"action": "level", "level": "watch"})
    assert role_allows("family", "/api/protect", "POST", {"action": "test"})
    for a_ in ("pin", "escalate", "presence", "fix_push", None):
        assert not role_allows("family", "/api/protect", "POST", {"action": a_}), a_
    assert not role_allows("kid", "/api/protect", "GET", {}) and not role_allows("kid", "/api/protect", "POST", {"action": "level"})
    assert not role_allows("custom", "/api/protect", "GET", {}, set())
    assert role_allows("admin", "/api/factory/backup/x", "GET", {}) and role_allows("admin", "/api/tunnel", "POST", {})
    import copy
    keys = ("armed", "protect_pin", "protect_level", "protect_auto", "escalate_on", "siren_on", "mode", "mode_prev", "camping", "camping_prev",
            "sim_on", "mode_gamer_watch", "sched_manual")
    keep = {k: copy.deepcopy(CFG.get(k)) for k in keys}
    fails = list(PROTECT["pin_fails"]); esc = (PROTECT["esc_t"], PROTECT["esc_id"])
    sched = {k: copy.deepcopy(v) for k, v in SCHED.items()}
    with LOCK:
        plans0 = [dict(s) for s in SCHEDULES]
    names = ("log_event", "save_settings")
    keep_f = {n: globals()[n] for n in names}
    try:
        for n in names:
            globals()[n] = lambda *a, **k: None
        # 4: what the web switches off - and the PIN
        CFG.update(armed=True, mode="", mode_prev={}, camping=False, camping_prev={}, sim_on=False, protect_pin="")
        assert web_disarms("/api/mode", {"mode": "transport"}) and not web_disarms("/api/mode", {"mode": "home"})
        assert not web_disarms("/api/mode", {"mode_fire_hours": 2}) and not web_disarms("/api/mode", {"mode": ""})
        assert web_disarms("/api/fleet", {"action": "disarm", "id": "all"}) and web_disarms("/api/fleet", {"action": "disarm", "id": "me"})
        assert not web_disarms("/api/fleet", {"action": "arm", "id": "all"}) and not web_disarms("/api/fleet", {"action": "disarm", "id": "x1"})
        assert web_disarms("/api/sim", {"on": True, "confirm": True}) and not web_disarms("/api/sim", {"on": True})
        assert web_disarms("/api/simintern", {"action": "start", "confirm": True}) and web_disarms("/api/set", {"key": "armed", "value": False})
        assert not web_disarms("/api/set", {"key": "record", "value": False}) and not web_disarms("/api/arm", {"action": "arm"})
        CFG.update(mode="home", mode_prev={"armed": False})
        assert web_disarms("/api/mode", {"mode": ""}), "back to the own settings that were «off»"
        CFG.update(mode="camping", camping=True, mode_prev={"armed": False}, camping_prev={"armed": False})
        assert web_disarms("/api/camping", {"on": False}) and not web_disarms("/api/camping", {"on": True})
        assert web_disarms("/api/mode", {"mode": "gamer", "mode_gamer_watch": False}) and not web_disarms("/api/mode", {"mode": "gamer", "mode_gamer_watch": True})
        CFG.update(mode="", mode_prev={}, camping=False, camping_prev={})
        CFG["armed"] = False
        assert not web_disarms("/api/mode", {"mode": "transport"}), "already off: nothing to protect"
        CFG["armed"] = True
        assert web_pin_guard("/api/mode", "POST", {"mode": "transport"}, "") is None, "no PIN set: as before"
        CFG["protect_pin"] = _pin_hash("4711"); PROTECT["pin_fails"] = []
        assert web_pin_guard("/api/mode", "POST", {"mode": "transport"}, "") == "PIN needed" and not PROTECT["pin_fails"], "asking is not a wrong PIN"
        assert web_pin_guard("/api/mode", "POST", {"mode": "transport"}, "0000") == "wrong PIN" and len(PROTECT["pin_fails"]) == 1
        assert web_pin_guard("/api/mode", "POST", {"mode": "transport"}, "4711") is None and not PROTECT["pin_fails"]
        assert web_pin_guard("/api/mode", "POST", {"mode": "home"}, "") is None and web_pin_guard("/api/mode", "GET", {"mode": "transport"}, "") is None
        assert web_pin_guard("/api/light", "POST", {"on": True}, "") is None
        assert protect_pin_check("4711")[0] and protect_pin_check("")[1] == "PIN needed"
        PROTECT["pin_fails"] = [time.time()] * 5
        assert protect_pin_check("4711")[1].startswith("too many"); PROTECT["pin_fails"] = []
        assert tr("PIN needed", "de") == "PIN nötig"
        # 3: the level decides about the siren
        CFG.update(protect_pin="", protect_level="full", protect_auto=[], escalate_on=False, siren_on="off")
        assert protect_siren_sync("full") and CFG["escalate_on"] and CFG["siren_on"] == "person" and CFG["protect_auto"] == ["escalate_on", "siren_on"]
        assert not protect_siren_sync() and CFG["escalate_on"], "armed again in «Voll»: stays"
        CFG["protect_level"] = "watch"
        assert protect_siren_sync("watch") and not CFG["escalate_on"] and CFG["siren_on"] == "off" and CFG["protect_auto"] == [], "Voll -> Wachsam"
        protect_siren_sync("full"); CFG["protect_level"] = "off"                    # Voll -> Aus -> switched on by a button / schedule
        assert CFG["escalate_on"] and protect_siren_sync() and not CFG["escalate_on"] and CFG["siren_on"] == "off", "Voll -> Aus -> an = Wachsam without siren"
        CFG.update(siren_on="alarm", escalate_on=False, protect_auto=[])            # the user's own siren stays
        protect_siren_sync("full"); assert CFG["siren_on"] == "alarm" and CFG["protect_auto"] == ["escalate_on"]
        protect_siren_sync("watch"); assert CFG["siren_on"] == "alarm" and not CFG["escalate_on"]
        protect_siren_sync("full"); protect_auto_user("escalate_on"); CFG["protect_level"] = "off"
        assert not protect_siren_sync() and CFG["escalate_on"], "the switch «Sirene nach … s» set by hand stays"
        CFG.update(protect_auto=["?"], escalate_on=True, siren_on="person", protect_level="off")     # older settings file
        assert protect_siren_sync() and not CFG["escalate_on"] and CFG["siren_on"] == "off" and CFG["protect_auto"] == []
        CFG.update(protect_auto=["?"], escalate_on=False, siren_on="person", protect_level="off")
        assert protect_siren_sync() and CFG["siren_on"] == "person" and CFG["protect_auto"] == [], "older file, own siren: stays (only the list is written)"
        CFG.update(protect_auto=[], siren_on="off", escalate_on=False, protect_level="watch")
        protect_siren_sync("watch", "siren"); assert CFG["escalate_on"] and CFG["siren_on"] == "person", "assistant: Wachsam with siren"
        # 11: the note «by hand» of a schedule survives a restart - until the schedule changes
        now = datetime.now().replace(second=0, microsecond=0)
        hm = lambda dt: dt.strftime("%H:%M")
        plan = _clean_schedule({"name": "Nacht", "enabled": True, "start": hm(now - timedelta(minutes=30)), "end": hm(now + timedelta(minutes=30)),
                                "days": list(range(7)), "actions": {"armed": True}}, 0)
        if plan and schedule_active(plan, now) and schedule_active(plan, now - timedelta(minutes=20)) and (now - timedelta(minutes=30)).date() == (now + timedelta(minutes=30)).date():
            CFG["armed"] = False
            for note, want in (({"armed": {"v": True, "t": time.time() - 600}}, True),        # switched off 10 min ago, same window: stays off
                               ({"armed": {"v": True, "t": time.time() - 3 * 3600}}, False),  # 3 h ago: the window was not active then = a new one
                               ({"armed": {"v": False, "t": time.time() - 600}}, False),      # the schedule forces something else now
                               ({"armed": {"v": True, "t": time.time() + 3600}}, False),      # clock nonsense
                               ({"nonsense": {"v": True, "t": time.time()}}, False)):
                SCHED.update(base={}, manual=set(), last={}, restored=False); CFG["sched_manual"] = copy.deepcopy(note)
                sched_manual_restore([plan], now)
                assert ("armed" in SCHED["manual"]) == want and (CFG["sched_manual"] == note) == want, (note, SCHED, CFG["sched_manual"])
                assert not want or (SCHED["last"] == {"armed": True} and SCHED["base"] == {"armed": False})
            SCHED.update(base={}, manual=set(), last={"armed": True}); CFG["sched_manual"] = {}
            sched_user_changed("armed")
            assert CFG["sched_manual"]["armed"]["v"] is True and abs(CFG["sched_manual"]["armed"]["t"] - time.time()) < 5, "written with the switch"
            SCHED["manual"].discard("armed"); assert _sched_manual_note({"armed": True}) and CFG["sched_manual"] == {}, "the schedule took over: note gone"
        assert "save_settings_flush" in globals() and '"mw-pin-ask"' in render_page("<html><head></head><body><p>x</p></body></html>", "live")
        assert render_page("<html><head></head><body></body></html>", "live").count('id="mw-pin-ask"') == 1 and "/*PINTX*/" not in PIN_ASK_JS
    finally:
        globals().update(keep_f)
        CFG.update(keep); PROTECT["pin_fails"] = fails; PROTECT["esc_t"], PROTECT["esc_id"] = esc
        SCHED.clear(); SCHED.update(sched)
    return "rights exact (factory, audio/live, tunnel, protect), PIN for everything the web switches off, level -> siren, schedule note"


SELFTEST_EXTRA.append(("Rights and protection: check of 10.11.2026 (639zzk)", rechte_schutz_selftest))
