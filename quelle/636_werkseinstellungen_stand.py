#@ MoveEye – Teil 636: Werkseinstellungen – die Standardwerte aller Teile, bevor die gespeicherten Einstellungen geladen werden (für «Auf Werkseinstellungen zurücksetzen», 586). Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# All parts have added their settings now (CFG.setdefault in later parts), the start (640) loads the file only after this.
import copy as _copy_g2
FACTORY_CFG = _copy_g2.deepcopy(CFG)
