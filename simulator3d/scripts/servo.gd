extends Node
## «Servo-Mechanik» (Zweig real-servo, 31.10.2026): die beiden Kopf-Servos (Schwenken / Neigen) wie zwei echte MG90S - Teil
## von «Servos wie echt» (realism.servo_real; aus = wie bisher: feste 200 °/s, kleines Nachschwingen der Kamera).
##  Modell pro Achse (Schritte von 1 ms):
##   - Regler im Servo: Potentiometer an der Abtriebswelle (= Kopf), Totband 5 µs (~0,5°), voller Antrieb ab ~8° Abweichung,
##     darunter proportional (analoger Servo-Regler). Ein Puls alle 20 ms (50 Hz wie der PCA9685).
##   - Motor + Getriebe: Leerlauf-Tempo 0,1 s/60° bei 4,8 V (MG90S-Datenblatt; 0,08 s/60° bei 6 V) -> 600 °/s × U / 4,8 V,
##     Anlaufen mit Zeitkonstante 10 ms + Kopflast (100 g -> 18 ms), Reibung (Leerlaufstrom ~ 0,1 A).
##   - Strom wie ein Gleichstrommotor: I = I_Block × (Antrieb − Drehzahl) -> beim Anlaufen ~0,7 A pro Servo (Blockierstrom
##     MG90S ~ 0,7 A bei 4,8 V), beim Drehen ~0,1 A, im Totband 0. Blockiert ein Servo (Störung), fliesst dauernd 0,7 A.
##   - Getriebespiel 1,5° (MG90S Metallgetriebe 1-2°, einstellbar 0-3°): der Kopf ist darin frei - er läuft beim Bremsen
##     mit seiner Trägheit weiter, schlägt an, federt zurück (Horn / Zähne ~30 Hz bei 100 g, schwach gedämpft):
##     Überschwingen ~1°, nach ~0,15 s ruhig. Beim Neigen hängt der Kopf im Spiel nach unten (Schwerpunkt vor der Achse).
##   - Kopfmasse 80-120 g (Kamera, Halter, Wärmebild; Weitwinkel-Kamera auf dem Kopf +25 g): schwerer = träger, tiefer federnd.
##   - Spannung: die 5-V-Schiene (simint.gd v5) sackt mit dem Strom der Servos ab (Innenwiderstand USV-HAT + Leitungen 0,22 Ω:
##     zwei Servos starten = 1,4 A = -0,3 V). Unterspannung bleibt wie bisher in simint (schwach, stottert, MoveEye meldet).
##   - Schwaches Signal (Störung «Schwaches Servosignal», oder Schiene unter 4,75 V): der Puls zittert um ±4 µs (~±0,4°) -
##     der Kopf zuckt immer wieder (ruckelnde Bilder am Rand, mögliche Fehlalarme).
##  Ausgaben: main.pan_vel / main.tilt_vel (rad/s, die echte Kopfbewegung mit Überschwingen - Bewegungsunschärfe im
##   Kamera-Paket), rate() in °/s, current() in A, im world_reply servo_sim: i_a, head_dps.
##  Nicht im Modell: Erwärmung, Verschleiss, Last durch Wind. Lite: gleich (kostet fast nichts: 2 Achsen × ~16 Schritte/Bild).
## Einstellungen in user://servo.json. Test: /control {"action": "servo", "do": info | set (key, value) | step (axis, deg, s)}.

const FILE := "user://servo.json"
const SAVE := ["mass_g", "play_deg", "weak_signal"]

# MG90S (TowerPro-Datenblatt: 4,8 V 0,1 s/60°, 6 V 0,08 s/60°, Blockiermoment 1,8 / 2,2 kg·cm, Totband 5 µs)
const W_NOLOAD := 600.0          # °/s bei 4,8 V (0,1 s / 60°)
const V_REF := 4.8
const I_STALL := 0.7             # A bei 4,8 V (Anlauf / blockiert, gemessen typ. 0,65-0,8 A)
const I_IDLE := 0.006            # A Ruhestrom der Elektronik
const FRIC := 0.14               # Reibung als Anteil des Antriebs (-> ~0,1 A beim Drehen ohne Last)
const DEAD := 0.5                # ° Totband (5 µs bei ~0,09 °/µs)
const BAND := 8.0                # ° ab hier voller Antrieb
const TAU0 := 0.010              # s Anlaufen Motor + Getriebe ohne Kopf
const TAU_G := 0.00008           # s pro Gramm Kopf
const F_HORN := 30.0             # Hz Feder Horn / Zähne bei 100 g
const ZETA := 0.3                # Dämpfung im Anschlag (Metallzähne, Kunststoffhorn, Fett)
const TAU_FREE := 0.03           # s: so schnell bremst die Lagerreibung den freien Kopf im Spiel
const R_SRC := 0.22              # Ω Innenwiderstand 5-V-Schiene (USV-HAT Boost + Leitungen)
const DT := 0.001
const PWM_T := 0.02              # 50 Hz
const JIT_DEG := 0.4             # ± bei schwachem Signal (±4 µs)

var main
var mass_g := 100.0
var play_deg := 1.5
var weak_signal := false

# state per axis: m = gear output (°), w = its speed (°/s), h = head (°), hv = head speed (°/s), tgt = target after the pulse
var ax := {"pan": {}, "tilt": {}}
var _i_avg := 0.0                # A both servos, mean of the last frame
var _i_peak := 0.0               # A highest of the last 0.5 s
var _peak_t := 0.0
var _v := 5.1                    # rail used for speed / current (from simint, without our own drop: last frame)
var _pwm_t := 0.0
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE)) if FileAccess.file_exists(FILE) else null
	if typeof(d) == TYPE_DICTIONARY:
		mass_g = clampf(float(d.get("mass_g", mass_g)), 80.0, 120.0)
		play_deg = clampf(float(d.get("play_deg", play_deg)), 0.0, 3.0)
		weak_signal = bool(d.get("weak_signal", weak_signal))
	_rng.randomize()
	for k in ax:
		ax[k] = _fresh(0.0)


func save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"mass_g": mass_g, "play_deg": play_deg, "weak_signal": weak_signal}))


static func _fresh(deg: float) -> Dictionary:
	return {"m": deg, "w": 0.0, "h": deg, "hv": 0.0, "cmd": deg, "tgt": deg, "i": 0.0, "u": 0.0, "set": false}


func active() -> bool:
	"""the model drives the head (Servos wie echt on)"""
	return main != null and main.realism != null and main.realism.servo_real


func load_g() -> float:
	var g := mass_g
	if main != null and main.weit != null and main.weit.has_method("on_head") and main.weit.on_head() and bool(main.weit.heavy):
		g += 25.0                                   # the wide camera on the head
	return g


func speed_dps(v := -1.0) -> float:
	"""no-load speed at this rail voltage (°/s)"""
	return W_NOLOAD * clampf((_v if v < 0.0 else v) / V_REF, 0.0, 1.4)


func signal_weak() -> bool:
	return weak_signal or _v < 4.75


# ---- one frame (main._process) ----------------------------------------------------------------------------------------
func step(dt: float, want_pan: float, want_tilt: float, hold_pan := false, hold_tilt := false) -> void:
	"""want_* in radians of the head nodes (head.rotation.y / head_pitch.rotation.x); moves them, sets main.pan_vel / tilt_vel"""
	var sim = main.simint
	_v = float(sim.v5_base()) if sim != null and sim.has_method("v5_base") else 5.1
	var k_uv: float = float(sim.servo_k()) if sim != null else 1.0      # under-voltage: weak (0.35) or stuttering (0)
	var off: bool = sim != null and bool(sim.pca_hold)                  # PCA9685 asleep: no pulses at all
	var frozen: bool = sim != null and main.now() < float(sim.i2c_until)   # I2C: the driver keeps the last pulse
	var blk: String = str(sim.block_axis) if sim != null else ""
	var nodes := {"pan": [main.head, "y", want_pan], "tilt": [main.head_pitch, "x", want_tilt]}
	var hold := {"pan": hold_pan, "tilt": hold_tilt}
	for k in ax:
		var s: Dictionary = ax[k]
		var nd: Node3D = nodes[k][0]
		var cur := rad_to_deg(nd.rotation.y if k == "pan" else nd.rotation.x)
		if not bool(s["set"]) or absf(cur - float(s["h"])) > 0.05:    # first frame / somebody else moved the head
			ax[k] = _fresh(cur)
			ax[k]["set"] = true
			s = ax[k]
		if not frozen:
			s["cmd"] = rad_to_deg(float(nodes[k][2]))
	var n := clampi(roundi(dt / DT), 1, 60)
	var h_ := dt / float(n)
	var mg := load_g()
	var tau := TAU0 + TAU_G * mg
	var wn := TAU * F_HORN * sqrt(100.0 / mg)
	var wmax := speed_dps()                      # the wide camera on the head: heavier (load_g), not slower by a factor
	var i_sum := 0.0
	for _i in range(n):
		_pwm_t += h_
		var pulse := _pwm_t >= PWM_T
		if pulse:
			_pwm_t = fmod(_pwm_t, PWM_T)
		var i_now := 0.0
		for k in ax:
			var s: Dictionary = ax[k]
			if pulse:                                    # a new pulse: the servo reads its target (with jitter on a weak signal)
				var j := _rng.randfn(0.0, JIT_DEG * 0.6) if signal_weak() else 0.0
				s["tgt"] = float(s["cmd"]) + clampf(j, -JIT_DEG * 1.5, JIT_DEG * 1.5)
			var e: float = float(s["tgt"]) - float(s["h"])
			var u := 0.0
			if not off and not bool(hold[k]) and absf(e) > DEAD:
				u = clampf(e / BAND, -1.0, 1.0) * k_uv
			var stuck: bool = blk == k
			var wf: float = float(s["w"]) / maxf(wmax, 1.0)
			if stuck:
				s["w"] = 0.0
				s["i"] = I_STALL * _v / V_REF * absf(u if u != 0.0 else (signf(e) if absf(e) > DEAD and not off else 0.0))
			else:
				var fr := FRIC * signf(wf) if absf(wf) > 0.002 else 0.0
				var acc := (u - wf - fr) / tau if u != 0.0 else (-wf / 0.004)    # unpowered: the gears stop it at once
				s["w"] = float(s["w"]) + acc * wmax * h_
				s["i"] = I_STALL * _v / V_REF * absf(u - wf) if u != 0.0 else 0.0
				s["m"] = float(s["m"]) + float(s["w"]) * h_
			s["u"] = u
			# the head on the output: free inside the play, a spring on the teeth outside
			var g: float = float(s["h"]) - float(s["m"])
			var half := play_deg / 2.0
			var a := 0.0
			if absf(g) > half:
				a = -wn * wn * (g - signf(g) * half) - 2.0 * ZETA * wn * (float(s["hv"]) - float(s["w"]))
			else:
				a = -float(s["hv"]) / TAU_FREE
				if k == "tilt":
					a -= 400.0                           # the head hangs forward: inside the play it sinks (°/s²)
			if stuck:
				s["hv"] = 0.0
				s["m"] = float(s["h"]) - clampf(g, -half, half)
			else:
				s["hv"] = float(s["hv"]) + a * h_
				s["h"] = float(s["h"]) + float(s["hv"]) * h_
			i_now += float(s["i"])
		i_sum += i_now
	_i_avg = I_IDLE * 2.0 + i_sum / float(n)
	var t: float = main.now()
	if _i_avg > _i_peak or t - _peak_t > 0.5:
		_i_peak = _i_avg
		_peak_t = t
	main.head.rotation.y = deg_to_rad(float(ax["pan"]["h"]))
	main.head_pitch.rotation.x = deg_to_rad(float(ax["tilt"]["h"]))
	main.pan_vel = deg_to_rad(float(ax["pan"]["hv"]))
	main.tilt_vel = deg_to_rad(float(ax["tilt"]["hv"]))


func reset() -> void:
	for k in ax:
		ax[k]["set"] = false


func current() -> float:
	"""both servos together now (A, mean of the last frame)"""
	return _i_avg if active() else 0.0


func rail_drop() -> float:
	"""how much the 5 V rail sags from the servo current (V) - simint.v5"""
	return R_SRC * current()


func rate() -> Vector2:
	"""head angular velocity (°/s): pan (positive = to the right like MoveEye's pan), tilt (positive = up)"""
	return Vector2(-rad_to_deg(float(main.pan_vel)), rad_to_deg(float(main.tilt_vel)))


# ---- MoveEye, controls, tests ------------------------------------------------------------------------------------------
func reply() -> Dictionary:
	"""added to world_reply servo_sim (simint.reply): current of the servos, head speed"""
	var r := rate()
	return {"i_a": snappedf(current(), 0.01), "i_peak": snappedf(_i_peak if active() else 0.0, 0.01), "head_dps": [snappedf(r.x, 0.1), snappedf(r.y, 0.1)],
			"weak_sig": signal_weak() and active()}


func add_controls() -> void:
	var m = main
	m.add_control("slider", "srv_mass", "Kopfgewicht für die Servos (Kamera, Halter)", func(): return mass_g,
			func(v): mass_g = clampf(float(v), 80.0, 120.0); save(), "Kamerabild", {"sub": "Wie echt", "min": 80, "max": 120, "step": 5, "unit": "g", "expert": true})
	m.add_control("slider", "srv_play", "Getriebespiel der Servos", func(): return play_deg,
			func(v): play_deg = clampf(float(v), 0.0, 3.0); save(), "Kamerabild", {"sub": "Wie echt", "min": 0, "max": 3, "step": 0.25, "unit": "°", "expert": true})
	m.add_control("toggle", "stoer_sig", "Schwaches Servosignal (lange Leitung: der Kopf zittert)", func(): return weak_signal,
			func(v): weak_signal = bool(v); save(), "Testlauf", {"sub": "Störungen"})


func info() -> Dictionary:
	var out := {"active": active(), "mass_g": mass_g, "load_g": load_g(), "play_deg": play_deg, "weak_signal": weak_signal,
			"signal_weak": signal_weak(), "v": snappedf(_v, 0.01), "speed_dps": snappedf(speed_dps(), 1.0), "i_a": snappedf(current(), 0.001),
			"i_peak": snappedf(_i_peak, 0.001), "rate_dps": [snappedf(rate().x, 0.1), snappedf(rate().y, 0.1)]}
	for k in ax:
		var s: Dictionary = ax[k]
		out[k] = {"cmd": snappedf(float(s.get("cmd", 0.0)), 0.01), "head": snappedf(float(s.get("h", 0.0)), 0.01),
				"gear": snappedf(float(s.get("m", 0.0)), 0.01), "hv": snappedf(float(s.get("hv", 0.0)), 0.1), "i": snappedf(float(s.get("i", 0.0)), 0.001)}
	return out


static func simulate(deg: float, secs := 0.6, mass := 100.0, play := 1.5, v := 5.0, dt := 1.0 / 60.0) -> Dictionary:
	"""offline step response (tests, REAL_SERVO.md): one axis from 0 to deg - time to 90 %, overshoot, settling (±0.5°), current peak"""
	var s := _fresh(0.0)
	s["cmd"] = deg
	s["tgt"] = deg
	var tau := TAU0 + TAU_G * mass
	var wn := TAU * F_HORN * sqrt(100.0 / mass)
	var wmax := W_NOLOAD * v / V_REF
	var t := 0.0
	var t90 := -1.0
	var over := 0.0
	var settle := 0.0
	var ipk := 0.0
	var trace := []
	var step_n := 0
	while t < secs:
		var e: float = deg - float(s["h"])
		var u := clampf(e / BAND, -1.0, 1.0) if absf(e) > DEAD else 0.0
		var wf: float = float(s["w"]) / wmax
		var fr := FRIC * signf(wf) if absf(wf) > 0.002 else 0.0
		var acc := (u - wf - fr) / tau if u != 0.0 else (-wf / 0.004)
		s["w"] = float(s["w"]) + acc * wmax * DT
		var i := I_STALL * v / V_REF * absf(u - wf) if u != 0.0 else 0.0
		s["m"] = float(s["m"]) + float(s["w"]) * DT
		var g: float = float(s["h"]) - float(s["m"])
		var a := -float(s["hv"]) / TAU_FREE
		if absf(g) > play / 2.0:
			a = -wn * wn * (g - signf(g) * play / 2.0) - 2.0 * ZETA * wn * (float(s["hv"]) - float(s["w"]))
		s["hv"] = float(s["hv"]) + a * DT
		s["h"] = float(s["h"]) + float(s["hv"]) * DT
		t += DT
		step_n += 1
		ipk = maxf(ipk, i)
		if t90 < 0.0 and absf(float(s["h"])) >= absf(deg) * 0.9:
			t90 = t
		over = maxf(over, (float(s["h"]) - deg) * signf(deg))
		if absf(float(s["h"]) - deg) > 0.5:
			settle = t
		if step_n % 10 == 0:
			trace.append([snappedf(t, 0.001), snappedf(float(s["h"]), 0.01), snappedf(i, 0.01)])
	return {"deg": deg, "t90_s": snappedf(t90, 0.001), "overshoot_deg": snappedf(over, 0.01), "settle_s": snappedf(settle, 0.001),
			"i_peak_a": snappedf(ipk, 0.01), "end_deg": snappedf(float(s["h"]), 0.01), "trace": trace}


func control(d: Dictionary) -> Dictionary:
	"""{do: info | set (key, value) | sim (deg, mass, play, v: offline step response)}"""
	match str(d.get("do", "info")):
		"set":
			var k := str(d.get("key", ""))
			if k in SAVE:
				set(k, bool(d.get("value", false)) if k == "weak_signal" else float(d.get("value", 0.0)))
				save()
		"sim":
			return {"ok": true, "sim": simulate(float(d.get("deg", 30.0)), float(d.get("secs", 0.6)), float(d.get("mass", mass_g)),
					float(d.get("play", play_deg)), float(d.get("v", 5.0)))}
	return {"ok": true, "info": info()}
