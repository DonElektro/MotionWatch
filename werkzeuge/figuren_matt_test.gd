extends SceneTree
## Test «Figuren matt» (Idee #45, 28.11.2026), ohne Bild, mit der echten Welt (main.tscn):
##   cd simulator3d && HOME=<test-home> <godot> --headless --path . -s "$PWD/../werkzeuge/figuren_matt_test.gd" -- --no-update --no-tour
## Prüft:
##   1. Stoffe (figur_mensch.gd stoff): Kleider Rauheit 0,9–1,0, Regenjacke glatter, Glanz höchstens 0,35.
##   2. Kontaktschatten (kontaktschatten.gd): jede Person hat ihn (Ebene 1, kein Schatten, multiplizieren, ohne Licht / Nebel,
##      Merkmal für Boxen), ein Tier nicht; er folgt der Figur; am Hang liegt er schräg wie der Boden; Kriechen = länger.
##   3. Box der Person (dataset.gd _box) ist mit und ohne Schatten gleich (die Scheibe gehört nicht zur Box).
##   4. Menschen-Paket (figur_mensch.gd, erzwungen): Haut matt (Rauheit ≥ 0,7, Glanz ≤ 0,25, kein Rim), Haare ohne Rim,
##      Kleider wie die Stoff-Tabelle. Quaternius (figur_paket.gd, erzwungen): kein Rim, Glanz ≤ 0,2, Kleider ≥ 0,9.
## Ende: «Figuren-matt-Test OK» oder «SCRIPT ERROR: Figuren-matt-Test: …» (Exit-Code 0 / 1).

const FM = preload("res://scripts/figur_mensch.gd")
const FP = preload("res://scripts/figur_paket.gd")
const K = preload("res://scripts/kontaktschatten.gd")

var main
var errs := []
var n_ok := 0


func ok(what: String, cond: bool) -> void:
	if cond:
		n_ok += 1
		print("  ok ", what)
	else:
		errs.append(what)
		print("  FEHLER ", what)


func _initialize() -> void:
	main = load("res://main.tscn").instantiate()
	root.add_child(main)
	current_scene = main
	_run.call_deferred()


func wait(s: float) -> void:
	await create_timer(s, true, false, true).timeout


func _quiet() -> void:
	main.control({"action": "set", "id": "auto", "value": false})
	for v in main.visitors.get_children():
		v.queue_free()


func _kontakt_of(a: Node) -> MeshInstance3D:
	for c in a.get_children():
		if c is MeshInstance3D and c.has_meta("kontaktschatten"):
			return c
	return null


func _run() -> void:
	await wait(2.0)
	main.eco_idle = false
	_quiet()
	await wait(0.3)
	# ---- 1. Stoffe ----
	for teil in ["jacke", "hose"]:
		for st in ["wandern", "freizeit", "arbeit", ""]:
			var v: Array = FM.stoff(st, teil)
			ok("Stoff %s/%s: Rauheit 0,9–1,0, Glanz ≤ 0,25" % [teil, st], v[0] >= 0.9 and v[0] <= 1.0 and v[1] <= 0.25)
	ok("Regenjacke glatter als Fleece / Softshell", FM.stoff("regen", "jacke")[0] < FM.stoff("wandern", "jacke")[0] and FM.stoff("regen", "jacke")[0] >= 0.5)
	ok("unbekannter Stil = Standard", FM.stoff("zzz", "jacke") == FM.stoff("", "jacke"))
	ok("Haut-Werte matt", FM.SKIN_ROUGH >= 0.7 and FM.SKIN_SPEC <= 0.25)
	# ---- 2. Kontaktschatten ----
	var p = main.spawn("person", Vector3(0, 0, -6), Vector3(4, 0, -6))
	var f = main.spawn("fox", Vector3(2, 0, -8), Vector3(5, 0, -8))
	await wait(0.5)
	var k: MeshInstance3D = _kontakt_of(p) if p != null else null
	ok("Person hat einen Kontaktschatten", k != null and p.kontakt == k)
	ok("Tier hat keinen", f != null and _kontakt_of(f) == null)
	if k != null:
		var mt := k.material_override as StandardMaterial3D
		ok("Ebene 1 (nicht im Wärmebild), wirft keinen Schatten", k.layers == 1 and k.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
		ok("Material: multiplizieren, ohne Licht, ohne Nebel", mt != null and mt.blend_mode == BaseMaterial3D.BLEND_MODE_MUL
				and mt.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED and mt.disable_fog)
		var img: Image = mt.albedo_texture.get_image()
		var c0: Color = img.get_pixel(32, 32)
		var c1: Color = img.get_pixel(0, 0)
		ok("Verlauf: Mitte dunkler, Rand = Boden unverändert (nie heller)", c0.r < 0.7 and c1.r > 0.97 and c0.r >= K.MITTE - 0.05)
		ok("folgt der Figur (Kind der Figur, an den Füssen)", k.get_parent() == p and absf(k.position.y - K.HOEHE) < 0.01)
		# am Hang: eine schräge Fläche (10 %) als eigener Boden
		var old_fn: Callable = main.ground_fn
		var old_t: bool = main.terrain
		main.ground_fn = func(x: float, _z: float) -> float: return 0.1 * x
		main.terrain = true
		K.tick(p, k)
		var up: Vector3 = (k.global_transform.basis.y).normalized()
		var want := Vector3(-0.1, 1.0, 0.0).normalized()
		ok("am Hang schräg wie der Boden", up.dot(want) > 0.995)
		main.ground_fn = old_fn
		main.terrain = old_t
		K.tick(p, k)
		ok("flach wieder flach", (k.global_transform.basis.y).normalized().dot(Vector3.UP) > 0.999)
		var l0: float = k.basis.z.length()
		p.prone = 1.0
		K.tick(p, k)
		ok("liegend länger", k.basis.z.length() > l0 * 1.8)
		p.prone = 0.0
		K.tick(p, k)
		# ---- 3. Box ----
		main.cams[0].look_at_from_position(Vector3(0, 1.6, 2), p.global_position + Vector3(0, 0.9, 0), Vector3.UP)
		await wait(0.2)
		var ds = main.get("dataset")
		if ds != null and ds.has_method("_box"):
			var b1: Array = ds._box(p)
			k.remove_meta("kontaktschatten")
			var b2: Array = ds._box(p)
			k.set_meta("kontaktschatten", true)
			ok("Box der Person ohne den Schatten (sonst breiter)", not b1.is_empty() and not b2.is_empty() and float(b2[2]) >= float(b1[2]) - 0.0001)
			print("  Box mit Merkmal ", b1, " ohne ", b2)
		else:
			print("  (dataset._box nicht gefunden - übersprungen)")
	_quiet()
	await wait(0.3)
	# ---- 4. Menschen-Paket / Quaternius ----
	FP.mode = "an"
	FM.mensch_mode = ""
	var h = main.spawn("person", Vector3(0, 0, -5), Vector3(3, 0, -5))
	await wait(0.5)
	if h != null and h.fig != null and h.fig is FM:
		var fg = h.fig
		var skin_ok := true
		for mt in fg._mats.get("skin", []):
			skin_ok = skin_ok and mt.roughness >= 0.7 and mt.metallic_specular <= 0.25 and not mt.rim_enabled
		ok("Menschen-Paket: Haut matt, ohne Rim", skin_ok and not fg._mats.get("skin", []).is_empty())
		var hair_ok := true
		for mt in fg._mats.get("hair", []):
			hair_ok = hair_ok and not mt.rim_enabled and mt.metallic_specular <= 0.35
		ok("Menschen-Paket: Haare ohne Rim", hair_ok)
		var st: String = str(fg._p.get("stil", ""))
		var cl_ok := true
		for mt in fg._mats.get("jacket", []):
			cl_ok = cl_ok and is_equal_approx(mt.roughness, float(FM.stoff(st, "jacke")[0]))
		for mt in fg._mats.get("trousers", []):
			cl_ok = cl_ok and is_equal_approx(mt.roughness, float(FM.stoff(st, "hose")[0]))
		ok("Menschen-Paket: Kleider wie die Stoff-Tabelle (Stil «%s»)" % st, cl_ok)
	else:
		print("  (Menschen-Paket nicht da - übersprungen)")
	_quiet()
	await wait(0.3)
	FM.mensch_mode = "aus"
	var q = main.spawn("person", Vector3(0, 0, -5), Vector3(3, 0, -5))
	await wait(0.5)
	if q != null and q.fig != null and q.fig is FP and not (q.fig is FM):
		var all_ok := true
		var cloth_ok := true
		for key in q.fig._mats:
			for mt in q.fig._mats[key]:
				all_ok = all_ok and not mt.rim_enabled and mt.metallic_specular <= 0.2
				if key in ["jacket", "trousers"]:
					cloth_ok = cloth_ok and mt.roughness >= 0.9
		ok("Quaternius: kein Rim, Glanz ≤ 0,2", all_ok)
		ok("Quaternius: Kleider Rauheit ≥ 0,9", cloth_ok)
		ok("Quaternius-Figur hat auch den Kontaktschatten", _kontakt_of(q) != null)
	else:
		print("  (Quaternius-Paket nicht da - übersprungen)")
	FM.mensch_mode = ""
	FP.mode = ""
	_quiet()
	await wait(0.2)
	if errs.is_empty():
		print("Figuren-matt-Test OK (%d Prüfungen)" % n_ok)
		quit(0)
	else:
		push_error("Figuren-matt-Test: " + "; ".join(errs))
		quit(1)
