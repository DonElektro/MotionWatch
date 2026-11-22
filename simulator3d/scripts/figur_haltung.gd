extends RefCounted
## Haltung und Wasser der Spielfigur - EIN Ablauf für «Frei erkunden» (explore_person.gd) und «Die Karte des Grossvaters»
## (kit_abenteuer.gd), 22.11.2026 (Besitzer: im Abenteuer dieselben Bewegungen wie beim Erkunden). Statische Funktionen auf
## einem «Wirt» mit den Feldern main, actor (actor.gd), figur (kit_figur.gd), haltung, wasser, spiegel, sitz:
##   * Haltung (C / ✚ ↓ / Knopf): stehen → geduckt → kriechen → stehen; X (✚ ←) hinsetzen (Bank / Stein in der Nähe, sonst
##     Boden), Z (✚ →) hinlegen; nochmals oder losgehen = aufstehen (liegend losgehen = kriechen). Geduckt / kriechend kein
##     Rennen; Springen heisst dann zuerst aufstehen.
##   * Wasser (erkunden_welt.gd): seicht = waten (langsamer, kein Rennen), tief = schwimmen an der Oberfläche.
##   * Was actor.gd daraus macht: ctl_posture, gear_speed, gear_norun, run_top, frozen, ctl_sit.

const T = preload("res://scripts/i18n.gd")
const ActorS = preload("res://scripts/actor.gd")
const Welt = preload("res://scripts/erkunden_welt.gd")

const HALTUNGEN := ["stehen", "geduckt", "kriechen"]
const POSTUR := {"stehen": 0, "geduckt": 1, "kriechen": 2, "sitzen": 0, "liegen": 2}
const AUGE := {"stehen": 1.62, "geduckt": 1.05, "kriechen": 0.38, "sitzen": 1.15, "liegen": 0.3}   # Rückfall ohne Kopf
const SCHWIMM_V := 0.9               # m/s an der Oberfläche
const SCHWIMM_TIEF := 0.25           # m: die Füsse so weit unter dem Wasserspiegel (der Körper liegt, der Kopf ist oben)
const WATEN_K := 0.55                # waten: so viel vom Tempo


static func weiter(w) -> void:
	"""C: stehen → geduckt → kriechen → stehen (sitting / lying: up to standing)"""
	if w.wasser == "schwimmen":
		return
	if w.haltung in ["sitzen", "liegen"]:
		aufstehen(w, "stehen")
		return
	setzen(w, HALTUNGEN[(HALTUNGEN.find(w.haltung) + 1) % HALTUNGEN.size()])


static func setzen(w, h: String) -> void:
	if not h in POSTUR or w.actor == null or not is_instance_valid(w.actor):
		return
	if w.wasser == "schwimmen" and h != "stehen":
		return                                              # swimming: no posture
	if h == w.haltung:
		return
	if w.haltung == "sitzen" and h != "sitzen":
		aufstehen(w, h)
		return
	if h == "sitzen":
		hinsetzen(w)
		return
	if h == "liegen" and w.wasser != "":
		w.main.start_info = T.t("Im Wasser kann man sich nicht hinlegen")
		return
	w.haltung = h


static func hinsetzen(w) -> void:
	if w.wasser != "":
		w.main.start_info = T.t("Im Wasser kann man sich nicht hinsetzen")
		return
	if w.figur.zustand != "boden":
		return
	var actor = w.actor
	var s: Dictionary = Welt.sitz(w.main, actor.global_position, float(actor.heading))
	w.sitz = s
	w.haltung = "sitzen"
	actor.cur_speed = 0.0
	actor.sit_seat = float(s["h"])
	actor.idle_kind = "sit"
	actor.idle_until = actor.now_s() + 1.0e6
	actor.ctl_sit = true
	if str(s["art"]) != "boden":
		var sp: Vector3 = s["p"]
		actor.position = Vector3(sp.x, actor.position.y, sp.z)
		actor.heading = float(s["yaw"])
		actor.rotation.y = actor.heading
		w.figur._p0 = actor.position


static func aufstehen(w, nach: String) -> void:
	var actor = w.actor
	if w.haltung == "sitzen" and actor != null and is_instance_valid(actor):
		actor.ctl_sit = false
		actor.idle_until = 0.0
		actor.idle_kind = ""
		if str(w.sitz.get("art", "boden")) != "boden":        # off the bench: a step away from it
			var q: Vector2 = w.main.keep_out(Vector2(actor.position.x, actor.position.z), float(actor.radius), true, true)
			actor.position.x = q.x
			actor.position.z = q.y
			w.figur._p0 = actor.position
		w.sitz = {}
	w.haltung = nach if nach in POSTUR and nach != "sitzen" else "stehen"


static func tick(w, ein: Dictionary, wunsch: Dictionary, tempo_k: float, darf_rennen: bool, run_top: float) -> void:
	"""the wishes of this frame (haltung / sitzen / liegen), walking off a seat, then what actor.gd does with it"""
	var mv: Vector2 = ein.get("mv", Vector2.ZERO)
	if bool(wunsch.get("haltung", false)):
		weiter(w)
	if bool(wunsch.get("sitzen", false)):
		if w.haltung == "sitzen":
			aufstehen(w, "stehen")
		else:
			setzen(w, "sitzen")
	if bool(wunsch.get("liegen", false)):
		setzen(w, "stehen" if w.haltung == "liegen" else "liegen")
	if w.haltung == "sitzen" and mv.length() > 0.3:
		aufstehen(w, "stehen")                              # walking off: up from the seat
	elif w.haltung == "liegen" and mv.length() > 0.3:
		w.haltung = "kriechen"                              # lying still, then moving: crawling on
	if w.wasser == "schwimmen" and w.haltung != "stehen":
		if w.haltung == "sitzen":
			aufstehen(w, "stehen")
		w.haltung = "stehen"
	anwenden(w, tempo_k, darf_rennen, run_top)


static func anwenden(w, tempo_k := 1.0, darf_rennen := true, run_top := 0.0) -> void:
	var actor = w.actor
	if actor == null or not is_instance_valid(actor):
		return
	actor.ctl_posture = 2 if w.wasser == "schwimmen" else int(POSTUR[w.haltung])
	actor.gear_speed = (SCHWIMM_V / float(ActorS.PLAYER_SPEED[2])) if w.wasser == "schwimmen" else (WATEN_K if w.wasser == "waten" else 1.0)
	actor.gear_norun = w.wasser != "" or not darf_rennen
	actor.gear_speed *= tempo_k
	actor.run_top = run_top
	actor.frozen = w.haltung in ["sitzen", "liegen"]


static func zuruecksetzen(w) -> void:
	"""back to standing, dry (a new place, a film, a climb): the seat let go, actor.gd normal"""
	if w.haltung == "sitzen":
		aufstehen(w, "stehen")
	w.haltung = "stehen"
	w.wasser = ""
	w.sitz = {}
	var actor = w.actor
	if actor != null and is_instance_valid(actor):
		actor.ctl_posture = 0
		actor.gear_speed = 1.0
		actor.gear_norun = false
		actor.ctl_sit = false


static func sprung_filter(w, ein: Dictionary) -> bool:
	"""a jump while low: first up (no jump); sitting / lying: no move, no jump. true = the jump may go on"""
	if w.haltung in ["sitzen", "liegen"]:
		ein["mv"] = Vector2.ZERO
		ein["sprung"] = false
		return false
	if bool(ein.get("sprung", false)) and w.haltung != "stehen":
		w.haltung = "stehen"                                # first up, then a jump
		ein["sprung"] = false
		return false
	return true


static func wasser_tick(w, ton: Callable) -> bool:
	"""after the actors: deep water = swimming at the surface (true: the figure swims, kit_figur.nach is skipped), shallow =
	wading, out of the deep water the feet on the bed / the bank"""
	var actor = w.actor
	var figur = w.figur
	var zs := str(figur.zustand)
	var wa: Dictionary = Welt.wasser(w.main, actor.position)
	var art: String = Welt.art_fuer_tiefe(float(wa.get("tiefe", 0.0)), str(wa.get("art", "")) == "bach")
	if art == "schwimmen" and (zs == "boden" or (zs == "luft" and figur.y <= float(wa["spiegel"]) - SCHWIMM_TIEF + 0.05)):
		if w.wasser != "schwimmen":
			ton.call("platsch")
			figur.nass += 1
			if w.haltung == "sitzen":
				aufstehen(w, "stehen")
			w.haltung = "stehen"
		w.wasser = "schwimmen"
		w.spiegel = float(wa["spiegel"])
		if zs == "luft":
			figur.geh_zu("boden")
		figur.y = w.spiegel - SCHWIMM_TIEF
		figur.vy = 0.0
		actor.position.y = figur.y
		figur._p0 = actor.position
		return true
	if w.wasser == "schwimmen":                              # out of the deep water: the feet on the bed / the bank
		figur.y = w.main.ground_y(actor.position.x, actor.position.z)
		figur._p0 = Vector3(figur._p0.x, figur.y, figur._p0.z)
	w.wasser = art if art != "schwimmen" else ""
	return false


static func augen_hoehe(haltung: String) -> float:
	return float(AUGE.get(haltung, 1.62))
