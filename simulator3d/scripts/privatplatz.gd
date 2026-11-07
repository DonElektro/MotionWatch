extends Node
## Privatsphäre am eigenen Platz (Wunsch des Besitzers Nr. 2, 07.11.2026): normale Besucher meiden deinen Platz – den
## bewachten Zeltplatz, wo MoveEye steht (MoveEye + das eigene Zelt, main.obj["pir"], wenn es nahe bei MoveEye steht).
## Ihre Wege gehen mit etwas Abstand um diesen Kreis herum statt mitten durch; liegt ein Ziel darin (eine Stelle «vor
## MoveEye», ein Wegpunkt der Polizei-Runde), wird es an den Rand verschoben. Auf Wegen dürfen sie mit Abstand vorbeigehen.
##
## Wer sich daran hält: Personen, die über main.visit() kommen (von selbst, Besuch-Knöpfe, Vorlagen, Tagesablauf),
## Statisten (statisten.gd) und die Kinder / Jogger des Tagesablaufs (life.gd) – Actor.privat = true.
## Ausnahmen (absichtlich am Platz, AUSNAHMEN unten): Einbrecher, Schleicher, Diebe (sie sind die Eindringlinge),
## eingeladene Gäste (Grillabend), wer heimkommt / ein Paket oder eine Pizza bringt, der Gartenbesuch an der Haustür,
## die Abläufe «Fremder kommt an deinen Platz», Velodieb, Tarnen. Gar nicht betroffen (nie markiert): Tiere, Fahrzeuge,
## Spielfiguren, Tests und Messungen (Testlauf, Prüfstand, Nacht-Testlauf, Erkennungstest-Proben, Einbruch-Abläufe,
## Geschichten und Spiele mit eigenen Figuren) – ihre Wege bleiben genau wie bisher (Zahlen vergleichbar).
## Schalter: Besuch → Verhalten «Besucher meiden deinen Platz (Privatsphäre)» (main.privat_on, Standard an).
## Steuerung: {"action": "privat"} -> Kreis, Abstand, wie viele Besucher sich gerade daran halten.

const R_DEV := 4.0            # m um MoveEye
const PAD_TENT := 2.6         # m um das eigene Zelt
const TENT_MAX := 14.0        # das Zelt gehört zum Platz, wenn es höchstens so weit von MoveEye steht
const MARGIN := 1.5           # so viel Abstand halten die Wege zusätzlich zum Kreis
const LOOK := 8.0             # ab so nahe am Rand wird der Weg um den Kreis gelenkt
const AUSNAHMEN := ["burglar", "sneaker", "thief", "bbq", "homecoming", "parcel", "courier", "garden_person", "platz_besuch",
		"velodieb", "tarn_robben", "tarn_schirm", "tarn_karton", "edge_sneak"]

var main
var ctx := 0                  # > 0: main.spawn() marks the persons it makes (main.visit() sets it)


static func exempt(kind: String) -> bool:
	return kind in AUSNAHMEN


func zone() -> Array:
	"""[centre (x, z), radius] of the private pitch: one circle round MoveEye and its own tent"""
	var hp: Vector3 = main.home_pos
	var d := Vector2(hp.x, hp.z)
	var t3: Vector3 = main.obj.get("pir", Vector3.ZERO)
	var t := Vector2(t3.x, t3.z)
	if t3 != Vector3.ZERO and t.distance_to(d) < TENT_MAX:
		return [(d + t) * 0.5, maxf(R_DEV, d.distance_to(t) * 0.5 + PAD_TENT)]
	return [d, R_DEV]


func mark(v) -> void:
	if v != null and is_instance_valid(v) and str(v.get("kind")) == "person" and str(v.get("variant")) != "burglar":
		v.privat = true


func on_spawn(v) -> void:
	if ctx > 0:
		mark(v)


func _active(v) -> bool:
	return bool(main.privat_on) and not v.controlled and not v.puppet


func steer(v, d: Vector2) -> Vector2:
	"""the direction to walk: d, or round the private circle when the way would cross it"""
	if not _active(v):
		return d
	var z := zone()
	var c: Vector2 = z[0]
	var r: float = float(z[1]) + MARGIN
	_fix_target(v, c, r)
	var p := Vector2(v.position.x, v.position.z)
	var w := c - p
	var dist := w.length()
	if dist < r:                                          # in the band at the edge: along the edge and outwards
		var n := -w / maxf(dist, 0.01)
		var tg := Vector2(-n.y, n.x)
		if tg.dot(d) < 0.0:
			tg = -tg
		var k := clampf((r - dist) / MARGIN, 0.0, 1.0)
		return (tg * (1.0 - 0.5 * k) + n * (0.3 + k)).normalized()
	if dist > r + LOOK or d.length() < 0.01:
		return d
	var dn := d.normalized()
	var along := w.dot(dn)
	var to_t := Vector2(v.target.x - p.x, v.target.z - p.y).length()
	if along <= 0.0 or along - r > to_t:
		return d                                          # the circle is behind, or the target comes before it
	if absf(w.cross(dn)) >= r:
		return d                                          # the way passes beside it
	var base := w / dist
	var a := asin(clampf(r / dist, 0.0, 1.0))
	var t1 := base.rotated(a)
	var t2 := base.rotated(-a)
	return t1 if t1.dot(dn) >= t2.dot(dn) else t2


func hold(v, d: Vector2) -> Vector2:
	"""after the steering round trees and people (main.avoid, statisten.steer, a detour when stuck): close to the circle,
	never towards it - the part of d that points inwards is taken away (the visitor slides along the edge)"""
	if not _active(v):
		return d
	var z := zone()
	var c: Vector2 = z[0]
	var r: float = float(z[1]) + MARGIN * 0.7
	var w := c - Vector2(v.position.x, v.position.z)
	var dist := w.length()
	if dist >= r or dist < 0.01:
		return d
	var inn := w / dist
	var k := d.dot(inn)
	if k <= 0.0:
		return d
	var out := d - inn * k * 1.15
	if out.length() < 0.05:
		out = Vector2(-inn.y, inn.x)
	return out.normalized()


func _fix_target(v, c: Vector2, r: float) -> void:
	var tq := Vector2(v.target.x, v.target.z)
	if tq.distance_to(c) >= r - 0.3:
		return
	var n := tq - c
	if n.length() < 0.2:
		n = Vector2(v.position.x, v.position.z) - c
	n = n.normalized() if n.length() > 0.01 else Vector2(1, 0)
	var q := c + n * (r + 0.2)
	v.target = Vector3(q.x, v.target.y, q.y)


func keep(v, pos: Vector3) -> Vector3:
	"""never inside the circle itself (only the band of MARGIN round it can be walked on, at the edge)"""
	if not _active(v):
		return pos
	var z := zone()
	var c: Vector2 = z[0]
	var r: float = float(z[1])
	var p := Vector2(pos.x, pos.z)
	var dv := p - c
	if dv.length() >= r:
		return pos
	var n := dv.normalized() if dv.length() > 0.01 else Vector2(1, 0)
	var q := c + n * r
	return Vector3(q.x, pos.y, q.y)


func control(_d: Dictionary) -> Dictionary:
	var z := zone()
	var n := 0
	var inside := 0
	for v in main.visitors.get_children():
		if bool(v.get("privat")):
			n += 1
			if Vector2(v.position.x, v.position.z).distance_to(z[0]) < float(z[1]):
				inside += 1
	return {"ok": true, "on": bool(main.privat_on), "centre": [snappedf(z[0].x, 0.01), snappedf(z[0].y, 0.01)],
			"radius": snappedf(float(z[1]), 0.01), "margin": MARGIN, "visitors": n, "inside": inside, "ausnahmen": AUSNAHMEN}
