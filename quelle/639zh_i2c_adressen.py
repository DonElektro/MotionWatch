#@ MoveEye – Teil 639zh: I2C-Adressen (Hardware-Klärung 01.11.2026) – Solar-Strommesser INA219 nicht mehr auf der Adresse des PCA9685, Shunt 0,01 Ohm, Selbsttests. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Hardware-Klärung 01.11.2026 (Paket «Bauen», Punkt 6):
#   - Der Solar-Strommesser (INA219) stand ab Werk auf 0x41 = Adresse des PCA9685 (Servos, Lötbrücke A0). Beide zusammen
#     lesen sich gegenseitig die Register. Doku, Materialliste und Gehäuse sagen 0x44 (INA219 mit Brücke A1 bzw. DIP 0x44).
#     Neu: Standard 0x44 (020, 280). Alte Einstellungen mit «Solar aus» und derselben Adresse wie der PCA9685 werden einmal
#     auf eine freie Adresse gesetzt (0x44, sonst 0x45); mit «Solar ein» bleibt alles, wie der Bediener es eingestellt hat.
#   - Die Konfliktprüfung (030) kennt jetzt auch die Wärmebildkamera (Thermal-90, fest 0x40) und lässt den UPS HAT (E) aus
#     (eigener Chip auf 0x2D, die Adresse «ups_addr» gilt nur für den INA219 der UPS HATs A / B / C).
#   - Entscheid Besitzer 01.11.2026: Shunt ab Werk 0,01 Ohm (Gravity INA219, DFRobot SEN0291, Bastelgarage 421023; vorher 0,1 =
#     blaues Billig-Modul). Alte Einstellungen werden EINMAL umgestellt (Merker «solar_shunt_mig_done»), wenn noch der alte
#     Standard 0,1 steht und Solar nie eingeschaltet wurde (= nie selbst eingerichtet). Mit Solar ein bleibt die eigene Wahl.
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


def solar_shunt_migrate(cfg=None):
    """once: the old standard 0.1 Ohm with «Solar» never switched on -> 0.01 Ohm (Gravity INA219); True = changed"""
    c = CFG if cfg is None else cfg
    if c.get("solar_shunt_mig_done"):
        return False
    c["solar_shunt_mig_done"] = True
    try:
        old = float(c.get("solar_shunt", 0.0))
    except (TypeError, ValueError):
        return False
    if c.get("solar_on") or abs(old - 0.1) > 1e-9:
        return False                                       # set up by the operator (or already another value): stays
    c["solar_shunt"] = 0.01
    return True


def _settings_migrations(cfg_in):                         # + 639zh: solar meter away from the address of the PCA9685
    _settings_migrations_before_i2c(cfg_in)
    try:
        old = CFG.get("solar_addr")
        if solar_addr_migrate():
            log_event("sys", f"Solar meter (INA219): address {old} is the servo board - set to {CFG['solar_addr']}")
        if solar_shunt_migrate():
            log_event("sys", "Solar meter (INA219): shunt set to the new standard 0.01 Ohm (Gravity INA219)")
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


def solar_shunt_selftest():
    """standard 0.01 Ohm; the old standard is changed once (solar off), a value of the operator stays; the reading scales"""
    assert DEFAULTS["solar_shunt"] == 0.01 and DEFAULTS["solar_shunt_mig_done"] is False, DEFAULTS["solar_shunt"]
    sl = [x for x in SLIDERS if x[1] == "solar_shunt"]
    assert sl and sl[0][3] <= 0.01 <= sl[0][4], sl
    c = {"solar_on": False, "solar_shunt": 0.1}
    assert solar_shunt_migrate(c) and c["solar_shunt"] == 0.01 and c["solar_shunt_mig_done"], c
    c["solar_shunt"] = 0.1                                 # chosen again after the change: stays (only once)
    assert not solar_shunt_migrate(c) and c["solar_shunt"] == 0.1
    c = {"solar_on": True, "solar_shunt": 0.1}
    assert not solar_shunt_migrate(c) and c["solar_shunt"] == 0.1, "set up by the operator: stays"
    c = {"solar_on": False, "solar_shunt": 0.05}
    assert not solar_shunt_migrate(c) and c["solar_shunt"] == 0.05
    for k in ("Current meter: shunt resistor (Ohm; Gravity INA219 0.01, blue modules 0.1)",
              "INA219 current meter between the panel and the charger (address 0x44 - 0x40 is the thermal camera, 0x41 the servo board; shunt 0.01 Ohm for the Gravity INA219)."):
        assert DE.get(k) and all(TRX[L].get(k) for L in ("fr", "it", "rm")), k
        assert "0,01" in DE[k] and all("0,01" in TRX[L][k] for L in ("fr", "it", "rm")), k
    return "standard 0.01 Ohm (Gravity INA219); old 0.1 changed once when solar was never on; the operator's value stays; texts in 5 languages"


SELFTEST_EXTRA.append(("I2C addresses: no conflict with the standard values (639zh)", i2c_adressen_selftest))
SELFTEST_EXTRA.append(("Solar meter: shunt 0.01 Ohm, old standard taken over once (639zh)", solar_shunt_selftest))
