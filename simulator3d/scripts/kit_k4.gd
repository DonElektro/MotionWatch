extends Node
## «Die Karte des Grossvaters», Kapitel 4 «Nebel im Couloir»: die neuen Teile in einer eigenen Datei (kit_abenteuer.gd lädt
## je Kapitel kit_k<n>.gd und hängt es ein – gleiche Schnittstelle wie kit_k3.gd; kit_figur.gd bleibt unverändert):
##   * Nebel: dichter Nebel im Couloir (Umgebung), bis die Seilschaft beginnt.
##   * Wärmebild: die Kamera zeigt die Wärme-Ebene von MoveEye (Ebene 2: Menschen und Hunde warm, Fels kalt), der Nebel
##     dünn – damit findet man Lia und Maggie. Aktion «Wärmebild» schaltet um.
##   * Peilung: der Kompass zeigt nur den Kurs (keine Leuchtmarke am Boden), unten ein Kurs-Hinweis in Grad.
##   * Seilschaft: Lia sichert von Stand zu Stand, das Seil läuft von ihr über die eingehängten Haken zur Figur. Erst
##     einhängen (Aktion am Haken), dann an der Kante hochklettern.
##   * Klettersteig: am Stahlseil über den Spalt; vor jedem Anker umhängen – sonst geht es nicht weiter.
##   * Steinschlag (QTE warnen), Maggie im Rucksack, das alte Biwak mit dem Buch von {jahr}.

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")

var kit
var par
var main
var daten
var _layer: CanvasLayer
var _ziel = null

var nebel_an := false
var waerme_an := false
var _waerme_lab: Label
var _kurs_lab: Label
var _buch: PanelContainer
var peilung := {}

var seil := {"an": false, "haken": []}       # the rope: on, the clipped bolts (world points)
var _seil_mi: MeshInstance3D
var _seil_im: ImmediateMesh
var anker := {}                              # anchor id -> clipped
var _anker_pos := {}                         # anchor id -> [s, q]
var _stand_i := 0
var rucksack := false
var _biwak_kugeln: Array = []
var gestuerzt := false


const WAERME_SCHIRM := """
shader_type canvas_item;
uniform sampler2D scr : hint_screen_texture, filter_linear_mipmap;
void fragment() {
	vec3 c = texture(scr, SCREEN_UV).rgb;
	float l = dot(c, vec3(0.3, 0.59, 0.11));
	float warm = clamp((c.r + c.b - 2.0 * c.g) * 1.4, 0.0, 1.0);          // the glow of warm bodies is magenta
	float t = clamp(l * 0.32 + warm, 0.0, 1.0);
	vec3 o = mix(vec3(0.02, 0.01, 0.1), vec3(0.3, 0.02, 0.42), smoothstep(0.0, 0.3, t));   // «iron»: cold dark violet ...
	o = mix(o, vec3(0.95, 0.35, 0.05), smoothstep(0.35, 0.7, t));                        // ... warm orange ...
	o = mix(o, vec3(1.0, 0.95, 0.65), smoothstep(0.72, 1.0, t));                         // ... hot pale yellow
	float n = fract(sin(dot(SCREEN_UV * 517.0 + TIME, vec2(12.9898, 78.233))) * 43758.5453);
	COLOR = vec4(o + (n - 0.5) * 0.04, 1.0);
}
"""
const WAERME_GLUT := """
shader_type spatial;
render_mode unshaded, fog_disabled, blend_add, cull_back, depth_draw_never;
uniform float k = 1.0;
void fragment() {
	float f = 0.55 + 0.45 * pow(1.0 - abs(dot(NORMAL, VIEW)), 1.5);
	ALBEDO = vec3(1.0, 0.0, 1.0) * f * k;
}
"""
var _schirm: ColorRect
var _glut_mat: ShaderMaterial


func _init(k) -> void:
	kit = k
	process_priority = 1000                                # after bergtal.gd: its fog tick would undo the fog of the couloir
	par = k.par
	main = k.main
	daten = k.daten
	name = "kit_k4"


# =======================================================================================================================
# the set
# =======================================================================================================================
func bauen() -> void:
	_layer = CanvasLayer.new()
	_layer.layer = 118
	add_child(_layer)
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = UI.theme()
	_layer.add_child(root)
	_waerme_lab = _label(root, 20, Color(1.0, 0.7, 0.3))
	_waerme_lab.text = T.t("WÄRMEBILD · MoveEye")
	_waerme_lab.visible = false
	_kurs_lab = _label(root, 20, Color(1.0, 0.9, 0.55))
	_kurs_lab.visible = false
	_haken_bauen()
	_klettersteig_bauen()
	_biwak_bauen()
	_seil_im = ImmediateMesh.new()
	_seil_mi = MeshInstance3D.new()
	_seil_mi.mesh = _seil_im
	var sm := StandardMaterial3D.new()
	sm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	sm.albedo_color = Color(1.0, 0.45, 0.1)
	_seil_mi.material_override = sm
	_seil_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	main.add_child(_seil_mi)


func _label(root: Control, sz: int, col: Color) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", sz)
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("outline_size", 6)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(l)
	return l


func _wand_punkt(sv: float, qv: float, h: float) -> Vector3:
	"""valley point at [s, q], h over the floor there"""
	var t: Vector2 = par.tal(sv, qv)
	return Vector3(t.x, par._H(t.x, t.y) + h, t.y)


func _haken_bauen() -> void:
	var eisen := Color(0.62, 0.63, 0.66)
	for hk in daten.SEIL["haken"]:
		var n: Node3D = par.node(par.holder, _wand_punkt(float(hk[1]), float(hk[2]), float(hk[3])), -par.rot)
		par.part(n, par.cylm(0.05, 0.05, 0.06, 8), Vector3.ZERO, eisen, 10.0, Vector3(0, 0, PI * 0.5))
		par.part(n, par.sphm(0.06, 0.12, 8), Vector3(0, 0.05, 0), eisen, 10.0)


func _klettersteig_bauen() -> void:
	"""the steel cable on the north wall over the strip, anchors with an eye"""
	var ks: Dictionary = daten.KLETTERSTEIG
	var h := float(ks["seil_h"])
	var pts: Array = []
	var sv := 34.0
	while sv <= 41.2:
		pts.append(par.W(_wand_punkt(sv, -4.15, h)))
		sv += 0.6
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(pts.size() - 1):
		var a: Vector3 = pts[i]
		var b: Vector3 = pts[i + 1]
		var L := a.distance_to(b)
		var tr := Transform3D(Basis.looking_at(b - a, Vector3.UP), (a + b) * 0.5)
		st.append_from(par.cylm(0.012, 0.012, L, 5), 0, tr * Transform3D(Basis(Vector3.RIGHT, PI * 0.5), Vector3.ZERO))
	var cable := MeshInstance3D.new()
	cable.mesh = st.commit()
	cable.material_override = par.m.mat(Color(0.72, 0.74, 0.77))
	main.add_child(cable)
	cable.set_meta("k4", true)
	_anker_pos.clear()
	for an in ks["anker"]:
		_anker_pos[str(an[0])] = [float(an[1]), float(an[2])]
		var n: Node3D = par.node(par.holder, _wand_punkt(float(an[1]), -4.15, h), -par.rot)
		par.part(n, par.cylm(0.06, 0.06, 0.22, 8), Vector3(0.1, 0, 0), Color(0.55, 0.56, 0.6), 10.0, Vector3(0, 0, PI * 0.5))
		par.part(n, par.sphm(0.07, 0.04, 8), Vector3(0.22, 0, 0), Color(0.85, 0.7, 0.2), 10.0)


func _biwak_bauen() -> void:
	"""the old bivouac: low stone walls, a tin roof, a door (to the couloir, west), a bench, a shelf for the book"""
	var bw: Dictionary = daten.BIWAK
	var c: Vector2 = par.tal(float(bw["c"][0]), float(bw["c"][1]))
	var ls := float(bw["gross"][0]) * 0.5
	var lq := float(bw["gross"][1]) * 0.5
	var y0: float = par._H(c.x, c.y)
	var n: Node3D = par.node(par.holder, Vector3(c.x, y0, c.y), -par.rot)        # local x = q, z = s
	var stein := Color(0.5, 0.48, 0.45)
	var h := 2.2
	var d := 0.25
	par.fels(par.part(n, par.boxm(lq * 2.0, h, d), Vector3(0, h * 0.5, -ls + d * 0.5), stein, "stone"))      # east (back) - local +z is down the couloir (west)
	par.fels(par.part(n, par.boxm(d, h, ls * 2.0), Vector3(-lq + d * 0.5, h * 0.5, 0), stein, "stone"))     # north
	par.fels(par.part(n, par.boxm(d, h, ls * 2.0), Vector3(lq - d * 0.5, h * 0.5, 0), stein, "stone"))      # south
	var tuer_q := -0.6                                                                           # the door: west, a little north (q 1.8)
	var tb := 0.95
	var links := (tuer_q - tb * 0.5) - (-lq)
	var rechts := lq - (tuer_q + tb * 0.5)
	par.fels(par.part(n, par.boxm(links, h, d), Vector3(-lq + links * 0.5, h * 0.5, ls - d * 0.5), stein, "stone"))
	par.fels(par.part(n, par.boxm(rechts, h, d), Vector3(lq - rechts * 0.5, h * 0.5, ls - d * 0.5), stein, "stone"))
	par.fels(par.part(n, par.boxm(tb, h - 1.85, d), Vector3(tuer_q, 1.85 + (h - 1.85) * 0.5, ls - d * 0.5), stein, "stone"))
	par.part(n, par.boxm(lq * 2.0 + 0.4, 0.08, ls * 2.0 + 0.4), Vector3(0, h + 0.04, 0), Color(0.55, 0.22, 0.16), "tent")   # the tin roof
	par.part(n, par.boxm(0.5, 0.45, ls * 2.0 - 0.6), Vector3(lq - 0.55, 0.22, 0.1), Color(0.42, 0.3, 0.2), "tree")       # the bench
	par.part(n, par.boxm(0.6, 0.06, 0.32), Vector3(0.2, 0.72, -ls + 0.38), Color(0.42, 0.3, 0.2), "tree")               # the shelf (east wall)
	var lab := Label3D.new()
	lab.text = "BIWAK"
	lab.font_size = 64
	lab.pixel_size = 0.004
	lab.modulate = Color(0.95, 0.92, 0.85)
	lab.outline_size = 8
	n.add_child(lab)
	lab.position = Vector3(0.3, h - 0.25, ls + 0.01)      # on the door wall (west), its text towards the couloir
	# a small window in the door wall (south of the door): dark glass by day, warm candle light at night
	_fenster_mat = StandardMaterial3D.new()
	_fenster_mat.albedo_color = Color(0.12, 0.13, 0.15)
	_fenster_mat.emission_enabled = true
	_fenster_mat.emission = Color(1.0, 0.68, 0.32)
	_fenster_mat.emission_energy_multiplier = 0.0
	var fenster := MeshInstance3D.new()
	fenster.mesh = par.boxm(0.62, 0.46, 0.04)
	fenster.material_override = _fenster_mat
	n.add_child(fenster)
	fenster.position = Vector3(1.15, 1.3, ls + 0.005)
	par.part(n, par.boxm(0.04, 0.5, 0.06), Vector3(1.15, 1.3, ls + 0.02), Color(0.36, 0.25, 0.16), "tree")      # the cross of the frame
	par.part(n, par.boxm(0.66, 0.04, 0.06), Vector3(1.15, 1.3, ls + 0.02), Color(0.36, 0.25, 0.16), "tree")
	par.part(n, par.boxm(0.74, 0.06, 0.1), Vector3(1.15, 1.04, ls + 0.04), Color(0.36, 0.25, 0.16), "tree")      # the sill
	var kerze := OmniLight3D.new()                       # the candle on the shelf: lights the room, the door and the window
	kerze.light_color = Color(1.0, 0.62, 0.3)
	kerze.omni_range = 4.5
	kerze.light_energy = 0.0
	kerze.shadow_enabled = false
	n.add_child(kerze)
	kerze.position = Vector3(0.4, 1.2, -ls + 0.6)
	var schein := OmniLight3D.new()                      # its glow outside, in front of the window and the door
	schein.light_color = Color(1.0, 0.6, 0.28)
	schein.omni_range = 3.2
	schein.light_energy = 0.0
	n.add_child(schein)
	schein.position = Vector3(0.6, 1.1, ls + 0.7)
	_biwak_lichter = [kerze, schein]
	# walls for people and for the camera (the door stays open)
	var mitte: Vector3 = par.W(Vector3(c.x, y0, c.y))
	var rot_y: float = -par.rot
	for wd in [[Vector3(0, 0, -ls), lq * 2.0, d], [Vector3(-lq, 0, 0), d, ls * 2.0], [Vector3(lq, 0, 0), d, ls * 2.0],
			[Vector3(-lq + links * 0.5, 0, ls), links, d], [Vector3(lq - rechts * 0.5, 0, ls), rechts, d]]:
		var lp: Vector3 = Basis(Vector3.UP, rot_y) * (wd[0] as Vector3)
		main.add_obstacle_box(mitte + lp, float(wd[1]), float(wd[2]), rot_y)
		main.set_obstacle_height(2.2)


func kugeln_welt() -> Array:
	return []


var _glut_t := 0.0


var _hund_glut: MeshInstance3D = null


func _glut_setzen(on: bool) -> void:
	"""the glow on the meshes of the warm bodies; Maggie gets a glowing body of her own (her model ignored the overlay)"""
	if kit.hund != null and kit.hund.hund != null and is_instance_valid(kit.hund.hund):
		if on and (_hund_glut == null or not is_instance_valid(_hund_glut)):
			_hund_glut = MeshInstance3D.new()
			_hund_glut.mesh = par.sphm(1.0, -1.0, 10)
			_hund_glut.scale = Vector3(0.17, 0.2, 0.36)
			_hund_glut.position = Vector3(0, 0.36, 0)
			_hund_glut.material_override = _glut_mat
			kit.hund.hund.add_child(_hund_glut)
		elif not on and _hund_glut != null and is_instance_valid(_hund_glut):
			_hund_glut.queue_free()
			_hund_glut = null
	for n in _warme_koerper():
		for mi in n.find_children("*", "MeshInstance3D", true, false):
			if (mi as MeshInstance3D).layers & 1:
				(mi as MeshInstance3D).material_overlay = _glut_mat if on else null


func _warme_koerper() -> Array:
	var out: Array = []
	if kit.figur != null and kit.figur.ok():
		out.append(kit.figur.a)
	if kit.hund != null and is_instance_valid(kit.hund):
		out.append(kit.hund)
	for id in kit.personen:
		var a = kit.personen[id]
		if a != null and is_instance_valid(a):
			out.append(a)
	return out


var nacht := false
var _fenster_mat: StandardMaterial3D
var _biwak_lichter: Array = []
var _himmel_t := 0.0
var _detail_vorher := -1.0


func nacht_setzen(on: bool) -> void:
	"""the last scene: a clear night over the bivouac - a dark sky with stars, the candle in the window"""
	nacht = on
	if on:
		_buch_zeigen(false)
	if _fenster_mat != null:
		_fenster_mat.emission_energy_multiplier = 3.2 if on else 0.0
	for l in _biwak_lichter:
		if is_instance_valid(l):
			(l as OmniLight3D).light_energy = (2.2 if l == _biwak_lichter[0] else 1.1) if on else 0.0
	if main.sky_mat != null:
		main.sky_mat.set_shader_parameter("star_vis", 1.0 if on else -1.0)
		main.sky_mat.set_shader_parameter("milky", 0.55 if on else 0.0)
		if on and _detail_vorher < 0.0:                  # (stars need the sky's detail - simple graphics too, for this short film)
			_detail_vorher = float(main.sky_mat.get_shader_parameter("detail"))
		elif not on and _detail_vorher >= 0.0:
			main.sky_mat.set_shader_parameter("detail", _detail_vorher)
			_detail_vorher = -1.0
	if not on and main.env != null:
		main.env.fog_sky_affect = 0.35                   # (main's value; colors.gd sets the aerial perspective again)
	if on:
		nebel_an = false
		if main.env != null and main.sky_mat != null:
			_nacht_licht(true)                               # (at once - not one frame of the day's sky)


func _process(dt: float) -> void:
	if nebel_an and main.env != null and kit.running:
		main.env.fog_density = 0.02 if waerme_an else 0.075     # (the thermal picture sees through the fog)
	if nacht and main.env != null and main.sky_mat != null and kit.running:   # the last scene: a clear, dark night
		_himmel_t -= dt
		_nacht_licht(_himmel_t <= 0.0)


func _nacht_licht(himmel: bool) -> void:
	if himmel and not bool(main.get("sim_active")) and main.has_method("_update_sky"):
		_himmel_t = 0.5                                       # (main only updates the sky while the simulation runs)
		main._update_sky()
	main.sky_mat.set_shader_parameter("star_vis", 1.0)        # (others set the stars too: every frame)
	main.sky_mat.set_shader_parameter("milky", 0.55)
	main.sky_mat.set_shader_parameter("detail", 1.0)
	main.env.tonemap_exposure = 0.9
	main.env.ambient_light_color = Color(0.32, 0.4, 0.6)
	main.env.ambient_light_energy = 0.2
	main.env.fog_density = 0.0025
	main.env.fog_light_color = Color(0.05, 0.07, 0.12)
	main.env.fog_aerial_perspective = 0.0                     # (it takes the fog colour from the sky's light map - still the day's)
	main.env.fog_sky_affect = 0.1
	if kit.bt != null and kit.bt.get("_fog_k") != null:
		kit.bt._fog_k = 0.0


# =======================================================================================================================
# hooks from kit_abenteuer.gd
# =======================================================================================================================
func schritt_start(st: Dictionary) -> void:
	if bool(st.get("peilung", false)):
		var p: Dictionary = daten.PEILUNG
		var a: Vector3 = par.welt(float(p["von"][0]), float(p["von"][1]))
		var b: Vector3 = par.welt(float(p["nach"][0]), float(p["nach"][1]))
		var dw := Vector3(b.x - a.x, 0, b.z - a.z).normalized()
		peilung = {"dir": dw, "grad": posmod(roundi(rad_to_deg(atan2(dw.x, -dw.z)) + kit.nord_off()), 360), "ziel": b}
	else:
		peilung = {}


func ziel():
	return _ziel


func kein_marker() -> bool:
	"""no glowing point on the ground while walking on the bearing (only the compass)"""
	return not peilung.is_empty()


func tick(dt: float, ein: Dictionary) -> Dictionary:
	if not kit.running or kit.phase in ["pause", "laden"]:
		return ein
	_ziel = null
	if not peilung.is_empty() and kit.phase == "spiel":
		_peilung_tick()
	else:
		_kurs_lab.visible = false
	if not anker.is_empty() or kit.szene_i >= 0 and str(kit.daten.SZENEN[kit.szene_i]["id"]) == "s05_querung":
		ein = _klettersteig_tick(ein)
	_seil_zeichnen()
	_innen_kamera_tick()
	if _buch != null and (kit.szene_i < 0 or str(kit.daten.SZENEN[kit.szene_i]["id"]) != "s10_eintrag"):
		_buch_zeigen(false)                              # (the card belongs to its scene only - also after a skip)
	if nacht and kit.szene_i >= 0 and str(kit.daten.SZENEN[kit.szene_i]["id"]) != "s12_nacht":
		nacht_setzen(false)                              # (tests and pictures jump back to earlier scenes)
	if rucksack and kit.hund != null and kit.hund.hund != null:
		var fp: Vector3 = kit.figur.pos()
		var back: Vector3 = fp - kit.figur.vorne() * 0.32 + Vector3(0, 1.05, 0)
		var q: Vector3 = kit.hund.VL(back)
		kit.hund.modus = "warten"
		kit.hund.place(kit.hund.hund, q, true)
		kit.hund.hund.rotation.y = kit.figur.a.rotation.y
	if waerme_an:
		_glut_t -= dt
		if _glut_t <= 0.0:                                 # (models are swapped / added later: Maggie, Lia)
			_glut_t = 0.5
			_glut_setzen(true)
		_waerme_lab.position = Vector2((_layer.get_viewport().get_visible_rect().size.x - _waerme_lab.size.x) * 0.5, 64)
	if kit.figur.zustand == "haengen" and kit.szene_i >= 0 and str(kit.daten.SZENEN[kit.szene_i]["id"]) == "s05_querung":
		if not gestuerzt:
			gestuerzt = true
			kit.merke("gestuerzt")
			kit.sag(kit.tx("Halt dich fest! – Lia hält das Seil."), "lia")
	return ein


# the camera inside the bivouac: a fixed corner on the door wall (the one further from the figure), looking at the
# shelf with the book and turning a little after the figure; the follow camera would look down onto the head
const INNEN_ECKEN := [[52.75, 0.75], [52.75, 4.05]]     # s, q: the two corners of the door (west) wall
const INNEN_REGAL := [55.3, 2.6, 0.75]                   # the shelf on the east wall
var _innen_shot := {}
var _innen_ecke := -1


func im_biwak(w: Vector3) -> bool:
	var d: Dictionary = daten.DECKEN[0]
	var sq: Vector2 = par.sq_von(w)
	return absf(sq.x - float(d["s"])) < float(d["ls"]) - 0.12 and absf(sq.y - float(d["q"])) < float(d["lq"]) - 0.12


func _innen_kamera_tick() -> void:
	var r = kit.regie
	var eigen: bool = not _innen_shot.is_empty() and r.art == "shot" and is_same(r._shot, _innen_shot)
	var drin: bool = kit.phase == "spiel" and not r.film_an and kit.figur.ok() and im_biwak(kit.figur.pos())
	if not drin:
		if eigen:
			r.zur_folge(0.5)
		_innen_shot = {}
		_innen_ecke = -1
		return
	if r.art != "folge" and not eigen:
		return
	if not eigen:
		_innen_ecke = -1
	var sq: Vector2 = par.sq_von(kit.figur.pos())
	var dist := []
	for e in INNEN_ECKEN:
		dist.append(Vector2(float(e[0]), float(e[1])).distance_to(sq))
	var beste := 0 if dist[0] > dist[1] else 1
	if _innen_ecke < 0 or (beste != _innen_ecke and dist[beste] > dist[_innen_ecke] + 0.6):   # (with a little hysteresis)
		_innen_ecke = beste
		var e: Array = INNEN_ECKEN[beste]
		_innen_shot = {"art": "fix", "s": float(e[0]), "q": float(e[1]), "h": 1.8, "fov": 74.0, "blick": INNEN_REGAL.duplicate(), "blende": 0.4}
		r.shot(_innen_shot, eigen)                   # (a soft blend on entering, a cut between the corners)
	var rg: Vector2 = Vector2(float(INNEN_REGAL[0]), float(INNEN_REGAL[1]))
	var mitte: Vector2 = rg.lerp(sq, 0.55)
	_innen_shot["blick"] = [mitte.x, mitte.y, lerpf(float(INNEN_REGAL[2]), 1.1, 0.55)]


func _peilung_tick() -> void:
	var fp: Vector3 = kit.figur.pos()
	var dw: Vector3 = peilung["dir"]
	_ziel = fp + dw * 40.0 + Vector3(0, 1.0, 0)            # the compass shows the bearing, not a point
	var v: Vector3 = kit.figur.vorne()
	var mein := posmod(roundi(rad_to_deg(atan2(v.x, -v.z)) + kit.nord_off()), 360)
	_kurs_lab.visible = true
	_kurs_lab.text = T.t("Kurs %d° · du gehst %d°") % [int(peilung["grad"]), mein]
	var vs: Vector2 = _layer.get_viewport().get_visible_rect().size
	_kurs_lab.position = Vector2((vs.x - _kurs_lab.size.x) * 0.5, vs.y - 150)


func aktion(art: String, ak: Dictionary) -> void:
	var id := str(ak.get("id", ""))
	match art:
		"waerme":
			kit.erledigt.erase(id)                           # it switches - done is set when it is on
			par.erledigt.erase(id)
			waerme_schalten(not waerme_an)
		"haken":
			_einhaengen(id)
		"anker":
			anker[id] = true
			kit.ton("klick")
			kit.figur.a.aktion("heben", 0.7)
			kit.sag(kit.tx("Umgehängt. Weiter."), "figur")


func waerme_schalten(on: bool) -> void:
	"""the thermal picture of MoveEye: the screen in a cold palette, warm bodies (the figure, Lia, Maggie) glow through the
	fog (an overlay without fog on their meshes, magenta - the screen shader makes it orange-yellow)"""
	waerme_an = on
	if _schirm == null:
		var sm := ShaderMaterial.new()
		var sh := Shader.new()
		sh.code = WAERME_SCHIRM
		sm.shader = sh
		_schirm = ColorRect.new()
		_schirm.material = sm
		_schirm.set_anchors_preset(Control.PRESET_FULL_RECT)
		_schirm.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var lay := CanvasLayer.new()
		lay.layer = 1                                       # under the HUD
		add_child(lay)
		lay.add_child(_schirm)
		_glut_mat = ShaderMaterial.new()
		var gs := Shader.new()
		gs.code = WAERME_GLUT
		_glut_mat.shader = gs
	_schirm.visible = on
	_glut_setzen(on)
	_waerme_lab.visible = on
	if on:
		kit.erledigt["waerme"] = true
		par.erledigt["waerme"] = true
		kit.hud.toast(T.t("Wärmebild an – Aktion schaltet zurück"), 2.5)


func _einhaengen(id: String) -> void:
	"""a bolt: the rope runs through it; Lia climbs to the stand below it"""
	var hk: Array = []
	var i := 0
	for h in daten.SEIL["haken"]:
		if str(h[0]) == id:
			hk = h
			break
		i += 1
	if hk.is_empty():
		return
	seil["haken"].append(par.W(_wand_punkt(float(hk[1]), float(hk[2]), float(hk[3]))))
	kit.ton("klick")
	kit.figur.a.aktion("heben", 0.7)
	kit.sag(kit.tx("Eingehängt!") if i > 0 else kit.tx("Eingehängt! Ich sichere."), "lia" if i == 0 else "figur")
	_lia_zum_stand(i)


func _lia_sicher(sv: float, qv: float):
	"""Lia as a figure of the kit (created when missing, e.g. after a jump between scenes)"""
	var a = kit.personen.get("lia", null)
	if a == null or not is_instance_valid(a):
		var d: Dictionary = (daten.LIA as Dictionary).duplicate(true)
		d["s"] = sv
		d["q"] = qv
		d["blick"] = [sv + 1.0, qv]
		kit._person("lia", d)
		a = kit.personen.get("lia", null)
	return a


func _lia_zum_stand(i: int) -> void:
	var L: Array = daten.SEIL["lia_stand"]
	if i >= L.size():
		return
	_stand_i = i
	var a = _lia_sicher(float(L[i][0]), float(L[i][1]))
	if a == null or not is_instance_valid(a):
		return
	var w: Vector3 = par.welt(float(L[i][0]), float(L[i][1]))
	var gy: float = main.ground_y(w.x, w.z)
	par.place(a, par.VL(Vector3(w.x, gy, w.z)), true)
	par.face(a, kit.figur.pos() - w)


func _klettersteig_tick(ein: Dictionary) -> Dictionary:
	"""the next anchor not clipped: no step past it (the lanyard is short) - the stick forward is taken out"""
	if kit.phase != "spiel":
		return ein
	var me: Vector2 = par.sq_von(kit.figur.pos())
	for an in daten.KLETTERSTEIG["anker"]:
		var aid := str(an[0])
		if anker.has(aid):
			continue
		var grenze := float(an[1]) + float(daten.KLETTERSTEIG["vor"])
		if me.y < -2.0 and me.x > grenze - 0.6:
			var mv: Vector2 = ein.get("mv", Vector2.ZERO)
			var ax: Vector2 = kit.tal_dir_welt(Vector2(1, 0)).normalized()
			if mv.dot(ax) > 0.0:
				ein = ein.duplicate()
				ein["mv"] = mv - ax * mv.dot(ax)
				if not bool(_meldung.get(aid, false)):
					_meldung[aid] = true
					kit.sag(kit.tx("Erst umhängen! Aktion am Anker."), "lia")
			if me.x > grenze:                                 # (a jump): back to the anchor
				var w: Vector3 = par.welt(grenze - 0.05, me.y)
				kit.figur.a.position.x = w.x
				kit.figur.a.position.z = w.z
		break
	return ein


var _meldung := {}


var _rohr: Mesh = null


func _seil_zeichnen() -> void:
	if _rohr == null:
		_rohr = par.cylm(0.018, 0.018, 1.0, 5)
	_seil_mi.mesh = null
	var pts: Array = []
	var a = kit.personen.get("lia", null)
	if bool(seil["an"]) and a != null and is_instance_valid(a):
		pts.append((a as Node3D).global_position + Vector3(0, 0.95, 0))
		for h in seil["haken"]:
			pts.append(h)
		pts.append(kit.figur.pos() + Vector3(0, 0.95, 0))
	elif not anker.is_empty() or (kit.szene_i >= 0 and str(kit.daten.SZENEN[kit.szene_i]["id"]) == "s05_querung"):
		var last := ""                                       # the lanyard to the last clipped anchor
		for an in daten.KLETTERSTEIG["anker"]:
			if anker.has(str(an[0])):
				last = str(an[0])
		if last != "":
			var ap: Array = _anker_pos[last]
			pts.append(par.W(_wand_punkt(float(ap[0]), -4.0, float(daten.KLETTERSTEIG["seil_h"]))))
			pts.append(kit.figur.pos() + Vector3(0, 0.95, 0))
	if pts.size() < 2:
		return
	var st := SurfaceTool.new()                             # a thin tube (a line of 1 px got lost in the fog)
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(pts.size() - 1):
		var p: Vector3 = pts[i]
		var q: Vector3 = pts[i + 1]
		var mid := (p + q) * 0.5 - Vector3(0, 0.02 * p.distance_to(q), 0)   # a little slack
		for seg in [[p, mid], [mid, q]]:
			var a3: Vector3 = seg[0]
			var b3: Vector3 = seg[1]
			var L := a3.distance_to(b3)
			if L < 0.02:
				continue
			var up := Vector3.UP if absf((b3 - a3).normalized().dot(Vector3.UP)) < 0.95 else Vector3.RIGHT
			var tr := Transform3D(Basis.looking_at(b3 - a3, up), (a3 + b3) * 0.5)
			st.append_from(_rohr, 0, tr * Transform3D(Basis(Vector3.RIGHT, PI * 0.5), Vector3.ZERO).scaled_local(Vector3(1, L, 1)))
	_seil_mi.mesh = st.commit()


func film(e: Dictionary, sprung: bool) -> void:
	match str(e.get("k", "")):
		"nebel":
			nebel_an = bool(e.get("an", true))
			if not nebel_an and main.env != null:
				main.env.fog_density = 0.0035
				main.weather = "cloudy"
				if kit.bt != null and kit.bt.get("_fog_k") != null:
					kit.bt._fog_k = 0.0                       # (the valley's fog would fade for 40 s - and light the night)
				waerme_schalten(false)
		"waerme":
			waerme_schalten(bool(e.get("an", false)))
		"person_k4":
			var id := str(e["id"])
			var a = kit.personen.get(id, null)
			if a == null or not is_instance_valid(a):
				var d: Dictionary = (daten.LIA as Dictionary).duplicate(true)
				d["s"] = e["s"]
				d["q"] = e["q"]
				d["blick"] = e.get("blick", [float(e["s"]) - 1.0, float(e["q"])])
				kit._person(id, d)
			else:
				var w: Vector3 = par.welt(float(e["s"]), float(e["q"]))
				par.place(a, par.VL(Vector3(w.x, main.ground_y(w.x, w.z), w.z)), true)
		"seil_an":
			seil["an"] = true
			seil["haken"] = []
			_lia_zum_stand(0)
		"seil_aus":
			seil["an"] = false
		"steinschlag":
			_steinschlag(sprung)
		"lia_reagiert":
			if kit.merker.has("lia_gewarnt"):
				kit.sag(kit.tx("Danke! Das war knapp."), "lia")
				if not kit.merker.has("gestuerzt"):
					kit.merke("seilschaft")
			else:
				kit.sag(kit.tx("Au! … Nur ein Kratzer. Nächstes Mal ruf bitte."), "lia")
		"maggie_rucksack":
			rucksack = bool(e.get("an", true))
			if not rucksack and kit.hund != null:
				kit.hund.setzen_welt(kit.figur.pos() + kit.figur.vorne().cross(Vector3.UP) * 0.9)
		"nacht":
			nacht_setzen(bool(e.get("an", true)))
		"logbuch_zeigen":
			_buch_zeigen(true)
		"logbuch_weg":
			_buch_zeigen(false)


func _steinschlag(sprung: bool) -> void:
	if sprung:
		return
	kit.regie.schuetteln(0.5)
	var a = kit.personen.get("lia", null)
	var ziel: Vector3 = (a as Node3D).global_position if a != null and is_instance_valid(a) else kit.figur.pos()
	for i in range(7):
		var st := MeshInstance3D.new()
		st.mesh = par.sphm(0.2 + 0.08 * (i % 3), -1.0, 6)
		st.scale = Vector3(1.0, 0.75, 0.9)
		st.material_override = par.m.mat(Color(0.3, 0.28, 0.26))
		main.add_child(st)
		var von := ziel + Vector3(0.5 * (i - 3), 4.5 + i * 0.6, 1.2 - 0.4 * i)
		st.global_position = von
		var tw := st.create_tween()
		tw.tween_property(st, "global_position", ziel + Vector3(0.8 * (i - 3), 0.15, 0.9 + 0.25 * i), 1.1 + 0.18 * i).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		tw.tween_interval(6.0)
		tw.tween_callback(st.queue_free)


func _buch_zeigen(on: bool) -> void:
	if _buch != null:
		_buch.queue_free()
		_buch = null
	if not on:
		return
	_buch = PanelContainer.new()
	_buch.add_theme_stylebox_override("panel", UI.box(Color(0.88, 0.82, 0.66, 0.97), Color(0.45, 0.3, 0.18, 0.9), 8, 22, 2))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	_buch.add_child(v)
	for zeile in [[kit.tx("Biwakbuch · {jahr}"), 22], [kit.tx("«Sturm seit Mittag. Toni verletzt, bleibt hier. Ich steige ab und hole Hilfe. – G.»"), 18],
			[kit.tx("«Zwei Tage nach dem Sturm. Biwak leer. Toni nicht mehr da. Keine Spur. – Bergrettung»"), 18]]:
		var l := Label.new()
		l.text = str(zeile[0])
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size = Vector2(460, 0)
		l.add_theme_font_size_override("font_size", int(zeile[1]))
		l.add_theme_color_override("font_color", Color(0.25, 0.16, 0.1))
		v.add_child(l)
	_layer.get_child(0).add_child(_buch)
	_buch.reset_size()
	var vs: Vector2 = _layer.get_viewport().get_visible_rect().size
	_buch.position = Vector2(maxf(8.0, vs.x - _buch.size.x - maxf(16.0, vs.x * 0.03)), vs.y * 0.12)   # (on the right: Lia and the figure stay free)


func control(d: Dictionary) -> Dictionary:
	match str(d.get("was", "info")):
		"waerme":
			waerme_schalten(bool(d.get("an", true)))
	return {"ok": true, "info": info()}


func info() -> Dictionary:
	return {"nebel": nebel_an, "waerme": waerme_an, "peilung": peilung.get("grad", -1), "seil": bool(seil["an"]),
		"haken": (seil["haken"] as Array).size(), "anker": anker.keys(), "rucksack": rucksack, "gestuerzt": gestuerzt, "nacht": nacht,
		"himmel": _himmel_info()}


func _himmel_info() -> Dictionary:
	if main.sky_mat == null:
		return {}
	var sm: ShaderMaterial = main.sky_mat
	var top = sm.get_shader_parameter("top_color")
	return {"nacht": sm.get_shader_parameter("night"), "sterne": sm.get_shader_parameter("star_vis"), "detail": sm.get_shader_parameter("detail"),
		"oben": (top as Color).to_html(false) if top is Color else "", "hell": snappedf(float(main.env.tonemap_exposure), 0.01) if main.env != null else 0.0}


func aufraeumen() -> void:
	waerme_schalten(false)
	if nacht:
		nacht_setzen(false)
	if _layer != null and is_instance_valid(_layer):
		_layer.queue_free()
	if _seil_mi != null and is_instance_valid(_seil_mi):
		_seil_mi.queue_free()
	for c in main.get_children():
		if c is MeshInstance3D and c.has_meta("k4"):
			c.queue_free()
