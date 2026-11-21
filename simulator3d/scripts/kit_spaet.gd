extends Node
## Abenteuer-Kit: läuft nach den Figuren (process_priority 95) – Höhe, Wände, Aktionen, Kamera, Bildschirm (kit_abenteuer.gd spaet()).

var kit
var _t := -1


func _process(dt: float) -> void:
	if kit == null:
		return
	var ts := maxf(Engine.time_scale, 0.01)
	kit.spaet(dt, dt / ts)
