extends Node
## Fotorealismus F2 «echte Inhalte» (Daniel 31.10.2026): freie Foto-Inhalte (CC0) für Boden, Wege, Zelt, Bäume und Himmel.
## Quellen: Poly Haven (HDRI-Himmel, Texturen), ambientCG (PBR-Texturen) – Liste mit Lizenz in simulator3d/CREDITS.md.
##
## Die Dateien liegen NICHT im Repository und nicht im Simulator-ZIP (GitHub-Grenze, ZIP schon ~62 MB). Sie werden beim ersten
## Start einer Szene aus `SZENEN` (zuerst «Camping-Platz») nachgeladen und in user://inhalte/ gemerkt:
##   1. das ganze Paket (inhalte/katalog.json → paket.url, ein ZIP als Anhang eines GitHub-Release, gebaut mit
##      werkzeuge/inhalte_paket.py), sonst
##   2. jede Datei einzeln von Poly Haven / ambientCG (katalog.json → inhalte[].laden).
## Wer die Dateien selbst lädt: in den Ordner «inhalte» neben MoveEyeSim3D.exe oder in user://inhalte/ legen (lose Bilder
## mit den Original-Namen oder die ZIP-Dateien von ambientCG / das Paket-ZIP – wird beim nächsten Laden ausgepackt).
## Fehlt eine Datei, bleibt für diese Fläche das bisherige Code-Material (Rauschen, Farbe) – nichts geht kaputt.
##
## Lite (Quality.lite()) und Prüfstand (--quality): aus, nichts wird geladen (Bilder für MoveEye bleiben vergleichbar).
## Grafikstufe «Hoch» (Zweig foto-hoch, grafik_hoch.gd) wird hier NICHT gebaut; sie kann die Materialien mit Meta «inhalte»
## erkennen und in Ruhe lassen (sie hat dann schon echte Texturen).
##
## Einstellung: System → Grafik → «Echte Oberflächen und Himmel (Fotos)» (an / nur Oberflächen / aus), eigene Datei
## user://inhalte.json. Test: /control {"action": "inhalte", "do": info | set (value) | laden | anwenden | zuruecksetzen}.
## Test-Optionen: --inhalte-quelle http://host/ordner/ (statt GitHub / Poly Haven / ambientCG: dort liegen Paket-ZIP und
## Einzeldateien unter ihrem Dateinamen), --inhalte-ordner PFAD (zusätzlicher Ordner mit Dateien), --no-inhalte.

const Quality = preload("res://scripts/quality.gd")
const T = preload("res://scripts/i18n.gd")
const KATALOG := "res://inhalte/katalog.json"
const FILE := "user://inhalte.json"
const DIR := "user://inhalte"
const MODES := [["an", "An: Fotos für Boden, Wege, Zelt, Bäume und Himmel"], ["boden", "Nur Oberflächen (Himmel wie bisher)"],
		["aus", "Aus (bisherige Code-Materialien)"]]
const HDRI_MAX_W := 4096               # Startfix: breitere HDRIs werden beim Einlesen verkleinert (Grafikspeicher, ANGLE)
# Fotos kleiner (Stabil-Start): in der .exe gibt es keine Kompression (siehe _can_compress) - darum dort Fotos höchstens 1024 px
# (RGB8 + Mipmaps ~4 MB statt ~16 MB je Bild) und den Himmel höchstens 2048 × 1024 (RGBH ~16 MB statt ~64 MB).
# Im Editor (Prüfstand, Entwicklung) bleibt es bei 2048 px komprimiert und HDRI_MAX_W.
const TEX_MAX_EDITOR := 2048
const TEX_MAX_EXE := 1024
const HDRI_MAX_W_EXE := 2048
const MARK := "user://inhalte_merker.json"   # Startfix: liegt da, solange Foto-Inhalte eingelesen / angewendet werden
const RETRY_S := 86400.0              # nach einem Fehlschlag frühestens nach einem Tag wieder von selbst laden
const SKY_DAY := "himmel_tag"
const SKY_DUSK := "himmel_daemmerung"

var main
var mode := "an"
var kat := {}                         # inhalte/katalog.json
var szenen: Array = ["camping"]
var tex := {}                         # "id/rolle" -> Texture2D
var mean := {}                        # "id" -> mittlere Farbe der Albedo-Textur
var hdri := {}                        # id -> {tex, sun_u, gain, cap}
var state := "leer"                   # leer | laden | bereit | teilweise | fehlt
var note := ""                        # Zustand in Worten (Anzeige)
var applied := false                  # wirkt gerade in der Szene
var stats := {}                       # Messwerte (Ladezeit, Speicher, Flächen)
var _loaded_ids := {}
var _loading := false
var _auto_tried := false
var _quelle := ""                     # --inhalte-quelle
var _extra_dir := ""                  # --inhalte-ordner
var _off := ""                        # warum aus (Lite, Prüfstand, Einstellung)
var _swapped: Array = []              # [WeakRef MeshInstance3D, altes Material]
var _extras: Array = []               # zusätzliche Flächen (Kies-Rand, Erd-Flecken)
var _mats := {}                       # "slot|farbe|art" -> StandardMaterial3D
var _t := 0.0
var _lite_was := false
var _http: HTTPRequest
var _sky_on := false
var _crash_note := ""                 # Startfix: Hinweis nach einem Absturz beim Laden (einmal als Meldung zeigen)


func _ready() -> void:
	var args := OS.get_cmdline_args() + OS.get_cmdline_user_args()
	for i in range(args.size()):
		if args[i] == "--inhalte-quelle" and i + 1 < args.size():
			_quelle = args[i + 1].trim_suffix("/") + "/"
		elif args[i] == "--inhalte-ordner" and i + 1 < args.size():
			_extra_dir = args[i + 1]
	if "--no-inhalte" in args:
		_off = "Test-Option --no-inhalte"
	elif "--quality" in args:
		_off = "Prüfstand (--quality): Bilder bleiben vergleichbar"
	_load_settings()
	_crash_check()
	_read_katalog()
	_lite_was = Quality.lite()
	call_deferred("on_scene")                 # (kommt die Welt erst nach der Update-Suche: on_scene wartet, siehe _world_ready)


# ---- Einstellung -------------------------------------------------------------------------------------------------------
func _load_settings() -> void:
	if not FileAccess.file_exists(FILE):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
	if typeof(d) == TYPE_DICTIONARY and str(d.get("mode", "")) in ["an", "boden", "aus"]:
		mode = str(d["mode"])


func _crash_check() -> void:
	"""Startfix 31.10.2026: liegt der Merker noch da, ist der letzte Start beim Einlesen / Anwenden der Foto-Inhalte
	abgestürzt. Dann diesmal (und bis man sie wieder einschaltet) ohne Foto-Inhalte, mit Hinweis."""
	if not FileAccess.file_exists(MARK):
		return
	DirAccess.remove_absolute(MARK)
	print("inhalte: the last start crashed while loading the photo contents - switched off (inhalte_merker.json)")
	if mode != "aus":
		mode = "aus"
		_save_settings()
	_crash_note = T.t("Der letzte Start brach beim Einlesen der Foto-Inhalte ab – sie sind jetzt aus (System › Grafik › Experte: «Echte Oberflächen und Himmel»).")
	if main != null:
		main.start_info = _crash_note                     # Statuszeile; dazu eine Meldung, sobald die Welt steht (on_scene)


func _exit_tree() -> void:
	_mark(false)                                          # normal beendet (auch mitten im Laden): kein Absturz


func _mark(on: bool) -> void:
	if on:
		var f := FileAccess.open(MARK, FileAccess.WRITE)
		if f != null:
			f.store_string(JSON.stringify({"t": Time.get_unix_time_from_system()}))
			f.close()                                 # gleich schreiben: ein harter Absturz soll ihn hinterlassen
	elif FileAccess.file_exists(MARK):
		DirAccess.remove_absolute(MARK)


var _unmark_n := 0


func _unmark_soon() -> void:
	"""Startfix: den Merker erst wegnehmen, wenn mit den Fotos (Boden, Himmel) schon einige Bilder gezeichnet sind - ein
	Absturz beim ersten Zeichnen (Grafiktreiber, ANGLE) soll den nächsten Start auch ohne Foto-Inhalte starten lassen"""
	_unmark_n += 1
	var n := _unmark_n
	for i in range(5):                                    # einige Bilder (auf einem langsamen PC 1 Bild/s: nicht zu viele)
		await get_tree().process_frame
	await get_tree().create_timer(3.0).timeout
	if n == _unmark_n and not _loading and is_inside_tree():
		_mark(false)


func _save_settings() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"mode": mode}))


func set_mode(v: String) -> void:
	mode = v if v in ["an", "boden", "aus"] else "an"
	_save_settings()
	on_scene()


func add_controls() -> void:
	var g := {"sub": "Grafik", "options": MODES, "expert": true}
	main.add_control("select", "inhalte_mode", "Echte Oberflächen und Himmel (Fotos, freie Inhalte CC0; nicht in Lite)",
			func(): return mode, func(v): set_mode(str(v)), "System", g)
	main.add_control("button", "inhalte_laden", "Foto-Inhalte jetzt laden / prüfen", null, func(): laden(true), "System",
			{"sub": "Grafik", "expert": true})
	main.add_control("button", "inhalte_ordner", "Ordner der Foto-Inhalte öffnen", null,
			func(): DirAccess.make_dir_recursive_absolute(DIR); OS.shell_open(ProjectSettings.globalize_path(DIR)), "System",
			{"sub": "Grafik", "expert": true})


func _toast(t: String) -> void:
	note = t
	print("inhalte: " + t)
	if main != null and main.get("mehr") != null and main.mehr.has_method("toast"):
		main.mehr.toast(t)


# ---- Katalog und Dateien -------------------------------------------------------------------------------------------------
func _read_katalog() -> void:
	if not FileAccess.file_exists(KATALOG):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(KATALOG))
	if typeof(d) == TYPE_DICTIONARY:
		kat = d
		if d.has("szenen"):
			szenen = d["szenen"]


func entries() -> Array:
	return kat.get("inhalte", [])


func entry(id: String) -> Dictionary:
	for e in entries():
		if e["id"] == id:
			return e
	return {}


func dirs() -> Array:
	"""wo Dateien liegen dürfen: user://inhalte, «inhalte» neben der .exe, --inhalte-ordner"""
	var out := [ProjectSettings.globalize_path(DIR)]
	if not OS.has_feature("editor"):
		out.append(OS.get_executable_path().get_base_dir().path_join("inhalte"))
	if _extra_dir != "":
		out.append(_extra_dir)
	return out


func find_file(name: String) -> String:
	for d in dirs():
		var p: String = str(d).path_join(name)
		if FileAccess.file_exists(p):
			return p
	return ""


func missing() -> Array:
	"""[id, …] der Inhalte, bei denen mindestens eine Datei fehlt"""
	var out := []
	for e in entries():
		for n in e["dateien"].values():
			if find_file(n) == "":
				out.append(e["id"])
				break
	return out


func _wanted_names() -> Dictionary:
	var w := {}
	for e in entries():
		for n in e["dateien"].values():
			w[str(n)] = true
	return w


func _unzip_into(zip_path: String) -> int:
	"""Dateien aus einem ZIP (Paket oder ambientCG), die der Katalog kennt, nach user://inhalte – Anzahl"""
	var z := ZIPReader.new()
	if z.open(zip_path) != OK:
		return 0
	var want := _wanted_names()
	var n := 0
	DirAccess.make_dir_recursive_absolute(DIR)
	for f in z.get_files():
		var base: String = f.get_file()
		if want.has(base) and not FileAccess.file_exists(DIR.path_join(base)):
			var data := z.read_file(f)
			var o := FileAccess.open(DIR.path_join(base), FileAccess.WRITE)
			if o != null and data.size() > 0:
				o.store_buffer(data)
				o.close()
				n += 1
	z.close()
	return n


func _scan_zips() -> int:
	"""selbst hingelegte ZIP-Dateien (Paket, ambientCG) auspacken"""
	var n := 0
	for d in dirs():
		var da := DirAccess.open(str(d))
		if da == null:
			continue
		for f in da.get_files():
			if f.to_lower().ends_with(".zip"):
				n += _unzip_into(str(d).path_join(f))
	return n


# ---- Laden (Download) ----------------------------------------------------------------------------------------------------
func _url(u: String) -> String:
	"""Test: --inhalte-quelle ersetzt den Server (Datei unter ihrem Namen; ambientCG get?file=X.zip -> X.zip)"""
	if _quelle == "":
		return u
	var name := u.get_file()
	if name.contains("file="):
		name = name.get_slice("file=", 1)
	return _quelle + name


func _download(u: String, to: String) -> String:
	"""eine Datei laden: curl (Windows: curl.exe mit Zertifikaten und Proxy von Windows), sonst Godot. "" = gut"""
	var why := ""
	var curl := "curl.exe" if OS.get_name() == "Windows" else "curl"
	var th := Thread.new()
	th.start(func():
		var out := []
		var code := OS.execute(curl, ["-L", "--fail", "-s", "-S", "--retry", "2", "--max-time", "300", "-A", "MoveEyeSim3D-Inhalte",
				"-o", to, u], out, true, false)
		return [code, "\n".join(out)])
	while th.is_alive():
		await get_tree().create_timer(0.25).timeout
	var c: Array = th.wait_to_finish()
	if int(c[0]) == 0 and FileAccess.file_exists(to) and FileAccess.get_file_as_bytes(to).size() > 0:
		return ""
	why = "curl: " + (str(c[1]).strip_edges().left(120) if str(c[1]).strip_edges() != "" else "Fehler %d" % int(c[0]))
	if int(c[0]) in [6, 7, 22, 28, 35, 56, 60]:          # curl lief: Name / Verbindung / HTTP-Fehler – Godot hilft da nicht
		return why
	if _http == null:
		_http = HTTPRequest.new()
		_http.use_threads = true
		add_child(_http)
	_http.download_file = to
	_http.timeout = 300.0
	if _http.request(u, ["User-Agent: MoveEyeSim3D-Inhalte"]) != OK:
		return why + " · Godot: startet nicht"
	var r: Array = await _http.request_completed
	if int(r[0]) == HTTPRequest.RESULT_SUCCESS and int(r[1]) == 200:
		return ""
	if FileAccess.file_exists(to):
		DirAccess.remove_absolute(to)
	return why + " · Godot: %s / HTTP %s" % [r[0], r[1]]


func _sha256(p: String) -> String:
	var f := FileAccess.open(p, FileAccess.READ)
	if f == null:
		return ""
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	while not f.eof_reached():
		h.update(f.get_buffer(1 << 20))
	return h.finish().hex_encode()


func _status_file() -> Dictionary:
	var p := DIR.path_join("status.json")
	if not FileAccess.file_exists(p):
		return {}
	var d = JSON.parse_string(FileAccess.get_file_as_string(p))
	return d if typeof(d) == TYPE_DICTIONARY else {}


func _fetch_missing() -> String:
	"""fehlende Dateien holen: erst das Paket, dann einzeln. Gibt einen Satz für die Anzeige zurück"""
	DirAccess.make_dir_recursive_absolute(DIR)
	var abs_dir := ProjectSettings.globalize_path(DIR)
	var errs := []
	var t0 := Time.get_ticks_msec()
	var pk: Dictionary = kat.get("paket", {})
	if str(pk.get("url", "")) != "" and not missing().is_empty():
		note = T.t("Lade das Paket der Foto-Inhalte …")
		var zp := abs_dir.path_join("paket.zip")
		var why: String = await _download(_url(str(pk["url"])), zp)
		if why == "":
			var sha := str(pk.get("sha256", ""))
			if sha != "" and _sha256(zp).to_lower() != sha.to_lower():
				errs.append("Paket: Prüfsumme falsch")
			else:
				stats["paket_mb"] = snappedf(FileAccess.get_file_as_bytes(zp).size() / 1048576.0, 0.1)
				_unzip_into(zp)
			DirAccess.remove_absolute(zp)
		else:
			errs.append("Paket: " + why)
	var bad_hosts := {}                                   # Server nicht erreichbar: die übrigen Dateien dort gar nicht versuchen
	for id in missing():
		var e := entry(id)
		note = T.t("Lade %s …", [str(e.get("name", id))])
		for u in e.get("laden", []):
			var name: String = str(u).get_file()
			if name.contains("file="):
				name = name.get_slice("file=", 1)
			if not name.ends_with(".zip") and find_file(name) != "":
				continue
			var to := abs_dir.path_join(name + ".part")
			var host := _url(str(u)).get_slice("/", 2)
			if bad_hosts.has(host):
				errs.append("%s: %s nicht erreichbar" % [name, host])
				continue
			var why2: String = await _download(_url(str(u)), to)
			if why2 != "":
				errs.append("%s: %s" % [name, why2])
				if not why2.contains("HTTP") and not why2.contains("error: 4"):
					bad_hosts[host] = true
				continue
			if name.ends_with(".zip"):
				_unzip_into(to)
				DirAccess.remove_absolute(to)
			else:
				DirAccess.rename_absolute(to, abs_dir.path_join(name))
	stats["laden_s"] = snappedf((Time.get_ticks_msec() - t0) / 1000.0, 0.1)
	var st := {"zeit": Time.get_unix_time_from_system(), "fehlt": missing(), "fehler": errs.slice(0, 12)}
	var f := FileAccess.open(DIR.path_join("status.json"), FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(st, " "))
	return "" if errs.is_empty() else "%d Fehler, z. B. %s" % [errs.size(), str(errs[0]).left(140)]


func laden(force := false) -> void:
	"""Dateien suchen, wenn nötig laden, Bilder einlesen, anwenden"""
	if _loading:
		return
	if _off != "":
		_toast(T.t("Foto-Inhalte sind aus: %s", [_off]))
		return
	_loading = true
	_mark(true)
	state = "laden"
	_scan_zips()
	var mis := missing()
	var err := ""
	if not mis.is_empty():
		var st := _status_file()
		var recent: bool = Time.get_unix_time_from_system() - float(st.get("zeit", 0.0)) < RETRY_S and not st.get("fehlt", []).is_empty()
		if force or not (_auto_tried or recent):
			_auto_tried = true
			err = await _fetch_missing()
	await _load_textures()
	_loading = false
	mis = missing()
	var have := _loaded_ids.size()
	state = "bereit" if mis.is_empty() else ("teilweise" if have > 0 else "fehlt")
	if mis.is_empty():
		note = T.t("Foto-Inhalte bereit: alle %d", [have])
	else:
		var names := []
		for id in mis:
			names.append(str(entry(id).get("name", id)) + ("" if not _loaded_ids.has(id) else " " + T.t("(teilweise)")))
		note = T.t("Foto-Inhalte: %d von %d nutzbar – fehlt: %s", [have, entries().size(), ", ".join(names)])
		if err != "":
			note += " (" + err + ")"
	if force:
		_toast(note)
	else:
		print("inhalte: " + note)
	_mats.clear()
	_reset_global()                                       # neu eingelesene Bilder: alles frisch anwenden
	_apply_now()
	_unmark_soon()                                        # eingelesen und angewendet: nach den ersten Bildern kein Absturz


# ---- Bilder einlesen ----------------------------------------------------------------------------------------------------
func _img_job(path: String, rolle: String, can_compress: bool) -> Image:
	"""im Hintergrund: Bild laden, Mipmaps, komprimieren (Grafikspeicher ~1/6)"""
	var img := Image.load_from_file(path)
	if img == null or img.is_empty():
		return null
	var editor := OS.has_feature("editor")
	if rolle == "hdri":
		var hw := HDRI_MAX_W if editor else HDRI_MAX_W_EXE
		if img.get_width() > hw:                          # Startfix: ein sehr grosses HDRI (8k) vor dem Hochladen verkleinern
			if img.get_format() == Image.FORMAT_RGBE9995:
				img.convert(Image.FORMAT_RGBH)
			img.resize(hw, maxi(1, hw * img.get_height() / img.get_width()), Image.INTERPOLATE_BILINEAR)
		return img                                        # Himmel: ohne Mipmaps (Panorama, Godot rechnet die Strahlung selbst)
	var tw := TEX_MAX_EDITOR if editor and can_compress else TEX_MAX_EXE
	if img.get_width() > tw or img.get_height() > tw:     # die längere Seite auf tw (auch hohe Bilder, z. B. Rinde)
		var k := float(tw) / float(maxi(img.get_width(), img.get_height()))
		img.resize(maxi(1, roundi(img.get_width() * k)), maxi(1, roundi(img.get_height() * k)), Image.INTERPOLATE_LANCZOS)
	if rolle == "rough":
		img.convert(Image.FORMAT_L8)
		img.generate_mipmaps()
		return img
	img.convert(Image.FORMAT_RGB8)
	img.generate_mipmaps()
	if can_compress and OS.has_feature("editor"):
		img.compress(Image.COMPRESS_S3TC, Image.COMPRESS_SOURCE_SRGB if rolle == "albedo" else Image.COMPRESS_SOURCE_GENERIC)
	return img


func _load_textures() -> void:
	var t0 := Time.get_ticks_msec()
	var can := _can_compress() and not Quality.lite()
	var jobs := []
	for e in entries():
		for rolle in e["dateien"]:                        # was da ist (z. B. Asphalt ohne Normal-Karte: trotzdem nutzen)
			if find_file(e["dateien"][rolle]) != "" and not tex.has(e["id"] + "/" + rolle) and not hdri.has(e["id"]):
				jobs.append([e["id"], rolle, find_file(e["dateien"][rolle])])
	if jobs.is_empty():
		return
	var th := Thread.new()
	th.start(func():
		var out := []
		for j in jobs:
			out.append([j[0], j[1], _img_job(j[2], j[1], can)])
		return out)
	while th.is_alive():
		await get_tree().create_timer(0.1).timeout
	var res: Array = th.wait_to_finish()
	var vram := 0
	for r in res:
		var id: String = r[0]
		var rolle: String = r[1]
		var img: Image = r[2]
		if img == null:
			push_warning("inhalte: Bild lässt sich nicht lesen: %s/%s" % [id, rolle])
			continue
		if rolle == "hdri":
			_add_hdri(id, img)
			vram += img.get_data().size()
			continue
		tex[id + "/" + rolle] = ImageTexture.create_from_image(img)
		vram += img.get_data().size()
		if rolle == "albedo":
			mean[id] = _mean_color(find_file(entry(id)["dateien"]["albedo"]))
	for e in entries():                                   # nutzbar: HDRI da, Farbe da, oder (Zeltstoff) die Normal-Karte
		var id: String = e["id"]
		if hdri.has(id) or tex.has(id + "/albedo") or (not e["dateien"].has("albedo") and tex.has(id + "/normal")):
			_loaded_ids[id] = true
	stats["einlesen_ms"] = Time.get_ticks_msec() - t0
	stats["grafikspeicher_mb"] = snappedf(stats.get("grafikspeicher_mb", 0.0) + vram / 1048576.0, 0.1)
	stats["komprimiert"] = can


func _mean_color(path: String) -> Color:
	var img := Image.load_from_file(path)
	if img == null or img.is_empty():
		return Color(0.5, 0.5, 0.5)
	img.convert(Image.FORMAT_RGB8)
	img.resize(8, 8, Image.INTERPOLATE_BILINEAR)
	var s := Vector3.ZERO
	for y in range(8):
		for x in range(8):
			var c := img.get_pixel(x, y).srgb_to_linear()
			s += Vector3(c.r, c.g, c.b)
	s /= 64.0
	return Color(s.x, s.y, s.z).linear_to_srgb()


func _add_hdri(id: String, img: Image) -> void:
	"""HDRI: Sonne des Fotos suchen (zum Drehen), Helligkeit messen (zum Angleichen)"""
	var small := img.duplicate() as Image
	if small.is_compressed():
		small.decompress()
	small.convert(Image.FORMAT_RGBF)
	small.resize(256, 128, Image.INTERPOLATE_BILINEAR)
	var best := -1.0
	var sun_u := 0.5
	var lum: Array = []
	for y in range(64):                                   # nur die obere Hälfte (Himmel)
		for x in range(256):
			var c := small.get_pixel(x, y)
			var l := 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b
			lum.append(l)
			if l > best:
				best = l
				sun_u = (x + 0.5) / 256.0
	lum.sort()
	var med: float = lum[lum.size() / 2]
	var p98: float = lum[int(lum.size() * 0.98)]
	var target := 0.62 if id == SKY_DAY else 0.5            # etwa so hell wie der bisherige Himmel (vor «energy»)
	var gain := target / maxf(med, 1e-4)
	hdri[id] = {"tex": ImageTexture.create_from_image(img), "sun_u": sun_u, "gain": gain, "cap": maxf(p98 * gain * 1.3, 1.2)}


# ---- Anwenden ------------------------------------------------------------------------------------------------------------
func active_here() -> bool:
	return _off == "" and mode != "aus" and not Quality.lite() and main != null and str(main.scene) in szenen


static func _can_compress() -> bool:
	"""Startfix 31.10.2026: Image.compress(S3TC) gibt es in Godot 4.3 nur im Editor - in der exportierten .exe fehlt der
	BC-Kompressor («_image_compress_bc_func is null»). Darum dort ohne Kompression (mehr Grafikspeicher, sonst gleich)."""
	return OS.has_feature("editor") and RenderingServer.has_os_feature("s3tc")


func _world_ready() -> bool:
	"""Startfix 31.10.2026: main baut die Welt erst NACH der Update-Suche (main._ready wartet dort). Der verzögerte erste
	Aufruf von on_scene kam vorher - grass_mat und scene_parent waren noch null. In der exportierten .exe ist ein Aufruf
	auf einer typisierten null-Variablen kein Skriptfehler, sondern ein harter Absturz (Fenster weg, Log bricht ab).
	main._build_scene ruft on_scene ohnehin, sobald die Welt steht."""
	return main != null and main.grass_mat != null and main.scene_parent != null and is_instance_valid(main.scene_parent)


func on_scene() -> void:
	"""nach jedem Aufbau einer Szene (main._build_scene) und bei Änderungen"""
	if not _world_ready():
		return
	if _crash_note != "":
		_toast(_crash_note)
		_crash_note = ""
	_swapped.clear()
	_extras = _extras.filter(func(n): return is_instance_valid(n))
	applied = false
	if not active_here():
		_reset_global()
		return
	_mark(true)
	if _loaded_ids.is_empty() or not missing().is_empty() and not _auto_tried:
		laden(false)                                      # lädt im Hintergrund, wendet danach an
	_apply_now()
	if not _loading:
		_unmark_soon()


func _apply_now() -> void:
	if not _world_ready():
		return
	if not active_here():
		_reset_global()
		return
	_apply_ground()
	_apply_meshes()
	_apply_extras()
	applied = not _loaded_ids.is_empty()


func _reset_global() -> void:
	if main == null or main.grass_mat == null:
		return
	main.grass_mat.set_shader_parameter("tex_on", 0.0)
	_sky_on = false
	if main.sky_mat != null:
		main.sky_mat.set_shader_parameter("hdri_mix_a", 0.0)
		main.sky_mat.set_shader_parameter("hdri_mix_b", 0.0)
	for p in _swapped:
		var mi = (p[0] as WeakRef).get_ref()
		if mi != null:
			mi.material_override = p[1]
	_swapped.clear()
	for n in _extras:
		if is_instance_valid(n):
			n.queue_free()
	_extras.clear()
	applied = false


func _apply_ground() -> void:
	var gm: ShaderMaterial = main.grass_mat
	if gm == null:
		return
	var a := "gras" if _loaded_ids.has("gras") else "wiese"
	var b := "wiese" if _loaded_ids.has("wiese") else "gras"
	if not _loaded_ids.has(a) or gm.shader == null or not _has_uniform(gm, "tex_on"):
		gm.set_shader_parameter("tex_on", 0.0)
		return
	gm.set_shader_parameter("tex_a_alb", tex.get(a + "/albedo"))
	gm.set_shader_parameter("tex_a_nrm", tex.get(a + "/normal"))
	gm.set_shader_parameter("tex_b_alb", tex.get(b + "/albedo"))
	gm.set_shader_parameter("tex_b_nrm", tex.get(b + "/normal"))
	gm.set_shader_parameter("ref_a", mean.get(a, Color(0.3, 0.35, 0.2)))
	gm.set_shader_parameter("ref_b", mean.get(b, Color(0.35, 0.33, 0.22)))
	gm.set_shader_parameter("scale_a", 1.0 / float(entry(a).get("kachel_m", 2.0)))
	gm.set_shader_parameter("scale_b", 1.0 / float(entry(b).get("kachel_m", 3.0)))
	gm.set_shader_parameter("tex_on", 1.0)


func _has_uniform(sm: ShaderMaterial, u: String) -> bool:
	"""die Grafikstufe «Hoch» kann den Boden-Shader tauschen – dann gibt es die Foto-Parameter nicht"""
	for p in sm.shader.get_shader_uniform_list():
		if str(p["name"]) == u:
			return true
	return false


func _kinds() -> Dictionary:
	"""Material -> Art («tent», «stone», «tree», «road» …) aus colors.gd"""
	var rev := {}
	if main.get("colors") == null:
		return rev
	var km: Dictionary = main.colors.kind_mats
	for k in km:
		rev[km[k]] = str(k).get_slice("|", 1)
	return rev


func slot_for(mi: MeshInstance3D, kind: String, c: Color) -> String:
	"""welche Foto-Textur passt zu diesem Teil (leer = keine)"""
	var me := mi.mesh
	var brown := c.r > c.b + 0.06 and c.r >= c.g and c.s > 0.2
	match kind:
		"road":
			return "asphalt"
		"tent":
			if me is PrismMesh and c.v > 0.25:
				return "zeltstoff"
			if me is BoxMesh:
				var s: Vector3 = (me as BoxMesh).size
				if minf(s.x, minf(s.y, s.z)) < 0.06 and c.v > 0.25 and maxf(s.x, s.z) > 0.8:
					return "zeltstoff"                      # Vordach
				if brown and minf(s.x, minf(s.y, s.z)) >= 0.3:
					return "holz"                           # Holzkisten
		"stone":
			if me is SphereMesh and c.s < 0.15 and c.v > 0.25 and c.v < 0.75:
				return "stein"
		"tree":
			if me is CylinderMesh and brown:
				return "rinde"
			if me is BoxMesh and brown:
				return "holz"                               # Bank
		"wood":
			return "holz"
	return ""


func _pbr(slot: String, base: StandardMaterial3D) -> StandardMaterial3D:
	var key := "%s|%s|%d" % [slot, base.albedo_color.to_html(), base.get_instance_id()]
	if _mats.has(key):
		return _mats[key]
	var m := base.duplicate() as StandardMaterial3D
	var a = tex.get(slot + "/albedo")
	var n = tex.get(slot + "/normal")
	var r = tex.get(slot + "/rough")
	var arm = tex.get(slot + "/arm")
	if a != null:
		m.albedo_texture = a
		var mc: Color = mean.get(slot, Color(0.5, 0.5, 0.5))
		var o := base.albedo_color
		var tint := Color(clampf(o.r / maxf(mc.r, 0.05), 0.5, 1.6), clampf(o.g / maxf(mc.g, 0.05), 0.5, 1.6), clampf(o.b / maxf(mc.b, 0.05), 0.5, 1.6))
		m.albedo_color = Color.WHITE.lerp(tint, 0.35)
	if n != null:
		m.normal_enabled = true
		m.normal_texture = n
		m.normal_scale = 1.0
	if r != null:
		m.roughness_texture = r
		m.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
		m.roughness = 1.0
	elif arm != null:
		m.roughness_texture = arm
		m.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_GREEN
		m.roughness = 1.0
		m.ao_enabled = true
		m.ao_texture = arm
		m.ao_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_RED
	m.uv1_triplanar = true
	m.uv1_world_triplanar = true
	m.uv1_scale = Vector3.ONE / float(entry(slot).get("kachel_m", 1.0))
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	m.set_meta("inhalte", slot)
	if main.get("colors") != null:
		main.colors.base_alb[m] = [m.albedo_color, m.roughness]    # nass im Regen wie die anderen Materialien
	_mats[key] = m
	return m


func _apply_meshes() -> void:
	var rev := _kinds()
	var n := 0
	var per := {}
	for mi in _meshes(main.scene_parent):
		var mat = mi.material_override
		if not (mat is StandardMaterial3D) or (mat as StandardMaterial3D).has_meta("inhalte"):
			continue
		var kind: String = rev.get(mat, "")
		var slot := slot_for(mi, kind, (mat as StandardMaterial3D).albedo_color)
		if slot == "" or not _loaded_ids.has(slot):
			continue
		_swapped.append([weakref(mi), mat])
		mi.material_override = _pbr(slot, mat)
		n += 1
		per[slot] = int(per.get(slot, 0)) + 1
	stats["flaechen"] = n
	stats["pro_textur"] = per


func _meshes(root: Node) -> Array:
	var out := []
	var stack := [root]
	while not stack.is_empty():
		var nd: Node = stack.pop_back()
		if nd == null or not is_instance_valid(nd):
			continue
		for ch in nd.get_children():
			stack.append(ch)
			if ch is MeshInstance3D and (ch as MeshInstance3D).layers & 1 and (ch as MeshInstance3D).mesh != null:
				out.append(ch)
	return out


func _apply_extras() -> void:
	"""Kies-Rand an der Strasse, ausgetretene Erde vor dem Zelt und beim Grill – nur flach auf dem Boden, nur mit Fotos"""
	if not _extras.filter(func(x): return is_instance_valid(x)).is_empty():
		return
	var root: Node3D = main.scenes.root if main.scenes != null and is_instance_valid(main.scenes.root) else main.scene_parent
	if main.scenes != null and main.scenes.data.has("road_z") and _loaded_ids.has("kies"):
		var z: float = float(main.scenes.data["road_z"]) - 1.2
		for s in [-1.0, 1.0]:
			var q := PlaneMesh.new()
			q.size = Vector2(400, 0.9)
			_extras.append(_flat(root, q, Vector3(0, 0.006, z + s * 2.95), _pbr("kies", main.mat(Color(0.55, 0.53, 0.5)))))
	if _loaded_ids.has("erde"):
		var spots := []
		var tz = main.test_props.get("Zelt")
		if tz != null and is_instance_valid(tz):
			spots.append([(tz as Node3D).transform * Vector3(0, 0, 1.9), 1.4])
		var gr = main.test_props.get("Grill")
		if gr != null and is_instance_valid(gr):
			spots.append([(gr as Node3D).position, 1.1])
		for sp in spots:
			var q2 := PlaneMesh.new()
			q2.size = Vector2(sp[1] * 2.0, sp[1] * 2.0)
			_extras.append(_flat(root, q2, Vector3(sp[0].x, 0.004, sp[0].z), _patch_mat()))


func _flat(root: Node3D, mesh: Mesh, p: Vector3, m: Material) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = p
	mi.material_override = m
	mi.layers = 1
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.name = "inhalte_flaeche"
	root.add_child(mi)
	return mi


var _patch: ShaderMaterial


func _patch_mat() -> ShaderMaterial:
	if _patch == null:
		_patch = ShaderMaterial.new()
		_patch.shader = load("res://shaders/flecken.gdshader")
	_patch.set_shader_parameter("alb", tex.get("erde/albedo"))
	_patch.set_shader_parameter("nrm", tex.get("erde/normal"))
	_patch.set_shader_parameter("scale", 1.0 / float(entry("erde").get("kachel_m", 2.0)))
	_patch.set_shader_parameter("noise_tex", main.noise_tex)
	return _patch


# ---- Himmel (läuft weiter, weil sich Sonne und Wetter ändern) -----------------------------------------------------------
func _process(dt: float) -> void:
	_t += dt
	if _t < 0.5:
		return
	_t = 0.0
	if main == null or main.sky_mat == null or main.sun == null or not _world_ready():
		return
	if Quality.lite() != _lite_was:                       # Lite an / aus
		_lite_was = Quality.lite()
		on_scene()
	_update_sky()


func sky_weights() -> Vector2:
	"""[Tag, Dämmerung] 0 … 1 nach Sonnenstand und Wolken"""
	var el: float = main.sun_el()
	var day := smoothstep(3.0, 12.0, el)
	var dusk := (1.0 - day) * smoothstep(-7.0, -1.0, el)
	var clear := 1.0 - smoothstep(0.3, 0.8, float(main.clouds()))
	var a := day * clear if hdri.has(SKY_DAY) else 0.0
	var b := dusk * clear if hdri.has(SKY_DUSK) else 0.0
	if not hdri.has(SKY_DAY) and hdri.has(SKY_DUSK):
		b = (day + dusk) * clear * (1.0 - day * 0.5)       # nur Dämmerung da: auch tagsüber (heller Abendhimmel), halb
	return Vector2(a, b)


func _update_sky() -> void:
	var sm: ShaderMaterial = main.sky_mat
	if not (applied and mode == "an" and active_here()) or hdri.is_empty():
		if _sky_on:
			_sky_on = false
			sm.set_shader_parameter("hdri_mix_a", 0.0)
			sm.set_shader_parameter("hdri_mix_b", 0.0)
		return
	_sky_on = true
	var w := sky_weights()
	var s: Vector3 = (main.sun as DirectionalLight3D).global_transform.basis.z     # Richtung zur Sonne
	var s_u := atan2(s.x, -s.z) / TAU + 0.5
	var day: float = clampf((main.sun_el() + 6.0) / 18.0, 0.02, 1.0)
	for pair in [["a", SKY_DAY, w.x], ["b", SKY_DUSK, w.y]]:
		var h: Dictionary = hdri.get(pair[1], {})
		if h.is_empty():
			sm.set_shader_parameter("hdri_mix_" + pair[0], 0.0)
			continue
		sm.set_shader_parameter("hdri_" + pair[0], h["tex"])
		sm.set_shader_parameter("hdri_mix_" + pair[0], pair[2])
		sm.set_shader_parameter("hdri_rot_" + pair[0], fposmod(float(h["sun_u"]) - s_u, 1.0))
		sm.set_shader_parameter("hdri_gain_" + pair[0], float(h["gain"]) * day)
		sm.set_shader_parameter("hdri_cap_" + pair[0], float(h["cap"]) * day)
		sm.set_shader_parameter("hdri_low_" + pair[0], float(entry(pair[1]).get("himmel_ab", -0.06)))


# ---- Test-Schnittstelle --------------------------------------------------------------------------------------------------
func info() -> Dictionary:
	var sw := sky_weights() if main != null and main.sky_mat != null else Vector2.ZERO
	return {"mode": mode, "state": state, "note": note, "applied": applied, "active_here": active_here(), "off": _off,
			"lite": Quality.lite(), "scene": str(main.scene), "szenen": szenen, "geladen": _loaded_ids.keys(), "fehlt": missing(),
			"hdri": hdri.keys(), "himmel_tag": snappedf(sw.x, 0.01), "himmel_daemmerung": snappedf(sw.y, 0.01),
			"ordner": dirs(), "paket_url": _url(str(kat.get("paket", {}).get("url", ""))), "stats": stats, "loading": _loading,
			"fps": Engine.get_frames_per_second()}


func control(d: Dictionary) -> Dictionary:
	var op := str(d.get("do", "info"))
	if op == "set":
		set_mode(str(d.get("value", "an")))
	elif op == "laden":
		laden(true)
	elif op == "anwenden":
		on_scene()
	elif op == "zuruecksetzen":
		_reset_global()
	return info()
