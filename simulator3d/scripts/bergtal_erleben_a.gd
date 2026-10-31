extends "res://scripts/bergtal_erleben_base.gd"
## 3D-4.x «Bergtal» – lustige und versteckte Ereignisse 1–17 (Daniel 31.10.2026, Stil «dezent», docs/Bergtal_Plan.md):
## kleine Abläufe an den reservierten Plätzen von bergtal.gd (VIGNETTES 1–16 und 29 = Daniels Nummer 17). Humor durch Timing
## und Bewegung, keine Sprechblasen, glaubwürdig – man muss genau hinschauen.
##    1 Murmeltier kommt zu spät zum Bau          ·  2 Kuh leckt am Zelt und klaut die Socke (am eigenen Schlafplatz)
##    3 Alpendohlen streiten um ein Sandwich      ·  4 Steinbock auf der steilen Kante (Felsturm)
##    5 Schafstau auf der Passstrasse             ·  6 Wanderer läuft im Kreis um den Wegweiser
##    7 Gipfelbuch mit lustigen Einträgen         ·  8 Fondue-Caquelon + Fuchs mit Käsefaden (nachts)
##    9 Echo in der Schlucht (das vierte Echo muht) · 10 Kristallhöhle hinter dem Wasserfall (Herbst, wenig Wasser)
##   11 Bunkertür nur nachts: Murmeltier-Büro     · 12 Yeti-Spuren bis zum Schneemann mit Wanderschuhen (Winter)
##   13 Bartgeier lässt einen Knochen fallen      · 14 Alphorn bei Sonnenaufgang, die Kühe kommen gerannt
##   15 Sternschnuppen-Platz auf dem Grat         · 16 Flaschenpost im Gumpisee -> alte Laterne in der Gletscherspalte
##   17 Murmeltier-Fussball mit einem Tennisball
## Wie im Ferienpark (erlebniswelt.gd): jede Vignette ist eine kleine Zustandsmaschine (innere Klasse), läuft nur, wenn die
## Ansicht (Fenster-Kamera) oder MoveEye näher als ACTIVE_R ist, Figuren erst beim ersten Zeigen gebaut (spart Startzeit),
## weiter weg als SHOW_R versteckt. Bei Testlauf / Prüfstand / Messung ist alles weg (vergleichbare Ergebnisse).
## Menschen und Tiere: Figuren von actor.gd im «puppet»-Modus (Wärmebild wie alle Figuren), kleine Dinge aus Grundformen
## mit Wärme-Zwilling. Entdeckungsbuch: main.entdecken.register() (Szene «bergtal», ids «berg.…»), nur wenn es das gibt.
## Steuerung: {"action": "bergtal", "do": "erleben", "what": "info | where | state | go", "id": …}.
## Lite (Engine-Meta «lite» wie bib_berg.gd; der Koordinator verbindet es mit Quality.lite()): weniger Schafe, Spuren und
## Sternschnuppen, keine Zusatzlichter.
## Zweiter Teil (18–34) kommt aus einer eigenen Datei (bergtal_erleben_b.gd) – gemeinsame Hilfen bleiben hier klein.



func _part() -> String:
	return "a"


func _make_vigs() -> Array:
	return [Spaet.new(self), KuhSocke.new(self), Dohlen.new(self), Steinbock.new(self), Schafstau.new(self), Kreis.new(self),
			Gipfelbuch.new(self), Fondue.new(self), Echo.new(self), Kristall.new(self), Buero.new(self), Yeti.new(self),
			Bartgeier.new(self), Alphorn.new(self), Sternschnuppen.new(self), Flaschenpost.new(self), Laterne.new(self), Fussball.new(self)]


# ---- 1 · the marmot that is late: the sentinel whistles (an eagle!), all vanish - only the fat one grazes on ------------------
class Spaet extends Vig:
	var mm: Array = []              # [actor, home burrow, graze point]
	var fat
	var fat_home := Vector3.ZERO
	var eagle: Node3D
	var e_from := Vector3.ZERO
	var e_to := Vector3.ZERO
	var wander_t := 0.0
	var in_hole := {}               # actor -> true while it is in the burrow
	var pushed := false

	func build() -> void:
		id = "murmeltier_zu_spaet"
		c = ew.G(-80.0, 215.0)

	func when_ok() -> bool:
		return ew.season != "winter" and not ew.dark()          # winter: hibernation (Oktober … April)

	func live() -> void:
		var homes := [ew.G(-100.0, 198.0), ew.G(-80.0, 222.0)]
		for i in range(2):
			var g: Vector3 = homes[i] + Vector3(randf_range(-3, 3), 0, randf_range(-3, 3))
			var a: Node3D = ew.marmot(g, g + Vector3(1, 0, 0))
			mm.append([a, homes[i], g])
			actors.append(a)
		fat_home = homes[1]
		var fg: Vector3 = ew.G(-69.0, 211.0)
		fat = ew.marmot(fg, fg + Vector3(-1, 0, 0), 1.0)
		fat.body_root.scale *= Vector3(1.25, 1.1, 1.05)         # the fat one (autumn fat: up to 7 kg)
		actors.append(fat)
		mm.append([fat, fat_home, fg])
		eagle = ew.bt._bird_node(2.1, Color(0.3, 0.22, 0.14), 34.0)   # Steinadler, Spannweite ≈ 2,1 m
		ew.add_child(eagle)
		eagle.visible = false
		go("graze")

	func _sink(a, home: Vector3, k: float) -> void:
		ew.place(a, Vector3(home.x, home.y - 0.65 * k + 0.05, home.z), true)

	func tick(dt: float) -> void:
		wander_t -= dt
		match st:
			"graze":
				for e in mm:
					var a = e[0]
					a.visible = true
					ew.idle(a, "graze")
					if wander_t <= 0.0:
						e[2] = (e[1] if a != fat else ew.G(-69.0, 211.0)) + Vector3(randf_range(-4, 4), 0, randf_range(-4, 4))
					if ew.walk(a, e[2], 0.35, dt):
						pass
				if wander_t <= 0.0:
					wander_t = randf_range(5.0, 9.0)
				if st_t > 22.0 + fmod(t * 0.37, 12.0):
					var w0: Vector3 = ew.W(c)
					e_from = w0 + Vector3(-90, 38, -50)
					e_to = w0 + Vector3(90, 34, 60)
					eagle.visible = true
					go("eagle")
			"eagle":
				_eagle()
				var sentinel = mm[0][0]
				if st_t > 3.5:
					ew.idle(sentinel, "sit_up")                   # Wächter macht Männchen ...
				if st_t > 4.5:
					ew.sound(ew.VL(sentinel.global_position) + Vector3(0, 0.4, 0), "whistle", [[0.0, 0.35, 2700.0, 3100.0, 1.0]], -4.0, -14.0)
					go("flee")                                    # ... und pfeift
			"flee":
				_eagle()
				for e in mm:
					var a = e[0]
					if a == fat:
						continue
					if in_hole.get(a, false):
						continue
					ew.idle(a, "")
					if ew.walk(a, e[1], 3.4, dt, null, 12.0):
						in_hole[a] = true
				for e in mm:                                      # in the hole: down and gone
					var a2 = e[0]
					if in_hole.get(a2, false) and a2 != fat:
						var k := clampf(st_t - 1.6, 0.0, 0.4) / 0.4
						if st_t > 1.0:
							_sink(a2, e[1], k)
						a2.visible = k < 1.0 or st_t > 6.0
						if st_t > 6.0:                            # «all clear» - the heads come out again
							ew.place(a2, Vector3(e[1].x, e[1].y - 0.32, e[1].z), true)
							ew.idle(a2, "sit_up")
				if st_t < 3.0:
					ew.idle(fat, "graze")                         # the fat one has heard nothing
					ew.stop(fat, dt)
				elif st_t < 4.0:
					ew.idle(fat, "sit_up")                        # looks up - where are the others?
					ew.stop(fat, dt)
				else:
					ew.idle(fat, "")
					if ew.walk(fat, fat_home, 2.0, dt, null, 10.0):
						go("squeeze")
			"squeeze":                                        # the fat one squeezes in (wiggles), the other one pops out
				_eagle()
				var k2 := clampf(st_t / 2.6, 0.0, 1.0)
				fat.body_root.rotation.z = 0.3 * sin(st_t * 15.0) * (1.0 - k2)
				_sink(fat, fat_home, k2 * 0.85)
				var other = mm[1][0]
				if st_t > 2.2 and not pushed:
					pushed = true
					other.visible = true
				if pushed:
					var k3 := clampf((st_t - 2.2) / 0.25, 0.0, 1.0)
					ew.place(other, Vector3(fat_home.x + 0.5, fat_home.y - 0.6 * (1.0 - k3), fat_home.z + 0.4), true)
					ew.idle(other, "sit_up")
				if st_t > 3.0:
					fat.visible = false
					fat.body_root.rotation.z = 0.0
				if st_t > 6.5:
					go("out")
			"out":
				eagle.visible = false
				for e in mm:
					var a3 = e[0]
					a3.visible = true
					in_hole.erase(a3)
					if a3.has_meta("be_y"):
						a3.remove_meta("be_y")
					ew.place(a3, ew.G(a3.global_position.x, 0.0) if false else ew.VL(a3.global_position) * Vector3(1, 0, 1) + Vector3(0, ew.bt.H(ew.VL(a3.global_position).x, ew.VL(a3.global_position).z), 0))
					ew.idle(a3, "")
				pushed = false
				go("graze")

	func _eagle() -> void:
		var k := clampf((t - _e_t0()) / 13.0, 0.0, 1.0)
		eagle.global_position = e_from.lerp(e_to, k)
		eagle.rotation = Vector3(0, atan2(-(e_to - e_from).x, -(e_to - e_from).z), 0.1 * sin(t))
		for w in ["wing_l", "wing_r"]:
			var wn := eagle.get_node_or_null(w)
			if wn != null:
				wn.rotation.z = 0.04 * sin(t * 2.0) * (1.0 if w == "wing_r" else -1.0)
		if k >= 1.0:
			eagle.visible = false

	var _et0 := -1.0
	func _e_t0() -> float:
		if st == "eagle" and st_t < 0.05:
			_et0 = t
		if _et0 < 0.0:
			_et0 = t
		return _et0

	func go(s_: String) -> void:
		super.go(s_)
		if s_ == "eagle":
			_et0 = t

	func on_hide() -> void:
		if eagle != null:
			eagle.visible = false

	func info() -> Dictionary:
		var d := super.info()
		d["fat_late"] = st == "flee" and st_t > 3.0
		return d


# ---- 2 · a cow licks the tent and walks off with the sock that dries on the backpack (at your own sleeping spot) -------------
class KuhSocke extends Vig:
	var cow
	var sock: Node3D
	var tongue: MeshInstance3D
	var start := Vector3.ZERO       # world
	var tent_at := Vector3.ZERO     # world: where the cow stands to lick
	var pack_at := Vector3.ZERO     # world: in front of the backpack
	var away := Vector3.ZERO        # world
	var drop := Vector3.ZERO        # world: where the sock lies now
	var bed_rot0 := 0.0

	func build() -> void:
		id = "kuh_socke"
		c = ew.VL(Vector3.ZERO)
		always = true

	func when_ok() -> bool:
		var h: float = ew.hour()
		var sp: Vector2 = ew.bt.spot_xz
		return ew.alp_season() and not ew.dark() and h > 6.5 and h < 19.0 and sp.distance_to(Vector2(110, 40)) < 360.0 \
				and ew.bt._pack_node != null and is_instance_valid(ew.bt._pack_node)

	func where() -> Vector3:
		return Vector3.ZERO

	func _sock_home() -> Vector3:
		return ew.bt._pack_node.global_position + Vector3(0, 0.62, 0)

	func live() -> void:
		var bedn: Node3D = ew.bt._bed_node
		var pk: Vector3 = ew.bt._pack_node.global_position
		var home := Vector2(110, 40)                          # the alp pasture: the cow comes from there
		var to_home: Vector3 = (ew.W(Vector3(home.x, 0, home.y)) - Vector3.ZERO) * Vector3(1, 0, 1)
		var dirw := to_home.normalized() if to_home.length() > 1.0 else Vector3(1, 0, 0)
		start = dirw * 32.0 + Vector3(dirw.z, 0, -dirw.x) * 6.0
		var bw: Vector3 = bedn.global_position if bedn != null else Vector3(2.4, 0, 2.2)
		var side := (bw - Vector3.ZERO) * Vector3(1, 0, 1)
		tent_at = bw + (side.normalized() if side.length() > 0.2 else Vector3(1, 0, 0)) * 1.9
		pack_at = pk + (pk * Vector3(1, 0, 1)).normalized() * 1.45
		away = pk + (pk * Vector3(1, 0, 1)).normalized() * 16.0 + Vector3(dirw.z, 0, -dirw.x) * 5.0
		cow = ew.actor("cow", ew.VL(start), ew.VL(tent_at), 0.6)
		actors.append(cow)
		sock = Node3D.new()
		ew.add_child(sock)
		var sc := Color(0.75, 0.12, 0.12)                     # a red hiking sock with a white ring
		ew.part(sock, ew.boxm(0.09, 0.03, 0.26), Vector3(0, 0, 0), sc, "tent")
		ew.part(sock, ew.boxm(0.09, 0.031, 0.04), Vector3(0, 0.001, -0.08), Color(0.92, 0.92, 0.9), "tent")
		ew.part(sock, ew.boxm(0.08, 0.03, 0.11), Vector3(0, -0.02, 0.15), sc, "tent", Vector3(0.9, 0, 0))
		sock.global_position = _sock_home()
		var hd: Node3D = cow.head if cow.head != null else cow
		tongue = ew.part(hd, ew.boxm(0.07, 0.025, 0.16), Vector3(0, -0.12, -0.55), Color(0.85, 0.45, 0.5), 34.0)
		ew.show_part(tongue, false)
		bed_rot0 = bedn.rotation.z if bedn != null else 0.0
		go("wait")

	func _mouth() -> Vector3:
		var hd: Node3D = cow.head if cow.head != null else cow
		return hd.global_transform * Vector3(0, -0.12, -0.5)

	func _at(w: Vector3) -> Vector3:
		return ew.VL(w)

	func tick(dt: float) -> void:
		var bedn: Node3D = ew.bt._bed_node
		match st:
			"wait":                                         # out of sight, then it comes slowly
				cow.visible = false
				ew.place(cow, _at(start))
				if st_t > 8.0:
					cow.visible = true
					ew.idle(cow, "")
					go("come")
			"come":
				if ew.walk(cow, _at(tent_at), 0.55, dt, null, 2.0):
					go("lick")
			"lick":                                         # licks the tent (salt from the sweat) - the tent wobbles a little
				ew.turn_to(cow, _at(ew.bt._bed_node.global_position if bedn != null else Vector3.ZERO) - ew.ppos(cow), dt, 2.0)
				var lk := sin(st_t * 6.0)
				if cow.head != null:
					cow.head.rotation.x = -0.35 + 0.18 * lk
				ew.show_part(tongue, lk > 0.2)
				if bedn != null:
					bedn.rotation.z = bed_rot0 + 0.015 * sin(st_t * 6.0)
				if st_t > 7.0:
					ew.show_part(tongue, false)
					if bedn != null:
						bedn.rotation.z = bed_rot0
					go("to_pack")
			"to_pack":
				if ew.walk(cow, _at(pack_at), 0.5, dt, null, 2.0):
					ew.idle(cow, "sniff", 2.0)
					go("sniff")
			"sniff":
				ew.turn_to(cow, _at(ew.bt._pack_node.global_position) - ew.ppos(cow), dt, 2.0)
				if st_t > 2.5:
					go("grab")
			"grab":                                         # the sock goes into the mouth
				var k := clampf(st_t / 0.6, 0.0, 1.0)
				sock.global_position = _sock_home().lerp(_mouth(), k)
				if k >= 1.0:
					go("carry")
			"carry":                                        # off it goes, chewing, the sock swings in the mouth
				sock.global_position = _mouth()
				sock.global_rotation = Vector3(0.3 * sin(t * 3.0), cow.rotation.y, 0.4)
				if cow.head != null:
					cow.head.rotation.x = 0.08 * sin(t * 4.0)
				if ew.walk(cow, _at(away), 0.6, dt, null, 2.0):
					go("stare")
			"stare":                                        # turns round and looks at MoveEye - the sock still in the mouth
				sock.global_position = _mouth()
				ew.turn_to(cow, _at(Vector3.ZERO) - ew.ppos(cow), dt, 1.5)
				ew.idle(cow, "stare")
				if st_t > 5.0:
					ew.idle(cow, "")
					drop = ew.W(ew.G(_at(_mouth()).x, _at(_mouth()).z, 0.02))
					go("drop")
			"drop":                                         # drops it in the grass and grazes on
				var k2 := clampf(st_t / 0.4, 0.0, 1.0)
				sock.global_position = _mouth().lerp(drop, k2)
				sock.global_rotation = Vector3(0, 0.7, 0)
				ew.idle(cow, "graze")
				if st_t > 4.0:
					ew.idle(cow, "")
					go("leave")
			"leave":
				if ew.walk(cow, _at(start), 0.5, dt, null, 2.0):
					cow.visible = false
					go("later")
			"later":                                        # much later the sock is back on the backpack (when nobody looks)
				if st_t > 150.0 and ew.unseen(sock.global_position, 6.0):
					sock.global_position = _sock_home()
					sock.global_rotation = Vector3.ZERO
					go("wait")

	func has_sock() -> bool:
		return st in ["grab", "carry", "stare"]

	func on_hide() -> void:
		var bedn: Node3D = ew.bt._bed_node
		if bedn != null and is_instance_valid(bedn):
			bedn.rotation.z = bed_rot0
		if sock != null:
			sock.visible = false

	func set_shown(on: bool) -> void:
		super.set_shown(on)
		if sock != null:
			sock.visible = on


# ---- 3 · alpine choughs fight over a sandwich - the third one takes it --------------------------------------------------------
class Dohlen extends Vig:
	var man
	var seat := Vector3.ZERO
	var sw: Node3D                  # the sandwich
	var sw_home := Vector3.ZERO
	var birds: Array = []           # [node, rest point (valley), from (valley)]
	var view_dir := Vector3.ZERO

	func build() -> void:
		id = "dohlen_sandwich"
		c = ew.G(66.0, 812.0)
		seat = c
		ew.mb.add("boulder", ew.G(c.x, c.z, -0.25), 0.3, {"r": 0.6, "v": 1})
		ew.mb.add("boulder", ew.G(c.x + 0.9, c.z + 0.3, -0.35), 1.2, {"r": 0.55, "v": 2})

	func when_ok() -> bool:
		var h: float = ew.hour()
		return not ew.dark() and h > 8.0 and h < 18.5 and ew.weather() != "rain"

	func live() -> void:
		view_dir = Vector3(-0.6, 0, 1.0)                    # looks over the pass to the south
		man = ew.actor("person", seat, seat + view_dir, 1.0, Color(0.15, 0.45, 0.3))
		ew.backpack(man)
		actors.append(man)
		sw = ew.node(vroot, Vector3.ZERO)
		ew.part(sw, ew.boxm(0.16, 0.025, 0.09), Vector3(0, 0.0, 0), Color(0.85, 0.7, 0.45), "tent")
		ew.part(sw, ew.boxm(0.17, 0.012, 0.1), Vector3(0, 0.018, 0), Color(0.95, 0.85, 0.3), "tent")
		ew.part(sw, ew.boxm(0.18, 0.006, 0.105), Vector3(0, 0.027, 0), Color(0.35, 0.7, 0.25), "tent")
		ew.part(sw, ew.boxm(0.16, 0.025, 0.09), Vector3(0, 0.042, 0), Color(0.85, 0.7, 0.45), "tent")
		sw_home = Vector3(c.x + 0.75, ew.bt.H(c.x + 0.9, c.z + 0.3) + 0.16, c.z + 0.3)
		sw.position = sw_home
		for i in range(3):
			# Alpendohle: schwarz, gelber Schnabel, rote Beine, Spannweite 75–85 cm; Gefieder-Oberfläche ≈ 38 °C (bergtal.gd)
			var b: Node3D = ew.bt._bird_node(0.8, Color(0.06, 0.06, 0.07), 38.0)
			ew.part(b, ew.cylm(0.0, 0.012, 0.05, 6), Vector3(0, 0.0, -0.17), Color(0.95, 0.8, 0.1), 36.0, Vector3(-PI / 2, 0, 0))
			vroot.add_child(b)
			var rest := sw_home + Vector3([-0.28, 0.28, 0.1][i], -0.02, [0.0, 0.05, -0.32][i])
			var from := rest + Vector3(randf_range(-20, 20), 25.0 + i * 3.0, randf_range(-30, -20))
			b.position = from
			b.visible = false
			birds.append([b, rest, from])
		go("eat")

	func _seat(dt: float) -> void:
		man.crouch = move_toward(float(man.crouch), 0.85, dt * 2.0)
		ew.place(man, Vector3(seat.x - 0.1, ew.bt.H(seat.x, seat.z) + 0.12, seat.z), true)

	func _fly(b: Node3D, a: Vector3, z: Vector3, k: float) -> void:
		var p: Vector3 = a.lerp(z, k)
		p.y += sin(k * PI) * 2.0
		b.position = p
		var d := z - a
		b.rotation = Vector3(0, atan2(-d.x, -d.z), 0)
		_flap(b, 1.0)

	func _flap(b: Node3D, amt: float) -> void:
		for w in ["wing_l", "wing_r"]:
			var wn := b.get_node_or_null(w)
			if wn != null:
				wn.rotation.z = amt * 0.7 * sin(t * 18.0) * (1.0 if w == "wing_r" else -1.0)

	func _fold(b: Node3D) -> void:
		for w in ["wing_l", "wing_r"]:
			var wn := b.get_node_or_null(w)
			if wn != null:
				wn.rotation.z = 0.0
				wn.scale = Vector3(0.45, 1, 1)

	func _open(b: Node3D) -> void:
		for w in ["wing_l", "wing_r"]:
			var wn := b.get_node_or_null(w)
			if wn != null:
				wn.scale = Vector3.ONE

	func tick(dt: float) -> void:
		_seat(dt)
		match st:
			"eat":
				sw.visible = true
				sw.position = sw_home
				ew.turn_to(man, view_dir, dt, 2.0)
				ew.idle(man, "")
				if st_t > 8.0:
					go("view")
			"view":                                         # he turns to the view and takes a photo with the phone
				ew.turn_to(man, Vector3(1.0, 0, 0.2), dt, 1.5)
				ew.idle(man, "phone")
				for i in range(birds.size()):
					var b: Node3D = birds[i][0]
					var k := clampf((st_t - 1.0 - i * 0.7) / 2.2, 0.0, 1.0)
					if k > 0.0:
						b.visible = true
						_open(b)
						_fly(b, birds[i][2], birds[i][1], k)
						if k >= 1.0:
							_fold(b)
				if st_t > 5.0:
					go("fight")
			"fight":                                        # two pull at the sandwich, hop and flap; the third walks round
				ew.idle(man, "phone")
				var a: Node3D = birds[0][0]
				var b2: Node3D = birds[1][0]
				var tug := 0.07 * sin(st_t * 7.0)
				sw.position = sw_home + Vector3(tug, 0, 0)
				a.position = birds[0][1] + Vector3(tug, 0.04 * absf(sin(st_t * 9.0)), 0)
				b2.position = birds[1][1] + Vector3(tug, 0.04 * absf(sin(st_t * 9.0 + 1.0)), 0)
				a.rotation.y = PI / 2.0
				b2.rotation.y = -PI / 2.0
				_open(a)
				_open(b2)
				a.get_node("wing_l").rotation.z = -0.5 * absf(sin(st_t * 11.0))
				a.get_node("wing_r").rotation.z = 0.5 * absf(sin(st_t * 11.0))
				b2.get_node("wing_l").rotation.z = -0.5 * absf(sin(st_t * 10.0 + 0.6))
				b2.get_node("wing_r").rotation.z = 0.5 * absf(sin(st_t * 10.0 + 0.6))
				var cb: Node3D = birds[2][0]
				var ang := st_t * 0.9
				cb.position = sw_home + Vector3(cos(ang) * 0.35, -0.02, sin(ang) * 0.35)
				cb.rotation.y = -ang
				if st_t > 4.5:
					go("steal")
			"steal":                                        # the quiet one takes it and flies off; the two fight on a moment
				var cb2: Node3D = birds[2][0]
				_open(cb2)
				var off := Vector3(-18, 22, 25)
				var k2 := clampf(st_t / 3.5, 0.0, 1.0)
				_fly(cb2, sw_home, sw_home + off, k2)
				sw.position = cb2.position + Vector3(0, -0.05, 0)
				if st_t > 1.6:
					for i in range(2):
						var bb: Node3D = birds[i][0]
						_open(bb)
						_fly(bb, birds[i][1], sw_home + off + Vector3(i * 2.0, -2.0, 0), clampf((st_t - 1.6) / 3.5, 0.0, 1.0))
				else:
					for i in range(2):
						_flap(birds[i][0], 0.6)
				if st_t > 5.5:
					for e in birds:
						e[0].visible = false
					sw.visible = false
					go("notice")
			"notice":                                       # he turns back - nothing there; bends to look, then up to the sky
				ew.turn_to(man, view_dir, dt, 2.0)
				if st_t < 1.5:
					ew.idle(man, "")
				elif st_t < 3.5:
					ew.idle(man, "bend")
				else:
					ew.idle(man, "look", 2.0)
				if st_t > 6.0:
					ew.idle(man, "bend", 1.5)                     # a new one out of the backpack
					go("new")
			"new":
				if st_t > 1.5:
					go("eat")

	func stolen() -> bool:
		return st in ["fight", "steal"]


# ---- 4 · an ibex on a rock tower: stands on a few square centimetres, scratches with the horn, lies at the very edge ------------
class Steinbock extends Vig:
	var ibex
	var top := Vector3.ZERO         # valley: the top of the tower
	var ledge := Vector3.ZERO       # valley: a ledge half way down
	var n := 0
	var from := Vector3.ZERO
	var to := Vector3.ZERO

	func build() -> void:
		id = "steinbock_kante"
		c = ew.G(-360.0, 210.0)
		# a free standing rock tower (Felsturm) of gneiss blocks, 7 m high, the top hardly bigger than the ibex
		var g: float = ew.bt.H(c.x, c.z)
		# K3 (Kontaktbogen: «blocks float beside the steep slope»): the foot reaches down to the lowest ground under it
		var lo := g
		for o in [Vector2(1.5, 0), Vector2(-1.5, 0), Vector2(0, 1.5), Vector2(0, -1.5), Vector2(1.1, 1.1), Vector2(-1.1, -1.1), Vector2(1.1, -1.1), Vector2(-1.1, 1.1)]:
			lo = minf(lo, float(ew.bt.H(c.x + o.x, c.z + o.y)))
		if lo < g - 0.2:
			var sy := (g - lo + 0.8) / 1.3                   # (block «v 2»: 1.3 high from -0.1, 1.5 × 1.4 wide)
			ew.mb.parts_of("boulder", Transform3D(Basis(Vector3.UP, 0.5).scaled(Vector3(1.8, sy, 1.8)),
					Vector3(c.x, lo - 0.3 + 0.1 * sy, c.z)), {"r": 1.0, "v": 2})
		var blocks := [[2.8, 2.6, 2.4, 0.0, 1.0, 0.0, 0.15], [2.2, 2.2, 1.9, 0.15, 3.2, -0.1, -0.2], [1.6, 2.0, 1.4, -0.1, 5.1, 0.05, 0.35],
				[1.0, 1.0, 0.85, 0.05, 6.5, 0.0, 0.1]]
		var col := ["7c7a72", "868278", "726f68", "7f7b72"]
		var i := 0
		for bl in blocks:
			ew.mb.parts_of("boulder", Transform3D(Basis(Vector3.UP, float(bl[6])).scaled(Vector3(float(bl[0]), float(bl[1]), float(bl[2])) * 0.5),
					Vector3(c.x + float(bl[3]), g + float(bl[4]) - float(bl[1]) * 0.5, c.z + float(bl[5]))), {"r": 1.0, "v": i % 3})
			i += 1
		ew.mb.add("boulder", Vector3(c.x + 1.55, g + 2.9, c.z + 0.2), 0.8, {"r": 0.45, "v": 1, "noob": true})   # the ledge
		top = Vector3(c.x + 0.05, g + 7.0, c.z)
		ledge = Vector3(c.x + 1.6, g + 3.3, c.z + 0.2)
		m_ob(g)
		var _u = col

	func m_ob(_g: float) -> void:
		ew.m.add_obstacle(ew.W(c), 1.6, false)
		ew.m.set_obstacle_height(7.0)

	func live() -> void:
		# Alpensteinbock (Capra ibex): Bock bis 100 kg, Hörner bis 1 m; geht an fast senkrechten Wänden (Salz lecken)
		ibex = ew.actor("ibex", top, top + Vector3(1, 0, 0.3), 0.8)
		actors.append(ibex)
		go("stand")

	func tick(dt: float) -> void:
		var near: bool = minf(ew.view_pos().distance_to(ew.W(top)), ew.head_pos().distance_to(ew.W(top))) < 30.0
		match st:
			"stand":
				ew.place(ibex, top, true)
				ew.idle(ibex, "stare" if near and st_t > 2.0 else "look", 3.0)
				if st_t > 9.0:
					n += 1
					go("scratch" if n % 3 == 1 else ("lie" if n % 3 == 0 else "hop_down"))
			"scratch":                                      # scratches his back with the tip of the horn
				ew.place(ibex, top, true)
				ew.idle(ibex, "")
				if ibex.head != null:
					ibex.head.rotation.x = lerpf(float(ibex.head.rotation.x), 1.0, clampf(dt * 4.0, 0.0, 1.0))
					ibex.head.rotation.y = 0.35 * sin(st_t * 9.0)
				if st_t > 3.5:
					if ibex.head != null:
						ibex.head.rotation = Vector3.ZERO
					go("stand")
			"hop_down":                                     # one jump down to the ledge (licks salt), then back up
				from = top
				to = ledge
				_hop(dt, "lick")
			"lick":
				ew.place(ibex, ledge, true)
				ew.face(ibex, Vector3(-1, 0, 0))
				ew.idle(ibex, "graze")
				if st_t > 7.0:
					from = ledge
					to = top
					go("hop_up")
			"hop_up":
				_hop(dt, "stand")
			"lie":                                          # lies down on the top, the front legs over the edge
				ew.place(ibex, top + Vector3(0.12, 0, 0), true)
				ew.idle(ibex, "lie")
				if st_t > 14.0:
					ew.idle(ibex, "")
					go("stand")

	func _hop(_dt: float, nxt: String) -> void:
		var k := clampf(st_t / 0.9, 0.0, 1.0)
		var p := from.lerp(to, k)
		p.y += sin(k * PI) * 1.2
		ew.place(ibex, p, true)
		ew.face(ibex, to - from)
		ibex.body_root.rotation.x = -0.4 * cos(k * PI)
		if k >= 1.0:
			ibex.body_root.rotation.x = 0.0
			go(nxt)


# ---- 5 · sheep jam on the pass road: the car waits, creeps, honks - the sheep take their time --------------------------------
class Schafstau extends Vig:
	var sheep: Array = []           # [actor, place on the road (distance along), side offset]
	var car: Node3D
	var pts := PackedVector2Array()
	var hs := PackedFloat32Array()
	var cum := PackedFloat32Array()
	var s0 := 0.0                   # the herd: distance along the road
	var cs := 0.0                   # the car: distance along the road
	var lier = null

	func build() -> void:
		id = "schafstau_pass"
		c = ew.G(240.0, 540.0)
		var rp: PackedVector2Array = ew.bt.road_pts
		var rh: PackedFloat32Array = ew.bt.road_h
		var best := 0
		var bd := INF
		for i in range(rp.size()):
			var d := rp[i].distance_to(Vector2(c.x, c.z))
			if d < bd:
				bd = d
				best = i
		var i0 := maxi(0, best - 45)
		var i1 := mini(rp.size() - 1, best + 45)
		var acc := 0.0
		for i in range(i0, i1 + 1):
			if i > i0:
				acc += rp[i].distance_to(rp[i - 1])
			pts.append(rp[i])
			hs.append(rh[mini(i, rh.size() - 1)] if rh.size() > 0 else ew.bt.H(rp[i].x, rp[i].y))
			cum.append(acc)
			if i == best:
				s0 = acc
		c = Vector3(rp[best].x, hs[best - i0], rp[best].y)

	func when_ok() -> bool:
		var h: float = ew.hour()
		return ew.alp_season() and not ew.dark() and h > 8.0 and h < 19.0

	func at(sd: float, side := 0.0) -> Vector3:
		"""valley point on the road: distance along + offset to the side (+ = right)"""
		sd = clampf(sd, 0.0, cum[cum.size() - 1])
		var i := 1
		while i < cum.size() - 1 and cum[i] < sd:
			i += 1
		var k := (sd - cum[i - 1]) / maxf(0.01, cum[i] - cum[i - 1])
		var p: Vector2 = pts[i - 1].lerp(pts[i], k)
		var d: Vector2 = (pts[i] - pts[i - 1]).normalized()
		p += Vector2(-d.y, d.x) * side
		return Vector3(p.x, lerpf(hs[i - 1], hs[i], k), p.y)

	func dir_at(sd: float) -> Vector3:
		var a := at(sd - 1.0)
		var b := at(sd + 1.0)
		return (b - a) * Vector3(1, 0, 1)

	func live() -> void:
		var n := 5 if ew.lite else 8
		for i in range(n):
			# Schaf (Weisses Alpenschaf): Wolle isoliert - Oberfläche nur ≈ 29 °C (actor.gd)
			var sd := s0 + randf_range(-4.0, 4.0)
			var sdv := randf_range(-2.0, 2.0)
			var a: Node3D = ew.actor("sheep", at(sd, sdv), at(sd + 1.0, sdv), 0.5)
			actors.append(a)
			sheep.append([a, sd, sdv])
		var d: Dictionary = ew.mb.make("car", {"col": "2b5fa8", "style": "sedan"})
		car = ew.mb._node_thing(d, Transform3D.IDENTITY, "car")
		car.reparent(vroot, false)
		ew.mb.stats["animals"] -= 1
		go("wait")

	func _car_at(sd: float) -> void:
		var p := at(sd)
		var dd := dir_at(sd)
		car.transform = Transform3D(Basis(Vector3.UP, atan2(dd.x, dd.z) - PI / 2.0), p)

	func _herd(dt: float, onroad: bool) -> void:
		for e in sheep:
			var a = e[0]
			if a == lier and onroad:
				continue
			var want := at(float(e[1]), float(e[2]) if onroad else (5.0 if float(e[2]) >= 0.0 else -5.0) + float(e[2]))
			if ew.walk(a, want, 0.45, dt, null, 3.0):
				if randf() < dt * 0.15:
					e[1] = clampf(float(e[1]) + randf_range(-1.5, 1.5), s0 - 5.0, s0 + 5.0)
				ew.idle(a, "graze", 3.0) if randf() < 0.6 else ew.idle(a, "look", 2.0)

	func tick(dt: float) -> void:
		match st:
			"wait":                                         # the sheep stand on the warm road
				car.visible = false
				_herd(dt, true)
				if st_t > 18.0:
					cs = s0 - 70.0
					car.visible = true
					go("arrive")
			"arrive":                                       # a car comes and brakes
				_herd(dt, true)
				var gap := (s0 - 7.5) - cs
				var v := clampf(gap * 0.6, 0.0, 9.0)
				cs += v * dt
				_car_at(cs)
				if gap < 0.15:
					lier = sheep[0][0]
					go("stand")
			"stand":                                        # one sheep comes to the bumper and lies down
				_herd(dt, true)
				var lp := at(cs + 3.2, 0.3)
				if ew.walk(lier, lp, 0.4, dt):
					ew.face(lier, dir_at(cs) * -1.0)
					ew.idle(lier, "lie")
				if st_t > 9.0:
					go("creep")
			"creep":                                        # the car creeps a little closer - nobody moves
				_herd(dt, true)
				if st_t < 2.5:
					cs += 0.35 * dt
				_car_at(cs)
				if st_t > 5.0:
					ew.sound(at(cs + 2.0) + Vector3(0, 1, 0), "honk", [[0.0, 0.25, 420.0, 420.0, 1.0], [0.4, 0.45, 420.0, 420.0, 1.0]], -2.0, -6.0)
					go("honk")
			"honk":                                         # honk - the sheep look at the car ... and then slowly go aside
				for e in sheep:
					if st_t < 3.0:
						ew.idle(e[0], "look", 3.0)
				if st_t > 3.0:
					if lier != null:
						ew.idle(lier, "")
					lier = null
					_herd(dt, false)
				if st_t > 9.0:
					go("pass")
			"pass":
				_herd(dt, false)
				cs += minf(1.0 + st_t * 2.0, 8.0) * dt
				_car_at(cs)
				if cs > s0 + 60.0:
					car.visible = false
					go("back")
			"back":                                         # back on the road (it is warm there)
				_herd(dt, true)
				if st_t > 30.0:
					go("wait")

	func jam() -> bool:
		return st in ["stand", "creep", "honk"]


# ---- 6 · a hiker walks round the signpost - again and again, reads it, turns the map, walks round once more ------------------
class Kreis extends Vig:
	var man
	var sign := Vector3.ZERO
	var ang := 0.0
	var lap := 0.0
	var laps := 0
	var cw := 1.0
	const R := 5.5

	func build() -> void:
		id = "wanderer_kreis"
		sign = ew.G(-296.0, 294.0)
		c = sign

	func when_ok() -> bool:
		var h: float = ew.hour()
		return not ew.dark() and h > 8.5 and h < 18.5

	func live() -> void:
		var p := sign + Vector3(R, 0, 0)
		man = ew.actor("person", p, p + Vector3(0, 0, -1), 1.0, Color(0.85, 0.3, 0.1))
		ew.backpack(man, Color(0.25, 0.25, 0.28))
		actors.append(man)
		go("round")

	func tick(dt: float) -> void:
		match st:
			"round":
				ew.idle(man, "")
				var step := 1.05 * dt / R
				ang += step * cw
				lap += step
				var tgt := sign + Vector3(cos(ang + 0.25 * cw) * R, 0, sin(ang + 0.25 * cw) * R)
				ew.walk(man, tgt, 1.05, dt, null, 4.0)
				if lap >= TAU:
					lap = 0.0
					laps += 1
					go("read")
			"read":                                         # looks at the signpost ...
				ew.turn_to(man, sign - ew.ppos(man), dt, 3.0)
				ew.stop(man, dt)
				ew.idle(man, "look", 2.0) if st_t < 2.5 else ew.idle(man, "phone")    # ... then at the map
				if st_t > 6.0:
					if laps % 2 == 0:
						cw = -cw                                  # and now the other way round
					go("round")

	func lost() -> bool:
		return laps >= 1 and st == "read"


# ---- 7 · the summit book: the wind turns the pages, every page another funny entry --------------------------------------------
class Gipfelbuch extends Vig:
	var book: Node3D
	var leaf: Node3D                # the page that turns
	var labels: Array = []          # [left label, right label, leaf front, leaf back]
	var spread := 0
	var wait := 8.0
	const ENTRIES := ["14.7. Endlich oben! Die Murmeltiere waren schneller. – Ruedi",
			"Kein Empfang. Herrlich. – Anna & Marco",
			"Ich bin nur wegen dem Gipfelbuch gekommen. – Beat",
			"Sandwich vergessen. Die Dohle nicht. – S.",
			"Wer hat meine Socke? Die Kuh weiss es. – Fam. Meier",
			"3. Versuch – diesmal der richtige Gipfel. – Hans",
			"Wegweiser unten: 1 h 30. Ich: 4 h. – Lea",
			"Liebes MoveEye, falls du das liest: Grüsse vom Steinbock."]

	func build() -> void:
		id = "gipfelbuch"
		var vp: Array = ew.bt.VIEWPOINTS[0]                # vp_horn: Tschingelspitz with cross and summit box
		var cc: Vector2 = ew.bt.vp_xz(vp)
		var yaw := deg_to_rad(float(vp[6]))
		var fwd := Vector2(sin(yaw), -cos(yaw))
		var side := Vector2(-fwd.y, fwd.x)
		var q := cc + fwd * 1.5 + side * 1.0
		c = ew.G(q.x, q.y)
		ew.mb.add("boulder", ew.G(q.x, q.y, -0.2), 0.4, {"r": 0.42, "v": 0})       # a flat stone beside the cross
		book = ew.node(vroot, ew.G(q.x, q.y, 0.47), PI - yaw)

	func live() -> void:
		var cover := Color(0.45, 0.12, 0.1)
		ew.part(book, ew.boxm(0.32, 0.02, 0.23), Vector3(0, 0, 0), cover, "tent")
		ew.part(book, ew.boxm(0.15, 0.012, 0.21), Vector3(-0.078, 0.014, 0), Color(0.96, 0.95, 0.9), "tent")
		ew.part(book, ew.boxm(0.15, 0.012, 0.21), Vector3(0.078, 0.014, 0), Color(0.96, 0.95, 0.9), "tent")
		ew.part(book, ew.cylm(0.004, 0.004, 0.22, 4), Vector3(0.0, 0.025, 0.1), Color(0.2, 0.2, 0.25), "tent", Vector3(0, 0, PI / 2))  # the pencil on a string
		labels.append(_label(book, Vector3(-0.078, 0.0215, 0), false))
		labels.append(_label(book, Vector3(0.078, 0.0215, 0), false))
		leaf = ew.node(book, Vector3(0, 0.021, 0))
		ew.part(leaf, ew.boxm(0.148, 0.002, 0.205), Vector3(0.076, 0, 0), Color(0.97, 0.96, 0.92), "tent")
		labels.append(_label(leaf, Vector3(0.076, 0.0015, 0), false))
		labels.append(_label(leaf, Vector3(0.076, -0.0015, 0), true))
		leaf.visible = false
		_show(0)
		go("read")

	func _label(par: Node3D, p: Vector3, back: bool) -> Label3D:
		var l := Label3D.new()
		l.position = p
		l.rotation = Vector3(-PI / 2.0, 0, 0) if not back else Vector3(PI / 2.0, PI, 0)
		l.pixel_size = 0.0007
		l.font_size = 20
		l.outline_size = 0
		l.modulate = Color(0.12, 0.16, 0.42)              # pencil / ballpoint blue
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.width = 190.0
		l.double_sided = false
		l.visibility_range_end = 9.0
		l.layers = 1
		par.add_child(l)
		return l

	func _txt(i: int) -> String:
		return T.t(ENTRIES[posmod(i, ENTRIES.size())])

	func _show(sp: int) -> void:
		labels[0].text = _txt(sp * 2)
		labels[1].text = _txt(sp * 2 + 1)

	func tick(_dt: float) -> void:
		match st:
			"read":
				if st_t > wait:
					var w: float = float(ew.m.wind)
					wait = randf_range(6.0, 12.0) * (1.4 if w < 5.0 else 0.8)
					leaf.visible = true
					labels[2].text = _txt(spread * 2 + 1)                # front of the turning leaf = old right page
					labels[3].text = _txt(spread * 2 + 2)                # back = the new left page
					labels[1].text = _txt(spread * 2 + 3)                # under it: the new right page
					go("turn")
			"turn":                                         # the wind lifts the page - it hesitates - and falls over
				var k := clampf(st_t / 1.6, 0.0, 1.0)
				var e := k * k * (3.0 - 2.0 * k)
				var hes := 0.25 * sin(clampf(st_t / 0.6, 0.0, 1.0) * PI) if st_t < 0.6 else 0.0
				leaf.rotation.z = PI * e + hes
				if k >= 1.0:
					spread = (spread + 1) % (ENTRIES.size() / 2)
					leaf.visible = false
					leaf.rotation.z = 0.0
					_show(spread)
					go("read")


# ---- 8 · the forgotten fondue (the burner still glows) - at night the fox pulls a long cheese thread -------------------------
class Fondue extends Vig:
	var fox
	var pot := Vector3.ZERO         # valley: the middle of the cheese
	var thread: MeshInstance3D
	var flame: MeshInstance3D
	var start := Vector3.ZERO
	var dips := 0

	func build() -> void:
		id = "fondue_fuchs"
		c = ew.G(-175.0, -300.0)
		pot = c + Vector3(0, 0.235, 0)
		var n: Node3D = ew.node(ew.holder, c)
		ew.part(n, ew.cylm(0.13, 0.13, 0.01, 12), Vector3(0, 0.236, 0), Color(0.92, 0.78, 0.35), 42.0)    # the cheese, still warm
		ew.part(n, ew.cylm(0.004, 0.004, 0.3, 4), Vector3(0.2, 0.02, 0.15), Color(0.5, 0.5, 0.55), "stone", Vector3(PI / 2, 0.6, 0))   # a fondue fork
		ew.part(n, ew.boxm(0.03, 0.03, 0.03), Vector3(0.12, 0.015, 0.25), Color(0.85, 0.7, 0.45), "tent")   # a piece of bread
		flame = ew.light_part(n, ew.cylm(0.0, 0.03, 0.06, 6), Vector3(0, 0.09, 0), ew.glow_mat(Color(1.0, 0.55, 0.15), 3.0))
		ew.part(n, ew.cylm(0.03, 0.035, 0.03, 6), Vector3(0, 0.075, 0), Color(0.6, 0.6, 0.62), 70.0)       # the burner: hot (Rechaud, Brennpaste)
		start = c + Vector3(-16.0, 0, 13.0)

	func when_ok() -> bool:
		return ew.dark() and ew.season != "winter"

	func live() -> void:
		# Rotfuchs (Vulpes vulpes): Fell-Oberfläche ≈ 28 °C (actor.gd); frisst fast alles - auch Käse
		fox = ew.actor("fox", start, c, 1.2)
		actors.append(fox)
		thread = ew.part(ew.holder, ew.cylm(0.006, 0.006, 1.0, 5), Vector3.ZERO, Color(0.95, 0.82, 0.4), 40.0)
		ew.show_part(thread, false)
		go("away")

	func _mouth() -> Vector3:
		var hd: Node3D = fox.head if fox.head != null else fox
		return ew.VL(hd.global_transform * Vector3(0, -0.03, -0.17))

	func _thread(a: Vector3, b: Vector3) -> void:
		var d := b - a
		var L := d.length()
		ew.show_part(thread, L > 0.02)
		if L < 0.02:
			return
		var mid := (a + b) * 0.5 - Vector3(0, minf(0.05, L * 0.08), 0)
		var bas := Basis.looking_at(d.normalized(), Vector3.UP if absf(d.normalized().y) < 0.95 else Vector3.RIGHT)
		var xf := Transform3D(bas * Basis(Vector3.RIGHT, PI / 2.0) * Basis.from_scale(Vector3(1.0, L, 1.0)), mid)
		thread.transform = xf
		var th: MeshInstance3D = ew.twin_of(thread)
		if th != null:
			th.transform = xf

	func tick(dt: float) -> void:
		flame.scale = Vector3.ONE * (0.85 + 0.2 * sin(t * 13.0) + 0.1 * sin(t * 31.0))
		var near := c + Vector3(-0.42, 0, 0.18)
		match st:
			"away":
				fox.visible = false
				ew.place(fox, start)
				if st_t > 25.0:
					fox.visible = true
					go("come")
			"come":
				if ew.walk(fox, c + Vector3(-3.0, 0, 2.0), 1.1, dt):
					ew.idle(fox, "look", 2.5)
					go("check")
			"check":                                        # looks round - nobody?
				if st_t > 2.8:
					ew.idle(fox, "sniff")
					go("sneak")
			"sneak":
				if ew.walk(fox, near, 0.5, dt):
					go("dip")
			"dip":                                          # the nose into the pot
				ew.idle(fox, "")
				ew.turn_to(fox, c - ew.ppos(fox), dt, 4.0)
				if fox.head != null:
					fox.head.rotation.x = lerpf(float(fox.head.rotation.x), -0.95, clampf(dt * 5.0, 0.0, 1.0))
				if st_t > 1.6:
					go("pull")
			"pull":                                         # backs off slowly - the cheese thread gets longer and longer
				var back := (near - c).normalized()
				ew.place(fox, near + back * minf(st_t, 2.2) * 0.32)
				ew.face(fox, c - ew.ppos(fox))
				if fox.head != null:
					fox.head.rotation.x = lerpf(-0.95, -0.2, clampf(st_t / 2.2, 0.0, 1.0))
				_thread(pot, _mouth())
				if st_t > 2.6:
					go("snap")
			"snap":                                         # snap! - the thread flies back, the fox shakes its head
				var k := clampf(st_t / 0.18, 0.0, 1.0)
				_thread(_mouth().lerp(pot, 1.0 - k * 0.0) if false else pot.lerp(_mouth(), k), _mouth())
				if fox.head != null:
					fox.head.rotation.y = 0.6 * sin(st_t * 22.0) * clampf(1.2 - st_t, 0.0, 1.0)
					fox.head.rotation.x = -0.1
				if st_t > 1.6:
					ew.show_part(thread, false)
					dips += 1
					go("dip_walk" if dips % 2 == 1 else "leave")
			"dip_walk":                                     # once more
				if ew.walk(fox, near, 0.4, dt):
					go("dip")
			"leave":
				if fox.head != null:
					fox.head.rotation = Vector3.ZERO
				if ew.walk(fox, start, 1.4, dt):
					go("away")

	func eating() -> bool:
		return st in ["dip", "pull", "snap"]

	func on_hide() -> void:
		if thread != null:
			ew.show_part(thread, false)


# ---- 9 · the echo in the gorge: «Hoo-hoo» - three echoes - and a fourth one that moos ----------------------------------------
class Echo extends Vig:
	var man
	var mid := Vector3.ZERO
	var ends: Array = []
	var side := 0
	var cycle := 0
	var walls: Array = []

	func build() -> void:
		id = "echo_schlucht"
		var bx: Vector2 = ew.bt.GORGE_BRIDGE
		c = Vector3(bx.x + 1.5, 0, bx.y)
		c.y = ew.m.ground_y(ew.W(c).x, ew.W(c).z) + ew.bt.h0 if false else ew.bt.H(c.x, c.z)
		mid = Vector3(bx.x + 1.5, 0, bx.y)
		ends = [Vector3(bx.x - 15.5, 0, bx.y + 1.0), Vector3(bx.x + 16.0, 0, bx.y + 1.0)]
		walls = [Vector3(bx.x + 8.0, 0, bx.y - 40.0), Vector3(bx.x - 10.0, 0, bx.y - 65.0), Vector3(bx.x + 5.0, 0, bx.y - 90.0)]
		for w in walls:
			w.y = ew.bt.H(w.x, w.z) + 8.0

	func when_ok() -> bool:
		var h: float = ew.hour()
		return not ew.dark() and h > 8.0 and h < 19.0

	func live() -> void:
		man = ew.actor("person", ends[0], mid, 1.0, Color(0.85, 0.75, 0.15))
		ew.backpack(man, Color(0.55, 0.15, 0.12))
		actors.append(man)
		go("walk")

	func _voice_at() -> Vector3:
		return ew.VL(man.global_position) + Vector3(0, 1.6, 0)

	func tick(dt: float) -> void:
		match st:
			"walk":
				man.visible = true
				ew.idle(man, "")
				if ew.walk(man, mid, 1.0, dt, null, 3.0):
					go("breathe")
			"breathe":                                      # turns to the gorge, a deep breath
				ew.turn_to(man, Vector3(0, 0, -1), dt, 2.0)
				ew.stop(man, dt)
				if st_t > 1.6:
					man.emote = "goal"
					man.emote_until = man.now_s() + 1.3
					var me := _voice_at()
					ew.sound(me, "voice", [[0.0, 0.45, 330.0, 300.0, 1.0], [0.55, 0.7, 260.0, 235.0, 1.0]], 0.0, -8.0)
					var late := cycle % 2 == 1
					for i in range(3):
						var dl := 1.45 + i * 1.25 + (5.5 if late and i == 2 else 0.0)
						ew.sound(walls[i], "voice", [[0.0, 0.45, 330.0, 300.0, 1.0], [0.55, 0.7, 260.0, 235.0, 1.0]], -6.0 - i * 5.0, -20.0 - i * 4.0, dl)
					if not late:
						ew.sound(walls[2] + Vector3(-20, 0, -30), "moo", [[0.0, 1.4, 125.0, 92.0, 1.0]], -10.0, -24.0, 6.4)
					go("listen")
			"listen":                                       # listens - head left, right
				ew.idle(man, "look", 2.0)
				var late2 := cycle % 2 == 1
				if not late2 and st_t > 6.4 and st_t < 7.4:
					man.startle_until = man.now_s() + 0.8       # the fourth «echo» moos
				if late2 and st_t > 4.5:
					go("turn_away")
				elif not late2 and st_t > 9.5:
					go("leave")
			"turn_away":                                    # only two echoes? he turns to go - and the third comes now
				var e2: Vector3 = ends[1 - side]
				ew.idle(man, "")
				ew.walk(man, e2, 0.8, dt, null, 3.0)
				if st_t > 2.4 and st_t < 3.2:
					man.startle_until = man.now_s() + 0.7
				if st_t > 2.4:
					ew.stop(man, dt)
					ew.turn_to(man, Vector3(0, 0, -1), dt, 3.0)
				if st_t > 6.0:
					go("leave")
			"leave":
				var e3: Vector3 = ends[1 - side]
				ew.idle(man, "")
				if ew.walk(man, e3, 1.0, dt, null, 3.0):
					side = 1 - side
					cycle += 1
					man.visible = false
					go("gone")
			"gone":
				if st_t > 25.0:
					go("walk")

	func calling() -> bool:
		return st in ["breathe", "listen", "turn_away"]


# ---- 10 · the crystal cave behind the waterfall - only when there is little water (autumn) -----------------------------------
class Kristall extends Vig:
	var crystals: Array = []
	var glow: OmniLight3D
	var cmat: StandardMaterial3D

	func build() -> void:
		id = "kristallhoehle"
		var gh: Vector2 = ew.bt.GORGE_HEAD
		var bot: float = ew.bt._bed_at(0, gh.y - 16.0)
		c = Vector3(gh.x + 1.25, bot, gh.y + 0.9)

	func when_ok() -> bool:
		return ew.season == "herbst"                      # Niedrigwasser im Herbst: der Vorhang ist schmal, die Höhle frei

	func live() -> void:
		var n: Node3D = ew.node(vroot, c, deg_to_rad(10.0))
		var rock := Color(0.32, 0.31, 0.3)
		ew.part(n, ew.boxm(2.2, 0.5, 1.6), Vector3(0, 2.0, 0.4), rock, "stone")            # the rock around the opening
		ew.part(n, ew.boxm(0.5, 2.0, 1.6), Vector3(-0.85, 1.0, 0.4), rock, "stone")
		ew.part(n, ew.boxm(0.5, 2.0, 1.6), Vector3(0.85, 1.0, 0.4), rock, "stone")
		ew.part(n, ew.boxm(1.3, 1.9, 0.2), Vector3(0, 0.95, 1.15), Color(0.04, 0.04, 0.05), "stone")   # dark inside
		ew.part(n, ew.boxm(1.3, 0.2, 1.4), Vector3(0, 0.05, 0.45), Color(0.2, 0.19, 0.18), "stone")
		# Bergkristall (Quarz): sechseckige, klare Spitzen; im Licht der Spalte schimmern sie leicht violett (Amethyst-Spuren)
		cmat = StandardMaterial3D.new()
		cmat.albedo_color = Color(0.88, 0.85, 1.0, 0.75)
		cmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		cmat.roughness = 0.05
		cmat.metallic_specular = 1.0
		cmat.emission_enabled = true
		cmat.emission = Color(0.7, 0.6, 1.0)
		cmat.emission_energy_multiplier = 0.35
		var pos := [[-0.35, 0.15, 0.9, 0.3, -0.2], [-0.2, 0.15, 1.0, 0.22, 0.3], [0.1, 0.15, 0.95, 0.38, 0.1], [0.3, 0.15, 0.85, 0.2, -0.4],
				[0.0, 0.15, 0.7, 0.16, 0.6], [-0.45, 1.75, 0.9, 0.18, 2.8], [0.4, 1.7, 0.95, 0.24, 3.3], [0.5, 0.9, 1.0, 0.2, 1.7], [-0.5, 0.7, 0.95, 0.17, -1.6]]
		for p in pos:
			var mi := MeshInstance3D.new()
			mi.mesh = ew.cylm(0.0, float(p[3]) * 0.22, float(p[3]), 6)
			mi.material_override = cmat
			mi.position = Vector3(p[0], p[1] + float(p[3]) * 0.5 * cos(float(p[4])), p[2])
			mi.rotation = Vector3(0.25 * sin(float(p[4]) * 3.0), 0, float(p[4]) * 0.35)
			mi.layers = 1
			n.add_child(mi)
			crystals.append(mi)
		ew.part(n, ew.boxm(0.08, 0.03, 0.25), Vector3(0.3, 0.17, 0.5), Color(0.25, 0.2, 0.15), "stone", Vector3(0, 0.8, 0))   # a forgotten hammer (Strahler)
		glow = ew.lamp(n, Vector3(0, 0.8, 0.6), Color(0.75, 0.65, 1.0), 0.5, 2.5)

	func tick(_dt: float) -> void:
		if cmat != null:                                  # the crystals sparkle a little in the moving light of the water
			cmat.emission_energy_multiplier = 0.3 + 0.15 * sin(t * 2.3) + 0.08 * sin(t * 7.1)
		if glow != null:
			glow.light_energy = 0.4 + 0.15 * sin(t * 3.1)


# ---- 11 · the bunker door opens only at night: inside works a marmot at a small desk (and it stops when you come) --------------
class Buero extends Vig:
	var door: Node3D                # the hinge
	var inside: Node3D
	var mm
	var lampm: StandardMaterial3D
	var light: OmniLight3D
	var xf := Transform3D()         # bunker -> valley
	var papers: Array = []
	var stamps := 0

	func build() -> void:
		id = "bunker_buero"
		var bk: Vector2 = ew.bt.BUNKER
		xf = Transform3D(Basis(Vector3.UP, -PI / 2.0), ew.G(bk.x, bk.y))
		c = xf * Vector3(-0.9, 0, 2.6)

	func when_ok() -> bool:
		return ew.dark()

	func live() -> void:
		var base: Node3D = ew.node(vroot, Vector3.ZERO)
		base.transform = xf
		inside = ew.node(base, Vector3(-0.9, 0, 1.955))
		var dm: StandardMaterial3D = ew.glow_mat(Color(0.16, 0.1, 0.05), 0.5)       # the dark room behind the door, a little warm light
		var back := MeshInstance3D.new()
		back.mesh = ew.boxm(0.98, 1.98, 0.01)
		back.material_override = dm
		back.position = Vector3(0, 0.99, 0.0)
		inside.add_child(back)
		door = ew.node(base, Vector3(-1.4, 0, 1.99))              # hinge on the left
		ew.part(door, ew.boxm(1.0, 2.0, 0.06), Vector3(0.5, 1.0, 0.0), Color(0.29, 0.29, 0.23), "stone")
		ew.part(door, ew.boxm(0.12, 0.04, 0.05), Vector3(0.85, 1.0, 0.05), Color(0.2, 0.2, 0.2), "stone")
		# the office on the threshold: a tiny desk, a lamp, a pile of papers, a stamp
		var desk: Node3D = ew.node(base, Vector3(-0.9, 0, 2.35))
		ew.part(desk, ew.boxm(0.5, 0.03, 0.3), Vector3(0, 0.3, 0), Color(0.45, 0.32, 0.2), "tree")
		for sx in [-0.22, 0.22]:
			ew.part(desk, ew.boxm(0.03, 0.3, 0.26), Vector3(sx, 0.15, 0), Color(0.4, 0.28, 0.18), "tree")
		lampm = ew.glow_mat(Color(1.0, 0.78, 0.4), 2.5)
		ew.part(desk, ew.cylm(0.005, 0.005, 0.16, 4), Vector3(-0.18, 0.39, -0.08), Color(0.2, 0.2, 0.2), "stone")
		var shade: MeshInstance3D = ew.light_part(desk, ew.cylm(0.025, 0.05, 0.05, 8), Vector3(-0.18, 0.47, -0.08), lampm)
		var _sh = shade
		for i in range(6):
			var pp: MeshInstance3D = ew.part(desk, ew.boxm(0.1, 0.004, 0.14), Vector3(0.13, 0.318 + i * 0.005, 0.02), Color(0.95, 0.95, 0.9), "tent", Vector3(0, 0.1 * (i % 3), 0))
			papers.append(pp)
		ew.part(desk, ew.cylm(0.012, 0.015, 0.035, 6), Vector3(0.0, 0.335, 0.06), Color(0.4, 0.25, 0.15), "tree")   # the stamp
		light = ew.lamp(desk, Vector3(-0.1, 0.6, 0.1), Color(1.0, 0.8, 0.5), 0.8, 3.5)
		var p0: Vector3 = ew.VL(desk.global_position) + Vector3(0, 0, 0)
		var lk := xf * Vector3(-0.9, 0, 1.0)
		mm = ew.marmot(xf * Vector3(-0.9, 0, 2.62), lk)
		actors.append(mm)
		var _u = p0
		go("closed")

	func _near() -> bool:
		var w: Vector3 = ew.W(c)
		return minf(ew.view_pos().distance_to(w), ew.head_pos().distance_to(w)) < 6.0

	func _open(k: float) -> void:
		door.rotation.y = -1.6 * k                         # opens outwards
		var on := k > 0.05
		inside.visible = on
		mm.visible = on
		lampm.emission_energy_multiplier = 2.5 if k > 0.6 else 0.0
		if light != null:
			light.visible = k > 0.6

	func tick(_dt: float) -> void:
		var near := _near()
		var mp: Vector3 = xf * Vector3(-0.9, 0, 2.62)
		match st:
			"closed":
				_open(0.0)
				if st_t > 6.0 and not near:
					ew.sound(c + Vector3(0, 1, 0), "creak", [[0.0, 0.9, 30.0, 18.0, 1.0]], -10.0, -22.0)
					go("opening")
			"opening":
				_open(clampf(st_t / 1.6, 0.0, 1.0))
				if st_t > 1.6:
					go("work")
			"work":                                         # stamps, sorts, stamps
				_open(1.0)
				ew.place(mm, Vector3(mp.x, ew.bt.H(mp.x, mp.z) + 0.0, mp.z))
				ew.face(mm, (xf * Vector3(-0.9, 0, 1.0)) - mp)
				ew.idle(mm, "sit_up")
				if mm.head != null:
					var u := fmod(st_t, 1.3)
					mm.head.rotation.x = -0.9 * smoothstep(0.0, 0.12, u) * (1.0 - smoothstep(0.18, 0.35, u))
					if u < 0.02:
						stamps += 1
						ew.sound(c + Vector3(0, 0.4, 0), "thud", [[0.0, 0.08, 1.0, 1.0, 0.4]], -18.0, -30.0)
				for i in range(papers.size()):
					papers[i].visible = i < 2 + (stamps % 5)
				if near:
					go("caught")
			"caught":                                       # caught - it freezes, looks at you, lamp off, door shut
				ew.idle(mm, "stare")
				if mm.head != null:
					mm.head.rotation.x = 0.0
				if st_t > 1.2:
					lampm.emission_energy_multiplier = 0.0
					if light != null:
						light.visible = false
				if st_t > 1.5:
					_open(1.0 - clampf((st_t - 1.5) / 0.4, 0.0, 1.0))
					lampm.emission_energy_multiplier = 0.0
				if st_t > 1.9:
					ew.sound(c + Vector3(0, 1, 0), "thud", [[0.0, 0.15, 1.0, 1.0, 1.0]], -6.0, -14.0)
					go("shut")
			"shut":
				_open(0.0)
				if st_t > 20.0 and not near:
					go("closed")

	func working() -> bool:
		return st in ["work", "caught"]

	func on_hide() -> void:
		if door != null:
			_open(0.0)
			st = "closed"


# ---- 12 · winter: huge tracks in the snow - they end at a snowman wearing hiking boots (who looks at you when you look away) -----
class Yeti extends Vig:
	var sm: Node3D
	var headn: Node3D
	var look_t := 0.0

	func build() -> void:
		id = "yeti_spuren"
		c = ew.G(700.0, 380.0)

	func when_ok() -> bool:
		return ew.season == "winter"

	func live() -> void:
		# the tracks: one mesh for all of them (pressed into the snow - a little darker, bluish)
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		var a := Vector2(655.0, 338.0)
		var b := Vector2(c.x, c.z)
		var L := a.distance_to(b)
		var dd := (b - a).normalized()
		var nn := Vector2(-dd.y, dd.x)
		var n := int(L / (2.2 if ew.lite else 1.1))
		var sole: BoxMesh = ew.boxm(0.24, 0.02, 0.48)
		var toe: SphereMesh = ew.sphm(0.05, 0.03, 6)
		for i in range(n):
			var k := float(i) / maxf(1.0, n - 1.0)
			var q := a.lerp(b, k * 0.97) + Vector2(sin(k * 9.0) * 1.2, 0) + nn * (0.28 if i % 2 == 0 else -0.28)
			var y: float = ew.bt.H(q.x, q.y) + 0.005
			var rot := Basis(Vector3.UP, atan2(dd.x, dd.y) + PI)
			var xf2 := Transform3D(rot, Vector3(q.x, y, q.y))
			st.append_from(sole, 0, xf2)
			for tt in range(4):
				st.append_from(toe, 0, xf2 * Transform3D(Basis(), Vector3(-0.09 + tt * 0.06, 0.0, -0.3)))
		var mi := MeshInstance3D.new()
		mi.mesh = st.commit()
		mi.material_override = ew.m.mat(Color(0.62, 0.68, 0.78))
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		vroot.add_child(mi)
		# the snowman: three balls, coal eyes, a carrot, a wool hat - and two real hiking boots under him
		sm = ew.node(vroot, c, atan2(-dd.x, -dd.y))
		var sn := Color(0.95, 0.96, 0.98)
		ew.part(sm, ew.sphm(0.45, 0.85, 14), Vector3(0, 0.55, 0), sn, "snow")
		ew.part(sm, ew.sphm(0.33, 0.62, 12), Vector3(0, 1.2, 0), sn, "snow")
		headn = ew.node(sm, Vector3(0, 1.62, 0))
		ew.part(headn, ew.sphm(0.23, 0.44, 12), Vector3.ZERO, sn, "snow")
		for sx in [-0.08, 0.08]:
			ew.part(headn, ew.sphm(0.025), Vector3(sx, 0.06, -0.2), Color(0.05, 0.05, 0.05), "stone")
		ew.part(headn, ew.cylm(0.0, 0.03, 0.18, 6), Vector3(0, 0.0, -0.3), Color(0.95, 0.45, 0.1), "tree", Vector3(-PI / 2, 0, 0))
		ew.part(headn, ew.cylm(0.17, 0.21, 0.16, 10), Vector3(0, 0.2, 0), Color(0.75, 0.1, 0.12), "tent")
		ew.part(headn, ew.sphm(0.06), Vector3(0, 0.31, 0), Color(0.95, 0.95, 0.95), "tent")
		for i in range(3):
			ew.part(sm, ew.sphm(0.03), Vector3(0, 1.05 + i * 0.13, -0.31 + i * 0.01), Color(0.05, 0.05, 0.05), "stone")
		for sx in [-0.17, 0.17]:                         # the boots - toes forward, red laces
			ew.part(sm, ew.boxm(0.13, 0.14, 0.3), Vector3(sx, 0.07, -0.28), Color(0.38, 0.24, 0.12), "tent")
			ew.part(sm, ew.boxm(0.14, 0.03, 0.32), Vector3(sx, 0.015, -0.29), Color(0.1, 0.1, 0.1), "tent")
			ew.part(sm, ew.boxm(0.1, 0.01, 0.12), Vector3(sx, 0.145, -0.32), Color(0.8, 0.1, 0.1), "tent")
		ew.part(sm, ew.cylm(0.015, 0.02, 1.1, 5), Vector3(0.42, 1.2, 0), Color(0.35, 0.25, 0.15), "tree", Vector3(0, 0, -0.9))   # a stick arm
		go("stand")

	func tick(dt: float) -> void:
		# when you look away, the head slowly turns to you; when you look, it keeps still (you never see it move)
		look_t -= dt
		if look_t > 0.0:
			return
		look_t = 0.25
		var hw: Vector3 = headn.global_position
		if ew.unseen(hw, 90.0):
			var to: Vector3 = ew.view_pos() - hw
			var want := atan2(-to.x, -to.z) - sm.global_rotation.y
			headn.rotation.y = rotate_toward(headn.rotation.y, clampf(wrapf(want, -PI, PI), -1.4, 1.4), 0.6)

	func turned() -> bool:
		return headn != null and absf(headn.rotation.y) > 0.3


# ---- 13 · a bearded vulture drops a bone onto the rock - right beside the hiker who has his lunch ------------------------------
class Bartgeier extends Vig:
	var man
	var seat := Vector3.ZERO
	var seat2 := Vector3.ZERO
	var slab := Vector3.ZERO        # valley: the top of the flat rock
	var bird: Node3D
	var bone: Node3D
	var bits: Array = []            # [node, velocity]
	var bpos := Vector3.ZERO
	var bvel := Vector3.ZERO
	var ang := 0.0
	var at_seat2 := false

	func build() -> void:
		id = "bartgeier_knochen"
		c = ew.G(-400.0, 420.0)
		seat = c
		seat2 = ew.G(c.x - 2.8, c.z - 1.2)
		ew.mb.add("boulder", ew.G(c.x, c.z, -0.25), 0.2, {"r": 0.6, "v": 0})
		ew.mb.add("boulder", ew.G(seat2.x, seat2.z, -0.28), 1.1, {"r": 0.6, "v": 2})
		var sp: Vector3 = ew.G(c.x + 2.2, c.z + 0.6)
		ew.mb.parts_of("boulder", Transform3D(Basis(Vector3.UP, 0.4).scaled(Vector3(1.4, 0.35, 1.1)), sp + Vector3(0, -0.1, 0)), {"r": 1.0, "v": 1})   # the flat rock (Knochenschmiede)
		slab = sp + Vector3(0, 0.25, 0)

	func when_ok() -> bool:
		var h: float = ew.hour()
		return not ew.dark() and h > 9.0 and h < 18.0 and ew.weather() in ["clear", "cloudy"]

	func live() -> void:
		man = ew.actor("person", seat, seat + Vector3(0.3, 0, 1.0), 1.0, Color(0.2, 0.3, 0.6))
		ew.backpack(man, Color(0.7, 0.45, 0.1))
		actors.append(man)
		# Bartgeier (Gypaetus barbatus): Spannweite 2,6–2,9 m, frisst Knochen; zu grosse lässt er aus 50–80 m auf Felsplatten fallen
		bird = ew.bt._bird_node(2.8, Color(0.55, 0.42, 0.3), 34.0)
		ew.part(bird, ew.sphm(0.12), Vector3(0, 0.08, -0.5), Color(0.85, 0.55, 0.3), 36.0)     # the rusty head
		vroot.add_child(bird)
		bone = ew.node(vroot, Vector3.ZERO)
		ew.part(bone, ew.cylm(0.03, 0.03, 0.34, 6), Vector3.ZERO, Color(0.92, 0.9, 0.82), "stone", Vector3(0, 0, PI / 2))
		for sx in [-0.17, 0.17]:
			ew.part(bone, ew.sphm(0.045), Vector3(sx, 0, 0), Color(0.92, 0.9, 0.82), "stone")
		bone.visible = false
		for i in range(3):
			var b: Node3D = ew.node(vroot, Vector3.ZERO)
			ew.part(b, ew.cylm(0.028, 0.03, 0.12, 5), Vector3.ZERO, Color(0.9, 0.88, 0.8), "stone", Vector3(0, 0, PI / 2 + i))
			b.visible = false
			bits.append([b, Vector3.ZERO])
		go("circle")

	func _sit(dt: float, p: Vector3) -> void:
		man.crouch = move_toward(float(man.crouch), 0.85, dt * 2.0)
		ew.place(man, Vector3(p.x - 0.1, ew.bt.H(p.x, p.z) + 0.12, p.z), true)

	func _flap(amt: float) -> void:
		for w in ["wing_l", "wing_r"]:
			var wn := bird.get_node_or_null(w)
			if wn != null:
				wn.rotation.z = amt * sin(t * 4.0) * (1.0 if w == "wing_r" else -1.0)

	func tick(dt: float) -> void:
		var sp: Vector3 = seat2 if at_seat2 else seat
		match st:
			"circle":                                       # high up, slowly round
				_sit(dt, sp)
				ew.face(man, Vector3(0.3, 0, 1.0))
				ang += dt * 0.18
				bird.position = slab + Vector3(cos(ang) * 30.0, 45.0 + 3.0 * sin(t * 0.3), sin(ang) * 30.0)
				bird.rotation = Vector3(0, -ang, 0.3)
				_flap(0.03)
				for b in bits:
					b[0].visible = false
				if st_t > 18.0 and absf(wrapf(ang, -PI, PI)) < 0.1:
					go("pass")
			"pass":                                         # straight over the rock ... and lets go
				_sit(dt, sp)
				var a := slab + Vector3(30.0, 45.0, 0)
				var b2 := slab + Vector3(-30.0, 40.0, 0)
				var k := clampf(st_t / 7.0, 0.0, 1.0)
				bird.position = a.lerp(b2, k)
				bird.rotation = Vector3(0, PI / 2.0, 0.0)
				_flap(0.02)
				if k > 0.5 and not bone.visible:
					bone.visible = true
					bpos = bird.position + Vector3(0, -0.3, 0)
					bvel = Vector3(-8.0, 0, 0)               # the bone keeps the speed of the bird for a moment
				if bone.visible:
					bvel.y -= 9.81 * dt
					bvel.x *= 1.0 - dt * 0.4
					bpos += bvel * dt
					bone.position = bpos
					bone.rotation.z += dt * 6.0
					if bpos.y <= slab.y + 0.05:
						bone.visible = false
						ew.sound(slab, "thud", [[0.0, 0.12, 1.0, 1.0, 1.0]], 0.0, -12.0)
						for i in range(bits.size()):
							bits[i][0].visible = true
							bits[i][0].position = slab
							bits[i][1] = Vector3(randf_range(-1.2, 1.2), randf_range(1.0, 2.0), randf_range(-1.2, 1.2))
						man.startle_until = man.now_s() + 1.0
						go("smash")
			"smash":                                        # the bits jump; he jumps up and looks up
				for e in bits:
					var bn: Node3D = e[0]
					if bn.position.y > slab.y - 0.03 or e[1].y > 0.0:
						e[1].y -= 9.81 * dt
						bn.position += e[1] * dt
						bn.rotation.x += dt * 8.0
					if bn.position.y < slab.y - 0.03:
						bn.position.y = slab.y - 0.03
						e[1] = Vector3.ZERO
				man.crouch = move_toward(float(man.crouch), 0.0, dt * 3.0)
				if man.has_meta("be_y"):
					man.remove_meta("be_y")
				ew.idle(man, "look", 2.0)
				var k3 := clampf(st_t / 4.0, 0.0, 1.0)
				bird.position = (slab + Vector3(-30.0, 40.0, 0)).lerp(slab + Vector3(-3.0, 8.0, 2.0), k3)
				bird.rotation = Vector3(0, -PI / 2.0, 0.2)
				if st_t > 2.5:
					go("move")
			"move":                                         # he moves a few metres away - you never know
				var dst: Vector3 = seat if at_seat2 else seat2
				ew.idle(man, "")
				var k4 := clampf(st_t / 3.0, 0.0, 1.0)
				bird.position = (slab + Vector3(-3.0, 8.0, 2.0)).lerp(slab + Vector3(-0.6, 0.0, 0.3), k4)
				_flap(0.4 * (1.0 - k4))
				if ew.walk(man, dst + Vector3(-0.1, 0, 0), 0.9, dt):
					at_seat2 = not at_seat2
					go("pick")
			"pick":                                         # the vulture walks to the bits, takes the biggest and flies off
				_sit(dt, seat2 if at_seat2 else seat)
				ew.face(man, slab - (seat2 if at_seat2 else seat))
				if st_t < 2.0:
					bird.position = slab + Vector3(-0.6, 0.0, 0.3) + Vector3(0.25 * st_t, 0, 0)
					_flap(0.0)
				else:
					var k5 := clampf((st_t - 2.0) / 6.0, 0.0, 1.0)
					bits[0][0].position = bird.position + Vector3(0, -0.2, 0)
					bird.position = (slab + Vector3(-0.1, 0.0, 0.3)).lerp(slab + Vector3(40.0, 50.0, -20.0), k5 * k5)
					bird.rotation = Vector3(0, atan2(-40.0, 20.0), 0.1)
					_flap(0.8 * (1.0 - k5))
					if k5 >= 1.0:
						bits[0][0].visible = false
						go("circle")

	func dropped() -> bool:
		return st in ["smash", "move"] or (st == "pass" and bone != null and bone.visible)

	func set_shown(on: bool) -> void:
		super.set_shown(on)
		if bird != null:
			bird.visible = on


# ---- 14 · the alphorn at sunrise - and the cows come running from all over the pasture ----------------------------------------
class Alphorn extends Vig:
	var man
	var cows: Array = []            # [actor, pasture point, listening point]
	var horn: Node3D
	var played := 0
	const MELODY := [[0.0, 1.1, 348.0, 348.0, 1.0], [1.1, 0.9, 435.0, 435.0, 1.0], [2.0, 1.4, 522.0, 522.0, 1.0], [3.4, 0.7, 609.0, 609.0, 0.8],
			[4.1, 1.6, 522.0, 522.0, 1.0], [5.7, 0.9, 435.0, 435.0, 0.9], [6.6, 1.0, 522.0, 522.0, 1.0], [7.6, 2.4, 348.0, 345.0, 1.0]]

	func build() -> void:
		id = "alphorn"
		c = ew.G(95.0, 60.0)

	func when_ok() -> bool:
		var h: float = ew.hour()
		var el: float = ew.m.sun_el()
		return ew.alp_season() and h > 4.5 and h < 9.5 and el > -5.0

	func live() -> void:
		var look := c + Vector3(1.0, 0, 0.15)
		man = ew.actor("person", c, look, 1.0, Color(0.15, 0.25, 0.5))       # the Senn in his blue «Chutteli»
		actors.append(man)
		horn = ew.node(man, Vector3(0, 1.42, -0.18))
		var wood := Color(0.55, 0.38, 0.2)
		# Alphorn: 3,4 m (in Fis), Fichtenholz mit Peddigrohr umwickelt; der Becher liegt auf dem Boden
		var bas := Basis(Vector3.RIGHT, deg_to_rad(-66.0))
		var segs := [[0.012, 0.016, 1.0, 0.5], [0.016, 0.025, 1.1, 1.55], [0.025, 0.045, 1.0, 2.6]]
		for sg in segs:
			ew.part(horn, ew.cylm(float(sg[0]), float(sg[1]), float(sg[2]), 8), bas * Vector3(0, -float(sg[3]), 0), wood, "tree", bas.get_euler())
		ew.part(horn, ew.cylm(0.06, 0.16, 0.42, 12), bas * Vector3(0, -3.25, 0) + Vector3(0, 0.12, -0.12), wood.darkened(0.1), "tree", Vector3(PI / 2 - 0.15, 0, 0))
		for k in [0.6, 1.2, 1.8, 2.4]:
			ew.part(horn, ew.cylm(0.03, 0.03, 0.03, 8), bas * Vector3(0, -k, 0), Color(0.15, 0.1, 0.08), "tree", bas.get_euler())
		var n := 4 if ew.lite else 6
		for i in range(n):
			var a := -0.9 + 1.8 * i / maxf(1.0, n - 1.0)
			var lp := c + Vector3(cos(a) * 6.5, 0, sin(a) * 6.5)
			var pp := c + Vector3(30.0 + randf_range(0, 25), 0, randf_range(-28, 28))
			pp.y = ew.bt.H(pp.x, pp.z)
			lp.y = ew.bt.H(lp.x, lp.z)
			# Kuh (Braunvieh / Simmentaler): Fell-Oberfläche ≈ 32 °C (actor.gd); Glocke um den Hals
			var cw: Node3D = ew.actor("cow", pp, pp + Vector3(randf_range(-1, 1), 0, 1), 0.6)
			actors.append(cw)
			cows.append([cw, pp, lp])
		go("wait")

	func _cows_graze(dt: float) -> void:
		for e in cows:
			if ew.walk(e[0], e[1], 0.4, dt, null, 2.0):
				ew.idle(e[0], "graze", 4.0)

	func tick(dt: float) -> void:
		ew.face(man, Vector3(1.0, 0, 0.15))
		match st:
			"wait":
				horn.rotation.x = 0.0
				_cows_graze(dt)
				if st_t > (10.0 if played == 0 else 40.0):
					ew.sound(c + Vector3(1.5, 0.6, 0), "horn", MELODY, 2.0, -4.0)
					played += 1
					go("play")
			"play":                                         # he plays (sways a little); the cows lift their heads ... and run
				horn.rotation.x = 0.02 * sin(st_t * 1.3)
				man.rotation.z = 0.02 * sin(st_t * 0.9)
				for i in range(cows.size()):
					var e: Array = cows[i]
					var a = e[0]
					if st_t < 1.8 + i * 0.3:
						ew.idle(a, "graze", 2.0)
						ew.stop(a, dt)
					elif st_t < 3.0 + i * 0.4:
						ew.idle(a, "look", 2.0)
						ew.turn_to(a, c - ew.ppos(a), dt, 2.0)
						ew.stop(a, dt)
					else:
						ew.idle(a, "")
						if ew.walk(a, e[2], 2.4 + 0.3 * (i % 2), dt, null, 2.5):
							ew.turn_to(a, c - ew.ppos(a), dt, 2.0)
				if st_t > 10.5:
					go("listen")
			"listen":                                       # they stand in a half circle and look at him
				man.rotation.z = 0.0
				for e in cows:
					if ew.walk(e[0], e[2], 0.8, dt, null, 2.5):
						ew.turn_to(e[0], c - ew.ppos(e[0]), dt, 2.0)
						ew.idle(e[0], "stare", 2.0) if false else ew.idle(e[0], "")
				if st_t > 8.0:
					go("drift")
			"drift":                                        # slowly back to the grass
				_cows_graze(dt)
				if st_t > 20.0:
					go("wait")

	func gathering() -> bool:
		return st in ["play", "listen"] and st_t > 2.0


# ---- 15 · the shooting-star place on the ridge: in clear nights many more shooting stars than elsewhere --------------------------
class Sternschnuppen extends Vig:
	var streaks: Array = []         # [mesh, material, from, to, t0, length]
	var next := 3.0
	var last := -100.0
	var count := 0

	func build() -> void:
		id = "sternschnuppen"
		c = ew.G(-640.0, 80.0)
		# a flat stone to lie on - K3 (Kontaktbogen: «block floats at the slope»): it lies along the slope, a little sunk in
		var hx: float = ew.bt.H(c.x + 1.0, c.z) - ew.bt.H(c.x - 1.0, c.z)
		var hz: float = ew.bt.H(c.x, c.z + 1.0) - ew.bt.H(c.x, c.z - 1.0)
		var nrm := Vector3(-hx, 2.0, -hz).normalized()
		var bs := Basis(Quaternion(Vector3.UP, nrm)) * Basis(Vector3.UP, 0.3).scaled(Vector3(1.9, 0.25, 1.0))
		ew.mb.parts_of("boulder", Transform3D(bs, c + Vector3(0, -0.18, 0)), {"r": 1.0, "v": 2})

	func when_ok() -> bool:
		return ew.dark() and ew.weather() == "clear"

	func live() -> void:
		for i in range(2 if ew.lite else 3):
			var mt: StandardMaterial3D = ew.glow_mat(Color(0.95, 0.97, 1.0), 4.0, 0.0)
			mt.no_depth_test = false
			var mi: MeshInstance3D = ew.light_part(ew, ew.boxm(0.5, 0.5, 30.0), Vector3.ZERO, mt)
			mi.visible = false
			mi.extra_cull_margin = 200.0
			streaks.append([mi, mt, Vector3.ZERO, Vector3.ZERO, -1.0, 0.7])
		go("watch")

	func _launch(e: Array) -> void:
		var cw: Vector3 = ew.W(c)
		var az := randf() * TAU
		var el := deg_to_rad(randf_range(35.0, 65.0))
		var dirv := Vector3(sin(az) * cos(el), sin(el), -cos(az) * cos(el))
		var p0 := cw + dirv * 380.0
		var tang := dirv.cross(Vector3.UP).normalized() * (1.0 if randf() < 0.5 else -1.0) + Vector3(0, -0.45, 0)
		e[2] = p0
		e[3] = p0 + tang.normalized() * randf_range(70.0, 120.0)
		e[4] = t
		e[5] = randf_range(0.5, 0.9)
		e[0].visible = true
		last = t
		count += 1

	func tick(_dt: float) -> void:
		if t > next:
			next = t + (randf_range(10.0, 25.0) if ew.lite else randf_range(5.0, 14.0))
			for e in streaks:
				if float(e[4]) < 0.0:
					_launch(e)
					break
		for e in streaks:
			if float(e[4]) < 0.0:
				continue
			var k := (t - float(e[4])) / float(e[5])
			if k >= 1.0:
				e[4] = -1.0
				e[0].visible = false
				continue
			var a: Vector3 = e[2]
			var b: Vector3 = e[3]
			var p := a.lerp(b, k)
			var mi: MeshInstance3D = e[0]
			mi.global_transform = Transform3D(Basis.looking_at((b - a).normalized(), Vector3.UP), p)
			mi.scale = Vector3(1.0, 1.0, 0.4 + 1.2 * sin(k * PI))
			(e[1] as StandardMaterial3D).albedo_color.a = sin(k * PI)

	func seen_now() -> bool:
		return t - last < 2.5 and shown

	func on_hide() -> void:
		for e in streaks:
			e[4] = -1.0
			e[0].visible = false


# ---- 16 · a bottle with a message in the Gumpisee - the riddle leads to an old lantern in the glacier crevasse -------------------
class Flaschenpost extends Vig:
	var bottle: Node3D
	var water := 0.0
	var ice := false
	var lan: Vig                    # the lantern part (its own place far away)

	func build() -> void:
		id = "flaschenpost_laterne"
		var lk: Array = ew.bt.LAKE1
		var cen: Vector2 = lk[0]
		var q := Vector2(-20.0, -335.0)
		var e: float = ew.bt._ell(q, lk)
		var p := cen + (q - cen) * (0.93 / sqrt(maxf(0.05, e)))   # near the shore (inside the lake)
		water = ew.bt.level_of(lk)
		ice = ew.season == "winter"
		c = Vector3(p.x, water, p.y)

	func live() -> void:
		bottle = ew.node(vroot, c)
		var gl := StandardMaterial3D.new()
		gl.albedo_color = Color(0.25, 0.5, 0.3, 0.55)
		gl.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		gl.roughness = 0.1
		var body := MeshInstance3D.new()
		body.mesh = ew.cylm(0.04, 0.04, 0.2, 10)
		body.material_override = gl
		body.rotation = Vector3(0, 0, PI / 2 - 0.25)
		bottle.add_child(body)
		var neck := MeshInstance3D.new()
		neck.mesh = ew.cylm(0.015, 0.035, 0.08, 8)
		neck.material_override = gl
		neck.position = Vector3(0.13, 0.03, 0)
		neck.rotation = Vector3(0, 0, -PI / 2 - 0.25)
		bottle.add_child(neck)
		ew.part(bottle, ew.cylm(0.016, 0.016, 0.03, 6), Vector3(0.18, 0.045, 0), Color(0.6, 0.45, 0.3), "tree", Vector3(0, 0, -PI / 2 - 0.25))
		ew.part(bottle, ew.cylm(0.022, 0.022, 0.15, 6), Vector3(0, 0, 0), Color(0.92, 0.88, 0.75), "tent", Vector3(0, 0, PI / 2 - 0.25))   # the rolled note
		go("float")

	func tick(_dt: float) -> void:
		if ice:                                           # frozen into the ice
			bottle.position = c + Vector3(0, 0.04, 0)
			bottle.rotation = Vector3(0, 0.6, 0.15)
			return
		bottle.position = c + Vector3(0.6 * sin(t * 0.05), 0.012 + 0.012 * sin(t * 1.7), 0.5 * cos(t * 0.04))
		bottle.rotation = Vector3(0.12 * sin(t * 1.3), t * 0.03, 0.1 * sin(t * 1.1 + 0.5))


class Laterne extends Vig:
	var glowm: StandardMaterial3D
	var light: OmniLight3D

	func build() -> void:
		id = "laterne"
		c = ew.G(760.0, 460.0, -0.35)                    # bergtal.gd puts the old lantern here (lantern_old)

	func when_ok() -> bool:
		return ew.dark()

	func live() -> void:
		glowm = ew.glow_mat(Color(1.0, 0.75, 0.35), 2.5)
		ew.light_part(vroot, ew.sphm(0.05), c + Vector3(0, 0.14, 0), glowm)
		var hot: MeshInstance3D = ew.part(vroot, ew.sphm(0.04), c + Vector3(0, 0.14, 0), Color(1.0, 0.8, 0.4), 55.0)   # a candle inside: warm
		hot.visible = false                                # (only the thermal twin)
		light = ew.lamp(vroot, c + Vector3(0, 0.4, 0), Color(1.0, 0.72, 0.4), 0.9, 6.0)
		go("glow")

	func tick(_dt: float) -> void:
		var f := 0.75 + 0.15 * sin(t * 9.0) + 0.1 * sin(t * 23.0)
		glowm.emission_energy_multiplier = 2.5 * f
		if light != null:
			light.light_energy = 0.9 * f


# ---- 17 · marmot football: three marmots push a lost tennis ball - until it rolls into a burrow ----------------------------------
class Fussball extends Vig:
	var pl: Array = []              # actors
	var ball: Node3D
	var bp := Vector3.ZERO          # ball (valley)
	var bv := Vector3.ZERO
	var kicker := -1
	var target := 0
	var kicks := 0
	var hole_a := Vector3.ZERO      # the burrow the ball falls into
	var hole_b := Vector3.ZERO      # ... and comes out of
	var young
	const R := 0.034

	func build() -> void:
		id = "murmeltier_fussball"
		c = ew.G(-60.0, 232.0)
		hole_a = ew.G(-62.0, 240.0)                       # a burrow of bergtal.gd
		hole_b = ew.G(-53.0, 227.0)
		ew.mb.add("burrow", hole_b, 0.0)
		for gz in [229.0, 231.2]:                         # two stones: the goal
			ew.mb.add("boulder", ew.G(-56.0, gz, -0.08), 0.0, {"r": 0.16, "v": 1, "noob": true})

	func when_ok() -> bool:
		return ew.season != "winter" and not ew.dark()

	func live() -> void:
		for i in range(3):
			var p := c + Vector3(randf_range(-3, 3), 0, randf_range(-3, 3))
			var a: Node3D = ew.marmot(ew.G(p.x, p.z), c)
			actors.append(a)
			pl.append(a)
		young = ew.marmot(hole_b, c, 0.62)
		actors.append(young)
		young.visible = false
		ball = ew.node(vroot, Vector3.ZERO)
		ew.part(ball, ew.sphm(R, -1, 10), Vector3.ZERO, Color(0.85, 0.92, 0.2), "tent")   # Tennisball (bleibt luftwarm)
		ew.part(ball, ew.boxm(0.07, 0.004, 0.012), Vector3(0, 0.0, 0), Color(0.95, 0.95, 0.95), "tent", Vector3(0, 0, 0.5))
		bp = Vector3(c.x + 0.5, 0, c.z - 0.3)
		go("chase")

	func _ball(dt: float) -> void:
		bv *= exp(-1.1 * dt)
		bp += bv * dt
		var d := Vector2(bp.x - c.x, bp.z - c.z)
		if d.length() > 7.0 and st != "to_hole":            # stays on the little field (bounces off the grass tufts)
			var nn := d.normalized()
			bp = Vector3(c.x + nn.x * 7.0, 0, c.z + nn.y * 7.0)
			var vv := Vector2(bv.x, bv.z)
			vv = vv - 2.0 * vv.dot(nn) * nn
			bv = Vector3(vv.x, 0, vv.y) * 0.6
		ball.position = Vector3(bp.x, ew.bt.H(bp.x, bp.z) + R, bp.z)
		var sp := Vector2(bv.x, bv.z).length()
		if sp > 0.01:
			ball.rotate(Vector3(bv.z, 0, -bv.x).normalized(), sp * dt / R)

	func tick(dt: float) -> void:
		match st:
			"chase":                                        # the nearest one runs behind the ball
				ball.visible = true
				_ball(dt)
				if kicker < 0 or Vector2(bv.x, bv.z).length() < 0.06:
					var best := 0
					var bd := INF
					for i in range(pl.size()):
						if i == kicker:
							continue
						var dd: float = ew.ppos(pl[i]).distance_to(bp)
						if dd < bd:
							bd = dd
							best = i
					kicker = best
					target = (best + 1 + (randi() % 2)) % pl.size()
					go("run")
				for i in range(pl.size()):
					if i != kicker:
						ew.idle(pl[i], "sit_up" if randf() < 0.01 else pl[i].idle_kind)
			"run":
				_ball(dt)
				var a = pl[kicker]
				var aim := _aim()
				var behind := bp - aim * 0.32
				ew.idle(a, "")
				if ew.walk(a, behind, 1.6, dt, null, 8.0):
					go("kick")
				for i in range(pl.size()):
					if i != kicker:
						ew.turn_to(pl[i], bp - ew.ppos(pl[i]), dt, 3.0)
			"kick":                                         # a push with the nose
				_ball(dt)
				var a2 = pl[kicker]
				ew.turn_to(a2, _aim(), dt, 8.0)
				if a2.head != null:
					a2.head.rotation.x = -0.5 * sin(clampf(st_t / 0.35, 0.0, 1.0) * PI)
				if st_t > 0.35:
					kicks += 1
					if kicks % 6 == 0:
						bv = (hole_a - bp).normalized() * 2.4 * Vector3(1, 0, 1)
						go("to_hole")
					else:
						bv = _aim() * randf_range(1.4, 2.4)
						go("chase")
			"to_hole":                                      # ... straight into the burrow
				_ball(dt)
				for i in range(pl.size()):
					ew.turn_to(pl[i], bp - ew.ppos(pl[i]), dt, 3.0)
				if Vector2(bp.x - hole_a.x, bp.z - hole_a.z).length() < 0.45:
					ball.visible = false
					bv = Vector3.ZERO
					go("stare")
				elif st_t > 6.0:
					go("chase")
			"stare":                                        # all three stare at the hole
				for i in range(pl.size()):
					ew.stop(pl[i], dt)
					ew.turn_to(pl[i], hole_a - ew.ppos(pl[i]), dt, 3.0)
					ew.idle(pl[i], "sit_up")
				if st_t > 3.0:
					go("pop")
			"pop":                                          # out of the other burrow: the ball - and a young marmot behind it
				var k := clampf(st_t / 0.5, 0.0, 1.0)
				ball.visible = true
				bp = Vector3(hole_b.x, 0, hole_b.z + 0.3 * k)
				ball.position = Vector3(bp.x, ew.bt.H(bp.x, bp.z) + R + 0.4 * sin(k * PI), bp.z)
				young.visible = st_t > 0.4 and st_t < 3.5
				ew.place(young, hole_b + Vector3(0, -0.22, 0), true)
				ew.idle(young, "sit_up")
				for i in range(pl.size()):
					ew.turn_to(pl[i], hole_b - ew.ppos(pl[i]), dt, 4.0)
				if st_t > 3.6:
					young.visible = false
					for i in range(pl.size()):
						ew.idle(pl[i], "")
					bv = (c - bp).normalized() * 1.2 * Vector3(1, 0, 1)
					kicker = -1
					go("chase")

	func _aim() -> Vector3:
		var tp: Vector3 = ew.ppos(pl[target])
		var d := (tp - bp) * Vector3(1, 0, 1)
		return d.normalized() if d.length() > 0.1 else Vector3(1, 0, 0)

	func playing() -> bool:
		return st in ["run", "kick", "chase", "to_hole", "stare", "pop"]


# =============================================================================================================================
# ---- the discovery book (entdecken.gd) -----------------------------------------------------------------------------------------
# =============================================================================================================================
func _reg(e, id: String, title: String, short: String, hint: String, icon: String, kind: String, pos: Vector3, size: Vector3, radius: float,
		when = "any", extra := {}) -> void:
	var inf := {"scene": SCENE, "title": title, "short_text": short, "hint": hint, "icon": icon, "kind": kind,
			"position": pos, "size": size, "radius": radius, "when": when}
	inf.merge(extra, true)
	e.register(id, inf)


func _register() -> void:
	var e = ent()
	if e == null:
		return
	var V: Dictionary = by_id
	var sp: Spaet = V["murmeltier_zu_spaet"]
	_reg(e, "berg.murmeltier_zu_spaet", T.t("Das Murmeltier, das zu spät kommt"),
			T.t("Der Wächter pfeift, alle verschwinden im Bau – nur das dicke frisst weiter. Es rennt erst los, als die anderen schon wieder herausschauen."),
			T.t("Unter der Blumenmatte frisst einer immer weiter, wenn die anderen pfeifen …"), "🐿", "tier", W(sp.c) + Vector3(0, 0.4, 0), Vector3(12, 1.2, 12), 25.0,
			"day", {"active": func(): return sp.shown and sp.st in ["flee", "squeeze"] and sp.season_ok()})
	var ks: KuhSocke = V["kuh_socke"]
	_reg(e, "berg.kuh_socke", T.t("Die Sockendiebin"),
			T.t("Eine Kuh leckt am Zelt, holt sich die Socke vom Rucksack und schaut MoveEye an – mit der Socke im Maul. Fotografiert mit MoveEyes Kamera."),
			T.t("Bei der Alp Tschuggen übernachten und die Socke auf dem Rucksack im Auge behalten – ein Foto mit MoveEyes Kamera!"), "🐄", "tier",
			Vector3(0, 1.0, 0), Vector3(1.2, 1.7, 2.6), 30.0, "day",
			{"node": null, "photo_required": true, "active": func(): return ks.shown and ks.has_sock() and ks.cow != null,
			"position": Vector3(0, 1.0, 0)})
	var dh: Dohlen = V["dohlen_sandwich"]
	_reg(e, "berg.dohlen_sandwich", T.t("Streit um das Sandwich"),
			T.t("Zwei Alpendohlen zerren am Sandwich des Wanderers – die dritte nimmt es mit, während die zwei noch streiten."),
			T.t("Auf dem Furggapass macht jemand Mittagspause. Ob das Sandwich lange liegen bleibt?"), "🐦", "tier", W(dh.c) + Vector3(0, 0.6, 0), Vector3(3, 1.6, 3), 18.0,
			"day", {"active": func(): return dh.shown and dh.stolen()})
	var sb: Steinbock = V["steinbock_kante"]
	_reg(e, "berg.steinbock_kante", T.t("Steinbock auf dem Felsturm"),
			T.t("Ganz oben auf einem Felsturm, kaum grösser als er selbst: er kratzt sich mit dem Horn den Rücken und legt sich an die Kante."),
			T.t("Beim Klettersteig steht ein Felsturm. Ganz oben steht jemand, der keine Höhenangst kennt."), "🐐", "tier",
			W(sb.top) + Vector3(0, 0.6, 0), Vector3(1.6, 1.4, 1.6), 30.0, "any", {"active": func(): return sb.shown})
	var sf: Schafstau = V["schafstau_pass"]
	_reg(e, "berg.schafstau_pass", T.t("Schafstau auf der Passstrasse"),
			T.t("Die Schafe liegen auf der warmen Strasse. Das Auto wartet, kriecht, hupt – und eines legt sich genau vor die Stossstange."),
			T.t("In den Furggakehren ist die Strasse manchmal ganz voll. Nicht mit Autos."), "🐑", "tier", W(sf.c) + Vector3(0, 0.6, 0), Vector3(14, 2, 14), 30.0,
			"day", {"active": func(): return sf.shown and sf.jam()})
	var kr: Kreis = V["wanderer_kreis"]
	_reg(e, "berg.wanderer_kreis", T.t("Der Wanderer im Kreis"),
			T.t("Er liest den Wegweiser, dreht die Karte, läuft eine Runde um den Wegweiser – und liest ihn wieder."),
			T.t("Beim Wegweiser im Murmelboden ist jemand schon lange unterwegs – aber nicht weit."), "🧭", "mensch", W(kr.c) + Vector3(0, 1.0, 0), Vector3(12, 2, 12), 25.0,
			"day", {"active": func(): return kr.shown and kr.lost()})
	var gb: Gipfelbuch = V["gipfelbuch"]
	_reg(e, "berg.gipfelbuch", T.t("Das Gipfelbuch"),
			T.t("Auf dem Tschingelspitz blättert der Wind im Gipfelbuch. Jede Seite ein Eintrag – manche kennen die Tiere des Tals."),
			T.t("Auf dem Tschingelspitz liegt beim Kreuz ein Buch. Wer hat sich da eingetragen?"), "📖", "ort", W(gb.c) + Vector3(0, 0.5, 0), Vector3(0.6, 0.4, 0.6), 4.0)
	var fd: Fondue = V["fondue_fuchs"]
	_reg(e, "berg.fondue_fuchs", T.t("Der Fondue-Fuchs"),
			T.t("Jemand hat sein Fondue vergessen – das Rechaud brennt noch. Nachts zieht der Fuchs einen langen Käsefaden aus dem Caquelon. Im Wärmebild leuchtet der Brenner."),
			T.t("Am Fondueplätzli am Gumpisee riecht es nachts nach Käse …"), "🧀", "tier", W(fd.c) + Vector3(0, 0.3, 0), Vector3(2, 1, 2), 14.0, "night",
			{"active": func(): return fd.shown and fd.eating()})
	var ec: Echo = V["echo_schlucht"]
	_reg(e, "berg.echo_schlucht", T.t("Das Echo im Tüfelsschlund"),
			T.t("Auf der Hängebrücke ruft jemand in die Schlucht. Das Echo antwortet dreimal – und einmal muht es."),
			T.t("Auf der Hängebrücke über den Tüfelsschlund ruft jemand. Gut zuhören!"), "📣", "mensch", W(ec.mid) + Vector3(0, 1.0, 0), Vector3(4, 2, 4), 22.0,
			"day", {"active": func(): return ec.shown and ec.calling(), "los": false})
	var kh: Kristall = V["kristallhoehle"]
	_reg(e, "berg.kristallhoehle", T.t("Die Kristallhöhle"),
			T.t("Im Herbst führt der Wasserfall wenig Wasser – dahinter öffnet sich eine kleine Höhle voller Bergkristalle. Ein Strahler hat seinen Hammer vergessen."),
			T.t("Im Herbst, wenn der Wasserfall im Tüfelsschlund schmal ist, lohnt sich ein Blick dahinter."), "💎", "ort", W(kh.c) + Vector3(0, 0.9, 0), Vector3(1.4, 1.8, 1.0), 7.0,
			"any", {"active": func(): return kh.when_ok()})
	var bu: Buero = V["bunker_buero"]
	_reg(e, "berg.bunker_buero", T.t("Das Murmeltier-Büro"),
			T.t("Nachts steht die Bunkertür im Fort Chrüzli offen: ein Murmeltier am Pult, Lampe, Stempel, Akten. Kommt man näher – Licht aus, Tür zu."),
			T.t("Am Fort Chrüzli brennt nachts manchmal Licht. Von weitem schauen, nicht zu nahe gehen!"), "🗂", "tier", W(bu.c) + Vector3(0, 0.6, 0), Vector3(1.4, 1.6, 1.4), 25.0,
			"night", {"active": func(): return bu.shown and bu.working()})
	var yt: Yeti = V["yeti_spuren"]
	_reg(e, "berg.yeti_spuren", T.t("Yeti-Spuren"),
			T.t("Riesige Spuren im Schnee – sie enden bei einem Schneemann mit echten Wanderschuhen. Schaut man weg, dreht er den Kopf."),
			T.t("Im Winter führen unter dem Wyssgletscher seltsame Spuren durch den Schnee."), "❄", "szene", W(yt.c) + Vector3(0, 1.0, 0), Vector3(1.2, 2.0, 1.2), 9.0,
			"any", {"active": func(): return yt.when_ok()})
	var bg: Bartgeier = V["bartgeier_knochen"]
	_reg(e, "berg.bartgeier_knochen", T.t("Der Knochen vom Himmel"),
			T.t("Der Bartgeier lässt seinen Knochen auf die Felsplatte fallen, damit er zerbricht – genau neben dem Wanderer, der gerade isst."),
			T.t("Am Höhenweg West rastet ein Wanderer bei einer Felsplatte. Über ihm kreist etwas Grosses."), "🦅", "tier", W(bg.slab) + Vector3(0, 1.0, 0), Vector3(5, 3, 5), 30.0,
			"day", {"active": func(): return bg.shown and bg.dropped(), "los": true})
	var ah: Alphorn = V["alphorn"]
	_reg(e, "berg.alphorn", T.t("Alphorn bei Sonnenaufgang"),
			T.t("Der Senn bläst bei Sonnenaufgang das Alphorn – und die Kühe kommen von der ganzen Weide angerannt und hören zu. Fotografiert mit MoveEyes Kamera."),
			T.t("Am frühen Morgen bei der Alp Tschuggen übernachten: wenn das Alphorn klingt, ein Foto mit MoveEyes Kamera!"), "🎺", "mensch",
			W(ah.c) + Vector3(0, 1.0, 0), Vector3(12, 2.2, 12), 90.0, "morning", {"photo_required": true, "active": func(): return ah.shown and ah.gathering()})
	var ss: Sternschnuppen = V["sternschnuppen"]
	_reg(e, "berg.sternschnuppen", T.t("Sternschnuppen-Platz"),
			T.t("Auf dem flachen Stein am Grat sieht man in klaren Nächten viel mehr Sternschnuppen als unten im Tal."),
			T.t("In einer klaren Nacht auf dem Grat beim Gratspitz liegt ein flacher Stein. Hinlegen und nach oben schauen."), "🌠", "ort",
			W(ss.c) + Vector3(0, 0.4, 0), Vector3(2.4, 0.8, 1.6), 10.0, "night", {"active": func(): return ss.seen_now(), "los": false})
	var fp: Flaschenpost = V["flaschenpost_laterne"]
	_reg(e, "berg.flaschenpost", T.t("Flaschenpost im Gumpisee"),
			T.t("In der Flasche steckt ein Zettel: «Wo der Gletscher die Ski behält und die Spalte blau schimmert, brennt nachts ein altes Licht.»"),
			T.t("Am Ostufer des Gumpisees schaukelt etwas Grünes im Wasser."), "🍾", "ort", Vector3.ZERO, Vector3(0.4, 0.3, 0.4), 8.0, "any",
			{"position": W(fp.c) + Vector3(0, 0.05, 0)})
	var la: Laterne = V["laterne"]
	_reg(e, "berg.laterne", T.t("Die Laterne in der Gletscherspalte"),
			T.t("Das Rätsel der Flaschenpost stimmt: in einer Spalte des Wyssgletschers brennt nachts eine alte Laterne. Wer sie wohl jeden Abend anzündet?"),
			T.t("Die Flaschenpost spricht vom Gletscher: nachts beim Wyssgletscher nach einem Licht in den Spalten suchen."), "🏮", "ort",
			W(la.c) + Vector3(0, 0.2, 0), Vector3(0.5, 0.6, 0.5), 10.0, "night", {"active": func(): return e.is_found("berg.flaschenpost"), "los": false})
	var fb: Fussball = V["murmeltier_fussball"]
	_reg(e, "berg.murmeltier_fussball", T.t("Murmeltier-Fussball"),
			T.t("Drei Murmeltiere schieben einen verlorenen Tennisball hin und her. Rollt er in den Bau, kommt er beim anderen Loch wieder heraus – mit einem Jungen dahinter."),
			T.t("Unter der Blumenmatte liegt ein gelber Ball – und er bleibt nicht lange liegen."), "🎾", "tier", W(fb.c) + Vector3(0, 0.3, 0), Vector3(10, 1, 10), 20.0,
			"day", {"active": func(): return fb.shown and fb.playing()})
	if not e.found.is_connected(_on_found):
		e.found.connect(_on_found)


func _on_found(id: String) -> void:
	if id == "berg.flaschenpost" and is_inside_tree():
		var e = ent()
		if e != null:
			e.call_deferred("show_hint", "berg.laterne")         # the riddle: Blinki tells where the light is


func _exit_tree() -> void:
	var e = ent()
	if e != null and e.found.is_connected(_on_found):
		e.found.disconnect(_on_found)


# =============================================================================================================================
# ---- control {"action": "bergtal", "do": "erleben", "what": …} -------------------------------------------------------------
# =============================================================================================================================
func control(d: Dictionary) -> Dictionary:
	var id := str(d.get("id", ""))
	match str(d.get("what", "info")):
		"where":                                         # where a vignette is (world, valley), for tests and quick travel
			if not by_id.has(id):
				return {"ok": false, "error": "unknown", "ids": by_id.keys()}
			var v = by_id[id]
			var w: Vector3 = v.where()
			return {"ok": true, "pos": [snappedf(w.x, 0.01), snappedf(w.y, 0.01), snappedf(w.z, 0.01)], "tal": [snappedf(v.c.x, 0.1), snappedf(v.c.y, 0.1), snappedf(v.c.z, 0.1)]}
		"go":                                            # the view flies to the vignette (tests, screenshots)
			if not by_id.has(id):
				return {"ok": false, "error": "unknown", "ids": by_id.keys()}
			var gw: Vector3 = by_id[id].where()
			m.fly_to(gw + Vector3(0, 1.0, 0), float(d.get("dist", 9.0)))
			return {"ok": true, "pos": [snappedf(gw.x, 0.01), snappedf(gw.y, 0.01), snappedf(gw.z, 0.01)]}
		"state":                                         # tests: jump a vignette to a state (and hold it)
			if by_id.has(id):
				if d.has("state"):
					by_id[id].go(str(d.get("state", "")))
				if d.has("t"):
					by_id[id].st_t = float(d["t"])
				by_id[id].hold = bool(d.get("hold", false))
				return {"ok": true, "info": by_id[id].info()}
			return {"ok": false, "error": "unknown", "ids": by_id.keys()}
	var out := []
	for v in vigs:
		out.append(v.info())
	return {"ok": true, "file": "a", "vignettes": out, "stats": stats, "lite": lite, "season": season}
