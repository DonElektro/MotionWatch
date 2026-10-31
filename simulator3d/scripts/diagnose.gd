extends RefCounted
## 3D-4.2x «Mehr» → Selbstdiagnose (Wunsch Daniel 30.10.2026), wie «Selbstdiagnose» von MoveEye (120 health_check, 530):
## pro Teil eine Ampel (ok / Hinweis / Problem / aus), eine kurze Angabe und – wenn nicht ok – ein Tipp «→ was tun».
## Nur aus dem, was der Simulator sowieso weiss (kein Warten, kein Netz).

const UI = preload("res://scripts/ui_style.gd")
const Icons = preload("res://scripts/mehr_icons.gd")
const Quality = preload("res://scripts/quality.gd")   # 3D-4.25: «Leistung» (Lite, Renderer)
const QNAMES := {"simple": "einfach", "medium": "mittel", "nice": "schön", "ultra": "ultra"}


static func _gb(b: float) -> String:
	if b >= 1e9:
		return "%.1f GB" % (b / 1e9)
	return "%d MB" % int(b / 1e6)


static func check(main) -> Array:
	var out := []
	var add := func(id: String, icon: String, title: String, level: String, text: String, tip := ""):
		out.append({"id": id, "icon": icon, "title": title, "level": level, "text": text, "tip": tip})
	# 3D-4.25 «Leistung»: frames per second, renderer, Lite on / off, resolution (to test on the Raspberry Pi)
	var fps := Engine.get_frames_per_second()
	var q := str(main.quality)
	var gpu := RenderingServer.get_video_adapter_name()
	var pf: Dictionary = main.perf_info()
	var gt := "%d Bilder/s · %s · %s · 3D %s (%d %%) · Kameras für MoveEye %s · Stufe «%s» · %s" % [fps,
			("Lite an (%s)" % str(pf["why"])) if pf["lite"] else "Lite aus (Grafik-Modus «%s»)" % Quality.mode_name(str(pf["mode"])),
			str(pf["renderer"]), str(pf["res"]), int(pf["scale"]), str(pf["cams"]), QNAMES.get(q, q), gpu if gpu != "" else "Grafikkarte unbekannt"]
	if main.in_vm:
		gt += " · virtuelle Maschine"
	if not main.win_open:
		add.call("gfx", "meter", "Leistung", "ok", gt + " · Fenster klein / versteckt")
	elif fps >= 20 or (pf["lite"] and fps >= 18):
		add.call("gfx", "meter", "Leistung", "ok", gt)
	elif fps >= 10:
		add.call("gfx", "meter", "Leistung", "warn", gt, "System → Grafik: «Grafik-Modus» auf «Lite» oder «Automatisch leichter» einschalten." if not pf["lite"] else "Schon Lite: andere Programme schliessen, das Fenster kleiner machen.")
	else:
		add.call("gfx", "meter", "Leistung", "bad", gt, "System → Grafik: «Grafik-Modus» auf «Lite», andere Programme schliessen." if not pf["lite"] else "Schon Lite: andere Programme schliessen, das Fenster kleiner machen, weniger Besucher gleichzeitig.")
	# CPU of the PC and of the simulator (mini.gd measures it)
	var own: Dictionary = main.mini_box.own if main.mini_box != null else {}
	var pc := float(own.get("pc", -1.0))
	var sm := float(own.get("sim", -1.0))
	var ct := "PC %s · Simulator %s" % ["–" if pc < 0 else "%d %%" % roundi(pc), "–" if sm < 0 else "%d %%" % roundi(sm)]
	if pc < 0:
		add.call("cpu", "gear", "CPU-Last", "off", "noch nicht gemessen")
	elif pc > 90:
		add.call("cpu", "gear", "CPU-Last", "bad", ct, "Der PC ist voll: andere Programme schliessen, Grafik leichter, weniger Besucher gleichzeitig.")
	elif pc > 70:
		add.call("cpu", "gear", "CPU-Last", "warn", ct, "Knapp: läuft MoveEye auf demselben PC, braucht es auch Rechenzeit – Grafik etwas leichter stellen.")
	else:
		add.call("cpu", "gear", "CPU-Last", "ok", ct)
	# memory
	var mi: Dictionary = OS.get_memory_info() if OS.has_method("get_memory_info") else {}
	var phys := float(mi.get("physical", -1))
	var avail := float(mi.get("available", -1))
	var used := float(OS.get_static_memory_usage())
	if phys <= 0 or avail < 0:
		add.call("ram", "box", "Arbeitsspeicher (RAM)", "off", "Simulator %s · der Rest ist unbekannt" % _gb(used))
	else:
		var rt := "frei %s von %s · Simulator %s" % [_gb(avail), _gb(phys), _gb(used)]
		if avail < 0.05 * phys or avail < 4e8:
			add.call("ram", "box", "Arbeitsspeicher (RAM)", "bad", rt, "Fast voll: Programme schliessen (Browser-Tabs), den Simulator neu starten.")
		elif avail < 0.15 * phys or avail < 1e9:
			add.call("ram", "box", "Arbeitsspeicher (RAM)", "warn", rt, "Wird knapp: nicht benötigte Programme schliessen.")
		else:
			add.call("ram", "box", "Arbeitsspeicher (RAM)", "ok", rt)
	# connection to MoveEye: sending, port, connected
	var conn: bool = main.mw_addr != "" and main.now() - main.mw_t < 3.0
	var port := int(main.stream_port)
	var pt := "Port %d (Bilder, Steuerung, /view.jpg)" % port + (" · Ersatz-Port, 8765 war besetzt" if port in main.ALT_PORTS else "")
	if conn:
		add.call("mw", "link", "Verbindung zu MoveEye", "ok", "verbunden mit «%s» · MoveEye %s · %s" % [str(main.mw.get("device", "MoveEye")), str(main.mw.get("mw_version", "?")), pt])
	elif main.stream_on:
		add.call("mw", "link", "Verbindung zu MoveEye", "warn", "wartet auf MoveEye · " + pt,
				"In MoveEye: Reiter Simulator → Verbindung: die Adresse dieses PCs eintragen (gleiches Netz) – oder unten den Tunnel nutzen.")
	else:
		add.call("mw", "link", "Verbindung zu MoveEye", "warn", "«An MoveEye senden» ist aus", "Karte Verbindung → «An MoveEye senden» einschalten.")
	# tunnel (MoveEye in another network)
	var tn = main.tunnel
	if not main.tunnel_on or tn == null:
		add.call("tunnel", "route", "Tunnel zu MoveEye", "off", "aus – nur nötig, wenn MoveEye in einem anderen Netz ist")
	elif main.now() - float(tn.ok_t) < 30.0:
		add.call("tunnel", "route", "Tunnel zu MoveEye", "ok", "%s · %s:%d" % [str(tn.msg), str(main.tunnel_host), int(tn.PORT)])
	else:
		add.call("tunnel", "route", "Tunnel zu MoveEye", "warn", "%s · %s:%d" % [str(tn.msg), str(main.tunnel_host), int(tn.PORT)],
				"Adresse und Code in der Karte Verbindung → Tunnel mit MoveEye (Reiter Simulator) vergleichen; MoveEye muss laufen.")
	# firewall: only a hint when MoveEye does not come
	var os_ := OS.get_name()
	if conn:
		add.call("fw", "lens", "Firewall", "ok", "durchlässig – MoveEye ist verbunden")
	elif main.stream_on and main.now() > 20.0:
		var tip := "Windows-Firewall: «3D-Simulator» (Godot) für private Netzwerke zulassen – eingehend TCP-Port %d." % port
		if os_ == "Linux":
			tip = "Firewall (z. B. ufw): eingehend TCP-Port %d erlauben – «sudo ufw allow %d/tcp»." % [port, port]
		elif os_ == "macOS":
			tip = "macOS: Systemeinstellungen → Netzwerk → Firewall: eingehende Verbindungen für den Simulator erlauben (Port %d)." % port
		add.call("fw", "lens", "Firewall", "warn", "MoveEye kommt nicht durch – vielleicht blockiert die Firewall", tip)
	else:
		add.call("fw", "lens", "Firewall", "off", "noch nichts zu prüfen (Senden aus oder gerade gestartet)")
	# disk space for recordings, training pictures, games
	var da := DirAccess.open("user://")
	var left := float(da.get_space_left()) if da != null else -1.0
	var where := OS.get_user_data_dir()
	if left < 0:
		add.call("disk", "box", "Speicherplatz für Aufnahmen", "off", "unbekannt · " + where)
	elif left < 1e9:
		add.call("disk", "box", "Speicherplatz für Aufnahmen", "bad", "frei %s · %s" % [_gb(left), where],
				"Fast voll: «Alte KI-Daten löschen» (Karte Testen) oder alte Aufnahmen und Trainingsbilder im Ordner löschen.")
	elif left < 5e9:
		add.call("disk", "box", "Speicherplatz für Aufnahmen", "warn", "frei %s · %s" % [_gb(left), where],
				"Für Trainingspakete und Aufnahmen bald Platz schaffen (Karte Testen → «Alte KI-Daten löschen»).")
	else:
		add.call("disk", "box", "Speicherplatz für Aufnahmen", "ok", "frei %s · %s" % [_gb(left), where])
	# Godot version (the simulator is made for 4.3)
	var v: Dictionary = Engine.get_version_info()
	var vs := str(v.get("string", ""))
	if int(v.get("major", 0)) == 4 and int(v.get("minor", 0)) == 3:
		add.call("godot", "gear", "Godot-Version", "ok", vs + " · " + os_ + " · " + str(ProjectSettings.get_setting("rendering/renderer/rendering_method", "")))
	else:
		add.call("godot", "gear", "Godot-Version", "warn", vs + " · " + os_, "Der Simulator ist für Godot 4.3 gebaut – die fertige Fassung (ZIP) von MoveEye verwenden.")
	# Godot errors since the start (the log, protokoll.gd)
	var pr = main.mehr.protokoll if main.mehr != null else null
	if pr != null:
		var ne: int = pr.errors()
		if ne == 0:
			add.call("err", "log", "Fehler seit dem Start", "ok", "keine")
		else:
			add.call("err", "log", "Fehler seit dem Start", "warn", "%d Meldungen von Godot" % ne, "Mehr → Protokoll → «Fehler»: ansehen, kopieren und mit einer Rückmeldung schicken.")
	# the interface with MoveEye (schnittstelle.json)
	if main.schnitt != null and str(main.schnitt.get("result")) != "":
		var r := str(main.schnitt.get("result"))
		if r.find("Schnittstelle: OK") >= 0:
			add.call("api", "check", "Schnittstelle zu MoveEye", "ok", r.replace("Schnittstelle: OK ", "").strip_edges())
		else:
			add.call("api", "check", "Schnittstelle zu MoveEye", "bad", r.replace("SCRIPT ERROR: ", ""), "Simulator und MoveEye auf die neueste Version bringen (Updates).")
	# updates
	var ui := str(main.update_info)
	var ut := ("automatisch" if main.auto_update else "von Hand") + " · " + (ui if ui != "" else "noch nicht geprüft")
	if ui.findn("neu") >= 0 and ui.findn("kein") < 0 and ui.findn("aktuell") < 0:
		add.call("upd", "update", "Updates", "warn", ut, "Mehr → Updates: die neue Version installieren.")
	elif ui.findn("fehl") >= 0 or ui.findn("nicht erreich") >= 0:
		add.call("upd", "update", "Updates", "warn", ut, "Internet prüfen; später nochmals «Jetzt nach Updates suchen».")
	else:
		add.call("upd", "update", "Updates", "ok", ut + " · Version " + str(main.VERSION))
	return out


static func summary(items: Array) -> String:
	var bad := items.filter(func(x): return x["level"] == "bad").size()
	var warn := items.filter(func(x): return x["level"] == "warn").size()
	if bad == 0 and warn == 0:
		return "alles in Ordnung"
	return (("1 Problem" if bad == 1 else "%d Probleme" % bad) if bad else "") + (" · " if bad and warn else "") + (("1 Hinweis" if warn == 1 else "%d Hinweise" % warn) if warn else "")


# ---- the window (like the card «Selbstdiagnose» of MoveEye: dot, name, value, «→ tip») -------------------------------------
static func build(main, body: VBoxContainer, mehr) -> void:
	var items := check(main)
	var sum := UI.small(summary(items), UI.TXT)
	sum.add_theme_font_size_override("font_size", 13)
	body.add_child(sum)
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(540, 380)
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	body.add_child(sc)
	var list := VBoxContainer.new()
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list.add_theme_constant_override("separation", 8)
	sc.add_child(list)
	for x in items:
		var r := HBoxContainer.new()
		r.add_theme_constant_override("separation", 10)
		var dot := Control.new()
		dot.custom_minimum_size = Vector2(12, 20)
		var col: Color = {"ok": UI.GRN, "warn": UI.ORG, "bad": UI.RED}.get(str(x["level"]), UI.MUT.darkened(0.2))
		dot.draw.connect(func(): dot.draw_circle(Vector2(6, 10), 5.0, col))
		r.add_child(dot)
		var ic := Icons.icon(str(x["icon"]), UI.MUT, 18.0)
		if not Icons.KINDS.has(str(x["icon"])):
			ic = UI.group_icon(str(x["icon"]))
			ic.set_meta("col", UI.MUT)
		r.add_child(ic)
		var b := VBoxContainer.new()
		b.add_theme_constant_override("separation", 1)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var tl := Label.new()
		tl.text = str(x["title"])
		tl.add_theme_font_override("font", UI.heading_font())
		tl.add_theme_font_size_override("font_size", 13)
		b.add_child(tl)
		var vl := UI.small(str(x["text"]))
		vl.custom_minimum_size = Vector2(440, 0)
		b.add_child(vl)
		if str(x["tip"]) != "" and str(x["level"]) != "ok":
			var tp := UI.small("→ " + str(x["tip"]), UI.TXT)
			tp.custom_minimum_size = Vector2(440, 0)
			b.add_child(tp)
		r.add_child(b)
		list.add_child(r)
	var bt := HBoxContainer.new()
	bt.alignment = BoxContainer.ALIGNMENT_END
	bt.add_theme_constant_override("separation", 8)
	body.add_child(bt)
	var cp := Button.new()
	cp.text = "Kopieren"
	cp.tooltip_text = "Das Ergebnis als Text in die Zwischenablage"
	cp.pressed.connect(func(): DisplayServer.clipboard_set(as_text(main, items)))
	bt.add_child(cp)
	var again := Button.new()
	again.text = "Nochmals prüfen"
	again.pressed.connect(func(): mehr.open_window("diag"))
	bt.add_child(again)
	var cl := Button.new()
	cl.text = "Schliessen"
	cl.pressed.connect(func(): mehr.close_window())
	bt.add_child(cl)


static func as_text(main, items: Array) -> String:
	var out := PackedStringArray(["3D-Simulator %s · Selbstdiagnose · %s" % [main.VERSION, summary(items)]])
	for x in items:
		out.append("[%s] %s: %s%s" % [str(x["level"]), str(x["title"]), str(x["text"]), (" → " + str(x["tip"])) if str(x["tip"]) != "" and x["level"] != "ok" else ""])
	return "\n".join(out)
