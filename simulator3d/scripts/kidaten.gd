extends RefCounted
## «KI-Daten aufräumen» (Wunsch Daniel, 29.10.2026): die Trainingspakete (dataset.gd) brauchen viel Platz – jedes liegt als
## Ordner user://trainingsbilder/<Zeit>[_hoch] und als ZIP «MoveEye-Trainingsbilder_<Zeit>.zip» (Schreibtisch oder daneben;
## bis 3D-4.21 hiessen sie «MW-Trainingsbilder_<Zeit>.zip» – beide Namen werden erkannt).
##   aufraeumen(false): nach jedem neuen Paket von selbst – die neuesten 3 bleiben, nichts älter als 30 Tage.
##   aufraeumen(true):  Knopf «Alte KI-Daten löschen» – alle ausser dem neuesten.
## Das neueste Paket (und das gerade benutzte) bleibt immer. Gelöscht wird nur, was genau so heisst – nie ein KI-Modell,
## nie andere Dateien auf dem Schreibtisch.
## CONTROL action "dataset": {"op": "packs"} (Liste) / {"op": "clean"} (alte löschen).

const KEEP := 3
const MAX_DAYS := 30
const ZIP_PREFIX := "MoveEye-Trainingsbilder_"
const ZIP_PREFIXES := ["MoveEye-Trainingsbilder_", "MW-Trainingsbilder_"]   # 3D-4.22: new name, the old one (until 3D-4.21) still counts


static func root() -> String:
	return OS.get_user_data_dir().path_join("trainingsbilder")


static func _zip_dirs() -> Array:
	var out := [root()]
	var desk := OS.get_system_dir(OS.SYSTEM_DIR_DESKTOP)
	if desk != "" and DirAccess.dir_exists_absolute(desk):
		out.append(desk)
	return out


static func _stamp(name: String) -> int:
	"""«20261029_170512» or «…_hoch» -> seconds (local time read as UTC: only the age counts); -1 = not a pack"""
	var rx := RegEx.create_from_string("^(\\d{4})(\\d{2})(\\d{2})_(\\d{2})(\\d{2})(\\d{2})(_hoch)?$")
	var m := rx.search(name)
	if m == null:
		return -1
	return Time.get_unix_time_from_datetime_dict({"year": int(m.get_string(1)), "month": int(m.get_string(2)), "day": int(m.get_string(3)),
			"hour": int(m.get_string(4)), "minute": int(m.get_string(5)), "second": int(m.get_string(6))})


static func _now() -> int:
	var d := Time.get_datetime_dict_from_system()           # local time, like the names of the packs
	return Time.get_unix_time_from_datetime_dict(d)


static func _size(path: String) -> int:
	if FileAccess.file_exists(path):
		var f := FileAccess.open(path, FileAccess.READ)
		if f == null:
			return 0
		var n := f.get_length()
		f.close()
		return n
	var da := DirAccess.open(path)
	if da == null:
		return 0
	var s := 0
	for fn in da.get_files():
		s += _size(path.path_join(fn))
	for dn in da.get_directories():
		s += _size(path.path_join(dn))
	return s


static func _rm_tree(path: String) -> void:
	var da := DirAccess.open(path)
	if da == null:
		return
	for fn in da.get_files():
		DirAccess.remove_absolute(path.path_join(fn))
	for dn in da.get_directories():
		_rm_tree(path.path_join(dn))
	DirAccess.remove_absolute(path)


static func packs() -> Array:
	"""[{name, t, dir, zips, bytes}], newest first"""
	var by := {}
	var da := DirAccess.open(root())
	if da != null:
		for dn in da.get_directories():
			if _stamp(dn) >= 0:
				by[dn] = {"name": dn, "t": _stamp(dn), "dir": root().path_join(dn), "zips": [], "bytes": 0}
	for zd in _zip_dirs():
		var dz := DirAccess.open(zd)
		if dz == null:
			continue
		for fn in dz.get_files():
			var pre := ""
			for zp in ZIP_PREFIXES:
				if fn.begins_with(zp):
					pre = zp
			if pre == "" or not fn.ends_with(".zip"):
				continue
			var nm: String = fn.trim_prefix(pre).trim_suffix(".zip")
			if _stamp(nm) < 0:
				continue
			if not by.has(nm):
				by[nm] = {"name": nm, "t": _stamp(nm), "dir": "", "zips": [], "bytes": 0}
			by[nm]["zips"].append(zd.path_join(fn))
	var out: Array = by.values()
	for p in out:
		var b := _size(p["dir"]) if p["dir"] != "" else 0
		for z in p["zips"]:
			b += _size(z)
		p["bytes"] = b
	out.sort_custom(func(a, b): return int(a["t"]) > int(b["t"]))
	return out


static func state(extra := {}) -> Dictionary:
	var ps := packs()
	var now := _now()
	var lst := []
	var total := 0
	for i in range(ps.size()):
		var p: Dictionary = ps[i]
		total += int(p["bytes"])
		lst.append({"name": p["name"], "mb": snappedf(float(p["bytes"]) / 1048576.0, 0.1), "age_days": maxi(0, int((now - int(p["t"])) / 86400)),
				"vielfalt": "hoch" if str(p["name"]).ends_with("_hoch") else "normal", "zip": not p["zips"].is_empty(), "folder": p["dir"] != "",
				"newest": i == 0})
	var st := {"ok": true, "packs": lst, "total_mb": snappedf(float(total) / 1048576.0, 0.1), "keep": KEEP, "max_days": MAX_DAYS}
	st.merge(extra, true)
	return st


static func aufraeumen(all_old: bool, protect := "") -> Dictionary:
	"""delete old packs; returns {deleted, freed_mb} (the newest and «protect» always stay)"""
	var ps := packs()
	var now := _now()
	var n := 0
	var freed := 0
	for i in range(ps.size()):
		var p: Dictionary = ps[i]
		if i == 0 or str(p["name"]) == protect:
			continue
		var old: bool = all_old or i >= KEEP or now - int(p["t"]) > MAX_DAYS * 86400
		if not old:
			continue
		for z in p["zips"]:
			DirAccess.remove_absolute(z)
		if p["dir"] != "" and str(p["dir"]).begins_with(root()):
			_rm_tree(p["dir"])
		n += 1
		freed += int(p["bytes"])
	if n > 0:
		print("KI-Daten aufgeräumt: %d Pakete, %.0f MB" % [n, float(freed) / 1048576.0])
	return {"deleted": n, "freed_mb": snappedf(float(freed) / 1048576.0, 0.1)}


static func summary() -> String:
	var st := state()
	if st["packs"].is_empty():
		return "KI-Daten: keine Trainingspakete"
	return "KI-Daten: %d Pakete · %.0f MB (die neuesten 3 bleiben, nichts älter als 30 Tage)" % [st["packs"].size(), float(st["total_mb"])]
