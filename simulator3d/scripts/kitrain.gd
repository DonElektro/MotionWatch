extends Node
## «KI trainieren» (3D-4.x, Wunsch Daniel): ein Knopf in der Karte «Testen» → «Trainingsbilder für eine eigene KI».
##   1. macht ein Trainingspaket (dataset.gd, mit der gewählten Vielfalt normal / hoch)
##   2. legt die ZIP-Datei als Anhang ins Release «ki-daten» auf GitHub (legt das Release an, wenn es fehlt)
##   3. startet auf GitHub das Training (Workflow ki_modell.yml, «workflow_dispatch»)
##   MoveEye holt das neue Modell danach selbst (Teil 196: täglich, nur wenn es nicht schlechter ist).
## Der GitHub-Schlüssel ist derselbe wie beim Prüfstand (user://pruefstand/schluessel.txt, pruefstand.gd) - Rechte:
## Contents lesen und schreiben + Actions lesen und schreiben, nur dieses Repository.
## Ohne Schlüssel: die ZIP liegt auf dem Schreibtisch, eine kurze Anleitung sagt, wohin damit.
## CONTROL action "kitrain": {"op": "get"} / {"op": "start", "n": 200, "vielfalt": "hoch", "dry": true} /
##   {"op": "upload", "dry": true} (das letzte Paket) - «dry» zeigt nur, was gesendet würde (ohne Netz).

const UI = preload("res://scripts/ui_style.gd")
const WORKFLOW := "ki_modell.yml"
const RELEASE_TAG := "ki-daten"

var main
var http: HTTPRequest
var running := false
var step := ""                  # what is going on (for the label)
var msg := ""
var last_run_url := ""
var dry_plan: Array = []        # the requests of the last dry run (without the key)
var vf_opt: OptionButton
var n_opt: OptionButton
var btn: Button
var lbl: Label
var key_le: LineEdit
const SIZES := [200, 500, 1000, 2000]


func _ready() -> void:
	http = HTTPRequest.new()
	http.timeout = 0.0
	add_child(http)


func repo_api() -> String:
	"""https://api.github.com/repos/<owner>/<repo> - from the address the Prüfstand uses (one place for it)"""
	var r: String = main.pruef.REPO_API if main != null and main.pruef != null else "https://api.github.com/repos/DonElektro/MotionWatch/contents/"
	return r.get_slice("/contents/", 0)


func token() -> String:
	return main.pruef._token() if main != null and main.pruef != null else ""


func build(parent: VBoxContainer, sizes: OptionButton) -> void:
	"""the controls below «Trainingspaket (YOLO) machen» (same size choice)"""
	n_opt = sizes
	var r := HBoxContainer.new()
	r.add_theme_constant_override("separation", 6)
	parent.add_child(r)
	vf_opt = OptionButton.new()
	vf_opt.add_item("Vielfalt: normal", 0)
	vf_opt.add_item("Vielfalt: hoch", 1)
	vf_opt.tooltip_text = "hoch: zufällige Kleider und Muster, Haltungen, Dinge in der Hand, Lampen und Sonnenstand, Wetter, alle Szenen, weit weg, teils verdeckt, Kamera-Fehler (Rauschen, Unschärfe, JPEG), leere Bilder mit Ästen, Fahnen, Lichtern und Insekten"
	vf_opt.select(1 if main.dataset.vielfalt == "hoch" else 0)
	vf_opt.item_selected.connect(func(i): main.dataset.vielfalt = "hoch" if i == 1 else "normal")
	r.add_child(vf_opt)
	btn = Button.new()
	btn.text = "KI trainieren"
	btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn.tooltip_text = "Macht ein Trainingspaket, legt es auf GitHub (Release «ki-daten») und startet dort das Training. MoveEye holt das neue Modell danach selbst, wenn es nicht schlechter ist."
	UI.primary(btn)
	btn.pressed.connect(func(): start(SIZES[n_opt.selected] if n_opt != null else 500, main.dataset.vielfalt, false))
	r.add_child(btn)
	var kr := HBoxContainer.new()
	parent.add_child(kr)
	var kl := UI.small("GitHub-Schlüssel (wie beim Prüfstand):", UI.TXT)
	kl.autowrap_mode = TextServer.AUTOWRAP_OFF
	kr.add_child(kl)
	key_le = LineEdit.new()
	key_le.secret = true
	key_le.placeholder_text = "github_pat_… (leer = ZIP auf den Schreibtisch)"
	key_le.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	key_le.text = token()
	key_le.text_changed.connect(func(s):
		main.pruef._save_token(s.strip_edges())
		if main.pruef.token_le != null and main.pruef.token_le.text != s.strip_edges():
			main.pruef.token_le.text = s.strip_edges())
	kr.add_child(key_le)
	lbl = UI.small("")
	lbl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	parent.add_child(lbl)


func _process(_dt: float) -> void:
	if lbl == null:
		return
	var t := msg
	if running and step == "paket":
		t = "1/3 Paket: " + main.dataset.msg
	lbl.text = t
	if btn != null:
		btn.text = "Abbrechen" if running and step == "paket" else "KI trainieren"
		btn.disabled = running and step != "paket"


func state() -> Dictionary:
	return {"ok": true, "running": running, "step": step, "msg": msg, "run_url": last_run_url, "key": token() != "",
			"pack": main.dataset.last_pack, "dry_plan": dry_plan,
			"ui": {"built": btn != null, "button": btn.text if btn != null else "", "vielfalt": vf_opt.get_item_text(vf_opt.selected) if vf_opt != null else "", "label": lbl.text if lbl != null else ""}}


func start(n: int, vf: String, dry: bool) -> Dictionary:
	if running:
		if step == "paket":
			main.dataset.stop()                          # the button is «Abbrechen» while the pack is made
		return state()
	if main.dataset.busy or main.busy_with() != "":
		msg = "Der Simulator ist gerade beschäftigt (%s)." % main.busy_with()
		return state()
	_run(n, vf, dry)
	return state()


func upload_last(dry: bool) -> Dictionary:
	if running:
		return state()
	var p: Dictionary = main.dataset.last_pack
	if str(p.get("zip", "")) == "" or not FileAccess.file_exists(str(p["zip"])):
		msg = "Noch kein Paket gemacht."
		return state()
	_upload_bg(str(p["zip"]), dry)
	return state()


func _upload_bg(zip: String, dry: bool) -> void:
	running = true
	dry_plan = []
	await _send(zip, dry)
	running = false


func _run(n: int, vf: String, dry: bool) -> void:
	running = true
	step = "paket"
	dry_plan = []
	main.dataset.export_pack(n, true, vf)
	await main.get_tree().process_frame
	while main.dataset.busy:
		await main.get_tree().create_timer(0.5).timeout
	var p: Dictionary = main.dataset.last_pack
	if main.dataset._stop or str(p.get("zip", "")) == "" or int(p.get("made", 0)) < 10:
		msg = "Abgebrochen – kein Paket." if main.dataset._stop else "Das Paket ging nicht (%s)." % main.dataset.msg
		running = false
		step = ""
		return
	await _send(str(p["zip"]), dry)
	running = false


func _no_key(zip: String) -> void:
	step = ""
	OS.shell_show_in_file_manager(zip)
	msg = ("Ohne GitHub-Schlüssel: die ZIP liegt hier: %s\nSo kommt sie ins Training: 1. GitHub → Releases → «ki-daten» → Edit → ZIP hineinziehen → Update release " +
			"(beim ersten Mal «Draft a new release», Tag ki-daten). 2. Actions → «KI-Modell» → Run workflow. MoveEye holt das neue Modell danach selbst.\n" +
			"Mit Schlüssel geht beides von selbst (Rechte: Contents und Actions lesen und schreiben, nur dieses Repository).") % zip


func _hdr(tok: String, ctype := "application/json") -> PackedStringArray:
	return PackedStringArray(["Authorization: Bearer " + tok, "Accept: application/vnd.github+json", "X-GitHub-Api-Version: 2022-11-28",
			"User-Agent: MotionWatch3D", "Content-Type: " + ctype])


func _req(url: String, method: int, tok: String, body := "", raw := PackedByteArray(), ctype := "application/json", dry := false) -> Array:
	"""[code, parsed JSON or text]; dry: only noted, never sent"""
	if dry:
		dry_plan.append({"method": ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "TRACE", "CONNECT", "PATCH"][method], "url": url,
				"headers": ["Authorization: Bearer ***"] + Array(_hdr("", ctype)).slice(1), "body": body if raw.is_empty() else "<%d Bytes %s>" % [raw.size(), ctype]})
		return [0, {}]
	var err: int = http.request_raw(url, _hdr(tok, ctype), method, raw) if not raw.is_empty() else http.request(url, _hdr(tok, ctype), method, body)
	if err != OK:
		return [-1, "request %d" % err]
	var r: Array = await http.request_completed
	var txt: String = (r[3] as PackedByteArray).get_string_from_utf8()
	var js = JSON.parse_string(txt) if txt != "" else {}
	return [int(r[1]) if int(r[0]) == HTTPRequest.RESULT_SUCCESS else -int(r[0]), js if js != null else txt]


func _send(zip: String, dry: bool) -> void:
	var tok := token()
	if tok == "" and not dry:
		_no_key(zip)
		return
	var api := repo_api()
	var name := zip.get_file()
	# 1. the release «ki-daten» (made when missing)
	step = "hochladen"
	msg = "2/3 Hochladen: Release «%s» suchen …" % RELEASE_TAG
	var rel: Array = await _req(api + "/releases/tags/" + RELEASE_TAG, HTTPClient.METHOD_GET, tok, "", PackedByteArray(), "application/json", dry)
	var rid := 0
	if dry:
		rid = 123456
	elif rel[0] == 200 and typeof(rel[1]) == TYPE_DICTIONARY:
		rid = int(rel[1].get("id", 0))
	elif rel[0] == 404:
		var cr: Array = await _req(api + "/releases", HTTPClient.METHOD_POST, tok, JSON.stringify({"tag_name": RELEASE_TAG, "name": "KI-Trainingsdaten",
				"body": "Trainingspakete aus dem Simulator (YOLO-ZIP). Das Training (Actions → KI-Modell) holt alle ZIPs von hier.", "prerelease": true, "make_latest": "false"}))
		if cr[0] == 201 and typeof(cr[1]) == TYPE_DICTIONARY:
			rid = int(cr[1].get("id", 0))
		else:
			_fail("Release «ki-daten» anlegen", cr[0], zip)
			return
	else:
		_fail("Release «ki-daten» suchen", rel[0], zip)
		return
	# 2. the ZIP as asset (uploads.github.com, raw body)
	var raw := PackedByteArray()
	var fz := FileAccess.open(zip, FileAccess.READ)
	var size := fz.get_length() if fz != null else 0
	if fz != null and not dry:
		raw = fz.get_buffer(size)
	if size <= 0 or (not dry and raw.size() != size):
		_fail("ZIP lesen", 0, zip)
		return
	if dry:
		raw = PackedByteArray([0])                       # only for the note «<size> Bytes»
		raw.resize(size)
	msg = "2/3 Hochladen: %s (%d MB) …" % [name, int(size / 1048576.0 + 0.5)]
	var up_url := api.replace("https://api.github.com/", "https://uploads.github.com/") + "/releases/%d/assets?name=%s" % [rid, name.uri_encode()]
	var up: Array = await _req(up_url, HTTPClient.METHOD_POST, tok, "", raw, "application/zip", dry)
	if not dry and up[0] != 201:
		_fail("ZIP hochladen" + (" (gleicher Name schon da)" if up[0] == 422 else ""), up[0], zip)
		return
	# 3. start the training (workflow_dispatch)
	step = "training"
	msg = "3/3 Training auf GitHub starten …"
	var ds: Array = await _req(api + "/actions/workflows/" + WORKFLOW + "/dispatches", HTTPClient.METHOD_POST, tok,
			JSON.stringify({"ref": "main", "inputs": {"epochen": "60", "basis": "yolov8n.pt", "veroeffentlichen": "true", "quelle": "Simulator: " + name}}), PackedByteArray(), "application/json", dry)
	if dry:
		step = ""
		msg = "Probelauf: nichts gesendet. %d Anfragen wären es gewesen (Release suchen, ZIP %s hochladen, Training starten)." % [dry_plan.size(), name]
		return
	if ds[0] != 204:
		_fail("Training starten (der Schlüssel braucht auch «Actions: Read and write»)", ds[0], zip)
		return
	last_run_url = ""
	await main.get_tree().create_timer(6.0).timeout
	var rn: Array = await _req(api + "/actions/workflows/" + WORKFLOW + "/runs?per_page=1&event=workflow_dispatch", HTTPClient.METHOD_GET, tok)
	if rn[0] == 200 and typeof(rn[1]) == TYPE_DICTIONARY and not (rn[1].get("workflow_runs", []) as Array).is_empty():
		last_run_url = str(rn[1]["workflow_runs"][0].get("html_url", ""))
	step = ""
	msg = ("✅ Paket %s hochgeladen, Training gestartet (dauert etwa 30 Minuten bis 2 Stunden). " +
			"MoveEye holt das neue Modell danach selbst, wenn es nicht schlechter ist.%s") % [name, ("\nLauf: " + last_run_url) if last_run_url != "" else ""]
	main.start_info = "KI-Training gestartet: " + name


func _fail(what: String, code, zip: String) -> void:
	step = ""
	var why := "Schlüssel abgelehnt – Rechte prüfen (Contents und Actions: Read and write)" if code in [401, 403] else ("nicht gefunden (Repository oder Workflow?)" if code == 404 else "Antwort %s" % str(code))
	msg = "%s ging nicht: %s.\nDie ZIP liegt hier: %s – von Hand: GitHub → Releases → «ki-daten» → Edit → ZIP hineinziehen, dann Actions → «KI-Modell» → Run workflow." % [what, why, zip]
