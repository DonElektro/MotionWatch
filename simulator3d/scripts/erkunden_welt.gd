extends RefCounted
## «Frei erkunden mit eigener Figur» (Besitzer 21.11.2026, Etappe 1): was die Welt der Figur beim Erkunden bietet -
## Wasser (waten / schwimmen), Sitzplätze (Bank, Stein, sonst der Boden) und Kanten zum Hochklettern. Nur Abfragen, kein
## Zustand: explore_person.gd fragt jedes Bild.
##   * Wasser: im Bergtal die Seen (Ellipsen von bergtal.gd, Wasserspiegel level_of, im Winter das begehbare Eis = trocken)
##     und die Bäche (Band entlang STREAMS, im Winter nicht). Sonst Wasserflächen, die eine Welt oder ein Test als Meta
##     «erkunden_wasser» an main hängt: [{"c": Vector2 (Welt x/z), "r": m, "spiegel": Welt-y}, …].
##   * Tiefe < WATEN_AB: trocken (nasse Füsse zählen nicht) · bis SCHWIMMEN_AB: waten (langsamer, nicht rennen) · tiefer:
##     schwimmen an der Oberfläche (kein Tauchen, niemand ertrinkt). Ein Bach ist immer «waten».
##   * Sitzen: eine Bank der Szene (scenes.data «bench» / «bench2») oder ein niedriges Hindernis (Höhe 0,25–0,95 m: Bank,
##     Stein, Mäuerchen) bis 0,9 m neben der Figur - sonst auf den Boden.
##   * Klettern: vor der Figur steigt der Boden um 0,62–2,2 m an und ist oben eben (Fels, Mauer im Gelände) - kleinere
##     Stufen steigt kit_figur.gd von selbst.

const Bt = preload("res://scripts/bergtal.gd")

const WATEN_AB := 0.25               # m Wassertiefe: ab hier waten
const SCHWIMMEN_AB := 1.1            # m: ab hier schwimmen
const BACH_TIEFE := 0.35             # m: so tief gilt ein Bach (das Band liegt knapp über dem Bachbett)
const SITZ_BODEN := 0.05             # m: auf dem Boden sitzen
const KANTE_MIN := 0.62              # m: ab hier klettern (darunter steigt kit_figur.gd selbst)
const KANTE_MAX := 2.2


static func art_fuer_tiefe(t: float, bach := false) -> String:
	"""'' (trocken) | waten | schwimmen"""
	if bach and t > 0.0:
		return "waten" if t < SCHWIMMEN_AB else "schwimmen"
	if t >= SCHWIMMEN_AB:
		return "schwimmen"
	if t >= WATEN_AB:
		return "waten"
	return ""


static func wasser(main, p: Vector3) -> Dictionary:
	"""das Wasser bei p (Welt): {} = trocken, sonst {art: see | bach | flaeche, tiefe (m), spiegel (Welt-y)}"""
	if main == null:
		return {}
	if main.has_meta("erkunden_wasser"):
		for f in main.get_meta("erkunden_wasser"):
			var c: Vector2 = f["c"]
			if Vector2(p.x, p.z).distance_to(c) < float(f["r"]):
				var sp := float(f["spiegel"])
				var t: float = sp - float(main.ground_y(p.x, p.z))
				if t > 0.02:
					return {"art": "flaeche", "tiefe": t, "spiegel": sp}
	if str(main.scene) != "bergtal" or main.scenes == null:
		return {}
	var b = main.scenes.data.get("bergtal", null)
	if b == null or b.get("tal") == null:
		return {}
	var v: Vector3 = b.V(p)
	var q := Vector2(v.x, v.z)
	var winter: bool = str(b.get("season")) == "winter"
	for lk in Bt.LAKES:
		var e: float = Bt._ell(q, lk)
		if e >= 1.0:
			continue
		var eis := false
		for ic in b.ice:
			if (ic[0][0] as Vector2) == (lk[0] as Vector2) and e >= float(ic[1]):
				eis = true                                    # winter: on the ice (bergtal.gy puts the feet on it)
		if eis:
			return {}
		var sp: float = Bt.level_of(lk) - float(b.h0)
		var t2: float = sp - float(main.ground_y(p.x, p.z))
		if t2 > 0.02:
			return {"art": "see", "tiefe": t2, "spiegel": sp}
		return {}
	if winter:
		return {}
	for st in Bt.STREAMS:
		var pts: Array = st[0]
		var half := float(st[1]) * 0.5 + 0.3
		for i in range(pts.size() - 1):
			var a: Vector2 = pts[i]
			var c2: Vector2 = pts[i + 1]
			if q.x < minf(a.x, c2.x) - half or q.x > maxf(a.x, c2.x) + half or q.y < minf(a.y, c2.y) - half or q.y > maxf(a.y, c2.y) + half:
				continue
			if Bt._seg_t(q, a, c2).y < half:
				var g: float = main.ground_y(p.x, p.z)
				return {"art": "bach", "tiefe": BACH_TIEFE, "spiegel": g + BACH_TIEFE}
	return {}


static func sitz(main, p: Vector3, heading: float) -> Dictionary:
	"""wo und wie hoch die Figur bei p sitzt: {art: bank | stein | boden, h (Sitzhöhe über den Füssen), p (Welt), yaw}"""
	var best := {}
	var bd := 1.6
	var d: Dictionary = main.scenes.data if main.scenes != null else {}
	for bk in ["bench", "bench2"]:
		if d.get(bk, null) is Vector3:
			var bp: Vector3 = d[bk]
			var dd := Vector2(bp.x, bp.z).distance_to(Vector2(p.x, p.z))
			if dd < bd:
				bd = dd
				best = {"art": "bank", "h": 0.45, "p": Vector3(bp.x, main.ground_y(bp.x, bp.z), bp.z), "yaw": heading}
	if not best.is_empty():
		return best
	var p2 := Vector2(p.x, p.z)
	var bo := 0.9
	for o in main._ob_near(p2):
		var ht := float(o.get("ht", 3.0))
		if ht < 0.25 or ht > 0.95 or bool(o.get("wasser", false)):
			continue
		var r: Array = main._ob_closest(o, p2)
		if float(r[1]) < bo:
			bo = float(r[1])
			var n: Vector2 = r[2]
			var at: Vector2 = (r[0] as Vector2) - n * 0.12        # the hips a little over the edge
			best = {"art": "bank" if o.has("h") else "stein", "h": clampf(ht, 0.3, 0.6),
					"p": Vector3(at.x, main.ground_y(at.x, at.y), at.y), "yaw": atan2(-n.x, -n.y)}
	if not best.is_empty():
		return best
	return {"art": "boden", "h": SITZ_BODEN, "p": p, "yaw": heading}


static func kante(main, p: Vector3, heading: float) -> Dictionary:
	"""eine Kante vor der Figur zum Hochklettern: {ziel (oben, Welt), kante (Vorderkante oben), h} oder {}"""
	var dir := Vector3(-sin(heading), 0, -cos(heading))
	for dd in [0.45, 0.7, 0.95, 1.2]:
		var q: Vector3 = p + dir * float(dd)
		var g: float = main.ground_y(q.x, q.z)
		var h := g - p.y
		if h < KANTE_MIN:
			continue
		if h > KANTE_MAX:
			return {}
		var q2: Vector3 = q + dir * 0.45
		var g2: float = main.ground_y(q2.x, q2.z)
		if absf(g2 - g) > 0.3:
			return {}                                        # not flat on top: no place to stand
		return {"ziel": Vector3(q2.x, g2, q2.z), "kante": Vector3(q.x, g, q.z) - dir * 0.1, "h": h}
	return {}
