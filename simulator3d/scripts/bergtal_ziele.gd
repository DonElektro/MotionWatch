extends RefCounted
## «Bergtal · Ziele» (Daniel 31.10.2026, Paket real-berg-orte, Vorlage: Daniels Fotos): zwei neue Orte im Bergtal (bergtal.gd).
##   Tuffwasserfall im Schattwald: eine Tuffwand mit Moos (grün auf beige-grauem Fels), das Wasser rinnt in mehreren Fäden
##     über Stufen in einen flachen, bräunlich-klaren Gumpen; Laub am Ufer, Laubbäume rundum, ein Abfluss zum Bach.
##     Plätschern (Klang aus mikrofon_klang.gd, «water»): am PC hörbar, nahe lauter; MoveEyes Mikrofon hört es auch.
##     Erreichbar über den neuen Tobelweg (Abzweigung vom Seeweg beim Schattwald).
##   Chalchstock: ein Kalkgipfel über der Obri Stafelhütte mit senkrechter heller Wand gegen Süden (zur Hütte), oben eine
##     Plattform mit Geländer, Antenne, Bank und Wegweiser. Die «Bergstation» ist die BESTEHENDE obere Station der
##     Materialseilbahn bei der Obri Stafelhütte (bergtal.gd / bergtal_orte.gd) - keine zweite Seilbahn, keine eigene Kabine
##     (Wunsch Koordinator: die Grossvater-Bahn über den Tüfelsschlund und die Materialseilbahn reichen). Von dort führt ein
##     Bergweg in Kehren hinauf, das letzte steile Stück mit Drahtseil und Eisenbügeln (Daniels Bilder 25 / 27 / 36),
##     bei der Station eine Holzbank mit Pfostenzaun (Bilder 21–23).
## Gelände: sculpt() (aus bergtal.generate(), nach Orte.sculpt) hebt den Gipfel an und gräbt den Gumpen; sonst bleibt alles.
## Lite: einfache Formen (weniger Felsstufen, 2 statt 5 Wasserfäden, kein fliessendes Wasser-Shader, weniger Laub, Antenne als
## Rohr statt Gittermast, Geländer mit weniger Pfosten, Felsplatten der Wand in gröberen Streifen).
## Steuerung: {"action": "bergtal", "do": "ziele", "what": "info | where"}.

const Bib = preload("res://scripts/bib_berg.gd")
const T = preload("res://scripts/i18n.gd")
const Klang = preload("res://scripts/mikrofon_klang.gd")

# ---- Tuffwasserfall (Tal-Koordinaten x = Osten, z = Süden) ----
const POOL := Vector2(-203.0, -600.0)            # the middle of the pool
const POOL_R := 6.8
const FALL := Vector2(-212.5, -600.0)            # the foot of the tuff wall (middle); the wall looks east (to the pool)
const WALL_W := 16.0
const WALL_H := 16.0
const OUTFLOW := [Vector2(-196.5, -600.5), Vector2(-182, -603), Vector2(-160, -598), Vector2(-132, -602), Vector2(-104, -599), Vector2(-74, -601), Vector2(-46, -600)]
const TOBELWEG := [Vector2(-120, -490), Vector2(-150, -530), Vector2(-172, -560), Vector2(-188, -584)]
# ---- Chalchstock ----
const PEAK := Vector2(437.0, 207.0)              # the top (platform in the middle)
const PEAK_A := 115.0                            # m above the ground around
const PLAT_R := 6.0                              # the flat top (platform)
const R_BACK := 80.0                             # radius of the gentle sides (north, east, west)
const R_FACE := 42.0                             # radius on the side of the face (south: towards the hut and the cable)
const FACE := Vector2(0.0, 1.0)
const BANK := Vector2(488.0, 290.0)              # bench with post fence beside the upper station of the goods lift
const GIPFELWEG := [Vector2(470, 300), Vector2(490, 268), Vector2(500, 244), Vector2(486, 228), Vector2(498, 210), Vector2(480, 196),
		Vector2(466, 182), Vector2(450, 186), Vector2(442, 198), Vector2(440, 206)]

const PLACES := [["Tuffwasserfall im Schattwald", -200.0, -600.0], ["Chalchstock (Gipfel mit Antenne)", 437.0, 207.0]]
# the discovery book: [id, title, short text, hint, icon, size (m), radius (m), when]
const ENT := [["berg.ort.tuffwasserfall", "Der Tuffwasserfall", "Über eine moosgrüne Tuffwand rinnt das Wasser in vielen Fäden in einen klaren Gumpen. Es plätschert.",
			"Im Schattwald westlich unter dem Gumpisee plätschert es – folge dem Tobelweg.", "💧", Vector3(16, 14, 10), 9.0, "any"],
		["berg.ort.chalchstock", "Auf dem Chalchstock", "Plattform mit Geländer, Antenne und Wegweiser – senkrecht unter dir die helle Kalkwand und die Obri Stafelhütte.",
			"Über der Obri Stafelhütte ragt ein heller Kalkgipfel mit Antenne auf.", "📡", Vector3(12, 4, 12), 8.0, "any"],
		["berg.ort.bergstation", "Bergstation Obri Stafel", "Hier endet die Materialseilbahn. Bank, Zaun und Wegweiser – 20 Minuten bis zum Gipfel.",
			"Fahr mit der Materialseilbahn von der Alp hinauf.", "🚡", Vector3(4, 2, 4), 5.0, "any"]]

static var pool_level := 0.0                     # the water level of the pool (set by sculpt)
static var peak_y := 0.0                         # the height of the platform


static func busy_pts() -> Array:
	"""no tree / rock of the valley here (bergtal.gd _vegetation)"""
	return [[POOL, POOL_R + 4.0], [FALL, 10.0], [PEAK, PLAT_R + 6.0], [BANK, 4.0]]


static func all_places() -> Array:
	return PLACES.duplicate()


static func place_options() -> Array:
	var out := []
	for p in PLACES:
		out.append(["p:" + str(p[0]), str(p[0])])
	return out


# =============================================================================================================================
# the ground (called from bergtal.generate(), before the colours)
# =============================================================================================================================
static func _at(hm: PackedFloat32Array, n: int, lo: float, step: float, x: float, z: float) -> float:
	var fx := clampf((x - lo) / step, 0.0, n - 1.001)
	var fz := clampf((z - lo) / step, 0.0, n - 1.001)
	var i := int(fx)
	var j := int(fz)
	var u := fx - i
	var v := fz - j
	var k := j * n + i
	return lerpf(lerpf(hm[k], hm[k + 1], u), lerpf(hm[k + n], hm[k + n + 1], u), v)


static func sculpt(hm: PackedFloat32Array, n: int, lo: float, step: float) -> PackedFloat32Array:
	# 1) Chalchstock: a cone with a flat top; steep (≈ 70°) on the side of the face, gentler elsewhere
	var c0 := _at(hm, n, lo, step, PEAK.x, PEAK.y)
	var i0 := maxi(0, int((PEAK.x - R_BACK - lo) / step))
	var i1 := mini(n - 1, int((PEAK.x + R_BACK - lo) / step) + 1)
	var j0 := maxi(0, int((PEAK.y - R_BACK - lo) / step))
	var j1 := mini(n - 1, int((PEAK.y + R_BACK - lo) / step) + 1)
	for j in range(j0, j1 + 1):
		for i in range(i0, i1 + 1):
			var q := Vector2(lo + i * step, lo + j * step)
			var d := q.distance_to(PEAK)
			if d >= R_BACK:
				continue
			var dir := (q - PEAK) / maxf(d, 0.01)
			var kf := smoothstep(0.1, 0.7, dir.dot(FACE))
			var r := lerpf(R_BACK, R_FACE, kf)
			var u := maxf(0.0, (d - PLAT_R) / (r - PLAT_R))
			if u < 1.0:                                              # face side: a block (high, then steep); else a flank
				var f := lerpf(pow(1.0 - u, 1.3), 1.0 - pow(u, 1.8), kf * 0.85)
				hm[j * n + i] += PEAK_A * f * (1.0 + 0.06 * sin(atan2(dir.y, dir.x) * 7.0) * (1.0 - f))
	peak_y = c0 + PEAK_A
	for j in range(j0, j1 + 1):                                        # the platform: flat
		for i in range(i0, i1 + 1):
			var d := Vector2(lo + i * step, lo + j * step).distance_to(PEAK)
			var w := 1.0 - smoothstep(PLAT_R, PLAT_R + 3.0, d)
			if w > 0.0:
				hm[j * n + i] = lerpf(hm[j * n + i], peak_y, w)
	# 2) the pool under the tuff wall: the water level = the lowest point of its rim; inside a shallow bowl
	var lv := INF
	for k in range(24):
		var a := TAU * k / 24.0
		lv = minf(lv, _at(hm, n, lo, step, POOL.x + cos(a) * (POOL_R + 0.7), POOL.y + sin(a) * (POOL_R + 0.7)))
	pool_level = lv - 0.05
	var R2 := 13.0
	for j in range(maxi(0, int((POOL.y - R2 - lo) / step)), mini(n - 1, int((POOL.y + R2 - lo) / step) + 1) + 1):
		for i in range(maxi(0, int((POOL.x - R2 - lo) / step)), mini(n - 1, int((POOL.x + R2 - lo) / step) + 1) + 1):
			var d := Vector2(lo + i * step, lo + j * step).distance_to(POOL)
			var t: float
			if d < POOL_R:
				t = pool_level - 0.85 * (1.0 - pow(d / POOL_R, 2.0))
			elif d < R2:
				t = lerpf(pool_level + 0.25, hm[j * n + i], smoothstep(POOL_R, R2, d))
			else:
				continue
			hm[j * n + i] = minf(hm[j * n + i], t)
	# the floor in front of the tuff wall: down to the water, from 6.5 m behind the wall face (the wall blocks fill that) to the
	# pool; the sides of the cut get rocks (_waterfall)
	var hw := WALL_W / 2.0
	for j in range(maxi(0, int((FALL.y - hw - 5.0 - lo) / step)), mini(n - 1, int((FALL.y + hw + 5.0 - lo) / step) + 1) + 1):
		for i in range(maxi(0, int((FALL.x - 7.0 - lo) / step)), mini(n - 1, int((POOL.x - lo) / step) + 1) + 1):
			var q := Vector2(lo + i * step, lo + j * step)
			var w := (1.0 - smoothstep(hw, hw + 4.0, absf(q.y - FALL.y))) * smoothstep(FALL.x - 7.5, FALL.x - 5.5, q.x)
			if w > 0.0:
				hm[j * n + i] = minf(hm[j * n + i], lerpf(hm[j * n + i], pool_level + 0.3, w))
	return hm


# =============================================================================================================================
var bt
var m
var s
var bib
var o                             # bergtal_orte.gd (its building helpers)
var lite := false
var season := "sommer"
var info := {}
var ent_pos := {}
var _snd: AudioStreamPlayer3D
var _snd_pos := Vector3.ZERO      # valley
var _slow := 0.0
var _rng := RandomNumberGenerator.new()
static var _water_wav: AudioStreamWAV


func _init(bt_) -> void:
	bt = bt_
	m = bt.m
	s = bt.s
	bib = bt.bib
	o = bt.orte
	season = str(bt.season)
	lite = bool(bt.lite) or Bib.lite()
	_rng.seed = 3112


func build() -> void:
	var t0 := Time.get_ticks_msec()
	_waterfall()
	_summit()
	_bank()
	_register()
	m.anims.append(Callable(self, "_tick"))
	info.merge({"ms": Time.get_ticks_msec() - t0, "lite": lite, "pool_level": snappedf(pool_level, 0.01), "peak_alt_m": int(peak_y + 1500.0),
			"places": PLACES.size(), "discoveries": ENT.size()}, true)


func _frame(c: Vector2, y: float, rot: float) -> Dictionary:
	return {"xf": Transform3D(Basis(Vector3.UP, rot), Vector3(c.x, y, c.y)), "rot": rot, "c": c, "y": y, "drop": 0.0, "p": [], "subs": []}


# ---- Tuffwasserfall ------------------------------------------------------------------------------------------------------------
const TUFF := ["a8956e", "9a8a66", "b5a37c", "8c7e60"]
const MOSS := ["4a7a22", "5a8a28", "3a6a1e", "6a9430"]


func _waterfall() -> void:
	var winter := season == "winter"
	var y0 := pool_level
	var b := _frame(FALL, y0, PI / 2.0)                       # local +z = valley east (to the pool), local x = valley north … south
	var nst := 4 if lite else 7
	var hk := (WALL_H + 0.8) / nst
	var tops := []                                            # [front z, top y] per step
	for k in range(nst):
		var zf := -k * 0.8 + 0.25 * sin(k * 2.3)
		var yb := -0.8 + k * hk
		var yt := yb + hk
		tops.append([zf, yt, yb])
		var cuts := 1 if lite else 3
		var xs := -WALL_W / 2.0
		for c in range(cuts):
			var w := WALL_W / cuts * (1.0 + (0.18 * sin(k * 1.7 + c * 2.1) if cuts > 1 else 0.0))
			if c == cuts - 1:
				w = WALL_W / 2.0 - xs
			var dz := 0.3 * sin(k * 3.1 + c * 1.3)
			o._bx(b, w + 0.4, hk + 0.35, 8.0, xs + w / 2.0, yb + hk / 2.0, zf + dz - 4.0, TUFF[(k + c) % 4], "stone", "far",
					3.0 * sin(k + c), -4.0 * sin(k * 1.9 + c), 1.5 * cos(k + c * 2.0))
			if not winter:                                    # moss on the edge of the step
				o._bx(b, w * (0.55 + 0.3 * absf(sin(k * 2.0 + c))), 0.22, 0.9, xs + w / 2.0 + 0.6 * sin(k + c), yt + 0.06, zf + dz - 0.4, MOSS[(k + c) % 4], "tree", "mid")
			xs += w
		if not winter:                                        # moss hanging down the face (Lite: fewer), light tuff bulges
			for j in range(2 if lite else 4):
				var mx := -6.5 + fposmod(k * 3.7 + j * 5.3, 13.0)
				o._pt(b, Bib.B(0.9 + 0.5 * (j % 2), hk * 0.75, 0.16, mx, yb + hk * 0.55, zf + 0.12, MOSS[(k + j) % 4], 0, 0, 4.0 * sin(k + j), "tree"), "mid")
			if not lite:
				o._pt(b, Bib.S(0.9, 1.1, -5.0 + fposmod(k * 4.1, 10.0), yb + hk * 0.4, zf + 0.15, TUFF[(k + 2) % 4], "stone"), "mid")
	# the rocks at both ends of the wall and the top edge (it goes into the slope)
	for sd in [-1.0, 1.0]:                                    # (and the sides of the cut in the slope)
		for j in range(3 if lite else 5):
			o._pt(b, Bib.S(1.7 + 0.25 * j, 2.2 + 0.6 * j, sd * (WALL_W / 2.0 + 0.9 + 0.4 * j), 0.6 + j * 3.2, -1.2 - j * 0.9, (MOSS[j % 4] if j % 2 == 1 and not winter else "8a7e62"), "stone"), "far")
		for j in range(2 if lite else 4):
			o._pt(b, Bib.S(1.4, 1.5, sd * (WALL_W / 2.0 + 2.2), 0.3 + j * 0.8, 1.5 + j * 2.4, "7e745c", "stone"), "mid")
	o._flush(b)
	m.add_obstacle_box(bt.W(Vector3(FALL.x - 3.0, y0, FALL.y)), WALL_W, 7.0, bt.wrot(PI / 2.0))
	m.set_obstacle_height(WALL_H)
	# the threads of water: over every step down, then a short way on the step below; one mesh (Lite: 2 threads, no shader)
	if not winter:
		var threads := [[1.4, 0.9], [-1.3, 0.3]] if lite else [[1.4, 0.9], [-1.3, 0.3], [-3.6, 0.18], [3.7, 0.24], [5.4, 0.14]]
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		for th in threads:
			var v := 0.0
			for k in range(nst - 1, -1, -1):
				var zf := float(tops[k][0]) + 0.06
				var yt := float(tops[k][1])
				var yb := maxf(float(tops[k][2]), -0.02)
				var x := float(th[0]) + 0.22 * sin(k * 2.7 + float(th[0]))
				var w := float(th[1]) * (1.0 + 0.6 * (1.0 - float(k) / nst))
				_quad(st, Vector3(x - w / 2.0, yt, zf), Vector3(x + w / 2.0, yt, zf), Vector3(x + w / 2.0, yb, zf), Vector3(x - w / 2.0, yb, zf), v, v + (yt - yb), Vector3(0, 0, 1))
				v += yt - yb
				if k > 0:                                     # over the top of the step below
					var z2 := float(tops[k - 1][0]) + 0.06
					var y2 := float(tops[k - 1][1]) + 0.04
					var x2 := float(th[0]) + 0.22 * sin((k - 1) * 2.7 + float(th[0]))
					_quad(st, Vector3(x - w / 2.0, y2, zf - 0.02), Vector3(x + w / 2.0, y2, zf - 0.02), Vector3(x2 + w / 2.0, y2, z2), Vector3(x2 - w / 2.0, y2, z2), v, v + 0.8, Vector3.UP)
					v += 0.8
		var mi: MeshInstance3D = m.add_mesh(bt.tal, st.commit(), Vector3(FALL.x, y0, FALL.y), _water_mat(), "pond", Vector3(0, PI / 2.0, 0))
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.visibility_range_end = 220.0 if lite else 420.0
	# the pool: brownish clear water over a muddy bed (winter: ice)
	var pm := StandardMaterial3D.new()
	if winter:
		pm.albedo_color = Color(0.8, 0.85, 0.88)
		pm.roughness = 0.4
	else:
		pm.albedo_color = Color(0.42, 0.36, 0.24, 0.55)
		pm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		pm.roughness = 0.04
		pm.metallic_specular = 0.8
	var cm := CylinderMesh.new()
	cm.top_radius = POOL_R + 0.4
	cm.bottom_radius = POOL_R + 0.4
	cm.height = 0.04
	cm.radial_segments = 14 if lite else 28
	cm.rings = 1
	var wi: MeshInstance3D = m.add_mesh(bt.tal, cm, Vector3(POOL.x, pool_level, POOL.y), pm, "pond" if not winter else "stone")
	wi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	wi.visibility_range_end = 260.0 if lite else 500.0
	if not lite and not winter:                               # a dark muddy bed under the water (Hoch / Normal)
		var bed := CylinderMesh.new()
		bed.top_radius = POOL_R - 0.6
		bed.bottom_radius = POOL_R - 0.6
		bed.height = 0.05
		bed.radial_segments = 12
		bed.rings = 1
		var bmat := StandardMaterial3D.new()
		bmat.albedo_color = Color(0.24, 0.19, 0.12)
		var bi: MeshInstance3D = m.add_mesh(bt.tal, bed, Vector3(POOL.x, pool_level - 0.55, POOL.y), bmat, "stone")
		bi.visibility_range_end = 160.0
	if not winter and not lite:                                # foam where the main thread falls in
		var fm := StandardMaterial3D.new()
		fm.albedo_color = Color(0.95, 0.96, 0.95, 0.5)
		fm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		var fq := QuadMesh.new()
		fq.size = Vector2(2.4, 1.6)
		var foam: MeshInstance3D = m.add_mesh(bt.tal, fq, Vector3(FALL.x + 0.9, pool_level + 0.03, FALL.y - 1.4), fm, "pond", Vector3(-PI / 2.0, 0, 0))
		foam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		foam.visibility_range_end = 120.0
	# stones in the water and on the rim
	for k in range(4 if lite else 9):
		var a := TAU * (k + 0.4) / (4 if lite else 9)
		var q := POOL + Vector2(cos(a), sin(a)) * (POOL_R + 0.3 + 0.4 * (k % 2))
		if q.x < FALL.x + 1.5:
			continue
		bib.add("boulder", Vector3(q.x, maxf(pool_level - 0.15, bt.H(q.x, q.y) - 0.25), q.y), a, {"r": 0.3 + 0.12 * (k % 3), "v": k % 3, "rock": "kalk", "noob": true, "snow": winter})
	# the outflow to the stream (a narrow brook on the ground)
	if not winter:
		bt._ribbon(bt.dense(OUTFLOW, 3.0), PackedFloat32Array(), 0.7, Color(0.33, 0.36, 0.33), 0.06, 140.0 if lite else 300.0, "pond")
	_leaves(winter)
	_trees(winter)
	ent_pos["berg.ort.tuffwasserfall"] = Vector3(POOL.x - 3.0, pool_level + 4.0, POOL.y)
	# the sound: splashing (PC) + MoveEye's microphone (a quiet long sound, like the other waterfalls)
	_snd_pos = Vector3(FALL.x + 1.0, pool_level + 1.5, FALL.y - 1.4)
	if not winter:
		if bt.W(_snd_pos).length() < 400.0:
			m.add_sound(-22.0, bt.W(_snd_pos), 1.0e7, "water")
		if bool(m.sound_on) and DisplayServer.get_name() != "headless":
			if _water_wav == null:
				_water_wav = Klang.make("water", 16000 if lite else 22050, 12.0)
			_snd = AudioStreamPlayer3D.new()
			_snd.stream = _water_wav
			_snd.unit_size = 5.0
			_snd.max_distance = 140.0
			_snd.volume_db = -6.0
			_snd.max_db = 3.0
			bt.tal.add_child(_snd)
			_snd.position = _snd_pos


func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, v0: float, v1: float, nrm: Vector3) -> void:
	var uv := [Vector2(0, v0), Vector2(1, v0), Vector2(1, v1), Vector2(0, v1)]
	var pts := [a, b, c, d]
	for k in [0, 1, 2, 0, 2, 3]:
		st.set_normal(nrm)
		st.set_uv(uv[k])
		st.add_vertex(pts[k])


static var _wshader: Shader


func _water_mat() -> Material:
	"""Lite: a plain see-through material; Hoch / Normal: streaks that run down (shader)"""
	if lite:
		var sm := StandardMaterial3D.new()
		sm.albedo_color = Color(0.9, 0.94, 0.97, 0.62)
		sm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		sm.cull_mode = BaseMaterial3D.CULL_DISABLED
		sm.roughness = 0.2
		return sm
	if _wshader == null:
		_wshader = Shader.new()
		_wshader.code = """shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;
void fragment() {
	float v = UV.y * 2.2 - TIME * 1.8;
	float s = 0.5 + 0.5 * sin(v * 6.2832 + sin(UV.x * 9.0 + UV.y * 3.0) * 1.7);
	float e = smoothstep(0.0, 0.25, UV.x) * smoothstep(1.0, 0.75, UV.x);
	ALBEDO = mix(vec3(0.78, 0.84, 0.86), vec3(1.0), s * 0.55);
	ALPHA = (0.38 + 0.42 * s) * (0.45 + 0.55 * e);
	ROUGHNESS = 0.15;
	SPECULAR = 0.7;
}
"""
	var mat := ShaderMaterial.new()
	mat.shader = _wshader
	return mat


func _leaves(winter: bool) -> void:
	if winter:
		return
	var n := 40 if lite else 170
	var cols := [Color(0.62, 0.36, 0.14), Color(0.72, 0.5, 0.18), Color(0.5, 0.32, 0.16), Color(0.78, 0.62, 0.2), Color(0.45, 0.28, 0.12)]
	if season in ["sommer", "fruehling"]:
		n = n / 2                                              # last year's leaves: fewer, darker
		cols = [Color(0.4, 0.28, 0.16), Color(0.46, 0.33, 0.18), Color(0.35, 0.25, 0.14)]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(n):
		var a := _rng.randf() * TAU
		var r := _rng.randf_range(POOL_R - 0.8, POOL_R + 5.5) if i % 9 != 0 else _rng.randf_range(0.5, POOL_R - 1.0)
		var q := POOL + Vector2(cos(a), sin(a)) * r
		if q.x < FALL.x + 0.5:
			continue
		var y: float = pool_level + 0.01 if r < POOL_R - 0.5 else bt.H(q.x, q.y) + 0.03
		var rot := _rng.randf() * TAU
		var sz := _rng.randf_range(0.07, 0.13)
		var bs := Basis(Vector3.UP, rot)
		var c: Color = cols[i % cols.size()]
		var pts := [Vector3(-sz, 0, -sz * 0.6), Vector3(sz, 0, -sz * 0.6), Vector3(sz, 0, sz * 0.6), Vector3(-sz, 0, sz * 0.6)]
		for k in [0, 2, 1, 0, 3, 2]:
			st.set_color(c)
			st.set_normal(Vector3.UP)
			st.add_vertex(Vector3(q.x, y, q.y) + bs * pts[k])
	var lm := StandardMaterial3D.new()
	lm.vertex_color_use_as_albedo = true
	lm.cull_mode = BaseMaterial3D.CULL_DISABLED
	lm.roughness = 0.9
	var li: MeshInstance3D = m.add_mesh(bt.tal, st.commit(), Vector3.ZERO, lm, "tree")
	li.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	li.visibility_range_end = 60.0 if lite else 110.0


func _trees(winter: bool) -> void:
	"""deciduous trees (beech, maple, ash) around the pool - the forest of the valley here is larch and spruce"""
	var cols: Array = {"sommer": ["3f6e2a", "4d7a2e", "5a8a34"], "fruehling": ["6a9a3a", "7aaa44", "5e9032"],
			"herbst": ["c9a227", "b8731f", "8a9a2a", "d4b030", "a8621c"]}.get(season, [])
	var n := 7 if lite else 15
	var placed := 0
	for i in range(n * 3):
		if placed >= n:
			break
		var a := _rng.randf() * TAU
		var r := _rng.randf_range(POOL_R + 4.0, 26.0)
		var q := POOL + Vector2(cos(a), sin(a)) * r
		if absf(q.y - FALL.y) < WALL_W / 2.0 + 1.0 and q.x < FALL.x + 2.0 and q.x > FALL.x - 8.0:
			continue                                           # not on the wall
		if bt._near_way(q.x, q.y, 3.0):
			continue
		var p: Vector3 = bt.P(q.x, q.y, -0.1)
		var sc := _rng.randf_range(0.9, 1.5)
		if winter or cols.is_empty():                          # bare: trunk and two branches
			bib._part(Bib.C(0.16 * sc, 6.0 * sc, p.x, p.y + 3.0 * sc, p.z, "4a3c2e", 0.2, 0, 0, 0, "tree"), Transform3D.IDENTITY, "tree", "far", bib._cell_key(p))
			bib._part(Bib.ROD(p + Vector3(0, 3.5 * sc, 0), p + Vector3(1.4, 5.8, 0.3) * sc, 0.07, "4a3c2e", "tree"), Transform3D.IDENTITY, "tree", "far", bib._cell_key(p))
			bib._part(Bib.ROD(p + Vector3(0, 4.0 * sc, 0), p + Vector3(-1.0, 6.2, -0.6) * sc, 0.06, "4a3c2e", "tree"), Transform3D.IDENTITY, "tree", "far", bib._cell_key(p))
		else:
			bib.add("tree", p, _rng.randf() * TAU, {"col": cols[placed % cols.size()], "scale": sc, "noob": r > 14.0})
		placed += 1
	info["leaf_trees"] = placed


# ---- Chalchstock ------------------------------------------------------------------------------------------------------------------
const KALK := ["b4b0a5", "a6a296", "bfbbb0", "9c988c", "aeaa9e"]


func _summit() -> void:
	var winter := season == "winter"
	var ck: String = bib._cell_key(Vector3(PEAK.x, peak_y, PEAK.y))
	# the light, almost vertical face on the south side: plates of limestone lying on the steep ground (tilted like it), in
	# columns with ledges at different heights (grass on the ledges, darker streaks); only where the ground is steep
	var da := 16.0 if lite else 8.0
	var a := -64.0
	var col_i := 0
	while a <= 64.0:
		var dirv := FACE.rotated(deg_to_rad(a))
		var yaw := atan2(dirv.x, dirv.y)
		var band := (24.0 if lite else 14.0) + 4.0 * sin(col_i * 2.3)
		var y := peak_y - 1.5 - fposmod(col_i * 5.3, band * 0.6)
		var j := 0
		var r_hi := _radius_at(dirv, y)
		while y > peak_y - PEAK_A + 4.0:
			var ylo := y - band
			var r_lo := _radius_at(dirv, ylo)
			var run := r_lo - r_hi
			if run > band * 0.85:                                   # gentler than ≈ 50°: no plate
				break
			var tilt := atan2(run, band)                            # 0 = vertical
			var ln := sqrt(run * run + band * band) + 1.0
			var w := 2.0 * (r_hi + r_lo) / 2.0 * sin(deg_to_rad(da) / 2.0) + 2.5
			var mid := PEAK + dirv * ((r_hi + r_lo) / 2.0 - 0.9)
			var xf := Transform3D(Basis(Vector3.UP, yaw) * Basis(Vector3.RIGHT, -tilt), Vector3(mid.x, (y + ylo) / 2.0, mid.y))
			var col: String = KALK[(j * 3 + col_i) % KALK.size()] if not winter else "e4e8ea"
			bib._part(Bib.B(w, ln, 2.6, 0, 0, 0, col, 2.5 * sin(a + j * 2.0), 4.0 * sin(j * 1.7 + a), 2.0 * cos(j + col_i), "stone"), xf, "stone", "far", ck)
			if not lite:
				bib._part(Bib.B(w * 0.9, 0.35, 1.4, 0.3 * sin(j + a), ln / 2.0, 0.6, "6c7440" if not winter else "f2f4f6", 0, 0, 0, "tree"), xf, "tree", "far", ck)
				bib._part(Bib.B(0.6 + 0.4 * (j % 2), ln * 0.8, 0.2, w * 0.25 * sin(j * 2.1 + a), -0.05 * ln, 1.32, "86827a", 0, 0, 0, "stone"), xf, "stone", "far", ck)
			y = ylo
			r_hi = r_lo
			j += 1
		a += da
		col_i += 1
	# the platform: concrete with a railing (posts + two rails), the antenna, a bench, the signpost (bergtal_wegweiser.gd)
	var top := Vector3(PEAK.x, peak_y, PEAK.y)
	bib._part(Bib.C(PLAT_R - 0.3, 0.3, top.x, top.y + 0.05, top.z, "a8a49a", 0, 0, 0, 0, "stone"), Transform3D.IDENTITY, "stone", "far", ck)
	var np := 10 if lite else 22
	var prev := Vector3.ZERO
	for k in range(np + 1):
		var an := TAU * k / np
		var p := top + Vector3(cos(an) * (PLAT_R - 0.5), 0.2, sin(an) * (PLAT_R - 0.5))
		if k < np:
			bib._part(Bib.B(0.06, 1.1, 0.06, p.x, p.y + 0.55, p.z, "5a5e62", 0, 0, 0, "metal"), Transform3D.IDENTITY, "metal", "mid", ck)
		if k > 0:
			for hh in [0.55, 1.08]:
				bib._part(Bib.ROD(prev + Vector3(0, hh, 0), p + Vector3(0, hh, 0), 0.035, "6a6e72", "metal"), Transform3D.IDENTITY, "metal", "mid", ck)
			if not lite:                                          # wire mesh between the rails (like on Daniel's photo 10)
				bib._part(Bib.ROD(prev + Vector3(0, 0.8, 0), p + Vector3(0, 0.8, 0), 0.012, "8a8e92", "metal"), Transform3D.IDENTITY, "metal", "small", ck)
				bib._part(Bib.ROD(prev + Vector3(0, 0.3, 0), p + Vector3(0, 0.3, 0), 0.012, "8a8e92", "metal"), Transform3D.IDENTITY, "metal", "small", ck)
		prev = p
	_antenna(top + Vector3(-2.6, 0.2, -2.6), ck)
	bib.add("bench", top + Vector3(1.0, 0.2, 3.6), PI)
	bt.decks.append([PEAK, Vector2(PLAT_R - 0.6, PLAT_R - 0.6), 0.0, peak_y + 0.2])
	ent_pos["berg.ort.chalchstock"] = top + Vector3(0, 1.5, 0)
	_via_ferrata(ck)


func _radius_at(dirv: Vector2, y: float) -> float:
	"""how far from the top (along dirv) the ground is lower than y"""
	var r := PLAT_R
	while r < R_BACK and bt.H(PEAK.x + dirv.x * r, PEAK.y + dirv.y * r) > y:
		r += 1.0
	return r


func _antenna(base: Vector3, ck: String) -> void:
	"""a radio mast like on the Stockhorn: lattice (Lite: a tube), dishes, a red light on top"""
	var h := 24.0
	if lite:
		bib._part(Bib.C(0.22, h, base.x, base.y + h / 2.0, base.z, "c8ccd0", 0.3, 0, 0, 0, "metal"), Transform3D.IDENTITY, "metal", "far", ck)
	else:
		var b0 := 0.75
		var b1 := 0.22
		for sx in [-1.0, 1.0]:
			for sz in [-1.0, 1.0]:
				bib._part(Bib.ROD(base + Vector3(sx * b0, 0, sz * b0), base + Vector3(sx * b1, h, sz * b1), 0.07, "c8ccd0", "metal"), Transform3D.IDENTITY, "metal", "far", ck)
		for k in range(1, 8):
			var f := k / 8.0
			var r := lerpf(b0, b1, f)
			var y := base.y + h * f
			for e in [[Vector3(-r, 0, -r), Vector3(r, 0, -r)], [Vector3(r, 0, -r), Vector3(r, 0, r)], [Vector3(r, 0, r), Vector3(-r, 0, r)], [Vector3(-r, 0, r), Vector3(-r, 0, -r)]]:
				bib._part(Bib.ROD(Vector3(base.x, y, base.z) + e[0], Vector3(base.x, y, base.z) + e[1], 0.04, "b8bcc0", "metal"), Transform3D.IDENTITY, "metal", "mid", ck)
		for dy in [9.0, 15.0]:                                    # two dishes
			bib._part(Bib.C(0.55, 0.2, base.x + 0.7, base.y + dy, base.z, "e8eaec", 0.3, 0, 0, 90, "metal"), Transform3D.IDENTITY, "metal", "mid", ck)
		bib._part(Bib.B(0.5, 1.6, 0.08, base.x - 0.5, base.y + 19.0, base.z + 0.3, "dcdee0", 0, 30, 0, "metal"), Transform3D.IDENTITY, "metal", "mid", ck)
	bib._part(Bib.C(0.05, 4.0, base.x, base.y + h + 2.0, base.z, "c8ccd0", 0, 0, 0, 0, "metal"), Transform3D.IDENTITY, "metal", "far", ck)
	bib._part(Bib.S(0.14, 0.2, base.x, base.y + h + 4.1, base.z, "*ff3020", "metal"), Transform3D.IDENTITY, "metal", "far", ck)
	m.add_obstacle(bt.W(base), 1.0)
	m.set_obstacle_height(h)


func _via_ferrata(ck: String) -> void:
	"""the last steep part of the Gipfelweg: a steel cable on short posts beside the path, iron rungs where it is steepest
	(Daniel's photos 25 / 27 / 36). Lite: the cable only."""
	var pts: PackedVector2Array = bt.dense(GIPFELWEG.slice(4), 2.5)
	var prev := Vector3.INF
	for i in range(pts.size()):
		var q := pts[i]
		var nx := (pts[mini(i + 1, pts.size() - 1)] - pts[maxi(i - 1, 0)]).normalized()
		var side := Vector2(-nx.y, nx.x) * 0.85
		var p: Vector3 = bt.P(q.x + side.x, q.y + side.y, 0.0)
		if i % 2 == 0 or i == pts.size() - 1:
			bib._part(Bib.B(0.04, 0.95, 0.04, p.x, p.y + 0.45, p.z, "5a5a5a", 0, 0, 0, "metal"), Transform3D.IDENTITY, "metal", "small", ck)
			var c := p + Vector3(0, 0.9, 0)
			if prev != Vector3.INF:
				bib._part(Bib.ROD(prev, c, 0.012, "9a9a9a", "metal"), Transform3D.IDENTITY, "metal", "small", ck)
			prev = c
			if not lite and bt.slope_deg(q.x, q.y) > 38.0:          # iron rungs in the rock
				var r: Vector3 = bt.P(q.x, q.y, 0.12)
				bib._part(Bib.B(0.32, 0.03, 0.03, r.x, r.y, r.z, "4a4a4a", 0, rad_to_deg(atan2(nx.x, nx.y)) + 90.0, 0, "metal"), Transform3D.IDENTITY, "metal", "small", ck)


func _bank() -> void:
	"""beside the upper station of the goods lift: a wooden bench made of one beam and a post fence (photos 21–23)"""
	var y: float = bt.H(BANK.x, BANK.y)
	var ck: String = bib._cell_key(Vector3(BANK.x, y, BANK.y))
	var face := Vector2(-1, 0.2).normalized()                     # looking west, down the side valley to the main valley
	var yaw := atan2(face.x, face.y)
	var xf := Transform3D(Basis(Vector3.UP, yaw), Vector3(BANK.x, y, BANK.y))
	for p in [Bib.B(2.2, 0.12, 0.32, 0, 0.45, 0, "8a7458", 0, 0, 0, "tree"), Bib.B(0.25, 0.42, 0.25, -0.8, 0.21, 0, "6a5a44", 0, 0, 0, "tree"),
			Bib.B(0.25, 0.42, 0.25, 0.8, 0.21, 0, "6a5a44", 0, 0, 0, "tree")]:
		bib._part(p, xf, "tree", "mid", ck)
	for k in range(4 if lite else 6):                              # the post fence in front (on the edge)
		var x := -2.5 + k * (5.0 / (3 if lite else 5))
		bib._part(Bib.B(0.1, 1.0, 0.1, x, 0.5, 1.6, "7a6248", 0, 0, 0, "tree"), xf, "tree", "small", ck)
	bib._part(Bib.B(5.1, 0.06, 0.06, 0, 0.85, 1.6, "8a7458", 0, 0, 0, "tree"), xf, "tree", "small", ck)
	if not lite:
		bib._part(Bib.B(5.1, 0.06, 0.06, 0, 0.45, 1.6, "8a7458", 0, 0, 0, "tree"), xf, "tree", "small", ck)
	ent_pos["berg.ort.bergstation"] = Vector3(BANK.x, y + 1.0, BANK.y)


# ---- discovery book, map, sound ---------------------------------------------------------------------------------------------------
func _register() -> void:
	var ed = m.get("entdecken")
	var out := []
	for e in ENT:
		var id := str(e[0])
		if not ent_pos.has(id):
			continue
		var wp: Vector3 = bt.W(ent_pos[id])
		out.append({"id": id, "x": snappedf(wp.x, 0.1), "y": snappedf(wp.y, 0.1), "z": snappedf(wp.z, 0.1)})
		if ed == null or not ed.has_method("register"):
			continue
		ed.register(id, {"scene": "bergtal", "title": T.t(str(e[1])), "short_text": T.t(str(e[2])), "hint": T.t(str(e[3])), "icon": str(e[4]),
				"position": wp, "size": e[5], "radius": float(e[6]), "when": str(e[7]), "kind": "ort"})
	info["registered"] = ed != null and ed.has_method("register")
	info["discovered_at"] = out


func publish() -> void:
	"""after bergtal._publish: the two places on the map and in the list for MoveEye"""
	var marks: Array = s.data.get("map_marks", [])
	var orte: Array = s.data.get("orte", [])
	for pl in PLACES:
		var wp: Vector3 = bt.WG(float(pl[1]), float(pl[2]))
		marks.append([wp, str(pl[0]), Color(0.95, 0.95, 0.9), false])
		orte.append([str(pl[0]), snappedf(wp.x, 0.1), snappedf(wp.z, 0.1), snappedf(Vector2(wp.x, wp.z).length(), 0.1)])


func _tick(dt: float, _t: float) -> bool:
	if bt.tal == null or not is_instance_valid(bt.tal):
		return true
	_slow -= dt
	if _slow > 0.0 or _snd == null or not is_instance_valid(_snd):
		return false
	_slow = 0.5
	var cam: Vector3 = m.view_cam.global_position
	var near: bool = cam.distance_to(bt.W(_snd_pos)) < 150.0 and bool(m.sound_on)    # play only near (saves the mixer)
	if near and not _snd.playing:
		_snd.play()
	elif not near and _snd.playing:
		_snd.stop()
	return false


func control(d: Dictionary) -> Dictionary:
	match str(d.get("what", "info")):
		"where":
			var out := {}
			for k in ent_pos:
				var wp: Vector3 = bt.W(ent_pos[k])
				out[k] = [snappedf(wp.x, 0.1), snappedf(wp.y, 0.1), snappedf(wp.z, 0.1)]
			return {"ok": true, "where": out}
	return {"ok": true, "info": info, "places": PLACES, "sound": _snd != null and is_instance_valid(_snd) and _snd.playing}
