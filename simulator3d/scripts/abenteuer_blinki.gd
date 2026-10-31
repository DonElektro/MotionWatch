extends RefCounted
## Blinki als Helfer im Bergtal-Abenteuer (Paket A6, Daniel 31.10.2026). Blinki ist dieselbe Figur wie im Spielbereich
## (tour.gd BlinkiView, spielbereich.gd): gezeichnet, blinzelt, keine Musik.
##   * gibt die Tipps der Schwierigkeit: Leicht sofort, Mittel nach einer Weile oder auf Wunsch («Blinki um einen Tipp
##     bitten»), Schwer nie (die Tipps selbst kommen wie bisher aus abenteuer_raetsel.gd - Blinki sagt sie nur).
##   * kommentiert Funde (Fundstücke, Ausrüstung, Tagebuchseiten, Grossvaters Sachen, Abzeichen, Ziel, Gipfel) kurz -
##     hängt an bergtal_abenteuer._diary() (ein Einhänge-Punkt), sichtbar 25 s in der Spalte «Unterwegs».
## Kostet nichts Teures (ein gezeichnetes Control, nur solange es sichtbar ist).

const T = preload("res://scripts/i18n.gd")
const Tour = preload("res://scripts/tour.gd")

const SHOW_S := 25.0

var ab
var say := ""                  # the comment now
var say_t := -1000.0
var mood := "normal"
var n_comments := 0


func _init(a) -> void:
	ab = a


func on_diary(kind: String, title: String, text: String) -> void:
	"""a line of the diary: Blinki says something about finds"""
	var c := ""
	var m := "happy"
	match kind:
		"find":
			if title == T.t("Fundstück"):
				c = T.t("Schön, %s! Aber denk dran: alles im Rucksack wiegt etwas.") % text
			else:
				c = T.t("Ausrüstung gefunden! Die bleibt dir für alle Kapitel.")
		"a3_page":
			c = T.t("Eine Seite aus Grossvaters Tagebuch! Lies sie gut - sie zeigt dir den Weg.")
		"a3_item":
			c = T.t("Das gehörte deinem Grossvater: %s. Das hilft dir unterwegs.") % title
		"a3_badge":
			c = T.t("Juhu, ein neues Abzeichen!")
		"found":
			c = T.t("Geschafft, das Ziel! Jetzt brauchst du einen guten Platz für die Nacht.")
		"summit":
			c = T.t("Ganz oben! Schau, wie die Sonne über die Berge kommt.")
		"a1_foto":
			c = T.t("MoveEye hat ein Tier aufgenommen - am Morgen kannst du es anschauen.")
		"read":
			if title == T.t("Falscher Ort"):
				c = T.t("Hmm, hier ist nichts. Schau nochmals auf die Karte!")
				m = "point"
		"forgot":
			c = T.t("Oh je - das nächste Mal packen wir das ein.")
			m = "normal"
	if c == "":
		return
	say = c
	mood = m
	say_t = ab.main.now()
	n_comments += 1


func tip_now() -> String:
	"""the tip of the difficulty that is due now (Leicht: at once, Mittel: after a while / on request, Schwer: never)"""
	var r = ab.raetsel
	if r == null or ab.R.is_empty() or (ab.R.get("pending", {}) as Dictionary).is_empty():
		return ""
	var rr: Dictionary = r.RR()
	var tip := str(rr.get("tip", ""))
	if tip == "" or r.hilfe() == "schwer":
		return ""
	if ab.main.now() - float(rr.get("ask_t", 0.0)) >= r.TIP_S:
		return tip
	return ""


func paint(parent: Control, tip := "") -> bool:
	"""Blinki with a speech bubble: the tip (if given) or a fresh comment; false = nothing to say"""
	var txt := tip
	var m := "point"
	if txt == "":
		if ab.main.now() - say_t > SHOW_S or say == "":
			return false
		txt = say
		m = mood
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	parent.add_child(row)
	var fig = Tour.BlinkiView.new()
	fig.mood = m
	fig.t = ab.main.now()                         # (painted again often: the blinking goes on from the clock)
	fig.custom_minimum_size = Vector2(40, 46)
	fig.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	fig.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(fig)
	var pc := PanelContainer.new()
	pc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	pc.add_theme_stylebox_override("panel", ab._box(Color(0.12, 0.15, 0.2), Color(0.3, 0.42, 0.6), 1, 12, 8))
	row.add_child(pc)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	pc.add_child(v)
	v.add_child(ab._lab(T.t("Blinki"), 12, Color(0.55, 0.7, 0.95), false))
	v.add_child(ab._lab((T.t("Tipp: %s") % txt) if tip != "" else txt, 13, Color.WHITE))
	return true


func state() -> Dictionary:
	return {"say": say if ab.main.now() - say_t <= SHOW_S else "", "comments": n_comments, "tip": tip_now()}
