extends Node
## F6 «Wind» (31.10.2026): Gras, Büsche, Baumkronen und Zeltplanen bewegen sich im Wind (Vertex-Shader), Stärke aus dem
## Wetter (main.wind × main.gust(): Regler «Wind», Schalter «Böen»), Böen rollen als Wellen in Windrichtung über Wiese
## und Bäume. Lite: Gras still, Bäume / Büsche / Zelte schwach. Schalter: Wetter → Natur und Wind.
## The shaders: grass_wind.gdshader (meadow tufts, scenes.gd meadow()), tent_wind.gdshader (tent fabric, scenes.gd /
## szenenplus.gd), foliage.gdshader (crowns, bushes, hedges - main.foliage_mats, new uniforms gust_amt / dir).
## Flags and laundry (cloth.gdshader) and loose tarps (flap.gdshader) move as before (main.cloth_mats).

const Quality = preload("res://scripts/quality.gd")
const SAVE := "user://wind_fx.json"

var main
var on := true                         # «Wind bewegt Gras, Büsche, Bäume und Zelte»
var grass_mats := {}                   # colour -> ShaderMaterial
var tent_mats: Array = []
var dir_a := 0.65                      # where the wind blows to (rad, world x/z); turns slowly
var _t := 0.0


func _ready() -> void:
	var f := FileAccess.open(SAVE, FileAccess.READ)
	if f != null:
		var d = JSON.parse_string(f.get_as_text())
		if typeof(d) == TYPE_DICTIONARY:
			on = bool(d.get("on", true))


func _save() -> void:
	var f := FileAccess.open(SAVE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"on": on}))


func grass_mat(col: Color) -> Material:
	"""scenes.gd meadow(): the material of the grass tufts (one per colour, shared)"""
	var k := col.to_html()
	if not grass_mats.has(k):
		var m := ShaderMaterial.new()
		m.shader = load("res://shaders/grass_wind.gdshader")
		m.set_shader_parameter("color", col)
		m.set_shader_parameter("noise_tex", main.noise_tex)
		grass_mats[k] = m
		_apply_one(m, _wind_now(), true)
	return grass_mats[k]


func tent_mat(col: Color, h := 1.5) -> Material:
	"""scenes.gd / szenenplus.gd: tent and flysheet (PrismMesh) - the fabric moves in the wind"""
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/tent_wind.gdshader")
	m.set_shader_parameter("color", col)
	m.set_shader_parameter("tent_h", h)
	m.set_shader_parameter("seed", randf() * 10.0)
	m.set_shader_parameter("noise_tex", main.noise_tex)
	tent_mats.append(m)
	_apply_one(m, _wind_now(), false)
	return m


func _wind_now() -> float:
	return float(main.wind) * float(main.gust()) if main != null else 0.0


func amounts() -> Array:
	"""[grass, trees / bushes / tents]: 0 = still"""
	if not on:
		return [0.0, 0.0]
	if Quality.lite():
		return [0.0, 0.4]
	return [1.0, 1.0]


func _apply_one(m: ShaderMaterial, w: float, grass: bool) -> void:
	var am := amounts()
	m.set_shader_parameter("wind", w)
	m.set_shader_parameter("amount", am[0] if grass else am[1])
	if grass:
		m.set_shader_parameter("dir", Vector2(cos(dir_a), sin(dir_a)))


func _process(dt: float) -> void:
	_t -= dt
	if _t > 0.0 or main == null:
		return
	_t = 0.1                                             # 10 × per second is enough (the shaders move on their own)
	dir_a = 0.65 + 0.35 * sin(main.now() * 0.003)        # the direction wanders a little
	var w := _wind_now()
	var am := amounts()
	var d := Vector2(cos(dir_a), sin(dir_a))
	for m in grass_mats.values():
		m.set_shader_parameter("wind", w)
		m.set_shader_parameter("amount", am[0])
		m.set_shader_parameter("dir", d)
	for i in range(tent_mats.size() - 1, -1, -1):
		var tm = tent_mats[i]
		if tm == null or (tm as RefCounted).get_reference_count() <= 1:
			tent_mats.remove_at(i)                       # the scene was changed: only this list still had it
			continue
		tm.set_shader_parameter("wind", w)
		tm.set_shader_parameter("amount", am[1])
	for fm in main.foliage_mats:
		if is_instance_valid(fm):
			fm.set_shader_parameter("gust_amt", am[1])
			fm.set_shader_parameter("dir", d)


func add_controls() -> void:
	main.add_control("toggle", "wind_plants", "Wind bewegt Gras, Büsche, Baumkronen und Zeltplanen (Böen als Wellen; Lite: schwach)",
			func(): return on, func(v): on = bool(v); _save(); _t = 0.0, "Wetter", {"sub": "Natur und Wind"})


func control(d: Dictionary) -> Dictionary:
	"""test action {"action": "wind_fx", "do": info | set (on)}"""
	if str(d.get("do", "info")) == "set":
		on = bool(d.get("on", on))
		_save()
		_t = 0.0
	return {"ok": true, "on": on, "wind_kmh": snappedf(_wind_now(), 0.1), "amounts": amounts(), "grass_mats": grass_mats.size(),
			"tent_mats": tent_mats.size(), "foliage_mats": main.foliage_mats.size(), "lite": Quality.lite()}
