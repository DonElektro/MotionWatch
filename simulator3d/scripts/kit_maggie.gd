extends "res://scripts/maggie_hund.gd"
## Abenteuer-Kit (Grossvater-Neubau, Besitzer 20.11.2026): Maggie als Begleiterin im neuen Spiel. Dieselbe Maggie wie in
## «Maggie und der Bergkristall» (maggie_hund.gd: Modell mit Skelett ab «mittel», Grundformen in Lite, Schwanz, Bellen,
## Knurren, Graben-Krümel, leuchtende Pfotenspuren) – ohne die Stationen der Maggie-Geschichte. Dazu:
##   * folgt der Figur (auf Steinen / Stufen springt sie mit; an Wänden und geschlossenen Toren wartet sie oder holt auf,
##     wenn man es nicht sieht)
##   * riechen(ziel): schnüffelt und legt eine sichtbare Spur zum Ziel
##   * warnen(p): knurrt und bellt in eine Richtung (Steinschlag, Rivalin)
##   * heben: die Figur hebt sie auf einen Sims (sie fliegt im Bogen hinauf und bleibt oben)
##   * steuern: an ein paar Stellen steuert man sie selbst (durch einen Spalt kriechen) – kit_abenteuer.gd gibt die
##     Richtung, dieses Skript prüft, wo sie stehen darf (kit.maggie_boden)
## Die Rahmen-API der Maggie-Geschichte (spieler_pos, region_aktiv) liefert kit_abenteuer.gd (story = kit).

var kit
var modus := "folgen"                # folgen | oben | gesteuert | getragen | warten
var _trag := {}
var _ziel_y = null                   # valley height to keep (on a ledge)
var tempo := 0.0


func G(x: float, z: float, dy := 0.0) -> Vector3:
	"""the ground of the kit (its own gorge), else the valley"""
	if kit != null and kit.par != null:
		return kit.par.G(x, z, dy)
	return super.G(x, z, dy)


func starten(k) -> bool:
	kit = k
	story = k
	if not _binden():
		return false
	_hund_bauen()
	if _layer != null:
		_layer.visible = false
	return true


func welt() -> Vector3:
	return hund.global_position if hund != null and is_instance_valid(hund) else Vector3.ZERO


func heading() -> float:
	return float(hund.heading) if hund != null and is_instance_valid(hund) else 0.0


func setzen_welt(w: Vector3) -> void:
	if hund == null or not is_instance_valid(hund):
		return
	var q := VL(w)
	place(hund, Vector3(q.x, 0, q.z))
	_ziel_y = null
	modus = "folgen"


func _folgen(dt: float) -> void:
	match modus:
		"oben", "warten":
			stop(hund, dt)
			face(hund, _spieler() - ppos(hund))
			tempo = 0.0
		"getragen":
			_getragen(dt)
		"gesteuert":
			pass                                          # steuern() moves her
		_:
			_folgen_kit(dt)


func _folgen_kit(dt: float) -> void:
	var sp := _spieler()
	var mv := sp - _sp_alt
	if mv.length() > 0.05:
		_sp_dir = mv.normalized()
		_steh_t = 0.0
	else:
		_steh_t += dt
	_sp_alt = sp
	var ziel := sp - _sp_dir * FOLGE_D + Vector3(-_sp_dir.z, 0, _sp_dir.x) * 0.7
	var hp := ppos(hund)
	var d := hp.distance_to(ziel)
	var frei: bool = kit.maggie_frei(Vector2(hp.x, hp.z), Vector2(ziel.x, ziel.z))
	if not frei:
		if d > 9.0 and unseen(W(G(hp.x, hp.z)), 30.0):
			_hin(ziel)
			return
		stop(hund, dt)
		face(hund, sp - hp)
		idle(hund, "sit", 1.0)
		tempo = 0.0
		return
	if d > WEIT_R and unseen(W(G(hp.x, hp.z)), 25.0):
		_hin(ziel)
		return
	if d > 0.6:
		idle(hund, "")
		var hy = kit.maggie_hoehe(Vector2(hp.x, hp.z))
		walk(hund, ziel, clampf(d * 1.3, 1.2, 5.5), dt, hy)
		tempo = float(hund.cur_speed)
	else:
		stop(hund, dt)
		tempo = 0.0
		face(hund, sp - hp)
		if _steh_t > 5.0 and (str(hund.idle_kind) == "" or hund.now_s() > float(hund.idle_until) + 2.0):
			idle(hund, ["sniff", "sit", "sniff", "schief"][randi() % 4], randf_range(2.0, 4.0))


func _hin(ziel: Vector3) -> void:
	var hy = kit.maggie_hoehe(Vector2(ziel.x, ziel.z))
	if hy == null:
		place(hund, ziel)
	else:
		place(hund, Vector3(ziel.x, float(hy), ziel.z), true)


# ---- lifting ---------------------------------------------------------------------------------------------------------------
func heben(von_welt: Vector3, nach_tal: Vector3) -> void:
	"""the figure lifts her from in front of it (world) onto a ledge (valley point with height)"""
	var a := VL(von_welt)
	_trag = {"a": a, "b": nach_tal, "t": 0.0}
	modus = "getragen"
	idle(hund, "")


func _getragen(dt: float) -> void:
	_trag["t"] = float(_trag["t"]) + dt
	var t := float(_trag["t"])
	var a: Vector3 = _trag["a"]
	var b: Vector3 = _trag["b"]
	if t < 0.6:                                           # first to the feet of the figure
		walk(hund, a, 2.5, dt)
		return
	var f := clampf((t - 0.6) / 1.1, 0.0, 1.0)
	var p := a.lerp(b, smoothstep(0.0, 1.0, f))
	var base := G(a.x, a.z).y
	var h := lerpf(base, b.y, f) + sin(f * PI) * 1.2
	place(hund, Vector3(p.x, h, p.z), true)
	hund.cur_speed = 0.0
	if f >= 1.0:
		place(hund, b, true)
		_ziel_y = b.y
		modus = "oben"
		freuen(2.0)
		bellen(b, 1)


# ---- steering ----------------------------------------------------------------------------------------------------------------
func steuern(mv_welt: Vector2, dt: float) -> void:
	"""the player steers her (world direction, 0..1); kit.maggie_boden says where she may stand and how high"""
	modus = "gesteuert"
	var hp := ppos(hund)
	var d3 := Vector3(mv_welt.x, 0, mv_welt.y)
	var tal_d: Vector3 = bt.tal.transform.basis.inverse() * d3
	var spd := 2.2 * clampf(mv_welt.length(), 0.0, 1.0)
	if spd < 0.05:
		stop(hund, dt)
		tempo = 0.0
		return
	var np := hp + Vector3(tal_d.x, 0, tal_d.z).normalized() * spd * dt
	var hy = kit.maggie_boden(Vector2(hp.x, hp.z), Vector2(np.x, np.z))
	if typeof(hy) == TYPE_BOOL:
		stop(hund, dt)
		tempo = 0.0
		return
	turn_to(hund, np - hp, dt, 8.0)
	hund.cur_speed = spd
	tempo = spd
	idle(hund, "")
	if hy == null:
		place(hund, np)
	else:
		place(hund, Vector3(np.x, float(hy), np.z), true)


# ---- sniffing, warning -----------------------------------------------------------------------------------------------------
func riechen(ziel_welt: Vector3, lang := 30.0) -> void:
	var hp := ppos(hund)
	var z := VL(ziel_welt)
	_aktion([{"t": "idle", "k": "sniff", "s": 1.4}, {"t": "call", "fn": func(): _pfoten_legen(hp, Vector3(z.x, 0, z.z), lang)},
		{"t": "walk", "p": hp.lerp(Vector3(z.x, 0, z.z), 0.15), "spd": 1.6}, {"t": "idle", "k": "sniff", "s": 1.0}, {"t": "bark", "n": 1}])


func warnen(richtung_welt: Vector3) -> void:
	var q := VL(richtung_welt)
	_aktion([{"t": "face", "p": Vector3(q.x, 0, q.z)}, {"t": "call", "fn": func(): knurren(ppos(hund))}, {"t": "wait", "s": 0.9},
		{"t": "bark", "n": 3}, {"t": "wait", "s": 0.6}])


func zur_figur_laufen(w: Vector3) -> void:
	"""a film: she runs to a world point"""
	var q := VL(w)
	modus = "folgen"
	_aktion([{"t": "walk", "p": Vector3(q.x, 0, q.z), "spd": 3.0}, {"t": "call", "fn": func(): kit.regie.zug_fertig("maggie")}])


func kit_info() -> Dictionary:
	var hp := ppos(hund) if hund != null and is_instance_valid(hund) else Vector3.ZERO
	return {"modus": modus, "zustand": zustand_hund, "x": snappedf(hp.x, 0.01), "z": snappedf(hp.z, 0.01), "tempo": snappedf(tempo, 0.01),
		"spur": _pfoten.size(), "lite": lite}
