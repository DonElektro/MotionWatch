extends Node
## Trainingsbilder (3D-3.44): the simulator makes pictures of the head camera with a person or an animal in it - by day, at
## dusk, at night with infrared, in rain and fog, near and far - and knows for each picture where the visitor really is
## (the box in the picture). Motion Watch fetches them (/dataset.json, /dataset/<i>.jpg) and checks how well its AI finds
## them; it can also pack them as training pictures. CONTROL action "dataset": {"op": "start", "n": 40} / "get" / "stop".

const CONDS := [["Tag", 11.0, "clear"], ["Abend", 19.6, "clear"], ["Nacht (Infrarot)", 23.5, "clear"], ["Regen", 14.0, "rain"],
		["Nebel", 9.0, "fog"], ["Nacht + Regen", 1.0, "rain"]]
const KINDS := ["person", "person", "person", "fox", "deer", "dog", "cat", "boar"]

var main
var busy := false
var total := 0
var items := []               # {"i", "kind", "cond", "dist", "box": [x, y, w, h] (0..1), "jpg": PackedByteArray}
var msg := ""
var _stop := false
var servo = null              # Vector2 pan / tilt degrees while making the pictures


var only := []                # which conditions (index into CONDS); empty = all


func start(n: int, conds := []) -> Dictionary:
	if busy:
		return state()
	n = clampi(n, 2, 80)
	only = conds.filter(func(c): return int(c) >= 0 and int(c) < CONDS.size()).map(func(c): return int(c))
	_run(n)
	return state()


func load_game() -> Dictionary:
	"""3D-3.53: the «missed» pictures of the game (players Motion Watch did not report) as the test pictures: the hard cases"""
	if busy:
		return state()
	items = []
	var base := "user://spiel"
	var d := DirAccess.open(base)
	if d != null:
		var rounds: Array = d.get_directories()
		rounds.sort()
		rounds.reverse()
		for r in rounds:
			var rep = JSON.parse_string(FileAccess.get_file_as_string(base + "/" + r + "/spielbericht.json"))
			if typeof(rep) != TYPE_DICTIONARY:
				continue
			for m in rep.get("verpasst", []):
				if items.size() >= 80 or typeof(m) != TYPE_DICTIONARY or not m.has("file"):
					continue
				var j := FileAccess.get_file_as_bytes(base + "/" + r + "/" + str(m["file"]))
				var img := Image.new()
				if j.size() < 100 or img.load_jpg_from_buffer(j) != OK:
					continue
				var cond: String = "Spiel: " + ("Nacht" if bool(m.get("dark", false)) else "Tag") + ", " + ["stehend", "geduckt", "kriechend"][clampi(int(m.get("post", 0)), 0, 2)]
				items.append({"i": items.size(), "kind": "person", "cond": cond, "dist": float(m.get("dist", 10.0)), "box": m["box"], "jpg": j,
						"w": img.get_width(), "h": img.get_height()})
	total = items.size()
	msg = "%d Bilder aus dem Spiel" % total if total > 0 else "Noch keine verpassten Bilder aus dem Spiel."
	return state()


func state() -> Dictionary:
	var by := {}
	for it in items:
		by[it["cond"]] = int(by.get(it["cond"], 0)) + 1
	return {"ok": true, "busy": busy, "done": items.size(), "total": total, "msg": msg, "conds": by}


func list() -> Array:
	var out := []
	for it in items:
		out.append({"i": it["i"], "kind": it["kind"], "cond": it["cond"], "dist": it["dist"], "box": it["box"], "w": it["w"], "h": it["h"]})
	return out


func jpg(i: int) -> PackedByteArray:
	for it in items:
		if int(it["i"]) == i:
			return it["jpg"]
	return PackedByteArray()


func _run(n: int) -> void:
	busy = true
	_stop = false
	total = n
	items = []
	msg = "bereitet vor …"
	# keep what the user had
	var keep := {"hour": main.hour(), "weather": main.weather, "auto": main.auto_visitors}
	main.auto_visitors = false
	for v in main.visitors.get_children():
		v.visible = false
	var k := 0
	while k < n and not _stop:
		var cond: Array = CONDS[only[k % only.size()]] if not only.is_empty() else CONDS[k % CONDS.size()]
		main.set_hour(float(cond[1]))
		main.weather = str(cond[2])
		var kind: String = KINDS[randi() % KINDS.size()]
		var dist := randf_range(4.0, 18.0) if kind == "person" else randf_range(3.0, 11.0)
		var side := randf_range(-22.0, 22.0)
		# where the head looks: the visitor somewhere in the picture, not always in the middle
		var yaw0: float = main.rig.rotation.y
		var a := yaw0 + deg_to_rad(side)
		var p: Vector3 = main.rig.global_position + Vector3(-sin(a) * dist, 0, -cos(a) * dist)
		p = main.free_spot(p, 0.5, true) if main.has_method("free_spot") else p
		p.y = main.ground_y(p.x, p.z)
		var aim := side + randf_range(-14.0, 14.0)
		servo = Vector2(-aim, randf_range(-6.0, 4.0))
		var far := p + Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)).normalized() * 40.0
		var v = main.spawn(kind, p, far)                 # a far goal: it must not reach it and leave (it would free itself)
		v.speed = 0.02
		msg = "Bild %d von %d · %s · %s" % [k + 1, n, cond[0], kind]
		# let the head turn, the light settle and the camera expose
		var t0 := Time.get_ticks_msec()
		while Time.get_ticks_msec() - t0 < 1600:
			await main.get_tree().process_frame
		if not is_instance_valid(v):
			continue
		# the normal picture loop takes the pictures (never a second capture at the same time - that crashed the graphics);
		# three new ones: the exposure settles like on the real camera
		var f0: int = int(main.frame_no[0])
		var t1 := Time.get_ticks_msec()
		while int(main.frame_no[0]) < f0 + 3 and Time.get_ticks_msec() - t1 < 8000:
			main.snap_want[0] = main.now()
			await main.get_tree().process_frame
		while main.capturing:
			await main.get_tree().process_frame
		if not is_instance_valid(v):
			continue
		var j: PackedByteArray = main.jpgs[0]
		var box := _box(v)
		var shown: bool = not box.is_empty() and main.line_free(main.cams[0].global_position, v.global_position + Vector3(0, 0.5, 0))
		if shown and j.size() > 0:
			var sz: Vector2i = main.vps[0].size
			items.append({"i": items.size(), "kind": kind, "cond": cond[0], "dist": snappedf(dist, 0.1), "box": box, "jpg": j, "w": sz.x, "h": sz.y})
			k += 1
		v.queue_free()
		await main.get_tree().process_frame
	servo = null
	main.set_hour(float(keep["hour"]))
	main.weather = str(keep["weather"])
	main.auto_visitors = bool(keep["auto"])
	for v2 in main.visitors.get_children():
		v2.visible = true
	msg = "fertig: %d Bilder" % items.size()
	busy = false


func stop() -> void:
	_stop = true


# ---- 3D-3.74: a training set for an own AI model (YOLO format), many pictures, written straight to disk ----------------
# Only picture data (no map): pictures with boxes, the conditions in the file name. Classes like COCO where they exist.
const EXPORT_CLASSES := ["person", "dog", "cat", "horse", "sheep", "cow", "fox", "deer", "boar", "badger", "hare", "hedgehog", "wolf", "marten",
		"squirrel", "lynx", "chamois", "ibex"]
const EXPORT_KIND_CLASS := {"person": "person", "child": "person", "jogger": "person", "cyclist": "person", "courier": "person", "police": "person",
		"drunk": "person", "stroller": "person", "dog": "dog", "cat": "cat", "horse": "horse", "sheep": "sheep", "cow": "cow", "fox": "fox",
		"deer": "deer", "boar": "boar", "badger": "badger", "hare": "hare", "hedgehog": "hedgehog", "wolf": "wolf", "marten": "marten",
		"squirrel": "squirrel", "lynx": "lynx", "chamois": "chamois", "ibex": "ibex"}
const EXPORT_PEOPLE := ["person", "person", "person", "child", "jogger", "cyclist", "courier", "police", "drunk", "stroller"]
const EXPORT_ANIMALS := ["dog", "cat", "fox", "fox", "deer", "boar", "badger", "hare", "hedgehog", "wolf", "marten", "squirrel", "lynx", "horse", "sheep", "cow", "chamois", "ibex"]
const EXPORT_SCENES := ["camping", "wald", "garten", "parkplatz", "lustig", "wild", "zuhause"]
const EXPORT_CONDS := [["tag", 11.0, "clear"], ["morgen", 7.2, "clear"], ["abend", 19.6, "clear"], ["daemmerung", 20.4, "cloudy"], ["nacht_ir", 23.5, "clear"],
		["regen", 14.0, "rain"], ["nebel", 9.0, "fog"], ["schnee", 12.0, "snow"], ["nacht_regen", 1.0, "rain"], ["bewoelkt", 15.0, "cloudy"]]
var export_dir := ""
var export_zip := ""


func export_pack(n: int, scenes_too := true) -> Dictionary:
	if busy:
		return state()
	_export(clampi(n, 10, 5000), scenes_too)
	return state()


func _export(n: int, scenes_too: bool) -> void:
	busy = true
	_stop = false
	total = n
	items = []
	var stamp := Time.get_datetime_string_from_system().replace(":", "").replace("-", "").replace("T", "_")
	export_dir = OS.get_user_data_dir().path_join("trainingsbilder").path_join(stamp)
	for sub in ["images/train", "images/val", "labels/train", "labels/val"]:
		DirAccess.make_dir_recursive_absolute(export_dir.path_join(sub))
	var keep := {"hour": main.hour(), "weather": main.weather, "auto": main.auto_visitors, "scene": main.scene}
	main.auto_visitors = false
	var counts := {}
	var k := 0
	var made := 0
	while made < n and not _stop:
		if scenes_too and made % 60 == 0:
			var sc: String = EXPORT_SCENES[(made / 60) % EXPORT_SCENES.size()]
			if sc != main.scene:
				main.set_scene(sc)
				for _w in 30:
					await main.get_tree().process_frame
		for v0 in main.visitors.get_children():
			v0.queue_free()
		var cond: Array = EXPORT_CONDS[randi() % EXPORT_CONDS.size()]
		main.set_hour(float(cond[1]) + randf_range(-0.6, 0.6))
		main.weather = str(cond[2])
		var empty := randf() < 0.08                       # some pictures without anybody: the AI must learn «nothing» too
		var vs := []
		var n_vis := 0 if empty else (1 if randf() < 0.65 else (2 if randf() < 0.7 else 3))
		var aim := randf_range(-60.0, 60.0)
		var yaw0: float = main.rig.rotation.y
		for q in range(n_vis):
			var kind: String = EXPORT_PEOPLE[randi() % EXPORT_PEOPLE.size()] if randf() < 0.5 else EXPORT_ANIMALS[randi() % EXPORT_ANIMALS.size()]
			var dist := randf_range(3.0, 26.0) if kind in EXPORT_PEOPLE else randf_range(2.5, 14.0)
			var side := aim + randf_range(-26.0, 26.0)
			var a := yaw0 + deg_to_rad(side)
			var p: Vector3 = main.rig.global_position + Vector3(-sin(a) * dist, 0, -cos(a) * dist)
			p = main.free_spot(p, 0.5, true)
			p.y = main.ground_y(p.x, p.z)
			var far := p + Vector3(randf_range(-1, 1), 0, randf_range(-1, 1)).normalized() * 40.0
			var v = main.spawn(kind, p, far)
			if v == null:
				continue
			v.speed = 0.02
			if kind in ["person", "drunk", "police"] and randf() < 0.3:
				v.ctl_posture = 1 if randf() < 0.6 else 2      # crouching / crawling, like a sneaking person
			vs.append([v, kind])
		servo = Vector2(-aim, randf_range(-8.0, 4.0))
		msg = "Paket: Bild %d von %d · %s · %s" % [made + 1, n, cond[0], main.scene]
		var t0 := Time.get_ticks_msec()
		while Time.get_ticks_msec() - t0 < 1400:
			await main.get_tree().process_frame
		var f0: int = int(main.frame_no[0])
		var t1 := Time.get_ticks_msec()
		while int(main.frame_no[0]) < f0 + 3 and Time.get_ticks_msec() - t1 < 8000:
			main.snap_want[0] = main.now()
			await main.get_tree().process_frame
		while main.capturing:
			await main.get_tree().process_frame
		var j: PackedByteArray = main.jpgs[0]
		var lines := []
		for e in vs:
			var v2 = e[0]
			if not is_instance_valid(v2):
				continue
			var box := _box(v2)
			if box.is_empty() or not main.line_free(main.cams[0].global_position, v2.global_position + Vector3(0, 0.5, 0)):
				continue
			if box[2] * box[3] < 0.0004:                    # smaller than a few pixels: no use
				continue
			var cl: String = EXPORT_KIND_CLASS.get(e[1], "person")
			counts[cl] = int(counts.get(cl, 0)) + 1
			lines.append("%d %.5f %.5f %.5f %.5f" % [EXPORT_CLASSES.find(cl), box[0] + box[2] / 2.0, box[1] + box[3] / 2.0, box[2], box[3]])
		if j.size() > 0 and (empty or not lines.is_empty()):
			var part := "val" if (made % 7) == 6 else "train"
			var nm := "%05d_%s_%s" % [made, main.scene, cond[0]]
			var f := FileAccess.open(export_dir.path_join("images/%s/%s.jpg" % [part, nm]), FileAccess.WRITE)
			if f != null:
				f.store_buffer(j)
				f.close()
			var fl := FileAccess.open(export_dir.path_join("labels/%s/%s.txt" % [part, nm]), FileAccess.WRITE)
			if fl != null:
				fl.store_string("\n".join(PackedStringArray(lines)) + ("\n" if not lines.is_empty() else ""))
				fl.close()
			made += 1
		k += 1
		if k > n * 4:
			break                                          # something does not work (never visible): stop
		for e2 in vs:
			if is_instance_valid(e2[0]):
				e2[0].queue_free()
		await main.get_tree().process_frame
	servo = null
	var yaml := "# Trainingsbilder aus dem MW Sim · 3D (%s) - YOLO-Format\npath: .\ntrain: images/train\nval: images/val\nnames:\n" % main.VERSION
	for i in range(EXPORT_CLASSES.size()):
		yaml += "  %d: %s\n" % [i, EXPORT_CLASSES[i]]
	var fy := FileAccess.open(export_dir.path_join("data.yaml"), FileAccess.WRITE)
	if fy != null:
		fy.store_string(yaml)
		fy.close()
	var info := {"made": made, "classes": counts, "scenes": EXPORT_SCENES if scenes_too else [keep["scene"]], "simulator": main.VERSION,
			"note": "Nur Bilddaten mit Rahmen, keine Kartendaten. Trainieren z. B. mit: yolo detect train data=data.yaml model=yolov8n.pt"}
	var fi := FileAccess.open(export_dir.path_join("info.json"), FileAccess.WRITE)
	if fi != null:
		fi.store_string(JSON.stringify(info, " "))
		fi.close()
	msg = "Paket wird gepackt …"
	await main.get_tree().process_frame
	export_zip = _zip_dir(export_dir)
	if main.scene != keep["scene"]:
		main.set_scene(str(keep["scene"]))
	main.set_hour(float(keep["hour"]))
	main.weather = str(keep["weather"])
	main.auto_visitors = bool(keep["auto"])
	msg = "fertig: %d Bilder · %s" % [made, export_zip if export_zip != "" else export_dir]
	busy = false


func _zip_dir(dir: String) -> String:
	"""the whole folder as one ZIP on the desktop (else next to the folder)"""
	var desk := OS.get_system_dir(OS.SYSTEM_DIR_DESKTOP)
	var out := (desk if desk != "" and DirAccess.dir_exists_absolute(desk) else dir.get_base_dir()).path_join("MW-Trainingsbilder_%s.zip" % dir.get_file())
	var z := ZIPPacker.new()
	if z.open(out) != OK:
		return ""
	var files := []
	for sub in ["images/train", "images/val", "labels/train", "labels/val"]:
		var da := DirAccess.open(dir.path_join(sub))
		if da == null:
			continue
		for fn in da.get_files():
			files.append(sub + "/" + fn)
	files.append("data.yaml")
	files.append("info.json")
	for rel in files:
		z.start_file(rel)
		z.write_file(FileAccess.get_file_as_bytes(dir.path_join(rel)))
		z.close_file()
	z.close()
	return out


func _box(v: Node3D) -> Array:
	"""the box of the visitor in the picture of the head camera (0..1), from the corners of its meshes"""
	var cam: Camera3D = main.cams[0]
	var sz: Vector2 = Vector2(main.vps[0].size)
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	var any := false
	for m in v.find_children("*", "MeshInstance3D", true, false):
		var mi := m as MeshInstance3D
		if not mi.visible or mi.mesh == null:
			continue
		var ab: AABB = mi.get_aabb()
		for c in 8:
			var w: Vector3 = mi.global_transform * ab.get_endpoint(c)
			if cam.is_position_behind(w):
				continue
			var q := cam.unproject_position(w)
			lo = lo.min(q)
			hi = hi.max(q)
			any = true
	if not any:
		return []
	lo = lo.clamp(Vector2.ZERO, sz)
	hi = hi.clamp(Vector2.ZERO, sz)
	if hi.x - lo.x < 4.0 or hi.y - lo.y < 4.0:
		return []
	return [snappedf(lo.x / sz.x, 0.001), snappedf(lo.y / sz.y, 0.001), snappedf((hi.x - lo.x) / sz.x, 0.001), snappedf((hi.y - lo.y) / sz.y, 0.001)]
