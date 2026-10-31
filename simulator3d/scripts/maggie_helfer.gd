extends RefCounted
## «Maggie und der Bergkristall» – die lieben Tiere (Paket S2, Daniel 31.10.2026). Werden von maggie_hund.gd gebaut und
## bewegt (h = maggie_hund.gd: Figuren, Töne, Wege, Rahmen-API).
##   * Eule (Waldkauz, ≈ 40 cm): im Winter und überall, wenn es dunkel ist – sitzt auf einem Pfosten vor dir, ruft
##     «hu-huu» und fliegt zur nächsten Stelle, sobald du nah bist; ein schwaches Licht zeigt den Weg zur nächsten Station.
##   * Steinbock: im Sommer an der Felsstufe (Station «s_fels») – kommt herunter und trägt dich über die steilen Felsen.
##   * Murmeltier (nicht im Winter: Winterschlaf Oktober … April): pfeift laut, wenn böse Tiere kommen (Gruppe
##     «maggie_boese»), und zeigt im Frühling seinen Geheimgang (Station «f_loecher»).
##   * Fuchs (lieb und schlau): sind böse Tiere nah, taucht er auf, bellt hell und rennt weg – sie laufen ihm nach
##     (ruft ablenken(welt_pos, s) der bösen Tiere, falls S3 das hat). Im Herbst begrüsst er dich am Anfang.
## Jede Region: eine kleine Begrüssungs-Szene des Tiers, das dort zu Hause ist.

const T = preload("res://scripts/i18n.gd")
const EULE_C := 24.0                 # Federkleid-Oberfläche einer Eule nachts ≈ 20–26 °C (gut isoliert)

var h                                # maggie_hund.gd
var region := ""
var c := Vector2.ZERO
var root: Node3D                     # Tal-Raum (Eule, Pfosten)
var fuchs: Node3D
var murmel: Node3D
var bock: Node3D
var eule: Node3D
var _eule_fl: Array = []             # Flügel-Pivots
var _eule_licht: OmniLight3D
var _pfosten: Node3D
var _e := {"auf": false, "fliegt": false, "von": Vector3.ZERO, "nach": Vector3.ZERO, "f": 0.0, "p": Vector3.ZERO}
var _fq := {"a": null, "q": [], "t": 0.0}      # Fuchs
var _mq := {"a": null, "q": [], "t": 0.0}      # Murmeltier
var _bq := {"a": null, "q": [], "t": 0.0}      # Steinbock
var _fuchs_bis := 0.0
var _murmel_bis := 0.0
var _gruss := {}
var _uhr := 0.0
var szenen: Array = []               # was schon gespielt hat (für Tests)


func _init(h_) -> void:
	h = h_


func aufraeumen() -> void:
	for a in [fuchs, murmel, bock]:
		if a != null and is_instance_valid(a):
			a.queue_free()
	if root != null and is_instance_valid(root):
		root.queue_free()
	_eule_fl = []
	_e["fliegt"] = false
	_e["auf"] = false
	fuchs = null
	murmel = null
	bock = null
	eule = null


func region_bauen(r: String, c_: Vector2, stationen: Array) -> void:
	aufraeumen()
	region = r
	c = c_
	_gruss = {}
	root = Node3D.new()
	root.name = "maggie_helfer"
	h.holder.add_child(root)
	var fp: Vector2 = h._platz(c + Vector2(-8, -6))
	fuchs = h.actor("fox", h.G(fp.x, fp.y), h.G(c.x, c.y), 1.2)
	fuchs.visible = r == "herbst"
	if r == "herbst":
		h.idle(fuchs, "sit")
	_fq["a"] = fuchs
	_fq["q"] = []
	if r != "winter":
		var mp: Vector2 = h._platz(c + Vector2(8, 6))
		murmel = h.marmot(h.G(mp.x, mp.y), h.G(c.x, c.y))
		murmel.visible = r == "fruehling"
		_mq["a"] = murmel
		_mq["q"] = []
	if r == "sommer":
		for st_ in stationen:
			if str(st_.get("helfer", "")) == "steinbock":
				var o: Vector3 = st_["oben"]
				bock = h.actor("ibex", Vector3(o.x, float(st_["oben_y"]), o.z), h.G(o.x, o.z - 5.0), 1.0)
				h.place(bock, Vector3(o.x, float(st_["oben_y"]), o.z), true)
				_bq["a"] = bock
				_bq["q"] = []
	_eule_bauen()


# ---- die Eule ---------------------------------------------------------------------------------------------------------
func _eule_bauen() -> void:
	eule = Node3D.new()
	root.add_child(eule)
	var braun := Color(0.46, 0.37, 0.28)
	h.part(eule, h.sphm(0.15, 0.34, 10), Vector3(0, 0.17, 0), braun, EULE_C)
	h.part(eule, h.sphm(0.12, 0.26, 10), Vector3(0, 0.14, -0.05), braun.lightened(0.35), EULE_C)        # helle Brust
	var kopf: Node3D = h.node(eule, Vector3(0, 0.38, 0))
	h.part(kopf, h.sphm(0.12, 0.22, 10), Vector3.ZERO, braun, EULE_C + 2.0)
	h.part(kopf, h.sphm(0.09, 0.15, 10), Vector3(0, -0.01, -0.06), braun.lightened(0.45), EULE_C + 2.0, Vector3.ZERO, Vector3(1.2, 1.0, 0.4))
	for sx in [-1, 1]:
		h.light_part(kopf, h.sphm(0.025), Vector3(sx * 0.045, 0.01, -0.105), h.glow_mat(Color(1.0, 0.7, 0.15), 2.5))
		var fl: Node3D = h.node(eule, Vector3(sx * 0.13, 0.26, 0.02))
		h.part(fl, h.sphm(0.12, 0.3, 8), Vector3(sx * 0.02, -0.08, 0), braun.darkened(0.15), EULE_C - 4.0, Vector3.ZERO, Vector3(0.35, 1.0, 1.0))
		_eule_fl.append(fl)
	h.part(kopf, h.cylm(0.0, 0.015, 0.04, 4), Vector3(0, -0.03, -0.12), Color(0.75, 0.65, 0.4), EULE_C, Vector3(PI / 2, 0, 0))   # Schnabel
	_pfosten = h.node(root, Vector3.ZERO)
	h.part(_pfosten, h.cylm(0.06, 0.08, 1.5, 6), Vector3(0, 0.75, 0), Color(0.36, 0.27, 0.18), "tree")
	_eule_licht = h.lamp(eule, Vector3(0, -0.6, 0), Color(1.0, 0.85, 0.6), 0.7, 7.0)
	eule.visible = false
	_pfosten.visible = false
	_e["auf"] = false


func _eule_aktiv() -> bool:
	return region == "winter" or h.dark()


func _eule_tick(dt: float) -> void:
	if eule == null:
		return
	var st_: Dictionary = h.aktuell()
	if not _eule_aktiv() or st_.is_empty():
		if not bool(_e["fliegt"]):
			eule.visible = false
			_pfosten.visible = false
			_e["auf"] = false
		return
	var sp: Vector3 = h._spieler()
	var ziel: Vector3 = st_["p"]
	if not bool(_e["auf"]):                       # zum ersten Mal: 8 m vor dir, Richtung Station
		var d0 := ziel - sp
		var p0 := sp + d0.normalized() * minf(8.0, d0.length() * 0.6) if d0.length() > 1.0 else sp + Vector3(3, 0, 0)
		_eule_setzen(p0)
		_e["auf"] = true
		if not _gruss.has("eule"):
			_gruss["eule"] = true
			_hu(p0)
			h.tipp(T.t("Eine Eule ruft «Hu-huu». Sie fliegt voraus und zeigt dir den Weg im Dunkeln."))
			szenen.append("eule")
	if bool(_e["fliegt"]):
		_e["f"] = minf(1.0, float(_e["f"]) + dt / maxf(1.0, (_e["von"] as Vector3).distance_to(_e["nach"]) / 5.0))
		var f := float(_e["f"])
		var q: Vector3 = (_e["von"] as Vector3).lerp(_e["nach"], f)
		var y := float(h.bt.H(q.x, q.z)) + 1.5 + sin(f * PI) * 2.5
		eule.position = Vector3(q.x, y, q.z)
		var fd: Vector3 = (_e["nach"] as Vector3) - (_e["von"] as Vector3)
		eule.rotation.y = atan2(-fd.x, -fd.z)
		for i in range(_eule_fl.size()):
			(_eule_fl[i] as Node3D).rotation.z = sin(_uhr * 14.0) * 0.9 * (1 if i == 0 else -1)
		if f >= 1.0:
			_e["fliegt"] = false
			_eule_setzen(_e["nach"])
			_hu(_e["nach"])
		return
	for fl in _eule_fl:
		(fl as Node3D).rotation.z = 0.0
	var ep: Vector3 = _e["p"]
	var zu_ziel := ep.distance_to(ziel)
	if sp.distance_to(ep) < 6.0 and zu_ziel > 5.0:   # du bist nah: sie fliegt weiter
		var nach := ep + (ziel - ep).normalized() * minf(14.0, zu_ziel - 3.0)
		nach = Vector3(nach.x, 0, nach.z)
		var p2: Vector2 = h._platz(Vector2(nach.x, nach.z))
		_e["von"] = ep
		_e["nach"] = Vector3(p2.x, 0, p2.y)
		_e["f"] = 0.0
		_e["fliegt"] = true
		_pfosten.visible = false
	elif eule.get_child_count() > 0:                  # sitzt: dreht den Kopf zu dir
		var to := sp - ep
		eule.rotation.y = lerp_angle(eule.rotation.y, atan2(-to.x, -to.z), dt * 2.0)


func _eule_setzen(p: Vector3) -> void:
	var g: Vector3 = h.G(p.x, p.z)
	_pfosten.position = g
	_pfosten.visible = true
	eule.position = g + Vector3(0, 1.5, 0)
	eule.visible = true
	_e["p"] = Vector3(p.x, 0, p.z)


func _hu(p: Vector3) -> void:
	# Waldkauz-Ruf: «huu … hu-hu-huuu», Grundton ≈ 400–500 Hz (Vogelwarte)
	h.sound(p, "hoot", [[0.0, 0.5, 450.0, 430.0, 1.0], [0.9, 0.18, 440.0, 440.0, 0.7], [1.15, 0.6, 450.0, 420.0, 0.9]], -6.0, -20.0)


# ---- Fuchs und Murmeltier: Hilfe, wenn böse Tiere nah sind -------------------------------------------------------------
func _fuchs_tick(dt: float) -> void:
	if fuchs == null or not is_instance_valid(fuchs):
		return
	var sp: Vector3 = h._spieler()
	if h._q_tick(_fq, dt) and fuchs.visible and region != "herbst" and not _gruss.has("fuchs_sitzt"):
		fuchs.visible = false
	if region == "herbst" and not _gruss.has("fuchs") and fuchs.visible and sp.distance_to(h.ppos(fuchs)) < 9.0:
		_gruss["fuchs"] = true
		szenen.append("fuchs_gruss")
		h.tipp(T.t("Ein Fuchs schaut dich freundlich an und wedelt mit dem Schwanz. Er will dir helfen!"))
		var weg: Vector2 = h._platz(Vector2(c.x - 30, c.y - 4))
		_fq["q"] = [{"t": "wait", "s": 3.0}, {"t": "call", "fn": func(): h.idle(fuchs, "")},
			{"t": "walk", "p": Vector3(weg.x, 0, weg.y), "spd": 2.5}, {"t": "call", "fn": func(): fuchs.visible = false}]
	if _uhr < _fuchs_bis or not (_fq["q"] as Array).is_empty():
		return
	var nah: Array = h.boese_nah(sp, 16.0)
	if nah.is_empty():
		return
	_fuchs_bis = _uhr + 75.0
	var bp: Vector3 = nah[0][1]
	_ablenken(sp + (sp - bp).normalized().rotated(Vector3.UP, 1.4) * 9.0, bp, nah)


func _ablenken(von: Vector3, gefahr: Vector3, nah: Array) -> void:
	"""der Fuchs taucht bei «von» auf, bellt hell und rennt quer weg - die bösen Tiere hinter ihm her"""
	var weg := gefahr + (gefahr - von).normalized().rotated(Vector3.UP, -1.2) * 40.0
	var w2: Vector2 = h._platz(Vector2(weg.x, weg.z))
	h.place(fuchs, von)
	fuchs.visible = true
	h.idle(fuchs, "")
	szenen.append("fuchs_ablenken")
	h.tipp(T.t("Der Fuchs bellt hell und rennt davon. Die bösen Tiere laufen ihm nach!"))
	_fq["q"] = [{"t": "face", "p": gefahr}, {"t": "call", "fn": func(): _jip(h.ppos(fuchs))}, {"t": "wait", "s": 0.8},
		{"t": "call", "fn": func():
			var wp: Vector3 = h.W(h.G(w2.x, w2.y))
			for n in nah:
				if is_instance_valid(n[0]) and n[0].has_method("ablenken"):
					n[0].ablenken(wp, 8.0)},
		{"t": "walk", "p": Vector3(w2.x, 0, w2.y), "spd": 6.0}, {"t": "call", "fn": func(): fuchs.visible = false}]


func _jip(p: Vector3) -> void:
	h.sound(p, "yip", [[0.0, 0.12, 1100.0, 900.0, 1.0], [0.22, 0.12, 1150.0, 900.0, 0.9], [0.44, 0.15, 1100.0, 850.0, 0.9]], -3.0, -10.0)


func _murmel_tick(dt: float) -> void:
	if murmel == null or not is_instance_valid(murmel):
		return
	h._q_tick(_mq, dt)
	var sp: Vector3 = h._spieler()
	if region == "fruehling" and not _gruss.has("murmel") and sp.distance_to(h.ppos(murmel)) < 12.0:
		_gruss["murmel"] = true
		szenen.append("murmel_gruss")
		_pfiff(murmel, 4.0)
		h.tipp(T.t("Ein Murmeltier pfeift und schaut dich an. Es kennt hier alle Geheimgänge."))
	if _uhr < _murmel_bis or not (_mq["q"] as Array).is_empty():
		return
	var nah: Array = h.boese_nah(sp, 34.0)
	if nah.is_empty():
		return
	_murmel_bis = _uhr + 50.0
	var bp: Vector3 = nah[0][1]
	var mp: Vector2 = h._platz(Vector2(sp.x, sp.z) + Vector2(bp.x - sp.x, bp.z - sp.z).normalized().rotated(0.9) * 8.0)
	h.place(murmel, Vector3(mp.x, 0, mp.y))
	h.face(murmel, bp - Vector3(mp.x, 0, mp.y))
	szenen.append("murmel_warnt")
	_pfiff(murmel, 3.0)
	h.tipp(T.t("Ein Murmeltier pfeift laut: Achtung, Gefahr!"))


func _pfiff(a: Node3D, s: float) -> void:
	# Alarmpfiff des Murmeltiers: kurz und schrill, 2–3 kHz
	a.visible = true
	h.sound(h.ppos(a), "whistle", [[0.0, 0.25, 2600.0, 2400.0, 1.0], [0.45, 0.25, 2600.0, 2400.0, 1.0]], -2.0, -6.0)
	_mq["q"] = [{"t": "idle", "k": "sit_up", "s": s}, {"t": "call", "fn": func(): a.visible = region == "fruehling" and not _gruss.has("murmel_bau")}]


# ---- Szenen, die maggie_hund.gd auslöst --------------------------------------------------------------------------------
func szene(name: String, st_: Dictionary) -> void:
	szenen.append(name)
	match name:
		"murmeltier_loch":                        # das Murmeltier schaut aus dem richtigen Loch und zeigt den Gang
			if murmel == null or not is_instance_valid(murmel):
				return
			var lo: Array = st_["loch_p"]
			var p: Vector3 = lo[int(st_["richtig"])]
			h.place(murmel, p + Vector3(0, 0, 0.9))
			h.face(murmel, h._spieler() - p)
			_gruss["murmel_bau"] = true
			_pfiff(murmel, 2.5)
		"fuchs_ablenken":                         # Herbst, Weggabelung gelöst: der Fuchs lockt die Wildschweine weg
			var bp: Vector3 = st_["boese_p"]
			_ablenken(bp + Vector3(-3, 0, -2), bp + Vector3(0, 0, 3), h.boese_nah(bp, 30.0))
			if st_.has("busch"):
				h.sound(bp, "creak", [[0.0, 0.6, 200.0, 150.0, 0.6]], -8.0, -24.0, 1.2)
		"steinbock":                              # kommt herunter und trägt dich über die Felsen
			if bock == null or not is_instance_valid(bock):
				h._fertig(st_)
				return
			var p2: Vector3 = st_["p"]
			var o: Vector3 = st_["oben"]
			var oy := float(st_["oben_y"])
			var hinter: Vector3 = o + Vector3(0, 0, 4.0)
			var hp: Vector2 = h._platz(Vector2(hinter.x, hinter.z))
			_bq["q"] = [{"t": "walk", "p": p2 + Vector3(0, 0, -1.6), "spd": 1.6}, {"t": "call", "fn": func():
					h.tipp(T.t("Der Steinbock senkt den Kopf. Halte dich gut fest!"))},
				{"t": "wait", "s": 1.6}, {"t": "call", "fn": func(): _tragen(Vector3(o.x, oy, o.z))},
				{"t": "tp", "p": Vector3(o.x, oy, o.z), "y": true}, {"t": "wait", "s": 1.2},
				{"t": "call", "fn": func(): _tragen(Vector3(hp.x, 0, hp.y))},
				{"t": "tp", "p": h.G(hp.x, hp.y)}, {"t": "wait", "s": 0.6},
				{"t": "call", "fn": func(): h._fertig(st_)},
				{"t": "walk", "p": Vector3(o.x, 0, o.z + 10.0), "spd": 1.2}]


func _tragen(p: Vector3) -> void:
	"""die Figur (und Maggie) mit dem Steinbock an p setzen - Rahmen: spieler_setzen(welt_pos), falls er das hat"""
	var wp: Vector3 = h.W(h.G(p.x, p.z) if p.y == 0.0 else p)
	var s_ = h.story
	if s_ != null and s_.has_method("spieler_setzen"):
		s_.spieler_setzen(wp)
	elif s_ != null and "pos" in s_:
		s_.pos = Vector3(p.x, 0, p.z)
	if h.hund != null and is_instance_valid(h.hund):
		h.place(h.hund, Vector3(p.x, p.y, p.z + 0.8) if p.y != 0.0 else Vector3(p.x + 0.8, 0, p.z), p.y != 0.0)


func tick(dt: float) -> void:
	_uhr += dt
	_eule_tick(dt)
	_fuchs_tick(dt)
	_murmel_tick(dt)
	if bock != null and is_instance_valid(bock):
		h._q_tick(_bq, dt)
		if region == "sommer" and not _gruss.has("bock") and h._spieler().distance_to(h.ppos(bock)) < 30.0:
			_gruss["bock"] = true
			szenen.append("bock_gruss")
			h.tipp(T.t("Oben auf dem Felsen steht ein Steinbock und schaut zu dir herunter."))


func info() -> Dictionary:
	return {"eule": eule != null and eule.visible, "eule_fliegt": _e["fliegt"], "fuchs": fuchs != null and is_instance_valid(fuchs) and fuchs.visible,
		"murmel": murmel != null and is_instance_valid(murmel) and murmel.visible, "bock": bock != null and is_instance_valid(bock),
		"szenen": szenen}
