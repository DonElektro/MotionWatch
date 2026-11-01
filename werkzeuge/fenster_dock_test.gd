extends SceneTree
## Test ohne Bild für das Paket «Andocken» (fenster.gd, pack()): die Fenster in den Leisten links / rechts bei
## 1280×720, 1920×1080 und 2560×1440 - keine Überlappung, alles im Bild, Werkzeugleiste unten und Knopf «Bedienfeld
## zeigen» frei. Die Grössen sind die echten Fenster bei Massstab 1 (Rahmen + Bild × Massstab); der Massstab wird wie im
## Simulator verkleinert, bis alles passt (fenster.gd _dock_tick).
##   cd simulator3d && <godot> --headless --path . -s "$PWD/../werkzeuge/fenster_dock_test.gd"   (absoluter Pfad nötig)
## Ende: «Andocktest OK» oder «SCRIPT ERROR: Andocktest: …» (Exit-Code 0 / 1).

var errs := []

# id -> [Leiste, Reihenfolge, unten, Rahmen, Bild bei Massstab 1 (0 = fest)]
const WINS := {
	"tabs": ["L", 0, false, Vector2(10, 24), Vector2(220, 220)],      # Seitenfenster mit Reitern (Karte gezeigt)
	"live": ["L", 10, false, Vector2(10, 26), Vector2(260, 146)],
	"kopf": ["L", 20, false, Vector2(12, 96), Vector2(320, 180)],
	"blinki": ["L", 90, true, Vector2(270, 70), Vector2.ZERO],
	"kameras": ["R", 0, false, Vector2(12, 26), Vector2(330, 380)],
	"geraet": ["R", 10, false, Vector2(10, 96), Vector2(260, 0)],
	"mover": ["R", 90, true, Vector2(150, 176), Vector2.ZERO],
}


func items(ids: Array, s: float) -> Array:
	var out := []
	for id in ids:
		var e: Array = WINS[id]
		var c: Vector2 = e[4]
		out.append({"id": id, "side": e[0], "i": float(e[1]), "end": e[2], "size": (e[3] as Vector2) + c * s})
	return out


func area(vs: Vector2, panel: bool) -> Dictionary:
	var right := vs.x - 400.0 if panel else vs.x                    # Bedienfeld offen: 400 px rechts
	var obs := [Rect2((right - 520.0) / 2.0, vs.y - 64.0, 520.0, 52.0)]   # Werkzeugleiste unten in der Mitte
	if not panel:
		obs.append(Rect2(vs.x - 48.0, 10.0, 38.0, 38.0))           # Knopf «Bedienfeld zeigen»
	return {"l": 0.0, "r": right, "vs": vs, "obs": obs, "maxcols": 1 if vs.x < 1700.0 else 2}


func check(F, name: String, ids: Array, vs: Vector2, panel: bool) -> void:
	var ar := area(vs, panel)
	var s := clampf(minf(vs.y / 900.0, vs.x / 1500.0), 0.7, 1.6)
	var res: Dictionary = F.pack(items(ids, s), ar)
	while not res["ok"] and s > F.S_MIN + 0.001:
		s = maxf(F.S_MIN, s - 0.1)
		res = F.pack(items(ids, s), ar)
	var rects := {}
	for it in items(ids, s):
		if not res["pos"].has(it["id"]):
			errs.append("%s %s: %s ohne Platz" % [name, vs, it["id"]])
			continue
		rects[it["id"]] = Rect2(res["pos"][it["id"]], it["size"])
	var keys := rects.keys()
	for i in range(keys.size()):
		var a: Rect2 = rects[keys[i]]
		if a.position.x < 0.0 or a.position.y < 0.0 or a.end.x > ar["r"] + 0.5 or a.end.y > vs.y + 0.5:
			errs.append("%s %s: %s ausserhalb %s" % [name, vs, keys[i], a])
		for o in ar["obs"]:
			if a.intersects(o):
				errs.append("%s %s: %s deckt die Leiste / den Knopf %s" % [name, vs, keys[i], o])
		for j in range(i + 1, keys.size()):
			if a.intersects(rects[keys[j]]):
				errs.append("%s %s: %s überlappt %s" % [name, vs, keys[i], keys[j]])
	print("  %s %dx%d%s: Massstab %.2f, passt %s, Spalten L %d / R %d" % [name, vs.x, vs.y, " (Bedienfeld offen)" if panel else "",
			s, res["ok"], res["cols_l"], res["cols_r"]])
	if not res["ok"]:
		errs.append("%s %s: passt auch mit Massstab %.2f nicht" % [name, vs, s])


func _init() -> void:
	var F = load("res://scripts/fenster.gd")
	if F == null:
		errs.append("fenster.gd lädt nicht")
	else:
		var std := ["tabs", "kameras", "geraet", "mover"]
		var alle := ["tabs", "live", "kopf", "blinki", "kameras", "geraet", "mover"]
		for vs in [Vector2(1280, 720), Vector2(1920, 1080), Vector2(2560, 1440)]:
			check(F, "Standard", std, vs, false)
			check(F, "Alle", alle, vs, false)
			check(F, "Bedienfeld", ["tabs", "live", "geraet", "mover"], vs, true)
		# Reihenfolge: die erste Spalte links beginnt oben, Mover rechts unten
		var ar := area(Vector2(1920, 1080), false)
		var r: Dictionary = F.pack(items(["tabs", "kameras", "mover"], 1.0), ar)
		if r["pos"]["tabs"].y > 20.0 or r["pos"]["tabs"].x > 20.0:
			errs.append("Seitenfenster nicht oben links: %s" % r["pos"]["tabs"])
		if r["pos"]["kameras"].y < 48.0:
			errs.append("Kameras unter dem Knopf «Bedienfeld zeigen»: %s" % r["pos"]["kameras"])
		if r["pos"]["mover"].y < 800.0:
			errs.append("Mover nicht unten: %s" % r["pos"]["mover"])
	if errs.is_empty():
		print("Andocktest OK")
		quit(0)
	else:
		for e in errs:
			push_error("Andocktest: " + str(e))
		quit(1)
