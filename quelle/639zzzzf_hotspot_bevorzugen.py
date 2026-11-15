#@ MoveEye – Teil 639zzzzf: «📶 Mein Handy-Hotspot bevorzugen» – ein gespeichertes Netz als eigener Handy-Hotspot, MoveEye wechselt hin, sobald er da ist. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Besitzer 15.11.2026. Ein Schalter (ab Werk aus) und EIN gespeichertes Netz als «Mein Handy-Hotspot» (Karte «WLAN / Hotspot»,
# Liste der gespeicherten Netze; Fenster: derselbe Abschnitt). Ist der Schalter an, schaut MoveEye alle 30 s nach, ob der
# Hotspot zu sehen ist, und verbindet sich, sobald er da ist – aus dem eigenen WLAN (AP), aus einem anderen WLAN und ohne Netz.
#   Suchen: die Liste von NetworkManager (`--rescan no`), ein echtes Neu-Suchen höchstens alle 2 min (`--rescan auto`, die
#     Grenze von NetworkManager gilt dazu); Im eigenen WLAN mit
#     nur einem Adapter liefert NetworkManager meist keine Liste: dann höchstens alle 5 min ein kurzer Blick (eigenes WLAN
#     ~15 s aus), nur wenn kein Gerät verbunden ist.
#   Warten statt wechseln: Geräte im eigenen WLAN (ausser mit zweitem Adapter, 150 DUAL), Alarm (rot, Aufnahme, Person,
#     Verfolgen, Diebstahl / GPS: hp_quiet 639zzzh), Update / Neustart / Ausschalten, Sicherung lädt hoch (060 Backup.busy),
#     Homepage lädt hoch (HP). Von Hand umgeschaltet (eigenes WLAN, Camping, «Jetzt verbinden»): 10 min Ruhe; Netz-Automatik
#     pausiert oder Camping-Profil: ganz Ruhe.
#   Sicherheitsnetz: klappt das Verbinden nicht oder hat der Hotspot kein Internet (40 s), geht es zurück wie bisher (das
#     vorherige Netz, sonst / vorher das eigene WLAN), der Hotspot wird getrennt (NetworkManager verbindet ihn dann nicht
#     gleich wieder von selbst). Danach Pause 2, 5, 10 min (bleibt 10). Bricht er in den ersten 10 min wieder weg, zählt
#     das auch als Fehler (kein Hin und Her). Nach 10 min stabil ist der Zähler wieder 0.
#   Push: keiner von hier; die bestehende Meldung «MoveEye ist online (bekanntes WLAN): Adresse» (110) kommt nach dem
#     Wechsel von selbst und nennt nie einen WLAN-Namen; der Name des Hotspots kommt zusätzlich in push_ssids (635c).
#   Protokoll: Wechsel und Rückweg mit dem Namen des Hotspots (nur lokal), nie ein Passwort.
# Läuft im Faden der Netz-Automatik (160 NetAuto.step), so kommen sich die beiden nie in die Quere. Nur NetworkManager.
# Texte: _HX_HSP (5 Sprachen). Test: werkzeuge/hotspot_bevorzugen_test.py (erfundenes nmcli / iw / ip).
# ----------------------------------------------------------------------------
HSP_DEF = {"hs_prefer": False, "hs_prefer_ssid": ""}
for _k, _v in HSP_DEF.items():
    CFG.setdefault(_k, _v); DEFAULTS.setdefault(_k, _v); FACTORY_CFG.setdefault(_k, _v)
FACTORY_KEEP.update(HSP_DEF)
LOCK_DENY_KEYS.update(HSP_DEF)
HSP_EVERY_S = 30.0                  # one look every 30 s
HSP_RESCAN_S = 120.0                # a real new search at most every 2 min (the stream suffers a little while the adapter scans)
HSP_PEEK_S = 300.0                  # own Wi-Fi, one adapter, no list: a short look at most every 5 min
HSP_NET_S = 40.0                    # the hotspot must give internet within this time
HSP_HAND_S = 600.0                  # switched by hand: quiet for 10 min
HSP_STABLE_S = 600.0                # gone again within 10 min = a failure
HSP_BACKOFF = (120.0, 300.0, 600.0)
HSPREF = {"state": "off", "n": 0, "fails": 0, "next": 0.0, "tick": 0.0, "rescan": 0.0, "peek": 0.0, "on_since": 0.0, "hand": -1e9,
          "saved": [], "saved_t": -1e9}
# the state is the English text itself (tr / t() on the page and in the window), {n} = minutes or devices
HSP_OK, HSP_AWAY, HSP_GO = "connected", "not in range", "found - connecting …"
HSP_BACK = "after a failure: next try in {n} min"
HSP_DEV1, HSP_DEVN = "waiting, because {n} device is connected", "waiting, because {n} devices are connected"


def hspref_hand():
    HSPREF["hand"] = time.monotonic()


def _hsp_set(state, n=0):
    HSPREF.update(state=state, n=n)
    return state


def hspref_block():
    """why not to switch now (alarm, update, backup / homepage upload), otherwise '' """
    try:
        w = WATCH_REF.get("w")
        if (not hp_quiet() or STATE.get("tracking") or STATE.get("persons") or STATE.get("recording")
                or getattr(w, "writer", None) is not None):
            return "found - waiting for the alarm to end"
        if UPD_PROG.get("phase") or RESTART.get("pending") or POWER.get("pending"):
            return "found - waiting for the update"
        if getattr(BACKUP, "busy", ""):
            return "found - waiting for the backup upload"
        if HP.get("busy"):
            return "found - waiting for the homepage upload"
    except Exception:
        pass
    return ""


def _hsp_saved(fresh=False):
    if fresh or time.monotonic() - HSPREF["saved_t"] > 300:
        HSPREF["saved"] = _nm_saved(); HSPREF["saved_t"] = time.monotonic()
    return HSPREF["saved"]


def _hsp_active():
    """(own Wi-Fi on, {uuid} of the joined Wi-Fi networks) straight from NetworkManager"""
    code, out, _e = _run(["nmcli", "-t", "-f", "NAME,UUID,TYPE", "connection", "show", "--active"], 10)
    ap, cur = False, set()
    for f in (map(_nm_split, out.splitlines()) if code == 0 else ()):
        if len(f) >= 3 and f[2] in ("802-11-wireless", "wifi"):
            ap = ap or f[0] == HOTSPOT_CON
            if f[0] != HOTSPOT_CON:
                cur.add(f[1])
    return ap, cur


def hspref_scan(iface, ap, rescan="no"):
    """{ssid: signal} the adapter sees, or None when it cannot search (own Wi-Fi, one adapter)"""
    for r in dict.fromkeys((rescan, "no")):
        code, out, _e = _run(["nmcli", "-t", "-f", "SSID,SIGNAL", "device", "wifi", "list", "ifname", iface, "--rescan", r], 30)
        if code == 0:
            break
    else:
        return None
    seen = {}
    for f in map(_nm_split, out.splitlines()):
        if len(f) >= 2 and f[0] and not (ap and f[0] == CFG["hotspot_ssid"]):
            seen[f[0]] = max(seen.get(f[0], 0), int(f[1]) if f[1].isdigit() else 0)
    return seen if seen or not ap else None


def hspref_online(secs=HSP_NET_S):
    """does the internet answer within secs?"""
    import socket
    end = time.monotonic() + secs
    while True:
        for hp in (("1.1.1.1", 443), ("8.8.8.8", 443), ("1.1.1.1", 53)):
            try:
                socket.create_connection(hp, timeout=3).close()
                return True
            except Exception:
                pass
        if time.monotonic() >= end:
            return False
        time.sleep(3)


def _hsp_ap(on):
    ok = hotspot_set(on, persist=False)[0]
    hotspot_refresh()
    return ok


def _hsp_fail(ssid, why):
    HSPREF["fails"] += 1
    d = HSP_BACKOFF[min(HSPREF["fails"], len(HSP_BACKOFF)) - 1]
    HSPREF["next"] = time.monotonic() + d; HSPREF["on_since"] = 0.0
    log_event("sys", f"Phone hotspot «{ssid}»: {why} - next try in {int(d / 60)} min")


def hspref_switch(tgt, prev, ap, frm):
    """join the hotspot; on failure back to where it was (previous network / own Wi-Fi). True = connected with internet"""
    uid, ssid = tgt["id"], tgt["ssid"]
    WIFI.update(busy=True, job=f"connecting to {ssid}…", job_ok=None)
    log_event("sys", f"Phone hotspot «{ssid}» in range: switching ({frm})")
    try:
        if ap and not DUAL["on"]:
            _hsp_ap(False)
        with _WIFI_LOCK:
            code, _o, err = _run(["nmcli", "--wait", "40", "connection", "up", "uuid", uid] + (["ifname", DUAL["up"]] if DUAL["on"] else []), 50)
        why = ("could not connect (" + _perm_hint(err)[:80] + ")") if code else "" if hspref_online() else "no internet"
        if not why:
            HSPREF["on_since"] = time.monotonic()
            WIFI.update(job=f"connected to {ssid} · {page_address()}", job_ok=True)
            log_event("sys", f"Phone hotspot «{ssid}»: connected, internet works")
            return True
        with _WIFI_LOCK:
            if not code:
                _run(["nmcli", "connection", "down", "uuid", uid], 30)     # NetworkManager then does not take it again by itself
            back = "" if not prev else " - back on «%s»" % prev["ssid"] if _nm_up(prev["id"]) else " - previous network did not come back"
        if (ap or not back.startswith(" - back")) and not DUAL["on"] and (ap or CFG["net_mode"] != "client"):
            back += " - own Wi-Fi on" if _hsp_ap(True) else " - own Wi-Fi did not come on"
        WIFI.update(job=f"failed: {why}{back}", job_ok=False)
        _hsp_fail(ssid, why + back)
        return False
    finally:
        WIFI.update(busy=False, refresh=True)


def hspref_tick(force=False):
    """one look (from the thread of the network automatic every 2 s, works every HSP_EVERY_S); returns the state"""
    ssid, now = str(CFG.get("hs_prefer_ssid") or ""), time.monotonic()
    if not CFG.get("hs_prefer"):
        HSPREF["on_since"] = 0.0
        return _hsp_set("off")
    if not ssid:
        return _hsp_set("choose a saved network as «My phone hotspot»")
    if not force and now < HSPREF["tick"] or WIFI.get("busy") or WIFI.get("hs_busy"):
        return HSPREF["state"]
    HSPREF["tick"] = now + HSP_EVERY_S
    if wifi_backend() != "nm":
        return _hsp_set("needs NetworkManager")
    tgt = next((s for s in _hsp_saved() if s["ssid"] == ssid), None) or next((s for s in _hsp_saved(True) if s["ssid"] == ssid), None)
    if tgt is None:
        return _hsp_set("no longer saved")
    ap, cur = _hsp_active()
    if tgt["id"] in cur:
        if HSPREF["on_since"] and now - HSPREF["on_since"] >= HSP_STABLE_S:
            HSPREF.update(fails=0, on_since=0.0)                  # stable: the next failure waits 2 min again
        return _hsp_set(HSP_OK)
    if HSPREF["on_since"]:
        if now - HSPREF["on_since"] < HSP_STABLE_S:
            _hsp_fail(ssid, "gone again soon after switching")    # no flapping
        HSPREF["on_since"] = 0.0
    if now < HSPREF["next"]:
        return _hsp_set(HSP_BACK, int((HSPREF["next"] - now) / 60 + 0.99))
    if NETAUTO.get("paused") or CFG.get("camping") or now - HSPREF["hand"] < HSP_HAND_S:
        return _hsp_set("paused (switched by hand)")
    prev = next((s for s in _hsp_saved() if s["id"] in cur), None)
    one = ap and not DUAL["on"]                                   # own Wi-Fi on the only adapter
    clients = _hotspot_clients(WIFI.get("ap_iface") or WIFI["iface"]) if one else 0
    resc = "auto" if not cur or now - HSPREF["rescan"] >= HSP_RESCAN_S else "no"
    if resc == "auto":
        HSPREF["rescan"] = now
    seen = hspref_scan(WIFI["iface"], one, resc)
    frm = "from the own Wi-Fi" if one else f"from «{prev['ssid']}»" if prev else "no network before"
    if seen is None and one:                                      # no list in the own Wi-Fi: a short look now and then
        blk = (HSP_DEVN if clients > 1 else HSP_DEV1) if clients else hspref_block()
        if blk or now - HSPREF["peek"] < HSP_PEEK_S:
            return _hsp_set(blk or "own Wi-Fi: next look in {n} min", clients or int((HSPREF["peek"] + HSP_PEEK_S - now) / 60 + 0.99))
        HSPREF["peek"] = now
        log_event("sys", f"Phone hotspot «{ssid}»: own Wi-Fi off for a moment to look for it")
        _hsp_ap(False)
        seen = hspref_scan(WIFI["iface"], False, "yes") or {}
        if ssid not in seen:
            _hsp_ap(True)
    if ssid not in (seen or {}):
        return _hsp_set(HSP_AWAY)
    blk = (HSP_DEVN if clients > 1 else HSP_DEV1) if clients else hspref_block()
    if blk:
        return _hsp_set(blk, clients)
    _hsp_set(HSP_GO)
    if hspref_switch(tgt, prev, ap, frm):
        return _hsp_set(HSP_OK)
    return _hsp_set(HSP_BACK, int((HSPREF["next"] - time.monotonic()) / 60 + 0.99))


def hspref_set(on=None, ssid=None):
    """the switch and / or the chosen network (a saved one, '' = none)"""
    if ssid:
        if wifi_backend() == "nm" and ssid not in {s["ssid"] for s in _hsp_saved(True)}:
            return False, "the network is not saved"
    if ssid is not None:
        CFG["hs_prefer_ssid"] = str(ssid)
    if on is not None:
        CFG["hs_prefer"] = bool(on)
    HSPREF.update(fails=0, next=0.0, tick=0.0, on_since=0.0, peek=0.0)
    save_settings()
    log_event("sys", f"Phone hotspot preferred: {'on' if CFG['hs_prefer'] else 'off'} «{CFG['hs_prefer_ssid']}»")
    return True, ""


def hspref_state():
    return {"on": bool(CFG.get("hs_prefer")), "ssid": CFG.get("hs_prefer_ssid") or "", "state": HSPREF["state"], "n": HSPREF["n"]}


def hspref_text(L=None):
    """«📶 Hotspot «name»: …» (the window; the page builds the same with t())"""
    h = hspref_state()
    if not h["on"] or h["state"] == "off":
        return ""
    s = trf(h["state"], L, n=h["n"])
    return trf("📶 Hotspot «{name}»: {state}", L, name=h["ssid"], state=s) if h["ssid"] else "📶 " + s


# ---- hooks: the network automatic runs it, manual switching pauses it, the state goes with /api/wifi -----------------------------
_hsp_netauto_step_base = NetAuto.step


def _hsp_netauto_step(self):
    _hsp_netauto_step_base(self)
    try:
        hspref_tick()
    except Exception as e:
        HSPREF["state"] = "error: " + str(e)[:80]


# wraps: NetAuto.step (160)
NetAuto.step = _hsp_netauto_step
_netauto_pause_base = netauto_pause


def netauto_pause():                                       # + 639zzzzf: switched by hand
    hspref_hand()
    _netauto_pause_base()


_wifi_connect_base = wifi_connect


def wifi_connect(ssid, password="", preferred=True):       # + 639zzzzf: «Connect now» by hand
    hspref_hand()
    return _wifi_connect_base(ssid, password, preferred)


_wifi_status_base = wifi_status


def wifi_status():                                         # + 639zzzzf
    st = _wifi_status_base()
    st["hsp"] = hspref_state()
    return st


_push_ssids_base = push_ssids


def push_ssids():                                          # + 639zzzzf: the name of the phone hotspot never leaves the device
    out = _push_ssids_base()
    s = str(CFG.get("hs_prefer_ssid") or "").strip()
    return sorted(out + [s], key=len, reverse=True) if len(s) >= 3 and s not in out and s not in _NOSSID_KEEP else out


# ---- the page: in the card «Wi-Fi / hotspot» (switch, state) and a mark in the list of saved networks ----------------------------
HSP_HTML = r"""
<style id="hsp-css">
#hsp-box{margin:10px 0 4px;padding:10px 12px;border-radius:12px;background:rgba(80,140,255,.07);border-left:4px solid #4a8cff}
#hsp-box .hsp-st{margin-top:6px;font-weight:600;overflow-wrap:anywhere}
#hsp-box .hsp-st.ok{color:var(--grn)}
.wf-saved .hsp-b{padding:3px 8px;margin-right:6px}
.wf-saved .hsp-b.on{background:#4a8cff;color:#fff;border-color:#4a8cff}
.wf-saved .hsp-tag{display:inline-block;margin-left:6px;padding:1px 7px;border-radius:9px;background:rgba(74,140,255,.18);font-size:12px}
</style>
<script>
try { Object.assign(I18N.de, {"Mark as my phone hotspot": "Als meinen Handy-Hotspot markieren", "tap again to remove the mark": "nochmals tippen entfernt die Markierung", "Mark one of the saved networks below with 📶.": "Eines der gespeicherten Netze unten mit 📶 markieren.", "As soon as it is in range, MoveEye switches to it by itself (checks every 30 s) - also from the own Wi-Fi or another network. Not during an alarm and not while a device is connected to the own Wi-Fi.": "Sobald er in Reichweite ist, wechselt MoveEye von selbst hin (prüft alle 30 s) – auch aus dem eigenen WLAN oder einem anderen Netz. Nicht während eines Alarms und nicht, solange ein Gerät mit dem eigenen WLAN verbunden ist."}); } catch (e) {}
// 639zzzzf «Mein Handy-Hotspot bevorzugen»: a box in the Wi-Fi card, 📶 in the saved networks, painted after wfRender (530)
(function () {
  const tt = (k, o) => { let s = t(k); for (const n in (o || {})) s = s.split("{" + n + "}").join(o[n]); return s; };
  window.hspText = function (h) {
    if (!h || !h.on || h.state === "off") return "";
    const st = tt(h.state, {n: h.n});
    return h.ssid ? tt("📶 Hotspot «{name}»: {state}", {name: h.ssid, state: st}) : "📶 " + st;
  };
  async function set(o) { const r = await wfPost(Object.assign({action: "prefer"}, o)); if (r && r.ok) toast(t("Saved")); }
  window.hspPaint = function (W) {
    let box = $("#hsp-box"); const er = $("#wf-err"); if (!W || !er) return;
    if (!box) { box = el("div", ""); box.id = "hsp-box"; er.after(box); }
    const h = W.hsp; box.hidden = !h || !W.backend; if (box.hidden) return;
    box.textContent = "";
    const row = el("label", "row pr-sw"); const cb = document.createElement("input"); cb.type = "checkbox"; cb.className = "sw"; cb.id = "hsp-on"; cb.checked = !!h.on;
    cb.onchange = () => set({on: cb.checked});
    const lab = el("span", ""); lab.append(el("b", "", "📶 " + t("Prefer my phone hotspot")), el("br"),
      el("span", "mut", t("As soon as it is in range, MoveEye switches to it by itself (checks every 30 s) - also from the own Wi-Fi or another network. Not during an alarm and not while a device is connected to the own Wi-Fi.")));
    row.append(lab, cb); box.appendChild(row);
    if (h.on) { const s = el("div", "hsp-st" + (h.state === "connected" ? " ok" : ""), hspText(h)); s.id = "hsp-st"; box.appendChild(s); }
    if (!h.ssid) box.appendChild(el("div", "mut", "👉 " + t("Mark one of the saved networks below with 📶.")));
    document.querySelectorAll("#wf-saved .wf-saved").forEach(r => {
      const nm = r.querySelector("b"), x = r.querySelector("button:last-child"); if (!nm || !x || r.querySelector(".hsp-b")) return;
      const ssid = nm.textContent, mine = ssid === h.ssid;
      const b = el("button", "sec hsp-b" + (mine ? " on" : ""), "📶"); b.type = "button";
      b.title = mine ? t("My phone hotspot") + " – " + t("tap again to remove the mark") : t("Mark as my phone hotspot");
      b.onclick = () => set({ssid: mine ? "" : ssid});
      r.insertBefore(b, x);
      if (mine) nm.after(el("span", "hsp-tag", "📶 " + t("My phone hotspot")));
    });
  };
  const base = wfRender;
  wfRender = function () { base(); try { hspPaint(WF); } catch (e) {} };
})();
</script>
"""


# ---- the Pi window: «Wi-Fi / hotspot» gets the switch, the choice of the network and the state ----------------------------------
_hsp_tk_build_section_base = App._build_section


def _hsp_tk_build_section(self, sec, sbody, settings_parent=None):
    _hsp_tk_build_section_base(self, sec, sbody, settings_parent)
    if sec != "Wi-Fi / hotspot" or CFG["lock_on"]:
        return
    try:
        v = tk.BooleanVar(value=bool(CFG.get("hs_prefer")))
        ttk.Checkbutton(sbody, text="📶 " + tr("Prefer my phone hotspot"), variable=v, command=lambda: hspref_set(v.get())).pack(anchor="w", pady=(10, 0))
        cb = ttk.Combobox(sbody, state="readonly"); cb.pack(fill="x", pady=(4, 0))
        lab = ttk.Label(sbody, text="", style="Mut.TLabel", wraplength=380, justify="left"); lab.pack(anchor="w", pady=(4, 0))
        nm = []
        threading.Thread(target=lambda: nm.extend(s["ssid"] for s in _hsp_saved(True)), daemon=True).start()
        cb.bind("<<ComboboxSelected>>", lambda _e: (hspref_set(None, nm[cb.current()]) if 0 <= cb.current() < len(nm) else None, self.root.focus_set()))

        def paint():
            if not lab.winfo_exists():
                return
            vals = [("📶 " if n == CFG["hs_prefer_ssid"] else "") + n for n in nm]
            if list(cb["values"]) != vals:
                cb["values"] = vals
                if CFG["hs_prefer_ssid"] in nm:
                    cb.current(nm.index(CFG["hs_prefer_ssid"]))
            lab.config(text=hspref_text() or tr("My phone hotspot") + ": " + (CFG["hs_prefer_ssid"] or "–"))
            lab.after(2000, paint)
        paint()
    except Exception as e:
        log_event("sys", f"Window: phone hotspot: {e}"[:160])


# wraps: App._build_section (570)
App._build_section = _hsp_tk_build_section


# ---- texts (English key: Deutsch, français, italiano, rumantsch) -------------------------------------------------------------------
_HX_HSP = {
    "Prefer my phone hotspot": ("Mein Handy-Hotspot bevorzugen", "Préférer le point d'accès de mon portable", "Preferire l'hotspot del mio cellulare",
                                "Preferir il hotspot da mes telefonin"),
    "My phone hotspot": ("Mein Handy-Hotspot", "Point d'accès de mon portable", "Hotspot del mio cellulare", "Hotspot da mes telefonin"),
    "📶 Hotspot «{name}»: {state}": ("📶 Hotspot «{name}»: {state}", "📶 Point d'accès «{name}» : {state}", "📶 Hotspot «{name}»: {state}", "📶 Hotspot «{name}»: {state}"),
    "connected": ("verbunden", "connecté", "connesso", "collià"),
    "found - connecting …": ("gefunden – verbindet …", "trouvé – connexion …", "trovato – collegamento …", "chattà – colliescha …"),
    "not in range": ("nicht in Reichweite", "hors de portée", "non a portata", "betg en la portada"),
    "after a failure: next try in {n} min": ("nach einem Fehler: nächster Versuch in {n} min", "après un échec : prochain essai dans {n} min",
                                              "dopo un errore: prossimo tentativo tra {n} min", "suenter in sbagl: proxim emprova en {n} min"),
    "paused (switched by hand)": ("pausiert (von Hand umgeschaltet)", "en pause (changé à la main)", "in pausa (cambiato a mano)", "pausà (midà a maun)"),
    "found - waiting for the alarm to end": ("gefunden – wartet, bis der Alarm vorbei ist", "trouvé – attend la fin de l'alarme",
                                             "trovato – aspetta la fine dell'allarme", "chattà – spetga ch'il alarm è a fin"),
    "found - waiting for the update": ("gefunden – wartet auf das Update", "trouvé – attend la mise à jour", "trovato – aspetta l'aggiornamento",
                                       "chattà – spetga l'actualisaziun"),
    "found - waiting for the backup upload": ("gefunden – wartet, bis die Sicherung hochgeladen ist", "trouvé – attend l'envoi de la sauvegarde",
                                              "trovato – aspetta il caricamento del backup", "chattà – spetga che la segirezza è chargiada si"),
    "found - waiting for the homepage upload": ("gefunden – wartet, bis die Homepage hochgeladen ist", "trouvé – attend l'envoi de la page d'accueil",
                                                "trovato – aspetta il caricamento della homepage", "chattà – spetga che la homepage è chargiada si"),
    "waiting, because {n} device is connected": ("wartet, weil {n} Gerät verbunden ist", "attend, car {n} appareil est connecté",
                                                 "aspetta, perché {n} dispositivo è collegato", "spetga, perquai ch'{n} apparat è collià"),
    "waiting, because {n} devices are connected": ("wartet, weil {n} Geräte verbunden sind", "attend, car {n} appareils sont connectés",
                                                   "aspetta, perché {n} dispositivi sono collegati", "spetga, perquai che {n} apparats èn collads"),
    "own Wi-Fi: next look in {n} min": ("eigenes WLAN: nächster Blick in {n} min", "Wi-Fi propre : prochain coup d'œil dans {n} min",
                                        "Wi-Fi proprio: prossima occhiata tra {n} min", "agen WLAN: proxim sguard en {n} min"),
    "no longer saved": ("nicht mehr gespeichert", "n'est plus enregistré", "non più salvato", "betg pli memorisà"),
    "needs NetworkManager": ("braucht NetworkManager", "nécessite NetworkManager", "richiede NetworkManager", "basegna NetworkManager"),
    "choose a saved network as «My phone hotspot»": ("ein gespeichertes Netz als «Mein Handy-Hotspot» wählen",
                                                    "choisir un réseau enregistré comme « Point d'accès de mon portable »",
                                                    "scegli una rete salvata come «Hotspot del mio cellulare»",
                                                    "tscherner ina rait memorisada sco «Hotspot da mes telefonin»"),
    "the network is not saved": ("das Netz ist nicht gespeichert", "le réseau n'est pas enregistré", "la rete non è salvata", "la rait n'è betg memorisada"),
}
for _k, _v in _HX_HSP.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
if 'id="hsp-css"' not in WEB_PAGE:                          # the box and its script at the end of the main page (530)
    WEB_PAGE = WEB_PAGE.replace("</body>", "<script>try { Object.assign(I18N.de, " + json.dumps({k: v[0] for k, v in _HX_HSP.items()}, ensure_ascii=False)
                                + "); } catch (e) {}</script>" + HSP_HTML + "</body>", 1)
TRX["fr"].update({'Mark as my phone hotspot': "Marquer comme point d'accès de mon portable", 'tap again to remove the mark': 'toucher encore pour enlever la marque', 'Mark one of the saved networks below with 📶.': 'Marque un des réseaux enregistrés ci-dessous avec 📶.', 'As soon as it is in range, MoveEye switches to it by itself (checks every 30 s) - also from the own Wi-Fi or another network. Not during an alarm and not while a device is connected to the own Wi-Fi.': "Dès qu'il est à portée, MoveEye s'y connecte tout seul (contrôle toutes les 30 s) – aussi depuis son propre Wi-Fi ou un autre réseau. Pas pendant une alarme ni tant qu'un appareil est connecté au Wi-Fi propre."})
TRX["it"].update({'Mark as my phone hotspot': 'Segna come hotspot del mio cellulare', 'tap again to remove the mark': 'tocca di nuovo per togliere il segno', 'Mark one of the saved networks below with 📶.': 'Segna con 📶 una delle reti salvate qui sotto.', 'As soon as it is in range, MoveEye switches to it by itself (checks every 30 s) - also from the own Wi-Fi or another network. Not during an alarm and not while a device is connected to the own Wi-Fi.': "Appena è a portata, MoveEye ci passa da solo (controlla ogni 30 s) – anche dal proprio Wi-Fi o da un'altra rete. Non durante un allarme e non finché un dispositivo è collegato al Wi-Fi proprio."})
TRX["rm"].update({'Mark as my phone hotspot': 'Marcar sco hotspot da mes telefonin', 'tap again to remove the mark': 'smatgar anc ina giada allontanescha la marca', 'Mark one of the saved networks below with 📶.': 'Marcar ina da las rets memorisadas sutvart cun 📶.', 'As soon as it is in range, MoveEye switches to it by itself (checks every 30 s) - also from the own Wi-Fi or another network. Not during an alarm and not while a device is connected to the own Wi-Fi.': "Uschespert ch'el è en la portada, mida MoveEye sez (controllescha mintga 30 s) – er ord l'agen WLAN u d'ina autra rait. Betg durant in alarm e betg uschè ditg ch'in apparat è collià cun l'agen WLAN."})


# ---- the manual: one paragraph at the end of «System & network» ------------------------------------------------------------------
HELP_HSP = {
    "de": '<p id="hsp-help"><b>📶 Mein Handy-Hotspot bevorzugen (Einstellungen → Netz &amp; Zugang → WLAN / Hotspot; auch im Pi-Fenster):</b> In der Liste der gespeicherten Netze eines mit 📶 als «Mein Handy-Hotspot» markieren und den Schalter einschalten (ab Werk aus). MoveEye schaut dann alle 30 s nach, ob der Hotspot da ist, und wechselt von selbst hin – aus dem eigenen WLAN, aus einem anderen WLAN (z. B. zu Hause) oder wenn gar kein Netz da ist. Es wartet, solange ein Gerät mit dem eigenen WLAN verbunden ist («wartet, weil 1 Gerät verbunden ist»), während eines Alarms (rot, Aufnahme, Person, Diebstahl) und während Update, Sicherung oder Homepage hochladen. Klappt es nicht oder hat der Hotspot kein Internet, geht MoveEye zurück wie bisher (voriges Netz oder eigenes WLAN) und versucht es erst nach 2, dann 5, dann 10 Minuten wieder. Nach dem Wechsel kommt wie immer die Push-Nachricht mit der neuen Adresse (ohne WLAN-Namen); Tailscale verbindet sich von selbst neu. Im eigenen WLAN mit nur einem WLAN-Adapter kann MoveEye nicht ständig suchen: dann schaut es höchstens alle 5 Minuten kurz nach (eigenes WLAN rund 15 s aus, nur wenn niemand verbunden ist). Von Hand umgeschaltet: 10 Minuten Ruhe.</p>',
    "en": '<p id="hsp-help"><b>📶 Prefer my phone hotspot (Settings → Network &amp; access → Wi-Fi / hotspot; also in the Pi window):</b> mark one of the saved networks with 📶 as «My phone hotspot» and switch it on (off from the factory). MoveEye then looks every 30 s whether the hotspot is there and switches to it by itself – from the own Wi-Fi, from another Wi-Fi (e.g. at home) or when there is no network at all. It waits while a device is connected to the own Wi-Fi («waiting, because 1 device is connected»), during an alarm (red, recording, person, theft) and while an update, a backup or the homepage is uploading. If it does not work or the hotspot has no internet, MoveEye goes back as before (previous network or own Wi-Fi) and tries again only after 2, then 5, then 10 minutes. After the change the push message with the new address comes as always (without Wi-Fi name); Tailscale reconnects by itself. In the own Wi-Fi with only one Wi-Fi adapter MoveEye cannot search all the time: it then looks at most every 5 minutes for a moment (own Wi-Fi off for about 15 s, only when nobody is connected). Switched by hand: quiet for 10 minutes.</p>',
    "fr": '<p id="hsp-help"><b>📶 Préférer le point d\'accès de mon portable (Réglages → Réseau &amp; accès → Wi-Fi / point d\'accès ; aussi dans la fenêtre du Pi) :</b> marque un des réseaux enregistrés avec 📶 comme « Point d\'accès de mon portable » et active l\'interrupteur (désactivé d\'usine). MoveEye regarde alors toutes les 30 s si le point d\'accès est là et s\'y connecte tout seul – depuis son propre Wi-Fi, depuis un autre Wi-Fi (p. ex. à la maison) ou quand il n\'y a aucun réseau. Il attend tant qu\'un appareil est connecté au Wi-Fi propre, pendant une alarme (rouge, enregistrement, personne, vol) et pendant une mise à jour ou l\'envoi d\'une sauvegarde ou de la page d\'accueil. Si cela échoue ou si le point d\'accès n\'a pas d\'Internet, MoveEye revient comme avant (réseau précédent ou Wi-Fi propre) et réessaie après 2, puis 5, puis 10 minutes. Après le changement, la notification avec la nouvelle adresse arrive comme toujours (sans nom de Wi-Fi) ; Tailscale se reconnecte tout seul. Dans le Wi-Fi propre avec un seul adaptateur, MoveEye ne peut pas chercher en continu : il regarde au plus toutes les 5 minutes (Wi-Fi propre coupé environ 15 s, seulement si personne n\'est connecté). Changé à la main : 10 minutes de pause.</p>',
    "it": '<p id="hsp-help"><b>📶 Preferire l\'hotspot del mio cellulare (Impostazioni → Rete &amp; accesso → Wi-Fi / hotspot; anche nella finestra del Pi):</b> segna con 📶 una delle reti salvate come «Hotspot del mio cellulare» e accendi l\'interruttore (spento di fabbrica). MoveEye guarda allora ogni 30 s se l\'hotspot c\'è e ci passa da solo – dal proprio Wi-Fi, da un altro Wi-Fi (p. es. a casa) o quando non c\'è nessuna rete. Aspetta finché un dispositivo è collegato al Wi-Fi proprio, durante un allarme (rosso, registrazione, persona, furto) e durante un aggiornamento o il caricamento di un backup o della homepage. Se non funziona o l\'hotspot non ha Internet, MoveEye torna come prima (rete precedente o Wi-Fi proprio) e riprova solo dopo 2, poi 5, poi 10 minuti. Dopo il cambio arriva come sempre la notifica con il nuovo indirizzo (senza nome del Wi-Fi); Tailscale si ricollega da solo. Nel Wi-Fi proprio con un solo adattatore MoveEye non può cercare di continuo: guarda al massimo ogni 5 minuti (Wi-Fi proprio spento circa 15 s, solo se nessuno è collegato). Cambiato a mano: 10 minuti di pausa.</p>',
    "rm": '<p id="hsp-help"><b>📶 Preferir il hotspot da mes telefonin (Parameters → Rait &amp; access → WLAN / hotspot; er en la fanestra dal Pi):</b> marcar ina da las rets memorisadas cun 📶 sco «Hotspot da mes telefonin» ed activar il cumutatur (deactivà da fabrica). MoveEye guarda lura mintga 30 s, sch\'il hotspot è qua, e mida sez – ord l\'agen WLAN, ord in auter WLAN (p.ex. a chasa) u sch\'i n\'ha nagina rait. El spetga uschè ditg ch\'in apparat è collià cun l\'agen WLAN, durant in alarm (cotschen, registraziun, persuna, ladernezi) e durant ina actualisaziun u sch\'ina segirezza u la homepage vegn chargiada si. Sch\'i na funcziuna betg u sch\'il hotspot n\'ha nagin internet, turna MoveEye sco fin ussa (rait da pli baud u agen WLAN) ed emprova pir suenter 2, lura 5, lura 10 minutas danovamain. Suenter la midada vegn sco adina l\'avis push cun la nova adressa (senza num dal WLAN); Tailscale sa collia sez danovamain. En l\'agen WLAN cun mo in adapter na po MoveEye betg tschertgar adina: el guarda lura maximalmain mintga 5 minutas curt (agen WLAN var 15 s deactivà, mo sche nagin è collià). Midà a maun: 10 minutas paus.</p>',
}


def _help_hsp(doc, lang):
    i = doc.find('<section id="system"')
    if i < 0 or 'id="hsp-help"' in doc:
        return doc
    j = doc.find("</section>", i)
    return doc[:j] + HELP_HSP[lang] + doc[j:] if j >= 0 else doc


_hp_en_hsp = HELP_PAGE.find('<div lang="en">')
if _hp_en_hsp > 0:
    HELP_PAGE = _help_hsp(HELP_PAGE[:_hp_en_hsp], "de") + _help_hsp(HELP_PAGE[_hp_en_hsp:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_hsp(HELP_X[_L], _L)


# ---- self-test ------------------------------------------------------------------------------------------------------------------------
def hspref_selftest():
    assert 'id="hsp-css"' in WEB_PAGE and "hspPaint(WF)" in WEB_PAGE, "page hooks"
    assert HELP_PAGE.count('id="hsp-help"') == 2, "manual"
    assert NetAuto.step is _hsp_netauto_step and "hs_prefer" in FACTORY_KEEP and "hs_prefer_ssid" in LOCK_DENY_KEYS
    keep = ({k: CFG.get(k) for k in ("hs_prefer", "hs_prefer_ssid", "lang")}, dict(HSPREF))
    try:
        CFG.update(hs_prefer=False, hs_prefer_ssid="Testhandy-7")
        assert hspref_tick(True) == "off" and hspref_text() == ""
        CFG["hs_prefer"] = True; CFG["hs_prefer_ssid"] = ""
        assert hspref_tick(True).startswith("choose a saved network")
        CFG["hs_prefer_ssid"] = "Testhandy-7"
        assert "Testhandy-7" in push_ssids()
        HSPREF.update(state=HSP_DEV1, n=1); CFG["lang"] = "de"
        assert hspref_text("de") == "📶 Hotspot «Testhandy-7»: wartet, weil 1 Gerät verbunden ist", hspref_text("de")
        for st in [k for k in _HX_HSP if k[:1].islower() and k != "the network is not saved"]:
            HSPREF.update(state=st, n=2)
            for L in ("de", "en", "fr", "it", "rm"):
                assert "{" not in hspref_text(L) and (L == "en" or hspref_text(L) != hspref_text("en")), (st, L)
    finally:
        CFG.update(keep[0]); HSPREF.update(keep[1])
    for k, v in _HX_HSP.items():
        assert len(v) == 4 and all(v) and "ß" not in "".join(v), k
    return True


SELFTEST_EXTRA.append(("Prefer my phone hotspot (639zzzzf)", hspref_selftest))
