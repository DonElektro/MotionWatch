extends SceneTree
## Test der Trailer (trailer.gd, trailer_buehne.gd, trailer_ton.gd) ohne Bild und ohne Welt:
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/trailer_test.gd"   (absoluter Pfad nötig)
## Prüft: Länge je Trailer (≈ 3 Min.), jede Einstellung hat ihre Methoden, jeder Klang lässt sich erzeugen, alle Texte
## (Tafeln, Erzähler) sind in en / fr / it / rm übersetzt, keine Spoiler-Wörter (Steinmännchen, Seeli, Kapelle am Gipfel …).
## Dazu (Fix 3.19.x): der Ton-Plan für den Browser (ton_plan: sortiert, nur bekannte Klänge, Ende = Ausblenden) und die
## WAV-Dateien (wav_bytes: RIFF-Kopf, mono 16 Bit). Ab 01.11.2026 (Klang): jeder Klang als Datei klang/<name>.ogg mit
## Schleife und Pegel (klaenge.json), MP3 für den Browser (klang/web), Schleifenpunkte im Plan, Bus «Trailer» mit Begrenzer.
## Mit «-- --mit-welt» zusätzlich ohne Bild mit der echten Welt (main.tscn, Port 9448): Stopp von aussen (/control wie
## MoveEye am iPad) während MoveEyes Browser-Bild (padview bare) die Knöpfe ausblendet – danach müssen Knöpfe sichtbar,
## Kamera zurück (nicht unter dem Boden), kein schwarzer Film-Layer da sein; dasselbe mit der Vorführung (maggie_vorfuehrung).
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/trailer_test.gd" -- --mit-welt --no-update --no-tour --port 9448
## Ende: «Trailer-Test OK» oder «SCRIPT ERROR: Trailer-Test: …» (Exit-Code 0 / 1).

var errs := []
const VERBOTEN := ["Steinm", "Seeli", "Bergkapelle", "Finale", "Karabiner", "Blechdose", "Geheimwort"]


func _init() -> void:
	var T = load("res://scripts/i18n.gd")
	var B = load("res://scripts/trailer_buehne.gd")
	var Ton = load("res://scripts/trailer_ton.gd")
	var R = load("res://scripts/trailer.gd")
	var tx: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://i18n/texte.json"))
	var keep_lang: String = T.choice()
	T.set_lang("de")                                          # the texts are checked in German (the keys of texte.json)
	var b = B.new()
	for id in R.IDS:
		var shots: Array = b.einstellungen(id)
		var d := 0.0
		for sh in shots:
			d = maxf(d, float(sh["t0"]) + float(sh["d"]))
			var auf := str(sh.get("auf", ""))
			if str(sh.get("art", "")) == "welt" and not b.has_method(auf):
				errs.append("%s: Methode %s fehlt" % [id, auf])
			for c in sh.get("ton", []):
				if str(c[1]) in ["loop", "one", "stop"] and not str(c[2]) in R.KLAENGE:
					errs.append("%s: Klang %s nicht in KLAENGE" % [id, c[2]])
			var texte := []
			for s in sh.get("say", []):
				texte.append(str(s[1]))
			for k in ["text", "sub"]:
				if sh.has(k):
					texte.append(str(sh[k]))
			for t in texte:
				for w in VERBOTEN:
					if t.contains(w):
						errs.append("%s: Spoiler-Wort «%s» in «%s»" % [id, w, t])
				for part in t.split("  ·  "):
					if part.contains("Jahren") or part.contains("Kapitel, je") or part.contains("Stunden"):
						continue                                   # (composed from texts that are translated on their own)
					var row = tx.get(part, null)
					if not (row is Dictionary):
						errs.append("%s: Text nicht in texte.json: %s" % [id, part])
						continue
					for l in ["en", "fr", "it", "rm"]:
						if str(row.get(l, "")) == "":
							errs.append("%s: %s fehlt für «%s»" % [id, l, part])
		print("Trailer %s: %d Einstellungen, %.0f s" % [id, shots.size(), d])
		if d < 165.0 or d > 195.0:
			errs.append("%s: Länge %.0f s statt etwa 180 s" % [id, d])
	b.free()
	T.set_lang(keep_lang if keep_lang != "" else "auto")
	var t0 := Time.get_ticks_msec()
	for k in R.KLAENGE:
		var w = Ton.get_snd(k)
		if w == null or w.get_length() <= 0.0:
			errs.append("Klang %s fehlt" % k)
	print("Klänge erzeugt: %d in %d ms" % [R.KLAENGE.size(), Time.get_ticks_msec() - t0])
	# the sound plan for the browser (MoveEye /sim/trailer: music and noises on the iPad)
	for id in R.IDS:
		var tr = R.new()
		tr.id = id
		var pl: Dictionary = tr.ton_plan()
		tr.free()
		var ev: Array = pl.get("plan", [])
		if ev.size() < 20:
			errs.append("%s: Ton-Plan zu kurz (%d)" % [id, ev.size()])
			continue
		var last := -1.0
		for e in ev:
			if float(e[0]) < last:
				errs.append("%s: Ton-Plan nicht sortiert bei %.2f" % [id, float(e[0])])
				break
			last = float(e[0])
		if str(ev[-1][1]) != "stille" or absf(float(ev[-1][0]) - float(pl["dauer"])) > 0.05:
			errs.append("%s: Ton-Plan endet nicht mit dem Ausblenden" % id)
		for k in pl.get("klaenge", []):
			if not k in R.KLAENGE:
				errs.append("%s: Klang %s im Plan unbekannt" % [id, k])
		var says := ev.filter(func(e): return str(e[1]) == "say").size()
		print("Ton-Plan %s: %d Befehle, %d Klänge, %d Erzählersätze" % [id, ev.size(), (pl.get("klaenge", []) as Array).size(), says])
	# the sounds as files (klang/, Besitzer 01.11.2026): every sound an Ogg with its loop flag and level, MP3 for the browser
	var info: Dictionary = Ton.info()
	for k in R.KLAENGE:
		var w = Ton.get_snd(k)
		if not w is AudioStreamOggVorbis:
			errs.append("Klang %s: keine Datei klang/%s.ogg (nur die alte Synthese)" % [k, k])
			continue
		var e = info.get(k, null)
		if not e is Dictionary or not e.has("db") or absf(float(e["db"])) > 20.0:
			errs.append("Klang %s: kein Pegel in klaenge.json" % k)
		elif bool(e.get("loop", false)) != (w as AudioStreamOggVorbis).loop:
			errs.append("Klang %s: Schleife falsch" % k)
		var mp: PackedByteArray = Ton.web_bytes(k)
		if mp.size() < 1000 or not (mp.slice(0, 3).get_string_from_ascii() == "ID3" or (mp[0] == 0xff and (mp[1] & 0xe0) == 0xe0)):
			errs.append("Klang %s: MP3 für den Browser fehlt oder falsch" % k)
	for id in R.IDS:
		var tr2 = R.new()
		tr2.id = id
		var pl2: Dictionary = tr2.ton_plan()
		tr2.free()
		for e in pl2["plan"]:
			if str(e[1]) in ["loop", "one"] and float(e[3]) > 12.0:
				errs.append("%s: %s zu laut im Plan (%.1f dB)" % [id, e[2], float(e[3])])
		for nm in ["pad_ruhig", "wind"]:
			var lp: Array = (pl2.get("schleifen", {}) as Dictionary).get(nm, [])
			if lp.size() != 2 or float(lp[0]) != 0.1 or float(lp[1]) < 2.0:
				errs.append("%s: Schleifenpunkte für %s fehlen" % [id, nm])
	var wb: PackedByteArray = R.wav_bytes("pad_ruhig")
	if wb.size() < 1000 or wb.slice(0, 3).get_string_from_ascii() != "ID3" and wb[0] != 0xff:
		errs.append("Browser-Klang pad_ruhig ist kein MP3 (%d Bytes)" % wb.size())
	var ws: AudioStreamWAV = Ton.synth("pad_ruhig")             # the old synthesis still works (fallback without files)
	if ws == null or ws.get_length() < 1.0:
		errs.append("alte Synthese pad_ruhig fehlt")
	var lim := AudioServer.get_bus_index(R.bus())
	if lim < 0 or AudioServer.get_bus_effect_count(lim) < 1 or not AudioServer.get_bus_effect(lim, 0) is AudioEffectHardLimiter:
		errs.append("Bus Trailer ohne Begrenzer")
	if not R.wav_bytes("../etc").is_empty():
		errs.append("WAV: unbekannter Name nicht abgewiesen")
	if "--mit-welt" in OS.get_cmdline_user_args():
		_welt_test.call_deferred()
		return
	_ende()


func _ende() -> void:
	if errs.is_empty():
		print("Trailer-Test OK")
		quit(0)
	else:
		for e in errs:
			push_error("Trailer-Test: " + str(e))
		quit(1)


# ---- with the real world (no picture): stop from outside while the browser picture hides the buttons ------------------------
var m = null
var _bare := false


func _process(_dt: float) -> bool:
	if _bare and m != null and m.padview != null:
		m.padview.bare_t = m.now()                          # like MoveEye's page: a picture with bare=1 every few hundred ms
	return false


func _warte(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func _normal_pruefen(was: String, cam0: Transform3D) -> void:
	var vc: Camera3D = m.view_cam
	var tr = load("res://scripts/trailer.gd").inst(m, false)
	if not m.ui_layer.visible:
		errs.append("%s: Knöpfe des Fensters nach dem Stopp unsichtbar" % was)
	if m.padview._hid:
		errs.append("%s: padview blendet noch aus" % was)
	if tr != null and tr._layer != null and tr._layer.visible:
		errs.append("%s: schwarzer Trailer-Layer noch sichtbar" % was)
	var p := vc.global_position
	if p.y < float(m.ground_y(p.x, p.z)) - 1.0:
		errs.append("%s: Kamera unter dem Boden %s" % [was, str(p)])
	if cam0 != Transform3D.IDENTITY and p.distance_to(cam0.origin) > 1.0:
		errs.append("%s: Kamera nicht zurück (%s statt %s)" % [was, str(p), str(cam0.origin)])
	if Engine.time_scale < 0.5:
		errs.append("%s: Zeit steht still" % was)
	print("%s: Knöpfe %s, Kamera %s, Zeit %.1f" % [was, str(m.ui_layer.visible), str(p.snapped(Vector3.ONE * 0.1)), Engine.time_scale])


func _welt_test() -> void:
	m = load("res://main.tscn").instantiate()
	root.add_child(m)
	for i in range(120):
		await process_frame
	await _warte(2.0)
	var R = load("res://scripts/trailer.gd")
	for fall in ["bare_vorher", "bare_nachher"]:
		var cam0: Transform3D = m.view_cam.global_transform
		if fall == "bare_vorher":
			_bare = true                                    # the iPad page asks for pictures before the film starts
			await _warte(0.5)
		var r: Dictionary = m.control({"action": "trailer", "do": "start", "id": "grossvater", "sprache": "de"})
		if not bool(r.get("ok", false)):
			errs.append("Trailer startet nicht: %s" % str(r))
			break
		await _warte(1.5)                                   # (until starten() set t back: info still shows the last run)
		var w := 0
		while w < 240 and float(m.control({"action": "trailer", "do": "info"}).get("t", 0.0)) < 3.0:
			await _warte(0.25)
			w += 1
		_bare = true                                        # (bare_nachher: the page was opened while it ran)
		await _warte(1.0)
		if m.ui_layer.visible:
			errs.append("Trailer (%s): Knöpfe während des Films sichtbar" % fall)
		r = m.control({"action": "trailer", "do": "stop"})
		if bool(r.get("laeuft", true)):
			errs.append("Trailer (%s): Stopp über /control wirkt nicht" % fall)
		await _warte(1.0)                                   # the page is still open for a moment (no more bare: Fix in 639n)
		_bare = false
		await _warte(3.6)                                   # padview gives the buttons back after 3 s, the watchdog after 1.5 / 3 s
		_normal_pruefen("Trailer (%s)" % fall, cam0)
	# the Vorführung: started and stopped from the browser
	var vf = load("res://scripts/maggie_vorfuehrung.gd").inst(m)
	if vf == null:
		errs.append("Vorführung: keine Instanz (main.maggie fehlt)")
	else:
		var cam1 := Transform3D.IDENTITY
		_bare = true
		await _warte(0.5)
		m.control({"action": "vorfuehrung", "do": "start", "len": "kurz"})
		await _warte(6.0)
		if not bool(vf.laeuft):
			errs.append("Vorführung läuft nicht")
		m.control({"action": "vorfuehrung", "do": "pause"})
		await _warte(0.5)
		m.control({"action": "vorfuehrung", "do": "stop"})
		await _warte(1.0)
		_bare = false
		await _warte(3.6)
		_normal_pruefen("Vorführung", cam1)
		if vf._bar != null and vf._bar.visible:
			errs.append("Vorführung: Leiste nach dem Stopp noch sichtbar")
		if vf._schwarz != null and vf._schwarz.color.a > 0.01:
			errs.append("Vorführung: schwarze Blende nach dem Stopp")
	print("Welt-Test fertig")
	_ende()
