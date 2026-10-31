extends RefCounted
## «Maggie und der Bergkristall» – die Dinge der Welt (Paket S1 «Rahmen»): Daten der vier Regionen (Jahreszeiten),
## Rastplätze, Jahreszeiten-Tor, Bergkapelle am Gipfel, der Kristall, Leuchtsäulen, einfache erzeugte Klänge.
## Alles aus einfachen Formen im Code (keine Modell-Dateien). Lite (Quality.lite()): keine Schatten, weniger Teilchen.
## Tal-Koordinaten wie bergtal.gd (x = Osten, z = Süden); jede Region baut das Bergtal neu, ihr erster Rastplatz ist
## der Schlafplatz «frei» (dort stehen das Zelt und MoveEye).

const Quality = preload("res://scripts/quality.gd")

const HELPER_LAYER := 128             # main.HELPER_LAYER: only the window sees it, never a camera of MoveEye

# region id -> data. rests: Rastplätze (valley x, z) – the first one is the spot of MoveEye; tor: the Jahreszeiten-Tor.
# All points checked on the height map (slope < 12°, not in a lake; Probe 31.10.2026).
const REG := {
	"herbst": {"name": "Herbsttal", "col": Color(0.95, 0.55, 0.18), "hour": 16.6, "weather": "clear",
		"rests": [Vector2(-420, -230), Vector2(-694, -134)], "tor": Vector2(-810, -230),
		"short": "Gelbe Lärchen, Nebel über dem Moor – und Wildschweine.",
		"intro": "Im Herbsttal hängt Nebel über dem Moor. Die Lärchen leuchten gelb. Zwischen den Büschen wühlen Wildschweine – sie haben den Kristall gerochen. Zum Glück mögen Wildschweine kein Wasser.",
		"done": "Die Wildschweine sind weg. Du hast das Herbsttal geschafft!",
		"tipp": "Wildschweine mögen kein Wasser. Bäche und Flaschen sind deine Freunde."},
	"winter": {"name": "Wintertal", "col": Color(0.6, 0.82, 1.0), "hour": 15.9, "weather": "clear",
		"rests": [Vector2(470, 310), Vector2(632, 450)], "tor": Vector2(690, 330),
		"short": "Schnee am Gletscher, kurze Tage – und Wölfe.",
		"intro": "Im Wintertal liegt tiefer Schnee. Es wird früh dunkel. Hinter den Felsen heulen Wölfe. Sie wollen den Kristall – aber vor Feuer und hellem Licht haben sie Respekt.",
		"done": "Die Wölfe halten Abstand. Du hast das Wintertal geschafft!",
		"tipp": "Wölfe meiden helles Licht. Deine Fackel hilft dir."},
	"fruehling": {"name": "Frühlingstal", "col": Color(0.5, 0.9, 0.45), "hour": 9.4, "weather": "clear",
		"rests": [Vector2(-30, -250), Vector2(-142, -332)], "tor": Vector2(-250, -470),
		"short": "Schmelzwasser, Krokusse am See – und ein Krähenschwarm.",
		"intro": "Im Frühlingstal rauscht das Schmelzwasser. Am See blühen Krokusse. Aber über dem Wald kreist ein grosser Krähenschwarm. Lauten Glockenklang mögen die Krähen gar nicht.",
		"done": "Der Krähenschwarm ist davongeflogen. Du hast das Frühlingstal geschafft!",
		"tipp": "Krähen erschrecken vor lautem Glockenklang."},
	"sommer": {"name": "Sommertal", "col": Color(1.0, 0.85, 0.3), "hour": 18.8, "weather": "clear",
		"rests": [Vector2(-512, 548), Vector2(-420, 450)], "tor": Vector2(-650, 430),
		"short": "Hoch oben, warme Steine – und Vipern.",
		"intro": "Im Sommertal ist es warm. Hoch oben liegen viele Steine in der Sonne. Dazwischen schlängeln sich Vipern. Wenn du fest auftrittst, spüren sie das und verschwinden.",
		"done": "Die Vipern haben sich verkrochen. Du hast das Sommertal geschafft!",
		"tipp": "Vipern fliehen, wenn der Boden zittert. Stampf mit dem Wanderstock!"},
}
const ORDER := ["herbst", "winter", "fruehling", "sommer"]
# the walk at the start (Alp Tschuggen) and the summit with the chapel
const INTRO_SPOT := Vector2(30, 22)
const INTRO_DIG := Vector2(-10, 40)
const FIN_START := Vector2(-700, 450)
const CHAPEL := Vector2(-832, 512)

# what MoveEye would do (short, for children, no technical words) – per season and for some moments
const MOVEEYE := {
	"herbst": ["MoveEye würde jetzt merken, dass sich im Gebüsch etwas bewegt, und dir Bescheid geben.",
		"MoveEye würde im Nebel genau hinschauen, ob da ein Wildschwein steht oder nur ein Busch.",
		"MoveEye würde dir sagen, wo der nächste Bach ist."],
	"winter": ["MoveEye würde auch im Dunkeln merken, ob etwas Warmes hinter dem Felsen steht.",
		"MoveEye würde die Spuren im Schnee sehen und dir sagen, ob sie frisch sind.",
		"MoveEye würde jetzt sein Licht einschalten, damit die Wölfe Abstand halten."],
	"fruehling": ["MoveEye würde jetzt den Himmel beobachten und dir sagen, wenn die Krähen näher kommen.",
		"MoveEye würde merken, dass es im Wald plötzlich ganz still ist.",
		"MoveEye würde zählen, wie viele Krähen auf dem Baum sitzen."],
	"sommer": ["MoveEye würde zwischen den warmen Steinen nach etwas suchen, das sich schlängelt.",
		"MoveEye würde dir sagen, wo der Weg sicher ist.",
		"MoveEye würde merken, dass sich hinter dem Stein etwas bewegt hat."],
	"rast": ["MoveEye würde sich diesen Platz merken, damit du immer sicher zurückfindest.",
		"MoveEye würde hier auf dich warten und gut aufpassen."],
	"erwischt": ["MoveEye würde jetzt Wache halten und dich warnen, wenn das Tier zurückkommt.",
		"MoveEye würde dir zeigen, wo das Tier hingelaufen ist."],
	"start": ["MoveEye würde am Rastplatz bleiben und aufpassen, während du unterwegs bist."],
	"tor": ["MoveEye würde dir jetzt den Weg zum Tor zeigen."],
	"einstieg": ["MoveEye würde sehen, dass Maggie etwas gefunden hat – und dich rufen."],
	"finale": ["MoveEye würde jetzt einfach zuschauen – und sich mit dir freuen."],
}

static func lite() -> bool:
	return Quality.lite()


static func rests(id: String) -> Array:
	return REG[id]["rests"] if REG.has(id) else []


# ---- materials --------------------------------------------------------------------------------------------------------
static func mat(c: Color, rough := 0.9) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = rough
	return m


static func glow(c: Color, e := 2.0, alpha := 1.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(c, alpha)
	m.emission_enabled = true
	m.emission = c
	m.emission_energy_multiplier = e
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	if alpha < 1.0:
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	return m


static func box(parent: Node3D, size: Vector3, pos: Vector3, m: Material, rot := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	mi.material_override = m
	mi.position = pos
	mi.rotation = rot
	parent.add_child(mi)
	return mi


static func cyl(parent: Node3D, r0: float, r1: float, h: float, pos: Vector3, m: Material, seg := 12) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var cm := CylinderMesh.new()
	cm.top_radius = r0
	cm.bottom_radius = r1
	cm.height = h
	cm.radial_segments = seg
	cm.rings = 1
	mi.mesh = cm
	mi.material_override = m
	mi.position = pos
	parent.add_child(mi)
	return mi


# ---- the crystal ------------------------------------------------------------------------------------------------------
static func crystal(scale := 1.0) -> Node3D:
	"""a clear, glowing mountain crystal: a hexagonal prism with a pointed tip, a few small ones around it, soft light"""
	var n := Node3D.new()
	n.name = "crystal"
	var c := Color(0.62, 0.85, 1.0)
	var mb := glow(c, 1.6, 0.82)
	var mt := glow(Color(0.85, 0.95, 1.0), 2.4, 0.9)
	cyl(n, 0.055 * scale, 0.06 * scale, 0.16 * scale, Vector3(0, 0.08 * scale, 0), mb, 6)
	cyl(n, 0.0, 0.055 * scale, 0.08 * scale, Vector3(0, 0.2 * scale, 0), mt, 6)
	for k in range(3):
		var a := k * TAU / 3.0 + 0.4
		var s := Node3D.new()
		s.position = Vector3(cos(a) * 0.05, 0.02, sin(a) * 0.05) * scale
		s.rotation = Vector3(sin(a) * 0.5, 0, cos(a) * 0.5)
		n.add_child(s)
		cyl(s, 0.0, 0.025 * scale, 0.05 * scale, Vector3(0, 0.09 * scale, 0), mt, 6)
		cyl(s, 0.025 * scale, 0.028 * scale, 0.08 * scale, Vector3(0, 0.03 * scale, 0), mb, 6)
	var l := OmniLight3D.new()
	l.name = "light"
	l.light_color = c
	l.light_energy = 0.8
	l.omni_range = 3.5 * maxf(1.0, scale * 0.6)
	l.shadow_enabled = false
	l.position = Vector3(0, 0.12 * scale, 0)
	n.add_child(l)
	return n


# ---- a rest place: fire ring with embers, a log to sit on and a stone with the crystal sign ----------------------------
static func rest_place(nr: int, col: Color) -> Node3D:
	var n := Node3D.new()
	n.name = "rest%d" % nr
	var stone := mat(Color(0.45, 0.44, 0.42))
	for k in range(9):
		var a := k * TAU / 9.0
		var s := box(n, Vector3(0.28, 0.18, 0.22), Vector3(cos(a) * 0.55, 0.07, sin(a) * 0.55), stone, Vector3(0, -a, 0))
		s.scale = Vector3(1.0, 0.8 + 0.3 * sin(k * 2.1), 1.0)
	var emb := glow(Color(1.0, 0.45, 0.12), 1.4)
	box(n, Vector3(0.5, 0.06, 0.5), Vector3(0, 0.03, 0), emb, Vector3(0, 0.4, 0))
	var wood := mat(Color(0.36, 0.24, 0.14))
	var log1 := cyl(n, 0.16, 0.16, 1.6, Vector3(0, 0.16, 1.5), wood, 10)
	log1.rotation = Vector3(0, 0, PI / 2.0)
	# the stone with the crystal sign (lights up when reached)
	var post := box(n, Vector3(0.5, 0.9, 0.35), Vector3(1.4, 0.45, -0.6), mat(Color(0.52, 0.5, 0.47)), Vector3(0, 0.3, 0))
	post.name = "post"
	var sign_ := cyl(post, 0.0, 0.09, 0.2, Vector3(0, 0.2, 0.18), glow(col, 0.4, 0.95), 6)
	sign_.rotation = Vector3(PI / 2.0, 0, 0)
	sign_.name = "sign"
	var l := OmniLight3D.new()
	l.name = "ember"
	l.light_color = Color(1.0, 0.55, 0.25)
	l.light_energy = 0.7
	l.omni_range = 4.0
	l.shadow_enabled = false
	l.position = Vector3(0, 0.4, 0)
	n.add_child(l)
	return n


static func rest_lit(n: Node3D, col: Color) -> void:
	var post := n.get_node_or_null("post")
	if post == null:
		return
	var s := post.get_node_or_null("sign") as MeshInstance3D
	if s != null:
		s.material_override = glow(col, 2.6, 0.95)


# ---- the Jahreszeiten-Tor: two stone pillars and a lintel, a glowing sign of the season when it is open -----------------
static func gate(col: Color) -> Node3D:
	var n := Node3D.new()
	n.name = "gate"
	var st := mat(Color(0.5, 0.49, 0.46))
	for sx in [-1.0, 1.0]:
		box(n, Vector3(0.7, 3.4, 0.7), Vector3(sx * 1.7, 1.2, 0), st)        # (goes 0.5 m into the ground)
		box(n, Vector3(0.9, 0.3, 0.9), Vector3(sx * 1.7, 2.95, 0), st)
	box(n, Vector3(4.4, 0.5, 0.8), Vector3(0, 3.3, 0), st)
	var veil := MeshInstance3D.new()
	veil.name = "veil"
	var qm := QuadMesh.new()
	qm.size = Vector2(2.7, 2.9)
	veil.mesh = qm
	veil.position = Vector3(0, 1.45, 0)
	veil.material_override = glow(col, 0.3, 0.12)
	n.add_child(veil)
	var back := veil.duplicate() as MeshInstance3D           # seen from both sides
	back.name = "veil2"
	back.rotation.y = PI
	n.add_child(back)
	var sym := cyl(n, 0.0, 0.22, 0.4, Vector3(0, 3.3, 0.42), glow(col, 0.4, 0.9), 6)
	sym.rotation = Vector3(PI / 2.0, 0, 0)
	sym.name = "sign"
	var l := OmniLight3D.new()
	l.name = "light"
	l.light_color = col
	l.light_energy = 0.0
	l.omni_range = 7.0
	l.shadow_enabled = false
	l.position = Vector3(0, 1.6, 0)
	n.add_child(l)
	return n


static func gate_open(n: Node3D, col: Color, on: bool) -> void:
	for nm in ["veil", "veil2"]:
		var v := n.get_node_or_null(nm) as MeshInstance3D
		if v != null:
			v.material_override = glow(col, 1.8 if on else 0.3, 0.45 if on else 0.12)
	var s := n.get_node_or_null("sign") as MeshInstance3D
	if s != null:
		s.material_override = glow(col, 3.0 if on else 0.4, 0.95)
	var l := n.get_node_or_null("light") as OmniLight3D
	if l != null:
		l.light_energy = 1.6 if on else 0.0


# ---- a column of light far away (the next goal) – only the window sees it ----------------------------------------------
static func beam(col: Color) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.name = "beam"
	var cm := CylinderMesh.new()
	cm.top_radius = 0.15
	cm.bottom_radius = 0.45
	cm.height = 70.0
	cm.radial_segments = 8
	cm.rings = 1
	cm.cap_top = false
	cm.cap_bottom = false
	mi.mesh = cm
	var m := glow(col, 1.2, 0.22)
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	mi.material_override = m
	mi.layers = HELPER_LAYER
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mi


# ---- the small chapel on the summit (Bergkapelle) ------------------------------------------------------------------
# local: door at +z (towards the way up), altar at -z. Inside 3.0 × 4.4 m, walls 0.35 m.
const CH_W := 3.7
const CH_L := 5.1
const CH_T := 0.35
const CH_DOOR := 1.3
const ALTAR := Vector3(0, 0, -1.65)


static func chapel() -> Node3D:
	var n := Node3D.new()
	n.name = "chapel"
	var wall := mat(Color(0.86, 0.84, 0.78))
	var stone := mat(Color(0.5, 0.48, 0.45))
	var roofm := mat(Color(0.34, 0.33, 0.35))
	var wood := mat(Color(0.4, 0.27, 0.15))
	var hw := CH_W / 2.0
	var hl := CH_L / 2.0
	var h := 3.0
	box(n, Vector3(CH_W + 0.4, 4.0, CH_L + 0.4), Vector3(0, -1.95, 0), stone)                  # base (into the slope)
	box(n, Vector3(CH_W, h, CH_T), Vector3(0, h / 2.0, -hl + CH_T / 2.0), wall)                 # back
	box(n, Vector3(CH_T, h, CH_L), Vector3(-hw + CH_T / 2.0, h / 2.0, 0), wall)                 # sides
	box(n, Vector3(CH_T, h, CH_L), Vector3(hw - CH_T / 2.0, h / 2.0, 0), wall)
	var side_w := (CH_W - CH_DOOR) / 2.0
	for sx in [-1.0, 1.0]:                                                                    # front with the door
		box(n, Vector3(side_w, h, CH_T), Vector3(sx * (CH_DOOR / 2.0 + side_w / 2.0), h / 2.0, hl - CH_T / 2.0), wall)
	box(n, Vector3(CH_DOOR, 0.8, CH_T), Vector3(0, h - 0.4, hl - CH_T / 2.0), wall)
	# gable ends and roof
	var gab := 1.3
	for z in [-hl + CH_T / 2.0, hl - CH_T / 2.0]:
		for k in range(4):
			var wv := CH_W * (1.0 - (k + 0.5) / 4.0)
			box(n, Vector3(wv, gab / 4.0, CH_T), Vector3(0, h + gab * (k + 0.5) / 4.0, z), wall)
	var ang := atan2(gab, hw)
	var rl := sqrt(hw * hw + gab * gab) + 0.35
	for sx in [-1.0, 1.0]:
		box(n, Vector3(rl, 0.12, CH_L + 0.6), Vector3(sx * hw / 2.0, h + gab / 2.0 + 0.08, 0), roofm, Vector3(0, 0, -sx * ang))
	# small bell tower on the front
	box(n, Vector3(0.7, 1.0, 0.7), Vector3(0, h + gab + 0.3, hl - 0.6), wall)
	cyl(n, 0.0, 0.55, 0.9, Vector3(0, h + gab + 1.25, hl - 0.6), roofm, 4)
	cyl(n, 0.12, 0.2, 0.25, Vector3(0, h + gab + 0.55, hl - 0.6), mat(Color(0.7, 0.55, 0.25), 0.4), 10)
	# a cross on the tower
	box(n, Vector3(0.05, 0.45, 0.05), Vector3(0, h + gab + 1.9, hl - 0.6), wood)
	box(n, Vector3(0.28, 0.05, 0.05), Vector3(0, h + gab + 1.98, hl - 0.6), wood)
	# inside: floor, two benches, altar with the place for the crystal, candles
	box(n, Vector3(CH_W - 0.2, 0.1, CH_L - 0.2), Vector3(0, 0.0, 0), stone)
	for z in [0.3, 1.2]:
		box(n, Vector3(1.0, 0.08, 0.35), Vector3(-0.75, 0.45, z), wood)
		box(n, Vector3(1.0, 0.08, 0.35), Vector3(0.75, 0.45, z), wood)
		for sx in [-1.2, -0.3, 0.3, 1.2]:
			box(n, Vector3(0.08, 0.42, 0.3), Vector3(sx, 0.21, z), wood)
	box(n, Vector3(1.3, 0.95, 0.6), ALTAR + Vector3(0, 0.47, -0.05), stone)
	var holder := cyl(n, 0.16, 0.2, 0.18, ALTAR + Vector3(0, 1.04, 0), mat(Color(0.62, 0.6, 0.56)), 8)
	holder.name = "holder"
	for sx in [-0.5, 0.5]:
		cyl(n, 0.03, 0.03, 0.22, ALTAR + Vector3(sx, 1.06, 0.05), mat(Color(0.95, 0.93, 0.85)), 8)
		cyl(n, 0.0, 0.02, 0.05, ALTAR + Vector3(sx, 1.2, 0.05), glow(Color(1.0, 0.7, 0.3), 3.0), 6)
	var cl := OmniLight3D.new()
	cl.name = "candles"
	cl.light_color = Color(1.0, 0.72, 0.4)
	cl.light_energy = 1.0
	cl.omni_range = 4.5
	cl.shadow_enabled = false
	cl.position = ALTAR + Vector3(0, 1.4, 0.4)
	n.add_child(cl)
	# a window on each side (glowing a little)
	for sx in [-1.0, 1.0]:
		var wq := box(n, Vector3(0.05, 0.8, 0.5), Vector3(sx * (hw + 0.005), 1.8, -0.4), glow(Color(1.0, 0.8, 0.5), 0.6))
		wq.name = "window"
	return n


static func chapel_push(local: Vector3, r := 0.3) -> Vector3:
	"""keep a point (chapel coordinates) out of the walls and the altar; the door at +z stays open"""
	var hw := CH_W / 2.0
	var hl := CH_L / 2.0
	var sw := (CH_W - CH_DOOR) / 2.0
	var rects := [[0.0, -hl + CH_T / 2.0, hw, CH_T / 2.0], [-hw + CH_T / 2.0, 0.0, CH_T / 2.0, hl], [hw - CH_T / 2.0, 0.0, CH_T / 2.0, hl],
			[-(CH_DOOR / 2.0 + sw / 2.0), hl - CH_T / 2.0, sw / 2.0, CH_T / 2.0], [CH_DOOR / 2.0 + sw / 2.0, hl - CH_T / 2.0, sw / 2.0, CH_T / 2.0],
			[0.0, ALTAR.z - 0.05, 0.65, 0.3]]
	var p := local
	for q in rects:
		var dx: float = float(q[2]) + r - absf(p.x - float(q[0]))
		var dz: float = float(q[3]) + r - absf(p.z - float(q[1]))
		if dx > 0.0 and dz > 0.0:
			if dx < dz:
				p.x += dx * (1.0 if p.x >= float(q[0]) else -1.0)
			else:
				p.z += dz * (1.0 if p.z >= float(q[1]) else -1.0)
	return p


# ---- dirt flying while digging (the start) -----------------------------------------------------------------------------
static func dirt() -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = 14 if lite() else 40
	p.lifetime = 0.9
	p.explosiveness = 0.0
	p.direction = Vector3(0, 1, 0)
	p.spread = 35.0
	p.initial_velocity_min = 1.5
	p.initial_velocity_max = 3.0
	p.gravity = Vector3(0, -9.0, 0)
	p.scale_amount_min = 0.5
	p.scale_amount_max = 1.0
	var bm := BoxMesh.new()
	bm.size = Vector3(0.05, 0.05, 0.05)
	p.mesh = bm
	p.material_override = mat(Color(0.3, 0.22, 0.14))
	return p


static func sparkles(col: Color) -> CPUParticles3D:
	var p := CPUParticles3D.new()
	p.amount = 16 if lite() else 48
	p.lifetime = 1.6
	p.direction = Vector3(0, 1, 0)
	p.spread = 180.0
	p.initial_velocity_min = 0.3
	p.initial_velocity_max = 1.0
	p.gravity = Vector3(0, 0.4, 0)
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 0.4
	var qm := QuadMesh.new()
	qm.size = Vector2(0.05, 0.05)
	p.mesh = qm
	var m := glow(col, 3.0, 0.9)
	m.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	p.material_override = m
	return p


# ---- generated sounds (no files) --------------------------------------------------------------------------------------
const SR := 22050


static func _wav(data: PackedFloat32Array) -> AudioStreamWAV:
	var b := PackedByteArray()
	b.resize(data.size() * 2)
	for i in range(data.size()):
		b.encode_s16(i * 2, int(clampf(data[i], -1.0, 1.0) * 30000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = SR
	w.stereo = false
	w.data = b
	return w


static func snd_chime() -> AudioStreamWAV:
	"""the crystal: a clear, soft glassy sound"""
	var n := int(SR * 1.8)
	var d := PackedFloat32Array()
	d.resize(n)
	for i in range(n):
		var t := float(i) / SR
		var e := exp(-t * 2.4) * minf(1.0, t * 80.0)
		d[i] = e * (0.35 * sin(TAU * 1318.5 * t) + 0.22 * sin(TAU * 1975.5 * t) + 0.12 * sin(TAU * 2637.0 * t + 0.3) + 0.08 * sin(TAU * 3951.0 * t))
	return _wav(d)


static func snd_fanfare() -> AudioStreamWAV:
	"""a small happy tune (C E G C) – region done"""
	var notes := [523.25, 659.25, 783.99, 1046.5]
	var n := int(SR * 1.6)
	var d := PackedFloat32Array()
	d.resize(n)
	for i in range(n):
		var t := float(i) / SR
		var v := 0.0
		for k in range(notes.size()):
			var t0 := k * 0.18
			if t >= t0:
				var tt := t - t0
				var e := exp(-tt * (3.0 if k < 3 else 1.6)) * minf(1.0, tt * 60.0)
				v += e * (0.25 * sin(TAU * notes[k] * tt) + 0.08 * sin(TAU * notes[k] * 2.0 * tt))
		d[i] = v
	return _wav(d)


static func snd_whoosh() -> AudioStreamWAV:
	"""the short fright when an animal catches you: a soft rushing sound (no scream, nothing loud)"""
	var n := int(SR * 0.9)
	var d := PackedFloat32Array()
	d.resize(n)
	var lp := 0.0
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for i in range(n):
		var t := float(i) / SR
		var e := sin(PI * clampf(t / 0.9, 0.0, 1.0))
		lp = lerpf(lp, rng.randf_range(-1.0, 1.0), 0.08 + 0.2 * e)
		d[i] = lp * e * 0.6 + 0.1 * e * sin(TAU * (110.0 - 40.0 * t) * t)
	return _wav(d)


static func snd_rest() -> AudioStreamWAV:
	"""a rest place: two warm tones"""
	var n := int(SR * 0.9)
	var d := PackedFloat32Array()
	d.resize(n)
	for i in range(n):
		var t := float(i) / SR
		var f := 587.33 if t < 0.22 else 880.0
		var tt := t if t < 0.22 else t - 0.22
		d[i] = exp(-tt * 4.0) * minf(1.0, tt * 60.0) * (0.3 * sin(TAU * f * tt) + 0.1 * sin(TAU * f * 2.0 * tt))
	return _wav(d)
