extends RefCounted
class_name RoboterKiGang
## Roboter-Labor: Gang-KI Stufe 1 «Sehen» + Stufe 2 «Setzen» (Besitzer 28.11.2026 14:36; Schnittstelle mit Helfer B:
## roboter_ki_lernen.gd = Stufe 3 «Lernen»). Der Benutzer gibt nur Richtung + Stil vor (Gangart «KI»), den Rest macht die KI.
##
## Sehen: ein Höhenraster vor dem Kopf (Zelle 2 cm, 1.5 m nach vorne × 1 m quer = 75 × 50 Zellen), gemessen mit
##   senkrechten Abtaststrahlen auf das Gelände (Ebene 1) - wie ein Tiefenbild der Roboter-Kamera, ohne Verdeckung (die
##   Kamera sieht in Wirklichkeit nicht hinter eine Stufe: hier schon). Wo ein Strahl hoch trifft, prüfen zwei weitere
##   Strahlen, ob darunter Luft ist (Balken). Aus dem Längsprofil in der Spur der Füsse (±20 cm) wird je Hindernis bestimmt:
##     art      stufe | treppe | graben | luecke | geroell | rampe | rohr | balken
##     abstand  m vom Kopf bis zum Anfang          hoehe   m über dem Boden (Balken: lichte Höhe darunter; Rampe: Hub)
##     breite   m in Gehrichtung (Graben / Lücke: Spannweite, Rohr: Durchmesser, Treppe: Auftritt, Rampe: gesehene Länge)
##     tiefe    m nach unten (Graben; Lücke: 0.5 = kein Boden gesehen)       quer  m quer zur Gehrichtung (höchstens 1 m)
##     neigung  ° (Rampe)     stufen  Zahl (Treppe)     pos  Vector3 (Welt, Anfang auf der Mittellinie)   richtung Vector3
## Setzen: jedes Bein prüft vor dem Aufsetzen seinen Trittpunkt (5 Strahlen: Boden da, nicht auf einer Kante) und
##   verschiebt ihn nach vorne / hinten; findet es keinen sicheren Punkt (über einer Lücke), bleibt es in der Luft.
##   Schritthöhe, Körperhöhe, Neigung (vorderes Gelenk) und Tempo kommen aus der Strategie; Rückkopplung: kippt der Körper
##   (Seitenneigung, Kipp-Reserve klein) oder rutschen Standfüsse, wird er tiefer, breiter und langsamer (Korrektur).
## Energie: Strom der Servos × 7.4 V (2S-Akku, Annahme).

const GEL = preload("res://scripts/roboter_gelaende.gd")
const ZELLE := 0.02
const LAENGE := 1.5
const BREITE := 1.0
const NX := 75                       # Zeilen nach vorne
const NZ := 50                       # Spalten quer (Spalte 0 = links)
const LEER := -9.0                   # kein Boden getroffen
const SPUR := 0.20                   # m links / rechts der Mitte: dort stehen die Füsse
const SPANNUNG := 7.4                # V (Annahme)
const STRATEGIEN := ["normal", "hoch_steigen", "aufrichten_vorne", "bruecke", "umgehen", "einrollen_rollen", "kriechen_drunter"]
const STRATEGIE_NAMEN := {"normal": "Normal gehen", "hoch_steigen": "Hoch steigen", "aufrichten_vorne": "Vorne aufrichten",
		"bruecke": "Brücke", "umgehen": "Umgehen", "einrollen_rollen": "Einrollen und rollen", "kriechen_drunter": "Drunter durch kriechen"}
const STILE := [["schnell", "Schnell"], ["sparsam", "Sparsam"], ["sicher", "Sicher"]]
# the numbers B may vary: [low, high, default]. Units: E = units of the template (× massstab = m), ° , m/s, m
const PARAM := {"schritt_hoehe": [0.2, 1.2, 0.35], "koerper_hoehe": [0.4, 1.6, 0.9], "neigung": [0.0, 40.0, 0.0],
		"tempo": [0.02, 0.15, 0.06], "segment_hub": [0.0, 15.0, 0.0], "anlauf": [0.0, 0.5, 0.15], "seitwaerts": [0.3, 1.5, 1.1],
		"spreiz": [0.8, 1.8, 1.25]}
const ZEIT_MAX := 120.0              # s for one strategy
const STILL_MAX := 12.0              # s without 3 cm progress = stuck

var m                                # roboter_modell.gd
var bew                              # roboter_bewegung.gd
var anz                              # roboter_anzeige.gd (Kipp-Reserve)
var labor                            # roboter_labor.gd (neu aufstellen, Seite)
var lernen = null                    # roboter_ki_lernen.gd (Stufe 3, Helfer B) - optional
var stil := "sicher"
var befehl := Vector3.ZERO           # x vor, y seitwärts (+ links), z drehen (+ links), −1 … 1
var gangart := "welle"               # what the KI walks with (gang_now)
var bild := {}                       # last sehen(): {hoehe, decke, hindernisse, t}
var _seh_t := 0.0
var _zeit := 0.0
var lauf := {}                       # running strategy: {name, param, t, energie, kipp_min, ...}; empty = none
var ergebnis := {}                   # last finished strategy status
var auto_versuche := 0               # strategies the KI picked itself (without Stufe 3)
var korrekturen := 0
var korrektur_grund := ""
var _korr_t := 0.0
var _bein := {}                      # leg key -> {alt, neu, frei, frei_neu, u}
var tritte := 0                      # touchdowns seen
var tritte_leer := 0                 # touchdowns without ground under the foot (should stay 0)
var tritte_versetzt := 0
var beine_frei := 0                  # legs kept in the air right now
var _slip_t := 0.0
var _foot_prev := {}
var _basis := {}                     # bew values before the KI changed them


# ==== Schnittstelle A → B ==================================================================================================
func aktiv() -> bool:
	return bew != null and bew.mode == "gang" and bew.gang == "ki" or (not lauf.is_empty() and str(lauf.get("name", "")) == "einrollen_rollen")


func setze_stil(s: String) -> void:
	stil = s if s in ["schnell", "sparsam", "sicher"] else "sicher"
	if lernen != null and lernen.has_method("setze_stil"):
		lernen.setze_stil(stil)


func setze_befehl(v: Vector3) -> void:
	befehl = Vector3(clampf(v.x, -1, 1), clampf(v.y, -1, 1), clampf(v.z, -1, 1))


func strategie_ausfuehren(name: String, param: Dictionary) -> void:
	if not name in STRATEGIEN:
		name = "normal"
	abbrechen()
	_merke_basis()
	if bew.mode != "gang" or bew.gang != "ki":
		if m.latch["state"] == "locked" and name != "einrollen_rollen":
			m.unlock()
		bew.start_gang("ki")
	var p := {}
	for k in PARAM:
		p[k] = float(param.get(k, _vorschlag(name, k, param.get("hindernis", _naechstes()))))
	var h: Dictionary = param.get("hindernis", _naechstes())
	var fwd := _vorne()
	var head := _kopf()
	var start_s := head.dot(fwd)
	var end_s := start_s + 0.8
	if not h.is_empty():
		var hp: Vector3 = h["pos"]
		var reach := float(h.get("breite", 0.0))
		if str(h.get("art", "")) in ["stufe", "treppe"]:
			reach = maxf(reach * float(h.get("stufen", 1)), 0.0)
		end_s = hp.dot(fwd) + maxf(reach, 0.05) + 0.12
	lauf = {"name": name, "param": p, "hindernis": h, "t": 0.0, "energie": 0.0, "kipp_min": 1.0, "gestuerzt": false,
			"fwd": fwd, "seite": fwd.cross(Vector3.UP), "start": head, "end_s": end_s, "best": -1e9, "best_t": 0.0,
			"phase": "seitwaerts" if name == "umgehen" else ("einrollen" if name == "einrollen_rollen" else "gehen"),
			"korrekturen": 0, "fertig": false, "erfolg": false, "grund": ""}
	_param_setzen(p)
	if name == "einrollen_rollen":
		bew.apply(bew.pose("ring"))
		bew.mode = ""


func strategie_status() -> Dictionary:
	var l := lauf if not lauf.is_empty() else ergebnis
	if l.is_empty():
		return {"laeuft": false, "fertig": false, "erfolg": false, "zeit": 0.0, "energie": 0.0, "kipp_min": 1.0, "gestuerzt": false}
	return {"laeuft": not lauf.is_empty(), "fertig": bool(l["fertig"]), "erfolg": bool(l["erfolg"]), "zeit": float(l["t"]),
			"energie": float(l["energie"]), "kipp_min": float(l["kipp_min"]), "gestuerzt": bool(l["gestuerzt"]),
			"strategie": str(l["name"]), "grund": str(l["grund"]), "korrekturen": int(l["korrekturen"])}


func abbrechen() -> void:
	if not lauf.is_empty() and not bool(lauf["fertig"]):
		_ende(false, "abgebrochen")
	lauf = {}


func neu_aufstellen(hindernis: Dictionary) -> void:
	"""the robot stands ~0.5 m before the obstacle, looking at it (for the next try)"""
	abbrechen()
	var p: Vector3 = hindernis.get("pos", _kopf())
	var dir: Vector3 = hindernis.get("richtung", Vector3.ZERO)
	if dir.length() < 0.1:
		dir = p - _kopf()
	dir.y = 0.0
	dir = dir.normalized() if dir.length() > 0.01 else Vector3.RIGHT
	var at: Vector3 = p - dir * (0.5 + m.pitch_len() * 0.5)
	at.y = _boden(at, 0.6)
	if at.y == LEER:
		at.y = 0.0
	if labor != null:
		labor.stop_all()
	m.root_xf = Transform3D(Basis(Vector3.UP, atan2(-dir.z, dir.x)), at)
	if labor != null:
		labor.apply_pose("gerade", true)
	else:
		bew.apply(bew.pose("gerade"))
		m.place(true)
	_bein = {}
	bew.start_gang("ki")


func sehen() -> Dictionary:
	"""the height raster ahead of the head and the obstacles in it (see top of the file)"""
	var hoehe := PackedFloat32Array()
	var decke := PackedFloat32Array()
	hoehe.resize(NX * NZ)
	decke.resize(NX * NZ)
	var fwd := _vorne()
	var lat := Vector3.UP.cross(fwd)              # + = links
	var head := _kopf()
	var ref := _boden_ref()
	var space := _space()
	for r in range(NX):
		for c in range(NZ):
			var p := head + fwd * ((r + 0.5) * ZELLE) + lat * (BREITE * 0.5 - (c + 0.5) * ZELLE)
			var y := LEER
			var dk := 0.0
			if space != null:
				var hit := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(p.x, ref + 0.6, p.z), Vector3(p.x, ref - 0.6, p.z), m.LAYER_GELAENDE))
				if not hit.is_empty():
					y = (hit["position"] as Vector3).y - ref
					if y > 0.06:                  # high: air below? (a beam) - from inside a body the ray sees nothing
						var top: float = (hit["position"] as Vector3).y
						var h2 := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(p.x, top - 0.004, p.z), Vector3(p.x, ref - 0.6, p.z), m.LAYER_GELAENDE))
						if not h2.is_empty():
							var g2: float = (h2["position"] as Vector3).y
							var h3 := space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(p.x, g2 + 0.004, p.z), Vector3(p.x, top, p.z), m.LAYER_GELAENDE))
							if not h3.is_empty() and (h3["position"] as Vector3).y - g2 > 0.05:
								dk = (h3["position"] as Vector3).y - g2
								y = g2 - ref
			hoehe[r * NZ + c] = y
			decke[r * NZ + c] = dk
	bild = {"hoehe": hoehe, "decke": decke, "nx": NX, "nz": NZ, "zelle": ZELLE, "t": _zeit, "kopf": head, "vorne": fwd, "ref": ref}
	bild["hindernisse"] = _analyse(hoehe, decke, head, fwd, ref)
	return bild


# ==== Hindernisse aus dem Raster ============================================================================================
func _profil(hoehe: PackedFloat32Array, decke: PackedFloat32Array) -> Array:
	"""per row: {h (median in the foot lane), leer (most cells without ground), rau (max − min), dk (beam clearance)}"""
	var out := []
	var c0 := int(round((BREITE * 0.5 - SPUR) / ZELLE))
	var c1 := int(round((BREITE * 0.5 + SPUR) / ZELLE))
	for r in range(NX):
		var vals := []
		var nleer := 0
		var dks := []
		for c in range(c0, c1):
			var v: float = hoehe[r * NZ + c]
			if v <= LEER + 1.0:
				nleer += 1
			else:
				vals.append(v)
			if decke[r * NZ + c] > 0.0:
				dks.append(decke[r * NZ + c])
		vals.sort()
		var n := c1 - c0
		var row := {"leer": nleer * 2 > n, "h": 0.0, "rau": 0.0, "dk": 0.0}
		if not vals.is_empty():
			row["h"] = vals[vals.size() / 2]
			row["rau"] = float(vals[vals.size() - 1]) - float(vals[0])
		if dks.size() * 2 > n:
			dks.sort()
			row["dk"] = dks[dks.size() / 2]
		out.append(row)
	return out


func _analyse(hoehe: PackedFloat32Array, decke: PackedFloat32Array, head: Vector3, fwd: Vector3, ref: float) -> Array:
	var pr := _profil(hoehe, decke)
	var out := []
	var r := 0
	while r < NX and out.size() < 3:
		var row: Dictionary = pr[r]
		var ev: bool = row["leer"] or absf(float(row["h"])) > 0.015 or float(row["dk"]) > 0.0 or float(row["rau"]) > 0.02
		if not ev:
			r += 1
			continue
		var h := _hindernis(pr, r)
		h["abstand"] = r * ZELLE
		h["pos"] = head + fwd * (r * ZELLE) + Vector3(0, ref, 0)
		h["richtung"] = fwd
		h["quer"] = _quer(hoehe, decke, r, int(h.get("_bis", r + 1)))
		var bis: int = h["_bis"]
		h.erase("_bis")
		out.append(h)
		if str(h["art"]) in ["stufe", "treppe", "rampe"]:
			break                                  # behind it everything is measured from the new height: one at a time
		r = maxi(bis, r + 1)
	return out


func _hindernis(pr: Array, r: int) -> Dictionary:
	var row: Dictionary = pr[r]
	# beam above the lane
	if float(row["dk"]) > 0.0:
		var e := r
		var dmin := 9.0
		while e < NX and float(pr[e]["dk"]) > 0.0:
			dmin = minf(dmin, float(pr[e]["dk"]))
			e += 1
		return {"art": "balken", "hoehe": dmin, "breite": (e - r) * ZELLE, "tiefe": 0.0, "neigung": 0.0, "_bis": e}
	# going down gently (a ramp down): no sharp drop from row to row
	var prev_h := 0.0 if r == 0 else float(pr[r - 1]["h"])
	if not row["leer"] and float(row["h"]) < -0.015 and prev_h - float(row["h"]) < 0.012:
		var e := r
		var gentle := true
		while e + 1 < NX and not pr[e + 1]["leer"] and float(pr[e + 1]["h"]) < float(pr[e]["h"]) + 0.002:
			if float(pr[e]["h"]) - float(pr[e + 1]["h"]) > 0.012:
				gentle = false
				break
			e += 1
		if gentle:
			var drop: float = float(pr[e]["h"])
			var ng := rad_to_deg(atan2(drop - float(pr[r]["h"]), maxf((e - r) * ZELLE, 0.02)))
			return {"art": "rampe", "hoehe": drop, "breite": (e - r) * ZELLE, "tiefe": -drop, "neigung": ng, "_bis": e + 1}
	# hole: ditch (bottom seen) or gap (no ground)
	if row["leer"] or float(row["h"]) < -0.015:
		var e := r
		var nleer := 0
		var hmin := 0.0
		while e < NX and (pr[e]["leer"] or float(pr[e]["h"]) < -0.015):
			if pr[e]["leer"]:
				nleer += 1
			else:
				hmin = minf(hmin, float(pr[e]["h"]))
			e += 1
		var luecke := nleer * 2 >= (e - r)
		return {"art": "luecke" if luecke else "graben", "hoehe": 0.0, "breite": (e - r) * ZELLE, "tiefe": 0.5 if luecke else -hmin,
				"neigung": 0.0, "ende_gesehen": e < NX, "_bis": e}
	# rough ground: the height changes across the lane (stones), a step or a pipe is flat across
	var w := mini(NX, r + 25)
	var rau := 0.0
	var hs := []
	for k in range(r, w):
		rau += float(pr[k]["rau"])
		hs.append(float(pr[k]["h"]))
	rau /= maxf(1.0, w - r)
	if rau > 0.012:
		var all := []
		for k in range(r, mini(NX, r + 40)):
			all.append(float(pr[k]["h"]) + float(pr[k]["rau"]) * 0.5)
		all.sort()
		return {"art": "geroell", "hoehe": all[int(all.size() * 0.9) - 1] if all.size() > 1 else 0.0, "breite": (mini(NX, r + 40) - r) * ZELLE,
				"tiefe": 0.0, "neigung": 0.0, "rauheit": rau, "_bis": mini(NX, r + 40)}
	# raised: a pipe comes down again within 25 cm
	var e := r
	var hmax := 0.0
	while e < NX and float(pr[e]["h"]) > 0.012 and not pr[e]["leer"]:
		hmax = maxf(hmax, float(pr[e]["h"]))
		e += 1
	if e < NX and (e - r) * ZELLE <= 0.25:
		return {"art": "rohr", "hoehe": hmax, "breite": (e - r) * ZELLE, "tiefe": 0.0, "neigung": 0.0, "_bis": e}
	# step / stairs / ramp: look at the jumps from row to row
	var jumps := []                                   # [row, height after]
	var prev := 0.0 if r == 0 else float(pr[r - 1]["h"])
	var steep := 0
	var k := r
	var end_rise := r
	while k < NX and not pr[k]["leer"]:
		var hk: float = pr[k]["h"]
		var dh := hk - prev
		if dh > 0.012:
			if not jumps.is_empty() and k - int(jumps[-1][0]) <= 2:
				jumps[-1][1] = hk                      # one edge over two rows
			else:
				jumps.append([k, hk])
			end_rise = k
		elif dh > 0.002:
			steep += 1
			end_rise = k
		prev = hk
		k += 1
	var top: float = pr[mini(end_rise + 2, NX - 1)]["h"] if not jumps.is_empty() else float(pr[end_rise]["h"])
	if jumps.size() >= 2:
		var tread := float(int(jumps[-1][0]) - int(jumps[0][0])) * ZELLE / float(jumps.size() - 1)
		return {"art": "treppe", "hoehe": float(jumps[-1][1]), "breite": tread, "tiefe": 0.0, "neigung": rad_to_deg(atan2(float(jumps[-1][1]), tread * jumps.size())),
				"stufen": jumps.size(), "stufe_hoehe": float(jumps[-1][1]) / jumps.size(), "_bis": k}
	if jumps.size() == 1 and steep < 5:
		return {"art": "stufe", "hoehe": float(jumps[0][1]), "breite": 0.0, "tiefe": 0.0, "neigung": 90.0, "_bis": k}
	# ramp: fit the rise
	var run := float(end_rise - r) * ZELLE
	var rise: float = pr[end_rise]["h"]
	var ng := rad_to_deg(atan2(rise - float(pr[r]["h"]), maxf(run, 0.02)))
	return {"art": "rampe", "hoehe": rise, "breite": run + float(pr[r]["h"]) / maxf(tan(deg_to_rad(ng)), 0.05), "tiefe": 0.0, "neigung": ng, "_bis": k}


func _quer(hoehe: PackedFloat32Array, decke: PackedFloat32Array, r0: int, r1: int) -> float:
	"""how wide across the obstacle is (m, the columns that differ from flat ground in its rows)"""
	var n := 0
	for c in range(NZ):
		var hit := false
		for r in range(r0, mini(r1, NX)):
			var v: float = hoehe[r * NZ + c]
			if v <= LEER + 1.0 or absf(v) > 0.012 or decke[r * NZ + c] > 0.0:
				hit = true
				break
		if hit:
			n += 1
	return n * ZELLE


# ==== Setzen: Regeln (ohne Stufe 3), Parameter, Ablauf =====================================================================
func regel(h: Dictionary) -> Array:
	"""[strategy, param] the KI picks itself when nothing has been learnt"""
	var art := str(h.get("art", ""))
	var hh := float(h.get("hoehe", 0.0))
	match art:
		"stufe", "rohr":
			return ["hoch_steigen", {}] if hh <= 0.07 else ["aufrichten_vorne", {}]
		"treppe":
			return ["hoch_steigen", {}]
		"graben", "luecke":
			var weit: bool = float(h.get("breite", 0.0)) > 0.4 and bool(h.get("ende_gesehen", true))
			return ["umgehen", {}] if weit else ["bruecke", {}]
		"balken":
			return ["kriechen_drunter", {}] if hh >= 0.10 else ["umgehen", {}]
		"geroell":
			return ["hoch_steigen", {}]
		"rampe":
			return ["normal", {}] if absf(float(h.get("neigung", 0.0))) < 25.0 else ["hoch_steigen", {}]
	return ["normal", {}]


func _vorschlag(name: String, k: String, h) -> float:
	"""the default of parameter k for strategy «name» (and the obstacle h)"""
	var sc: float = m.bp["massstab"]
	var hh := float((h as Dictionary).get("hoehe", 0.0)) if h is Dictionary else 0.0
	var d: float = PARAM[k][2]
	var tempo: float = {"schnell": 0.12, "sparsam": 0.08, "sicher": 0.07}.get(stil, 0.07)
	match k:
		"tempo":
			d = tempo if name == "normal" else tempo * 0.8
		"schritt_hoehe":
			if name in ["hoch_steigen", "aufrichten_vorne"]:
				d = clampf((hh + 0.025) / sc, 0.5, 1.2)
			elif name == "kriechen_drunter":
				d = 0.25
			elif stil == "sparsam":
				d = 0.25
		"koerper_hoehe":
			if name in ["hoch_steigen", "aufrichten_vorne"]:
				d = clampf(0.9 + hh / sc * 0.5, 0.9, 1.4)
			elif name == "kriechen_drunter":
				d = 0.5
			elif h is Dictionary and str((h as Dictionary).get("art", "")) in ["rampe", "geroell"]:
				d = 1.0
		"neigung":
			d = 25.0 if name == "aufrichten_vorne" else 0.0
		"spreiz":
			d = 1.5 if name == "kriechen_drunter" else 1.25
		"seitwaerts":
			var q := float((h as Dictionary).get("quer", 1.0)) if h is Dictionary else 1.0
			d = clampf(q * 0.5 + 0.55, 0.3, 1.5)
	return clampf(d, PARAM[k][0], PARAM[k][1])


func _merke_basis() -> void:
	if _basis.is_empty():
		_basis = {"schritt_hoehe": bew.schritt_hoehe, "hoehe": bew.hoehe, "tempo": bew.tempo, "spreiz": bew.spreiz}


func _param_setzen(p: Dictionary) -> void:
	bew.schritt_hoehe = float(p["schritt_hoehe"])
	bew.hoehe = float(p["koerper_hoehe"])
	bew.tempo = float(p["tempo"])
	bew.spreiz = float(p["spreiz"])
	bew.anpassen = true


func _stil_param() -> void:
	"""walking without a strategy: the values of the style"""
	_merke_basis()
	var p := {}
	for k in PARAM:
		p[k] = _vorschlag("normal", k, {})
	_param_setzen(p)


func step(dt: float) -> void:
	"""every physics step, before bew.step(): see, pick, run, correct"""
	_zeit += dt
	if m == null or not m.built_ok:
		return
	var ki_gang: bool = bew.mode == "gang" and bew.gang == "ki"
	if not ki_gang and lauf.is_empty():
		return
	_seh_t -= dt
	if _seh_t <= 0.0:
		_seh_t = 0.25
		sehen()
	if lauf.is_empty():
		gangart = "dreifuss" if stil == "schnell" and _naechstes().is_empty() else "welle"
		var lernt: bool = lernen != null and lernen.get("an") == true
		var h := _naechstes()
		if not lernt and befehl.x > 0.3 and not h.is_empty() and float(h["abstand"]) < 0.45:
			var w := regel(h)
			auto_versuche += 1
			var pp: Dictionary = (w[1] as Dictionary).duplicate()
			pp["hindernis"] = h
			strategie_ausfuehren(w[0], pp)
		else:
			if int(_zeit * 4.0) % 4 == 0 and _korr_t <= 0.0:
				_stil_param()
			bew.cmd = Vector3(befehl.y, befehl.x, befehl.z)
	if not lauf.is_empty():
		_lauf_step(dt)
	_rueckkopplung(dt)


func _lauf_step(dt: float) -> void:
	var l := lauf
	l["t"] = float(l["t"]) + dt
	l["energie"] = float(l["energie"]) + float(m.total_current) * SPANNUNG * dt / 3600.0
	l["kipp_min"] = minf(float(l["kipp_min"]), kipp_reserve())
	var fwd: Vector3 = l["fwd"]
	var p: Dictionary = l["param"]
	gangart = "welle"
	var hinten: Vector3 = m.segment_xf(m.n() - 1).origin
	if str(l["name"]) == "einrollen_rollen" and m.latch["state"] == "locked":
		hinten = bew.ring_state()["c"]
	var s := hinten.dot(fwd)
	var prog := s + absf(hinten.dot(l["seite"]) - (l["start"] as Vector3).dot(l["seite"]))
	if prog > float(l["best"]) + 0.03:
		l["best"] = prog
		l["best_t"] = l["t"]
	if _gekippt():
		l["gestuerzt"] = true
		_ende(false, "gestürzt")
		return
	if s >= float(l["end_s"]):
		_ende(true, "geschafft")
		return
	if float(l["t"]) - float(l["best_t"]) > STILL_MAX:
		_ende(false, "steckt fest")
		return
	if float(l["t"]) > ZEIT_MAX:
		_ende(false, "zu langsam")
		return
	var vor := 1.0
	var seit := 0.0
	match str(l["name"]):
		"umgehen":
			var off: float = (_kopf() - (l["start"] as Vector3)).dot(Vector3.UP.cross(fwd))
			if str(l["phase"]) == "seitwaerts":
				vor = 0.0
				seit = 1.0
				if off >= float(p["seitwaerts"]):
					l["phase"] = "gehen"
		"einrollen_rollen":
			if str(l["phase"]) == "einrollen":
				if m.latch["state"] == "locked":
					l["phase"] = "rollen"
					bew.start_ring()
				elif float(l["t"]) > 8.0:
					_ende(false, "Ring schliesst nicht")
					return
				return
			bew.keys = Vector2(0.0, 1.0)
			return
	bew.cmd = Vector3(seit, vor, 0.0)


func vorne_neigen() -> void:
	"""after bew.step(): «aufrichten_vorne» lifts the front at the edge; «segment_hub» = a small wave in the back"""
	if lauf.is_empty() or m == null:
		return
	var p: Dictionary = lauf["param"]
	var ng := float(p.get("neigung", 0.0))
	var hub := float(p.get("segment_hub", 0.0))
	if ng <= 0.0 and hub <= 0.0:
		return
	var h: Dictionary = lauf["hindernis"]
	var fwd: Vector3 = lauf["fwd"]
	var edge: float = (h["pos"] as Vector3).dot(fwd) if not h.is_empty() else 1e9
	var dk := edge - _kopf().dot(fwd)
	if ng > 0.0 and dk < 0.2 and dk > -m.pitch_len() * 1.5:
		for j in range(mini(2, m.n() - 1)):
			var id := "sp%d" % j
			var si: int = m.servo_index(id)
			if si >= 0:
				m.set_target(id, float(m.servos[si]["target"]) + ng * (1.0 if j == 0 else 0.5))
	if hub > 0.0:
		for j in range(m.n() - 1):
			var id := "sp%d" % j
			var si: int = m.servo_index(id)
			if si >= 0:
				m.set_target(id, float(m.servos[si]["target"]) + hub * sin(TAU * (bew.phase - float(j) / maxf(1.0, m.n() - 1))))


func _ende(ok: bool, grund: String) -> void:
	lauf["fertig"] = true
	lauf["erfolg"] = ok
	lauf["grund"] = grund
	ergebnis = lauf.duplicate()
	lauf = {}
	if not _basis.is_empty():
		for k in _basis:
			bew.set(k, _basis[k])
		_basis = {}
	if str(ergebnis["name"]) == "einrollen_rollen":
		bew.keys = Vector2.ZERO
	if lernen != null and lernen.has_method("melde_status_von_a"):
		lernen.melde_status_von_a(ergebnis)


func _rueckkopplung(dt: float) -> void:
	"""tilting or slipping: lower, wider, slower for 3 s"""
	if _korr_t > 0.0:
		_korr_t -= dt
		if _korr_t <= 0.0 and not lauf.is_empty():
			_param_setzen(lauf["param"])          # back to the values of the strategy
		return
	if bew.mode != "gang":
		return
	var roll := 0.0
	for i in range(m.n()):
		roll = maxf(roll, rad_to_deg(acos(clampf(_seitenlage(i), -1.0, 1.0))))
	var slip := _rutschen(dt)
	var grund := ""
	if roll > 18.0:
		grund = "Seitenlage zu gross"
	elif kipp_reserve() < 0.12 and anz != null:
		grund = "Kipp-Reserve klein"
	elif slip:
		grund = "Füsse rutschen"
	if grund == "":
		return
	korrekturen += 1
	korrektur_grund = grund
	if not lauf.is_empty():
		lauf["korrekturen"] = int(lauf["korrekturen"]) + 1
	var base: Dictionary = lauf["param"] if not lauf.is_empty() else {"koerper_hoehe": bew.hoehe, "spreiz": bew.spreiz, "tempo": bew.tempo}
	bew.hoehe = maxf(0.5, float(base["koerper_hoehe"]) - 0.15)
	bew.spreiz = minf(1.7, float(base["spreiz"]) + 0.15)
	bew.tempo = maxf(0.02, float(base["tempo"]) * 0.7)
	_korr_t = 3.0


func _seitenlage(i: int) -> float:
	"""cos of the roll of segment i (1 = upright)"""
	var b: Basis = m.segment_xf(i).basis.orthonormalized()
	var z := b.z
	return sqrt(maxf(0.0, 1.0 - z.y * z.y))


func _rutschen(dt: float) -> bool:
	"""stance feet that touch the ground and move faster than 6 cm/s for 0.4 s"""
	var n := 0
	var tot := 0
	for i in range(m.n()):
		for s in [-1, 1]:
			var k := "%d%d" % [i, s]
			var st: Dictionary = _bein.get(k, {})
			var fw: Vector3 = m.foot_world(i, s)
			if not st.is_empty() and float(st["u"]) < bew.BETA.get(gangart, 0.75) and m.foot_contact(i, s) and _foot_prev.has(k):
				tot += 1
				var dv: Vector3 = (fw - (_foot_prev[k] as Vector3)) / maxf(dt, 1e-4)
				dv.y = 0.0
				if dv.length() > 0.06:
					n += 1
			_foot_prev[k] = fw
	_slip_t = _slip_t + dt if tot > 0 and n * 3 > tot else 0.0
	return _slip_t > 0.4


# ==== Trittpunkte (Haken in roboter_bewegung._gang_step) ===================================================================
func tritt(i: int, s: int, u: float, beta: float, a2: Vector2, xf: Transform3D, lv: Basis, lift: float) -> Vector3:
	"""shift of the foot (x, z in the level frame of the segment) + extra height y: safe landing, never into nothing"""
	if bew.gang != "ki":
		return Vector3.ZERO
	var k := "%d%d" % [i, s]
	if not _bein.has(k):
		_bein[k] = {"alt": 0.0, "neu": 0.0, "frei": false, "frei_neu": false, "u": u}
	var st: Dictionary = _bein[k]
	var swing := u >= beta
	var was_swing := float(st["u"]) >= beta
	if swing and not was_swing:                        # lift-off: where will it land?
		st["alt"] = st["neu"]
		var f0: Vector3 = bew.stand_foot(s)
		var ahead := Vector3(a2.x, 0.0, a2.y) * (1.0 + 2.0 * (1.0 - beta) / beta)
		var land: Vector3 = xf.origin + lv * Vector3(f0.x, 0.0, f0.z) + lv * ahead
		var fx: Vector3 = lv.x
		var amax: float = maxf(bew.schritt_laenge * float(m.bp["massstab"]) * 0.5, 0.02)
		var best := 999.0
		var dx := 0.0
		while dx <= 2.5 * amax + 1e-4:
			for sg in ([1.0] if dx == 0.0 else [-1.0, 1.0]):
				var cand: float = dx * sg
				if cand > amax * 1.2 or best < 900.0:
					continue
				if _sicher(land + fx * cand):
					best = cand
			if best < 900.0:
				break
			dx += 0.01
		st["frei_neu"] = best > 900.0
		st["neu"] = 0.0 if best > 900.0 else best
		if best > 900.0 or absf(best) > 0.005:
			tritte_versetzt += 1
	elif not swing and was_swing:                      # touch-down
		st["frei"] = st["frei_neu"]
		if not bool(st["frei"]):
			st["pruef"] = 3                            # look a few steps later (the foot reaches its point)
	if not swing and int(st.get("pruef", 0)) > 0:
		st["pruef"] = int(st["pruef"]) - 1
		if int(st["pruef"]) == 0:
			tritte += 1
			var fw: Vector3 = m.foot_world(i, s)
			if _boden(fw + Vector3(0, 0.03, 0), 0.09) == LEER:
				tritte_leer += 1
	st["u"] = u
	var sh := float(st["neu"])
	var y := 0.0
	if swing:
		var q := (u - beta) / (1.0 - beta)
		sh = lerpf(float(st["alt"]), float(st["neu"]), q * q * (3.0 - 2.0 * q))
		if bool(st["frei_neu"]) and q > 0.5:
			y = lift * (1.0 - sin(PI * q))            # stays up instead of coming down
		elif bool(st["frei"]) and q < 0.5:
			y = lift * (1.0 - sin(PI * q))
	elif bool(st["frei"]):
		y = lift
	return Vector3(sh, y, 0.0)


func zaehle_frei() -> void:
	var n := 0
	for k in _bein:
		if bool(_bein[k]["frei"]):
			n += 1
	beine_frei = n


func _sicher(p: Vector3) -> bool:
	"""ground under p and around it (±2.5 cm), not on an edge: a slope is fine (ramp up to 35°), a kink is not"""
	var fx := _vorne()
	var lat := Vector3.UP.cross(fx)
	var y0 := _boden(p, 0.35)
	if y0 == LEER:
		return false
	for d in [fx * 0.025, lat * 0.025]:
		var ya := _boden(p + d, 0.35)
		var yb := _boden(p - d, 0.35)
		if ya == LEER or yb == LEER:
			return false
		if absf(ya + yb - 2.0 * y0) > 0.008 or absf(ya - yb) > 0.05 * 0.7:
			return false
	return true


# ==== Hilfen ================================================================================================================
func kipp_reserve() -> float:
	"""0 … 1: margin of the centre of mass inside the support (anz.margin) relative to the half foot spread"""
	if anz == null:
		return 1.0
	var ref: float = m.u("halbe_breite") + bew.spreiz * float(m.bp["massstab"])
	return clampf(float(anz.margin) / maxf(ref, 0.02), 0.0, 1.0)


func _gekippt() -> bool:
	for i in range(m.n()):
		if m.segment_xf(i).basis.y.y < 0.2:
			return true
	return m.com().y < -0.3


func _naechstes() -> Dictionary:
	var hs: Array = bild.get("hindernisse", [])
	return hs[0] if not hs.is_empty() else {}


func _vorne() -> Vector3:
	var fx: Vector3 = m.segment_xf(0).basis.x
	fx.y = 0.0
	return fx.normalized() if fx.length() > 0.1 else Vector3.RIGHT


func _kopf() -> Vector3:
	var o: Vector3 = m.segment_xf(0).origin
	return o + _vorne() * (m.pitch_len() * 0.5)


func _space() -> PhysicsDirectSpaceState3D:
	var w3: World3D = m.get_world_3d() if m.is_inside_tree() else null
	return w3.direct_space_state if w3 != null else null


func _boden(p: Vector3, span: float) -> float:
	"""ground height under p (ray from p.y + span down 2 × span), LEER if nothing"""
	var sp := _space()
	if sp == null:
		return LEER
	var hit := sp.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(p.x, p.y + span, p.z), Vector3(p.x, p.y - span, p.z), m.LAYER_GELAENDE))
	return float((hit["position"] as Vector3).y) if not hit.is_empty() else LEER


func _boden_ref() -> float:
	"""the ground the robot stands on now (under the first two segments)"""
	var best := LEER
	for i in range(mini(1, m.n())):
		var o: Vector3 = m.segment_xf(i).origin
		var y := _boden(o, 0.4)
		best = maxf(best, y)
	return best if best > LEER else 0.0


static func text_hindernis(h: Dictionary) -> String:
	"""«Stufe · 6 cm hoch · in 32 cm» in the current language"""
	if h.is_empty():
		return T.t("freie Bahn")
	var art := str(h["art"])
	var cm := func(k: String) -> int: return int(round(float(h.get(k, 0.0)) * 100.0))
	var parts := [art_text(art)]
	match art:
		"stufe", "rohr", "geroell":
			parts.append(T.t("%d cm hoch") % cm.call("hoehe"))
		"treppe":
			parts.append(T.t("%d Stufen, %d cm hoch") % [int(h.get("stufen", 0)), cm.call("hoehe")])
		"graben":
			parts.append(T.t("%d cm breit, %d cm tief") % [cm.call("breite"), cm.call("tiefe")])
		"luecke":
			parts.append(T.t("%d cm breit, ohne Boden") % cm.call("breite"))
		"rampe":
			parts.append(T.t("%d° steil") % int(round(float(h.get("neigung", 0.0)))))
		"balken":
			parts.append(T.t("%d cm frei darunter") % cm.call("hoehe"))
	parts.append(T.t("in %d cm") % cm.call("abstand"))
	return " · ".join(parts)


static func art_text(art: String) -> String:
	match art:
		"stufe":
			return T.t("Einzelne Stufe")
		"treppe":
			return T.t("Treppe")
		"graben":
			return T.t("Graben")
		"luecke":
			return T.t("Lücke")
		"geroell":
			return T.t("Geröll")
		"rampe":
			return T.t("Rampe")
		"rohr":
			return T.t("Rohr")
		"balken":
			return T.t("Balken")
	return art


static func grund_text(g: String) -> String:
	match g:
		"geschafft":
			return T.t("geschafft")
		"gestürzt":
			return T.t("gestürzt")
		"steckt fest":
			return T.t("steckt fest")
		"zu langsam":
			return T.t("zu langsam")
		"abgebrochen":
			return T.t("abgebrochen")
		"Ring schliesst nicht":
			return T.t("Ring schliesst nicht")
		"Seitenlage zu gross":
			return T.t("Seitenlage zu gross")
		"Kipp-Reserve klein":
			return T.t("Kipp-Reserve klein")
		"Füsse rutschen":
			return T.t("Füsse rutschen")
	return g


func raster_bild() -> Image:
	"""the raster as a small picture: forward = up, grey = flat, warm = higher, dark blue = hole, violet = beam"""
	var img := Image.create(NZ, NX, false, Image.FORMAT_RGB8)
	var hs: PackedFloat32Array = bild.get("hoehe", PackedFloat32Array())
	var dk: PackedFloat32Array = bild.get("decke", PackedFloat32Array())
	if hs.size() != NX * NZ:
		img.fill(Color("#0c121a"))
		return img
	for r in range(NX):
		for c in range(NZ):
			var v: float = hs[r * NZ + c]
			var col := Color("#3a4656")
			if dk[r * NZ + c] > 0.0:
				col = Color("#9a6bff")
			elif v <= LEER + 1.0:
				col = Color("#050a14")
			elif v < -0.01:
				col = Color("#1d3b6e").lerp(Color("#0a1830"), clampf(-v / 0.2, 0.0, 1.0))
			elif v > 0.01:
				col = Color("#3fcf6b").lerp(Color("#ff4d4d"), clampf(v / 0.12, 0.0, 1.0))
			img.set_pixel(c, NX - 1 - r, col)
	var c0 := int(round((BREITE * 0.5 - SPUR) / ZELLE))
	var c1 := int(round((BREITE * 0.5 + SPUR) / ZELLE)) - 1
	for r in range(NX):                                # the foot lane
		for c in [c0, c1]:
			img.set_pixel(c, r, img.get_pixel(c, r).lerp(Color.WHITE, 0.35))
	return img


func info() -> Dictionary:
	var hs: Array = []
	for h in bild.get("hindernisse", []):
		var d: Dictionary = (h as Dictionary).duplicate()
		d["pos"] = [d["pos"].x, d["pos"].y, d["pos"].z]
		d["richtung"] = [d["richtung"].x, d["richtung"].y, d["richtung"].z]
		hs.append(d)
	return {"aktiv": aktiv(), "stil": stil, "gangart": gangart, "hindernisse": hs, "status": strategie_status(),
			"korrekturen": korrekturen, "korrektur_grund": korrektur_grund, "tritte": tritte, "tritte_leer": tritte_leer,
			"tritte_versetzt": tritte_versetzt, "beine_frei": beine_frei, "auto_versuche": auto_versuche, "lernen": lernen != null}


# ==== Anzeige-Feld «KI» (Reiter im Bedienfeld des Labors, gleiche Bausteine wie die anderen Reiter) =========================
const UI = preload("res://scripts/ui_style.gd")
const T = preload("res://scripts/i18n.gd")
var _w := {}


func baue_seite(pg: VBoxContainer, lab) -> void:
	_w = {}
	pg.add_child(UI.small(T.t("Gang-KI: du gibst nur Richtung und Stil vor. Der Roboter sieht das Gelände vor sich (Höhenraster 1.5 × 1 m), erkennt Hindernisse, wählt eine Strategie und setzt jeden Fuss auf sicheren Boden.")))
	var st: Button = lab._button(pg, T.t("Mit der KI gehen"), func():
		lab.start_gang("ki"), true)
	_w["start"] = st
	pg.add_child(UI.small(T.t("Stil")))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 4)
	pg.add_child(row)
	for e in STILE:
		var sid: String = e[0]
		var b: Button = lab._button(row, T.t(e[1]), func():
			setze_stil(sid)
			_male_stil(lab))
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_w["stil_" + sid] = b
	_male_stil(lab)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 10)
	pg.add_child(hb)
	var tr := TextureRect.new()
	tr.name = "ki_raster"
	tr.custom_minimum_size = Vector2(150, 225)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_SCALE
	tr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	tr.tooltip_text = T.t("Was der Roboter sieht: oben = vorne, grau = eben, grün → rot = höher, blau = tiefer, schwarz = kein Boden, violett = Balken darüber, helle Linien = Spur der Füsse")
	hb.add_child(tr)
	_w["raster"] = tr
	var col := VBoxContainer.new()
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_theme_constant_override("separation", 4)
	hb.add_child(col)
	var sieht := Label.new()
	sieht.add_theme_font_size_override("font_size", 13)
	sieht.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sieht.custom_minimum_size = Vector2(150, 0)
	col.add_child(sieht)
	_w["sieht"] = sieht
	var sl := UI.small("", UI.TXT)
	sl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(sl)
	_w["strat"] = sl
	var ll := UI.small("", UI.MUT)
	ll.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	pg.add_child(ll)
	_w["lernen"] = ll
	if lernen != null:
		var tg: CheckButton = lab._toggle(pg, T.t("Lernen im Hintergrund"), bool(lernen.get("an")), func(on: bool): lernen.set("an", on))
		_w["lernen_an"] = tg
	var vg: Button = lab._button(pg, T.t("Vergessen"), func():
		if lernen != null and lernen.has_method("vergessen"):
			lernen.vergessen())
	vg.disabled = lernen == null
	vg.tooltip_text = T.t("Alles Gelernte dieser Variante löschen") if lernen != null else T.t("Lernen (Stufe 3) ist noch nicht eingebaut")
	_w["vergessen"] = vg
	pg.add_child(UI.small(T.t("Grund-Strategien von Hand ausprobieren (vor dem Hindernis):")))
	var gr := GridContainer.new()
	gr.columns = 2
	gr.add_theme_constant_override("h_separation", 6)
	gr.add_theme_constant_override("v_separation", 6)
	pg.add_child(gr)
	for sn in STRATEGIEN:
		var nm: String = sn
		var b: Button = lab._button(gr, T.t(STRATEGIE_NAMEN[nm]), func():
			var pp := {}
			var h := _naechstes()
			if not h.is_empty():
				pp["hindernis"] = h
			strategie_ausfuehren(nm, pp))
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_w["s_" + nm] = b
	lab._button(pg, T.t("Abbrechen"), func():
		abbrechen()
		lab.stop_all())


func _male_stil(lab) -> void:
	for e in STILE:
		var b: Button = _w.get("stil_" + e[0])
		if b != null:
			lab._paint_btn(b, e[0] == stil)


func auffrischen() -> void:
	"""the tab is visible: picture, what it sees, the strategy"""
	if _w.is_empty() or not is_instance_valid(_w.get("raster")):
		return
	if bild.is_empty() and m != null and m.built_ok:
		sehen()
	(_w["raster"] as TextureRect).texture = ImageTexture.create_from_image(raster_bild())
	var hs: Array = bild.get("hindernisse", [])
	var lines := [T.t("Sieht:")]
	if hs.is_empty():
		lines.append("· " + T.t("freie Bahn"))
	for h in hs:
		lines.append("· " + text_hindernis(h))
	(_w["sieht"] as Label).text = "\n".join(lines)
	var st := strategie_status()
	var sl := []
	if not lauf.is_empty():
		sl.append(T.t("Strategie: %s") % T.t(STRATEGIE_NAMEN.get(st["strategie"], st["strategie"])) + " · " + T.t("%d s") % int(st["zeit"]))
	elif not ergebnis.is_empty():
		sl.append(T.t("Zuletzt: %s") % T.t(STRATEGIE_NAMEN.get(st["strategie"], st["strategie"])) + " – " + (T.t("geschafft") if st["erfolg"] else T.t("nicht geschafft") + " (" + grund_text(str(st["grund"])) + ")"))
		sl.append(T.t("%d s · %.2f Wh · Kipp-Reserve min. %d %%") % [int(st["zeit"]), float(st["energie"]), int(round(float(st["kipp_min"]) * 100.0))])
	else:
		sl.append(T.t("Strategie: %s") % (T.t("Normal gehen") if aktiv() else T.t("KI aus")))
	zaehle_frei()
	sl.append(T.t("Tritte %d · versetzt %d · ins Leere %d · Beine in der Luft %d") % [tritte, tritte_versetzt, tritte_leer, beine_frei])
	if korrekturen > 0:
		sl.append(T.t("Korrekturen %d (zuletzt: %s)") % [korrekturen, grund_text(korrektur_grund)])
	(_w["strat"] as Label).text = "\n".join(sl)
	var ll := []
	if lernen != null and lernen.has_method("anzeige_zeilen"):
		for z in lernen.anzeige_zeilen():
			ll.append(str(z))
	else:
		ll.append(T.t("Ohne Lernen: die KI wählt nach festen Regeln (Versuch %d).") % auto_versuche)
	(_w["lernen"] as Label).text = "\n".join(ll)
	for sn in STRATEGIEN:
		var b: Button = _w.get("s_" + sn)
		if b != null and labor != null:
			labor._paint_btn(b, not lauf.is_empty() and str(lauf["name"]) == sn)
	if labor != null and _w.has("start"):
		labor._paint_btn(_w["start"], bew.mode == "gang" and bew.gang == "ki")
		_male_stil(labor)


func steuern(d: Dictionary) -> void:
	"""/control {"action": "roboter", "do": "ki", stil, strategie (name), param {…}, abbrechen, sehen, neu_aufstellen}"""
	if d.has("stil"):
		setze_stil(str(d["stil"]))
	if d.has("sehen"):
		sehen()
	if d.has("strategie"):
		var pp: Dictionary = (d.get("param", {}) as Dictionary).duplicate()
		if not pp.has("hindernis") and not _naechstes().is_empty():
			pp["hindernis"] = _naechstes()
		strategie_ausfuehren(str(d["strategie"]), pp)
	if d.has("abbrechen"):
		abbrechen()
	if d.has("neu_aufstellen") and not _naechstes().is_empty():
		neu_aufstellen(_naechstes())
