extends RefCounted
## Erzeugte Klänge der Umgebungsgeräusche (mikrofon.gd, am PC hören): kurze Schleifen, alle etwa gleich laut (RMS −20 dBFS),
## die Lautstärke setzt mikrofon.gd nach dem Pegel am Mikrofon. Läuft im Hintergrund (WorkerThreadPool), eigener Zufall.
## Grillen zirpen nach der Temperatur (Dolbear: Zirper pro Minute ≈ 7 × °C − 30).

const LOOP := {"wind": 6.0, "rain": 3.0, "water": 4.0, "frogs": 4.0, "crickets": 4.0, "birds": 6.0, "owl": 4.2, "dog": 0.6,
		"cows": 5.0, "road": 8.0, "voices": 5.0}


static func make(kind: String, rate: int, temp_c: float) -> AudioStreamWAV:
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	var secs: float = LOOP.get(kind, 4.0)
	var n := int(secs * rate)
	var x := PackedFloat32Array()
	x.resize(n)
	var dt := 1.0 / rate
	match kind:
		"wind":
			var lp := 0.0
			var lp2 := 0.0
			var a := _a(260.0, rate)
			for i in range(n):
				lp += a * (rng.randf() * 2.0 - 1.0 - lp)
				lp2 += a * (lp - lp2)
				var t := i * dt
				var g := 0.55 + 0.3 * sin(TAU * t / secs) + 0.15 * sin(TAU * 3.0 * t / secs + 1.3)
				x[i] = lp2 * g
		"rain":
			var lp := 0.0
			var a := _a(1800.0, rate)
			var drop := 0.0
			for i in range(n):
				var w := rng.randf() * 2.0 - 1.0
				lp += a * (w - lp)
				if rng.randf() < 0.0025:
					drop = rng.randf_range(0.5, 1.0)
				drop *= 0.985
				x[i] = (w - lp) * 0.6 + drop * (rng.randf() * 2.0 - 1.0)
		"water":
			var lp := 0.0
			var hp := 0.0
			var a1 := _a(1100.0, rate)
			var a2 := _a(180.0, rate)
			for i in range(n):
				var w := rng.randf() * 2.0 - 1.0
				lp += a1 * (w - lp)
				hp += a2 * (lp - hp)
				x[i] = (lp - hp) * 0.8
			for b in range(int(secs * 14)):                    # Blubbern: kurze Töne, die nach oben gleiten
				_sweep(x, rate, rng.randf() * secs, 0.03, rng.randf_range(350, 600), rng.randf_range(700, 1200), rng.randf_range(0.2, 0.5))
		"frogs":
			for c in range(int(secs * 2.5)):
				var t0 := rng.randf() * secs
				var f := rng.randf_range(220.0, 320.0)
				for p in range(rng.randi_range(3, 6)):
					_buzz(x, rate, t0 + p * 0.07, 0.045, f, 0.5)
		"crickets":
			var per_s := clampf((7.0 * temp_c - 30.0) / 60.0, 0.6, 3.5)
			for c in range(3):
				var f := rng.randf_range(4300.0, 4900.0)
				var t := rng.randf() * 0.5
				while t < secs - 0.1:
					for p in range(3):
						_tone(x, rate, t + p * 0.024, 0.012, f, 0.35)
					t += 1.0 / per_s * rng.randf_range(0.9, 1.1)
		"birds":
			var t := 0.1
			while t < secs - 0.6:
				var f0 := rng.randf_range(2200.0, 4800.0)
				for k in range(rng.randi_range(3, 8)):
					var dur := rng.randf_range(0.04, 0.12)
					_sweep(x, rate, t, dur, f0, f0 * rng.randf_range(0.75, 1.35), 0.4)
					t += dur + rng.randf_range(0.02, 0.06)
				t += rng.randf_range(0.4, 1.4)
		"owl":                                                 # Waldkauz: huu … hu, hu-huuuu
			_hoot(x, rate, 0.1, 0.9, 400.0)
			_hoot(x, rate, 2.0, 0.18, 380.0)
			_hoot(x, rate, 2.5, 0.18, 380.0)
			_hoot(x, rate, 2.85, 1.0, 395.0)
		"dog":
			var nb := int(0.22 * rate)
			var lp := 0.0
			var a := _a(1500.0, rate)
			for i in range(nb):
				var t := i * dt
				var env := minf(1.0, t / 0.008) * exp(-t / 0.07)
				var f := 520.0 - 300.0 * t
				lp += a * (rng.randf() * 2.0 - 1.0 - lp)
				x[i] = env * (0.55 * sin(TAU * f * t) + 0.3 * sin(TAU * 2.0 * f * t) + 0.8 * lp)
		"cows":
			for c in range(int(secs * 1.4)):
				var t0 := rng.randf() * (secs - 0.7)
				for pf in [[720.0, 1.0], [1185.0, 0.6], [1690.0, 0.4], [2510.0, 0.25]]:
					_ring(x, rate, t0, 0.7, float(pf[0]) * rng.randf_range(0.98, 1.02), float(pf[1]) * 0.25)
		"road":
			var lp := 0.0
			var lp2 := 0.0
			var a := _a(140.0, rate)
			for i in range(n):
				lp += a * (rng.randf() * 2.0 - 1.0 - lp)
				lp2 += a * (lp - lp2)
				var t := i * dt
				x[i] = lp2 * (0.6 + 0.4 * sin(TAU * t / secs) * sin(TAU * 2.0 * t / secs + 0.4))
		"voices":
			var t := 0.0
			var lp := 0.0
			var a := _a(900.0, rate)
			var ph := 0.0
			while t < secs - 0.3:
				var syl := rng.randi_range(4, 12)
				var f0 := rng.randf_range(110.0, 230.0)
				for s in range(syl):
					var dur := rng.randf_range(0.12, 0.25)
					var i0 := int(t * rate)
					var i1 := mini(n, int((t + dur) * rate))
					for i in range(i0, i1):
						var u := float(i - i0) / float(maxi(1, i1 - i0))
						ph += TAU * f0 * (1.0 + 0.08 * sin(u * PI)) * dt
						var pulse := pow(maxf(0.0, sin(ph)), 8.0)
						lp += a * (pulse + 0.15 * (rng.randf() - 0.5) - lp)
						x[i] += lp * sin(u * PI) * 3.0
					t += dur
				t += rng.randf_range(0.2, 0.7)
	if kind in ["wind", "rain", "water", "road"]:
		_crossfade(x, int(0.15 * rate))
	return _wav(x, rate, kind != "owl")


static func _a(fc: float, rate: int) -> float:
	return 1.0 - exp(-TAU * fc / rate)


static func _tone(x: PackedFloat32Array, rate: int, t0: float, dur: float, f: float, amp: float) -> void:
	var i0 := int(t0 * rate)
	var nn := int(dur * rate)
	for i in range(nn):
		if i0 + i >= x.size():
			return
		var u := float(i) / nn
		x[i0 + i] += amp * sin(PI * u) * sin(TAU * f * i / rate)


static func _sweep(x: PackedFloat32Array, rate: int, t0: float, dur: float, f0: float, f1: float, amp: float) -> void:
	var i0 := int(t0 * rate)
	var nn := int(dur * rate)
	var ph := 0.0
	for i in range(nn):
		if i0 + i >= x.size():
			return
		var u := float(i) / nn
		ph += TAU * lerpf(f0, f1, u) / rate
		x[i0 + i] += amp * sin(PI * u) * sin(ph)


static func _buzz(x: PackedFloat32Array, rate: int, t0: float, dur: float, f: float, amp: float) -> void:
	var i0 := int(t0 * rate)
	var nn := int(dur * rate)
	for i in range(nn):
		if i0 + i >= x.size():
			return
		var u := float(i) / nn
		x[i0 + i] += amp * sin(PI * u) * signf(sin(TAU * f * i / rate)) * 0.6


static func _ring(x: PackedFloat32Array, rate: int, t0: float, dur: float, f: float, amp: float) -> void:
	var i0 := int(t0 * rate)
	var nn := int(dur * rate)
	for i in range(nn):
		if i0 + i >= x.size():
			return
		var tt := float(i) / rate
		x[i0 + i] += amp * minf(1.0, tt / 0.003) * exp(-tt / 0.18) * sin(TAU * f * tt)


static func _hoot(x: PackedFloat32Array, rate: int, t0: float, dur: float, f: float) -> void:
	var i0 := int(t0 * rate)
	var nn := int(dur * rate)
	var ph := 0.0
	for i in range(nn):
		if i0 + i >= x.size():
			return
		var u := float(i) / nn
		var tt := float(i) / rate
		ph += TAU * f * (1.0 + 0.02 * sin(TAU * 6.0 * tt)) / rate
		x[i0 + i] += 0.6 * pow(sin(PI * u), 0.6) * sin(ph)


static func _crossfade(x: PackedFloat32Array, m: int) -> void:
	"""das Ende weich in den Anfang: die Schleife knackt nicht"""
	var n := x.size()
	if m * 2 >= n:
		return
	for i in range(m):
		var u := float(i) / m
		x[i] = x[i] * u + x[n - m + i] * (1.0 - u)
	x.resize(n - m)


static func _wav(x: PackedFloat32Array, rate: int, loop: bool) -> AudioStreamWAV:
	var s := 0.0
	for v in x:
		s += v * v
	var rms := sqrt(s / maxf(1.0, x.size()))
	var k := 0.1 / maxf(rms, 1e-6)                        # RMS −20 dBFS
	var pcm := PackedByteArray()
	pcm.resize(x.size() * 2)
	for i in range(x.size()):
		pcm.encode_s16(i * 2, int(clampf(x[i] * k, -1.0, 1.0) * 32000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = rate
	w.data = pcm
	if loop:
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_begin = 0
		w.loop_end = x.size()
	return w
