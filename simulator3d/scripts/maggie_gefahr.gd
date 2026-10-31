extends Node
## «Maggie und der Bergkristall» · Paket S3: böse Tiere, Schutzdinge, Grusel-Stimmung und Jahreszeit-Tipps
## (Daniel, 31.10.2026, Brief /tmp/claude-0/maggie_brief.md). Für Daniels Tochter (12): etwas gruselig, aber niemand wird
## verletzt, kein Blut, keine harten Schreckmomente. Alles eigen erfunden (nur lose inspiriert, keine Namen/Figuren aus Filmen).
##
## Die bösen Tiere wollen den Kristall. Jede Region (= Jahreszeit) hat ihre Tiere, deren Schwäche und ein Schutzding:
##   herbst    Wildschweine  – scheuen Wasser            → Wasserflasche (spritzen) / am Bach oder Fluss bist du sicher
##   winter    Wölfe         – scheuen Feuer und Licht   → Fackel (an = sie halten Abstand, schwenken = sie laufen weg)
##   fruehling Krähenschwarm – scheut Glockenklang       → Kuhglocke (läuten = der Schwarm fliegt davon)
##   sommer    Vipern        – fliehen vor Erschütterung → Wanderstock (stampfen = sie kriechen weg)
## Erwischt (Tier ganz nah, Schutzding nicht benutzt): story.erwischt(art) – S1 macht den kurzen Schreck und bringt dich zum
## letzten Rastplatz, der Kristall bleibt bei dir. Danach haben alle Tiere eine Pause und gehen zurück.
## Die Tiere jagen nur, wenn du den Kristall trägst (story.kristall_bei_spieler()).
##
## Anbindung an S1 (scripts/maggie_story.gd, Zweig real-maggie-rahmen; API-Stand 79aecaa): die Story legt dieses Modul beim
##   Öffnen als Kind an und setzt `main` und `story` (sonst sucht es main.maggie). Benutzt: region_aktiv(), spieler_pos(),
##   spieler(), kristall_bei_spieler(), geschuetzt(), erwischt(von), tipp(text), moveeye_sagt(text), region_mitte(id),
##   rastplatz_pos(), zukunftsbild_ort(pos, text), aufgabe_anmelden(id, text) / aufgabe_erledigt(id) (Aufgabe
##   "schutz_<region>": das Schutzding finden), Signale region_gestartet / region_beendet / geschichte_beendet.
##   Fehlt die Story (Tests über /control): ein eigener kleiner Ersatz (_Stub, freie Kamera = Spieler).
## Für S1/S2 (Maggie, liebe Tiere, Kristall-Zukunftsbilder, Speichern):
##   signal warnung(stufe, art, pos)    0 ruhig · 1 nah (Maggie knurrt) · 2 sehr nah (Maggie bellt) – S2 lässt Maggie reagieren
##   signal erwischt_von(art) · signal schutz_gefunden(id) · signal vertrieben(art)
##   benutze()                          das Schutzding benutzen (Taste B oder Knopf im Bild)
##   schutz_geben(id) / schutz_hat(id) / schutz_ort(region) -> Vector3   (Maggie kann das Schutzding holen / ausgraben)
##   ablenken(pos, secs)                der Fuchs lenkt die bösen Tiere ab: sie laufen dorthin
##   vertreiben()                       alle Tiere der Region laufen weg (z. B. Murmeltier-Pfiff, Steinbock trägt dich weg)
##   naechste_gefahr() -> {art, pos, dist}   (Murmeltier warnt, Eule zeigt den Weg)
##   zukunft_ziel() -> Vector3          wohin das Kristall-Zukunftsbild schauen soll (die nächste Gefahr vor dir)
##   pause(on)                          Tiere stehen still (Szenen, Zukunftsbild, Abspann)
##   sicher_hier(pos, r)                ein Rastplatz: dort jagt kein Tier
##   rastplatz()                        am Rastplatz: Fackel und Wasserflasche wieder voll
##   zustand() / lade(d) / neu()        für das Speichern am Rastplatz (S1); ohne S1: eigene Datei user://maggie_gefahr.json
## Lite: Quality.lite() – weniger Tiere und Vögel, keine Schatten der Fackel, weniger Geräusche gleichzeitig.
## Test / Fernsteuerung: /control {"action": "maggie_gefahr", "do": "info" | "start" (region) | "stop" | "use" |
##   "give" (id) | "put" (x, z) | "spawn" | "pause" (on) | "lure" (x, z)}.

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Quality = preload("res://scripts/quality.gd")
const Bergtal = preload("res://scripts/bergtal.gd")
const Actor = preload("res://scripts/actor.gd")

signal warnung(stufe: int, art: String, pos: Vector3)
signal erwischt_von(art: String)
signal schutz_gefunden(id: String)
signal vertrieben(art: String)

const FILE := "user://maggie_gefahr.json"
const SR := 16000
const REGIONS := ["herbst", "winter", "fruehling", "sommer"]

# Geschwindigkeiten: bewusst langsamer als echt, damit man rennend immer entkommt (Spieler gehen 1,5 m/s, rennen 3,45 m/s,
# actor.gd PLAYER_SPEED). Echte Werte zum Vergleich: Wildschwein bis 40 km/h (≈ 11 m/s), Wolf Trab 8–10 km/h, Sprint bis
# 50 km/h; Kreuzotter (Vipera berus) 50–65 cm, kriecht etwa 0,3–0,5 m/s; Rabenkrähe (Corvus corone) fliegt 30–50 km/h.
const TIER := {
	"herbst": {"art": "wildschwein", "kind": "boar", "n": 3, "n_lite": 2, "sinn": 26.0, "jagd": 2.6, "fang": 1.3, "ruhe": 0.6},
	"winter": {"art": "wolf", "kind": "wolf", "n": 3, "n_lite": 2, "sinn": 30.0, "jagd": 2.9, "fang": 1.4, "ruhe": 0.8},
	"fruehling": {"art": "kraehe", "kind": "crow", "n": 9, "n_lite": 5, "sinn": 32.0, "jagd": 3.4, "fang": 1.7, "ruhe": 2.0},
	"sommer": {"art": "viper", "kind": "viper", "n": 4, "n_lite": 3, "sinn": 9.0, "jagd": 0.4, "fang": 1.1, "ruhe": 0.0}}
const SCHUTZ := {"herbst": "wasserflasche", "winter": "fackel", "fruehling": "kuhglocke", "sommer": "wanderstock"}
const SCHUTZ_NAME := {"wasserflasche": "Wasserflasche", "fackel": "Fackel", "kuhglocke": "Kuhglocke", "wanderstock": "Wanderstock"}
const ART_NAME := {"wildschwein": "Wildschweine", "wolf": "Wölfe", "kraehe": "Krähen", "viper": "Schlangen"}
const WASSER_MAX := 4            # Spritzer pro Füllung (0,75-l-Flasche, je ein kräftiger Schwall)
const FACKEL_MAX := 150.0        # Sekunden Brennzeit (Pechfackel: echt 15–30 Min.; im Spiel kürzer, damit man haushalten muss)
const GNADE := 10.0              # nach «erwischt» / Regionsstart: so lange jagt kein Tier

# Tipps je Jahreszeit (kurz, einfach, für 12-Jährige). Werden der Reihe nach gezeigt, dazu passende Tipps bei Ereignissen.
const TIPPS := {
	"herbst": ["Wildschweine mögen kein Wasser. Bleib nah am Bach!",
		"Hörst du es im Laub rascheln und grunzen? Dann sind Wildschweine in der Nähe.",
		"Über den Fluss folgen dir die Wildschweine nicht.",
		"Mit der Wasserflasche kannst du Wildschweine verscheuchen. Drück B.",
		"Ist die Flasche leer? Am Bach füllst du sie wieder auf."],
	"winter": ["Wölfe fürchten Feuer und Licht.",
		"Mit brennender Fackel bleiben die Wölfe auf Abstand. Drück B zum Anzünden.",
		"Kommt ein Wolf zu nah? Schwenk die Fackel – drück nochmals B.",
		"Die Fackel brennt nicht ewig. Mach sie aus, wenn kein Wolf da ist.",
		"Im Dunkeln leuchten die Augen der Wölfe. So siehst du sie früh."],
	"fruehling": ["Krähen erschrecken vor lautem Glockenklang.",
		"Krähen lieben glänzende Dinge. Pass gut auf den Kristall auf!",
		"Kommt der Schwarm herunter? Läute die Kuhglocke – drück B.",
		"Unter Bäumen sehen dich die Krähen schlechter."],
	"sommer": ["Schlangen spüren Schritte im Boden.",
		"Auf warmen Steinen und im hohen Gras liegen gern Schlangen.",
		"Stampf mit dem Wanderstock auf den Boden (B). Dann kriechen die Schlangen weg.",
		"Geh lieber langsam. Maggie warnt dich, wenn eine Schlange nah ist."]}
const SUCH_TIPP := {"herbst": "Hier liegt irgendwo eine Wasserflasche. Maggie kann sie bestimmt finden.",
	"winter": "Hier liegt irgendwo eine Fackel. Ohne Licht wird es gefährlich.",
	"fruehling": "Hier hängt irgendwo eine Kuhglocke. Such sie, bevor die Krähen kommen.",
	"sommer": "Hier liegt irgendwo ein Wanderstock. Damit bist du sicherer im Gras."}
const GEFUNDEN := {"wasserflasche": "Du hast die Wasserflasche! Wildschweine verscheuchst du mit B.",
	"fackel": "Du hast die Fackel! Mit B zündest du sie an.",
	"kuhglocke": "Du hast die Kuhglocke! Mit B läutest du sie laut.",
	"wanderstock": "Du hast den Wanderstock! Mit B stampfst du auf den Boden."}
const AUFGABE := {"wasserflasche": "Finde die Wasserflasche", "fackel": "Finde die Fackel", "kuhglocke": "Finde die Kuhglocke",
	"wanderstock": "Finde den Wanderstock"}
# Kristall-Zukunftsbilder (S1 zeigt sie): wo die bösen Tiere warten, wo das Schutzding liegt
const ZUKUNFT := {"herbst": "Bei der Schlammsuhle warten Wildschweine.", "winter": "Hinter den Felsen warten Wölfe.",
	"fruehling": "Auf dem kahlen Baum sitzen die Krähen.", "sommer": "Auf den warmen Steinen liegen Schlangen."}
const ZUKUNFT_DING := {"wasserflasche": "Hier liegt eine Wasserflasche.", "fackel": "Hier liegt eine Fackel.",
	"kuhglocke": "Hier liegt eine Kuhglocke.", "wanderstock": "Hier liegt ein Wanderstock."}
# MoveEye ist einfach dabei: ein kurzer, kindgerechter Satz, was MoveEye jetzt machen würde (keine Technik-Wörter)
const MOVEEYE := {
	"herbst": ["MoveEye würde jetzt merken, dass sich im Laub etwas bewegt, und dir Bescheid geben.",
		"MoveEye würde die Wildschweine schon von weitem sehen und leise piepsen."],
	"winter": ["MoveEye würde die Wölfe auch im Dunkeln sehen, weil sie warm sind.",
		"MoveEye würde jetzt sein Licht anmachen. Das mögen Wölfe gar nicht."],
	"fruehling": ["MoveEye würde den Schwarm schon am Himmel entdecken und dich warnen.",
		"MoveEye würde jetzt laut piepsen. Das mögen Krähen nicht."],
	"sommer": ["MoveEye würde die Schlange auf dem warmen Stein entdecken, bevor du hinkommst.",
		"MoveEye würde dir sagen: Langsam, da vorne liegt etwas im Gras."],
	"erwischt": ["MoveEye hätte jetzt laut gepiepst, damit du schneller wegläufst.",
		"MoveEye würde sich merken, wo das Tier herkam, und dich nächstes Mal früher warnen."]}

var main
var story = null                  # scripts/maggie_story.gd (S1) – oder der eigene Ersatz _Stub
var eigene_datei := true          # S1 speichert selbst (zustand/lade): dann false setzen
var region := ""                  # die Region, die gerade läuft ("" = keine)
var paused := false

# Schutzdinge und ihr Zustand (bleibt über die Regionen)
var schutz := {}                  # id -> true
var wasser := WASSER_MAX
var fackel_zeit := FACKEL_MAX
var fackel_an := false
var _gefunden_ort := {}           # region -> Vector3 (wo das Schutzding liegt)

# Tiere
var _tiere: Array = []            # {n: Node3D, art, st, home, t, ...}
var _schwarm := {}                # Krähen: {birds: [...], c, st, home, t, hold}
var _dens: Array = []             # Vector3 – wo die Tiere wohnen
var _deko: Array = []             # Suhle, Krähenbaum, Steinplatten, Schutzding-Modell
var _pickup: Node3D = null
var _held: Node3D = null          # das Schutzding in der Hand (an der Kamera)
var _held_light: OmniLight3D = null
var _sicher: Array = []           # [pos, r] Rastplätze
var _gnade_bis := 0.0
var _lock_bis := 0.0
var _ablenk_pos := Vector3.ZERO
var _ablenk_bis := 0.0
var _last_pos := Vector3.ZERO
var _vel := Vector3.ZERO
var _stufe := 0
var _grusel := 0.0                # 0 … 1: wie nah die Gefahr ist (Nebel, dunkler Rand)
var _fog := 0.0

# Tipps / MoveEye
var _tipp_i := 0
var _tipp_next := 0.0
var _gesehen := false
var _me_i := 0
var _warn_tipp_bis := 0.0
var _ev_tipp := {}                # Ereignis-Tipps nur einmal pro Region

# Geräusche
var _snd := {}
var _amb: AudioStreamPlayer
var _ui_snd: AudioStreamPlayer
var _players: Array = []
var _amb_next := 0.0

# Bild
var _layer: CanvasLayer
var _vignette: TextureRect
var _flash: ColorRect
var _box: PanelContainer
var _box_lbl: Label
var _box_btn: Button
var _say_lbl: Label
var _say_bis := 0.0

var _poll := 0.0
var _tick_t := 0.0


static func _lite() -> bool:
	"""zentrale Abfrage «Lite?» (quality.gd, Engine-Meta «lite»)"""
	return Quality.lite()


static func hole(m) -> Node:
	"""die Gefahr-Ebene von main (wird beim ersten Mal angelegt, z. B. für /control-Tests ohne Story)"""
	var n = m.get_node_or_null("MaggieGefahr")
	var st = m.get("maggie")
	if n == null and st != null and st is Node:          # S1 legt das Modul als Kind der Story an
		for c in (st as Node).get_children():
			if c.get_script() != null and str(c.get_script().resource_path).ends_with("maggie_gefahr.gd"):
				n = c
	if n == null:
		n = load("res://scripts/maggie_gefahr.gd").new()
		n.name = "MaggieGefahr"
		n.main = m
		m.add_child(n)
	return n


func _ready() -> void:
	_load()
	_amb = AudioStreamPlayer.new()
	_amb.volume_db = -60.0
	add_child(_amb)
	_ui_snd = AudioStreamPlayer.new()
	add_child(_ui_snd)
	_connect_story()


# =======================================================================================================================
# die Story (S1) – oder der eigene Ersatz
# =======================================================================================================================
class _Stub extends RefCounted:
	## TODO verbinden mit maggie_story.gd: Ersatz, solange S1 (real-maggie-rahmen) noch nicht da ist, und für Tests
	var g
	var reg := ""
	var kristall := true

	func region_aktiv() -> String:
		return reg

	func spieler_pos() -> Vector3:
		var c: Camera3D = g.main.view_cam
		var p := c.global_position
		return Vector3(p.x, g.main.ground_y(p.x, p.z), p.z)

	func kristall_bei_spieler() -> bool:
		return kristall

	func erwischt(von: String) -> void:
		g._stub_erwischt(von)

	func tipp(text: String) -> void:
		g._say(text, 6.0)

	func moveeye_sagt(text: String) -> void:
		g._say(text, 6.0)

	func region_fertig(_id: String) -> void:
		reg = ""

	func region_mitte(id: String) -> Vector3:
		var bt = g._bt()
		var xz: Vector2 = {"herbst": Vector2(-640, -200), "winter": Vector2(590, 360), "fruehling": Vector2(-110, -330),
				"sommer": Vector2(-530, 480)}.get(id, Vector2.ZERO)     # wie maggie_story.gd MITTE (Tal-Koordinaten)
		if bt != null:
			return bt.WG(xz.x, xz.y)
		var f: Vector2 = {"herbst": Vector2(0, -40), "winter": Vector2(40, 0), "fruehling": Vector2(0, 40), "sommer": Vector2(-40, 0)}.get(id, Vector2.ZERO)
		return Vector3(f.x, g.main.ground_y(f.x, f.y), f.y)


var _stub: _Stub = null


func _connect_story() -> void:
	if story == null:
		for k in ["maggie_story", "maggie"]:
			var s = main.get(k) if main != null else null
			if s != null and s is Object and (s as Object).has_method("region_aktiv"):
				story = s
				break
	if story == null or not (story is Object):
		return
	var o := story as Object
	for pair in [["region_gestartet", "_on_region_gestartet"], ["region_beendet", "_on_region_beendet"],
			["geschichte_beendet", "_on_geschichte_beendet"]]:
		if o.has_signal(pair[0]):
			var cb := Callable(self, pair[1])
			if not o.is_connected(pair[0], cb):
				o.connect(pair[0], cb)


func _hat_signal_start() -> bool:
	"""die Story meldet den Start einer Region selbst (dann nicht schon beim Abfragen starten: die Szene ist evtl. noch nicht gebaut)"""
	return story != null and is_instance_valid(story) and (story as Object).has_signal("region_gestartet")


func _st():
	"""die Story oder der Ersatz"""
	if story != null and is_instance_valid(story):
		return story
	if _stub == null:
		_stub = _Stub.new()
		_stub.g = self
	return _stub


func _call(fn: String, args := []):
	var s = _st()
	if s != null and s.has_method(fn):
		return s.callv(fn, args)
	return null


func _region_aktiv() -> String:
	var r = _call("region_aktiv")
	return str(r) if r != null else ""


func _spieler() -> Vector3:
	var p = _call("spieler_pos")
	if p is Vector3:
		return p
	var c: Camera3D = main.view_cam
	return Vector3(c.global_position.x, main.ground_y(c.global_position.x, c.global_position.z), c.global_position.z)


func _kristall() -> bool:
	var k = _call("kristall_bei_spieler")
	return true if k == null else bool(k)


func _mitte(id: String) -> Vector3:
	var p = _call("region_mitte", [id])
	return p if p is Vector3 else Vector3.ZERO


func _tipp(text: String) -> void:
	_call("tipp", [T.t(text)])


func _moveeye(text: String) -> void:
	_call("moveeye_sagt", [T.t(text)])


func _bt():
	if main == null or main.get("scenes") == null:
		return null
	var bt = main.scenes.data.get("bergtal", null)
	return bt if bt != null and is_instance_valid(bt) and bt.tal != null and is_instance_valid(bt.tal) else null


func _on_region_gestartet(id: String) -> void:
	region = ""                                          # (eine neu gebaute Szene: alles neu anlegen, auch bei gleicher Region)
	start(id)


func _on_region_beendet(_id: String) -> void:
	stop()


func _on_geschichte_beendet() -> void:
	stop()


func _spieler_node() -> Node3D:
	var n = _call("spieler")
	return n if n is Node3D and is_instance_valid(n) else null


func _geschuetzt() -> bool:
	"""die Story sagt: gerade erwischt / Schreck / Karte offen / Pause – böse Tiere warten"""
	var g = _call("geschuetzt")
	return g != null and bool(g)


func _rast() -> Vector3:
	var r = _call("rastplatz_pos")
	return r if r is Vector3 and r != Vector3.ZERO else Vector3(INF, 0, INF)


# =======================================================================================================================
# Region starten / beenden
# =======================================================================================================================
func start(id: String) -> void:
	if not id in REGIONS:
		stop()
		return
	if region == id:
		return
	stop()
	region = id
	_make_sounds()
	_ensure_ui()
	var now := _now()
	_gnade_bis = now + GNADE * 1.5
	_tipp_i = 0
	_tipp_next = now + 8.0
	_gesehen = false
	_ev_tipp = {}
	_amb_next = now + 6.0
	_last_pos = _spieler()
	_build_region()
	_amb.stream = _snd["amb_" + id]
	_amb.volume_db = -26.0
	_amb.play()
	_layer.visible = true
	_update_box()
	if not schutz_hat(SCHUTZ[id]):
		_say_later(SUCH_TIPP[id], 3.0)


func stop() -> void:
	for t in _tiere:
		if is_instance_valid(t["n"]):
			(t["n"] as Node).queue_free()
	_tiere.clear()
	if not _schwarm.is_empty():
		for b in _schwarm["birds"]:
			if is_instance_valid(b["n"]):
				(b["n"] as Node).queue_free()
	_schwarm = {}
	for d in _deko:
		if is_instance_valid(d):
			(d as Node).queue_free()
	_deko.clear()
	_dens.clear()
	_pickup = null
	_drop_held()
	fackel_an = false
	region = ""
	_stufe = 0
	_grusel = 0.0
	if _amb != null:
		_amb.stop()
	if _layer != null:
		_layer.visible = false


func _build_region() -> void:
	var c := _mitte(region)
	var p := _spieler()
	var away := (c - p)
	away.y = 0.0
	var base_a := atan2(away.x, away.z) if away.length() > 2.0 else randf() * TAU
	# drei Verstecke 40 … 70 m um die Mitte, nicht direkt beim Spieler
	for i in range(3):
		var a := base_a + (i - 1) * 1.1 + randf_range(-0.3, 0.3)
		_dens.append(_boden(c + Vector3(sin(a), 0, cos(a)) * randf_range(40.0, 70.0)))
	var cfg: Dictionary = TIER[region]
	var n := int(cfg["n_lite"] if _lite() else cfg["n"])
	match region:
		"herbst":
			for d in _dens:
				_deko.append(_suhle(d))
			for i in range(n):
				_tier_neu("boar", _dens[i % _dens.size()] + Vector3(randf_range(-3, 3), 0, randf_range(-3, 3)))
		"winter":
			for d in _dens:
				_deko.append(_felsen(d))
			for i in range(n):
				_tier_neu("wolf", _dens[i % _dens.size()] + Vector3(randf_range(-3, 3), 0, randf_range(-3, 3)))
		"fruehling":
			_deko.append(_kraehenbaum(_dens[0]))
			_schwarm_neu(_dens[0], n)
		"sommer":
			for d in _dens:
				_deko.append(_steinplatte(d))
	for d in _dens:                                      # der Kristall darf die Verstecke als «Bild der Zukunft» zeigen
		_call("zukunftsbild_ort", [d, T.t(ZUKUNFT[region])])
	# das Schutzding: 12 … 20 m von der Mitte, auf der Seite zum Spieler hin (zu finden, aber nicht vor den Füssen)
	var sid: String = SCHUTZ[region]
	_call("aufgabe_anmelden", ["schutz_" + region, T.t(AUFGABE[sid])])
	if schutz_hat(sid):
		_call("aufgabe_erledigt", ["schutz_" + region])
	if not schutz_hat(sid):
		var a2 := base_a + PI + randf_range(-0.8, 0.8)
		var at := _boden(c + Vector3(sin(a2), 0, cos(a2)) * randf_range(12.0, 20.0))
		_gefunden_ort[region] = at
		_pickup = _ding_modell(sid)
		_pickup.position = at + Vector3(0, 0.05, 0)
		_root().add_child(_pickup)
		_deko.append(_pickup)
		_call("zukunftsbild_ort", [at, T.t(ZUKUNFT_DING[sid])])
		var glow := OmniLight3D.new()                     # ein leiser Schimmer, damit man es in der Dämmerung findet
		glow.light_color = Color(1.0, 0.92, 0.6)
		glow.light_energy = 0.6
		glow.omni_range = 2.5
		glow.shadow_enabled = false
		glow.position = Vector3(0, 0.4, 0)
		_pickup.add_child(glow)
	else:
		_halte(sid)


func _root() -> Node3D:
	return main.scene_parent if main.scene_parent != null else main


func _boden(p: Vector3) -> Vector3:
	return Vector3(p.x, main.ground_y(p.x, p.z), p.z)


func _now() -> float:
	return Time.get_ticks_msec() / 1000.0


# =======================================================================================================================
# Tiere am Boden (Wildschwein, Wolf) – Figuren aus actor.gd, von hier gesteuert (puppet: tiere.gd lässt sie in Ruhe)
# =======================================================================================================================
func _tier_neu(kind: String, at: Vector3) -> void:
	var v = Actor.new()
	main.visitors.add_child(v)
	var p := _boden(at)
	v.setup(main, kind, p, p + Vector3(1, 0, 0), 1.0)
	v.puppet = true
	v.set_meta("maggie_gefahr", true)
	v.set_night(main.is_dark())
	_tiere.append({"n": v, "kind": kind, "st": "ruhe", "home": p, "ziel": p, "t": 0.0, "bis": 0.0, "laut": _now() + randf_range(4, 12)})


func _tick_land(t: Dictionary, dt: float, now: float, sp: Vector3) -> void:
	var v: Node3D = t["n"]
	var cfg: Dictionary = TIER[region]
	var pos := v.global_position
	var to_p := sp - pos
	to_p.y = 0.0
	var d := to_p.length()
	var st: String = t["st"]
	var spd := 0.0
	var ziel: Vector3 = t["ziel"]
	var jagt_ok := _kristall() and now > _gnade_bis and not _ist_sicher(sp)
	if now < _ablenk_bis and st != "flucht":
		st = "abgelenkt"
	elif st == "abgelenkt":
		st = "zurueck"
	match st:
		"ruhe":
			spd = float(cfg["ruhe"])
			if pos.distance_to(ziel) < 1.0 or now > float(t["bis"]):
				var h: Vector3 = t["home"]
				ziel = _boden(h + Vector3(randf_range(-10, 10), 0, randf_range(-10, 10)))
				t["bis"] = now + randf_range(6.0, 14.0)
			if jagt_ok and d < float(cfg["sinn"]):
				st = "achtung"
				t["bis"] = now + 1.2                   # bleibt kurz stehen, schnaubt / knurrt: man hat Zeit zu reagieren
				_laut("snort" if t["kind"] == "boar" else "growl", pos, -14.0)
		"achtung":
			spd = 0.0
			ziel = sp
			if now > float(t["bis"]):
				st = "jagd"
				if not _gesehen:
					_gesehen = true
					_moveeye(MOVEEYE[region][0])
		"jagd":
			spd = float(cfg["jagd"])
			ziel = sp
			if not jagt_ok or d > float(cfg["sinn"]) * 1.7:
				st = "zurueck"
			elif t["kind"] == "boar" and _wasser_dist(sp) < 5.0:
				st = "zoegern"                           # Wasser: das Wildschwein bleibt stehen und dreht ab
				t["bis"] = now + 3.0
				_ev("wasser", "Gut gemacht! Am Wasser trauen sich die Wildschweine nicht weiter.")
			elif t["kind"] == "wolf" and fackel_an and d < 10.0:
				st = "kreisen"                           # Licht: der Wolf hält Abstand und schleicht im Kreis
				t["a"] = atan2(-to_p.x, -to_p.z)
				_ev("licht", "Die Wölfe bleiben weg vom Licht. Schwenk die Fackel mit B!")
			elif d < float(cfg["fang"]):
				_erwischt(str(cfg["art"]))
				return
			elif d < 6.0 and not _ev_tipp.has("nah"):
				_ev("nah", TIPPS[region][3] if region == "herbst" else (TIPPS[region][2]))
		"zoegern":
			spd = 0.0
			ziel = sp
			if _wasser_dist(pos) < 7.0:                   # nie näher ans Wasser
				ziel = pos - to_p.normalized() * 2.0
				spd = 0.8
			if now > float(t["bis"]):
				st = "zurueck"
				t["bis"] = now + 15.0
		"kreisen":
			spd = 1.2
			t["a"] = float(t["a"]) + dt * 0.25
			ziel = _boden(sp + Vector3(sin(float(t["a"])), 0, cos(float(t["a"]))) * 10.0)
			if not fackel_an:
				st = "jagd"
			elif not jagt_ok or d > 25.0:
				st = "zurueck"
		"flucht":
			spd = float(cfg["jagd"]) * 1.25
			ziel = pos - to_p.normalized() * 10.0
			if now > float(t["bis"]):
				st = "zurueck"
		"zurueck", "abgelenkt":
			spd = float(cfg["ruhe"]) * 2.0
			ziel = t["home"] if st == "zurueck" else _ablenk_pos
			if st == "zurueck" and pos.distance_to(ziel) < 2.0:
				st = "ruhe"
				t["bis"] = now + randf_range(15.0, 25.0)   # Pause, bevor es wieder jagt
			if st == "zurueck" and jagt_ok and d < float(cfg["sinn"]) * 0.6 and now > float(t["bis"]):
				st = "achtung"
				t["bis"] = now + 1.2
	t["st"] = st
	t["ziel"] = ziel
	_bewege(v, ziel, spd, dt)
	if now > float(t["laut"]):
		t["laut"] = now + randf_range(7.0, 16.0)
		if t["kind"] == "boar":
			_laut("grunt", pos, -18.0 if st == "ruhe" else -12.0)
		elif st != "ruhe" or randf() < 0.3:
			_laut("growl" if d < 20.0 else "howl", pos, -16.0 if d < 20.0 else -8.0)


func _bewege(v: Node3D, ziel: Vector3, spd: float, dt: float) -> void:
	var a = v
	var to := ziel - v.global_position
	to.y = 0.0
	var dist := to.length()
	var want := spd if dist > 0.3 else 0.0
	a.cur_speed = move_toward(float(a.cur_speed), want, dt * 4.0)
	if want > 0.0:
		a.speed = maxf(1.0, spd)
		var h := atan2(-to.x, -to.z)
		a.heading = lerp_angle(float(a.heading), h, clampf(dt * 5.0, 0.0, 1.0))
		v.rotation.y = float(a.heading)
	var fwd := Vector3(-sin(float(a.heading)), 0, -cos(float(a.heading)))
	var p := v.position + fwd * minf(float(a.cur_speed) * dt, dist)
	if main.get("avoid_on"):
		var q: Vector2 = main.keep_out(Vector2(p.x, p.z), 0.4, false)
		p.x = q.x
		p.z = q.y
	p.y = main.ground_y(p.x, p.z)
	v.position = p


# =======================================================================================================================
# der Krähenschwarm (eigene einfache Vögel: Körper + zwei Flügel, die schlagen)
# =======================================================================================================================
func _vogel() -> Node3D:
	# Rabenkrähe: 45–50 cm lang, Spannweite 85–100 cm, ganz schwarz
	var b := Node3D.new()
	var body := MeshInstance3D.new()
	var cm := CapsuleMesh.new()
	cm.radius = 0.07
	cm.height = 0.42
	body.mesh = cm
	body.rotation.x = PI / 2
	body.material_override = main.mat(Color(0.05, 0.05, 0.06))
	b.add_child(body)
	var head := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.06
	sm.height = 0.12
	head.mesh = sm
	head.position = Vector3(0, 0.03, -0.22)
	head.material_override = main.mat(Color(0.06, 0.06, 0.07))
	b.add_child(head)
	for sd in [-1.0, 1.0]:
		var piv := Node3D.new()
		piv.name = "wl" if sd < 0 else "wr"
		b.add_child(piv)
		var w := MeshInstance3D.new()
		w.mesh = main.box(0.42, 0.015, 0.16)
		w.position = Vector3(sd * 0.22, 0, 0)
		w.material_override = main.mat(Color(0.04, 0.04, 0.05))
		piv.add_child(w)
	var th := MeshInstance3D.new()                      # warm im Wärmebild (Vögel: Körper ≈ 38–40 °C, Gefieder kühler)
	th.mesh = cm
	th.rotation.x = PI / 2
	th.layers = 2
	th.material_override = main.tmat_fixed(30.0)
	b.add_child(th)
	return b


func _schwarm_neu(home: Vector3, n: int) -> void:
	var birds := []
	for i in range(n):
		var b := _vogel()
		_root().add_child(b)
		var off := Vector3(randf_range(-1, 1), randf_range(-0.4, 0.4), randf_range(-1, 1)).normalized() * randf_range(1.5, 4.5)
		b.position = home + Vector3(0, 14, 0) + off
		birds.append({"n": b, "off": off, "ph": randf() * TAU, "w": randf_range(0.6, 1.2)})
	_schwarm = {"birds": birds, "c": home + Vector3(0, 14, 0), "st": "kreisen", "home": home, "t": 0.0, "bis": 0.0, "hold": 0.0,
			"laut": _now() + 5.0}


func _tick_schwarm(dt: float, now: float, sp: Vector3) -> void:
	var s := _schwarm
	var c: Vector3 = s["c"]
	var home: Vector3 = s["home"]
	var cfg: Dictionary = TIER["fruehling"]
	var head := sp + Vector3(0, 1.4, 0)
	var flat := Vector2(head.x - c.x, head.z - c.z).length()
	var jagt_ok := _kristall() and now > _gnade_bis and not _ist_sicher(sp) and not _unter_baeumen(sp)
	var st: String = s["st"]
	var ziel := c
	var spd := 2.0
	var r := 3.5
	if now < _ablenk_bis and st != "flucht":
		st = "kreisen"
		home = _ablenk_pos
	match st:
		"kreisen":
			s["t"] = float(s["t"]) + dt * 0.35
			ziel = home + Vector3(sin(float(s["t"])) * 10.0, 14.0, cos(float(s["t"])) * 10.0)
			if jagt_ok and Vector2(sp.x - home.x, sp.z - home.z).length() < float(cfg["sinn"]) and now > float(s["bis"]):
				st = "anflug"
				_laut("caw", c, -6.0)
				if not _gesehen:
					_gesehen = true
					_moveeye(MOVEEYE["fruehling"][0])
		"anflug":
			ziel = head + Vector3(0, 6.0, 0)
			spd = float(cfg["jagd"])
			if not jagt_ok or flat > float(cfg["sinn"]) * 1.8:
				st = "heim"
			elif flat < 6.0:
				st = "stoss"
				s["hold"] = 0.0
				_laut("caw", c, -4.0)
				_ev("nah", "Der Schwarm kommt herunter! Läute die Kuhglocke – drück B.")
		"stoss":
			ziel = head
			spd = float(cfg["jagd"]) * 0.9
			r = 1.6
			if c.distance_to(head) < float(cfg["fang"]):
				s["hold"] = float(s["hold"]) + dt
				if float(s["hold"]) > 1.2:               # sie zupfen am Rucksack – kurzer Schreck, sie bekommen den Kristall nicht
					_erwischt("kraehe")
					return
			if not jagt_ok:
				st = "heim"
		"flucht":
			ziel = c + (c - head).normalized() * 8.0 + Vector3(0, 3.0, 0)
			ziel.y = minf(ziel.y, head.y + 30.0)
			spd = 6.0
			r = 6.0
			if now > float(s["bis"]):
				st = "heim"
		"heim":
			ziel = home + Vector3(0, 14, 0)
			spd = 3.0
			if c.distance_to(ziel) < 3.0:
				st = "kreisen"
				s["bis"] = now + randf_range(12.0, 20.0)
	s["st"] = st
	c = c.move_toward(ziel, spd * dt)
	var gy: float = main.ground_y(c.x, c.z)
	c.y = maxf(c.y, gy + 1.0)
	s["c"] = c
	for b in s["birds"]:
		var n: Node3D = b["n"]
		if not is_instance_valid(n):
			continue
		b["ph"] = float(b["ph"]) + dt * float(b["w"])
		var o: Vector3 = (b["off"] as Vector3).rotated(Vector3.UP, float(b["ph"])) * (r / 3.0)
		var want := c + o + Vector3(0, sin(float(b["ph"]) * 2.0) * 0.4, 0)
		var old := n.position
		n.position = old.lerp(want, clampf(dt * 3.0, 0.0, 1.0))
		var mv := n.position - old
		if mv.length() > 0.001:
			n.rotation.y = atan2(-mv.x, -mv.z)
		var flap := sin(now * (14.0 if st in ["flucht", "anflug", "stoss"] else 9.0) + float(b["ph"]) * 3.0) * 0.7
		var wl: Node3D = n.get_node("wl")
		var wr: Node3D = n.get_node("wr")
		wl.rotation.z = flap
		wr.rotation.z = -flap
	if now > float(s["laut"]):
		s["laut"] = now + randf_range(5.0, 11.0)
		_laut("caw" if randf() < 0.7 else "flap", c, -10.0 if st == "kreisen" else -5.0)


# =======================================================================================================================
# Vipern (Kreuzotter: grau-braun mit dunklem Zickzack-Band, 50–65 cm; hier 0,7 m, damit man sie im Gras überhaupt sieht)
# =======================================================================================================================
func _schlange() -> Node3D:
	var s := Node3D.new()
	var segs := []
	var nseg := 8 if _lite() else 12
	for i in range(nseg):
		var m := MeshInstance3D.new()
		var sm := SphereMesh.new()
		var k := 1.0 - absf(float(i) - nseg * 0.3) / nseg
		sm.radius = 0.028 * (0.6 + 0.6 * k)
		sm.height = sm.radius * 2.0
		sm.radial_segments = 8
		sm.rings = 4
		m.mesh = sm
		m.material_override = main.mat(Color(0.18, 0.14, 0.1) if i % 2 == 0 else Color(0.42, 0.36, 0.28))
		m.position = Vector3(0, 0.03, i * 0.7 / nseg)
		s.add_child(m)
		segs.append(m)
	var eye := MeshInstance3D.new()                    # ein kleiner heller Fleck am Kopf, damit man die Richtung erkennt
	var es := SphereMesh.new()
	es.radius = 0.012
	es.height = 0.024
	eye.mesh = es
	eye.material_override = main.mat(Color(0.75, 0.35, 0.15))
	eye.position = Vector3(0, 0.05, -0.02)
	s.add_child(eye)
	s.set_meta("segs", segs)
	s.set_meta("eye", eye)
	return s


func _viper_neu(at: Vector3) -> void:
	var n := _schlange()
	_root().add_child(n)
	n.position = _boden(at)
	n.rotation.y = randf() * TAU
	_tiere.append({"n": n, "kind": "viper", "st": "liegen", "home": n.position, "ziel": n.position, "t": randf() * 10.0, "bis": 0.0,
			"laut": _now() + randf_range(6, 14)})


func _tick_viper(t: Dictionary, dt: float, now: float, sp: Vector3) -> void:
	var n: Node3D = t["n"]
	var to_p := sp - n.global_position
	to_p.y = 0.0
	var d := to_p.length()
	var st: String = t["st"]
	t["t"] = float(t["t"]) + dt
	var raise := 0.0
	var wig := 0.6
	match st:
		"liegen":
			if _kristall() and now > _gnade_bis and d < 1.8 and not _ist_sicher(sp):
				st = "zischen"                           # warnt zuerst: zischt und hebt den Kopf
				t["bis"] = now + 1.3
				_laut("hiss", n.global_position, -16.0)
				_ev("zischen", "Eine Schlange! Bleib stehen und stampf mit dem Wanderstock (B).")
		"zischen":
			raise = 0.08
			wig = 0.2
			if d > 2.6:
				st = "liegen"
			elif now > float(t["bis"]):
				if d < float(TIER["sommer"]["fang"]):
					_erwischt("viper")
					return
				st = "liegen"
		"flucht":
			wig = 3.0
			var away := -to_p.normalized() if d > 0.01 else Vector3(1, 0, 0)
			n.rotation.y = lerp_angle(n.rotation.y, atan2(away.x, away.z), clampf(dt * 4.0, 0.0, 1.0))
			var fw := Vector3(sin(n.rotation.y), 0, cos(n.rotation.y))
			n.position = _boden(n.position + fw * 0.45 * dt)
			n.position.y -= clampf((now - float(t["bis"]) + 4.0) * 0.02, 0.0, 0.08)   # verschwindet im Gras
			if now > float(t["bis"]):
				t["weg"] = true
	t["st"] = st
	var segs: Array = n.get_meta("segs")
	for i in range(segs.size()):
		var m: MeshInstance3D = segs[i]
		var k := float(i) / segs.size()
		m.position.x = sin(float(t["t"]) * wig * 2.0 - k * 7.0) * 0.06 * (0.3 + k)
		m.position.y = 0.03 + raise * maxf(0.0, 1.0 - k * 4.0)
	if now > float(t["laut"]) and d < 12.0:
		t["laut"] = now + randf_range(8.0, 16.0)
		_laut("rustle", n.global_position, -22.0)


func _viper_nachschub(sp: Vector3) -> void:
	"""Sommer: Schlangen liegen auf dem Weg vor dir (und bei den warmen Steinplatten); weit weg verschwinden sie"""
	var cfg: Dictionary = TIER["sommer"]
	var nmax := int(cfg["n_lite"] if _lite() else cfg["n"])
	_tiere = _tiere.filter(func(t): return is_instance_valid(t["n"]) and not t.get("weg", false) \
			and (t["n"] as Node3D).global_position.distance_to(sp) < 70.0 or _frei(t))
	if _tiere.size() >= nmax or randf() > 0.25:
		return
	var fwd := _vel
	fwd.y = 0.0
	if fwd.length() < 0.2:
		fwd = -(main.view_cam as Camera3D).global_transform.basis.z
		fwd.y = 0.0
	fwd = fwd.normalized() if fwd.length() > 0.01 else Vector3(0, 0, -1)
	var at := sp + fwd * randf_range(9.0, 16.0) + fwd.cross(Vector3.UP) * randf_range(-2.0, 2.0)
	if randf() < 0.35 and not _dens.is_empty():
		at = _dens[randi() % _dens.size()] + Vector3(randf_range(-1, 1), 0, randf_range(-1, 1))
	_viper_neu(at)


func _frei(t: Dictionary) -> bool:
	"""(beim Aufräumen) ein ungültiger Eintrag: Knoten freigeben"""
	if is_instance_valid(t["n"]):
		(t["n"] as Node).queue_free()
	return false


# =======================================================================================================================
# jedes Bild
# =======================================================================================================================
func _process(dt: float) -> void:
	if main == null:
		return
	_poll -= dt
	if _poll <= 0.0:
		_poll = 0.5
		if story == null:
			_connect_story()
		var r := _region_aktiv()
		if r != region:
			if r in REGIONS and not _hat_signal_start():
				start(r)
			elif region != "":
				stop()
	if region == "":
		return
	var now := _now()
	if _flash != null and _flash.color.a > 0.0:
		_flash.color.a = maxf(0.0, _flash.color.a - dt * 1.5)
	if _say_lbl != null:
		_say_lbl.visible = now < _say_bis
	_tick_fog(dt)
	if paused:
		_bewege_alle_still(dt)
		return
	var sp := _spieler()
	if dt > 0.0:
		_vel = _vel.lerp((sp - _last_pos) / dt, clampf(dt * 3.0, 0.0, 1.0))
	_last_pos = sp
	_tick_schutz(dt, now, sp)
	for t in _tiere.duplicate():
		if region == "":
			return
		if not is_instance_valid(t["n"]):
			continue
		if t["kind"] == "viper":
			_tick_viper(t, dt, now, sp)
		else:
			_tick_land(t, dt, now, sp)
	if region == "":
		return
	if not _schwarm.is_empty():
		_tick_schwarm(dt, now, sp)
	_tick_t -= dt
	if _tick_t <= 0.0:
		_tick_t = 0.5
		_tick_warnung(sp)
		_tick_nachschub(sp, now)
		_tick_tipps(now)
		_update_box()
	if now > _amb_next:
		_amb_next = now + randf_range(12.0, 24.0)
		_ambient(sp)


func _bewege_alle_still(dt: float) -> void:
	for t in _tiere:
		if is_instance_valid(t["n"]) and t["kind"] != "viper":
			var a = t["n"]
			a.cur_speed = move_toward(float(a.cur_speed), 0.0, dt * 4.0)


func _tick_nachschub(sp: Vector3, now: float) -> void:
	if region == "sommer":
		_viper_nachschub(sp)
		return
	# die Verstecke wandern mit: ist seit langem kein Tier in der Nähe, zieht ein Versteck 50 … 70 m vor den Spieler
	if _dens.is_empty() or randf() > 0.03:
		return
	var nahe := false
	for d in _dens:
		if (d as Vector3).distance_to(sp) < 90.0:
			nahe = true
	if nahe:
		return
	var fwd := _vel
	fwd.y = 0.0
	fwd = fwd.normalized() if fwd.length() > 0.3 else Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)).normalized()
	var nd := _boden(sp + fwd.rotated(Vector3.UP, randf_range(-0.7, 0.7)) * randf_range(50.0, 70.0))
	var far_i := 0
	for i in range(_dens.size()):
		if (_dens[i] as Vector3).distance_to(sp) > (_dens[far_i] as Vector3).distance_to(sp):
			far_i = i
	var old: Vector3 = _dens[far_i]
	_dens[far_i] = nd
	for t in _tiere:
		if (t["home"] as Vector3).distance_to(old) < 15.0 and t["st"] == "ruhe" and is_instance_valid(t["n"]):
			t["home"] = nd
			(t["n"] as Node3D).position = _boden(nd + Vector3(randf_range(-3, 3), 0, randf_range(-3, 3)))
	if not _schwarm.is_empty() and (_schwarm["home"] as Vector3).distance_to(old) < 15.0 and _schwarm["st"] == "kreisen":
		_schwarm["home"] = nd
		_schwarm["c"] = nd + Vector3(0, 14, 0)
	if now > _gnade_bis:
		_laut("crack", nd, -14.0)


func _tick_warnung(sp: Vector3) -> void:
	var ng := naechste_gefahr()
	var d: float = ng["dist"]
	var aktiv := false
	for t in _tiere:
		if t.get("st", "") in ["achtung", "jagd", "kreisen", "zischen", "zoegern"]:
			aktiv = true
	if not _schwarm.is_empty() and _schwarm["st"] in ["anflug", "stoss"]:
		aktiv = true
	var lim1 := 25.0 if region != "sommer" else 8.0
	var lim2 := 12.0 if region != "sommer" else 3.5
	var s := 0
	if d < lim2 or (aktiv and d < lim1):
		s = 2
	elif d < lim1:
		s = 1
	_grusel = clampf(1.0 - d / (lim1 * 1.6), 0.0, 1.0) * (1.0 if _kristall() else 0.5)
	if _vignette != null:
		_vignette.modulate.a = 0.25 + 0.55 * _grusel
	if s != _stufe:
		var up := s > _stufe
		_stufe = s
		warnung.emit(s, str(ng["art"]), ng["pos"])
		# Maggie warnt – das Bellen/Knurren macht S2 (Signal «warnung»); hört niemand zu, sagt es der Text
		if up and get_signal_connection_list("warnung").is_empty() and _now() > _warn_tipp_bis:
			_warn_tipp_bis = _now() + 15.0
			_say(T.t("Maggie bellt laut – ganz nah ist etwas!") if s == 2 else T.t("Maggie knurrt leise. Da ist etwas …"), 3.5)


func _tick_tipps(now: float) -> void:
	if now < _tipp_next:
		return
	_tipp_next = now + randf_range(70.0, 110.0)             # ≈ alle 1,5 Min. ein Tipp (25–30 Min. pro Region)
	var list: Array = TIPPS[region]
	_tipp(list[_tipp_i % list.size()])
	_tipp_i += 1
	if _tipp_i % 3 == 0:
		_me_i += 1
		_moveeye(MOVEEYE[region][_me_i % MOVEEYE[region].size()])


func _ev(key: String, text: String) -> void:
	"""ein Tipp zu einem Ereignis – nur einmal pro Region"""
	if _ev_tipp.has(key):
		return
	_ev_tipp[key] = true
	_tipp(text)
	_tipp_next = maxf(_tipp_next, _now() + 30.0)


func _tick_fog(dt: float) -> void:
	# Grusel-Stimmung: Nebel je Jahreszeit (Herbst dicht, Sommer kaum), dichter, wenn Gefahr nah ist
	var base: float = {"herbst": 0.018, "winter": 0.012, "fruehling": 0.008, "sommer": 0.004}.get(region, 0.0)
	_fog = move_toward(_fog, base + 0.012 * _grusel, dt * 0.004)
	if main.env != null:
		main.env.fog_density = maxf(main.env.fog_density, _fog)


func _ambient(sp: Vector3) -> void:
	"""unheimliche, aber harmlose Geräusche rundherum (20 … 40 m): Knacken, Rascheln, ferne Rufe"""
	var a := randf() * TAU
	var p := _boden(sp + Vector3(sin(a), 0, cos(a)) * randf_range(20.0, 40.0))
	var k: Array = {"herbst": ["rustle", "crack", "grunt"], "winter": ["howl", "crack", "wind"],
			"fruehling": ["caw", "flap", "crack"], "sommer": ["rustle", "hiss", "crack"]}[region]
	_laut(k[randi() % k.size()], p, -16.0)


# =======================================================================================================================
# Schutzdinge
# =======================================================================================================================
func schutz_hat(id: String) -> bool:
	return bool(schutz.get(id, false))


func schutz_ort(r: String) -> Vector3:
	return _gefunden_ort.get(r, _mitte(r))


func schutz_geben(id: String) -> void:
	"""das Schutzding bekommen (gefunden, oder Maggie hat es geholt / ausgegraben)"""
	if not id in SCHUTZ_NAME or schutz_hat(id):
		return
	schutz[id] = true
	if id == "wasserflasche":
		wasser = WASSER_MAX
	if id == "fackel":
		fackel_zeit = FACKEL_MAX
	if _pickup != null and is_instance_valid(_pickup) and SCHUTZ.get(region, "") == id:
		_pickup.queue_free()
		_pickup = null
	_tipp(GEFUNDEN[id])
	_ui_play("pickup", -10.0)
	schutz_gefunden.emit(id)
	if SCHUTZ.get(region, "") == id:
		_halte(id)
		_call("aufgabe_erledigt", ["schutz_" + region])
	_save()
	_update_box()


func _tick_schutz(dt: float, now: float, sp: Vector3) -> void:
	if _pickup != null and is_instance_valid(_pickup):
		_pickup.rotation.y += dt * 0.8
		if Vector2(_pickup.global_position.x - sp.x, _pickup.global_position.z - sp.z).length() < 1.8:
			schutz_geben(SCHUTZ[region])
	if region == "herbst" and schutz_hat("wasserflasche") and wasser < WASSER_MAX and _wasser_dist(sp) < 3.0:
		wasser = WASSER_MAX
		_say(T.t("Flasche am Bach aufgefüllt."), 3.0)
		_ui_play("splash", -14.0)
	if _rast().distance_to(sp) < 4.0 and ((schutz_hat("wasserflasche") and wasser < WASSER_MAX) \
			or (schutz_hat("fackel") and fackel_zeit < FACKEL_MAX - 1.0 and not fackel_an)):
		rastplatz()
		_say(T.t("Am Rastplatz: Flasche und Fackel sind wieder voll."), 3.0)
	if fackel_an:
		fackel_zeit -= dt
		if fackel_zeit <= 0.0:
			fackel_zeit = 0.0
			_fackel(false)
			_tipp("Die Fackel ist aus. Am Rastplatz bekommst du eine neue.")
	elif schutz_hat("fackel"):
		fackel_zeit = minf(FACKEL_MAX, fackel_zeit + dt * 0.25)    # glimmt nach (etwas Pech bleibt warm)
	if _held_light != null:
		_held_light.light_energy = (2.2 + 0.4 * sin(now * 13.0) + 0.25 * sin(now * 7.3)) if fackel_an else 0.0


func benutze() -> Dictionary:
	"""das Schutzding der Region benutzen (Taste B / Knopf)"""
	if region == "" or paused:
		return {"ok": false, "error": "keine_region"}
	var id: String = SCHUTZ[region]
	if not schutz_hat(id):
		_say(T.t("Du hast hier noch kein Schutzding. Such zuerst danach!"), 3.0)
		return {"ok": false, "error": "fehlt"}
	var sp := _spieler()
	var n := 0
	match id:
		"wasserflasche":
			if wasser <= 0:
				_say(T.t("Die Flasche ist leer. Füll sie am Bach auf."), 3.0)
				return {"ok": false, "error": "leer"}
			wasser -= 1
			_laut("splash", sp, -12.0)
			_spritzer(sp)
			n = _verscheuche("boar", sp, 8.0, 12.0)
		"fackel":
			if not fackel_an:
				if fackel_zeit < 3.0:
					_say(T.t("Die Fackel ist abgebrannt. Am Rastplatz bekommst du eine neue."), 3.0)
					return {"ok": false, "error": "leer"}
				_fackel(true)
				return {"ok": true, "fackel": true}
			_laut("whoosh", sp, -12.0)
			if _held != null:
				var tw := create_tween()
				tw.tween_property(_held, "rotation:z", 0.9, 0.15)
				tw.tween_property(_held, "rotation:z", -0.6, 0.2)
				tw.tween_property(_held, "rotation:z", 0.0, 0.2)
			fackel_zeit = maxf(0.0, fackel_zeit - 4.0)
			n = _verscheuche("wolf", sp, 14.0, 15.0)
		"kuhglocke":
			_laut("bell", sp, -4.0)
			_ui_play("bell", -8.0)
			if not _schwarm.is_empty() and (_schwarm["c"] as Vector3).distance_to(sp) < 40.0 and _schwarm["st"] != "flucht":
				_schwarm["st"] = "flucht"
				_schwarm["bis"] = _now() + 20.0
				n = (_schwarm["birds"] as Array).size()
				_laut("flap", _schwarm["c"], -6.0)
				vertrieben.emit("kraehe")
			if _held != null:
				var tw2 := create_tween()
				tw2.tween_property(_held, "rotation:x", 0.5, 0.1)
				tw2.tween_property(_held, "rotation:x", -0.4, 0.15)
				tw2.tween_property(_held, "rotation:x", 0.0, 0.15)
		"wanderstock":
			_laut("stamp", sp, -10.0)
			if _held != null:
				var tw3 := create_tween()
				tw3.tween_property(_held, "position:y", _held.position.y - 0.12, 0.08)
				tw3.tween_property(_held, "position:y", _held.position.y, 0.2)
			for t in _tiere:
				if t["kind"] == "viper" and is_instance_valid(t["n"]) and t["st"] != "flucht" \
						and (t["n"] as Node3D).global_position.distance_to(sp) < 6.0:
					t["st"] = "flucht"
					t["bis"] = _now() + 5.0
					n += 1
			if n > 0:
				vertrieben.emit("viper")
	if n > 0:
		_ev("vertrieben", "Super! Sie sind weg. Aber sie kommen vielleicht wieder.")
	_update_box()
	return {"ok": true, "vertrieben": n}


func _verscheuche(kind: String, sp: Vector3, r: float, secs: float) -> int:
	var n := 0
	for t in _tiere:
		if t["kind"] == kind and is_instance_valid(t["n"]) and (t["n"] as Node3D).global_position.distance_to(sp) < r:
			t["st"] = "flucht"
			t["bis"] = _now() + secs
			n += 1
	if n > 0:
		vertrieben.emit(str(TIER[region]["art"]))
		_laut("snort" if kind == "boar" else "growl", sp, -14.0)
	return n


func _fackel(on: bool) -> void:
	fackel_an = on
	if _held != null and _held.has_meta("flame"):
		(_held.get_meta("flame") as Node3D).visible = on
	if on:
		_laut("whoosh", _spieler(), -16.0)
	_update_box()


func rastplatz() -> void:
	"""am Rastplatz: Wasserflasche und Fackel wieder voll"""
	if schutz_hat("wasserflasche"):
		wasser = WASSER_MAX
	if schutz_hat("fackel"):
		fackel_zeit = FACKEL_MAX
	_update_box()


func _spritzer(sp: Vector3) -> void:
	var fwd := -(main.view_cam as Camera3D).global_transform.basis.z
	for i in range(6 if _lite() else 12):
		var m := MeshInstance3D.new()
		var s := SphereMesh.new()
		s.radius = 0.04
		s.height = 0.08
		m.mesh = s
		var mt := StandardMaterial3D.new()
		mt.albedo_color = Color(0.6, 0.8, 1.0, 0.7)
		mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.material_override = mt
		_root().add_child(m)
		var a := sp + Vector3(0, 1.2, 0) + fwd * 0.4
		m.global_position = a
		var b := a + (fwd + Vector3(randf_range(-0.3, 0.3), randf_range(0.1, 0.4), randf_range(-0.3, 0.3))) * randf_range(2.5, 4.0)
		b.y = main.ground_y(b.x, b.z)
		var tw := m.create_tween()
		tw.tween_property(m, "global_position", b, randf_range(0.4, 0.7))
		tw.tween_callback(m.queue_free)


func _ding_modell(id: String) -> Node3D:
	var n := Node3D.new()
	match id:
		"wasserflasche":
			_teil(n, _zyl(0.04, 0.04, 0.24), Vector3(0, 0.12, 0), Color(0.2, 0.45, 0.85))
			_teil(n, _zyl(0.02, 0.025, 0.04), Vector3(0, 0.26, 0), Color(0.15, 0.15, 0.17))
		"fackel":
			_teil(n, _zyl(0.018, 0.022, 0.6), Vector3(0, 0.3, 0), Color(0.42, 0.28, 0.14))
			_teil(n, _zyl(0.035, 0.03, 0.1), Vector3(0, 0.62, 0), Color(0.12, 0.1, 0.08))
			var fl := MeshInstance3D.new()
			var fs := SphereMesh.new()
			fs.radius = 0.05
			fs.height = 0.16
			fl.mesh = fs
			var fm := StandardMaterial3D.new()
			fm.albedo_color = Color(1.0, 0.6, 0.15)
			fm.emission_enabled = true
			fm.emission = Color(1.0, 0.55, 0.12)
			fm.emission_energy_multiplier = 4.0
			fm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			fl.material_override = fm
			fl.position = Vector3(0, 0.72, 0)
			fl.visible = false
			n.add_child(fl)
			n.set_meta("flame", fl)
		"kuhglocke":
			_teil(n, _zyl(0.05, 0.08, 0.14), Vector3(0, 0.1, 0), Color(0.72, 0.56, 0.22))
			_teil(n, main.box(0.03, 0.12, 0.012), Vector3(0, 0.22, 0), Color(0.45, 0.12, 0.1))
		"wanderstock":
			_teil(n, _zyl(0.014, 0.012, 1.25), Vector3(0, 0.62, 0), Color(0.5, 0.36, 0.2))
			_teil(n, _zyl(0.02, 0.02, 0.1), Vector3(0, 1.2, 0), Color(0.2, 0.15, 0.1))
	return n


func _teil(parent: Node3D, mesh: Mesh, p: Vector3, col: Color) -> MeshInstance3D:
	var m := MeshInstance3D.new()
	m.mesh = mesh
	m.position = p
	m.material_override = main.mat(col)
	parent.add_child(m)
	return m


func _zyl(top: float, bot: float, h: float) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = top
	c.bottom_radius = bot
	c.height = h
	c.radial_segments = 10
	return c


func _halte(id: String) -> void:
	"""das Schutzding in der Hand: unten rechts im Bild (an der Kamera); die Fackel mit eigenem Licht"""
	_drop_held()
	_held = _ding_modell(id)
	var fig := _spieler_node()
	if fig != null:                                     # die Spielfigur trägt es in der rechten Hand
		fig.add_child(_held)
		_held.position = {"wasserflasche": Vector3(0.3, 0.75, -0.12), "fackel": Vector3(0.32, 0.55, -0.25),
				"kuhglocke": Vector3(0.3, 0.75, -0.12), "wanderstock": Vector3(0.34, 0.0, -0.3)}[id]
	elif main.view_cam != null:                         # ohne Figur (freie Ansicht): unten rechts im Bild
		(main.view_cam as Camera3D).add_child(_held)
		_held.position = {"wasserflasche": Vector3(0.28, -0.32, -0.55), "fackel": Vector3(0.3, -0.62, -0.6),
				"kuhglocke": Vector3(0.28, -0.3, -0.55), "wanderstock": Vector3(0.32, -1.0, -0.65)}[id]
		for mi in _held.find_children("*", "MeshInstance3D", true, false):
			(mi as MeshInstance3D).layers = 128          # main.HELPER_LAYER: nur das Fenster sieht es, nie eine Kamera von MoveEye
			(mi as MeshInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	else:
		_held.queue_free()
		_held = null
		return
	if id == "fackel":
		_held_light = OmniLight3D.new()
		_held_light.light_color = Color(1.0, 0.68, 0.35)  # Flammenlicht ≈ 1900 K
		_held_light.omni_range = 11.0
		_held_light.light_energy = 0.0
		_held_light.shadow_enabled = not _lite()
		_held_light.position = Vector3(0, 0.8, 0)
		_held.add_child(_held_light)
		(_held.get_meta("flame") as Node3D).visible = fackel_an


func _drop_held() -> void:
	if _held != null and is_instance_valid(_held):
		_held.queue_free()
	_held = null
	_held_light = null


# =======================================================================================================================
# Deko der Verstecke (dezent): Suhle, kahler Krähenbaum, warme Steinplatten
# =======================================================================================================================
func _suhle(p: Vector3) -> Node3D:
	var n := Node3D.new()
	var m := MeshInstance3D.new()
	var c := _zyl(2.2, 2.4, 0.04)
	c.radial_segments = 16
	m.mesh = c
	m.material_override = main.mat(Color(0.2, 0.15, 0.1))
	n.add_child(m)
	_root().add_child(n)
	n.global_position = p + Vector3(0, 0.01, 0)
	return n


func _kraehenbaum(p: Vector3) -> Node3D:
	var n := Node3D.new()
	_teil(n, _zyl(0.12, 0.22, 7.0), Vector3(0, 3.5, 0), Color(0.18, 0.16, 0.14))
	for i in range(3 if _lite() else 6):
		var a := i * 1.7
		var br := _teil(n, _zyl(0.03, 0.07, 2.4), Vector3(sin(a) * 0.6, 4.5 + i * 0.4, cos(a) * 0.6), Color(0.17, 0.15, 0.13))
		br.rotation = Vector3(cos(a) * 0.9, 0, -sin(a) * 0.9)
	_root().add_child(n)
	n.global_position = p
	return n


func _felsen(p: Vector3) -> Node3D:
	"""Winter: ein paar grosse Felsblöcke – dahinter warten die Wölfe"""
	var n := Node3D.new()
	for i in range(3):
		var h := randf_range(1.2, 2.2)
		var m := _teil(n, main.box(randf_range(1.2, 2.0), h, randf_range(1.0, 1.6)), Vector3(randf_range(-2.0, 2.0), h * 0.45, randf_range(-2.0, 2.0)),
				Color(0.42, 0.42, 0.44))
		m.rotation = Vector3(randf_range(-0.15, 0.15), randf() * PI, randf_range(-0.15, 0.15))
	_root().add_child(n)
	n.global_position = p + Vector3(3.0, 0, 0)
	return n


func _steinplatte(p: Vector3) -> Node3D:
	var n := Node3D.new()
	for i in range(3):
		var m := _teil(n, main.box(randf_range(0.8, 1.4), 0.18, randf_range(0.6, 1.1)), Vector3(randf_range(-1.2, 1.2), 0.09, randf_range(-1.2, 1.2)),
				Color(0.55, 0.52, 0.48))
		m.rotation.y = randf() * PI
	_root().add_child(n)
	n.global_position = p
	return n


# =======================================================================================================================
# erwischt / sicher
# =======================================================================================================================
func _erwischt(art: String) -> void:
	var now := _now()
	if now < _lock_bis:
		return
	_lock_bis = now + 4.0
	_gnade_bis = now + GNADE
	fackel_an = false if not schutz_hat("fackel") else fackel_an
	for t in _tiere:                                       # alle gehen zurück und machen eine Pause
		if t["kind"] == "viper":
			t["st"] = "flucht"
			t["bis"] = now + 3.0
		else:
			t["st"] = "zurueck"
			t["bis"] = now + 20.0
	if not _schwarm.is_empty():
		_schwarm["st"] = "flucht"
		_schwarm["bis"] = now + 10.0
	erwischt_von.emit(art)
	_call("erwischt", [art])
	_moveeye(MOVEEYE["erwischt"][randi() % MOVEEYE["erwischt"].size()])


func _stub_erwischt(_von: String) -> void:
	"""(ohne Story) kurzer, sanfter Schreck: das Bild wird kurz dunkel, dann zurück zur Mitte der Region"""
	if _flash != null:
		_flash.color = Color(0.02, 0.02, 0.05, 0.85)
	_ui_play("schreck", -12.0)
	_say(T.t("Huch! Das war knapp. Zurück zum Rastplatz – der Kristall ist noch bei dir."), 4.0)
	var c := _mitte(region)
	_versetze(c)
	_last_pos = c
	rastplatz()


func _versetze(p: Vector3) -> void:
	"""(Ersatz / Tests) die Figur – oder die freie Kamera – an einen Ort stellen"""
	var fig := _spieler_node()
	if fig != null:
		fig.global_position = _boden(p)
	else:
		(main.view_cam as Camera3D).global_position = _boden(p) + Vector3(0, 1.7, 0)


func sicher_hier(pos: Vector3, r := 12.0) -> void:
	_sicher.append([pos, r])


func _ist_sicher(p: Vector3) -> bool:
	"""am Rastplatz (10 m), an einem gemeldeten sicheren Ort oder solange die Story schützt, jagt kein Tier"""
	if _geschuetzt() or _rast().distance_to(p) < 10.0:
		return true
	for s in _sicher:
		if (s[0] as Vector3).distance_to(p) < float(s[1]):
			return true
	return false


func _unter_baeumen(wp: Vector3) -> bool:
	"""Frühling: im Wald sehen dich die Krähen schlechter (bergtal.gd forest_k: Anteil Wald am Ort)"""
	var bt = _bt()
	if bt == null:
		return false
	var q: Vector3 = bt.V(wp)
	return Bergtal.forest_k(q.x, q.z, Bergtal.H(q.x, q.z)) > 0.55


func _wasser_dist(wp: Vector3) -> float:
	"""Abstand zum nächsten Wasser (Bach, Fluss, See) in m – Bergtal (bergtal.gd STREAMS / LAKES); sonst weit weg"""
	var bt = _bt()
	if bt == null:
		return 999.0
	var q: Vector3 = bt.V(wp)
	var p := Vector2(q.x, q.z)
	var best := 999.0
	for s in Bergtal.STREAMS:
		var pts: Array = s[0]
		for i in range(pts.size() - 1):
			var se: Vector2 = Bergtal._seg_t(p, pts[i], pts[i + 1])
			best = minf(best, se.y - float(s[1]) * 0.5)
	for lk in Bergtal.LAKES:
		var e := Bergtal._ell(p, lk)
		best = minf(best, maxf(0.0, (e - 1.0)) * minf(float(lk[1]), float(lk[2])))
	return maxf(best, 0.0)


# =======================================================================================================================
# für S1 / S2
# =======================================================================================================================
func naechste_gefahr() -> Dictionary:
	var sp := _spieler()
	var best := {"art": "", "pos": Vector3.ZERO, "dist": 9999.0}
	for t in _tiere:
		if not is_instance_valid(t["n"]) or t.get("st", "") == "flucht":
			continue
		var d := (t["n"] as Node3D).global_position.distance_to(sp)
		if d < float(best["dist"]):
			best = {"art": str(TIER[region]["art"]) if region != "" else "", "pos": (t["n"] as Node3D).global_position, "dist": d}
	if not _schwarm.is_empty() and _schwarm["st"] != "flucht":
		var c: Vector3 = _schwarm["c"]
		var d2 := c.distance_to(sp + Vector3(0, 1.4, 0))
		if d2 < float(best["dist"]):
			best = {"art": "kraehe", "pos": c, "dist": d2}
	return best


func zukunft_ziel() -> Vector3:
	var ng := naechste_gefahr()
	if float(ng["dist"]) < 200.0:
		return ng["pos"]
	return _dens[0] if not _dens.is_empty() else _mitte(region)


func ablenken(pos: Vector3, secs := 12.0) -> void:
	_ablenk_pos = _boden(pos)
	_ablenk_bis = _now() + secs


func vertreiben() -> void:
	var now := _now()
	for t in _tiere:
		t["st"] = "flucht"
		t["bis"] = now + 12.0
	if not _schwarm.is_empty():
		_schwarm["st"] = "flucht"
		_schwarm["bis"] = now + 15.0
	if region != "":
		vertrieben.emit(str(TIER[region]["art"]))


func pause(on: bool) -> void:
	paused = on
	if _amb != null:
		_amb.stream_paused = on


# =======================================================================================================================
# speichern (S1 ruft zustand/lade; ohne S1 die eigene Datei)
# =======================================================================================================================
func zustand() -> Dictionary:
	return {"schutz": schutz.duplicate(), "wasser": wasser, "fackel": snappedf(fackel_zeit, 0.1)}


func lade(d: Dictionary) -> void:
	schutz = (d.get("schutz", {}) as Dictionary).duplicate() if d.get("schutz", {}) is Dictionary else {}
	wasser = clampi(int(d.get("wasser", WASSER_MAX)), 0, WASSER_MAX)
	fackel_zeit = clampf(float(d.get("fackel", FACKEL_MAX)), 0.0, FACKEL_MAX)
	_update_box()


func neu() -> void:
	schutz = {}
	wasser = WASSER_MAX
	fackel_zeit = FACKEL_MAX
	_gefunden_ort = {}
	_save()


func _load() -> void:
	if not FileAccess.file_exists(FILE):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
	if d is Dictionary:
		lade(d)


func _save() -> void:
	if not eigene_datei:
		return
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(zustand()))


# =======================================================================================================================
# Bild: dunkler Rand (Grusel), Schutzding-Kasten unten links, kurze Sätze
# =======================================================================================================================
func _ensure_ui() -> void:
	if _layer != null:
		return
	_layer = CanvasLayer.new()
	_layer.layer = 55
	_layer.visible = false
	add_child(_layer)
	var ui := Control.new()
	ui.set_anchors_preset(Control.PRESET_FULL_RECT)
	ui.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.theme = UI.theme()
	_layer.add_child(ui)
	_vignette = TextureRect.new()                         # dunkler Rand: je näher die Gefahr, desto dunkler
	var g := Gradient.new()
	g.set_color(0, Color(0, 0, 0, 0))
	g.set_color(1, Color(0.0, 0.0, 0.03, 0.85))
	g.add_point(0.55, Color(0, 0, 0, 0))
	var gt := GradientTexture2D.new()
	gt.gradient = g
	gt.fill = GradientTexture2D.FILL_RADIAL
	gt.fill_from = Vector2(0.5, 0.5)
	gt.fill_to = Vector2(1.05, 1.05)
	gt.width = 128
	gt.height = 128
	_vignette.texture = gt
	_vignette.stretch_mode = TextureRect.STRETCH_SCALE
	_vignette.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_vignette.set_anchors_preset(Control.PRESET_FULL_RECT)
	_vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_vignette.modulate.a = 0.25
	ui.add_child(_vignette)
	_flash = ColorRect.new()
	_flash.color = Color(0, 0, 0, 0)
	_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui.add_child(_flash)
	_box = PanelContainer.new()
	_box.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.88), UI.LINE, 10, 8))
	_box.anchor_top = 1.0
	_box.anchor_bottom = 1.0
	_box.offset_left = 16
	_box.offset_top = -64
	_box.offset_bottom = -16
	ui.add_child(_box)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	_box.add_child(row)
	_box_lbl = Label.new()
	_box_lbl.add_theme_font_size_override("font_size", 15)
	row.add_child(_box_lbl)
	_box_btn = Button.new()
	_box_btn.focus_mode = Control.FOCUS_NONE
	_box_btn.pressed.connect(func(): benutze())
	row.add_child(_box_btn)
	_say_lbl = Label.new()
	_say_lbl.anchor_left = 0.5
	_say_lbl.anchor_right = 0.5
	_say_lbl.anchor_top = 1.0
	_say_lbl.anchor_bottom = 1.0
	_say_lbl.offset_left = -330
	_say_lbl.offset_right = 330
	_say_lbl.offset_top = -130
	_say_lbl.offset_bottom = -80
	_say_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_say_lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_say_lbl.add_theme_font_size_override("font_size", 17)
	_say_lbl.add_theme_color_override("font_outline_color", Color.BLACK)
	_say_lbl.add_theme_constant_override("outline_size", 5)
	_say_lbl.visible = false
	ui.add_child(_say_lbl)


func _update_box() -> void:
	if _box == null or region == "":
		return
	var id: String = SCHUTZ[region]
	var nm := T.t(SCHUTZ_NAME[id])
	if not schutz_hat(id):
		_box_lbl.text = T.t("Schutzding: {ding} – noch nicht gefunden", {"ding": nm})
		_box_btn.visible = false
		return
	_box_btn.visible = true
	match id:
		"wasserflasche":
			_box_lbl.text = T.t("{ding} · noch {n} Spritzer", {"ding": nm, "n": wasser})
			_box_btn.text = T.t("Spritzen (B)")
		"fackel":
			_box_lbl.text = T.t("{ding} · brennt noch {s} s", {"ding": nm, "s": int(fackel_zeit)}) if fackel_an \
					else T.t("{ding} · aus ({s} s übrig)", {"ding": nm, "s": int(fackel_zeit)})
			_box_btn.text = T.t("Schwenken (B)") if fackel_an else T.t("Anzünden (B)")
		"kuhglocke":
			_box_lbl.text = nm
			_box_btn.text = T.t("Läuten (B)")
		"wanderstock":
			_box_lbl.text = nm
			_box_btn.text = T.t("Stampfen (B)")


func _say(text: String, secs := 4.0) -> void:
	_ensure_ui()
	_say_lbl.text = text
	_say_bis = _now() + secs
	_say_lbl.visible = true


func _say_later(text: String, secs: float) -> void:
	get_tree().create_timer(secs).timeout.connect(func():
		if region != "":
			_tipp(text))


func _unhandled_input(ev: InputEvent) -> void:
	if region == "" or not (ev is InputEventKey):
		return
	var k := ev as InputEventKey
	if k.pressed and not k.echo and k.keycode == KEY_B:
		benutze()
		get_viewport().set_input_as_handled()


# =======================================================================================================================
# Geräusche (selbst erzeugt, 16 kHz): Grunzen, Schnauben, Heulen, Knurren, Krächzen, Flügel, Zischen, Rascheln, Knacken,
# Glocke, Spritzer, Fackel-Wusch, Stampfen, sanfter Schreck; dazu je Jahreszeit eine leise Schleife (Wind, Grillen)
# =======================================================================================================================
func _laut(kind: String, pos: Vector3, db1m: float) -> void:
	if not _snd.has(kind):
		return
	var w: AudioStreamWAV = _snd[kind]
	main.add_sound(db1m, pos, w.get_length())               # MoveEyes Mikrofon hört es auch
	_players = _players.filter(func(p): return is_instance_valid(p))
	if _players.size() >= (2 if _lite() else 5):
		return
	var p := AudioStreamPlayer3D.new()
	p.stream = w
	p.unit_size = 5.0
	p.max_distance = 160.0
	p.max_db = 0.0
	p.volume_db = clampf(db1m + 14.0, -24.0, 4.0)
	p.attenuation_filter_cutoff_hz = 3000.0
	p.attenuation_filter_db = -12.0
	_root().add_child(p)
	p.global_position = pos + Vector3(0, 0.6, 0)
	p.finished.connect(p.queue_free)
	_players.append(p)
	p.play()


func _ui_play(kind: String, db: float) -> void:
	if _ui_snd == null or not _snd.has(kind):
		return
	_ui_snd.stream = _snd[kind]
	_ui_snd.volume_db = db
	_ui_snd.play()


func _make_sounds() -> void:
	if not _snd.is_empty():
		return
	var t0 := Time.get_ticks_msec()
	_snd["grunt"] = _wav(_s_grunt())
	_snd["snort"] = _wav(_s_noise(0.35, 0.5, 0.06, 0.3))
	_snd["howl"] = _wav(_s_howl())
	_snd["growl"] = _wav(_s_growl())
	_snd["caw"] = _wav(_s_caw())
	_snd["flap"] = _wav(_s_flap())
	_snd["hiss"] = _wav(_s_noise(0.9, 0.95, 0.3, 0.35))
	_snd["rustle"] = _wav(_s_rustle())
	_snd["crack"] = _wav(_s_crack())
	_snd["bell"] = _wav(_s_bell())
	_snd["splash"] = _wav(_s_noise(0.6, 0.6, 0.12, 0.6))
	_snd["whoosh"] = _wav(_s_whoosh())
	_snd["stamp"] = _wav(_s_stamp())
	_snd["pickup"] = _wav(_s_chime())
	_snd["schreck"] = _wav(_s_schreck())
	_snd["wind"] = _wav(_s_wind(3.0, 0.5))
	_snd["amb_herbst"] = _wav(_s_wind(6.0, 0.35), true)
	_snd["amb_winter"] = _wav(_s_wind(6.0, 0.7), true)
	_snd["amb_fruehling"] = _wav(_s_wind(6.0, 0.25), true)
	_snd["amb_sommer"] = _wav(_s_crickets(), true)
	print("Maggie-Gefahr: Geräusche erzeugt (%d ms)" % (Time.get_ticks_msec() - t0))


func _wav(buf: PackedFloat32Array, loop := false) -> AudioStreamWAV:
	var pcm := PackedByteArray()
	pcm.resize(buf.size() * 2)
	for i in range(buf.size()):
		pcm.encode_s16(i * 2, int(clampf(buf[i], -1.0, 1.0) * 30000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = SR
	w.data = pcm
	if loop:
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_end = buf.size()
	return w


func _buf(secs: float) -> PackedFloat32Array:
	var b := PackedFloat32Array()
	b.resize(int(secs * SR))
	return b


func _s_noise(secs: float, hp: float, att: float, amp: float) -> PackedFloat32Array:
	"""Rauschen mit Hochpass-Anteil hp (0 … 1), Einschwingen att s – Schnauben, Zischen, Spritzer"""
	var b := _buf(secs)
	var prev := 0.0
	var lp := 0.0
	for i in range(b.size()):
		var t := float(i) / SR
		var n := randf() * 2.0 - 1.0
		var h := n - prev
		prev = n
		lp += (n - lp) * 0.2
		var env := minf(1.0, t / att) * minf(1.0, (secs - t) / (secs * 0.5))
		b[i] = (h * hp + lp * (1.0 - hp)) * env * amp
	return b


func _s_grunt() -> PackedFloat32Array:
	# Wildschwein: kurze, tiefe Grunzer (Grundton ≈ 100–200 Hz, rau)
	var b := _buf(1.1)
	for st in [0.0, 0.38, 0.7]:
		var o := int(st * SR)
		var f := randf_range(95.0, 130.0)
		for i in range(int(0.22 * SR)):
			var t := float(i) / SR
			var env := sin(PI * t / 0.22)
			var v := (fposmod(t * f, 1.0) * 2.0 - 1.0) * 0.4 + (randf() * 2.0 - 1.0) * 0.25
			if o + i < b.size():
				b[o + i] += v * env * 0.5
	var lp := 0.0
	for i in range(b.size()):
		lp += (b[i] - lp) * 0.18
		b[i] = lp * 1.6
	return b


func _s_howl() -> PackedFloat32Array:
	# Wolf: langes Heulen, Grundton ≈ 300–600 Hz, gleitet hoch und sinkt; weit weg und leise
	var b := _buf(3.0)
	var ph := 0.0
	for i in range(b.size()):
		var t := float(i) / SR
		var f := 380.0 + 170.0 * sin(PI * minf(t / 2.4, 1.0)) + 6.0 * sin(TAU * 5.0 * t)
		ph += TAU * f / SR
		var env := minf(1.0, t / 0.4) * clampf((3.0 - t) / 0.8, 0.0, 1.0)
		b[i] = (sin(ph) * 0.8 + sin(ph * 2.0) * 0.15) * env * 0.35
	return b


func _s_growl() -> PackedFloat32Array:
	var b := _buf(0.9)
	var lp := 0.0
	for i in range(b.size()):
		var t := float(i) / SR
		var am := 0.6 + 0.4 * sin(TAU * 28.0 * t)
		lp += (randf() * 2.0 - 1.0 - lp) * 0.08
		var env := minf(1.0, t / 0.1) * minf(1.0, (0.9 - t) / 0.3)
		b[i] = (lp * 2.5 + sin(TAU * 85.0 * t) * 0.2) * am * env * 0.45
	return b


func _s_caw() -> PackedFloat32Array:
	# Krähe: rau «kraa kraa», Grundton ≈ 500–800 Hz
	var b := _buf(0.8)
	for st in [0.0, 0.42]:
		var o := int(st * SR)
		var f := randf_range(560.0, 680.0)
		for i in range(int(0.28 * SR)):
			var t := float(i) / SR
			var env := sin(PI * t / 0.28)
			var saw := fposmod(t * (f - 120.0 * t), 1.0) * 2.0 - 1.0
			var v := saw * 0.5 + (randf() * 2.0 - 1.0) * 0.2
			if o + i < b.size():
				b[o + i] += v * env * 0.4
	return b


func _s_flap() -> PackedFloat32Array:
	var b := _buf(0.9)
	var lp := 0.0
	for i in range(b.size()):
		var t := float(i) / SR
		lp += (randf() * 2.0 - 1.0 - lp) * 0.3
		var beat := pow(maxf(0.0, sin(TAU * 7.0 * t)), 6.0)
		b[i] = lp * beat * minf(1.0, (0.9 - t) / 0.4) * 0.7
	return b


func _s_rustle() -> PackedFloat32Array:
	var b := _buf(1.3)
	for i in range(b.size()):
		var t := float(i) / SR
		var crackle := (randf() * 2.0 - 1.0) * (1.0 if randf() < 0.06 else 0.15)
		b[i] = crackle * (0.5 + 0.5 * sin(TAU * 2.0 * t)) * minf(1.0, (1.3 - t) / 0.4) * 0.5
	return b


func _s_crack() -> PackedFloat32Array:
	var b := _buf(0.3)
	var prev := 0.0
	for i in range(b.size()):
		var t := float(i) / SR
		var n := randf() * 2.0 - 1.0
		var h := n - prev
		prev = n
		b[i] = h * exp(-t / 0.018) * 0.8 + (h * exp(-(t - 0.06) / 0.012) * 0.5 if t > 0.06 else 0.0)
	return b


func _s_bell() -> PackedFloat32Array:
	# Kuhglocke: unharmonische Teiltöne, ein paar Schläge kurz hintereinander (laut und hell)
	var b := _buf(1.8)
	var parts := [[620.0, 1.0, 0.7], [930.0, 0.6, 0.5], [1250.0, 0.45, 0.4], [1710.0, 0.3, 0.3]]
	for st in [[0.0, 1.0], [0.22, 0.8], [0.45, 0.9], [0.7, 0.6]]:
		var o := int(float(st[0]) * SR)
		for i in range(b.size() - o):
			var t := float(i) / SR
			var v := (randf() * 2.0 - 1.0) * exp(-t / 0.006) * 0.4
			for p in parts:
				v += sin(TAU * float(p[0]) * t) * float(p[1]) * exp(-t / float(p[2]))
			b[o + i] += v * 0.16 * float(st[1])
	return b


func _s_whoosh() -> PackedFloat32Array:
	var b := _buf(0.5)
	var lp := 0.0
	for i in range(b.size()):
		var t := float(i) / SR
		var k := 0.05 + 0.4 * sin(PI * t / 0.5)
		lp += (randf() * 2.0 - 1.0 - lp) * k
		b[i] = lp * sin(PI * t / 0.5) * 0.8
	return b


func _s_stamp() -> PackedFloat32Array:
	var b := _buf(0.3)
	for i in range(b.size()):
		var t := float(i) / SR
		b[i] = (sin(TAU * 55.0 * t) * 0.9 + (randf() * 2.0 - 1.0) * 0.3 * exp(-t / 0.01)) * exp(-t / 0.07)
	return b


func _s_chime() -> PackedFloat32Array:
	var b := _buf(0.8)
	for i in range(b.size()):
		var t := float(i) / SR
		var v := sin(TAU * 880.0 * t) * exp(-t / 0.3)
		if t > 0.12:
			v += sin(TAU * 1320.0 * (t - 0.12)) * exp(-(t - 0.12) / 0.3)
		b[i] = v * 0.3
	return b


func _s_schreck() -> PackedFloat32Array:
	# sanfter Schreck: ein tiefer, kurzer «Wusch» nach unten – kein lauter Knall
	var b := _buf(0.9)
	var ph := 0.0
	for i in range(b.size()):
		var t := float(i) / SR
		ph += TAU * lerpf(320.0, 90.0, t / 0.9) / SR
		b[i] = sin(ph) * exp(-t / 0.4) * 0.45
	return b


func _s_wind(secs: float, amt: float) -> PackedFloat32Array:
	"""Wind, nahtlose Schleife (das Ende wird in den Anfang überblendet)"""
	var n := int(secs * SR)
	var x := int(0.8 * SR)
	var raw := PackedFloat32Array()
	raw.resize(n + x)
	var br := 0.0
	for i in range(raw.size()):
		var t := float(i) / SR
		br = br * 0.993 + (randf() * 2.0 - 1.0) * 0.035
		raw[i] = br * (0.6 + 0.4 * sin(TAU * 0.31 * t) * sin(TAU * 0.17 * t)) * 2.4 * amt
	var b := PackedFloat32Array()
	b.resize(n)
	for i in range(n):
		b[i] = raw[i]
	for i in range(x):
		var k := float(i) / float(x)
		b[i] = raw[i] * k + raw[n + i] * (1.0 - k)
	return b


func _s_crickets() -> PackedFloat32Array:
	# Sommerabend: Grillen (Feldgrille zirpt ≈ 4–5 kHz, 3–4 Silben pro Zirpen) + leiser Wind; Schleife 4 s
	var b := _s_wind(4.0, 0.2)
	for c in range(3):
		var f := 4300.0 + c * 260.0
		var rate := 1.6 + c * 0.35
		var off := randf()
		for i in range(b.size()):
			var t := float(i) / SR
			var ph := fposmod(t * rate + off, 1.0)
			if ph < 0.18:
				var syl := maxf(0.0, sin(PI * fposmod(ph * 22.0, 1.0)))
				b[i] += sin(TAU * f * t) * syl * 0.035
	return b


# =======================================================================================================================
# /control {"action": "maggie_gefahr", "do": …}
# =======================================================================================================================
static func control(m, d: Dictionary) -> Dictionary:
	var g = hole(m)
	return g.command(d)


func command(d: Dictionary) -> Dictionary:
	var op := str(d.get("do", "info"))
	match op:
		"start":
			var r := str(d.get("region", "herbst"))
			var s = _st()
			if s is _Stub:
				(s as _Stub).reg = r
				(s as _Stub).kristall = bool(d.get("kristall", true))
			start(r)
			if bool(d.get("now", false)):
				_gnade_bis = 0.0
		"stop":
			var s2 = _st()
			if s2 is _Stub:
				(s2 as _Stub).reg = ""
			stop()
		"use":
			return benutze()
		"give":
			schutz_geben(str(d.get("id", SCHUTZ.get(region, ""))))
		"neu":
			neu()
		"pause":
			pause(bool(d.get("on", true)))
		"lure":
			ablenken(Vector3(float(d.get("x", 0)), 0, float(d.get("z", 0))), float(d.get("secs", 12)))
		"put":
			var x := float(d.get("x", 0))
			var z := float(d.get("z", 0))
			if d.has("rel"):                                     # relativ zur Mitte der Region
				var c := _mitte(region)
				x += c.x
				z += c.z
			_versetze(Vector3(x, 0, z))
			if d.has("look_x") and _spieler_node() == null:
				(main.view_cam as Camera3D).look_at(Vector3(float(d["look_x"]), main.ground_y(float(d["look_x"]), float(d["look_z"])) + 0.5, float(d["look_z"])))
		"near":                                                   # Tests: die Tiere dicht vor den Spieler holen
			var sp := _spieler()
			var fwd := -(main.view_cam as Camera3D).global_transform.basis.z
			fwd.y = 0.0
			fwd = fwd.normalized()
			var i := 0
			for t in _tiere:
				if is_instance_valid(t["n"]):
					var p := _boden(sp + fwd * (float(d.get("dist", 8.0)) + i * 1.5) + fwd.cross(Vector3.UP) * (i - 1) * 1.5)
					(t["n"] as Node3D).global_position = p
					t["home"] = p
					i += 1
			if not _schwarm.is_empty():
				_schwarm["c"] = sp + fwd * float(d.get("dist", 8.0)) + Vector3(0, 5, 0)
				_schwarm["home"] = sp + fwd * float(d.get("dist", 8.0))
		"spawn":
			if region == "sommer":
				_viper_neu(_spieler() + Vector3(0, 0, -float(d.get("dist", 3.0))))
			elif region in ["herbst", "winter"]:
				_tier_neu(str(TIER[region]["kind"]), _spieler() + Vector3(0, 0, -float(d.get("dist", 15.0))))
	var tiere := []
	for t in _tiere:
		if is_instance_valid(t["n"]):
			tiere.append({"kind": t["kind"], "st": t["st"], "d": snappedf((t["n"] as Node3D).global_position.distance_to(_spieler()), 0.1)})
	var ng := naechste_gefahr()
	return {"ok": true, "region": region, "story": "stub" if _st() is _Stub else "maggie_story", "tiere": tiere,
			"schwarm": "" if _schwarm.is_empty() else str(_schwarm["st"]), "schutz": schutz, "wasser": wasser,
			"fackel": snappedf(fackel_zeit, 0.1), "fackel_an": fackel_an, "stufe": _stufe, "grusel": snappedf(_grusel, 0.01),
			"naechste": {"art": ng["art"], "dist": snappedf(float(ng["dist"]), 0.1)}, "wasser_dist": snappedf(_wasser_dist(_spieler()), 0.1),
			"fog": snappedf(main.env.fog_density, 0.0001) if main.env != null else 0.0, "lite": _lite(), "paused": paused}
