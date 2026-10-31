extends Node
## «Maggie und der Bergkristall» (Daniel, 31.10.2026) – Geschichte für Kinder (ca. 12) im Bergtal. Paket S1 «Rahmen».
## Eigene Kachel unter «Spielen». Alles selbst erfunden (nur lose Inspiration: vier Reiche = vier Jahreszeiten).
##
## API für S2 (maggie_hund.gd / maggie_helfer.gd) und S3 (maggie_gefahr.gd) – Zugriff über main.maggie:
##   region_aktiv() -> String         "herbst" | "winter" | "fruehling" | "sommer" | "" (keine Region läuft)
##   spieler_pos() -> Vector3         wo die Spielfigur gerade steht (Weltkoordinaten)
##   kristall_bei_spieler() -> bool   der Kristall ist bei der Figur (immer true, solange die Geschichte läuft)
##   erwischt(von: String)            ein böses Tier hat die Figur erwischt: kurzer Schreck, dann zurück zum Rastplatz
##   tipp(text: String)               kurzer Tipp unten im Bild (einfache Sprache, mit T.t() übersetzt übergeben)
##   moveeye_sagt(text: String)       ein kurzer Satz «MoveEye würde jetzt …» (kindgerecht, keine Technik-Wörter)
##   region_fertig(id: String)        die Region ist geschafft (Schutzding + Rätsel erledigt) -> zurück zur Auswahl
##   region_mitte(id: String) -> Vector3   (static) die Mitte einer Region im Bergtal (für Tiere, Rätsel, Helfer)
##   signal region_gestartet(id)      eine Region beginnt (die Figur steht dann am ersten Rastplatz der Region)
##   signal region_beendet(id)        die Region ist fertig (Aufräumen: eigene Knoten der Region entfernen)
##   signal geschichte_beendet()      die Geschichte wurde verlassen oder ist fertig (alles aufräumen)
## Module: ist res://scripts/maggie_hund.gd, maggie_helfer.gd oder maggie_gefahr.gd vorhanden, wird es beim Start als Kind
## dieses Knotens angelegt; vorher werden (wenn vorhanden) die Variablen `main` und `story` gesetzt.
##
## TODO (S1): Kachel, Figur wählen, Einstieg, Regionen-Auswahl, Rastplätze/Speichern, Zukunftsbilder, Finale, Abspann.

const T = preload("res://scripts/i18n.gd")

signal region_gestartet(id: String)
signal region_beendet(id: String)
signal geschichte_beendet()

const REGIONEN := ["herbst", "winter", "fruehling", "sommer"]
# the middle of every region in the Bergtal (x, z; y from the ground)
const MITTE := {"herbst": Vector2(-420, 260), "winter": Vector2(380, -420), "fruehling": Vector2(-380, -360), "sommer": Vector2(420, 300)}

var main
var running := false
var region := ""
var _spieler := Vector3.ZERO


static func region_mitte(id: String) -> Vector3:
	var m: Vector2 = MITTE.get(id, Vector2.ZERO)
	return Vector3(m.x, 0.0, m.y)


func region_aktiv() -> String:
	return region if running else ""


func spieler_pos() -> Vector3:
	return _spieler


func kristall_bei_spieler() -> bool:
	return running


func erwischt(von: String) -> void:
	print("Maggie: erwischt von ", von)


func tipp(text: String) -> void:
	print("Maggie-Tipp: ", text)


func moveeye_sagt(text: String) -> void:
	print("MoveEye: ", text)


func region_fertig(id: String) -> void:
	region_beendet.emit(id)
