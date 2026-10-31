extends Node
## «Maggie und der Bergkristall» (Daniel, 31.10.2026) – Geschichte für Kinder (ca. 12) im Bergtal. Paket S1 «Rahmen».
## Eigene Kachel unter «Spielen». Alles selbst erfunden (nur lose Inspiration: vier Reiche = vier Jahreszeiten).
##
## API für S2 (maggie_hund.gd / maggie_helfer.gd) und S3 (maggie_gefahr.gd) – Zugriff über main.maggie (oder `story`):
##   region_aktiv() -> String         "herbst" | "winter" | "fruehling" | "sommer" | "" (keine Region läuft: Einstieg, Auswahl,
##                                    Finale, Pause zählt als laufend)
##   spieler_pos() -> Vector3         wo die Spielfigur steht (WELT-Koordinaten, wie main.ground_y / visitors)
##   spieler() -> Node3D              die Figur selbst (actor.gd, controlled) oder null
##   kristall_bei_spieler() -> bool   der Kristall ist bei der Figur (true, sobald Maggie ihn ausgegraben hat)
##   erwischt(von: String)            ein böses Tier hat die Figur erwischt ("wildschwein" | "wolf" | "kraehe" | "viper" …):
##                                    kurzer Schreck, dann sicher zurück zum letzten Rastplatz; der Kristall bleibt. Danach
##                                    ein paar Sekunden Schonzeit (geschuetzt() = true) – in der Zeit nicht nochmals erwischen.
##   geschuetzt() -> bool             gerade erwischt / Schreck läuft / Karte offen / Pause: böse Tiere warten
##   tipp(text: String)               kurzer Tipp unten im Bild (einfache Sprache; schon mit T.t() übersetzt übergeben)
##   moveeye_sagt(text: String)       ein kurzer Satz «MoveEye würde jetzt …» (kindgerecht, keine Technik-Wörter)
##   region_fertig(id: String)        die Region ist geschafft -> Freude, Speichern, zurück zur Auswahl der Regionen
##   region_mitte(id: String) -> Vector3   die Mitte einer Region in WELT-Koordinaten auf dem Boden (gilt für die Szene,
##                                    die gerade gebaut ist; jede Region baut das Bergtal neu, mit ihrer Jahreszeit)
##   tal_punkt(x: float, z: float) -> Vector3   Tal-Koordinaten (bergtal.gd: x = Osten, z = Süden) -> Welt, auf dem Boden
##   rastplatz_pos() -> Vector3       der letzte Rastplatz (Welt)
##   zukunftsbild_ort(pos: Vector3, text: String)   ein Ort, den der Kristall als «Bild der Zukunft» zeigen darf (eine
##                                    Gefahr oder ein Weg; text z. B. T.t("Hinter den Felsen warten Wölfe.")) – gilt bis
##                                    zum Ende der Region
##   aufgabe_anmelden(id: String, text: String)   eine Aufgabe der Region (Rätsel, Schutzding …) – nach region_gestartet
##   aufgabe_erledigt(id: String)     die Aufgabe ist geschafft. Sind alle angemeldeten Aufgaben erledigt, leuchtet das
##                                    Jahreszeiten-Tor am Ende der Region; wer hindurchgeht, hat die Region geschafft
##                                    (ohne angemeldete Aufgaben ist das Tor gleich offen). region_fertig(id) geht auch direkt.
##   tor_pos() -> Vector3             wo das Jahreszeiten-Tor der Region steht (Welt)
##   signal region_gestartet(id)      eine Region beginnt (Szene fertig gebaut, Figur am ersten Rastplatz)
##   signal region_beendet(id)        die Region ist vorbei (geschafft oder verlassen): eigene Knoten der Region entfernen
##   signal einstieg_graben(pos)      der Einstieg: Maggie soll bei pos graben (S2 lässt den Hund hinlaufen und graben)
##   signal geschichte_beendet()      die Geschichte wurde verlassen oder ist fertig (alles aufräumen)
## Module: gibt es res://scripts/maggie_hund.gd, maggie_helfer.gd oder maggie_gefahr.gd, wird jedes beim Öffnen der Geschichte
## als Kind dieses Knotens angelegt; vorher werden (wenn vorhanden) die Variablen `main` und `story` gesetzt.
##
## TODO (S1): Kachel, Figur wählen, Einstieg, Regionen-Auswahl, Rastplätze/Speichern, Zukunftsbilder, Finale, Abspann.

const T = preload("res://scripts/i18n.gd")

signal region_gestartet(id: String)
signal region_beendet(id: String)
signal einstieg_graben(pos: Vector3)
signal geschichte_beendet()

const REGIONEN := ["herbst", "winter", "fruehling", "sommer"]
# the middle of every region (valley coordinates x, z of bergtal.gd)
const MITTE := {"herbst": Vector2(-640, -200), "winter": Vector2(590, 360), "fruehling": Vector2(-110, -330), "sommer": Vector2(-530, 480)}

var main
var running := false
var region := ""
var player: Node3D = null
var has_crystal := false
var _rest := Vector3.ZERO
var _safe_until := 0.0


func _bt():
	if main == null or main.scenes == null:
		return null
	return main.scenes.data.get("bergtal", null)


func tal_punkt(x: float, z: float) -> Vector3:
	var bt = _bt()
	if bt == null:
		return Vector3(x, 0.0, z)
	return bt.WG(x, z)


func region_mitte(id: String) -> Vector3:
	var m: Vector2 = MITTE.get(id, Vector2.ZERO)
	return tal_punkt(m.x, m.y)


func region_aktiv() -> String:
	return region if running else ""


func spieler() -> Node3D:
	return player if player != null and is_instance_valid(player) else null


func spieler_pos() -> Vector3:
	var p := spieler()
	return p.global_position if p != null else Vector3.ZERO


func kristall_bei_spieler() -> bool:
	return running and has_crystal


func geschuetzt() -> bool:
	return not running or main.now() < _safe_until


func rastplatz_pos() -> Vector3:
	return _rest


func erwischt(von: String) -> void:
	print("Maggie: erwischt von ", von)


func tipp(text: String) -> void:
	print("Maggie-Tipp: ", text)


func moveeye_sagt(text: String) -> void:
	print("MoveEye: ", text)


func zukunftsbild_ort(pos: Vector3, text: String) -> void:
	pass


func aufgabe_anmelden(id: String, text: String) -> void:
	pass


func aufgabe_erledigt(id: String) -> void:
	pass


func tor_pos() -> Vector3:
	return Vector3.ZERO


func region_fertig(id: String) -> void:
	region_beendet.emit(id)
