#@ MoveEye – Teil 639zzzzp: Mitteilungen eine bestimmte Zeit pausieren (15 min · 30 min · 1 h · 2 h · bis morgen früh · bis ich zurück bin · eigene Zeit) – über die Glocke 🔔 im Kopf, auf der Seite Push-Nachrichten («Wann»), im Pi-Fenster und mit dem Knopf «🔕 1 h pausieren» in der Push-Nachricht; endet von selbst mit einer kurzen Nachricht. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Wish of Besitzer (15.11.2026, approved after the preview): a temporary push pause that ends by itself.
#   * Choices: 15 min, 30 min, 1 h, 2 h; «until tomorrow morning» (the wake-up time wake_time when the alarm clock is on, else
#     07:00, the next one); «until I am back» (ends when the presence detection (030 presence_home) says «home» after it said
#     «away» during the pause; at the latest after 24 h; without a configured presence the choice is disabled with a hint);
#     «own time» (minutes, hours or an end time, at most 24 h). A running pause can be ended or extended (+15 min, +1 h, morning).
#   * During the pause still delivered: sabotage / theft / sensor alarms (event «tamper»), the SOS lamp (info «🆘 SOS»), «battery
#     almost empty» / «battery empty», tests and the messages of the pause itself. Everything else (person, pre-alarm, warm body,
#     noise, notes) is held back - logged in the message list and recorded as always (like the quiet hours). At the end one
#     short push «🔔 Notifications on again» with «During the pause: 3 alarms (in the history)».
#   * Who: the administrator pauses for all receivers (the main channels, Pushover, e-mail, SMS, web push and the own ntfy topics
#     of the users); a user who gets alarm pushes pauses only his own ntfy topic. Logged in the protocol with the name and the way.
#   * State in the settings (push_pause, push_pause_users - not VOLATILE): survives a restart; a pause that ended while MoveEye
#     was off ends at the next start with the same short message.
#   * Push button «🔕 1 h pausieren» (066 mechanism: one key per message, 1 h valid, each button once, no PIN like «False alarm»,
#     logged as «push button»): on alarm / motion pushes. ntfy shows at most 3 buttons - the pause button takes the place of
#     «Siren» (Live · False alarm · Pause); Telegram keeps all buttons, the pause gets its own row. After the button a quiet
#     confirmation «🔕 Paused until 23:41» with the button «🔔 End pause».
#   * Web: the bell 🔔 (510) opens a small menu: «Pause notifications» + «Sound in the browser» (switch + the old panel); during
#     a pause the bell shows «🔕 43 min». Users without alarm pushes get the old sound panel only. Push page «Wann» (531a, slot
#     #pp-push): the same choices. The Live tab itself is unchanged (only the shared header).
#   * Window (571a): the same choices under «Wann», the status line of the section shows the pause.
#   * Renamed (Besitzer): «Pause zwischen Alarmen (s)» → «Abstand zwischen Alarmen (s)», also for pre-alarms (579a / 639a).
# Test: werkzeuge/push_pause_test.py, self-test push_pause_selftest.
# ----------------------------------------------------------------------------
for _k in ("push_pause", "push_pause_users"):
    CFG.setdefault(_k, {}); DEFAULTS.setdefault(_k, {})
try:
    USER_SETTINGS_DENY.update({"push_pause", "push_pause_users"})
except NameError:
    pass
VIEW_GET = VIEW_GET + ("/api/pushpause",)                # every logged-in user may ask (the answer says whether he may pause)
VIEW_POST.add("/api/pushpause")                          # the route checks the right itself (alarm pushes / administrator)

PP_DUR = {"15": 15, "30": 30, "60": 60, "120": 120}     # minutes of the quick choices
PP_MAX_S = 24 * 3600                                     # own time and «until I am back»: at most 24 h
PP_ALARM_EV = ("person", "prealarm", "warm", "noise")
PP_EXEMPT_TEXTS = ("Battery almost empty: about {pct} % ({hours:.1f} h)", "Battery almost empty: about {pct} % ({hours:.1f} h) left – please charge or swap",
                   "Battery empty – the Pi shuts down cleanly")
PP = {"lock": threading.Lock(), "started": False, "logt": {}}
_PP_TL = threading.local()

_HX_PP = {
    "Pause notifications": ("Mitteilungen pausieren", "Mettre les notifications en pause", "Mettere in pausa le notifiche", "Pausar las communicaziuns"),
    "Notifications paused": ("Mitteilungen pausiert", "Notifications en pause", "Notifiche in pausa", "Communicaziuns en pausa"),
    "Until tomorrow morning": ("Bis morgen früh", "Jusqu’à demain matin", "Fino a domattina", "Fin damaun marvegl"),
    "Until I am back": ("Bis ich zurück bin", "Jusqu’à mon retour", "Finché torno", "Fin che jau sun enavos"),
    "Own time …": ("Eigene Zeit …", "Durée libre …", "Tempo a scelta …", "Agen temp …"),
    "min · h · time": ("min · h · Uhrzeit", "min · h · heure", "min · h · ora", "min · h · ura"),
    "phone away": ("Handy weg", "téléphone absent", "telefono via", "telefonin davent"),
    "phone at home": ("Handy da", "téléphone là", "telefono qui", "telefonin qua"),
    "no presence set up": ("nicht eingerichtet", "pas configuré", "non configurato", "betg endrizzà"),
    "First enter your phone under Time & presence": ("Dafür zuerst dein Handy unter Zeit & Anwesenheit eintragen",
                                                     "D’abord inscrire ton téléphone sous Heure & présence",
                                                     "Prima inserisci il tuo telefono in Ora & presenza",
                                                     "L’emprim inscriver tes telefonin sut Temp & preschientscha"),
    "End pause": ("Pause beenden", "Terminer la pause", "Termina la pausa", "Terminar la pausa"),
    "Extend:": ("Verlängern:", "Prolonger :", "Prolunga:", "Prolungar:"),
    "until {hm}": ("bis {hm}", "jusqu’à {hm}", "fino alle {hm}", "fin las {hm}"),
    "until tomorrow {hm}": ("bis morgen {hm}", "jusqu’à demain {hm}", "fino a domani alle {hm}", "fin damaun las {hm}"),
    "{left} left": ("noch {left}", "encore {left}", "ancora {left}", "anc {left}"),
    "until you are back (at the latest {hm})": ("bis du zurück bist (spätestens {hm})", "jusqu’à ton retour (au plus tard {hm})",
                                                "finché torni (al più tardi alle {hm})", "fin che ti es enavos (il pli tard las {hm})"),
    "by {who}": ("von {who}", "par {who}", "da {who}", "da {who}"),
    "via the bell 🔔": ("über die Glocke 🔔", "avec la cloche 🔔", "con la campanella 🔔", "cun la sajetta 🔔"),
    "on the push page": ("auf der Seite Push-Nachrichten", "sur la page Messages push", "nella pagina Messaggi push", "sin la pagina Messadis push"),
    "in the Pi window": ("im Pi-Fenster", "dans la fenêtre du Pi", "nella finestra del Pi", "en la fanestra dal Pi"),
    "with the push button": ("mit dem Knopf in der Push-Nachricht", "avec le bouton du message push", "con il pulsante del messaggio push", "cun il buttun dal messadi push"),
    "push button": ("Push-Knopf", "bouton du push", "pulsante del push", "buttun dal push"),
    "1 alarm": ("1 Alarm", "1 alarme", "1 allarme", "1 alarm"),
    "{n} alarms": ("{n} Alarme", "{n} alarmes", "{n} allarmi", "{n} alarms"),
    "1 note": ("1 Hinweis", "1 note", "1 avviso", "1 indicaziun"),
    "{n} notes": ("{n} Hinweise", "{n} notes", "{n} avvisi", "{n} indicaziuns"),
    "Held back so far: {what}": ("Bisher zurückgehalten: {what}", "Retenu jusqu’ici : {what}", "Trattenuto finora: {what}", "Retegnì fin ussa: {what}"),
    "Nothing held back so far.": ("Bisher nichts zurückgehalten.", "Rien de retenu jusqu’ici.", "Finora nulla trattenuto.", "Fin ussa nagut retegnì."),
    "During the pause: {what} (in the history)": ("Während der Pause: {what} (im Verlauf)", "Pendant la pause : {what} (dans l’historique)",
                                                  "Durante la pausa: {what} (nella cronologia)", "Durant la pausa: {what} (en la cronologia)"),
    "During the pause nothing was held back.": ("Während der Pause wurde nichts zurückgehalten.", "Rien n’a été retenu pendant la pause.",
                                                "Durante la pausa non è stato trattenuto nulla.", "Durant la pausa n’è nagut vegnì retegnì."),
    "Sabotage, theft, emergency call and «battery almost empty» still come.": (
        "Sabotage, Diebstahl, Notruf und «Akku fast leer» kommen trotzdem.",
        "Sabotage, vol, appel d’urgence et « batterie presque vide » arrivent quand même.",
        "Sabotaggio, furto, chiamata d’emergenza e «batteria quasi scarica» arrivano comunque.",
        "Sabotascha, engul, clom d’urgenza e «accu prest vid» vegnan tuttina."),
    "Everything else is only recorded – at the end a short message comes.": (
        "Alles andere wird nur aufgezeichnet – am Ende kommt eine kurze Nachricht.",
        "Tout le reste est seulement enregistré – à la fin arrive un court message.",
        "Tutto il resto viene solo registrato – alla fine arriva un breve messaggio.",
        "Tut il rest vegn mo registrà – a la fin vegn in curt messadi."),
    "Ends by itself.": ("Endet von selbst.", "Se termine d’elle-même.", "Finisce da sola.", "Finescha da sasez."),
    "Also with the bell 🔔 at the top and the button in the push message.": (
        "Auch über die Glocke 🔔 oben und den Knopf in der Push-Nachricht.",
        "Aussi avec la cloche 🔔 en haut et le bouton dans le message push.",
        "Anche con la campanella 🔔 in alto e il pulsante nel messaggio push.",
        "Er cun la sajetta 🔔 sisum ed il buttun en il messadi push."),
    "Only your own push messages are paused.": ("Nur deine eigenen Push-Nachrichten werden pausiert.", "Seuls tes propres messages push sont mis en pause.",
                                                "Vengono messi in pausa solo i tuoi messaggi push.", "Mo tes agens messadis push vegnan pausads."),
    "Sound in the browser": ("Ton im Browser", "Son dans le navigateur", "Suono nel browser", "Tun en il navigatur"),
    "🔔 Alarm sound in this browser": ("🔔 Alarmton in diesem Browser", "🔔 Son d’alarme dans ce navigateur", "🔔 Suono d’allarme in questo browser", "🔔 Tun d’alarm en quest navigatur"),
    "Sound settings …": ("Ton-Einstellungen …", "Réglages du son …", "Impostazioni audio …", "Parameters dal tun …"),
    "Duration": ("Dauer", "Durée", "Durata", "Durada"),
    "Until a time": ("Bis Uhrzeit", "Jusqu’à une heure", "Fino a un’ora", "Fin ad in’ura"),
    "minutes": ("Minuten", "minutes", "minuti", "minutas"),
    "hours": ("Stunden", "heures", "ore", "uras"),
    "Pause until {hm}": ("Pausieren bis {hm}", "Pause jusqu’à {hm}", "Pausa fino alle {hm}", "Pausa fin las {hm}"),
    "‹ back": ("‹ zurück", "‹ retour", "‹ indietro", "‹ enavos"),
    "🔕 Pause 1 h": ("🔕 1 h pausieren", "🔕 Pause 1 h", "🔕 Pausa 1 h", "🔕 Pausa 1 h"),
    "🔔 End pause": ("🔔 Pause beenden", "🔔 Terminer la pause", "🔔 Termina la pausa", "🔔 Terminar la pausa"),
    "Notifications paused until {hm}": ("Mitteilungen pausiert bis {hm}", "Notifications en pause jusqu’à {hm}", "Notifiche in pausa fino alle {hm}",
                                        "Communicaziuns en pausa fin las {hm}"),
    "Notifications on again": ("Mitteilungen wieder an", "Notifications de nouveau actives", "Notifiche di nuovo attive", "Communicaziuns puspè activas"),
    "🔕 paused until {hm}": ("🔕 pausiert bis {hm}", "🔕 en pause jusqu’à {hm}", "🔕 in pausa fino alle {hm}", "🔕 en pausa fin las {hm}"),
    "Minutes, hours (e.g. 90 or 1.5 h) or an end time (e.g. 22:30)": (
        "Minuten, Stunden (z. B. 90 oder 1.5 h) oder eine Endzeit (z. B. 22:30)",
        "Minutes, heures (p. ex. 90 ou 1.5 h) ou une heure de fin (p. ex. 22:30)",
        "Minuti, ore (p. es. 90 o 1.5 h) o un’ora di fine (p. es. 22:30)",
        "Minutas, uras (p. ex. 90 u 1.5 h) u in’ura da la fin (p. ex. 22:30)"),
    "Enter minutes, hours or a time (HH:MM).": ("Minuten, Stunden oder eine Uhrzeit (HH:MM) eingeben.", "Saisis des minutes, des heures ou une heure (HH:MM).",
                                                "Inserisci minuti, ore o un’ora (HH:MM).", "Endatescha minutas, uras u in’ura (HH:MM)."),
    "At most 24 hours.": ("Höchstens 24 Stunden.", "24 heures au maximum.", "Al massimo 24 ore.", "Maximalmain 24 uras."),
    "The presence detection is not set up.": ("Die Anwesenheit ist nicht eingerichtet.", "La détection de présence n’est pas configurée.",
                                              "Il rilevamento di presenza non è configurato.", "La constataziun da preschientscha n’è betg endrizzada."),
    "Only who gets alarm pushes may pause them.": ("Pausieren darf nur, wer Alarm-Pushes bekommt.", "Seul qui reçoit les push d’alarme peut les mettre en pause.",
                                                   "Solo chi riceve i push d’allarme può metterli in pausa.", "Mo tgi che survegn ils push d’alarm po als pausar."),
    "Notifications paused, {left} left – menu": ("Mitteilungen pausiert, noch {left} – Menü", "Notifications en pause, encore {left} – menu",
                                                 "Notifiche in pausa, ancora {left} – menu", "Communicaziuns en pausa, anc {left} – menu"),
    "1 minute": ("1 Minute", "1 minute", "1 minuto", "1 minuta"),
    "{n} minutes": ("{n} Minuten", "{n} minutes", "{n} minuti", "{n} minutas"),
    "1 hour": ("1 Stunde", "1 heure", "1 ora", "1 ura"),
    "{n} hours": ("{n} Stunden", "{n} heures", "{n} ore", "{n} uras"),
    "No pause is running.": ("Es läuft keine Pause.", "Aucune pause en cours.", "Nessuna pausa in corso.", "I na va nagina pausa."),
    "running": ("läuft", "en cours", "in corso", "en funcziun"),
    "off": ("aus", "désactivé", "spento", "deactivà"),
}
for _k, _v in _HX_PP.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
# the titles of the two messages of the pause (635b: symbol + short title, translated when sent)
PK_TITLES.setdefault("Notifications paused", ("🔕", "Notifications paused", "info", False))
PK_TITLES.setdefault("Notifications on again", ("🔔", "Notifications on again", "info", False))


# ---- state ----------------------------------------------------------------------------------------------------------------
def _pp_clean(s):
    """a stored pause (dict) or None - checked like everything that comes from the settings file"""
    if not isinstance(s, dict):
        return None
    try:
        until, t0 = float(s.get("until") or 0), float(s.get("t0") or 0)
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(until) and math.isfinite(t0)) or until <= 0 or until - t0 > PP_MAX_S + 3600:
        return None
    mode = s.get("mode") if s.get("mode") in ("min", "morning", "home") else "min"
    via = s.get("via") if s.get("via") in ("bell", "page", "window", "push") else "page"
    return {"until": until, "t0": t0, "mode": mode, "via": via, "by": str(s.get("by") or "")[:40],
            "held": max(0, int(s.get("held") or 0)), "held_info": max(0, int(s.get("held_info") or 0)), "away": bool(s.get("away"))}


def pp_raw(scope=""):
    """the stored pause of the administrator (scope «») or of one user (scope = his name), also when it has run out"""
    if not scope:
        return _pp_clean(CFG.get("push_pause"))
    allu = CFG.get("push_pause_users") if isinstance(CFG.get("push_pause_users"), dict) else {}
    return _pp_clean(allu.get(scope))


def pp_active(scope="", now=None):
    s = pp_raw(scope)
    return s if s and (time.time() if now is None else now) < s["until"] else None


def _pp_put(scope, s, save=True):
    with PP["lock"]:
        if not scope:
            CFG["push_pause"] = dict(s) if s else {}
        else:
            allu = dict(CFG.get("push_pause_users") if isinstance(CFG.get("push_pause_users"), dict) else {})
            if s:
                allu[scope] = dict(s)
            else:
                allu.pop(scope, None)
            CFG["push_pause_users"] = allu
    if save:
        save_settings()


def pp_presence_ready():
    return bool(CFG.get("presence_hosts") or CFG.get("presence_macs") or CFG.get("presence_bt"))


def pp_presence():
    """True home / False away / None unknown (030)"""
    try:
        return presence_home() if pp_presence_ready() else None
    except Exception:
        return None


def pp_morning_ts(now=None):
    """the next wake-up time (wake_time while the alarm clock is on, else 07:00)"""
    now = time.time() if now is None else now
    hm = str(CFG.get("wake_time") or "07:00") if CFG.get("wake_on") else "07:00"
    m = re.match(r"^([01]?\d|2[0-3]):([0-5]\d)$", hm.strip())
    h, mi = (int(m.group(1)), int(m.group(2))) if m else (7, 0)
    d = datetime.fromtimestamp(now)
    t = d.replace(hour=h, minute=mi, second=0, microsecond=0)
    if t.timestamp() <= now + 60:
        t = t + timedelta(days=1)
    return t.timestamp()


def pp_morning_hm():
    return datetime.fromtimestamp(pp_morning_ts()).strftime("%H:%M")


def pp_parse(text, now=None):
    """«Eigene Zeit»: «45», «45 min», «1.5 h», «1:30 h», «22:30» (an end time, the next one) -> (end, "") or (0, error)"""
    now = time.time() if now is None else now
    v = str(text or "").strip().lower().replace(",", ".")
    m = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", v)
    if m:
        d = datetime.fromtimestamp(now)
        t = d.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
        if t.timestamp() <= now:
            t = t + timedelta(days=1)
        return t.timestamp(), ""
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(m|min|mins|minuten|minutes|minuti|minutas|h|std|stunden|hours|heures|ore|uras)?", v)
    m2 = re.fullmatch(r"(\d+):([0-5]\d)\s*h", v)
    if m2:
        sec = int(m2.group(1)) * 3600 + int(m2.group(2)) * 60
    elif m:
        n = float(m.group(1))
        sec = n * 3600 if (m.group(2) or "") in ("h", "std", "stunden", "hours", "heures", "ore", "uras") else n * 60
    else:
        return 0, "Enter minutes, hours or a time (HH:MM)."
    if sec < 60:
        return 0, "Enter minutes, hours or a time (HH:MM)."
    if sec > PP_MAX_S:
        return 0, "At most 24 hours."
    return now + sec, ""


def _pp_log(msg):
    try:
        log_event("sys", msg)
    except Exception:
        pass


def pp_who(who, scope=""):
    return str(scope or who or "admin")[:40]


def pp_start(scope, mode, who="admin", via="page", value=None, now=None, save=True):
    """start (or replace) a pause. mode: "15" "30" "60" "120" | "morning" | "home" | "own" (value = text of pp_parse) ->
    (ok, error, state)"""
    now = time.time() if now is None else now
    m_ = "min"
    if str(mode) in PP_DUR:
        until = now + PP_DUR[str(mode)] * 60
    elif mode == "morning":
        until, m_ = pp_morning_ts(now), "morning"
    elif mode == "home":
        if not pp_presence_ready():
            return False, "The presence detection is not set up.", None
        until, m_ = now + PP_MAX_S, "home"
    elif mode == "own":
        until, err = pp_parse(value, now)
        if err:
            return False, err, None
    else:
        return False, "unknown", None
    old = pp_active(scope, now)
    s = {"until": until, "t0": old["t0"] if old else now, "mode": m_, "via": via, "by": pp_who(who, scope),
         "held": old["held"] if old else 0, "held_info": old["held_info"] if old else 0, "away": pp_presence() is False}
    _pp_put(scope, s, save)
    _pp_log(f"Push messages paused until {datetime.fromtimestamp(until).strftime('%d.%m. %H:%M')} ({mode}) by {pp_who(who)} ({via})"
            + (f" - only the own pushes of «{scope}»" if scope else " - for all receivers"))
    pp_thread()
    return True, "", s


def pp_extend(scope, add_min=0, morning=False, who="admin", via="page", save=True):
    s = pp_active(scope)
    if not s:
        return False, "No pause is running.", None
    if morning:
        s["until"], s["mode"] = max(s["until"], pp_morning_ts()), "morning"
    else:
        s["until"] = min(s["until"] + max(1, int(add_min)) * 60, time.time() + PP_MAX_S)
        if s["mode"] == "home":
            s["mode"] = "min"
    _pp_put(scope, s, save)
    _pp_log(f"Push pause extended until {datetime.fromtimestamp(s['until']).strftime('%d.%m. %H:%M')} by {pp_who(who)} ({via})"
            + (f" - «{scope}»" if scope else ""))
    return True, "", s


def pp_what(held, held_info, lang=None):
    parts = []
    if held:
        parts.append(tr("1 alarm", lang) if held == 1 else trf("{n} alarms", lang, n=held))
    if held_info:
        parts.append(tr("1 note", lang) if held_info == 1 else trf("{n} notes", lang, n=held_info))
    return " · ".join(parts)


def pp_end(scope, reason="ended", who="admin", via="page", push=True, save=True):
    """end a pause (by hand, run out, back home); the short message «on again» with the count"""
    s = pp_raw(scope)
    if not s:
        return False, "No pause is running."
    _pp_put(scope, None, save)
    _pp_log(f"Push messages on again ({reason}" + (f", {pp_who(who)}, {via}" if reason == "ended" else "") + f") - held back: {s['held']} alarms, "
            f"{s['held_info']} notes" + (f" - «{scope}»" if scope else ""))
    if push:
        pp_end_push(scope, s)
    return True, ""


# ---- what still comes, what is held back -----------------------------------------------------------------------------------
def pp_exempt(p):
    """sabotage / theft / sensor alarms (tamper), the SOS lamp, battery almost empty / empty, tests and the messages of the pause"""
    if not isinstance(p, dict):
        return True
    ev = p.get("event")
    if ev in ("tamper", "test") or p.get("pp_pass") or p.get("_test") or p.get("fs_tok"):
        return True
    if ev == "info":
        tt = str(p.get("info_title") or "")
        if "🆘" in tt or "SOS" in tt:
            return True
        tx = str(p.get("text") or "")
        for k in PP_EXEMPT_TEXTS:
            for L in (None, "en"):
                pre = tr(k, L).split("{")[0].strip()[:18]
                if pre and tx.startswith(pre):
                    return True
    return False


def _pp_count(scope, ev):
    with PP["lock"]:
        if not scope:
            s = CFG.get("push_pause") if isinstance(CFG.get("push_pause"), dict) else None
        else:
            s = (CFG.get("push_pause_users") or {}).get(scope)
        if isinstance(s, dict):
            k = "held" if ev in PP_ALARM_EV else "held_info"
            s[k] = int(s.get(k) or 0) + 1
    t = time.time()
    if t - PP["logt"].get(scope, 0) > 30:               # the settings file at most every 30 s (the count is also in memory)
        PP["logt"][scope] = t
        try:
            save_settings()
        except Exception:
            pass


_pp_dispatch_before = Notifier._dispatch


def _pp_dispatch(self, p, jpg, fname):
    """+ 639zzzzp: a running pause of the administrator holds everything back that is not exempt"""
    ex = pp_exempt(p)
    if not ex and pp_active(""):
        ev = self._event(p)
        _pp_count("", ev)
        STATE["notify_status"] = "paused (push pause)"
        try:
            msglog_add(self._title(p), push_with_map(self._text(p), p, " · "), ev, jpg, "none", "🔕 Pause")
        except Exception:
            pass
        _pp_log(f"No push message (push pause): {ev}")
        return None
    _PP_TL.exempt = ex
    try:
        return _pp_dispatch_before(self, p, jpg, fname)
    finally:
        _PP_TL.exempt = False


# wraps: Notifier._dispatch
Notifier._dispatch = _pp_dispatch

_pp_users_dispatch_before = users_push_dispatch


# wraps: users_push_dispatch
def users_push_dispatch(title, text, cat, click=""):
    """+ 639zzzzp: inside, users_push_wants knows that it is about sending (a paused user gets nothing that is not exempt)"""
    _PP_TL.users = True
    try:
        return _pp_users_dispatch_before(title, text, cat, click)
    finally:
        _PP_TL.users = False


_pp_users_wants_before = users_push_wants


# wraps: users_push_wants
def users_push_wants(name, cat):
    ok = _pp_users_wants_before(name, cat)
    if ok and getattr(_PP_TL, "users", False) and cat != "test" and not getattr(_PP_TL, "exempt", False) and pp_active(str(name or "")):
        _pp_count(str(name), "person" if cat == "alarm" else "info")
        return False
    return ok


# ---- the messages of the pause ------------------------------------------------------------------------------------------------
def _pp_notifier():
    try:
        w = WATCH_REF.get("w")
        n = getattr(w, "notifier", None) if w is not None else None
        return n if n is not None and n.configured() and CFG.get("notify_on") else None
    except Exception:
        return None


def _pp_send_info(title, text, link="", acts=None):
    n = _pp_notifier()
    if n is None:
        return False
    p = {"event": "info", "persons": 0, "time": datetime.now().isoformat(timespec="seconds"), "text": text, "info_title": "{name}: " + title,   # title: a key of PK_TITLES
         "snapshot": None, "rain": False, "wind": "", "source": STATE.get("source_label", ""), "link": link, "pp_pass": True}
    if acts:
        p["alx_acts"] = tuple(acts)
    threading.Thread(target=n._dispatch, args=(p, None, ""), daemon=True, name="push-pause").start()
    return True


def pp_end_push(scope, s):
    what = pp_what(s["held"], s["held_info"])
    text = trf("During the pause: {what} (in the history)", what=what) if what else tr("During the pause nothing was held back.")
    base = alx_base()
    link = base + "/recordings" if base else ""
    if not scope:
        return _pp_send_info("Notifications on again", text, link)
    title = "🔔 " + tr("Notifications on again")
    u = user_get(scope)
    if u and u.get("ntfy"):
        threading.Thread(target=_users_ntfy_send, args=(u["name"], _users_ntfy_url(u["ntfy"]), title, text, "info", link),
                         daemon=True, name="push-pause-user").start()
        return True
    return False


def pp_confirm_push(s):
    """after the button «🔕 1 h pausieren»: a quiet message with the button «🔔 End pause»"""
    hm = datetime.fromtimestamp(s["until"]).strftime("%H:%M")
    return _pp_send_info("Notifications paused", trf("until {hm}", hm=hm).capitalize() + ". "
                         + tr("Sabotage, theft, emergency call and «battery almost empty» still come."), "", ("resume",))


# ---- the clock: run out, back home, ended while MoveEye was off --------------------------------------------------------------
def pp_tick(now=None):
    now = time.time() if now is None else now
    scopes = [""] + [k for k in (CFG.get("push_pause_users") or {}) if isinstance(k, str)]
    for sc in scopes:
        s = pp_raw(sc)
        if s is None:
            if sc and sc in (CFG.get("push_pause_users") or {}):
                _pp_put(sc, None)
            elif not sc and CFG.get("push_pause"):
                _pp_put("", None)
            continue
        if s["mode"] == "home":
            h = pp_presence()
            if h is False and not s["away"]:
                s["away"] = True; _pp_put(sc, s)
            elif h is True and s["away"]:
                pp_end(sc, "back home")
                continue
        if now >= s["until"]:
            pp_end(sc, "time is up")


def pp_thread():
    if PP["started"]:
        return
    PP["started"] = True

    def loop():
        while True:
            try:
                pp_tick()
            except Exception as e:
                _pp_log(f"Push pause: {e}"[:150])
            time.sleep(5.0)
    threading.Thread(target=loop, daemon=True, name="push-pause").start()


# ---- what the pages and the window show --------------------------------------------------------------------------------------
def pp_left_text(sec, short=False):
    mins = max(1, (max(0, int(sec)) + 59) // 60)
    if mins < 60:
        return "%d min" % mins
    h, m = divmod(mins, 60)
    return ("%d h %02d" % (h, m)) if short else ("%d h %d min" % (h, m) if m else "%d h" % h)


def pp_badge(sec, mode):
    """the small badge on the bell 🔕 (the button stays 44 px): «43′», «1h», «7h», «☾» until tomorrow morning"""
    if mode == "morning":
        return "☾"
    mins = max(1, (max(0, int(sec)) + 59) // 60)
    return "%d′" % mins if mins < 60 else "%dh" % (mins // 60)


def pp_left_long(sec, lang=None):
    """«43 Minuten», «7 Stunden 49 Minuten» (for the screen reader)"""
    mins = max(1, (max(0, int(sec)) + 59) // 60)
    h, m = divmod(mins, 60)
    hs = (tr("1 hour", lang) if h == 1 else trf("{n} hours", lang, n=h)) if h else ""
    ms = (tr("1 minute", lang) if m == 1 else trf("{n} minutes", lang, n=m)) if m else ""
    return (hs + " " + ms).strip()


def pp_info(scope="", lang=None, can=True):
    """everything the bell menu, the push page and the window need"""
    L = cur_lang(lang)
    now = time.time()
    s = pp_active(scope, now)
    pres = pp_presence()
    out = {"can": bool(can), "scope": "user" if scope else "all", "on": bool(s), "morning": pp_morning_hm(),
           "presence": {"ready": pp_presence_ready(), "home": pres,
                        "text": tr("no presence set up", L) if not pp_presence_ready() else tr("phone at home", L) if pres else tr("phone away", L) if pres is False else ""}}
    if s:
        hm = datetime.fromtimestamp(s["until"]).strftime("%H:%M")
        tomorrow = datetime.fromtimestamp(s["until"]).date() != datetime.fromtimestamp(now).date()
        left = s["until"] - now
        if s["mode"] == "home":
            until = trf("until you are back (at the latest {hm})", L, hm=hm)
        else:
            until = trf("until tomorrow {hm}", L, hm=hm) if tomorrow else trf("until {hm}", L, hm=hm)
        via = {"bell": "via the bell 🔔", "page": "on the push page", "window": "in the Pi window", "push": "with the push button"}[s["via"]]
        who = tr("push button", L) if s["by"] == "push button" else s["by"]
        what = pp_what(s["held"], s["held_info"], L)
        out.update(until=s["until"], left=int(left), hm=hm, mode=s["mode"], short=pp_left_text(left, True), badge=pp_badge(left, s["mode"]),
                   aria=trf("Notifications paused, {left} left – menu", L, left=pp_left_long(left, L)),
                   line=until + " · " + trf("{left} left", L, left=pp_left_text(left)),
                   by=trf("by {who}", L, who=who) + " · " + tr(via, L), held=s["held"], held_info=s["held_info"],
                   held_line=trf("Held back so far: {what}", L, what=what) if what else tr("Nothing held back so far.", L))
    return out


def pp_tx(lang=None):
    L = cur_lang(lang)
    keys = list(_HX_PP) + ["Sabotage, theft, emergency call and «battery almost empty» still come."]
    return {k: (EN_SHOW.get(k, k) if L == "en" else tr(k, L)) for k in keys}


_pp_status_line_before = push_status_line


# wraps: push_status_line
def push_status_line(lang=None, ch=None, te=None):
    out = _pp_status_line_before(lang, ch, te)
    s = pp_active("")
    if s and CFG.get("notify_on"):
        out += " · " + trf("🔕 paused until {hm}", lang, hm=datetime.fromtimestamp(s["until"]).strftime("%H:%M"))
    return out


_pp_push_info_before = push_info


# wraps: push_info
def push_info(lang=None):
    d = _pp_push_info_before(lang)
    d["pause"] = pp_info("", lang)
    return d


# ---- push button «🔕 1 h pausieren» (066) --------------------------------------------------------------------------------------
ALX_ACTS = tuple(ALX_ACTS) + ("pause", "resume")
ALX_NAMES.update({"pause": "🔕 Pause 1 h", "resume": "🔔 End pause"})
_pp_alx_token_before = alx_token


# wraps: alx_token
def alx_token(p):
    """+ 639zzzzp: alarm / motion messages get the pause button too (the key knows it: a key of another message does not)"""
    if isinstance(p, dict) and not p.get("alx_acts") and p.get("event") in PP_ALARM_EV:
        return _pp_alx_token_before(dict(p, alx_acts=("fa", "siren", "off", "pause")))
    return _pp_alx_token_before(p)


_pp_alx_buttons_before = alx_buttons


# wraps: alx_buttons
def alx_buttons(p, lang=None):
    """the pause / resume buttons are placed by the outer wrappers below (ntfy: instead of «Siren»; Telegram: an own row)"""
    b = _pp_alx_buttons_before(p, lang)
    if getattr(_PP_TL, "hide", False):
        return [x for x in b if not x[1].endswith(("/pause", "/resume"))]
    return b


def _pp_extra(p):
    try:
        return [x for x in _pp_alx_buttons_before(p) if x[1].endswith(("/pause", "/resume"))]
    except Exception:
        return []


_pp_ntfy_before = alx_ntfy_actions


# wraps: alx_ntfy_actions (after 639zzzzb)
def alx_ntfy_actions(p):
    _PP_TL.hide = True
    try:
        acts = _pp_ntfy_before(p)
    finally:
        _PP_TL.hide = False
    ex = _pp_extra(p) if isinstance(p, dict) and not p.get("fs_tok") else []
    if not ex:
        return acts
    lst = [a.strip() for a in str(acts or "").split(";") if a.strip()]
    def url_of(a):
        x = a.split(",")
        return x[2].strip() if len(x) > 2 else ""
    for lab, url, _c in ex:
        if url.endswith("/pause"):                       # ntfy: at most 3 buttons - the pause takes the place of «Siren»
            lst = [a for a in lst if not url_of(a).endswith("/siren")]
        lst.append(f"http, {' '.join(lab.replace(',', ' ').replace(';', ' ').split())}, {url}, method=POST, clear=true")
    if len(lst) > 3:
        lst = [a for a in lst if not url_of(a).endswith("/off")]
        lst = lst[:2] + lst[-1:] if len(lst) > 3 else lst
    return "; ".join(lst)


_pp_tg_before = alx_telegram_markup


# wraps: alx_telegram_markup (after 639zzzzb)
def alx_telegram_markup(p):
    _PP_TL.hide = True
    try:
        mk = _pp_tg_before(p)
    finally:
        _PP_TL.hide = False
    ex = _pp_extra(p) if isinstance(p, dict) and not p.get("fs_tok") else []
    if not ex:
        return mk
    rows = list((mk or {}).get("inline_keyboard") or []) + [[{"text": lab, "url": url}] for lab, url, _c in ex]
    return {"inline_keyboard": rows}


_pp_alx_do_before = alx_do


# wraps: alx_do
def alx_do(act, e, who="push"):
    if act == "pause":
        ok, err, s = pp_start("", "60", who="push button", via="push")
        if not ok:
            return False, tr_err(err)
        pp_confirm_push(s)
        return True, "🔕 " + trf("Notifications paused until {hm}", hm=datetime.fromtimestamp(s["until"]).strftime("%H:%M"))
    if act == "resume":
        if not pp_active(""):
            return True, tr("No pause is running.")
        pp_end("", "ended", who="push button", via="push")
        return True, "🔔 " + tr("Notifications on again")
    return _pp_alx_do_before(act, e, who)


# ---- web: /api/pushpause --------------------------------------------------------------------------------------------------------
def pp_scope_of(role, user):
    """(may pause, scope): the administrator = all receivers; a user who gets alarm pushes = his own pushes"""
    if role == "admin":
        return True, ""
    n = str(user or "")
    try:
        u = user_get(n)
        n = u["name"] if u else n
        return bool(u and _pp_users_wants_before(n, "alarm")), n
    except Exception:
        return False, n


def pp_api(d, role, user, method="POST"):
    """GET / POST of /api/pushpause (also used by the test); -> (answer, http code)"""
    lang = norm_lang((d or {}).get("lang"))
    can, scope = pp_scope_of(role, user)
    if method == "GET":
        out = pp_info(scope, lang, can)
        if (d or {}).get("tx"):
            out["tx"] = pp_tx(lang)
        return out, 200
    if not can:
        return {"ok": False, "error": tr("Only who gets alarm pushes may pause them.", lang)}, 403
    a = str(d.get("action") or "")
    via = d.get("via") if d.get("via") in ("bell", "page", "window") else "page"
    who = "admin" if role == "admin" else scope
    if a == "pause":
        ok, err, _s = pp_start(scope, str(d.get("mode") or ""), who=who, via=via, value=d.get("value"))
    elif a == "extend":
        ok, err, _s = pp_extend(scope, add_min=int(d.get("min") or 0) if str(d.get("min") or "0").isdigit() else 0,
                                morning=d.get("mode") == "morning", who=who, via=via)
    elif a == "end":
        ok, err = pp_end(scope, "ended", who=who, via=via)
    else:
        ok, err = False, "unknown action"
    if not ok:
        return {"ok": False, "error": tr_err(err, lang) if err not in _HX_PP else tr(err, lang)}, 400
    return dict(pp_info(scope, lang, can), ok=True), 200


_pp_sx_routes_before = sx_routes


def sx_routes(app, watch, reply, body):                    # + /api/pushpause (called once by 550)
    _pp_sx_routes_before(app, watch, reply, body)
    from flask import request, g as g_
    pp_thread()

    @app.route("/api/pushpause", methods=["GET", "POST"])
    def api_pushpause():
        role, user = getattr(g_, "role", "admin"), getattr(g_, "user", "")
        if request.method == "GET":
            out, code = pp_api({"lang": request.args.get("lang"), "tx": request.args.get("tx")}, role, user, "GET")
        else:
            out, code = pp_api(body(), role, user, "POST")
        return reply(out, code)


# ---- web: the bell menu and the block on the push page (one script on every page with the bell, 510 ALERT_JS) -----------------
PP_JS = r"""
// ---- 639zzzzp: the bell 🔔 = a small menu «Pause notifications» + «Sound in the browser»; the pause in the header ----
(function () {
  const btn = document.getElementById("btn-sound"); if (!btn || btn.dataset.ppOn) return; btn.dataset.ppOn = "1";
  const st = document.createElement("style");
  st.textContent = `
.pp-pop{position:fixed;top:58px;right:12px;z-index:85;width:310px;max-width:calc(100vw - 24px);padding:12px 14px;max-height:calc(100vh - 70px);overflow:auto;box-sizing:border-box}
body.hdrhidden .pp-pop{top:44px}
.pp-h{font-size:11px;letter-spacing:.09em;color:var(--mut);font-weight:700;text-transform:uppercase;margin:2px 0 8px}
.pp-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
.pp-grid button,.pp-wide button{padding:9px 4px;font-size:14px;border-radius:10px;min-height:40px}
.pp-wide{display:flex;flex-direction:column;gap:6px;margin-top:6px}
.pp-wide button{text-align:left;padding:9px 12px;display:flex;justify-content:space-between;align-items:center;gap:8px}
.pp-wide button span{white-space:nowrap}.pp-wide button small{color:var(--mut);font-size:12px;font-weight:400;white-space:nowrap}
.pp-wide button[disabled]{opacity:.5}
.pp-note{font-size:12px;color:var(--mut);margin-top:8px;line-height:1.4}.pp-note a{color:var(--acc2);text-decoration:none}
.pp-sep{border-top:1px solid var(--line);margin:12px -14px 10px}
.pp-link{display:flex;justify-content:space-between;align-items:center;color:var(--acc2);font-size:14px;padding:6px 0 0;cursor:pointer;background:none;border:0;width:100%;font:inherit}
.pp-row{display:flex;justify-content:space-between;align-items:center;margin:4px 0}
.pp-on{background:rgba(224,165,38,.12);border:1px solid rgba(224,165,38,.45);border-radius:12px;padding:10px 12px;margin-bottom:6px}
.pp-on b{color:var(--yel);font-size:15px}.pp-on .pp-sub{font-size:13px;color:var(--txt);margin-top:3px}
.pp-on .pp-sub2{font-size:12px;color:var(--mut);margin-top:2px}
.pp-end{width:100%;margin-top:10px;padding:10px;border-radius:10px;font-size:15px;font-weight:600;background:var(--acc);color:#fff;border:0;cursor:pointer}
.pp-ext{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;align-items:center}
.pp-ext span{font-size:12px;color:var(--mut);flex-basis:100%}.pp-ext button{flex:1;padding:7px 6px;font-size:13px;border-radius:9px}
.pp-own{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:6px}
.pp-own .seg{grid-column:1/-1;display:flex;border:1px solid var(--line);border-radius:10px;overflow:hidden}
.pp-own .seg button{flex:1;border:0;border-radius:0;padding:8px;font-size:13px}.pp-own .seg button.on{background:var(--acc);color:#fff}
.pp-own input,.pp-own select{width:100%;box-sizing:border-box;padding:9px;border-radius:10px;font-size:15px;background:var(--field);color:var(--txt);border:1px solid var(--line)}
.pp-own .go{grid-column:1/-1;padding:10px;border-radius:10px;background:var(--acc);color:#fff;border:0;font-size:15px;font-weight:600;cursor:pointer}
.pp-own .wide{grid-column:1/-1}.pp-err{grid-column:1/-1;color:var(--red);font-size:12px}
#btn-sound[data-pp]{position:relative;color:var(--yel)!important;border-color:rgba(224,165,38,.6)!important;background:rgba(224,165,38,.14)!important}
#btn-sound[data-pp]>svg{display:none}#btn-sound .pp-left{display:contents}
#btn-sound .pp-left svg{width:22px;height:22px}
#btn-sound .pp-badge{position:absolute;right:-3px;bottom:-3px;min-width:15px;height:15px;padding:0 3px;box-sizing:border-box;border-radius:8px;
  background:var(--yel);color:#111;font:700 10px/15px system-ui,sans-serif;text-align:center;pointer-events:none;white-space:nowrap}
.pp-box{border:1px solid var(--line);border-radius:12px;padding:12px;margin:6px 0 12px;background:var(--panel2)}
.pp-box .pp-t{display:flex;justify-content:space-between;align-items:center;font-weight:600;margin-bottom:8px}
.pp-box .pp-t small{color:var(--mut);font-weight:400;font-size:13px}`;
  document.head.appendChild(st);
  const L = () => (typeof LANG !== "undefined" && LANG) || "de";
  let P = null, TX = {}, pop = null, view = "", unit = "min";
  const t = s => TX[s] || s;
  const E = (tag, c, x) => { const e = document.createElement(tag); if (c) e.className = c; if (x != null) e.textContent = x; return e; };
  const B = (x, cls) => { const b = E("button", "sec" + (cls ? " " + cls : ""), x); b.type = "button"; return b; };
  const SLASH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20.5a2 2 0 0 0 4 0"/><path d="M3 3l18 18"/></svg>';
  const say = m => { try { toast(m); } catch (e) {} };
  async function load(tx) {
    try { const r = await fetch("/api/pushpause?lang=" + L() + (tx ? "&tx=1" : ""), {cache: "no-store"}); if (!r.ok) return null;
      const d = await r.json(); if (d.tx) TX = d.tx; P = d; paintAll(); return d; } catch (e) { return null; } }
  async function act(d, via) {
    try { const r = await fetch("/api/pushpause", {method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify(Object.assign({lang: L(), via: via}, d))});
      const j = await r.json(); if (!j || j.ok === false) { say("⚠ " + ((j && j.error) || "error")); return j; }
      P = j; view = ""; paintAll(); return j; } catch (e) { say("⚠ error"); return null; } }
  function choices(box, via) {
    const g = E("div", "pp-grid");
    [["15", "15 min"], ["30", "30 min"], ["60", "1 h"], ["120", "2 h"]].forEach(([m, x]) => { const b = B(x); b.onclick = () => act({action: "pause", mode: m}, via); g.appendChild(b); });
    box.appendChild(g);
    const w = E("div", "pp-wide");
    const mo = B(""); mo.append(E("span", "", "🌅 " + t("Until tomorrow morning")), E("small", "", P.morning)); mo.onclick = () => act({action: "pause", mode: "morning"}, via); w.appendChild(mo);
    const ho = B(""); ho.append(E("span", "", "🏠 " + t("Until I am back")), E("small", "", (P.presence.ready ? "📱 " : "") + (P.presence.text || "")));
    ho.disabled = !P.presence.ready; ho.onclick = () => act({action: "pause", mode: "home"}, via); w.appendChild(ho);
    if (!P.presence.ready) { const n = E("div", "pp-note"); n.style.marginTop = "0";
      if (P.scope === "all") { const a = E("a", "", t("First enter your phone under Time & presence") + " ›"); a.href = "/settings?setting=presence_hosts"; n.appendChild(a); }
      else n.textContent = t("The presence detection is not set up."); w.appendChild(n); }
    if (via !== "page") { const ow = B(""); ow.append(E("span", "", "⏱ " + t("Own time …")), E("small", "", t("min · h · time")));
      ow.onclick = () => { view = "own"; paintAll(); }; w.appendChild(ow); }
    box.appendChild(w);
  }
  function ownView(box, via) {
    const o = E("div", "pp-own");
    const sg = E("div", "seg"), s1 = B(t("Duration")), s2 = B(t("Until a time"));
    s1.classList.toggle("on", unit !== "at"); s2.classList.toggle("on", unit === "at");
    s1.onclick = () => { unit = "min"; paintAll(); }; s2.onclick = () => { unit = "at"; paintAll(); };
    sg.append(s1, s2); o.appendChild(sg);
    const er = E("div", "pp-err");
    let val;
    if (unit === "at") { const i = E("input"); i.type = "time"; i.value = P.morning; i.className = "wide"; o.appendChild(i); val = () => i.value; }
    else { const n = E("input"); n.type = "number"; n.min = "1"; n.max = "1440"; n.value = "45"; n.inputMode = "numeric";
      const u = E("select"); [["min", t("minutes")], ["h", t("hours")]].forEach(([v, x]) => { const q = E("option", "", x); q.value = v; u.appendChild(q); });
      o.append(n, u); val = () => (n.value || "") + " " + u.value; }
    const go = E("button", "go", "🔕 " + t("Pause notifications")); go.type = "button";
    go.onclick = async () => { const j = await act({action: "pause", mode: "own", value: val()}, via); if (j && j.ok === false) er.textContent = j.error || ""; };
    const back = B(t("‹ back")); back.classList.add("wide"); back.onclick = () => { view = ""; paintAll(); };
    o.append(go, er, back); box.appendChild(o);
  }
  function running(box, via) {
    const on = E("div", "pp-on");
    on.append(E("b", "", "🔕 " + t("Notifications paused")), E("div", "pp-sub", P.line), E("div", "pp-sub2", P.by), E("div", "pp-sub2", P.held_line));
    const end = E("button", "pp-end", "🔔 " + t("End pause")); end.type = "button"; end.onclick = () => act({action: "end"}, via); on.appendChild(end);
    const ex = E("div", "pp-ext"); ex.appendChild(E("span", "", t("Extend:")));
    [["+15 min", {min: 15}], ["+1 h", {min: 60}], ["🌅 " + P.morning, {mode: "morning"}]].forEach(([x, d]) => { const b = B(x); b.onclick = () => act(Object.assign({action: "extend"}, d), via); ex.appendChild(b); });
    on.appendChild(ex); box.appendChild(on);
  }
  function body(box, via) {
    if (P.on) running(box, via); else if (view === "own" && via !== "page") ownView(box, via); else choices(box, via);
    if (!P.on && view !== "own") box.appendChild(E("div", "pp-note", t("Sabotage, theft, emergency call and «battery almost empty» still come.") + " "
      + t("Everything else is only recorded – at the end a short message comes.") + (P.scope === "user" ? " " + t("Only your own push messages are paused.") : "")));
  }
  function close() { if (pop) { pop.remove(); pop = null; view = ""; } }
  function open() {
    if (pop) { pop.remove(); pop = null; } if (!P) return;           // a repaint keeps the view («own time»)
    pop = E("div", "pp-pop card");
    pop.appendChild(E("div", "pp-h", t("Pause notifications"))); body(pop, "bell");
    pop.appendChild(E("div", "pp-sep")); pop.appendChild(E("div", "pp-h", t("Sound in the browser")));
    if (window.mwSoundSet) { const r = E("label", "row pp-row"); const cb = E("input"); cb.type = "checkbox"; cb.className = "sw"; cb.checked = !!(window.mwSoundOn && mwSoundOn());
      cb.onchange = () => mwSoundSet(cb.checked); r.append(E("span", "", t("🔔 Alarm sound in this browser")), cb); pop.appendChild(r); }
    const l = E("button", "pp-link"); l.type = "button"; l.append(E("span", "", t("Sound settings …")), E("span", "", "›"));
    l.onclick = () => { close(); if (window.mwSoundPanel) mwSoundPanel(); }; pop.appendChild(l);
    pop.addEventListener("pointerdown", e => e.stopPropagation());
    document.body.appendChild(pop);
  }
  let aria0 = null;                                    // the label of the bell without a pause (510 / 578)
  function headPaint() {                               // the pause on the bell itself: 🔕 in the same 44 px button + a small badge
    const on = !!(P && P.can && P.on);
    const has = btn.querySelector(".pp-left");
    if (!on) { if (btn.dataset.pp !== undefined) { delete btn.dataset.pp; if (aria0 != null) btn.setAttribute("aria-label", aria0); } if (has) has.remove(); return; }
    if (btn.dataset.pp === undefined) aria0 = btn.getAttribute("aria-label");
    btn.dataset.pp = "1";
    const tl = "🔕 " + t("Notifications paused") + " · " + (P.line || "");
    if (btn.title !== tl) btn.title = tl;
    if (P.aria && btn.getAttribute("aria-label") !== P.aria) btn.setAttribute("aria-label", P.aria);
    if (has) { const b = has.querySelector(".pp-badge"); if (b && b.textContent !== P.badge) b.textContent = P.badge; return; }
    const sp = E("span", "pp-left"); sp.innerHTML = SLASH; sp.appendChild(E("span", "pp-badge", P.badge)); sp.lastChild.setAttribute("aria-hidden", "true");
    btn.appendChild(sp);
  }
  new MutationObserver(() => { if (P && P.on && P.can && (!btn.querySelector(".pp-left") || btn.getAttribute("aria-label") !== P.aria || !btn.title.startsWith("🔕"))) headPaint(); })
    .observe(btn, {childList: true, attributes: true, attributeFilter: ["aria-label", "title"]});
  function pagePaint() {
    const slot = document.getElementById("pp-push"); if (!slot || !P) return;
    if (slot.contains(document.activeElement) && document.activeElement.tagName === "INPUT") return;
    slot.textContent = ""; const box = E("div", "pp-box");
    const h = E("div", "pp-t"); h.append(E("span", "", "🔕 " + t("Pause notifications")), E("small", "", P.on ? t("running") : t("off"))); box.appendChild(h);
    if (P.on) running(box, "page");
    else { choices(box, "page");
      const own = E("div", "pp-own"); const lb = E("div", "pp-note wide", "⏱ " + t("Own time …") + " " + t("Minutes, hours (e.g. 90 or 1.5 h) or an end time (e.g. 22:30)"));
      const i = E("input"); i.type = "text"; i.placeholder = "45 min · 1.5 h · 22:30"; i.autocomplete = "off"; i.className = "wide";
      const go = E("button", "sec wide", "🔕 " + t("Pause notifications")); go.type = "button"; const er = E("div", "pp-err");
      go.onclick = async () => { const j = await act({action: "pause", mode: "own", value: i.value}, "page"); if (j && j.ok === false) er.textContent = j.error || ""; };
      own.append(lb, i, go, er); box.appendChild(own); }
    box.appendChild(E("div", "pp-note", t("Ends by itself.") + " " + t("Sabotage, theft, emergency call and «battery almost empty» still come.") + " "
      + t("Everything else is only recorded – at the end a short message comes.") + " " + t("Also with the bell 🔔 at the top and the button in the push message.")));
    slot.appendChild(box);
  }
  function paintAll() { headPaint(); pagePaint(); if (pop) open(); }
  const orig = btn.onclick;
  btn.onclick = ev => { if (pop) { close(); return; } if (P && P.can) { open(); return; } if (orig) orig.call(btn, ev); };
  document.addEventListener("pointerdown", close);
  document.addEventListener("keydown", e => { if (e.key === "Escape") close(); });
  load(true); setInterval(() => { if (!document.hidden) load(false); }, 30000);
  new MutationObserver(() => { const s = document.getElementById("pp-push"); if (s && !s.firstChild && P) pagePaint(); }).observe(document.body, {childList: true, subtree: true});
})();
"""
ALERT_JS = ALERT_JS + PP_JS


# ---- the manual: one paragraph at the end of «Push-Nachrichten» --------------------------------------------------------------
HELP_PP = {
    "de": '<p id="pp-help"><b>🔕 Mitteilungen pausieren:</b> Die Glocke 🔔 oben öffnet ein kleines Menü: 15 min, 30 min, 1 h, 2 h, «Bis morgen früh» (Weckzeit, sonst 07:00), «Bis ich zurück bin» (endet, wenn die Anwesenheit dein Handy wieder sieht, spätestens nach 24 h; braucht die Anwesenheit) oder «Eigene Zeit». Dasselbe unter Push-Nachrichten → Wann, im Pi-Fenster und mit dem Knopf «🔕 1 h pausieren» in der Push-Nachricht (bei ntfy anstelle von «Sirene»). Während der Pause zeigt die Glocke «🔕 43 min». Sabotage, Diebstahl, Notruf und «Akku fast leer» kommen trotzdem; alles andere wird nur aufgezeichnet und in der Nachrichtenliste vermerkt. Am Ende kommt «Mitteilungen wieder an» mit der Zahl der zurückgehaltenen Alarme. Der Administrator pausiert für alle, ein Nutzer mit Alarm-Pushes nur seine eigenen. Die Pause bleibt nach einem Neustart. Nicht zu verwechseln mit «Abstand zwischen Alarmen» (Mindestzeit zwischen zwei Pushes) und den Ruhezeiten (jeden Tag zur gleichen Zeit).</p>',
    "en": '<p id="pp-help"><b>🔕 Pause notifications:</b> The bell 🔔 at the top opens a small menu: 15 min, 30 min, 1 h, 2 h, «Until tomorrow morning» (wake-up time, else 07:00), «Until I am back» (ends when the presence detection sees your phone again, at the latest after 24 h; needs the presence detection) or «Own time». The same under Push messages → When, in the Pi window and with the button «🔕 Pause 1 h» in the push message (with ntfy instead of «Siren»). During the pause the bell shows «🔕 43 min». Sabotage, theft, emergency call and «battery almost empty» still come; everything else is only recorded and noted in the message list. At the end «Notifications on again» comes with the number of alarms held back. The administrator pauses for everybody, a user with alarm pushes only his own. The pause stays after a restart. Not the same as «Gap between alarms» (minimum time between two pushes) and the quiet hours (every day at the same time).</p>',
    "fr": '<p id="pp-help"><b>🔕 Mettre les notifications en pause :</b> la cloche 🔔 en haut ouvre un petit menu : 15 min, 30 min, 1 h, 2 h, « Jusqu’à demain matin » (heure du réveil, sinon 07:00), « Jusqu’à mon retour » (se termine quand la détection de présence revoit ton téléphone, au plus tard après 24 h ; demande la détection de présence) ou « Durée libre ». La même chose sous Messages push → Quand, dans la fenêtre du Pi et avec le bouton « 🔕 Pause 1 h » du message push (avec ntfy à la place de « Sirène »). Pendant la pause, la cloche affiche « 🔕 43 min ». Sabotage, vol, appel d’urgence et « batterie presque vide » arrivent quand même ; tout le reste est seulement enregistré et noté dans la liste des messages. À la fin arrive « Notifications de nouveau actives » avec le nombre d’alarmes retenues. L’administrateur met en pause pour tous, un utilisateur avec des push d’alarme seulement les siens. La pause reste après un redémarrage. À ne pas confondre avec « Écart entre les alarmes » (temps minimal entre deux push) et les heures calmes (chaque jour à la même heure).</p>',
    "it": '<p id="pp-help"><b>🔕 Mettere in pausa le notifiche:</b> la campanella 🔔 in alto apre un piccolo menu: 15 min, 30 min, 1 h, 2 h, «Fino a domattina» (ora della sveglia, altrimenti 07:00), «Finché torno» (finisce quando il rilevamento di presenza rivede il tuo telefono, al più tardi dopo 24 h; richiede il rilevamento di presenza) o «Tempo a scelta». Lo stesso in Messaggi push → Quando, nella finestra del Pi e con il pulsante «🔕 Pausa 1 h» nel messaggio push (con ntfy al posto di «Sirena»). Durante la pausa la campanella mostra «🔕 43 min». Sabotaggio, furto, chiamata d’emergenza e «batteria quasi scarica» arrivano comunque; tutto il resto viene solo registrato e annotato nella lista dei messaggi. Alla fine arriva «Notifiche di nuovo attive» con il numero di allarmi trattenuti. L’amministratore mette in pausa per tutti, un utente con push d’allarme solo i propri. La pausa resta dopo un riavvio. Da non confondere con «Intervallo tra gli allarmi» (tempo minimo tra due push) e le ore di quiete (ogni giorno alla stessa ora).</p>',
    "rm": '<p id="pp-help"><b>🔕 Pausar las communicaziuns:</b> la sajetta 🔔 sisum avra in pitschen menu: 15 min, 30 min, 1 h, 2 h, «Fin damaun marvegl» (ura da sveglia, uschiglio 07:00), «Fin che jau sun enavos» (finescha, cura che la constataziun da preschientscha vesa puspè tes telefonin, il pli tard suenter 24 h; basegna la constataziun da preschientscha) u «Agen temp». Il medem sut Messadis push → Cura, en la fanestra dal Pi e cun il buttun «🔕 Pausa 1 h» en il messadi push (cun ntfy empè da «Sirena»). Durant la pausa mussa la sajetta «🔕 43 min». Sabotascha, engul, clom d’urgenza e «accu prest vid» vegnan tuttina; tut il rest vegn mo registrà e notà en la glista dals messadis. A la fin vegn «Communicaziuns puspè activas» cun il dumber dals alarms retegnids. L’administratur pausescha per tuts, in utilisader cun push d’alarm mo ses agens. La pausa resta suenter in reavviament. Betg da confunder cun «Distanza tranter alarms» (temp minimal tranter dus push) e las uras da paus (mintga di a la medema ura).</p>',
}


def _help_pp(doc, lang):
    i = doc.find('<section id="notify"')
    if i < 0 or 'id="pp-help"' in doc:
        return doc
    j = doc.find("</section>", i)
    return doc[:j] + HELP_PP[lang] + doc[j:] if j >= 0 else doc


_hp_en_pp = HELP_PAGE.find('<div lang="en">')
if _hp_en_pp > 0:
    HELP_PAGE = _help_pp(HELP_PAGE[:_hp_en_pp], "de") + _help_pp(HELP_PAGE[_hp_en_pp:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_pp(HELP_X[_L], _L)


# ---- Pi window: the same choices under «Wann» (571a), the status line shows the pause ----------------------------------------
_PP_TK = {"app": None}


def _pp_tk_box(app, parent):
    box = tk.Frame(parent, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"], padx=8, pady=6)
    box.pack(fill="x", pady=(2, 6))
    S = app._pp = {"box": box, "sig": None}
    _pp_tk_fill(app)


def _pp_tk_do(app, fn):
    try:
        res = fn()
    except Exception as e:
        res = (False, str(e))
    if res and not res[0] and res[1]:
        messagebox.showinfo("MoveEye", tr_err(res[1]) if res[1] not in _HX_PP else tr(res[1]), parent=app.root)
    _pp_tk_fill(app, force=True)
    try:
        _px_tk_paint(app)
    except Exception:
        pass


def _pp_tk_own(app):
    from tkinter import simpledialog
    v = simpledialog.askstring("MoveEye", tr("Minutes, hours (e.g. 90 or 1.5 h) or an end time (e.g. 22:30)"), parent=app.root)
    if v:
        _pp_tk_do(app, lambda: pp_start("", "own", who="admin", via="window", value=v)[:2])


def _pp_tk_fill(app, force=False):
    S = getattr(app, "_pp", None)
    if not S:
        return
    try:
        if not S["box"].winfo_exists():
            return
    except Exception:
        return
    I = pp_info("")
    sig = (I["on"], I.get("line"), I.get("held_line"), I["presence"]["ready"], I["presence"]["text"], I["morning"])
    if sig == S["sig"] and not force:
        return
    S["sig"] = sig
    for c in S["box"].winfo_children():
        c.destroy()
    box = S["box"]
    top = tk.Frame(box, bg=C["panel"]); top.pack(fill="x")
    tk.Label(top, text="🔕 " + tr("Pause notifications"), bg=C["panel"], fg=C["txt"], font=("DejaVu Sans", 9, "bold"), anchor="w").pack(side="left")
    tk.Label(top, text=tr("running") if I["on"] else tr("off"), bg=C["panel"], fg=C["yel"] if I["on"] else C["mut"]).pack(side="right")
    if I["on"]:
        for txt, fg in (("🔕 " + tr("Notifications paused"), C["yel"]), (I["line"], C["txt"]), (I["by"], C["mut"]), (I["held_line"], C["mut"])):
            tk.Label(box, text=txt, bg=C["panel"], fg=fg, anchor="w", justify="left", wraplength=330).pack(fill="x")
        ttk.Button(box, text="🔔 " + tr("End pause"), command=lambda: _pp_tk_do(app, lambda: pp_end("", "ended", via="window"))).pack(fill="x", pady=(6, 2))
        r = tk.Frame(box, bg=C["panel"]); r.pack(fill="x")
        tk.Label(r, text=tr("Extend:"), bg=C["panel"], fg=C["mut"]).pack(side="left")
        for lab, kw in (("+15 min", {"add_min": 15}), ("+1 h", {"add_min": 60}), ("🌅 " + I["morning"], {"morning": True})):
            ttk.Button(r, text=lab, command=lambda kw=kw: _pp_tk_do(app, lambda: pp_extend("", via="window", **kw)[:2])).pack(side="left", padx=2)
        return
    g = tk.Frame(box, bg=C["panel"]); g.pack(fill="x", pady=(4, 0))
    for i, (m, lab) in enumerate((("15", "15 min"), ("30", "30 min"), ("60", "1 h"), ("120", "2 h"))):
        g.columnconfigure(i, weight=1)
        ttk.Button(g, text=lab, command=lambda m=m: _pp_tk_do(app, lambda: pp_start("", m, via="window")[:2])).grid(row=0, column=i, sticky="ew", padx=1)
    ttk.Button(box, text="🌅 " + tr("Until tomorrow morning") + "  (" + I["morning"] + ")",
               command=lambda: _pp_tk_do(app, lambda: pp_start("", "morning", via="window")[:2])).pack(fill="x", pady=(3, 0))
    hb = ttk.Button(box, text="🏠 " + tr("Until I am back") + "  (" + I["presence"]["text"] + ")",
                    command=lambda: _pp_tk_do(app, lambda: pp_start("", "home", via="window")[:2]))
    hb.pack(fill="x", pady=(3, 0))
    if not I["presence"]["ready"]:
        hb.state(["disabled"])
        tk.Label(box, text=tr("First enter your phone under Time & presence"), bg=C["panel"], fg=C["mut"], anchor="w", wraplength=330, justify="left").pack(fill="x")
    ttk.Button(box, text="⏱ " + tr("Own time …"), command=lambda: _pp_tk_own(app)).pack(fill="x", pady=(3, 0))
    tk.Label(box, text=tr("Ends by itself.") + " " + tr("Sabotage, theft, emergency call and «battery almost empty» still come.") + " "
             + tr("Everything else is only recorded – at the end a short message comes."), bg=C["panel"], fg=C["mut"], anchor="w",
             wraplength=330, justify="left", font=("DejaVu Sans", 8)).pack(fill="x", pady=(4, 0))


_pp_tk_head_before = _px_tk_head


# wraps: _px_tk_head (571a)
def _px_tk_head(parent, text):
    _pp_tk_head_before(parent, text)
    app = _PP_TK["app"]
    if text == "When" and app is not None:
        try:
            _pp_tk_box(app, parent)
        except Exception as e:
            log_event("sys", f"Window: push pause: {e}"[:160])


_pp_tk_panel_before = _px_tk_panel


# wraps: _px_tk_panel (571a)
def _px_tk_panel(app, sbody):
    _PP_TK["app"] = app
    try:
        return _pp_tk_panel_before(app, sbody)
    finally:
        _PP_TK["app"] = None


_pp_tk_paint_before = _px_tk_paint


# wraps: _px_tk_paint (571a, every 4 s)
def _px_tk_paint(app):
    _pp_tk_paint_before(app)
    try:
        _pp_tk_fill(app)
    except Exception:
        pass


# ---- self-test ------------------------------------------------------------------------------------------------------------------
def push_pause_selftest():
    keep = {k: json.loads(json.dumps(CFG.get(k))) for k in ("push_pause", "push_pause_users", "wake_on", "wake_time", "presence_hosts",
                                                             "presence_macs", "presence_bt", "lang", "public_url", "push_actions")}
    try:
        CFG.update(lang="de", wake_on=True, wake_time="06:30", presence_hosts=[], presence_macs=[], presence_bt=[], push_pause={}, push_pause_users={})
        now = datetime(2026, 11, 15, 22, 0).timestamp()
        assert datetime.fromtimestamp(pp_morning_ts(now)).strftime("%d %H:%M") == "16 06:30"
        assert datetime.fromtimestamp(pp_morning_ts(datetime(2026, 11, 16, 2, 0).timestamp())).strftime("%d %H:%M") == "16 06:30"
        CFG["wake_on"] = False
        assert datetime.fromtimestamp(pp_morning_ts(now)).strftime("%H:%M") == "07:00"
        assert pp_parse("45", now) == (now + 2700, "") and pp_parse("1.5 h", now) == (now + 5400, "") and pp_parse("1:30 h", now)[0] == now + 5400
        assert datetime.fromtimestamp(pp_parse("23:15", now)[0]).strftime("%d %H:%M") == "15 23:15"
        assert datetime.fromtimestamp(pp_parse("21:00", now)[0]).strftime("%d %H:%M") == "16 21:00"
        assert pp_parse("25 h", now)[1] and pp_parse("abc", now)[1] and pp_parse("0", now)[1]
        # pp_start starts the clock thread (pp_tick on the real clock): a pause from the fixed «now» above would be ended at
        # once after 15.11.2026 23:00 - so this part starts the pause at the real time
        t = time.time()
        ok, err, s = pp_start("", "60", now=t, save=False)
        assert ok and s["until"] == t + 3600 and pp_active("", t + 10) and not pp_active("", t + 3601)
        assert not pp_start("", "home", now=t, save=False)[0], "home needs the presence"
        for p, ex in (({"event": "person"}, False), ({"event": "prealarm"}, False), ({"event": "info", "text": "Update"}, False),
                      ({"event": "tamper"}, True), ({"event": "test"}, True), ({"event": "info", "info_title": "{name}: 🆘 SOS"}, True),
                      ({"event": "info", "text": trf("Battery almost empty: about {pct} % ({hours:.1f} h) left – please charge or swap", pct=9, hours=0.5)}, True),
                      ({"event": "info", "text": "Battery empty – the Pi shuts down cleanly"}, True), ({"event": "info", "pp_pass": True}, True)):
            assert pp_exempt(p) == ex, p
        assert pp_what(3, 0) == "3 Alarme" and pp_what(1, 2) == "1 Alarm · 2 Hinweise" and pp_left_text(43 * 60 - 5) == "43 min"
        assert pp_left_text(7 * 3600 + 49 * 60, True) == "7 h 49" and pp_left_text(3595, True) == "1 h 00"
        assert [pp_badge(x, "min") for x in (43 * 60 - 5, 3595, 7 * 3600 + 49 * 60)] == ["43′", "1h", "7h"] and pp_badge(9000, "morning") == "☾"
        assert pp_left_long(43 * 60 - 5) == "43 Minuten" and pp_left_long(7 * 3600 + 49 * 60 - 5) == "7 Stunden 49 Minuten" and pp_left_long(3600) == "1 Stunde"
        _pp_put("", None, False)
        assert pp_scope_of("admin", "") == (True, "")
        assert tr("Gap between alarms (s)") == "Abstand zwischen Alarmen (s)"
        for L in ("fr", "it", "rm"):
            assert all(TRX[L].get(k) for k in _HX_PP), L
        assert 'id="pp-help"' in HELP_PAGE and all('id="pp-help"' in HELP_X.get(L_, 'id="pp-help"') for L_ in ("fr", "it", "rm"))
        assert "pause" in ALX_ACTS and "resume" in ALX_ACTS and ALX_NAMES["pause"] == "🔕 Pause 1 h"
        assert "/api/pushpause" in VIEW_POST and role_allows("kid", "/api/pushpause", "GET", {})
    finally:
        CFG.update(keep)
    return "times, own time, exempt messages, counts, rights, 5 languages, manual"


SELFTEST_EXTRA.append(("Push pause (639zzzzp)", push_pause_selftest))
