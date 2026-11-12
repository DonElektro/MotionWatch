#@ MoveEye – Teil 639zzw: «🎒 Packlisten» im Datentausch (/tausch/packlisten) – Listen mit Gewicht, Anzahl, Kategorie, Foto, «gepackt» und «fehlt noch / kaufen», Import aus Text / CSV / Excel / Notizen mit Vorschau, gemeinsam packen
# ----------------------------------------------------------------------------
# Wunsch des Besitzers (11.11.2026, Entscheide fest):
#   * Ort: ein Bereich «🎒 Packlisten» im Datentausch (Kachel auf /tausch, Seite /tausch/packlisten) – nicht im Almanach.
#   * Import aus Textdateien (ein Gegenstand pro Zeile), Excel (.xlsx), CSV und eingefügtem Text (Notizen-App). Die Formate
#     sind verschieden: tolerant lesen, IMMER zuerst eine Vorschau (Spalten zuordnen, Zeilen korrigieren, abwählen), nie blind.
#   * Rechte wie der Datentausch, kein neues Recht: «Dateien: ansehen» (files_view) sieht die Listen, «Dateien: hochladen»
#     (files_up) bearbeitet sie (anlegen, abhaken, Fotos, Import); eine Liste löscht, wer sie angelegt hat, oder files_admin.
#     «Nur ich» (area mine) wie «Meine Dateien». Gäste (Gast-Link, Schalter tausch_guest): nur ansehen, wie beim Datentausch –
#     gemeinsame Listen mit Stand und Vorschaubildern, kein Abhaken, keine Namen.
#   * Bilder: ein Foto vom Handy pro Gegenstand (Kamera oder Mediathek) über DENSELBEN Weg in Stücken wie der Datentausch
#     (639zzc: tausch_up_start / chunk / finish, hier nur um das Ziel «pack» erweitert; das Skript der Seite ist dasselbe,
#     aus TAUSCH_PAGE herausgeschnitten). Gespeichert wird nur neu Gerechnetes (320 px + 1280 px JPEG), nie die Original-Bytes.
#     HEIC: die Seite rechnet das Foto vor dem Senden im Browser zu JPEG um (Safari kann HEIC zeichnen); geht das nicht und
#     kommt HEIC an, sagt MoveEye es klar (OpenCV liest kein HEIC). Ohne Foto: ein gezeichnetes Symbol der Kategorie.
#   * Dazu: Gewichtsziel pro Liste (Balken, «… darüber / darunter»), «Fehlt noch / kaufen» mit eigener Einkaufsansicht,
#     gemeinsam packen (jedes Handy hakt ab, alle sehen den Stand). Nicht gewünscht: Ablaufdatum, Lagerort.
# Gebaut:
#   * Gegenstand: Name, Gewicht pro Stück (frei eingegeben – «350 g», «1.2 kg», «0,5kg» – gespeichert in Gramm), Anzahl,
#     Kategorie (12 feste mit Symbol + eigene), Notiz, Foto, «gepackt», «kaufen», Art: Basisgewicht / Verbrauch (Essen, Wasser,
#     Gas) / am Körper getragen. Summen pro Liste und Kategorie; das Ziel gilt für den Rucksack (Basis + Verbrauch).
#   * Mehrere Listen, Vorlagen (Tagestour, Zeltnacht, Winter – Richtwerte), Liste kopieren, alle Häkchen zurücksetzen,
#     sortieren / filtern / suchen, Druckansicht, Export CSV (gegen Formeln geschützt), JSON (die Datei der Liste) und ZIP
#     (JSON + Fotos).
#   * Speicher: einfache Dateien im Ordner des Datentausches: pack/<Nummer>.json (eine Liste, lesbares JSON) und
#     pack/b/<Liste>/<Gegenstand>.jpg (+ _p.jpg). Geschrieben wird immer zuerst in eine Nebendatei, dann umbenannt (nie eine
#     halbe Liste). Der Datentausch ist in KEINER Sicherung von MoveEye (639zzc) – darum der ZIP-Export pro Liste.
#   * Gemeinsam packen: jede Änderung nennt nur ihren Gegenstand und ihre Felder; das Gerät führt sie zusammen (zwei Handys
#     haken verschiedene Sachen ab: beides bleibt; dasselbe Feld zweimal: das letzte gilt) und zählt den Stand der Liste hoch
#     («rev»). Die offene Liste fragt alle 3 s nach dem, was seit ihrem Stand neu ist, und zeigt «geändert von … vor 5 s».
#   * Grenzen: 100 Listen, 500 Gegenstände pro Liste, Import-Datei 5 MB, eingefügter Text 200 KB, Foto 25 MB (gespeichert
#     ≤ 1280 px), alle Fotos zusammen 1 GB; der freie Platz und die Ratenbremse des Datentausches gelten mit.
#   * Sicherheit: alles vom Benutzer wird auf der Seite nur als Text gesetzt (textContent), in Druck- und Gast-Seite
#     html.escape; Excel: kleines eigenes Lesen (ZIP + XML, erstes Blatt, gemeinsame Texte), Formeln werden nie gerechnet,
#     höchstens PL_X_ENTRIES Einträge / PL_X_TOTAL entpackt, kein DOCTYPE / ENTITY im XML; CSV-Export: Zellen, die mit
#     = + - @ beginnen, bekommen ein Hochkomma; Dateinamen der Listen und Fotos sind nur geprüfte Nummern.
# Tests: werkzeuge/packlisten_test.py, Selbsttest pl_selftest unten.
# ----------------------------------------------------------------------------
import io as _pl_io
import unicodedata as _pl_ud

PL_MAX_LISTS = 100
PL_MAX_ITEMS = 500
PL_NAME_MAX = 120
PL_NOTE_MAX = 300
PL_CAT_MAX = 40
PL_IMPORT_MAX = 5 * 1024 * 1024                           # an import file (text, CSV, xlsx)
PL_TEXT_MAX = 200 * 1024                                  # pasted text
PL_ROWS_MAX = 2000                                        # rows read from a table
PL_COLS_MAX = 30
PL_PHOTO_MAX = 25 * 1024 * 1024                           # one photo as it comes from the phone (stored: 320 px + 1280 px)
PL_PHOTO_TOTAL = 1024 ** 3                                # all stored photos of all lists
PL_X_ENTRIES = 300                                        # xlsx: files inside the ZIP
PL_X_TOTAL = 40 * 1024 * 1024                             # xlsx: unpacked size of everything / of what is read
PL_X_RATIO = 250                                          # xlsx: unpacked / packed of one entry (a bomb is far above)
PL_GONE_MAX = 300                                         # deleted items a list remembers for the other phones
PL_IID = re.compile(r"^[0-9a-f]{8}$")
PL = {"lock": threading.RLock(), "root": None, "lists": None, "photo_bytes": 0}

for _p in TZ_PERMS:                                       # role_guard (550) lets these through, the routes check the exact right
    PERM_POST[_p] = set(PERM_POST.get(_p, ())) | {"/api/tausch/pack", "/api/tausch/pack/import"}

# key, English name (= text key), colour, symbol (24 × 24, drawn for MoveEye: lines only)
PL_CATS = (
    ("sleep", "Sleeping", "#8b9bff", "M2.5 20h19M12 5 3.5 20M12 5l8.5 15M12 12.5 9 20M12 12.5l3 7.5"),
    ("clothes", "Clothes", "#f472b6", "M8.5 3.5 3 6.5l2 4.2 2.8-1.2V20.5h8.4V9.5l2.8 1.2 2-4.2-5.5-3c-.5 1.7-1.8 2.7-3.5 2.7S9 5.2 8.5 3.5z"),
    ("kitchen", "Kitchen", "#f59a4a", "M5 10.5h14v5.5a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4zM2.8 10.5h18.4M9.5 7c0-1.6 1.4-1.4 1.4-3M13.5 7c0-1.6 1.4-1.4 1.4-3"),
    ("food", "Food", "#fb7185", "M12 7.6c-1.8-1.9-6.8-1.6-6.8 3.9 0 4.8 3.3 8.8 5.3 8.8.7 0 1-.5 1.5-.5s.8.5 1.5.5c2 0 5.3-4 5.3-8.8 0-5.5-5-5.8-6.8-3.9zM12 7.6c0-2 .9-3.4 2.8-4.1"),
    ("water", "Water", "#38bdf8", "M12 3c3.9 4.9 6.3 7.9 6.3 11.4a6.3 6.3 0 0 1-12.6 0C5.7 10.9 8.1 7.9 12 3zM9.2 15.2a2.9 2.9 0 0 0 2.6 2.6"),
    ("hygiene", "Hygiene", "#2dd4bf", "M8.5 10h7v9.5a1 1 0 0 1-1 1h-5a1 1 0 0 1-1-1zM11 10V6.5M9 6.5h4.5l2.5-1.8M10.5 14h3"),
    ("firstaid", "First aid", "#f87171", "M4 7.5h16a1 1 0 0 1 1 1V19a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V8.5a1 1 0 0 1 1-1zM9 7.5V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2.5M12 10.8v6M9 13.8h6"),
    ("tools", "Tools & repair", "#a8b3c4", "M4 20.5 12.5 12M10 9.5l4.5-4.5 5 5-1.8 1.8-3.2-3.2-2.7 2.7zM14.5 5l2-1.5"),
    ("electronics", "Electronics", "#facc15", "M3.5 8h14a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1h-14a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1zM21.3 10.5v3M11.5 9.8l-2.6 2.6h3.2l-2.6 2.6"),
    ("navigation", "Navigation", "#34d399", "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM15.8 8.2l-2.2 5.4-5.4 2.2 2.2-5.4z"),
    ("documents", "Documents & money", "#c084fc", "M7 3h7l4 4v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM14 3v4h4M9 12h6M9 16h6"),
    ("other", "Miscellaneous", "#8a9bb0", "M3.5 8 12 3.5 20.5 8v8L12 20.5 3.5 16zM3.5 8l8.5 4.5L20.5 8M12 12.5v8"),
)
PL_CAT_KEYS = tuple(c[0] for c in PL_CATS)
PL_KINDS = ("base", "cons", "worn")
# headings and column values -> category (lower case, de / en / fr / it; the start of the word is enough)
PL_CAT_WORDS = {
    "sleep": ("schlaf", "zelt", "übernacht", "uebernacht", "biwak", "sleep", "shelter", "tent", "camp", "dormir", "couchage",
              "tente", "tenda"),
    "clothes": ("kleid", "bekleid", "klamott", "wäsche", "waesche", "schuh", "anzieh", "cloth", "wear", "apparel", "vêtement", "vetement", "habit",
                "vestit", "abbigl"),
    "kitchen": ("küche", "kueche", "koch", "geschirr", "kitchen", "cook", "cuisine", "cucina"),
    "food": ("essen", "verpfleg", "proviant", "nahrung", "lebensmittel", "food", "snack", "nourrit", "repas", "cibo", "mangiare", "aliment"),
    "water": ("wasser", "trinken", "getränk", "getraenk", "water", "drink", "hydrat", "eau", "boisson", "acqua", "bevand"),
    "hygiene": ("hygien", "körperpfleg", "koerperpfleg", "pflege", "toilet", "wasch", "kosmetik", "bad", "igiene", "soin"),
    "firstaid": ("erste hilfe", "erste-hilfe", "apothek", "medik", "medizin", "notfall", "sicherheit", "first aid", "first-aid", "emergency", "safety", "pharmac", "secours",
                 "pronto soccorso", "farmac", "urgence"),
    "tools": ("werkzeug", "reparatur", "flick", "tool", "repair", "outil", "attrezz", "utensil"),
    "electronics": ("elektr", "technik", "strom", "akku", "foto", "kamera", "electr", "tech", "gadget", "power", "camera", "électr", "elettr"),
    "navigation": ("navig", "orientier", "karte", "map", "carte", "orientation", "orientamento"),
    "documents": ("dokument", "papier", "ausweis", "geld", "wertsachen", "document", "money", "paper", "argent", "soldi", "denaro"),
    "other": ("sonstig", "divers", "anderes", "übrig", "uebrig", "kleinkram", "misc", "other", "various", "autre", "altro", "vari"),
}
# a word in the name of an item -> category (only when the import gives none)
PL_CAT_GUESS = (
    ("firstaid", ("pflaster", "verband", "erste hilfe", "erste-hilfe", "first aid", "rettungsdecke", "blasen", "zeckenzange", "schmerz", "tablette",
                  "medikament", "desinfekt", "notfall", "pfeife", "biwaksack")),
    ("water", ("wasser", "trinkflasche", "trinkblase", "thermos", "wasserfilter", "water", "bottle", "bidon")),
    ("food", ("riegel", "müesli", "muesli", "müsli", "brot", "käse", "kaese", "schokolade", "nüsse", "nuesse", "trockenfleisch", "landjäger", "tee",
              "kaffee", "suppe", "pasta", "reis", "essen", "proviant", "snack", "frühstück", "abendessen", "mittagessen", "znüni", "zvieri",
              "food", "meal", "salz", "zucker", "wurst", "apfel", "trockenfrüchte")),
    ("kitchen", ("kocher", "gaskartusche", "gas", "brennstoff", "spiritus", "topf", "pfanne", "tasse", "becher", "löffel", "loeffel", "göffel", "gabel",
                 "besteck", "teller", "feuerzeug", "zündh", "streichh", "schwamm", "abwasch", "stove", "pot", "spork", "lighter")),
    ("sleep", ("zelt", "schlafsack", "isomatte", "matte", "kissen", "hering", "heringe", "zeltunterlage", "footprint", "tarp", "hängematte", "inlett",
               "biwak", "tent", "sleeping", "pillow")),
    ("clothes", ("jacke", "hose", "socken", "shirt", "pullover", "fleece", "mütze", "muetze", "kappe", "handschuh", "unterwäsche", "unterhose",
                 "regenjacke", "regenhose", "daunen", "schuhe", "sandalen", "gamaschen", "buff", "schal", "hemd", "leggings", "badehose",
                 "sonnenhut", "jacket", "socks", "gloves", "trousers", "pants")),
    ("hygiene", ("zahnbürste", "zahnbuerste", "zahnpasta", "seife", "handtuch", "wc-papier", "toilettenpapier", "wc papier", "sonnencreme",
                 "sonnenschutz", "deo", "taschentücher", "mückenschutz", "insektenschutz", "feuchttücher", "lippen", "toothbrush", "soap", "towel")),
    ("electronics", ("stirnlampe", "lampe", "powerbank", "akku", "batterie", "ladekabel", "kabel", "handy", "telefon", "kamera", "kopfhörer",
                     "ladegerät", "solarpanel", "moveeye", "headlamp", "charger", "phone", "camera")),
    ("navigation", ("karte", "kompass", "gps", "höhenmesser", "wanderführer", "map", "compass")),
    ("documents", ("ausweis", "pass", "identitätskarte", "geld", "bargeld", "kreditkarte", "bankkarte", "halbtax", "billett", "ticket", "schlüssel",
                   "schluessel", "versicherung", "passport", "wallet", "portemonnaie", "money", "keys")),
    ("tools", ("messer", "taschenmesser", "multitool", "klebeband", "panzertape", "tape", "schnur", "reepschnur", "kabelbinder", "nähzeug", "flickzeug",
               "karabiner", "säge", "schaufel", "knife", "repair", "cord", "stöcke", "stoecke", "wanderstöcke")),
)
PL_WATER_GEAR = ("flasche", "filter", "bottle", "blase", "thermos", "bidon", "sack", "beutel", "becher", "gourde", "borraccia", "kanister")
PL_CONS_WORDS = ("gaskartusche", "gas ", "brennstoff", "spiritus", "benzin", "sonnencreme", "wc-papier", "toilettenpapier", "zahnpasta", "fuel")
# templates: (category, grams per piece, number, kind, (Deutsch, English, français, italiano)); Romansh uses German
PL_TEMPLATES = (
    ("day", ("Tagestour", "Day hike", "Randonnée d’un jour", "Gita di un giorno"), (
        ("other", 900, 1, "base", ("Rucksack 25 l", "Backpack 25 l", "Sac à dos 25 l", "Zaino 25 l")),
        ("clothes", 350, 1, "base", ("Regenjacke", "Rain jacket", "Veste de pluie", "Giacca antipioggia")),
        ("clothes", 300, 1, "base", ("Warme Schicht (Fleece)", "Warm layer (fleece)", "Couche chaude (polaire)", "Strato caldo (pile)")),
        ("clothes", 70, 1, "base", ("Mütze oder Sonnenhut", "Hat or sun hat", "Bonnet ou chapeau", "Berretto o cappello")),
        ("clothes", 1100, 1, "worn", ("Wanderschuhe", "Hiking boots", "Chaussures de marche", "Scarponi")),
        ("water", 1000, 1, "cons", ("Wasser 1 l", "Water 1 l", "Eau 1 l", "Acqua 1 l")),
        ("water", 150, 1, "base", ("Trinkflasche", "Water bottle", "Gourde", "Borraccia")),
        ("food", 400, 1, "cons", ("Mittagessen und Riegel", "Lunch and bars", "Pique-nique et barres", "Pranzo e barrette")),
        ("firstaid", 200, 1, "base", ("Erste-Hilfe-Set", "First-aid kit", "Trousse de secours", "Kit di pronto soccorso")),
        ("firstaid", 60, 1, "base", ("Rettungsdecke", "Rescue blanket", "Couverture de survie", "Telo termico")),
        ("hygiene", 80, 1, "cons", ("Sonnencreme", "Sunscreen", "Crème solaire", "Crema solare")),
        ("navigation", 90, 1, "base", ("Karte", "Map", "Carte", "Cartina")),
        ("electronics", 200, 1, "worn", ("Handy", "Phone", "Téléphone", "Telefono")),
        ("electronics", 85, 1, "base", ("Stirnlampe", "Headlamp", "Lampe frontale", "Lampada frontale")),
        ("tools", 70, 1, "base", ("Taschenmesser", "Pocket knife", "Couteau de poche", "Coltellino")),
        ("documents", 40, 1, "worn", ("Ausweis und Geld", "ID and money", "Pièce d’identité et argent", "Documento e soldi")),
    )),
    ("camp", ("Zeltnacht", "Night in the tent", "Nuit sous tente", "Notte in tenda"), (
        ("other", 1600, 1, "base", ("Rucksack 50 l", "Backpack 50 l", "Sac à dos 50 l", "Zaino 50 l")),
        ("sleep", 1800, 1, "base", ("Zelt", "Tent", "Tente", "Tenda")),
        ("sleep", 950, 1, "base", ("Schlafsack", "Sleeping bag", "Sac de couchage", "Sacco a pelo")),
        ("sleep", 480, 1, "base", ("Isomatte", "Sleeping mat", "Matelas", "Materassino")),
        ("sleep", 80, 1, "base", ("Kissen", "Pillow", "Oreiller", "Cuscino")),
        ("kitchen", 90, 1, "base", ("Gaskocher", "Gas stove", "Réchaud à gaz", "Fornello a gas")),
        ("kitchen", 200, 1, "cons", ("Gaskartusche 100 g", "Gas canister 100 g", "Cartouche de gaz 100 g", "Cartuccia di gas 100 g")),
        ("kitchen", 250, 1, "base", ("Topf", "Pot", "Casserole", "Pentola")),
        ("kitchen", 20, 1, "base", ("Löffel", "Spoon", "Cuillère", "Cucchiaio")),
        ("kitchen", 15, 1, "base", ("Feuerzeug", "Lighter", "Briquet", "Accendino")),
        ("food", 600, 1, "cons", ("Abendessen und Frühstück", "Dinner and breakfast", "Souper et déjeuner", "Cena e colazione")),
        ("food", 300, 1, "cons", ("Riegel und Nüsse", "Bars and nuts", "Barres et noix", "Barrette e noci")),
        ("water", 2000, 1, "cons", ("Wasser 2 l", "Water 2 l", "Eau 2 l", "Acqua 2 l")),
        ("water", 150, 2, "base", ("Trinkflasche", "Water bottle", "Gourde", "Borraccia")),
        ("clothes", 350, 1, "base", ("Regenjacke", "Rain jacket", "Veste de pluie", "Giacca antipioggia")),
        ("clothes", 320, 1, "base", ("Daunenjacke", "Down jacket", "Doudoune", "Piumino")),
        ("clothes", 80, 2, "base", ("Socken", "Socks", "Chaussettes", "Calze")),
        ("clothes", 180, 1, "base", ("Schlafkleider", "Sleeping clothes", "Habits de nuit", "Vestiti per la notte")),
        ("clothes", 1100, 1, "worn", ("Wanderschuhe", "Hiking boots", "Chaussures de marche", "Scarponi")),
        ("hygiene", 60, 1, "base", ("Zahnbürste und Zahnpasta", "Toothbrush and toothpaste", "Brosse à dents et dentifrice", "Spazzolino e dentifricio")),
        ("hygiene", 50, 1, "cons", ("WC-Papier", "Toilet paper", "Papier WC", "Carta igienica")),
        ("firstaid", 200, 1, "base", ("Erste-Hilfe-Set", "First-aid kit", "Trousse de secours", "Kit di pronto soccorso")),
        ("electronics", 85, 1, "base", ("Stirnlampe", "Headlamp", "Lampe frontale", "Lampada frontale")),
        ("electronics", 230, 1, "base", ("Powerbank", "Power bank", "Batterie externe", "Powerbank")),
        ("electronics", 200, 1, "worn", ("Handy", "Phone", "Téléphone", "Telefono")),
        ("navigation", 90, 1, "base", ("Karte", "Map", "Carte", "Cartina")),
        ("tools", 70, 1, "base", ("Taschenmesser", "Pocket knife", "Couteau de poche", "Coltellino")),
        ("documents", 40, 1, "worn", ("Ausweis und Geld", "ID and money", "Pièce d’identité et argent", "Documento e soldi")),
    )),
    ("winter", ("Winter", "Winter", "Hiver", "Inverno"), (
        ("other", 1200, 1, "base", ("Rucksack 35 l", "Backpack 35 l", "Sac à dos 35 l", "Zaino 35 l")),
        ("clothes", 450, 1, "base", ("Hardshell-Jacke", "Hardshell jacket", "Veste hardshell", "Giacca hardshell")),
        ("clothes", 420, 1, "base", ("Daunenjacke", "Down jacket", "Doudoune", "Piumino")),
        ("clothes", 250, 1, "worn", ("Thermo-Unterwäsche", "Thermal underwear", "Sous-vêtements thermiques", "Intimo termico")),
        ("clothes", 150, 2, "base", ("Handschuhe (dünn + dick)", "Gloves (thin + thick)", "Gants (fins + épais)", "Guanti (sottili + spessi)")),
        ("clothes", 80, 1, "base", ("Mütze", "Warm hat", "Bonnet", "Berretto")),
        ("clothes", 60, 1, "base", ("Halstuch (Buff)", "Neck gaiter", "Tour de cou", "Scaldacollo")),
        ("clothes", 90, 1, "base", ("Ersatzsocken", "Spare socks", "Chaussettes de rechange", "Calze di ricambio")),
        ("clothes", 1600, 1, "worn", ("Winterschuhe", "Winter boots", "Chaussures d’hiver", "Scarponi invernali")),
        ("clothes", 200, 1, "base", ("Gamaschen", "Gaiters", "Guêtres", "Ghette")),
        ("other", 1900, 1, "base", ("Schneeschuhe", "Snowshoes", "Raquettes", "Racchette da neve")),
        ("other", 500, 1, "base", ("Stöcke mit grossen Tellern", "Poles with big baskets", "Bâtons avec grandes rondelles", "Bastoncini con rotelle grandi")),
        ("water", 600, 1, "base", ("Thermosflasche", "Thermos flask", "Thermos", "Thermos")),
        ("water", 750, 1, "cons", ("Heisser Tee 0,75 l", "Hot tea 0.75 l", "Thé chaud 0,75 l", "Tè caldo 0,75 l")),
        ("food", 500, 1, "cons", ("Essen und Riegel", "Food and bars", "Repas et barres", "Cibo e barrette")),
        ("firstaid", 200, 1, "base", ("Erste-Hilfe-Set", "First-aid kit", "Trousse de secours", "Kit di pronto soccorso")),
        ("firstaid", 60, 1, "base", ("Rettungsdecke", "Rescue blanket", "Couverture de survie", "Telo termico")),
        ("firstaid", 110, 1, "base", ("Biwaksack", "Bivouac bag", "Sac de bivouac", "Sacco da bivacco")),
        ("hygiene", 80, 1, "cons", ("Sonnencreme und Lippenschutz", "Sunscreen and lip balm", "Crème solaire et baume à lèvres", "Crema solare e burrocacao")),
        ("other", 40, 1, "base", ("Sonnenbrille", "Sunglasses", "Lunettes de soleil", "Occhiali da sole")),
        ("electronics", 85, 1, "base", ("Stirnlampe", "Headlamp", "Lampe frontale", "Lampada frontale")),
        ("electronics", 230, 1, "base", ("Powerbank (warm tragen)", "Power bank (keep it warm)", "Batterie externe (au chaud)", "Powerbank (al caldo)")),
        ("electronics", 200, 1, "worn", ("Handy", "Phone", "Téléphone", "Telefono")),
        ("navigation", 90, 1, "base", ("Karte", "Map", "Carte", "Cartina")),
        ("documents", 40, 1, "worn", ("Ausweis und Geld", "ID and money", "Pièce d’identité et argent", "Documento e soldi")),
    )),
)


PL_HEIC_MSG = "This photo is HEIC - MoveEye cannot read that format. Choose it from the photo library (Safari then sends JPEG) or set the camera to «Most compatible»."


class PLError(Exception):
    """a refused import / change: the message is an English text key (tr)"""


# ---- small things: text, weight, category -----------------------------------------------------------------------------------
def pl_text(s, n):
    """one line of user text: NFC, no control / direction characters, single spaces, at most n characters"""
    if not isinstance(s, str):
        s = "" if s is None or isinstance(s, (dict, list, bool)) else str(s)
    s = _TZ_CTRL.sub("", _pl_ud.normalize("NFC", s).replace("\t", " ").replace(" ", " ").replace("\n", " "))
    return re.sub(r"\s{2,}", " ", s).strip()[:n].strip()


def pl_num(s, thousands3=False):
    """«1.2», «0,5», «1'200», «1.234,5» -> float (None = no number). thousands3: «1.200» means 1200 (grams)"""
    s = str(s).strip().replace("'", "").replace("’", "").replace(" ", "").replace(" ", "")
    if not re.fullmatch(r"\d+(?:[.,]\d+)*", s):
        return None
    seps = [i for i, ch in enumerate(s) if ch in ".,"]
    if not seps:
        return float(s)
    last = seps[-1]
    head, dec = re.sub(r"[.,]", "", s[:last]), s[last + 1:]
    if len(seps) > 1 and len({s[i] for i in seps}) == 1 and all(len(p) == 3 for p in re.split(r"[.,]", s)[1:]):
        return float(head + dec)                           # 1.234.567
    if thousands3 and len(seps) == 1 and len(dec) == 3 and head.strip("0"):
        return float(head + dec)
    return float((head or "0") + "." + dec)


_PL_N = r"\d{1,6}(?:[.,'’]\d{1,3})*"
_PL_W_RE = re.compile(r"(?<![\w.,'’])(" + _PL_N + r")\s*(kilogramm|kilogram|kilos?|kg|gramm|grams?|gr|g|oz|lbs?)(?![\w])\.?", re.I)
_PL_L_RE = re.compile(r"(?<![\w.,'’])(" + _PL_N + r")\s*(ml|cl|dl|liter|litres?|lt|l)(?![\w])\.?", re.I)
_PL_UNIT_G = {"kg": 1000.0, "kilo": 1000.0, "kilos": 1000.0, "kilogramm": 1000.0, "kilogram": 1000.0, "g": 1.0, "gr": 1.0, "gramm": 1.0,
              "gram": 1.0, "grams": 1.0, "oz": 28.3495, "lb": 453.592, "lbs": 453.592}


def _pl_grams(num, unit):
    u = unit.lower()
    v = pl_num(num, thousands3=u in ("g", "gr", "gramm", "gram", "grams"))
    if v is None:
        return None
    g = int(round(v * _PL_UNIT_G[u]))
    if v > 0 and g == 0:
        g = 1
    return g if 0 < g <= 500000 else None


def pl_weight(text, unit="g"):
    """a weight as people type it -> grams (int) or None: «350 g», «1.2 kg», «0,5kg», «1'200», «12 oz»; a bare number = unit"""
    if isinstance(text, bool) or text is None:
        return None
    if isinstance(text, (int, float)):
        text = repr(float(text))
    s = str(text).strip()
    if not s:
        return None
    m = _PL_W_RE.search(s)
    if m:
        return _pl_grams(m.group(1), m.group(2))
    m = re.fullmatch(r"[~≈]?\s*(" + _PL_N + r")", s)
    if m:
        return _pl_grams(m.group(1), "kg" if unit == "kg" else "g")
    return None


def pl_fmt_g(g, lang=None):
    """«350 g», «1,2 kg» (comma in de / fr / it / rm), «–» for unknown"""
    if g is None:
        return "–"
    g = int(g)
    if g < 1000:
        return f"{g} g"
    s = f"{g / 1000:.2f}".rstrip("0").rstrip(".")
    return (s if cur_lang(lang) == "en" else s.replace(".", ",")) + " kg"


def pl_cat_key(text):
    """a heading / a column value -> one of the fixed categories, else the cleaned text itself (an own category)"""
    s = pl_text(text, PL_CAT_MAX).strip(" :-–—#*=_")
    if not s:
        return "other"
    low = s.lower()
    if low in PL_CAT_KEYS:
        return low
    for key, en, _c, _p in PL_CATS:                           # the names of the categories in every language
        if low == en.lower() or any(low == tr(en, L).lower() for L in ("de", "fr", "it", "rm")):
            return key
    for key, words in PL_CAT_WORDS.items():
        if any(low.startswith(w) or (" " + w) in low or ("-" + w) in low or ("/" + w) in low or ("&" + w) in low.replace(" ", "") for w in words):
            return key
    return s[:1].upper() + s[1:]


def pl_cat_clean(text):
    """a category as it is stored: one of the fixed keys (also by its name in any language), else the user's own text"""
    s = pl_text(text, PL_CAT_MAX)
    low = s.lower()
    if not s or low in PL_CAT_KEYS:
        return low or "other"
    for key, en, _c, _p in PL_CATS:
        if low == en.lower() or any(low == tr(en, L).lower() for L in ("de", "fr", "it", "rm")):
            return key
    return s


# a row of a table with one single cell is a heading only when it is clearly one (an item without a weight looks the same)
PL_HEAD_EXACT = {"schlafen", "kleider", "kleidung", "bekleidung", "küche", "kochen", "essen", "verpflegung", "proviant", "trinken", "hygiene",
                 "erste hilfe", "apotheke", "werkzeug", "elektronik", "technik", "navigation", "dokumente", "sonstiges", "diverses"}


def pl_cat_guess(name):
    low = " " + name.lower() + " "
    for key, words in PL_CAT_GUESS:
        if any(w in low for w in words):
            return key
    return "other"


def pl_cat_head(text):
    """a heading of the user: a fixed category when it is exactly its name, else his own words stay («Tourenausrüstung»)"""
    c = pl_cat_clean(str(text).strip(" :-–—#*=_"))
    if c == c.upper() and c != c.lower():                    # «TOURENAUSRÜSTUNG» -> «Tourenausrüstung»
        c = pl_cat_clean(" ".join(w[:1] + w[1:].lower() for w in c.split(" ")))
    return c if c in PL_CAT_KEYS else c[:1].upper() + c[1:]


def pl_cat_icon(cat):
    """the fixed category whose symbol (and rules) an own category gets: «Kleidung» -> clothes"""
    k = cat if cat in PL_CAT_KEYS else pl_cat_key(cat)
    return k if k in PL_CAT_KEYS else "other"


def pl_kind_auto(cat, name):
    """food and drink are consumables, a bottle or a filter is not; also gas, fuel, sunscreen … (the user can change it per item)"""
    low = " " + name.lower() + " "
    cat = pl_cat_icon(cat)
    if any(w in low for w in PL_CONS_WORDS) or (cat in ("food", "water") and not any(w in low for w in PL_WATER_GEAR)):
        return "cons"
    return "base"


# ---- one line of a note -> an item or a heading ------------------------------------------------------------------------------
_PL_BOX = re.compile(r"^\s*(?:[-*+•]\s*)?(?:\[\s?([xX✓✔]?)\s?\]|([☐☑☒✅✔✓]))\s*")
_PL_BULLET = re.compile(r"^\s*(?:[-*+•‣◦⁃∙·–—▪▫●○◯■□➤►>]+\s*|\d{1,3}[.)]\s+)")
_PL_BUY = re.compile(r"\s*(?:[(\[]\s*(?:noch\s+)?(?:kaufen|fehlt noch|fehlt|besorgen|einkaufen|to buy|buy|acheter|comprare)\s*!*\s*[)\]]"
                     r"|(?:\s[-–—→>:,;!]+|!+)\s*(?:noch\s+)?(?:kaufen|fehlt noch|fehlt|besorgen|einkaufen)\s*!*)\s*$", re.I)
_PL_QTY_A = re.compile(r"^(\d{1,3})\s*(?:[x×]\s+|×|x(?=[^a-zäöü\s]))(?=\S)")       # «2x Socken», «2 x Socken», «2×Socken» - not «3 XL Shirts»
_PL_QTY_B = re.compile(r"^(\d{1,3})\s*(?:stk\.?|stück|stueck|st\.|pcs?\.?|pz\.?)\s+", re.I)
_PL_QTY_Z = re.compile(r"(?:\s+|(?=[(\[]))[(\[]?\s*(?:(\d{1,3})\s*(?:[x×]|[sS]tk\.?|[sS]tück|[sS]tueck|pcs?\.?)|[x×]\s*(\d{1,3}))\s*[)\]]?\s*$")
_PL_NOQTY = {"m", "cm", "mm", "km", "l", "ml", "dl", "cl", "w", "v", "a", "mah", "ah", "wh", "x", "in", "ft", "°c", "c", "h", "min", "tage", "tag",
             "days", "day", "nächte", "nacht", "jahre", "uhr", "kg", "g", "gr", "prozent", "lumen", "lm", "fach", "mal", "er", "liter"}
_PL_EDGE = " \t-–—:,;|=~/→·•"


def _pl_tidy(s):
    s = re.sub(r"[(\[]\s*(?:ca\.?|etwa|je|à|a|~|≈|each|per|pro stück|pro stk\.?)?\s*[)\]]", " ", s, flags=re.I)
    s = re.sub(r"(?:\s|^)(?:ca\.?|etwa|je|à|~|≈|pro stück|pro stk\.?)\s*$", "", s, flags=re.I)
    s = re.sub(r"\s{2,}", " ", s.replace("\t", " ")).strip(_PL_EDGE)
    return re.sub(r"\s+([,;:])", r"\1", s)


PL_LINE_MAX = 500                                         # one line of a note / a pasted text (a name has 120, a remark 300)


def _pl_fence(t):
    """«== Küche ==», «**KLEIDUNG**», «--- Essen ---»: the text between the same signs at both ends, or None. Written out
    by hand (3.83.2): as one pattern with a back reference a line of 4000 signs took more than 25 s (it tried every split)."""
    m = re.match(r"[=*_~]{2,}", t)
    if m:
        f = m.group(0)
        h = t[len(f):len(t) - len(f)].strip() if len(t) > 2 * len(f) and t.endswith(f) else ""
        return h if h and h[0] not in "=*_~" else None
    m = re.match(r"-{3,}", t)
    if m:
        for k in range(min(len(m.group(0)), len(t) - len(t.rstrip("-")), (len(t) - 1) // 2), 2, -1):
            h = t[k:len(t) - k].strip()
            if h and h[0] not in "=*_~":
                return h
    return None


def pl_parse_line(raw):
    """("cat", text) for a heading, ("item", {...}) for an item, None for nothing (empty, a rule, only signs)"""
    s = _TZ_CTRL.sub("", _pl_ud.normalize("NFC", str(raw)[:8 * PL_LINE_MAX]).replace(" ", " ").replace(" ", " ")).rstrip()
    if not s.strip():
        return None
    lead = len(s) - len(s.lstrip())                          # 3.83.2: runs of blanks inside the line are one blank, and a line has an
    s = s[:lead] + re.sub(r"[ \t]{2,}", " ", s[lead:])[:PL_LINE_MAX]    # end - the patterns below need time by the square of the length
    m = re.match(r"^\s*#{1,6}\s*(.+?)\s*#*\s*$", s)
    f = None if m else _pl_fence(s.strip())
    if m or f is not None:
        h = pl_text(m.group(1) if m else f, PL_CAT_MAX).strip(_PL_EDGE)
        return ("cat", h) if h else None
    if re.fullmatch(r"[\s\-=_*~#.·•]+", s):
        return None
    packed, marked = None, False
    m = _PL_BOX.match(s)
    if m:
        packed, marked, s = bool(m.group(1)) or (m.group(2) or "") in "☑☒✅✔✓" and bool(m.group(2)), True, s[m.end():]
    else:
        m = _PL_BULLET.match(s)
        if m:
            marked, s = True, s[m.end():]
    s = s.strip()
    if not s:
        return None
    has_w = bool(_PL_W_RE.search(s))
    if s.endswith(":") and not has_w and len(s) <= 60 and packed is None:
        h = pl_text(s[:-1], PL_CAT_MAX).strip(_PL_EDGE)
        return ("cat", h) if h else None
    letters = [ch for ch in s if ch.isalpha()]
    if (not marked and len(letters) >= 4 and s == s.upper() and s != s.lower() and not re.search(r"\d", s) and len(s) <= 40):
        return ("caps", pl_text(s, PL_CAT_MAX).strip(_PL_EDGE))
    buy = False
    m = _PL_BUY.search(s)
    if m and m.start() > 0:
        buy, s = True, s[:m.start()]
    g, note = None, ""
    ms = list(_PL_W_RE.finditer(s))
    if ms:
        m = ms[-1]
        g = _pl_grams(m.group(1), m.group(2))
        s = s[:m.start()] + " " + s[m.end():]
    else:
        m = re.match(r"^(.*?[^\W\d].*?)(?:\t+\s*|\s+[-–—:|=]\s*|:\s+|\s{3,})[~≈]?(" + _PL_N + r")\s*$", s)
        if m:                                                # «Zelt – 1800», «Zelt<Tab>1800»: a bare number at the end = grams
            g, s = _pl_grams(m.group(2), "g"), m.group(1)
    ml = list(_PL_L_RE.finditer(s))
    rest = _pl_tidy(s[:ml[-1].start()] + " " + s[ml[-1].end():]).lower() if ml else ""
    if re.search(r"wasser|water|tee\b|saft|getränk|benzin|spiritus|milch|wein|bier|öl\b|sirup|kaffee|eau\b|acqua|drink", rest) and not any(
            w in rest for w in PL_WATER_GEAR):               # litres of a liquid: a note. «Tasche (20-30 Liter)», «Topf 1 l»: part of the name
        m = ml[-1]
        note = m.group(1) + " " + m.group(2).lower().replace("liter", "l").replace("litres", "l").replace("litre", "l").replace("lt", "l")
        s = s[:m.start()] + " " + s[m.end():]
    s = _pl_tidy(s)
    n = 1
    m = _PL_QTY_A.match(s) or _PL_QTY_B.match(s)
    if m:
        n, s = int(m.group(1)), s[m.end():]
    else:
        m = _PL_QTY_Z.search(s)
        if m and m.start() > 0 and ("(" in m.group(0) or "[" in m.group(0) or int(m.group(1) or m.group(2)) <= 20):   # not «Garmin 64x»
            n, s = int(m.group(1) or m.group(2)), s[:m.start()]
        else:
            m = re.match(r"^(\d{1,2})\s+([^\W\d][^\s]*)", s)
            if m and m.group(2).lower().strip(".") not in _PL_NOQTY:
                n, s = int(m.group(1)), s[m.end(1):]
    name = pl_text(_pl_tidy(s), PL_NAME_MAX)
    if not name or not any(ch.isalnum() for ch in name):
        return None
    return ("item", {"name": name, "g": g, "n": max(1, min(999, n)), "note": note, "packed": bool(packed), "buy": buy})


def pl_parse_text(text):
    """a note with one item per line -> {"items": [...], "skipped": n}; headings become categories"""
    lines = str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")[:PL_ROWS_MAX * 2]
    parsed = [pl_parse_line(ln) for ln in lines]
    real = [p for p in parsed if p]
    caps = sum(1 for p in real if p[0] == "caps")
    caps_are_items = caps > 0 and caps * 2 > len(real)        # everything is written in capitals: these are items, not headings
    items, skipped, cat, title, heads = [], 0, None, "", []
    idx = [i for i, p in enumerate(parsed) if p]
    # a bare line («Schlafen») is a heading only when the structure shows it; a plain list (one item per line) stays a list
    mark = [bool(_PL_BOX.match(ln) or _PL_BULLET.match(ln) or re.match(r"(?: {2,}|\t)\S", ln)) for ln in lines]

    def bare(i):
        p = parsed[i]
        return bool(p and p[0] == "item" and not mark[i] and p[1]["g"] is None and p[1]["n"] == 1 and not p[1]["note"] and not p[1]["buy"])
    B, M, up = [i for i in idx if bare(i)], [i for i in idx if mark[i] and parsed[i][0] == "item"], []
    if M and len(M) >= len(B):                               # A: a bare line right above bulleted / numbered / ticked / indented lines
        up = [i for i in B if i + 1 < len(lines) and mark[i + 1] and parsed[i + 1]]
    elif not M:                                              # B: no bullets at all - blocks between empty lines, each led by a bare line
        blocks, cur = [], []
        for i, ln in enumerate(lines + [""]):
            if ln.strip():
                cur.append(i)
            elif cur:
                blocks.append(cur)
                cur = []
        big = [b for b in blocks if len(b) >= 2 and not (parsed[b[0]] and parsed[b[0]][0] != "item")]
        rest = [i for b in big for i in b[1:] if parsed[i] and parsed[i][0] == "item"]
        if len(big) >= 2 and all(bare(b[0]) for b in big) and rest and (
                all(lines[b[0]].strip().lower() in PL_HEAD_EXACT or pl_cat_clean(lines[b[0]]) in PL_CAT_KEYS for b in big)
                or sum(1 for i in rest if not bare(i)) >= 0.6 * len(rest)):   # … the lines below carry weights / numbers, the first never
            up = [b[0] for b in big]
    for i in up:
        parsed[i] = ("cat", parsed[i][1]["name"])
    if (len(idx) >= 3 and parsed[idx[0]][0] == "item" and idx[1] > idx[0] + 1 and parsed[idx[1]][0] in ("cat", "caps") and not caps_are_items
            and parsed[idx[0]][1]["g"] is None and not re.match(r"\s*[-*+•\[☐☑\d]", lines[idx[0]])):
        title = pl_text(lines[idx[0]], 80)                   # «Wochenende Jura», an empty line, then the first heading: the name of the list
        parsed[idx[0]] = None
        lines[idx[0]] = ""
    for ln, p in zip(lines, parsed):
        if p is None:
            skipped += 1 if ln.strip() and any(ch.isalnum() for ch in ln) else 0
            continue
        if p[0] == "caps":
            if caps_are_items:
                p = ("item", {"name": p[1][:1] + p[1][1:].lower(), "g": None, "n": 1, "note": "", "packed": False, "buy": False})
            else:
                p = ("cat", " ".join(w[:1] + w[1:].lower() for w in p[1].split(" ")))
        if p[0] == "cat":
            cat = pl_cat_head(p[1])
            heads.append([len(items), pl_text(p[1], PL_NAME_MAX), cat])   # for the preview: «as item» puts it back
            continue
        it = p[1]
        it["cat"] = cat or pl_cat_guess(it["name"])
        it["kind"] = pl_kind_auto(it["cat"], it["name"])
        items.append(it)
        if len(items) >= PL_ROWS_MAX:
            break
    return {"items": items, "skipped": skipped, "title": title, "heads": heads}


# ---- tables: CSV / pasted table / xlsx -> rows of cells -> items ----------------------------------------------------------------
def pl_decode(data):
    """bytes of a text file -> str: UTF-8 (with / without BOM), UTF-16 with BOM, else Windows-1252"""
    if data[:3] == b"\xef\xbb\xbf":
        return data[3:].decode("utf-8", "replace")
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", "replace")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252", "replace")


_PL_HTML_OPEN = re.compile(r"(?i)<!--|<(script|style|head|title)\b")
_PL_HTML_TAG = "[^<>]{0,2000}>"                           # the rest of a tag: never over the next «<», never endless


def pl_html_text(t):
    """HTML (a note of Apple Notes saved as text, a pasted page) -> plain lines. Nothing is rendered: comments and script /
    style / head / title are cut out, blocks become line breaks, list points a «- », every other tag goes away, then the
    entities are decoded. The time grows with the length only (3.83.2: the first version searched from every «<!--» /
    «<script» / «<li» to the end of the text again - 80 KB of «<!--» took 6 s, a file of 5 MB hours, and MoveEye stood still)."""
    import html as _h
    out, pos, nie = [], 0, set()                             # nie: block kinds whose end does not come any more
    while True:
        m = _PL_HTML_OPEN.search(t, pos)
        if not m:
            out.append(t[pos:])
            break
        out.append(t[pos:m.start()])
        kind = (m.group(1) or "!").lower()
        end = -1
        if kind not in nie:
            if kind == "!":
                j = t.find("-->", m.end())
                end = j + 3 if j >= 0 else -1
            else:
                c = re.compile(r"(?i)</%s\s{0,20}>" % kind).search(t, m.end())
                end = c.end() if c else -1
            if end < 0:
                nie.add(kind)
        pos = end if end >= 0 else m.end()                   # no end: only the opening goes away, the rest stays text
    t = "".join(out)
    t = re.sub(r"(?i)<li\b" + _PL_HTML_TAG, "\n- ", t)
    t = re.sub(r"(?i)</t[dh]\s{0,20}>", "\t", t)
    t = re.sub(r"(?i)</?(?:div|p|br|tr|li|ul|ol|h[1-6]|table|body|html)\b" + _PL_HTML_TAG, "\n", t)
    return _h.unescape(re.sub(r"<[a-zA-Z/!]" + _PL_HTML_TAG, "", t))


def pl_sniff(text, csv_file=False):
    """the separator of a table in this text, or "" (= a note with one item per line). Comma only for a .csv file."""
    lines = [ln for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if ln.strip()][:80]
    if len(lines) < 2:
        return ""
    best, best_n = "", 0.0
    for d in ("\t", ";", "|") + ((",",) if csv_file else ()):
        cnt = [ln.lstrip().count(d) for ln in lines]         # a tab in front is indentation (Apple Notes), not a column
        have = [c for c in cnt if c]
        if len(have) < max(2, 0.6 * len(lines)):
            continue
        mode = max(set(have), key=have.count)
        score = have.count(mode) / len(lines) + (0.2 if d == "\t" else 0.1 if d == ";" else 0)
        if have.count(mode) >= 0.5 * len(lines) and score > best_n:
            best, best_n = d, score
    return best


def pl_csv_rows(text, delim):
    import csv as _csv
    rows = []
    try:
        for r in _csv.reader(_pl_io.StringIO(text.replace("\r\n", "\n").replace("\r", "\n")), delimiter=delim, quotechar='"', skipinitialspace=True):
            cells = [pl_text(c, 300) for c in r[:PL_COLS_MAX]]
            if any(cells):
                rows.append(cells)
            if len(rows) >= PL_ROWS_MAX:
                break
    except _csv.Error:
        raise PLError("This table could not be read.")
    return rows


def _pl_xml(data):
    """parse XML from an xlsx: no DOCTYPE, no entities (nothing is expanded, nothing is fetched)"""
    import xml.etree.ElementTree as _ET
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data or b"<!doctype" in data:
        raise PLError("This Excel file is not accepted (unusual content).")
    # 3.82.0: only UTF-8 (what Excel and every other program writes). In UTF-16 the search above finds nothing (every second
    # byte is 0) and the parser would expand the entities of a DOCTYPE - so: no byte order mark of UTF-16 / UTF-32, no zero
    # byte, and an «encoding» in the first line may only say UTF-8.
    enc = re.match(rb"\s*<\?xml[^>]{0,200}?encoding\s*=\s*[\"']([A-Za-z0-9._-]{1,40})[\"']", data[:300])
    if data[:2] in (b"\xff\xfe", b"\xfe\xff") or b"\x00" in data or (enc and enc.group(1).lower() not in (b"utf-8", b"utf8")):
        raise PLError("This Excel file is not accepted (unusual content).")
    try:
        return _ET.fromstring(data)
    except _ET.ParseError:
        raise PLError("This Excel file could not be read.")


def pl_xlsx_rows(data):
    """the cells of the first sheet of an .xlsx as rows of text. Formulas are never computed (only the stored value).
    Guards: number of entries, unpacked size (declared AND really read), compression ratio, no DOCTYPE / ENTITY."""
    import zipfile as _zf
    if len(data) > PL_IMPORT_MAX:
        raise PLError("The file is too big.")
    try:
        z = _zf.ZipFile(_pl_io.BytesIO(data))
    except (_zf.BadZipFile, ValueError, OSError):
        raise PLError("This Excel file could not be read.")
    with z:
        infos = z.infolist()
        if len(infos) > PL_X_ENTRIES or sum(i.file_size for i in infos) > PL_X_TOTAL:
            raise PLError("This Excel file is not accepted (too big when unpacked).")
        for i in infos:
            if i.file_size > 64 * 1024 and i.file_size > PL_X_RATIO * max(1, i.compress_size):
                raise PLError("This Excel file is not accepted (too big when unpacked).")
        names = {i.filename: i for i in infos}
        budget = {"n": PL_X_TOTAL}

        def read(name):
            i = names.get(name)
            if i is None:
                return None
            try:
                with z.open(i) as f:
                    b = f.read(budget["n"] + 1)
            except (_zf.BadZipFile, RuntimeError, OSError, ValueError, NotImplementedError):
                raise PLError("This Excel file could not be read.")
            budget["n"] -= len(b)
            if budget["n"] < 0:
                raise PLError("This Excel file is not accepted (too big when unpacked).")
            return b

        def local(tag):
            return tag.rsplit("}", 1)[-1]
        sheet = None
        wb, rels = read("xl/workbook.xml"), read("xl/_rels/workbook.xml.rels")
        if wb is not None and rels is not None:
            rid = None
            for e in _pl_xml(wb).iter():
                if local(e.tag) == "sheet":
                    rid = next((v for k, v in e.attrib.items() if local(k) == "id"), None)
                    break
            for e in _pl_xml(rels).iter():
                if local(e.tag) == "Relationship" and rid and e.attrib.get("Id") == rid:
                    tgt = e.attrib.get("Target", "").replace("\\", "/")
                    tgt = tgt[1:] if tgt.startswith("/") else "xl/" + tgt
                    parts = []
                    for p in tgt.split("/"):
                        if p == "..":
                            parts = parts[:-1]
                        elif p and p != ".":
                            parts.append(p)
                    sheet = "/".join(parts)
        if sheet not in names:
            sheet = next((n for n in sorted(names) if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n)), None)
        if sheet is None:
            raise PLError("This Excel file has no table.")
        shared = []
        sst = read("xl/sharedStrings.xml")
        if sst is not None:
            for si in _pl_xml(sst):
                if local(si.tag) == "si":                    # plain <t> or rich text <r><t>; phonetic runs <rPh> are left out
                    shared.append("".join(t.text or "" for r in si for t in ([r] if local(r.tag) == "t" else
                                                                             [x for x in r if local(x.tag) == "t"] if local(r.tag) == "r" else [])))
        rows = []
        root = _pl_xml(read(sheet) or b"")
        for row in root.iter():
            if local(row.tag) != "row":
                continue
            cells, nxt = {}, 0
            for c in row:
                if local(c.tag) != "c":
                    continue
                ref = re.match(r"([A-Z]{1,3})", c.attrib.get("r", ""))
                if ref:
                    col = 0
                    for ch in ref.group(1):
                        col = col * 26 + ord(ch) - 64
                    col -= 1
                else:
                    col = nxt
                nxt = col + 1
                if col >= PL_COLS_MAX:
                    continue
                t_ = c.attrib.get("t", "n")
                v = next((x for x in c if local(x.tag) == "v"), None)
                val = ""
                if t_ == "s":
                    try:
                        val = shared[int(v.text)] if v is not None else ""
                    except (ValueError, IndexError, TypeError):
                        val = ""
                elif t_ == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter() if local(x.tag) == "t")
                elif t_ == "b":
                    val = "x" if v is not None and v.text == "1" else ""
                elif t_ == "e":
                    val = ""
                elif v is not None and v.text is not None:
                    val = v.text
                    if t_ == "n":
                        try:
                            f = float(val)
                            val = str(int(f)) if f == int(f) and abs(f) < 1e12 else repr(round(f, 4))
                        except (ValueError, OverflowError):
                            pass
                cells[col] = pl_text(val, 300)
            if any(cells.values()):
                rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
            if len(rows) >= PL_ROWS_MAX:
                break
        return rows


# what a heading of a column can be called (lower case; the names of the export in every language are added below)
PL_HEAD = {
    "name": ["name", "artikel", "gegenstand", "bezeichnung", "item", "was", "ausrüstung", "ausruestung", "produkt", "teil", "gear", "article", "nom",
             "nome", "oggetto", "objet", "sache", "titel", "equipment", "material", "ding"],
    "g": ["gewicht", "weight", "gramm", "gram", "grams", "g", "kg", "masse", "poids", "peso", "gew", "gew.", "einzelgewicht", "stückgewicht"],
    "n": ["anzahl", "menge", "stk", "stk.", "stück", "stueck", "qty", "quantity", "anz", "anz.", "quantité", "quantità", "pcs", "#", "x", "nombre", "numero"],
    "cat": ["kategorie", "category", "gruppe", "bereich", "rubrik", "catégorie", "categoria", "group", "kat", "kat.", "typ", "type", "abteilung"],
    "note": ["notiz", "notizen", "bemerkung", "bemerkungen", "kommentar", "note", "notes", "comment", "comments", "hinweis", "beschreibung",
             "description", "remarque", "nota", "info", "details"],
    "kind": ["art"],
    "packed": ["gepackt", "packed", "erledigt", "ok", "✓", "dabei", "eingepackt", "done"],
    "buy": ["kaufen", "fehlt", "fehlt noch", "buy", "einkaufen", "besorgen"],
}
PL_FIELDS = ("name", "g", "n", "cat", "note", "kind", "packed", "buy")
PL_CSV_HEAD = (("cat", "Category"), ("name", "Name"), ("n", "Quantity"), ("g", "Weight (g)"), ("kind", "Kind"), ("note", "Remark"),
               ("packed", "Packed"), ("buy", "To buy"))
PL_KIND_NAMES = (("base", "Base weight"), ("cons", "Consumable"), ("worn", "Worn"))
_PL_TRUE = {"x", "ja", "yes", "y", "j", "1", "true", "wahr", "✓", "✔", "☑", "✅", "oui", "sì", "si", "gepackt", "ok", "kaufen"}


def _pl_head_norm(cell):
    low = cell.lower().strip()
    unit = ""
    m = re.search(r"[(\[]\s*(?:in\s+)?(kg|g|gramm|gr)\s*[)\]]|\s+(?:in\s+)?(kg|g|gramm|gr)$|/\s*(kg|g)$", low)
    if m:
        unit = "kg" if (m.group(1) or m.group(2) or m.group(3)) == "kg" else "g"
        low = (low[:m.start()] + low[m.end():]).strip()
    if low == "kg":
        unit = "kg"
    low = re.sub(r"[(\[].*?[)\]]", "", low).strip(" :.*#-_")
    return low, unit


def _pl_head_field(cell):
    low, unit = _pl_head_norm(cell)
    if not low:
        return "", unit
    for f in PL_FIELDS:
        words = set(PL_HEAD[f])
        en = dict(PL_CSV_HEAD)[f]
        words.update(_pl_head_norm(tr(en, L))[0] for L in LANGS)
        if low in words or low.rstrip(".") in words:
            return f, unit
    for f in ("g", "n", "cat", "note", "name"):                # «Gewicht pro Stück», «Anzahl Stk.»
        if any(low.startswith(w + " ") or low.startswith(w + "-") or low.startswith(w + "/") for w in PL_HEAD[f] if len(w) > 3):
            return f, unit
    return "", unit


def pl_table_guess(rows):
    """{"header": bool, "map": {field: column or -1}, "unit": "g" | "kg"} for a table - only a proposal, the user decides"""
    mp = {f: -1 for f in PL_FIELDS}
    unit, header = "", False
    if not rows:
        return {"header": False, "map": mp, "unit": "g"}
    ncol = max(len(r) for r in rows)
    first = rows[0]
    hits = [_pl_head_field(c) for c in first]
    if sum(1 for f, _u in hits if f) >= 1 and not any(pl_num(c) is not None or _PL_W_RE.fullmatch(c.strip()) for c in first if c):
        header = True
        for i, (f, u) in enumerate(hits):
            if f and mp[f] < 0:
                mp[f] = i
                if f == "g" and u:
                    unit = u
    data = rows[1:] if header else rows
    data = data[:200]

    def col(i):
        return [r[i] for r in data if i < len(r) and r[i]]
    stats = []
    for i in range(ncol):
        cs = col(i)
        n = max(1, len(cs))
        nums = [pl_num(c) for c in cs]
        stats.append({"i": i, "fill": len(cs), "w": sum(1 for c in cs if _PL_W_RE.search(c)) / n, "num": sum(1 for v in nums if v is not None) / n,
                      "txt": sum(1 for c, v in zip(cs, nums) if v is None and any(ch.isalpha() for ch in c)) / n,
                      "vals": [v for v in nums if v is not None], "distinct": len({c.lower() for c in cs}), "len": sum(len(c) for c in cs) / n})
    used = {v for v in mp.values() if v >= 0}
    if mp["name"] < 0:
        cand = [s for s in stats if s["i"] not in used and s["fill"] and s["txt"] >= 0.6 and s["w"] < 0.5]
        if not header and len(cand) > 1:                     # two text columns: the one with few different values is the category
            cand.sort(key=lambda s: (s["distinct"] <= max(2, 0.4 * s["fill"]), s["i"]))
        if cand:
            mp["name"] = cand[0]["i"]
            used.add(mp["name"])
    if not header:
        cw = [s for s in stats if s["i"] not in used and s["fill"] and s["w"] >= 0.3]
        if cw:
            mp["g"] = max(cw, key=lambda s: s["w"])["i"]
        numc = [s for s in stats if s["i"] not in used and s["i"] != mp["g"] and s["fill"] and s["num"] >= 0.6]
        small = [s for s in numc if s["vals"] and all(v == int(v) and 0 < v <= 12 for v in s["vals"])]   # 1 … 12: a number of pieces
        if mp["g"] < 0 and numc:
            big = [s for s in numc if s not in small] or (numc if len(numc) > 1 else [])
            if big:
                mp["g"] = max(big, key=lambda s: sum(s["vals"]) / max(1, len(s["vals"])))["i"]
        small = [s for s in small if s["i"] != mp["g"]]
        if small:
            mp["n"] = small[0]["i"]
        used = {v for v in mp.values() if v >= 0}
        txt = [s for s in stats if s["i"] not in used and s["fill"] and s["txt"] >= 0.6]
        for s in txt:
            if mp["cat"] < 0 and s["distinct"] <= max(2, 0.4 * s["fill"]) and s["len"] <= 25:
                mp["cat"] = s["i"]
            elif mp["note"] < 0:
                mp["note"] = s["i"]
    if not unit and mp["g"] >= 0:
        vals = [v for c in col(mp["g"]) for v in [pl_num(c)] if v is not None]
        if vals:
            vals.sort()
            unit = "kg" if vals[len(vals) // 2] < 30 and any(v != int(v) for v in vals) else "g"
    return {"header": header, "map": mp, "unit": unit or "g"}


def _pl_unquote(c):
    """the apostrophe the CSV export puts before = + - @ goes away again"""
    return c[1:] if len(c) > 1 and c[0] == "'" and c[1] in "=+-@" else c


def pl_table_items(rows, guess):
    """rows + the chosen columns -> {"items", "skipped"}"""
    mp = {f: -1 for f in PL_FIELDS}
    for f, v in (guess.get("map") or {}).items():
        if f in mp and isinstance(v, int) and not isinstance(v, bool) and -1 <= v < PL_COLS_MAX:
            mp[f] = v
    unit = "kg" if guess.get("unit") == "kg" else "g"
    data = rows[1:] if guess.get("header") else rows
    kinds = {}
    for k, en in PL_KIND_NAMES:
        for L in LANGS:
            kinds[tr(en, L).lower()] = k
    kinds.update({"verbrauch": "cons", "consumable": "cons", "basis": "base", "base": "base", "getragen": "worn", "worn": "worn", "am körper": "worn"})
    items, skipped, cat = [], 0, None

    def cell(r, f):
        i = mp[f]
        return _pl_unquote(r[i]) if 0 <= i < len(r) else ""
    for r in data:
        full = [c for c in r if c]
        if not full:
            continue
        if len(full) == 1 and mp["cat"] < 0 and max(len(x) for x in data) >= 2:
            c = full[0]
            p = pl_parse_line(c)
            if c.endswith(":") or (p and p[0] in ("cat", "caps")) or c.lower() in PL_HEAD_EXACT or any(
                    c.lower() == tr(en, L).lower() for _k, en, _c, _p in PL_CATS for L in LANGS):
                cat = pl_cat_head(c.title() if c == c.upper() else c)
                continue
        raw = cell(r, "name") if mp["name"] >= 0 else ""
        if not raw:
            skipped += 1
            continue
        gw = pl_weight(cell(r, "g"), unit) if cell(r, "g") else None
        p = pl_parse_line(raw) if mp["g"] < 0 else None      # weights have their own column: the name is taken as it is written
        it = dict(p[1]) if p and p[0] == "item" else {"name": pl_text(raw, PL_NAME_MAX), "g": None, "n": 1, "note": "", "packed": False, "buy": False}
        if not it["name"]:
            skipped += 1
            continue
        if gw is not None:
            it["g"] = gw
        if cell(r, "n"):
            v = pl_num(re.sub(r"\s*(?:x|×|stk\.?|stück)\s*$", "", cell(r, "n"), flags=re.I))
            if v is not None and 1 <= v <= 999:
                it["n"] = int(v)
        if cell(r, "note"):
            it["note"] = pl_text((it["note"] + " · " if it["note"] else "") + cell(r, "note"), PL_NOTE_MAX)
        it["cat"] = pl_cat_head(cell(r, "cat")) if cell(r, "cat") else (cat or pl_cat_guess(it["name"]))
        k = kinds.get(cell(r, "kind").lower())
        it["kind"] = k or pl_kind_auto(it["cat"], it["name"])
        if mp["packed"] >= 0:
            it["packed"] = cell(r, "packed").lower() in _PL_TRUE
        if mp["buy"] >= 0:
            it["buy"] = cell(r, "buy").lower() in _PL_TRUE
        items.append(it)
    return {"items": items, "skipped": skipped}


def pl_import_preview(data=None, text=None, name="", guess=None, rows=None, lang=None):
    """what an import would bring - nothing is stored. A file (bytes + name), pasted text, or rows with the user's columns.
    -> {"kind": "lines" | "table", "items", "skipped", "rows" (table), "map", "header", "unit", "title"}"""
    ext = tausch_ext(name) if name else ""
    title = pl_text(os.path.splitext(os.path.basename(str(name).replace("\\", "/")))[0], 80) if name else ""
    if rows is None:
        if data is not None:
            if len(data) > PL_IMPORT_MAX:
                raise PLError("The file is too big.")
            if data[:4] == b"PK\x03\x04" or ext in ("xlsx", "xlsm"):
                if ext in ("docx", "pptx", "odt", "ods", "numbers", "pages", "zip"):
                    raise PLError("This kind of file cannot be imported. Save the list as .xlsx, CSV or text.")
                rows = pl_xlsx_rows(data)
            elif data[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" or ext == "xls":
                raise PLError("Old Excel files (.xls) cannot be read. Save the table as .xlsx or CSV.")
            elif data[:5] == b"%PDF-" or ext in ("pdf", "doc", "rtf", "jpg", "jpeg", "png", "heic"):
                raise PLError("This kind of file cannot be imported. Save the list as .xlsx, CSV or text.")
            else:
                text = pl_decode(data)
        if rows is None:
            text = str(text or "")
            if len(text.encode("utf-8", "replace")) > PL_IMPORT_MAX:
                raise PLError("The text is too long.")
            if "\x00" in text[:2000]:
                raise PLError("This kind of file cannot be imported. Save the list as .xlsx, CSV or text.")
            if sum(c < " " and c not in "\t\n\r" for c in text[:4000]) > 8:
                raise PLError("This kind of file cannot be imported. Save the list as .xlsx, CSV or text.")
            if len(re.findall(r"(?i)<(?:html|body|div|p|br|li|span|tr)\b[^<>]{0,2000}>", text[:20000])) >= 2:
                text = pl_html_text(text)
            if ext == "json" or text.lstrip()[:1] == "{":
                try:
                    j = json.loads(text)
                except ValueError:
                    j = None
                if isinstance(j, dict) and isinstance(j.get("items"), list):          # a list exported by MoveEye
                    its = []
                    for d in j["items"][:PL_ROWS_MAX]:
                        if isinstance(d, dict) and pl_text(d.get("name"), PL_NAME_MAX):
                            g = d.get("g")
                            its.append({"name": pl_text(d.get("name"), PL_NAME_MAX), "g": g if isinstance(g, int) and not isinstance(g, bool) and 0 < g <= 500000 else None,
                                        "n": d.get("n") if isinstance(d.get("n"), int) and 1 <= d.get("n") <= 999 else 1, "note": pl_text(d.get("note"), PL_NOTE_MAX),
                                        "cat": pl_cat_clean(d.get("cat") or "other"), "kind": d.get("kind") if d.get("kind") in PL_KINDS else "base",
                                        "packed": d.get("packed") is True, "buy": d.get("buy") is True})
                    return {"kind": "lines", "items": its, "skipped": 0, "title": pl_text(j.get("name"), 80) or title, "goal_g": j.get("goal_g") if isinstance(j.get("goal_g"), int) else 0}
                if ext == "json":
                    raise PLError("This JSON file is not a packing list of MoveEye.")
            d = pl_sniff(text, csv_file=ext in ("csv", "tsv"))
            if not d:
                res = pl_parse_text(text)
                return {"kind": "lines", "items": res["items"], "skipped": res["skipped"], "title": res["title"] or title, "heads": res["heads"]}
            rows = pl_csv_rows(text, d)
    rows = [[pl_text(c, 300) for c in r[:PL_COLS_MAX]] for r in rows[:PL_ROWS_MAX] if isinstance(r, list)]
    if not rows:
        raise PLError("Nothing to import was found.")
    g = pl_table_guess(rows)
    if isinstance(guess, dict):
        g = {"header": bool(guess.get("header")), "map": dict(g["map"], **{k: v for k, v in (guess.get("map") or {}).items() if k in g["map"] and isinstance(v, int)}),
             "unit": "kg" if guess.get("unit") == "kg" else "g"}
    res = pl_table_items(rows, g)
    return {"kind": "table", "items": res["items"], "skipped": res["skipped"], "rows": rows, "map": g["map"], "header": g["header"], "unit": g["unit"],
            "title": title}


# ---- where the lists are: plain files next to the files of the exchange ------------------------------------------------------
def _pl_write(path, obj):
    """a whole list at once: first a side file (flushed to the storage), then renamed - never half a list"""
    tmp = f"{path}.{os.getpid()}.{threading.get_ident()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    os.replace(tmp, path)


def _pl_item_ok(d):
    """an item as it is stored (from a file or built here) -> cleaned dict or None"""
    if not isinstance(d, dict) or not PL_IID.match(str(d.get("id", ""))):
        return None
    name = pl_text(d.get("name"), PL_NAME_MAX)
    if not name:
        return None
    g, n = d.get("g"), d.get("n")
    it = {"id": d["id"], "name": name, "g": g if isinstance(g, int) and not isinstance(g, bool) and 0 < g <= 500000 else None,
          "n": n if isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= 999 else 1,
          "cat": pl_cat_clean(d.get("cat")) if isinstance(d.get("cat"), str) else "other", "note": pl_text(d.get("note"), PL_NOTE_MAX),
          "photo": d.get("photo") if isinstance(d.get("photo"), int) and not isinstance(d.get("photo"), bool) and d.get("photo") > 0 else 0,
          "packed": d.get("packed") is True, "buy": d.get("buy") is True, "kind": d.get("kind") if d.get("kind") in PL_KINDS else "base",
          "rev": d.get("rev") if isinstance(d.get("rev"), int) and d.get("rev") >= 0 else 0, "by": pl_text(d.get("by"), 40),
          "t": d.get("t") if isinstance(d.get("t"), int) else 0}
    return it


def _pl_list_ok(d, lid):
    if not isinstance(d, dict) or d.get("id") != lid or not isinstance(d.get("items"), list):
        return None
    name = pl_text(d.get("name"), 80)
    if not name or not isinstance(d.get("owner"), str):
        return None
    items, seen = [], set()
    for x in d["items"][:PL_MAX_ITEMS]:
        it = _pl_item_ok(x)
        if it and it["id"] not in seen:
            seen.add(it["id"])
            items.append(it)
    rev = d.get("rev") if isinstance(d.get("rev"), int) and d.get("rev") >= 0 else 0
    rev = max([rev] + [it["rev"] for it in items])
    gone = [[g[0], g[1]] for g in (d.get("gone") if isinstance(d.get("gone"), list) else [])
            if isinstance(g, list) and len(g) == 2 and PL_IID.match(str(g[0])) and isinstance(g[1], int)][-PL_GONE_MAX:]
    goal = d.get("goal_g")
    last = d.get("last") if isinstance(d.get("last"), dict) else {}
    return {"moveeye_packliste": 1, "id": lid, "name": name, "area": "mine" if d.get("area") == "mine" else "all", "owner": d["owner"][:60],
            "owner_name": pl_text(d.get("owner_name"), 40) or d["owner"][:40], "t": d.get("t") if isinstance(d.get("t"), int) else 0, "rev": rev,
            "meta_rev": d.get("meta_rev") if isinstance(d.get("meta_rev"), int) else 0,
            "goal_g": goal if isinstance(goal, int) and not isinstance(goal, bool) and 0 < goal <= 500000 else 0, "note": pl_text(d.get("note"), PL_NOTE_MAX),
            "last": {"by": pl_text(last.get("by"), 40), "t": last.get("t") if isinstance(last.get("t"), int) else 0},
            "gone": gone, "gone_floor": d.get("gone_floor") if isinstance(d.get("gone_floor"), int) else 0, "items": items}


def pl_load():
    """the lists of the present storage (cached; another storage = read again). None = no storage now."""
    root = _tz_load()
    if root is None:
        return None
    with PL["lock"]:
        if PL["root"] == root and PL["lists"] is not None:
            return root
        d = os.path.join(root, "pack")
        try:
            os.makedirs(os.path.join(d, "b"), exist_ok=True)
            names = sorted(os.listdir(d))
        except OSError as e:
            log_event("sys", f"Packing lists: folder {d} cannot be made: {e}"[:180])
            return None
        lists = {}
        for nm in names:
            p = os.path.join(d, nm)
            if nm.endswith(".tmp"):
                try:
                    os.remove(p)
                except OSError:
                    pass
                continue
            if not nm.endswith(".json") or not TZ_ID.match(nm[:-5]) or len(lists) >= PL_MAX_LISTS:
                continue
            try:
                if os.path.getsize(p) > 8 * 1024 * 1024:
                    continue
                with open(p, encoding="utf-8") as f:
                    L = _pl_list_ok(json.load(f), nm[:-5])
            except (OSError, ValueError, RecursionError):
                L = None
            if L:
                lists[L["id"]] = L
        total = 0
        try:
            for dp, _dn, fns in os.walk(os.path.join(d, "b")):
                total += sum(os.path.getsize(os.path.join(dp, fn)) for fn in fns if fn.endswith(".jpg"))
        except OSError:
            pass
        PL.update(root=root, lists=lists, photo_bytes=total)
    return root


def _pl_save(L):
    _pl_write(os.path.join(PL["root"], "pack", L["id"] + ".json"), L)


def _pl_photo_paths(lid, iid):
    """the two pictures of an item - only from checked numbers, never from a name"""
    if not TZ_ID.match(str(lid or "")) or not PL_IID.match(str(iid or "")):
        return None
    d = os.path.join(PL["root"], "pack", "b", lid)
    return os.path.join(d, iid + ".jpg"), os.path.join(d, iid + "_p.jpg")


def _pl_photo_rm(lid, iid):
    pp = _pl_photo_paths(lid, iid)
    for p in pp or ():
        try:
            n = os.path.getsize(p)
            os.remove(p)
            PL["photo_bytes"] = max(0, PL["photo_bytes"] - n)
        except OSError:
            pass


# ---- who may what -----------------------------------------------------------------------------------------------------------
def pl_can_see(L, who):
    return "files_view" in who["perms"] and (L["area"] == "all" or L["owner"] == who["key"] or who["admin"])


def pl_can_edit(L, who):
    return pl_can_see(L, who) and "files_up" in who["perms"]


def pl_can_del(L, who):
    return pl_can_see(L, who) and (who["admin"] or (L["owner"] == who["key"] and "files_up" in who["perms"]))


def pl_can_export(L, who):
    return pl_can_see(L, who) and ("files_down" in who["perms"] or L["owner"] == who["key"])


def pl_totals(items):
    """sums in grams: «pack» = base + consumables (what is in the rucksack), worn = on the body; rows without a weight are counted"""
    t = {"n": len(items), "pieces": 0, "packed": 0, "buy": 0, "total": 0, "base": 0, "cons": 0, "worn": 0, "packed_g": 0, "unknown": 0, "cats": {}}
    for it in items:
        w = (it["g"] or 0) * it["n"]
        t["pieces"] += it["n"]
        t["packed"] += 1 if it["packed"] else 0
        t["buy"] += 1 if it["buy"] else 0
        t["unknown"] += 1 if it["g"] is None else 0
        t["total"] += w
        t[it["kind"]] += w
        t["packed_g"] += w if it["packed"] else 0
        c = t["cats"].setdefault(it["cat"], {"g": 0, "n": 0, "packed": 0})
        c["g"] += w
        c["n"] += 1
        c["packed"] += 1 if it["packed"] else 0
    t["pack"] = t["base"] + t["cons"]
    return t


def _pl_pub_item(it, guest=False):
    d = {k: it[k] for k in ("id", "name", "g", "n", "cat", "note", "photo", "packed", "buy", "kind", "rev", "t")}
    if not guest:
        d["by"] = it["by"]
    return d


def _pl_pub_head(L, who):
    t = pl_totals(L["items"])
    return {"id": L["id"], "name": L["name"], "area": L["area"], "by": L["owner_name"], "mine": L["owner"] == who["key"], "t": L["t"], "rev": L["rev"],
            "goal_g": L["goal_g"], "note": L["note"], "n": t["n"], "packed": t["packed"], "buy": t["buy"], "total": t["total"], "pack": t["pack"],
            "edit": pl_can_edit(L, who) and bool(CFG.get("tausch_on", True)), "rm": pl_can_del(L, who), "dl": pl_can_export(L, who),
            "ci": {c: pl_cat_icon(c) for c in {x["cat"] for x in L["items"]} if c not in PL_CAT_KEYS}}


def pl_overview(who, lang=None):
    root = pl_load()
    r0, kind, prob = tausch_root()
    out = {"ok": True, "on": bool(CFG.get("tausch_on", True)), "perms": sorted(who["perms"]),
           "me": {"name": who["name"], "admin": who["admin"]}, "store": {"problem": prob or ("missing" if root is None else "")}, "lists": [],
           "templates": [{"key": k, "name": nm[_pl_tl(lang)], "n": len(its)} for k, nm, its in PL_TEMPLATES],
           "caps": {"lists": PL_MAX_LISTS, "items": PL_MAX_ITEMS, "import": PL_IMPORT_MAX, "text": PL_TEXT_MAX, "photo": PL_PHOTO_MAX}, "now": int(time.time())}
    if root is None or "files_view" not in who["perms"]:
        return out
    with PL["lock"]:
        out["lists"] = sorted((_pl_pub_head(L, who) for L in PL["lists"].values() if pl_can_see(L, who)), key=lambda x: -x["t"])
    return out


def _pl_tl(lang):
    return {"de": 0, "en": 1, "fr": 2, "it": 3, "rm": 0}.get(cur_lang(lang), 1)


def pl_get(who, lid, since=0, lang=None):
    """a list for the page: everything (since 0) or only what changed after the state the page has («since»)"""
    if pl_load() is None or not TZ_ID.match(str(lid or "")):
        return False, tr("unknown list", lang), {}
    with PL["lock"]:
        L = PL["lists"].get(lid)
        if L is None or not pl_can_see(L, who):
            return False, tr("unknown list", lang), {}
        out = {"rev": L["rev"], "now": int(time.time()), "last": dict(L["last"]), "head": _pl_pub_head(L, who)}
        if since and since == L["rev"]:
            out["same"] = True
            del out["head"]
        elif since and since >= L["gone_floor"] and since < L["rev"]:
            out["items"] = [_pl_pub_item(it) for it in L["items"] if it["rev"] > since]
            out["gone"] = [g[0] for g in L["gone"] if g[1] > since]
            out["order"] = [it["id"] for it in L["items"]]
        else:
            out["full"] = True
            out["items"] = [_pl_pub_item(it) for it in L["items"]]
    return True, "", out


# ---- changes (everything goes through here: one lock, one new state, one write) -----------------------------------------------
def _pl_ready(who, lang, write=True):
    """"" or why nothing can be changed now"""
    if not CFG.get("tausch_on", True):
        return tr("The file exchange is switched off.", lang)
    if write and "files_up" not in who["perms"]:
        return tr("You may look at the packing lists, but not change them.", lang)
    root = pl_load()
    r0, kind, prob = tausch_root()
    if root is None:
        return tr("The storage (USB stick / SSD) is not there - plug it in again.", lang)
    if prob == "ro":
        return tr("The memory card is write-protected (overlay) - files would be lost at the next restart. Use a USB stick.", lang)
    if write and tausch_disk_free(root) < 8 * TZ_MB:
        return tr("The storage is full.", lang)
    if write and not tausch_rate(who["key"], "pl", 4000):
        return tr("Too many changes in a short time - wait a few minutes.", lang)
    return ""


def _pl_bump(L, who, meta=False):
    L["rev"] += 1
    L["last"] = {"by": who["name"], "t": int(time.time())}
    if meta:
        L["meta_rev"] = L["rev"]
    return L["rev"]


def _pl_new_item(L, who, d):
    """a new item from cleaned import / quick-add fields (name, g | w, n, cat, note, kind, packed, buy)"""
    name = pl_text(d.get("name"), PL_NAME_MAX)
    if not name:
        return None
    g = d.get("g")
    if not (isinstance(g, int) and not isinstance(g, bool) and 0 < g <= 500000):
        g = pl_weight(d.get("w")) if isinstance(d.get("w"), (str, int, float)) and not isinstance(d.get("w"), bool) else None
    n = d.get("n")
    try:
        n = int(n) if not isinstance(n, bool) else 1
    except (TypeError, ValueError):
        n = 1
    cat = pl_cat_clean(d.get("cat")) if isinstance(d.get("cat"), str) and d.get("cat").strip() else pl_cat_guess(name)
    own = {x["cat"] for x in L["items"] if x["cat"] not in PL_CAT_KEYS and pl_cat_icon(x["cat"]) == cat}
    if len(own) == 1 and not d.get("cat") and not any(x["cat"] == cat for x in L["items"]):
        cat = own.pop()                                      # a guessed «Kleider» goes to the user's own «Kleidung»
    iid = secrets.token_hex(4)
    have = {x["id"] for x in L["items"]} | {x[0] for x in L["gone"]}
    while iid in have:
        iid = secrets.token_hex(4)
    return {"id": iid, "name": name, "g": g, "n": max(1, min(999, n)), "cat": cat, "note": pl_text(d.get("note"), PL_NOTE_MAX), "photo": 0,
            "packed": d.get("packed") is True, "buy": d.get("buy") is True, "kind": d.get("kind") if d.get("kind") in PL_KINDS else pl_kind_auto(cat, name),
            "rev": L["rev"], "by": who["name"], "t": int(time.time())}


def pl_dups(items, L=None):
    """mark doubles in an import preview: "list" = already in the target list, "import" = twice in this import (nothing is dropped)"""
    def words(n):                                            # «Wasserflasche/ auch Trinkblase» ~ «Wasserflaschen»: the same stem
        return frozenset(re.sub(r"(?<=...)(?:en|n|e|s)$", "", w) for w in re.findall(r"[^\W\d_]{3,}", n.casefold())
                         if w not in ("evtl", "eventuell", "oder", "auch", "inkl", "nach", "und", "aus", "mit", "ggf", "ggfs", "für", "and", "the", "with"))
    have = {it["name"].casefold(): it["name"] for it in (L["items"] if L else ())}
    near = [(words(n), n) for n in have.values()]
    seen = set()
    for it in items:
        k, w = it["name"].casefold(), words(it["name"])
        it["dup"] = "list" if k in have else "import" if k in seen else ""
        like = "" if it["dup"] or not w else next((n for v, n in near if v and (v <= w or w <= v)), "")
        if like:
            it["like"] = like                                # only a hint in the preview: nothing is merged, nothing unticked
        seen.add(k)
    return items


def pl_action(who, d, lang=None):
    """every change of the lists. -> (ok, error, result, http code)"""
    a = d.get("action")
    if a == "preview":                                       # pasted text, or the rows again with the columns the user chose
        err = _pl_ready(who, lang)
        if err:
            return False, err, {}, 403 if "files_up" not in who["perms"] else 409
        if isinstance(d.get("cat"), str):                     # the preview turns a row into a heading: which category is that?
            return True, "", {"cat": pl_cat_head(d["cat"])}, 200
        try:
            if isinstance(d.get("rows"), list):
                res = pl_import_preview(rows=d["rows"], guess=d.get("guess") if isinstance(d.get("guess"), dict) else None, lang=lang)
            else:
                text = d.get("text")
                if not isinstance(text, str) or not text.strip():
                    return False, tr("Nothing to import was found.", lang), {}, 400
                if len(text.encode("utf-8", "replace")) > PL_TEXT_MAX:
                    return False, tr("The text is too long.", lang), {}, 413
                res = pl_import_preview(text=text, lang=lang)
        except PLError as e:
            return False, tr(str(e), lang), {}, 400
        return True, "", pl_preview_out(who, res, str(d.get("list") or "")), 200
    err = _pl_ready(who, lang)
    if err:
        return False, err, {}, 403 if "files_up" not in who["perms"] else 409
    now = int(time.time())
    with PL["lock"]:
        lists = PL["lists"]
        if a in ("new", "copy") or (a == "import" and not d.get("list")):
            if len(lists) >= PL_MAX_LISTS:
                return False, trf("At most {n} packing lists - delete an old one first.", lang, n=PL_MAX_LISTS), {}, 400
            src = None
            if a == "copy":
                src = lists.get(str(d.get("id") or ""))
                if src is None or not pl_can_see(src, who):
                    return False, tr("unknown list", lang), {}, 404
            name = pl_text(d.get("name"), 80) or (trf("{name} (copy)", lang, name=src["name"])[:80] if src else "")
            if not name:
                return False, tr("The list needs a name.", lang), {}, 400
            taken = {x["name"].casefold() for x in lists.values()}
            base_name, i = name, 2
            while name.casefold() in taken and i < 500:
                name = f"{base_name[:74]} ({i})"
                i += 1
            lid = secrets.token_hex(8)
            while lid in lists:
                lid = secrets.token_hex(8)
            goal = pl_weight(d.get("goal"), "kg") if isinstance(d.get("goal"), (str, int, float)) and not isinstance(d.get("goal"), bool) else None
            L = {"moveeye_packliste": 1, "id": lid, "name": name, "area": "mine" if d.get("area") == "mine" else "all", "owner": who["key"],
                 "owner_name": who["name"], "t": now, "rev": 1, "meta_rev": 1, "goal_g": goal or (src["goal_g"] if src else 0), "note": src["note"] if src else "",
                 "last": {"by": who["name"], "t": now}, "gone": [], "gone_floor": 0, "items": []}
            if src:
                for it in src["items"]:
                    L["items"].append(dict(it, packed=False, rev=1, by=who["name"], t=now))
            tpl = next((x for x in PL_TEMPLATES if x[0] == d.get("template")), None) if a == "new" else None
            if tpl:
                li = _pl_tl(lang)
                for cat, g, n, kind, names in tpl[2]:
                    it = _pl_new_item(L, who, {"name": names[li], "g": g, "n": n, "cat": cat, "kind": kind})
                    L["items"].append(it)
                L["note"] = tr("Weights are typical values - weigh your own things.", lang)
            added = dups = 0
            if a == "import":
                added, dups = _pl_import_into(L, who, d.get("items"))
                if not added:
                    return False, tr("Nothing to import was found.", lang), {}, 400
            try:
                if src:                                          # the photos of the copy
                    for it in L["items"]:
                        pp, qq = _pl_photo_paths(src["id"], it["id"]), _pl_photo_paths(lid, it["id"])
                        if it["photo"] and pp and all(os.path.isfile(p) for p in pp) and PL["photo_bytes"] < PL_PHOTO_TOTAL:
                            os.makedirs(os.path.dirname(qq[0]), exist_ok=True)
                            for p, q in zip(pp, qq):
                                shutil.copyfile(p, q)
                                PL["photo_bytes"] += os.path.getsize(q)
                        else:
                            it["photo"] = 0
                _pl_save(L)
            except OSError as e:
                shutil.rmtree(os.path.join(PL["root"], "pack", "b", lid), ignore_errors=True)
                return False, tr("The storage cannot be written to.", lang) + f" ({e.__class__.__name__})", {}, 507
            lists[lid] = L
            log_event("web", f"Packing lists: {who['name']} " + ("copied a list" if src else "imported a list" if a == "import" else "created a list")
                      + f" ({len(L['items'])} items)")
            return True, "", {"id": lid, "added": added, "dups": dups, "head": _pl_pub_head(L, who)}, 200
        lid = str(d.get("list") or d.get("id") or "")
        L = lists.get(lid) if TZ_ID.match(lid) else None
        if L is None or not pl_can_see(L, who):
            return False, tr("unknown list", lang), {}, 404
        if a == "del":
            if not pl_can_del(L, who):
                return False, tr("Only the person who created this list (or the administrator) may delete it.", lang), {}, 403
            lists.pop(lid, None)
            try:
                os.remove(os.path.join(PL["root"], "pack", lid + ".json"))
            except OSError:
                pass
            bd = os.path.join(PL["root"], "pack", "b", lid)
            try:
                for fn in os.listdir(bd):
                    PL["photo_bytes"] = max(0, PL["photo_bytes"] - os.path.getsize(os.path.join(bd, fn)))
            except OSError:
                pass
            shutil.rmtree(bd, ignore_errors=True)
            log_event("web", f"Packing lists: {who['name']} deleted a list ({len(L['items'])} items, from {L['owner_name']})")
            return True, "", {}, 200
        if not pl_can_edit(L, who):
            return False, tr("You may look at the packing lists, but not change them.", lang), {}, 403
        res = {}
        dirty = True
        if a == "meta":
            if "name" in d:
                nm = pl_text(d.get("name"), 80)
                if not nm:
                    return False, tr("The list needs a name.", lang), {}, 400
                L["name"] = nm
            if "goal" in d:
                gv = d.get("goal")
                L["goal_g"] = (pl_weight(gv, "kg") or 0) if isinstance(gv, (str, int, float)) and not isinstance(gv, bool) else 0
            if "note" in d:
                L["note"] = pl_text(d.get("note"), PL_NOTE_MAX)
            if d.get("area") in ("all", "mine") and (L["owner"] == who["key"] or who["admin"]):
                L["area"] = d["area"]
            _pl_bump(L, who, meta=True)
        elif a == "add":
            if len(L["items"]) >= PL_MAX_ITEMS:
                return False, trf("At most {n} items per list.", lang, n=PL_MAX_ITEMS), {}, 400
            f = d
            if isinstance(d.get("text"), str):                   # the quick line «Name, Gewicht» - the same reading as the import
                p = pl_parse_line(d["text"][:400].replace("\n", " "))
                if not p or p[0] != "item":
                    p = ("item", {"name": pl_text(d["text"], PL_NAME_MAX)})
                f = dict(p[1])
                if isinstance(d.get("cat"), str) and d["cat"].strip():
                    f["cat"] = d["cat"]
                if d.get("buy") is True:
                    f["buy"] = True
            _pl_bump(L, who)
            it = _pl_new_item(L, who, f)
            if it is None:
                L["rev"] -= 1
                return False, tr("The item needs a name.", lang), {}, 400
            L["items"].append(it)
            res = {"item": _pl_pub_item(it), "dup": sum(1 for x in L["items"] if x["name"].casefold() == it["name"].casefold()) > 1}
        elif a == "import":
            room = PL_MAX_ITEMS - len(L["items"])
            if room <= 0:
                return False, trf("At most {n} items per list.", lang, n=PL_MAX_ITEMS), {}, 400
            _pl_bump(L, who)
            added, dups = _pl_import_into(L, who, d.get("items"))
            if not added:
                L["rev"] -= 1
                return False, tr("Nothing to import was found.", lang), {}, 400
            res = {"added": added, "dups": dups}
            log_event("web", f"Packing lists: {who['name']} imported {added} items into a list")
        elif a == "reset":
            r = _pl_bump(L, who)
            n = 0
            for it in L["items"]:
                if it["packed"]:
                    it.update(packed=False, rev=r, by=who["name"], t=now)
                    n += 1
            res = {"n": n}
        elif a in ("item", "rm", "photo_rm"):
            iid = str(d.get("id") or "")
            it = next((x for x in L["items"] if x["id"] == iid), None)
            if it is None:
                return False, tr("This item does not exist (any more).", lang), {"gone": True}, 404
            if a == "rm":
                r = _pl_bump(L, who)
                L["items"] = [x for x in L["items"] if x is not it]
                L["gone"].append([iid, r])
                if len(L["gone"]) > PL_GONE_MAX:                 # a phone that knows less than this asks for the whole list
                    L["gone_floor"] = L["gone"][-PL_GONE_MAX][1]
                    L["gone"] = L["gone"][-PL_GONE_MAX:]
                _pl_photo_rm(lid, iid)
            elif a == "photo_rm":
                it.update(photo=0, rev=_pl_bump(L, who), by=who["name"], t=now)
                _pl_photo_rm(lid, iid)
                res = {"item": _pl_pub_item(it)}
            else:
                st = d.get("set") if isinstance(d.get("set"), dict) else {}
                new = {}
                if "name" in st:
                    nm = pl_text(st.get("name"), PL_NAME_MAX)
                    if not nm:
                        return False, tr("The item needs a name.", lang), {}, 400
                    new["name"] = nm
                if "w" in st:
                    w = st.get("w")
                    if isinstance(w, str) and w.strip() and pl_weight(w) is None:
                        return False, tr("This weight is not understood. Examples: 350 g, 1.2 kg, 0,5 kg.", lang), {}, 400
                    new["g"] = pl_weight(w) if isinstance(w, (str, int, float)) and not isinstance(w, bool) else None
                if "n" in st:
                    try:
                        new["n"] = max(1, min(999, int(st.get("n")))) if not isinstance(st.get("n"), bool) else 1
                    except (TypeError, ValueError):
                        new["n"] = 1
                if "cat" in st and isinstance(st.get("cat"), str):
                    new["cat"] = pl_cat_clean(st["cat"])
                if "note" in st:
                    new["note"] = pl_text(st.get("note"), PL_NOTE_MAX)
                if st.get("kind") in PL_KINDS:
                    new["kind"] = st["kind"]
                for k in ("packed", "buy"):
                    if isinstance(st.get(k), bool):
                        new[k] = st[k]
                base = d.get("base") if isinstance(d.get("base"), int) else None
                res = {"stale": base is not None and base < it["rev"]}   # somebody else changed this item meanwhile: fields are merged
                dirty = any(it[k] != v for k, v in new.items())
                if dirty:
                    it.update(new, rev=_pl_bump(L, who), by=who["name"], t=now)
                res["item"] = _pl_pub_item(it)
        else:
            return False, tr("unknown action", lang), {}, 400
        try:
            if dirty:
                _pl_save(L)
        except OSError as e:
            PL["lists"] = None                                   # the file is the truth: read again at the next request
            return False, tr("The storage cannot be written to.", lang) + f" ({e.__class__.__name__})", {}, 507
        res.update(rev=L["rev"], head=_pl_pub_head(L, who))
        return True, "", res, 200


def _pl_import_into(L, who, items):
    """append the items of a confirmed preview; doubles are counted, not dropped -> (added, doubles)"""
    added = dups = 0
    have = {x["name"].casefold() for x in L["items"]}
    for d in (items if isinstance(items, list) else [])[:PL_ROWS_MAX]:
        if len(L["items"]) >= PL_MAX_ITEMS:
            break
        it = _pl_new_item(L, who, d) if isinstance(d, dict) else None
        if it is None:
            continue
        if it["name"].casefold() in have:
            dups += 1
        have.add(it["name"].casefold())
        L["items"].append(it)
        added += 1
    return added, dups


def pl_preview_out(who, res, lid=""):
    with PL["lock"]:
        L = (PL["lists"] or {}).get(lid) if TZ_ID.match(lid or "") else None
        if L is not None and not pl_can_see(L, who):
            L = None
        pl_dups(res["items"], L)
        room = PL_MAX_ITEMS - (len(L["items"]) if L else 0)
    res["room"] = room
    res["rows"] = (res.get("rows") or [])[:PL_ROWS_MAX]
    return res


# ---- the photo of an item: the upload of the file exchange (639zzc), only the end is different ---------------------------------
_pl_up_start_base = tausch_up_start


# wraps: tausch_up_start
def tausch_up_start(who, d, lang=None):                    # + 639zzw: «pack» = this upload is the photo of an item
    pk = d.get("pack") if isinstance(d, dict) else None
    if not pk:
        return _pl_up_start_base(who, d, lang)
    err = _pl_ready(who, lang)
    if err:
        return False, err, {}
    lid, iid = (str(pk.get("list") or ""), str(pk.get("item") or "")) if isinstance(pk, dict) else ("", "")
    with PL["lock"]:
        L = PL["lists"].get(lid) if TZ_ID.match(lid) else None
        if L is None or not pl_can_edit(L, who) or not PL_IID.match(iid) or not any(x["id"] == iid for x in L["items"]):
            return False, tr("This item does not exist (any more).", lang), {}
        if PL["photo_bytes"] >= PL_PHOTO_TOTAL:
            return False, tr("The space for photos of the packing lists is full - remove some photos first.", lang), {}
    try:
        size = int(d.get("size"))
    except (TypeError, ValueError):
        size = -1
    if size > PL_PHOTO_MAX:
        return False, trf("Too big: at most {n} per file.", lang, n=tausch_fmt(PL_PHOTO_MAX, lang)), {}
    nm = tausch_clean_name(d.get("name"))[0] or "foto.jpg"
    if tausch_type(nm)[1] != "image" or tausch_type(nm)[2]:
        return False, tr("Please choose a photo (JPEG, PNG or WebP).", lang), {}
    ok, err, res = _pl_up_start_base(who, dict(d, area="mine", folder="", name=f"pl-{lid}-{iid}-{nm[-60:]}"), lang)
    if ok:
        with TZ["lock"]:
            u = TZ["ups"].get(res["id"])
            if u is not None:
                u["pack"] = {"list": lid, "item": iid}
                try:
                    _tz_write_json(os.path.join(TZ["root"], "up", res["id"] + ".json"), {k: v for k, v in u.items() if k not in ("lock", "have")})
                except OSError:
                    pass
    return ok, err, res


_pl_up_finish_base = tausch_up_finish


# wraps: tausch_up_finish
def tausch_up_finish(who, uid, lang=None):                 # + 639zzw: a photo of an item does not become a file of the exchange
    with TZ["lock"]:
        u = TZ["ups"].get(uid) if TZ_ID.match(str(uid or "")) else None
    if u is None or not isinstance(u.get("pack"), dict) or u["owner"] != who["key"]:
        return _pl_up_finish_base(who, uid, lang)
    return pl_photo_finish(who, uid, u, lang)


def pl_photo_finish(who, uid, u, lang=None):
    root = pl_load()
    if root is None:
        return False, tr("The storage (USB stick / SSD) is not there - plug it in again.", lang), {}
    lid, iid = str(u["pack"].get("list") or ""), str(u["pack"].get("item") or "")
    part = os.path.join(root, "up", uid + ".part")
    with u["lock"]:
        if u.get("have", 0) != u["size"]:
            return False, tr("The upload is not complete yet.", lang), {"have": u.get("have", 0)}
        img, heic = None, False
        try:
            with open(part, "rb") as f:
                data = f.read(PL_PHOTO_MAX + 1)
        except OSError:
            data = b""
        if data and len(data) <= PL_PHOTO_MAX:
            heic = data[4:8] == b"ftyp" and data[8:12] in (b"heic", b"heix", b"hevc", b"mif1", b"msf1", b"heim", b"heis", b"avif")
            head = img_head(data)
            flag = cv2.IMREAD_REDUCED_COLOR_4 if head and head[0] == "jpeg" and head[1] * head[2] > 16_000_000 else None
            img = img_decode_checked(data, flag)             # head first (no pixel bombs), then decoded - the bytes are never kept
        data = None
        tausch_up_abort(who, uid, lang)                      # the piece file goes away in every case
    if img is None or img.size == 0:
        if heic:
            return False, tr(PL_HEIC_MSG, lang), {}
        return False, tr("This picture could not be read. Please choose a photo (JPEG, PNG or WebP).", lang), {}
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    with PL["lock"]:
        L = PL["lists"].get(lid) if PL["lists"] is not None else None
        it = next((x for x in L["items"] if x["id"] == iid), None) if L is not None and pl_can_edit(L, who) else None
        if it is None:
            return False, tr("This item does not exist (any more).", lang), {}
        pp = _pl_photo_paths(lid, iid)
        try:
            os.makedirs(os.path.dirname(pp[0]), exist_ok=True)
            _pl_photo_rm(lid, iid)
            if not (_tz_jpg_write(img, pp[0], 320, 80) and _tz_jpg_write(img, pp[1], 1280, 84)):
                raise OSError("encode")
            PL["photo_bytes"] += os.path.getsize(pp[0]) + os.path.getsize(pp[1])
            it.update(photo=max(int(time.time()), it["photo"] + 1), rev=_pl_bump(L, who), by=who["name"], t=int(time.time()))
            _pl_save(L)
        except OSError as e:
            _pl_photo_rm(lid, iid)
            return False, tr("The storage cannot be written to.", lang) + f" ({e.__class__.__name__})", {}
        return True, "", {"item": _pl_pub_item(it), "rev": L["rev"], "pack": True}


# ---- export: CSV (safe for spreadsheets), the list's own JSON, ZIP with the photos, a page to print ------------------------------
def pl_csv_cell(v):
    """a cell that a spreadsheet will not run as a formula: = + - @ (also after blanks, tab, return) get an apostrophe"""
    s = "" if v is None else str(v)
    s = s.replace("\r", " ").replace("\n", " ")
    if s[:1] in ("\t",) or s.lstrip()[:1] in ("=", "+", "-", "@"):
        s = "'" + s.lstrip()
    return s


def _pl_sorted(L, lang=None):
    """the items in the order of the categories (fixed ones first, own ones by name), inside as they were added"""
    def key(c):
        return (PL_CAT_KEYS.index(c), "") if c in PL_CAT_KEYS[:-1] else (len(PL_CAT_KEYS) + 1, "") if c == "other" else (len(PL_CAT_KEYS), c.lower())
    groups = {}
    for it in L["items"]:
        groups.setdefault(it["cat"], []).append(it)
    return [(c, groups[c]) for c in sorted(groups, key=key)]


def pl_cat_name(cat, lang=None):
    en = next((c[1] for c in PL_CATS if c[0] == cat), None)
    return tr(en, lang) if en else cat


def pl_export_csv(L, lang=None):
    import csv as _csv
    buf = _pl_io.StringIO()
    w = _csv.writer(buf, delimiter=";", quotechar='"', lineterminator="\r\n")
    w.writerow([tr(en, lang) for _f, en in PL_CSV_HEAD])
    kn = {k: tr(en, lang) for k, en in PL_KIND_NAMES}
    for cat, items in _pl_sorted(L, lang):
        for it in items:
            w.writerow([pl_csv_cell(x) for x in (pl_cat_name(cat, lang), it["name"], it["n"], "" if it["g"] is None else it["g"], kn[it["kind"]],
                                                 it["note"], "x" if it["packed"] else "", "x" if it["buy"] else "")])
    return ("﻿" + buf.getvalue()).encode("utf-8")


def pl_export_json(L):
    d = {k: L[k] for k in ("moveeye_packliste", "id", "name", "goal_g", "note", "t")}
    d["items"] = [dict({k: it[k] for k in ("id", "name", "g", "n", "cat", "kind", "note", "packed", "buy")},
                       **({"photo_file": f"fotos/{it['id']}.jpg"} if it["photo"] else {})) for it in L["items"]]
    return json.dumps(d, ensure_ascii=False, indent=1).encode("utf-8")


def pl_export_zip(L, lang=None):
    import zipfile as _zf
    buf = _pl_io.BytesIO()
    with _zf.ZipFile(buf, "w", _zf.ZIP_DEFLATED) as z:
        z.writestr("packliste.json", pl_export_json(L))
        z.writestr("packliste.csv", pl_export_csv(L, lang))
        for it in L["items"]:
            pp = _pl_photo_paths(L["id"], it["id"])
            if it["photo"] and pp and os.path.isfile(pp[1]):
                z.write(pp[1], f"fotos/{it['id']}.jpg", _zf.ZIP_STORED)
    return buf.getvalue()


def pl_file_name(L, ext):
    n = tausch_clean_name(re.sub(r"\s+", "_", L["name"]) + "." + ext)[0]
    return n or "packliste." + ext


def pl_icon_svg(cat, size=22):
    c = next(x for x in PL_CATS if x[0] == pl_cat_icon(cat))
    return (f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="{c[2]}" stroke-width="1.7" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true"><path d="{c[3]}"/></svg>')


def _pl_rows_html(L, lang, img_base, esc):
    """the items as HTML rows for the pages without a script (print, guests): every user text escaped"""
    out = []
    t = pl_totals(L["items"])
    for cat, items in _pl_sorted(L, lang):
        c = t["cats"][cat]
        out.append(f'<tr class="cat"><td colspan="2">{pl_icon_svg(cat, 18)} {esc(pl_cat_name(cat, lang))}</td><td class="w">{esc(pl_fmt_g(c["g"], lang))}</td></tr>')
        for it in items:
            pic = (f'<img src="{img_base}/{L["id"]}/{it["id"]}.jpg?v={it["photo"]}" alt="" loading="lazy">' if it["photo"] and img_base else "")
            sub = " · ".join(x for x in (trf("{n} each", lang, n=pl_fmt_g(it["g"], lang)) if it["n"] > 1 and it["g"] else "",
                                         tr("Consumable", lang) if it["kind"] == "cons" else tr("Worn", lang) if it["kind"] == "worn" else "",
                                         "🛒 " + tr("To buy", lang) if it["buy"] else "", it["note"]) if x)
            out.append(f'<tr class="{"done" if it["packed"] else ""}"><td class="bx">{"☑" if it["packed"] else "☐"}</td><td><div class="c">{pic}<span><b>'
                       f'{esc((str(it["n"]) + "× " if it["n"] > 1 else "") + it["name"])}</b>' + (f'<small>{esc(sub)}</small>' if sub else "")
                       + f'</span></div></td><td class="w">{esc(pl_fmt_g(it["g"] * it["n"], lang) if it["g"] else "–")}</td></tr>')
    return "".join(out), t


def _pl_sum_html(L, t, lang, esc):
    parts = [f'<b>{esc(tr("Rucksack", lang))} {esc(pl_fmt_g(t["pack"], lang))}</b>', f'{esc(tr("Base weight", lang))} {esc(pl_fmt_g(t["base"], lang))}',
             f'{esc(tr("Consumable", lang))} {esc(pl_fmt_g(t["cons"], lang))}', f'{esc(tr("Worn", lang))} {esc(pl_fmt_g(t["worn"], lang))}',
             esc(trf("{a} of {b} packed", lang, a=t["packed"], b=t["n"]))]
    if L["goal_g"]:
        diff = t["pack"] - L["goal_g"]
        parts.insert(1, esc(trf("Goal {n}", lang, n=pl_fmt_g(L["goal_g"], lang)) + ": " + (trf("{n} over", lang, n=pl_fmt_g(diff, lang)) if diff > 0
                                                                                           else trf("{n} under", lang, n=pl_fmt_g(-diff, lang)))))
    if t["unknown"]:
        parts.append(esc(trf("{n} without a weight", lang, n=t["unknown"])))
    return " · ".join(parts)


PL_PRINT_HTML = """<!doctype html>
<html lang="%(lang)s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>%(title)s</title>
<style>
body{font:14px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:#111;background:#fff;margin:0;padding:18px;max-width:820px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px}.sum{color:#333;font-size:13px;margin:0 0 4px}.nt{color:#555;font-size:12.5px;margin:0 0 12px}
table{width:100%%;border-collapse:collapse}td{padding:6px 6px;border-bottom:1px solid #ddd;vertical-align:middle;overflow-wrap:anywhere}
tr.cat td{font-weight:700;background:#f1f3f6;border-bottom:1px solid #bbb;padding-top:8px}tr.cat svg{vertical-align:-4px;margin-right:4px}
td.bx{width:26px;font-size:20px;line-height:1}td.w{text-align:right;white-space:nowrap;width:84px}
td small{display:block;color:#555;font-size:12px}td img{flex:none;width:44px;height:44px;object-fit:cover;border-radius:6px}.c{display:flex;align-items:center;gap:10px}.c span{min-width:0}
tr.done b{color:#666}.bar{display:flex;gap:10px;margin:0 0 14px;flex-wrap:wrap}.bar button,.bar a{font:inherit;padding:9px 16px;border-radius:10px;border:1px solid #888;background:#fff;color:#111;text-decoration:none;min-height:44px;display:inline-flex;align-items:center;box-sizing:border-box}
.ft{color:#777;font-size:11.5px;margin-top:14px}
@media print{.bar{display:none}body{padding:0}tr{break-inside:avoid}}
</style></head><body>
%(bar)s<h1>🎒 %(name)s</h1><p class="sum">%(sum)s</p>%(note)s
<table>%(rows)s</table><p class="ft">MoveEye · %(date)s</p>
</body></html>
"""


def pl_print_html(L, lang=None):
    import html as _h
    rows, t = _pl_rows_html(L, lang, "/tausch/pack/b", _h.escape)
    bar = ('<div class="bar"><button type="button" onclick="window.print()">🖨 ' + _h.escape(tr("Print", lang)) + '</button><a data-mw-exit href="/tausch/packlisten#l='
           + L["id"] + '">‹ ' + _h.escape(tr("Back to the list", lang)) + "</a></div>")
    return PL_PRINT_HTML % {"lang": cur_lang(lang), "title": _h.escape(L["name"]) + " – MoveEye", "name": _h.escape(L["name"]),
                            "sum": _pl_sum_html(L, t, lang, _h.escape), "note": f'<p class="nt">{_h.escape(L["note"])}</p>' if L["note"] else "",
                            "rows": rows, "bar": bar, "date": time.strftime("%d.%m.%Y")}


PL_GUEST_HTML = """<!doctype html>
<html lang="%(lang)s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex">%(refresh)s<title>MoveEye – %(title)s</title>
<style>
html,body{margin:0;background:#0a0e14;color:#e6edf3;font:15px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.top{display:flex;align-items:center;gap:10px;padding:10px 14px;padding-top:max(10px,env(safe-area-inset-top))}.top b{font-size:17px;flex:1;min-width:0;overflow-wrap:anywhere}
.top a{color:#8ab4f8;text-decoration:none;font-size:14px;white-space:nowrap}main{padding:0 14px 30px;max-width:820px;margin:0 auto}
.mut{color:#8b9bb0;font-size:13px}a.li{display:block;border:1px solid #1f2b3a;border-radius:12px;background:#111822;padding:12px 14px;margin:0 0 10px;color:inherit;text-decoration:none}
a.li b{display:block;font-size:16px;overflow-wrap:anywhere}table{width:100%%;border-collapse:collapse}td{padding:8px 6px;border-bottom:1px solid #1f2b3a;vertical-align:middle;overflow-wrap:anywhere}
tr.cat td{font-weight:700;background:#111822;padding-top:10px}tr.cat svg{vertical-align:-4px;margin-right:4px}td.bx{width:26px;font-size:20px;line-height:1}
td.w{text-align:right;white-space:nowrap;width:80px}td small{display:block;color:#8b9bb0;font-size:12.5px}
td img{flex:none;width:44px;height:44px;object-fit:cover;border-radius:8px}.c{display:flex;align-items:center;gap:10px}.c span{min-width:0}tr.done b{color:#8b9bb0;text-decoration:line-through}
</style></head><body>
<div class="top"><b>🎒 %(name)s</b><a href="%(back)s">‹ %(backtx)s</a></div>
<main><p class="mut">%(sum)s</p>%(body)s<p class="mut">%(foot)s</p></main>
</body></html>
"""


def pl_guest_html(token, lid="", lang=None):
    """the shared lists for a guest: only to look at, no names, no script. None = this list is not for guests."""
    import html as _h
    esc = _h.escape
    base = "/g/" + token
    if pl_load() is None:
        lists = []
    else:
        with PL["lock"]:
            lists = [L for L in PL["lists"].values() if L["area"] == "all"]
    common = {"lang": cur_lang(lang), "foot": esc(tr("Only to look at - changing the lists needs a login.", lang))}
    if lid:
        L = next((x for x in lists if x["id"] == lid), None)
        if L is None:
            return None
        with PL["lock"]:
            rows, t = _pl_rows_html(L, lang, base + "/tausch/pack/b", esc)
            return PL_GUEST_HTML % dict(common, refresh='<meta http-equiv="refresh" content="20">', title=esc(L["name"]), name=esc(L["name"]),
                                        back=base + "/tausch/pack", backtx=esc(tr("Packing lists", lang)), sum=_pl_sum_html(L, t, lang, esc),
                                        body="<table>" + rows + "</table>")
    body = []
    with PL["lock"]:
        for L in sorted(lists, key=lambda x: -x["t"]):
            t = pl_totals(L["items"])
            body.append(f'<a class="li" href="{base}/tausch/pack?l={L["id"]}"><b>{esc(L["name"])}</b><span class="mut">'
                        + esc(trf("{a} of {b} packed", lang, a=t["packed"], b=t["n"]) + " · " + pl_fmt_g(t["pack"], lang)) + "</span></a>")
    return PL_GUEST_HTML % dict(common, refresh="", title=esc(tr("Packing lists", lang)), name=esc(tr("Packing lists", lang)), back=base + "/tausch",
                                backtx=esc(tr("Shared files", lang)), sum="", body="".join(body) or '<p class="mut">' + esc(tr("No packing lists yet.", lang)) + "</p>")


# ---- web ----------------------------------------------------------------------------------------------------------------------------
_smalltv_routes_639zzw = smalltv_routes


def smalltv_routes(app, reply, body):                     # + 639zzw: /tausch/packlisten, /api/tausch/pack, photos, export, guests
    _smalltv_routes_639zzw(app, reply, body)
    from flask import Response, request, g

    def lang_():
        return norm_lang(request.args.get("lang") or CFG.get("lang"))

    def too_big():                                       # an import file is refused before it is read
        if request.path == "/api/tausch/pack/import" and request.method == "POST":
            n = request.content_length
            if n is None or n > PL_IMPORT_MAX:
                return Response(json.dumps({"ok": False, "error": tr("The file is too big.", lang_())}), 413, mimetype="application/json",
                                headers={"Connection": "close"})
        return None
    app.before_request_funcs.setdefault(None, []).insert(0, too_big)

    @app.route("/tausch/packlisten")
    def pl_page():
        who = tausch_who(g)
        if "files_view" not in who["perms"]:
            return sx_err(403, "error")
        return Response(pl_page_html(), mimetype="text/html", headers={"Cache-Control": "no-store"})

    @app.route("/api/tausch/pack", methods=["GET", "POST"])
    def api_pl():
        who = tausch_who(g)
        if request.method == "GET":
            L = lang_()
            if "files_view" not in who["perms"]:
                return reply({"ok": False, "error": tr("not allowed for your user", L)}, 403)
            lid = str(request.args.get("id") or "")
            if not lid:
                return reply(pl_overview(who, L))
            ok, err, res = pl_get(who, lid, _tz_int(request.args.get("since")), L)
            return reply(dict(res, ok=ok, error=err or None), 200 if ok else 404)
        d = body()
        L = norm_lang(d.get("lang") or CFG.get("lang"))
        if "files_view" not in who["perms"]:
            return reply({"ok": False, "error": tr("not allowed for your user", L)}, 403)
        ok, err, res, code = pl_action(who, d, L)
        return reply(dict(res, ok=ok, error=err or None), code)

    @app.route("/api/tausch/pack/import", methods=["POST"])
    def api_pl_import():                                 # a file -> the preview (nothing is stored)
        who = tausch_who(g)
        L = lang_()
        err = _pl_ready(who, L)
        if err:
            return reply({"ok": False, "error": err}, 403 if "files_up" not in who["perms"] else 409)
        data = request.get_data(cache=False)
        if len(data) > PL_IMPORT_MAX:
            return reply({"ok": False, "error": tr("The file is too big.", L)}, 413)
        try:
            res = pl_import_preview(data=data, name=str(request.args.get("name") or "")[:200], lang=L)
        except PLError as e:
            return reply({"ok": False, "error": tr(str(e), L)}, 400)
        except Exception as e:                                # a broken file must never be more than a refused import
            log_event("sys", f"Packing lists: import failed ({e.__class__.__name__})")
            return reply({"ok": False, "error": tr("This file could not be read.", L)}, 400)
        return reply(dict(pl_preview_out(who, res, str(request.args.get("list") or "")), ok=True))

    def list_of(lid, who):
        if not TZ_ID.match(lid or "") or pl_load() is None:
            return None
        with PL["lock"]:
            L = PL["lists"].get(lid)
        return L if L is not None and (who is None and L["area"] == "all" or who is not None and pl_can_see(L, who)) else None

    def photo(lid, iid, who):
        L = list_of(lid, who)
        pp = _pl_photo_paths(lid, iid) if L is not None else None
        if pp is None or not any(x["id"] == iid and x["photo"] for x in L["items"]):
            return Response("not found", 404)
        p = pp[1] if request.args.get("p") == "1" else pp[0]
        if not os.path.isfile(p):
            return Response("not found", 404)
        return _tz_send(p, "image/jpeg", False, cache="private, max-age=86400")

    @app.route("/tausch/pack/b/<lid>/<iid>.jpg")
    def pl_photo(lid, iid):
        return photo(lid, iid, tausch_who(g))

    @app.route("/tausch/pack/x/<lid>.<ext>")
    def pl_export(lid, ext):
        who = tausch_who(g)
        L = list_of(lid, who)
        if L is None or ext not in ("csv", "json", "zip"):
            return reply({"ok": False, "error": tr("unknown list", lang_())}, 404)
        if not pl_can_export(L, who):
            return reply({"ok": False, "error": tr("You may not download files.", lang_())}, 403)
        if not tausch_rate(who["key"], "dl", 400):
            return reply({"ok": False, "error": tr("Too many downloads in a short time - wait a few minutes.", lang_())}, 429)
        with PL["lock"]:
            data = pl_export_csv(L, lang_()) if ext == "csv" else pl_export_json(L) if ext == "json" else pl_export_zip(L, lang_())
        from urllib.parse import quote
        return Response(data, mimetype={"csv": "text/csv; charset=utf-8", "json": "application/json", "zip": "application/zip"}[ext],
                        headers={"Content-Disposition": "attachment; filename*=UTF-8''" + quote(pl_file_name(L, ext)), "X-Content-Type-Options": "nosniff",
                                 "Cache-Control": "no-store", "Content-Security-Policy": "sandbox; default-src 'none'"})

    @app.route("/tausch/pack/druck/<lid>")
    def pl_print(lid):
        who = tausch_who(g)
        L = list_of(lid, who)
        if L is None:
            return sx_err(404, "notfound")
        with PL["lock"]:
            html_ = pl_print_html(L, lang_())
        return Response(html_, mimetype="text/html", headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
                                                              "Content-Security-Policy": "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'"})

    def guest_gate(token):
        return tausch_guest_ok(token) and tausch_rate("guest|" + (request.remote_addr or "?"), "g", 2000)

    @app.route("/g/<token>/tausch/pack")
    def pl_guest(token):
        if not guest_gate(token):
            return sx_err(404, "guest")
        html_ = pl_guest_html(token, str(request.args.get("l") or ""), sx_req_lang())
        if html_ is None:
            return sx_err(404, "guest")
        return Response(html_, mimetype="text/html", headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer",
                                                              "Content-Security-Policy": "default-src 'none'; img-src 'self'; style-src 'unsafe-inline'"})

    @app.route("/g/<token>/tausch/pack/b/<lid>/<iid>.jpg")
    def pl_guest_photo(token, lid, iid):
        if not guest_gate(token):
            return Response("not found", 404)
        return photo(lid, iid, None)


# ---- the page /tausch/packlisten ----------------------------------------------------------------------------------------------------
PL_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>MoveEye - Packing lists</title>
<style>
/*BASECSS*/
main{padding:12px 14px 30px;max-width:820px;margin:0 auto}
.mut{color:var(--mut)}
.pl-h{display:flex;align-items:center;gap:8px;margin:0 0 8px;min-width:0}.pl-h h2{margin:0;font-size:20px;flex:1;min-width:0;overflow-wrap:anywhere}
.pl-back{color:var(--acc2);text-decoration:none;font-weight:600;min-height:44px;min-width:44px;display:inline-flex;align-items:center;white-space:nowrap}
.pl-bar{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 12px}.pl-bar button{min-height:44px}
.pl-msg{border:1px solid var(--yel);color:var(--yel);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:13px}.pl-msg.bad{border-color:var(--red);color:var(--red)}
.pl-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}
button.pl-card{border:1px solid var(--line);border-radius:var(--r);background:var(--panel);box-shadow:var(--shadow);padding:12px 14px;display:flex;flex-direction:column;gap:6px;
  min-width:0;text-align:left;color:var(--txt);font-weight:400;min-height:92px}
.pl-card b{font-size:16px;overflow-wrap:anywhere}.pl-card small{color:var(--mut);font-size:12.5px;overflow-wrap:anywhere}
.pl-card .g{font-size:13px}.pl-over{color:var(--red)}.pl-under{color:var(--grn)}
.pl-meter{height:8px;border-radius:5px;background:var(--field);border:1px solid var(--line);overflow:hidden}
.pl-meter i{display:block;height:100%;background:var(--grn);width:0;transition:width .3s}.pl-meter.goal i{background:var(--acc)}.pl-meter.over i{background:var(--red)}
.pl-empty{color:var(--mut);text-align:center;padding:26px 10px}
.pl-sum{position:sticky;top:var(--plh,0px);z-index:20;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:6px 12px 8px;margin:0 0 10px;box-shadow:var(--shadow)}
.pl-sum .big{display:flex;align-items:baseline;gap:4px 10px;flex-wrap:wrap;font-size:12.5px}.pl-sum .big b{font-size:17px;white-space:nowrap}
.pl-sum .big #pl-prog{margin-left:auto;white-space:nowrap;color:var(--mut)}
.pl-sum .pl-meter{height:5px;margin-top:4px;border:0}
.pl-parts{font-size:12.5px;color:var(--mut);margin:-2px 2px 8px;overflow-wrap:anywhere}
.pl-hint{color:var(--org);font-weight:600;font-size:12.5px;margin-top:4px}.pl-hint:empty{display:none}
.pl-note{font-size:12.5px;color:var(--mut);margin:-4px 2px 10px;overflow-wrap:anywhere}
.pl-tabs{display:flex;gap:4px;background:var(--field);border:1px solid var(--line);border-radius:12px;padding:4px;margin:0 0 10px}
.pl-tabs button{flex:1;border:0;background:transparent;color:var(--mut);font:inherit;font-weight:600;padding:9px 10px;border-radius:9px;min-height:44px}
.pl-tabs button.on{background:var(--acc);color:#fff}
.pl-tool{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 6px}.pl-tool input{flex:1 1 150px;min-height:40px}.pl-tool select{flex:1 1 120px;min-height:40px}
.pl-tool input,.pl-f input,.pl-f textarea,.pl-add input,.pl-pv input{background:var(--field);color:var(--txt);border:1px solid var(--line);border-radius:10px;padding:8px 10px;font:inherit}
.pl-cat{display:flex;align-items:center;gap:8px;padding:12px 4px 6px;font-weight:700;border-bottom:1px solid var(--line)}
.pl-cat .w{margin-left:auto;font-weight:600;color:var(--mut);font-size:12.5px;white-space:nowrap}
.pl-ic{flex:none;display:grid;place-items:center;border-radius:9px}.pl-cat .pl-ic{width:28px;height:28px}
.pl-row{display:flex;align-items:center;gap:8px;padding:5px 2px 5px 0;border-bottom:1px solid var(--line);min-width:0;transition:background .8s}
.pl-row.flash{background:var(--glow)}
button.pl-tick{flex:none;width:48px;height:48px;border-radius:50%;border:0;background:none;padding:0;display:grid;place-items:center}
.pl-tick i{width:30px;height:30px;border-radius:50%;border:2px solid var(--mut);display:grid;place-items:center;font-style:normal;color:transparent;font-weight:700;font-size:17px;line-height:1}
.pl-row.done .pl-tick i{background:var(--grn);border-color:var(--grn);color:#fff}.pl-tick:disabled{opacity:.75}
button.pl-pic{flex:none;width:46px;height:46px;border-radius:10px;border:0;padding:0;overflow:hidden;display:grid;place-items:center;background:var(--field)}
.pl-pic img{width:100%;height:100%;object-fit:cover;display:block}
.pl-tx{flex:1;min-width:0}.pl-tx .nm{font-weight:600;font-size:15px;overflow-wrap:anywhere}.pl-row.done .nm{color:var(--mut);text-decoration:line-through}
.pl-tx .sb{font-size:12.5px;color:var(--mut);overflow-wrap:anywhere}.pl-tx .sb b{color:var(--txt);font-weight:600}
.pl-tag{display:inline-block;border:1px solid var(--line);border-radius:99px;padding:0 7px;font-size:11.5px;margin-left:4px;white-space:nowrap}.pl-tag.buy{border-color:var(--org);color:var(--org)}
button.pl-ib{flex:none;width:44px;height:44px;border-radius:10px;border:1px solid var(--line);background:var(--btn2);color:var(--txt);font-size:17px;padding:0}
button.pl-ib.on{background:var(--org);color:#16110a;border-color:var(--org)}
.pl-add{position:sticky;bottom:0;z-index:15;display:flex;gap:8px;align-items:center;background:var(--bg);border-top:1px solid var(--line);margin:10px -14px 0;
  padding:8px 14px;padding-bottom:max(8px,env(safe-area-inset-bottom))}
.pl-add input{flex:1;min-width:0;min-height:46px}.pl-add button{flex:none;min-width:52px;min-height:46px;font-size:20px;padding:0 12px}
.pl-add select{flex:0 1 104px;min-width:0;min-height:46px}
.pl-ov{position:fixed;inset:0;z-index:120;background:rgba(0,0,0,.6);display:flex;align-items:flex-end;justify-content:center}
.pl-sh{background:var(--panel);border:1px solid var(--line);border-radius:18px 18px 0 0;width:100%;max-width:640px;max-height:94vh;max-height:94dvh;display:flex;flex-direction:column;box-shadow:0 -8px 30px #0008}
.pl-sh.full{height:94vh;height:94dvh}
.pl-shh{display:flex;align-items:center;gap:8px;padding:10px 12px 8px 16px;border-bottom:1px solid var(--line)}.pl-shh b{flex:1;min-width:0;font-size:16px;overflow-wrap:anywhere}
.pl-shh button{min-width:44px;min-height:44px;padding:0}
.pl-shb{padding:12px 16px;overflow:auto;-webkit-overflow-scrolling:touch;flex:1;min-height:0}
.pl-shf{display:flex;gap:8px;padding:10px 16px;padding-bottom:max(10px,env(safe-area-inset-bottom));border-top:1px solid var(--line)}.pl-shf button{flex:1;min-height:46px}
.pl-f{display:flex;flex-direction:column;gap:4px;margin:0 0 12px;min-width:0}.pl-f>span{font-size:12.5px;color:var(--mut);font-weight:600}
.pl-f input,.pl-f select,.pl-f textarea{min-height:44px;width:100%}.pl-f textarea{min-height:120px;resize:vertical}
.pl-2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.pl-seg{display:flex;gap:4px;background:var(--field);border:1px solid var(--line);border-radius:11px;padding:3px}
.pl-seg button{flex:1;border:0;background:transparent;color:var(--mut);padding:6px 4px;border-radius:8px;min-height:40px;font-size:13px}.pl-seg button.on{background:var(--acc);color:#fff}
.pl-sw{display:flex;align-items:center;gap:10px;min-height:44px;margin:0 0 6px}.pl-sw span{flex:1}
.pl-ph{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:0 0 6px}.pl-ph img{width:84px;height:84px;object-fit:cover;border-radius:12px;border:1px solid var(--line)}
.pl-ph button{min-height:44px}.pl-upm{font-size:12.5px;color:var(--mut);margin:0 0 10px;overflow-wrap:anywhere}.pl-upm.err{color:var(--red)}
.pl-upm .dg{font:11px/1.35 ui-monospace,Menlo,Consolas,monospace;margin-top:4px;-webkit-user-select:all;user-select:all}
.pl-menu{display:flex;flex-direction:column;gap:8px}.pl-menu button,.pl-menu a{min-height:48px;text-align:left;padding:10px 14px;font-size:15px}
.pl-pv{display:flex;gap:6px;align-items:flex-start;padding:8px 0;border-bottom:1px solid var(--line)}.pl-pv.off .pl-pvf{opacity:.4}
.pl-pvc{flex:none;width:44px;height:44px;display:grid;place-items:center}.pl-pvc input{width:22px;height:22px}
.pl-pvf{flex:1;min-width:0;display:flex;flex-direction:column;gap:6px}.pl-pvf input,.pl-pvf select{min-height:40px;min-width:0}.pl-pvf .nm{width:100%}
.pl-pvf .r2{display:grid;grid-template-columns:minmax(0,1fr) 64px minmax(0,1.3fr);gap:6px}
.pl-pvf small{color:var(--org);font-size:12px}
.pl-sw2{align-self:flex-start;min-height:40px;padding:4px 12px;font-size:13px}.pl-pvh{align-items:center;justify-content:space-between;gap:10px;padding-left:10px;background:var(--panel2)}.pl-pvh b{min-width:0;overflow-wrap:anywhere}
#gd-card{bottom:calc(16px + var(--plb,0px) + env(safe-area-inset-bottom,0px))!important}
.pl-map{border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin:0 0 10px;background:var(--panel2)}
.pl-map .g{display:grid;grid-template-columns:auto minmax(0,1fr);gap:6px 10px;align-items:center}.pl-map select{min-height:40px;width:100%}
.pl-lb{position:fixed;inset:0;z-index:140;background:rgba(0,0,0,.92);display:flex;flex-direction:column}
.pl-lb .bar{display:flex;gap:8px;align-items:center;padding:10px 12px;padding-top:max(10px,env(safe-area-inset-top));color:#fff}.pl-lb .bar b{flex:1;min-width:0;overflow-wrap:anywhere}
.pl-lb .bd{flex:1;display:flex;align-items:center;justify-content:center;min-height:0;padding:8px}.pl-lb img{max-width:100%;max-height:100%;object-fit:contain;border-radius:8px}
</style></head><body>
<header>
  <h1>MoveEye</h1>
  <!--NAV-->
  <span class="hdr-ctl">
    <button class="sec" id="btn-theme" onclick="toggleTheme()">&#9728;</button>
    <button class="sec" id="btn-lang" onclick="toggleLang()">DE</button>
  </span>
</header>
<main id="pl">
  <div class="pl-msg" id="pl-msg" hidden></div>
  <section id="pl-ov">
    <div class="pl-h"><a class="pl-back" href="/tausch">‹ <span data-i18n="File exchange">File exchange</span></a></div>
    <div class="pl-h"><h2>🎒 <span data-i18n="Packing lists">Packing lists</span></h2></div>
    <div class="pl-bar" id="pl-ovbar" hidden><button type="button" id="pl-new">＋ <span data-i18n="New list">New list</span></button>
      <button type="button" class="sec" id="pl-imp">⬇ <span data-i18n="Import">Import</span></button></div>
    <div class="pl-cards" id="pl-lists"></div><div class="pl-empty" id="pl-none" hidden></div>
  </section>
  <section id="pl-li" hidden>
    <div class="pl-h"><a class="pl-back" href="#" id="pl-up">‹ <span data-i18n="Packing lists">Packing lists</span></a><h2 id="pl-name"></h2>
      <button type="button" class="sec pl-ib" id="pl-more" aria-label="Menu">⋯</button></div>
    <div class="pl-note" id="pl-note" hidden></div>
    <div class="pl-parts" id="pl-parts"></div>
    <div class="pl-sum" id="pl-sum">
      <div class="big"><b id="pl-pack"></b><span id="pl-goalt"></span><span id="pl-prog"></span></div>
      <div class="pl-meter goal" id="pl-goalm"><i></i></div><div class="pl-meter" id="pl-progm"><i></i></div>
      <div class="pl-hint" id="pl-hint"></div>
    </div>
    <div class="pl-tabs"><button type="button" id="pl-t-list" class="on">☑ <span data-i18n="List">List</span></button>
      <button type="button" id="pl-t-buy">🛒 <span data-i18n="To buy">To buy</span> <span id="pl-buyn"></span></button></div>
    <div class="pl-tool" id="pl-tool"><input type="search" id="pl-q" data-i18n-ph="Search" placeholder="Search" autocomplete="off">
      <select id="pl-filter" aria-label="Filter"><option value="all" data-i18n="All items">All items</option><option value="open" data-i18n="Not packed yet">Not packed yet</option>
        <option value="buy" data-i18n="To buy">To buy</option><option value="now" data-i18n="Without a weight">Without a weight</option></select>
      <select id="pl-sort" aria-label="Sort"><option value="cat" data-i18n="By category">By category</option><option value="name" data-i18n="By name">By name</option>
        <option value="weight" data-i18n="Heaviest first">Heaviest first</option><option value="open" data-i18n="Not packed first">Not packed first</option></select></div>
    <div id="pl-items"></div><div class="pl-empty" id="pl-inone" hidden></div>
    <form class="pl-add" id="pl-add" hidden autocomplete="off"><input type="text" id="pl-addin" enterkeyhint="done" data-i18n-ph="Name, weight – e.g. Headlamp 85 g" placeholder="Name, weight – e.g. Headlamp 85 g" maxlength="300">
      <button type="submit" id="pl-addb" aria-label="Add">＋</button></form>
  </section>
</main>
<script>
/*COMMON*/
Object.assign(I18N.de, /*PLDE*/{});
(function () {
  const CATS = /*PLCATS*/[], CK = {}, NS = "http://www.w3.org/2000/svg";
  CATS.forEach((c, i) => { CK[c[0]] = {en: c[1], col: c[2], d: c[3], i}; });
  const S = {ov: null, L: null, items: [], rev: 0, view: "list", poll: 0, hint: null, flash: {}, me: "", sheet: null};
  const tf = (s, o) => { let x = t(s); Object.keys(o || {}).forEach(k => { x = x.split("{" + k + "}").join(o[k]); }); return x; };
  const num = x => { const s = x.toFixed(2).replace(/\.?0+$/, ""); return LANG === "en" ? s : s.replace(".", ","); };
  const fmtG = g => g == null ? "–" : g < 1000 ? g + " g" : num(g / 1000) + " kg";
  const fmtW = g => g == null ? "" : (g < 1000 || g % 10) ? g + " g" : num(g / 1000) + " kg";          // exact: for a field that is read again
  const catName = c => CK[c] ? t(CK[c].en) : c;
  const catOrder = c => { const o = CK[((S.L || {}).ci || {})[c]]; return c === "other" ? [900, ""] : CK[c] ? [CK[c].i, ""] : o ? [o.i + .5, c.toLowerCase()] : [800, c.toLowerCase()]; };
  const msg = (txt, bad) => { const m = $("#pl-msg"); m.hidden = !txt; m.textContent = txt || ""; m.classList.toggle("bad", !!bad); };
  const when = s => new Date(s * 1000).toLocaleDateString();
  function icon(cat, size, bg) {
    const k = CK[cat] || CK[((S.L || {}).ci || {})[cat]] || CK.other, b = el("span", "pl-ic"), s = document.createElementNS(NS, "svg"), p = document.createElementNS(NS, "path");
    s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("width", size); s.setAttribute("height", size); s.setAttribute("fill", "none"); s.setAttribute("stroke", k.col);
    s.setAttribute("stroke-width", "1.7"); s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round"); s.setAttribute("aria-hidden", "true");
    p.setAttribute("d", k.d); s.appendChild(p); b.appendChild(s); if (bg) { b.style.background = k.col + "26"; b.style.width = b.style.height = "100%"; }
    return b;
  }
  function totals(items) {
    const T = {n: items.length, packed: 0, buy: 0, total: 0, base: 0, cons: 0, worn: 0, unknown: 0, cats: {}};
    items.forEach(it => { const w = (it.g || 0) * it.n; if (it.packed) T.packed++; if (it.buy) T.buy++; if (it.g == null) T.unknown++; T.total += w; T[it.kind] += w;
      const c = T.cats[it.cat] || (T.cats[it.cat] = {g: 0, n: 0, packed: 0}); c.g += w; c.n++; if (it.packed) c.packed++; });
    T.pack = T.base + T.cons; return T;
  }
  const goalText = (pack, goal) => { const d = pack - goal; return tf("Goal {n}", {n: fmtG(goal)}) + ": " + (d > 0 ? tf("{n} over", {n: fmtG(d)}) : tf("{n} under", {n: fmtG(-d)})); };
  async function api(d) {
    try { const r = await fetch("/api/tausch/pack", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(Object.assign({lang: LANG}, d))});
      return await r.json(); }
    catch (e) { return {ok: false, error: t("No connection to MoveEye."), lost: true}; }
  }
  async function get(q) { try { const r = await fetch("/api/tausch/pack?lang=" + LANG + (q || ""), {cache: "no-store"}); const j = await r.json(); j.status = r.status; return j; } catch (e) { return null; } }
  const canEdit = () => !!(S.L && S.L.edit);
  // ---- sheets ----
  function sheet(title, full) {
    const ov = el("div", "pl-ov"), bx = el("div", "pl-sh" + (full ? " full" : "")), hd = el("div", "pl-shh"), x = el("button", "sec", "✕"), bd = el("div", "pl-shb"), ft = el("div", "pl-shf");
    x.type = "button"; x.setAttribute("aria-label", t("Close")); hd.append(el("b", "", title), x); bx.append(hd, bd, ft); ov.appendChild(bx); ft.hidden = true;
    const sh = {ov, bd, ft, title: hd.firstChild, onclose: null, close() { ov.remove(); if (S.sheet === sh) S.sheet = null; if (sh.onclose) sh.onclose(); }};
    x.onclick = () => sh.close(); ov.addEventListener("click", e => { if (e.target === ov) sh.close(); });
    sh.btn = (txt, cls, fn) => { const b = el("button", cls || "", txt); b.type = "button"; b.onclick = fn; ft.appendChild(b); ft.hidden = false; return b; };
    document.body.appendChild(ov); S.sheet = sh; return sh;
  }
  function field(label, node) { const f = el("label", "pl-f"); f.append(el("span", "", label), node); return f; }
  function input(val, ph, type) { const i = el("input"); i.type = type || "text"; i.value = val == null ? "" : val; if (ph) i.placeholder = ph; i.autocomplete = "off"; return i; }
  function catSelect(cur, withAuto) {
    const s = el("select"), own = [...new Set(S.items.map(x => x.cat).concat(cur ? [cur] : []).filter(c => c && !CK[c]))].sort();
    if (withAuto) { const o = el("option", "", t("Category: automatic")); o.value = ""; s.appendChild(o); }
    CATS.forEach(c => { const o = el("option", "", t(c[1])); o.value = c[0]; s.appendChild(o); });
    own.forEach(c => { const o = el("option", "", c); o.value = c; s.insertBefore(o, s.lastChild); });
    const n = el("option", "", "＋ " + t("Own category …")); n.value = "\u0001"; s.appendChild(n);
    s.value = cur || (withAuto ? "" : "other"); let last = s.value;
    s.addEventListener("change", () => { if (s.value !== "\u0001") { last = s.value; return; }
      const v = (prompt(t("Name of the own category")) || "").trim().slice(0, 40);
      if (!v) { s.value = last; return; } let o = [...s.options].find(z => z.value.toLowerCase() === v.toLowerCase());
      if (!o) { o = el("option", "", v); o.value = v; s.insertBefore(o, n); } s.value = o.value; last = s.value; });
    return s;
  }
  // ---- overview ----
  async function showOverview() {
    stopPoll(); S.L = null; $("#pl-li").hidden = true; $("#pl-ov").hidden = false;
    const j = await get("");
    if (!j) { msg("⚠ " + t("No connection to MoveEye."), true); return; }
    S.ov = j; S.me = (j.me || {}).name || ""; paintOv();
  }
  function ovState() { const j = S.ov || {}, st = j.store || {};
    if (!j.on) msg("⏸ " + t("The file exchange is switched off."));
    else if (st.problem === "missing") msg("⚠ " + t("The storage (USB stick / SSD) is not there - plug it in again."), true);
    else if (st.problem === "ro") msg("⚠ " + t("The memory card is write-protected (overlay) - files would be lost at the next restart. Use a USB stick."), true);
    else msg("");
    return !!(j.on && !st.problem && (j.perms || []).includes("files_up")); }
  function paintOv() {
    const j = S.ov, can = ovState(), box = $("#pl-lists");
    $("#pl-ovbar").hidden = !can; box.textContent = "";
    (j.lists || []).forEach(L => {
      const c = el("button", "pl-card"); c.type = "button"; c.dataset.id = L.id;
      c.append(el("b", "", (L.area === "mine" ? "🔒 " : "") + L.name), el("span", "g", tf("{a} of {b} packed", {a: L.packed, b: L.n}) + " · " + fmtG(L.pack)));
      const m = el("div", "pl-meter"); m.appendChild(el("i")); m.firstChild.style.width = (L.n ? 100 * L.packed / L.n : 0) + "%"; c.appendChild(m);
      if (L.goal_g) { const g = el("span", "g " + (L.pack > L.goal_g ? "pl-over" : "pl-under"), goalText(L.pack, L.goal_g)); c.appendChild(g); }
      c.appendChild(el("small", "", (L.mine ? t("you") : L.by) + " · " + when(L.t) + (L.buy ? " · 🛒 " + L.buy : "")));
      c.onclick = () => { location.hash = "l=" + L.id; }; box.appendChild(c);
    });
    const none = $("#pl-none"); none.hidden = (j.lists || []).length > 0;
    none.textContent = t("No packing lists yet.") + (can ? " " + t("Start with «New list» (also from a template) or import a list you already have.") : "");
    applyI18n();
  }
  function newList() {
    const sh = sheet("＋ " + t("New list")), nm = input("", t("e.g. Weekend in the Jura")), tp = el("select"), goal = input("", t("e.g. 8 kg")), prv = el("input", "sw");
    [["", t("Empty list")]].concat((S.ov.templates || []).map(x => [x.key, tf("Template «{name}» ({n} items)", {name: x.name, n: x.n})])).forEach(o => { const e = el("option", "", o[1]); e.value = o[0]; tp.appendChild(e); });
    prv.type = "checkbox"; const sw = el("label", "pl-sw"); sw.append(el("span", "", "🔒 " + t("Only for me (private)")), prv);
    sh.bd.append(field(t("Name of the list"), nm), field(t("Start from"), tp), field(t("Weight goal for the rucksack (optional)"), goal), sw);
    tp.onchange = () => { if (!nm.value.trim() && tp.value) nm.value = (S.ov.templates.find(x => x.key === tp.value) || {}).name || ""; };
    sh.btn(t("Cancel"), "sec", () => sh.close());
    const ok = sh.btn(t("Create"), "", async () => { if (!nm.value.trim()) { nm.focus(); return; } ok.disabled = true;
      const r = await api({action: "new", name: nm.value, template: tp.value, goal: goal.value, area: prv.checked ? "mine" : "all"}); ok.disabled = false;
      if (!r.ok) { toast("⚠ " + (r.error || t("error"))); return; } sh.close(); location.hash = "l=" + r.id; });
    setTimeout(() => nm.focus(), 50);
  }
  // ---- one list ----
  function stopPoll() { clearInterval(S.poll); S.poll = 0; }
  async function openList(id) {
    stopPoll(); $("#pl-ov").hidden = true; $("#pl-li").hidden = false; $("#pl-items").textContent = ""; $("#pl-name").textContent = "…";
    const j = await get("&id=" + id + "&since=0");
    if (!j) { msg("⚠ " + t("No connection to MoveEye."), true); S.poll = setInterval(() => { if (!S.L) route(); }, 4000); return; }
    if (!j.ok) { toast("⚠ " + (j.error || t("error"))); location.hash = ""; return; }
    if (!S.ov) { S.ov = await get("") || {}; S.me = (S.ov.me || {}).name || ""; }
    msg(""); S.L = j.head; S.items = j.items; S.rev = j.rev; S.hint = null; paintList();
    S.poll = setInterval(poll, window.PL_POLL_MS || 3000);
  }
  function take(it, mine) {
    const old = S.items.find(x => x.id === it.id);
    if (!old) { S.items.push(it); return true; }
    if (old._p && !mine) return false;                                   // my own change is on its way: the answer decides
    if (it.rev < old.rev) return false;
    const ch = it.rev !== old.rev; const p = old._p; Object.assign(old, it); old._p = p; return ch;
  }
  let polling = false;
  async function poll() {
    if (polling || !S.L || document.hidden) return; polling = true;
    try {
      const id = S.L.id, j = await get("&id=" + id + "&since=" + S.rev);
      if (!S.L || S.L.id !== id) return;
      if (!j) { $("#pl-hint").textContent = "⚠ " + t("No connection to MoveEye."); return; }
      if (j.status === 404) { stopPoll(); toast(t("This list was deleted.")); location.hash = ""; return; }
      if (!j.ok || j.same) { if (j.same && $("#pl-hint").textContent.startsWith("⚠")) paintHint(); return; }
      const changed = [];
      if (j.full) { const pend = S.items.filter(x => x._p); S.items = j.items; pend.forEach(p => { const n = S.items.find(x => x.id === p.id); if (n) { ["packed", "buy"].forEach(k => n[k] = p[k]); n._p = p._p; } }); }
      else { (j.items || []).forEach(it => { if (take(it)) changed.push(it.id); });
        if ((j.gone || []).length) S.items = S.items.filter(x => !j.gone.includes(x.id));
        if (j.order) { const pos = {}; j.order.forEach((x, i) => pos[x] = i); S.items.sort((a, b) => (pos[a.id] === undefined ? 1e9 : pos[a.id]) - (pos[b.id] === undefined ? 1e9 : pos[b.id])); } }
      S.rev = j.rev; if (j.head) S.L = j.head;
      const other = S.items.filter(x => changed.includes(x.id) && x.by && x.by !== S.me).sort((a, b) => b.t - a.t)[0];      // who changed what I just received
      if (other) S.hint = {by: other.by, age: Math.max(0, j.now - other.t), at: Date.now()};
      else if (j.last && j.last.by && j.last.by !== S.me && ((j.gone || []).length || (j.full && S.rev))) S.hint = {by: j.last.by, age: Math.max(0, j.now - j.last.t), at: Date.now()};
      changed.forEach(i => S.flash[i] = Date.now());
      paintList();
    } finally { polling = false; }
  }
  function paintHint() {
    const h = $("#pl-hint"), x = S.hint;
    if (!x) { h.textContent = ""; return; }
    const age = Math.round(x.age + (Date.now() - x.at) / 1000);
    if (age > 120) { S.hint = null; h.textContent = ""; return; }
    h.textContent = age < 60 ? tf("changed by {who} {n} s ago", {who: x.by, n: age}) : tf("changed by {who} {n} min ago", {who: x.by, n: Math.floor(age / 60)});
  }
  setInterval(() => { if (S.L && S.hint) paintHint(); }, 1000);
  function shown() {
    const q = ($("#pl-q").value || "").trim().toLowerCase(), f = $("#pl-filter").value, buyView = S.view === "buy";
    return S.items.filter(it => (buyView ? it.buy : (f === "all" || (f === "open" && !it.packed) || (f === "buy" && it.buy) || (f === "now" && it.g == null)))
      && (!q || it.name.toLowerCase().includes(q) || (it.note || "").toLowerCase().includes(q) || catName(it.cat).toLowerCase().includes(q)));
  }
  function paintList() {
    const L = S.L; if (!L) return;
    const T = totals(S.items), edit = canEdit(), buyView = S.view === "buy";
    $("#pl-name").textContent = (L.area === "mine" ? "🔒 " : "") + L.name; document.title = L.name + " – MoveEye";
    const nt = $("#pl-note"); nt.hidden = !(L.note || !edit); nt.textContent = (edit ? "" : "👁 " + t("You may look at the packing lists, but not change them.") + " ") + (L.note || "");
    $("#pl-pack").textContent = "🎒 " + fmtG(T.pack);
    $("#pl-parts").textContent = t("Base weight") + " " + fmtG(T.base) + " · " + t("Consumable") + " " + fmtG(T.cons) + (T.worn ? " · " + t("Worn") + " " + fmtG(T.worn) : "")
      + (T.unknown ? " · " + tf("{n} without a weight", {n: T.unknown}) : "") + " · " + tf("{a} of {b} packed", {a: T.packed, b: T.n});
    $("#pl-goalm").hidden = !L.goal_g; $("#pl-goalt").textContent = "";
    if (L.goal_g) { const over = T.pack > L.goal_g, gt = $("#pl-goalt"); gt.textContent = goalText(T.pack, L.goal_g); gt.className = over ? "pl-over" : "pl-under";
      const m = $("#pl-goalm"); m.classList.toggle("over", over); m.firstChild.style.width = Math.min(100, 100 * T.pack / L.goal_g).toFixed(1) + "%"; }
    $("#pl-prog").textContent = "✓ " + T.packed + "/" + T.n; $("#pl-prog").title = tf("{a} of {b} packed", {a: T.packed, b: T.n});
    $("#pl-progm").firstChild.style.width = (T.n ? 100 * T.packed / T.n : 0).toFixed(1) + "%";
    paintHint();
    $("#pl-t-list").classList.toggle("on", !buyView); $("#pl-t-buy").classList.toggle("on", buyView); $("#pl-buyn").textContent = T.buy ? "(" + T.buy + ")" : "";
    $("#pl-filter").hidden = $("#pl-sort").hidden = buyView;
    $("#pl-add").hidden = !edit; $("#pl-addin").placeholder = buyView ? t("Still missing – e.g. Gas canister") : t("Name, weight – e.g. Headlamp 85 g");
    const box = $("#pl-items"), keepY = window.scrollY; box.textContent = "";
    const list = shown(), so = buyView ? "cat" : $("#pl-sort").value, now = Date.now();
    const w = it => (it.g || 0) * it.n;
    if (so === "cat") {
      const groups = {}; list.forEach(it => (groups[it.cat] || (groups[it.cat] = [])).push(it));
      Object.keys(groups).sort((a, b) => { const x = catOrder(a), y = catOrder(b); return x[0] - y[0] || x[1].localeCompare(y[1]); }).forEach(c => {
        const h = el("div", "pl-cat"), ic = icon(c, 20, true), tc = T.cats[c] || {g: 0, n: 0, packed: 0}; ic.style.width = ic.style.height = "28px";
        h.append(ic, el("span", "", catName(c)), el("span", "w", buyView ? String(groups[c].length) : tc.packed + "/" + tc.n + " · " + fmtG(tc.g))); box.appendChild(h);
        groups[c].forEach(it => box.appendChild(row(it, buyView, edit, now)));
      });
    } else {
      const cmp = {name: (a, b) => a.name.localeCompare(b.name), weight: (a, b) => w(b) - w(a) || a.name.localeCompare(b.name), open: (a, b) => (a.packed - b.packed) || a.name.localeCompare(b.name)}[so];
      list.slice().sort(cmp).forEach(it => box.appendChild(row(it, buyView, edit, now)));
    }
    const none = $("#pl-inone"); none.hidden = list.length > 0;
    none.textContent = buyView ? (S.items.length ? "✓ " + t("Nothing is missing.") : t("This list is still empty.")) + (edit ? " " + t("Mark an item with 🛒 or add what is missing below.") : "")
      : S.items.length ? t("Nothing found.") : t("This list is still empty.") + (edit ? " " + t("Add the first item below or import a list.") : "");
    if (Math.abs(window.scrollY - keepY) > 2) window.scrollTo(0, keepY);
  }
  function row(it, buyView, edit, now) {
    const r = el("div", "pl-row" + (!buyView && it.packed ? " done" : "") + (it.buy ? " buy" : "")), tk = el("button", "pl-tick"), pic = el("button", "pl-pic"), tx = el("div", "pl-tx"), sb = el("div", "sb");
    r.dataset.id = it.id; if (S.flash[it.id] && now - S.flash[it.id] < 2500) { r.classList.add("flash"); setTimeout(() => r.classList.remove("flash"), 900); }
    tk.type = "button"; tk.appendChild(el("i", "", "✓")); tk.disabled = !edit;
    tk.setAttribute("role", "checkbox"); tk.setAttribute("aria-checked", buyView ? "false" : String(!!it.packed));
    tk.setAttribute("aria-label", (buyView ? t("Bought") : t("Packed")) + ": " + it.name);
    tk.onclick = () => buyView ? setItem(it, {buy: false}, "🛒 ✓ " + it.name) : setItem(it, {packed: !it.packed});
    pic.type = "button"; pic.setAttribute("aria-label", it.photo ? t("Show the photo") : catName(it.cat));
    if (it.photo) { const im = el("img"); im.alt = ""; im.loading = "lazy"; im.src = "/tausch/pack/b/" + S.L.id + "/" + it.id + ".jpg?v=" + it.photo;
      im.onerror = () => { im.remove(); pic.appendChild(icon(it.cat, 24, true)); }; pic.appendChild(im); pic.onclick = () => lightbox(it); }
    else { pic.appendChild(icon(it.cat, 24, true)); pic.onclick = () => { if (edit) editItem(it); }; }
    tx.appendChild(el("div", "nm", (it.n > 1 ? it.n + "× " : "") + it.name));
    if (it.g != null) { sb.appendChild(el("b", "", fmtG(it.g * it.n))); if (it.n > 1) sb.appendChild(document.createTextNode(" (" + tf("{n} each", {n: fmtG(it.g)}) + ")")); }
    else sb.appendChild(document.createTextNode("– g"));
    if (it.kind !== "base") sb.appendChild(el("span", "pl-tag", t(it.kind === "cons" ? "Consumable" : "Worn")));
    if (it.buy && !buyView && !edit) sb.appendChild(el("span", "pl-tag buy", "🛒 " + t("To buy")));
    if (it.note) sb.appendChild(document.createTextNode(" · " + it.note));
    tx.appendChild(sb); r.append(tk, pic, tx);
    if (edit) {
      if (!buyView) { const b = el("button", "pl-ib" + (it.buy ? " on" : ""), "🛒"); b.type = "button"; b.setAttribute("aria-label", t("Still missing / to buy") + ": " + it.name); b.setAttribute("aria-pressed", String(!!it.buy));
        b.onclick = () => setItem(it, {buy: !it.buy}); r.appendChild(b); }
      const e = el("button", "pl-ib pl-ed", "✎"); e.type = "button"; e.setAttribute("aria-label", t("Edit") + ": " + it.name); e.onclick = () => editItem(it); r.appendChild(e);
    }
    return r;
  }
  async function setItem(it, set, say) {
    Object.assign(it, set); it._p = (it._p || 0) + 1; paintList();
    const r = await api({action: "item", list: S.L.id, id: it.id, set, base: it.rev}); it._p--;
    if (!r.ok) { if (r.gone) S.items = S.items.filter(x => x.id !== it.id); toast("⚠ " + (r.error || t("error"))); S.rev = 0; await poll(); paintList(); return false; }
    take(r.item, true); if (r.head) S.L = r.head; if (say) toast(say); paintList(); return true;
  }
  function lightbox(it) {
    const ov = el("div", "pl-lb"), bar = el("div", "bar"), bd = el("div", "bd"), x = el("button", "sec", "✕"), im = el("img");
    x.type = "button"; x.onclick = () => ov.remove(); bar.append(el("b", "", it.name), x);
    im.alt = it.name; im.src = "/tausch/pack/b/" + S.L.id + "/" + it.id + ".jpg?p=1&v=" + it.photo; bd.appendChild(im);
    ov.append(bar, bd); ov.addEventListener("click", e => { if (e.target === ov || e.target === bd) ov.remove(); }); document.body.appendChild(ov);
  }
  // ---- the photo of an item: the upload of the file exchange (same script, cut out of its page) ----
  let upPaint = null;
  function paintJobs() { if (upPaint) upPaint(); }
  /*PLUP*/
  const canUp = typeof upOne === "function";
  async function shrink(file) {                                            // smaller before sending (fast over a slow link); HEIC -> JPEG where the browser can draw it
    try {
      if (window.PL_NO_SHRINK) return file;
      const url = URL.createObjectURL(file);
      const im = await new Promise((ok, bad) => { const i = new Image(), tm = setTimeout(() => bad(new Error("timeout")), 10000);
        i.onload = () => { clearTimeout(tm); ok(i); }; i.onerror = () => { clearTimeout(tm); bad(new Error("decode")); }; i.src = url; });
      const w = im.naturalWidth, h = im.naturalHeight, s = Math.min(1, 1600 / Math.max(w, h, 1));
      if (!w || !h) throw new Error("empty");
      if (s === 1 && file.size < 1200000 && /jpe?g$/i.test(file.type || "")) { URL.revokeObjectURL(url); return file; }
      const c = document.createElement("canvas"); c.width = Math.max(1, Math.round(w * s)); c.height = Math.max(1, Math.round(h * s));
      c.getContext("2d").drawImage(im, 0, 0, c.width, c.height); URL.revokeObjectURL(url);
      const bl = await new Promise(ok => c.toBlob(ok, "image/jpeg", 0.86));
      if (!bl || bl.size < 300) return file;
      const nm = String(file.name || "foto").replace(/\.[^.]+$/, "") + ".jpg", lm = file.lastModified || Date.now();
      try { return new File([bl], nm, {type: "image/jpeg", lastModified: lm}); } catch (e) { bl.name = nm; bl.lastModified = lm; return bl; }
    } catch (e) { return file; }
  }
  // ---- edit one item ----
  function editItem(it) {
    const sh = sheet("✎ " + it.name), nm = input(it.name), wt = input(fmtW(it.g), t("e.g. 350 g or 1.2 kg")), qn = input(it.n, "", "number"), cat = catSelect(it.cat), note = input(it.note, t("optional"));
    qn.min = 1; qn.max = 999; qn.inputMode = "numeric"; wt.inputMode = "text"; nm.maxLength = 120; note.maxLength = 300;
    let kind = it.kind; const seg = el("div", "pl-seg");
    [["base", "Base weight"], ["cons", "Consumable"], ["worn", "Worn"]].forEach(k => { const b = el("button", kind === k[0] ? "on" : "", t(k[1])); b.type = "button"; b.dataset.k = k[0];
      b.onclick = () => { kind = k[0]; [...seg.children].forEach(z => z.classList.toggle("on", z === b)); }; seg.appendChild(b); });
    cat.addEventListener("change", () => { if (cat.value === "food" && kind === "base") seg.children[1].click(); });
    const two = el("div", "pl-2"); two.append(field(t("Weight per piece"), wt), field(t("Quantity"), qn));
    const mk = (label, on) => { const l = el("label", "pl-sw"), c = el("input", "sw"); c.type = "checkbox"; c.checked = !!on; l.append(el("span", "", label), c); return [l, c]; };
    const [l1, cPacked] = mk("✓ " + t("Packed"), it.packed), [l2, cBuy] = mk("🛒 " + t("Still missing / to buy"), it.buy);
    // photo
    const ph = el("div", "pl-ph"), upm = el("div", "pl-upm"), fi = el("input"); fi.type = "file"; fi.accept = "image/*"; fi.hidden = true; fi.id = "pl-photo";
    const paintPh = () => { ph.textContent = "";
      if (it.photo) { const im = el("img"); im.alt = ""; im.src = "/tausch/pack/b/" + S.L.id + "/" + it.id + ".jpg?v=" + it.photo; im.onclick = () => lightbox(it); ph.appendChild(im); }
      else { const b = el("span", ""); b.style.cssText = "width:84px;height:84px;border-radius:12px;overflow:hidden;display:block"; b.appendChild(icon(cat.value, 44, true)); ph.appendChild(b); }
      if (canUp) { const b = el("button", "sec", "📷 " + t(it.photo ? "Change the photo" : "Take or choose a photo")); b.type = "button"; b.id = "pl-photob"; b.onclick = () => fi.click(); ph.appendChild(b); }
      if (it.photo) { const b = el("button", "sec", "✕ " + t("Remove the photo")); b.type = "button"; b.onclick = async () => { const r = await api({action: "photo_rm", list: S.L.id, id: it.id});
        if (r.ok) { take(r.item, true); paintPh(); paintList(); } else toast("⚠ " + (r.error || t("error"))); }; ph.appendChild(b); } };
    let jb = null;
    const paintUp = () => { if (!jb) return; upm.textContent = ""; upm.classList.toggle("err", !!jb.err);
      const got = Math.min(jb.file.size, jb.have + (jb.part || 0)), p = jb.file.size ? Math.floor(100 * got / jb.file.size) : 0;
      upm.appendChild(document.createTextNode(jb.err ? "⚠ " + jb.err : jb.done ? "✓ " + t("Photo saved") : "⬆ " + p + " %" + (jb.state ? " · " + jb.state : "")));
      if (jb.err && jb.diag) upm.appendChild(el("div", "dg", jb.diag));
      if (jb.err && jb.retry) { const b = el("button", "sec", "↻ " + t("Try once more")); b.type = "button"; b.style.cssText = "display:block;margin-top:6px;min-height:44px";
        b.onclick = () => { jb.err = ""; jb.retry = false; jb.cancel = false; jb.state = ""; go(); }; upm.appendChild(b); } };
    const go = async () => { upPaint = paintUp; paintUp();
      try { await upOne(jb); } catch (e) { jb.err = t("error") + ": " + String((e && e.message) || e).slice(0, 80); jb.retry = true; }
      paintUp(); if (jb.done) { S.rev = 0; await poll(); const n = S.items.find(x => x.id === it.id); if (n) { it = n; } paintPh(); } };
    fi.onchange = async () => { const f = fi.files && fi.files[0]; fi.value = ""; if (!f) return;
      upm.classList.remove("err"); upm.textContent = "… " + t("Preparing the photo"); const f2 = await shrink(f);
      jb = {file: f2, area: "mine", folder: "", pack: {list: S.L.id, item: it.id}, have: 0, part: 0, done: false, err: "", cancel: false}; go(); };
    sh.onclose = () => { if (jb && !jb.done && !jb.err) { jb.cancel = true; if (jb.xhr) try { jb.xhr.abort(); } catch (e) {} } upPaint = null; };
    sh.bd.append(field(t("Name"), nm), two, field(t("Category"), cat), field(t("Counts as"), seg), field(t("Remark"), note), l1, l2, el("div", "pl-f"), ph, upm, fi);
    sh.bd.children[7].appendChild(el("span", "", t("Photo")));
    paintPh();
    const del = sh.btn("🗑", "sec", async () => { if (!confirm(t("Delete this item?") + "\n" + it.name)) return;
      const r = await api({action: "rm", list: S.L.id, id: it.id}); if (!r.ok && !r.gone) { toast("⚠ " + (r.error || t("error"))); return; }
      S.items = S.items.filter(x => x.id !== it.id); if (r.head) S.L = r.head; sh.close(); paintList(); });
    del.style.flex = "0 0 52px"; del.setAttribute("aria-label", t("Delete this item?"));
    sh.btn(t("Cancel"), "sec", () => sh.close());
    const ok = sh.btn(t("Save"), "", async () => { ok.disabled = true;
      const r = await api({action: "item", list: S.L.id, id: it.id, base: it.rev, set: {name: nm.value, w: wt.value, n: parseInt(qn.value, 10) || 1, cat: cat.value, note: note.value, kind, packed: cPacked.checked, buy: cBuy.checked}});
      ok.disabled = false; if (!r.ok) { toast("⚠ " + (r.error || t("error"))); if (r.gone) { sh.close(); S.rev = 0; poll(); } return; }
      take(r.item, true); if (r.head) S.L = r.head; sh.close(); paintList(); });
    ok.id = "pl-save";
  }
  // ---- menu, list settings ----
  function menu() {
    const L = S.L, sh = sheet(L.name), m = el("div", "pl-menu"); sh.bd.appendChild(m);
    const b = (txt, fn, cls) => { const x = el("button", cls || "sec", txt); x.type = "button"; x.onclick = () => { sh.close(); fn(); }; m.appendChild(x); return x; };
    const a = (txt, href, dl) => { const x = el("a", "btn sec", txt); x.href = href; if (dl) x.setAttribute("download", ""); x.onclick = () => setTimeout(() => sh.close(), 100); m.appendChild(x); };
    if (L.edit) { b("✎ " + t("Name, weight goal, note"), meta); b("⬇ " + t("Import into this list"), () => importFlow(L));
      b("↺ " + t("Reset all ticks (next trip)"), async () => { if (!confirm(t("Remove all ticks of this list?"))) return; const r = await api({action: "reset", id: L.id});
        if (!r.ok) { toast("⚠ " + (r.error || t("error"))); return; } S.rev = 0; await poll(); toast("↺ " + tf("{n} ticks removed", {n: r.n})); }); }
    if ((S.ov.perms || []).includes("files_up") && S.ov.on) b("⧉ " + t("Copy this list"), async () => { const n = prompt(t("Name of the copy"), tf("{name} (copy)", {name: L.name})); if (!n) return;
      const r = await api({action: "copy", id: L.id, name: n}); if (!r.ok) { toast("⚠ " + (r.error || t("error"))); return; } location.hash = "l=" + r.id; });
    a("🖨 " + t("Print"), "/tausch/pack/druck/" + L.id + "?lang=" + LANG);
    if (L.dl) { a("⬇ CSV (" + t("table for Excel / Numbers") + ")", "/tausch/pack/x/" + L.id + ".csv?lang=" + LANG, true); a("⬇ JSON (" + t("the list as MoveEye stores it") + ")", "/tausch/pack/x/" + L.id + ".json", true);
      a("⬇ ZIP (" + t("list and photos, as a backup") + ")", "/tausch/pack/x/" + L.id + ".zip?lang=" + LANG, true); }
    if (L.rm) b("🗑 " + t("Delete this list"), async () => { if (!confirm(t("Delete this list with all its photos? It cannot be undone.") + "\n" + L.name)) return;
      const r = await api({action: "del", id: L.id}); if (!r.ok) { toast("⚠ " + (r.error || t("error"))); return; } toast("🗑 " + L.name); location.hash = ""; }, "red");
  }
  function meta() {
    const L = S.L, sh = sheet("✎ " + L.name), nm = input(L.name), goal = input(L.goal_g ? fmtW(L.goal_g) : "", t("e.g. 8 kg")), note = input(L.note, t("optional")), prv = el("input", "sw");
    nm.maxLength = 80; note.maxLength = 300; prv.type = "checkbox"; prv.checked = L.area === "mine";
    const sw = el("label", "pl-sw"); sw.append(el("span", "", "🔒 " + t("Only for me (private)")), prv);
    sh.bd.append(field(t("Name of the list"), nm), field(t("Weight goal for the rucksack (optional)"), goal), field(t("Remark"), note)); if (L.mine || (S.ov.me || {}).admin) sh.bd.appendChild(sw);
    sh.bd.appendChild(el("div", "mut", t("The goal counts base weight and consumables - not what you wear.")));
    sh.btn(t("Cancel"), "sec", () => sh.close());
    sh.btn(t("Save"), "", async () => { const r = await api({action: "meta", id: L.id, name: nm.value, goal: goal.value, note: note.value, area: prv.checked ? "mine" : "all"});
      if (!r.ok) { toast("⚠ " + (r.error || t("error"))); return; } S.L = r.head; sh.close(); paintList(); });
  }
  // ---- import: file or pasted text -> preview (columns, rows) -> import ----
  function importFlow(target) {
    const sh = sheet("⬇ " + t("Import"), true); let P = null, into = target ? target.id : "";
    const step1 = () => {
      sh.bd.textContent = ""; sh.ft.textContent = ""; sh.ft.hidden = true; sh.title.textContent = "⬇ " + t("Import");
      const fi = el("input"); fi.type = "file"; fi.hidden = true; fi.id = "pl-impfile";      // no «accept»: a list can have any ending (a note saved as .py) - the device looks at the content
      const fb = el("button", "", "📄 " + t("Choose a file")); fb.type = "button"; fb.style.minHeight = "48px"; fb.onclick = () => fi.click();
      const ta = el("textarea"); ta.id = "pl-imptext"; ta.placeholder = t("Paste the text here – one item per line. Example:") + "\n\nKüche:\n- Kocher 90 g\n- 2x Gaskartusche (230 g)\nZelt – 1.8 kg";
      const pv = el("button", "sec", t("Preview")); pv.type = "button"; pv.style.minHeight = "48px"; pv.id = "pl-imppv";
      const st = el("div", "pl-upm"); st.id = "pl-impst";
      if (target) { const sel = el("select"); sel.id = "pl-impinto"; [["" + target.id, tf("Add to «{name}»", {name: target.name})], ["", t("Make a new list from it")]].forEach(o => { const e = el("option", "", o[1]); e.value = o[0]; sel.appendChild(e); });
        sel.value = into; sel.onchange = () => { into = sel.value; }; sh.bd.appendChild(field(t("Where to"), sel)); }
      sh.bd.append(el("p", "mut", t("Text file (one item per line), Excel (.xlsx) or CSV. You always see a preview first and can correct everything.")), fb, fi,
        field(t("… or paste text (e.g. from the Notes app)"), ta), pv, st);
      const run = async fn => { st.classList.remove("err"); st.textContent = "… " + t("Reading"); fb.disabled = pv.disabled = true; let r = null;
        try { r = await fn(); } catch (e) { r = {ok: false, error: t("No connection to MoveEye.")}; } fb.disabled = pv.disabled = false;
        if (!r || !r.ok) { st.classList.add("err"); st.textContent = "⚠ " + ((r && r.error) || t("error")); return; }
        if (!r.items.length && r.kind !== "table") { st.classList.add("err"); st.textContent = "⚠ " + t("Nothing to import was found."); return; }
        P = r; P.items.forEach(x => x.on = true); mergeHeads(); step2(); };
      fi.onchange = () => { const f = fi.files && fi.files[0]; fi.value = ""; if (!f) return;
        if (f.size > ((S.ov.caps || {}).import || 5242880)) { st.classList.add("err"); st.textContent = "⚠ " + t("The file is too big."); return; }
        run(async () => { const buf = await f.arrayBuffer(); const r = await fetch("/api/tausch/pack/import?lang=" + LANG + "&name=" + encodeURIComponent(f.name) + "&list=" + into,
          {method: "POST", headers: {"Content-Type": "application/octet-stream"}, body: buf}); return await r.json(); }); };
      pv.onclick = () => { if (!ta.value.trim()) { ta.focus(); return; } run(() => api({action: "preview", text: ta.value, list: into})); };
    };
    const mergeHeads = () => { let c = null; const hs = P.heads || [], out = [];                 // headings as rows of their own: one tap makes an item of them (and back)
      P.items.forEach((x, i) => { hs.filter(h => h[0] === i).forEach(h => { c = h[2]; out.push({head: true, name: h[1], cat: h[2], on: false}); }); x.auto = P.kind === "lines"; x.c0 = c ? "other" : x.cat; out.push(x); });
      hs.filter(h => h[0] >= P.items.length).forEach(h => out.push({head: true, name: h[1], cat: h[2], on: false})); P.items = out; };
    const recat = () => { let c = null; P.items.forEach(x => { if (x.head) c = x.cat; else if (x.auto) x.cat = c || x.c0; }); };
    const remap = async () => { const r = await api({action: "preview", rows: P.rows, guess: {map: P.map, header: P.header, unit: P.unit}, list: into});
      if (!r.ok) { toast("⚠ " + (r.error || t("error"))); return; } const title = P.title; P = r; P.title = title; P.items.forEach(x => x.on = true); step2(); };
    const step2 = () => {
      sh.bd.textContent = ""; sh.ft.textContent = ""; sh.title.textContent = "⬇ " + t("Preview");
      const tgt = S.L && into === S.L.id ? S.L : null, nm = input(P.title || "", t("Name of the list")); nm.id = "pl-impname"; nm.maxLength = 80;
      if (!into) sh.bd.appendChild(field(t("Name of the new list"), nm));
      if (P.kind === "table") {
        const mp = el("div", "pl-map"), g = el("div", "g"), cols = Math.max.apply(null, P.rows.map(r => r.length)), first = P.rows[0] || [];
        mp.appendChild(el("div", "mut", t("Which column is what? MoveEye guessed - please check."))); mp.firstChild.style.margin = "0 0 8px";
        [["name", "Name"], ["g", "Weight"], ["n", "Quantity"], ["cat", "Category"], ["note", "Remark"]].forEach(f => {
          const s = el("select"); s.dataset.f = f[0]; const o0 = el("option", "", "–"); o0.value = "-1"; s.appendChild(o0);
          for (let i = 0; i < cols; i++) { const o = el("option", "", String.fromCharCode(65 + i % 26) + (i > 25 ? i : "") + " · " + String(first[i] || "").slice(0, 24)); o.value = i; s.appendChild(o); }
          s.value = String(P.map[f[0]]); s.onchange = () => { const v = parseInt(s.value, 10); Object.keys(P.map).forEach(k => { if (k !== f[0] && v >= 0 && P.map[k] === v) P.map[k] = -1; }); P.map[f[0]] = v; remap(); };
          g.append(el("span", "", t(f[1])), s); });
        const us = el("select"); us.id = "pl-unit"; [["g", t("grams (g)")], ["kg", t("kilograms (kg)")]].forEach(o => { const e = el("option", "", o[1]); e.value = o[0]; us.appendChild(e); }); us.value = P.unit;
        us.onchange = () => { P.unit = us.value; remap(); }; g.append(el("span", "", t("Numbers without a unit are")), us); mp.appendChild(g);
        const hl = el("label", "pl-sw"), hc = el("input", "sw"); hc.type = "checkbox"; hc.checked = !!P.header; hc.id = "pl-hdr"; hc.onchange = () => { P.header = hc.checked; remap(); };
        hl.append(el("span", "", t("The first row is the heading")), hc); mp.appendChild(hl); sh.bd.appendChild(mp);
      }
      const sum = el("div", "pl-upm"); sum.id = "pl-pvsum"; sh.bd.appendChild(sum);
      const box = el("div"); box.id = "pl-pvlist"; sh.bd.appendChild(box);
      const room = P.room == null ? 500 : P.room;
      const paintSum = () => { const on = P.items.filter(x => x.on), d = on.filter(x => x.dup).length;
        let g = 0; on.forEach(x => { g += (x.g || 0) * (x.n || 1); });
        sum.classList.toggle("err", on.length > room);
        sum.textContent = tf("{n} items", {n: on.length}) + " · " + fmtG(g) + (d ? " · ⚠ " + tf("{n} doubles", {n: d}) : "") + (P.skipped ? " · " + tf("{n} lines not understood", {n: P.skipped}) : "")
          + (on.length > room ? " · ⚠ " + tf("only {n} more fit into this list", {n: room}) : "");
        go.textContent = "✓ " + tf("Import {n} items", {n: Math.min(on.length, room)}); go.disabled = !on.length; };
      P.items.forEach((x, i) => {
        const sw = (txt, fn) => { const b = el("button", "sec pl-sw2", txt); b.type = "button"; b.onclick = fn; return b; };
        if (x.head) { const r = el("div", "pl-pv pl-pvh"); r.append(el("b", "", catName(x.cat) + (catName(x.cat).toLowerCase() === x.name.toLowerCase() ? "" : " («" + x.name + "»)")),
          sw(t("As item"), () => { Object.assign(x, {head: false, on: true, g: null, w: "", n: 1, note: "", auto: true, c0: "other"}); recat(); step2(); })); box.appendChild(r); return; }
        const r = el("div", "pl-pv"), cl = el("label", "pl-pvc"), c = el("input"), f = el("div", "pl-pvf"), n1 = input(x.name), r2 = el("div", "r2"), w = input(fmtW(x.g), t("Weight")), q = input(x.n, "", "number"), cs = catSelect(x.cat);
        c.type = "checkbox"; c.checked = true; c.setAttribute("aria-label", t("Import") + ": " + x.name); cl.appendChild(c); n1.className = "nm"; n1.maxLength = 120; q.min = 1; q.max = 999; n1.setAttribute("aria-label", t("Name")); w.setAttribute("aria-label", t("Weight")); q.setAttribute("aria-label", t("Quantity"));
        if (x.w === undefined) x.w = fmtW(x.g); w.value = x.w; c.checked = x.on; r.classList.toggle("off", !x.on);
        c.onchange = () => { x.on = c.checked; r.classList.toggle("off", !x.on); paintSum(); };
        n1.oninput = () => { x.name = n1.value; }; w.oninput = () => { x.w = w.value; x.g = null; }; q.oninput = () => { x.n = parseInt(q.value, 10) || 1; paintSum(); }; cs.addEventListener("change", () => { x.cat = cs.value; x.auto = false; });
        r2.append(w, q, cs); f.append(n1, r2);
        if (x.dup) f.appendChild(el("small", "", "⚠ " + t(x.dup === "list" ? "Double: already in the list" : "Double: twice in this import")));
        if (x.like) f.appendChild(el("small", "", "≈ " + tf("Similar to «{name}» in the list", {name: x.like})));
        if (x.packed || x.buy || x.note) f.appendChild(el("small", "", [x.packed ? "✓ " + t("Packed") : "", x.buy ? "🛒 " + t("To buy") : "", x.note].filter(Boolean).join(" · "))).style.color = "var(--mut)";
        if (P.kind === "lines") f.appendChild(sw(t("As category"), async () => { const k = await api({action: "preview", cat: x.name}); if (!k.ok) return;
          Object.assign(x, {head: true, on: false, cat: k.cat}); recat(); step2(); }));
        r.append(cl, f); box.appendChild(r);
      });
      sh.ft.hidden = false; sh.btn("‹ " + t("Back"), "sec", step1).style.flex = "0 0 auto";
      const go = sh.btn("", "", async () => { go.disabled = true;
        const items = P.items.filter(x => x.on && String(x.name || "").trim()).map(x => ({name: x.name, w: x.g != null ? x.g + " g" : x.w, n: x.n, cat: x.cat, note: x.note, kind: x.kind, packed: !!x.packed, buy: !!x.buy}));
        if (!into && !nm.value.trim()) { nm.focus(); go.disabled = false; toast(t("The list needs a name.")); return; }
        const r = await api(into ? {action: "import", list: into, items} : {action: "import", name: nm.value, items, goal: P.goal_g ? P.goal_g + " g" : ""}); go.disabled = false;
        if (!r.ok) { toast("⚠ " + (r.error || t("error"))); return; }
        sh.close(); toast("✓ " + tf("{n} items imported", {n: r.added}) + (r.dups ? " · " + tf("{n} doubles", {n: r.dups}) : ""));
        if (S.L && into === S.L.id) { S.rev = 0; poll(); } else location.hash = "l=" + (r.id || into); });
      go.id = "pl-impgo"; paintSum();
    };
    step1();
  }
  // ---- wiring ----
  function route() {
    const h = new URLSearchParams(location.hash.slice(1)), id = h.get("l") || "";
    if (S.sheet) S.sheet.close();
    S.view = h.get("v") === "buy" ? "buy" : "list";
    if (!/^[0-9a-f]{16}$/.test(id)) { showOverview(); return; }
    if (!S.L || S.L.id !== id) openList(id); else paintList();
  }
  $("#pl-new").onclick = newList; $("#pl-imp").onclick = () => importFlow(null); $("#pl-more").onclick = menu;
  $("#pl-up").onclick = e => { e.preventDefault(); location.hash = ""; };
  $("#pl-t-list").onclick = () => { if (S.L) location.hash = "l=" + S.L.id; }; $("#pl-t-buy").onclick = () => { if (S.L) location.hash = "l=" + S.L.id + "&v=buy"; };
  ["#pl-q", "#pl-filter", "#pl-sort"].forEach(s => $(s).addEventListener("input", () => S.L && paintList()));
  $("#pl-add").addEventListener("submit", async e => { e.preventDefault(); const i = $("#pl-addin"), v = i.value.trim(); if (!v || !S.L) return; $("#pl-addb").disabled = true;
    const r = await api({action: "add", list: S.L.id, text: v, buy: S.view === "buy"}); $("#pl-addb").disabled = false;
    if (!r.ok) { toast("⚠ " + (r.error || t("error"))); return; }
    i.value = ""; take(r.item, true); if (r.head) S.L = r.head; S.flash[r.item.id] = Date.now(); paintList();
    if (r.dup) toast("⚠ " + tf("«{name}» is in the list twice now", {name: r.item.name}));
    const n = document.querySelector('.pl-row[data-id="' + r.item.id + '"]'); if (n && n.scrollIntoView) n.scrollIntoView({block: "center"}); i.focus(); });
  addEventListener("hashchange", route);
  document.addEventListener("visibilitychange", () => { if (!document.hidden && S.L) poll(); });
  const hd = document.querySelector("header");
  const setTop = () => { const st = hd && getComputedStyle(hd); $("#pl").style.setProperty("--plh", (st && (st.position === "sticky" || st.position === "fixed") ? hd.offsetHeight : 0) + "px"); };
  if (hd && window.ResizeObserver) new ResizeObserver(setTop).observe(hd); addEventListener("resize", setTop);
  // the tip card of the guide (515, #gd-card, fixed at the bottom) never lies on the quick-add bar: it sits above it
  const setBar = () => { const a = $("#pl-add"), r = a.hidden || $("#pl-li").hidden ? null : a.getBoundingClientRect(), h = window.innerHeight;
    document.documentElement.style.setProperty("--plb", (r && r.top < h && r.bottom > h - 260 ? Math.max(0, Math.round(h - r.top)) : 0) + "px"); };
  ["scroll", "resize"].forEach(e => addEventListener(e, setBar, {passive: true})); if (window.visualViewport) visualViewport.addEventListener("resize", setBar); setInterval(setBar, 700);
  (async () => { await initAppearance(); setTop(); route(); })();
})();
/*ALERTS*/
</script>
</body></html>
"""


def _pl_upload_js():
    """the upload script of the file exchange page (pieces, watchdog, retries - 639zzc), cut out so that the packing lists send
    photos through exactly the same code; "" when the page looks different (then the photo button stays away, the self-test says so)"""
    a = TAUSCH_PAGE.find("  const UP = Object.assign(")
    b = TAUSCH_PAGE.find("  // a JSON request that cannot wait for ever")
    c = TAUSCH_PAGE.find('  $("#tz-upb").onclick')
    if a < 0 or b < 0 or c < b:
        return ""
    js = TAUSCH_PAGE[a:TAUSCH_PAGE.find("\n", a) + 1] + TAUSCH_PAGE[b:c]
    out = js.replace("folder: jb.folder, lang: LANG}", "folder: jb.folder, pack: jb.pack, lang: LANG}", 1)
    return out if out != js and "async function upOne(jb)" in out else ""


def pl_page_html():
    cats = json.dumps([list(c) for c in PL_CATS], ensure_ascii=False)
    return (render_page(PL_PAGE, "more").replace("/*PLDE*/{}", json.dumps(_PL_DE, ensure_ascii=False).replace("</", "<\\/"), 1)
            .replace("/*PLCATS*/[]", cats, 1).replace("/*PLUP*/", _pl_upload_js(), 1))


# ---- the entry on /tausch and on the guest page ----------------------------------------------------------------------------------
PL_TILE = ('  <a class="tz-card" id="tz-pack" href="/tausch/packlisten" style="display:flex;align-items:center;gap:12px;text-decoration:none;color:inherit;min-height:56px">'
           '<span style="font-size:28px">🎒</span><span style="flex:1;min-width:0"><b data-i18n="Packing lists">Packing lists</b><br>'
           '<small class="mut" data-i18n="Lists with weight, photos and ticks - pack together">Lists with weight, photos and ticks - pack together</small></span>'
           '<span class="mut" style="font-size:20px">›</span></a>\n')
_pl_anchor = '  <div class="tz-msg" id="tz-msg" hidden></div>\n'
if 'id="tz-pack"' not in TAUSCH_PAGE and _pl_anchor in TAUSCH_PAGE:
    TAUSCH_PAGE = TAUSCH_PAGE.replace(_pl_anchor, PL_TILE + _pl_anchor, 1)
_pl_gtop = '<a href="__BASE__">← __LIVE__</a>'
if "__PACK__" not in TAUSCH_GUEST_HTML and _pl_gtop in TAUSCH_GUEST_HTML:
    TAUSCH_GUEST_HTML = TAUSCH_GUEST_HTML.replace(_pl_gtop, '<a href="__BASE__/tausch/pack">🎒 __PACK__</a><a href="__BASE__" style="margin-left:14px">← __LIVE__</a>', 1)

_pl_guest_html_base = tausch_guest_html


# wraps: tausch_guest_html
def tausch_guest_html(token):                              # + 639zzw: the link to the packing lists
    import html as _h
    return _pl_guest_html_base(token).replace("__PACK__", _h.escape(tr("Packing lists", sx_req_lang())))


# ---- texts (English key: Deutsch, français, italiano, rumantsch) --------------------------------------------------------------------
_HX_PACK = {
    "Packing lists": ("Packlisten", "Listes de bagages", "Liste di cose da portare", "Glistas da pachetar"),
    "Lists with weight, photos and ticks - pack together": (
        "Listen mit Gewicht, Fotos und Häkchen – gemeinsam packen", "Listes avec poids, photos et coches – préparer ensemble",
        "Liste con peso, foto e spunte – preparare insieme", "Glistas cun paisa, fotos e crutschs – pachetar ensemen"),
    "New list": ("Neue Liste", "Nouvelle liste", "Nuova lista", "Nova glista"),
    "Import": ("Importieren", "Importer", "Importa", "Importar"),
    "To buy": ("Kaufen", "À acheter", "Da comprare", "Da cumprar"),
    "All items": ("Alle", "Tout", "Tutti", "Tuts"),
    "Not packed yet": ("Noch nicht gepackt", "Pas encore emballé", "Non ancora preparato", "Betg anc pachetà"),
    "Without a weight": ("Ohne Gewicht", "Sans poids", "Senza peso", "Senza paisa"),
    "By category": ("Nach Kategorie", "Par catégorie", "Per categoria", "Tenor categoria"),
    "By name": ("Nach Name", "Par nom", "Per nome", "Tenor num"),
    "Heaviest first": ("Schwerstes zuerst", "Le plus lourd d’abord", "Prima il più pesante", "Il pli grev l’emprim"),
    "Not packed first": ("Nicht Gepacktes zuerst", "Non emballé d’abord", "Prima il non preparato", "Betg pachetà l’emprim"),
    "Name, weight – e.g. Headlamp 85 g": ("Name, Gewicht – z. B. Stirnlampe 85 g", "Nom, poids – p. ex. Lampe frontale 85 g",
                                          "Nome, peso – p. es. Lampada frontale 85 g", "Num, paisa – p.ex. Lampa frontala 85 g"),
    "Still missing – e.g. Gas canister": ("Fehlt noch – z. B. Gaskartusche", "Manque encore – p. ex. Cartouche de gaz", "Manca ancora – p. es. Cartuccia di gas",
                                          "Manca anc – p.ex. Cartuscha da gas"),
    "Sleeping": ("Schlafen", "Dormir", "Dormire", "Durmir"),
    "Clothes": ("Kleider", "Vêtements", "Vestiti", "Vestgadira"),
    "Kitchen": ("Küche", "Cuisine", "Cucina", "Cuschina"),
    "Food": ("Essen", "Nourriture", "Cibo", "Mangiar"),
    "Water": ("Wasser", "Eau", "Acqua", "Aua"),
    "Hygiene": ("Hygiene", "Hygiène", "Igiene", "Igiena"),
    "First aid": ("Erste Hilfe", "Premiers secours", "Pronto soccorso", "Emprim agid"),
    "Tools & repair": ("Werkzeug", "Outils", "Attrezzi", "Utensils"),
    "Electronics": ("Elektronik", "Électronique", "Elettronica", "Electronica"),
    "Navigation": ("Navigation", "Navigation", "Navigazione", "Navigaziun"),
    "Documents & money": ("Dokumente", "Documents", "Documenti", "Documents"),
    "Miscellaneous": ("Sonstiges", "Divers", "Varie", "Divers"),
    "Base weight": ("Basisgewicht", "Poids de base", "Peso base", "Paisa da basa"),
    "Consumable": ("Verbrauch", "Consommable", "Consumabile", "Consum"),
    "Worn": ("Am Körper", "Porté", "Indossato", "Vi dal corp"),
    "Rucksack": ("Rucksack", "Sac à dos", "Zaino", "Satgados"),
    "Category": ("Kategorie", "Catégorie", "Categoria", "Categoria"),
    "Quantity": ("Anzahl", "Quantité", "Quantità", "Quantitad"),
    "Weight (g)": ("Gewicht (g)", "Poids (g)", "Peso (g)", "Paisa (g)"),
    "Kind": ("Art", "Type", "Tipo", "Tip"),
    "Remark": ("Notiz", "Remarque", "Nota", "Remartga"),
    "Packed": ("Gepackt", "Emballé", "Preparato", "Pachetà"),
    "Bought": ("Gekauft", "Acheté", "Comprato", "Cumprà"),
    "Still missing / to buy": ("Fehlt noch / kaufen", "Manque encore / à acheter", "Manca ancora / da comprare", "Manca anc / da cumprar"),
    "Goal {n}": ("Ziel {n}", "Objectif {n}", "Obiettivo {n}", "Finamira {n}"),
    "{n} over": ("{n} darüber", "{n} de trop", "{n} in più", "{n} da memia"),
    "{n} under": ("{n} darunter", "{n} en dessous", "{n} in meno", "{n} sutvart"),
    "{a} of {b} packed": ("{a} von {b} gepackt", "{a} sur {b} emballés", "{a} di {b} preparati", "{a} da {b} pachetads"),
    "{n} without a weight": ("{n} ohne Gewicht", "{n} sans poids", "{n} senza peso", "{n} senza paisa"),
    "{n} each": ("je {n}", "{n} pièce", "{n} cad.", "{n} per toc"),
    "changed by {who} {n} s ago": ("geändert von {who} vor {n} s", "modifié par {who} il y a {n} s", "modificato da {who} {n} s fa", "midà da {who} avant {n} s"),
    "changed by {who} {n} min ago": ("geändert von {who} vor {n} Min.", "modifié par {who} il y a {n} min", "modificato da {who} {n} min fa", "midà da {who} avant {n} min"),
    "No packing lists yet.": ("Noch keine Packlisten.", "Pas encore de listes.", "Ancora nessuna lista.", "Anc naginas glistas."),
    "Start with «New list» (also from a template) or import a list you already have.": (
        "Beginne mit «Neue Liste» (auch aus einer Vorlage) oder importiere eine Liste, die du schon hast.",
        "Commence avec «Nouvelle liste» (aussi depuis un modèle) ou importe une liste que tu as déjà.",
        "Inizia con «Nuova lista» (anche da un modello) o importa una lista che hai già.",
        "Cumenza cun «Nova glista» (er or d’in model) u importa ina glista che ti has gia."),
    "This list is still empty.": ("Diese Liste ist noch leer.", "Cette liste est encore vide.", "Questa lista è ancora vuota.", "Questa glista è anc vida."),
    "Add the first item below or import a list.": ("Füge unten den ersten Gegenstand hinzu oder importiere eine Liste.", "Ajoute le premier objet en bas ou importe une liste.",
                                                   "Aggiungi il primo oggetto qui sotto o importa una lista.", "Agiunta sutvart l’emprim object u importa ina glista."),
    "Nothing is missing.": ("Es fehlt nichts.", "Il ne manque rien.", "Non manca niente.", "I na manca nagut."),
    "Mark an item with 🛒 or add what is missing below.": ("Markiere einen Gegenstand mit 🛒 oder trage unten ein, was fehlt.", "Marque un objet avec 🛒 ou ajoute en bas ce qui manque.",
                                                          "Segna un oggetto con 🛒 o aggiungi sotto ciò che manca.", "Marca in object cun 🛒 u agiunta sutvart quai che manca."),
    "You may look at the packing lists, but not change them.": (
        "Du darfst die Packlisten ansehen, aber nicht ändern.", "Tu peux regarder les listes, mais pas les modifier.",
        "Puoi guardare le liste, ma non modificarle.", "Ti dastgas guardar las glistas, ma betg midar ellas."),
    "Empty list": ("Leere Liste", "Liste vide", "Lista vuota", "Glista vida"),
    "Template «{name}» ({n} items)": ("Vorlage «{name}» ({n} Sachen)", "Modèle «{name}» ({n} objets)", "Modello «{name}» ({n} oggetti)", "Model «{name}» ({n} objects)"),
    "Only for me (private)": ("Nur für mich (privat)", "Seulement pour moi (privé)", "Solo per me (privato)", "Mo per mai (privat)"),
    "Name of the list": ("Name der Liste", "Nom de la liste", "Nome della lista", "Num da la glista"),
    "Name of the new list": ("Name der neuen Liste", "Nom de la nouvelle liste", "Nome della nuova lista", "Num da la nova glista"),
    "Name of the copy": ("Name der Kopie", "Nom de la copie", "Nome della copia", "Num da la copia"),
    "Name of the own category": ("Name der eigenen Kategorie", "Nom de ta catégorie", "Nome della tua categoria", "Num da l’atgna categoria"),
    "Own category …": ("Eigene Kategorie …", "Ma catégorie …", "Categoria propria …", "Atgna categoria …"),
    "Category: automatic": ("Kategorie: automatisch", "Catégorie : automatique", "Categoria: automatica", "Categoria: automatic"),
    "Start from": ("Beginnen mit", "Commencer avec", "Inizia da", "Cumenzar cun"),
    "Weight goal for the rucksack (optional)": ("Gewichtsziel für den Rucksack (freiwillig)", "Objectif de poids pour le sac (facultatif)",
                                                "Obiettivo di peso per lo zaino (facoltativo)", "Finamira da paisa per il satgados (facultativ)"),
    "The goal counts base weight and consumables - not what you wear.": (
        "Das Ziel zählt Basisgewicht und Verbrauch – nicht, was du am Körper trägst.", "L’objectif compte le poids de base et les consommables – pas ce que tu portes sur toi.",
        "L’obiettivo conta peso base e consumabili – non ciò che indossi.", "La finamira dumbra paisa da basa e consum – betg quai che ti portas vi dal corp."),
    "e.g. 8 kg": ("z. B. 8 kg", "p. ex. 8 kg", "p. es. 8 kg", "p.ex. 8 kg"),
    "e.g. 350 g or 1.2 kg": ("z. B. 350 g oder 1,2 kg", "p. ex. 350 g ou 1,2 kg", "p. es. 350 g o 1,2 kg", "p.ex. 350 g u 1,2 kg"),
    "e.g. Weekend in the Jura": ("z. B. Wochenende im Jura", "p. ex. Week-end dans le Jura", "p. es. Fine settimana nel Giura", "p.ex. Fin d’emna en il Giura"),
    "Create": ("Anlegen", "Créer", "Crea", "Crear"),
    "Weight per piece": ("Gewicht pro Stück", "Poids par pièce", "Peso per pezzo", "Paisa per toc"),
    "Counts as": ("Zählt als", "Compte comme", "Conta come", "Dumbra sco"),
    "Take or choose a photo": ("Foto aufnehmen oder wählen", "Prendre ou choisir une photo", "Scatta o scegli una foto", "Far u tscherner ina foto"),
    "Change the photo": ("Foto ändern", "Changer la photo", "Cambia la foto", "Midar la foto"),
    "Remove the photo": ("Foto entfernen", "Retirer la photo", "Rimuovi la foto", "Allontanar la foto"),
    "Show the photo": ("Foto zeigen", "Afficher la photo", "Mostra la foto", "Mussar la foto"),
    "Preparing the photo": ("Foto wird vorbereitet", "Préparation de la photo", "Preparazione della foto", "La foto vegn preparada"),
    "Delete this item?": ("Diesen Gegenstand löschen?", "Supprimer cet objet ?", "Eliminare questo oggetto?", "Stizzar quest object?"),
    "Name, weight goal, note": ("Name, Gewichtsziel, Notiz", "Nom, objectif de poids, remarque", "Nome, obiettivo di peso, nota", "Num, finamira da paisa, remartga"),
    "Import into this list": ("In diese Liste importieren", "Importer dans cette liste", "Importa in questa lista", "Importar en questa glista"),
    "Reset all ticks (next trip)": ("Alle Häkchen zurücksetzen (nächste Tour)", "Enlever toutes les coches (prochaine sortie)", "Togli tutte le spunte (prossima gita)",
                                    "Allontanar tut ils crutschs (proxima tura)"),
    "Remove all ticks of this list?": ("Alle Häkchen dieser Liste entfernen?", "Enlever toutes les coches de cette liste ?", "Togliere tutte le spunte di questa lista?",
                                       "Allontanar tut ils crutschs da questa glista?"),
    "{n} ticks removed": ("{n} Häkchen entfernt", "{n} coches enlevées", "{n} spunte tolte", "{n} crutschs allontanads"),
    "Copy this list": ("Liste kopieren", "Copier cette liste", "Copia questa lista", "Copiar questa glista"),
    "{name} (copy)": ("{name} (Kopie)", "{name} (copie)", "{name} (copia)", "{name} (copia)"),
    "table for Excel / Numbers": ("Tabelle für Excel / Numbers", "tableau pour Excel / Numbers", "tabella per Excel / Numbers", "tabella per Excel / Numbers"),
    "the list as MoveEye stores it": ("die Liste, wie MoveEye sie speichert", "la liste telle que MoveEye l’enregistre", "la lista come la salva MoveEye",
                                      "la glista sco che MoveEye la memorisescha"),
    "list and photos, as a backup": ("Liste und Fotos, als Sicherung", "liste et photos, comme sauvegarde", "lista e foto, come backup", "glista e fotos, sco copia da segirezza"),
    "Delete this list": ("Liste löschen", "Supprimer cette liste", "Elimina questa lista", "Stizzar questa glista"),
    "Delete this list with all its photos? It cannot be undone.": (
        "Diese Liste mit allen Fotos löschen? Das lässt sich nicht rückgängig machen.", "Supprimer cette liste avec toutes ses photos ? C’est définitif.",
        "Eliminare questa lista con tutte le foto? Non si può annullare.", "Stizzar questa glista cun tut las fotos? Quai na sa lascha betg revocar."),
    "This list was deleted.": ("Diese Liste wurde gelöscht.", "Cette liste a été supprimée.", "Questa lista è stata eliminata.", "Questa glista è vegnida stizzada."),
    "Back to the list": ("Zurück zur Liste", "Retour à la liste", "Torna alla lista", "Enavos a la glista"),
    "Choose a file": ("Datei wählen", "Choisir un fichier", "Scegli un file", "Tscherner ina datoteca"),
    "Paste the text here – one item per line. Example:": ("Text hier einfügen – ein Gegenstand pro Zeile. Beispiel:", "Colle le texte ici – un objet par ligne. Exemple :",
                                                          "Incolla qui il testo – un oggetto per riga. Esempio:", "Encollar qua il text – in object per lingia. Exempel:"),
    "… or paste text (e.g. from the Notes app)": ("… oder Text einfügen (z. B. aus der Notizen-App)", "… ou coller du texte (p. ex. depuis Notes)",
                                                 "… o incolla del testo (p. es. dall’app Note)", "… u encollar text (p.ex. da l’app Notizias)"),
    "Text file (one item per line), Excel (.xlsx) or CSV. You always see a preview first and can correct everything.": (
        "Textdatei (ein Gegenstand pro Zeile), Excel (.xlsx) oder CSV. Du siehst immer zuerst eine Vorschau und kannst alles korrigieren.",
        "Fichier texte (un objet par ligne), Excel (.xlsx) ou CSV. Tu vois toujours d’abord un aperçu et tu peux tout corriger.",
        "File di testo (un oggetto per riga), Excel (.xlsx) o CSV. Vedi sempre prima un’anteprima e puoi correggere tutto.",
        "Datoteca da text (in object per lingia), Excel (.xlsx) u CSV. Ti vesas adina l’emprim ina prevista e pos curreger tut."),
    "Reading": ("Wird gelesen", "Lecture", "Lettura", "Vegn legì"),
    "Add to «{name}»": ("An «{name}» anhängen", "Ajouter à «{name}»", "Aggiungi a «{name}»", "Agiuntar a «{name}»"),
    "Make a new list from it": ("Neue Liste daraus machen", "En faire une nouvelle liste", "Farne una nuova lista", "Far ina nova glista londeror"),
    "Which column is what? MoveEye guessed - please check.": ("Welche Spalte ist was? MoveEye hat geraten – bitte prüfen.", "Quelle colonne est quoi ? MoveEye a deviné – vérifie.",
                                                              "Quale colonna è cosa? MoveEye ha indovinato – controlla.", "Tge colonna è tge? MoveEye ha engiavinà – controllescha p.pl."),
    "Numbers without a unit are": ("Zahlen ohne Einheit sind", "Les nombres sans unité sont", "I numeri senza unità sono", "Cifras senza unitad èn"),
    "grams (g)": ("Gramm (g)", "grammes (g)", "grammi (g)", "grams (g)"),
    "kilograms (kg)": ("Kilogramm (kg)", "kilogrammes (kg)", "chilogrammi (kg)", "kilograms (kg)"),
    "The first row is the heading": ("Die erste Zeile sind Überschriften", "La première ligne contient les titres", "La prima riga contiene i titoli", "L’emprima lingia èn ils titels"),
    "{n} items": ("{n} Sachen", "{n} objets", "{n} oggetti", "{n} objects"),
    "{n} doubles": ("{n} doppelt", "{n} doublons", "{n} doppi", "{n} dubels"),
    "{n} lines not understood": ("{n} Zeilen nicht verstanden", "{n} lignes non comprises", "{n} righe non capite", "{n} lingias betg chapidas"),
    "only {n} more fit into this list": ("nur noch {n} haben in dieser Liste Platz", "seulement {n} de plus entrent dans cette liste", "solo altri {n} entrano in questa lista",
                                         "mo anc {n} han plaz en questa glista"),
    "Import {n} items": ("{n} Sachen importieren", "Importer {n} objets", "Importa {n} oggetti", "Importar {n} objects"),
    "{n} items imported": ("{n} Sachen importiert", "{n} objets importés", "{n} oggetti importati", "{n} objects importads"),
    "Double: already in the list": ("Doppelt: schon in der Liste", "Doublon : déjà dans la liste", "Doppio: già nella lista", "Dubel: gia en la glista"),
    "Double: twice in this import": ("Doppelt: zweimal in diesem Import", "Doublon : deux fois dans cet import", "Doppio: due volte in questa importazione",
                                     "Dubel: duas giadas en quest import"),
    "«{name}» is in the list twice now": ("«{name}» steht jetzt zweimal in der Liste", "«{name}» est maintenant deux fois dans la liste", "«{name}» ora è due volte nella lista",
                                          "«{name}» stat ussa duas giadas en la glista"),
    "Similar to «{name}» in the list": ("Ähnlich wie «{name}» in der Liste", "Semblable à «{name}» dans la liste", "Simile a «{name}» nella lista", "Sumegliant a «{name}» en la glista"),
    "As category": ("Als Kategorie", "Comme catégorie", "Come categoria", "Sco categoria"),
    "As item": ("Als Gegenstand", "Comme objet", "Come oggetto", "Sco object"),
    "unknown list": ("unbekannte Liste", "liste inconnue", "lista sconosciuta", "glista nunenconuschenta"),
    "The list needs a name.": ("Die Liste braucht einen Namen.", "La liste a besoin d’un nom.", "La lista ha bisogno di un nome.", "La glista dovra in num."),
    "The item needs a name.": ("Der Gegenstand braucht einen Namen.", "L’objet a besoin d’un nom.", "L’oggetto ha bisogno di un nome.", "L’object dovra in num."),
    "This item does not exist (any more).": ("Diesen Gegenstand gibt es nicht (mehr).", "Cet objet n’existe pas (plus).", "Questo oggetto non esiste (più).", "Quest object n’exista betg (pli)."),
    "At most {n} items per list.": ("Höchstens {n} Gegenstände pro Liste.", "Au plus {n} objets par liste.", "Al massimo {n} oggetti per lista.", "Maximalmain {n} objects per glista."),
    "At most {n} packing lists - delete an old one first.": ("Höchstens {n} Packlisten – lösche zuerst eine alte.", "Au plus {n} listes – supprime d’abord une ancienne.",
                                                             "Al massimo {n} liste – elimina prima una vecchia.", "Maximalmain {n} glistas – stizza l’emprim ina veglia."),
    "Only the person who created this list (or the administrator) may delete it.": (
        "Nur wer die Liste angelegt hat (oder der Administrator), darf sie löschen.", "Seule la personne qui a créé la liste (ou l’administrateur) peut la supprimer.",
        "Solo chi ha creato la lista (o l’amministratore) può eliminarla.", "Mo tgi che ha creà la glista (u l’administratur) dastga stizzar ella."),
    "This weight is not understood. Examples: 350 g, 1.2 kg, 0,5 kg.": ("Dieses Gewicht verstehe ich nicht. Beispiele: 350 g, 1.2 kg, 0,5 kg.",
                                                                        "Ce poids n’est pas compris. Exemples : 350 g, 1.2 kg, 0,5 kg.",
                                                                        "Questo peso non è chiaro. Esempi: 350 g, 1.2 kg, 0,5 kg.", "Questa paisa na vegn betg chapida. Exempels: 350 g, 1.2 kg, 0,5 kg."),
    "Nothing to import was found.": ("Nichts zum Importieren gefunden.", "Rien à importer.", "Niente da importare.", "Chattà nagut per importar."),
    "The file is too big.": ("Die Datei ist zu gross.", "Le fichier est trop grand.", "Il file è troppo grande.", "La datoteca è memia gronda."),
    "The text is too long.": ("Der Text ist zu lang.", "Le texte est trop long.", "Il testo è troppo lungo.", "Il text è memia lung."),
    "The storage is full.": ("Der Speicher ist voll.", "Le stockage est plein.", "La memoria è piena.", "La memoria è plaina."),
    "This file could not be read.": ("Diese Datei konnte nicht gelesen werden.", "Ce fichier n’a pas pu être lu.", "Impossibile leggere questo file.", "Questa datoteca n’ha betg pudì vegnir legida."),
    "This table could not be read.": ("Diese Tabelle konnte nicht gelesen werden.", "Ce tableau n’a pas pu être lu.", "Impossibile leggere questa tabella.", "Questa tabella n’ha betg pudì vegnir legida."),
    "This Excel file could not be read.": ("Diese Excel-Datei konnte nicht gelesen werden.", "Ce fichier Excel n’a pas pu être lu.", "Impossibile leggere questo file Excel.",
                                           "Questa datoteca Excel n’ha betg pudì vegnir legida."),
    "This Excel file has no table.": ("Diese Excel-Datei hat keine Tabelle.", "Ce fichier Excel n’a pas de tableau.", "Questo file Excel non ha una tabella.", "Questa datoteca Excel n’ha nagina tabella."),
    "This Excel file is not accepted (too big when unpacked).": ("Diese Excel-Datei wird nicht angenommen (entpackt zu gross).", "Ce fichier Excel est refusé (trop grand une fois décompressé).",
                                                                "Questo file Excel non è accettato (troppo grande una volta estratto).", "Questa datoteca Excel na vegn betg acceptada (memia gronda extratga)."),
    "This Excel file is not accepted (unusual content).": ("Diese Excel-Datei wird nicht angenommen (ungewöhnlicher Inhalt).", "Ce fichier Excel est refusé (contenu inhabituel).",
                                                          "Questo file Excel non è accettato (contenuto insolito).", "Questa datoteca Excel na vegn betg acceptada (cuntegn nunusità)."),
    "This JSON file is not a packing list of MoveEye.": ("Diese JSON-Datei ist keine Packliste von MoveEye.", "Ce fichier JSON n’est pas une liste de MoveEye.",
                                                        "Questo file JSON non è una lista di MoveEye.", "Questa datoteca JSON n’è betg ina glista da MoveEye."),
    "This kind of file cannot be imported. Save the list as .xlsx, CSV or text.": (
        "Diese Art Datei kann nicht importiert werden. Speichere die Liste als .xlsx, CSV oder Text.", "Ce type de fichier ne peut pas être importé. Enregistre la liste en .xlsx, CSV ou texte.",
        "Questo tipo di file non può essere importato. Salva la lista come .xlsx, CSV o testo.", "Questa sort datoteca na po betg vegnir importada. Memorisescha la glista sco .xlsx, CSV u text."),
    "Old Excel files (.xls) cannot be read. Save the table as .xlsx or CSV.": (
        "Alte Excel-Dateien (.xls) können nicht gelesen werden. Speichere die Tabelle als .xlsx oder CSV.", "Les anciens fichiers Excel (.xls) ne peuvent pas être lus. Enregistre le tableau en .xlsx ou CSV.",
        "I vecchi file Excel (.xls) non possono essere letti. Salva la tabella come .xlsx o CSV.", "Veglias datotecas Excel (.xls) na pon betg vegnir legidas. Memorisescha la tabella sco .xlsx u CSV."),
    "Please choose a photo (JPEG, PNG or WebP).": ("Bitte ein Foto wählen (JPEG, PNG oder WebP).", "Choisis une photo (JPEG, PNG ou WebP).", "Scegli una foto (JPEG, PNG o WebP).",
                                                   "Tscherna p.pl. ina foto (JPEG, PNG u WebP)."),
    "This picture could not be read. Please choose a photo (JPEG, PNG or WebP).": (
        "Dieses Bild konnte nicht gelesen werden. Bitte ein Foto wählen (JPEG, PNG oder WebP).", "Cette image n’a pas pu être lue. Choisis une photo (JPEG, PNG ou WebP).",
        "Impossibile leggere questa immagine. Scegli una foto (JPEG, PNG o WebP).", "Quest maletg n’ha betg pudì vegnir legì. Tscherna p.pl. ina foto (JPEG, PNG u WebP)."),
    PL_HEIC_MSG: ("Dieses Foto ist HEIC – dieses Format kann MoveEye nicht lesen. Wähle es aus der Fotomediathek (Safari schickt dann JPEG) oder stelle die Kamera auf «Maximale Kompatibilität».",
                  "Cette photo est en HEIC – MoveEye ne lit pas ce format. Choisis-la dans la photothèque (Safari envoie alors du JPEG) ou règle l’appareil photo sur «Le plus compatible».",
                  "Questa foto è HEIC – MoveEye non legge questo formato. Sceglila dalla libreria foto (Safari invia allora JPEG) o imposta la fotocamera su «Più compatibile».",
                  "Questa foto è HEIC – quest format na po MoveEye betg leger. Tscherna ella or da la fototeca (Safari trametta lura JPEG) u metta la camera sin «Maximala cumpatibilitad»."),
    "The space for photos of the packing lists is full - remove some photos first.": (
        "Der Platz für Fotos der Packlisten ist voll – entferne zuerst einige Fotos.", "L’espace pour les photos des listes est plein – retire d’abord quelques photos.",
        "Lo spazio per le foto delle liste è pieno – rimuovi prima alcune foto.", "Il plaz per fotos da las glistas è plain – allontanescha l’emprim intginas fotos."),
    "Weights are typical values - weigh your own things.": ("Die Gewichte sind Richtwerte – wiege deine eigenen Sachen.", "Les poids sont indicatifs – pèse tes propres affaires.",
                                                            "I pesi sono indicativi – pesa le tue cose.", "Las paisas èn valurs approximativas – paisa tias atgnas chaussas."),
    "Only to look at - changing the lists needs a login.": ("Nur zum Ansehen – zum Ändern der Listen braucht es eine Anmeldung.", "Seulement pour regarder – modifier les listes demande une connexion.",
                                                            "Solo da guardare – per modificare le liste serve un accesso.", "Mo per guardar – per midar las glistas dovri in’annunzia."),
}
for _k, _v in _HX_PACK.items():
    DE.setdefault(_k, _v[0])
    for _i, _L in enumerate(("fr", "it", "rm")):
        TRX[_L].setdefault(_k, _v[_i + 1])
MORE_DE.update({"Packing lists": "Packlisten"})
# the German of every text of the page (also the ones other parts already translate: «Save», «Cancel» …)
_PL_DE = {_k: DE[_k] for _k in set(re.findall(r'\bt[f]?\(\s*"((?:[^"\\]|\\.)+)"', PL_PAGE)) | set(re.findall(r'data-i18n(?:-ph)?="([^"]+)"', PL_PAGE))
          | {"Change the photo", "Take or choose a photo", "Consumable", "Worn", "Double: already in the list", "Double: twice in this import"}
          | {_c[1] for _c in PL_CATS} if _k in DE}

# ---- the manual (5 languages) ------------------------------------------------------------------------------------------------------
_HELP_PL = {
    "de": ('<section id="packlisten" data-icon="🎒"><h2>Packlisten</h2><p>Unter <i>Mehr → 📁 Datentausch → 🎒 Packlisten</i> (oder direkt <code>/tausch/packlisten</code>) '
           'führst du Packlisten mit Gewicht, Anzahl, Kategorie, Foto und Häkchen.</p><ul>'
           '<li><b>Schnell eintragen:</b> unten «Name, Gewicht» tippen, z. B. <code>Stirnlampe 85 g</code>, <code>2x Socken 80 g</code>, <code>Zelt (1.8 kg)</code>. Das Gewicht gilt pro Stück.</li>'
           '<li><b>Importieren:</b> Textdatei (ein Gegenstand pro Zeile), Excel (.xlsx), CSV oder Text aus der Notizen-App einfügen. Du siehst immer zuerst eine Vorschau: Spalten zuordnen, Zeilen ändern oder abwählen; Doppeltes ist markiert. Zeilen, die mit «:» enden oder gross geschrieben sind, werden Kategorien.</li>'
           '<li><b>Gewicht:</b> oben stehen Rucksack (Basisgewicht + Verbrauch wie Essen, Wasser, Gas) und «am Körper». Mit einem <b>Gewichtsziel</b> zeigt der Balken, wie viel du darüber oder darunter bist.</li>'
           '<li><b>🛒 Kaufen:</b> markiere, was noch fehlt – der Reiter «Kaufen» ist deine Einkaufsliste.</li>'
           '<li><b>Gemeinsam packen:</b> alle öffnen dieselbe Liste und haken auf ihrem Handy ab; der Stand erscheint bei allen nach wenigen Sekunden («geändert von …»).</li>'
           '<li><b>Foto:</b> ✎ → «Foto aufnehmen oder wählen». Ohne Foto zeigt MoveEye das Symbol der Kategorie.</li>'
           '<li><b>Mehr (⋯):</b> Vorlagen (Tagestour, Zeltnacht, Winter), Liste kopieren, alle Häkchen zurücksetzen, drucken, Export als CSV, JSON oder ZIP mit Fotos.</li>'
           '<li><b>Rechte</b> wie der Datentausch: «Dateien: ansehen» sieht die Listen, «Dateien: hochladen» ändert sie; Gäste mit dem Gast-Link sehen gemeinsame Listen nur an. '
           'Die Listen liegen beim Datentausch (Ordner <code>tausch/pack</code>) und sind wie er in keiner Sicherung – nutze den ZIP-Export.</li></ul></section>\n'),
    "en": ('<section id="packlisten" data-icon="🎒"><h2>Packing lists</h2><p>Under <i>More → 📁 File exchange → 🎒 Packing lists</i> (or directly <code>/tausch/packlisten</code>) '
           'you keep packing lists with weight, quantity, category, photo and ticks.</p><ul>'
           '<li><b>Quick add:</b> type «name, weight» at the bottom, e.g. <code>Headlamp 85 g</code>, <code>2x Socks 80 g</code>, <code>Tent (1.8 kg)</code>. The weight is per piece.</li>'
           '<li><b>Import:</b> a text file (one item per line), Excel (.xlsx), CSV, or paste text from a notes app. You always see a preview first: choose the columns, change or untick rows; doubles are marked. Lines ending with «:» or written in capitals become categories.</li>'
           '<li><b>Weight:</b> the top shows the rucksack (base weight + consumables like food, water, gas) and what you wear. With a <b>weight goal</b> the bar shows how far you are over or under.</li>'
           '<li><b>🛒 To buy:</b> mark what is still missing – the tab «To buy» is your shopping list.</li>'
           '<li><b>Packing together:</b> everybody opens the same list and ticks on their own phone; all see the state within a few seconds («changed by …»).</li>'
           '<li><b>Photo:</b> ✎ → «Take or choose a photo». Without a photo MoveEye shows the symbol of the category.</li>'
           '<li><b>More (⋯):</b> templates (day hike, night in the tent, winter), copy a list, reset all ticks, print, export as CSV, JSON or ZIP with photos.</li>'
           '<li><b>Rights</b> as in the file exchange: «Files: see» sees the lists, «Files: upload» changes them; guests with the guest link only look at shared lists. '
           'The lists are stored with the file exchange (folder <code>tausch/pack</code>) and, like it, are in no backup – use the ZIP export.</li></ul></section>\n'),
    "fr": ('<section id="packlisten" data-icon="🎒"><h2>Listes de bagages</h2><p>Sous <i>Plus → 📁 Échange de fichiers → 🎒 Listes de bagages</i> (ou <code>/tausch/packlisten</code>) '
           'tu gères des listes avec poids, quantité, catégorie, photo et coches.</p><ul>'
           '<li><b>Ajout rapide :</b> en bas «nom, poids», p. ex. <code>Lampe frontale 85 g</code>, <code>2x Chaussettes 80 g</code>. Le poids vaut par pièce.</li>'
           '<li><b>Importer :</b> fichier texte (un objet par ligne), Excel (.xlsx), CSV ou texte collé. Toujours d’abord un aperçu : colonnes, lignes, doublons marqués.</li>'
           '<li><b>Poids :</b> sac à dos (poids de base + consommables) et «porté» ; avec un <b>objectif</b>, la barre montre l’écart.</li>'
           '<li><b>🛒 À acheter :</b> marque ce qui manque – l’onglet est ta liste de courses.</li>'
           '<li><b>Ensemble :</b> chacun coche sur son téléphone, tous voient l’état après quelques secondes.</li>'
           '<li><b>Plus (⋯) :</b> modèles, copier, enlever les coches, imprimer, export CSV / JSON / ZIP avec photos.</li>'
           '<li><b>Droits</b> comme l’échange de fichiers : «voir» regarde, «envoyer» modifie ; les invités regardent seulement. Dans aucune sauvegarde – utilise l’export ZIP.</li></ul></section>\n'),
    "it": ('<section id="packlisten" data-icon="🎒"><h2>Liste di cose da portare</h2><p>In <i>Altro → 📁 Scambio di file → 🎒 Liste</i> (o <code>/tausch/packlisten</code>) '
           'tieni liste con peso, quantità, categoria, foto e spunte.</p><ul>'
           '<li><b>Aggiunta rapida:</b> in basso «nome, peso», p. es. <code>Lampada frontale 85 g</code>, <code>2x Calze 80 g</code>. Il peso vale per pezzo.</li>'
           '<li><b>Importare:</b> file di testo (un oggetto per riga), Excel (.xlsx), CSV o testo incollato. Sempre prima un’anteprima: colonne, righe, doppi segnati.</li>'
           '<li><b>Peso:</b> zaino (peso base + consumabili) e «indossato»; con un <b>obiettivo</b> la barra mostra lo scarto.</li>'
           '<li><b>🛒 Da comprare:</b> segna ciò che manca – la scheda è la tua lista della spesa.</li>'
           '<li><b>Insieme:</b> ognuno spunta sul proprio telefono, tutti vedono lo stato dopo pochi secondi.</li>'
           '<li><b>Altro (⋯):</b> modelli, copiare, togliere le spunte, stampare, export CSV / JSON / ZIP con foto.</li>'
           '<li><b>Diritti</b> come lo scambio di file: «vedere» guarda, «caricare» modifica; gli ospiti guardano soltanto. In nessun backup – usa l’export ZIP.</li></ul></section>\n'),
    "rm": ('<section id="packlisten" data-icon="🎒"><h2>Glistas da pachetar</h2><p>Sut <i>Dapli → 📁 Barat da datotecas → 🎒 Glistas da pachetar</i> (u <code>/tausch/packlisten</code>) '
           'has ti glistas cun paisa, quantitad, categoria, foto e crutschs.</p><ul>'
           '<li><b>Agiuntar svelt:</b> giusut «num, paisa», p.ex. <code>Lampa frontala 85 g</code>, <code>2x Chaltschiels 80 g</code>. La paisa vala per toc.</li>'
           '<li><b>Importar:</b> datoteca da text (in object per lingia), Excel (.xlsx), CSV u text encollà. Adina l’emprim ina prevista: colonnas, lingias, dubels marcads.</li>'
           '<li><b>Paisa:</b> satgados (paisa da basa + consum) e «vi dal corp»; cun ina <b>finamira</b> mussa la trav la differenza.</li>'
           '<li><b>🛒 Da cumprar:</b> marca quai che manca – il register è tia glista da cumpras.</li>'
           '<li><b>Ensemen:</b> mintgin marca sin ses telefonin, tuts vesan il stadi suenter paucas secundas.</li>'
           '<li><b>Dapli (⋯):</b> models, copiar, allontanar ils crutschs, stampar, export CSV / JSON / ZIP cun fotos.</li>'
           '<li><b>Dretgs</b> sco il barat da datotecas: «guardar» vesa, «chargiar si» mida; giasts guardan mo. En nagina copia da segirezza – dovra l’export ZIP.</li></ul></section>\n'),
}


def _help_pl(doc, lang):
    if 'id="packlisten"' in doc:
        return doc
    i = doc.find('<section id="tips"')
    return doc[:i] + _HELP_PL[lang] + doc[i:] if i >= 0 else doc


_hp_en_pl = HELP_PAGE.find('<div lang="en">')
if _hp_en_pl > 0:
    HELP_PAGE = _help_pl(HELP_PAGE[:_hp_en_pl], "de") + _help_pl(HELP_PAGE[_hp_en_pl:], "en")
for _L in ("fr", "it", "rm"):
    if HELP_X.get(_L):
        HELP_X[_L] = _help_pl(HELP_X[_L], _L)


# ---- self-test (without a server; werkzeuge/packlisten_test.py tests the web side) ------------------------------------------------
def _pl_test_xlsx(rows, extra=None, doctype="", sst=None):
    """a small real .xlsx (shared strings, numbers, one formula with its stored value) - also used by the test tool"""
    import zipfile as _zf
    from xml.sax.saxutils import escape as _x
    strs, cells = [], []
    for r, row in enumerate(rows, 1):
        cs = []
        for c, v in enumerate(row):
            ref = chr(65 + c) + str(r)
            if v is None or v == "":
                continue
            if isinstance(v, tuple):                         # ("=A1*2", 42): a formula and the value Excel stored
                cs.append(f'<c r="{ref}"><f>{_x(v[0][1:])}</f><v>{v[1]}</v></c>')
            elif isinstance(v, (int, float)):
                cs.append(f'<c r="{ref}"><v>{v}</v></c>')
            else:
                if v not in strs:
                    strs.append(v)
                cs.append(f'<c r="{ref}" t="s"><v>{strs.index(v)}</v></c>')
        cells.append(f'<row r="{r}">' + "".join(cs) + "</row>")
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    buf = _pl_io.BytesIO()
    with _zf.ZipFile(buf, "w", _zf.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr("xl/workbook.xml", f'<?xml version="1.0"?><workbook {ns} xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                                      '<sheets><sheet name="Liste" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                                                 '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/sharedStrings.xml", sst if sst is not None else                          # sst: these bytes instead (tests of the encoding)
                   f'<?xml version="1.0"?>{doctype}<sst {ns}>' + "".join(f"<si><t>{_x(s)}</t></si>" for s in strs) + "</sst>")
        z.writestr("xl/worksheets/sheet1.xml", f'<?xml version="1.0"?><worksheet {ns}><sheetData>' + "".join(cells) + "</sheetData></worksheet>")
        for nm, data in (extra or {}).items():
            z.writestr(nm, data)
    return buf.getvalue()


def pl_selftest():
    keep = {k: CFG.get(k) for k in ("tausch_on", "lang", "tausch_free_gb", "tausch_total_gb", "tausch_file_mb", "tausch_user_gb")}
    keepTZ = {k: TZ.get(k) for k in ("root", "files", "folders", "ups", "rate", "root_test", "chats")}
    keepPL = {k: PL.get(k) for k in ("root", "lists", "photo_bytes")}
    g = globals()
    sv = {k: g[k] for k in ("tausch_disk_free", "log_event", "tausch_thumb_queue")}
    tmp = tempfile.mkdtemp(prefix="mw_pl_")
    try:
        g["log_event"] = lambda *a, **k: None
        g["tausch_thumb_queue"] = lambda fid: None
        g["tausch_disk_free"] = lambda p: 50 * TZ_GB
        CFG.update(tausch_on=True, lang="de", tausch_free_gb=2.0, tausch_total_gb=5.0, tausch_file_mb=200.0, tausch_user_gb=1.0)
        TZ.update(root=None, files=None, folders=None, ups={}, rate={}, root_test=tmp, chats={})
        PL.update(root=None, lists=None, photo_bytes=0)
        # weights and lines
        for txt, want in (("350 g", 350), ("1.2 kg", 1200), ("0,5kg", 500), ("1'200 g", 1200), ("1.200 g", 1200), ("2 KG", 2000), ("85", 85), ("12 oz", 340),
                          ("ca. 90 Gramm", 90), ("", None), ("viel", None), ("1,25 kg", 1250)):
            assert pl_weight(txt) == want, (txt, pl_weight(txt))
        assert pl_weight("1,5", "kg") == 1500 and pl_fmt_g(1250, "de") == "1,25 kg" and pl_fmt_g(350, "de") == "350 g" and pl_fmt_g(1200, "en") == "1.2 kg"
        L = lambda s: pl_parse_line(s)
        assert L("- [x] Zelt (1.8 kg)") == ("item", {"name": "Zelt", "g": 1800, "n": 1, "note": "", "packed": True, "buy": False})
        assert L("2x Socken – 80 g")[1] == {"name": "Socken", "g": 80, "n": 2, "note": "", "packed": False, "buy": False}
        assert L("3. Stirnlampe\t85")[1]["g"] == 85 and L("• Wasser 1,5 l")[1] == {"name": "Wasser", "g": None, "n": 1, "note": "1,5 l", "packed": False, "buy": False}
        assert L("Küche:") == ("cat", "Küche") and L("ERSTE HILFE") == ("caps", "ERSTE HILFE") and L("## Kleider") == ("cat", "Kleider") and L("---") is None
        assert L("Gaskartusche 230g (kaufen)")[1]["buy"] and L("3 XL Shirts")[1]["name"] == "XL Shirts" and L("Garmin 64x")[1]["n"] == 1
        r = pl_parse_text("SCHLAFEN\nZelt 1,8kg\n\nEssen:\n[ ] 4 Riegel à 45 g\n<img src=x onerror=alert(1)> 5 g\n???\n")
        assert [(i["name"], i["g"], i["n"], i["cat"], i["kind"]) for i in r["items"]] == [("Zelt", 1800, 1, "sleep", "base"), ("Riegel", 45, 4, "food", "cons"),
                                                                                         ("<img src=x onerror=alert(1)>", 5, 1, "food", "cons")], r
        # tables: separator, heading, columns, decimal comma, Windows-1252, xlsx, bombs
        csvb = "Gegenstand;Gewicht (kg);Anzahl;Kategorie\r\nKäse;0,25;2;Essen\r\nZelt;1,8;1;Schlafen\r\n=SUM(A1);1;1;x\r\n".encode("cp1252")
        p = pl_import_preview(data=csvb, name="Liste.csv")
        assert p["kind"] == "table" and p["header"] and p["unit"] == "kg" and p["map"]["name"] == 0 and p["map"]["g"] == 1 and p["map"]["n"] == 2 and p["map"]["cat"] == 3, p
        assert [(i["name"], i["g"], i["n"], i["cat"]) for i in p["items"]] == [("Käse", 250, 2, "food"), ("Zelt", 1800, 1, "sleep"), ("=SUM(A1)", 1000, 1, "X")], p["items"]
        x = _pl_test_xlsx([["Name", "Gewicht", "Stk"], ["Schlafsack", 950, 1], ["Müesli", ("=B2/2", 475), 2]])
        p = pl_import_preview(data=x, name="Tour.xlsx")
        assert [(i["name"], i["g"], i["n"]) for i in p["items"]] == [("Schlafsack", 950, 1), ("Müesli", 475, 2)] and p["title"] == "Tour", p
        for bad in (_pl_test_xlsx([["a"]], {"xl/media/bombe.bin": b"\0" * (PL_X_TOTAL + 1024)}), _pl_test_xlsx([["a"]], {f"x/{i}.xml": b"<a/>" for i in range(PL_X_ENTRIES + 5)}),
                    _pl_test_xlsx([["a"]], doctype='<!DOCTYPE s [<!ENTITY a "aaaa">]>'), b"PK\x03\x04kaputt",
                    _pl_test_xlsx([["a"]], sst=('<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE s [<!ENTITY a "aaaa">]>'
                                                '<sst><si><t>&a;</t></si></sst>').encode("utf-16")),      # the words are not findable as bytes
                    _pl_test_xlsx([["a"]], sst=b'<?xml version="1.0" encoding="ISO-8859-1"?><sst><si><t>a</t></si></sst>')):
            try:
                pl_import_preview(data=bad, name="b.xlsx")
                raise AssertionError("an unsafe xlsx was read")
            except PLError:
                pass
        assert pl_csv_cell("=1+1") == "'=1+1" and pl_csv_cell("@x") == "'@x" and pl_csv_cell("-5") == "'-5" and pl_csv_cell(" +x") == "'+x" and pl_csv_cell("Zelt") == "Zelt"
        # lists: create, merge of two phones, rights, export and back
        P = lambda r: tausch_imply(ROLE_PERMS.get(r, ()))
        anna = {"key": "anna", "name": "Anna", "admin": False, "perms": P("family"), "is_admin": False}
        carl = dict(anna, key="carl", name="Carl")
        bob = {"key": "bob", "name": "Bob", "admin": False, "perms": P("friend"), "is_admin": False}
        kim = {"key": "kim", "name": "Kim", "admin": False, "perms": P("kid"), "is_admin": False}
        ok, err, res, code = pl_action(anna, {"action": "new", "name": "Jura", "template": "camp", "goal": "9 kg"})
        assert ok and code == 200, err
        lid = res["id"]
        Lx = PL["lists"][lid]
        assert Lx["goal_g"] == 9000 and len(Lx["items"]) == len(PL_TEMPLATES[1][2]) and os.path.isfile(os.path.join(tmp, "pack", lid + ".json"))
        a, b = Lx["items"][0], Lx["items"][1]
        r0 = Lx["rev"]
        assert pl_action(anna, {"action": "item", "list": lid, "id": a["id"], "set": {"packed": True}, "base": a["rev"]})[0]
        ok, err, res, code = pl_action(carl, {"action": "item", "list": lid, "id": b["id"], "set": {"packed": True}, "base": r0})
        assert ok and a["packed"] and b["packed"] and Lx["rev"] == r0 + 2 and not res["stale"], "two phones, two items: both stay"
        ok, err, res, code = pl_action(carl, {"action": "item", "list": lid, "id": a["id"], "set": {"buy": True}, "base": r0})
        assert ok and res["stale"] and a["packed"] and a["buy"] and a["by"] == "Carl", "the same item: fields are merged, the last change wins"
        d = pl_get(carl, lid, r0)[2]
        assert {x["id"] for x in d["items"]} == {a["id"], b["id"]} and pl_get(carl, lid, Lx["rev"])[2].get("same")
        assert pl_action(bob, {"action": "item", "list": lid, "id": a["id"], "set": {"packed": False}})[3] == 403 and pl_get(bob, lid)[0], "friend: look, not change"
        assert not pl_get(kim, lid)[0] and pl_action(kim, {"action": "new", "name": "x"})[3] == 403
        assert pl_action(carl, {"action": "del", "id": lid})[3] == 403 and pl_action(anna, {"action": "add", "list": lid, "name": "=HYPERLINK(\"x\")", "w": "5 g"})[0]
        t = pl_totals(Lx["items"])
        assert t["pack"] == t["base"] + t["cons"] and t["worn"] > 0 and t["cons"] > 0 and t["total"] == t["pack"] + t["worn"]
        csvx = pl_export_csv(Lx, "de")
        assert b"'=HYPERLINK" in csvx and b";=HYPERLINK" not in csvx and b';"=HYPERLINK' not in csvx and csvx[:3] == b"\xef\xbb\xbf"
        back = pl_import_preview(data=csvx, name="Jura.csv")
        assert back["kind"] == "table" and len(back["items"]) == len(Lx["items"]), (back["map"], len(back["items"]))
        key = lambda i: (i["name"], i["g"], i["n"], i["cat"], i["kind"], i["packed"], i["buy"])
        assert sorted(map(key, back["items"])) == sorted(map(key, Lx["items"])), "CSV out and in again: the same items"
        PL.update(root=None, lists=None)
        assert pl_load() and PL["lists"][lid]["items"][0]["packed"], "read again from the file"
        assert "pack: jb.pack" in _pl_upload_js() and 'id="tz-pack"' in TAUSCH_PAGE and "/tausch/pack" in TAUSCH_GUEST_HTML, "hooks in the file exchange pages"
        assert role_allows("family", "/api/tausch/pack", "POST", {}) and role_allows("friend", "/tausch/packlisten", "GET", {}) and not role_allows("kid", "/tausch/packlisten", "GET", {})
        import html as _h
        hp = pl_print_html(PL["lists"][lid], "de")
        assert "&lt;" not in hp or "<img src=x" not in hp
        assert pl_action(anna, {"action": "add", "list": lid, "text": "<img src=x onerror=alert(1)>"})[0] and "<img src=x" not in pl_print_html(PL["lists"][lid], "de")
        assert "<img src=x" not in (pl_guest_html("tok", lid, "de") or "") and _h.escape("<img src=x onerror=alert(1)>") in pl_guest_html("tok", lid, "de")
        assert pl_action(anna, {"action": "del", "id": lid})[0] and not os.path.exists(os.path.join(tmp, "pack", lid + ".json"))
    finally:
        CFG.update(keep); TZ.update(keepTZ); PL.update(keepPL); g.update(sv)
        shutil.rmtree(tmp, ignore_errors=True)
    return "weights, lines, CSV (cp1252, decimal comma), xlsx + bombs refused, two phones merged, rights, CSV out and in, escaping"


SELFTEST_EXTRA.append(("Packing lists: import, merge, rights, export (639zzw)", pl_selftest))
