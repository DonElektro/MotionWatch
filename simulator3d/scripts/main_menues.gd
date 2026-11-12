extends Object
## Teil von main.gd (Vorschlag 24 «main.gd zerlegen»): die Menüs und das Fenster: Seitenleiste mit den Karten, Ansichts-Leiste, Aufklappen, Suche, Kinder-Modus, Vorschaubilder, HUD.
## main.gd lädt diesen Teil erst beim ersten Aufruf (_mod) und leitet seine Funktionen weiter: main.xyz bleibt gleich.
## Hier steht «main.» vor allem, was zu main.gd gehört.

var main                              # main.gd
const TestrunS := preload("res://scripts/testrun.gd")
const T := preload("res://scripts/i18n.gd")


func _build_ui() -> void:
	"""the window: phone on the left, on the right the panel in the look of the web page of MoveEye (ui_style.gd):
	toolbar (hide, search, groups only, expand all, collapse all), cards, at the bottom «Einfach | Experte»"""
	var layer := CanvasLayer.new()
	main.add_child(layer)
	main.ui_layer = layer
	var th: Theme = main.UI.theme()
	main.phone = main.Phone.new()
	main.phone.main = main
	main.phone.position = Vector2(0, 0)
	main.phone.theme = th
	layer.add_child(main.phone)
	main._build_crosshair(layer)
	main._build_view_bar(layer, th)
	main._build_cpu_pill(layer)
	main.karte = main.Karte.new()
	main.karte.main = main
	main.karte.theme = th
	main.karte.visible = false
	layer.add_child(main.karte)
	main.dataset = preload("res://scripts/dataset.gd").new()      # Trainingsbilder (3D-3.44)
	main.dataset.main = main
	main.add_child(main.dataset)
	main.kitrain = preload("res://scripts/kitrain.gd").new()      # «KI trainieren»: pack -> GitHub release «ki-daten» -> workflow
	main.kitrain.main = main
	main.add_child(main.kitrain)
	main.replay = preload("res://scripts/replay.gd").new()        # Alarm-Rückblick (3D-3.44)
	main.replay.main = main
	main.add_child(main.replay)
	main.replay.setup(layer)
	main.planner = preload("res://scripts/planner.gd").new()      # Aufstell-Planer (3D-3.44)
	main.planner.main = main
	main.planner.theme = th
	layer.add_child(main.planner)
	main.pruef = preload("res://scripts/pruefstand.gd").new()    # Prüfstand (3D-3.49)
	main.pruef.main = main
	main.pruef.theme = th
	layer.add_child(main.pruef)
	var tvl := CanvasLayer.new()                            # the TV mode lies over everything (3D-3.44)
	tvl.layer = 5
	main.add_child(tvl)
	main.tv = preload("res://scripts/tv.gd").new()
	main.tv.main = main
	main.tv.theme = th
	tvl.add_child(main.tv)
	main.gamewiz = preload("res://scripts/gamewiz.gd").new()     # the game wizard (3D-3.41)
	main.gamewiz.main = main
	main.gamewiz.theme = th
	layer.add_child(main.gamewiz)
	main.abenteuer = preload("res://scripts/bergtal_abenteuer.gd").new()   # Bergtal-Abenteuer (same look as the wizard)
	main.abenteuer.main = main
	main.abenteuer.theme = th
	layer.add_child(main.abenteuer)
	var panel := PanelContainer.new()
	panel.theme = th
	panel.anchor_left = 1.0
	panel.anchor_right = 1.0
	panel.anchor_bottom = 1.0
	panel.offset_left = -392
	panel.grow_horizontal = Control.GROW_DIRECTION_BEGIN   # 3D-3.43: if something is too wide it grows to the left, never off the window
	var sb = main.UI.box(Color(main.UI.BG, 0.97), main.UI.LINE, 0, 8, 0)
	sb.border_width_left = 1
	sb.content_margin_left = 10
	sb.content_margin_right = 6
	sb.content_margin_top = 10
	sb.content_margin_bottom = 6
	panel.add_theme_stylebox_override("panel", sb)
	layer.add_child(panel)
	main.ui_root = panel
	main.show_btn = main.UI.icon_button("show", "Bedienfeld zeigen (H)")
	main.show_btn.theme = th
	main.show_btn.anchor_left = 1.0
	main.show_btn.anchor_right = 1.0
	main.show_btn.offset_left = -48
	main.show_btn.offset_top = 10
	main.show_btn.offset_right = -10
	main.show_btn.offset_bottom = 48
	main.show_btn.visible = false
	main.show_btn.pressed.connect(func(): main.show_panel(true))
	layer.add_child(main.show_btn)
	var outer := VBoxContainer.new()                      # from 3D-3.7: name, toolbar and the camera pictures stay at the top,
	outer.add_theme_constant_override("separation", 10)  # only the rest scrolls
	panel.add_child(outer)
	var top_box := VBoxContainer.new()
	top_box.add_theme_constant_override("separation", 10)
	top_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	outer.add_child(top_box)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	outer.add_child(scroll)
	var box_ := VBoxContainer.new()
	main.ui_box = box_
	box_.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box_.add_theme_constant_override("separation", 10)
	scroll.add_child(box_)
	# header: logo, name, version (like the top bar of the page)
	var hdr := HBoxContainer.new()
	hdr.add_theme_constant_override("separation", 8)
	top_box.add_child(hdr)
	var wm = preload("res://scripts/wordmark.gd").new()   # 3D-3.87: the wordmark W6 like on the web page
	if wm.build(44.0):                                   # 3D-4.23: moving like on the web (person, cone, pupil, blink)
		hdr.add_child(wm)
	else:
		wm.free()
		var logo: Control = load("res://scripts/mw_logo.gd").new()  # (fallback) the orange MoveEye symbol
		logo.custom_minimum_size = Vector2(30, 30)
		hdr.add_child(logo)
	var title := Label.new()
	title.text = "Simulator"
	title.add_theme_font_override("font", main.UI.heading_font())
	title.add_theme_font_size_override("font_size", 14)
	title.add_theme_color_override("font_color", main.UI.MUT)
	title.size_flags_vertical = Control.SIZE_SHRINK_END
	hdr.add_child(title)
	var ver = main.UI.small(main.VERSION)
	ver.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ver.autowrap_mode = TextServer.AUTOWRAP_OFF
	ver.size_flags_vertical = Control.SIZE_SHRINK_END
	hdr.add_child(ver)
	main.kopf = preload("res://scripts/kopf.gd").new()       # 639t (Besitzer 01.11.2026): the one header - ? 🔔 ↻ DE ☰ ⛶ ▲ 🛠 like MoveEye
	main.kopf.build(main)                                      # (list and texts: ui_gemeinsam.json «kopf»; narrow panel: from DE on in ☰)
	hdr.add_child(main.kopf)
	main.devzugang = preload("res://scripts/devzugang.gd").new()   # 3.26 (MoveEye 639s): long press on wordmark / title = developer window,
	main.devzugang.name = "DevZugang"                               # and the drawn tool button at the top right (developer area + owner)
	main.add_child(main.devzugang)
	main.devzugang.setup(main, hdr, [hdr.get_child(0), title, main.show_btn])
	# Paket real-layout-leiste (Besitzer 31.10.2026): the bar under the header like on every page of MoveEye (639o) -
	# Einfach | Experte · Symbole farbig | schlicht · Beim Start: Nur Gruppen · Alle zuklappen / Nur Gruppen / Alle aufklappen
	main.UI.icons_plain = main.ui_icons == "plain"
	main.UI.motion_still = main.motion_reduced()                # 3.23 «Bewegung reduzieren»
	main.leiste = preload("res://scripts/bedienleiste.gd").new()
	main.leiste.build(main)
	top_box.add_child(main.leiste)
	main.simple_seg = main.leiste.simple_seg
	main._sg_cb = main.leiste.sg_cb
	main._fold_btns = main.leiste.fold_btns
	# toolbar like above the settings of MoveEye: hide and search (the fold buttons are in the bar)
	var tb := HBoxContainer.new()
	main.ui_tb = tb
	tb.add_theme_constant_override("separation", 6)
	top_box.add_child(tb)
	var hide_b = main.UI.icon_button("hide", "Bedienfeld ausblenden (H)")
	hide_b.pressed.connect(func(): main.show_panel(false))
	tb.add_child(hide_b)
	main.search_in = main.UI.search_field("Einstellung suchen …")
	main.search_in.text_changed.connect(main._search)
	tb.add_child(main.search_in)
	main.search_none = main.UI.small("Kein Treffer")
	main.search_none.visible = false
	box_.add_child(main.search_none)
	main._mode_row = HBoxContainer.new()                 # 3D-3.94: one small line; Kinder | Erwachsene (Einfach | Experte is in the bar, real-layout-leiste)
	main._mode_row.add_theme_constant_override("separation", 6)
	box_.add_child(main._mode_row)
	main.top_cards.append(main._mode_row)
	main.quick = preload("res://scripts/quick.gd").new()            # 3D-3.86: the quick tiles, at the very top
	main.quick.main = main
	box_.add_child(main.quick)
	main.top_cards.append(main.quick)
	# connection to MoveEye
	var cn = main.UI.fold_card(box_, "Verbindung", true, "link")     # from 3D-3.37 it folds; the symbol is green when connected
	main.fold_bodies.append(cn)
	main.top_cards.append(cn.get_meta("card"))
	main.conn_body = cn
	main.stream_cb = CheckButton.new()
	main.stream_cb.text = "An MoveEye senden (Port %d)" % main.stream_port
	main.stream_cb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	main.stream_cb.add_theme_font_size_override("font_size", 15)
	main.stream_cb.button_pressed = main.stream_on
	main.stream_cb.toggled.connect(func(on): main.set_stream(on, true); main.stream_last = on; main._settings_dirty = true)   # 3D-3.75: busy -> spare port
	cn.add_child(main.stream_cb)
	main.stream_note = main.UI.small("")
	cn.add_child(main.stream_note)
	main.status_label = main.UI.small("", main.UI.TXT)
	main.status_label.add_theme_font_size_override("font_size", 13)
	cn.add_child(main.status_label)
	# 3D-3.45: tunnel - when the firewall of this PC lets nothing in (no admin rights)
	if OS.get_name() == "Windows":                 # 3D-3.92: the real fix for «MoveEye findet den Simulator nicht»: one firewall rule
		var fwb := Button.new()
		fwb.text = "Windows-Firewall: Simulator freigeben (einmal, fragt nach Adminrechten)"
		fwb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		fwb.tooltip_text = "Erlaubt dem Simulator eingehende Verbindungen im privaten Netz. Danach braucht es keinen Tunnel und keinen Code mehr."
		fwb.pressed.connect(main._firewall_allow)
		cn.add_child(fwb)
	var tn = main.UI.sub_fold(cn, "Tunnel zu MoveEye (Firewall ohne Adminrechte)", main.tunnel_on)
	tn.set_meta("always", true)                     # 3D-3.46: it has no settings of the list - without this it was always hidden
	main.sub_bodies.append(tn)
	var tnote = main.UI.small("Lässt die Firewall dieses PCs MoveEye nicht herein, verbindet sich der Simulator selbst zu MoveEye. Adresse und Code stehen auf der Seite von MoveEye unter Simulator → «Simulator hinter einer Firewall».")
	tnote.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tn.add_child(tnote)
	var th_ := LineEdit.new()
	th_.placeholder_text = "Adresse von MoveEye, z. B. 192.168.1.20"
	th_.text = main.tunnel_host
	tn.add_child(th_)
	var tc_ := LineEdit.new()
	tc_.placeholder_text = "Code (6 Ziffern)"
	tc_.max_length = 6
	tc_.text = main.tunnel_code
	tn.add_child(tc_)
	var tcb := CheckButton.new()
	tcb.text = "Tunnel verwenden"
	tcb.button_pressed = main.tunnel_on
	tn.add_child(tcb)
	main.tunnel_label = main.UI.small("")
	main.tunnel_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	tn.add_child(main.tunnel_label)
	var apply_t := func():
		main.tunnel_host = th_.text.strip_edges().trim_prefix("http://").trim_prefix("https://").get_slice("/", 0).get_slice(":", 0)
		main.tunnel_code = tc_.text.strip_edges()
		main.tunnel_on = tcb.button_pressed
		main.tunnel.host = main.tunnel_host
		main.tunnel.code = main.tunnel_code
		main.tunnel.set_on(false)
		main.tunnel.set_on(main.tunnel_on)
		main._settings_dirty = true
	th_.text_submitted.connect(func(_t): apply_t.call())
	th_.focus_exited.connect(apply_t)
	tc_.text_submitted.connect(func(_t): apply_t.call())
	tc_.focus_exited.connect(apply_t)
	# 3D-3.92: saved at once while typing (an update a minute later restarted the simulator before the field was left)
	var keep_t := func(_t):
		main.tunnel_host = th_.text.strip_edges().trim_prefix("http://").trim_prefix("https://").get_slice("/", 0).get_slice(":", 0)
		main.tunnel_code = tc_.text.strip_edges()
		main._save_settings()
	th_.text_changed.connect(keep_t)
	tc_.text_changed.connect(keep_t)
	tcb.toggled.connect(func(_v): apply_t.call())
	# camera pictures
	# 3D-3.50: order by logic - first the connection, then the cameras (still visible while searching: not in top_cards)
	var cm = main.UI.fold_card(box_, "Kameras", true, "camera")
	main.fold_bodies.append(cm)
	main.cam_body = cm
	main.cam_card = cm.get_meta("card")
	box_.move_child(main.cam_card, main.conn_body.get_meta("card").get_index() + 1)
	main.cam_float = VBoxContainer.new()
	main.cam_float.theme = th
	main.cam_float.visible = false
	main.cam_float.add_theme_constant_override("separation", 0)
	main.cam_float.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var grip := PanelContainer.new()
	grip.add_theme_stylebox_override("panel", main.UI.box(Color(main.UI.BG, 0.92), main.UI.LINE, 8, 4, 1))
	grip.mouse_default_cursor_shape = Control.CURSOR_MOVE
	grip.tooltip_text = "Kamerabilder verschieben: hier ziehen"
	var gl = main.UI.small("✥ Ziehen zum Verschieben · H = Bedienfeld")
	gl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	gl.mouse_filter = Control.MOUSE_FILTER_IGNORE
	grip.add_child(gl)
	grip.gui_input.connect(main._cam_float_input)
	main.cam_float.add_child(grip)
	layer.add_child(main.cam_float)
	main.prev0 = TextureRect.new()
	main.prev0.texture = main.vps[0].get_texture()
	main.prev0.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	main.prev0.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	main.prev0.custom_minimum_size = Vector2(300, 169)
	cm.add_child(main.prev0)
	var row := HBoxContainer.new()
	cm.add_child(row)
	main.prev1 = TextureRect.new()
	main.prev1.texture = main.vps[1].get_texture()
	main.prev1.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	main.prev1.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	main.prev1.custom_minimum_size = Vector2(146, 82)
	row.add_child(main.prev1)
	main.prevt = TextureRect.new()
	main.prevt.texture = main.th_preview
	main.prevt.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	main.prevt.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	main.prevt.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	main.prevt.custom_minimum_size = Vector2(146, 112)
	row.add_child(main.prevt)
	# tools: MoveEye on this PC, map, phone
	var tl = main.UI.fold_card(box_, "Testen", true, "check")      # 3D-3.90: everything that measures or tests MoveEye in one card; Menüs A: symbol «check» like the group (not the spanner of «Entwickler»)
	main.fold_bodies.append(tl)
	main.tools_body = tl
	main.top_cards.append(tl.get_meta("card"))
	main.mwpc_btn = Button.new()
	main.mwpc_btn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	main.mwpc_btn.pressed.connect(func(): main.mwpc.toggle())
	main.UI.primary(main.mwpc_btn)
	tl.add_child(main.mwpc_btn)
	main.mwpc_label = main.UI.small("")
	tl.add_child(main.mwpc_label)
	var tl_main = tl                                # 3D-3.86: the rest in folds - tests for MoveEye, training pictures, more
	tl = main.UI.sub_fold(tl_main, "Erkennung messen (Testlauf, Prüfstand, blinde Flecken)", true)
	tl.set_meta("always", true)
	main.sub_bodies.append(tl)
	main.testen_measure = tl                              # 3D-4.x: the group «Testlauf» lives here now (one place for testing)
	main.testen_rec = main.UI.sub_fold(tl_main, "Aufnahme: Besuch aufnehmen und genau gleich abspielen", false)
	main.testen_rec.set_meta("always", true)
	main.sub_bodies.append(main.testen_rec)
	var trh := HBoxContainer.new()
	trh.add_theme_constant_override("separation", 6)
	tl.add_child(trh)
	var trp := OptionButton.new()
	for p_ in ["quick", "standard", "night", "hard", "wetter"]:      # real-wetter: + «Wetter physikalisch»
		trp.add_item(str(TestrunS.PLANS[p_]["name"]).get_slice(" (", 0) + " · " + str(int(round(TestrunS.DAUER[p_] / 30.0)) / 2.0).trim_suffix(".0") + " Min.")
	trp.select(0)
	trh.add_child(trp)
	var trb := Button.new()
	trb.text = "Testlauf starten"
	trb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	trb.pressed.connect(func():
		var r_: String = main.testrun.start(["quick", "standard", "night", "hard", "wetter"][trp.selected])
		if r_ != "":
			main.start_info = r_)
	trh.add_child(trb)
	var bmb := Button.new()
	bmb.text = "Blinde Flecken: Person rund um MoveEye aufstellen"
	bmb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	bmb.pressed.connect(func():
		var r2: Dictionary = main.blindmap.start({})
		if not bool(r2.get("ok", true)):
			main.start_info = "Blinde Flecken: " + str(r2.get("error", "")))
	tl.add_child(bmb)
	var psb := Button.new()                          # Menüs A: the one place of the Prüfstand (no tile, not in the developer window)
	psb.text = "Prüfstand: mehrere Testläufe, Ergebnis für GitHub"
	psb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	psb.pressed.connect(func(): main.pruef.open(not main.pruef.visible))
	tl.add_child(psb)
	main.expert_cards.append(bmb)                         # Menüs A: «Einfach» = Testlauf, Aufnahme, Parcours, Einbruch - the rest «Experte»
	main.expert_cards.append(psb)
	tl = main.UI.sub_fold(tl_main, "Geräusche (Klatschschalter, Gesundheit, Lärm)", false)   # 3D-3.98
	tl.set_meta("always", true)
	tl.set_meta("expert_sub", true)                  # Menüs A: only «Experte» (_apply_simple)
	main.sub_bodies.append(tl)
	tl.add_child(main.UI.small("Das Geräusch kommt von der Person im Bett, sonst vom nächsten Besucher, sonst 2 m vor MoveEye. MoveEye braucht dafür «Klatschschalter» bzw. «Gesundheit» – beim klingelnden Wecker heisst Klatschen schlummern."))
	var sgr := GridContainer.new()
	sgr.columns = 3
	tl.add_child(sgr)
	for b_ in [["Klatschen 2×", "clap", 2], ["Klatschen 3×", "clap", 3], ["Klatschen 4×", "clap", 4], ["Niesen", "sneeze", 1], ["Reden", "voice", 1], ["Rufen", "shout", 1]]:
		var snb := Button.new()
		snb.text = b_[0]
		snb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		snb.pressed.connect(func(): main.emit_sound(b_[1], b_[2]))
		sgr.add_child(snb)
	main.testen_stoer = main.UI.sub_fold(tl_main, "Störungen (Servos, Unterspannung, I2C – reagiert MoveEye richtig?)", false)   # 30.10.2026 (simint.gd)
	main.testen_stoer.set_meta("always", true)
	main.testen_stoer.set_meta("expert_sub", true)        # Menüs A: servo faults, I2C, undervoltage - only «Experte»
	main.sub_bodies.append(main.testen_stoer)
	main.testen_stoer.add_child(main.UI.small("Wie bei echter Hardware: MoveEye stoppt die Servos, meldet die Störung im Fehlerspeicher (Servo-Diagnose) und braucht bei Treiber-Fehlern «Freigeben»."))
	main.simint.add_info(main.testen_stoer, main.UI)
	main.testen_einbruch = main.UI.sub_fold(tl_main, "Einbruch-Abläufe (auskundschaften, ablenken, stehlen – wann warnt MoveEye?)", false)
	main.testen_einbruch.set_meta("always", true)
	main.sub_bodies.append(main.testen_einbruch)
	main.einbruch.add_info(main.testen_einbruch, main.UI)
	tl = main.UI.sub_fold(tl_main, "Diebstahlschutz prüfen (Referenz-Scan, Sabotage, Überraschung)", false)
	tl.set_meta("always", true)
	tl.set_meta("expert_sub", true)                  # Menüs A: only «Experte»
	main.sub_bodies.append(tl)
	# 3D-3.71: the reference scan of MoveEye, started from here
	var rsh := HBoxContainer.new()
	rsh.add_theme_constant_override("separation", 6)
	tl.add_child(rsh)
	for b_ in [["MoveEye: Referenz-Scan", "refscan"], ["Mit Referenz vergleichen", "refcompare"]]:
		var rb := Button.new()
		rb.text = b_[0]
		rb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		rb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		rb.tooltip_text = "MoveEye fährt mit dem Kopf alle Richtungen ab: Referenz-Fotos aufnehmen bzw. vergleichen (Bericht in MoveEye unter Werkzeuge → Referenz-Scan)"
		rb.pressed.connect(main.mw_request.bind(b_[1]))
		rsh.add_child(rb)
	var ntb := Button.new()                          # 3D-3.72
	ntb.text = "Referenz-Scan: am Tag aufnehmen, in der Nacht vergleichen"
	ntb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	ntb.pressed.connect(main.ref_night_test)
	tl.add_child(ntb)
	var gsb := Button.new()                          # 3D-3.98: theft with the GPS module
	gsb.text = "GPS: MoveEye wird weggetragen"
	gsb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	gsb.tooltip_text = "Die GPS-Position wandert mit 1.6 m/s weg (wie zu Fuss). MoveEye braucht «GPS-Modul» und «Diebstahl-Alarm» und muss scharf sein. Nochmals drücken = zurückstellen."
	gsb.pressed.connect(func():
		main.gps_steal(main.gps_steal_t <= 0.0)
		gsb.text = "GPS: zurückstellen" if main.gps_steal_t > 0.0 else "GPS: MoveEye wird weggetragen")
	tl.add_child(gsb)
	# 3D-4.7 («Dinge wegnehmen zusammenlegen»): ONE list of the things to take away - «Bewachte Sachen» in «Gegenstände»
	var pgb := Button.new()
	pgb.text = "→ Bewachte Sachen: Velo, Zelt, Tisch, Kühlbox, Grill wegnehmen – merkt MoveEye, dass etwas fehlt?"
	pgb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	pgb.pressed.connect(func(): main.inventar.open_sec("guard"))   # 3D-4.22: window «Gegenstände», part «Bewachte Sachen»
	tl.add_child(pgb)
	tl.add_child(main.UI.small("Sabotage-Test für den Diebstahlschutz von MoveEye (scharf schalten):"))
	var sg := HBoxContainer.new()
	sg.add_theme_constant_override("separation", 6)
	tl.add_child(sg)
	for b2 in [["Kamera abdecken", "cover"], ["Kopf wegdrehen", "turn"], ["Alles normal", "off"]]:
		var sb_ := Button.new()
		sb_.text = b2[0]
		sb_.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		sb_.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		sb_.pressed.connect(main._sabotage_btn.bind(str(b2[1])))
		sg.add_child(sb_)
	main.refscan_label = main.UI.small("")
	tl.add_child(main.refscan_label)
	tl.add_child(main.UI.small("Überraschung jetzt auslösen (bewertet MoveEye; nachts von selbst: Wetter → Überraschungsnacht):"))
	var sug := GridContainer.new()                   # 3D-3.75
	sug.columns = 3
	sug.add_theme_constant_override("h_separation", 6)
	sug.add_theme_constant_override("v_separation", 6)
	tl.add_child(sug)
	for kk in main.surprise.KINDS + [["morning", "Bewertung jetzt"]]:
		var ub := Button.new()
		ub.text = kk[1]
		ub.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		ub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		var key_: String = kk[0]
		ub.pressed.connect(func(): main.surprise.morning() if key_ == "morning" else main.surprise.start(key_))
		sug.add_child(ub)
	main.surprise_label = main.UI.small("")
	tl.add_child(main.surprise_label)
	tl = main.UI.sub_fold(tl_main, "Trainingsbilder für eine eigene KI", false)
	main.testen_train = tl
	tl.set_meta("always", true)
	main.sub_bodies.append(tl)
	var dsr := HBoxContainer.new()                   # 3D-3.74: a training set for an own AI model
	dsr.add_theme_constant_override("separation", 6)
	tl.add_child(dsr)
	var dsn := OptionButton.new()
	for n_ in [200, 500, 1000, 2000]:
		dsn.add_item("%d Bilder" % n_)
	dsn.select(1)
	dsr.add_child(dsn)
	var dsb := Button.new()
	dsb.text = "Trainingspaket (YOLO) machen"
	dsb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	dsb.tooltip_text = "Bilder mit Rahmen für ein eigenes KI-Modell: viele Szenen, Tag, Nacht, Regen, Nebel, Schnee, Menschen und Tiere. ZIP auf den Schreibtisch."
	dsb.pressed.connect(func():
		if main.dataset.busy:
			main.dataset.stop()
		else:
			main.dataset.export_pack([200, 500, 1000, 2000][dsn.selected], true))
	dsr.add_child(dsb)
	main.ds_label = main.UI.small("")
	tl.add_child(main.ds_label)
	main.kitrain.build(tl, dsn)                           # Vielfalt normal / hoch, «KI trainieren» (kitrain.gd)
	var kdr := HBoxContainer.new()                   # «KI-Daten aufräumen» (kidaten.gd)
	kdr.add_theme_constant_override("separation", 6)
	tl.add_child(kdr)
	var kdl = main.UI.small(preload("res://scripts/kidaten.gd").summary())
	kdl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	kdl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var kdb := Button.new()
	kdb.text = "Alte KI-Daten löschen"
	kdb.tooltip_text = "Löscht alle Trainingspakete ausser dem neuesten (Ordner und ZIP). Das KI-Modell bleibt."
	kdb.pressed.connect(func():
		if main.dataset.busy or main.kitrain.running:
			kdl.text = "Gerade beschäftigt – später nochmals."
			return
		var KD = preload("res://scripts/kidaten.gd")
		var r: Dictionary = KD.aufraeumen(true, str(main.dataset.last_pack.get("dir", "")).get_file())
		kdl.text = "Gelöscht: %d Pakete (%.0f MB) · %s" % [int(r["deleted"]), float(r["freed_mb"]), KD.summary()])
	kdr.add_child(kdb)
	kdr.add_child(kdl)
	# Menüs A, Punkt 5 (Besitzer 31.10.2026): the part «Mehr: Aufstellen, Erkunden, Handy-Simulator» is gone - Aufstell-Planer =
	# tile «Aufstellen», Erkunden = bar below, Handy-Simulator = System → Karte und Livebild (phone_sim), Rückmeldung = «Mehr»
	# the settings of the simulator: one card per group (with a symbol), parts inside (the same list the page of Motion
	# Watch shows, in the same order - GROUPS / PLACE)
	var groups := {}
	var subs := {}
	var fine_folds := {}
	for c in main.controls:
		if c.extra.get("hide", false) or c.extra.get("wiz", false) or c.extra.get("devwin", false):
			continue                                     # 3D-3.90: only for MoveEye (the web page), not in the window; 3D-4.7: «wiz» = only in the game assistant; «devwin»: in the window «Mehr → Entwickler» (tab «Schalter» / «Spieltest»)
		if c.group == "Testen" and main.testen_measure != null:   # 3D-4.x: into the card «Testen» (no own card «Testlauf» any more)
			if c.id in ["testrun_plan", "testrun_start"]:
				continue                                 # the card has its own row «plan + Testlauf starten»
			var tgt: VBoxContainer = main.testen_rec if c.id.begins_with("rec_") else (main.testen_stoer if c.id.begins_with("stoer_") and main.testen_stoer != null else main.testen_measure)
			if c.id.begins_with("einbruch_") and main.testen_einbruch != null:
				tgt = main.testen_einbruch

			var k0 = main.ui_items.size()
			main._ui_control(tgt, c)
			for i in range(k0, main.ui_items.size()):
				main.ui_items[i][3] = main.tools_body
				main.ui_items[i].append(tgt)
			continue
		if not groups.has(c.group):
			var ic := ""
			for g in main.GROUPS:
				if g[0] == c.group:
					ic = g[1]
			groups[c.group] = main.UI.fold_card(box_, c.group, c.group in ["Szene", "Besuch"], ic)
			main.group_bodies[c.group] = groups[c.group]
			main.fold_bodies.append(groups[c.group])
			main.setting_bodies.append(groups[c.group])
		if c.group == "Besuch" and str(c.extra.get("sub", "")) != "Vorlagen" and not subs.has("Besuch/Besucher hinsetzen"):
			# after «Vorlagen»: the pictures of the visitors, people and animals apart (3D-3.38)
			var vs = main.UI.sub_fold(groups[c.group], "Besucher hinsetzen", true)
			vs.set_meta("always", true)
			main.sub_bodies.append(vs)
			subs["Besuch/Besucher hinsetzen"] = vs
			var ivb := Button.new()                  # 3D-3.86: all people, animals and things in the inventory
			ivb.text = "«Gegenstände» öffnen"
			ivb.tooltip_text = "Zelt, Auto, bewachte Sachen, Menschen, Tiere und alle 80 Dinge der KI"
			ivb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			main.UI.primary(ivb)
			ivb.pressed.connect(func(): main.inventar.toggle())
			vs.add_child(ivb)
			vs.add_child(main.UI.small("Bild in die Welt ziehen – oder anklicken und dann in die Welt klicken. Die Knöpfe weiter unten schicken Besuch, der von selbst daherkommt."))
		var card_body: VBoxContainer = groups[c.group]
		var target: VBoxContainer = card_body
		var sub := str(c.extra.get("sub", ""))
		var to_fine: bool = c.extra.get("expert", false) and c.group != "Entwickler"
		if sub == "Feineinstellungen":                    # 3D-4.22: a part named «Feineinstellungen» = the one fold of the card (not two)
			sub = ""
			to_fine = true
		if sub != "":
			var key: String = c.group + "/" + sub
			if not subs.has(key):
				subs[key] = main.UI.sub_fold(card_body, sub, sub in ["Vorlagen", "Menschen einzeln", "Wildtiere"])
				main.sub_bodies.append(subs[key])
			target = subs[key]
		# 3D-4.21 (Menü 2, same rule as MoveEye): «Einfach» shows the main switches, the rest sits in a closed «Feineinstellungen»
		var folded := false
		if to_fine:
			var fk := str(target.get_instance_id())
			if not fine_folds.has(fk):
				var fb = main.UI.sub_fold(target, "Feineinstellungen", false)
				if target != card_body:
					fb.set_meta("outer", target)
				fine_folds[fk] = fb
				main.sub_bodies.append(fb)
				main.fine_bodies.append(fb)
			target = fine_folds[fk]
			folded = true
		var n0 = main.ui_items.size()
		main._ui_control(target, c)
		for i in range(n0, main.ui_items.size()):
			main.ui_items[i][3] = card_body
			main.ui_items[i].append(target)
			if folded:
				main.ui_items[i][2] = false                     # not hidden in «Einfach» - folded
	for fb in fine_folds.values():                     # «Feineinstellungen» last in its part / card
		var w: Control = fb.get_meta("wrap")
		w.get_parent().move_child(w, -1)
	if groups.has("Entwickler"):
		# 3D-4.22 (Angleichen, Besitzer 30.10.2026): «Entwickler» like MoveEye - shown when MoveEye's «Entwickler-Bereich» is on
		# (dev_area, sent by MoveEye), no longer tied to «Experte». Paket «Entwickler zusammenlegen»: the card has only the
		# button «Entwickler-Fenster öffnen» (dev_open); «Diagnose-Paket» is in the window (devtool_schalter.gd); only the owner
		main.dev_body = groups["Entwickler"]
	main.update_btn = Button.new()
	main.update_btn.text = "Nach Updates suchen (jetzt %s)" % main.VERSION
	main.update_btn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	main.update_btn.pressed.connect(main.check_updates)
	(subs.get("System/Updates", tl) as Control).add_child(main.update_btn)
	if main.testen_measure != null:
		main.testrun.add_info(main.testen_measure, main.UI)          # progress and result of the test run (card «Testen»)
		main.nacht.add_info(main.testen_measure, main.UI)            # Nacht-Testlauf: progress, «abbrechen»
	elif groups.has("Testen"):
		main.testrun.add_info(groups["Testen"], main.UI)
	if subs.has("Licht & Ton/Status-LED & Tasten") and main.statusled != null:   # 3D-4.22: the rules of the buttons are in MoveEye - hint + link
		main.statusled.add_info(subs["Licht & Ton/Status-LED & Tasten"], main.UI)
	if subs.has("Zusatzgeräte/Bewegungsmelder (PIR)"):    # real-pir-ton: state, reach, triggers (pir.gd)
		main.pir.add_info(subs["Zusatzgeräte/Bewegungsmelder (PIR)"], main.UI)
	if subs.has("Licht & Ton/Mikrofon"):              # real-pir-ton: level, background, the loudest sources (mikrofon.gd)
		main.mikro.add_info(subs["Licht & Ton/Mikrofon"], main.UI)
	if subs.has("Zusatzgeräte/Strom"):                # Simulator-Werte: what goes to MoveEye (power.gd)
		main.simwerte.add_info(subs["Zusatzgeräte/Strom"], main.UI)
	if subs.has("Kamerabild/Wie echt"):              # 3D-3.94: what the real look adjustment does
		main.real_label = main.UI.small("")
		main.real_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		subs["Kamerabild/Wie echt"].add_child(main.real_label)
	if subs.has("Spiel/Runde"):
		main.game.add_info(subs["Spiel/Runde"], main.UI)        # address, QR code and players of the game
	elif groups.has("Spiel"):
		main.game.add_info(groups["Spiel"], main.UI)
	var keys = main.UI.fold_card(box_, "Tasten", false, "keys")
	main.fold_bodies.append(keys)
	main.info_label = main.UI.small("Maus: links ziehen = verschieben · rechts ziehen = drehen · Rad = zoomen (Shift + Rad: Tempo von W A S D) · mittlere Taste oder Alt + rechts = umschauen · Doppelklick = hinfliegen · Besucher anklicken = auswählen, ziehen = tragen.  Tasten: W A S D Q E fliegen (Shift schneller) · 1 / 2 Kamera · 3 Wärmebild · 0 frei · F folgen · Entf entfernen · Esc abwählen · H Bedienfeld · P Handy / Tablet · K Karte · G Gewehr (Linksklick = Schuss)")
	keys.add_child(main.info_label)
	var kb := Button.new()                                  # tasten.gd: keys instead of the mouse wheel (touchpad without scrolling)
	kb.text = T.t("Tasten ohne Mausrad (F1)")
	kb.tooltip_text = T.t("+ / − zoomen · Bild ↑ / ↓ blättern · Pfeile drehen und neigen")
	kb.pressed.connect(func(): main.tasten.show_help(true))
	keys.add_child(kb)
	main.expert_cards.append(keys.get_meta("card"))
	main.top_cards.append(keys.get_meta("card"))
	main.mehr = preload("res://scripts/mehr.gd").new()      # 3D-4.2x: card «Mehr» like MoveEye (Hilfe, Rundgang, Diagnose, Protokoll, Ansicht, Rückmeldung, Über)
	main.mehr.main = main
	main.add_child(main.mehr)
	main.mehr.build(box_)
	if preload("res://scripts/hp_kiosk.gd").helper_path() != "":   # only in the kiosk of the simulator PC (kiosk_sitzung.sh): Controller koppeln, Browser, Ausschalten
		main.hp_kiosk = preload("res://scripts/hp_kiosk.gd").new()
		main.hp_kiosk.main = main
		main.add_child(main.hp_kiosk)
		main.hp_kiosk.build(box_)
	# Kinder | Erwachsene: on top (3D-3.90); Einfach | Experte is in the bar (leiste)
	var se: Control = main.simple_seg
	main.kids_seg = main.UI.segment("Kinder", "Erwachsene", not main.kids_on, func(adult): main._kids_switch(adult), true)   # 3D-3.69
	main.kids_seg.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	main._mode_row.add_child(main.kids_seg)
	se.tooltip_text = "Einfach: das Wichtigste (Szene, Zeit, Wetter, Besuch, Testen, Spiel-Assistent). «Experte» zeigt alle."
	main.simple_note = main.UI.small("")                      # 3D-3.94: the explanation as a tooltip, no line of its own
	main.simple_note.visible = false
	main._apply_simple()
	main._sync_ui()
	main._fold_setup()                                      # nurgruppen: the own open / closed state, then «Nur Gruppen» on start
	await main._make_thumbs()
	main.kids = preload("res://scripts/kids.gd").new()       # 3D-3.69: the panel of the «Kinder» mode (after the pictures)
	main.kids.main = main
	box_.add_child(main.kids)
	box_.move_child(main.kids, 0)
	main._apply_kids()


func _build_view_bar(layer: CanvasLayer, th: Theme) -> void:
	"""buttons at the bottom of the view, a compass at the top left, the box of the chosen visitor"""
	main.thermal_full = TextureRect.new()
	main.thermal_full.texture = main.th_preview
	main.thermal_full.set_anchors_preset(Control.PRESET_FULL_RECT)
	main.thermal_full.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	main.thermal_full.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	main.thermal_full.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	main.thermal_full.mouse_filter = Control.MOUSE_FILTER_IGNORE
	main.thermal_full.visible = false
	layer.add_child(main.thermal_full)
	layer.move_child(main.thermal_full, 0)
	main.view_bar = HBoxContainer.new()
	main.view_bar.theme = th
	main.view_bar.add_theme_constant_override("separation", 6)
	main.view_bar.anchor_top = 1.0
	main.view_bar.anchor_bottom = 1.0
	main.view_bar.offset_left = 12
	main.view_bar.offset_top = -50
	main.view_bar.offset_bottom = -12
	main.view_bar.grow_vertical = Control.GROW_DIRECTION_BEGIN
	main.view_bar.anchor_right = 1.0
	main.view_bar.offset_right = -404                          # not under the panel
	layer.add_child(main.view_bar)
	for k in [[0, "Frei", "Frei herumfliegen (0)"], [1, "Kamera 1", "Durch die Kopfkamera schauen (1)"], [2, "Kamera 2", "Durch die zweite Kamera schauen (2)"],
			[3, "Wärmebild", "Das Wärmebild gross (3)"]]:
		var b := Button.new()
		b.text = k[1]
		b.tooltip_text = k[2]
		b.toggle_mode = true
		b.focus_mode = Control.FOCUS_NONE
		var m: int = k[0]
		b.pressed.connect(func(): main.set_view(m))
		main.view_bar.add_child(b)
		main.view_btns[m] = b
	main.map_btn = Button.new()
	main.map_btn.text = "Karte"
	main.map_btn.tooltip_text = "Übersichtskarte ein / aus (M)"
	main.map_btn.toggle_mode = true
	main.map_btn.focus_mode = Control.FOCUS_NONE
	main.map_btn.button_pressed = main.map_on
	main.map_btn.toggled.connect(func(on): main.set_map(on))
	main.view_bar.add_child(main.map_btn)
	main.live_btn = Button.new()
	main.live_btn.text = "Livebild"
	main.live_btn.tooltip_text = "Livebild einer Kamera unter der Karte ein / aus (L)"
	main.live_btn.toggle_mode = true
	main.live_btn.focus_mode = Control.FOCUS_NONE
	main.live_btn.button_pressed = main.live_on
	main.live_btn.toggled.connect(func(on): main.set_live(on))
	main.view_bar.add_child(main.live_btn)
	for k in [["head", "Zum Kopf", "Zurück zu MoveEye"], ["top", "Von oben", "Von oben auf den Platz schauen"]]:
		var b := Button.new()
		b.text = k[1]
		b.tooltip_text = k[2]
		b.focus_mode = Control.FOCUS_NONE
		var w: String = k[0]
		b.pressed.connect(func(): main._view_preset(w))
		main.view_bar.add_child(b)
	main.set_view(main.view_mode)
	var help = main.UI.small("Links ziehen: verschieben · Rechts ziehen: drehen · Rad: zoomen · Doppelklick: hinfliegen")
	main.view_help = help
	help.add_theme_color_override("font_color", Color(1, 1, 1, 0.75))
	help.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.8))
	help.add_theme_constant_override("shadow_offset_x", 1)
	help.add_theme_constant_override("shadow_offset_y", 1)
	help.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	help.autowrap_mode = TextServer.AUTOWRAP_OFF
	help.clip_text = true
	help.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	help.custom_minimum_size = Vector2(10, 0)
	help.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	main.view_bar.add_child(help)
	# compass: the red needle shows north; a click turns the view to the north
	main.compass = Control.new()
	main.compass.position = Vector2(14, 26)
	main.compass.size = Vector2(54, 54)
	main.compass.tooltip_text = "Norden – anklicken: nach Norden schauen"
	main.compass.draw.connect(func():
		var c = main.compass.size / 2.0                        # Paket «Fenster»: in the middle of its frame (room for the «N»)
		main.compass.draw_circle(c, 25, Color(0.05, 0.07, 0.1, 0.75))
		main.compass.draw_arc(c, 25, 0, TAU, 32, Color(1, 1, 1, 0.35), 1.5, true)
		var fwd = -main.view_cam.global_transform.basis.z
		var a := atan2(fwd.x, -fwd.z)                      # 0 = looking north
		var n := Vector2(sin(-a), -cos(-a))
		main.compass.draw_colored_polygon(PackedVector2Array([c + n * 19, c + n.orthogonal() * 5, c - n.orthogonal() * 5]), Color(0.95, 0.3, 0.25))
		main.compass.draw_colored_polygon(PackedVector2Array([c - n * 19, c + n.orthogonal() * 5, c - n.orthogonal() * 5]), Color(0.85, 0.87, 0.9))
		main.compass.draw_string(ThemeDB.fallback_font, c + n * 33 + Vector2(-4, 4), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 1, 1, 0.95)))
	main.compass.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
			main.set_view(0)
			var p = main.view_cam.global_position
			var fwd = -main.view_cam.global_transform.basis.z
			var tilt := asin(clampf(fwd.y, -1.0, 1.0))
			var start = main.view_cam.global_transform
			var end := Transform3D(Basis.from_euler(Vector3(tilt, 0.0, 0.0)), p)
			if main.fly_tw != null:
				main.fly_tw.kill()
			main.fly_tw = main.create_tween()
			main.fly_tw.tween_method(func(f: float): main.view_cam.global_transform = start.interpolate_with(end, f), 0.0, 1.0, 0.5))
	layer.add_child(main.compass)
	main.sel_ring = Control.new()                              # a ring round the chosen visitor
	main.sel_ring.set_anchors_preset(Control.PRESET_FULL_RECT)
	main.sel_ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	main.sel_ring.draw.connect(func():
		if main.selected == null or not is_instance_valid(main.selected) or main.view_mode != 0:
			return
		var w: Vector3 = main.selected.global_position
		if main.view_cam.is_position_behind(w):
			return
		var pts := PackedVector2Array()
		for i in range(33):
			var a := TAU * i / 32.0
			pts.append(main.view_cam.unproject_position(w + Vector3(cos(a), 0.05, sin(a)) * (main.selected.radius + 0.35)))
		main.sel_ring.draw_polyline(pts, Color(1.0, 0.75, 0.2, 0.95), 2.5, true))
	layer.add_child(main.sel_ring)
	layer.move_child(main.sel_ring, 1)
	main.minimap = preload("res://scripts/minimap.gd").new()
	main.minimap.main = main
	main.minimap.size_px = main.map_size
	main.minimap.span = main.map_span
	main.minimap.visible = main.map_on
	layer.add_child(main.minimap)
	main.liveview = preload("res://scripts/liveview.gd").new()
	main.liveview.main = main
	main.liveview.cam = main.live_cam
	main.liveview.width_px = main.live_size
	main.liveview.visible = main.live_on
	layer.add_child(main.liveview)
	if main.statusled != null:
		main.statusled.make_tile(layer)                         # das Fenster «Gerät» (LED + Tasten)
	if main.smalltv != null:
		main.smalltv.make_tile(layer)                           # 3D-4.19: das Bild des virtuellen SmallTV, unter Karte / Livebild
	main.rover_pad = preload("res://scripts/rover_pad.gd").new()
	main.rover_pad.main = main
	layer.add_child(main.rover_pad)
	main.explore = preload("res://scripts/explore.gd").new()       # 3D-3.55: explore with the rover
	main.explore.main = main
	layer.add_child(main.explore)
	main.padview = preload("res://scripts/padview.gd").new()       # the «Controller-Ansicht» of MoveEye: views, turning, zoom, picture without buttons
	main.padview.main = main
	main.add_child(main.padview)
	main.padmap = preload("res://scripts/padmap.gd").new()         # 3D-4.13: ONE controller mapping (window, explore, game, MoveEye)
	main.padmap.main = main
	main.add_child(main.padmap)
	main.padhud = preload("res://scripts/padhud.gd").new()         # 3D-4.13: chips, direction, focus ring of the controller
	main.padhud.main = main
	main.padhud.pm = main.padmap
	var phl := CanvasLayer.new()                              # above the control panel (the focus ring), below the game at the PC
	phl.layer = 25
	main.add_child(phl)
	phl.add_child(main.padhud)
	main.padmap.hud = main.padhud
	main.patrol = preload("res://scripts/patrol.gd").new()         # 3D-3.61: the mover drives MoveEye round a route
	main.patrol.main = main
	main.add_child(main.patrol)
	main.patrol.load_route()
	main.toolbar = preload("res://scripts/toolbar.gd").new()       # 3D-3.61: everything with the mouse
	main.toolbar.main = main
	layer.add_child(main.toolbar)
	main.headpad = preload("res://scripts/headpad.gd").new()       # 3D-3.77: steer the head of MoveEye
	main.headpad.main = main
	main.headpad.theme = th
	layer.add_child(main.headpad)
	main.templates = preload("res://scripts/templates.gd").new()   # 3D-3.82: «Vorlagen»
	main.templates.main = main
	main.templates.theme = th
	layer.add_child(main.templates)
	if main.scene == "vorlage":
		main.set_scene("vorlage")                                   # built before the window existed: once more with the files
	main.inventar = preload("res://scripts/inventar.gd").new()     # 3D-3.86: the inventory (all 80 things of the AI)
	main.inventar.main = main
	main.inventar.theme = th
	layer.add_child(main.inventar)
	main.inventar.rebuild()
	main.blindmap = preload("res://scripts/blindmap.gd").new()     # 3D-3.85: blind spots / night rehearsal
	main.blindmap.main = main
	main.add_child(main.blindmap)
	main.overlay = preload("res://scripts/overlay3d.gd").new()     # 3D-3.83: zones and detections of MoveEye in 3D
	main.overlay.main = main
	main.add_child(main.overlay)
	main.news = preload("res://scripts/news.gd").new()             # 3D-3.82: «Neu in dieser Version» after an update
	main.news.main = main
	main.news.theme = th
	layer.add_child(main.news)
	main.get_tree().create_timer(3.0).timeout.connect(func(): main.news.check())
	main.localplay = preload("res://scripts/localplay.gd").new()   # 3D-3.77: play here at the PC
	main.localplay.main = main
	main.localplay.theme = th
	var lp_layer := CanvasLayer.new()                         # above everything of the window
	lp_layer.layer = 30
	main.add_child(lp_layer)
	lp_layer.add_child(main.localplay)
	main.home_editor = preload("res://scripts/home_editor.gd").new()   # 3D-3.73: «Mein Zuhause bauen»
	main.home_editor.main = main
	main.home_editor.theme = th
	main.home_editor.position = Vector2(10, 345)
	layer.add_child(main.home_editor)
	# the chosen visitor
	main.sel_box = PanelContainer.new()
	main.sel_box.theme = th
	main.sel_box.add_theme_stylebox_override("panel", main.UI.box(Color(main.UI.PANEL, 0.95), main.UI.LINE, 10, 8))
	main.sel_box.anchor_top = 1.0
	main.sel_box.anchor_bottom = 1.0
	main.sel_box.offset_left = 12
	main.sel_box.offset_top = -104
	main.sel_box.offset_bottom = -58
	main.sel_box.grow_vertical = Control.GROW_DIRECTION_BEGIN
	main.sel_box.visible = false
	layer.add_child(main.sel_box)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 6)
	main.sel_box.add_child(hb)
	main.sel_label = Label.new()
	main.sel_label.custom_minimum_size = Vector2(90, 0)
	main.sel_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	hb.add_child(main.sel_label)
	main.follow_btn = Button.new()
	main.follow_btn.focus_mode = Control.FOCUS_NONE
	main.follow_btn.pressed.connect(func():
		main.follow = not main.follow
		main._paint_sel())
	hb.add_child(main.follow_btn)
	for k in [["scare", "Erschrecken"], ["away", "Wegschicken"], ["del", "Entfernen (Entf)"]]:
		var b := Button.new()
		b.text = k[1]
		b.focus_mode = Control.FOCUS_NONE
		var w: String = k[0]
		b.pressed.connect(main._sel_action.bind(w))
		hb.add_child(b)
	var x := Button.new()
	x.text = "×"
	x.focus_mode = Control.FOCUS_NONE
	x.pressed.connect(func(): main.select_visitor(null))
	hb.add_child(x)


func _palette_item(kind: String, name_: String) -> Control:
	var pc := PanelContainer.new()
	pc.custom_minimum_size = Vector2(72, 88)
	pc.tooltip_text = name_ + ": in die Welt ziehen, oder anklicken und in die Welt klicken"
	pc.mouse_default_cursor_shape = Control.CURSOR_DRAG
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 2)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc.add_child(v)
	var tr := TextureRect.new()
	tr.custom_minimum_size = Vector2(60, 54)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(tr)
	var l := Label.new()
	l.text = name_
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", 11)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART     # 3D-3.43: long names wrap - before they pushed the panel over the right edge
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(l)
	main.thumb_rects[kind] = tr
	main.palette_items[kind] = pc
	pc.gui_input.connect(func(ev):
		if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT and not ev.pressed and main.drag_kind == "":
			main.place_kind = "" if main.place_kind == kind else kind
			main._paint_palette())
	var drag_fn := func(_pos):
		main.drag_kind = kind
		var pv := TextureRect.new()
		pv.texture = main.thumbs.get(kind)
		pv.custom_minimum_size = Vector2(72, 66)
		pv.size = Vector2(72, 66)
		pv.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		pv.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		pv.modulate = Color(1, 1, 1, 0.85)
		pc.set_drag_preview(pv)
		return {"visitor": kind}
	pc.set_drag_forwarding(drag_fn, func(_p, _d): return false, func(_p, _d): pass)
	main._paint_palette.call_deferred()
	return pc


func _paint_palette() -> void:
	for k in main.palette_items:
		var on: bool = k == main.place_kind
		main.palette_items[k].add_theme_stylebox_override("panel", main.UI.box(main.UI.PANEL if not on else main.UI.ACC.darkened(0.55), main.UI.ACC if on else main.UI.LINE, 10, 4, 2 if on else 1))


func _make_thumbs() -> void:
	"""a little moving picture of every visitor (3D-3.24): each walks on the spot in a small world of its own; only
	the pictures that can be seen are drawn again, about 12 times a second"""
	var sizes := {"person": 1.9, "child": 1.3, "jogger": 1.9, "deer": 1.7, "boar": 1.1, "fox": 0.8, "dog": 0.9, "cat": 0.6, "badger": 0.6, "hare": 0.65, "hedgehog": 0.32,
			"wolf": 1.1, "marten": 0.38, "squirrel": 0.3, "cyclist": 1.9, "stroller": 1.9, "courier": 1.9, "police": 1.9, "drunk": 1.9,
			"cow": 1.7, "sheep": 0.9, "horse": 2.0, "chamois": 1.1, "ibex": 1.3, "lynx": 0.9}
	for k in main.VISITOR_LIST:
		var vp := SubViewport.new()
		vp.size = Vector2i(128, 116)
		vp.transparent_bg = true
		vp.own_world_3d = true
		vp.msaa_3d = Viewport.MSAA_2X
		vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		main.add_child(vp)
		var cam := Camera3D.new()
		cam.cull_mask = 1
		cam.fov = 30
		var e := Environment.new()
		e.background_mode = Environment.BG_CLEAR_COLOR
		e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		e.ambient_light_color = Color(0.75, 0.78, 0.85)
		e.ambient_light_energy = 0.7
		cam.environment = e
		vp.add_child(cam)
		var sun_ := DirectionalLight3D.new()
		sun_.rotation = Vector3(deg_to_rad(-45), deg_to_rad(-35), 0)
		sun_.light_energy = 1.3
		vp.add_child(sun_)
		var a = main.Actor.new()
		a.preview = true
		vp.add_child(a)
		a.setup(main, k[0], Vector3.ZERO, Vector3(-0.8, 0, 1.0), 0.0)
		a.speed = main.THUMB_SPEED.get(k[0], 1.0)
		var h: float = sizes.get(k[0], 1.0)
		var wide: bool = k[0] in ["fox", "deer", "boar", "dog", "cat", "badger", "hare", "hedgehog", "wolf", "marten", "squirrel", "cow", "sheep", "horse",
				"chamois", "ibex", "lynx", "cyclist", "stroller"]
		cam.position = Vector3(h * 1.1, h * 0.62, h * 1.75) * (1.15 if wide else 0.78)
		cam.look_at(Vector3(0, h * 0.48, 0), Vector3.UP)
		main.thumb_vps[k[0]] = [vp, a]
		var t: Texture2D = vp.get_texture()
		main.thumbs[k[0]] = t
		if main.thumb_rects.has(k[0]):
			main.thumb_rects[k[0]].texture = t
		for tb in main.thumb_btns:
			if tb[1] == k[0] and is_instance_valid(tb[0]):
				tb[0].icon = t
		await main.get_tree().process_frame


func ask_adult(done: Callable) -> void:
	"""a little sum for the adults (7 × 8 = ?) before leaving the «Kinder» mode (3D-3.95: can be switched off)"""
	if not main.kids_ask:
		done.call(true)
		return
	if main._adult_box != null and is_instance_valid(main._adult_box):
		main._adult_box.queue_free()
	var a := randi_range(6, 9)
	var b := randi_range(6, 9)
	var pc := PanelContainer.new()
	pc.theme = main.ui_root.theme
	pc.add_theme_stylebox_override("panel", main.UI.box(main.UI.PANEL, main.UI.ACC, 14, 16, 2))
	main.ui_layer.add_child(pc)
	main._adult_box = pc
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	pc.add_child(v)
	v.add_child(main.UI.heading("Frage für Erwachsene"))
	var q := Label.new()
	q.text = "Wie viel ist %d × %d?" % [a, b]
	q.add_theme_font_size_override("font_size", 22)
	v.add_child(q)
	var le := LineEdit.new()
	le.placeholder_text = "Antwort"
	le.virtual_keyboard_type = LineEdit.KEYBOARD_TYPE_NUMBER
	v.add_child(le)
	var msg = main.UI.small("")
	v.add_child(msg)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	v.add_child(h)
	var ok_b := Button.new()
	ok_b.text = "Weiter"
	main.UI.primary(ok_b)
	var no_b := Button.new()
	no_b.text = "Abbrechen"
	for x in [ok_b, no_b]:
		x.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		x.custom_minimum_size = Vector2(0, 40)
		h.add_child(x)
	var check := func(_t = null):
		if le.text.strip_edges() == str(a * b):
			pc.queue_free()
			done.call(true)
		else:
			msg.text = "Leider falsch – noch einmal."
			le.text = ""
	ok_b.pressed.connect(check)
	le.text_submitted.connect(check)
	no_b.pressed.connect(func():
		pc.queue_free()
		done.call(false))
	pc.custom_minimum_size = Vector2(320, 0)
	await main.get_tree().process_frame
	var vs = main.get_viewport().get_visible_rect().size
	pc.position = (vs - pc.size) / 2.0
	le.grab_focus()


func _fold_state() -> String:
	"""which of the three fold buttons matches what is open now ("" = mixed)"""
	var all_open := true
	var all_closed := true
	var groups := true
	for b in main.fold_bodies:
		if not is_instance_valid(b) or not b.get_parent().visible:
			continue
		var o: bool = b.visible
		all_open = all_open and o
		all_closed = all_closed and not o
		groups = groups and o == main._fold_group_open(b)
	for sb in main.sub_bodies:
		if not is_instance_valid(sb) or not sb.has_meta("fold"):
			continue
		var so: bool = (sb.get_meta("fold") as Control).visible
		all_open = all_open and so
		all_closed = all_closed and not so
		groups = groups and not so
	if main.mine_on:                                        # 639r «Meine Ansicht»: the middle is blue while it is on
		return "mine"
	if all_closed:
		return "close"
	if all_open:
		return "open"
	return "groups" if groups else ""


func _fold_paint() -> void:
	"""light the button of the current fold state (called a few times a second, repaints only on a change)"""
	if main._fold_btns.is_empty():
		return
	var st = main._fold_state()
	if st == main._fold_lit:
		return
	main._fold_lit = st
	for k in main._fold_btns:
		var b: Button = main._fold_btns[k]
		for n in ["normal", "hover", "pressed"]:
			if k == st:
				b.add_theme_stylebox_override(n, main.UI.box(main.UI.ACC, main.UI.ACC, 10))
			else:
				b.remove_theme_stylebox_override(n)


func _fold_group_open(b: Control) -> bool:
	"""«Nur Gruppen» like MoveEye (Paket angleich, Besitzer 31.10.2026): the groups open, their parts (Themen) closed.
	3D-4.12 (Besitzer): «Verbindung» stays closed; «Tasten» is a help card, no group"""
	return not str(b.get_meta("title", "")) in ["Verbindung", "Tasten"]


func _fold_all(how: String, _own) -> void:
	"""639r: «mine» = Meine Ansicht (the own state); «close» / «open» / «groups»: Meine Ansicht off, the own state stays as kept"""
	main._fold_lit = "-"
	if how == "mine":
		main.set_mine()
		return
	main.mine_on = false
	for b in main.fold_bodies:
		main.UI.set_open(b, how == "open" or (how == "groups" and main._fold_group_open(b)))
	for sb in main.sub_bodies:
		main.UI.set_sub_open(sb, how == "open")


func _fold_key(b: Control) -> String:
	if b.has_meta("fold"):                             # a part (sub_fold): its card in front, the names are not unique
		var w: Node = b.get_meta("wrap")
		var par: Node = w.get_parent() if w != null else null
		return "s:%s/%s" % [str(par.get_meta("title", "")) if par != null else "", str(b.get_meta("title", ""))]
	return "c:" + str(b.get_meta("title", ""))


func _fold_is_open(b: Control) -> bool:
	return (b.get_meta("fold") as Control).visible if b.has_meta("fold") else b.visible


func _fold_put(b: Control, open: bool) -> void:
	if b.has_meta("fold"):
		main.UI.set_sub_open(b, open)
	else:
		main.UI.set_open(b, open)


func _fold_keep(b: Control) -> void:
	if is_instance_valid(b) and main.mine_on:
		main._mine_change(main._fold_key(b), main._fold_is_open(b))


func _mine_change(key: String, open: bool) -> void:
	"""639r: the ONE function per change of «Meine Ansicht» (saved locally; P2 hangs the sync with MoveEye in here)"""
	if not main.mine_on or key == "":
		return
	main.fold_mem[key] = open
	main._settings_dirty = true


func set_mine() -> void:
	"""639r: the middle button «Meine Ansicht» - every card and part as the user left them"""
	main.mine_on = true
	main._fold_own()


func _fold_setup() -> void:
	"""after building the panel: remember how it was built, follow the clicks on the headings, own state, then the start view"""
	for b in main.fold_bodies + main.sub_bodies:
		if not is_instance_valid(b):
			continue
		main._fold_init[main._fold_key(b)] = main._fold_is_open(b)
		var hdr: Node = null
		if b.has_meta("fold"):
			var w: Node = b.get_meta("wrap")
			hdr = w.get_child(1) if w != null and w.get_child_count() > 1 else null
		elif b.get_parent() != null:
			hdr = b.get_parent().get_child(0)
		if hdr is Button:
			(hdr as Button).pressed.connect(func(): main._fold_keep(b))   # after the heading's own handler: the new state
	if not main.mine_mig:                                   # 639r: once - who had «Beim Start: Nur Gruppen» gets it as the first Meine Ansicht
		main.mine_mig = true
		main._settings_dirty = true
		if main.start_groups:
			main.start_groups = false
			if main._sg_cb != null:
				main._sg_cb.set_pressed_no_signal(false)
			main._fold_all("groups")
			main.mine_on = true
			for b in main.fold_bodies + main.sub_bodies:
				main._fold_keep(b)
	main.start_groups = false                              # 3.23: the switch is gone - an old saved value is ignored, the start is «Meine Ansicht»
	main._fold_own()
	main.mine_on = true


func _fold_own() -> void:
	"""every card and part as the user left it (cards he never touched: as built)"""
	main._fold_lit = "-"
	for b in main.fold_bodies + main.sub_bodies:
		if is_instance_valid(b):
			var k = main._fold_key(b)
			if main.fold_mem.has(k) or main._fold_init.has(k):
				main._fold_put(b, bool(main.fold_mem.get(k, main._fold_init.get(k))))


func set_start_groups(_on: bool) -> void:
	"""3.23: the switch «Beim Start: Nur Gruppen» is gone (an old call only goes back to «Meine Ansicht»)"""
	main.start_groups = false
	main.set_mine()


func _search(q: String) -> void:
	"""type into the search field: only the matching settings stay, their cards open; empty = everything as before"""
	q = q.strip_edges().to_lower()
	var any := false
	for c in main.top_cards:
		c.visible = q == "" and not (c in main.expert_cards and main.ui_simple)
	var hit_bodies := {}
	for it in main.ui_items:
		var show_it: bool = (q == "" or str(it[1]).to_lower().contains(q)) and not (main.ui_simple and it[2] and q == "") and not main._dev_hidden(it)
		it[0].visible = show_it
		if q != "" and show_it:
			hit_bodies[it[3]] = true
			any = true
			if it.size() > 4 and it[4] != it[3]:
				main.UI.set_sub_open(it[4], true)
				if (it[4] as Control).has_meta("wrap"):
					it[4].get_meta("wrap").visible = true        # Menüs A: a hit in a part that «Einfach» hides («expert_sub»)
				if it[4].has_meta("outer"):
					main.UI.set_sub_open(it[4].get_meta("outer"), true)
	for b in main.setting_bodies:
		b.get_meta("card").visible = q == "" or hit_bodies.has(b)
		if q != "":
			main.UI.set_open(b, hit_bodies.has(b))
	main.search_none.visible = q != "" and not any
	if q == "":
		main._apply_simple()


func _kids_switch(adult: bool) -> void:
	"""the switch «Kinder | Erwachsene»: to the children at once, back to the adults only with a little sum"""
	if not adult:
		main.kids_on = true
		main._settings_dirty = true
		main._apply_kids()
		return
	if not main.kids_on:
		return
	main.ask_adult(func(ok):
		if ok:
			main.kids_on = false
			main._settings_dirty = true
			main._apply_kids()
		else:
			main.kids_seg.get_meta("paint").call(false))


func _apply_kids() -> void:
	"""Kinder: only the panel with the picture buttons and the switch; no search, no tool bar. Erwachsene: as before."""
	if main.ui_box == null or main.kids == null:
		return
	if main.kids_on:
		for c in main.ui_box.get_children():
			c.visible = c == main.kids or c == main.kids_seg or c == main._mode_row
		if main.simple_seg != null:
			main.simple_seg.visible = false
		main.kids._build()
		var sc = main.ui_box.get_parent()
		if sc is ScrollContainer:
			(sc as ScrollContainer).scroll_vertical = 0      # start at the top with the marmot
	else:
		main.kids.visible = false
		for c in main.ui_box.get_children():
			if c != main.kids and c != main.search_none:
				c.visible = true
		if main.simple_seg != null:
			main.simple_seg.visible = true
		var keep = main.kids_on
		main.kids_on = false
		main._apply_simple()
		main.kids_on = keep
	if main.ui_tb != null:
		main.ui_tb.visible = not main.kids_on
	if main.leiste != null:
		main.leiste.visible = not main.kids_on
	if main.toolbar != null:
		main.toolbar.visible = not main.kids_on
	if main.kids_seg != null and main.kids_seg.has_meta("paint"):
		main.kids_seg.get_meta("paint").call(not main.kids_on)


func _apply_simple() -> void:
	"""Simple: settings marked "expert" are hidden (and cards that would be empty)"""
	var counts := {}
	for it in main.ui_items:
		var vis: bool = not (main.ui_simple and it[2])
		if main.dev_body != null and it[3] == main.dev_body:
			vis = main._dev_card_ok()                           # 3D-4.22: «Entwickler» with MoveEye's switch, also in «Einfach» (+ only the owner)
		elif vis and main._dev_hidden(it):
			vis = false                                    # 3D-4.28: «only» (e.g. «Standort im Ferienpark» only in that scene)
		it[0].visible = vis
		if vis:
			counts[it[3]] = true
	for b in main.setting_bodies:
		b.get_meta("card").visible = counts.has(b)
	var sub_counts := {}
	for it in main.ui_items:
		if it.size() > 4 and it[0].visible:
			sub_counts[it[4]] = true
			if (it[4] as Control).has_meta("outer"):          # 3D-4.22: a part with only «Feineinstellungen» stays visible
				sub_counts[it[4].get_meta("outer")] = true
	for sb in main.sub_bodies:
		sb.get_meta("wrap").visible = (sub_counts.has(sb) or sb.has_meta("always")) and not (main.ui_simple and sb.has_meta("expert_sub"))   # Menüs A: «expert_sub» = whole part only «Experte»
	for c in main.expert_cards:
		c.visible = not main.ui_simple
	for fb in main.fine_bodies:                             # 3D-4.21: closed in «Einfach», open in «Experte»
		if is_instance_valid(fb):
			main.UI.set_sub_open(fb, not main.ui_simple)
	if main.simple_note != null:
		main.simple_note.visible = false                    # 3D-3.94: tooltip of the switch instead
	if main.kids_on and main.kids != null:
		main._apply_kids()


func _build_crosshair(layer: CanvasLayer) -> void:
	main.crosshair = Control.new()
	main.crosshair.set_anchors_preset(Control.PRESET_FULL_RECT)
	main.crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	main.crosshair.visible = false
	main.crosshair.draw.connect(func():
		var p: Vector2 = main.crosshair.size / 2.0 if main.look else main.crosshair.get_local_mouse_position()
		var c := Color(1.0, 0.25, 0.2, 0.95)
		main.crosshair.draw_arc(p, 18.0, 0.0, TAU, 40, c, 2.0)
		for d in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]:
			main.crosshair.draw_line(p + d * 8.0, p + d * 30.0, c, 2.0)
		main.crosshair.draw_circle(p, 1.5, c)
		var f := ThemeDB.fallback_font
		var txt = "Gewehr (unblutig): Treffer %d von %d Schüssen · %d Punkte · G: Gewehr aus" % [main.hits, main.shots, main.points]
		main.crosshair.draw_string(f, Vector2(18, 34), txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(1, 1, 1))
		if main.now() - main.shot_msg_t < 2.5:
			main.crosshair.draw_string(f, Vector2(18, 64), main.shot_msg, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, Color(1.0, 0.85, 0.3)))
	layer.add_child(main.crosshair)
	main.shot_sound = AudioStreamPlayer.new()
	main.shot_sound.stream = main._make_sound("shot")
	main.add_child(main.shot_sound)
	main.hit_sound = AudioStreamPlayer.new()
	main.hit_sound.stream = main._make_sound("boing")
	main.add_child(main.hit_sound)


func _build_cpu_pill(layer: CanvasLayer) -> void:
	"""always to see: CPU of this PC and of the simulator (3D-3.26), like in the small box"""
	main.cpu_pill = Label.new()
	main.cpu_pill.add_theme_font_size_override("font_size", 13)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.07, 0.1, 0.72)
	sb.set_corner_radius_all(9)
	sb.content_margin_left = 10
	sb.content_margin_right = 10
	sb.content_margin_top = 3
	sb.content_margin_bottom = 3
	main.cpu_pill.add_theme_stylebox_override("normal", sb)
	main.cpu_pill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	main.cpu_pill.text = "CPU …"
	layer.add_child(main.cpu_pill)


func _hud_layout() -> void:
	if main.compass == null or main.view_bar == null or main.phone == null:
		return
	var vw: float = main.get_viewport().get_visible_rect().size.x
	var right: float = main.ui_root.get_global_rect().position.x if main.ui_root != null and main.ui_root.visible else vw
	var ph: bool = main.phone.visible
	var left: float = main.phone.get_global_rect().end.x + 10.0 if ph else 0.0
	var key = "%s|%d|%d|%d" % [ph, int(left), int(right), int(main.minimap.size.x) if main.minimap != null else 0]
	if key == main._hud_key:
		return
	main._hud_key = key
	if ph:
		if main.fenster == null:                              # Paket «Fenster»: the frames place compass and map (fenster.gd)
			main.compass.position = Vector2(right - 68.0, 26.0)
			if main.minimap != null:
				main.minimap.position = Vector2(right - main.minimap.size.x - 14.0, 92.0)
		main.view_bar.offset_left = left + 12.0
		main.view_bar.offset_right = -(vw - right) - 12.0
		main.view_bar.alignment = BoxContainer.ALIGNMENT_CENTER
		if main.view_help != null:
			main.view_help.visible = false                   # not enough room next to the phone
		var room: float = right - left - 24.0
		var fs: int = 14 if room > 640.0 else (12 if room > 520.0 else 11)
		main.view_bar.add_theme_constant_override("separation", 6 if room > 640.0 else 3)
		for b in main.view_bar.get_children():
			if b is Button:
				b.add_theme_font_size_override("font_size", fs)
	else:
		if main.fenster == null:
			main.compass.position = Vector2(14, 26)
			if main.minimap != null:
				main.minimap.position = Vector2(14, 92)
		main.view_bar.offset_left = 12.0
		main.view_bar.offset_right = -404.0
		main.view_bar.alignment = BoxContainer.ALIGNMENT_BEGIN
		if main.view_help != null:
			main.view_help.visible = true
		main.view_bar.add_theme_constant_override("separation", 6)
		for b in main.view_bar.get_children():
			if b is Button:
				b.remove_theme_font_size_override("font_size")
