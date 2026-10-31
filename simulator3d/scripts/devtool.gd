extends Node
## Entwicklertool 1 «Karte, Sprung, Kamera» (Daniel 31.10.2026): alle Szenen und Orte ansehen, ohne hinzulaufen.
## Nur im Simulator (gewollt: MoveEye braucht es nicht). Fenster «Entwickler» unter «Mehr → Entwickler», nur für den
## Besitzer (is_owner(): wie der Nacht-Testlauf in MoveEye 579b nacht_may - dort «Rolle admin, nicht im Bedienermodus»; der
## Simulator kennt keine Rollen, sein Gegenstück zum Bedienermodus ist der Kinder-Modus: nur «Erwachsene» sehen es).
##   * Liste: alle Welten und Szenen (worlds.gd SHOWN / ORDER, kompakte Szenen) und pro Welt alle bekannten Orte.
##   * Karte: Draufsicht pro Welt mit Markern (Bergtal: die Landeskarte von bergtal.map_texture(), sobald das Tal einmal
##     gebaut ist; sonst und in Lite nur Raster, Seen, Bäche, Strasse, Wege als Linien). Rad = zoomen, ziehen = verschieben.
##   * Sprung: Klick auf Marker oder Listeneintrag lädt nötigenfalls die Welt / Szene und setzt die Ansicht (bzw. beim
##     Erkunden den Rover, bei der Flugkamera die Kamera) an den Ort, Blick auf den Ort. Räume (… (innen)): bergtal_orte.fly.
##   * Flugkamera: explore.gd set_fly (die Erkunden-Kamera, erweitert - keine zweite Kamera).
##
## ZENTRALE FUNKTION für die Pakete 2 und 3 (Testläufe, Fotos, Rundgänge):
##   const Dev = preload("res://scripts/devtool.gd")
##   Dev.alle_orte(main) -> Array of Dictionary, ein Eintrag pro Ort:
##     id     String  eindeutig und fest, z. B. "szene.wald", "bergtal.aussicht.vp_horn", "bergtal.vignette.kuh_socke",
##                    "bergtal.ort.gumpisee", "bergtal.raum.kapelle_st_jodern_innen", "ferienpark.erlebnis.angler",
##                    "pfadilager.ort.sarasani"
##     name   String  deutscher Name (anzeigen mit T.t(name))
##     world  String  Welt: camping | bergtal | ferienpark | festival | daheim | ort | zuhause | vorlage
##     kind   String  szene | ort | aussicht | vignette | schlafplatz | raum | standort | erlebnis
##     x, z   float   Position in Welt-Koordinaten (Bergtal: Tal-Koordinaten, Ferienpark: Park-Koordinaten; x = Osten,
##                    z = Süden). Kompakte Orte (Pfadilager, Bergdorf, Hofladen): Mitte des Orts + Park-Koordinaten.
##     scene  String  diese Szene muss geladen sein ("" = irgendeine Szene dieser Welt genügt)
##     r      float   Grösse (m) - für den Abstand der Ansicht
##     src    String  woher die Daten kommen (Datei · Liste) - es gibt keine eigene Ortsliste hier
##     (at_mw true: der Ort ist beim Standort von MoveEye, z. B. «Kuh leckt am Zelt»; room true: ein Innenraum)
##   Dev.ort(main, id) -> ein Eintrag oder {} · main.mehr.dev.scene_pos(e) -> Vector3 in der geladenen Szene oder null
##   main.mehr.dev.goto(id) -> {ok, …} springt hin (lädt nötigenfalls).
## Steuerbefehl /control {"action": "dev", "do": "places" (world, kind) | "goto" (id) | "fly" (on, speed) | "open" | "close"
##   | "info" | Teil 2: "layer" (name, on) | "set" (time, weather, season, quality) | "regler"} - damit Tests automatisch springen können. MoveEye nutzt ihn nicht (nicht in schnittstelle.json).
## Lite: _lite() (Quality.lite()) - die Karte ohne Landeskarten-Bild und ohne Wege, nur 2 × pro Sekunde neu gezeichnet.
## Entwicklertool 3 (Notizen an Claude, Kontaktbogen, Kapitel-Sprung): eigene Dateien devtool_extra.gd (+ _notizen, _kontakt,
## _kapitel); hier nur die Haken extra.build / extra.control / extra.map_click / extra.map_draw.

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")
const Worlds = preload("res://scripts/worlds.gd")
const Bt = preload("res://scripts/bergtal.gd")
const Orte = preload("res://scripts/bergtal_orte.gd")
const Fp = preload("res://scripts/ferienpark.gd")
const Kompakt = preload("res://scripts/kompakt.gd")
const Scenes = preload("res://scripts/scenes.gd")
const Quality = preload("res://scripts/quality.gd")

# the worlds of the list (worlds.gd SHOWN, in this order) and how big their map is (world coordinates: x0, z0, x1, z1)
const BOUNDS := {"camping": [-30.0, -30.0, 30.0, 30.0], "bergtal": [-1024.0, -1024.0, 1024.0, 1024.0],
		"ferienpark": [-330.0, -260.0, 330.0, 300.0], "festival": [-130.0, -130.0, 130.0, 130.0],
		"daheim": [-50.0, -50.0, 90.0, 50.0], "ort": [-200.0, -200.0, 200.0, 200.0], "zuhause": [-30.0, -30.0, 30.0, 30.0],
		"vorlage": [-30.0, -30.0, 30.0, 30.0]}
const GRID := {"camping": 5.0, "bergtal": 100.0, "ferienpark": 50.0, "festival": 20.0, "daheim": 10.0, "ort": 50.0, "zuhause": 5.0, "vorlage": 5.0}
const KIND_COL := {"szene": Color("#3b8cff"), "ort": Color("#e8eef5"), "aussicht": Color("#f5d04a"), "vignette": Color("#ff6fb0"),
		"schlafplatz": Color("#3fcf6b"), "raum": Color("#c08a5a"), "standort": Color("#3fcf6b"), "erlebnis": Color("#ff6fb0")}
const KIND_NAME := {"szene": "Szene", "ort": "Ort", "aussicht": "Aussichtspunkt", "vignette": "Vignette", "schlafplatz": "Schlafplatz",
		"raum": "Raum (innen)", "standort": "Standort", "erlebnis": "Vignette"}
const SPEEDS := [1.0, 3.0, 8.0, 20.0, 60.0]       # m/s of the fly camera (Shift = × 3)

var main
var panel: PanelContainer = null
var shown := false
var world := ""
var _list: ItemList
var _items: Array = []                 # the entries of the list (same order)
var _search: LineEdit
var _world_opt: OptionButton
var _map: DevMap
var _status: Label
var _fly_chk: CheckButton
var _speed_opt: OptionButton
var _all: Array = []                   # alle_orte() of the last refresh
var _t := 0.0
var ebenen = null                      # Entwicklertool 2 «Regler + Ebenen» (devtool_ebenen.gd): eb()
var extra                              # devtool_extra.gd: Entwicklertool 3 (Notizen, Kontaktbogen, Kapitel-Sprung)


func _ready() -> void:
	extra = preload("res://scripts/devtool_extra.gd").new()
	extra.dev = self
	extra.main = main
	add_child(extra)


static func _lite() -> bool:
	"""the central question «Lite?» (Quality.lite(); the coordinator connects the Lite package)"""
	return Quality.lite()


func eb():
	"""Teil 2 (devtool_ebenen.gd): Schnellregler und Ebenen - eigene Datei, hier nur eingehängt"""
	if ebenen == null:
		ebenen = preload("res://scripts/devtool_ebenen.gd").new()
		ebenen.main = main
		ebenen.dev = self
		add_child(ebenen)
	return ebenen


static func is_owner(m) -> bool:
	"""only the owner: like MoveEye's night test run (579b nacht_may: admin and not in operator mode) - in the simulator: not
	in the children's mode (the way out of it needs the little sum of main.ask_adult)"""
	return m != null and not bool(m.get("kids_on"))


# =============================================================================================================================
# the central list of all places
# =============================================================================================================================
static func _slug(s: String) -> String:
	var t := s.to_lower()
	for p in [["ä", "ae"], ["ö", "oe"], ["ü", "ue"], ["é", "e"], ["è", "e"], ["à", "a"], ["ß", "ss"]]:
		t = t.replace(p[0], p[1])
	var o := ""
	for i in t.length():
		var c := t[i]
		o += c if (c >= "a" and c <= "z") or (c >= "0" and c <= "9") else "_"
	while o.find("__") >= 0:
		o = o.replace("__", "_")
	return o.strip_edges().trim_prefix("_").trim_suffix("_")


static func _add(out: Array, seen: Dictionary, id: String, name: String, world: String, kind: String, x: float, z: float,
		scene := "", r := 5.0, src := "", extra := {}) -> void:
	var k := id
	var n := 2
	while seen.has(k):
		k = "%s_%d" % [id, n]
		n += 1
	seen[k] = true
	var e := {"id": k, "name": name, "world": world, "kind": kind, "x": snappedf(x, 0.1), "z": snappedf(z, 0.1), "scene": scene, "r": r, "src": src}
	e.merge(extra)
	out.append(e)


static func _world_pose(m, w: String) -> Vector2:
	"""where MoveEye stands in a world loaded as itself (the chosen sleeping spot / park spot / festival spot)"""
	match w:
		"bergtal":
			var k := str(m.get("bt_spot")) if m != null and m.get("bt_spot") != null else "huette"
			var sp = Bt.spot_data(k)
			if sp == null and k == "frei" and m.get("bt_free") is Array and (m.bt_free as Array).size() >= 2:
				return Vector2(float(m.bt_free[0]), float(m.bt_free[1]))
			if sp == null:
				sp = Bt.spot_data("huette")
			return Vector2(float(sp[1]), float(sp[2]))
		"ferienpark":
			var k2 := str(m.get("fp_spot")) if m != null and m.get("fp_spot") != null else "zelt"
			var sp2: Array = Fp.SPOTS.get(k2, Fp.SPOTS["zelt"])
			return Vector2(float(sp2[1]), float(sp2[2]))
		"festival":
			var sps: Dictionary = Kompakt.spots_of("festival")
			var k3 := str(m.scene_spot("festival")) if m != null and m.has_method("scene_spot") else ""
			if not sps.has(k3):
				k3 = str(Kompakt.spot_options("festival")[0][0]) if not sps.is_empty() else ""
			return Vector2(float(sps[k3][1]), float(sps[k3][2])) if sps.has(k3) else Vector2.ZERO
	return Vector2.ZERO


static func alle_orte(m = null) -> Array:
	"""ALL known places of the simulator with name, world and position (see the head of the file). Made from the lists that
	are there already (worlds.gd, bergtal.gd, bergtal_orte.gd, ferienpark.gd, kompakt_*.gd) - nothing invented here."""
	var out := []
	var seen := {}
	# the worlds and scenes (worlds.gd SHOWN; the places of a world: worlds.gd ORDER)
	for w in Worlds.SHOWN:
		var wp := _world_pose(m, w)
		var nm := Scenes.name_of(w)
		_add(out, seen, "szene." + w, nm, w, "szene", wp.x, wp.y, w, 30.0, "worlds.gd:SHOWN", {"at_mw": true})
		for k in Worlds.ORDER.get(w, []):
			var p: Array = Worlds.PLACES[k]
			_add(out, seen, "szene." + k, str(p[1]), w, "szene", float(p[2]), float(p[3]), k, float(p[5]), "worlds.gd:PLACES", {"at_mw": true})
	if Worlds.PLACES.has("schlafzimmer"):                      # the bedroom: in the house of the garden (worlds._home_xf)
		for e in out:
			if e["id"] == "szene.schlafzimmer":
				var o: Vector3 = Worlds._home_xf("schlafzimmer").origin
				e["x"] = snappedf(o.x, 0.1)
				e["z"] = snappedf(o.z, 0.1)
	# Bergtal: named places, viewpoints, sleeping spots, vignettes (bergtal.gd), places to explore and rooms (bergtal_orte.gd)
	for p in Bt.PLACES:
		_add(out, seen, "bergtal.ort." + _slug(str(p[0])), str(p[0]), "bergtal", "ort", float(p[1]), float(p[2]), "", 25.0, "bergtal.gd:PLACES")
	for vp in Bt.VIEWPOINTS:
		var c := Bt.vp_xz(vp)
		_add(out, seen, "bergtal.aussicht." + str(vp[0]), str(vp[1]), "bergtal", "aussicht", c.x, c.y, "", 20.0, "bergtal.gd:VIEWPOINTS")
	for k in Bt.SPOT_ORDER:
		if Bt.SPOTS.has(k):
			var sp: Array = Bt.SPOTS[k]
			_add(out, seen, "bergtal.schlafplatz." + k, str(sp[0]), "bergtal", "schlafplatz", float(sp[1]), float(sp[2]), "", 8.0, "bergtal.gd:SPOTS")
	for v in Bt.VIGNETTES:
		var at0: bool = absf(float(v[3])) < 0.01 and absf(float(v[4])) < 0.01
		_add(out, seen, "bergtal.vignette." + str(v[1]), str(v[2]), "bergtal", "vignette", float(v[3]), float(v[4]), "",
				maxf(6.0, float(v[5]) * 2.0), "bergtal.gd:VIGNETTES", {"at_mw": true} if at0 else {})
	var rooms := {}
	for e in Orte.INSIDE:
		rooms[str(e[0])] = true
	for p in Orte.all_places():
		var room := rooms.has(str(p[0]))
		_add(out, seen, ("bergtal.raum." if room else "bergtal.ort.") + _slug(str(p[0])), str(p[0]), "bergtal", "raum" if room else "ort",
				float(p[1]), float(p[2]), "", 6.0 if room else 25.0, "bergtal_orte.gd:INSIDE" if room else "bergtal_orte.gd:PLACES", {"room": true} if room else {})
	# Ferienpark: named places, MoveEye spots, the vignettes of the Erlebniswelt (ferienpark.gd ERLEBNIS)
	for p in Fp.PLACES:
		_add(out, seen, "ferienpark.ort." + _slug(str(p[0])), str(p[0]), "ferienpark", "ort", float(p[1]), float(p[2]), "", 20.0, "ferienpark.gd:PLACES")
	for k in Fp.SPOT_ORDER:
		var sp: Array = Fp.SPOTS[k]
		_add(out, seen, "ferienpark.standort." + k, str(sp[0]), "ferienpark", "standort", float(sp[1]), float(sp[2]), "", 8.0, "ferienpark.gd:SPOTS")
	for v in Fp.ERLEBNIS:
		_add(out, seen, "ferienpark.erlebnis." + str(v[1]), str(v[2]), "ferienpark", "erlebnis", float(v[3]), float(v[4]), "",
				maxf(6.0, float(v[5]) * 2.0), "ferienpark.gd:ERLEBNIS")
	# the compact scenes (kompakt_*.gd PLACES / SPOTS): in their world (centre of the place + park coordinates) or own world
	for sid in Kompakt.SCENES:
		var c := Vector2.ZERO
		var w := str(sid)
		if Worlds.PLACES.has(sid):
			c = Vector2(float(Worlds.PLACES[sid][2]), float(Worlds.PLACES[sid][3]))
			w = str(Worlds.PLACES[sid][0])
		var cm := Kompakt._consts(str(sid))
		for p in cm.get("PLACES", []):
			_add(out, seen, "%s.ort.%s" % [sid, _slug(str(p[0]))], str(p[0]), w, "ort", c.x + float(p[1]), c.y + float(p[2]), sid, 15.0,
					"kompakt_%s.gd:PLACES" % sid, {"lx": float(p[1]), "lz": float(p[2])})
		for k in cm.get("SPOT_ORDER", []):
			var sp: Array = cm["SPOTS"][k]
			_add(out, seen, "%s.standort.%s" % [sid, k], str(sp[0]), w, "standort", c.x + float(sp[1]), c.y + float(sp[2]), sid, 8.0,
					"kompakt_%s.gd:SPOTS" % sid, {"lx": float(sp[1]), "lz": float(sp[2])})
	return out


static func ort(m, id: String) -> Dictionary:
	for e in alle_orte(m):
		if e["id"] == id:
			return e
	return {}


static func world_name(w: String) -> String:
	return T.t(str(Worlds.SHORT[w])) if Worlds.SHORT.has(w) else T.t(Scenes.name_of(w))


# =============================================================================================================================
# coordinates: world <-> the scene that is loaded
# =============================================================================================================================
func loaded_world() -> String:
	var sc := str(main.scene)
	if Worlds.solo(main, sc) and Worlds.is_place(sc):
		return "solo:" + sc                                  # «allein»: the old scene without its world
	return Worlds.world_of(sc)


func frame():
	"""Transform3D world -> scene of the world that is loaded (null: unknown)"""
	var w := loaded_world()
	var d: Dictionary = main.scenes.data if main.scenes != null else {}
	match w:
		"bergtal":
			var bt = d.get("bergtal")
			return bt.tal.transform if bt != null and is_instance_valid(bt.tal) else null
		"ferienpark":
			var fp = d.get("ferienpark")
			return fp.park.transform if fp != null and is_instance_valid(fp.park) else null
		"festival":
			var k = d.get("kompakt")
			return k.park.transform if k != null and is_instance_valid(k.park) else null
		"daheim":
			return Worlds._home_xf(str(main.scene)).affine_inverse()
		"camping", "ort", "zuhause", "vorlage":
			return Transform3D.IDENTITY
	return null


func scene_pos(e: Dictionary):
	"""where a place is in the scene that is loaded now (Vector3 on the ground, or null if its world is not loaded)"""
	var sc := Worlds.default_place(str(e.get("scene", ""))) if str(e.get("scene", "")) != "" else ""
	if sc != "" and str(main.scene) != sc:
		return null
	if bool(e.get("at_mw", false)) and (sc != "" or str(e["world"]) == loaded_world()):
		return Vector3(0, main.ground_y(0, 0), 0)                # MoveEye stands in the origin of every scene
	var p := Vector3(float(e["x"]), 0, float(e["z"]))
	var w := loaded_world()
	if w.begins_with("solo:"):
		var k = main.scenes.data.get("kompakt") if main.scenes != null else null
		if e.has("lx") and k != null and is_instance_valid(k.park):
			p = k.park.transform * Vector3(float(e["lx"]), 0, float(e["lz"]))
		else:
			return null
	else:
		if str(e["world"]) != w:
			return null
		var f = frame()
		if f == null:
			return null
		p = (f as Transform3D) * p
	p.y = main.ground_y(p.x, p.z)
	return p


func to_world(p: Vector3):
	"""scene -> world coordinates (Vector2) of the world that is loaded (null: not possible)"""
	var f = frame()
	if f == null:
		return null
	var q: Vector3 = (f as Transform3D).affine_inverse() * p
	return Vector2(q.x, q.z)


# =============================================================================================================================
# the jump
# =============================================================================================================================
func _need_scene(e: Dictionary) -> String:
	"""the scene to load for this place ("" = nothing to load)"""
	var sc := str(e.get("scene", ""))
	if sc != "":
		return "" if str(main.scene) == Worlds.default_place(sc) else sc
	if loaded_world() == str(e["world"]):
		return ""
	return Worlds.default_place(str(e["world"]))


func goto(id: String) -> Dictionary:
	var e := {}
	for x in (_all if not _all.is_empty() else alle_orte(main)):
		if x["id"] == id:
			e = x
	if e.is_empty():
		e = ort(main, id)
	if e.is_empty():
		return {"ok": false, "error": "unknown place", "id": id}
	var need := _need_scene(e)
	var loaded := false
	if need != "":
		if not main.set_scene(need):
			return {"ok": false, "error": "cannot load", "scene": need}
		loaded = true
	var p = scene_pos(e)
	if p == null:
		return {"ok": false, "error": "not in this scene", "scene": main.scene, "world": loaded_world()}
	if loaded and panel != null:
		_all = alle_orte(main)                               # (a new sleeping spot / park spot moves the markers «Szene»)
		if world != str(e["world"]):
			set_world(str(e["world"]))
	if _map != null:
		_map.sel = id
		_map.queue_redraw()
	_say(T.t("Sprung: %s") % T.t(str(e["name"])))
	var ex = main.explore
	if bool(e.get("room", false)) and not (ex != null and ex.on):
		var bt = main.scenes.data.get("bergtal")
		if bt != null and bt.get("orte") != null and bt.orte.fly(str(e["name"])):
			return {"ok": true, "id": id, "loaded": need, "room": true, "pos": _v(p)}
	view_at(p, _dist(e), loaded)
	return {"ok": true, "id": id, "loaded": need, "pos": _v(p), "scene": main.scene}


static func _w2(q) -> Array:
	return [snappedf(q.x, 0.1), snappedf(q.y, 0.1)] if q != null else []


static func _v(p: Vector3) -> Array:
	return [snappedf(p.x, 0.01), snappedf(p.y, 0.01), snappedf(p.z, 0.01)]


func _dist(e: Dictionary) -> float:
	return clampf(float(e.get("r", 10.0)) * 1.1, 7.0, 60.0)


func view_at(p: Vector3, d: float, at_once := false) -> void:
	"""the view (or, while exploring, the rover) to the place, looking at it"""
	var ex = main.explore
	if ex != null and ex.on:                                  # «Erkunden»: the rover goes there, its camera follows
		var a: Vector3 = main.free_spot(p + Vector3(0, 0, 3.0), 0.6, false)
		main.rig.position = Vector3(a.x, main.ground_y(a.x, a.z), a.z)
		return
	main._to_free_view()
	main.follow = false
	if main.spectate:
		main.spectate_stop()
	if main.fly_tw != null:
		main.fly_tw.kill()
	var cam: Camera3D = main.view_cam
	var fwd := -cam.global_transform.basis.z
	fwd.y = 0.0
	fwd = fwd.normalized() if fwd.length() > 0.01 else Vector3(0, 0, -1)
	var tgt := p + Vector3(0, 1.2, 0)
	var to := tgt - fwd * d + Vector3(0, d * 0.45, 0)
	to.y = maxf(to.y, main.ground_y(to.x, to.z) + 1.5)
	var end := Transform3D(Basis(), to).looking_at(tgt, Vector3.UP)
	if at_once or cam.global_position.distance_to(to) > 600.0:
		cam.global_transform = end                            # a new scene / far away: no long flight through the valley
		return
	var start: Transform3D = cam.global_transform
	main.fly_tw = main.create_tween()
	main.fly_tw.tween_method(func(f: float): cam.global_transform = start.interpolate_with(end, f), 0.0, 1.0, 0.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)


func set_fly(on: bool, speed := -1.0) -> void:
	var ex = main.explore
	if ex == null:
		return
	if speed > 0.0:
		ex.fly_speed = speed
	ex.set_fly(on)
	_paint()


func _say(t: String) -> void:
	main.start_info = t
	if _status != null:
		_status.text = t


# =============================================================================================================================
# the window
# =============================================================================================================================
func open() -> void:
	if not is_owner(main):
		_say(T.t("Das Entwicklertool ist nur für den Besitzer (nicht im Kinder-Modus)."))
		return
	if panel == null:
		_build()
	_all = alle_orte(main)
	var lw := loaded_world()
	set_world(lw if BOUNDS.has(lw) else (world if world != "" else "bergtal"))
	shown = true
	if main.fenster != null:
		main.fenster.changed()
	panel.visible = true


func close() -> void:
	shown = false
	if main.fenster != null:
		main.fenster.changed()


func _build() -> void:
	panel = PanelContainer.new()
	panel.theme = main.ui_root.theme if main.ui_root != null else UI.theme()
	panel.add_theme_stylebox_override("panel", UI.box(Color(UI.PANEL, 0.98), UI.LINE, 12, 10, 1))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	panel.add_child(v)
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 8)
	v.add_child(top)
	var wl := Label.new()
	wl.text = T.t("Welt")
	top.add_child(wl)
	_world_opt = OptionButton.new()
	_world_opt.custom_minimum_size = Vector2(170, 34)
	for w in Worlds.SHOWN:
		_world_opt.add_item(world_name(w))
		_world_opt.set_item_metadata(_world_opt.item_count - 1, w)
	_world_opt.item_selected.connect(func(i): set_world(str(_world_opt.get_item_metadata(i))))
	top.add_child(_world_opt)
	_search = UI.search_field(T.t("Ort suchen …"))
	_search.custom_minimum_size = Vector2(200, 34)
	_search.text_changed.connect(func(_t): _fill())
	top.add_child(_search)
	var mid := HBoxContainer.new()
	mid.add_theme_constant_override("separation", 8)
	v.add_child(mid)
	_list = ItemList.new()
	_list.custom_minimum_size = Vector2(230, 380)
	_list.add_theme_font_size_override("font_size", 13)
	_list.item_clicked.connect(func(i, _p, b):
		if b == MOUSE_BUTTON_LEFT and i < _items.size():
			goto(str(_items[i]["id"])))
	mid.add_child(_list)
	_map = DevMap.new()
	_map.dev = self
	_map.custom_minimum_size = Vector2(360, 380)
	_map.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	mid.add_child(_map)
	var leg := UI.small(T.t("Blau Szene · Weiss Ort · Gelb Aussicht · Grün Schlaf- / Standort · Rosa Vignette · Braun Raum · ▲ Ansicht · ● MoveEye — Klick = hinspringen, Rad = zoomen, ziehen = verschieben"))
	leg.custom_minimum_size = Vector2(598, 0)
	v.add_child(leg)
	var bot := HBoxContainer.new()
	bot.add_theme_constant_override("separation", 10)
	v.add_child(bot)
	_fly_chk = CheckButton.new()
	_fly_chk.text = T.t("Flugkamera (durch Wände)")
	_fly_chk.tooltip_text = T.t("W A S D fliegen · Q / E runter / hoch · Shift schneller · rechte Maustaste umschauen · Rad oder + / − Tempo · Esc zurück")
	_fly_chk.toggled.connect(func(on): set_fly(on))
	bot.add_child(_fly_chk)
	var sl := Label.new()
	sl.text = T.t("Tempo")
	bot.add_child(sl)
	_speed_opt = OptionButton.new()
	for s in SPEEDS:
		_speed_opt.add_item("%s m/s" % str(s).trim_suffix(".0"))
	_speed_opt.item_selected.connect(func(i):
		if main.explore != null:
			main.explore.fly_speed = float(SPEEDS[i]))
	bot.add_child(_speed_opt)
	_status = UI.small("", UI.TXT)
	_status.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_status.clip_text = true
	bot.add_child(_status)
	v.add_child(eb().section())                          # Teil 2: Schnellregler + Ebenen
	extra.build(v)                                       # Teil 3: Notizen, Kontaktbogen, Kapitel-Sprung
	if main.fenster != null:
		main.fenster.add("dev", "Entwickler", panel, {"on": func(): return shown, "set_on": func(x): shown = bool(x),
				"shown": func(): return shown, "list": false, "home": _home})
	else:
		main.ui_layer.add_child(panel)
	var mh = get_parent()
	if mh != null and mh.get("farben") != null:
		mh.farben.register(panel, "all")                     # Hell / Rotlicht / Dunkel like the other windows of «Mehr»
	_paint()


func _home(w) -> Vector2:
	"""in the middle of the free view (left of the control panel), under the CPU line"""
	var lr: Vector2 = main.fenster.free_lr()
	return Vector2(maxf(lr.x + 14.0, (lr.x + lr.y - w.size.x) * 0.5), 60.0)


func set_world(w: String) -> void:
	if not BOUNDS.has(w):
		w = "bergtal"
	world = w
	if _world_opt != null:
		for i in _world_opt.item_count:
			if str(_world_opt.get_item_metadata(i)) == w:
				_world_opt.select(i)
	if _map != null:
		_map.fit()
	_fill()


func _fill() -> void:
	if _list == null:
		return
	_list.clear()
	_items = []
	var q := _search.text.strip_edges().to_lower() if _search != null else ""
	for e in _all:
		if str(e["world"]) != world:
			continue
		var nm := T.t(str(e["name"]))
		if q != "" and nm.to_lower().find(q) < 0 and str(e["name"]).to_lower().find(q) < 0:
			continue
		_items.append(e)
		var i := _list.add_item(("▣ " if e["kind"] == "szene" else "• ") + nm)
		_list.set_item_custom_fg_color(i, KIND_COL.get(str(e["kind"]), UI.TXT))
		_list.set_item_tooltip(i, "%s · %s" % [T.t(str(KIND_NAME.get(str(e["kind"]), e["kind"]))), str(e["src"])])
	if _map != null:
		_map.queue_redraw()


func _paint() -> void:
	var ex = main.explore
	if _fly_chk != null and ex != null:
		_fly_chk.set_pressed_no_signal(bool(ex.fly))
		var best := 0
		for i in SPEEDS.size():
			if absf(float(SPEEDS[i]) - float(ex.fly_speed)) < absf(float(SPEEDS[best]) - float(ex.fly_speed)):
				best = i
		_speed_opt.select(best)


func _process(dt: float) -> void:
	if panel == null or not shown:
		return
	_t -= dt
	if _t > 0.0:
		return
	_t = 0.5 if _lite() else 0.25
	_paint()
	if _map != null and _map.is_visible_in_tree():
		_map.queue_redraw()                                  # the view and MoveEye move


# =============================================================================================================================
# /control {"action": "dev", …}
# =============================================================================================================================
func control(d: Dictionary) -> Dictionary:
	var xr = extra.control(d) if extra != null else null      # Entwicklertool 3: notes | contact … | chapters … (devtool_extra.gd)
	if xr != null:
		return xr
	match str(d.get("do", "info")):
		"places":
			var L := alle_orte(main)
			var w := str(d.get("world", ""))
			var k := str(d.get("kind", ""))
			if w != "" or k != "":
				L = L.filter(func(e): return (w == "" or e["world"] == w) and (k == "" or e["kind"] == k))
			return {"ok": true, "n": L.size(), "places": L}
		"goto":
			_all = alle_orte(main)
			return goto(str(d.get("id", d.get("value", ""))))
		"fly":
			var on = d.get("on", d.get("value", null))
			var v := (str(on) in ["on", "true", "1"]) if on != null else not bool(main.explore.fly)
			set_fly(v, float(d.get("speed", -1.0)))
			return {"ok": true, "fly": main.explore.fly, "speed": main.explore.fly_speed}
		"open":
			open()
			if d.has("world"):
				set_world(str(d["world"]))
			return {"ok": shown, "world": world}
		"close":
			close()
			return {"ok": true}
		"layer", "layers", "set", "regler", "values", "parts":   # Teil 2 (devtool_ebenen.gd)
			return eb().control(d)
	var ex = main.explore
	var cam: Camera3D = main.view_cam
	return {"ok": true, "owner": is_owner(main), "open": shown, "world": world, "loaded": loaded_world(), "scene": main.scene,
			"fly": ex.fly if ex != null else false, "speed": ex.fly_speed if ex != null else 0.0, "cam": _v(cam.global_position),
			"cam_world": _w2(to_world(cam.global_position)),
			"n": alle_orte(main).size(), "ebenen": eb().info()}


# =============================================================================================================================
# the map (top view of one world)
# =============================================================================================================================
class DevMap extends Control:
	var dev
	var center := Vector2.ZERO           # world coordinates in the middle
	var scale_ := 0.2                    # pixels per metre
	var sel := ""
	var hover := -1
	var _drag := false
	var _moved := 0.0
	var _pts: Array = []                 # [screen position, entry] of the markers drawn last

	func _init() -> void:
		clip_contents = true
		mouse_filter = Control.MOUSE_FILTER_STOP

	func fit() -> void:
		var b: Array = BOUNDS.get(dev.world, [-50.0, -50.0, 50.0, 50.0])
		center = Vector2((float(b[0]) + float(b[2])) * 0.5, (float(b[1]) + float(b[3])) * 0.5)
		var sz := size if size.x > 10.0 else custom_minimum_size
		scale_ = minf(sz.x / (float(b[2]) - float(b[0])), sz.y / (float(b[3]) - float(b[1])))
		queue_redraw()

	func S(w: Vector2) -> Vector2:
		return (w - center) * scale_ + size * 0.5

	func Wd(s: Vector2) -> Vector2:
		return (s - size * 0.5) / scale_ + center

	func _gui_input(ev: InputEvent) -> void:
		if ev is InputEventMouseButton:
			if ev.button_index == MOUSE_BUTTON_WHEEL_UP and ev.pressed:
				_zoom(ev.position, 1.25)
			elif ev.button_index == MOUSE_BUTTON_WHEEL_DOWN and ev.pressed:
				_zoom(ev.position, 0.8)
			elif ev.button_index == MOUSE_BUTTON_LEFT:
				if ev.pressed:
					_drag = true
					_moved = 0.0
				else:
					_drag = false
					if _moved < 5.0:
						var e = _at(ev.position)
						if dev.extra != null and dev.extra.map_click(Wd(ev.position)):
							pass                         # Entwicklertool 3: a note's place / a note marker
						elif e != null:
							dev.goto(str(e["id"]))
			accept_event()
		elif ev is InputEventMouseMotion:
			if _drag:
				_moved += ev.relative.length()
				center -= ev.relative / scale_
				queue_redraw()
			else:
				var e = _at(ev.position)
				var h := -1
				for i in _pts.size():
					if e != null and _pts[i][1] == e:
						h = i
				if h != hover:
					hover = h
					tooltip_text = "" if e == null else "%s (%s)" % [T.t(str(e["name"])), T.t(str(KIND_NAME.get(str(e["kind"]), e["kind"])))]
					queue_redraw()

	func _zoom(p: Vector2, f: float) -> void:
		var w := Wd(p)
		scale_ = clampf(scale_ * f, 0.05, 40.0)
		center = w - (p - size * 0.5) / scale_
		queue_redraw()

	func _at(p: Vector2):
		var best = null
		var bd := 10.0
		for x in _pts:
			var d: float = (x[0] as Vector2).distance_to(p)
			if d < bd:
				bd = d
				best = x[1]
		return best

	func _draw() -> void:
		var lite: bool = dev._lite()
		draw_rect(Rect2(Vector2.ZERO, size), Color("#0c121a"))
		var w: String = dev.world
		var b: Array = BOUNDS.get(w, [-50.0, -50.0, 50.0, 50.0])
		var r0 := S(Vector2(float(b[0]), float(b[1])))
		var r1 := S(Vector2(float(b[2]), float(b[3])))
		if w == "bergtal" and not lite and not Bt._hm.is_empty():
			draw_texture_rect(Bt.map_texture(), Rect2(S(Vector2(Bt.LO, Bt.LO)), Vector2(2048.0, 2048.0) * scale_), false, Color(1, 1, 1, 0.9))
		else:
			draw_rect(Rect2(r0, r1 - r0), Color("#111822"))
		# the grid
		var g: float = float(GRID.get(w, 10.0))
		while g * scale_ < 24.0:
			g *= 2.0
		var gc := Color(1, 1, 1, 0.07)
		var x := ceilf(float(b[0]) / g) * g
		while x <= float(b[2]):
			draw_line(S(Vector2(x, float(b[1]))), S(Vector2(x, float(b[3]))), gc, 1.0)
			x += g
		var z := ceilf(float(b[1]) / g) * g
		while z <= float(b[3]):
			draw_line(S(Vector2(float(b[0]), z)), S(Vector2(float(b[2]), z)), gc, 1.0)
			z += g
		draw_string(get_theme_default_font(), Vector2(6, size.y - 6), "%s m" % str(g).trim_suffix(".0"), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(1, 1, 1, 0.5))
		if w == "bergtal" and (lite or Bt._hm.is_empty()):
			_draw_valley(lite)
		if dev.ebenen != null:
			dev.ebenen.draw_map(self)                        # Teil 2: die Ebenen auch auf der Karte
		# the markers (scenes last: on top)
		_pts = []
		var font := get_theme_default_font()
		for pass_ in [0, 1]:
			for e in dev._all:
				if str(e["world"]) != w or (pass_ == 1) != (str(e["kind"]) == "szene"):
					continue
				var p := S(Vector2(float(e["x"]), float(e["z"])))
				if p.x < -10.0 or p.y < -10.0 or p.x > size.x + 10.0 or p.y > size.y + 10.0:
					continue
				var col: Color = KIND_COL.get(str(e["kind"]), Color.WHITE)
				var on: bool = str(e["id"]) == sel
				if pass_ == 1:
					draw_rect(Rect2(p - Vector2(5, 5), Vector2(10, 10)), col)
					draw_rect(Rect2(p - Vector2(5, 5), Vector2(10, 10)), Color.BLACK, false, 1.0)
					if scale_ > 0.25 or w != "bergtal":
						draw_string(font, p + Vector2(8, 4), T.t(str(e["name"])).left(28), HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(1, 1, 1, 0.85))
				else:
					draw_circle(p, 3.5, col)
					draw_arc(p, 3.5, 0.0, TAU, 10, Color(0, 0, 0, 0.6), 1.0)
				if on:
					draw_arc(p, 8.0, 0.0, TAU, 16, Color.WHITE, 2.0)
				_pts.append([p, e])
		if hover >= 0 and hover < _pts.size():
			var hp: Vector2 = _pts[hover][0]
			var tx: String = T.t(str(_pts[hover][1]["name"]))
			var tw := font.get_string_size(tx, HORIZONTAL_ALIGNMENT_LEFT, -1, 12).x
			var bx := Vector2(clampf(hp.x + 10.0, 2.0, size.x - tw - 10.0), clampf(hp.y - 22.0, 2.0, size.y - 20.0))
			draw_rect(Rect2(bx, Vector2(tw + 8.0, 18.0)), Color(0, 0, 0, 0.8))
			draw_string(font, bx + Vector2(4, 13), tx, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color.WHITE)
		# where the view and MoveEye are (only when this world is loaded)
		if dev.loaded_world() == w:
			var mw = dev.to_world(Vector3.ZERO)
			if mw != null:
				var mp := S(mw)
				draw_circle(mp, 5.0, Color("#3fcf6b"))
				draw_arc(mp, 5.0, 0.0, TAU, 12, Color.BLACK, 1.5)
			var cam: Camera3D = dev.main.view_cam
			var cp = dev.to_world(cam.global_position)
			var ca = dev.to_world(cam.global_position - cam.global_transform.basis.z * 10.0)
			if cp != null and ca != null:
				var a := S(cp)
				var dir := (S(ca) - a).normalized() if S(ca).distance_to(a) > 0.01 else Vector2.UP
				var sd := Vector2(-dir.y, dir.x)
				draw_colored_polygon(PackedVector2Array([a + dir * 10.0, a - dir * 5.0 + sd * 6.0, a - dir * 5.0 - sd * 6.0]), Color("#ffcc33"))
		if dev.extra != null:
			dev.extra.map_draw(self)                         # Entwicklertool 3: the notes on the map
		draw_rect(Rect2(Vector2.ZERO, size), Color(1, 1, 1, 0.15), false, 1.0)

	func _draw_valley(lite: bool) -> void:
		"""the Bergtal without its map picture: lakes, streams, the road, the trails (constants of bergtal.gd)"""
		for lk in Bt.LAKES:
			var pts := PackedVector2Array()
			for i in 24:
				var t := TAU * float(i) / 24.0
				pts.append(S((lk[0] as Vector2) + Vector2(float(lk[1]) * cos(t), float(lk[2]) * sin(t)).rotated(float(lk[3]))))
			draw_colored_polygon(pts, Color(0.3, 0.5, 0.8, 0.8))
		for st in Bt.STREAMS:
			_poly(st[0], Color(0.35, 0.55, 0.9, 0.8), 1.5)
		_poly(Bt.ROAD, Color(0.85, 0.25, 0.2, 0.9), 2.0)
		if not lite:
			for tr in Bt.TRAILS:
				_poly(tr[1], Color(0.8, 0.8, 0.8, 0.45), 1.0)

	func _poly(pts: Array, c: Color, wd: float) -> void:
		var L := PackedVector2Array()
		for q in pts:
			L.append(S(q))
		if L.size() >= 2:
			draw_polyline(L, c, wd)
