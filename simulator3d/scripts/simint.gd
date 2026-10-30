extends Node
## Simulator «wie echt» für MoveEye (Entwurf 30.10.2026, Wunsch Daniel) – vier Dinge, die bisher fehlten:
##   1. Lautsprecher: was MoveEye abspielt (Sirene, Wecker-Melodie, Stimme – mw.sound, auch im Test-Postfach-Betrieb) hört man
##      hier am PC (einfache erzeugte Töne, Lautstärke, Stummschalter) UND das simulierte Mikrofon am Gerät hört es (sound_db,
##      Pieps-/Knall-Töne zusätzlich als kurze Geräusche wie Klatschen): so lässt sich prüfen, dass MoveEye nicht auf seine eigene
##      Sirene hereinfällt (Lärm-Alarm, Klatschschalter).
##   2. Servo-Störungen (Karte «Testen» → «Störungen»): Unterspannung aus dem simulierten Akku (power.gd: 5-V-Schiene des USV-HAT
##      sackt bei schwachem Akku und Servo-Strom ab – die Servos werden schwach und stottern), PCA9685-Reset (Kopf steht, bis
##      MoveEye den Treiber neu einrichtet), I2C-Fehler (5 s keine Antwort), Servo blockiert am Anschlag (Kopf klemmt).
##      MoveEye bekommt die Werte mit jeder Antwort («servo_sim», world_reply über net.gd) und reagiert wie bei echter Hardware.
##   3. Wärmebild-Modell: «Thermal-90 (Waveshare)» (80 × 62, 90° × 67°, 15 Bilder/s wie der Treiber, NETD 125 mK) oder das alte
##      45°-Modell (45° × 35°, 8 Bilder/s) – /info meldet das gewählte Modell.
##   4. Warme Hand: eine Hand (34 °C) 2 m vor dem Kopf, die sich langsam bewegt – für den Assistenten «Wärmebild ausrichten» von
##      MoveEye (findet den warmen Fleck im Wärmebild und die Bewegung im Kamerabild).
## Einstellungen: user://simint.json (eigene Datei).

var main
const FILE := "user://simint.json"

# ---- 1. Lautsprecher -------------------------------------------------------------------------------------------------
var spk_vol := 50.0                  # % auf dem PC
var spk_mute := false                # PC stumm (das simulierte Mikrofon hört die Sirene trotzdem)
var _player: AudioStreamPlayer
var _cache := {}                     # kind -> AudioStreamWAV
var _cur := ""
var _snd_t := 0.0
var _clap_t := 0.0
const RATE := 22050

# ---- 2. Servo-Störungen ------------------------------------------------------------------------------------------------
var uv_force := false                # «Unterspannung erzwingen» (sonst nur aus dem Akku)
var i2c_until := 0.0
var pca_id := 0                      # zählt die PCA9685-Resets (MoveEye merkt jeden einmal)
var pca_hold := false                # Kopf steht, bis MoveEye den Treiber neu einrichtet
var pca_reinit0 := 0
var pca_t := 0.0
var block_axis := ""                 # "" | "pan" | "tilt": Servo klemmt am Anschlag
var _uv := false
var _stut := 0.0

# ---- 3. Wärmebild-Modell ----------------------------------------------------------------------------------------------
const TH_MODELS := {
	"t90": {"name": "Thermal-90 (Waveshare)", "fov_h": 90.0, "fov_v": 67.0, "fps": 15.0, "netd": 0.125},
	"t45": {"name": "45°-Modell (alt)", "fov_h": 45.0, "fov_v": 35.0, "fps": 8.0, "netd": 0.15}}
var th_model := "t90"
var _th_applied := ""

# ---- 4. Warme Hand -----------------------------------------------------------------------------------------------------
var hand_on := false
var _hand: Node3D = null
var _hand_t0 := 0.0
var info_label: Label


func _ready() -> void:
	if FileAccess.file_exists(FILE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
		if typeof(d) == TYPE_DICTIONARY:
			spk_vol = clampf(float(d.get("spk_vol", spk_vol)), 0.0, 100.0)
			spk_mute = bool(d.get("spk_mute", spk_mute))
			if TH_MODELS.has(str(d.get("th_model", th_model))):
				th_model = str(d.get("th_model", th_model))
	_player = AudioStreamPlayer.new()
	add_child(_player)


func save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"spk_vol": spk_vol, "spk_mute": spk_mute, "th_model": th_model}))


# ======================================================================================================================
# 1. Lautsprecher
# ======================================================================================================================
func mw_sound() -> String:
	"""what MoveEye plays right now ('' = nothing); MoveEye 2.98.49+ sends the real kind (siren, chime, tts …)"""
	if main.now() - main.mw_t > 3.0:
		return ""
	return str(main.mw.get("sound", ""))


func _family(k: String) -> String:
	if k in ["siren", "two-tone", "beeps", "horn", "whistle", "bangs", "chime", "birds", "marmot"]:
		return k
	if k.begins_with("beep"):
		return "beeps"
	return "voice"                                    # talk, tts, own sound files: a voice-like murmur


func db_1m() -> float:
	"""the loudness of the loudspeaker of MoveEye at 1 m (same scale as the sounds of the world: 0 = very loud).
	PAM8403 + small speaker: about -2 dB (= a shout) at 100 %, the wake-up melody is softer"""
	var v := clampf(float(main.mw.get("sound_vol", 80.0)) / 100.0, 0.05, 1.0)
	var k := _family(mw_sound())
	var base := -2.0 if k in ["siren", "two-tone", "horn", "whistle", "beeps", "bangs"] else -10.0
	return base + 20.0 * log(v) / log(10.0)


func _process(_delta: float) -> void:
	if main == null:
		return
	if _th_applied != th_model and main.cams.size() >= 3 and main.vps.size() >= 3:
		apply_thermal()
	var k := mw_sound()
	var t: float = main.now()
	if k != _cur:
		_cur = k
		if k == "":
			_player.stop()
		else:
			_play(_family(k))
	if k != "":
		_player.volume_db = -80.0 if (spk_mute or not main.sound_on) else linear_to_db(maxf(0.001, spk_vol / 100.0)) - 6.0
		if t - _snd_t > 0.4:                          # the simulated microphone at the device hears it
			_snd_t = t
			main.add_sound(db_1m(), _dev_pos(), 0.7)
		var fam := _family(k)
		if fam in ["beeps", "bangs", "marmot"] and t - _clap_t > 2.0 and main.sound_on:
			_clap_t = t                               # short loud pulses: a clap switch could take them for claps
			main.sound_ev_id += 1
			main.sound_ev.append({"id": main.sound_ev_id, "kind": "clap", "n": 3, "db": snappedf(db_1m(), 0.1), "t": t, "own": true})
	_servo_tick(t)
	if hand_on:
		_hand_tick(t)
	if info_label != null and Engine.get_process_frames() % 20 == 0:
		info_label.text = main.no_emoji(status_text())   # 3D-4.22: ♪ ⚡ ⚠ - no empty boxes (MoveEye gets them with the symbols)


func _dev_pos() -> Vector3:
	return main.head.global_position if main.head != null else Vector3(0, main.HEAD_H, 0)


func _play(fam: String) -> void:
	if not _cache.has(fam):
		_cache[fam] = _make(fam)
	_player.stream = _cache[fam]
	_player.play()


func _make(fam: String) -> AudioStreamWAV:
	"""a loop of a few seconds, made here (no sound files): like MoveEye's sound_samples (250), simpler"""
	var secs := {"siren": 3.6, "two-tone": 2.4, "beeps": 1.0, "horn": 3.0, "whistle": 1.2, "bangs": 2.0, "chime": 3.2,
			"birds": 3.0, "marmot": 2.0, "voice": 2.4}.get(fam, 2.0) as float
	var n := int(secs * RATE)
	var data := PackedByteArray()
	data.resize(n * 2)
	var ph := 0.0
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	for i in range(n):
		var t := float(i) / RATE
		var v := 0.0
		match fam:
			"siren":
				ph += TAU * (950.0 + 550.0 * sin(TAU * t / 1.8)) / RATE
				v = (sin(ph) + 0.35 * sin(2.0 * ph)) * 0.6
			"two-tone":
				ph += TAU * (960.0 if fmod(t, 1.2) < 0.6 else 770.0) / RATE
				v = (sin(ph) + 0.3 * sin(2.0 * ph)) * 0.6
			"beeps":
				ph += TAU * 2400.0 / RATE
				v = sin(ph) * (0.6 if fmod(t, 0.25) < 0.12 else 0.0)
			"horn":
				ph += TAU * 330.0 / RATE
				v = (sin(ph) + 0.4 * sin(2.0 * ph) + 0.25 * sin(3.0 * ph)) * (0.5 if fmod(t, 1.5) < 1.0 else 0.0)
			"whistle":
				ph += TAU * (6500.0 + 3500.0 * absf(fmod(t * 3.0, 2.0) - 1.0)) / RATE
				v = sin(ph) * (0.5 if fmod(t, 0.6) < 0.45 else 0.0)
			"bangs":
				var dt := fmod(t, 0.45)
				v = rng.randf_range(-1.0, 1.0) * exp(-dt / 0.012) * 0.8
			"chime":
				var notes := [523.25, 659.25, 783.99, 1046.5, 783.99, 659.25]
				for kk in range(notes.size()):
					var st := kk * 0.32
					if t >= st and t < st + 1.6:
						var tt := t - st
						v += sin(TAU * float(notes[kk]) * tt) * exp(-tt * 2.6) * 0.3
			"birds":
				var c := fmod(t, 0.75)
				if c < 0.11:
					ph += TAU * (3200.0 + 1800.0 * c / 0.11) / RATE
					v = sin(ph) * sin(PI * c / 0.11) * 0.5
			"marmot":
				var m := fmod(t, 1.0)
				if m < 0.26:
					ph += TAU * (3000.0 - 900.0 * pow(m / 0.26, 1.5)) / RATE
					v = sin(ph) * 0.5
			_:                                         # voice: a buzzing «murmur» with syllables
				var syl := 0.5 + 0.5 * sin(TAU * 4.0 * t + sin(TAU * 0.7 * t) * 2.0)
				ph += TAU * (130.0 + 25.0 * sin(TAU * 1.3 * t)) / RATE
				v = (sin(ph) + 0.5 * sin(3.0 * ph) + 0.3 * sin(5.0 * ph) + 0.2 * sin(8.0 * ph)) * syl * 0.3
		data.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 30000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = RATE
	w.stereo = false
	w.data = data
	w.loop_mode = AudioStreamWAV.LOOP_FORWARD
	w.loop_begin = 0
	w.loop_end = n
	return w


# ======================================================================================================================
# 2. Servo-Störungen
# ======================================================================================================================
func v5() -> float:
	"""the 5 V rail of the UPS HAT (what the Pi and the servos get): sags with a weak battery and with the servo current"""
	var v := 5.12
	var sv: Dictionary = main.mw.get("servo", {}) if main.mw.get("servo") is Dictionary else {}
	var moving: bool = bool(sv.get("moving", false)) and main.now() - main.mw_t < 3.0
	var sw = main.simwerte
	if sw != null and sw.batt_on and not sw.mains:
		var vb: float = float(sw.volts)
		if vb < 6.8:
			v -= (6.8 - vb) * 0.9                     # the boost converter cannot hold 5 V any more
		if sw.empty:
			v = 4.3
	if moving:
		v -= 0.18                                     # two MG90S starting: a short current peak
	if uv_force:
		v = minf(v, 4.55)
	return v


func uv() -> bool:
	return _uv


func _servo_tick(t: float) -> void:
	var x := v5()
	_uv = x < (4.70 if _uv else 4.63)                 # the Pi 5 reports under-voltage below about 4.63 V (with hysteresis)
	if pca_hold:
		var sv: Dictionary = main.mw.get("servo", {}) if main.mw.get("servo") is Dictionary else {}
		if int(sv.get("reinit", 0)) > pca_reinit0 or t - pca_t > 180.0:
			pca_hold = false                          # MoveEye has set the driver up again (or nobody cares: after 3 min)
			main.start_info = "PCA9685: MoveEye hat den Servo-Treiber neu eingerichtet – der Kopf folgt wieder"
	if _uv and t > _stut + 0.25 and randf() < 0.06:
		_stut = t + randf_range(0.05, 0.2)           # under-voltage: the servos stutter (short stops)


func servo_k() -> float:
	"""speed factor for the head (main.gd): under-voltage = weak and stuttering"""
	if _uv:
		return 0.0 if main.now() < _stut else 0.35
	return 1.0


func hold(axis: String) -> bool:
	"""this axis does not move now (no I2C, the PCA9685 is asleep after a reset, the servo is blocked)"""
	return main.now() < i2c_until or pca_hold or block_axis == axis


func head_follows_mw() -> bool:
	"""does the head follow MoveEye's angles right now? (not the game guard, the patrol, the training pictures, the replay)"""
	if main.game != null and main.game.guard_auto:
		return false
	if main.patrol != null and main.patrol.active and not main.measuring() and not main.mw_following():
		return false
	if main.dataset != null and main.dataset.servo != null:
		return false
	if main.replay != null and main.replay.on:
		return false
	return true


func pca_reset() -> void:
	var sv: Dictionary = main.mw.get("servo", {}) if main.mw.get("servo") is Dictionary else {}
	pca_id += 1
	pca_hold = true
	pca_reinit0 = int(sv.get("reinit", 0))
	pca_t = main.now()
	main.start_info = "Störung: PCA9685-Reset (Brown-out) – die Servos sind kraftlos, bis MoveEye den Treiber neu einrichtet («Freigeben»)"


func i2c_error(secs := 5.0) -> void:
	i2c_until = main.now() + secs
	main.start_info = "Störung: I2C-Fehler – der Servo-Treiber antwortet %d s nicht" % int(secs)


func set_block(axis: String) -> void:
	block_axis = axis
	main.start_info = ("Störung: %s-Servo blockiert am Anschlag – der Kopf klemmt" % ("Schwenk" if axis == "pan" else "Neige")) if axis != "" else "Servo wieder frei"


func clear_faults() -> void:
	uv_force = false
	i2c_until = 0.0
	pca_hold = false
	block_axis = ""
	main.start_info = "Störungen aus – alles normal"


# ======================================================================================================================
# 3. Wärmebild-Modell
# ======================================================================================================================
func th() -> Dictionary:
	return TH_MODELS.get(th_model, TH_MODELS["t90"])


func apply_thermal() -> void:
	"""field of view, picture size (non-square pixels like the real lens: 90° × 67°), frames per second, noise"""
	var m := th()
	_th_applied = th_model
	main.TH_FOV = float(m["fov_h"])
	main.th_fps = float(m["fps"])
	main.th_noise = float(m["netd"])
	if main.cams.size() >= 3:
		main.cams[2].fov = float(m["fov_h"])
	if main.vps.size() >= 3:
		var w: int = main.TH_W * 2
		var h: int = int(round(w * tan(deg_to_rad(float(m["fov_v"]) * 0.5)) / tan(deg_to_rad(float(m["fov_h"]) * 0.5))))
		main.vps[2].size = Vector2i(w, maxi(h, 4))
	if main.dev2 != null and main.dev2.get("tcam") != null:
		main.dev2.tcam.fov = float(m["fov_h"])


func set_model(m: String) -> void:
	if not TH_MODELS.has(m):
		return
	th_model = m
	apply_thermal()
	save()
	main.start_info = "Wärmebild: %s – %d° × %d°, %d Bilder/s" % [str(th()["name"]), int(th()["fov_h"]), int(th()["fov_v"]), int(th()["fps"])]


func thermal_info() -> Dictionary:
	var m := th()
	return {"w": main.TH_W, "h": main.TH_H, "fps": float(m["fps"]), "fov_h": float(m["fov_h"]), "fov_v": float(m["fov_v"]),
			"unit": "C", "on_head": true, "model": th_model, "name": str(m["name"]), "netd_mk": int(round(float(m["netd"]) * 1000.0))}


# ======================================================================================================================
# 4. Warme Hand vor dem Kopf
# ======================================================================================================================
func set_hand(on: bool) -> void:
	hand_on = on
	if on and _hand == null:
		_hand = Node3D.new()
		main.add_child(_hand)
		var skin := StandardMaterial3D.new()
		skin.albedo_color = Color(0.86, 0.66, 0.55)
		main.add_mesh(_hand, main.box(0.10, 0.12, 0.03), Vector3(0, 0, 0), skin, 34.0)          # palm
		for i in range(4):                                                                        # fingers
			main.add_mesh(_hand, main.box(0.018, 0.075, 0.02), Vector3(-0.036 + i * 0.024, 0.095, 0), skin, 33.0)
		main.add_mesh(_hand, main.box(0.02, 0.06, 0.02), Vector3(0.065, 0.02, 0), skin, 33.0, Vector3(0, 0, -0.6))
		main.add_mesh(_hand, main.box(0.07, 0.30, 0.06), Vector3(0, -0.21, 0.02), skin, 32.5)   # forearm (warm too)
		_hand_t0 = main.now()
	if _hand != null:
		_hand.visible = on
		_hand.process_mode = Node.PROCESS_MODE_INHERIT if on else Node.PROCESS_MODE_DISABLED
	main.start_info = "Warme Hand vor MoveEye: bewegt sich langsam 2 m vor dem Kopf (für «Wärmebild ausrichten» in MoveEye)" if on else "Warme Hand weg"


func _hand_tick(t: float) -> void:
	if _hand == null or main.cams.size() < 1:
		return
	var k := t - _hand_t0
	var cam: Camera3D = main.cams[0]
	var off := Vector3(0.55 * sin(k * 0.45), 0.08 + 0.30 * sin(k * 0.31 + 0.7), -2.0)   # a slow figure, 2 m in front
	var tr: Transform3D = cam.global_transform
	_hand.global_transform = Transform3D(tr.basis, tr * off)


# ======================================================================================================================
# answer to MoveEye, controls, info line
# ======================================================================================================================
func reply() -> Dictionary:
	"""added to world_reply in net.gd (MoveEye 554 / 555 / 557)"""
	return {"servo_sim": {"v5": snappedf(v5(), 0.01), "uv": _uv, "i2c": main.now() < i2c_until, "pca_reset": pca_id,
			"pca_hold": pca_hold, "blocked": block_axis, "head_mw": head_follows_mw()},
			"thermal_model": thermal_info(), "warm_hand": hand_on}


func op(d: Dictionary) -> Dictionary:
	"""control action «simint» (tests, remote): {do: info | uv (on) | pca | i2c (s) | block (axis) | off | model (m) | hand (on)}"""
	match str(d.get("do", "info")):
		"uv":
			uv_force = bool(d.get("on", true))
		"pca":
			pca_reset()
		"i2c":
			i2c_error(float(d.get("s", 5.0)))
		"block":
			set_block(str(d.get("axis", "")))
		"off":
			clear_faults()
		"model":
			set_model(str(d.get("m", "t90")))
		"hand":
			set_hand(bool(d.get("on", true)))
	var r := reply()
	r["ok"] = true
	r["playing"] = _cur
	r["sound_db"] = snappedf(main.sound_db(), 0.1)
	r["sound_ev_last"] = main.sound_ev_id
	r["spk"] = {"vol": spk_vol, "mute": spk_mute, "pc_on": main.sound_on}
	r["th_render"] = [main.vps[2].size.x, main.vps[2].size.y] if main.vps.size() >= 3 else []
	r["th_fov"] = main.TH_FOV
	r["status"] = status_text()
	return r


func status_text() -> String:
	var s := "♪ MoveEye spielt: %s" % (_cur if _cur != "" else "nichts")
	if _cur != "":
		s += " · am PC %s" % ("stumm" if spk_mute or not main.sound_on else "%d %%" % int(spk_vol))
	s += "\n⚡ 5-V-Schiene %.2f V%s" % [v5(), " · ⚠ Unterspannung (Servos schwach)" if _uv else ""]
	var f := []
	if main.now() < i2c_until:
		f.append("I2C-Fehler")
	if pca_hold:
		f.append("PCA9685-Reset (wartet auf MoveEye)")
	if block_axis != "":
		f.append(("Schwenk" if block_axis == "pan" else "Neige") + "-Servo blockiert")
	if not f.is_empty():
		s += "\n⚠ " + " · ".join(PackedStringArray(f))
	return s


func add_controls() -> void:
	var g := "Licht & Ton"                              # 3D-4.22: like MoveEye (Licht & Ton → Lautsprecher), before «Sensoren»
	var S := {"sub": "Lautsprecher"}
	main.add_control("slider", "spk_vol", "♪ Lautsprecher von MoveEye am PC (Sirene, Wecker, Stimme)", func(): return spk_vol,
			func(v): spk_vol = clampf(float(v), 0.0, 100.0); save(), g, {"sub": "Lautsprecher", "min": 0, "max": 100, "step": 5, "unit": "%"})
	main.add_control("toggle", "spk_mute", "Am PC stumm (das simulierte Mikrofon hört es trotzdem)", func(): return spk_mute,
			func(v): spk_mute = bool(v); save(), g, S)
	var T := {"sub": "Störungen"}                      # card «Testen» → «Störungen» (main.gd), and the Simulator control of MoveEye
	main.add_control("toggle", "stoer_uv", "⚡ Unterspannung erzwingen (5 V sackt ab, Servos schwach)", func(): return uv_force,
			func(v): uv_force = bool(v), "Testlauf", T)
	main.add_control("button", "stoer_pca", "PCA9685-Reset (Brown-out)", null, func(): pca_reset(), "Testlauf", T)
	main.add_control("button", "stoer_i2c", "I2C-Fehler (5 s keine Antwort)", null, func(): i2c_error(5.0), "Testlauf", T)
	main.add_control("select", "stoer_block", "Servo blockiert am Anschlag", func(): return block_axis if block_axis != "" else "off",
			func(v): set_block("" if str(v) == "off" else str(v)), "Testlauf",
			{"sub": "Störungen", "options": [["off", "frei"], ["pan", "Schwenken klemmt"], ["tilt", "Neigen klemmt"]]})
	main.add_control("button", "stoer_off", "Alle Störungen aus", null, func(): clear_faults(), "Testlauf", T)
	var W := {"sub": "Wärmebild"}
	main.add_control("select", "th_model", "🌡 Wärmebild-Kamera", func(): return th_model, func(v): set_model(str(v)), "Kamerabild",
			{"sub": "Wärmebild", "options": [["t90", "Thermal-90 (Waveshare) · 90° × 67° · 15 Bilder/s"], ["t45", "45°-Modell (alt) · 45° × 35° · 8 Bilder/s"]]})
	main.add_control("toggle", "warm_hand", "Warme Hand vor MoveEye (für «Wärmebild ausrichten»)", func(): return hand_on,
			func(v): set_hand(bool(v)), "Kamerabild", W)


func add_info(parent: Control, ui) -> void:
	info_label = ui.small(main.no_emoji(status_text()))
	info_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	parent.add_child(info_label)
