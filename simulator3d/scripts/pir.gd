extends Node
## Paket «PIR, Mikrofon & Umgebungsgeräusche» (Zweig real-pir-ton, 31.10.2026): der Bewegungsmelder AM GERÄT wie echt.
##   AS312 Micro-PIR mit Linse Ø 12,2 an der Stirnseite des Gehäuses – «vorne» = Pan-0-Richtung (dreht nicht mit dem Kopf).
##   Datenblatt (Senba AS312 / Angabe Daniel): Fächer ca. 100° waagrecht, Reichweite ~3–5 m bei 25 °C, Ausgang 2,3 s hoch
##   (TOH, bei weiterer Bewegung verlängert), danach 2,3 s gesperrt (TOL, nicht einstellbar). Angenommen (nicht im Datenblatt):
##   30 s Aufwärmen nach dem Einschalten, ~0,2 s bis das Signal reicht.
##   Modell pro Körper (10 × pro s): Signal = Temperaturunterschied × Grösse × Bewegung × (R0 / Abstand)²
##     - quer zur Linse zählt voll, auf die Linse zu / weg nur ~ein Viertel (PIR sieht Wechsel zwischen den Linsen-Zonen)
##     - warme Umgebung = weniger Unterschied zur Haut / zum Fell = kürzere Reichweite (bei 31 °C quer nur noch ~2,7 m)
##     - Hindernisse (Bäume, Wände, Autos – main.obstacles) verdecken, die Linse sieht höchstens 7 m
##   Fehlauslösungen: warme Luft in Böen über sonnigem Boden, Sonne bricht durch die Wolken / tiefe Sonne in der Linse,
##   Rauch / Feuer / Grill im Fächer (im Wind).
##   An MoveEye wie die anderen Sensoren: /info «sensors» (Name «PIR Gerät», kind «pir»), Ereignisse mit active true / false
##   (350 holt /events → 280 sens_event: true = Bewegung, false = wieder ruhig). Keine neue Schnittstelle nötig.
##   Während Prüfstand / Testlauf meldet er nichts (vergleichbare Messungen; Test-Aktion «pir» → in_tests).
## Einstellungen: user://pir.json.

var main
const T = preload("res://scripts/i18n.gd")
const FILE := "user://pir.json"
const NAME := "PIR Gerät"
const FOV_H := 100.0               # ° waagrecht (Datenblatt: ~100°)
const EDGE := 5.0                  # ° weicher Rand des Fächers
const R0 := 5.0                    # m: Person quer bei 25 °C (Datenblatt 3–5 m: frontal ~3 m, quer ~5 m)
const R_LENS := 7.0                # m: weiter sieht die kleine Linse nichts mehr (auch in kalten Nächten)
const RADIAL := 0.24               # Bewegung auf die Linse zu zählt so viel wie quer
const V_FULL := 0.8                # m/s quer = volles Signal
const TOH := 2.3                   # s Ausgang hoch
const TOL := 2.3                   # s danach gesperrt
const WARMUP := 30.0               # s nach dem Einschalten (Annahme)
const T_REF := 6.0                 # K Unterschied bei 25 °C (Kleidung ~31 °C)
# Oberfläche °C und Grösse (Person = 1) der warmen Körper - grob nach Fell / Kleidung / Fläche
const BODY := {"person": [31.0, 1.0], "car": [45.0, 2.5], "dog": [30.0, 0.35], "deer": [30.0, 1.1], "boar": [30.0, 0.7],
		"fox": [29.0, 0.22], "cat": [30.0, 0.1], "badger": [29.0, 0.2], "hare": [30.0, 0.1], "hedgehog": [28.0, 0.04],
		"marten": [30.0, 0.08], "squirrel": [30.0, 0.04], "wolf": [30.0, 0.5], "lynx": [30.0, 0.4], "chamois": [30.0, 0.6],
		"cow": [32.0, 2.2], "horse": [32.0, 2.0], "sheep": [27.0, 0.7], "owl": [28.0, 0.05], "bats": [30.0, 0.02]}

var on := true                     # PIR am Gerät simulieren
var show_fan := false              # Fächer am Boden zeigen (nur für dich, MoveEye sieht ihn nicht)
var false_on := true               # Fehlauslösungen (warme Luft, Sonne, Rauch)
var in_tests := false              # auch während Prüfstand / Testlauf melden (Test-Aktion)

var out := false                   # Ausgang des AS312
var hi_until := 0.0
var block_until := 0.0
var warm_until := 0.0
var _acc := 0.0                    # wie lange das Signal schon reicht
var _tick := 0.0
var _prev := {}                    # instance id -> Vector3
var sig := 0.0                     # stärkstes Signal (1 = Schwelle)
var who := ""                      # wer es war (oder die Ursache der Fehlauslösung)
var who_d := 0.0
var n_true := 0
var n_false := 0
var log_: Array = []               # [{t, who, d, cause}] die letzten 20 Auslösungen
var _fan: MeshInstance3D = null
var _fan_key := ""
var _fan_mat: StandardMaterial3D = null
var info_label: Label
var _false_cause := ""


func _ready() -> void:
	if FileAccess.file_exists(FILE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
		if typeof(d) == TYPE_DICTIONARY:
			on = bool(d.get("on", on))
			show_fan = bool(d.get("show_fan", show_fan))
			false_on = bool(d.get("false_on", false_on))
	warm_until = _t() + WARMUP


func save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"on": on, "show_fan": show_fan, "false_on": false_on}))


func _t() -> float:
	return main.now() if main != null else Time.get_ticks_msec() / 1000.0


func set_on(v: bool) -> void:
	if v and not on:
		warm_until = _t() + WARMUP                     # frisch eingeschaltet: der Sensor wärmt auf
	on = v
	if not on and out:
		_fall()
	save()


# ---- wo der Sensor ist -------------------------------------------------------------------------------------------------
func sensor_pos() -> Vector3:
	if main.rig == null:
		return Vector3(0, main.HEAD_H - 0.15, 0)
	return main.rig.global_transform * Vector3(0, maxf(0.3, main.mast_h - 0.15), -0.12)


func forward() -> Vector3:
	"""Pan-0-Richtung des Gehäuses (der Kopf dreht, das Gehäuse nicht)"""
	if main.rig == null:
		return Vector3(0, 0, -1)
	var f: Vector3 = -main.rig.global_transform.basis.z
	f.y = 0.0
	return f.normalized() if f.length() > 0.01 else Vector3(0, 0, -1)


func temp_factor(surface_c: float) -> float:
	"""weniger Unterschied zur Umgebung = schwächeres Signal (AS312 hat eine Temperatur-Kompensation: nur ^0.7)"""
	var dt: float = maxf(1.0, absf(surface_c - float(main.ambient)))   # Gesicht / Hände sind immer etwas wärmer (≥ 1 K)
	return pow(clampf(dt / T_REF, 0.0, 2.0), 0.7)


func reach(kind := "person", across := true) -> float:
	"""wie weit eine gehende Person (quer / frontal) jetzt erkannt wird - für Anzeige, Fächer und Test"""
	var b: Array = BODY.get(kind, [30.0, 0.3])
	var m := 1.0 if across else minf(1.0, RADIAL * 1.2 / V_FULL)
	return minf(R_LENS, R0 * sqrt(maxf(0.0, temp_factor(float(b[0])) * float(b[1]) * m)))


# ---- 10 × pro Sekunde ----------------------------------------------------------------------------------------------------
func _process(delta: float) -> void:
	if main == null or main.rig == null:
		return
	_tick -= delta
	if _tick > 0.0:
		return
	var dt := 0.1 - _tick
	_tick = 0.1
	var t := _t()
	_fan_update()
	if info_label != null and info_label.is_visible_in_tree():
		info_label.text = main.no_emoji(status_text())
	if out and t >= hi_until:
		_fall()
	if not on:
		return
	var quiet: bool = not in_tests and main.busy_with() in ["Prüfstand", "Testlauf"]
	var s := _bodies(dt)
	sig = s
	var fire := false
	if s >= 1.0:
		_acc += dt
		fire = _acc >= 0.2
	else:
		_acc = maxf(0.0, _acc - dt)
	var cause := ""
	if not fire and false_on and not quiet and randf() < _false_rate() * dt:
		fire = true
		cause = _false_cause
	if t < warm_until or quiet:
		return
	if fire:
		if out:
			hi_until = t + TOH                             # weitere Bewegung: bleibt hoch
		elif t >= block_until:
			_rise(t, cause)


func _bodies(dt: float) -> float:
	"""das stärkste Signal aller warmen Körper (1 = Schwelle); merkt wer"""
	var sp := sensor_pos()
	var fw := forward()
	var best := 0.0
	var seen := {}
	var list: Array = []
	if main.visitors != null:
		list = main.visitors.get_children()
	if main.game != null:
		for p in main.game.players:
			if p != null and p.get("actor") != null and is_instance_valid(p["actor"]) and (p["actor"] as Node3D).visible:
				list.append(p["actor"])
	for v in list:
		if not v is Node3D or not is_instance_valid(v):
			continue
		var n: Node3D = v
		var k := str(n.get("kind")) if n.get("kind") != null else ""
		if not BODY.has(k) or not n.visible:
			continue
		var id := n.get_instance_id()
		seen[id] = true
		var p := n.global_position
		var pv = _prev.get(id, null)
		_prev[id] = p
		if pv == null:
			continue
		var b: Array = BODY[k]
		var c: Vector3 = p + Vector3(0, 0.9 if k == "person" else 0.4, 0) - sp
		var hd := Vector2(c.x, c.z).length()
		if hd > R_LENS + 0.5 or hd < 0.05:
			continue
		var dir := Vector3(c.x, 0, c.z) / hd
		var az := rad_to_deg(absf(fw.signed_angle_to(dir, Vector3.UP)))
		var wf := clampf((FOV_H / 2.0 + EDGE - az) / (2.0 * EDGE), 0.0, 1.0)
		if wf <= 0.0:
			continue
		var el := rad_to_deg(atan2(c.y, hd))
		var wv := clampf((el + 55.0) / 10.0, 0.0, 1.0) * clampf((40.0 - el) / 10.0, 0.0, 1.0)
		if wv <= 0.0:
			continue
		var vel: Vector3 = (p - (pv as Vector3)) / maxf(0.02, dt)
		vel.y = 0.0
		var vr := absf(vel.dot(dir))
		var vt := (vel - dir * vel.dot(dir)).length()
		var mv := minf(1.0, (vt + RADIAL * vr) / V_FULL)
		if mv < 0.05:
			continue
		var s := temp_factor(float(b[0])) * float(b[1]) * mv * wf * wv * pow(R0 / maxf(0.3, hd), 2.0)
		s *= clampf((R_LENS + 0.5 - hd) / 0.5, 0.0, 1.0)
		if s >= 0.5 and _hidden(sp, p):
			continue
		s *= 1.0 + randfn(0.0, 0.05)
		if s > best:
			best = s
			who = _kind_name(k, n)
			who_d = hd
	for id in _prev.keys():
		if not seen.has(id):
			_prev.erase(id)
	return best


func _hidden(a: Vector3, b: Vector3) -> bool:
	"""ein Hindernis zwischen Sensor und Körper (Bäume, Wände, Autos, Zäune - grob, ohne Höhe)"""
	var d := Vector2(b.x - a.x, b.z - a.z)
	var n := int(d.length() / 0.5)
	for i in range(1, n):
		var q := Vector2(a.x, a.z) + d * (float(i) / float(n))
		if main.blocked(q, 0.05, true):
			return true
	return false


func _kind_name(k: String, n: Node3D) -> String:
	if k == "person":
		return T.t("Person")
	var nm := {"car": "Auto", "dog": "Hund", "deer": "Reh", "boar": "Wildschwein", "fox": "Fuchs", "cat": "Katze",
			"badger": "Dachs", "hare": "Hase", "hedgehog": "Igel", "marten": "Marder", "squirrel": "Eichhörnchen", "wolf": "Wolf",
			"lynx": "Luchs", "chamois": "Gämse", "cow": "Kuh", "horse": "Pferd", "sheep": "Schaf", "owl": "Eule", "bats": "Fledermaus"}
	return T.t(str(nm.get(k, k)))


func _false_rate() -> float:
	"""Fehlauslösungen pro Sekunde - und die Ursache, die am meisten beiträgt"""
	var g: float = main.wind * main.gust()
	var el: float = main.sun_el()
	var sunny: float = 0.0 if main.is_dark() or el < 2.0 else clampf(el / 25.0, 0.0, 1.0) * (1.0 - main.clouds())
	var parts := {}
	# warme Luft: Böen über sonnig aufgeheiztem Boden (auch abends noch etwas)
	parts["air"] = 0.004 * clampf((g - 12.0) / 25.0, 0.0, 1.0) * (0.25 + sunny)
	# Sonne: bricht durch die Wolken (Wolken-Schatten) oder steht tief in der Linse
	var sun_in := 0.0
	if el > 0.0 and el < 15.0 and not main.is_dark():
		var saz: float = deg_to_rad(main.sun_pos().y)
		var sdir := Vector3(sin(saz), 0, -cos(saz))
		if rad_to_deg(forward().angle_to(sdir)) < FOV_H / 2.0:
			sun_in = 1.0 - main.clouds() * 0.7
	var flick: float = 1.0 if main.weather == "cloudy" or (main.cloud_shadows and main.weather == "clear") else 0.0
	parts["sun"] = 0.002 * flick * clampf(el / 20.0, 0.0, 1.0) + 0.006 * sun_in
	# Rauch, Feuer, Grill im Fächer
	var hot := 0.0
	var sp := sensor_pos()
	for n in main.get_tree().get_nodes_in_group("smoke"):
		if n is Node3D and (n as Node3D).is_visible_in_tree():
			var c: Vector3 = (n as Node3D).global_position - sp
			var hd := Vector2(c.x, c.z).length()
			if hd < 6.0 and rad_to_deg(forward().angle_to(Vector3(c.x, 0, c.z))) < FOV_H / 2.0:
				hot = maxf(hot, 1.0 - hd / 6.0)
	parts["smoke"] = 0.02 * hot * clampf(0.3 + g / 20.0, 0.3, 1.5)
	var tot := 0.0
	var top := 0.0
	for k in parts:
		tot += float(parts[k])
		if float(parts[k]) > top:
			top = float(parts[k])
			_false_cause = k
	return tot


func _rise(t: float, cause: String) -> void:
	out = true
	hi_until = t + TOH
	main.add_event(NAME, "pir", true)
	var e := {"t": snappedf(t, 0.1), "who": who if cause == "" else "", "d": snappedf(who_d, 0.1) if cause == "" else null, "cause": cause}
	if cause == "":
		n_true += 1
	else:
		n_false += 1
	log_.append(e)
	if log_.size() > 20:
		log_ = log_.slice(log_.size() - 20)


func _fall() -> void:
	out = false
	block_until = _t() + TOL
	main.add_event(NAME, "pir", false)


# ---- Fächer am Boden (nur für den Bediener: HELPER_LAYER) --------------------------------------------------------------
func _fan_update() -> void:
	if not show_fan or not on:
		if _fan != null:
			_fan.visible = false
		return
	var r1 := reach("person", true)
	var r2 := reach("person", false)
	var key := "%.1f|%.1f" % [r1, r2]
	if _fan == null:
		_fan = MeshInstance3D.new()
		_fan.layers = main.HELPER_LAYER
		_fan.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		_fan_mat = StandardMaterial3D.new()
		_fan_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_fan_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_fan_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		_fan_mat.vertex_color_use_as_albedo = true
		_fan.material_override = _fan_mat
		main.rig.add_child(_fan)
	_fan.visible = true
	_fan.position = Vector3(0, 0.04, -0.12)
	_fan_mat.albedo_color = Color(1.0, 0.35, 0.3, 1.0) if out else Color(1.0, 0.85, 0.3, 1.0)
	if key == _fan_key:
		return
	_fan_key = key
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n := 24
	for ring in [[0.0, r2, Color(1, 1, 1, 0.30)], [r2, r1, Color(1, 1, 1, 0.14)]]:
		for i in range(n):
			var a0 := deg_to_rad(-FOV_H / 2.0 + FOV_H * i / n)
			var a1 := deg_to_rad(-FOV_H / 2.0 + FOV_H * (i + 1) / n)
			var p := []
			for q in [[ring[0], a0], [ring[1], a0], [ring[1], a1], [ring[0], a1]]:
				p.append(Vector3(sin(q[1]) * q[0], 0, -cos(q[1]) * q[0]))
			st.set_color(ring[2])
			for j in [0, 1, 2, 0, 2, 3]:
				st.add_vertex(p[j])
	_fan.mesh = st.commit()


# ---- Anzeige, Regler, Test-Aktion --------------------------------------------------------------------------------------------
func status_text() -> String:
	if not on:
		return T.t("PIR am Gerät: aus")
	var t := _t()
	var s := T.t("PIR am Gerät (AS312, 100°): %s") % (T.t("wärmt auf (%d s)") % int(ceil(warm_until - t)) if t < warm_until
			else (T.t("BEWEGUNG") if out else (T.t("gesperrt") if t < block_until else T.t("ruhig"))))
	s += "\n" + T.t("Reichweite jetzt bei %.0f °C: quer %.1f m · frontal %.1f m") % [float(main.ambient), reach("person", true), reach("person", false)]
	s += "\n" + T.t("Auslösungen: %d echt · %d Fehlauslösungen") % [n_true, n_false]
	if not log_.is_empty():
		var e: Dictionary = log_[-1]
		s += "\n" + T.t("Zuletzt: %s") % (str(e["who"]) + (" %.1f m" % float(e["d"]) if e["d"] != null else "") if str(e["cause"]) == "" else cause_text(str(e["cause"])))
	if not in_tests and main.busy_with() in ["Prüfstand", "Testlauf"]:
		s += "\n" + T.t("(still während Prüfstand / Testlauf)")
	return s


func cause_text(k: String) -> String:
	return {"air": T.t("Fehlauslösung: warme Luft (Böe)"), "sun": T.t("Fehlauslösung: Sonne (Wolken / tiefe Sonne)"),
			"smoke": T.t("Fehlauslösung: warmer Rauch / Feuer")}.get(k, k)


func add_controls() -> void:
	var g := "Sensoren"
	var P := {"sub": "Bewegungsmelder (PIR)"}
	main.add_control("toggle", "pir_dev", "PIR am Gerät (AS312, vorne, 100°, 3–5 m)", func(): return on, func(v): set_on(bool(v)), g, P)
	main.add_control("toggle", "pir_fan", "Erfassungsfächer am Boden zeigen", func(): return show_fan, func(v): show_fan = bool(v); save(), g, P)
	main.add_control("toggle", "pir_false", "Fehlauslösungen (warme Luft, Sonne, Rauch)", func(): return false_on, func(v): false_on = bool(v); save(), g,
			{"sub": "Bewegungsmelder (PIR)", "expert": true})
	main.add_control("button", "pir_dev_fire", "PIR am Gerät auslösen", null, func(): op({"do": "fire"}), g, {"sub": "Bewegungsmelder (PIR)", "expert": true})


func add_info(parent: Control, ui) -> void:
	info_label = ui.small(main.no_emoji(status_text()))
	info_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	parent.add_child(info_label)


func op(d: Dictionary) -> Dictionary:
	"""Test-Aktion «pir»: {do: info | fire | set (key, value) | reset}"""
	match str(d.get("do", "info")):
		"fire":
			var t := _t()
			if out:
				hi_until = t + TOH
			else:
				block_until = 0.0
				who = T.t("Knopf")
				who_d = 0.0
				_rise(t, "")
		"set":
			var k := str(d.get("key", ""))
			var v = d.get("value", true)
			match k:
				"on":
					set_on(bool(v))
				"show_fan":
					show_fan = bool(v)
				"false_on":
					false_on = bool(v)
				"in_tests":
					in_tests = bool(v)
				"warm":
					warm_until = _t() + float(v)              # Sekunden Aufwärmen (0 = sofort bereit)
		"reset":
			n_true = 0
			n_false = 0
			log_.clear()
	return {"ok": true, "on": on, "out": out, "sig": snappedf(sig, 0.01), "who": who, "who_d": snappedf(who_d, 0.1),
			"warm": maxf(0.0, warm_until - _t()), "blocked": maxf(0.0, block_until - _t()), "n_true": n_true, "n_false": n_false,
			"reach_across": snappedf(reach("person", true), 0.1), "reach_front": snappedf(reach("person", false), 0.1),
			"ambient_c": main.ambient, "false_rate_s": snappedf(_false_rate(), 0.0001), "log": log_.slice(maxi(0, log_.size() - 8)),
			"pos": [snappedf(sensor_pos().x, 0.01), snappedf(sensor_pos().z, 0.01)], "fwd": [snappedf(forward().x, 0.01), snappedf(forward().z, 0.01)],
			"status": status_text()}


