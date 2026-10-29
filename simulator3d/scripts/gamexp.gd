extends RefCounted
## 3D-4.x: the level of a player (per name, over all evenings). Experience points (XP) come from the score of a round, the
## badges, the task of the round, the challenge of the day and a right guess as a watcher. Every few levels a small thing
## for the own figure is unlocked (headband, scarf, golden jacket, top hat, cape, crown) - only for the look, never an
## advantage. Kept next to the badges in user://spiel/.

const FILE := "user://spiel/stufen.json"
# [level, id, name] - what the figure gets (look "deco" or the golden jacket)
const UNLOCKS := [[2, "band", "🎽 Stirnband"], [3, "scarf", "🧣 Schal"], [4, "gold", "✨ Goldene Jacke"], [5, "tophat", "🎩 Zylinder"],
		[7, "cape", "🦸 Umhang"], [9, "crown", "👑 Krone"]]
const MAX_LV := 30

var game
var db := {}
var _loaded := false


static func need(lv: int) -> int:
	"""XP needed for this level: 2 = 200, 3 = 500, 4 = 900, 5 = 1400 … (a level is a few rounds more each time)"""
	return 50 * (lv - 1) * (lv + 2)


static func level_of(xp: int) -> int:
	var lv := 1
	while lv < MAX_LV and xp >= need(lv + 1):
		lv += 1
	return lv


static func key(name_: String) -> String:
	return str(name_).strip_edges().to_lower()


static func is_bot(name_: String) -> bool:
	return str(name_).begins_with("Bot ") or str(name_).begins_with("🤖")


func _load() -> void:
	if _loaded:
		return
	_loaded = true
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	db = d if typeof(d) == TYPE_DICTIONARY else {}


func _save() -> void:
	DirAccess.make_dir_recursive_absolute("user://spiel")
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(db))
		f.close()


func known(name_: String) -> bool:
	"""has this name played before (a level, badges, the ranking of the evening or of the week)?"""
	_load()
	var k := key(name_)
	if k == "" or db.has(k):
		return true
	if game != null:
		if game.badges_all().has(k) or game.board.has(k) or game.week.has(k):
			return true
	return false


func info(name_: String) -> Dictionary:
	"""for the phone and the end screen: level, XP, the bar to the next level, what is unlocked and what comes next"""
	_load()
	var e: Dictionary = db.get(key(name_), {})
	var xp := int(e.get("xp", 0))
	var lv := level_of(xp)
	var unl := []
	var nxt := ""
	for u in UNLOCKS:
		if lv >= int(u[0]):
			unl.append(u[1])
		elif nxt == "":
			nxt = "%s (Stufe %d)" % [u[2], int(u[0])]
	return {"lv": lv, "xp": xp, "from": need(lv), "to": need(lv + 1), "unl": unl, "next": nxt, "rounds": int(e.get("rounds", 0)),
			"all": UNLOCKS.map(func(u): return [int(u[0]), u[1], u[2]])}


func unlocked(name_: String, id: String) -> bool:
	return id in info(name_)["unl"]


func award(name_: String, parts: Array) -> Dictionary:
	"""parts = [[what, xp], …]; returns {"gain", "lv", "up", "new": [names of new things], "parts"}"""
	if is_bot(name_) or key(name_) == "":
		return {}
	_load()
	var k := key(name_)
	var e: Dictionary = db.get(k, {"n": name_, "xp": 0, "rounds": 0})
	var before := level_of(int(e.get("xp", 0)))
	var gain := 0
	var used := []
	for pr in parts:
		var v := int(pr[1])
		if v > 0:
			gain += v
			used.append([str(pr[0]), v])
	e["n"] = name_
	e["xp"] = int(e.get("xp", 0)) + gain
	e["rounds"] = int(e.get("rounds", 0)) + 1
	db[k] = e
	_save()
	var after := level_of(int(e["xp"]))
	var fresh := []
	for u in UNLOCKS:
		if int(u[0]) > before and int(u[0]) <= after:
			fresh.append(u[2])
	return {"gain": gain, "lv": after, "up": after > before, "new": fresh, "parts": used}


func daily_first(name_: String, day: String) -> bool:
	"""the challenge of the day: the first round of this name today gives a bonus (once a day)"""
	_load()
	var k := key(name_)
	var e: Dictionary = db.get(k, {"n": name_, "xp": 0, "rounds": 0})
	if str(e.get("daily", "")) == day:
		return false
	e["daily"] = day
	db[k] = e
	return true


func clean_look(name_: String, lk: Dictionary) -> Dictionary:
	"""what is not unlocked yet is taken off again (the phone remembers the choice)"""
	var u: Array = info(name_)["unl"]
	var out := lk.duplicate()
	if not str(out.get("deco", "")) in u:
		out["deco"] = ""
	out["gold"] = bool(out.get("gold", false)) and "gold" in u
	return out


# ---- the things on the figure -------------------------------------------------------------------------------------------
static func _m(c: Color, metal := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.metallic = metal
	m.roughness = 0.35 if metal > 0.0 else 0.8
	return m


static func _add(parent: Node3D, mesh: Mesh, pos: Vector3, c: Color, metal := 0.0, rot := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = pos
	mi.rotation = rot
	mi.material_override = _m(c, metal)
	parent.add_child(mi)
	return mi


static func decorate(a, lk: Dictionary, col: Color) -> void:
	"""the unlocked thing on the figure of the player (MoveEye sees it too - small, like a real cap)"""
	var deco := str(lk.get("deco", ""))
	if deco == "" or a == null or a.head == null:
		return
	var hd: Node3D = a.head
	var ts: Node3D = a.torso if a.torso != null else a.body_root
	match deco:
		"band":
			var tm := TorusMesh.new()
			tm.inner_radius = 0.1
			tm.outer_radius = 0.125
			_add(hd, tm, Vector3(0, 0.215, 0), col.lightened(0.25))
		"scarf":
			var tm2 := TorusMesh.new()
			tm2.inner_radius = 0.06
			tm2.outer_radius = 0.11
			_add(ts, tm2, Vector3(0, 0.58, 0), col.darkened(0.35))
			var bm := BoxMesh.new()
			bm.size = Vector3(0.07, 0.24, 0.025)
			_add(ts, bm, Vector3(0.06, 0.45, -0.17), col.darkened(0.35))
		"tophat":
			var cm := CylinderMesh.new()
			cm.top_radius = 0.1
			cm.bottom_radius = 0.1
			cm.height = 0.2
			_add(hd, cm, Vector3(0, 0.36, 0.0), Color(0.08, 0.08, 0.09))
			var cb := CylinderMesh.new()
			cb.top_radius = 0.17
			cb.bottom_radius = 0.17
			cb.height = 0.015
			_add(hd, cb, Vector3(0, 0.265, 0.0), Color(0.08, 0.08, 0.09))
			var cr := CylinderMesh.new()
			cr.top_radius = 0.102
			cr.bottom_radius = 0.102
			cr.height = 0.035
			_add(hd, cr, Vector3(0, 0.29, 0.0), col)
		"cape":
			var bx := BoxMesh.new()
			bx.size = Vector3(0.46, 0.8, 0.02)
			_add(ts, bx, Vector3(0, 0.12, 0.2), col.darkened(0.3), 0.0, Vector3(-0.12, 0, 0))
		"crown":
			var c1 := CylinderMesh.new()
			c1.top_radius = 0.1
			c1.bottom_radius = 0.09
			c1.height = 0.07
			_add(hd, c1, Vector3(0, 0.29, 0), Color(0.95, 0.75, 0.2), 0.8)
			for k in range(5):
				var sm := SphereMesh.new()
				sm.radius = 0.02
				sm.height = 0.04
				var an := TAU * k / 5.0
				_add(hd, sm, Vector3(cos(an) * 0.09, 0.34, sin(an) * 0.09), Color(0.95, 0.2, 0.25) if k % 2 == 0 else Color(0.2, 0.6, 1.0), 0.5)
