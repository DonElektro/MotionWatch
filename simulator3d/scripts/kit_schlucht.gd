extends RefCounted
## Abenteuer-Kit (Besitzer 21.11.2026, «Beides» – 1): eine eigene, von Hand gebaute Schlucht für Kapitel 2 – ein lokales
## Gelände (Höhenfeld) samt Wänden, Stufen, Bach und Wasserfall-Schlitz, unabhängig vom Einschnitt der Bäche in bergtal.gd
## (der vertieft dort bei jedem Schritt weiter; Korrektur später separat). Rund 15–19 m tief, warm und stilisiert:
## Wände mit Gesteinsbändern (Ocker, warmes Grau, Rost) und Absätzen, Moos unten, Alpweide oben.
## Die Form steht in den Daten des Kapitels (SCHLUCHT: Mitte, Achse, Länge, Breite je Stelle, Boden je Stelle, Kanal).
## Wie es eingebaut ist:
##   * Höhe: boden(x, z) (Tal-Koordinaten) – in der Schlucht dieses Höhenfeld, sonst null (dann gilt bergtal.H). bergtal.gd
##     fragt es in gy() über boden_fn (main.ground_y: Menschen, Kamera, Fuss-IK), der Parcours und Maggie direkt.
##   * Bild: ein Netz (Gitter 0,75 m in der Schlucht, gröber aussen), Vertex-Farben, ein Material; das Gelände des Bergtals
##     wird dort ausgeschnitten (bergtal.clip_ground, die Räume von bergtal_orte.gd bleiben), Steine / Gras des Tals
##     innerhalb werden versteckt – beim Aufräumen alles zurück.
## Lite: Gitter 1 m statt 0,75 m, keine Schatten.

const Bt = preload("res://scripts/bergtal.gd")

var bt
var S: Dictionary                    # the data (daten.SCHLUCHT)
var c := Vector2.ZERO
var d := Vector2(0, 1)
var qd := Vector2(1, 0)
var s0 := 0.0
var s1 := 0.0
var qmax := 30.0
var mesh_mi: MeshInstance3D
var _mat_alt := {}                   # ground chunk mesh -> its material_override before the clip
var _mm_alt: Array = []              # [multimesh, index, transform] of hidden rocks / grass
var _boden_tab: Array = []
static var _fels_sh: Shader = null

# art pass (Koordinator 21.11.): the walls in world space – strata by height (no stretched UVs on steep faces), a planar
# rock grain on the side facing the camera, dark seams under each ledge, moss where it is flat on top; the floor / the
# alpine meadow keep the vertex colours. One shader for the gorge and all rock pieces of the course (blocks, steps, stones).
const FELS_SHADER := """
shader_type spatial;
render_mode cull_disabled;
uniform float moos_oben = 0.0;           // 1 = rock pieces: moss on flat tops
uniform vec3 tint = vec3(1.0);
varying vec3 wp;
varying vec3 wn;
float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y);
}
vec3 band(float k) {
	float r = h21(vec2(k, 7.0));
	vec3 a = vec3(0.74, 0.57, 0.38); vec3 b = vec3(0.6, 0.52, 0.46); vec3 c = vec3(0.69, 0.45, 0.31); vec3 d = vec3(0.8, 0.69, 0.52);
	return r < 0.25 ? a : (r < 0.5 ? b : (r < 0.75 ? c : d));
}
void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wn = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}
void fragment() {
	float up = clamp(wn.y, 0.0, 1.0);
	float steil = 1.0 - smoothstep(0.55, 0.85, up);
	vec2 puv = abs(wn.x) > abs(wn.z) ? wp.zy : wp.xy;           // planar on the wall (world space: no stretching)
	float det = vn(puv * vec2(0.9, 2.6)) * 0.55 + vn(puv * vec2(3.1, 6.0)) * 0.3 + vn(puv * 11.0) * 0.15;
	// 21.11. «weniger künstlich»: the strata bend and change thickness, faces of other rock break them up, cracks, moss
	// in the seams, darker in recesses (the vertex alpha of the gorge = AO from its shape)
	float warp = vn(wp.xz * 0.12) * 1.8 + vn(puv * 0.31) * 1.3 + vn(puv * vec2(0.07, 0.02)) * 2.5;
	float dick = 0.5 + 0.35 * vn(puv * vec2(0.05, 0.0) + 3.0);    // thicker and thinner layers along the gorge
	float yy = wp.y * dick + warp;
	float k = floor(yy);
	float f = fract(yy);
	vec3 rock = mix(band(k), band(k + 1.0), smoothstep(0.85, 1.0, f) * 0.5);
	float flaeche = smoothstep(0.52, 0.72, vn(puv * 0.09 + 11.0));  // big faces of grey limestone over the bands
	rock = mix(rock, vec3(0.6, 0.58, 0.55) * (0.85 + 0.3 * vn(puv * 0.6)), flaeche * 0.75);
	rock *= 0.72 + 0.48 * det;
	float seam = 1.0 - smoothstep(0.0, 0.12, f);
	rock *= 1.0 - 0.38 * seam * (1.0 - flaeche * 0.6);          // the seam under each ledge
	float riss = 1.0 - smoothstep(0.0, 0.022, abs(vn(vec2(puv.x * 1.3, puv.y * 0.22)) - 0.5));
	riss *= smoothstep(0.6, 0.8, vn(puv * vec2(0.25, 0.12) + 7.0));   // only here and there, and broken along their length
	rock *= 1.0 - 0.35 * riss * steil;                          // cracks
	vec3 moss = vec3(0.32, 0.42, 0.2) * (0.8 + 0.4 * vn(wp.xz * 1.7));
	float moos_naht = seam * smoothstep(0.5, 0.75, vn(puv * 0.7 + 5.0)) + riss * smoothstep(0.55, 0.8, vn(puv * 0.5));
	rock = mix(rock, moss * 0.85, clamp(moos_naht, 0.0, 1.0) * 0.55 * steil);
	vec3 base = COLOR.rgb;
	if (moos_oben > 0.5) {                                      // rock pieces: mostly grey limestone, the bands only faint
		rock = mix(rock, vec3(0.58, 0.56, 0.53) * (0.75 + 0.45 * det), 0.6);
		base = mix(rock, moss, smoothstep(0.75, 0.95, up) * smoothstep(0.35, 0.65, vn(wp.xz * 0.9)));
	}
	vec3 col = mix(base, rock, steil);
	col *= mix(0.55, 1.0, COLOR.a);                             // recesses darker (AO of the gorge shape; rock pieces: 1)
	float lum = dot(col, vec3(0.3, 0.59, 0.11));
	col = mix(vec3(lum), col, 1.3);                            // a little more colour …
	col = clamp((col - 0.42) * 1.18 + 0.4, 0.0, 1.0);          // … and contrast (bright laptop screens: not washed out)
	ALBEDO = col * tint;
	ROUGHNESS = 0.88;
}
"""


static func fels_material(oben_moos: bool, tint := Color(1, 1, 1)) -> ShaderMaterial:
	if _fels_sh == null:
		_fels_sh = Shader.new()
		_fels_sh.code = FELS_SHADER
	var sm := ShaderMaterial.new()
	sm.shader = _fels_sh
	sm.set_shader_parameter("moos_oben", 1.0 if oben_moos else 0.0)
	sm.set_shader_parameter("tint", Vector3(tint.r, tint.g, tint.b))
	return sm
var _breite_tab: Array = []


func _init(bt_, daten_schlucht: Dictionary) -> void:
	bt = bt_
	S = daten_schlucht
	c = S["mitte"]
	d = (S["achse"] as Vector2).normalized()
	qd = Vector2(-d.y, d.x)
	s0 = float(S["s"][0])
	s1 = float(S["s"][1])
	qmax = float(S["q"])
	_boden_tab = S["boden"]
	_breite_tab = S["breite"]


func sq(v: Vector2) -> Vector2:
	var o := v - c
	return Vector2(o.dot(d), o.dot(qd))


func tal(sv: float, qv: float) -> Vector2:
	return c + d * sv + qd * qv


static func _tab(t: Array, x: float) -> float:
	if x <= float(t[0][0]):
		return float(t[0][1])
	for i in range(t.size() - 1):
		var a: Array = t[i]
		var b: Array = t[i + 1]
		if x <= float(b[0]):
			var f := (x - float(a[0])) / maxf(0.001, float(b[0]) - float(a[0]))
			return lerpf(float(a[1]), float(b[1]), f)
	return float(t[-1][1])


func boden_sq(sv: float, qv: float) -> float:
	"""the height (valley y) at [s, q] of the set"""
	var t := tal(sv, qv)
	var R: float = Bt.H(t.x, t.y)
	var F := _tab(_boden_tab, sv)
	for k in S.get("kanal", []):                         # a slot where the upper floor is cut (the waterfall)
		if sv >= float(k[0]) and sv <= float(k[1]) and qv >= float(k[2]) and qv <= float(k[3]):
			F = float(k[4])
	var w := _tab(_breite_tab, sv) + 0.6 * sin(sv * 0.37) + 0.4 * sin(sv * 0.91 + qv * 0.1)
	var depth := R - F
	var dicke := 2.2 + 0.3 * maxf(depth, 0.0)
	var aq := absf(qv)
	var h: float
	if aq <= w:
		h = F + 0.12 * sin(sv * 1.3 + qv * 0.7) * smoothstep(w * 0.4, w, aq)
	elif aq >= w + dicke:
		h = R
	else:
		var u := (aq - w) / dicke
		var bands := 4.0
		var fb := u * bands
		var stair: float = (floor(fb) + smoothstep(0.35, 0.95, fb - floor(fb))) / bands   # ledges: flat, then steep
		var f := lerpf(stair, u, 0.25)
		h = F + (R - F) * f
	var ends := smoothstep(s0 + 6.0, s0, sv) + smoothstep(s1 - 6.0, s1, sv)
	h = lerpf(h, R, clampf(ends, 0.0, 1.0))
	h = lerpf(h, R, smoothstep(qmax - 4.0, qmax, aq))
	return h


func drin(v: Vector2) -> bool:
	var p := sq(v)
	return p.x > s0 and p.x < s1 and absf(p.y) < qmax


func boden(x: float, z: float):
	"""valley height inside the set, null outside (bergtal.H then)"""
	var p := sq(Vector2(x, z))
	if p.x <= s0 or p.x >= s1 or absf(p.y) >= qmax:
		return null
	return boden_sq(p.x, p.y)


# =======================================================================================================================
# the picture
# =======================================================================================================================
func _farbe(sv: float, qv: float, h: float, F: float, R: float, steil: float) -> Color:
	var depth := maxf(R - F, 0.01)
	var rel := clampf((h - F) / depth, 0.0, 1.0)
	var gras := Color(0.47, 0.55, 0.26)
	var weide := Color(0.58, 0.6, 0.3)
	var kies := Color(0.56, 0.5, 0.42)
	var moos := Color(0.33, 0.42, 0.22)
	var baender := [Color(0.71, 0.55, 0.36), Color(0.58, 0.5, 0.45), Color(0.66, 0.43, 0.3), Color(0.76, 0.66, 0.5), Color(0.55, 0.45, 0.38)]
	if steil < 0.55:
		if rel < 0.08:
			var n := 0.5 + 0.5 * sin(sv * 2.1 + qv * 1.7)
			return kies.lerp(moos, 0.25 * n + 0.35 * smoothstep(3.0, 7.0, absf(qv)))
		return gras.lerp(weide, 0.5 + 0.5 * sin(sv * 0.3 + qv * 0.2))
	var bi := int(floor((h - F) / 1.7 + sin(sv * 0.15) * 0.6)) % baender.size()
	var col: Color = baender[absi(bi)]
	col = col.darkened(0.12 * (1.0 - rel))                 # darker and cooler deeper down
	col = col.lerp(moos, 0.35 * smoothstep(0.25, 0.0, rel))
	return col


var bau_ms := 0
var ecken := 0


func bauen(holder: Node3D, m, lite: bool) -> void:
	var t0 := Time.get_ticks_msec()
	var step := 1.0 if lite else 0.75
	var ns := int(ceil((s1 - s0) / step)) + 1
	var qs: Array = []
	var qv := -qmax
	while qv < qmax:
		qs.append(qv)
		var inner := absf(qv) < 22.0
		qv += step if inner else step * 2.5
	qs.append(qmax)
	var nq := qs.size()
	var hs := PackedFloat32Array()
	hs.resize(ns * nq)
	for i in range(ns):
		var sv := s0 + i * step
		for j in range(nq):
			hs[i * nq + j] = boden_sq(sv, float(qs[j]))
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(ns):
		var sv := s0 + i * step
		var tF := _tab(_boden_tab, sv)
		for j in range(nq):
			var q := float(qs[j])
			var h := hs[i * nq + j]
			var tp := tal(sv, q)
			var R: float = Bt.H(tp.x, tp.y)
			var hn := hs[mini(i + 1, ns - 1) * nq + j]
			var hq := hs[i * nq + mini(j + 1, nq - 1)]
			var dq := maxf(0.1, float(qs[mini(j + 1, nq - 1)]) - q)
			var steil := maxf(absf(hn - h) / step, absf(hq - h) / dq)
			var fc := _farbe(sv, q, h, tF, R, steil)
			fc.a = _ao(hs, i, j, ns, nq, h, tF, R, steil, q, sv)
			st.set_color(fc)
			st.set_uv(Vector2(sv * 0.25, h * 0.25))
			st.add_vertex(Vector3(tp.x, h, tp.y))
	for i in range(ns - 1):
		for j in range(nq - 1):
			var a := i * nq + j
			var b := a + 1
			var c2 := a + nq
			var d2 := c2 + 1
			st.add_index(a)
			st.add_index(c2)
			st.add_index(b)
			st.add_index(b)
			st.add_index(c2)
			st.add_index(d2)
	st.generate_normals()
	var mesh := st.commit()
	var mt := fels_material(false)
	mesh_mi = MeshInstance3D.new()
	mesh_mi.name = "kit_schlucht"
	mesh_mi.mesh = mesh
	mesh_mi.material_override = mt
	mesh_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if lite else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	holder.add_child(mesh_mi)
	if m != null and m.has_method("tmat_fixed"):          # MoveEye's thermal picture: the rock at about 12 °C
		var tw := MeshInstance3D.new()
		tw.mesh = mesh
		tw.material_override = m.tmat_fixed(12.0)
		tw.layers = 2
		tw.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		holder.add_child(tw)
	_ausschneiden()
	_steine_weg()                                          # (before the details: they are multimeshes in the valley too)
	_details(holder, lite)
	ecken = ns * nq
	bau_ms = Time.get_ticks_msec() - t0


func _ao(hs: PackedFloat32Array, i: int, j: int, ns: int, nq: int, h: float, F: float, R: float, steil: float, q: float, sv: float) -> float:
	"""a cheap ambient occlusion from the shape: lower than the neighbours = a recess; the foot of the walls darker"""
	var sum := 0.0
	var n := 0
	for o in [[-2, 0], [2, 0], [0, -2], [0, 2], [-3, 0], [3, 0]]:
		var i2: int = clampi(i + int(o[0]), 0, ns - 1)
		var j2: int = clampi(j + int(o[1]), 0, nq - 1)
		sum += hs[i2 * nq + j2]
		n += 1
	var conc := clampf((sum / float(n) - h) / 1.4, 0.0, 1.0)
	var rel := clampf((h - F) / maxf(R - F, 1.0), 0.0, 1.0)
	var w := _tab(_breite_tab, sv)
	var fuss := (1.0 - smoothstep(0.0, 0.22, rel)) * smoothstep(w - 2.0, w, absf(q))   # floor and wall right at the foot
	return clampf(1.0 - 0.45 * conc - 0.3 * fuss, 0.0, 1.0)


func _mm(holder: Node3D, mesh: Mesh, mat: Material, xs: Array) -> void:
	"""many copies in one draw call (web Lite)"""
	if xs.is_empty():
		return
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.mesh = mesh
	mm.instance_count = xs.size()
	for i in range(xs.size()):
		mm.set_instance_transform(i, xs[i])
	var mi := MultiMeshInstance3D.new()
	mi.multimesh = mm
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	holder.add_child(mi)


func _kanal_bei(sv: float, qv: float) -> bool:
	for k in S.get("kanal", []):
		if sv >= float(k[0]) - 0.6 and sv <= float(k[1]) + 0.6 and qv >= float(k[2]) - 0.6 and qv <= float(k[3]) + 0.6:
			return true
	return false


func _details(holder: Node3D, lite: bool) -> void:
	"""art pass: boulders on the floor, tufts of fern at the foot of the walls, rock ledges sticking out of the walls, larches
	on the rim - all as MultiMesh (5 draw calls), the same rock shader; fixed seed (same picture every time)"""
	var rng := RandomNumberGenerator.new()
	rng.seed = 7411
	var fels_m := fels_material(true)
	var blk: Array = []
	var farn: Array = []
	var sims: Array = []
	var stamm: Array = []
	var krone: Array = []
	var n_blk := 14 if lite else 28
	var n_farn := 30 if lite else 70
	var n_sims := 18 if lite else 34
	var n_baum := 8 if lite else 14
	var tries := 0
	while blk.size() < n_blk and tries < 400:
		tries += 1
		var sv := rng.randf_range(s0 + 8.0, s1 - 6.0)
		var sd := -1.0 if rng.randf() < 0.5 else 1.0
		var w := _tab(_breite_tab, sv)
		var qv := sd * (w - rng.randf_range(0.2, 1.6))
		if _kanal_bei(sv, qv) or (absf(qv) < 4.0):
			continue
		var t := tal(sv, qv)
		var sc := rng.randf_range(0.35, 1.0)
		var b := Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(sc * rng.randf_range(0.9, 1.4), sc * 0.7, sc))
		blk.append(Transform3D(b, Vector3(t.x, boden_sq(sv, qv) + sc * 0.2, t.y)))
	tries = 0
	while farn.size() < n_farn and tries < 600:
		tries += 1
		var sv2 := rng.randf_range(s0 + 6.0, s1 - 5.0)
		var sd2 := -1.0 if rng.randf() < 0.5 else 1.0
		var qv2 := sd2 * (_tab(_breite_tab, sv2) + rng.randf_range(-0.3, 0.5))
		if _kanal_bei(sv2, qv2):
			continue
		var t2 := tal(sv2, qv2)
		var sc2 := rng.randf_range(0.6, 1.3)
		farn.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(sc2, sc2 * rng.randf_range(0.7, 1.1), sc2)),
				Vector3(t2.x, boden_sq(sv2, qv2) - 0.02, t2.y)))
	for i in range(n_sims):
		var sv3 := rng.randf_range(s0 + 10.0, s1 - 8.0)
		var sd3 := -1.0 if i % 2 == 0 else 1.0
		var tp0 := tal(sv3, sd3 * qmax * 0.5)
		var F := _tab(_boden_tab, sv3)
		var R: float = Bt.H(tp0.x, tp0.y)
		if R - F < 5.0:
			continue
		var f := rng.randf_range(0.25, 0.8)
		var w3 := _tab(_breite_tab, sv3)
		var dicke := 2.2 + 0.3 * (R - F)
		var qv3 := sd3 * (w3 + f * dicke - 0.35)
		var t3 := tal(sv3, qv3)
		var hy := boden_sq(sv3, qv3)
		var yaw := atan2(qd.y, qd.x)
		var b3 := Basis(Vector3.UP, -yaw).scaled(Vector3(rng.randf_range(0.5, 0.9), rng.randf_range(0.18, 0.3), rng.randf_range(1.2, 2.6)))
		sims.append(Transform3D(b3, Vector3(t3.x, hy, t3.y)))
	tries = 0
	while stamm.size() < n_baum and tries < 200:
		tries += 1
		var sv4 := rng.randf_range(s0 + 4.0, s1 - 2.0)
		var sd4 := -1.0 if rng.randf() < 0.5 else 1.0
		var tp1 := tal(sv4, sd4 * qmax * 0.5)
		var dicke4 := 2.2 + 0.3 * maxf(0.0, Bt.H(tp1.x, tp1.y) - _tab(_boden_tab, sv4))
		var qv4 := sd4 * (_tab(_breite_tab, sv4) + dicke4 + rng.randf_range(1.5, 7.0))
		if absf(qv4) > qmax - 3.0:
			continue
		var t4 := tal(sv4, qv4)
		var hy4 := boden_sq(sv4, qv4)
		var hb := rng.randf_range(5.0, 8.5)
		stamm.append(Transform3D(Basis.from_scale(Vector3(1, hb, 1)), Vector3(t4.x, hy4 + hb * 0.5, t4.y)))
		krone.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3(1, hb * 0.75, 1)), Vector3(t4.x, hy4 + hb * 0.62, t4.y)))
	# 21.11.: scree at the foot of the walls, big half-buried chunks, overhanging slabs high up
	var geroell: Array = []
	var brocken: Array = []
	var dach: Array = []
	for i5 in range(60 if lite else 150):
		var sv5 := rng.randf_range(s0 + 7.0, s1 - 5.0)
		var sd5 := -1.0 if rng.randf() < 0.5 else 1.0
		var w5 := _tab(_breite_tab, sv5)
		var qv5 := sd5 * (w5 + rng.randf_range(-1.4, 1.2) * rng.randf())       # dense at the foot, a fan into the floor
		if _kanal_bei(sv5, qv5) or absf(qv5) < 3.2:
			continue
		var t5 := tal(sv5, qv5)
		var sc5 := rng.randf_range(0.08, 0.32)
		geroell.append(Transform3D(Basis(Vector3(rng.randf(), 1, rng.randf()).normalized(), rng.randf() * TAU).scaled(Vector3(sc5 * 1.3, sc5 * 0.7, sc5)),
				Vector3(t5.x, boden_sq(sv5, qv5) + sc5 * 0.15, t5.y)))
	for i6 in range(10 if lite else 22):
		var sv6 := rng.randf_range(s0 + 9.0, s1 - 6.0)
		var sd6 := -1.0 if rng.randf() < 0.5 else 1.0
		var qv6 := sd6 * (_tab(_breite_tab, sv6) + rng.randf_range(0.2, 1.2))
		if _kanal_bei(sv6, qv6):
			continue
		var t6 := tal(sv6, qv6)
		var sc6 := rng.randf_range(1.0, 2.2)
		brocken.append(Transform3D(Basis(Vector3.UP, rng.randf() * TAU).rotated(Vector3.RIGHT, rng.randf_range(-0.3, 0.3)).scaled(Vector3(sc6, sc6 * 0.75, sc6 * 1.2)),
				Vector3(t6.x, boden_sq(sv6, qv6) + sc6 * 0.05, t6.y)))
	for i7 in range(8 if lite else 16):
		var sv7 := rng.randf_range(s0 + 10.0, s1 - 8.0)
		var sd7 := -1.0 if i7 % 2 == 0 else 1.0
		var tp7 := tal(sv7, sd7 * qmax * 0.5)
		var F7 := _tab(_boden_tab, sv7)
		var R7: float = Bt.H(tp7.x, tp7.y)
		if R7 - F7 < 8.0:
			continue
		var f7 := rng.randf_range(0.55, 0.85)
		var dicke7 := 2.2 + 0.3 * (R7 - F7)
		var qv7 := sd7 * (_tab(_breite_tab, sv7) + f7 * dicke7 - 0.9)
		var t7 := tal(sv7, qv7)
		var yaw7 := atan2(qd.y, qd.x)
		var b7 := Basis(Vector3.UP, -yaw7).rotated(Vector3(qd.x, 0, qd.y).normalized(), sd7 * rng.randf_range(0.05, 0.18)).scaled(
				Vector3(rng.randf_range(1.6, 2.8), rng.randf_range(0.5, 0.9), rng.randf_range(2.5, 5.0)))
		dach.append(Transform3D(b7, Vector3(t7.x, boden_sq(sv7, qv7) + 0.3, t7.y)))
	var kl := SphereMesh.new()
	kl.radius = 1.0
	kl.height = 1.5
	kl.radial_segments = 6
	kl.rings = 3
	_mm(holder, kl, fels_m, geroell)
	var gr := SphereMesh.new()
	gr.radius = 1.0
	gr.height = 1.7
	gr.radial_segments = 9 if lite else 14
	gr.rings = 5 if lite else 8
	_mm(holder, gr, fels_m, brocken)
	var dk := BoxMesh.new()
	dk.size = Vector3(1, 1, 1)
	_mm(holder, dk, fels_material(true, Color(0.92, 0.9, 0.88)), dach)
	var sph := SphereMesh.new()
	sph.radius = 1.0
	sph.height = 1.6
	sph.radial_segments = 8 if lite else 12
	sph.rings = 5 if lite else 7
	_mm(holder, sph, fels_m, blk)
	var bx := BoxMesh.new()
	bx.size = Vector3(1, 1, 1)
	_mm(holder, bx, fels_m, sims)
	var fm := CylinderMesh.new()                       # a tuft of fern: an open funnel of green
	fm.top_radius = 0.38
	fm.bottom_radius = 0.04
	fm.height = 0.42
	fm.radial_segments = 6
	fm.rings = 1
	fm.cap_top = false
	var fmat := StandardMaterial3D.new()
	fmat.albedo_color = Color(0.3, 0.46, 0.18)
	fmat.roughness = 0.95
	fmat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_mm(holder, fm, fmat, farn)
	var tm := CylinderMesh.new()
	tm.top_radius = 0.08
	tm.bottom_radius = 0.16
	tm.height = 1.0
	tm.radial_segments = 6
	var tmat := StandardMaterial3D.new()
	tmat.albedo_color = Color(0.36, 0.26, 0.18)
	_mm(holder, tm, tmat, stamm)
	var cm := CylinderMesh.new()                       # larch crown: a slim cone, warm green
	cm.top_radius = 0.0
	cm.bottom_radius = 1.4
	cm.height = 1.0
	cm.radial_segments = 7
	var cmat := StandardMaterial3D.new()
	cmat.albedo_color = Color(0.42, 0.52, 0.22)
	cmat.roughness = 0.9
	_mm(holder, cm, cmat, krone)


func _rect() -> Array:
	"""[centre, half, turn] of the set in valley coordinates (for the clip)"""
	var mid := tal((s0 + s1) * 0.5, 0.0)
	return [mid, Vector2((s1 - s0) * 0.5 - 0.3, qmax - 0.3), atan2(d.y, d.x)]


func _ausschneiden() -> void:
	"""the ground of the valley is not drawn where the set is (bergtal.clip_ground, with the rooms of bergtal_orte.gd)"""
	var r := _rect()
	var clips: Array = []
	if bt.orte != null and bt.orte.get("_clips") is Array:
		clips = (bt.orte._clips as Array).duplicate()
	clips.append([r[0], r[1], r[2], -10000.0, 10000.0])
	for cell in bt._chunk_mi:
		for mi in bt._chunk_mi[cell]:
			if is_instance_valid(mi):
				_mat_alt[mi] = (mi as MeshInstance3D).material_override
	bt.clip_ground(clips)


func _steine_weg() -> void:
	"""rocks, grass, flowers of the valley inside the set would float in the air: hidden (scale 0) until the end"""
	var inv: Transform3D = bt.tal.global_transform.affine_inverse()
	for mmi in bt.tal.find_children("*", "MultiMeshInstance3D", true, false):
		var mm: MultiMesh = (mmi as MultiMeshInstance3D).multimesh
		if mm == null or mm.transform_format != MultiMesh.TRANSFORM_3D:
			continue
		var xf: Transform3D = inv * (mmi as Node3D).global_transform
		var n := mm.visible_instance_count if mm.visible_instance_count >= 0 else mm.instance_count
		for i in range(n):
			var it := mm.get_instance_transform(i)
			var p := xf * it.origin
			if drin(Vector2(p.x, p.z)):
				_mm_alt.append([mm, i, it])
				mm.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3.ONE * 0.0001), it.origin))


func aufraeumen() -> void:
	for mi in _mat_alt:
		if is_instance_valid(mi):
			(mi as MeshInstance3D).material_override = _mat_alt[mi]
	_mat_alt.clear()
	for e in _mm_alt:
		if is_instance_valid(e[0]):
			(e[0] as MultiMesh).set_instance_transform(int(e[1]), e[2])
	_mm_alt.clear()
	if mesh_mi != null and is_instance_valid(mesh_mi):
		mesh_mi.queue_free()
	mesh_mi = null


func info() -> Dictionary:
	return {"mitte": [c.x, c.y], "s": [s0, s1], "versteckt": _mm_alt.size(), "ausschnitt": _mat_alt.size(), "ecken": ecken, "bau_ms": bau_ms}
