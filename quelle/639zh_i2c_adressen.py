#@ MoveEye – Teil 639zh: I2C-Adressen (Hardware-Klärung 01.11.2026) – Solar-Strommesser INA219 nicht mehr auf der Adresse des PCA9685, Selbsttest der Adresskonflikte. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Hardware-Klärung 01.11.2026 (Paket «Bauen», Punkt 6):
#   - Der Solar-Strommesser (INA219) stand ab Werk auf 0x41 = Adresse des PCA9685 (Servos, Lötbrücke A0). Beide zusammen
#     lesen sich gegenseitig die Register. Doku, Materialliste und Gehäuse sagen 0x44 (INA219 mit Brücke A1 bzw. DIP 0x44).
#     Neu: Standard 0x44 (020, 280). Alte Einstellungen mit «Solar aus» und derselben Adresse wie der PCA9685 werden einmal
#     auf eine freie Adresse gesetzt (0x44, sonst 0x45); mit «Solar ein» bleibt alles, wie der Bediener es eingestellt hat.
#   - Die Konfliktprüfung (030) kennt jetzt auch die Wärmebildkamera (Thermal-90, fest 0x40) und lässt den UPS HAT (E) aus
#     (eigener Chip auf 0x2D, die Adresse «ups_addr» gilt nur für den INA219 der UPS HATs A / B / C).
# ----------------------------------------------------------------------------
_settings_migrations_before_i2c = _settings_migrations


def solar_addr_migrate(cfg=None):
    """«Solar» off and on the address of the servo board: to the first free address of 0x44 / 0x45 (True = changed)"""
    c = CFG if cfg is None else cfg
    a = str(c.get("solar_addr", "")).lower()
    if c.get("solar_on") or a != str(c.get("pca_address", "")).lower():
        return False
    used = {str(c.get(k, "")).lower() for k in ("pca_address", "mover_addr", "ups_addr")} | set(I2C_FIXED.values())
    for cand in ("0x44", "0x45"):
        if cand not in used:
            c["solar_addr"] = cand
            return True
    return False


def _settings_migrations(cfg_in):                         # + 639zh: solar meter away from the address of the PCA9685
    _settings_migrations_before_i2c(cfg_in)
    try:
        old = CFG.get("solar_addr")
        if solar_addr_migrate():
            log_event("sys", f"Solar meter (INA219): address {old} is the servo board - set to {CFG['solar_addr']}")
    except Exception as e:
        log_event("sys", f"Settings migration (639zh): {e}"[:150])


def i2c_adressen_selftest():
    """standard addresses without a conflict; the thermal camera on 0x40 and the PCA9685 on 0x41 are seen; the migration"""
    base = {"servo_driver": "pca9685", "pca_address": "0x41", "solar_on": True, "solar_addr": DEFAULTS["solar_addr"],
            "mover_mode": "auto", "mover_addr": DEFAULTS["mover_addr"], "ups_on": True, "ups_model": "auto",
            "ups_addr": DEFAULTS["ups_addr"], "thermal_on": True, "thermal_source": "senxor"}
    assert DEFAULTS["solar_addr"] == "0x44", DEFAULTS["solar_addr"]
    assert DEFAULTS["solar_addr"] != DEFAULTS["pca_address"], "solar meter on the address of the servo board"
    assert i2c_conflicts(base) == [], i2c_conflicts(base)
    cf = i2c_conflicts(dict(base, solar_addr="0x41"))
    assert cf == [("pca_address", "solar_addr", "0x41")], cf
    cf = i2c_conflicts(dict(base, solar_addr="0x40"))
    assert cf == [("_thermal", "solar_addr", "0x40")], cf
    assert i2c_conflicts(dict(base, solar_addr="0x40", thermal_on=False)) == []
    assert i2c_conflicts(dict(base, solar_addr="0x42", ups_model="e")) == [], "UPS HAT (E) has no INA219 on 0x42"
    assert i2c_conflicts(dict(base, solar_addr="0x42"))[0][2] == "0x42"
    c = dict(base, solar_on=False, solar_addr="0x41")
    assert solar_addr_migrate(c) and c["solar_addr"] == "0x44", c["solar_addr"]
    c = dict(base, solar_on=False, solar_addr="0x44", pca_address="0x44")
    assert solar_addr_migrate(c) and c["solar_addr"] == "0x45", c["solar_addr"]
    c = dict(base, solar_on=True, solar_addr="0x41")
    assert not solar_addr_migrate(c) and c["solar_addr"] == "0x41", "switched on: the operator's choice stays"
    c = dict(base, solar_on=False, solar_addr="0x45")
    assert not solar_addr_migrate(c)
    return "thermal 0x40 · PCA9685 0x41 · solar INA219 0x44 · UPS INA219 0x42 / UPS HAT (E) 0x2D · mover 0x60: no conflict"


SELFTEST_EXTRA.append(("I2C addresses: no conflict with the standard values (639zh)", i2c_adressen_selftest))
