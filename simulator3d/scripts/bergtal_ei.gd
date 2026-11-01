extends Node
## Bergtal · ein Geheimnis (Entscheid des Besitzers 1.11.2026, Paket real-easter-egg). NICHTS davon in Hilfe, Blinki oder Anleitung –
## nur der Satz «Psst …» im Fenster «Über den Simulator» (mehr.gd), wie in MoveEye (Teil 584).
##
## Ablauf (Spoiler, nur für Entwickler):
##   1. Hinweis: nachts blinkt das rote Flugwarnlicht der Chalchstock-Antenne nicht gleichmässig, sondern im Muster MUSTER
##      (k = kurz, l = lang), danach eine Pause. Am Tag brennt es ruhig und schwach.
##   2. Antwort: Kopfkamera von MoveEye oder die Ansicht des Simulators grob auf die Antenne richten (AIM_DEG) und das Muster
##      mit dem Lichtknopf nachblinken – MoveEyes Licht kommt mit dem Zustand («lights.white», ca. 10× pro Sekunde, main.on_state),
##      ohne MoveEye der Lichtknopf des Simulators (Fenster «Kopf» / Controller, main.mw_light). Die Zeiten werden grosszügig
##      gelesen: nur «lang ist deutlich länger als kurz» (Verhältnis), Lücken bis 3.5 s – so stören wenige Bilder/s und
##      Netzwerk-Verzögerung nicht.
##   3. Reaktion: die Antenne blinkt dreimal schnell, dann schwenkt vom Gipfel ein Lichtkegel ins Tal und bleibt HOLD_S auf dem
##      Tuffwasserfall (bergtal_ziele.gd) stehen.
##   4. Versteck: am Fuss der Tuffwand, hinter dem Hauptfaden, rollt ein bemooster Stein zur Seite – eine kleine, dunkle Höhle
##      (bleibt offen, bis der Simulator neu startet; auch wenn der Schlafplatz wechselt und das Tal neu gebaut wird). Darin sitzt
##      ein dunkles Murmeltier, mit blossem Auge kaum zu sehen; im Wärmebild (Kopf-Wärmekamera, Ansicht «Wärmebild» des Simulators
##      und MoveEyes Wärme-Ansicht) leuchtet es warm (Zwilling auf Ebene 2, wie alles in main.add_mesh).
##   5. Finale: auf dem Murmeltier ein grosses Herz im Gegenuhrzeigersinn zeichnen (ccw_heart: dieselben Regeln wie ccw_heart in
##      MoveEye quelle/230_waermebild.py und ccwHeart in 510) – im Simulator-Fenster mit Maus / Finger, oder in MoveEyes
##      Live-Ansicht über dem Bild (Teil 639z: reply() meldet, wo das Murmeltier im Bild der Kopfkamera ist, MoveEye schickt
##      {"action": "egg", "do": "heart", "x", "y"}). Dann dreht es sich um und zeigt auf dem Bauch das Muster belly_matrix()
##      (BELLY = _BELLY in Teil 230, nur mit Zoom lesbar), Herzchen, ein leiser Pfiff, Tusch (klang.gd). Gefunden: Eintrag ID im Entdeckungsbuch
##      (erst jetzt angemeldet, also vorher kein «???» und kein Blinki-Hinweis) + geheimes Abzeichen (spielbereich.badges()).
## Lite: Höhle mit weniger Flächen, keine Steine rundum, Kegel mit einfachem Material.
## Testbefehl (Entwickler): {"action": "egg", "do": "info | light (on) | signal (falsch) | beam | cave | heart (x, y | auto) |
##   belly | look (what: antenna | beam | waterfall | cave | belly | head | thermal) | place | reset"}. Test ohne Bild: werkzeuge/ei_test.gd.

const T = preload("res://scripts/i18n.gd")
const Ziele = preload("res://scripts/bergtal_ziele.gd")
const Waerme = preload("res://scripts/waerme.gd")
const Quality = preload("res://scripts/quality.gd")

const MUSTER := "kklkl"                          # the signal: short short long short long
const KURZ := 0.35
const LANG := 1.15
const LUECKE := 0.45
const PAUSE := 3.2
const AIM_DEG := 20.0                            # «roughly at the antenna»: so far off the middle of the picture
const GAP_MAX := 3.5                             # longer dark = a new try
const ON_MAX := 3.5
const RATIO := 1.4                               # the shortest long one at least 1.4 × the longest short one
const ACK_S := 0.7                               # three fast flashes, then the beam
const SWING_S := 7.0
const HOLD_S := 30.0
const BELLY := "25:fe87bfc14c106eb2ebb75df5dba6aaec172507faaafe006700ce29179083c51cf8728e897041b1972f895c703f641812f524ff98ff0049463f8eab9055117ba9afa5d29fbee9fec505c09efe89178"
const ID := "berg.geheim.murmeltier"
const BADGE := "geheim_murmeltier"
const U0 := 1.4                                  # the cave: along the wall, under the main thread of water

static var cave_open_run := false                # opened in this run of the simulator (survives a new build of the valley)
static var _halo_tex: ImageTexture
static var _heart_tex: ImageTexture
static var _pfiff: AudioStreamWAV

var bt
var m
var lite := false
var stage := "idle"                              # idle | ack | swing | hold | open | turned
var _t0 := 0.0                                   # real time when the stage began
var top := Vector3.ZERO                          # the red light (valley coordinates)
var lamp: MeshInstance3D
var _lamp_mat: StandardMaterial3D
var _lamp_light: OmniLight3D
var _halo: MeshInstance3D
var _beam: MeshInstance3D
var _beam_mat: Material
var _spot: SpotLight3D
var _aim_w := Vector3.ZERO                       # where the beam ends (the waterfall)
var _aim_s := Vector3.ZERO                       # where it starts its swing
var cave: Node3D
var _slab: Node3D
var _slab_p0 := Vector3.ZERO
var marmot: Node3D
var _belly: MeshInstance3D
var _xf := Transform3D.IDENTITY                  # the frame of the wall (u along it, v up, w to the pool)
var _floor := 0.0
var _wc := 0.0                                   # the back of the cave (w in the frame of the wall)
var _phases: Array = []                          # [[t_on, t_off, aimed], …]
var _on := {}                                    # source -> [t_on, aimed] while lit
var _lit := {}                                   # source -> lit now
var tries := 0
var tusch := false                               # the flourish of klang.gd was played (info; false without sound / headless)
var tusch_n := 0                                 # how often it was asked for (tests)
var last := ""                                   # the last answer («ok», «muster», «zielen», «tag»)
var _open_t := -1.0
var _turn_t := -1.0
var _fx: Array = []                              # hearts [node, t0, v]
var _draw: Array = []                            # points of the heart being drawn (screen)
var _drawing := false
var _trail: Line2D
var _layer: CanvasLayer
var _rng := RandomNumberGenerator.new()
var _snd: AudioStreamPlayer3D


func _init(bt_) -> void:
	bt = bt_
	m = bt.m
	lite = bool(bt.lite) or Quality.lite()
	_rng.seed = 2511
	name = "bergtal_ei"


static func _rt() -> float:
	return Time.get_ticks_msec() / 1000.0


func build(antenna_top: Vector3) -> void:
	top = antenna_top
	_lamp()
	_cave()
	_marmot()
	_beam_build()
	if cave_open_run or _found():
		_open(true)
	if _found():
		_register()
	m.bt_ei = self


# =============================================================================================================================
# 1. the red light on the antenna
# =============================================================================================================================
func _lamp() -> void:
	lamp = MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.18
	sm.height = 0.3
	sm.radial_segments = 10
	sm.rings = 6
	lamp.mesh = sm
	_lamp_mat = StandardMaterial3D.new()
	_lamp_mat.albedo_color = Color(0.55, 0.06, 0.04)
	_lamp_mat.emission_enabled = true
	_lamp_mat.emission = Color(1.0, 0.12, 0.06)
	_lamp_mat.emission_energy_multiplier = 0.4
	lamp.material_override = _lamp_mat
	lamp.position = top
	lamp.layers = 1
	bt.tal.add_child(lamp)
	_lamp_light = OmniLight3D.new()
	_lamp_light.light_color = Color(1.0, 0.15, 0.08)
	_lamp_light.omni_range = 6.0
	_lamp_light.light_energy = 0.0
	_lamp_light.position = top
	bt.tal.add_child(_lamp_light)
	# a glow around it that keeps a few pixels in size far away (the Chalchstock is hundreds of metres from the places)
	_halo = MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(1, 1)
	_halo.mesh = q
	var hm := StandardMaterial3D.new()
	hm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	hm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	hm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	hm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	hm.albedo_texture = _halo_texture()
	hm.albedo_color = Color(1.0, 0.18, 0.08)
	hm.no_depth_test = false
	hm.cull_mode = BaseMaterial3D.CULL_DISABLED
	_halo.material_override = hm
	_halo.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_halo.position = top
	_halo.layers = 1
	bt.tal.add_child(_halo)


static func _halo_texture() -> ImageTexture:
	if _halo_tex == null:
		var img := Image.create(64, 64, false, Image.FORMAT_RGBA8)
		for y in range(64):
			for x in range(64):
				var d := Vector2(x - 31.5, y - 31.5).length() / 31.5
				var a := clampf(pow(1.0 - d, 2.2), 0.0, 1.0) if d < 1.0 else 0.0
				img.set_pixel(x, y, Color(1, 1, 1, a))
		_halo_tex = ImageTexture.create_from_image(img)
	return _halo_tex


static func pattern_on(t: float) -> bool:
	"""the light of the pattern at time t (seconds): k / l with gaps, then a pause"""
	var seq := []
	for c in MUSTER:
		seq.append(KURZ if c == "k" else LANG)
	var cyc := PAUSE
	for d in seq:
		cyc += float(d) + LUECKE
	var x := fposmod(t, cyc)
	for d in seq:
		if x < float(d):
			return true
		x -= float(d)
		if x < LUECKE:
			return false
		x -= LUECKE
	return false


static func ack_on(t: float) -> bool:
	"""the answer of the antenna: three fast flashes (0 / 0.24 / 0.48 s) while «ack» lasts (ACK_S)"""
	return t >= 0.0 and t < ACK_S and fposmod(t, 0.24) < 0.12


func _lamp_tick() -> void:
	var dark: bool = m.is_dark()
	var on := false
	var e := 0.4
	if stage == "ack":
		on = ack_on(_rt() - _t0)                        # three times fast
		e = 6.0
	elif dark:
		on = pattern_on(_rt())
		e = 5.0
	else:
		on = true                                       # by day: steady and weak
		e = 0.35
	_lamp_mat.emission_energy_multiplier = e if on else 0.0
	_lamp_light.light_energy = (1.2 if dark else 0.0) if on and e > 1.0 else 0.0
	_halo.visible = on and dark
	if _halo.visible:
		var cam: Camera3D = m.view_cam
		var d := 50.0
		if cam != null:
			d = maxf(cam.global_position.distance_to(lamp.global_position), m.cams[0].global_position.distance_to(lamp.global_position) if m.cams.size() > 0 else 0.0)
		var s := clampf(d * 0.008, 0.9, 14.0)
		_halo.scale = Vector3(s, s, s)


# =============================================================================================================================
# 2. the answer: the light of MoveEye (state) or of the simulator (own button), read generously
# =============================================================================================================================
func aimed() -> bool:
	"""the head camera of MoveEye or the view of the simulator looks roughly at the light"""
	if lamp == null or not is_instance_valid(lamp):
		return false
	var p := lamp.global_position
	for cam in [m.view_cam, m.cams[0] if m.cams.size() > 0 else null]:
		if cam == null or not is_instance_valid(cam):
			continue
		var fw: Vector3 = -(cam as Camera3D).global_transform.basis.z
		var to: Vector3 = p - (cam as Camera3D).global_position
		if to.length() > 1.0 and rad_to_deg(fw.angle_to(to)) < AIM_DEG:
			return true
	return false


func on_light(on: bool, src := "mw") -> void:
	"""the white light of MoveEye (every state) or a press of the light button here"""
	if bool(_lit.get(src, false)) == on:
		return
	_lit[src] = on
	var t := _rt()
	if on:
		_on[src] = [t, aimed()]
	elif _on.has(src):
		var a: Array = _on[src]
		_on.erase(src)
		_phase(float(a[0]), t, bool(a[1]) or aimed())


func _phase(t_on: float, t_off: float, aim: bool) -> bool:
	if not _phases.is_empty() and t_on - float(_phases[-1][1]) > GAP_MAX:
		_phases.clear()
	_phases.append([t_on, t_off, aim])
	while _phases.size() > 8:
		_phases.pop_front()
	return _check()


func _check() -> bool:
	var n := MUSTER.length()
	if _phases.size() < n:
		return false
	var ph: Array = _phases.slice(_phases.size() - n)
	var long_min := INF
	var short_max := 0.0
	var aims := 0
	for i in range(n):
		var d := float(ph[i][1]) - float(ph[i][0])
		if d < 0.03 or d > ON_MAX:
			return false
		if i > 0 and float(ph[i][0]) - float(ph[i - 1][1]) > GAP_MAX:
			return false
		if MUSTER[i] == "l":
			long_min = minf(long_min, d)
		else:
			short_max = maxf(short_max, d)
		aims += 1 if bool(ph[i][2]) else 0
	if not (long_min >= short_max * RATIO and long_min >= 0.3):
		return false
	tries += 1
	if aims < n - 1:
		last = "zielen"
		return false
	if not m.is_dark():
		last = "tag"
		return false
	if stage in ["ack", "swing", "hold"]:
		return false
	last = "ok"
	_phases.clear()
	_go("ack")
	return true


func _go(st: String) -> void:
	stage = st
	_t0 = _rt()
	if st == "swing":
		_beam.visible = true
	elif st == "hold":
		_spot.visible = true
		_open(false)


# =============================================================================================================================
# 3. the beam from the summit to the waterfall
# =============================================================================================================================
func _beam_build() -> void:
	_aim_w = _xf * Vector3(U0, _floor + 4.5, float(bt.ziele._wall_z(U0, _floor + 4.5)) + 0.3)   # (valley coordinates) the waterfall above the cave
	var dirv := (_aim_w - top)
	var side := Vector3(-dirv.z, 0, dirv.x).normalized()
	_aim_s = top + dirv * 0.35 + side * dirv.length() * 0.3 + Vector3(0, -20, 0)
	_beam = MeshInstance3D.new()
	var cm := CylinderMesh.new()                       # real size (set in _beam_to): a scaled mesh would bend the normals
	cm.top_radius = 0.12
	cm.bottom_radius = 1.0
	cm.height = 1.0
	cm.radial_segments = 10 if lite else 20
	cm.rings = 1
	cm.cap_top = false
	cm.cap_bottom = false
	_beam.mesh = cm
	if lite:
		var sm := StandardMaterial3D.new()
		sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		sm.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		sm.cull_mode = BaseMaterial3D.CULL_DISABLED
		sm.albedo_color = Color(1.0, 0.95, 0.8, 0.1)
		sm.no_depth_test = false
		_beam_mat = sm
	else:
		var sh := Shader.new()
		sh.code = """shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;
uniform float amount = 1.0;
uniform vec3 col = vec3(1.0, 0.95, 0.82);
void fragment() {
	float edge = pow(clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0), 1.4);
	float along = mix(1.0, 0.5, UV.y) * smoothstep(1.0, 0.75, UV.y);
	float dust = 0.85 + 0.15 * sin(UV.y * 40.0 - TIME * 0.7 + UV.x * 9.0);
	ALBEDO = col;
	ALPHA = clamp(0.45 * amount * edge * along * dust, 0.0, 1.0);
}
"""
		var mat := ShaderMaterial.new()
		mat.shader = sh
		_beam_mat = mat
	_beam.material_override = _beam_mat
	_beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_beam.layers = 1
	_beam.visible = false
	bt.tal.add_child(_beam)
	_spot = SpotLight3D.new()
	_spot.light_color = Color(1.0, 0.95, 0.82)
	_spot.spot_range = 48.0
	_spot.spot_angle = 5.0
	_spot.spot_attenuation = 0.6
	_spot.light_energy = 0.0
	_spot.shadow_enabled = false
	_spot.visible = false
	bt.tal.add_child(_spot)


func _beam_amount(a: float) -> void:
	if _beam_mat is ShaderMaterial:
		(_beam_mat as ShaderMaterial).set_shader_parameter("amount", a)
	else:
		(_beam_mat as StandardMaterial3D).albedo_color.a = 0.1 * a


func _beam_to(target: Vector3) -> void:
	var v := target - top
	v -= v.normalized() * minf(7.0, v.length() * 0.5)   # it fades out just before the wall (the spot light makes the patch)
	var L := maxf(1.0, v.length())
	var y := -v / L                                     # the mesh: narrow end (+y) at the light
	var x := y.cross(Vector3.UP)
	if x.length() < 0.01:
		x = Vector3.RIGHT
	x = x.normalized()
	var z := x.cross(y).normalized()
	var cm := _beam.mesh as CylinderMesh
	if absf(cm.height - L) > 0.5:
		cm.height = L
		cm.bottom_radius = clampf(L * 0.0035, 0.8, 3.5)  # ≈ 0.2°: 3.5 m wide at 1 km
	_beam.transform = Transform3D(Basis(x, y, z), top + v / 2.0)


func beam_target() -> Vector3:
	var t := _rt() - _t0
	match stage:
		"swing":
			return _aim_s.lerp(_aim_w, smoothstep(0.0, 1.0, t / SWING_S))
		"hold", "open", "turned":
			return _aim_w
	return _aim_s


func _beam_tick() -> void:
	var t := _rt() - _t0
	match stage:
		"ack":
			if t >= ACK_S:
				_go("swing")
		"swing":
			_beam_amount(clampf(t / 1.2, 0.0, 1.0))
			_beam_to(beam_target())
			if t >= SWING_S:
				_go("hold")
		"hold":
			_beam_to(_aim_w)
			var f := 1.0 - clampf((t - HOLD_S) / 2.0, 0.0, 1.0)
			_beam_amount(f)
			var lit := _xf * Vector3(U0, _floor + 6.0, _wc)         # the light falls on the wall above the cave, not into it
			var back := (top - lit).normalized()
			_spot.position = lit + back * 34.0
			_spot.look_at(bt.W(lit), Vector3.UP if absf(back.y) < 0.95 else Vector3.FORWARD)
			_spot.light_energy = 7.0 * f
			if t >= HOLD_S + 2.0:
				_beam.visible = false
				_spot.visible = false
				_go("turned" if _turn_t >= 0.0 else "open")


# =============================================================================================================================
# 4. the cave behind the waterfall, and its dark marmot
# =============================================================================================================================
func _cave() -> void:
	var z: Object = bt.ziele
	_xf = Transform3D(Basis(Vector3.UP, PI / 2.0), Vector3(Ziele.FALL.x, Ziele.pool_level, Ziele.FALL.y))
	_wc = float(z.cave_back())                           # the tuff wall bulges here and there: the cave stands in front of all of it
	var mouth: Vector3 = _xf * Vector3(U0, 0.0, _wc + 1.4)
	_floor = maxf(float(bt.H(mouth.x, mouth.z)), Ziele.pool_level + 0.25) - Ziele.pool_level
	cave = Node3D.new()
	cave.name = "ei_hoehle"
	cave.transform = _xf * Transform3D(Basis(), Vector3(U0, _floor, _wc))
	bt.tal.add_child(cave)
	# a half dome against the wall (local: x along the wall, y up, z towards the pool), the mouth on the front
	var a := 1.25
	var b := 1.15
	var c := 1.5
	var np := 10 if lite else 22
	var nt := 4 if lite else 9
	var outer := SurfaceTool.new()
	var inner := SurfaceTool.new()
	outer.begin(Mesh.PRIMITIVE_TRIANGLES)
	inner.begin(Mesh.PRIMITIVE_TRIANGLES)
	var tuff: Array = Ziele.TUFF
	var moss: Array = Ziele.MOSS_C
	var winter: bool = str(bt.season) == "winter"
	var P := []
	var C := []
	for j in range(nt + 1):
		var th := (PI / 2.0) * float(j) / nt
		for i in range(np + 1):
			var ph := -PI / 2.0 + PI * float(i) / np
			var k := 1.0 + (0.1 * sin(ph * 5.0 + th * 3.0) + 0.06 * sin(ph * 11.0 - th * 7.0) if j < nt and i > 0 and i < np else 0.0)
			P.append(Vector3(a * sin(ph) * cos(th) * k, b * sin(th) * k, c * cos(ph) * cos(th) * k))
			var col: Color = (tuff[(i + j) % 3] as Color).lerp(moss[(i * 7 + j) % 3], 0.0 if winter else clampf(0.25 + 0.5 * sin(i * 1.3 + j * 0.8), 0.0, 0.8))
			C.append(col)
	for j in range(nt):
		var th := (PI / 2.0) * (j + 0.5) / nt
		for i in range(np):
			var ph := -PI / 2.0 + PI * (i + 0.5) / np
			if absf(ph) < 0.55 and th < 0.9:
				continue                                    # the mouth
			var q0 := j * (np + 1) + i
			var q := [q0, q0 + 1, q0 + np + 2, q0, q0 + np + 2, q0 + np + 1]   # (Godot: clockwise = front - this one looks in)
			for kk in [q[0], q[2], q[1], q[3], q[5], q[4]]:
				outer.set_color(C[kk])
				outer.add_vertex(P[kk])
			for kk in q:
				inner.set_color(Color(0.035, 0.03, 0.026))
				inner.add_vertex(P[kk] * 0.97)
	outer.generate_normals()
	inner.generate_normals()
	var om := StandardMaterial3D.new()
	om.vertex_color_use_as_albedo = true
	om.roughness = 0.95
	var im := StandardMaterial3D.new()
	im.vertex_color_use_as_albedo = true
	im.roughness = 1.0
	var cool: float = float(m.ambient) - 2.0          # inside: cool rock (no sun) - the marmot stands out in the thermal picture
	m.add_mesh(cave, outer.commit(), Vector3.ZERO, om, "stone")
	m.add_mesh(cave, inner.commit(), Vector3.ZERO, im, cool)
	var dark := StandardMaterial3D.new()
	dark.albedo_color = Color(0.03, 0.026, 0.022)
	dark.roughness = 1.0
	var fl := CylinderMesh.new()
	fl.top_radius = 1.0
	fl.bottom_radius = 1.0
	fl.height = 0.06
	fl.radial_segments = 12
	m.add_mesh(cave, fl, Vector3(0, 0.01, 0.2), dark, cool, Vector3.ZERO, Vector3(a * 0.95, 1.0, c * 0.8))
	m.add_mesh(cave, _box(2.3, 1.15, 0.08), Vector3(0, 0.55, -0.05), dark, cool)
	# the stone in front of the mouth (looks like part of the wall); it rolls aside when the light comes
	_slab = Node3D.new()
	_slab_p0 = Vector3(0, 0.42, c * 0.86)
	_slab.position = _slab_p0
	cave.add_child(_slab)
	var sm := SphereMesh.new()
	sm.radius = 0.5
	sm.height = 1.0
	sm.radial_segments = 8 if lite else 16
	sm.rings = 5 if lite else 10
	var stm := StandardMaterial3D.new()
	stm.albedo_color = (tuff[1] as Color).lerp(moss[0], 0.0 if winter else 0.45)
	stm.roughness = 0.95
	m.add_mesh(_slab, sm, Vector3.ZERO, stm, "stone", Vector3.ZERO, Vector3(1.75, 1.05, 0.75))
	if not lite:                                          # a few stones around: the dome grows out of the scree
		for i in range(6):
			var u := -1.6 + i * 0.64 + _rng.randf_range(-0.15, 0.15)
			var sz := _rng.randf_range(0.18, 0.34)
			var sp := Vector3(u, sz * 0.4, 1.0 + 0.55 * cos(u * 1.2) + _rng.randf_range(-0.1, 0.1))
			if absf(u) < 0.7:
				sp.z += 0.55
			var gm := StandardMaterial3D.new()
			gm.albedo_color = (tuff[i % 3] as Color).darkened(0.1)
			gm.roughness = 0.95
			var gs := SphereMesh.new()
			gs.radius = sz
			gs.height = sz * 1.6
			gs.radial_segments = 8
			gs.rings = 4
			m.add_mesh(cave, gs, sp, gm, "stone")
	# a thin veil of water in front of the mouth («behind the waterfall»): streaks with gaps, no thermal twin (the thermal
	# camera looks through it - like the rest of the threads of the wall)
	if not winter:
		var vq := QuadMesh.new()
		vq.size = Vector2(1.6, 1.25)
		var vm := MeshInstance3D.new()
		vm.mesh = vq
		var vs := Shader.new()
		vs.code = """shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;
void fragment() {
	float s = 0.5 + 0.5 * sin(UV.x * 37.0 + sin(UV.y * 3.0) * 1.5);
	float band = 0.5 + 0.5 * sin((UV.y * 2.0 - TIME * 2.2) * 6.2832 + UV.x * 4.0);
	float e = smoothstep(0.0, 0.18, UV.x) * smoothstep(1.0, 0.82, UV.x);
	ALBEDO = vec3(0.55, 0.58, 0.6) * (0.6 + 0.4 * band);
	ALPHA = clamp(smoothstep(0.55, 0.95, s) * (0.25 + 0.3 * band) * e, 0.0, 0.7);
	ROUGHNESS = 0.2;
	SPECULAR = 0.6;
}
"""
		var vmat := ShaderMaterial.new()
		vmat.shader = vs
		vm.material_override = vmat
		vm.position = Vector3(0, 0.62, c * 1.02 + 0.12)
		vm.layers = 1
		vm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		cave.add_child(vm)


func _box(x: float, y: float, z: float) -> BoxMesh:
	var bx := BoxMesh.new()
	bx.size = Vector3(x, y, z)
	return bx


func _sph(r: float, segs := 10) -> SphereMesh:
	var s := SphereMesh.new()
	s.radius = r
	s.height = r * 2.0
	s.radial_segments = segs
	s.rings = maxi(4, segs / 2)
	return s


func _marmot() -> void:
	"""sitting up, back to the mouth (facing the back of the cave); fur very dark - in the dark nearly invisible"""
	marmot = Node3D.new()
	marmot.name = "ei_murmeltier"
	marmot.position = Vector3(0.05, 0.03, 0.45)
	marmot.rotation.y = PI                              # local +z = where it looks: now to the back of the cave
	cave.add_child(marmot)
	var fur := StandardMaterial3D.new()
	fur.albedo_color = Color(0.085, 0.062, 0.045)
	fur.roughness = 1.0
	var pale := StandardMaterial3D.new()
	pale.albedo_color = Color(0.13, 0.1, 0.075)
	pale.roughness = 1.0
	var blk := StandardMaterial3D.new()
	blk.albedo_color = Color(0.02, 0.015, 0.012)
	var amb: float = float(m.ambient)
	var tb := warm_c()                                  # warmer than a sun-warmed rock at night: it glows in the thermal picture
	var th := tb + 2.0
	var te := tb + 5.0
	var s := 8 if lite else 14
	m.add_mesh(marmot, _sph(0.17, s), Vector3(0, 0.25, 0), fur, tb, Vector3.ZERO, Vector3(1.0, 1.45, 0.9))
	m.add_mesh(marmot, _sph(0.13, s), Vector3(0, 0.23, 0.085), pale, tb + 1.0, Vector3.ZERO, Vector3(0.9, 1.3, 0.55))
	m.add_mesh(marmot, _sph(0.1, s), Vector3(0, 0.5, 0.03), fur, th, Vector3.ZERO, Vector3(1.05, 0.9, 1.0))
	m.add_mesh(marmot, _sph(0.05, 8), Vector3(0, 0.475, 0.11), pale, th)
	m.add_mesh(marmot, _sph(0.016, 6), Vector3(0, 0.49, 0.158), blk, te)
	for sx in [-1.0, 1.0]:
		m.add_mesh(marmot, _sph(0.026, 6), Vector3(sx * 0.07, 0.585, 0.0), fur, th)
		m.add_mesh(marmot, _sph(0.014, 6), Vector3(sx * 0.042, 0.52, 0.105), blk, te)
		m.add_mesh(marmot, _sph(0.035, 6), Vector3(sx * 0.06, 0.34, 0.13), fur, tb)
		m.add_mesh(marmot, _sph(0.05, 6), Vector3(sx * 0.085, 0.025, 0.05), fur, tb - 2.0, Vector3.ZERO, Vector3(1.0, 0.5, 1.6))
	m.add_mesh(marmot, _sph(0.06, 8), Vector3(0, 0.06, -0.2), fur, tb - 3.0, Vector3.ZERO, Vector3(0.7, 0.5, 1.8))
	# the belly: the same pattern as the marmot of MoveEye (belly_matrix, part 230) - one square ≈ 3 mm
	_belly = MeshInstance3D.new()
	var q := QuadMesh.new()
	q.size = Vector2(0.09, 0.09)
	_belly.mesh = q
	var bm := StandardMaterial3D.new()
	bm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	bm.albedo_texture = belly_texture()
	bm.albedo_color = Color(0.7, 0.7, 0.7)
	bm.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	_belly.material_override = bm
	_belly.position = Vector3(0, 0.26, 0.162)
	_belly.layers = 1
	_belly.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	marmot.add_child(_belly)


func warm_c() -> float:
	var amb: float = float(m.ambient)
	return maxf(maxf(Waerme.animal("marmot", amb, "body"), amb + 16.0), 30.0)


static func belly_matrix() -> Array:
	"""the same as belly_matrix() in MoveEye (230): rows of bools"""
	var parts := BELLY.split(":")
	var n := int(parts[0])
	var bits := ""
	for ch in parts[1]:
		var v := ("0123456789abcdef").find(ch)
		for k in [8, 4, 2, 1]:
			bits += "1" if v & k else "0"
	var out := []
	for r in range(n):
		var row := []
		for c in range(n):
			row.append(bits[r * n + c] == "1")
		out.append(row)
	return out


static func belly_texture() -> ImageTexture:
	var bm := belly_matrix()
	var n := bm.size()
	var img := Image.create(n + 4, n + 4, false, Image.FORMAT_RGB8)
	img.fill(Color8(0xc9, 0x9d, 0x6e))                   # like microBelly in 510
	for r in range(n):
		for c in range(n):
			if bm[r][c]:
				img.set_pixel(c + 2, r + 2, Color8(0x6e, 0x45, 0x29))
	return ImageTexture.create_from_image(img)


func _open(now_: bool) -> void:
	if _open_t >= 0.0:
		return
	cave_open_run = true
	_open_t = _rt() - (10.0 if now_ else 0.0)
	if stage == "idle":
		stage = "open"


func cave_open() -> bool:
	return _open_t >= 0.0


func _cave_tick() -> void:
	if _open_t >= 0.0 and _slab != null:
		var f := smoothstep(0.0, 1.0, clampf((_rt() - _open_t) / 3.0, 0.0, 1.0))
		_slab.position = _slab_p0 + Vector3(1.55 * f, -0.12 * f, 0.25 * f)
		_slab.rotation = Vector3(0, 0, -1.6 * f)
	if _turn_t >= 0.0 and marmot != null:
		var g := smoothstep(0.0, 1.0, clampf((_rt() - _turn_t) / 1.3, 0.0, 1.0))
		marmot.rotation.y = PI * (1.0 - g)
		var hop := clampf((_rt() - _turn_t - 1.3) / 0.35, 0.0, 1.0)
		marmot.position.y = 0.03 + 0.06 * sin(hop * PI)


# =============================================================================================================================
# 5. the heart, the turn, the belly, the badge
# =============================================================================================================================
static func ccw_heart(P: Array, min_size := 90.0) -> bool:
	"""a big closed heart drawn counter-clockwise (screen: y down) - the rules of ccw_heart (MoveEye 230) / ccwHeart (510)"""
	if P.size() < 12:
		return false
	var left := INF
	var right := -INF
	var top_ := INF
	var bot := -INF
	for p in P:
		left = minf(left, p.x)
		right = maxf(right, p.x)
		top_ = minf(top_, p.y)
		bot = maxf(bot, p.y)
	var w := right - left
	var h := bot - top_
	var size := maxf(w, h)
	var asp := w / maxf(h, 1e-6)
	if size < min_size or asp < 0.6 or asp > 1.6 or (P[0] as Vector2).distance_to(P[-1]) > size * 0.3:
		return false
	var area := 0.0
	var n := P.size()
	for i in range(n):
		var a: Vector2 = P[i]
		var b: Vector2 = P[(i + 1) % n]
		area += a.x * b.y - b.x * a.y
	area /= 2.0
	if area >= 0.0 or -area / (w * h) < 0.4 or -area / (w * h) > 0.88:
		return false
	var cx := (left + right) / 2.0
	var D := []
	for i in range(n):
		var a: Vector2 = P[i]
		var b: Vector2 = P[(i + 1) % n]
		var k := maxi(1, int(a.distance_to(b) / (size / 80.0)))
		for j in range(k):
			D.append(a + (b - a) * float(j) / k)
	var tip: Vector2 = D[0]
	for p in D:
		if p.y > tip.y:
			tip = p
	if absf(tip.x - cx) > 0.22 * w:
		return false
	var lo := INF
	var hi := -INF
	var mid := INF
	var lt := INF
	var rt := INF
	for p in D:
		if p.y > top_ + 0.8 * h:
			lo = minf(lo, p.x)
			hi = maxf(hi, p.x)
		if absf(p.x - cx) < 0.07 * w and p.y < top_ + 0.6 * h:
			mid = minf(mid, p.y)
		if p.x < cx - 0.15 * w:
			lt = minf(lt, p.y)
		if p.x > cx + 0.15 * w:
			rt = minf(rt, p.y)
	if hi > lo and hi - lo > 0.55 * w:
		return false
	if mid == INF or mid < top_ + 0.07 * h:
		return false
	return lt != INF and rt != INF and lt <= top_ + 0.15 * h and rt <= top_ + 0.15 * h


static func heart_points(cx: float, cy: float, s: float, n := 48) -> Array:
	"""the outline of a heart (screen: y down), clockwise like heart_points in 230 - reversed it is counter-clockwise"""
	var out := []
	for i in range(n):
		var t := TAU * i / n
		var x := 16.0 * pow(sin(t), 3.0)
		var y := -(13.0 * cos(t) - 5.0 * cos(2.0 * t) - 2.0 * cos(3.0 * t) - cos(4.0 * t))
		out.append(Vector2(cx + x / 16.0 * s, cy + (y + 2.5) / 16.0 * s))
	return out


func _marmot_point() -> Vector3:
	return marmot.global_position + Vector3(0, 0.3, 0) if marmot != null else Vector3.ZERO


func head_view() -> Dictionary:
	"""where the marmot is in the picture of MoveEye's head camera (0 … 1), {} if not in it"""
	if marmot == null or m.cams.is_empty():
		return {}
	var cam: Camera3D = m.cams[0]
	var p := _marmot_point()
	if cam.is_position_behind(p) or cam.global_position.distance_to(p) > 45.0:
		return {}
	var vs: Vector2 = cam.get_viewport().get_visible_rect().size
	var s := cam.unproject_position(p) / vs
	if s.x < -0.05 or s.x > 1.05 or s.y < -0.05 or s.y > 1.05:
		return {}
	var s2 := cam.unproject_position(p + Vector3(0, 0.3, 0)) / vs
	return {"x": snappedf(s.x, 0.001), "y": snappedf(s.y, 0.001), "r": snappedf(clampf(absf(s2.y - s.y) * 1.3, 0.02, 0.5), 0.001)}


func screen_pos() -> Variant:
	"""where the marmot is in the window of the simulator (px), null = not in view"""
	if marmot == null:
		return null
	var p := _marmot_point()
	if m.view_mode == 3 and m.thermal_full != null and m.thermal_full.visible and m.cams.size() > 2:
		var tc: Camera3D = m.cams[2]
		if tc.is_position_behind(p):
			return null
		var tv: Vector2 = tc.get_viewport().get_visible_rect().size
		var n := tc.unproject_position(p) / tv
		var tf: TextureRect = m.thermal_full
		var ts: Vector2 = tf.texture.get_size() if tf.texture != null else tv
		var sc := minf(tf.size.x / ts.x, tf.size.y / ts.y)
		return tf.global_position + (tf.size - ts * sc) / 2.0 + n * ts * sc
	var cam: Camera3D = m.view_cam
	if cam == null or cam.is_position_behind(p) or cam.global_position.distance_to(p) > 45.0:
		return null
	return cam.unproject_position(p)


func can_heart() -> bool:
	return cave_open() and stage in ["open", "hold", "swing"] and _turn_t < 0.0


func heart(src: String) -> Dictionary:
	if not can_heart():
		return {"ok": false, "error": "not now", "stage": stage}
	_turn_t = _rt()
	if stage == "open":
		stage = "turned"
	_hearts()
	_whistle()
	tusch_n += 1
	tusch = bool(preload("res://scripts/klang.gd").tusch(true))   # drum roll and flourish (klang.gd, 3.28) - also when walking freely
	var first := not _found()
	_register()
	var ed = m.get("entdecken")
	if ed != null and ed.has_method("mark_found"):
		ed.mark_found(ID, "api")
	return {"ok": true, "src": src, "first": first}


func _found() -> bool:
	var ed = m.get("entdecken")
	return ed != null and ed.has_method("is_found") and ed.is_found(ID)


func _register() -> void:
	var ed = m.get("entdecken")
	if ed == null or not ed.has_method("register"):
		return
	ed.register(ID, {"scene": "bergtal", "title": T.t("Das Murmeltier hinter dem Wasserfall"),
			"short_text": T.t("Du hast das Licht vom Chalchstock verstanden. Das Murmeltier hat dir sein Geheimnis gezeigt."),
			"hint": "", "icon": "🥚", "position": _marmot_point(), "size": Vector3(0.6, 0.7, 0.6), "radius": 3.0, "when": "night",
			"kind": "tier", "active": func(): return false})


func _hearts() -> void:
	if _heart_tex == null:
		var img := Image.create(32, 32, false, Image.FORMAT_RGBA8)
		for y in range(32):
			for x in range(32):
				var px := (x - 15.5) / 13.0
				var py := -(y - 14.0) / 13.0
				var f := pow(px * px + py * py - 1.0, 3.0) - px * px * py * py * py
				img.set_pixel(x, y, Color(1, 1, 1, 1.0 if f <= 0.0 else 0.0))
		_heart_tex = ImageTexture.create_from_image(img)
	for i in range(5 if lite else 8):
		var h := MeshInstance3D.new()
		var q := QuadMesh.new()
		q.size = Vector2(0.09, 0.09)
		h.mesh = q
		var mt := StandardMaterial3D.new()
		mt.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mt.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mt.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
		mt.albedo_texture = _heart_tex
		mt.albedo_color = Color(0.91, 0.26, 0.42) if i % 2 else Color(1.0, 0.48, 0.64)
		h.material_override = mt
		h.layers = 1
		h.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		cave.add_child(h)
		var v := Vector3(_rng.randf_range(-0.25, 0.25), _rng.randf_range(0.35, 0.6), _rng.randf_range(0.05, 0.3))
		h.position = marmot.position + Vector3(0, 0.55, 0.05)
		_fx.append([h, _rt() + i * 0.12, v])


func _fx_tick() -> void:
	for i in range(_fx.size() - 1, -1, -1):
		var e: Array = _fx[i]
		var h: MeshInstance3D = e[0]
		var age := _rt() - float(e[1])
		if not is_instance_valid(h):
			_fx.remove_at(i)
			continue
		h.visible = age >= 0.0
		if age < 0.0:
			continue
		h.position += (e[2] as Vector3) * get_process_delta_time()
		(h.material_override as StandardMaterial3D).albedo_color.a = clampf(1.0 - age / 2.2, 0.0, 1.0)
		if age > 2.3:
			h.queue_free()
			_fx.remove_at(i)


func _whistle() -> void:
	"""a short, quiet whistle (two falling notes, like the marmot of MoveEye 510)"""
	if not bool(m.sound_on) or DisplayServer.get_name() == "headless":
		return
	if _pfiff == null:
		var rate := 22050
		var n := int(rate * 0.85)
		var pcm := PackedByteArray()
		pcm.resize(n * 2)
		var ph := 0.0
		for i in range(n):
			var t := float(i) / rate
			var v := 0.0
			for st in [0.0, 0.5]:
				var u: float = t - st
				if u >= 0.0 and u < 0.27:
					var f := 3000.0 * pow(2100.0 / 3000.0, u / 0.26)
					ph += TAU * f / rate
					v = sin(ph) * minf(1.0, u / 0.02) * clampf((0.27 - u) / 0.12, 0.0, 1.0)
			pcm.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 9000.0))
		_pfiff = AudioStreamWAV.new()
		_pfiff.format = AudioStreamWAV.FORMAT_16_BITS
		_pfiff.mix_rate = rate
		_pfiff.data = pcm
	if _snd == null:
		_snd = AudioStreamPlayer3D.new()
		_snd.stream = _pfiff
		_snd.unit_size = 4.0
		_snd.max_distance = 60.0
		_snd.volume_db = -10.0
		cave.add_child(_snd)
	_snd.position = marmot.position + Vector3(0, 0.5, 0)
	_snd.play()


func _unhandled_input(ev: InputEvent) -> void:
	"""drawing the heart in the window: starts only when pressed near the marmot (else the view moves as always)"""
	if ev is InputEventMouseButton and (ev as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var mb := ev as InputEventMouseButton
		if mb.pressed:
			if not can_heart():
				return
			var sp = screen_pos()
			if sp == null or (sp as Vector2).distance_to(mb.position) > 280.0:
				return
			_drawing = true
			_draw = [mb.position]
			_trail_show()
			get_viewport().set_input_as_handled()
		elif _drawing:
			_drawing = false
			_trail_hide()
			get_viewport().set_input_as_handled()
			draw_done(_draw)
	elif ev is InputEventMouseMotion and _drawing:
		_draw.append((ev as InputEventMouseMotion).position)
		if _trail != null:
			_trail.add_point((ev as InputEventMouseMotion).position)
		get_viewport().set_input_as_handled()


func draw_done(pts: Array) -> Dictionary:
	"""a stroke in the window (px): a big counter-clockwise heart around / on the marmot?"""
	if not ccw_heart(pts):
		return {"ok": false, "error": "no heart"}
	var sp = screen_pos()
	if sp == null:
		return {"ok": false, "error": "not in view"}
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for p in pts:
		lo = lo.min(p)
		hi = hi.max(p)
	var c := (lo + hi) / 2.0
	if c.distance_to(sp) > maxf(150.0, (hi - lo).length() * 0.6):
		return {"ok": false, "error": "not on it"}
	return heart("sim")


func _trail_show() -> void:
	if _layer == null:
		_layer = CanvasLayer.new()
		_layer.layer = 90
		add_child(_layer)
		_trail = Line2D.new()
		_trail.width = 4.0
		_trail.default_color = Color(1.0, 0.48, 0.64, 0.85)
		_trail.joint_mode = Line2D.LINE_JOINT_ROUND
		_trail.begin_cap_mode = Line2D.LINE_CAP_ROUND
		_trail.end_cap_mode = Line2D.LINE_CAP_ROUND
		_layer.add_child(_trail)
	_trail.clear_points()
	for p in _draw:
		_trail.add_point(p)
	_layer.visible = true


func _trail_hide() -> void:
	if _layer != null:
		_layer.visible = false


# =============================================================================================================================
func _process(_dt: float) -> void:
	if bt.tal == null or not is_instance_valid(bt.tal):
		return
	_lamp_tick()
	_beam_tick()
	_cave_tick()
	if not _fx.is_empty():
		_fx_tick()


func reply() -> Variant:
	"""for MoveEye (world_reply «egg»): only while a heart can be drawn and the marmot is in the picture of the head camera"""
	if not can_heart():
		return null
	var hv := head_view()
	if hv.is_empty():
		return null
	hv["st"] = "heart"
	return hv


func info() -> Dictionary:
	var sp = screen_pos()
	return {"ok": true, "stage": stage, "cave_open": cave_open(), "turned": _turn_t >= 0.0, "found": _found(), "dark": m.is_dark(),
			"aimed": aimed(), "phases": _phases.size(), "tries": tries, "last": last, "lite": lite,
			"lamp_on": _lamp_mat.emission_energy_multiplier > 1.0, "beam": _beam.visible, "spot": _spot.visible,
			"beam_end": [snappedf(beam_target().x, 0.1), snappedf(beam_target().y, 0.1), snappedf(beam_target().z, 0.1)],
			"waterfall": [snappedf(_aim_w.x, 0.1), snappedf(_aim_w.y, 0.1), snappedf(_aim_w.z, 0.1)],
			"slab_moved": _slab.position.distance_to(_slab_p0) if _slab != null else 0.0,
			"marmot_turn": snappedf(rad_to_deg(marmot.rotation.y), 0.1) if marmot != null else 0.0,
			"belly_facing_out": marmot != null and absf(marmot.rotation.y) < 0.2,
			"warm": snappedf(warm_c(), 0.1), "ambient": snappedf(float(m.ambient), 0.1),
			"head": head_view(), "screen": [snappedf((sp as Vector2).x, 0.1), snappedf((sp as Vector2).y, 0.1)] if sp != null else null,
			"reply": reply(), "badge": _found(), "tusch": tusch, "tusch_n": tusch_n}


func _look(what: String) -> Dictionary:
	"""places the view of the window (tests, pictures); «thermal» = the thermal picture of the head camera"""
	if what in ["thermal", "head"]:
		m.set_view(3 if what == "thermal" else 1)
		return {"ok": true, "view": m.view_mode}
	m.set_view(0)
	var vc: Camera3D = m.view_cam
	var at: Vector3
	var from: Vector3
	match what:
		"antenna":
			at = lamp.global_position
			from = bt.W(top + Vector3(-60, -45, 90))
		"belly":
			at = marmot.global_position + Vector3(0, 0.27, 0)
			var out: Vector3 = (bt.W(_xf * Vector3(U0, 0, 5)) - bt.W(_xf * Vector3(U0, 0, 0))).normalized()
			from = at + out * 0.55 + Vector3(0, 0.02, 0)
		"beam":                                         # from the side: the whole cone from the summit into the valley
			var a0: Vector3 = bt.W(top)
			var a1: Vector3 = bt.W(_aim_w)
			var mid := (a0 + a1) / 2.0
			var sd := (a1 - a0).cross(Vector3.UP).normalized()
			at = mid
			from = mid + sd * (a1 - a0).length() * 0.75 + Vector3(0, 160, 0)
		"waterfall":
			at = bt.W(_aim_w)
			var out2: Vector3 = (bt.W(_xf * Vector3(U0, 0, 5)) - bt.W(_xf * Vector3(U0, 0, 0))).normalized()
			from = at + out2 * 16.0 + Vector3(0, 2.5, 0) + out2.cross(Vector3.UP) * 5.0
		_:
			at = marmot.global_position + Vector3(0, 0.35, 0)
			var out3: Vector3 = (bt.W(_xf * Vector3(U0, 0, 5)) - bt.W(_xf * Vector3(U0, 0, 0))).normalized()
			from = at + out3 * 3.2 + Vector3(0, 0.5, 0)
	vc.global_transform = Transform3D(Basis(), from).looking_at(at, Vector3.UP)
	return {"ok": true, "at": [at.x, at.y, at.z], "from": [from.x, from.y, from.z]}


func reset() -> void:
	stage = "idle"
	cave_open_run = false
	_open_t = -1.0
	_turn_t = -1.0
	_phases.clear()
	_on.clear()
	_lit.clear()
	tries = 0
	tusch = false
	tusch_n = 0
	last = ""
	if _slab != null:
		_slab.position = _slab_p0
		_slab.rotation = Vector3.ZERO
	if marmot != null:
		marmot.rotation.y = PI
		marmot.position.y = 0.03
	_beam.visible = false
	_spot.visible = false
	var ed = m.get("entdecken")
	if ed != null and ed.has_method("forget"):
		ed.forget(ID)


func control(d: Dictionary) -> Dictionary:
	match str(d.get("do", "info")):
		"light":
			on_light(bool(d.get("on", true)), str(d.get("src", "api")))
		"signal":                                       # the answer at once (timestamps made up), aimed; «falsch»: all short
			var t := _rt() - 20.0
			_phases.clear()
			var ok := false
			for c in MUSTER:
				var dd := KURZ if (c == "k" or bool(d.get("falsch", false))) else LANG
				ok = _phase(t, t + dd, not bool(d.get("daneben", false)))
				t += dd + LUECKE
			return {"ok": true, "accepted": ok, "last": last, "stage": stage}
		"beam":
			_go("ack")
		"cave":
			_open(bool(d.get("now", true)))
		"heart":
			if bool(d.get("auto", false)):
				return heart("api")
			var hv := head_view()
			if hv.is_empty():
				return {"ok": false, "error": "not in the picture of the head camera"}
			var dx := float(d.get("x", -1)) - float(hv["x"])
			var dy := float(d.get("y", -1)) - float(hv["y"])
			if Vector2(dx, dy * 0.5625).length() > maxf(0.12, float(hv["r"]) * 2.5):
				return {"ok": false, "error": "not on it", "at": hv}
			return heart(str(d.get("src", "mw")))
		"draw":                                         # a stroke in px of the window (tests): [[x, y], …]
			var pts := []
			for p in d.get("pts", []):
				pts.append(Vector2(float(p[0]), float(p[1])))
			return draw_done(pts)
		"belly":
			if _turn_t < 0.0:
				_turn_t = _rt() - 3.0
		"look":
			return _look(str(d.get("what", "cave")))
		"place":                                        # MoveEye (the head) in front of the cave, looking in (the valley is built again)
			var here: Vector3 = _xf * Vector3(U0, 0, _wc + 4.5)
			var hw: Vector3 = bt.W(Vector3(here.x, bt.H(here.x, here.z), here.z))
			var dv: Vector3 = marmot.global_position - hw
			var yaw := rad_to_deg(-(atan2(-dv.x, -dv.z) - bt.tal.rotation.y))
			return m.control({"action": "bergtal", "do": "here", "x": here.x, "z": here.z, "yaw": yaw})
		"reset":
			reset()
	return info()
