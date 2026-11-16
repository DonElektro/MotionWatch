#@ MoveEye – Teil 639zzzzu: Geekworm X1206 (Besitzer 16.11.2026) – Einstellung «Lade-LED: GPIO» (neue Geräte GPIO 13, Taste «Schutz» GPIO 12; ältere Einstellungen behalten 6 / 16), Texte in 5 Sprachen, Selbsttest. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Entscheide Besitzer 16.11.2026 (Akku: Geekworm X1206 V2.0 statt Waveshare UPS HAT (E); das UPS HAT (E) bleibt unterstützt):
#   * Teil 100: dritter Weg «x12» (MAX17043 auf I2C 0x36, 1S4P), automatisch in der Reihenfolge 0x2D -> 0x36 -> 0x42. GPIO 6 (PLD:
#     Strom am Eingang) und GPIO 16 (Laden ein / aus) gehören der Platine: MoveEye liest sie nur (pinctrl) und schaltet sie nie -
#     Lade-LED (639zi), Tasten (163a) und Relais / GPIO-Lampen (080) bleiben dort aus und melden es einmal im Protokoll.
#   * Lade-LED und Taste «Schutz» sind Einstellungen: neue Geräte GPIO 13 (Pin 33) und 12 (Pin 32); eine Einstellungsdatei einer
#     älteren Version (ohne die Schlüssel) behält 6 / 16 (Geräte mit UPS HAT (E) sind so verdrahtet).
# Test: werkzeuge/x1206_test.py (erfundener I2C-Bus mit 0x2D / 0x36 / 0x42, Stromausfall, Schutz-Alarm, Abschalten, GPIO-Sperre).
# ----------------------------------------------------------------------------
# Was ohne die Zusatz-ZIP gelten muss, steht ausserhalb des Literals: die Übernahme älterer Einstellungen (6 / 16). Die Einstellung
# selbst (Auswahl, Hilfe, Texte) und der Selbsttest stehen im Literal X1206_PY (bauen.py legt es in die ZIP, zd_exec von 639zzzzk).
def x12_pins_migrate(cfg_in):
    """settings of an older version (no key): charge LED GPIO 6, button «Protection» GPIO 16 - as those devices are wired"""
    for k, v in (("charge_led_gpio", "6"), ("btn_gpio_protect", "16")):
        if isinstance(cfg_in, dict) and k not in cfg_in:
            CFG[k] = v


_settings_migrations_before_x12 = _settings_migrations


def _settings_migrations(cfg_in):                         # + 639zzzzu: older settings keep GPIO 6 / 16
    _settings_migrations_before_x12(cfg_in)
    x12_pins_migrate(cfg_in)


X1206_PY = r'''_CLG_LABEL = "Charge LED: GPIO"
TEXTS.append(("Battery", "charge_led_gpio", _CLG_LABEL, "enum", "cl_gpio"))
TEXT_SPECS["charge_led_gpio"] = ("enum", "cl_gpio")
SET_HELP["charge_led_gpio"] = ("Where the green charge LED is wired. New devices: GPIO 13 (pin 33). Older devices keep GPIO 6 (pin 31). "
                               "With a Geekworm X1206 never GPIO 6 or 16: they belong to the board, the LED then stays off.", "GPIO 13.")


_text_choice_pairs_x12_base = text_choice_pairs


def text_choice_pairs(key):                               # + 639zzzzu: free GPIOs for the charge LED (never 6 / 16 with an X1206)
    if (TEXT_SPECS.get(key) or (None, None))[1] != "cl_gpio":
        return _text_choice_pairs_x12_base(key)
    cur = str(CFG.get(key) or "")
    try:
        used = set(_sens_used_gpios_cl_base(None)) | ups_x12_pins()
    except Exception:
        used = set()
    gs = [g for g in FREE_GPIOS if g not in used] + ([int(cur)] if cur.isdigit() else [])
    return [("", "– " + tr("none") + " –")] + [(str(g), f"GPIO {g}") for g in sorted(set(gs))]


_HX_X1206 = {
    _CLG_LABEL: ("Lade-LED: GPIO", "LED de charge : GPIO", "LED di carica: GPIO", "LED da chargiar: GPIO"),
    SET_HELP["charge_led_gpio"][0]:
        ("Wo die grüne Lade-LED angeschlossen ist. Neue Geräte: GPIO 13 (Pin 33). Ältere Geräte behalten GPIO 6 (Pin 31). Mit einem "
         "Geekworm X1206 nie GPIO 6 oder 16: sie gehören der Platine, die LED bleibt dann aus.",
         "Où la LED de charge verte est branchée. Nouveaux appareils : GPIO 13 (broche 33). Les appareils plus anciens gardent le "
         "GPIO 6 (broche 31). Avec un Geekworm X1206, jamais le GPIO 6 ou 16 : ils appartiennent à la carte, la LED reste alors éteinte.",
         "Dove è collegato il LED di carica verde. Nuovi dispositivi: GPIO 13 (pin 33). I dispositivi più vecchi mantengono il GPIO 6 "
         "(pin 31). Con un Geekworm X1206 mai GPIO 6 o 16: appartengono alla scheda, il LED resta allora spento.",
         "Nua che la LED da chargiar verda è colliada. Apparats novs: GPIO 13 (pin 33). Apparats pli vegls tegnan GPIO 6 (pin 31). "
         "Cun in Geekworm X1206 mai GPIO 6 u 16: els appartegnan a la platina, la LED resta lura stizzada."),
    "GPIO 13.": ("GPIO 13.", "GPIO 13.", "GPIO 13.", "GPIO 13."),
}
for _k, _v in _HX_X1206.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])


def x1206_selftest():
    """the third battery board: model choice, detection order, GPIO 6 / 16 locked, older settings keep 6 / 16, texts"""
    keep = {k: CFG.get(k) for k in ("charge_led_gpio", "btn_gpio_protect", "ups_model")}
    keep_x = dict(UPS_X12)
    try:
        assert ("x12", "Geekworm X1206 – 4 × 21700, I2C 0x36") in text_choice_pairs("ups_model")
        assert DEFAULTS["charge_led_gpio"] == "13" and DEFAULTS["btn_gpio_protect"] == "12", "new devices: GPIO 13 / 12"
        UPS_X12.update(seen=False, probed=True)
        CFG["ups_model"] = "auto"
        assert ups_x12_pins() == set(), "without an X1206 GPIO 6 / 16 stay free (UPS HAT (E) devices)"
        UPS_X12["seen"] = True
        assert ups_x12_pins() == {6, 16}
        CFG["btn_gpio_protect"] = "16"; UPS_X12["warned"] = {("button «protect»", 16)}      # no log line from the self-test
        assert "protect" not in led_gpio_pins(), "no pull-up on GPIO 16 with an X1206"
        CFG["charge_led_gpio"] = "13"
        ch = dict(text_choice_pairs("charge_led_gpio"))
        assert "6" not in ch and "16" not in ch and ch.get("13") == "GPIO 13", ch
        x12_pins_migrate({"lang": "de"})
        assert CFG["charge_led_gpio"] == "6" and CFG["btn_gpio_protect"] == "16", "older settings keep GPIO 6 / 16"
        CFG.update(charge_led_gpio="13", btn_gpio_protect="12")
        x12_pins_migrate({"charge_led_gpio": "13", "btn_gpio_protect": "12"}); x12_pins_migrate(None)
        assert CFG["charge_led_gpio"] == "13" and CFG["btn_gpio_protect"] == "12"
        for L_ in ("fr", "it", "rm"):
            assert tr(_CLG_LABEL, L_) != _CLG_LABEL and tr(SET_HELP["charge_led_gpio"][0], L_) != SET_HELP["charge_led_gpio"][0], L_
        assert "Geekworm X1206" in WEB_PAGE and "0x36" in HELP_PAGE
        return "model «x12», GPIO 6 / 16 locked only with an X1206, new devices 13 / 12, older settings keep 6 / 16, texts in 5 languages"
    finally:
        CFG.update(keep)
        UPS_X12.clear(); UPS_X12.update(keep_x)


SELFTEST_EXTRA.append(("Geekworm X1206: model, GPIO 6 / 16 locked, charge LED / button GPIO (639zzzzu)", x1206_selftest))
'''
zd_exec(X1206_PY, '639zzzzu_x1206.py')
