extends Object
## Teil von main.gd (Vorschlag 24 «main.gd zerlegen»): Netzwerk und Status: Statuszeile, Gruppen-Symbole der Karten, Abgleich der Bedienelemente, Rechnername.
## main.gd lädt diesen Teil erst beim ersten Aufruf (_mod) und leitet seine Funktionen weiter: main.xyz bleibt gleich.
## Hier steht «main.» vor allem, was zu main.gd gehört.

var main                              # main.gd
const T := preload("res://scripts/i18n.gd")
const Versionen = preload("res://scripts/versionen.gd")
const Worlds := preload("res://scripts/worlds.gd")


func _update_status() -> void:
	if main.real_label != null and main.realism != null:
		main.real_label.text = "Echt-Abgleich: " + main.realism.info
		var cps: String = main.camphys.status() if main.camphys != null else ""
		if cps != "":
			main.real_label.text += "\n" + cps                 # 3D-4.x P1: exposure and gain of the head camera right now
	main._night_test_tick()
	if main.refscan_label != null:
		main.refscan_label.text = main.refscan_text()
	if main.surprise_label != null:
		main.surprise_label.text = main.surprise.status_text()
	if main.ds_label != null and main.dataset != null:
		main.ds_label.text = ("Trainingspaket: " + main.dataset.msg) if main.dataset.msg != "" else ""
	if not main.mw_cmd.is_empty() and main.start_info.begins_with("MoveEye: "):
		var r_ = main.mw.get("refscan", null)
		if typeof(r_) == TYPE_DICTIONARY and int(r_.get("cmd_seen", 0)) >= int(main.mw_cmd["id"]):
			main.start_info = ""                                  # MoveEye took the request
	if main.status_label != null:
		main.status_label.text = main.Sym.clean(main.status_text())     # 3D-4.22: no empty boxes (MoveEye gets the text with its emoji)
	if main.tunnel_label != null and main.tunnel != null:
		var ts: Dictionary = main.tunnel.state()
		main.tunnel_label.text = ("Ziel: %s:%d (Port von MoveEye) · " % [main.tunnel_host if main.tunnel_host != "" else "?", main.tunnel.PORT]) + str(ts["msg"]) + ((" · %d offen · %.1f MB" % [int(ts["pipes"]), float(ts["mb"])]) if ts["on"] else "")
		main.tunnel_label.add_theme_color_override("font_color", main.UI.GRN if ts["ok"] else (main.UI.ORG if ts["on"] else main.UI.MUT))
	if main.conn_body != null:                                  # symbol: green = MoveEye connected, orange = sending, grey = off
		var st = 2 if main.connected() else (1 if main.stream_on else 0)
		if st != main._conn_state:
			main._conn_state = st
			main.UI.fold_active(main.conn_body, [0, 2, 1][st])          # 3D-3.50: symbol and arrow; the name stays white
			var hd: Label = main.conn_body.get_meta("head", null)
			if hd != null:
				hd.text = ("Verbindung · " + ["aus", "wartet auf MoveEye", "verbunden"][st]).to_upper()
	main._paint_groups()
	if main.stream_note != null:
		if main.stream_on:
			main.stream_note.text = "Sendet: MoveEye findet den Simulator im Netz und bekommt die Bilder." + ("" if main.net.port == main.stream_port else " (Port %d war besetzt – sendet auf Port %d; MoveEye findet ihn von selbst, der Tunnel auch.)" % [main.stream_port, main.net.port])
			main.stream_note.add_theme_color_override("font_color", main.UI.GRN)
		elif main.net != null and main.net.error_text != "":
			main.stream_note.text = "⚠ " + main.net.error_text + (" – versucht es weiter (gleich auf einem freien Port)" if (main.stream_last or main.tunnel_on) else "")
			main.stream_note.add_theme_color_override("font_color", main.UI.ORG)
		else:
			main.stream_note.text = "Senden aus – zum Ausprobieren. MoveEye sieht den Simulator erst, wenn der Schalter eingeschaltet ist."
			main.stream_note.add_theme_color_override("font_color", main.UI.MUT)
	if Engine.get_process_frames() % 4 == 0:
		main._sync_ui()


func status_text() -> String:
	var h = main.hour()
	var mwc = "verbunden mit %s" % str(main.mw.get("device", "MoveEye")) if main.now() - main.mw_t < 3.0 else ("MoveEye nicht verbunden" if main.stream_on else "Senden aus")
	var mww = main.mw_watchers()
	if not mww.is_empty():                     # 3D-4.9: a second MoveEye only watches (does not steer the head)
		mwc += " · schaut nur zu: " + ", ".join(mww)
	if main.schnitt != null:
		mwc += main.schnitt.mw_extra()                 # Aufräumen 2: «Schutz an · Relais …» from MoveEye
	var score = " · Treffer %d von %d Schüssen, %d Punkte" % [main.hits, main.shots, main.points] if main.rifle_on else ""
	return "%s · %02d:%02d · %s · %s · %.1f °C · Besucher %d%s · %s" % [Worlds.full_name(main.scene) if Worlds.is_place(main.scene) and not Worlds.solo(main, main.scene) else main.Scenes.name_of(main.scene), int(h), int(fmod(h, 1.0) * 60), "Nacht" if main.is_dark() else "Tag", {"clear": "klar", "cloudy": "bewölkt", "rain": "Regen", "fog": "Nebel", "snow": "Schnee"}.get(main.weather, main.weather), main.ambient, main.visitors.get_child_count(), score, mwc] + (" · Update: " + main.update_info if main.update_info != "" else "") + (" · " + main.start_info if main.start_info != "" else "") + (" · " + main.game.status() if main.game != null and main.game.status() != "" else "") + (" · " + main.testrun.status() if main.testrun != null and main.testrun.status() != "" else "") + (" · " + main.nacht.status() if main.nacht != null and main.nacht.running else "") + (" · " + main.dev2.status() if main.dev2 != null and main.dev2.on else "") + (" · " + main.recorder.info if main.recorder != null and main.recorder.info != "" and (main.recorder.recording or main.recorder.playing) else "") + (" · " + main.life.info if main.life != null and main.life.info != "" and (main.real_weather or main.daily_life) else "") + (" · " + main.geo.info if main.geo != null and main.geo.busy else "") + (" · " + main.geo_note if main.geo_note != "" else "") + (" · " + main.wetter.lens_hint() if main.get("wetter") != null and main.wetter.lens_hint() != "" else "")


func host_name() -> String:
	## the name of this computer (MoveEye shows it next to the simulator in its list)
	for k in ["COMPUTERNAME", "HOSTNAME"]:
		var h := OS.get_environment(k).strip_edges()
		if h != "":
			return h.substr(0, 40)
	var f := FileAccess.open("/etc/hostname", FileAccess.READ)
	if f != null:
		return f.get_as_text().strip_edges().substr(0, 40)
	return ""


func refresh_controls() -> void:
	"""the list of recordings changed: new options for the select (the page of MoveEye shows them at once)"""
	for c in main.controls:
		if c.id == "rec_pick":
			c.extra["options"] = main.recorder.options()
	main._sync_ui()


func _sync_ui() -> void:
	main._syncing = true
	for c in main.controls:
		if not main.ui_rows.has(c.id) or c["get"] == null:
			continue
		var w = main.ui_rows[c.id]
		var v = c["get"].call()
		if w is CheckBox or w is CheckButton:
			w.set_pressed_no_signal(bool(v))
		elif w is OptionButton:
			for i in range(w.item_count):
				if str(w.get_item_metadata(i)) == str(v):
					w.select(i)
		elif w is HSlider and not w.has_focus():
			w.value = float(v)
		elif w is LineEdit and not w.has_focus():
			w.text = str(v)
		if w is HSlider and c.has("ro"):              # Aufräumen 2: only readable now (e.g. the battery size «von MoveEye»)
			w.editable = not bool(c["ro"].call())
	for c in main.controls:                                # Menüs A: switches, choices and buttons greyed out too (e.g. «Foto-Modus» without a photo)
		if c.has("ro") and main.ui_rows.has(c.id) and (main.ui_rows[c.id] is BaseButton):
			var ro_: bool = bool(c["ro"].call())
			main.ui_rows[c.id].disabled = ro_
			main.ui_rows[c.id].tooltip_text = T.t("Zuerst ein Foto des Platzes laden (Gegenstände → Foto des Platzes)") if ro_ and c.id in main.PHOTO_IDS else ""
	main._syncing = false


func group_active(g: String) -> int:
	"""3D-3.43: is something of this group switched on? 0 = no, 1 = on (green), 2 = something to watch (orange)"""
	match g:
		"Szene":
			return 1 if main.geo != null and main.geo.loaded and main.scene == "ort" else 0
		"Wetter":
			return 1 if main.real_weather else 0
		"Besuch":
			return 1 if main.auto_visitors else 0
		"Kamerabild":
			return 2 if main.cond.values().has(true) else 0
		"Zusatzgeräte":
			return 2 if main.door_open or main.gas_on else 0
		"Mover":
			return 1 if main.mover_on else 0
		"Spiel":
			return 1 if main.game != null and main.game.open else 0
		"Wildtier":
			return 1 if main.rifle_on else 0
		"Testen":
			return 1 if main.testrun != null and main.testrun.running else 0
	return 0


func _groups_on() -> Dictionary:
	var o := {}
	for g in main.group_bodies:
		var v = main.group_active(g)
		if v > 0:
			o[g] = v
	o["Verbindung"] = 1 if main.connected() else 0
	return o


func _paint_groups() -> void:
	"""the symbol of a group card turns green when it is on (like «Verbindung»), orange when something is to be watched"""
	for g in main.group_bodies:
		var st = main.group_active(g)
		if main._group_state.get(g, -1) == st:
			continue
		main._group_state[g] = st
		main.UI.fold_active(main.group_bodies[g], st)              # 3D-3.50: symbol and arrow green / orange, the name stays white
	if main.cam_body != null:
		main.UI.fold_active(main.cam_body, 1 if main.connected() else 0)
	if main.tools_body != null:
		main.UI.fold_active(main.tools_body, 1 if (main.mwpc != null and main.mwpc.state == "running") or (main.pruef != null and main.pruef.running) or (main.dataset != null and main.dataset.busy) or (main.testrun != null and main.testrun.running) or (main.blindmap != null and main.blindmap.busy) else 0)


func _sync_update_ui() -> void:
	if main.update_btn != null:
		main.update_btn.text = "Nach Updates suchen (jetzt %s)" % main.VERSION


func control_info() -> Dictionary:
	var out := []
	for c in main.controls:
		if c.has("only") and not bool(c["only"].call()):
			continue                                     # 3D-4.28: e.g. «Standort im Ferienpark» only in that scene
		var d := {"type": c.type, "id": c.id, "label": c.label, "group": c.group}
		d.merge(c.extra)
		if c["get"] != null:
			var v = c["get"].call()
			d["value"] = snappedf(v, 0.001) if typeof(v) == TYPE_FLOAT else v
		if c.has("ro"):
			d["ro"] = bool(c["ro"].call())            # Aufräumen 2: the page of MoveEye shows it read-only too
		out.append(d)
	return {"ok": true, "v": 1, "name": Versionen.label(main.VERSION), "version": main.VERSION,
				"scenarios": main.scenarios(), "scenario": Worlds.world_of(main.scene), "place": main.scene if Worlds.is_place(main.scene) else "",
			"controls": out, "status": main.status_text(), "upload": null, "groups_on": main._groups_on(),
			"game": {"open": main.game != null and main.game.open, "url": main.game.address() if main.game != null and main.game.open else "", "players": main.game.count() if main.game != null else 0}}
