class_name RoboterKiLernen
extends RefCounted
## Gang-KI Stufe 3 «Lernen» (Besitzer 28.11.2026 14:36, Schnittstelle in gang_ki_schnittstelle.md): der Roboter merkt sich pro
## Hindernis (Art + gerundete Masse), welche Strategie mit welchen Werten am besten ging, und nimmt sie beim nächsten gleichen
## oder ähnlichen Hindernis gleich wieder (ähnliche Masse: die nächsten Erfahrungen, gewichtet gemischt).
##   Suche: klein und ohne Netz. Zwischen den Strategien ein «Bandit» (UCB: zuerst jede passende einmal, dann die mit dem besten
##   Schnitt plus einem Neugier-Zuschlag), in einer Strategie eine Kreuzentropie-Suche über die Zahlen (Mittel und Streuung aus
##   den besten 30 % der Versuche, die Streuung wird nie ganz null). Nach dem ersten Erfolg meist das Beste mit kleiner
##   Abweichung («weiter leicht verbessern»), selten noch eine andere Strategie; nach VERSUCHE_LERNEN nur noch das Beste.
##   Bewertung: Erfolg >> Zeit, Energie, Kipp-Reserve. Jeder Erfolg zählt mehr als jeder Fehlschlag (1 … 1.9 gegen −1.5 … −0.5);
##   die Gewichte von Zeit / Energie / Kipp-Reserve kommen vom Stil (schnell / sparsam / sicher). Gespeichert werden die rohen
##   Messwerte, so gilt ein neuer Stil sofort auch für alte Versuche.
##   Grenze: VERSUCHE_MAX Versuche ohne einen Erfolg → «umgehen» und ein Hinweis; «Vergessen» löscht alles der Variante.
## Ablauf im Hintergrund (tick, jedes Physik-Bild, Schalter «an» ab Werk an): sieht die KI (Stufe 1, roboter_ki_gang.gd) ein
## Hindernis näher als NAH, wählt waehle() Strategie + Werte, die KI führt sie aus (Stufe 2); fertig → melde(). Fehlschlag (Sturz,
## kein Fortschritt nach STILL s, länger als ZEIT_MAX) → abbrechen, vor dem Hindernis neu aufstellen, nächster Versuch.
## Speicher: user://roboter_ki_<variante>.json (8 / 6 / 4 Segmente getrennt).

const T = preload("res://scripts/i18n.gd")
const FORMAT := 1
const VERSUCHE_MAX := 12          # tries without any success, then «umgehen» + hint
const VERSUCHE_LERNEN := 30       # after that only the best (with a small variation)
const NAH := 0.6                  # m: an obstacle this close starts a try (the KI sets the robot up 0.5 m before it)
const STILL := 20.0               # s without 3 cm progress = stuck (the KI has its own 12 s; this is the safety net)
const ZEIT_MAX := 100.0           # s per try (the KI stops at 90 s)
const RUHE := 1.0                 # s after «neu aufstellen» before the next try
const ZEIT_REF := 20.0            # s: score of the time 1 / (1 + zeit / ZEIT_REF)
const E_REF := 0.3                # Wh: score of the energy 1 / (1 + energie / E_REF)
const ELITE := 0.3
const HALTON := [2, 3, 5, 7, 11, 13, 17, 19]
const MIN_PROBEN := 5             # after the first success: every fitting strategy at least this often (a bad first draw is no verdict)
const STILE := ["schnell", "sparsam", "sicher"]
const GEWICHTE := {"schnell": {"zeit": 0.6, "energie": 0.2, "kipp": 0.2},
		"sparsam": {"zeit": 0.2, "energie": 0.6, "kipp": 0.2},
		"sicher": {"zeit": 0.15, "energie": 0.15, "kipp": 0.7}}
# rounding of the key and scale of the similarity (m / m / m / ° / steps); like sehen() of the KI: breite = in walking
# direction (span of a ditch, diameter of a pipe), tiefe = downwards
const RASTER := {"hoehe": 0.02, "breite": 0.05, "tiefe": 0.05, "neigung": 5.0, "stufen": 1.0}
const SKALA := {"hoehe": 0.04, "breite": 0.1, "tiefe": 0.1, "neigung": 8.0, "stufen": 1.0}
const EINRASTEN := 0.4            # a measurement this close to a known obstacle counts as the same one (sehen() is ± 1.5 cm)
const AEHNLICH := 3.0             # distance (in SKALA units) up to which an experience counts as «ähnlich»
# the numbers B varies: [lowest, highest, start] (if the KI brings its own PARAM_RAUM, that one wins)
const PARAM_RAUM := {"schritt_hoehe": [0.1, 1.0, 0.35], "koerper_hoehe": [0.5, 1.4, 0.9], "neigung": [-30.0, 30.0, 0.0],
		"tempo": [0.3, 1.0, 0.7], "segment_hub": [0.0, 1.0, 0.3], "anlauf": [0.0, 0.5, 0.1]}
# which strategies fit which obstacle (order = what is tried first); «umgehen» is the way out, not learned
const PASSEND := {"stufe": ["normal", "hoch_steigen", "aufrichten_vorne"], "treppe": ["hoch_steigen", "normal", "aufrichten_vorne"],
		"graben": ["bruecke", "normal", "hoch_steigen"], "luecke": ["bruecke", "normal"],
		"geroell": ["normal", "hoch_steigen", "einrollen_rollen"], "rampe": ["normal", "einrollen_rollen", "hoch_steigen"],
		"rohr": ["kriechen_drunter", "hoch_steigen", "normal"], "balken": ["hoch_steigen", "kriechen_drunter", "normal"]}
var variante := "8"
var stil := "sicher"
var an := true                    # «Lernen im Hintergrund» (ab Werk an)
var daten := {}                   # key -> entry (see _eintrag)
var rng := RandomNumberGenerator.new()
var pfad := ""                    # "" = user://roboter_ki_<variante>.json; tests set their own
var speichern_an := true
# background run
var ki = null                     # roboter_ki_gang.gd (Stufe 1 + 2)
var labor = null                  # roboter_labor.gd (fallback for «neu aufstellen»)
var lauf := {}                    # the running try: {phase, h, strategie, param, t, best_d, last_t, aufstell}
var vorbei := []                  # positions of obstacles already passed (no new try there)
var letzte := {}                  # the last finished try for the field: {key, strategie, erfolg, score, grund}
var meldungen := 0                # finished tries since the start (for the field and tests)
var _seh_t := 0.0
var _geladen := false             # the store of the lab's variant is read at the first tick


func _init(v := "8") -> void:
	variante = str(v)
	rng.randomize()


# ---- Speicher ------------------------------------------------------------------------------------------------------------
func datei() -> String:
	return pfad if pfad != "" else "user://roboter_ki_%s.json" % variante


func laden(v = null) -> void:
	_geladen = true
	if v != null:
		variante = str(v)
	daten = {}
	lauf = {}
	vorbei = []
	letzte = {}
	var p := datei()
	if not FileAccess.file_exists(p):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(p))
	if typeof(d) == TYPE_DICTIONARY and int(d.get("format", 0)) == FORMAT and typeof(d.get("hindernisse")) == TYPE_DICTIONARY:
		daten = d["hindernisse"]
		if str(d.get("stil", "")) in STILE:
			stil = str(d["stil"])


func speichern() -> void:
	if not speichern_an:
		return
	var f := FileAccess.open(datei(), FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"format": FORMAT, "variante": variante, "stil": stil, "hindernisse": daten}))


func vergessen() -> void:
	"""Knopf «Vergessen»: alles Gelernte dieser Variante weg (auch die Datei)"""
	if not lauf.is_empty() and ki != null and ki.has_method("abbrechen"):
		ki.abbrechen()
	daten = {}
	lauf = {}
	vorbei = []
	letzte = {}
	var p := datei()
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(p))


func setze_stil(s: String) -> void:
	if s in STILE and s != stil:
		stil = s
		for k in daten:
			_neu_bester(daten[k])
		speichern()


# ---- Schlüssel und Ähnlichkeit -------------------------------------------------------------------------------------------
static func masse(h: Dictionary) -> Dictionary:
	var m := {}
	for k in RASTER:
		var r: float = RASTER[k]
		m[k] = snappedf(float(h.get(k, 0.0)), r)
	return m


static func schluessel(h: Dictionary) -> String:
	var m := masse(h)
	return "%s|h%d|b%d|t%d|n%d|s%d" % [str(h.get("art", "?")), roundi(m["hoehe"] * 100.0), roundi(m["breite"] * 100.0),
			roundi(m["tiefe"] * 100.0), roundi(m["neigung"]), roundi(m["stufen"])]


static func abstand(a: Dictionary, b: Dictionary) -> float:
	var s := 0.0
	for k in SKALA:
		var d: float = (float(a.get(k, 0.0)) - float(b.get(k, 0.0))) / float(SKALA[k])
		s += d * d
	return sqrt(s)


func raum() -> Dictionary:
	if ki != null and ki.get_script() != null:
		var cm: Dictionary = ki.get_script().get_script_constant_map()
		var pr = cm.get("PARAM_RAUM", cm.get("PARAM"))   # A calls it PARAM: {name: [lo, hi, default]}
		if typeof(pr) == TYPE_DICTIONARY and not (pr as Dictionary).is_empty():
			return pr
	return PARAM_RAUM


func strategien_fuer(art: String) -> Array:
	var alle: Array = PASSEND.get(art, ["normal", "hoch_steigen"])
	if ki != null and ki.get_script() != null:
		var cm: Dictionary = ki.get_script().get_script_constant_map()
		if typeof(cm.get("STRATEGIEN")) == TYPE_ARRAY:
			alle = alle.filter(func(s): return s in cm["STRATEGIEN"])
	return alle


func key(h: Dictionary) -> String:
	"""the key of the obstacle; a slightly different measurement of a known one snaps to it (no split of the experience)"""
	var k := schluessel(h)
	if daten.has(k):
		return k
	var m := masse(h)
	var best := k
	var bd := EINRASTEN
	for kk in daten:
		var e: Dictionary = daten[kk]
		if str(e.get("art")) == str(h.get("art", "?")):
			var d := abstand(m, e["masse"])
			if d <= bd:
				bd = d
				best = kk
	return best


func _eintrag(h: Dictionary) -> Dictionary:
	var k := key(h)
	if not daten.has(k):
		daten[k] = {"art": str(h.get("art", "?")), "masse": masse(h), "versuche": 0, "erfolge": 0, "aufgegeben": false,
				"strategien": {}, "best": {}, "start": _von_nachbarn(h)}
	return daten[k]


func nachbarn(h: Dictionary, n := 2) -> Array:
	"""the nearest learned obstacles of the same art with a success: [[distance, entry], …] (nearest first)"""
	var art := str(h.get("art", "?"))
	var m := masse(h)
	var own := key(h)
	var l := []
	for k in daten:
		var e: Dictionary = daten[k]
		if k == own or str(e.get("art")) != art or (e.get("best", {}) as Dictionary).is_empty():
			continue
		var d := abstand(m, e["masse"])
		if d <= AEHNLICH:
			l.append([d, e])
	l.sort_custom(func(a, b): return a[0] < b[0])
	return l.slice(0, n)


func _von_nachbarn(h: Dictionary) -> Dictionary:
	"""a start for a new obstacle from similar ones: the strategy of the nearest, its numbers mixed with the second
	nearest of the same strategy (weighted 1 / distance) - so a 9 cm step lies between what worked at 6 and at 12 cm"""
	var nb := nachbarn(h, 3)
	if nb.is_empty():
		return {}
	var b0: Dictionary = nb[0][1]["best"]
	var s: String = b0["strategie"]
	var sum := {}
	var wsum := 0.0
	for x in nb:
		var b: Dictionary = x[1]["best"]
		if str(b["strategie"]) != s:
			continue
		var w := 1.0 / maxf(0.05, float(x[0]))
		wsum += w
		for p in b["param"]:
			sum[p] = float(sum.get(p, 0.0)) + w * float(b["param"][p])
	var par := {}
	for p in sum:
		par[p] = float(sum[p]) / wsum
	return {"strategie": s, "param": par, "von": nb.size()}


# ---- Bewertung -----------------------------------------------------------------------------------------------------------
func bewerte(st: Dictionary, s := "") -> float:
	"""Erfolg >> Zeit, Energie, Kipp-Reserve: a success scores 1 … 1.9, a failure −1.5 … −0.5 (progress helps a little)"""
	if s == "":
		s = stil
	if not bool(st.get("erfolg", false)):
		var v := -1.0 + 0.5 * clampf(float(st.get("fortschritt", 0.0)), 0.0, 1.0)
		if bool(st.get("gestuerzt", false)):
			v -= 0.5
		return v
	var w: Dictionary = GEWICHTE.get(s, GEWICHTE["sicher"])
	var z := 1.0 / (1.0 + maxf(0.0, float(st.get("zeit", 0.0))) / ZEIT_REF)
	var e := 1.0 / (1.0 + maxf(0.0, float(st.get("energie", 0.0))) / E_REF)
	var k := clampf(float(st.get("kipp_min", 0.0)), 0.0, 1.0)
	return 1.0 + 0.9 * (float(w["zeit"]) * z + float(w["energie"]) * e + float(w["kipp"]) * k)


static func _roh(st: Dictionary) -> Dictionary:
	var r := {}
	for k in ["erfolg", "zeit", "energie", "kipp_min", "gestuerzt", "fortschritt"]:
		if st.has(k):
			r[k] = st[k]
	return r


func _neu_bester(e: Dictionary) -> void:
	var best := {}
	var bs := -1e9
	for s in e["strategien"]:
		for r in e["strategien"][s]["res"]:
			if not bool(r["st"].get("erfolg", false)):
				continue
			var v := bewerte(r["st"])
			if v > bs:
				bs = v
				best = {"strategie": s, "param": (r["p"] as Dictionary).duplicate(), "score": v, "st": r["st"]}
	e["best"] = best


# ---- Wählen --------------------------------------------------------------------------------------------------------------
func waehle(h: Dictionary) -> Array:
	"""[strategie, param]: das beste Gemerkte (leicht verändert) oder ein neuer Versuch"""
	var e := _eintrag(h)
	var best: Dictionary = e["best"]
	if best.is_empty() and bool(e["aufgegeben"]):
		return ["umgehen", {}]
	var n := int(e["versuche"])
	var s := ""
	if not best.is_empty():
		if n >= VERSUCHE_LERNEN or rng.randf() < 0.7:
			return [best["strategie"], _nah(best["param"], 0.04 if n < VERSUCHE_LERNEN else 0.02)]
		s = _ucb(e, str(h.get("art", "")), MIN_PROBEN)
	else:
		var st: Dictionary = e.get("start", {})
		if n == 0 and not st.is_empty():
			return [st["strategie"], (st["param"] as Dictionary).duplicate()]   # gleich das, was beim Ähnlichen ging
		if n == 0 and ki != null and ki.has_method("regel"):
			var rg: Array = ki.regel(h)                   # nothing learnt yet: first what the KI does by itself (Stufe 2)
			if str(rg[0]) != "umgehen":
				return [rg[0], _probe(e, rg[0], h, true)]
		s = _ucb(e, str(h.get("art", "")))
	return [s, _probe(e, s, h)]


func _ucb(e: Dictionary, art: String, mindest := 1) -> String:
	var kand := strategien_fuer(art)
	var stt: Dictionary = e.get("start", {})
	if not stt.is_empty() and not kand.has(stt["strategie"]):
		kand.push_front(stt["strategie"])
	var total := 0
	for s in kand:
		total += (e["strategien"].get(s, {"res": []})["res"] as Array).size()
	var bs := ""
	var bv := -1e9
	var wenig := 1 << 30
	for s in kand:                                        # every fitting strategy «mindest» times first (fewest tries first)
		var nr: int = (e["strategien"].get(s, {"res": []})["res"] as Array).size()
		if nr < mindest and nr < wenig:
			wenig = nr
			bs = s
	if bs != "":
		return bs
	for s in kand:
		var res: Array = e["strategien"].get(s, {"res": []})["res"]
		if res.is_empty():
			return s
		var sc := res.map(func(r): return bewerte(r["st"]))
		sc.sort()
		sc.reverse()
		var top: Array = sc.slice(0, 3)                   # how good it can be (mean of its 3 best), not its average
		var m := 0.0
		for x in top:
			m += float(x)
		m /= top.size()
		var v := m + 0.8 * sqrt(log(float(total) + 1.0) / res.size())
		if v > bv:
			bv = v
			bs = s
	return bs


func _probe(e: Dictionary, s: String, h := {}, nur_start := false) -> Dictionary:
	"""Kreuzentropie: Mittel / Streuung aus den besten Versuchen dieser Strategie, daraus ziehen"""
	var r := raum()
	var res: Array = e["strategien"].get(s, {"res": []})["res"]
	var mu := {}
	var sd := {}
	var st: Dictionary = e.get("start", {})
	for p in r:
		var lo: float = r[p][0]
		var hi: float = r[p][1]
		mu[p] = float(r[p][2]) if (r[p] as Array).size() > 2 else (lo + hi) * 0.5
		if ki != null and ki.has_method("_vorschlag") and not h.is_empty():
			mu[p] = float(ki._vorschlag(s, p, h))          # the KI's own value for this strategy and obstacle
		if str(st.get("strategie", "")) == s and (st["param"] as Dictionary).has(p):
			mu[p] = float(st["param"][p])
		sd[p] = 0.3 * (hi - lo)
	var ok := res.filter(func(x): return bool(x["st"].get("erfolg", false)))
	if ok.is_empty() and not res.is_empty() and str(st.get("strategie", "")) != s:
		# no success with this strategy yet: spread the tries evenly over the whole range (Halton, randomly shifted),
		# a failure says little about where the good numbers are
		var out := {}
		var i := 0
		for p in r:
			var lo: float = r[p][0]
			var hi: float = r[p][1]
			var u := fposmod(_halton(res.size(), HALTON[i % HALTON.size()]) + _versatz(e, s, i), 1.0)
			out[p] = lo + u * (hi - lo)
			i += 1
		return out
	if not ok.is_empty():
		var sorted := ok.duplicate()
		sorted.sort_custom(func(a, b): return bewerte(a["st"]) > bewerte(b["st"]))
		var el: Array = sorted.slice(0, maxi(1, int(ceil(sorted.size() * ELITE))))
		for p in r:
			var lo: float = r[p][0]
			var hi: float = r[p][1]
			var m := 0.0
			for x in el:
				m += float(x["p"].get(p, mu[p]))
			m /= el.size()
			var v := 0.0
			for x in el:
				v += pow(float(x["p"].get(p, mu[p])) - m, 2.0)
			mu[p] = m
			sd[p] = clampf(sqrt(v / el.size()) * 1.3, (0.15 if el.size() < 3 else 0.05) * (hi - lo), 0.3 * (hi - lo))
	if nur_start or (res.is_empty() and ki != null and ki.has_method("_vorschlag") and not h.is_empty()):
		return mu                                         # a strategy's first try: exactly the KI's own values
	var out := {}
	for p in r:
		out[p] = clampf(rng.randfn(float(mu[p]), float(sd[p])), float(r[p][0]), float(r[p][1]))
	return out


static func _halton(i: int, b: int) -> float:
	var f := 1.0
	var x := 0.0
	var k := i + 1
	while k > 0:
		f /= b
		x += f * (k % b)
		k = k / b
	return x


func _versatz(e: Dictionary, s: String, i: int) -> float:
	"""one random shift per obstacle, strategy and number (kept in the entry, so the sequence stays even)"""
	if not e.has("versatz"):
		e["versatz"] = {}
	var k := "%s%d" % [s, i]
	if not e["versatz"].has(k):
		e["versatz"][k] = rng.randf()
	return float(e["versatz"][k])


func _nah(par: Dictionary, anteil: float) -> Dictionary:
	var r := raum()
	var out := {}
	for p in par:
		if r.has(p):
			var lo: float = r[p][0]
			var hi: float = r[p][1]
			out[p] = clampf(float(par[p]) + rng.randfn(0.0, anteil * (hi - lo)), lo, hi)
		else:
			out[p] = par[p]
	return out


# ---- Melden --------------------------------------------------------------------------------------------------------------
func melde(h: Dictionary, strategie: String, param: Dictionary, status: Dictionary) -> void:
	"""ein Versuch ist fertig: merken, Bestes neu bestimmen, speichern"""
	if strategie == "umgehen":
		return
	var e := _eintrag(h)
	e["versuche"] = int(e["versuche"]) + 1
	meldungen += 1
	var st := _roh(status)
	var ok := bool(st.get("erfolg", false))
	if ok:
		e["erfolge"] = int(e["erfolge"]) + 1
	if not e["strategien"].has(strategie):
		e["strategien"][strategie] = {"res": []}
	var res: Array = e["strategien"][strategie]["res"]
	res.append({"p": param.duplicate(), "st": st})
	if res.size() > 40:                                   # keep it small: drop the worst of the oldest half
		var old := res.slice(0, 20)
		old.sort_custom(func(a, b): return bewerte(a["st"]) < bewerte(b["st"]))
		res.erase(old[0])
	_neu_bester(e)
	if int(e["erfolge"]) == 0 and int(e["versuche"]) >= VERSUCHE_MAX:
		e["aufgegeben"] = true
	letzte = {"key": key(h), "strategie": strategie, "erfolg": ok, "score": bewerte(st), "h": h}
	speichern()


func eintrag(h: Dictionary) -> Dictionary:
	return daten.get(key(h), {})


# ---- Ablauf im Hintergrund ----------------------------------------------------------------------------------------------
func tick(dt: float) -> void:
	"""jedes Physik-Bild (aus dem Labor): sehen → wählen → ausführen → melden; Fehlschlag → neu aufstellen → nochmals"""
	if not _geladen:
		_geladen = true
		if labor != null and labor.get("variante") != null:
			laden(str(labor.variante))
	if not an or ki == null:
		if not lauf.is_empty() and ki != null:
			ki.abbrechen()
			lauf = {}
		return
	if lauf.is_empty():
		_seh_t -= dt
		if _seh_t > 0.0:
			return
		_seh_t = 0.5
		if ki.has_method("aktiv") and not ki.aktiv():
			return
		var h := _naechstes()
		if not h.is_empty():
			_versuch(h, true)
		return
	lauf["t"] = float(lauf["t"]) + dt
	match str(lauf["phase"]):
		"ruhe":
			if float(lauf["t"]) >= RUHE:
				_versuch(lauf["h"], false)
		"versuch":
			var st: Dictionary = ki.strategie_status()
			var d := _rest()
			if d < float(lauf["best_d"]) - 0.03:
				lauf["best_d"] = d
				lauf["last_t"] = lauf["t"]
			var grund := ""
			if bool(st.get("gestuerzt", false)):
				grund = "gestürzt"
			elif bool(st.get("fertig", false)):
				grund = "" if bool(st.get("erfolg", false)) else "nicht geschafft"
			elif float(lauf["t"]) - float(lauf["last_t"]) > STILL:
				grund = "kein Fortschritt"
			elif float(lauf["t"]) > ZEIT_MAX:
				grund = "zu langsam"
			else:
				return
			var s := st.duplicate()
			if grund != "":
				s["erfolg"] = false
			if not s.has("zeit"):
				s["zeit"] = lauf["t"]
			if not s.has("fortschritt"):
				s["fortschritt"] = clampf(1.0 - float(lauf["best_d"]) / maxf(0.1, float(lauf["d0"])), 0.0, 1.0)
			var h: Dictionary = lauf["h"]
			melde(h, lauf["strategie"], lauf["param"], s)
			letzte["grund"] = grund
			if grund == "":
				vorbei.append(h.get("pos", Vector3.ZERO))
				lauf = {}
				return
			ki.abbrechen()
			_neu_aufstellen(h)
			lauf = {"phase": "ruhe", "h": h, "t": 0.0, "aufstell": lauf["aufstell"], "d0": lauf["d0"]}


func nochmal() -> bool:
	"""üben: das zuletzt gemeldete Hindernis gleich nochmals - abbrechen, davor neu aufstellen, nächster Versuch"""
	var h: Dictionary = letzte.get("h", {})
	if h.is_empty() or ki == null:
		return false
	ki.abbrechen()
	var a = lauf.get("aufstell", null)
	lauf = {"phase": "ruhe", "h": h, "t": 0.0, "aufstell": a, "d0": float(h.get("abstand", 0.5)) + float(h.get("breite", 0.2)) + 0.3}
	_neu_aufstellen(h)
	return true


func _naechstes() -> Dictionary:
	var sicht: Dictionary = ki.sehen()
	var best := {}
	for h in sicht.get("hindernisse", []):
		if float(h.get("abstand", 99.0)) > NAH:
			continue
		var p = h.get("pos", null)
		var schon := false
		for v in vorbei:
			if p is Vector3 and v is Vector3 and (p as Vector3).distance_to(v) < 0.4:
				schon = true
		if schon:
			continue
		if best.is_empty() or float(h["abstand"]) < float(best["abstand"]):
			best = h
	return best


func _versuch(h: Dictionary, erst: bool) -> void:
	var w := waehle(h)
	var aufstell = lauf.get("aufstell", null)
	if erst:
		aufstell = _jetzt_xf()
	var d0: float = float(lauf.get("d0", 0.0)) if not erst else float(h.get("abstand", 0.5)) + float(h.get("tiefe", 0.2)) + 0.3
	lauf = {"phase": "versuch", "h": h, "strategie": w[0], "param": w[1], "t": 0.0, "last_t": 0.0, "aufstell": aufstell, "d0": d0}
	lauf["best_d"] = _rest()
	if w[0] == "umgehen":
		vorbei.append(h.get("pos", Vector3.ZERO))         # the KI walks around it; no more tries here (hint in the field)
		letzte = {"key": key(h), "strategie": "umgehen", "erfolg": false, "grund": "zu schwer"}
	var pk: Dictionary = (w[1] as Dictionary).duplicate()
	pk["hindernis"] = h                                   # the KI aims at exactly this obstacle
	ki.strategie_ausfuehren(w[0], pk)
	if w[0] == "umgehen":
		lauf = {}


func _rest() -> float:
	"""how far the robot still has to go: from its rear end to behind the obstacle (along the line start → obstacle)"""
	if labor == null or labor.get("model") == null or lauf.get("aufstell") == null:
		return float(lauf.get("d0", 1.0)) * (1.0 - clampf(float(lauf.get("t", 0.0)) / ZEIT_MAX, 0.0, 1.0))
	var a: Transform3D = lauf["aufstell"]
	var m = labor.model
	var hinten: Vector3 = m.segment_xf(m.n() - 1).origin
	var vor := Vector3(a.basis.x.x, 0.0, a.basis.x.z).normalized()
	return float(lauf["d0"]) - (hinten - a.origin).dot(vor)


func _jetzt_xf():
	if labor == null or labor.get("model") == null:
		return null
	var m = labor.model
	var xf: Transform3D = m.segment_xf(0)
	var x := Vector3(xf.basis.x.x, 0.0, xf.basis.x.z).normalized()
	var y0: float = (labor.starts.get("start", Transform3D()) as Transform3D).origin.y if labor.get("starts") != null else 0.0
	return Transform3D(Basis(Vector3.UP, atan2(-x.z, x.x)), Vector3(xf.origin.x, y0, xf.origin.z))


func _neu_aufstellen(h: Dictionary) -> void:
	if ki.has_method("neu_aufstellen"):
		ki.neu_aufstellen(h)
		return
	if labor == null or lauf.get("aufstell") == null:
		return
	labor.bew.stop()
	labor.manual = Vector3.ZERO
	labor.model.root_xf = lauf["aufstell"]
	labor.apply_pose("gerade", true)


# ---- Anzeige (KI-Feld, baut Helfer A) -------------------------------------------------------------------------------------
func text_hindernis(h: Dictionary) -> String:
	var m := masse(h)
	var art := str(h.get("art", "?"))
	var t := art_text(art)
	if art in ["rampe"]:
		return t + " %d°" % roundi(m["neigung"])
	if art in ["graben", "luecke"]:
		return t + " %d cm" % roundi(m["breite"] * 100.0)
	if art == "treppe" and int(m["stufen"]) > 1:
		return t + " %d × %d cm" % [int(m["stufen"]), roundi(m["hoehe"] * 100.0)]
	return t + " %d cm" % roundi(m["hoehe"] * 100.0)


static func grund_text(g: String) -> String:
	match g:
		"gestürzt":
			return T.t("gestürzt")
		"nicht geschafft":
			return T.t("nicht geschafft")
		"kein Fortschritt":
			return T.t("kein Fortschritt")
		"zu langsam":
			return T.t("zu langsam")
		"zu schwer":
			return T.t("zu schwer")
	return g


static func strategie_text(s: String) -> String:
	match s:
		"normal":
			return T.t("Normal gehen")
		"hoch_steigen":
			return T.t("Hoch steigen")
		"aufrichten_vorne":
			return T.t("Vorne aufrichten")
		"bruecke":
			return T.t("Brücke")
		"umgehen":
			return T.t("Umgehen")
		"einrollen_rollen":
			return T.t("Einrollen und rollen")
		"kriechen_drunter":
			return T.t("Drunter durch kriechen")
	return s


static func art_text(a: String) -> String:
	match a:
		"stufe":
			return T.t("Geländestufe")
		"treppe":
			return T.t("Treppe")
		"graben":
			return T.t("Graben")
		"luecke":
			return T.t("Lücke")
		"geroell":
			return T.t("Geröll")
		"rampe":
			return T.t("Rampe")
		"rohr":
			return T.t("Rohr")
		"balken":
			return T.t("Balken")
	return a


func anzeige_zeilen() -> PackedStringArray:
	"""Zeilen fürs KI-Feld: Hindernis, Versuch n / max, gewählte Strategie, bestes Ergebnis, Hinweis"""
	var z := PackedStringArray()
	if not an:
		z.append(T.t("Lernen: aus"))
		return z
	var h: Dictionary = lauf.get("h", {})
	var e := {}
	if not h.is_empty():
		e = eintrag(h)
	elif not letzte.is_empty():
		e = daten.get(letzte["key"], {})
	if e.is_empty():
		z.append(T.t("Lernen: wartet auf ein Hindernis") + " · " + T.t("%d gemerkt") % daten.size())
		return z
	var hh: Dictionary = h if not h.is_empty() else (e["masse"] as Dictionary).merged({"art": e["art"]})
	var n := int(e["versuche"]) + (1 if str(lauf.get("phase", "")) == "versuch" else 0)
	var zeile := text_hindernis(hh) + " · " + T.t("Versuch %d") % n
	if (e["best"] as Dictionary).is_empty():
		zeile += " / %d" % VERSUCHE_MAX
	if not lauf.is_empty() and lauf.has("strategie"):
		zeile += " · " + strategie_text(lauf["strategie"])
	elif str(lauf.get("phase", "")) == "ruhe":
		zeile += " · " + T.t("neu aufstellen")
	z.append(zeile)
	var b: Dictionary = e["best"]
	if b.is_empty():
		z.append(T.t("Bestes: noch kein Erfolg"))
	else:
		var st: Dictionary = b["st"]
		z.append(T.t("Bestes: %s · %.1f s · %.2f Wh · Kipp-Reserve %d %%") % [strategie_text(b["strategie"]),
				float(st.get("zeit", 0.0)), float(st.get("energie", 0.0)), roundi(100.0 * float(st.get("kipp_min", 0.0)))])
	if bool(e["aufgegeben"]) and b.is_empty():
		z.append(T.t("Zu schwer: nach %d Versuchen wird es umgangen") % VERSUCHE_MAX)
	elif not letzte.is_empty() and str(letzte.get("grund", "")) != "":
		z.append(T.t("Letzter Versuch: %s") % grund_text(str(letzte["grund"])))
	return z


func info() -> Dictionary:
	"""für /control und Tests"""
	return {"an": an, "stil": stil, "variante": variante, "gemerkt": daten.size(), "phase": str(lauf.get("phase", "")),
			"strategie": str(lauf.get("strategie", "")), "letzte": {"key": letzte.get("key", ""), "strategie": letzte.get("strategie", ""), "erfolg": letzte.get("erfolg", false), "grund": letzte.get("grund", "")}, "zeilen": Array(anzeige_zeilen())}
