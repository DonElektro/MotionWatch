extends Node
## Zwei-Spieler-Bausteine (Daniel 31.10.2026, Paket «Zwei-Spieler-Bausteine»): gemeinsame Bausteine fürs Spielen zu zweit
## (ein Bildschirm, zwei Controller) - für BEIDE Geschichten. Die Bausteine kennen keine Geschichte: alles, was sie über die
## Welt wissen müssen, fragen sie einen «Wirt» (host) mit kleinen zb_*-Funktionen. Allein spielen: zb_aktiv() = false, dann
## zeigt und tut dieser Knoten nichts.
##   «Die Karte des Grossvaters»: Wirt = abenteuer_zwei_team.gd (eingehängt in abenteuer_zweit.gd)
##   «Maggie und der Bergkristall»: Wirt = maggie_zwei_team.gd (Kind von maggie_zwei.gd; Anleitung ganz unten in diesem Kopf)
##
## Die zehn Bausteine (alle für den Wirt aufrufbar):
##   1 Geteiltes Wissen   wissen(id, [text_spieler1, text_spieler2])  · wissen_weg(id = "")
##                        Jeder Text erscheint NUR in seinem Bildschirmteil (gross, unten). "" = für diesen nichts.
##   2 Räuberleiter       teamstelle(id, pos, text := "", hoehe := 2.6, sicht := -1) · teamstelle_aktiv(id) · teamstelle_weg(id)
##                        Ein Felsblock. Beide hin (Gummiband) → wer zuerst A drückt, hilft hoch → der andere A = hochsteigen →
##                        oben A = Seil hinunterwerfen (braucht «seil» beim Oberen; hat es der Untere: B = hochgeben; ohne
##                        Seil: Rucksackgurt) → unten A = hochklettern → geschafft (Signal team_geschafft, High-Five).
##                        sicht = Spieler, der den Pfeil dorthin sieht (-1 = beide; z. B. nur der Kartenleser).
##   3 Rucksack teilen    rucksack_setzen([[id, name, kg], …]) verteilt neue Dinge auf den Leichteren · traeger(id) -> 0/1 ·
##                        hat(i, id) · geben(von, id) (nur nah beieinander, B) · last_kg(i) · tempo(i) (0.85 … 1.0)
##   4 Rücken an Rücken   geraeusch(text := "", tier := "") - zusammenkommen, jeder schaut in eine andere Richtung
##                        (je ±95°); erst zusammen ist alles abgedeckt → wer in Richtung des Geräuschs schaut, sieht das Tier
##   5 Wer findet mehr    zaehle(i, kat, n := 1) · fundstueck(id, pos, kat, text) (wer zuerst dort ist) · spuren_zeigen(pos, r, s)
##                        kat: funde · tiere · steinmaennchen · spuren · tagebuch · fotos · teamwork · auszeichnungen() am Ende
##   6 Fotowettbewerb     foto(i) (Y): Bild des eigenen Bildschirmteils, Tier darin, Wertung über zb_foto_wertung (A1) ·
##                        beste_fotos() · paint_fotowettbewerb(parent) (am Abend vergleichen)
##   7 Lagerfeuer-Tagebuch lagerfeuer_frage(frage, optionen) · paint_lagerfeuer(parent) · antwort(i, text) ·
##                        tag_speichern(titel, bilder) (Reisetagebuch in zb_ordner(), pro Spielstand) · tagebuch() ·
##                        tagebuch_knopf(parent) · tagebuch_oeffnen() - nichts verlässt den PC
##   8 High-Five          high_five(grund) - beide A innert 0,8 s → kurzer Jubel (Lite: ohne Konfetti)
##   9 Rollen             zb_rollen() vom Wirt (zwei Rollen, je mit Fähigkeit), X = Fähigkeit → zb_faehigkeit(i, rolle_id) ·
##                        rolle(i) · rolle_index(id) · rollen_tauschen() · titel_form(i) ("m" / "f")
##  10 Gummiband          wichtig(id, pos, radius, text, halten := true, max_s := 90.0, sicht := -1) · wichtig_weg(id) ·
##                        haelt() (der Wirt hält solange die Tour / den Ablauf an) · pfeil(i, pos, text, sekunden);
##                        sind die zwei weiter als WEIT m auseinander, zeigt jeder Bildschirmteil einen Pfeil zum anderen.
## Bedienung (grosse Hinweise oben in jedem Bildschirmteil):
##   Controller: A = Team-Knopf (Räuberleiter, Seil, High-Five) · B = weitergeben · X = Fähigkeit · Y = Foto · ◀ ▶ = Ding wählen
##     (der Wirt kann das ändern: zb_pad() -> {"team": "l1", …}; Maggie: LB Team · RB geben · ⬇ Fähigkeit · ⬆ Foto, weil A B X Y
##     dort Maggie und den Teamrätseln gehören)
##   Tastatur Spieler 1: F Team · G geben · V Ding wählen · R Fähigkeit · T Foto
##   Tastatur Spieler 2: N Team · M geben · . Ding wählen · P Fähigkeit · , Foto
## Speichern: zustand() / laden(d) / neu() - der Wirt legt es in seinen Spielstand (Grossvater: R["zb"]). Einstellungen
##   (Rollen getauscht, Titelform er/sie) in user://zwei_bausteine.json. Reisetagebuch: <zb_ordner()>/reisetagebuch.json + bilder/.
## Lite (Quality.lite()): kein Konfetti, Fundstücke ohne Leuchtstrahl, Overlay nur 15 × pro Sekunde neu gezeichnet.
## Spieltest-Haken: Spieltest.ereignis(modus, "fortschritt", {"zwei": art}) bei jedem Team-Erfolg, "abschnitt" beim Tagebuch.
## Steuerbefehl (über den Wirt): op({"k": "zb", "was": state | knopf (p 1/2, knopf team|geben|wahl|faehig|foto) | wissen (a, b) |
##   teamstelle (x, z) | geraeusch | high_five | zaehle (p, kat) | fund (x, z, kat) | antwort (p, value) | frage | tag (titel) |
##   tagebuch | oeffnen | schliessen | tauschen | form (p, value) | rucksack | geben (p, id) | wichtig (x, z) | weg | foto (p, tier)})
##
## ---- Wirt (host): Pflicht ---------------------------------------------------------------------------------------------
##   zb_aktiv() -> bool          zu zweit und gerade unterwegs (sonst ist alles aus)
##   zb_spieler() -> int         Figuren im Spiel: 2 (oder 1, wenn Spieler 2 keine eigene Figur hat)
##   zb_pos(i) -> Vector2        Boden-Position (x, z) von Spieler i (0/1), in den Koordinaten des Wirts
##   zb_yaw(i) -> float          Blickrichtung (Godot rotation.y: 0 = nach -z, vorwärts = (-sin, -cos))
##   zb_name(i) -> String · zb_farbe(i) -> Color · zb_dev(i) -> int (Controller, -1 = Tastatur)
##   zb_rect(i) -> Rect2         Bildschirmteil von Spieler i (gemeinsame Ansicht: beide dasselbe Rechteck)
##   zb_ui() -> Control          wo das Overlay hinkommt (null = noch nicht)
##   zb_welt(q: Vector2, h: float) -> Vector3   Boden-Position + Höhe -> Welt (für Felsblock, Fundstücke)
##   zb_3d() -> Node3D           Eltern-Knoten für die 3D-Dinge · zb_ordner() -> String (user://…, pro Spielstand)
## ---- Wirt: freiwillig (sonst Standard) ---------------------------------------------------------------------------------
##   zb_knoepfe(i) -> bool (true: Controller von i lesen) · zb_eingabe_frei(i) -> bool (true: kein Menü offen) · zb_layer() -> int (1) ·
##   zb_pad() -> {team, geben, faehig, foto: padmap-Knopf}
##   zb_heben(i, h) (Figur auf den Felsen) · zb_setzen(i, q) (Figur dorthin) · zb_bild(i) -> Image · zb_kamera(i) -> Camera3D
##   zb_tiere() -> Array[Node3D] · zb_tier_id(node) -> String · zb_foto_wertung(foto) -> {tier, schaerfe, punkte} · zb_licht() -> 0…1
##   zb_rollen() -> [{id, name, name_f, icon, faehigkeit, text, cd}, {…}] · zb_faehigkeit(i, rolle_id) -> String (Meldung; "" = geht nicht)
##   zb_info(i) -> String (kleine Zeile im Bildschirmteil) · zb_ereignis(art, daten) (Tagebuch, Ton …) · zb_maler() -> Objekt mit
##   _group / _lab / _btn (gleicher Look wie das Bedienfeld; sonst einfache eigene Knöpfe)
##
## ---- Einbau «Maggie und der Bergkristall» (so gebaut in maggie_zwei_team.gd, Anleitung für Änderungen) -------------------
##   Einhänge-Punkte: maggie_zwei.gd _ready (Wirt anlegen), _p1_buttons (B: darf_benutzen), control k "zb";
##   maggie_story.gd _region_tick (_zwei_wartet: das Tor wartet). Die Punkte unten beschreiben, was der Wirt dort tut.
##   1. Im Wirt:              const ZB = preload("res://scripts/zwei_bausteine.gd")
##                           var zb = ZB.new();  zb.setup(self, main, "maggie");  add_child(zb)
##      und die Pflicht-Funktionen oben als Methoden des Wirts. Koordinaten: q = Vector2(welt.x, welt.z),
##      zb_welt(q, h) = Vector3(q.x, main.ground_y(q.x, q.y) + h, q.y), zb_yaw(i) = Figur.rotation.y, zb_3d() = story (main.maggie).
##   2. Rollen: zb_rollen() -> [{"id": "kristall", "name": "Kristall-Hüter", "name_f": "Kristall-Hüterin", "icon": "💎",
##      "faehigkeit": "Kristall-Licht", "text": …, "cd": 25}, {"id": "nase", "name": "Hundeführer", "name_f": "Hundeführerin", "icon": "🐕",
##      "faehigkeit": "Spürnase", …}]; zb_faehigkeit(i, "kristall") -> story.look_into_crystal(), "nase" -> Spuren + Pfeil zur Station.
##   3. Geteiltes Wissen: was der Kristall über nahe Gefahren weiss (story._zk_orte) nur bei Spieler 1: zb.wissen("maggie", [text, ""]);
##      was Maggie riecht (maggie_hund.aktuell()) nur bei Spieler 2: zb.wissen("maggie", ["", text]).
##   4. Räuberleiter: eine Felsstufe zwischen Rastplatz und Tor zb.teamstelle(id, q, T.t("Felsstufe"), 1.6, 0) (nur Spieler 2 als
##      Wanderer); «oben» = zb_setzen über die Stufe drüber. (Als Pflicht-Aufgabe: im Signal team_geschafft story.aufgabe_erledigt(id).)
##   5. Rücken an Rücken: maggie_gefahr.warnung(stufe, art, pos) -> zb.geraeusch(T.t("Da ist etwas!"), art, T.t("einen Wolf"), q) (höchstens alle 150 s).
##   6. Wer findet mehr: zb.fundstueck(id, q, "funde", T.t("Ein Glitzerstein")) für Fundstücke, zb.zaehle(i, "tiere") für liebe Tiere.
##   7. Lagerfeuer: maggie_zwei.rastplatz (erster neuer Rastplatz der Region) -> zb.lagerfeuer_frage(…, true) + zb.lagerfeuer_fenster()
##      (◀ ▶ wählen, LB = so!); story.region_beendet -> zb.tag_speichern(Titel) + zb.neu(); das Fenster hat «📔 Reisetagebuch ansehen».
##   8. High-Five: maggie_zwei.teamraetsel_geloest / gerettet_zwei / fund -> zb.high_five(…).
##   9. Gummiband: Wirt.haelt() (vom Tor-Test in maggie_story): Spieler 2 weiter als 15 m vom Tor -> zb.wichtig("tor", …) und warten (≤ 60 s).
##  10. Rucksack: die Schutzdinge (maggie_gefahr.schutz) -> zb.rucksack_setzen([[id, Name, 0.6], …]); B (Schutzding) nur, wenn Spieler 1
##      es trägt (Wirt.darf_benutzen), sonst gibt Spieler 2 es mit RB weiter.
##   Ohne Bausteine (allein): zb_aktiv() = false - nichts ändert sich.

signal team_geschafft(art: String, id: String)
signal gefunden(i: int, kat: String, id: String)
signal high_five_geschafft(grund: String)

const T = preload("res://scripts/i18n.gd")
const Quality = preload("res://scripts/quality.gd")
const Spieltest = preload("res://scripts/spieltest.gd")

const KATS := ["funde", "tiere", "steinmaennchen", "spuren", "tagebuch", "fotos", "teamwork"]
const KAT_ICON := {"funde": "Fundstücke", "tiere": "Tiere", "steinmaennchen": "Steinmännchen", "spuren": "Spuren", "tagebuch": "Tagebuchseiten",
		"fotos": "Tierfotos", "teamwork": "geholfen"}   # Text statt Emoji (die Schrift hat sie nicht), T.t() beim Anzeigen
# kat -> [Titel (er), Titel (sie), wofür]
const TITEL := {"spuren": ["Spurenleser", "Spurenleserin", "die meisten Spuren gelesen"],
		"tiere": ["Adlerauge", "Adlerauge", "die meisten Tiere entdeckt"],
		"funde": ["Schatzsucher", "Schatzsucherin", "die meisten Fundstücke"],
		"steinmaennchen": ["Steinmännchen-Kenner", "Steinmännchen-Kennerin", "die meisten Steinmännchen"],
		"tagebuch": ["Tagebuch-Hüter", "Tagebuch-Hüterin", "die meisten Tagebuchseiten"],
		"fotos": ["Tierfotograf", "Tierfotografin", "das schönste Tierfoto"],
		"teamwork": ["Seilschaft-Held", "Seilschaft-Heldin", "am meisten geholfen"]}
const TITEL_SONST := ["Treuer Begleiter", "Treue Begleiterin", "immer gut gelaunt dabei"]
const FILE := "user://zwei_bausteine.json"
const NAH := 4.0                     # m: so nah zum Weitergeben, Fundstück aufheben
const TS_R := 6.0                    # m: an der Teamstelle
const WEIT := 60.0                   # m: weiter = Pfeil zum anderen
const HF_DT := 0.8                   # s: High-Five gleichzeitig
const SICHT := 95.0                  # °: so weit sieht jeder nach links und rechts (Rücken an Rücken)
const TIERE_NACHT := [["fuchs", "einen Fuchs"], ["reh", "ein Reh"], ["dachs", "einen Dachs"], ["eule", "eine Eule"], ["hase", "einen Hasen"]]

var host
var main
var modus := "abenteuer"
var _ov: Control
var _pp: Array = []                  # per player: {panel, prompt, wpanel, wissen, info}
var _jubel: Label
var _ov_t := 0.0
# state
var zaehler: Array = [{}, {}]
var hf_n := 0
var _wissen := {}                    # id -> [t0, t1]
var _prompt: Array = [{}, {}]        # {text, until, prio}
var _pfeile: Array = [[], []]        # [{pos, text, until, col}]
var _wichtig := {}                   # id -> {pos, r, text, halten, t0, max_s, sicht}
var _ts := {}                        # id -> {pos, h, text, phase, helfer, klett, node, rope, sicht, t0, aktiv}
var _funde := {}                     # id -> {pos, kat, text, node, bis}
var _traeger := {}                   # item id -> 0/1
var _items := {}                     # item id -> [name, kg]
var _sel: Array = [0, 0]
var _ruecken := {}
var _hf := {}                        # {grund, until}
var _last_team: Array = [-9.0, -9.0]
var _cd: Array = [0.0, 0.0]
var _fotos: Array = [[], []]         # today: [{file, punkte, tier, schaerfe}]
var _tiere_heute: Array = [{}, {}]
var _lf := {}                        # campfire: {frage, optionen, antworten [a, b]}
var tausch := false
var form: Array = ["m", "f"]
var _keys_prev := {}
var _inj: Array = [[], []]
var _viewer: CanvasLayer
var _rng := RandomNumberGenerator.new()


func setup(h, m, mod := "abenteuer") -> void:
	host = h
	main = m
	modus = mod
	_rng.randomize()
	_prefs_load()


func now() -> float:
	return Time.get_ticks_msec() / 1000.0


func _lite() -> bool:
	return Quality.lite()


static func sauber(t: String) -> String:
	"""without the colour emoji (the font of the simulator has none - they would be empty boxes in the big hints)"""
	var o := ""
	for k in range(t.length()):
		var c := t.unicode_at(k)
		if c >= 0x1F000 or (c >= 0x2300 and c <= 0x23FF) or c == 0xFE0F or c == 0x200D or (c >= 0x2B00 and c <= 0x2BFF) or (c >= 0x24B6 and c <= 0x24E9):
			continue
		o += t[k]
	return o.replace("  ", " ").strip_edges()


func _h(m: String, args: Array = [], def = null):
	if host != null and host.has_method(m):
		return host.callv(m, args)
	return def


func aktiv() -> bool:
	return host != null and bool(_h("zb_aktiv", [], false))


func n_fig() -> int:
	return clampi(int(_h("zb_spieler", [], 2)), 1, 2)


func pos(i: int) -> Vector2:
	return _h("zb_pos", [i], Vector2.ZERO)


func yaw(i: int) -> float:
	return float(_h("zb_yaw", [i], 0.0))


func nm(i: int) -> String:
	return str(_h("zb_name", [i], "Spieler %d" % (i + 1)))


func col(i: int) -> Color:
	return _h("zb_farbe", [i], Color.WHITE)


func abstand() -> float:
	return pos(0).distance_to(pos(1)) if n_fig() == 2 else 0.0


# =======================================================================================================================
# saving
# =======================================================================================================================
func neu() -> void:
	"""a new run: nothing of the last one stays (the travel diary file stays)"""
	zaehler = [{}, {}]
	hf_n = 0
	_wissen = {}
	_prompt = [{}, {}]
	_pfeile = [[], []]
	_wichtig = {}
	for id in _ts.keys():
		teamstelle_weg(id)
	for id in _funde.keys():
		fund_weg(id)
	_traeger = {}
	_items = {}
	_ruecken = {}
	_hf = {}
	_fotos = [[], []]
	_tiere_heute = [{}, {}]
	_lf = {}
	for i in range(2):
		_h("zb_heben", [i, 0.0])


func zustand() -> Dictionary:
	return {"zaehler": zaehler.duplicate(true), "hf": hf_n, "traeger": _traeger.duplicate(), "fotos": _fotos.duplicate(true),
			"tiere": _tiere_heute.duplicate(true), "lf": _lf.duplicate(true)}


func laden(d: Dictionary) -> void:
	neu()
	if d.get("zaehler") is Array and (d["zaehler"] as Array).size() == 2:
		zaehler = (d["zaehler"] as Array).duplicate(true)
	hf_n = int(d.get("hf", 0))
	if d.get("traeger") is Dictionary:
		for k in d["traeger"]:
			_traeger[str(k)] = clampi(int(d["traeger"][k]), 0, 1)
	if d.get("fotos") is Array and (d["fotos"] as Array).size() == 2:
		_fotos = (d["fotos"] as Array).duplicate(true)
	if d.get("tiere") is Array and (d["tiere"] as Array).size() == 2:
		_tiere_heute = (d["tiere"] as Array).duplicate(true)
	if d.get("lf") is Dictionary:
		_lf = (d["lf"] as Dictionary).duplicate(true)


func _prefs_load() -> void:
	if not FileAccess.file_exists(FILE):
		return
	var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
	if d is Dictionary:
		tausch = bool(d.get("tausch", false))
		if d.get("form") is Array and (d["form"] as Array).size() == 2:
			form = [str(d["form"][0]), str(d["form"][1])]


func _prefs_save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"tausch": tausch, "form": form}))


# =======================================================================================================================
# 9 roles
# =======================================================================================================================
func _rollen() -> Array:
	var r = _h("zb_rollen", [], [])
	if r is Array and (r as Array).size() == 2:
		return r
	return [{"id": "a", "name": "Spieler 1", "icon": "1", "faehigkeit": "", "text": "", "cd": 10}, {"id": "b", "name": "Spieler 2", "icon": "2", "faehigkeit": "", "text": "", "cd": 10}]


func rolle(i: int) -> Dictionary:
	return _rollen()[(i + (1 if tausch else 0)) % 2]


func rolle_index(id: String) -> int:
	for i in range(2):
		if str(rolle(i).get("id", "")) == id:
			return i
	return 0


func rolle_name(i: int) -> String:
	var r := rolle(i)
	return T.t(str(r.get("name_f", r.get("name", "")) if titel_form(i) == "f" else r.get("name", "")))


func rollen_tauschen() -> void:
	tausch = not tausch
	_prefs_save()


func titel_form(i: int) -> String:
	return str(form[clampi(i, 0, 1)])


func set_form(i: int, v: String) -> void:
	form[clampi(i, 0, 1)] = "f" if v == "f" else "m"
	_prefs_save()


func _faehigkeit(i: int) -> void:
	var r := rolle(i)
	if str(r.get("faehigkeit", "")) == "":
		return
	if now() < float(_cd[i]):
		say(i, T.t("%s: noch %d s") % [T.t(str(r["faehigkeit"])), int(ceil(float(_cd[i]) - now()))], 2.0)
		return
	var msg := str(_h("zb_faehigkeit", [i, str(r.get("id", ""))], ""))
	if msg == "":
		say(i, T.t("%s geht hier gerade nicht.") % T.t(str(r["faehigkeit"])), 2.5)
		return
	_cd[i] = now() + float(r.get("cd", 12))
	say(i, "%s %s" % [str(r.get("icon", "")), msg], 5.0, 2)


# =======================================================================================================================
# 1 shared knowledge
# =======================================================================================================================
func wissen(id: String, texte: Array) -> void:
	_wissen[id] = [str(texte[0]) if texte.size() > 0 else "", str(texte[1]) if texte.size() > 1 else ""]


func wissen_weg(id := "") -> void:
	if id == "":
		_wissen = {}
	else:
		_wissen.erase(id)


func _wissen_text(i: int) -> String:
	var L: Array = []
	for id in _wissen:
		var t := str(_wissen[id][i])
		if t != "":
			L.append(t)
	return "\n".join(L)


# =======================================================================================================================
# messages and arrows
# =======================================================================================================================
func say(i: int, text: String, secs := 4.0, prio := 1) -> void:
	"""a big line at the top of player i's part (-1 = both)"""
	for j in ([0, 1] if i < 0 else [i]):
		var p: Dictionary = _prompt[j]
		if not p.is_empty() and now() < float(p["until"]) and int(p["prio"]) > prio:
			continue
		_prompt[j] = {"text": text, "until": now() + secs, "prio": prio}


func pfeil(i: int, q: Vector2, text: String, secs := 6.0) -> void:
	for j in ([0, 1] if i < 0 else [i]):
		var L: Array = _pfeile[j]
		L = L.filter(func(a): return str(a["text"]) != text)
		L.append({"pos": q, "text": text, "until": now() + secs, "col": Color("#ffd166")})
		_pfeile[j] = L


# =======================================================================================================================
# 10 rubber band
# =======================================================================================================================
func wichtig(id: String, q: Vector2, radius := 10.0, text := "", halten := true, max_s := 90.0, sicht := -1) -> void:
	if _wichtig.has(id):
		_wichtig[id]["pos"] = q
		return
	_wichtig[id] = {"pos": q, "r": radius, "text": text, "halten": halten, "t0": now(), "max_s": max_s, "sicht": sicht}


func wichtig_weg(id: String) -> void:
	_wichtig.erase(id)


func haelt() -> bool:
	if not aktiv() or n_fig() < 2:
		return false
	for id in _wichtig:
		var w: Dictionary = _wichtig[id]
		if bool(w["halten"]) and now() - float(w["t0"]) < float(w["max_s"]) and not _beide_da(w):
			return true
	for id in _ts:
		var s: Dictionary = _ts[id]
		if bool(s["aktiv"]) and str(s["phase"]) != "fertig" and now() - float(s["t0"]) < 240.0:
			return true                                  # a team place is being climbed: the tour waits
	return false


func _beide_da(w: Dictionary) -> bool:
	var q: Vector2 = w["pos"]
	for i in range(n_fig()):
		if pos(i).distance_to(q) > float(w["r"]):
			return false
	return true


func _gummiband_tick() -> void:
	if n_fig() < 2:
		return
	var t := now()
	for id in _wichtig.keys():
		var w: Dictionary = _wichtig[id]
		if t - float(w["t0"]) > float(w["max_s"]) + 2.0:
			_wichtig.erase(id)
			continue
		var q: Vector2 = w["pos"]
		var da: Array = [pos(0).distance_to(q) <= float(w["r"]), pos(1).distance_to(q) <= float(w["r"])]
		for i in range(2):
			var o := 1 - i
			if da[i] and not da[o]:
				say(i, T.t("⏳ Warte auf %s") % nm(o), 0.5, 0)
				_pf_now(i, pos(o), "%s %d m" % [nm(o), int(pos(i).distance_to(pos(o)))])
			elif not da[i]:
				var see := int(w.get("sicht", -1))
				if see < 0 or see == i or da[o]:
					_pf_now(i, q, "%s %d m" % [str(w["text"]), int(pos(i).distance_to(q))])
				else:
					say(i, T.t("Frag %s, wo es hingeht!") % nm(see), 0.5, 0)
	if abstand() > WEIT:
		for i in range(2):
			_pf_now(i, pos(1 - i), "%s %d m" % [nm(1 - i), int(abstand())])


var _pf_frame: Array = [[], []]


func _pf_now(i: int, q: Vector2, text: String) -> void:
	"""an arrow for this frame only (rubber band, team place)"""
	(_pf_frame[i] as Array).append({"pos": q, "text": text, "col": col(1 - i) if text.begins_with(nm(1 - i)) else Color("#ffd166")})


# =======================================================================================================================
# 2 team place (Räuberleiter)
# =======================================================================================================================
func teamstelle(id: String, q: Vector2, text := "", hoehe := 2.6, sicht := -1) -> void:
	if _ts.has(id):
		return
	var s := {"pos": q, "h": hoehe, "text": text if text != "" else T.t("Felsstufe"), "phase": "warten", "helfer": -1, "klett": -1,
			"node": null, "rope": null, "sicht": sicht, "t0": now(), "aktiv": false, "fertig_t": 0.0}
	_ts[id] = s
	_ts_build(s)


func teamstelle_aktiv(id: String) -> void:
	if _ts.has(id) and not bool(_ts[id]["aktiv"]) and str(_ts[id]["phase"]) != "fertig":
		_ts[id]["aktiv"] = true
		_ts[id]["t0"] = now()
		var s: Dictionary = _ts[id]
		wichtig("ts_" + id, s["pos"], TS_R, "🧗 " + str(s["text"]), false, 240.0, int(s["sicht"]))
		var see := int(s["sicht"])
		for i in range(2):
			if see < 0 or see == i:
				say(i, T.t("🧗 %s: nur zu zweit! Geht beide hin.") % str(s["text"]), 6.0, 2)
			else:
				say(i, T.t("🧗 %s weiss, wo es eine Felsstufe gibt - frag nach!") % nm(see), 6.0, 2)


func teamstelle_weg(id: String) -> void:
	if not _ts.has(id):
		return
	var s: Dictionary = _ts[id]
	if s["node"] != null and is_instance_valid(s["node"]):
		(s["node"] as Node).queue_free()
	for i in range(2):
		if int(s["helfer"]) == i or int(s["klett"]) == i:
			_h("zb_heben", [i, 0.0])
	_wichtig.erase("ts_" + id)
	_ts.erase(id)


func _ts_build(s: Dictionary) -> void:
	var par = _h("zb_3d", [], null)
	if par == null:
		return
	var n := Node3D.new()
	var lay := int(_h("zb_layer", [], 1))
	var rock := MeshInstance3D.new()
	var bx := BoxMesh.new()
	bx.size = Vector3(3.4, float(s["h"]), 2.6)
	rock.mesh = bx
	rock.position.y = float(s["h"]) / 2.0
	var mt := StandardMaterial3D.new()
	mt.albedo_color = Color(0.48, 0.46, 0.43)
	mt.roughness = 0.95
	rock.material_override = mt
	rock.layers = lay
	n.add_child(rock)
	var rope := MeshInstance3D.new()
	var cy := CylinderMesh.new()
	cy.top_radius = 0.035
	cy.bottom_radius = 0.035
	cy.height = float(s["h"])
	rope.mesh = cy
	rope.position = Vector3(0, float(s["h"]) / 2.0, 1.35)
	var mr := StandardMaterial3D.new()
	mr.albedo_color = Color(0.85, 0.55, 0.15)
	rope.material_override = mr
	rope.layers = lay
	rope.visible = false
	n.add_child(rope)
	var lb := Label3D.new()
	lb.text = str(s["text"])
	lb.font_size = 64
	lb.pixel_size = 0.01
	lb.position.y = float(s["h"]) + 1.3
	lb.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lb.outline_size = 10
	lb.modulate = Color("#ffd166")
	lb.layers = lay
	n.add_child(lb)
	(par as Node).add_child(n)
	n.global_position = _h("zb_welt", [s["pos"], 0.0], Vector3.ZERO)
	s["node"] = n
	s["rope"] = rope


func _ts_tick() -> void:
	for id in _ts.keys():
		var s: Dictionary = _ts[id]
		var q: Vector2 = s["pos"]
		var ph := str(s["phase"])
		if ph == "fertig":
			if float(s["fertig_t"]) > 0.0 and now() > float(s["fertig_t"]):
				s["fertig_t"] = 0.0
				for i in range(2):
					_h("zb_heben", [i, 0.0])             # both jump down again
			continue
		var near: Array = [pos(0).distance_to(q) < 12.0 if n_fig() > 0 else false, pos(1).distance_to(q) < 12.0 if n_fig() > 1 else false]
		if not bool(s["aktiv"]) and (near[0] or near[1]):
			teamstelle_aktiv(id)
		if not bool(s["aktiv"]):
			continue
		var da: Array = [pos(0).distance_to(q) <= TS_R, pos(1).distance_to(q) <= TS_R]
		var hf := int(s["helfer"])
		var kl := int(s["klett"])
		match ph:
			"warten":
				if da[0] and da[1]:
					s["phase"] = "bereit"
				# (the rubber band shows the way)
			"bereit":
				for i in range(2):
					say(i, T.t("🧗 Räuberleiter! Wer hilft hoch? %s drücken") % _k(i, "team"), 0.4, 3)
			"hoch":
				say(hf, T.t("🤲 Du machst die Räuberleiter - %s steigt hoch") % nm(kl), 0.4, 3)
				say(kl, T.t("⬆ %s: hochsteigen!") % _k(kl, "team"), 0.4, 3)
			"oben":
				if pos(kl).distance_to(q) > 2.8:
					_h("zb_heben", [kl, 0.0])            # walked off the rock: down again
					s["phase"] = "hoch"
					say(-1, T.t("Runtergesprungen - nochmals!"), 2.5, 3)
					continue
				var who := traeger("seil")
				if _items.has("seil") and who == hf:
					say(hf, T.t("🪢 Du hast das Seil: %s = %s geben") % [_k(hf, "geben"), nm(kl)], 0.4, 3)
					say(kl, T.t("Oben! %s hat das Seil - warte") % nm(hf), 0.4, 3)
				else:
					var was := T.t("Seil") if _items.has("seil") else T.t("Rucksackgurt")
					say(kl, T.t("Oben! %s: %s hinunterwerfen") % [_k(kl, "team"), was], 0.4, 3)
					say(hf, T.t("⏳ %s ist oben - gleich kommt das Seil") % nm(kl), 0.4, 3)
			"seil":
				say(hf, T.t("🪢 %s: am Seil hochklettern!") % _k(hf, "team"), 0.4, 3)
				say(kl, T.t("Halt das Seil fest - %s klettert") % nm(hf), 0.4, 3)


func _ts_press(i: int) -> bool:
	"""the team button at a team place - true = used"""
	for id in _ts:
		var s: Dictionary = _ts[id]
		if not bool(s["aktiv"]):
			continue
		var q: Vector2 = s["pos"]
		var ph := str(s["phase"])
		var o := 1 - i
		match ph:
			"bereit":
				if pos(i).distance_to(q) <= TS_R:
					s["helfer"] = i
					s["klett"] = o
					s["phase"] = "hoch"
					figur_aktion(i, "aufheben", 1.8)                # anim_mensch.gd: the hands down as a step
					_rumble([i])
					return true
			"hoch":
				if i == int(s["klett"]):
					_h("zb_setzen", [i, q])
					_h("zb_heben", [i, float(s["h"])])
					figur_aktion(i, "klettern", 1.6)
					s["phase"] = "oben"
					_rumble([0, 1])
					return true
			"oben":
				if i == int(s["klett"]) and not (_items.has("seil") and traeger("seil") == int(s["helfer"])):
					if s["rope"] != null and is_instance_valid(s["rope"]):
						(s["rope"] as Node3D).visible = true
					s["phase"] = "seil"
					return true
			"seil":
				if i == int(s["helfer"]):
					_h("zb_setzen", [i, q + Vector2(0.7, 0.0)])
					_h("zb_heben", [i, float(s["h"])])
					figur_aktion(i, "klettern", 2.2)               # up the rope
					s["phase"] = "fertig"
					s["fertig_t"] = now() + 7.0
					wichtig_weg("ts_" + str(id))
					zaehle(i, "teamwork")
					zaehle(o, "teamwork")
					say(-1, T.t("🎉 Geschafft - zusammen oben!"), 4.0, 4)
					_ereignis("raeuberleiter", {"id": str(id), "helfer": nm(int(s["klett"])), "text": str(s["text"])})
					team_geschafft.emit("raeuberleiter", str(id))
					high_five("raeuberleiter")
					return true
	return false


# =======================================================================================================================
# 3 backpack
# =======================================================================================================================
func rucksack_setzen(items: Array) -> void:
	"""the things of the run [[id, name, kg], …]: new ones go to the lighter one, gone ones are forgotten"""
	var seen := {}
	for e in items:
		var id := str(e[0])
		seen[id] = true
		_items[id] = [str(e[1]), float(e[2])]
	for id in _items.keys():
		if not seen.has(id):
			_items.erase(id)
			_traeger.erase(id)
	var neue: Array = []
	for id in _items:
		if not _traeger.has(id):
			neue.append(id)
	neue.sort_custom(func(a, b): return float(_items[a][1]) > float(_items[b][1]))
	for id in neue:
		_traeger[id] = 0 if last_kg(0) <= last_kg(1) else 1


func traeger(id: String) -> int:
	return int(_traeger.get(id, -1))


func hat(i: int, id: String) -> bool:
	return traeger(id) == i


func items_von(i: int) -> Array:
	var L: Array = []
	for id in _items:
		if traeger(str(id)) == i:
			L.append(str(id))
	L.sort()
	return L


func last_kg(i: int) -> float:
	var kg := 0.0
	for id in _items:
		if int(_traeger.get(id, -1)) == i:
			kg += float(_items[id][1])
	return snappedf(kg, 0.1)


func tempo(i: int) -> float:
	"""the one with much more weight walks a bit slower (at most 15 %)"""
	if not aktiv() or n_fig() < 2:
		return 1.0
	return 1.0 - clampf((last_kg(i) - last_kg(1 - i)) / 25.0, 0.0, 0.15)


func geben(von: int, id: String) -> bool:
	if traeger(id) != von:
		return false
	if n_fig() == 2 and abstand() > NAH:
		say(von, T.t("Zu weit weg - geh zu %s (%d m)") % [nm(1 - von), int(abstand())], 2.5)
		return false
	_traeger[id] = 1 - von
	var name_ := str(_items.get(id, [id])[0])
	say(von, T.t("🎒 %s an %s gegeben") % [name_, nm(1 - von)], 3.0)
	say(1 - von, T.t("🎒 %s gibt dir: %s") % [nm(von), name_], 3.0)
	_rumble([1 - von])
	return true


func _sel_item(i: int) -> String:
	var L := items_von(i)
	if L.is_empty():
		return ""
	return str(L[posmod(int(_sel[i]), L.size())])


# =======================================================================================================================
# 4 back to back
# =======================================================================================================================
func geraeusch(text := "", tier := "", wen := "", quelle := Vector2.INF) -> void:
	"""a noise: wen = what one sees then (T.t() already), quelle = where it is (otherwise a random direction)"""
	if not aktiv() or n_fig() < 2 or not _ruecken.is_empty():
		return
	var e: Array = TIERE_NACHT[_rng.randi() % TIERE_NACHT.size()]
	if tier != "":
		for x in TIERE_NACHT:
			if str(x[0]) == tier:
				e = x
	var a := _rng.randf_range(-PI, PI)
	if quelle != Vector2.INF:
		var to: Vector2 = quelle - (pos(0) + pos(1)) / 2.0
		a = atan2(-to.x, -to.y)
	_ruecken = {"t0": now(), "src": a, "tier": tier if tier != "" else str(e[0]), "wen": wen if wen != "" else T.t(str(e[1])), "ok_t": 0.0,
			"text": text if text != "" else T.t("Ein Knacken im Dunkeln!")}
	say(-1, "👂 " + str(_ruecken["text"]) + " " + T.t("Rücken an Rücken!"), 4.0, 3)
	_rumble([0, 1])


func abdeckung() -> float:
	"""how much of the circle (°) the two see together (each ±SICHT)"""
	var n := 0
	for k in range(72):
		var a := -PI + k * TAU / 72.0
		for i in range(n_fig()):
			if absf(wrapf(a - yaw(i), -PI, PI)) <= deg_to_rad(SICHT):
				n += 1
				break
	return n * 5.0


func ruecken_quelle() -> Vector2:
	"""where the noise is (for the ability «orten»): 25 m in its direction from the middle"""
	if _ruecken.is_empty():
		return Vector2.INF
	var a := float(_ruecken["src"])
	return (pos(0) + pos(1)) / 2.0 + Vector2(-sin(a), -cos(a)) * 25.0


func _ruecken_tick(dt: float) -> void:
	if _ruecken.is_empty():
		return
	var t := now()
	if t - float(_ruecken["t0"]) > 45.0:
		say(-1, T.t("Das Geräusch ist weg. Was das wohl war?"), 4.0, 3)
		_ruecken = {}
		return
	if abstand() > 10.0:
		for i in range(2):
			say(i, T.t("👂 Rücken an Rücken! Komm zu %s") % nm(1 - i), 0.4, 3)
			_pf_now(i, pos(1 - i), "%s %d m" % [nm(1 - i), int(abstand())])
		_ruecken["ok_t"] = 0.0
		return
	var cov := abdeckung()
	if cov >= 340.0:
		_ruecken["ok_t"] = float(_ruecken["ok_t"]) + dt
	else:
		_ruecken["ok_t"] = 0.0
	for i in range(2):
		say(i, (T.t("👀 Schau in die andere Richtung als %s! Zusammen: %d°") % [nm(1 - i), int(cov)]) if cov < 340.0 else T.t("👀 Gut so - ihr seht alles. Ruhig bleiben …"), 0.4, 3)
	if float(_ruecken["ok_t"]) >= 2.5:
		var a := float(_ruecken["src"])
		var best := 0
		if absf(wrapf(a - yaw(1), -PI, PI)) < absf(wrapf(a - yaw(0), -PI, PI)):
			best = 1
		zaehle(best, "tiere")
		say(-1, T.t("🔦 %s sieht es: %s!") % [nm(best), str(_ruecken["wen"])], 5.0, 4)
		_ereignis("ruecken", {"wer": nm(best), "tier": str(_ruecken["tier"]), "wen": str(_ruecken["wen"])})
		team_geschafft.emit("ruecken", str(_ruecken["tier"]))
		_ruecken = {}
		high_five("ruecken")


# =======================================================================================================================
# 5 who finds more
# =======================================================================================================================
func zaehle(i: int, kat: String, n := 1) -> void:
	i = clampi(i, 0, 1)
	var z: Dictionary = zaehler[i]
	z[kat] = int(z.get(kat, 0)) + n


func fundstueck(id: String, q: Vector2, kat: String, text: String) -> void:
	if _funde.has(id):
		return
	var e := {"pos": q, "kat": kat, "text": text, "node": null, "bis": 0.0}
	_funde[id] = e
	var par = _h("zb_3d", [], null)
	if par == null:
		return
	var n := Node3D.new()
	var lay := int(_h("zb_layer", [], 1))
	var lite := _lite()
	match kat:
		"steinmaennchen":
			for k in range(3):
				var mi := MeshInstance3D.new()
				var sp := SphereMesh.new()
				sp.radius = 0.32 - k * 0.07
				sp.height = 0.32 - k * 0.04
				sp.radial_segments = 8
				sp.rings = 4
				mi.mesh = sp
				mi.position.y = 0.14 + k * 0.27
				mi.material_override = _mat(Color(0.62, 0.6, 0.56), false)
				mi.layers = lay
				n.add_child(mi)
		"spuren":
			for k in range(4):
				var mi2 := MeshInstance3D.new()
				var cy := CylinderMesh.new()
				cy.top_radius = 0.07
				cy.bottom_radius = 0.07
				cy.height = 0.02
				cy.radial_segments = 8
				mi2.mesh = cy
				mi2.position = Vector3(0.12 * (1 if k % 2 == 0 else -1), 0.02, -0.45 * k)
				mi2.material_override = _mat(Color(0.95, 0.75, 0.3), true)
				mi2.layers = lay
				n.add_child(mi2)
			n.visible = false                               # only the scout sees tracks (ability)
		_:
			var mi3 := MeshInstance3D.new()
			var gm := SphereMesh.new()
			gm.radius = 0.2
			gm.height = 0.34
			gm.radial_segments = 6
			gm.rings = 2
			mi3.mesh = gm
			mi3.position.y = 0.35
			mi3.material_override = _mat(Color(1.0, 0.82, 0.3), true)
			mi3.layers = lay
			n.add_child(mi3)
			if not lite:
				var beam := MeshInstance3D.new()
				var bc := CylinderMesh.new()
				bc.top_radius = 0.03
				bc.bottom_radius = 0.06
				bc.height = 2.2
				bc.radial_segments = 6
				beam.mesh = bc
				beam.position.y = 1.4
				beam.material_override = _mat(Color(1.0, 0.85, 0.4), true)
				beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				beam.layers = lay
				n.add_child(beam)
	(par as Node).add_child(n)
	n.global_position = _h("zb_welt", [q, 0.0], Vector3.ZERO)
	e["node"] = n


func _mat(c: Color, glow: bool) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = c
	m.roughness = 0.9
	if glow:
		m.emission_enabled = true
		m.emission = c
		m.emission_energy_multiplier = 1.4
	return m


func fund_weg(id: String) -> void:
	if not _funde.has(id):
		return
	var n = _funde[id]["node"]
	if n != null and is_instance_valid(n):
		(n as Node).queue_free()
	_funde.erase(id)


func spuren_zeigen(q: Vector2, r := 45.0, secs := 25.0) -> int:
	var k := 0
	for id in _funde:
		var e: Dictionary = _funde[id]
		if str(e["kat"]) == "spuren" and (e["pos"] as Vector2).distance_to(q) <= r:
			e["bis"] = now() + secs
			k += 1
	return k


func naechster_fund(q: Vector2) -> Dictionary:
	var best := {}
	var bd := INF
	for id in _funde:
		var e: Dictionary = _funde[id]
		if str(e["kat"]) == "spuren" and now() > float(e["bis"]):
			continue
		var d := (e["pos"] as Vector2).distance_to(q)
		if d < bd:
			bd = d
			best = e
	return best


func _funde_tick() -> void:
	var t := now()
	for id in _funde.keys():
		var e: Dictionary = _funde[id]
		var vis := str(e["kat"]) != "spuren" or t < float(e["bis"])
		if e["node"] != null and is_instance_valid(e["node"]):
			(e["node"] as Node3D).visible = vis
			if vis and str(e["kat"]) == "funde":
				(e["node"] as Node3D).rotation.y = fmod(t * 1.2, TAU)
		if not vis:
			continue
		for i in range(n_fig()):
			if pos(i).distance_to(e["pos"]) <= NAH:
				zaehle(i, str(e["kat"]))
				figur_aktion(i, "aufheben")                      # anim_mensch.gd: bends down and picks it up
				say(i, T.t("Gefunden: %s") % str(e["text"]), 3.5, 2)
				if n_fig() == 2:
					say(1 - i, T.t("%s hat zuerst gefunden: %s") % [nm(i), str(e["text"])], 3.0, 1)
				_ereignis("fund", {"wer": nm(i), "kat": str(e["kat"]), "text": str(e["text"])})
				gefunden.emit(i, str(e["kat"]), str(id))
				fund_weg(str(id))
				break


func auszeichnungen() -> Array:
	"""friendly titles: [[i (-1 = both), Titel, wofür], …] - everybody gets at least one"""
	var out: Array = []
	var bf := beste_fotos()
	var any: Array = [false, false]
	for kat in ["spuren", "tiere", "funde", "steinmaennchen", "tagebuch", "fotos", "teamwork"]:
		var a := 0.0
		var b := 0.0
		if kat == "fotos":
			a = float(bf[0].get("punkte", 0)) if not (bf[0] as Dictionary).is_empty() and str(bf[0].get("tier", "")) != "" else 0.0
			b = float(bf[1].get("punkte", 0)) if not (bf[1] as Dictionary).is_empty() and str(bf[1].get("tier", "")) != "" else 0.0
		else:
			a = float(zaehler[0].get(kat, 0))
			b = float(zaehler[1].get(kat, 0)) if n_fig() == 2 or kat in ["tagebuch", "fotos"] else 0.0
		if a <= 0.0 and b <= 0.0:
			continue
		var tt: Array = TITEL[kat]
		if a == b:
			out.append([-1, T.t(str(tt[0])) + " / " + T.t(str(tt[1])) if titel_form(0) != titel_form(1) else T.t(str(tt[1 if titel_form(0) == "f" else 0])), T.t(str(tt[2]))])
			any = [true, true]
		else:
			var w := 0 if a > b else 1
			out.append([w, T.t(str(tt[1 if titel_form(w) == "f" else 0])), T.t(str(tt[2]))])
			any[w] = true
	for i in range(2):
		if not any[i]:
			out.append([i, T.t(str(TITEL_SONST[1 if titel_form(i) == "f" else 0])), T.t(str(TITEL_SONST[2]))])
	return out


# =======================================================================================================================
# 6 photo contest
# =======================================================================================================================
func foto(i: int, tier_test := "") -> Dictionary:
	"""Y: a picture of player i's view - which animal is in it, how good (A1 rating via the host)"""
	var img = _h("zb_bild", [i], null)
	var cam = _h("zb_kamera", [i], null)
	var f := {"tier": "", "dist": 30.0, "px": 10.0, "speed": 0.0, "licht": float(_h("zb_licht", [], 1.0)), "mw": false}
	var best := -1.0
	if cam is Camera3D and (cam as Camera3D).is_inside_tree():
		var c: Camera3D = cam
		var vh := maxf(1.0, c.get_viewport().get_visible_rect().size.y)
		for a in _h("zb_tiere", [], []):
			if a == null or not is_instance_valid(a) or not (a is Node3D):
				continue
			var p: Vector3 = (a as Node3D).global_position
			if c.is_position_behind(p) or not c.is_position_in_frustum(p + Vector3(0, 0.3, 0)):
				continue
			var d := c.global_position.distance_to(p)
			if d > 90.0:
				continue
			var y0 := c.unproject_position(p).y
			var y1 := c.unproject_position(p + Vector3(0, 0.8, 0)).y
			var px := absf(y1 - y0) / vh * 720.0                 # as tall as in a 720-line picture
			var off := (c.unproject_position(p) / c.get_viewport().get_visible_rect().size - Vector2(0.5, 0.5)).length()
			var sc := px * (1.2 - off)
			if sc > best:
				best = sc
				f["tier"] = str(_h("zb_tier_id", [a], ""))
				f["dist"] = snappedf(d, 0.1)
				f["px"] = snappedf(px, 0.1)
				f["speed"] = float(a.get("cur_speed")) if "cur_speed" in a else 0.0
	if tier_test != "":
		f["tier"] = tier_test
		f["dist"] = 12.0
		f["px"] = 60.0
	var w = _h("zb_foto_wertung", [f], null)
	if not w is Dictionary:
		w = {"tier": f["tier"], "schaerfe": 0.5, "punkte": 20 if str(f["tier"]) != "" else 0}
	var e := {"tier": str(f["tier"]), "punkte": int(w.get("punkte", 0)) if str(f["tier"]) != "" else 0, "schaerfe": float(w.get("schaerfe", 0.0)),
			"file": "", "name": nm(i), "zeit": Time.get_time_string_from_system().substr(0, 5)}
	if img is Image and not (img as Image).is_empty():
		var im: Image = (img as Image).duplicate()
		if im.is_compressed():
			im.decompress()
		if im.get_width() > 480:
			im.resize(480, int(480.0 * im.get_height() / im.get_width()), Image.INTERPOLATE_BILINEAR)
		var dir := _dir() + "/bilder"
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(dir))
		var fn := "%s/foto_%d_p%d.jpg" % [dir, int(Time.get_unix_time_from_system() * 1000.0) % 1000000000, i + 1]
		if im.save_jpg(fn, 0.82) == OK:
			e["file"] = fn
	var L: Array = _fotos[i]
	L.append(e)
	L.sort_custom(func(a, b): return int(a["punkte"]) > int(b["punkte"]))
	for old in L.slice(4):
		if str(old.get("file", "")) != "" and not _im_tagebuch(str(old["file"])):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(str(old["file"])))
	_fotos[i] = L.slice(0, 4)
	if e["tier"] != "":
		zaehle(i, "fotos")
		if not (_tiere_heute[i] as Dictionary).has(e["tier"]):
			_tiere_heute[i][e["tier"]] = true
			zaehle(i, "tiere")
		say(i, T.t("📸 Tierfoto: %d Punkte") % int(e["punkte"]), 3.5, 2)
	else:
		say(i, T.t("📸 Foto gemacht - aber kein Tier im Bild"), 3.0, 2)
	_ereignis("foto", e)
	return e


func beste_fotos() -> Array:
	var out: Array = [{}, {}]
	for i in range(2):
		if not (_fotos[i] as Array).is_empty():
			out[i] = _fotos[i][0]
	return out


func _im_tagebuch(fn: String) -> bool:
	return false                                         # (photos in the diary are copied there - the day list may delete its own)


# =======================================================================================================================
# 7 campfire diary
# =======================================================================================================================
func lagerfeuer_frage(frage: String, optionen: Array, neu_ := false) -> void:
	if not neu_ and not _lf.is_empty() and str(_lf.get("frage", "")) == frage:
		return
	_lf = {"frage": frage, "optionen": optionen.slice(0, 5), "antworten": ["", ""]}


func antwort(i: int, text: String) -> void:
	if _lf.is_empty():
		lagerfeuer_frage(T.t("Was war heute das Schönste?"), [])
	(_lf["antworten"] as Array)[clampi(i, 0, 1)] = text.strip_edges().left(80)


func _dir() -> String:
	return str(_h("zb_ordner", [], "user://zwei_tagebuch/platz_1/spiel"))


func tagebuch() -> Array:
	var p := _dir() + "/reisetagebuch.json"
	if not FileAccess.file_exists(p):
		return []
	var d = JSON.parse_string(FileAccess.get_file_as_string(p))
	return d if d is Array else []


func tag_speichern(titel: String, bilder: Array = []) -> Dictionary:
	"""the day goes into the travel diary (user://, per save slot) - with the answers, the best photos, the pictures, the titles"""
	var dir := _dir()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(dir + "/bilder"))
	var stamp := int(Time.get_unix_time_from_system())
	var pics: Array = []
	for b in bilder.slice(0, 4):
		var src := str(b)
		if src == "" or not FileAccess.file_exists(src):
			continue
		var dst := "%s/bilder/tag_%d_%d.%s" % [dir, stamp, pics.size(), src.get_extension()]
		if DirAccess.copy_absolute(ProjectSettings.globalize_path(src), ProjectSettings.globalize_path(dst)) == OK:
			pics.append(dst)
	var fs: Array = []
	var bf := beste_fotos()
	for i in range(2):
		var f: Dictionary = bf[i]
		if f.is_empty():
			continue
		var keep := str(f.get("file", ""))
		if keep != "" and FileAccess.file_exists(keep):
			var dst2 := "%s/bilder/tag_%d_foto%d.jpg" % [dir, stamp, i + 1]
			if DirAccess.copy_absolute(ProjectSettings.globalize_path(keep), ProjectSettings.globalize_path(dst2)) == OK:
				keep = dst2
		fs.append({"name": nm(i), "file": keep, "punkte": int(f.get("punkte", 0)), "tier": str(f.get("tier", ""))})
	var ans: Array = []
	if not _lf.is_empty():
		for i in range(2):
			ans.append({"name": nm(i), "text": str(_lf["antworten"][i])})
	var aw: Array = []
	for a in auszeichnungen():
		aw.append({"name": nm(int(a[0])) if int(a[0]) >= 0 else T.t("beide"), "titel": str(a[1]), "grund": str(a[2])})
	var e := {"datum": Time.get_datetime_string_from_system().substr(0, 16).replace("T", " "), "titel": titel, "frage": str(_lf.get("frage", "")),
			"antworten": ans, "fotos": fs, "bilder": pics, "zaehler": [zaehler[0].duplicate(), zaehler[1].duplicate()], "namen": [nm(0), nm(1)],
			"auszeichnungen": aw, "high_fives": hf_n}
	var L := tagebuch()
	L.append(e)
	var f2 := FileAccess.open(dir + "/reisetagebuch.json", FileAccess.WRITE)
	if f2 != null:
		f2.store_string(JSON.stringify(L.slice(-60), " "))
		f2.close()
	Spieltest.ereignis(modus, "abschnitt", {"name": "Reisetagebuch"})
	_ereignis("tagebuch", e)
	return e


# =======================================================================================================================
# 8 high five
# =======================================================================================================================
func figur_aktion(i: int, art: String, secs := -1.0, zu := -1) -> void:
	"""anim_mensch.gd: the figure of player i (if the host has one: zb_figur(i), actor.gd) shows the action; zu = turns
	towards the figure of that player (High-Five)"""
	var f = _h("zb_figur", [i], null)
	if f == null or not is_instance_valid(f) or not f.has_method("aktion"):
		return
	var ziel = null
	if zu >= 0:
		var g = _h("zb_figur", [zu], null)
		if g != null and is_instance_valid(g):
			ziel = (g as Node3D).global_position
	f.aktion(art, secs, ziel)


func high_five(grund: String) -> void:
	if not aktiv() or n_fig() < 1:
		return
	_hf = {"grund": grund, "until": now() + 8.0}
	for i in range(2):
		say(i, T.t("🙌 High-Five! Beide gleichzeitig %s") % _k(i, "team"), 8.0, 5)


func _jubel_show(txt: String) -> void:
	if _jubel == null:
		return
	_jubel.text = sauber(txt) if sauber(txt) != "" else T.t("Super!")
	_jubel.visible = true
	_jubel.pivot_offset = _jubel.size / 2.0
	_jubel.scale = Vector2(0.4, 0.4)
	_jubel.modulate.a = 1.0
	var tw := _jubel.create_tween()
	tw.tween_property(_jubel, "scale", Vector2.ONE, 0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_interval(1.6)
	tw.tween_property(_jubel, "modulate:a", 0.0, 0.5)
	tw.tween_callback(func(): _jubel.visible = false)
	if not _lite() and _ov != null:
		var cp := CPUParticles2D.new()
		cp.one_shot = true
		cp.amount = 70
		cp.lifetime = 1.6
		cp.explosiveness = 0.95
		cp.direction = Vector2(0, -1)
		cp.spread = 70.0
		cp.initial_velocity_min = 260.0
		cp.initial_velocity_max = 520.0
		cp.gravity = Vector2(0, 600)
		cp.scale_amount_min = 4.0
		cp.scale_amount_max = 8.0
		var g := Gradient.new()
		g.set_color(0, Color("#ffd166"))
		g.add_point(0.33, Color("#3b8cff"))
		g.add_point(0.66, Color("#34c759"))
		g.set_color(g.get_point_count() - 1, Color("#ff6b6b"))
		cp.color_initial_ramp = g
		cp.position = _jubel.position + _jubel.size / 2.0
		_ov.add_child(cp)
		cp.emitting = true
		get_tree().create_timer(2.2).timeout.connect(cp.queue_free)


func _team_press(i: int) -> void:
	var t := now()
	_last_team[i] = t
	if _ts_press(i):
		return
	var o := 1 - i
	if not _hf.is_empty() and t < float(_hf["until"]):
		if t - float(_last_team[o]) <= HF_DT:
			hf_n += 1
			var g := str(_hf["grund"])
			_hf = {}
			_prompt = [{}, {}]
			_jubel_show(T.t("🙌 Super Team!"))
			figur_aktion(0, "highfive", 1.3, 1)
			figur_aktion(1, "highfive", 1.3, 0)
			_rumble([0, 1])
			Spieltest.ereignis(modus, "fortschritt", {"zwei": "high_five_" + g})
			high_five_geschafft.emit(g)
			_ereignis("high_five", {"grund": g})
		else:
			say(i, T.t("Gleichzeitig mit %s!") % nm(o), 1.2, 6)
		return
	if t - float(_last_team[o]) <= HF_DT and abstand() < 6.0:
		_jubel_show("🙌")                                 # just for fun (not counted)


# =======================================================================================================================
# input
# =======================================================================================================================
const KEYS := [{"team": KEY_F, "geben": KEY_G, "wahl": KEY_V, "faehig": KEY_R, "foto": KEY_T},
		{"team": KEY_N, "geben": KEY_M, "wahl": KEY_PERIOD, "faehig": KEY_P, "foto": KEY_COMMA}]
const PAD := {"team": "a", "geben": "b", "faehig": "x", "foto": "y"}
const KEY_TXT := [{"team": "F", "geben": "G", "wahl": "V", "faehig": "R", "foto": "T"}, {"team": "N", "geben": "M", "wahl": ".", "faehig": "P", "foto": ","}]
const PAD_TXT := {"team": "[A]", "geben": "[B]", "wahl": "[← →]", "faehig": "[X]", "foto": "[Y]"}


const PAD_NAME := {"a": "[A]", "b": "[B]", "x": "[X]", "y": "[Y]", "l1": "[LB]", "r1": "[RB]", "up": "[↑]", "down": "[↓]", "left": "[←]", "right": "[→]"}


func _pad() -> Dictionary:
	"""which controller button does what (the host may change it: Maggie has A B X Y for herself)"""
	var p = _h("zb_pad", [], null)
	return p if p is Dictionary else PAD


func _k(i: int, act: String) -> String:
	if int(_h("zb_dev", [i], -1)) >= 0:
		if act == "wahl":
			return str(PAD_TXT["wahl"])
		return str(PAD_NAME.get(str(_pad().get(act, "")), PAD_TXT[act]))
	return "«%s»" % str(KEY_TXT[clampi(i, 0, 1)][act])


func _presses(i: int) -> Array:
	var out: Array = []
	var free := bool(_h("zb_eingabe_frei", [i], true))
	var dv := int(_h("zb_dev", [i], -1))
	var pm = main.padmap if main != null else null
	if free and dv >= 0 and pm != null and bool(_h("zb_knoepfe", [i], true)):     # (Rollen: the controller of player 2 is MoveEye's)
		var pd := _pad()
		for act in pd:
			if pm.hit(str(pd[act]), [dv]):
				out.append(act)
		if pm.hit("left", [dv]) or pm.hit("right", [dv]):
			out.append("wahl")
	for act in KEYS[i]:
		var kc: int = KEYS[i][act]
		var down := Input.is_physical_key_pressed(kc)
		var kk := "%d_%s" % [i, act]
		if down and not bool(_keys_prev.get(kk, false)) and free:
			out.append(act)
		_keys_prev[kk] = down
	out.append_array(_inj[i])
	_inj[i] = []
	return out


func _unhandled_input(ev: InputEvent) -> void:
	"""(_unhandled_input: it comes before the one of main.gd) our keys (F G V R T / N M . P ,) do not reach the hotkeys of the window (main.gd: T = TV, G, M = map, P, F) while two play"""
	if not (ev is InputEventKey) or not aktiv():
		return
	var pk: int = (ev as InputEventKey).physical_keycode
	for i in range(2):
		if pk in (KEYS[i] as Dictionary).values() and bool(_h("zb_eingabe_frei", [i], true)):
			get_viewport().set_input_as_handled()
			return


func _input_tick() -> void:
	for i in range(2):
		for act in _presses(i):
			if lagerfeuer_offen() and str(act) in ["team", "wahl"]:
				_lf_knopf(i, str(act))
				continue
			match str(act):
				"team":
					_team_press(i)
				"geben":
					var it := _sel_item(i)
					if it == "":
						say(i, T.t("Dein Rucksack ist leer."), 2.0)
					else:
						geben(i, it)
				"wahl":
					_sel[i] = int(_sel[i]) + 1
				"faehig":
					_faehigkeit(i)
				"foto":
					foto(i)


func _rumble(L: Array) -> void:
	if main == null or main.padmap == null:
		return
	var devs: Array = []
	for i in L:
		var d := int(_h("zb_dev", [i], -1))
		if d >= 0:
			devs.append(d)
	if not devs.is_empty():
		main.padmap.rumble("catch", devs)


func _ereignis(art: String, d: Dictionary) -> void:
	if art in ["raeuberleiter", "ruecken"]:
		Spieltest.ereignis(modus, "fortschritt", {"zwei": art})
	_h("zb_ereignis", [art, d])


# =======================================================================================================================
# every frame
# =======================================================================================================================
func _process(dt: float) -> void:
	var on := aktiv()
	if _ov != null:
		_ov.visible = on
	if not on:
		if lagerfeuer_offen():
			_input_tick()
			_lf_tick()
		return
	_ensure_ov()
	_pf_frame = [[], []]
	_input_tick()
	_ts_tick()
	_funde_tick()
	_ruecken_tick(dt)
	_gummiband_tick()
	if not _hf.is_empty() and now() > float(_hf["until"]):
		_hf = {}
	_lf_tick()
	_ov_t -= dt
	if _ov != null and (_ov_t <= 0.0):
		_ov_t = 1.0 / 15.0 if _lite() else 0.0
		_hud()
		_ov.queue_redraw()


func _ensure_ov() -> void:
	var ui = _h("zb_ui", [], null)
	if ui == null:
		return
	if _ov != null and is_instance_valid(_ov) and _ov.get_parent() == ui:
		return
	_ov = Control.new()
	_ov.set_anchors_preset(Control.PRESET_FULL_RECT)
	_ov.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ov.draw.connect(_draw_ov)
	(ui as Control).add_child(_ov)
	_pp = []
	for i in range(2):
		var e := {}
		for k in ["prompt", "wissen", "info"]:
			var pc := PanelContainer.new()
			pc.mouse_filter = Control.MOUSE_FILTER_IGNORE
			var sb := StyleBoxFlat.new()
			sb.bg_color = Color(0.03, 0.05, 0.08, 0.82) if k != "info" else Color(0.03, 0.05, 0.08, 0.6)
			sb.border_color = col(i)
			sb.border_width_bottom = 3 if k == "prompt" else 0
			sb.border_width_left = 4 if k == "wissen" else 0
			sb.set_corner_radius_all(10)
			sb.set_content_margin_all(8 if k != "info" else 5)
			pc.add_theme_stylebox_override("panel", sb)
			var l := Label.new()
			l.add_theme_font_size_override("font_size", {"prompt": 24, "wissen": 21, "info": 15}[k])
			l.add_theme_color_override("font_color", Color.WHITE if k != "wissen" else Color("#ffe3a3"))
			l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART if k != "info" else TextServer.AUTOWRAP_OFF
			l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER if k == "prompt" else HORIZONTAL_ALIGNMENT_LEFT
			pc.add_child(l)
			_ov.add_child(pc)
			e[k] = pc
			e[k + "_l"] = l
		_pp.append(e)
	_jubel = Label.new()
	_jubel.add_theme_font_size_override("font_size", 56)
	_jubel.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_jubel.add_theme_constant_override("outline_size", 12)
	_jubel.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_jubel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_jubel.visible = false
	_ov.add_child(_jubel)


func _rect(i: int) -> Rect2:
	var r0: Rect2 = _h("zb_rect", [0], Rect2())
	var r1: Rect2 = _h("zb_rect", [1], Rect2())
	if r0.is_equal_approx(r1) or r1.size == Vector2.ZERO:       # one view for both: left half / right half
		if r1.size == Vector2.ZERO and i == 1:
			return Rect2(r0.position + Vector2(r0.size.x / 2.0, 0), Vector2(r0.size.x / 2.0, r0.size.y))
		var hw := r0.size.x / 2.0
		return Rect2(r0.position + Vector2(hw * i, 0), Vector2(hw, r0.size.y))
	return r0 if i == 0 else r1


func _hud() -> void:
	if _pp.size() < 2:
		return
	var t := now()
	for i in range(2):
		var e: Dictionary = _pp[i]
		var r := _rect(i)
		var vis := true
		var p: Dictionary = _prompt[i]
		var pt := str(p.get("text", "")) if not p.is_empty() and t < float(p["until"]) else ""
		var pl: Label = e["prompt_l"]
		pl.text = sauber(pt)
		var pp: PanelContainer = e["prompt"]
		pp.visible = vis and pt != ""
		var w := minf(r.size.x - 24.0, 560.0)
		pp.custom_minimum_size = Vector2(w, 0)
		pp.size = Vector2(w, 0)
		pp.position = Vector2(r.position.x + (r.size.x - w) / 2.0, r.position.y + 54.0)
		var wt := _wissen_text(i)
		var wl: Label = e["wissen_l"]
		wl.text = sauber(wt)
		var wp: PanelContainer = e["wissen"]
		wp.visible = vis and wt != ""
		wp.custom_minimum_size = Vector2(w, 0)
		wp.size = Vector2(w, 0)
		wp.position = Vector2(r.position.x + (r.size.x - w) / 2.0, r.position.y + r.size.y - 92.0 - wp.get_combined_minimum_size().y)
		var il: Label = e["info_l"]
		il.text = sauber(_info(i))
		var ip: PanelContainer = e["info"]
		ip.visible = vis and il.text != ""
		ip.size = Vector2(0, 0)
		ip.position = Vector2(r.position.x + 10.0, r.position.y + r.size.y - 84.0)
	var u := _rect(0).merge(_rect(1))
	_jubel.size = Vector2(u.size.x, 80)
	_jubel.position = Vector2(u.position.x, u.position.y + u.size.y * 0.4)


func _info(i: int) -> String:
	var r := rolle(i)
	var tx := "%s %s" % [str(r.get("icon", "")), rolle_name(i)]
	if str(r.get("faehigkeit", "")) != "":
		var cd := float(_cd[i]) - now()
		tx += "  ·  %s %s%s" % [_k(i, "faehig"), T.t(str(r["faehigkeit"])), (" (%d s)" % int(ceil(cd))) if cd > 0.0 else ""]
	var it := _sel_item(i)
	tx += "\n" + T.t("Rucksack") + " %.1f kg" % last_kg(i)
	if it != "":
		tx += "  ▸ %s  (%s %s · %s)" % [str(_items[it][0]), _k(i, "geben"), T.t("geben"), _k(i, "wahl")]
	tx += "   %s %s" % [T.t("Foto"), _k(i, "foto")]
	var ex := str(_h("zb_info", [i], ""))
	if ex != "":
		tx += "\n" + ex
	return tx


func _draw_ov() -> void:
	var font := ThemeDB.fallback_font
	var t := now()
	for i in range(2):
		var r := _rect(i)
		var L: Array = []
		for a in _pfeile[i]:
			if t < float(a["until"]):
				L.append(a)
		_pfeile[i] = L
		var all: Array = _pf_frame[i] + L
		var c := r.position + Vector2(r.size.x * 0.5, r.size.y * 0.42)
		var rad := minf(r.size.x, r.size.y) * 0.26
		var k := 0
		for a in all.slice(0, 4):
			var to: Vector2 = (a["pos"] as Vector2) - pos(i)
			var rel := wrapf(atan2(-to.x, -to.y) - yaw(i), -PI, PI)
			var v := Vector2(-sin(rel), -cos(rel))
			var p := c + v * rad + Vector2(0, k * 6.0)
			var s := 26.0
			var cc: Color = a["col"]
			var pts := PackedVector2Array([p + v * s, p + v.orthogonal() * s * 0.6 - v * s * 0.4, p - v.orthogonal() * s * 0.6 - v * s * 0.4])
			draw_colored_polygon_ov(pts, Color(0, 0, 0, 0.7), 4.0)
			_ov.draw_colored_polygon(pts, cc)
			var txt := sauber(str(a["text"]))
			var tw := font.get_string_size(txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 18).x
			var tp := p - v * 30.0 + Vector2(-tw / 2.0, 6.0)
			_ov.draw_string_outline(font, tp, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, 6, Color(0, 0, 0, 0.9))
			_ov.draw_string(font, tp, txt, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, cc)
			k += 1
		if not _ruecken.is_empty() and n_fig() == 2:
			var rc := r.position + Vector2(r.size.x - 64.0, 150.0)
			var rr := 40.0
			_ov.draw_circle(rc, rr + 4.0, Color(0, 0, 0, 0.55))
			_ov.draw_arc(rc, rr, 0, TAU, 48, Color(1.0, 0.35, 0.3, 0.9), 4.0)
			for j in range(2):
				var y := yaw(j)
				var fan := PackedVector2Array([rc])
				for s2 in range(13):
					var a2 := y - deg_to_rad(SICHT) + s2 * deg_to_rad(2.0 * SICHT) / 12.0
					fan.append(rc + Vector2(-sin(a2), -cos(a2)) * rr)
				var cj := col(j)
				cj.a = 0.55
				_ov.draw_colored_polygon(fan, cj)
			var me := Vector2(-sin(yaw(i)), -cos(yaw(i)))
			_ov.draw_line(rc, rc + me * (rr + 10.0), Color.WHITE, 3.0)
			_ov.draw_string_outline(font, rc + Vector2(-14, -rr - 8), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, 5, Color.BLACK)
			_ov.draw_string(font, rc + Vector2(-5, -rr - 8), "N", HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color.WHITE)


func draw_colored_polygon_ov(pts: PackedVector2Array, c: Color, w: float) -> void:
	var cl := pts.duplicate()
	cl.append(pts[0])
	_ov.draw_polyline(cl, c, w)


# =======================================================================================================================
# panels (camp, morning, chapter page)
# =======================================================================================================================
func _m():
	return _h("zb_maler", [], null)


func _g(title: String, parent: Control) -> VBoxContainer:
	var m = _m()
	if m != null and m.has_method("_group"):
		return m._group(title, parent)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	parent.add_child(v)
	v.add_child(_l(title, 16, Color.WHITE))
	return v


func _l(text: String, sz := 14, c := Color(0.85, 0.88, 0.92), wrap := true) -> Label:
	var m = _m()
	if m != null and m.has_method("_lab"):
		return m._lab(text, sz, c, wrap)
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", sz)
	l.add_theme_color_override("font_color", c)
	if wrap:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


func _b(parent: Control, text: String, cb: Callable, primary := false) -> Button:
	var m = _m()
	if m != null and m.has_method("_btn"):
		return m._btn(parent, text, cb, primary)
	var b := Button.new()
	b.text = text
	b.pressed.connect(cb)
	parent.add_child(b)
	return b


func paint_lagerfeuer(parent: Control) -> void:
	"""campfire: one short question to both - an answer by picking or a short text"""
	if _lf.is_empty():
		return
	var gg := _g(T.t("🔥 Lagerfeuer"), parent)
	gg.add_child(_l(str(_lf["frage"]), 18, Color("#ffd166")))
	for i in range(2):
		var row := VBoxContainer.new()
		gg.add_child(row)
		var a := str(_lf["antworten"][i])
		row.add_child(_l("%d · %s%s" % [i + 1, nm(i), ("   ✓ «%s»" % a) if a != "" else ""], 15, col(i), false))
		var fl := HFlowContainer.new()
		fl.add_theme_constant_override("h_separation", 6)
		fl.add_theme_constant_override("v_separation", 6)
		row.add_child(fl)
		for o in _lf["optionen"]:
			var oo := str(o)
			var ii := i
			var b := _b(fl, ("● " if a == oo else "") + oo, func(): antwort(ii, oo); _h("zb_neu_malen", []))
			b.custom_minimum_size = Vector2(0, 40)
		var le := LineEdit.new()
		le.placeholder_text = T.t("Oder eigene kurze Antwort …")
		le.max_length = 80
		le.custom_minimum_size = Vector2(0, 40)
		if a != "" and not a in _lf["optionen"]:
			le.text = a
		var ii2 := i
		le.text_submitted.connect(func(tx): antwort(ii2, tx); _h("zb_neu_malen", []))
		le.focus_exited.connect(func():
			if le.text.strip_edges() != "":
				antwort(ii2, le.text))
		row.add_child(le)
	if str(_lf["antworten"][0]) != "" and str(_lf["antworten"][1]) != "":
		gg.add_child(_l(T.t("Schön! Das kommt am Morgen ins Reisetagebuch."), 13, Color(0.3, 0.85, 0.45)))


func paint_fotowettbewerb(parent: Control) -> void:
	"""in the evening: both best animal photos side by side"""
	var bf := beste_fotos()
	if (bf[0] as Dictionary).is_empty() and (bf[1] as Dictionary).is_empty():
		return
	var gg := _g(T.t("📸 Fotowettbewerb: das schönste Tierfoto"), parent)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 12)
	gg.add_child(hb)
	var pa := int(bf[0].get("punkte", -1)) if not (bf[0] as Dictionary).is_empty() else -1
	var pb := int(bf[1].get("punkte", -1)) if not (bf[1] as Dictionary).is_empty() else -1
	for i in range(2):
		var f: Dictionary = bf[i]
		var vb := VBoxContainer.new()
		hb.add_child(vb)
		vb.add_child(_thumb(str(f.get("file", "")), Vector2(200, 112)))
		var win := (i == 0 and pa > pb) or (i == 1 and pb > pa)
		var cap := "%s%s: " % ["🏆 " if win else "", nm(i)]
		cap += (T.t("%d Punkte") % int(f["punkte"]) + (" · " + T.t(_tiername(str(f.get("tier", "")))) if str(f.get("tier", "")) != "" else "")) if not f.is_empty() else T.t("noch kein Foto")
		vb.add_child(_l(cap, 13, col(i)))
	if pa == pb and pa > 0:
		gg.add_child(_l(T.t("Unentschieden - beide gleich schön!"), 13, Color("#ffd166")))


func _tiername(t: String) -> String:
	return {"murmeltier": "Murmeltier", "schneehase": "Schneehase", "gaemse": "Gämse", "steinbock": "Steinbock", "steinadler": "Steinadler",
			"bartgeier": "Bartgeier", "luchs": "Luchs", "fuchs": "Fuchs", "deer": "Reh", "boar": "Wildschwein", "reh": "Reh"}.get(t, t.capitalize())


func paint_zwischenstand(parent: Control) -> void:
	var gg := _g(T.t("Wer findet mehr?"), parent)
	for i in range(2):
		var z: Dictionary = zaehler[i]
		var tx := "%s   " % nm(i)
		for kat in KATS:
			tx += "%s %d · " % [T.t(str(KAT_ICON[kat])), int(z.get(kat, 0))]
		gg.add_child(_l(tx, 14, col(i), false))
	gg.add_child(_l(T.t("High-Fives: %d") % hf_n, 11, Color(0.55, 0.6, 0.68)))


func paint_auszeichnungen(parent: Control, e: Dictionary = {}) -> void:
	var aw: Array = e.get("auszeichnungen", []) if not e.is_empty() else []
	if e.is_empty():
		for a in auszeichnungen():
			aw.append({"name": nm(int(a[0])) if int(a[0]) >= 0 else T.t("beide"), "titel": str(a[1]), "grund": str(a[2])})
	if aw.is_empty():
		return
	var gg := _g(T.t("🏅 Auszeichnungen"), parent)
	for a in aw:
		gg.add_child(_l("🏅 %s: «%s» - %s" % [str(a["name"]), str(a["titel"]), str(a["grund"])], 15, Color("#ffd166")))


# ---- the campfire as a window (for stories without a panel, e.g. Maggie): controllers answer with «wahl» and «team» ------
var _lf_win: CanvasLayer
var _lf_box: VBoxContainer
var _lf_sel: Array = [0, 0]
var _lf_t := 0.0
var _lf_sig := ""


func lagerfeuer_fenster() -> void:
	if _lf.is_empty():
		return
	lagerfeuer_zu()
	_lf_win = CanvasLayer.new()
	_lf_win.layer = 35
	(main if main != null else self).add_child(_lf_win)
	var pc := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.07, 0.06, 0.05, 0.96)
	sb.border_color = Color("#ff9f43")
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(14)
	sb.set_content_margin_all(18)
	pc.add_theme_stylebox_override("panel", sb)
	pc.anchor_left = 0.5
	pc.anchor_right = 0.5
	pc.anchor_top = 0.5
	pc.anchor_bottom = 0.5
	pc.offset_left = -380
	pc.offset_right = 380
	pc.offset_top = -230
	pc.offset_bottom = 230
	_lf_win.add_child(pc)
	_lf_box = VBoxContainer.new()
	_lf_box.add_theme_constant_override("separation", 8)
	pc.add_child(_lf_box)
	_lf_t = now()
	_lf_sig = ""
	_lf_paint()


func lagerfeuer_offen() -> bool:
	return _lf_win != null and is_instance_valid(_lf_win)


func lagerfeuer_zu() -> void:
	if lagerfeuer_offen():
		_lf_win.queue_free()
	_lf_win = null


func _lf_paint() -> void:
	if not lagerfeuer_offen() or _lf.is_empty():
		return
	var sig := str(_lf["antworten"]) + str(_lf_sel)
	if sig == _lf_sig:
		return
	_lf_sig = sig
	for c in _lf_box.get_children():
		c.queue_free()
	_lf_box.add_child(_plain(T.t("🔥 Lagerfeuer"), 26, Color("#ff9f43")))
	_lf_box.add_child(_plain(str(_lf["frage"]), 20, Color.WHITE))
	var opts: Array = _lf["optionen"]
	for i in range(2):
		var a := str(_lf["antworten"][i])
		_lf_box.add_child(_plain("%d · %s%s" % [i + 1, nm(i), ("   ✓ «%s»" % a) if a != "" else "   " + T.t("(%s wählen, %s = so!)") % [_k(i, "wahl"), _k(i, "team")]], 17, col(i)))
		var fl := HFlowContainer.new()
		fl.add_theme_constant_override("h_separation", 6)
		_lf_box.add_child(fl)
		for j in range(opts.size()):
			var b := Button.new()
			var oo := str(opts[j])
			b.text = ("> " if int(_lf_sel[i]) % maxi(1, opts.size()) == j and a == "" else "") + ("✓ " if a == oo else "") + oo
			if int(_lf_sel[i]) % maxi(1, opts.size()) == j and a == "":
				b.add_theme_color_override("font_color", col(i))
			b.custom_minimum_size = Vector2(0, 38)
			var ii := i
			b.pressed.connect(func(): antwort(ii, oo); _lf_sig = "")
			fl.add_child(b)
	var le := LineEdit.new()
	le.placeholder_text = T.t("Oder eigene kurze Antwort (Tastatur, Enter) - für Spieler 1")
	le.max_length = 80
	le.text_submitted.connect(func(tx): antwort(0, tx); _lf_sig = "")
	_lf_box.add_child(le)
	var hb := HBoxContainer.new()
	_lf_box.add_child(hb)
	var bz := Button.new()
	bz.text = T.t("Schliessen")
	bz.pressed.connect(lagerfeuer_zu)
	hb.add_child(bz)
	if not tagebuch().is_empty():
		var bt := Button.new()
		bt.text = sauber(T.t("📔 Reisetagebuch ansehen"))
		bt.pressed.connect(tagebuch_oeffnen)
		hb.add_child(bt)


func _lf_knopf(i: int, act: String) -> void:
	var opts: Array = _lf.get("optionen", [])
	if opts.is_empty():
		return
	if act == "wahl":
		_lf_sel[i] = int(_lf_sel[i]) + 1
	else:
		antwort(i, str(opts[int(_lf_sel[i]) % opts.size()]))
	_lf_sig = ""


func _lf_tick() -> void:
	if not lagerfeuer_offen():
		return
	_lf_paint()
	var done: bool = not _lf.is_empty() and str(_lf["antworten"][0]) != "" and (str(_lf["antworten"][1]) != "" or n_fig() < 2)
	if done and float(_lf.get("done_t", 0.0)) == 0.0:
		_lf["done_t"] = now()
	if float(_lf.get("done_t", 0.0)) > 0.0 and now() - float(_lf["done_t"]) > 2.5 or now() - _lf_t > 90.0:
		lagerfeuer_zu()


func tagebuch_knopf(parent: Control) -> void:
	if tagebuch().is_empty():
		return
	_b(parent, T.t("📔 Reisetagebuch ansehen"), tagebuch_oeffnen)


func _thumb(path: String, sz: Vector2) -> TextureRect:
	var tr := TextureRect.new()
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr.custom_minimum_size = sz
	if path != "" and FileAccess.file_exists(path):
		var im := Image.load_from_file(path)
		if im != null and not im.is_empty():
			tr.texture = ImageTexture.create_from_image(im)
	return tr


func tagebuch_oeffnen() -> void:
	"""the travel diary to look at: every evening with the answers, the photos, the pictures and the titles"""
	tagebuch_schliessen()
	_viewer = CanvasLayer.new()
	_viewer.layer = 40
	(main if main != null else self).add_child(_viewer)
	var bg := ColorRect.new()
	bg.color = Color(0.02, 0.03, 0.05, 0.92)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_viewer.add_child(bg)
	var mc := MarginContainer.new()
	mc.set_anchors_preset(Control.PRESET_FULL_RECT)
	for s in ["left", "right", "top", "bottom"]:
		mc.add_theme_constant_override("margin_" + s, 40)
	_viewer.add_child(mc)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	mc.add_child(v)
	var top := HBoxContainer.new()
	v.add_child(top)
	var tl := _plain(T.t("📔 Reisetagebuch"), 28, Color.WHITE)
	tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(tl)
	var close := Button.new()
	close.text = T.t("Schliessen")
	close.custom_minimum_size = Vector2(160, 44)
	close.pressed.connect(tagebuch_schliessen)
	top.add_child(close)
	var sc := ScrollContainer.new()
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	sc.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	v.add_child(sc)
	var lst := VBoxContainer.new()
	lst.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	lst.add_theme_constant_override("separation", 18)
	sc.add_child(lst)
	var L := tagebuch()
	if L.is_empty():
		lst.add_child(_plain(T.t("Noch leer - am Abend am Lagerfeuer beginnt es."), 16, Color(0.7, 0.75, 0.8)))
	L.reverse()
	for e in L:
		var pc := PanelContainer.new()
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(0.09, 0.08, 0.06)
		sb.border_color = Color("#ffd166")
		sb.border_width_left = 4
		sb.set_corner_radius_all(10)
		sb.set_content_margin_all(14)
		pc.add_theme_stylebox_override("panel", sb)
		lst.add_child(pc)
		var ev := VBoxContainer.new()
		ev.add_theme_constant_override("separation", 6)
		pc.add_child(ev)
		ev.add_child(_plain("%s  ·  %s" % [str(e.get("datum", "")), str(e.get("titel", ""))], 20, Color("#ffd166")))
		if str(e.get("frage", "")) != "":
			ev.add_child(_plain("🔥 " + str(e["frage"]), 15, Color(0.85, 0.8, 0.7)))
			for a in e.get("antworten", []):
				if str(a.get("text", "")) != "":
					ev.add_child(_plain("   %s: «%s»" % [str(a["name"]), str(a["text"])], 16, Color.WHITE))
		var fl := HFlowContainer.new()
		fl.add_theme_constant_override("h_separation", 10)
		ev.add_child(fl)
		for f in e.get("fotos", []):
			var vb := VBoxContainer.new()
			fl.add_child(vb)
			vb.add_child(_thumb(str(f.get("file", "")), Vector2(240, 135)))
			vb.add_child(_plain("📸 %s · %d %s%s" % [str(f.get("name", "")), int(f.get("punkte", 0)), T.t("Punkte"), (" · " + T.t(_tiername(str(f["tier"])))) if str(f.get("tier", "")) != "" else ""], 12, Color(0.8, 0.84, 0.9)))
		for b in e.get("bilder", []):
			fl.add_child(_thumb(str(b), Vector2(240, 135)))
		var aw: Array = e.get("auszeichnungen", [])
		for a in aw:
			ev.add_child(_plain("🏅 %s: «%s»" % [str(a.get("name", "")), str(a.get("titel", ""))], 15, Color("#ffd166")))
		var nms: Array = e.get("namen", ["1", "2"])
		var zz: Array = e.get("zaehler", [{}, {}])
		for i in range(mini(2, zz.size())):
			var tx := "%s  " % str(nms[i] if i < nms.size() else "")
			for kat in KATS:
				if int(zz[i].get(kat, 0)) > 0:
					tx += "%s %d · " % [T.t(str(KAT_ICON[kat])), int(zz[i][kat])]
			ev.add_child(_plain(tx, 13, Color(0.7, 0.75, 0.82)))
		if int(e.get("high_fives", 0)) > 0:
			ev.add_child(_plain(T.t("🙌 %d High-Fives") % int(e["high_fives"]), 13, Color(0.7, 0.75, 0.82)))
	close.grab_focus.call_deferred()


func _plain(text: String, sz: int, c: Color) -> Label:
	var l := Label.new()
	l.text = sauber(text)
	l.add_theme_font_size_override("font_size", sz)
	l.add_theme_color_override("font_color", c)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


func tagebuch_schliessen() -> void:
	if _viewer != null and is_instance_valid(_viewer):
		_viewer.queue_free()
	_viewer = null


func tagebuch_offen() -> bool:
	return _viewer != null and is_instance_valid(_viewer)


# =======================================================================================================================
# control API
# =======================================================================================================================
func op(d: Dictionary) -> Dictionary:
	var w := str(d.get("was", "state"))
	var i := clampi(int(d.get("p", 1)) - 1, 0, 1)
	var out := {"ok": true}
	match w:
		"knopf":
			(_inj[i] as Array).append(str(d.get("knopf", "team")))
		"wissen":
			wissen(str(d.get("id", "test")), [str(d.get("a", "")), str(d.get("b", ""))])
		"wissen_weg":
			wissen_weg(str(d.get("id", "")))
		"teamstelle":
			teamstelle(str(d.get("id", "test")), Vector2(float(d.get("x", 0.0)), float(d.get("z", 0.0))), str(d.get("text", "")))
			if bool(d.get("aktiv", true)):
				teamstelle_aktiv(str(d.get("id", "test")))
		"geraeusch":
			geraeusch(str(d.get("text", "")), str(d.get("tier", "")))
		"high_five":
			high_five(str(d.get("grund", "test")))
		"zaehle":
			zaehle(i, str(d.get("kat", "funde")))
		"fund":
			fundstueck(str(d.get("id", "f%d" % _funde.size())), Vector2(float(d.get("x", 0.0)), float(d.get("z", 0.0))), str(d.get("kat", "funde")), str(d.get("text", "Test")))
		"spuren":
			out["n"] = spuren_zeigen(pos(i), 60.0, 30.0)
		"foto":
			out["foto"] = foto(i, str(d.get("tier", "")))
		"fenster":
			lagerfeuer_fenster()
		"fenster_zu":
			lagerfeuer_zu()
		"frage":
			lagerfeuer_frage(str(d.get("frage", T.t("Was war heute das Schönste?"))), d.get("optionen", ["A", "B"]))
		"antwort":
			antwort(i, str(d.get("value", "")))
		"tag":
			out["tag"] = tag_speichern(str(d.get("titel", "Test")), d.get("bilder", []))
		"tagebuch":
			out["tagebuch"] = tagebuch()
		"oeffnen":
			tagebuch_oeffnen()
		"schliessen":
			tagebuch_schliessen()
		"tauschen":
			rollen_tauschen()
		"form":
			set_form(i, str(d.get("value", "f")))
		"geben":
			out["ok"] = geben(i, str(d.get("id", "")))
		"wichtig":
			wichtig(str(d.get("id", "test")), Vector2(float(d.get("x", 0.0)), float(d.get("z", 0.0))), float(d.get("r", 10.0)), str(d.get("text", "Ziel")), bool(d.get("halten", true)), float(d.get("max_s", 60.0)))
		"weg":
			for id in _ts.keys():
				teamstelle_weg(id)
			for id in _funde.keys():
				fund_weg(id)
			_wichtig = {}
			_ruecken = {}
		"auszeichnungen":
			out["auszeichnungen"] = auszeichnungen()
	out["zb"] = state()
	return out


func state() -> Dictionary:
	var ts := {}
	for id in _ts:
		var s: Dictionary = _ts[id]
		ts[id] = {"phase": s["phase"], "aktiv": s["aktiv"], "helfer": s["helfer"], "klett": s["klett"], "pos": [snappedf(s["pos"].x, 0.1), snappedf(s["pos"].y, 0.1)]}
	var fu := {}
	for id in _funde:
		fu[id] = {"kat": _funde[id]["kat"], "pos": [snappedf(_funde[id]["pos"].x, 0.1), snappedf(_funde[id]["pos"].y, 0.1)], "sichtbar": str(_funde[id]["kat"]) != "spuren" or now() < float(_funde[id]["bis"])}
	var pr: Array = []
	for i in range(2):
		var p: Dictionary = _prompt[i]
		pr.append(str(p.get("text", "")) if not p.is_empty() and now() < float(p["until"]) else "")
	var wi: Array = [_wissen_text(0), _wissen_text(1)]
	return {"aktiv": aktiv(), "zaehler": zaehler, "hf": hf_n, "hf_offen": not _hf.is_empty(), "ts": ts, "funde": fu, "haelt": haelt(),
			"wichtig": _wichtig.keys(), "traeger": _traeger, "kg": [last_kg(0), last_kg(1)], "tempo": [snappedf(tempo(0), 0.01), snappedf(tempo(1), 0.01)],
			"ruecken": {} if _ruecken.is_empty() else {"tier": _ruecken["tier"], "abdeckung": abdeckung(), "ok_t": snappedf(float(_ruecken["ok_t"]), 0.1)},
			"fotos": _fotos, "lf": _lf, "rollen": [rolle(0).get("id", ""), rolle(1).get("id", "")], "form": form, "prompt": pr, "wissen": wi,
			"abstand": snappedf(abstand(), 0.1), "tagebuch_n": tagebuch().size(), "tagebuch_offen": tagebuch_offen(), "lf_offen": lagerfeuer_offen()}
