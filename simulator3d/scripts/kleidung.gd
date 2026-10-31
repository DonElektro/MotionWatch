extends RefCounted
## «Kleidung nach Jahreszeit» (Zweig real-kleidung, 31.10.2026, Entscheid Daniel): EINE Stelle, die sagt, was die Menschen
## im Simulator tragen - für alle Figuren (Figuren-Paket figur_paket.gd, Ring-Figuren figur.gd, einfache Formen actor.gd,
## Aussehen aus menschen.gd).
##   Winter, Nacht und Berg (Bergtal, Ort «Berge»)  -> lange Kleidung (Winter / kalt: dazu warme Jacke, Handschuhe, Mütze)
##   Sommer am Tag                                  -> gemischt: ein Teil in kurzen Hosen und / oder kurzen Ärmeln
##   Frühling / Herbst am Tag                       -> lang, kurz nur an heissen Tagen (ab 22 °C)
## Quellen der Jahreszeit / Zeit: main.jahreszeit() (jahreszeiten.gd, Szene → Zeit → Jahreszeit), main.is_dark()
## (licht.gd / Uhrzeit), Bergtal (Worlds.world_of(scene) == "bergtal", 1500-2400 m ü. M.) und der echte Ort (ort_env
## «berge»); dazu die Temperatur (Wetter → Temperatur) und Regen.
## Wärmebild: nackte Haut ist wärmer als Kleidung (waerme.gd skin("leg" / "arm") gegen cloth()) - so sieht MoveEye im
## Sommer hellere Beine und Arme, im Winter ist die ganze Figur kühler (dicke Jacke).
## Kostet nichts (eine Abfrage beim Bau einer Figur) - Lite: gleich (keine Effekte).

const Worlds = preload("res://scripts/worlds.gd")
const STUFEN := ["warm", "lang", "gemischt"]

static var force := ""                   # tests (/control figuren op kleidung): "" | warm | lang | gemischt


static func berg(main) -> bool:
	"""in den Bergen (Bergtal, echter Ort mit Umgebung «Berge»)"""
	var sc := str(main.get("scene"))
	if Worlds.world_of(sc) == "bergtal":
		return true
	if sc == "ort":
		var e := str(main.get("ort_env"))
		if e == "auto" and main.get("geo") != null:
			e = str(main.geo.get("env"))
		return e == "berge"
	return false


static func season(main) -> String:
	return str(main.jahreszeit()) if main.has_method("jahreszeit") else "sommer"


static func night(main) -> bool:
	return bool(main.is_dark()) if main.has_method("is_dark") else false


static func stufe(main) -> String:
	"""warm (Winterjacke, Handschuhe) | lang (lange Hosen und Ärmel) | gemischt (Sommer: manche kurz)"""
	if force in STUFEN:
		return force
	var amb: float = float(main.get("ambient")) if main.get("ambient") != null else 14.0
	var s := season(main)
	if s == "winter" or amb < 10.0:                                   # unter 10 °C: wie bisher «cold» in actor.gd
		return "warm"
	if night(main) or berg(main) or str(main.get("weather")) in ["rain", "snow"]:
		return "lang"
	if s == "sommer":
		return "gemischt" if amb >= 12.0 else "lang"
	return "gemischt" if amb >= 22.0 else "lang"


static func wahl(main, variant := "", kid := false, old_ := false, jog := false) -> Dictionary:
	"""was eine neue Figur trägt: {stufe, shorts, short_sleeves, cold}. Zufall pro Figur (gemischt)."""
	var st := stufe(main)
	var amb: float = float(main.get("ambient")) if main.get("ambient") != null else 14.0
	var out := {"stufe": st, "shorts": false, "short_sleeves": false, "cold": st == "warm"}
	if st != "gemischt":
		return out
	if variant in ["police", "burglar", "courier"]:
		return out                                                    # Uniform / dunkle Kleider: immer lang
	# wie viele kurz tragen: an warmen Sommertagen etwa die Hälfte, an kühlen (12-18 °C) etwa ein Viertel
	var k := clampf((amb - 12.0) / 10.0, 0.0, 1.0)
	var p_shorts := lerpf(0.2, 0.5, k) * (0.3 if old_ else 1.0) * (1.4 if kid else 1.0)
	var p_sleeves := lerpf(0.3, 0.65, k) * (0.5 if old_ else 1.0)
	if jog:
		p_shorts = 0.85
		p_sleeves = 0.9
	out["shorts"] = randf() < p_shorts
	out["short_sleeves"] = randf() < p_sleeves
	return out


static func info(main) -> Dictionary:
	return {"stufe": stufe(main), "force": force, "season": season(main), "night": night(main), "berg": berg(main),
			"ambient": main.get("ambient"), "weather": main.get("weather")}
