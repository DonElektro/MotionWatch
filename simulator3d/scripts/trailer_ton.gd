extends RefCounted
## Trailer-Ton (Daniel 31.10.2026, trailer.gd): Musik und Geräusche der beiden Trailer, alles im Code erzeugt (keine Dateien),
## wie die übrige Ton-Synthese (maggie_welt.gd snd_*, maggie_hund.gd _synth, bergtal_erleben_base.gd _synth).
##   Musik: Streicherflächen (pad: ruhig / dunkel / hell – Schleifen, Wellentabelle statt vieler sin()), Puls (pulse, ein Takt
##   als Schleife), schneller Puls (ostinato), Paukenschlag (pauke), tiefer Kino-Schlag (boom), Anstieg (riser), Glasklang
##   (chime), Luftzug beim Schnitt (whoosh).
##   Geräusche: Wind, Bach / Wasserfall, Regen (Schleifen), Donner, Schritte (Schleife), Knurren, Bellen, Heulen, Grunzen,
##   Krähen, Zischen, Knacken, Rascheln, Kuhglocke, Papier, Murmeltier-Pfiff.
## Jeder Klang wird einmal erzeugt und bleibt im Speicher (_cache); alles mono, 22,05 kHz, 16 Bit.
## Schleifen sind nahtlos: Frequenzen auf Vielfache von 1/Länge gerundet (pad) oder Ende in den Anfang überblendet (Rauschen).

const SR := 22050
const TAB_N := 2048

static var _cache := {}
static var _tabs := {}


static func get_snd(kind: String) -> AudioStreamWAV:
	if _cache.has(kind):
		return _cache[kind]
	var w: AudioStreamWAV = null
	match kind:
		"pad_ruhig":
			w = _pad([110.0, 164.81, 246.94, 261.63, 329.63], 8.0, 0.9)        # A-Moll mit None (A2 E3 H3 C4 E4)
		"pad_dunkel":
			w = _pad([55.0, 73.42, 110.0, 146.83, 174.61, 220.0], 8.0, 0.55)    # tief, D-Moll über A (dunkel, nicht schrill)
		"pad_hell":
			w = _pad([87.31, 130.81, 174.61, 220.0, 261.63, 392.0], 8.0, 1.2)   # F-Dur mit None (Staunen, Kristall)
		"pulse":
			w = _pulse(96.0, false)
		"ostinato":
			w = _pulse(120.0, true)
		"pauke":
			w = _pauke()
		"boom":
			w = _boom()
		"riser":
			w = _riser(4.0)
		"chime":
			w = _chime()
		"whoosh":
			w = _whoosh()
		"wind":
			w = _noise_loop(6.0, 0.035, 0.6, 0.18, 1)
		"wasser":
			w = _noise_loop(5.0, 0.28, 0.5, 0.05, 2)
		"regen":
			w = _noise_loop(5.0, 0.5, 0.45, 0.02, 3)
		"donner":
			w = _donner()
		"schritte":
			w = _schritte(0.56)
		"rennen":
			w = _schritte(0.32)
		"knurren":
			w = _voice(1.6, 105.0, 92.0, "growl")
		"bellen":
			w = _voice(0.7, 700.0, 520.0, "bark")
		"heulen":
			w = _voice(3.2, 380.0, 520.0, "howl")
		"grunzen":
			w = _voice(1.0, 120.0, 90.0, "grunt")
		"kraehen":
			w = _voice(1.4, 900.0, 700.0, "caw")
		"zischen":
			w = _hiss()
		"knacken":
			w = _knack()
		"rascheln":
			w = _rascheln()
		"kuhglocke":
			w = _glocke()
		"papier":
			w = _papier()
		"pfiff":
			w = _voice(0.5, 2600.0, 2300.0, "whistle")
	if w != null:
		_cache[kind] = w
	return w


static func vorbereiten(kinds: Array) -> void:
	"""all the sounds of a trailer once at the start (a moment of black instead of a stutter later)"""
	for k in kinds:
		get_snd(str(k))


# ---- helpers -------------------------------------------------------------------------------------------------------------
static func _wav(d: PackedFloat32Array, loop := false, gain := 1.0) -> AudioStreamWAV:
	var b := PackedByteArray()
	b.resize(d.size() * 2)
	for i in range(d.size()):
		b.encode_s16(i * 2, int(clampf(d[i] * gain, -1.0, 1.0) * 30000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = SR
	w.stereo = false
	w.data = b
	if loop:
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_begin = 0
		w.loop_end = d.size()
	return w


static func _tab(kind: String) -> PackedFloat32Array:
	"""one cycle of a wave (strings: soft saw with few partials; pluck: brighter)"""
	if _tabs.has(kind):
		return _tabs[kind]
	var t := PackedFloat32Array()
	t.resize(TAB_N)
	var parts: Array = [[1, 1.0], [2, 0.42], [3, 0.24], [4, 0.13], [5, 0.08], [6, 0.05]] if kind == "str" \
			else [[1, 1.0], [2, 0.6], [3, 0.4], [4, 0.28], [5, 0.2], [6, 0.14], [7, 0.1], [8, 0.07]]
	var mx := 0.0
	for i in range(TAB_N):
		var ph := TAU * float(i) / TAB_N
		var v := 0.0
		for p in parts:
			v += sin(ph * float(p[0])) * float(p[1])
		t[i] = v
		mx = maxf(mx, absf(v))
	for i in range(TAB_N):
		t[i] /= mx
	_tabs[kind] = t
	return t


static func _rng(sd: int) -> RandomNumberGenerator:
	var r := RandomNumberGenerator.new()
	r.seed = sd
	return r


# ---- music -----------------------------------------------------------------------------------------------------------------
static func _pad(notes: Array, secs: float, bright: float) -> AudioStreamWAV:
	"""a calm string pad: every note twice, slightly detuned, slow swell - a seamless loop of «secs» seconds"""
	var n := int(SR * secs)
	var d := PackedFloat32Array()
	d.resize(n)
	var tab := _tab("str")
	var voices := []
	for f in notes:
		for det in [-0.0018, 0.0021]:
			var fq: float = round(float(f) * (1.0 + det) * secs) / secs       # whole cycles in the loop
			voices.append([fq * TAB_N / SR, randf() * TAB_N, 1.0 / sqrt(float(f) / 110.0) * (0.75 + 0.25 * bright)])
	var lp := 0.0
	var a := 0.12 + 0.25 * bright
	for i in range(n):
		var v := 0.0
		for vc in voices:
			var ph: float = fmod(float(vc[1]) + float(vc[0]) * i, TAB_N)
			v += tab[int(ph)] * float(vc[2])
		lp += (v - lp) * a                                                  # soft, a bit dark
		var sw := 0.82 + 0.18 * sin(TAU * float(i) / n * 2.0)                # two swells per loop
		d[i] = lp * sw
	return _wav(d, true, 0.5 / sqrt(float(voices.size())))


static func _pulse(bpm: float, fast: bool) -> AudioStreamWAV:
	"""one bar (4 beats): a low thump on every beat, muted string notes (8ths, or 16ths for «ostinato»)"""
	var beat := 60.0 / bpm
	var n := int(SR * beat * 4.0)
	var d := PackedFloat32Array()
	d.resize(n)
	var tab := _tab("pl")
	var steps := 16 if fast else 8
	var seq := [110.0, 110.0, 164.81, 110.0, 130.81, 110.0, 164.81, 146.83] if not fast \
			else [110.0, 164.81, 220.0, 164.81, 110.0, 164.81, 220.0, 246.94, 110.0, 164.81, 220.0, 164.81, 98.0, 146.83, 196.0, 146.83]
	var stl := beat * 4.0 / steps
	for k in range(steps):
		var i0 := int(k * stl * SR)
		var ln := int(stl * SR * 0.9)
		var f: float = seq[k % seq.size()]
		var ph := 0.0
		var lp := 0.0
		for i in range(ln):
			if i0 + i >= n:
				break
			var t := float(i) / SR
			ph = fmod(ph + f * TAB_N / SR, TAB_N)
			var v := tab[int(ph)] * exp(-t * (18.0 if fast else 11.0)) * minf(1.0, t * 300.0)
			lp += (v - lp) * 0.35
			d[i0 + i] += lp * (0.26 if fast else 0.22)
	for b in range(4):                                                   # the thump
		var i0 := int(b * beat * SR)
		var ph2 := 0.0
		for i in range(int(0.35 * SR)):
			if i0 + i >= n:
				break
			var t := float(i) / SR
			ph2 += TAU * (62.0 - 20.0 * minf(1.0, t * 6.0)) / SR
			d[i0 + i] += sin(ph2) * exp(-t * 9.0) * minf(1.0, t * 400.0) * (0.85 if b % 2 == 0 else 0.55)
	return _wav(d, true, 0.8)


static func _pauke() -> AudioStreamWAV:
	"""a big drum (timpani-like): low tone falling a little, a soft mallet noise, long decay"""
	var n := int(SR * 3.0)
	var d := PackedFloat32Array()
	d.resize(n)
	var r := _rng(11)
	var ph := 0.0
	var lp := 0.0
	for i in range(n):
		var t := float(i) / SR
		ph += TAU * (78.0 - 14.0 * minf(1.0, t * 2.0)) / SR
		lp += (r.randf_range(-1.0, 1.0) - lp) * 0.08
		d[i] = (sin(ph) + 0.35 * sin(ph * 1.5) + 0.18 * sin(ph * 2.0)) * exp(-t * 1.6) * minf(1.0, t * 500.0) \
				+ lp * exp(-t * 14.0) * 1.4
	return _wav(d, false, 0.75)


static func _boom() -> AudioStreamWAV:
	"""the deep cinema hit under the title: a low brass-like cluster with a rumble, decaying over 5 s"""
	var n := int(SR * 5.5)
	var d := PackedFloat32Array()
	d.resize(n)
	var tab := _tab("pl")
	var fs := [36.71, 73.42, 110.0, 146.83]
	var phs := [0.0, 0.0, 0.0, 0.0]
	var r := _rng(5)
	var lp := 0.0
	for i in range(n):
		var t := float(i) / SR
		var v := 0.0
		for k in range(fs.size()):
			phs[k] = fmod(float(phs[k]) + float(fs[k]) * (1.0 + 0.002 * k) * TAB_N / SR, TAB_N)
			v += tab[int(phs[k])] * (1.0 if k < 2 else 0.6)
		v = tanh(v * 1.6)
		lp += (r.randf_range(-1.0, 1.0) - lp) * 0.02
		d[i] = (v * 0.6 + lp * 2.0) * exp(-t * 0.85) * minf(1.0, t * 60.0)
	return _wav(d, false, 0.8)


static func _riser(secs: float) -> AudioStreamWAV:
	"""rising noise and tone before the climax (stops sharp - then the silence)"""
	var n := int(SR * secs)
	var d := PackedFloat32Array()
	d.resize(n)
	var r := _rng(3)
	var lp := 0.0
	var ph := 0.0
	for i in range(n):
		var t := float(i) / secs / SR
		lp += (r.randf_range(-1.0, 1.0) - lp) * (0.02 + 0.5 * t * t)
		ph += TAU * (180.0 + 900.0 * t * t) / SR
		d[i] = (lp * 0.9 + sin(ph) * 0.25 + sin(ph * 1.5) * 0.12) * t * t * 1.1
	return _wav(d, false, 0.9)


static func _chime() -> AudioStreamWAV:
	"""the crystal: clear glassy tones, a little shimmering"""
	var n := int(SR * 3.0)
	var d := PackedFloat32Array()
	d.resize(n)
	var fs := [1318.5, 1975.5, 2637.0, 3951.0, 1567.98]
	var am := [0.35, 0.22, 0.12, 0.06, 0.15]
	for i in range(n):
		var t := float(i) / SR
		var v := 0.0
		for k in range(fs.size()):
			var t0 := 0.0 if k < 4 else 0.35
			if t >= t0:
				v += sin(TAU * float(fs[k]) * (t - t0)) * float(am[k]) * exp(-(t - t0) * 1.4) * minf(1.0, (t - t0) * 80.0)
		d[i] = v * (1.0 + 0.15 * sin(TAU * 5.0 * t))
	return _wav(d, false, 0.9)


static func _whoosh() -> AudioStreamWAV:
	var n := int(SR * 1.0)
	var d := PackedFloat32Array()
	d.resize(n)
	var r := _rng(7)
	var lp := 0.0
	for i in range(n):
		var t := float(i) / n
		var e := sin(PI * t) * sin(PI * t)
		lp += (r.randf_range(-1.0, 1.0) - lp) * (0.05 + 0.3 * e)
		d[i] = lp * e * 1.3
	return _wav(d, false, 0.9)


# ---- surroundings ---------------------------------------------------------------------------------------------------------
static func _noise_loop(secs: float, cut: float, gain: float, slow: float, sd: int) -> AudioStreamWAV:
	"""filtered noise as a loop: wind (slow, dark, swelling), water (brighter, bubbling), rain (bright, dense)"""
	var x := 1.0
	var n := int(SR * secs)
	var m := int(SR * x)
	var raw := PackedFloat32Array()
	raw.resize(n + m)
	var r := _rng(20 + sd)
	var lp := 0.0
	var lp2 := 0.0
	for i in range(n + m):
		var t := float(i) / SR
		var c := cut * (1.0 + 0.5 * sin(TAU * t * slow * 2.0) + 0.3 * sin(TAU * t * 0.37))
		lp += (r.randf_range(-1.0, 1.0) - lp) * clampf(c, 0.005, 0.95)
		lp2 += (lp - lp2) * clampf(c * 1.5, 0.005, 0.95)
		var sw := 0.7 + 0.3 * sin(TAU * t / secs * 2.0) if sd == 1 else 1.0
		var bub := (1.0 + 0.6 * sin(TAU * t * (7.0 + 3.0 * sin(t * 1.3)))) if sd == 2 else 1.0
		raw[i] = lp2 * sw * bub * (3.0 if sd == 1 else 1.6)
	var d := PackedFloat32Array()
	d.resize(n)
	for i in range(n):
		d[i] = raw[i]
	for i in range(m):                                                 # what follows the end fades into the start: seamless
		var k := float(i) / m
		d[i] = raw[n + i] * (1.0 - k) + raw[i] * k
	return _wav(d, true, gain)


static func _donner() -> AudioStreamWAV:
	var n := int(SR * 5.0)
	var d := PackedFloat32Array()
	d.resize(n)
	var r := _rng(9)
	var lp := 0.0
	var lp2 := 0.0
	for i in range(n):
		var t := float(i) / SR
		lp += (r.randf_range(-1.0, 1.0) - lp) * 0.03
		lp2 += (lp - lp2) * 0.05
		var e := exp(-t * 0.9) * minf(1.0, t * 30.0) * (1.0 + 0.8 * maxf(0.0, sin(TAU * t * 1.7)) * exp(-t * 0.5))
		var crack := r.randf_range(-1.0, 1.0) * exp(-t * 18.0) * 0.5
		d[i] = lp2 * e * 14.0 + crack
	return _wav(d, false, 0.9)


static func _schritte(step: float) -> AudioStreamWAV:
	"""steps on a gravel path as a loop (two steps)"""
	var n := int(SR * step * 2.0)
	var d := PackedFloat32Array()
	d.resize(n)
	var r := _rng(13)
	for k in range(2):
		var i0 := int(k * step * SR)
		var lp := 0.0
		for i in range(int(0.16 * SR)):
			var t := float(i) / SR
			lp += (r.randf_range(-1.0, 1.0) - lp) * 0.45
			var v := lp * exp(-t * 28.0) * minf(1.0, t * 800.0) + sin(TAU * 90.0 * t) * exp(-t * 40.0) * 0.5
			d[(i0 + i) % n] += v * (1.0 if k == 0 else 0.85)
	return _wav(d, true, 0.8)


static func _voice(secs: float, f0: float, f1: float, kind: String) -> AudioStreamWAV:
	"""animal voices: growl, bark (two barks), howl, grunt, caw (three), whistle (marmot)"""
	var n := int(SR * secs)
	var d := PackedFloat32Array()
	d.resize(n)
	var r := _rng(kind.hash() & 0xffff)
	var ph := 0.0
	var lp := 0.0
	for i in range(n):
		var t := float(i) / SR
		var u := t / secs
		var f := lerpf(f0, f1, u)
		var v := 0.0
		match kind:
			"growl":
				ph += TAU * f * (1.0 + 0.04 * sin(TAU * 9.0 * t)) / SR
				lp += (r.randf_range(-1.0, 1.0) - lp) * 0.25
				v = (sin(ph) + 0.7 * sin(2.0 * ph + 0.3) + 0.45 * sin(3.0 * ph) + lp * 0.9) * (0.55 + 0.45 * sin(TAU * 23.0 * t)) \
						* minf(1.0, t / 0.2) * clampf((secs - t) / 0.3, 0.0, 1.0)
			"bark":
				var tt := fmod(t, 0.32)
				var fb := lerpf(f0, f1, tt / 0.16)
				ph += TAU * fb / SR
				v = (sin(ph) + 0.5 * sin(2.0 * ph) + 0.35 * r.randf_range(-1.0, 1.0)) * minf(1.0, tt / 0.008) * exp(-tt * 14.0) * 1.4 \
						if t < 0.64 else 0.0
			"howl":
				var fh := f0 + (f1 - f0) * sin(PI * minf(1.0, u * 1.3)) - 60.0 * maxf(0.0, u - 0.7)
				ph += TAU * fh * (1.0 + 0.012 * sin(TAU * 5.5 * t)) / SR
				v = (sin(ph) + 0.25 * sin(2.0 * ph) + 0.1 * sin(3.0 * ph)) * sin(PI * u) * 0.9
			"grunt":
				var tg := fmod(t, 0.33)
				ph += TAU * f / SR
				lp += (r.randf_range(-1.0, 1.0) - lp) * 0.3
				v = (sin(ph) * 0.6 + 0.5 * sin(2.0 * ph) + lp * 1.2) * minf(1.0, tg / 0.02) * exp(-tg * 9.0)
			"caw":
				var tc := fmod(t, 0.45)
				var fc := lerpf(f0, f1, tc / 0.3)
				ph += TAU * fc / SR
				lp += (r.randf_range(-1.0, 1.0) - lp) * 0.6
				v = (signf(sin(ph)) * 0.35 + sin(2.0 * ph) * 0.3 + lp * 0.5) * minf(1.0, tc / 0.01) * clampf((0.3 - tc) / 0.08, 0.0, 1.0)
			"whistle":
				ph += TAU * f / SR
				v = sin(ph) * minf(1.0, t / 0.02) * clampf((secs - t) / 0.08, 0.0, 1.0)
		d[i] = v
	return _wav(d, false, 0.55)


static func _hiss() -> AudioStreamWAV:
	var n := int(SR * 1.4)
	var d := PackedFloat32Array()
	d.resize(n)
	var r := _rng(17)
	var lp := 0.0
	for i in range(n):
		var t := float(i) / n
		var x := r.randf_range(-1.0, 1.0)
		lp += (x - lp) * 0.6
		d[i] = (x - lp) * sin(PI * t) * 1.2
	return _wav(d, false, 0.6)


static func _knack() -> AudioStreamWAV:
	"""a twig cracks in the dark (two short clicks)"""
	var n := int(SR * 0.5)
	var d := PackedFloat32Array()
	d.resize(n)
	var r := _rng(19)
	for k in [0.0, 0.07]:
		var i0 := int(k * SR)
		for i in range(int(0.06 * SR)):
			var t := float(i) / SR
			d[i0 + i] += r.randf_range(-1.0, 1.0) * exp(-t * 90.0) * (1.0 if k == 0.0 else 0.6)
	return _wav(d, false, 0.9)


static func _rascheln() -> AudioStreamWAV:
	var n := int(SR * 1.6)
	var d := PackedFloat32Array()
	d.resize(n)
	var r := _rng(23)
	var lp := 0.0
	for i in range(n):
		var t := float(i) / SR
		lp += (r.randf_range(-1.0, 1.0) - lp) * 0.4
		var e := maxf(0.0, sin(TAU * t * 2.3) * sin(TAU * t * 0.9))
		d[i] = lp * e * sin(PI * t / 1.6) * 1.6
	return _wav(d, false, 0.6)


static func _glocke() -> AudioStreamWAV:
	"""a cow bell (two strokes, inharmonic partials)"""
	var n := int(SR * 2.2)
	var d := PackedFloat32Array()
	d.resize(n)
	for k in [0.0, 0.55]:
		var i0 := int(k * SR)
		for i in range(n - i0):
			var t := float(i) / SR
			var ph := TAU * 640.0 * t
			d[i0 + i] += (sin(ph) + 0.6 * sin(2.76 * ph) + 0.35 * sin(5.4 * ph)) * exp(-t * 3.5) * minf(1.0, t * 600.0) * 0.4
	return _wav(d, false, 0.7)


static func _papier() -> AudioStreamWAV:
	"""an old letter is unfolded"""
	var n := int(SR * 1.2)
	var d := PackedFloat32Array()
	d.resize(n)
	var r := _rng(29)
	for i in range(n):
		var t := float(i) / SR
		var e := maxf(0.0, sin(TAU * t * 3.1)) * (1.0 if r.randf() < 0.3 else 0.3)
		d[i] = r.randf_range(-1.0, 1.0) * e * sin(PI * t / 1.2) * 0.7
	return _wav(d, false, 0.6)
