#@ Motion Watch – Teil 320: Extras: Spielecke und Spieleabend. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ---- game corner (2.95.29): party games for the phones in the own Wi-Fi - quiz with buzzer, werewolf narrator,
# drawing and guessing, connect four, dice / timer / scores - and a collection of free browser games (from GitHub).
# The phones join with a QR code (a room key in the address, no password); the room closes by itself after some hours.
PARTY = {"key": "", "until": 0.0, "game": "lobby", "seq": 0, "players": {}, "host": "", "g": {}, "tools": {}}
PARTY_COND = threading.Condition()
GAMES_PKG = {"version": "GS-1.3", "file": "games/MotionWatch_Spiele.zip", "size": 13881572, "sha256": "201b9b0b0271fce9f2f273d3c0cbd6da4ff79015eda91512ee38cbf92f73305a"}
GAMES_DL = {"running": False, "msg": "", "got": 0}

QUIZ = [("Wie heisst der höchste Berg der Schweiz?", "Dufourspitze (4634 m)"), ("Wie viele Kantone hat die Schweiz?", "26"),
        ("Welches Tier ist das grösste Landtier der Schweiz?", "Rothirsch (oder Wisent im Gehege)"), ("Wie viele Beine hat eine Spinne?", "8"),
        ("Welcher Planet ist der Sonne am nächsten?", "Merkur"), ("Wie heisst der längste Fluss der Schweiz?", "Rhein (Aare: längster ganz in der Schweiz)"),
        ("In welchem Jahr landeten Menschen zum ersten Mal auf dem Mond?", "1969"), ("Welches Gas atmen Pflanzen ein?", "Kohlendioxid (CO₂)"),
        ("Wie heisst die Hauptstadt von Australien?", "Canberra"), ("Wie viele Minuten hat ein Tag?", "1440"),
        ("Welches Tier schläft im Winter in einer Höhle und frisst vorher Honig und Beeren?", "Braunbär"),
        ("Wie heisst der grösste See, der ganz in der Schweiz liegt?", "Neuenburgersee"), ("Welche Farbe hat der Fuchs im Winter in der Arktis?", "Weiss (Polarfuchs)"),
        ("Wie viele Spieler hat eine Fussballmannschaft auf dem Feld?", "11"), ("Was misst ein Barometer?", "Luftdruck"),
        ("Welcher Vogel kann rückwärts fliegen?", "Kolibri"), ("Wie heisst der Stern, der uns am nächsten ist?", "Die Sonne"),
        ("Welches ist das schnellste Landtier?", "Gepard"), ("Aus welchem Land kommt die Pizza?", "Italien"),
        ("Wie viele Zähne hat ein erwachsener Mensch normalerweise?", "32"), ("Welches Metall ist bei Zimmertemperatur flüssig?", "Quecksilber"),
        ("Wie heisst das Nationalgericht mit geschmolzenem Käse im Caquelon?", "Fondue"), ("Welcher Pass verbindet Uri und das Tessin?", "Gotthard"),
        ("Wie viele Seiten hat ein Sechseck?", "6"), ("Welches Tier ist das Wappentier von Bern?", "Bär"),
        ("Was ist schwerer: ein Kilo Federn oder ein Kilo Steine?", "Gleich schwer"), ("Welche Blume ist das Symbol der Alpen?", "Edelweiss"),
        ("Wie heisst der kleinste Planet unseres Sonnensystems?", "Merkur"), ("Bei wie viel Grad kocht Wasser auf Meereshöhe?", "100 °C"),
        ("Welches Tier legt die grössten Eier?", "Strauss"), ("Wie viele Kontinente gibt es?", "7"),
        ("Welcher Schweizer erfand die Klettverschluss-Idee?", "George de Mestral"), ("Welche Sprache spricht man im Engadin neben Deutsch?", "Rätoromanisch"),
        ("Wie heisst der Wind, der warm über die Alpen fällt?", "Föhn"), ("Welches Organ pumpt das Blut?", "Herz"),
        ("Wie lange braucht das Licht von der Sonne zur Erde (ungefähr)?", "8 Minuten"), ("Welches Tier hat schwarz-weisse Streifen am Kopf und gräbt Baue?", "Dachs"),
        ("Wie viele Stunden Zeitunterschied hat die Schweiz im Sommer zu UTC?", "2"), ("Was sammeln Bienen?", "Nektar und Pollen"),
        ("Welcher Kontinent ist der kälteste?", "Antarktis"), ("Welches Werkzeug zeigt immer nach Norden?", "Kompass"),
        ("Wie heisst ein junger Fuchs?", "Welpe"), ("Wie viele Ecken hat ein Würfel?", "8"), ("Welches Sternbild zeigt den Polarstern?", "Kleiner Bär (Kleiner Wagen)")]
WORDS = ["Zelt", "Wohnwagen", "Lagerfeuer", "Fuchs", "Igel", "Eule", "Berg", "Kuh", "Käse", "Fondue", "Schokolade", "Uhr", "Velo", "Zug",
         "Schiff", "Ballon", "Regenbogen", "Gewitter", "Schneemann", "Ski", "Taschenlampe", "Mond", "Stern", "Sonne", "Wolke", "Baum", "Pilz",
         "Blume", "Biene", "Schnecke", "Frosch", "Fisch", "Angel", "Brücke", "Tunnel", "Burg", "Krone", "Drache", "Ritter", "Pirat",
         "Schatz", "Insel", "Palme", "Kaktus", "Wüste", "Kamel", "Elefant", "Giraffe", "Schlange", "Krokodil", "Pinguin", "Eisbär",
         "Iglu", "Rakete", "Roboter", "Kamera", "Brille", "Schirm", "Hut", "Schuh", "Socke", "Handschuh", "Gitarre", "Trommel",
         "Glocke", "Kuchen", "Pizza", "Banane", "Apfel", "Karotte", "Ei", "Hamburger", "Glace", "Teller", "Gabel", "Tasse",
         "Kerze", "Lampe", "Sofa", "Bett", "Fenster", "Tür", "Schlüssel", "Leiter", "Hammer", "Schere", "Buch", "Brief", "Telefon",
         "Computer", "Maus", "Katze", "Hund", "Pferd", "Hase", "Reh", "Wildschwein", "Spinne", "Schmetterling", "Vogelnest",
         "Sandburg", "Wasserfall", "Vulkan", "Kompass", "Karte", "Rucksack", "Schlafsack", "Grill", "Wurst", "Marshmallow",
         "Gespenst", "Hexe", "Zauberer", "König", "Clown", "Feuerwehr", "Polizei", "Traktor", "Helikopter", "Flugzeug", "U-Boot",
         "Leuchtturm", "Anker", "Schneeflocke", "Herz", "Diamant", "Zahnbürste", "Badewanne", "Dusche", "Kran", "Bagger"]
WOLF_NIGHT = ["Es wird Nacht. Alle schliessen die Augen.", "Die Werwölfe erwachen und einigen sich still auf ein Opfer. Zeigt auf die Person.",
              "Die Werwölfe schlafen wieder ein.", "Die Seherin erwacht und zeigt auf eine Person. Der Erzähler zeigt Daumen hoch für Werwolf, Daumen runter für keinen.",
              "Die Seherin schläft wieder ein.", "Die Hexe erwacht. Der Erzähler zeigt ihr das Opfer. Will sie heilen? Will sie jemanden vergiften?",
              "Die Hexe schläft wieder ein.", "Es wird Tag. Alle wachen auf."]
WOLF_DAY = ["Der Erzähler sagt, wer in der Nacht gestorben ist, und tippt diese Person als tot an.",
            "Diskussion: Wer könnte ein Werwolf sein? Danach stimmen alle auf dem Handy ab."]
WOLF_ROLES = {"wolf": "🐺 Werwolf", "seer": "🔮 Seherin", "witch": "🧪 Hexe", "villager": "🧑‍🌾 Dorfbewohner"}


def party_on():
    return bool(PARTY["key"]) and time.time() < PARTY["until"]


def party_bump():
    with PARTY_COND:
        PARTY["seq"] += 1
        PARTY_COND.notify_all()


def party_open(hours=6.0):
    if not party_on():
        PARTY.update(key=secrets.token_urlsafe(9), game="lobby", players={}, host="", g={}, tools={})
    PARTY["until"] = time.time() + max(0.5, min(24.0, float(hours))) * 3600
    log_event("sys", f"Game corner open for {hours:g} h")
    if toolmode_on() and TOOLMODE.get("by") == "game corner":
        toolmode_set(max(5, min(720, int((PARTY["until"] - time.time()) / 60 + 0.99))), "game corner")
    party_bump()


GAMES_ALL = {"sim": False}       # 2.98.7: «Spiele freigeben» opened the game of the 3D simulator too (closed with it)


def games_all_open(hours=6.0, who="web"):
    """2.98.7: ONE switch for all games - the game corner (quiz, werewolf ...), the game collection (installed if it is
    missing) and the game of the 3D simulator «Team gegen MoveEye» (when the simulation runs). The players scan one QR code,
    type their name and are in; the page of the game corner shows the collection and the simulator game too."""
    party_open(hours)
    if not games_list() and not GAMES_DL.get("running"):
        threading.Thread(target=games_install, daemon=True, name="games-dl").start()
    if CFG.get("sim_on") and SIM.get("ok"):
        def _sim():
            try:
                r = sim_control({"action": "set", "id": "game_open", "value": True})
                GAMES_ALL["sim"] = bool(isinstance(r, dict) and r.get("ok", True))
                SIMGAME["t"] = 0.0
            except Exception:
                GAMES_ALL["sim"] = False
        threading.Thread(target=_sim, daemon=True, name="games-sim").start()
    log_event("sys", f"All games open for {hours:g} h ({who})")


def games_all_close(who="web"):
    party_close()
    if GAMES_ALL["sim"] and CFG.get("sim_on"):
        try:
            threading.Thread(target=lambda: sim_control({"action": "set", "id": "game_open", "value": False}), daemon=True).start()
        except Exception:
            pass
    GAMES_ALL["sim"] = False


def games_all_state():
    g = sim_game() if CFG.get("sim_on") else None
    return {"on": party_on(), "left": int(max(0, PARTY["until"] - time.time())) if party_on() else 0, "players": len(PARTY["players"]),
            "sim": bool(g and g.get("url")), "sim_n": int((g or {}).get("runners") or 0), "coll": len(games_list())}


def party_close():
    if toolmode_on() and TOOLMODE.get("by") == "game corner":
        toolmode_set(0, "game corner")              # the rest mode ends with the game corner
    PARTY.update(key="", until=0.0, game="lobby", players={}, host="", g={}, tools={})
    log_event("sys", "Game corner closed")
    party_bump()


def _pl(pid):
    return PARTY["players"].get(pid)


def _pname(pid):
    p = _pl(pid)
    return p["name"] if p else "?"


def _pub_map():
    """secret player key -> public id (2.95.33: the other phones only ever see the public one)"""
    m = {}
    for k, p in PARTY["players"].items():
        if "pub" not in p:
            p["pub"] = "u" + secrets.token_hex(4)
        m[k] = p["pub"]
    return m


def _pubify(x, m):
    if isinstance(x, str):
        return m.get(x, x)
    if isinstance(x, list):
        return [_pubify(y, m) for y in x]
    if isinstance(x, dict):
        return {(m.get(k, k) if isinstance(k, str) else k): _pubify(v, m) for k, v in x.items()}
    return x


def party_unpub(d):
    """actions name other players by their public id -> the secret key"""
    rev = {v: k for k, v in _pub_map().items()}
    for k in ("id", "by"):
        if isinstance(d.get(k), str) and d[k] in rev:
            d[k] = rev[d[k]]
    return d


def party_view(pid):
    return _pubify(_party_view(pid), _pub_map())


def _party_view(pid):
    """what one phone sees (the secret role only its own)"""
    now = time.time()
    me = _pl(pid)
    pls = [{"id": k, "name": v["name"], "score": v["score"], "on": now - v["t"] < 25, "host": k == PARTY["host"]}
           for k, v in sorted(PARTY["players"].items(), key=lambda kv: -kv[1]["score"])]
    v = {"seq": PARTY["seq"], "now": now, "game": PARTY["game"], "players": pls, "me": pid if me else "", "host": PARTY["host"] == pid,
         "hostname": _pname(PARTY["host"]) if PARTY["host"] else "", "until": int(PARTY["until"] - now), "tools": PARTY["tools"],
         "games": games_list(), "nt": NETTEST["round"] if nettest_open() else 0}
    sg = sim_game() if CFG.get("sim_on") else None
    if sg and sg.get("url"):                               # 2.98.7: the game of the 3D simulator, open for the phones
        v["sim"] = {"url": sg["url"], "max": sg.get("max") or 4, "runners": sg.get("runners") or 0, "round": sg.get("round") or ""}
    G = PARTY["g"]; gm = PARTY["game"]
    if gm == "quiz":
        q = QUIZ[G.get("qi", 0) % len(QUIZ)]
        v["quiz"] = {"phase": G.get("phase", "wait"), "order": [{"id": x, "name": _pname(x)} for x in G.get("order", [])],
                     "q": q[0] if (G.get("show") or v["host"]) else "", "a": q[1] if v["host"] else "", "n": G.get("qi", 0) + 1, "own": G.get("own", "")}
    elif gm == "wolf":
        alive = G.get("alive", {})
        v["wolf"] = {"phase": G.get("phase", "setup"), "step": G.get("step", 0), "cfg": G.get("cfg", {}),
                     "role": WOLF_ROLES.get(G.get("roles", {}).get(pid, ""), "") if pid != PARTY["host"] else "",
                     "alive": [{"id": k, "name": _pname(k), "alive": a} for k, a in alive.items()],
                     "voting": G.get("voting", False), "myvote": G.get("votes", {}).get(pid, ""),
                     "votes": len(G.get("votes", {})), "text": G.get("text", ""), "winner": G.get("winner", "")}
        if v["host"]:
            v["wolf"]["roles"] = [{"name": _pname(k), "role": WOLF_ROLES.get(r, r), "alive": alive.get(k, True)} for k, r in G.get("roles", {}).items()]
            tally = {}
            for t_ in G.get("votes", {}).values():
                tally[t_] = tally.get(t_, 0) + 1
            v["wolf"]["tally"] = sorted([{"name": _pname(k), "id": k, "n": n} for k, n in tally.items()], key=lambda x: -x["n"])
    elif gm == "draw":
        drawer = G.get("drawer", "")
        v["draw"] = {"drawer": drawer, "drawername": _pname(drawer), "word": G.get("word", "") if pid == drawer else "",
                     "hint": " ".join("_" if c.isalpha() else c for c in G.get("word", "")) if pid != drawer else "",
                     "strokes": G.get("strokes", []), "guessed": [_pname(x) for x in G.get("guessed", [])], "iguessed": pid in G.get("guessed", []),
                     "left": int(max(0, G.get("until", 0) - now)), "log": G.get("log", [])[-12:], "round": G.get("round", 0), "last": G.get("lastword", "")}
    elif gm == "c4":
        v["c4"] = {"seats": [{"id": x, "name": _pname(x)} if x else None for x in G.get("seats", [None, None])], "board": G.get("board", []),
                   "turn": G.get("turn", 0), "win": G.get("win", -1), "line": G.get("line", [])}
    elif gm in MORE_GAMES:
        party_view_more(pid, v, G, gm, now)
    return v


def _c4_win(b):
    for r in range(6):
        for c in range(7):
            p = b[r][c]
            if p < 0:
                continue
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                cells = [(r + i * dr, c + i * dc) for i in range(4)]
                if all(0 <= rr < 6 and 0 <= cc < 7 and b[rr][cc] == p for rr, cc in cells):
                    return p, cells
    return -1, []


def _draw_next():
    G = PARTY["g"]
    ids = [k for k, v in PARTY["players"].items() if time.time() - v["t"] < 40]
    if not ids:
        return
    cur = G.get("drawer", "")
    nxt = ids[(ids.index(cur) + 1) % len(ids)] if cur in ids else ids[0]
    used = G.setdefault("used", [])
    pool = [w for w in WORDS if w not in used] or WORDS
    w = random.choice(pool); used.append(w)
    G.update(lastword=G.get("word", ""), drawer=nxt, word=w, strokes=[], guessed=[], until=time.time() + 90, round=G.get("round", 0) + 1)
    G.setdefault("log", []).append({"n": "🎨", "t": f"{_pname(nxt)} zeichnet jetzt."})


def party_tick():
    """time based things (drawing: next round when the time is over)"""
    if PARTY["game"] == "draw":
        G = PARTY["g"]
        if G.get("drawer") and time.time() > G.get("until", 0):
            G.setdefault("log", []).append({"n": "⏰", "t": "Zeit um! Es war: " + G.get("word", "")})
            _draw_next(); party_bump()
    party_tick_more()


# ---- more party games (2.95.32): Stadt-Land-Fluss, estimating, explaining (taboo), battleships, reaction, who am I ----
SLF_CATS = ["Stadt", "Land", "Fluss", "Tier", "Beruf", "Name"]
SLF_LETTERS = "ABCDEFGHIKLMNOPRSTUVWZ"
SCHAETZ = [("Wie hoch ist der Eiffelturm (mit Antennen)?", 330, "m"), ("Wie viele Einwohner hat die Schweiz (Millionen, 2024)?", 9, "Mio."),
           ("Wie lang ist der Rhein?", 1230, "km"), ("Wie viele Knochen hat ein erwachsener Mensch?", 206, ""),
           ("Wie schwer ist ein ausgewachsener Afrikanischer Elefant (Bulle)?", 6000, "kg"), ("Wie hoch ist das Matterhorn?", 4478, "m"),
           ("Wie viele Tasten hat ein Klavier?", 88, ""), ("Wie weit ist der Mond von der Erde entfernt?", 384400, "km"),
           ("Wie viele Liter Blut hat ein erwachsener Mensch?", 5, "l"), ("Wie lang ist der Gotthard-Basistunnel?", 57, "km"),
           ("Wie viele Gemeinden hat die Schweiz (ungefähr, 2024)?", 2130, ""), ("Wie schnell fliegt ein Wanderfalke im Sturzflug höchstens?", 390, "km/h"),
           ("Wie tief ist der Lago Maggiore an der tiefsten Stelle?", 372, "m"), ("Wie viele Herzschläge hat ein Mensch in Ruhe pro Minute (Mittel)?", 70, ""),
           ("Wie alt kann eine Riesenschildkröte werden?", 150, "Jahre"), ("Wie viele Stacheln hat ein Igel?", 7000, ""),
           ("Wie viele Länder gibt es auf der Welt (UNO-Mitglieder)?", 193, ""), ("Wie hoch ist der Mount Everest?", 8849, "m"),
           ("Wie lang ist die Chinesische Mauer (alle Teile)?", 21196, "km"), ("Wie viele Kilometer Wanderwege hat die Schweiz (ungefähr)?", 65000, "km"),
           ("Wie viele Kühe gibt es in der Schweiz (ungefähr)?", 1500000, ""), ("Wie gross ist der Bodensee?", 536, "km²"),
           ("Wie viele Zähne hat ein Hund?", 42, ""), ("Wie heiss ist die Oberfläche der Sonne?", 5500, "°C"),
           ("Wie lange braucht Licht vom Mond zur Erde?", 1.3, "s"), ("Wie viele Augen hat eine Spinne meistens?", 8, ""),
           ("In welchem Jahr wurde die Schweiz (Bundesstaat) gegründet?", 1848, ""), ("Wie schnell ist ein Gepard höchstens?", 110, "km/h"),
           ("Wie viele Stockwerke hat der Burj Khalifa?", 163, ""), ("Wie viele Federn hat ein Schwan (ungefähr)?", 25000, ""),
           ("Wie lang ist ein Blauwal höchstens?", 30, "m"), ("Wie viele Kilometer Bahnnetz hat die Schweiz (ungefähr)?", 5300, "km"),
           ("Wie viele Kalorien hat eine Tafel Milchschokolade (100 g)?", 540, "kcal"), ("Wie hoch fliegt ein Linienflugzeug normalerweise?", 11000, "m"),
           ("Wie viele Sterne sieht man nachts ohne Fernglas höchstens (ungefähr)?", 4500, ""), ("Wie viele Seen hat die Schweiz (grösser als 0,5 ha, ungefähr)?", 1500, ""),
           ("Wie viele Stunden schläft eine Katze pro Tag?", 15, "h"), ("Wie lang ist die Aare?", 288, "km"),
           ("Wie viele Erdbeeren wachsen ungefähr an einer Pflanze pro Saison?", 50, ""), ("Wie viele Liter Milch gibt eine Kuh pro Tag (Durchschnitt CH)?", 22, "l")]
TABU = [("Fondue", ["Käse", "Caquelon", "Brot", "Schmelzen"]), ("Zelt", ["Camping", "Schlafen", "Hering", "Plane"]), ("Lagerfeuer", ["Holz", "Wärme", "Flamme", "Wurst"]),
        ("Schokolade", ["Kakao", "Süss", "Milch", "Tafel"]), ("Gotthard", ["Tunnel", "Pass", "Tessin", "Uri"]), ("Kuh", ["Milch", "Muh", "Weide", "Glocke"]),
        ("Ski", ["Schnee", "Piste", "Fahren", "Winter"]), ("Velo", ["Fahrrad", "Pedal", "Lenker", "Rad"]), ("Zug", ["SBB", "Schiene", "Bahnhof", "Lok"]),
        ("Kamera", ["Foto", "Bild", "Objektiv", "Linse"]), ("Igel", ["Stacheln", "Tier", "Winterschlaf", "Rollen"]), ("Gewitter", ["Blitz", "Donner", "Regen", "Sturm"]),
        ("Regenbogen", ["Farben", "Regen", "Sonne", "Himmel"]), ("Pirat", ["Schiff", "Schatz", "Augenklappe", "Meer"]), ("Rakete", ["Weltall", "Start", "Mond", "Fliegen"]),
        ("Zahnbürste", ["Zähne", "Putzen", "Zahnpasta", "Bad"]), ("Kühlschrank", ["Kalt", "Küche", "Essen", "Tür"]), ("Pizza", ["Italien", "Teig", "Käse", "Tomate"]),
        ("Feuerwehr", ["Brand", "Löschen", "Rot", "Schlauch"]), ("Leuchtturm", ["Licht", "Meer", "Schiffe", "Turm"]), ("Schneemann", ["Schnee", "Karotte", "Winter", "Bauen"]),
        ("Uhr", ["Zeit", "Zeiger", "Stunde", "Tick"]), ("Brille", ["Augen", "Sehen", "Gläser", "Nase"]), ("Geburtstag", ["Kuchen", "Geschenk", "Party", "Jahr"]),
        ("Gitarre", ["Saiten", "Musik", "Spielen", "Instrument"]), ("Hexe", ["Besen", "Zaubern", "Märchen", "Hut"]), ("Spinne", ["Netz", "Acht", "Beine", "Insekt"]),
        ("Sonnenbrille", ["Sonne", "Augen", "Dunkel", "Sommer"]), ("Kompass", ["Norden", "Nadel", "Richtung", "Wandern"]), ("Rucksack", ["Tragen", "Rücken", "Wandern", "Tasche"]),
        ("Schlafsack", ["Schlafen", "Zelt", "Warm", "Camping"]), ("Taschenlampe", ["Licht", "Dunkel", "Batterie", "Leuchten"]), ("Wasserfall", ["Wasser", "Fallen", "Fluss", "Rauschen"]),
        ("Vulkan", ["Lava", "Ausbruch", "Berg", "Feuer"]), ("Pinguin", ["Eis", "Vogel", "Schwarz", "Antarktis"]), ("Elefant", ["Rüssel", "Gross", "Grau", "Afrika"]),
        ("Giraffe", ["Hals", "Lang", "Flecken", "Afrika"]), ("Biene", ["Honig", "Summen", "Stechen", "Blume"]), ("Fussball", ["Tor", "Ball", "Spieler", "Kicken"]),
        ("Polizei", ["Verbrecher", "Blaulicht", "Uniform", "Gesetz"]), ("Arzt", ["Krank", "Spital", "Medizin", "Doktor"]), ("Bäcker", ["Brot", "Backen", "Mehl", "Gipfeli"]),
        ("Helikopter", ["Fliegen", "Rotor", "Rettung", "Hubschrauber"]), ("Brücke", ["Fluss", "Über", "Bauen", "Überqueren"]), ("Schlüssel", ["Tür", "Schloss", "Öffnen", "Bund"]),
        ("Kerze", ["Wachs", "Licht", "Docht", "Flamme"]), ("Regenschirm", ["Regen", "Nass", "Aufspannen", "Schutz"]), ("Weihnachten", ["Baum", "Geschenke", "Dezember", "Christkind"]),
        ("Ostern", ["Hase", "Eier", "Suchen", "Frühling"]), ("Märchen", ["Prinzessin", "Es war einmal", "Grimm", "Geschichte"]), ("Drache", ["Feuer", "Flügel", "Ritter", "Spucken"]),
        ("Roboter", ["Maschine", "Metall", "Computer", "Programm"]), ("Handy", ["Telefon", "Anrufen", "Smartphone", "App"]), ("Bergsteiger", ["Klettern", "Gipfel", "Seil", "Berg"]),
        ("Seilbahn", ["Gondel", "Berg", "Seil", "Fahren"]), ("Muesli", ["Haferflocken", "Frühstück", "Bircher", "Milch"]), ("Alphorn", ["Blasen", "Lang", "Holz", "Musik"]),
        ("Murmeltier", ["Pfeifen", "Alpen", "Winterschlaf", "Bau"]), ("Edelweiss", ["Blume", "Alpen", "Weiss", "Berg"]), ("Schwingen", ["Sägemehl", "Ringen", "Hosen", "Schwinger"])]
WHO = ["Fuchs", "Eule", "Igel", "Murmeltier", "Steinbock", "Pinguin", "Elefant", "Giraffe", "Krokodil", "Delfin", "Biene", "Schnecke", "Katze", "Hund",
       "Pferd", "Kuh", "Feuerwehrfrau", "Bäcker", "Astronautin", "Pirat", "Zauberer", "Hexe", "Ritter", "Prinzessin", "Lokführer", "Pilotin", "Koch",
       "Bergführer", "Polizist", "Ärztin", "Lehrer", "Rotkäppchen", "Schneewittchen", "Froschkönig", "Rumpelstilzchen", "Weihnachtsmann", "Osterhase",
       "Schneemann", "Roboter", "Drache", "Gespenst", "Vampir", "Dinosaurier", "Einhorn", "Meerjungfrau", "Bär", "Wolf", "Adler", "Känguru", "Koala"]


def _slf_norm(t):
    t = str(t or "").strip().lower()
    for a, b in (("ä", "a"), ("ö", "o"), ("ü", "u"), ("é", "e"), ("è", "e"), ("à", "a"), ("ç", "c")):
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t)


def _slf_results():
    """points per player and per answer: 20 = only one in this category, 10 = unique, 5 = same as someone else, 0 = invalid"""
    G = PARTY["g"]; L = G.get("letter", "").lower(); veto = set(G.get("veto", [])); res = {}
    for i, _c in enumerate(G.get("cats", [])):
        valid = {}
        for pid, A in G.get("ans", {}).items():
            a = _slf_norm(A.get(str(i), ""))
            if a and a[0] == L and f"{pid}|{i}" not in veto:
                valid[pid] = a
        cnt = {}
        for a in valid.values():
            cnt[a] = cnt.get(a, 0) + 1
        for pid in G.get("ans", {}):
            pts = 0
            if pid in valid:
                pts = 20 if len(valid) == 1 else (10 if cnt[valid[pid]] == 1 else 5)
            res.setdefault(pid, {})[str(i)] = pts
    return res


def _ships_place():
    """ships 4,3,3,2,2 on 8x8, not touching each other; returns a list of cell lists"""
    for _ in range(200):
        taken, ships = set(), []
        ok = True
        for n in (4, 3, 3, 2, 2):
            for _t in range(200):
                hor = random.random() < 0.5
                x = random.randrange(8 - (n - 1 if hor else 0)); y = random.randrange(8 - (0 if hor else n - 1))
                cells = [(x + k, y) if hor else (x, y + k) for k in range(n)]
                if all((cx + dx, cy + dy) not in taken for cx, cy in cells for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    ships.append([list(c) for c in cells]); taken.update(cells); break
            else:
                ok = False; break
        if ok:
            return ships
    return []


def _ships_new(seats=None):
    return {"seats": seats or [None, None], "ships": [_ships_place(), _ships_place()], "shots": [[], []], "ready": [False, False],
            "turn": 0, "win": -1, "last": None}


def _ships_hit(ships, x, y):
    for s in ships:
        if [x, y] in s:
            return s
    return None


def _react_done():
    G = PARTY["g"]
    if G.get("phase") not in ("wait",):
        return
    act = [k for k, v in PARTY["players"].items() if time.time() - v["t"] < 40 and k != PARTY["host"] or k == PARTY["host"] and G.get("hostplays")]
    if time.time() > G.get("go_at", 0) + 6 or (act and all(k in G.get("res", {}) for k in act)):
        ok = {k: v for k, v in G.get("res", {}).items() if v >= 0}
        G["phase"] = "done"
        if ok:
            best = min(ok, key=ok.get); G["winner"] = best
            p = _pl(best)
            if p:
                p["score"] += 1
        party_bump()


def party_tick_more():
    G = PARTY["g"]; gm = PARTY["game"]; now = time.time()
    if gm == "slf" and G.get("phase") == "play" and G.get("stop_at") and now > G["stop_at"]:
        G["phase"] = "review"; party_bump()
    elif gm == "taboo" and G.get("phase") == "turn" and now > G.get("until", 0):
        G["phase"] = "pause"; G.setdefault("log", []).append(f"⏰ Zeit um! {_pname(G.get('explainer'))} hat {G.get('turn_n', 0)} Begriffe erklärt.")
        party_bump()
    elif gm == "react":
        _react_done()


def party_act_more(pid, a, d, host, G):
    """actions of the new games; returns None when the action is not theirs"""
    gm = PARTY["game"]; me = _pl(pid); now = time.time()
    if gm == "slf":
        if a == "cats" and host and G.get("phase") != "play":
            cats = [c.strip()[:20] for c in str(d.get("t") or "").split(",") if c.strip()][:10]
            if cats:
                G["cats"] = cats
        elif a == "start" and host:
            used = G.setdefault("used", [])
            pool = [c for c in SLF_LETTERS if c not in used] or list(SLF_LETTERS)
            L = random.choice(pool); used.append(L)
            G.update(phase="play", letter=L, ans={}, veto=[], stop_at=0, stop_by="", round=G.get("round", 0) + 1, awarded=False)
        elif a == "ans" and G.get("phase") == "play":
            i = str(int(d.get("i", 0)))
            if int(i) < len(G.get("cats", [])):
                G.setdefault("ans", {}).setdefault(pid, {})[i] = str(d.get("t") or "")[:40]
                return "quiet"                         # no bump for every letter typed
        elif a == "stop" and G.get("phase") == "play" and not G.get("stop_at"):
            A = G.get("ans", {}).get(pid, {})
            if sum(1 for i in range(len(G["cats"])) if A.get(str(i), "").strip()) < len(G["cats"]):
                return "Zuerst alles ausfüllen"
            G.update(stop_at=now + 10, stop_by=pid)
        elif a == "end" and host and G.get("phase") == "play":
            G["phase"] = "review"
        elif a == "veto" and host and G.get("phase") == "review":
            k = f"{d.get('id')}|{int(d.get('i', 0))}"; v = G.setdefault("veto", [])
            v.remove(k) if k in v else v.append(k)
        elif a == "award" and host and G.get("phase") == "review" and not G.get("awarded"):
            for p_, R in _slf_results().items():
                if _pl(p_):
                    _pl(p_)["score"] += sum(R.values()) // 5          # 5 table points = 1 game point
            G.update(awarded=True, phase="setup")
        else:
            return "Gerade nicht möglich"
        return ""
    if gm == "guess":
        if a == "next" and host:
            used = G.setdefault("used", [])
            pool = [i for i in range(len(SCHAETZ)) if i not in used] or list(range(len(SCHAETZ)))
            qi = random.choice(pool); used.append(qi)
            G.update(qi=qi, phase="ask", g={}, n=G.get("n", 0) + 1, win=[])
        elif a == "guess" and G.get("phase") == "ask" and not host:
            try:
                v = float(str(d.get("n", "")).replace("'", "").replace(",", ".").replace(" ", ""))
            except ValueError:
                return "Bitte eine Zahl"
            if not math.isfinite(v) or abs(v) > 1e15:
                return "Bitte eine Zahl"
            G.setdefault("g", {})[pid] = v
        elif a == "reveal" and host and G.get("phase") == "ask":
            ans = SCHAETZ[G["qi"]][1]; gs = G.get("g", {})
            if gs:
                best = min(abs(v - ans) for v in gs.values())
                G["win"] = [k for k, v in gs.items() if abs(v - ans) == best]
                for k in G["win"]:
                    if _pl(k):
                        _pl(k)["score"] += 1
            G["phase"] = "reveal"
        else:
            return "Gerade nicht möglich"
        return ""
    if gm == "taboo":
        if a == "start" and (host or pid == G.get("next_up")) and G.get("phase") != "turn":
            ids = [k for k, v in PARTY["players"].items() if now - v["t"] < 40]
            cur = G.get("explainer", "")
            nxt = ids[(ids.index(cur) + 1) % len(ids)] if cur in ids else (ids[0] if ids else pid)
            G.update(phase="turn", explainer=nxt, until=now + int(G.get("secs", 60)), turn_n=0, round=G.get("round", 0) + 1)
            _taboo_word(G)
        elif a == "secs" and host and G.get("phase") != "turn":
            G["secs"] = max(30, min(180, int(d.get("s", 60))))
        elif a in ("ok", "taboo", "skip") and G.get("phase") == "turn" and pid == G.get("explainer"):
            w = TABU[G["wi"]][0]
            if a == "ok":
                by = d.get("by") if d.get("by") in PARTY["players"] and d.get("by") != pid else ""
                me["score"] += 1; G["turn_n"] = G.get("turn_n", 0) + 1
                if by:
                    _pl(by)["score"] += 1
                G.setdefault("log", []).append(f"✅ {w}" + (f" – erraten von {_pname(by)}" if by else ""))
            else:
                G.setdefault("log", []).append(("🚫 Tabu: " if a == "taboo" else "⏭ ") + w)
            _taboo_word(G)
        else:
            return "Gerade nicht möglich"
        return ""
    if gm == "ships":
        seat = G["seats"].index(pid) if pid in G["seats"] else -1
        if a == "sit":
            i = int(d.get("seat", 0)) % 2
            if not G["seats"][i] and seat < 0:
                G["seats"][i] = pid
        elif a == "leave" and seat >= 0:
            G["seats"][seat] = None; G["ready"] = [False, False]
        elif a == "shuffle" and seat >= 0 and not all(G["ready"]):
            G["ships"][seat] = _ships_place(); G["ready"][seat] = False
        elif a == "ready" and seat >= 0:
            G["ready"][seat] = True
        elif a == "shoot":
            if not all(G["ready"]) or None in G["seats"] or G["win"] >= 0 or seat != G["turn"]:
                return "Du bist nicht dran"
            x, y = int(d.get("x", -1)), int(d.get("y", -1))
            if not (0 <= x < 8 and 0 <= y < 8) or [x, y] in G["shots"][seat]:
                return "Nicht möglich"
            G["shots"][seat].append([x, y])
            s = _ships_hit(G["ships"][1 - seat], x, y)
            G["last"] = {"by": seat, "x": x, "y": y, "hit": bool(s), "sunk": bool(s) and all(c in G["shots"][seat] for c in s)}
            if all(c in G["shots"][seat] for sh in G["ships"][1 - seat] for c in sh):
                G["win"] = seat
                if _pl(pid):
                    _pl(pid)["score"] += 1
            elif not s:
                G["turn"] = 1 - seat
        elif a == "reset":
            if seat < 0 and not host:
                return "Nicht möglich"
            PARTY["g"] = _ships_new([G["seats"][1], G["seats"][0]])
        else:
            return "Gerade nicht möglich"
        return ""
    if gm == "react":
        if a == "start" and host and G.get("phase") != "wait":
            G.update(phase="wait", go_at=now + 2.5 + random.random() * 3.5, res={}, winner="", round=G.get("round", 0) + 1)
        elif a == "hostplays" and host:
            G["hostplays"] = not G.get("hostplays")
        elif a == "tap" and G.get("phase") == "wait" and pid not in G.get("res", {}):
            if host and not G.get("hostplays"):
                return "Gerade nicht möglich"
            try:
                ms = float(d.get("ms", -1))
            except (TypeError, ValueError):
                ms = -1
            early = now < G["go_at"] - 0.15 or ms < 0
            G.setdefault("res", {})[pid] = -1 if early else max(80.0, min(5000.0, ms))
            _react_done()
        else:
            return "Gerade nicht möglich"
        return ""
    if gm == "whoami":
        if a == "start" and host:
            ids = list(PARTY["players"]); pool = random.sample(WHO, min(len(WHO), len(ids)))
            G.update(roles=dict(zip(ids, pool)), solved=[], round=G.get("round", 0) + 1)
        elif a == "solved" and pid in G.get("roles", {}) and pid not in G.get("solved", []):
            G.setdefault("solved", []).append(pid)
            n = len(G["solved"])
            me["score"] += 3 if n == 1 else 2 if n == 2 else 1
        else:
            return "Gerade nicht möglich"
        return ""
    return None


def _taboo_word(G):
    used = G.setdefault("used", [])
    pool = [i for i in range(len(TABU)) if i not in used] or list(range(len(TABU)))
    G["wi"] = random.choice(pool); used.append(G["wi"])


def party_view_more(pid, v, G, gm, now):
    host = v["host"]
    if gm == "slf":
        R = _slf_results() if G.get("phase") == "review" else {}
        A = G.get("ans", {})
        done = [p for p, X in A.items() if sum(1 for i in range(len(G.get("cats", []))) if X.get(str(i), "").strip()) >= len(G.get("cats", []))]
        v["slf"] = {"phase": G.get("phase", "setup"), "cats": G.get("cats", SLF_CATS), "letter": G.get("letter", ""), "round": G.get("round", 0),
                    "mine": A.get(pid, {}), "stop_by": _pname(G["stop_by"]) if G.get("stop_by") else "", "stop_left": max(0, G.get("stop_at", 0) - now) if G.get("stop_at") else -1,
                    "done": [_pname(p) for p in done]}
        if G.get("phase") == "review" or G.get("awarded"):
            v["slf"]["table"] = [{"id": p, "name": _pname(p), "ans": [A[p].get(str(i), "") for i in range(len(G.get("cats", [])))],
                                  "pts": [R.get(p, {}).get(str(i), 0) for i in range(len(G.get("cats", [])))],
                                  "veto": [f"{p}|{i}" in G.get("veto", []) for i in range(len(G.get("cats", [])))]} for p in A]
    elif gm == "guess":
        q = SCHAETZ[G["qi"]] if "qi" in G else None
        v["guess"] = {"phase": G.get("phase", "setup"), "q": q[0] if q else "", "unit": q[2] if q else "", "n": G.get("n", 0),
                      "count": len(G.get("g", {})), "mine": G.get("g", {}).get(pid)}
        if G.get("phase") == "reveal" and q:
            v["guess"]["answer"] = q[1]
            v["guess"]["list"] = sorted([{"name": _pname(k), "v": x, "d": abs(x - q[1]), "win": k in G.get("win", [])} for k, x in G.get("g", {}).items()], key=lambda r: r["d"])
        if host and q:
            v["guess"]["answer"] = q[1]
    elif gm == "taboo":
        ex = G.get("explainer", "")
        ids = [k for k, x in PARTY["players"].items() if now - x["t"] < 40]
        nxt = ids[(ids.index(ex) + 1) % len(ids)] if ex in ids else (ids[0] if ids else "")
        G["next_up"] = nxt
        v["taboo"] = {"phase": G.get("phase", "setup"), "explainer": ex, "explainername": _pname(ex) if ex else "", "left": max(0, int(G.get("until", 0) - now)),
                      "secs": G.get("secs", 60), "log": G.get("log", [])[-10:], "n": G.get("turn_n", 0), "next": nxt, "nextname": _pname(nxt) if nxt else ""}
        if pid == ex and G.get("phase") == "turn":
            v["taboo"]["word"], v["taboo"]["forbidden"] = TABU[G["wi"]]
    elif gm == "ships":
        seat = G["seats"].index(pid) if pid in G["seats"] else -1
        def board(i, show_ships):           # board of seat i: what was shot on it
            shots = G["shots"][1 - i]
            cells = [[0] * 8 for _ in range(8)]   # 0 water, 1 ship (own only), 2 miss, 3 hit, 4 sunk
            if show_ships:
                for s in G["ships"][i]:
                    for x, y in s:
                        cells[y][x] = 1
            for x, y in shots:
                s = _ships_hit(G["ships"][i], x, y)
                cells[y][x] = (4 if all(c in shots for c in s) else 3) if s else 2
            return cells
        left = lambda i: sum(1 for s in G["ships"][i] if not all(c in G["shots"][1 - i] for c in s))
        v["ships"] = {"seats": [{"id": x, "name": _pname(x)} if x else None for x in G["seats"]], "seat": seat, "ready": G["ready"], "turn": G["turn"],
                      "win": G["win"], "last": G.get("last"), "left": [left(0), left(1)],
                      "boards": [board(i, i == seat or G["win"] >= 0) for i in (0, 1)]}
    elif gm == "react":
        v["react"] = {"phase": G.get("phase", "idle"), "go_at": G.get("go_at", 0), "round": G.get("round", 0), "hostplays": bool(G.get("hostplays")),
                      "res": sorted([{"name": _pname(k), "ms": x, "me": k == pid} for k, x in G.get("res", {}).items()], key=lambda r: (r["ms"] < 0, r["ms"])),
                      "mine": G.get("res", {}).get(pid), "winner": _pname(G["winner"]) if G.get("winner") else ""}
    elif gm == "whoami":
        R = G.get("roles", {}); S = G.get("solved", [])
        v["whoami"] = {"round": G.get("round", 0), "others": [{"name": _pname(k), "word": w, "solved": k in S} for k, w in R.items() if k != pid],
                       "mine": R.get(pid, "") if pid in S else "", "have": pid in R, "solved": pid in S, "order": [_pname(k) for k in S]}

MORE_GAMES = ("slf", "guess", "taboo", "ships", "react", "whoami")


def party_act(pid, d):
    """one action of a phone; returns an error text or ''"""
    me = _pl(pid)
    if not me:
        return "please join first"
    me["t"] = time.time()
    a = str(d.get("a") or ""); host = PARTY["host"] == pid; G = PARTY["g"]
    if a == "quit":                                    # 2.95.36: a player leaves the game corner
        PARTY["players"].pop(pid, None)
        for k_ in ("seats",):
            if isinstance(G.get(k_), list):
                G[k_] = [None if x == pid else x for x in G[k_]]
        if host:
            PARTY["host"] = next((k for k, v in PARTY["players"].items() if time.time() - v["t"] < 60), next(iter(PARTY["players"]), ""))
        return ""
    if a == "game":                                    # the host chooses the game
        if not host:
            return "only the host"
        gm = str(d.get("game") or "lobby")
        if gm not in ("lobby", "quiz", "wolf", "draw", "c4") + MORE_GAMES:
            return "unknown game"
        PARTY["game"] = gm; PARTY["g"] = {}
        if gm == "slf":
            PARTY["g"] = {"phase": "setup", "cats": SLF_CATS[:]}
        if gm == "ships":
            PARTY["g"] = _ships_new()
        if gm == "c4":
            PARTY["g"] = {"seats": [None, None], "board": [[-1] * 7 for _ in range(6)], "turn": 0, "win": -1}
        if gm == "wolf":
            n = len(PARTY["players"]) - 1
            PARTY["g"] = {"phase": "setup", "cfg": {"wolf": max(1, n // 4), "seer": 1 if n >= 4 else 0, "witch": 1 if n >= 6 else 0}}
        if gm == "draw":
            _draw_next()
    elif a == "makehost":
        if not host and PARTY["host"] in PARTY["players"]:
            return "only the host"
        if d.get("id") in PARTY["players"]:
            PARTY["host"] = d["id"]
    elif a == "score":                                 # the host changes points (scoreboard)
        if not host:
            return "only the host"
        p = _pl(d.get("id"))
        if p:
            p["score"] += max(-10, min(10, int(d.get("n", 1))))
    elif a == "resetscores":
        if not host:
            return "only the host"
        for p in PARTY["players"].values():
            p["score"] = 0
    elif a == "dice":                                  # tools for everybody
        n = max(1, min(6, int(d.get("n", 1)))); sides = int(d.get("sides", 6)) if int(d.get("sides", 6)) in (4, 6, 8, 10, 12, 20) else 6
        PARTY["tools"]["dice"] = {"by": me["name"], "vals": [random.randint(1, sides) for _ in range(n)], "sides": sides, "t": time.time()}
    elif a == "timer":
        s_ = max(0, min(3600, int(d.get("s", 60))))
        PARTY["tools"]["timer"] = {"by": me["name"], "end": time.time() + s_, "s": s_} if s_ else {}
    elif PARTY["game"] in MORE_GAMES:
        r_ = party_act_more(pid, a, d, host, G)
        if r_ is None:
            return "unknown action"
        if r_ == "quiet":
            PARTY["_quiet"] = True; r_ = ""
        return r_
    elif PARTY["game"] == "quiz":
        if a == "buzz":
            if G.get("phase") == "open" and pid not in G.get("order", []) and not host:
                G.setdefault("order", []).append(pid)
                if len(G["order"]) == 1:
                    G["phase"] = "locked"
        elif not host:
            return "only the host"
        elif a == "open":
            G.update(phase="open", order=[])
        elif a == "right":
            if G.get("order"):
                p = _pl(G["order"][0])
                if p:
                    p["score"] += 1
            G.update(phase="wait", order=[], qi=G.get("qi", 0) + (0 if G.get("own") else 1), show=False)
        elif a == "wrong":
            if G.get("order"):
                G["order"].pop(0)
            G["phase"] = "locked" if G.get("order") else "open"
        elif a == "nextq":
            G.update(qi=G.get("qi", random.randrange(len(QUIZ))) + 1, phase="wait", order=[], show=False, own="")
        elif a == "showq":
            G["show"] = not G.get("show")
    elif PARTY["game"] == "wolf":
        if a == "vote":
            if G.get("voting") and G.get("alive", {}).get(pid) and d.get("id") in G.get("alive", {}):
                G.setdefault("votes", {})[pid] = d["id"]
        elif not host:
            return "only the narrator"
        elif a == "cfg":
            for k in ("wolf", "seer", "witch"):
                if k in d:
                    G.setdefault("cfg", {})[k] = max(0, min(6, int(d[k])))
        elif a == "start":
            ids = [k for k in PARTY["players"] if k != PARTY["host"]]
            c = G.get("cfg", {}); roles = ["wolf"] * c.get("wolf", 1) + ["seer"] * c.get("seer", 0) + ["witch"] * c.get("witch", 0)
            if len(ids) < len(roles) + 1:
                return "too few players"
            roles += ["villager"] * (len(ids) - len(roles)); random.shuffle(roles)
            G.update(roles=dict(zip(ids, roles)), alive={k: True for k in ids}, phase="night", step=0, votes={}, voting=False, winner="",
                     text=WOLF_NIGHT[0])
        elif a == "next":
            if G.get("phase") == "night":
                G["step"] = G.get("step", 0) + 1
                if G["step"] >= len(WOLF_NIGHT):
                    G.update(phase="day", step=0)
            elif G.get("phase") == "day":
                G["step"] = G.get("step", 0) + 1
                if G["step"] >= len(WOLF_DAY):
                    G.update(phase="night", step=0)
            G["text"] = (WOLF_NIGHT if G.get("phase") == "night" else WOLF_DAY)[G.get("step", 0)]
        elif a == "kill":
            if d.get("id") in G.get("alive", {}):
                G["alive"][d["id"]] = not G["alive"][d["id"]]
        elif a == "voteopen":
            G.update(voting=True, votes={})
        elif a == "voteclose":
            G["voting"] = False
        if G.get("roles"):
            al = [k for k, x in G.get("alive", {}).items() if x]
            w = sum(1 for k in al if G["roles"].get(k) == "wolf")
            G["winner"] = "Das Dorf gewinnt! 🎉" if w == 0 else ("Die Werwölfe gewinnen! 🐺" if w >= len(al) - w else "")
    elif PARTY["game"] == "draw":
        if a == "stroke" and pid == G.get("drawer"):
            pts = d.get("p") or []
            if isinstance(pts, list) and len(G.get("strokes", [])) < 1500:
                pts = [[round(float(x), 3), round(float(y), 3)] for x, y in pts[:200] if 0 <= float(x) <= 1 and 0 <= float(y) <= 1]
                col = d.get("c") if re.fullmatch(r"#[0-9a-fA-F]{6}", str(d.get("c") or "")) else "#000000"
                G.setdefault("strokes", []).append({"p": pts, "c": col, "w": max(1, min(30, int(d.get("w", 4))))})
        elif a == "clear" and pid == G.get("drawer"):
            G["strokes"] = []
        elif a == "skip" and (pid == G.get("drawer") or host):
            G.setdefault("log", []).append({"n": "⏭", "t": "Übersprungen. Es war: " + G.get("word", "")}); _draw_next()
        elif a == "guess" and pid != G.get("drawer") and pid not in G.get("guessed", []):
            txt = str(d.get("t") or "")[:40].strip()
            norm = lambda s_: re.sub(r"[^a-z0-9äöü]", "", s_.lower().replace("ss", "ß").replace("ß", "ss"))
            if txt and norm(txt) == norm(G.get("word", "")):
                G.setdefault("guessed", []).append(pid)
                me["score"] += 2 if len(G["guessed"]) == 1 else 1
                dr = _pl(G.get("drawer"))
                if dr:
                    dr["score"] += 1
                G.setdefault("log", []).append({"n": "✅", "t": f"{me['name']} hat es erraten!"})
                others = [k for k, v in PARTY["players"].items() if k != G.get("drawer") and time.time() - v["t"] < 40]
                if set(others) <= set(G["guessed"]):
                    G.setdefault("log", []).append({"n": "🎉", "t": "Alle haben es! Es war: " + G.get("word", "")}); _draw_next()
            elif txt:
                G.setdefault("log", []).append({"n": me["name"], "t": txt})
        elif a == "start" and host:
            _draw_next()
    elif PARTY["game"] == "c4":
        if a == "sit":
            i = int(d.get("seat", 0)) % 2
            if not G["seats"][i] and pid not in G["seats"]:
                G["seats"][i] = pid
        elif a == "drop":
            if G.get("win", -1) >= 0 or None in G["seats"] or G["seats"][G["turn"]] != pid:
                return "not your turn"
            c = int(d.get("col", 0))
            if not 0 <= c < 7:
                return "bad column"
            for r in range(5, -1, -1):
                if G["board"][r][c] < 0:
                    G["board"][r][c] = G["turn"]; break
            else:
                return "column full"
            w, line = _c4_win(G["board"])
            if w >= 0:
                G.update(win=w, line=line); p = _pl(G["seats"][w])
                if p:
                    p["score"] += 1
            elif all(G["board"][0][x] >= 0 for x in range(7)):
                G["win"] = 2
            else:
                G["turn"] = 1 - G["turn"]
        elif a == "reset":
            G.update(board=[[-1] * 7 for _ in range(6)], turn=0, win=-1, line=[])
            if d.get("swap"):
                G["seats"] = [G["seats"][1], G["seats"][0]]
        elif a == "leave":
            G["seats"] = [None if x == pid else x for x in G["seats"]]
    else:
        return "unknown action"
    return ""


def games_dir():
    return os.path.join(DATA_DIR, "games")


