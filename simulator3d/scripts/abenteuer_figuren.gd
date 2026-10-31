extends Node
## A2 «Figuren, Gespräche, Nebenaufgaben» im Bergtal-Abenteuer (Daniel, 31.10.2026 - Paket A2 des Abenteuer-Ausbaus).
##
## Figuren: Sepp (Älpler) und Vreni (Sennerin) auf der Alp Tschuggen, Anna (Hüttenwartin, Hütte und Biwak), Ruedi
##   (Wildhüter, überall im Tal), dazu jeden Tag (jede Tour) eine andere Wanderin / ein anderer Wanderer und eine andere
##   Bergsteigerin / ein anderer Bergsteiger. Gebaut mit actor.gd über menschen.gd (Aussehen: menschen._next_look) -
##   es gibt keine neuen Figuren-Modelle. Im Gespräch steht die Figur im Tal vor dir (Puppe, zählt nicht für Tests).
## Gespräche: Gruss je nach Gedächtnis, dann 2–3 Antworten zur Wahl (Themen, Nebenaufgabe, «Tschüss»). Rückfragen der
##   Figuren merkt sie sich (Flags) und spricht sie beim nächsten Mal an. Mit dem Hut des Grossvaters (hat("hut"))
##   erkennen die Figuren dich als Enkel: eigener Gruss und das Thema «Grossvater» - ohne neue Infos über ihn (Daniel).
## Nebenaufgaben: Tiere zurückbringen (Ziege, Schaf, Kuh zur Alp), Botendienste (Brief, Käse, Ersatzteil, Proviant -
##   Hütte, Alp, Postauto-Haltestelle, Biwak), Hilfe am Berg (verletzter Wanderer, Wegmarkierungen auffrischen),
##   Wildhüter-Aufträge (Auftrag und Abschluss; das Foto macht MoveEye - Paket A1, siehe foto_da()).
## Tausch: die Wunschlisten stehen in abenteuer_figuren_daten.gd (WUENSCHE); die Mechanik baut A4 mit wuensche(fid).
##
## Spielstand: Feld "a2_figuren" im Abenteuer-Fortschritt (user://bergtal_abenteuer/fortschritt.json). Während einer
##   Tour arbeitet A2 auf einer Kopie (R["a2"]["mem"]); die Kopie steht als erster Entscheid ["a2_snap"] in der
##   Situation, damit «Genau gleich nochmals abspielen» dieselben Gespräche zeigt (Wiedergaben speichern nichts).
##   Gespräche am Lager und Test-Gespräche zählen nicht zu den Entscheiden der Wiedergabe.
## Einhänge-Punkte in bergtal_abenteuer.gd (je eine Zeile): _ready, start_run (on_start), _post_leg (after_leg),
##   choose (Art "a2_…"), _paint_camp (paint_camp), _paint_chapter (paint_overview), op ("a2").
## Schnittstellen für die anderen Pakete:
##   wuensche(figur_id) -> Dictionary  A4 (statisch): {name, will: [ids], gibt: [ids]} («wanderer» / «bergsteiger» = von heute)
##   wunschliste(figur_id) -> Array    die festen Paare [{will, will_n, gibt, gibt_n, einmal}]
##   tausch_erledigt(figur_id, i)      A4: ein Tausch ist passiert (die Figur merkt es sich, «einmal»-Wünsche verschwinden)
##   foto_gemeldet(tier_id)            A1: MoveEye hat ein Tier aufgenommen (murmeltier, schneehase, gaemse, steinbock,
##                                     bartgeier, steinadler, luchs) - oder A1 bietet ab.a1.hat_foto(tier_id)
##   wild_auftraege() -> Array         A1: offene Wildhüter-Aufträge [{qid, tier, text}]
##   signal aufgabe(qid, st)           eine Nebenaufgabe ändert sich (aktiv | fertig | abgelehnt | melden | geholt)
##   signal gespraech(fid, ctx)        ein Gespräch beginnt (ctx: weg | lager | test)
## Steuerbefehl: {"action": "abenteuer", "do": "a2", "sub": state | talk (fid) | hut (value) | foto (value) |
##               wuensche (fid) | tag (value) | quest (qid, value) | reset}

const FD = preload("res://scripts/abenteuer_figuren_daten.gd")
const T = preload("res://scripts/i18n.gd")

signal aufgabe(qid, st)
signal gespraech(fid, ctx)

var ab                                # bergtal_abenteuer.gd
var _fig = null                       # the figure of the talk (actor.gd puppet)
var _tier = null                      # the found animal (actor.gd puppet)
var _planning := false                # on_start is planning (the run's day counts, not the saved one)


# =======================================================================================================================
# the memory
# =======================================================================================================================
static func _mem0() -> Dictionary:
	return {"tag": 0, "fig": {}, "q": {}, "fotos": {}, "besitz": {}, "test_hut": false, "tausch": []}


func _saved() -> Dictionary:
	var m = ab.P.get("a2_figuren", null)
	if not m is Dictionary:
		m = _mem0()
		ab.P["a2_figuren"] = m
	var z := _mem0()
	for k in z:
		if not m.has(k):
			m[k] = z[k]
	return m


func mem() -> Dictionary:
	"""during a tour: the copy of the run (a replay shows the same talks); else the saved memory"""
	if not ab.R.is_empty() and ab.R.has("a2"):
		return ab.R["a2"]["mem"]
	return _saved()


func _persist() -> void:
	if ab.replaying:
		return
	ab.P["a2_figuren"] = mem().duplicate(true)
	ab._save()


func fm(fid: String) -> Dictionary:
	var m := mem()
	if not m["fig"].has(fid):
		m["fig"][fid] = {"n": 0, "flags": {}, "asked": {}, "v": 0, "last": -1, "said": []}
	return m["fig"][fid]


func _A() -> Dictionary:
	return ab.R["a2"]


func _qst(qid: String) -> String:
	return str((mem()["q"] as Dictionary).get(qid, {}).get("st", ""))


func _set_q(qid: String, st: String, extra := {}) -> void:
	var e := {"st": st, "tag": int(mem()["tag"])}
	for k in extra:
		e[k] = extra[k]
	mem()["q"][qid] = e
	emit_signal("aufgabe", qid, st)


func heute() -> Dictionary:
	"""the wanderer and the climber of today (every tour is a new day; outside a tour: the next one)"""
	var t := int(mem()["tag"])
	if not _planning and (ab.R.is_empty() or not ab.R.has("a2") or not ab.step in [4, 5, 6]):
		t = int(_saved()["tag"]) + 1
	return {"wanderer": FD.WANDERER[t % FD.WANDERER.size()], "bergsteiger": FD.BERGSTEIGER[(t + 1) % FD.BERGSTEIGER.size()]}


# =======================================================================================================================
# things (A4 owns the inventory) and photos (A1 takes them)
# =======================================================================================================================
# Das Inventar gehört A4 (abenteuer_inventar.gd: hat / gib / nimm / anzahl). Es wird zur Laufzeit geladen, damit dieser
# Zweig auch ohne A4 läuft; nach dem Zusammenführen ist es immer da (dann ist der Ersatz unten nie aktiv).
# Verbrauchsdinge (brief, kaese, ersatzteil, proviant) liegen im Rucksack der Tour - eine Botschaft, die man über
# mehrere Touren trägt, packt on_start() wieder ein.
const INV_PATH := "res://scripts/abenteuer_inventar.gd"
const RUCK_PATH := "res://scripts/abenteuer_rucksack.gd"
static var _inv_s = null
static var _inv_tried := false


func _inv():
	if not _inv_tried:
		_inv_tried = true
		if ResourceLoader.exists(INV_PATH):
			_inv_s = load(INV_PATH)
			if _inv_s != null and ab != null:
				_inv_s.verbinde(ab)
	return _inv_s


func hat(id: String) -> bool:
	if id == "hut" and bool(mem().get("test_hut", false)):
		return true                                            # Test-Schalter (Übersicht im Kapitel)
	var inv = _inv()
	if inv != null:
		return bool(inv.hat(id))
	if not ab.R.is_empty() and ab.has(id):                     # Ersatz ohne A4
		return true
	return int((mem()["besitz"] as Dictionary).get(id, 0)) > 0


func gib(id: String, n := 1) -> void:
	var inv = _inv()
	if inv != null:
		inv.gib(id, n)
		return
	var b: Dictionary = mem()["besitz"]
	b[id] = int(b.get(id, 0)) + n


func nimm(id: String, n := 1) -> void:
	var inv = _inv()
	if inv != null:
		inv.nimm(id, n)                                        # (false = nicht mehr da - die Aufgabe gilt trotzdem)
		return
	var b: Dictionary = mem()["besitz"]
	b[id] = maxi(0, int(b.get(id, 0)) - n)
	if int(b[id]) == 0:
		b.erase(id)


func _carry_again() -> void:
	"""a delivery over several tours: the thing is in the backpack again (consumables belong to one tour)"""
	for qid in FD.QUEST_ORDER:
		var q: Dictionary = FD.QUESTS[qid]
		if str(q["typ"]) != "bote":
			continue
		var st := _qst(qid)
		var carried: bool = st == "geholt" or (st == "aktiv" and not q.has("hol"))
		if carried and not hat(str(q["item"])):
			gib(str(q["item"]))


# A1 (MoveEye-Lager + Wildkamera, abenteuer_moveeye.gd): ab.a1.hat_foto(tier) - Aufnahmen dieser Nacht und frühere (P["a1_fotos"]).
# foto_gemeldet(tier) bleibt für Tests (Steuerbefehl «foto»).
func foto_da(tier: String) -> bool:
	var a1 = ab.get("a1")
	if a1 != null and is_instance_valid(a1) and bool(a1.hat_foto(tier)):
		return true
	return bool((mem()["fotos"] as Dictionary).get(tier, false))


func foto_gemeldet(tier: String) -> void:
	mem()["fotos"][tier] = true
	_persist()


func wild_auftraege() -> Array:
	var out := []
	for qid in FD.QUEST_ORDER:
		var q: Dictionary = FD.QUESTS[qid]
		if str(q["typ"]) == "wild" and _qst(qid) == "aktiv":
			out.append({"qid": qid, "tier": str(q["tier"]), "text": T.t(str(q["kurz"]))})
	return out


# =======================================================================================================================
# trading (the mechanics: A4)
# =======================================================================================================================
static var _me = null                 # the running instance (for the static wuensche() that A4 calls)


func _enter_tree() -> void:
	_me = self


static func wuensche(fid: String) -> Dictionary:
	"""A4 (abenteuer_rucksack.gd) ruft das auf: {name, will: [ids], gibt: [ids], figur}; die Paare für den Tausch holt A4 mit wunschliste().
	«wanderer» / «bergsteiger» = die Figur von heute. Die genauen Paare (wie viele gegen wie viele): wunschliste()."""
	if fid in ["wanderer", "bergsteiger"]:
		if _me == null:
			return {}
		fid = str(_me.heute()[fid])
	if not FD.WUENSCHE.has(fid):
		return {}
	var will := []
	var gibt := []
	for w in FD.WUENSCHE[fid]:
		if not str(w["will"]) in will:
			will.append(str(w["will"]))
		if not str(w["gibt"]) in gibt:
			gibt.append(str(w["gibt"]))
	return {"name": T.t(str(FD.FIG[fid]["name"])), "will": will, "gibt": gibt, "figur": fid}


func wunschliste(fid: String) -> Array:
	"""die festen Paare je Figur: [{will, will_n, gibt, gibt_n, einmal, i, figur, erledigt}]"""
	if fid in ["wanderer", "bergsteiger"]:
		fid = heute()[fid]
	var out := []
	var lst: Array = FD.WUENSCHE.get(fid, [])
	for i in range(lst.size()):
		var w: Dictionary = (lst[i] as Dictionary).duplicate(true)
		w["i"] = i
		w["figur"] = fid
		w["erledigt"] = bool(w["einmal"]) and _traded(fid, i)
		out.append(w)
	return out


func _traded(fid: String, i: int) -> bool:
	for t in mem()["tausch"]:
		if str(t[0]) == fid and int(t[1]) == i:
			return true
	return false


func tausch_erledigt(fid: String, i: int) -> void:
	(mem()["tausch"] as Array).append([fid, i, int(mem()["tag"])])
	fm(fid)["flags"]["getauscht"] = true
	_persist()


func _item(id: String, n := 1) -> String:
	var nm := T.t(str(FD.ITEM_NAMES.get(id, id)))
	return nm if n <= 1 else "%d × %s" % [n, nm]


# =======================================================================================================================
# conditions, offers, hand-ins
# =======================================================================================================================
func _cond(c: String, fid: String) -> bool:
	if c == "":
		return true
	var f := fm(fid)
	for part in c.split("&"):
		var p := part.strip_edges()
		var neg := p.begins_with("!")
		if neg:
			p = p.substr(1)
		var ok := false
		if p == "erst":
			ok = int(f["n"]) == 0
		elif p == "wieder":
			ok = int(f["n"]) > 0
		elif p == "hut":
			ok = hat("hut")
		elif p == "neuhut":
			ok = hat("hut") and not (f["flags"] as Dictionary).has("hut_erkannt")
		elif p.begins_with("f:"):
			ok = (f["flags"] as Dictionary).has(p.substr(2))
		elif p.begins_with("q:"):
			ok = _qst(p.substr(2)) == "fertig"
		elif p.length() == 2 and p.begins_with("v"):
			ok = int(f["v"]) >= int(p.substr(1))
		if ok == neg:
			return false
	return true


func _offer(fid: String) -> String:
	"""the side task fid would give now (one at a time per figure)"""
	for qid in FD.QUEST_ORDER:
		if str(FD.QUESTS[qid]["von"]) == fid and _qst(qid) in ["aktiv", "geholt"]:
			return ""
	for qid in FD.QUEST_ORDER:
		var q: Dictionary = FD.QUESTS[qid]
		if str(q["von"]) != fid:
			continue
		var st := _qst(qid)
		if st == "abgelehnt" and int(mem()["q"][qid].get("tag", 0)) >= int(mem()["tag"]):
			continue                                         # asked again the next day
		if st in ["", "abgelehnt"] and _cond(str(q.get("cond", "")), fid):
			return qid
	return ""


func _turnins(fid: String) -> Array:
	"""what can be handed in to fid now"""
	var out := []
	for qid in FD.QUEST_ORDER + ["q_verletzt"]:
		var q: Dictionary = FD.QUESTS[qid]
		var st := _qst(qid)
		match str(q["typ"]):
			"bote":
				if str(q.get("an", "")) == fid and (st == "geholt" or (st == "aktiv" and not q.has("hol"))):
					out.append(qid)
			"wild":
				if str(q["von"]) == fid and st == "aktiv" and foto_da(str(q["tier"])):
					out.append(qid)
			"hilfe":
				if qid == "q_verletzt" and st == "melden" and fid in ["huettenwartin", "wildhueter"]:
					out.append(qid)
	return out


func _wants(fid: String) -> bool:
	"""someone you have something for (a delivery, a report, a photo) - you meet them more likely"""
	return not _turnins(fid).is_empty()


# =======================================================================================================================
# the tour: plan the meetings, the events after a leg
# =======================================================================================================================
func on_start() -> void:
	"""bergtal_abenteuer.start_run: the memory of this run (from the situation in a replay), plan who you meet"""
	var m: Dictionary = {}
	if ab.replaying and not ab.replay_q.is_empty() and str(ab.replay_q[0][1]) == "a2_snap":
		var s = JSON.parse_string(str(ab.replay_q.pop_front()[2]))
		if s is Dictionary:
			m = s
	if m.is_empty():
		m = _saved().duplicate(true)
		if not ab.replaying:
			m["tag"] = int(m.get("tag", 0)) + 1                # a new day: other wanderers and climbers
	var z := _mem0()
	for k in z:
		if not m.has(k):
			m[k] = z[k]
	ab.choices.append([0, "a2_snap", JSON.stringify(m)])
	ab.R["a2"] = {"mem": m, "plan": {}, "talk": {}, "met": {}, "essen": false}
	_carry_again()
	_planning = true
	_plan()
	_planning = false
	_persist()


func _plan() -> void:
	var rng := RandomNumberGenerator.new()                     # own random numbers: the tour's rng stays untouched
	rng.seed = int(ab.R["seed"]) * 31 + 162
	var stages: Array = ab.chapter()["stages"]
	var ends := {}
	var legs := []
	for i in range(stages.size()):
		var st: Dictionary = stages[i]
		if st.has("walk"):
			ends[i] = st["walk"][-1]
			legs.append(i)
		elif st.has("fork"):
			ends[i] = st["fork"][0][1][-1]
			legs.append(i)
	var plan := {}
	# 1) at home: Alp, hut, biwak (in a random order - not always the same one first)
	var homes := ["aelpler", "sennerin", "huettenwartin"]
	for k in range(homes.size() - 1, 0, -1):
		var j := rng.randi() % (k + 1)
		var tmp = homes[k]
		homes[k] = homes[j]
		homes[j] = tmp
	for fid in homes:
		var f: Dictionary = FD.FIG[fid]
		var r1 := rng.randf()
		for i in legs:
			if plan.has(str(i)):
				continue
			var near := false
			for o in f["orte"]:
				if (ends[i] as Vector2).distance_to(o) < float(f["r"]):
					near = true
			if near:
				if r1 < 0.7 or _wants(fid):
					plan[str(i)] = fid
				break
	# 2) on the way: the gamekeeper, whoever you have something for, the wanderer and the climber of today
	var free := []
	for i in legs:
		if not plan.has(str(i)):
			free.append(i)
	var roam := []
	for fid in FD.FEST:
		if fid in plan.values():
			continue
		var p := float(FD.FIG[fid]["unterwegs"])
		if _wants(fid):
			p = maxf(p, 0.65)
		if rng.randf() < p:
			roam.append(fid)
	var h := heute()
	var hurt := ""
	if rng.randf() < 0.22:
		hurt = str(h["wanderer"]) if rng.randf() < 0.6 else str(h["bergsteiger"])
	for k in ["wanderer", "bergsteiger"]:
		var fid2 := str(h[k])
		if fid2 == hurt or rng.randf() < float(FD.FIG[fid2]["unterwegs"]):
			roam.append(fid2)
	for fid in roam:
		if free.is_empty() or plan.size() >= 3:
			break
		var j := rng.randi() % free.size()
		var i: int = free[j]
		free.remove_at(j)
		plan[str(i)] = ("!" + fid) if fid == hurt else fid
	_A()["plan"] = plan


func after_leg(i: int) -> bool:
	"""bergtal_abenteuer._post_leg: a side task at this place, or the meeting planned for this leg (true = wait for it)"""
	if ab.R.is_empty() or not ab.R.has("a2"):
		return false
	var A := _A()
	var done: Dictionary = ab.R["events_done"]
	var pos: Vector2 = ab.R["pos"]
	for qid in FD.QUEST_ORDER:
		var q: Dictionary = FD.QUESTS[qid]
		var st := _qst(qid)
		var key := "a2_%d_%s" % [i, qid]
		if done.has(key) or st != "aktiv":
			continue
		var typ := str(q["typ"])
		if typ == "tier" and pos.distance_to(q["ort"]) < float(q["r"]):
			done[key] = true
			_ev_tier(i, qid)
			return true
		if typ == "bote" and q.has("hol") and pos.distance_to(q["hol"]) < float(q["r"]):
			done[key] = true
			_ev_hol(i, qid)
			return true
		if typ == "bote" and q.has("an_ort") and pos.distance_to(q["an_ort"]) < float(q["r"]):
			done[key] = true
			_ev_ablegen(i, qid)
			return true
		if qid == "q_markieren" and i > int(A.get("mark_from", -1)) and not A.has("mark_try"):
			done[key] = true
			A["mark_try"] = true
			_ev_markieren(i)
			return true
	var who := str(A["plan"].get(str(i), ""))
	if who != "" and not done.has("a2_%d_talk" % i):
		done["a2_%d_talk" % i] = true
		if who.begins_with("!"):
			_ev_verletzt(i, who.substr(1))
		else:
			start_talk(who, "weg", i)
		return true
	return false


# =======================================================================================================================
# talks
# =======================================================================================================================
func start_talk(fid: String, ctx: String, leg := -1) -> void:
	var f := fm(fid)
	var g := ""
	for gr in FD.GRUSS.get(fid, []):
		if _cond(str(gr[0]), fid):
			g = T.t(str(gr[1]))
			if str(gr[0]) == "neuhut":
				f["flags"]["hut_erkannt"] = true
			break
	if int(f["n"]) > 0:                                        # it remembers what you promised
		for qid in FD.QUEST_ORDER:
			var q: Dictionary = FD.QUESTS[qid]
			if str(q["von"]) == fid and _qst(qid) == "aktiv" and q.has("erinnerung") and not qid in _turnins(fid):
				g += "\n" + T.t(str(q["erinnerung"]))
				break
	f["n"] = int(f["n"]) + 1
	f["last"] = int(mem()["tag"])
	_A()["talk"] = {"fid": fid, "ctx": ctx, "leg": leg, "asked": [], "topic": ""}
	_A()["met"][fid] = true
	_show_fig(fid)
	ab._diary("person", T.t(str(FD.FIG[fid]["name"])), g)
	emit_signal("gespraech", fid, ctx)
	_menu(g)
	_persist()


func _name(fid: String) -> String:
	return T.t(str(FD.FIG[fid]["name"]))


func _ask(text: String, opts: Array) -> void:
	var t: Dictionary = _A()["talk"]
	ab._ask("a2_talk", _name(str(t["fid"])), text, opts, {"a2": {"leg": int(t["leg"]), "ctx": str(t["ctx"])}})


func _topics(fid: String) -> Array:
	"""the topics you can pick now: the grandfather first (with the hat), then new ones, then the known ones"""
	var t: Dictionary = _A()["talk"]
	var f := fm(fid)
	var a := []
	var b := []
	for x in FD.THEMEN.get(fid, []):
		var id := str(x["id"])
		if id in t["asked"] or not _cond(str(x.get("cond", "")), fid):
			continue
		var n := int((f["asked"] as Dictionary).get(id, 0))
		if bool(x.get("einmal", false)) and n > 0:
			continue
		if n == 0:
			a.append(x)
		else:
			b.append(x)
	return a + b


func _menu(text: String) -> void:
	"""2–3 answers: hand in / help / topics, always «Tschüss»"""
	var t: Dictionary = _A()["talk"]
	var fid := str(t["fid"])
	var opts := []
	var ti := _turnins(fid)
	if not ti.is_empty():
		opts.append(["q:%s:abgabe" % ti[0], T.t(str(FD.QUESTS[ti[0]]["abgabe"]))])
	var off := _offer(fid)
	if off != "" and not ("q:" + off) in t["asked"] and opts.size() < 2:
		opts.append(["q:%s:frage" % off, T.t("Hast du einen Auftrag für mich?") if fid == "wildhueter" else T.t("Kann ich dir helfen?")])
	for x in _topics(fid):
		if opts.size() >= 2:
			break
		opts.append(["t:" + str(x["id"]), T.t(str(x["frage"]))])
	opts.append(["x", T.t("Auf Wiedersehen!") if fid == "w_gerber" else T.t("Tschüss!")])
	_ask(text, opts)


func choose(pe: Dictionary, v: String) -> void:
	"""bergtal_abenteuer.choose for the kinds «a2_…»"""
	var ex: Dictionary = pe.get("a2", {})
	if str(ex.get("ctx", "weg")) != "weg" and not ab.choices.is_empty():
		ab.choices.pop_back()                                  # at the camp / tests: not part of the replay
	if not ab.R.has("a2"):
		return
	if str(pe["kind"]) == "a2_ev":
		_ev_choose(ex, v)
		return
	var t: Dictionary = _A()["talk"]
	if t.is_empty():
		_continue(str(ex.get("ctx", "weg")), int(ex.get("leg", -1)))
		return
	if v == "x":
		_end_talk()
	elif v.begins_with("t:"):
		_topic(v.substr(2))
	elif v.begins_with("a:"):
		_answer(int(v.substr(2)))
	elif v.begins_with("q:"):
		var pr := v.split(":")
		_quest_talk(pr[1], pr[2])
	_persist()


func _topic_def(fid: String, id: String) -> Dictionary:
	for x in FD.THEMEN.get(fid, []):
		if str(x["id"]) == id:
			return x
	return {}


func _topic(id: String) -> void:
	var t: Dictionary = _A()["talk"]
	var fid := str(t["fid"])
	var f := fm(fid)
	var x := _topic_def(fid, id)
	if x.is_empty():
		_menu("")
		return
	(t["asked"] as Array).append(id)
	f["asked"][id] = int((f["asked"] as Dictionary).get(id, 0)) + 1
	if x.has("merkt"):
		f["flags"][str(x["merkt"])] = true
	var txt := _effect(str(x["effekt"]), fid) if x.has("effekt") else T.t(str(x.get("antwort", "")))
	if x.has("frage2"):
		t["topic"] = id
		var opts := []
		var ans: Array = x["frage2"]["antworten"]
		for k in range(ans.size()):
			opts.append(["a:%d" % k, T.t(str(ans[k][0]))])
		_ask(txt + "\n\n" + T.t(str(x["frage2"]["text"])), opts)
		return
	_menu(txt)


func _answer(k: int) -> void:
	var t: Dictionary = _A()["talk"]
	var fid := str(t["fid"])
	var f := fm(fid)
	var x := _topic_def(fid, str(t["topic"]))
	if x.is_empty() or not x.has("frage2"):
		_menu("")
		return
	var ans: Array = x["frage2"]["antworten"]
	k = clampi(k, 0, ans.size() - 1)
	for a in ans:                                              # the latest answer counts
		(f["flags"] as Dictionary).erase(str(a[1]))
	var fl := str(ans[k][1])
	f["flags"][fl] = true
	(f["said"] as Array).append([str(x["id"]), fl])
	f["said"] = (f["said"] as Array).slice(-10)
	var txt := T.t(str(x["frage2"]["nach"].get(fl, "")))
	var e2: Dictionary = x.get("effekt2", {})
	if str(e2.get(fl, "")) == "essen" and not bool(_A()["essen"]):
		_A()["essen"] = true
		ab.R["food"] = minf(100.0, float(ab.R.get("food", 50.0)) + 30.0)
		txt += "\n" + T.t("(Essen +30)")
		ab._diary("meet", T.t("Alpkäse"), T.t("Ein Stück Käse von Vreni - gibt Kraft."))
	t["topic"] = ""
	_menu(txt)


func _effect(e: String, fid: String) -> String:
	var tag := int(mem()["tag"])
	match e:
		"tausch":
			var lines := []
			for w in wunschliste(fid):
				if bool(w["erledigt"]):
					continue
				lines.append("• " + T.t("%s gegen %s") % [_item(str(w["will"]), int(w["will_n"])), _item(str(w["gibt"]), int(w["gibt_n"]))])
			if lines.is_empty():
				return T.t("Im Moment brauche ich nichts. Danke!")
			var tx := T.t("Ich hätte gern etwas - und gebe dir etwas dafür:") + "\n" + "\n".join(lines)
			if ResourceLoader.exists(RUCK_PATH):               # A4: the trading window
				var rk = load(RUCK_PATH)
				if rk != null:
					rk.tausch_oeffnen(ab, fid)
					tx += "\n" + T.t("Das Tausch-Fenster ist offen.")
				else:
					tx += "\n" + T.t("(Tauschen geht über den Rucksack.)")
			else:
				tx += "\n" + T.t("(Tauschen geht über den Rucksack.)")
			return tx
		"wetter":
			var nxt := ""
			if ab.step == 4:
				for k in (ab.R["weather"] as Dictionary).keys():
					if int(k) >= int(ab.R["stage"]) and not ab.R["events_done"].has("wx" + str(k)):
						nxt = str(ab.R["weather"][k])
						break
			if nxt == "storm":
				return T.t("Pass auf: heute kommt noch ein Gewitter. Wenn es donnert, weg vom Grat und von einzelnen Bäumen.")
			if nxt == "fog":
				return T.t("Heute steigt noch Nebel aus dem Tal. Halte den Kompass bereit und bleib auf dem Weg.")
			if str(ab.R.get("season", "sommer")) in ["herbst", "winter"]:
				return T.t("Es bleibt trocken. Heute Nacht wird es aber richtig kalt - der Schlafsack muss warm genug sein.")
			return T.t("Bis heute Abend bleibt es schön. Nachts wird es in der Höhe kühl - nimm die Jacke heraus.")
		"schlafplatz":
			var b = ab.bt()
			var ch: Dictionary = ab.chapter()
			var p: Vector2 = ab.R.get("camp_xz", Vector2(float(ch["camp"][1]), float(ch["camp"][2]))) if ab.step == 5 else Vector2(float(ch["camp"][1]), float(ch["camp"][2]))
			if b == null:
				return T.t("Bei der Hütte bist du sicher.")
			var ev: Dictionary = b.evaluate(p.x, p.y)
			var tx2 := T.t("Dein Platz für heute Nacht: Sicherheit %d, Aussicht %d, Ruhe %d - von 5.") % [int(ev["sicherheit"]), int(ev["aussicht"]), int(ev["ruhe"])]
			for n in (ev.get("notes", []) as Array).slice(0, 2):
				tx2 += "\n• " + T.t(str(n))
			return tx2
		"tipp":
			return T.t(str(FD.TIPPS[(tag + int(fm(fid)["asked"].get("tipp", 0))) % FD.TIPPS.size()]))
		"geruecht":
			return T.t(str(FD.GERUECHTE[(tag * 3 + FD.ORDER.find(fid)) % FD.GERUECHTE.size()]))
	return ""


func _lohn(qid: String, fid: String) -> String:
	"""a side task is done: experience, trust, maybe a thing"""
	var q: Dictionary = FD.QUESTS[qid]
	var l: Dictionary = q["lohn"]
	var keep: Dictionary = ((mem()["q"] as Dictionary).get(qid, {}) as Dictionary).duplicate()
	keep.erase("st")
	keep.erase("tag")
	_set_q(qid, "fertig", keep)
	var giver := str(q["von"]) if str(q["von"]) != "" else fid
	if giver != "":
		fm(giver)["v"] = int(fm(giver)["v"]) + int(l["v"])
	if not ab.replaying:
		ab.P["xp"] = int(ab.P.get("xp", 0)) + int(l["xp"])
	var tx := T.t("+%d Erfahrung") % int(l["xp"])
	if str(l["gib"]) != "":
		gib(str(l["gib"]))
		tx += " · " + T.t("du bekommst: %s") % _item(str(l["gib"]))
	ab._diary("a2", T.t("Nebenaufgabe erledigt"), T.t(str(q["kurz"])) + " (" + tx + ")")
	return tx


func _quest_talk(qid: String, what: String) -> void:
	var t: Dictionary = _A()["talk"]
	var fid := str(t["fid"])
	if not FD.QUESTS.has(qid):
		_menu("")
		return
	var q: Dictionary = FD.QUESTS[qid]
	match what:
		"frage":
			(t["asked"] as Array).append("q:" + qid)
			_ask(T.t(str(q["angebot"])), [["q:%s:ja" % qid, T.t("Ja, mache ich.")], ["q:%s:nein" % qid, T.t("Jetzt gerade nicht.")]])
		"ja":
			_set_q(qid, "aktiv")
			var tx := T.t("Danke! Das ist lieb von dir.")
			if str(q["typ"]) == "bote" and not q.has("hol"):
				gib(str(q["item"]))
				tx += "\n" + T.t("Du bekommst: %s") % _item(str(q["item"]))
			if qid == "q_markieren":
				_A()["mark_from"] = int(t["leg"])
			tx += "\n" + T.t("Neue Nebenaufgabe: %s") % T.t(str(q["kurz"]))
			ab._diary("a2", T.t("Neue Nebenaufgabe"), T.t(str(q["kurz"])))
			_menu(tx)
		"nein":
			_set_q(qid, "abgelehnt")
			_menu(T.t("Kein Problem. Vielleicht ein andermal."))
		"abgabe":
			var tx2 := T.t(str(q["dank"]))
			match str(q["typ"]):
				"bote":
					nimm(str(q["item"]))
				"wild":
					fm(fid)["flags"]["auftrag_fertig"] = true
				"hilfe":
					var wer := str((mem()["q"] as Dictionary).get(qid, {}).get("wer", ""))
					if wer != "":
						fm(wer)["flags"]["hilfe_bekommen"] = true
			tx2 += "\n" + _lohn(qid, fid)
			_menu(tx2)


func _end_talk() -> void:
	var t: Dictionary = _A()["talk"]
	_A()["talk"] = {}
	_hide_fig()
	_continue(str(t.get("ctx", "weg")), int(t.get("leg", -1)))


func _continue(ctx: String, leg: int) -> void:
	if ctx == "weg" and leg >= 0 and ab.step == 4:
		ab._post_leg(leg)                                      # the next thing after this leg (or the next stage)
	else:
		ab._changed()


# =======================================================================================================================
# side-task events on the way
# =======================================================================================================================
func _ev(text: String, title: String, opts: Array, ex: Dictionary) -> void:
	ex["ctx"] = "weg"
	ab._ask("a2_ev", title, text, opts, {"a2": ex})


func _ok(title: String, text: String, leg: int) -> void:
	_ev(text, title, [["ok", T.t("Weiter")]], {"ev": "ok", "leg": leg})


func _ev_tier(i: int, qid: String) -> void:
	var q: Dictionary = FD.QUESTS[qid]
	_show_tier(str(q["tier"]))
	var h := _detour_h(q["ort"])
	_ev(T.t(str(q["gefunden"])), T.t("Ausgebüxt!"), [["zurueck", T.t("Zur Alp zurückbringen (Umweg %d Min.)") % int(round(h * 60.0))],
			["nein", T.t("Jetzt nicht - weiter")]], {"ev": "tier", "qid": qid, "leg": i})


func _detour_h(p: Vector2) -> float:
	# hin und zurück zur Alp mit dem Tier, gemütlich ~3,5 km/h (Wanderzeit ohne Steigung)
	return clampf(2.0 * p.distance_to(FD.ALP) / 3500.0, 0.3, 1.2)


func _ev_hol(i: int, qid: String) -> void:
	var q: Dictionary = FD.QUESTS[qid]
	_ev(T.t(str(q["abholen"])), T.t("Botendienst"), [["nehmen", T.t("Mitnehmen")], ["nein", T.t("Liegen lassen")]], {"ev": "hol", "qid": qid, "leg": i})


func _ev_ablegen(i: int, qid: String) -> void:
	var q: Dictionary = FD.QUESTS[qid]
	nimm(str(q["item"]))
	var tx := T.t(str(q["abholen"])) + "\n" + _lohn(qid, str(q["von"]))
	_persist()
	_ok(T.t("Botendienst"), tx, i)


func _ev_markieren(i: int) -> void:
	var q: Dictionary = FD.QUESTS["q_markieren"]
	_ev(T.t(str(q["arbeit"])), T.t("Hilfe am Berg"), [["ja", T.t("Jetzt markieren (20 Min.)")], ["nein", T.t("Später")]], {"ev": "mark", "leg": i})


func _ev_verletzt(i: int, fid: String) -> void:
	_show_fig(fid)
	fm(fid)["n"] = int(fm(fid)["n"]) + 1
	var opts := []
	if ab.has("apotheke"):
		opts.append(["apotheke", T.t("Erste Hilfe geben (15 Min.)")])
	opts.append(["stuetzen", T.t("Fuss einbinden und ein Stück begleiten (40 Min.)")])
	opts.append(["melden", T.t("Weitergehen und Hilfe holen")])
	_ev(T.t(str(FD.QUESTS["q_verletzt"]["angebot"])) % _name(fid), T.t("Hilfe am Berg"), opts, {"ev": "hurt", "fid": fid, "leg": i})


func _ev_choose(ex: Dictionary, v: String) -> void:
	var leg := int(ex.get("leg", -1))
	var qid := str(ex.get("qid", ""))
	match str(ex.get("ev", "ok")):
		"ok":
			_hide_fig()
			_continue("weg", leg)
			return
		"tier":
			if v == "zurueck":
				var q: Dictionary = FD.QUESTS[qid]
				ab._pause(_detour_h(q["ort"]), false)
				var tx := _name(str(q["von"])) + ": «" + T.t(str(q["dank"])) + "»\n" + _lohn(qid, str(q["von"]))
				_persist()
				_ok(T.t("Zurück auf der Alp"), tx, leg)
				return
		"hol":
			if v == "nehmen":
				var q2: Dictionary = FD.QUESTS[qid]
				gib(str(q2["item"]))
				_set_q(qid, "geholt")
				ab._diary("a2", T.t("Botendienst"), T.t("Mitgenommen: %s") % _item(str(q2["item"])))
				_persist()
		"mark":
			if v == "ja":
				ab._pause(1.0 / 3.0, false)
				fm("aelpler")["flags"]["markiert"] = true
				var tx2 := T.t(str(FD.QUESTS["q_markieren"]["gemacht"])) + "\n" + _lohn("q_markieren", "aelpler")
				_persist()
				_ok(T.t("Hilfe am Berg"), tx2, leg)
				return
		"hurt":
			var fid := str(ex.get("fid", ""))
			if v == "melden":
				_set_q("q_verletzt", "melden", {"wer": fid})
				ab._diary("a2", T.t("Hilfe am Berg"), T.t("Du sagst der Hüttenwartin oder dem Wildhüter Bescheid, sobald du sie triffst."))
				_persist()
				_ok(T.t("Hilfe am Berg"), T.t("Du versprichst, Hilfe zu holen. Sag es der Hüttenwartin oder dem Wildhüter, sobald du sie triffst."), leg)
				return
			ab._pause(0.25 if v == "apotheke" else 2.0 / 3.0, false)
			fm(fid)["flags"]["hilfe_bekommen"] = true
			var tx3 := (T.t("Mit Pflaster und Binde geht es wieder. «Danke, das vergesse ich dir nicht!»") if v == "apotheke"
					else T.t("Du bindest den Fuss mit einem Tuch ein und begleitest ein Stück. «Danke, jetzt schaffe ich es allein.»"))
			_set_q("q_verletzt", "hilfe", {"wer": fid})
			tx3 += "\n" + _lohn("q_verletzt", fid)
			_persist()
			_ok(T.t("Hilfe am Berg"), tx3, leg)
			return
	_hide_fig()
	_continue("weg", leg)


# =======================================================================================================================
# the figures in the valley (actor.gd via menschen.gd - no new models)
# =======================================================================================================================
func _spot() -> Array:
	"""[where the figure stands, where it looks]: 7 m ahead on the way (the view looks there) or beside the camp"""
	if ab.step == 5 and ab.R.has("camp_xz"):
		var c: Vector2 = ab.R["camp_xz"]
		return [c + Vector2(4.0, 3.0), c]
	var p: Vector2 = ab.R.get("pos", Vector2.ZERO)
	var w: Array = ab.R.get("walked", [])
	var d := Vector2(0, -1)
	if w.size() >= 2 and p.distance_to(w[-2]) > 0.1:
		d = (p - (w[-2] as Vector2)).normalized()
	return [p + d * 7.0, p]


func _show_fig(fid: String) -> void:
	_hide_fig()
	var b = ab.bt()
	if b == null or ab.main == null:
		return
	var F: Dictionary = FD.FIG[fid]
	var sp := _spot()
	var at: Vector2 = sp[0]
	var look: Vector2 = sp[1]
	var mm = ab.main.menschen
	if mm != null:
		mm._next_look = {"force": true, "jacket": F["jacke"], "cap": bool(F["cap"]), "hood": false, "pack": bool(F["pack"]),
				"height": float(F["gross"]), "gait": "stand", "umbrella": false, "vest": false, "bag": false, "bike": false}
	var wa: Vector3 = b.WG(at.x, at.y)
	var wl: Vector3 = b.WG(look.x, look.y)
	var v = ab.main.spawn(str(F["kind"]), wa, wl)
	if v == null:
		return
	_puppet(v, wa, wl)
	v.set_meta("a2_figur", fid)
	_fig = v
	if not ab.fast and ab.step == 4:
		ab._fly_view(b.WG(look.x, look.y, 1.7), wa + Vector3(0, 1.2, 0))


func _show_tier(tier: String) -> void:
	var b = ab.bt()
	if b == null or ab.main == null or not FD.TIERE.has(tier):
		return
	var td: Array = FD.TIERE[tier]
	var sp := _spot()
	var at: Vector2 = (sp[0] as Vector2) + Vector2(3.0, 2.0)
	var wa: Vector3 = b.WG(at.x, at.y)
	var wl: Vector3 = b.WG((sp[1] as Vector2).x, (sp[1] as Vector2).y)
	var v = ab.main.spawn(str(td[0]), wa, wl)
	if v == null:
		return
	_puppet(v, wa, wl)
	b._recolor(v, td[1], float(td[2]))
	_tier = v
	if not ab.fast and ab.step == 4:
		ab._fly_view(wl + Vector3(0, 1.7, 0), wa + Vector3(0, 0.6, 0))


func _puppet(v, wa: Vector3, wl: Vector3) -> void:
	v.puppet = true                                            # stands there, only the idle animation runs
	v.set_meta("nachbar", true)                                # never part of a test
	v.global_position = wa
	var d := wl - wa
	d.y = 0.0
	if d.length() > 0.01:
		v.heading = atan2(-d.x, -d.z)
		v.rotation.y = v.heading


func _hide_fig() -> void:
	for x in [_fig, _tier]:
		if x != null and is_instance_valid(x):
			x.queue_free()
	_fig = null
	_tier = null


func _process(_dt: float) -> void:
	if ab == null:
		return
	var live: bool = not ab.R.is_empty() and ab.step in [4, 5]
	var pe = ab.R.get("pending", {}) if not ab.R.is_empty() else {}
	var mine: bool = pe is Dictionary and str(pe.get("kind", "")).begins_with("a2_")
	if not live:
		if _fig != null or _tier != null:
			_hide_fig()
		if mine:                                               # the night began during a talk at the camp
			ab.R["pending"] = {}
			_A()["talk"] = {}
		return
	if (_fig != null or _tier != null) and not mine:
		_hide_fig()


# =======================================================================================================================
# the panel: at the camp, on the chapter page
# =======================================================================================================================
func leute_am_lager() -> Array:
	if ab.R.is_empty() or not ab.R.has("camp_xz"):
		return []
	var c: Vector2 = ab.R["camp_xz"]
	var out := []
	for fid in FD.FEST:
		var f: Dictionary = FD.FIG[fid]
		for o in f["orte"]:
			if c.distance_to(o) < float(f["r"]) + 80.0 and not fid in out:
				out.append(fid)
	var h := heute()
	if c.distance_to(Vector2(-520, 560)) < 300.0:
		out.append(str(h["bergsteiger"]))                       # the climbers sleep in the biwak too
	if str(ab.R.get("camp_spot", "")) in ["seeufer", "huette", "pass"]:
		out.append(str(h["wanderer"]))
	return out


func paint_camp(body: VBoxContainer) -> void:
	"""bergtal_abenteuer._paint_camp: the talk at the camp, or who is here to talk to"""
	if ab.R.is_empty() or not ab.R.has("a2"):
		return
	var pe: Dictionary = ab.R.get("pending", {})
	if not pe.is_empty() and str(pe.get("kind", "")).begins_with("a2_"):
		var g = ab._group(str(pe["title"]), body)
		g.add_child(ab._lab(str(pe["text"]), 14, Color.WHITE))
		for o in pe["options"]:
			var vv: String = str(o[0])
			var bb: Button = ab._btn(g, str(o[1]), func(): ab.op({"do": "choose", "value": vv}), (pe["options"] as Array).size() == 1)
			bb.custom_minimum_size = Vector2(0, 40)
		return
	var here := leute_am_lager()
	if here.is_empty():
		return
	var g2 = ab._group(T.t("Leute beim Lager"), body)
	for fid in here:
		var ff: String = fid
		ab._btn(g2, T.t("Mit %s sprechen") % _name(fid), func(): ab.op({"do": "a2", "sub": "talk", "fid": ff}))


func paint_overview(parent: Control) -> void:
	"""bergtal_abenteuer._paint_chapter: whom you know, the open side tasks"""
	var m := mem()
	var g = ab._group(T.t("Leute im Tal"), parent)
	var h := heute()
	g.add_child(ab._lab(T.t("Heute unterwegs: %s und %s.") % [_name(str(h["wanderer"])), _name(str(h["bergsteiger"]))], 12, Color(0.6, 0.66, 0.74)))
	var known := []
	for fid in FD.ORDER:
		var e: Dictionary = (m["fig"] as Dictionary).get(fid, {})
		if int(e.get("n", 0)) > 0:
			known.append(T.t("%s - %d× gesprochen") % [_name(fid), int(e["n"])] + ("  " + "★".repeat(mini(int(e.get("v", 0)), 5)) if int(e.get("v", 0)) > 0 else ""))
	if not known.is_empty():
		g.add_child(ab._lab("\n".join(known), 12))
	var open := []
	for qid in FD.QUEST_ORDER + ["q_verletzt"]:
		if _qst(qid) in ["aktiv", "geholt", "melden"]:
			open.append("• " + T.t(str(FD.QUESTS[qid]["kurz"])))
	if not open.is_empty():
		g.add_child(ab._lab(T.t("Nebenaufgaben:") + "\n" + "\n".join(open), 12, Color(0.95, 0.85, 0.6)))
	# 3D-4.70: the switch «Test: Hut des Grossvaters tragen» is gone - A3 (abenteuer_raetsel.gd) gives the hat in chapter 1.
	# For tests only: /control abenteuer a2 {sub: hut, value} (test_hut) still works.


# =======================================================================================================================
# control / tests
# =======================================================================================================================
func info() -> Dictionary:
	var m := mem()
	var figs := {}
	for fid in FD.ORDER:
		var e: Dictionary = (m["fig"] as Dictionary).get(fid, {})
		figs[fid] = {"name": FD.FIG[fid]["name"], "n": int(e.get("n", 0)), "v": int(e.get("v", 0)), "flags": (e.get("flags", {}) as Dictionary).keys()}
	var qs := {}
	for qid in m["q"]:
		qs[qid] = str(m["q"][qid].get("st", ""))
	var out := {"tag": int(m["tag"]), "heute": heute(), "hut": hat("hut"), "figuren": figs, "quests": qs, "fotos": m["fotos"],
			"besitz": m["besitz"]}
	if not ab.R.is_empty() and ab.R.has("a2"):
		out["plan"] = _A()["plan"]
		out["talk"] = _A()["talk"]
		out["camp"] = leute_am_lager() if ab.step == 5 else []
	return out


func op(d: Dictionary) -> Dictionary:
	var sub := str(d.get("sub", "state"))
	match sub:
		"talk":
			var fid := str(d.get("fid", ""))
			if not FD.FIG.has(fid):
				return {"ok": false, "error": "figur: " + ", ".join(FD.ORDER)}
			if ab.R.is_empty() or not ab.R.has("a2") or not ab.step in [4, 5]:
				return {"ok": false, "error": "kein Abenteuer unterwegs"}
			if bool(ab.R.get("walking", false)) or not (ab.R["pending"] as Dictionary).is_empty():
				return {"ok": false, "error": "gerade beschäftigt"}
			start_talk(fid, "lager" if ab.step == 5 else "test")
			ab._changed()
		"hut":
			mem()["test_hut"] = bool(d.get("value", true))
			_persist()
			ab._changed()
		"foto":
			foto_gemeldet(str(d.get("value", "")))
		"wuensche":
			return {"ok": true, "wuensche": wuensche(str(d.get("fid", ""))), "paare": wunschliste(str(d.get("fid", "")))}
		"tag":
			mem()["tag"] = int(d.get("value", 0))
			_persist()
		"quest":
			var qid := str(d.get("qid", ""))
			if not FD.QUESTS.has(qid):
				return {"ok": false, "error": "qid"}
			_set_q(qid, str(d.get("value", "aktiv")))
			_persist()
		"reset":
			ab.P["a2_figuren"] = _mem0()
			if not ab.R.is_empty() and ab.R.has("a2"):
				_A()["mem"] = _mem0()
			ab._save()
			ab._changed()
	return {"ok": true, "a2": info()}
