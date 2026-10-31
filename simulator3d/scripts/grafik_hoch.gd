extends Node
## F1 «Grafikstufe Hoch» (Paket Realismus, Daniel 31.10.2026; Ziel: der 3D-Simulator Schritt für Schritt Richtung Fotorealismus).
## Nur eingebaute Mittel von Godot 4.3, keine Dateien: alle Texturen (Normal-, Rauheits-Karten) entstehen hier aus Rauschen.
##
## Stufen (zusammen mit «Lite» aus quality.gd):   Lite  <  Normal (= bisher, «Voll»)  <  Hoch
##   - Normal: alles wie bisher (Compatibility-Renderer / OpenGL).
##   - Hoch: braucht den Forward+-Renderer (Vulkan). Der Simulator startet dafür einmal neu mit
##     «--rendering-method forward_plus». Geht Vulkan nicht, kommt der nächste Start wieder mit Normal (Merker «pending»).
##     Hoch schaltet ein: SDFGI (Licht prallt von Flächen ab), SSAO + SSIL, Volumen-Nebel (feiner Dunst am Boden morgens /
##     abends, folgt dem Wetter-Nebel), Leuchten in der Nacht, weiche Schatten (PCSS über die Sonnengrösse 0.53°, grössere
##     Schattenkarte, 4 Stufen), TAA + MSAA 2× in der grossen Ansicht, Spiegelungen (SSR) auf dem See und nassen Flächen,
##     ACES-Tonemapping, Belichtungs-Automatik und (wahlweise) Tiefenschärfe nur in der freien Ansicht, bessere Oberflächen
##     (Stein, Holz/Rinde, Stoff, Lack, Wasser mit Wellen, Wiese mit Unebenheiten).
##   - Lite (anderes Paket): Hoch ist dann immer aus.
##
## Einbau in main.gd (kleine Haken, beim Zusammenführen leicht zu verbinden):
##   1. _ready: nach _vm_needs_angle:   if GrafikHoch.start_check(self, args): return      (Neustart mit Forward+)
##   2. _ready: nach _load_settings:    hoch = GrafikHoch.new(); hoch.main = self; add_child(hoch)
##   3. Ende von _apply_quality():      if hoch != null: hoch.after_quality()
##   4. Bedienung: add_control("select", "grafik_stufe", …) in «System › Grafik» (ein Auswahlfeld Normal / Hoch)
##   5. _control: {"action": "grafik", "do": "info" | "set" (value) | "perf"}  (Tests, Messungen)
## Zusammenführen mit quality.gd («Grafik-Modus» Automatisch / Voll / Lite): Vorschlag für den Koordinator – ein einziges
## Auswahlfeld «Grafik-Modus»: Automatisch · Lite · Normal (= Voll) · Hoch; set_grafik_mode("high") ruft hoch.set_stufe("hoch"),
## jede andere Wahl hoch.set_stufe("normal"). _lite() unten fragt dieselbe Meta «lite» ab wie Quality.lite().
##
## Einstellung: eigene kleine Datei user://grafik_stufe.json (nicht in KEEP von main.gd, damit kein Konflikt entsteht).
## Den Himmel baut das Licht-&-Nacht-Paket (sky.gdshader: Sonne, Mond, Sterne) – hier wird der Himmel NICHT ersetzt;
## physical_sky() liefert nur einen PhysicalSkyMaterial (Rayleigh / Mie), falls der Himmel ihn einmal nutzen will.

const FILE := "user://grafik_stufe.json"
const STUFEN := [["normal", "Normal (wie bisher)"], ["hoch", "Hoch (fotorealistisch – braucht eine gute Grafikkarte)"]]
const FLAG := "--hoch-fwd"            # dieser Prozess wurde für «Hoch» mit Forward+ gestartet

var main
var stufe := "normal"                 # gespeicherte Wahl
var active := false                   # Hoch wirkt gerade (Forward+ läuft, nicht Lite, nicht «zu langsam»)
var dof_free := false                 # Tiefenschärfe in der freien Ansicht (die Kameras von MoveEye bleiben immer scharf)
var why_off := ""                     # warum Hoch gerade nicht wirkt (für die Anzeige)
var _orig := {}                       # [Objekt-ID, Eigenschaft] -> [Objekt, alter Wert]
var _mat_orig := {}                   # StandardMaterial3D -> {Eigenschaft: alter Wert}
var _water_nodes: Array = []          # [WeakRef MeshInstance3D, altes Material]
var _ground_orig := {}                # ShaderMaterial -> alter Shader
var _queue: Array = []                # neu hinzugekommene Teile der Welt (node_added), werden pro Bild verbessert
var _rev := {}                        # StandardMaterial3D -> Art («stone», «wood», «tree», «tent», «car» …) aus colors.kind_mats
var _rev_n := -1
var _fog_vol: FogVolume
var _view_attr: CameraAttributesPractical
var _old_view_attr: CameraAttributes
var _t := 0.0
var _slow := 0
var _tex := {}                        # erzeugte Texturen (einmal pro Sitzung)
var _water_shader: Shader
var _water_mats := {}
var _feed_env: Environment            # Umgebung der Kamerabilder für MoveEye: wie env, aber ohne SDFGI (Leistung, Speicher)
var _feed_props: Array = []


# ---- Abfragen -----------------------------------------------------------------------------------------------------------
static func _lite() -> bool:
	"""dieselbe zentrale Abfrage wie Quality.lite() (quality.gd des Lite-Pakets)"""
	return Engine.has_meta("lite") and bool(Engine.get_meta("lite"))


static func forward_plus() -> bool:
	"""Forward+ / Vulkan läuft (SDFGI, SSAO, SSR, Volumen-Nebel gibt es nur dort)"""
	return RenderingServer.get_rendering_device() != null


static func _read() -> Dictionary:
	if not FileAccess.file_exists(FILE):
		return {}
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
	return d if typeof(d) == TYPE_DICTIONARY else {}


static func _write(d: Dictionary) -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify(d))


static func start_check(m, args: Array) -> bool:
	"""beim Start (main._ready, gleich nach _vm_needs_angle): «Hoch» gespeichert, aber OpenGL läuft -> einmal mit Forward+
	neu starten. Ist der letzte Versuch nicht angekommen (Vulkan geht nicht, Fenster ging nie auf), bleibt es bei Normal."""
	var d := _read()
	var want := str(d.get("stufe", "normal")) == "hoch" or "--hoch" in args
	if forward_plus():
		if bool(d.get("pending", false)):
			d["pending"] = false
			_write(d)
		return false
	if not want or "--no-hoch" in args or _lite() or ("--quality" in args and not "--hoch" in args):
		return false
	if bool(d.get("pending", false)) or FLAG in args:
		d["stufe"] = "normal"                         # Forward+ ging beim letzten Mal nicht: nicht nochmals versuchen
		d["pending"] = false
		d["failed"] = true
		_write(d)
		print("graphics Hoch: Forward+ (Vulkan) did not start last time - back to Normal")
		return false
	d["pending"] = true
	_write(d)
	_restart(m, true, true)
	return true


static func _restart(m, fwd: bool, early := false) -> void:
	"""neu starten (mit / ohne Forward+). early: ganz am Anfang von main._ready - noch nichts geladen und nichts offen, also
	auch nichts speichern (release_ports würde sonst die Einstellungen mit den Standardwerten überschreiben)"""
	var a: Array = []
	var skip := false
	for x in OS.get_cmdline_args():
		if skip:
			skip = false
			continue
		if x in ["--rendering-method", "--rendering-driver"]:
			skip = true
			continue
		a.append(x)
	if fwd:
		a.append_array(["--rendering-method", "forward_plus"])
	a.append("--")
	var ua := OS.get_cmdline_user_args()
	var i := 0
	while i < ua.size():
		if ua[i] == "--old-pid":
			i += 2                                      # the pid of an older restart: not again
			continue
		if ua[i] != FLAG and ua[i] != "--hoch":
			a.append(ua[i])
		i += 1
	if fwd:
		a.append(FLAG)
	a.append_array(["--old-pid", str(OS.get_process_id())])
	print("graphics: restart with %s" % ("Forward+ (Hoch)" if fwd else "the normal renderer"))
	if not early and m != null and m.has_method("release_ports"):
		m.release_ports()
	OS.create_process(OS.get_executable_path(), a)
	m.get_tree().quit()


# ---- Bedienung --------------------------------------------------------------------------------------------------------
func _ready() -> void:
	var d := _read()
	stufe = "hoch" if str(d.get("stufe", "normal")) == "hoch" or "--hoch" in OS.get_cmdline_user_args() else "normal"
	dof_free = bool(d.get("dof", false))
	if bool(d.get("failed", false)):
		d.erase("failed")
		_write(d)
		main.start_info = "Grafik «Hoch» braucht Vulkan – auf diesem PC ging es nicht, deshalb wieder «Normal»."
	if "--no-preview" in OS.get_cmdline_user_args():
		main.preview_on = false                         # Messungen: keine Vorschaubilder der Kameras im Fenster
	get_tree().node_added.connect(_on_node_added)
	RenderingServer.frame_pre_draw.connect(_pre_draw)


func set_stufe(v: String) -> void:
	"""aus dem Auswahlfeld «Grafikstufe»"""
	stufe = "hoch" if v == "hoch" else "normal"
	var d := _read()
	d["stufe"] = stufe
	d["pending"] = false
	_write(d)
	if stufe == "hoch" and not forward_plus():
		if _lite():
			main.start_info = "Grafik «Hoch» geht nicht zusammen mit «Lite»."
			return
		main.start_info = "Grafik «Hoch»: der Simulator startet jetzt mit Vulkan neu (braucht eine gute Grafikkarte) …"
		d["pending"] = true
		_write(d)
		get_tree().create_timer(1.2).timeout.connect(func(): _restart(main, true))
		return
	if stufe == "normal" and FLAG in OS.get_cmdline_user_args():
		main.start_info = "Grafik «Normal»: der Simulator startet jetzt wieder mit dem normalen Renderer neu …"
		get_tree().create_timer(1.2).timeout.connect(func(): _restart(main, false))
		return
	main._apply_quality()


func set_dof(on: bool) -> void:
	dof_free = on
	var d := _read()
	d["dof"] = on
	_write(d)


func state_text() -> String:
	if active:
		return "Hoch aktiv (Forward+ / Vulkan)"
	if stufe == "hoch":
		return "Hoch gewählt, aber aus: " + why_off
	return "Normal"


# ---- ein / aus ----------------------------------------------------------------------------------------------------------
func after_quality() -> void:
	"""am Ende von main._apply_quality(): Hoch auf die gewählte Stufe obendrauf (oder wieder weg)"""
	var want := stufe == "hoch" and forward_plus() and not _lite() and why_off != "zu langsam"
	if not forward_plus():
		why_off = "kein Vulkan (OpenGL läuft)"
	elif _lite():
		why_off = "Lite ist an"
	if want:
		why_off = ""
		apply_high(main.env, main.get_viewport(), main)
	elif active:
		remove_high()


static func _skip() -> PackedStringArray:
	"""für Tests / Messungen: --hoch-skip sdfgi,volumetric_fog,ssil,ssr,ssao,glow (einzelne Effekte weglassen)"""
	var ua := OS.get_cmdline_user_args()
	var i := ua.find("--hoch-skip")
	return ua[i + 1].split(",") if i >= 0 and i + 1 < ua.size() else PackedStringArray()


func _keep(obj: Object, prop: String, v) -> void:
	"""Wert setzen und den alten einmal merken (für remove_high)"""
	if obj == null:
		return
	for sk in _skip():
		if prop.begins_with(sk + "_") and v is bool and v:
			return
	var k := [obj.get_instance_id(), prop]
	if not _orig.has(k):
		_orig[k] = [obj, obj.get(prop)]
	obj.set(prop, v)


func apply_high(env: Environment, viewport: Viewport, world: Node) -> void:
	"""die Stufe Hoch einschalten: Umgebung (Licht, Nebel, Nachbearbeitung), Sonne, grosse Ansicht, Oberflächen.
	Die Kamerabilder für MoveEye (SubViewports) teilen sich dieselbe Welt und dieselbe Umgebung - sie bekommen also SDFGI,
	SSAO, Nebel, Spiegelungen und Tonemapping mit, aber kein TAA (das verschmiert bewegte Besucher) und keine Tiefenschärfe."""
	active = true
	# Tonemapping wie eine Kamera: ACES (filmischer Kontrast, helle Lampen laufen weich aus)
	_keep(env, "tonemap_mode", Environment.TONE_MAPPER_ACES)
	_keep(env, "tonemap_white", 6.0)
	_keep(env, "tonemap_exposure", 1.15)
	# Licht vom Himmel als Himmel (nicht als flache Farbe) - SDFGI verdeckt es in Ecken, unter Dächern und Bäumen
	_keep(env, "ambient_light_source", Environment.AMBIENT_SOURCE_SKY)
	_keep(env, "ambient_light_sky_contribution", 1.0)
	_keep(env, "reflected_light_source", Environment.REFLECTION_SOURCE_SKY)
	if env.sky != null:
		_keep(env.sky, "radiance_size", Sky.RADIANCE_SIZE_128)
	# Leuchten: Lampen, Feuer und Scheinwerfer strahlen nachts sichtbar (Schwelle in _tick nach Tageszeit)
	_keep(env, "glow_enabled", true)
	_keep(env, "glow_intensity", 0.75)
	_keep(env, "glow_strength", 1.0)
	_keep(env, "glow_bloom", 0.02)
	_keep(env, "glow_hdr_scale", 2.2)
	_keep(env, "glow_blend_mode", Environment.GLOW_BLEND_MODE_SOFTLIGHT)
	# Schatten in Ecken und Fugen (SSAO), farbiges Streulicht von nahen Flächen (SSIL)
	_keep(env, "ssao_enabled", true)
	_keep(env, "ssao_radius", 1.4)
	_keep(env, "ssao_intensity", 1.8)
	_keep(env, "ssao_power", 1.6)
	_keep(env, "ssao_detail", 0.6)
	_keep(env, "ssao_light_affect", 0.12)
	_keep(env, "ssil_enabled", true)
	_keep(env, "ssil_radius", 4.0)
	_keep(env, "ssil_intensity", 0.9)
	# Spiegelungen auf dem See, in Pfützen, auf nassem Boden und Autolack
	_keep(env, "ssr_enabled", true)
	_keep(env, "ssr_max_steps", 64)
	_keep(env, "ssr_fade_in", 0.15)
	_keep(env, "ssr_fade_out", 2.0)
	_keep(env, "ssr_depth_tolerance", 0.25)
	# globale Beleuchtung: Licht prallt von Wiese, Wänden und Zelt ab (draussen nötig: dynamische Szenen, nichts zu «backen»;
	# VoxelGI wäre günstiger, muss aber für jede Szene gebacken werden - darum SDFGI)
	_keep(env, "sdfgi_enabled", true)
	_keep(env, "sdfgi_use_occlusion", true)
	_keep(env, "sdfgi_read_sky_light", true)
	_keep(env, "sdfgi_bounce_feedback", 0.4)
	_keep(env, "sdfgi_cascades", 4)
	_keep(env, "sdfgi_min_cell_size", 0.25)
	_keep(env, "sdfgi_energy", 1.0)
	_keep(env, "sdfgi_y_scale", Environment.SDFGI_Y_SCALE_75_PERCENT)
	RenderingServer.gi_set_use_half_resolution(true)
	# Volumen-Nebel: Luft mit Tiefe, Lichtkegel von Lampen und Sonnenstrahlen; die Dichte folgt in _tick der Tageszeit und
	# dem Wetter-Nebel von main (env.fog_density, colors.ground_fog)
	_keep(env, "volumetric_fog_enabled", true)
	_keep(env, "volumetric_fog_density", 0.002)
	_keep(env, "volumetric_fog_albedo", Color(0.9, 0.92, 0.95))
	_keep(env, "volumetric_fog_anisotropy", 0.55)
	_keep(env, "volumetric_fog_length", 120.0)
	_keep(env, "volumetric_fog_detail_spread", 2.0)
	_keep(env, "volumetric_fog_gi_inject", 0.6)
	_keep(env, "volumetric_fog_ambient_inject", 0.25)
	_keep(env, "volumetric_fog_sky_affect", 0.05)
	if _fog_vol == null:
		_fog_vol = FogVolume.new()                    # Bodendunst (ein flacher Kasten, folgt der Ansicht)
		_fog_vol.size = Vector3(320, 5, 320)
		_fog_vol.shape = RenderingServer.FOG_VOLUME_SHAPE_BOX
		var fm := FogMaterial.new()
		fm.density = 0.0
		fm.albedo = Color(0.92, 0.94, 0.96)
		fm.height_falloff = 0.9
		fm.edge_fade = 0.25
		_fog_vol.material = fm
		world.add_child(_fog_vol)
	_fog_vol.visible = true
	# Sonne: weiche Schatten wie draussen (Halbschatten wächst mit dem Abstand: PCSS über die echte Sonnengrösse 0.53°)
	var sun: DirectionalLight3D = main.sun
	_keep(sun, "shadow_enabled", true)
	_keep(sun, "light_angular_distance", 0.53)
	_keep(sun, "shadow_blur", 1.0)
	_keep(sun, "directional_shadow_mode", DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS)
	_keep(sun, "directional_shadow_max_distance", 150.0)
	_keep(sun, "directional_shadow_blend_splits", true)
	_keep(main.moonlight, "light_angular_distance", 0.52)
	RenderingServer.directional_shadow_atlas_set_size(4096, true)          # wie «ultra»; 8192 kostet 256 MB Grafikspeicher und bringt mit 4 Stufen kaum mehr
	RenderingServer.directional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_HIGH)
	RenderingServer.positional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_HIGH)
	# grosse Ansicht: TAA + MSAA 2× (die Kamerabilder für MoveEye behalten ihr MSAA 2× und bekommen KEIN TAA)
	_keep(viewport, "msaa_3d", Viewport.MSAA_2X)
	_keep(viewport, "use_taa", true)
	_keep(viewport, "screen_space_aa", Viewport.SCREEN_SPACE_AA_DISABLED)
	_keep(viewport, "positional_shadow_atlas_size", 4096)
	# Belichtungs-Automatik nur in der freien Ansicht (die Kameras haben ihre eigene Belichtung in main / realism.gd)
	if _view_attr == null:
		_view_attr = CameraAttributesPractical.new()
		_view_attr.auto_exposure_enabled = true
		_view_attr.auto_exposure_scale = 0.4
		_view_attr.auto_exposure_speed = 0.6
		_view_attr.auto_exposure_min_sensitivity = 50.0
		_view_attr.auto_exposure_max_sensitivity = 400.0      # nachts höchstens 2 Blenden heller: die Nacht bleibt Nacht
		_view_attr.dof_blur_far_distance = 60.0
		_view_attr.dof_blur_far_transition = 50.0
		_view_attr.dof_blur_amount = 0.04
		_old_view_attr = main.view_cam.attributes
	main.view_cam.attributes = _view_attr
	for c in main.cams:
		if c.attributes is CameraAttributesPractical:     # die Kameras von MoveEye: sicher keine Tiefenschärfe
			c.attributes.dof_blur_far_enabled = false
			c.attributes.dof_blur_near_enabled = false
	_upgrade_all()
	_tick()


func _pre_draw() -> void:
	"""kurz vor dem Zeichnen: die zwei Kameras für MoveEye zeichnen mit einer Kopie der Umgebung ohne SDFGI. SDFGI rechnet
	pro Ansicht eigene Kaskaden (Speicher, Zeit) - für den Videostrom zu teuer; SSAO, SSIL, Nebel, Spiegelungen, Leuchten
	und Tonemapping bleiben gleich. Die Nacht-Kopien von main (night_envs, alle 0.5 s neu) bekommen SDFGI ebenfalls weg."""
	if not active:
		return
	var env: Environment = main.env
	if _feed_env == null:
		_feed_env = env.duplicate()
		for pr in env.get_property_list():
			if pr["usage"] & PROPERTY_USAGE_STORAGE and pr["name"] != "sdfgi_enabled" and pr["name"] != "resource_name":
				_feed_props.append(pr["name"])
	for pn in _feed_props:                               # was main gerade ändert (Licht, Nebel, Blitz …) mitnehmen
		var v = env.get(pn)
		if _feed_env.get(pn) != v:
			_feed_env.set(pn, v)
	_feed_env.sdfgi_enabled = false
	for i in range(2):
		var c: Camera3D = main.cams[i]
		if c.environment == null:
			c.environment = _feed_env
		elif c.environment != _feed_env and c.environment.sdfgi_enabled:
			c.environment.sdfgi_enabled = false


func remove_high() -> void:
	"""zurück zur gewählten Normal-Stufe (alles Gemerkte zurück, dann rechnet main._apply_quality neu)"""
	if not active:
		return
	active = false
	for k in _orig:
		var e: Array = _orig[k]
		if is_instance_valid(e[0]):
			e[0].set(k[1], e[1])
	_orig.clear()
	RenderingServer.gi_set_use_half_resolution(false)
	RenderingServer.directional_soft_shadow_filter_set_quality(int(ProjectSettings.get_setting("rendering/lights_and_shadows/directional_shadow/soft_shadow_filter_quality", 2)))
	RenderingServer.positional_soft_shadow_filter_set_quality(int(ProjectSettings.get_setting("rendering/lights_and_shadows/positional_shadow/soft_shadow_filter_quality", 2)))
	if _fog_vol != null:
		_fog_vol.visible = false
	main.view_cam.attributes = _old_view_attr
	for i in range(2):
		if main.cams[i].environment == _feed_env:
			main.cams[i].environment = null
	main.moonlight.shadow_enabled = false
	_downgrade_all()
	main._apply_quality()


# ---- jede halbe Sekunde: Tageszeit, Wetter ---------------------------------------------------------------------------------
func _process(dt: float) -> void:
	if not active:
		return
	_work_queue()
	_t += dt
	if _t < 0.5:
		return
	_t = 0.0
	_tick()
	_perf()


func _tick() -> void:
	var env: Environment = main.env
	var el: float = main.sun_el()
	var day := clampf((el + 6.0) / 18.0, 0.0, 1.0)
	var twilight := clampf(1.0 - absf(el - 2.0) / 10.0, 0.0, 1.0)     # Morgen- und Abenddämmerung (Sonne -8° … 12°)
	var gf := 0.0
	if main.colors != null and "ground_fog" in main.colors:
		gf = float(main.colors.ground_fog)
	var weather_fog := float(env.fog_density)                          # aus dem Wetter (main._update_sky): klar 0.0007 … Nebel 0.045
	# feiner Dunst in der Luft: etwas immer (Tiefe), mehr in der Dämmerung, viel bei Wetter-Nebel
	env.volumetric_fog_density = 0.0015 + 0.004 * twilight + weather_fog * 0.3 + 0.004 * gf
	env.volumetric_fog_albedo = Color(0.9, 0.92, 0.95) if day > 0.3 else Color(0.75, 0.8, 0.9)
	if _fog_vol != null:
		var fm: FogMaterial = _fog_vol.material
		fm.density = 0.012 * twilight + 0.05 * gf + (0.02 if main.weather == "fog" else 0.0)
		var p: Vector3 = main.view_cam.global_position
		_fog_vol.global_position = Vector3(snappedf(p.x, 10.0), main.ground_y(p.x, p.z) + 1.0, snappedf(p.z, 10.0))
	# Leuchten: nachts tiefere Schwelle (Lampen, Feuer, Scheinwerfer strahlen), am Tag nur sehr Helles (Sonne auf Glas)
	env.glow_hdr_threshold = lerpf(0.7, 1.1, day)
	# Mondschatten in hellen Nächten (wichtig für Fehlalarme: Schatten von Ästen bewegen sich auch nachts)
	main.moonlight.shadow_enabled = not main.sun.visible and main.moonlight.light_energy > 0.004
	# Tiefenschärfe nur in der freien Ansicht und nur wenn gewählt; Blick durch eine Kamera von MoveEye: immer scharf
	if _view_attr != null:
		var free: bool = main.view_mode == 0
		_view_attr.dof_blur_far_enabled = dof_free and free
		_view_attr.auto_exposure_enabled = free


func _perf() -> void:
	"""«Automatisch leichter» (main.auto_perf): bleibt die grosse Ansicht 30 s unter 12 Bildern/s, wird Hoch für diese
	Sitzung abgeschaltet (die Wahl bleibt gespeichert)"""
	if not main.auto_perf or not main.win_open:
		_slow = 0
		return
	if Engine.get_frames_per_second() < 12.0:
		_slow += 1
	else:
		_slow = maxi(0, _slow - 2)
	if _slow >= 60:
		_slow = 0
		why_off = "zu langsam"
		main.start_info = "Grafik «Hoch» war zu langsam – für diese Sitzung aus (die Wahl bleibt gespeichert)."
		remove_high()


# ---- Oberflächen --------------------------------------------------------------------------------------------------------
func _on_node_added(n: Node) -> void:
	if active and n is MeshInstance3D:
		_queue.append(weakref(n))


func _work_queue() -> void:
	var k := 0
	while not _queue.is_empty() and k < 200:
		var w: WeakRef = _queue.pop_back()
		var n = w.get_ref()
		if n != null and n.is_inside_tree():
			_upgrade_node(n)
		k += 1


func _upgrade_all() -> void:
	var todo: Array = [main]
	while not todo.is_empty():
		var n: Node = todo.pop_back()
		todo.append_array(n.get_children())
		if n is MeshInstance3D:
			_upgrade_node(n)
	_upgrade_ground(main.grass_mat)


func _kind(m: StandardMaterial3D) -> String:
	if main.colors == null:
		return ""
	var km: Dictionary = main.colors.kind_mats
	if km.size() != _rev_n:
		_rev_n = km.size()
		_rev.clear()
		for key in km:
			_rev[km[key]] = str(key).get_slice("|", 1)
	return str(_rev.get(m, ""))


func _upgrade_node(mi: MeshInstance3D) -> void:
	if mi.layers & 1 == 0:
		return                                          # nur die sichtbare Welt (nicht das Wärmebild auf Ebene 2)
	var m = mi.material_override
	if not m is StandardMaterial3D:
		return
	var sm: StandardMaterial3D = m
	if _is_water(sm):
		_water_nodes.append([weakref(mi), sm])
		mi.material_override = _water_mat(sm)
		return
	if _mat_orig.has(sm):
		return
	_upgrade_mat(sm, _kind(sm))


func _is_water(m: StandardMaterial3D) -> bool:
	"""See und Teich (scenes.gd): glatt, leicht metallisch, blau"""
	var c := m.albedo_color
	return m.roughness <= 0.15 and m.metallic >= 0.2 and m.metallic <= 0.5 and c.b > c.r * 1.3 and c.b > 0.3 \
			and m.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED and m.albedo_texture == null


func _upgrade_mat(m: StandardMaterial3D, kind: String) -> void:
	var keep := {}
	for p in ["normal_enabled", "normal_texture", "normal_scale", "roughness_texture", "texture_filter", "clearcoat_enabled",
			"clearcoat", "clearcoat_roughness", "uv1_scale", "uv1_triplanar", "uv1_world_triplanar", "rim_enabled", "rim", "rim_tint"]:
		keep[p] = m.get(p)
	_mat_orig[m] = keep
	if m.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED or m.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED:
		return                                          # Glas, Lampen, Leuchtendes: so lassen
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	if m.uv1_triplanar:
		m.roughness_texture = _noise_tex("rough")        # Rauheit nicht überall gleich (Fett, Abrieb, Staub)
	var h := m.albedo_color.h
	var s := m.albedo_color.s
	match kind:
		"stone":
			_nrm(m, "stone", 0.9)
		"wood", "tree":
			_nrm(m, "grain", 0.8)
			if kind == "tree":                          # Rinde: tiefere Furchen längs des Stamms
				m.uv1_scale = Vector3(1.2, 0.35, 1.2)
		"tent":
			_nrm(m, "weave", 0.45)
			m.uv1_scale = Vector3(4.0, 4.0, 4.0)
			m.rim_enabled = true                         # Stoff: heller Saum im Gegenlicht
			m.rim = 0.25
			m.rim_tint = 0.6
		"car", "caravan":
			m.clearcoat_enabled = true                   # Autolack / Wohnwagen: Klarlack-Glanz über der Farbe
			m.clearcoat = 0.7
			m.clearcoat_roughness = 0.12
		"metal":
			m.normal_scale = m.normal_scale * 0.6
		_:
			if s > 0.25 and h > 0.03 and h < 0.13 and m.albedo_color.v < 0.6:
				_nrm(m, "grain", 0.6)                      # braun: wahrscheinlich Holz
			elif s < 0.1:
				_nrm(m, "stone", 0.6)                      # grau: Stein, Beton
			elif m.normal_enabled:
				m.normal_scale = minf(m.normal_scale * 1.8, 0.7)


func _nrm(m: StandardMaterial3D, key: String, k: float) -> void:
	m.normal_enabled = true
	m.normal_texture = _noise_tex(key)
	m.normal_scale = k
	if not m.uv1_triplanar:
		m.uv1_triplanar = true
		m.uv1_world_triplanar = true


const GROUND_ADD := """uniform sampler2D hoch_nrm : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
void fragment() {
	vec3 hw = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	NORMAL_MAP = normalize(mix(texture(hoch_nrm, hw.xz * 0.55).rgb, texture(hoch_nrm, hw.xz * 0.07).rgb, 0.4) * 2.0 - 1.0) * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = 1.4;
"""


func _upgrade_ground(gm: ShaderMaterial) -> void:
	"""Wiese: dieselbe Shader-Datei, im Speicher um eine Normal-Karte ergänzt (Unebenheiten, Grasbüschel) - die Datei
	grass.gdshader bleibt unverändert; passt der Text nicht mehr, bleibt die Wiese wie sie ist"""
	if gm == null or gm.shader == null or _ground_orig.has(gm):
		return
	var code: String = gm.shader.code
	if not "void fragment() {" in code or "NORMAL_MAP" in code:
		return
	var sh := Shader.new()
	sh.code = code.replace("void fragment() {\n", GROUND_ADD)
	_ground_orig[gm] = gm.shader
	gm.shader = sh
	gm.set_shader_parameter("hoch_nrm", _noise_tex("ground"))


func _downgrade_all() -> void:
	for m in _mat_orig:
		if is_instance_valid(m):
			var keep: Dictionary = _mat_orig[m]
			for p in keep:
				m.set(p, keep[p])
	_mat_orig.clear()
	for e in _water_nodes:
		var mi = e[0].get_ref()
		if mi != null:
			mi.material_override = e[1]
	_water_nodes.clear()
	for gm in _ground_orig:
		if is_instance_valid(gm):
			gm.shader = _ground_orig[gm]
	_ground_orig.clear()
	_queue.clear()


func _water_mat(src: StandardMaterial3D) -> ShaderMaterial:
	"""Wasser: zwei gegeneinander wandernde Wellen-Normalkarten, sehr glatt -> der Himmel und das Ufer spiegeln sich (SSR),
	am Rand flach betrachtet mehr Spiegelung (Fresnel), von oben dunkel und tief"""
	if _water_mats.has(src):
		return _water_mats[src]
	if _water_shader == null:
		_water_shader = Shader.new()
		_water_shader.code = """shader_type spatial;
uniform vec4 deep : source_color = vec4(0.06, 0.16, 0.22, 1.0);
uniform sampler2D ripples : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float flow = 1.0;
void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vec3 a = texture(ripples, w.xz * 0.23 + TIME * vec2(0.018, 0.011) * flow).rgb;
	vec3 b = texture(ripples, w.xz * 0.071 - TIME * vec2(0.009, 0.015) * flow).rgb;
	NORMAL_MAP = normalize(mix(a, b, 0.5) * 2.0 - 1.0) * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = 0.35;
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 5.0);
	ALBEDO = deep.rgb * (1.0 - 0.6 * fres);
	ROUGHNESS = 0.02;
	METALLIC = 0.0;
	SPECULAR = 0.5 + 0.5 * fres;
}
"""
	var m := ShaderMaterial.new()
	m.shader = _water_shader
	m.set_shader_parameter("deep", src.albedo_color.darkened(0.45))
	m.set_shader_parameter("ripples", _noise_tex("ripples"))
	_water_mats[src] = m
	return m


func _noise_tex(key: String) -> Texture2D:
	"""alle Texturen aus Rauschen, einmal pro Sitzung (keine Dateien)"""
	if _tex.has(key):
		return _tex[key]
	var t: Texture2D
	match key:
		"rough":
			var fn := FastNoiseLite.new()
			fn.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
			fn.frequency = 0.02
			fn.fractal_octaves = 4
			var nt := NoiseTexture2D.new()
			nt.noise = fn
			nt.seamless = true
			nt.width = 256
			nt.height = 256
			var g := Gradient.new()
			g.set_color(0, Color(0.7, 0.7, 0.7))
			g.set_color(1, Color(1.0, 1.0, 1.0))
			nt.color_ramp = g
			t = nt
		"stone":                                        # Kiesel / Körnung: Zellen-Rauschen
			var fn := FastNoiseLite.new()
			fn.noise_type = FastNoiseLite.TYPE_CELLULAR
			fn.cellular_return_type = FastNoiseLite.RETURN_DISTANCE2_SUB
			fn.frequency = 0.06
			fn.fractal_octaves = 2
			t = _nt(fn, 6.0)
		"ground":                                       # Wiese: Büschel und kleine Mulden
			var fn := FastNoiseLite.new()
			fn.noise_type = FastNoiseLite.TYPE_SIMPLEX
			fn.frequency = 0.05
			fn.fractal_octaves = 5
			fn.fractal_gain = 0.6
			t = _nt(fn, 9.0)
		"ripples":                                      # kleine Wellen
			var fn := FastNoiseLite.new()
			fn.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
			fn.frequency = 0.03
			fn.fractal_octaves = 3
			t = _nt(fn, 4.0)
		"grain", "weave":
			t = _pattern(key)
	_tex[key] = t
	return t


func _nt(fn: FastNoiseLite, bump: float) -> NoiseTexture2D:
	var nt := NoiseTexture2D.new()
	nt.noise = fn
	nt.seamless = true
	nt.width = 256
	nt.height = 256
	nt.as_normal_map = true
	nt.bump_strength = bump
	return nt


func _pattern(key: String) -> Texture2D:
	"""Holzmaserung / Rindenfurchen (verwirbelte Streifen) oder Stoffgewebe - als Höhenbild gerechnet, dann Normal-Karte"""
	var n := 128
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var fn := FastNoiseLite.new()
	fn.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	fn.frequency = 0.05
	for y in range(n):
		for x in range(n):
			var v := 0.0
			if key == "grain":
				var warp := fn.get_noise_2d(x * 0.6, y * 2.5) * 2.5
				v = 0.5 + 0.5 * sin((float(x) / n * 18.0 + warp) * TAU)
				v = pow(v, 3.0)
			else:
				var u := sin(float(x) / n * 64.0 * PI)
				var w := sin(float(y) / n * 64.0 * PI)
				v = 0.5 + 0.25 * (u * signf(w) + w * signf(u)) * 0.5 + 0.08 * fn.get_noise_2d(x * 4.0, y * 4.0)
			img.set_pixel(x, y, Color(v, v, v))
	img.bump_map_to_normal_map(5.0 if key == "grain" else 2.0)
	img.generate_mipmaps()
	return ImageTexture.create_from_image(img)


# ---- für den Himmel (Licht-&-Nacht-Paket) ---------------------------------------------------------------------------------
static func physical_sky(turbidity := 10.0) -> PhysicalSkyMaterial:
	"""ein physikalischer Himmel (Rayleigh-Streuung = Blau, Mie = Dunst um die Sonne) - wird hier NICHT eingesetzt, der
	Himmel gehört dem Licht-&-Nacht-Paket (sky.gdshader mit Mond und Sternen). Werte: Erdatmosphäre auf Meereshöhe."""
	var p := PhysicalSkyMaterial.new()
	p.rayleigh_coefficient = 2.0
	p.rayleigh_color = Color(0.3, 0.405, 0.6)
	p.mie_coefficient = 0.005
	p.mie_eccentricity = 0.8
	p.mie_color = Color(0.69, 0.729, 0.812)
	p.turbidity = turbidity
	p.sun_disk_scale = 1.0
	p.ground_color = Color(0.1, 0.12, 0.08)
	p.energy_multiplier = 1.0
	p.use_debanding = true
	return p


# ---- Steuer-API (Tests, Messungen) --------------------------------------------------------------------------------------
func info() -> Dictionary:
	var vp: Viewport = main.get_viewport()
	RenderingServer.viewport_set_measure_render_time(vp.get_viewport_rid(), true)
	return {"ok": true, "frames": Engine.get_frames_drawn(),
			"render_ms": [snappedf(RenderingServer.viewport_get_measured_render_time_cpu(vp.get_viewport_rid()), 0.01),
					snappedf(RenderingServer.viewport_get_measured_render_time_gpu(vp.get_viewport_rid()), 0.01)], "stufe": stufe, "active": active, "forward_plus": forward_plus(), "lite": _lite(), "why_off": why_off,
			"renderer": "Forward+" if forward_plus() else "Compatibility", "fps": Engine.get_frames_per_second(),
			"materials": _mat_orig.size(), "water": _water_nodes.size(), "ground": _ground_orig.size(), "dof": dof_free}


func op(d: Dictionary) -> Dictionary:
	match str(d.get("do", "info")):
		"set":
			set_stufe(str(d.get("value", "normal")))
		"dof":
			set_dof(bool(d.get("value", false)))
		"off_session":                                  # für Messungen: Hoch aus, ohne die Wahl zu ändern
			why_off = "zu langsam"
			remove_high()
		"on_session":
			why_off = ""
			after_quality()
		"preview":                                      # für Messungen: Vorschaubilder der Kameras im Fenster an / aus
			main.preview_on = bool(d.get("value", true))
	return info()
