#@ MoveEye – Teil 635c: Kein WLAN-Name in ausgehenden Meldungen (Datenschutz, Besitzer 01.11.2026): Push, ntfy, Telegram, Pushover, Web-Push, E-Mail, SMS, Webhook und das Test-Postfach zeigen statt der SSID nur einen Platzhalter («bekanntes WLAN»). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Der Name des WLAN verrät, wo das Gerät steht (Heim-WLAN, Campingplatz, Handy-Hotspot mit Vorname). Lokal (Web-Seite, Fenster)
# bleibt er sichtbar - das sieht nur der Besitzer. Zwei Stufen:
#   * die Aufrufer schreiben ihn nicht mehr hinein: 110 «MoveEye is online ({net}): {addr}», 150 «Internet … is back ({net})»,
#     {net} = push_net_label() (Kurzform in 635b PK_TEXTS «{net} · open page»);
#   * Sicherheitsnetz in 060 Notifier._dispatch: push_no_ssid(p) ersetzt den Namen des verbundenen WLAN (auch des zweiten
#     Adapters) in Titel und Text durch den Platzhalter, bevor irgendein Kanal etwas bekommt. Der Name des eigenen WLAN des
#     Geräts (hotspot_ssid, ab Werk «MoveEye») ist kein persönliches Datum und bleibt (sonst würde «MoveEye» überall ersetzt).
# Kein ntfy-Thema, keine Adresse, keine Zugangsdaten hier. Nach 635b (PK_TEXTS, _HX_PK, pk_tr), vor 636 Werkseinstellungen.
# ----------------------------------------------------------------------------
_HX_NOSSID = {
    "MoveEye is online ({net}): {addr}": ("MoveEye ist online ({net}): {addr}", "MoveEye est en ligne ({net}) : {addr}",
                                          "MoveEye è online ({net}): {addr}", "MoveEye è online ({net}): {addr}"),
    "Internet was gone for {min} min - it is back ({net})": ("Internet war {min} Min. weg – es ist wieder da ({net})",
                                                             "Internet était coupé {min} min - il est revenu ({net})",
                                                             "Internet assente per {min} min - è tornato ({net})",
                                                             "Internet era davent {min} min - el è puspè qua ({net})"),
}
for _k, _v in _HX_NOSSID.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])

_NOSSID_KEEP = ("MoveEye", "MotionWatch")                 # names of the device itself, never replaced


def push_net_label():
    """the neutral name of the network in a message: «known Wi-Fi» (the Pi connects only to saved networks)"""
    return pk_tr("known Wi-Fi")


def push_ssids():
    """the Wi-Fi names that must not leave the device: the connected network (main adapter, second adapter of 150) -
    not the own Wi-Fi of the device (hotspot_ssid), names shorter than 3 characters are not searched (too many false hits)"""
    own = {str(CFG.get("hotspot_ssid") or "").strip(), *_NOSSID_KEEP}
    out = []
    for src in (STATE.get("wifi"), (STATE.get("dual") or {}).get("uplink") if isinstance(STATE.get("dual"), dict) else None):
        s = str((src or {}).get("ssid") or "").strip() if isinstance(src, dict) else ""
        if len(s) >= 3 and s not in own and s not in out:
            out.append(s)
    return sorted(out, key=len, reverse=True)


def push_no_ssid(p, ssids=None):
    """a copy of the message with every Wi-Fi name replaced by the placeholder (title, text, extra fields)"""
    names = push_ssids() if ssids is None else [s for s in ssids if len(str(s)) >= 3]
    if not names or not isinstance(p, dict):
        return p
    rx = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(s) for s in names) + r")(?!\w)")
    lab = push_net_label()
    q = dict(p)
    for k in ("text", "info_title", "text_full", "dist", "where", "source"):
        if isinstance(q.get(k), str):
            q[k] = rx.sub(lab, q[k])
    return q


def push_no_ssid_selftest():
    keep_l, keep_w, keep_h = CFG.get("lang"), STATE.get("wifi"), CFG.get("hotspot_ssid")
    test = "Testnetz-Q7x Müller"
    try:
        CFG["lang"] = "de"; CFG["hotspot_ssid"] = "MoveEye"
        STATE["wifi"] = {"connected": True, "ssid": test, "ip": "192.0.2.5", "dbm": -50}
        now = datetime(2026, 11, 1, 9, 0, 0).isoformat(timespec="seconds")
        P = lambda **kw: dict({"event": "info", "persons": 0, "time": now, "snapshot": None, "rain": False, "wind": "",
                               "source": "cam", "link": ""}, **kw)
        # the call sites (110 online, 150 internet back) and an old text that still names the network (safety net)
        cases = [P(text=trf("MoveEye is online ({net}): {addr}", net=push_net_label(), addr="http://192.0.2.5:5000/")),
                 P(text=trf("Internet was gone for {min} min - it is back ({net})", min=5, net=push_net_label()),
                   info_title="{name}: " + tr("Network")),
                 P(text=trf("MoveEye is online in Wi-Fi {ssid}: {addr}", ssid=test, addr="http://192.0.2.5:5000/")),
                 P(text="WLAN «" + test + "» weg", info_title="{name}: " + test),
                 P(event="tamper", text=test + " – " + tr("Wi-Fi jamming attack"), info_title="{name}: " + tr("Wi-Fi jamming attack"))]
        for p in cases:
            q = push_no_ssid(p)
            outs = [Notifier._title(q), Notifier._text(q), push_long(q), Notifier._sms(q), str(q.get("info_title"))]
            for o in outs:
                assert test not in o and "Testnetz" not in o, f"Wi-Fi name in an outgoing message: «{o}»"
        assert "bekanntes WLAN" in push_long(push_no_ssid(cases[0])), push_long(push_no_ssid(cases[0]))
        assert Notifier._text(push_no_ssid(cases[0])) == "bekanntes WLAN · Seite öffnen", Notifier._text(push_no_ssid(cases[0]))
        # the own Wi-Fi of the device and words that only contain the name stay
        assert push_no_ssid(P(text="MoveEye ist online"))["text"] == "MoveEye ist online"
        assert push_no_ssid(P(text="Camping-Platz"), ["Camp"])["text"] == "Camping-Platz"
        STATE["wifi"] = {"connected": True, "ssid": "MoveEye", "ap": True}
        assert push_ssids() == [], push_ssids()
        # all languages have the placeholder and the new texts
        for L in ("fr", "it", "rm"):
            for k in _HX_NOSSID:
                assert TRX[L].get(k) and "{net}" in TRX[L][k], (L, k)
        for L in ("de", "en", "fr", "it", "rm"):
            CFG["lang"] = L
            assert push_net_label() and "{" not in push_net_label(), L
    finally:
        CFG["lang"], CFG["hotspot_ssid"] = keep_l, keep_h
        STATE["wifi"] = keep_w
    return True


SELFTEST_EXTRA.append(("No Wi-Fi name (SSID) in push messages (635c)", push_no_ssid_selftest))
