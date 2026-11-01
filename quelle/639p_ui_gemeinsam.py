#@ MoveEye – Teil 639p: gemeinsame Menü-Datei MoveEye ↔ MoveEye Sim (simulator3d/ui_gemeinsam.json, P1 «totale Integration», Daniel 31.10.2026): Gruppen-IDs, Namen, Symbole, Reihenfolge, Texte der Leiste, geteilte Einstellungen; Selbsttest prüft beide Seiten dagegen. Wird von werkzeuge/bauen.py mit den anderen Teilen zu einer Datei zusammengesetzt.
# ----------------------------------------------------------------------------
# Eine Quelle für beide Programme. Entscheide Daniel (31.10.2026): eine Einfach/Experte-Wahl, eine Sprache, Auf-/Zuklappen
# wird nicht geteilt, «Sensoren» im Simulator heisst «Zusatzgeräte» (extras, Strom und Netz bleiben darin).
#   * UI_GEMEINSAM: die Datei, beim Bauen eingebettet (werkzeuge/bauen.py schreibt den Block unten neu, --pruefen meldet
#     einen alten Stand) - die Signatur der Hauptdatei deckt sie mit ab. Nicht von Hand ändern: die JSON-Datei ändern, bauen.
#   * ui_gem_text("close", "fr") -> Text der Bedienleiste (Komponente aus Paket P0, 639o) - en ist der Schlüssel in DE / TRX.
#   * ui_gem_gid("system") -> "sys": alte Gruppen-IDs älterer Simulatoren (dieselbe Tabelle steht als SC_GID_ALIAS in 470).
#   * sim_features(): was der verbundene Simulator kann (/info «features», z. B. "menu1"); ältere senden nichts.
#   * Selbsttest «One menu file …»: Web-Gruppen (GROUPS 530), Fenster-Gruppen (TK_GROUPS / TK_GROUP_ICONS 639c),
#     Übersetzungen, Texte der Leiste, Alias und Symbole der Seite «Simulator» (470) - und, wenn der Ordner simulator3d da
#     ist, die Gruppen des Simulators (main.gd GROUPS / GROUP_IDS / GROUP_RENAME, i18n/texte.json, export_presets.cfg).
#     Der Simulator prüft dasselbe ohne Bild (werkzeuge/ui_gemeinsam_test.gd) und beim Start (Log «Menü-Datei: OK»).
# ----------------------------------------------------------------------------

# ---- UI_GEMEINSAM (von werkzeuge/bauen.py aus simulator3d/ui_gemeinsam.json – nicht von Hand ändern) ----
UI_GEMEINSAM = json.loads(r"""{
 "v": 1,
 "_hinweis": "Gemeinsame Menü-Datei MoveEye ↔ MoveEye Sim (P1 «totale Integration», Daniel 31.10.2026). Eine Quelle für Gruppen-IDs, Namen, Symbole, Reihenfolge, die Texte der Bedienleiste und die geteilten Einstellungen. MoveEye bettet sie beim Bauen ein (werkzeuge/bauen.py → quelle/639p_ui_gemeinsam.py, UI_GEMEINSAM); der Simulator liest sie aus res:// (kommt mit in die .exe, export_presets.cfg) über scripts/ui_gemeinsam.gd. Geprüft: Selbsttest von MoveEye («One menu file …») und werkzeuge/ui_gemeinsam_test.gd (Simulator, ohne Bild); beim Start schreibt der Simulator «Menü-Datei: OK …» ins Log. Neue gemeinsame Gruppe oder Umbenennung: zuerst hier, dann beide Seiten.",
 "_felder": {
  "groups": "Reihenfolge nach «order» (beide Seiten zeigen ihre Gruppen in dieser Reihenfolge). «mw» / «sim»: gibt es auf dieser Seite, «key» = Übersetzungs-Schlüssel der Seite (MoveEye: englischer Text, Simulator: deutscher Text), «names» = Anzeige in de / en / fr / it / rm. «emoji» = Web und Seite «Simulator» von MoveEye, «draw» = gezeichnetes Symbol im Simulator (ui_style.gd / mehr_icons.gd, keine Emoji-Schrift) und SC_ICON auf der Seite «Simulator», «tk» = Zeichen im Pi-Fenster. «sim.emoji» / «sim.draw»: bewusste Abweichung (mit «abweichung»). «alias»: alte IDs, gelten weiter (ältere Simulatoren, gespeicherte Werte). «sim.old»: alte Namen im Simulator (gespeicherter Klappzustand wird übernommen).",
  "parts": "Teile (Unterkarten) im Simulator mit eigener Regel: «gid/teil» -> neuer Name, alte Namen, Bezug zu einer MoveEye-Gruppe («same_as»: gleicher Name gewollt).",
  "bar": "Texte der Bedienleiste (Komponente aus Paket P0 «real-layout-leiste»): «en» = Schlüssel in MoveEye, «de» = Schlüssel im Simulator (T.t).",
  "shared": "Einstellungen, die beide Seiten gleich haben (Abgleich kommt mit P2; Entscheide Daniel 31.10.2026: E1 eine Einfach/Experte-Wahl, E2 eine Sprache, E3 Auf-/Zuklappen nicht teilen, E4 Sensoren -> Zusatzgeräte).",
  "local": "bleibt pro Gerät / Programm, wird nie geteilt",
  "features": "Feld «features» in /info des Simulators: was er kann (MoveEye richtet sich danach, ältere Simulatoren senden es nicht)"
 },
 "features": [
  "menu1"
 ],
 "alias": {
  "system": "sys",
  "sensors": "extras"
 },
 "groups": [
  {
   "id": "alarm",
   "order": 10,
   "emoji": "🛡",
   "tk": "🛡",
   "mw": {
    "key": "Protection",
    "names": {
     "de": "Schutz",
     "en": "Protection",
     "fr": "Protection",
     "it": "Protezione",
     "rm": "Protecziun"
    }
   }
  },
  {
   "id": "notify",
   "order": 11,
   "emoji": "🚨",
   "tk": "⚠",
   "mw": {
    "key": "What happens at an alarm?",
    "names": {
     "de": "Was passiert bei Alarm?",
     "en": "What happens at an alarm?",
     "fr": "Que se passe-t-il en cas d’alarme ?",
     "it": "Cosa succede in caso di allarme?",
     "rm": "Tge capita tar in alarm?"
    }
   }
  },
  {
   "id": "theft",
   "order": 12,
   "emoji": "🔒",
   "tk": "⚷",
   "mw": {
    "key": "Theft protection",
    "names": {
     "de": "Diebstahlschutz",
     "en": "Theft protection",
     "fr": "Protection antivol",
     "it": "Protezione antifurto",
     "rm": "Protecziun cunter il ladernezi"
    }
   }
  },
  {
   "id": "sched",
   "order": 13,
   "emoji": "🗓",
   "tk": "🗓",
   "mw": {
    "key": "Zones, schedule, presence",
    "names": {
     "de": "Zonen, Zeitplan, Anwesenheit",
     "en": "Zones, schedule, presence",
     "fr": "Zones, horaire, présence",
     "it": "Zone, orario, presenza",
     "rm": "Zonas, urari, preschientscha"
    }
   }
  },
  {
   "id": "detect",
   "order": 14,
   "emoji": "🎯",
   "tk": "◎",
   "mw": {
    "key": "Detection",
    "names": {
     "de": "Erkennung",
     "en": "Detection",
     "fr": "Détection",
     "it": "Rilevamento",
     "rm": "Identificaziun"
    }
   }
  },
  {
   "id": "scene",
   "order": 20,
   "emoji": "🌍",
   "draw": "globe",
   "sim": {
    "key": "Szene",
    "names": {
     "de": "Szene",
     "en": "Scene",
     "fr": "Scène",
     "it": "Scena",
     "rm": "Scena"
    }
   }
  },
  {
   "id": "weather",
   "order": 21,
   "emoji": "🌦",
   "draw": "cloud",
   "sim": {
    "key": "Wetter",
    "names": {
     "de": "Wetter",
     "en": "Weather",
     "fr": "Météo",
     "it": "Meteo",
     "rm": "Aura"
    }
   }
  },
  {
   "id": "visit",
   "order": 22,
   "emoji": "🚶",
   "draw": "person",
   "sim": {
    "key": "Besuch",
    "names": {
     "de": "Besuch",
     "en": "Visit",
     "fr": "Visite",
     "it": "Visita",
     "rm": "Visita"
    }
   }
  },
  {
   "id": "camera",
   "order": 30,
   "emoji": "📷",
   "draw": "camera",
   "tk": "▣",
   "mw": {
    "key": "Cameras & head",
    "names": {
     "de": "Kameras & Kopf",
     "en": "Cameras & head",
     "fr": "Caméras et tête",
     "it": "Telecamere e testa",
     "rm": "Cameras e chau"
    }
   },
   "sim": {
    "key": "Kamerabild",
    "names": {
     "de": "Kamerabild",
     "en": "Camera picture",
     "fr": "Image de la caméra",
     "it": "Immagine della telecamera",
     "rm": "Maletg da la camera"
    },
    "emoji": "👁",
    "draw": "lens",
    "abweichung": "anderer Inhalt (Bild-Effekte statt Kameras und Kopf) und das Kamera-Symbol hat im Simulator schon die Karte «Kameras» (Verbindung der Kameras)"
   }
  },
  {
   "id": "mover",
   "order": 40,
   "emoji": "🚜",
   "draw": "track",
   "tk": "⇕",
   "mw": {
    "key": "Mover",
    "names": {
     "de": "Mover",
     "en": "Mover",
     "fr": "Mover",
     "it": "Mover",
     "rm": "Mover"
    }
   },
   "sim": {
    "key": "Mover",
    "names": {
     "de": "Mover",
     "en": "Mover",
     "fr": "Mover",
     "it": "Mover",
     "rm": "Mover"
    }
   }
  },
  {
   "id": "lightsound",
   "order": 50,
   "emoji": "💡",
   "draw": "bulb",
   "tk": "☀",
   "mw": {
    "key": "Light & sound",
    "names": {
     "de": "Licht & Ton",
     "en": "Light & sound",
     "fr": "Lumière et son",
     "it": "Luce e suono",
     "rm": "Glisch e tun"
    }
   },
   "sim": {
    "key": "Licht & Ton",
    "names": {
     "de": "Licht & Ton",
     "en": "Light & sound",
     "fr": "Lumière et son",
     "it": "Luce e suono",
     "rm": "Glisch e tun"
    }
   }
  },
  {
   "id": "extras",
   "order": 60,
   "alias": [
    "sensors"
   ],
   "emoji": "🔌",
   "draw": "puzzle",
   "tk": "◉",
   "mw": {
    "key": "Extra devices",
    "names": {
     "de": "Zusatzgeräte",
     "en": "Extra devices",
     "fr": "Appareils supplémentaires",
     "it": "Dispositivi aggiuntivi",
     "rm": "Apparats supplementars"
    }
   },
   "sim": {
    "key": "Zusatzgeräte",
    "old": [
     "Sensoren"
    ],
    "names": {
     "de": "Zusatzgeräte",
     "en": "Extra devices",
     "fr": "Appareils supplémentaires",
     "it": "Dispositivi aggiuntivi",
     "rm": "Apparats supplementars"
    },
    "abweichung": "im Simulator mit den Teilen «Strom» und «Netz» (Fehler simulieren statt einrichten; Entscheid E4 b) - MoveEye hat dafür eigene Gruppen"
   }
  },
  {
   "id": "power",
   "order": 70,
   "emoji": "🔋",
   "tk": "⚡",
   "mw": {
    "key": "Power supply",
    "names": {
     "de": "Stromversorgung",
     "en": "Power supply",
     "fr": "Alimentation",
     "it": "Alimentazione",
     "rm": "Alimentaziun"
    }
   }
  },
  {
   "id": "net",
   "order": 71,
   "emoji": "📶",
   "tk": "📶",
   "mw": {
    "key": "Network & access",
    "names": {
     "de": "Netz & Zugang",
     "en": "Network & access",
     "fr": "Réseau et accès",
     "it": "Rete e accesso",
     "rm": "Rait ed access"
    }
   }
  },
  {
   "id": "security",
   "order": 72,
   "emoji": "🔐",
   "tk": "🔐",
   "reserved": [
    "Sicherheit"
   ],
   "mw": {
    "key": "Security",
    "names": {
     "de": "Sicherheit",
     "en": "Security",
     "fr": "Sécurité",
     "it": "Sicurezza",
     "rm": "Segirezza"
    }
   }
  },
  {
   "id": "game",
   "order": 73,
   "emoji": "🎮",
   "draw": "pad",
   "sim": {
    "key": "Spiel",
    "names": {
     "de": "Spiel",
     "en": "Game",
     "fr": "Jeu",
     "it": "Gioco",
     "rm": "Gieu"
    }
   }
  },
  {
   "id": "wildlife",
   "order": 74,
   "emoji": "🎯",
   "draw": "target",
   "sim": {
    "key": "Wildtier",
    "names": {
     "de": "Wildtier",
     "en": "Wild animal",
     "fr": "Animal sauvage",
     "it": "Animale selvatico",
     "rm": "Animal selvadi"
    }
   }
  },
  {
   "id": "testrun",
   "order": 75,
   "emoji": "✅",
   "draw": "check",
   "sim": {
    "key": "Testen",
    "names": {
     "de": "Testen",
     "en": "Testing",
     "fr": "Tester",
     "it": "Testare",
     "rm": "Testar"
    }
   }
  },
  {
   "id": "sys",
   "order": 80,
   "alias": [
    "system"
   ],
   "emoji": "⚙",
   "draw": "gear",
   "tk": "⚙",
   "mw": {
    "key": "System",
    "names": {
     "de": "System",
     "en": "System",
     "fr": "Système",
     "it": "Sistema",
     "rm": "Sistem"
    }
   },
   "sim": {
    "key": "System",
    "names": {
     "de": "System",
     "en": "System",
     "fr": "Système",
     "it": "Sistema",
     "rm": "Sistem"
    }
   }
  },
  {
   "id": "dev",
   "order": 90,
   "emoji": "🧪",
   "draw": "tools",
   "tk": "⚒",
   "mw": {
    "key": "Developer",
    "names": {
     "de": "Entwickler",
     "en": "Developer",
     "fr": "Développeur",
     "it": "Sviluppatore",
     "rm": "Sviluppader"
    }
   },
   "sim": {
    "key": "Entwickler",
    "names": {
     "de": "Entwickler",
     "en": "Developer",
     "fr": "Développeur",
     "it": "Sviluppatore",
     "rm": "Sviluppader"
    }
   }
  }
 ],
 "parts": {
  "sys/kids": {
   "sim": "Kinder-Modus",
   "old": [
    "Sicherheit / Benutzer"
   ],
   "names": {
    "de": "Kinder-Modus",
    "en": "Kids mode",
    "fr": "Mode enfants",
    "it": "Modalità bambini",
    "rm": "Modus d’uffants"
   },
   "note": "eindeutiger Name: «Sicherheit» ist in MoveEye die Gruppe Passwort / Benutzer (security)"
  },
  "sys/sicherung": {
   "sim": "Sicherung",
   "mw_sec": "Backup",
   "names": {
    "de": "Sicherung",
    "en": "Backup",
    "fr": "Sauvegarde",
    "it": "Backup",
    "rm": "Copia da segirezza"
   },
   "note": "gleicher Name wie MoveEye «Sicherung» (Abschnitt Backup, Gruppe Schutz): dort erscheint die Simulator-Sicherung als Eintrag «Simulator» (Teil 639s). Abweichung: im Simulator unter System (Entscheid Daniel 01.11.2026)"
  },
  "extras/power": {
   "sim": "Strom",
   "same_as": "power",
   "note": "Akku / Solar simulieren - in MoveEye eigene Gruppe «Stromversorgung»"
  },
  "extras/net": {
   "sim": "Netz",
   "same_as": "net",
   "note": "Netz-Ausfall simulieren - in MoveEye eigene Gruppe «Netz & Zugang»"
  }
 },
 "bar": {
  "mode": [
   "simple",
   "expert"
  ],
  "icons": [
   "color",
   "plain"
  ],
  "fold": [
   "close",
   "groups",
   "open"
  ],
  "texts": {
   "simple": {
    "en": "Simple",
    "de": "Einfach",
    "fr": "Simple",
    "it": "Semplice",
    "rm": "Simpel"
   },
   "expert": {
    "en": "Expert",
    "de": "Experte",
    "fr": "Expert",
    "it": "Esperto",
    "rm": "Expert"
   },
   "color": {
    "en": "Symbols coloured",
    "de": "Symbole farbig",
    "fr": "Symboles en couleur",
    "it": "Simboli a colori",
    "rm": "Simbols colurads"
   },
   "plain": {
    "en": "plain",
    "de": "schlicht",
    "fr": "simples",
    "it": "semplici",
    "rm": "simpels"
   },
   "close": {
    "en": "Collapse all",
    "de": "Alle zuklappen",
    "fr": "Tout fermer",
    "it": "Chiudi tutto",
    "rm": "Serrar tut"
   },
   "groups": {
    "en": "Groups only",
    "de": "Nur Gruppen",
    "fr": "Ouvrir seulement les groupes",
    "it": "Aprire solo i gruppi",
    "rm": "Avrir mo las gruppas"
   },
   "open": {
    "en": "Expand all",
    "de": "Alle aufklappen",
    "fr": "Tout ouvrir",
    "it": "Apri tutto",
    "rm": "Avrir tut"
   }
  }
 },
 "shared": {
  "simple": {
   "mw": "CFG ui_simple",
   "sim": "ui_simple",
   "values": [
    true,
    false
   ],
   "note": "E1: eine Einfach/Experte-Wahl für alles (MoveEye-Standard, Seiten und Simulator)"
  },
  "icons": {
   "mw": "mw-icons (web_ui)",
   "sim": "ui_icons",
   "values": [
    "color",
    "plain"
   ]
  },
  "lang": {
   "mw": "CFG lang",
   "sim": "i18n.gd Wahl",
   "values": [
    "auto",
    "de",
    "fr",
    "it",
    "rm",
    "en"
   ],
   "note": "E2: eine Sprache (mw-lang folgt CFG lang)"
  },
  "dev_area": {
   "mw": "CFG dev_area",
   "sim": "dev_area",
   "values": [
    true,
    false
   ],
   "dir": "mw->sim",
   "note": "nur der Besitzer schaltet in MoveEye"
  }
 },
 "local": [
  "open",
  "hdr",
  "panel",
  "search",
  "kids",
  "windows",
  "theme"
 ]
}""")
# ---- Ende UI_GEMEINSAM ----

UI_GEM_LANGS = ("de", "en", "fr", "it", "rm")


def ui_gem_tr(key, lang):
    """the text of a MoveEye key (English) in a language - the same rule as the web page / window (DE, TRX, else English)"""
    if lang == "en":
        return key
    if lang == "de":
        return DE.get(key, key)
    return (TRX.get(lang) or {}).get(key) or key


def ui_gem_text(k, lang="de"):
    """a text of the bar: simple, expert, color, plain, close, groups, open"""
    t = ((UI_GEMEINSAM.get("bar") or {}).get("texts") or {}).get(k) or {}
    return t.get(lang) or t.get("en") or k


def ui_gem_gid(gid):
    """an old group id (older simulators) -> the id of today"""
    return (UI_GEMEINSAM.get("alias") or {}).get(gid, gid)


def ui_gem_groups(side):
    """the groups of one side («mw» / «sim») in their order"""
    return sorted((g for g in UI_GEMEINSAM.get("groups") or [] if side in g), key=lambda g: g.get("order", 0))


def sim_features():
    """/info «features» of the connected simulator (P1: "menu1" = gids sys / extras, part «Kinder-Modus"); [] = older one"""
    f = (SIM.get("info") or {}).get("features") or []
    return [str(x) for x in f] if isinstance(f, list) else []


_sim_status_639p_base = sim_status


def sim_status():                                         # + 639p: the page «Simulator» knows what the simulator can
    r = _sim_status_639p_base()
    r["features"] = sim_features()
    return r


def ui_gem_check(base=None):
    """(problems, counts) - MoveEye (and the simulator sources, if there) against simulator3d/ui_gemeinsam.json"""
    base = base or os.path.dirname(os.path.abspath(__file__))
    U, probs = UI_GEMEINSAM, []
    p = os.path.join(base, "simulator3d", "ui_gemeinsam.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            if json.load(f) != U:
                probs.append("UI_GEMEINSAM is older than simulator3d/ui_gemeinsam.json - run werkzeuge/bauen.py")
    if not U.get("groups"):
        return ["UI_GEMEINSAM is empty (werkzeuge/bauen.py embeds simulator3d/ui_gemeinsam.json)"], {}
    ids = [g["id"] for g in U["groups"]]
    if len(set(ids)) != len(ids):
        probs.append("a group id twice in the file")
    for old, new in (U.get("alias") or {}).items():
        if new not in ids or old in ids:
            probs.append(f"alias {old} -> {new}: the new id must exist, the old one not")
    mw = ui_gem_groups("mw")
    src = zd_source()
    # 1. the web page (GROUPS in 530): ids in this order, symbol and name
    m = re.search(r"const GROUPS = \[(.*?)\n\];", src, re.S)
    web = re.findall(r'\{id: "(\w+)", tab: "\w+", icon: "([^"]*)", name: "([^"]*)"', m.group(1)) if m else []
    if [w[0] for w in web] != [g["id"] for g in mw]:
        probs.append("web GROUPS (530): " + ", ".join(w[0] for w in web) + " instead of " + ", ".join(g["id"] for g in mw))
    for gid_, icon, name in web:
        g = next((x for x in mw if x["id"] == gid_), None)
        if g and (icon != g.get("emoji") or name != g["mw"]["key"]):
            probs.append(f"web GROUPS {gid_}: «{icon} {name}» instead of «{g.get('emoji')} {g['mw']['key']}»")
    # 2. the window (TK_GROUPS, TK_GROUP_ICONS)
    if [t[0] for t in TK_GROUPS] != [g["id"] for g in mw]:
        probs.append("window TK_GROUPS: " + ", ".join(t[0] for t in TK_GROUPS) + " instead of " + ", ".join(g["id"] for g in mw))
    for t in TK_GROUPS:
        g = next((x for x in mw if x["id"] == t[0]), None)
        if g and t[1] != g["mw"]["key"]:
            probs.append(f"window TK_GROUPS {t[0]}: «{t[1]}» instead of «{g['mw']['key']}»")
        if g and g.get("tk") and TK_GROUP_ICONS.get(t[0]) != g["tk"]:
            probs.append(f"window symbol {t[0]}: «{TK_GROUP_ICONS.get(t[0])}» instead of «{g['tk']}»")
    # 3. names and texts of the bar in every language (as the web page / window shows them)
    for g in mw:
        for lg in UI_GEM_LANGS:
            want = (g["mw"].get("names") or {}).get(lg)
            if want and ui_gem_tr(g["mw"]["key"], lg) != want:
                probs.append(f"name {g['id']} ({lg}): «{ui_gem_tr(g['mw']['key'], lg)}» instead of «{want}»")
    bar = (U.get("bar") or {}).get("texts") or {}
    for k, t in bar.items():
        for lg in UI_GEM_LANGS:
            if ui_gem_tr(t["en"], lg) != t.get(lg):
                probs.append(f"bar text {k} ({lg}): «{ui_gem_tr(t['en'], lg)}» instead of «{t.get(lg)}»")
    # 4. the page «Simulator» (470): alias table and the drawn symbols of the simulator groups
    m = re.search(r"const SC_GID_ALIAS = (\{[^}]*\});", src)
    if not m or json.loads(m.group(1)) != (U.get("alias") or {}):
        probs.append("470 SC_GID_ALIAS is not the alias table of the file")
    m = re.search(r"const SC_ICON = \{(.*?)\};", src, re.S)
    sc = set(re.findall(r"\n  (\w+): '", m.group(1))) if m else set()
    for g in ui_gem_groups("sim"):
        dr = g["sim"].get("draw", g.get("draw"))
        if dr and dr not in sc:
            probs.append(f"470 SC_ICON: the symbol «{dr}» of the simulator group {g['id']} is missing")
    n = {"mw": len(mw), "sim": len(ui_gem_groups("sim")), "both": len([g for g in U["groups"] if "mw" in g and "sim" in g]),
         "bar": len(bar), "simsrc": False}
    # 5. the simulator (sources, if the folder is there - GitHub has no Godot)
    gdir = os.path.join(base, "simulator3d", "scripts")
    if os.path.isfile(os.path.join(gdir, "main.gd")):
        with open(os.path.join(gdir, "main.gd"), encoding="utf-8") as f:
            gd = f.read()
        n["simsrc"] = True
        m = re.search(r"\nconst GROUPS := \[(.*?)\]\]\n", gd, re.S)
        rows = re.findall(r'\[\s*"([^"]+)", "(\w*)", "([^"]*)", \[([^\]]*)\]', m.group(1) + "]]") if m else []
        sim = ui_gem_groups("sim")
        if [r[0] for r in rows] != [g["sim"]["key"] for g in sim]:
            probs.append("simulator GROUPS (main.gd): " + ", ".join(r[0] for r in rows) + " instead of " + ", ".join(g["sim"]["key"] for g in sim))
        m = re.search(r"\nconst GROUP_IDS := \{(.*?)\}", gd, re.S)
        gids = dict(re.findall(r'"([^"]+)": "(\w+)"', m.group(1))) if m else {}
        m = re.search(r"\nconst GROUP_RENAME := \{(.*?)\}", gd, re.S)
        ren = dict(re.findall(r'"([^"]+)": "([^"]+)"', m.group(1))) if m else {}
        for g in sim:
            r = next((x for x in rows if x[0] == g["sim"]["key"]), None)
            if gids.get(g["sim"]["key"]) != g["id"]:
                probs.append(f"simulator GROUP_IDS {g['sim']['key']}: «{gids.get(g['sim']['key'])}» instead of «{g['id']}»")
            if r and (r[1] != g["sim"].get("draw", g.get("draw")) or r[2] != g["sim"].get("emoji", g.get("emoji"))):
                probs.append(f"simulator symbol {g['id']}: «{r[1]} {r[2]}» instead of «{g['sim'].get('draw', g.get('draw'))} {g['sim'].get('emoji', g.get('emoji'))}»")
            for o in g["sim"].get("old") or []:
                if ren.get(o) != g["sim"]["key"]:
                    probs.append(f"simulator GROUP_RENAME: old name «{o}» -> «{g['sim']['key']}» missing")
        for pid, pt in (U.get("parts") or {}).items():
            g = next((x for x in sim if x["id"] == pid.split("/")[0]), None)
            r = next((x for x in rows if g and x[0] == g["sim"]["key"]), None)
            if not r or f'"{pt["sim"]}"' not in r[3]:
                probs.append(f"simulator part {pid}: «{pt['sim']}» missing in main.gd GROUPS")
            for o in pt.get("old") or []:
                if f'"{o}"' in gd:
                    probs.append(f"simulator part {pid}: the old name «{o}» is still in main.gd")
        for g in U["groups"]:
            for rv in g.get("reserved") or []:
                for r in rows:
                    for nm in [r[0]] + re.findall(r'"([^"]*)"', r[3]):
                        if nm == rv or nm.startswith(rv + " ") or nm.startswith(rv + "/"):
                            probs.append(f"simulator «{nm}»: the name belongs to the group {g['id']} of MoveEye")
        tp = os.path.join(base, "simulator3d", "i18n", "texte.json")
        if os.path.exists(tp):
            with open(tp, encoding="utf-8") as f:
                tx = json.load(f)
            for g in sim:
                for lg in ("en", "fr", "it", "rm"):
                    w = (g["sim"].get("names") or {}).get(lg)
                    if w and (tx.get(g["sim"]["key"]) or {}).get(lg) != w:
                        probs.append(f"simulator name {g['id']} ({lg}): «{(tx.get(g['sim']['key']) or {}).get(lg)}» instead of «{w}» (i18n/texte.json)")
            for k, t in bar.items():
                for lg in ("en", "fr", "it", "rm"):
                    if (tx.get(t["de"]) or {}).get(lg) != t.get(lg):
                        probs.append(f"simulator bar text {k} ({lg}): «{(tx.get(t['de']) or {}).get(lg)}» instead of «{t.get(lg)}» (i18n/texte.json)")
        ep = os.path.join(base, "simulator3d", "export_presets.cfg")
        if os.path.exists(ep):
            with open(ep, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("include_filter=") and "ui_gemeinsam.json" not in line:
                        probs.append("simulator export_presets.cfg: ui_gemeinsam.json is not in the .exe")
    return probs, n


def ui_gem_selftest():
    probs, n = ui_gem_check()
    assert not probs, f"{len(probs)} problems: " + " | ".join(probs[:12])
    assert ui_gem_gid("system") == "sys" and ui_gem_gid("sensors") == "extras" and ui_gem_gid("dev") == "dev", "alias"
    keep = SIM.get("info")
    try:
        SIM["info"] = {"features": ["menu1"]}
        assert "menu1" in sim_features() and sim_status().get("features") == ["menu1"], "features of the simulator"
        SIM["info"] = {"v": 1}
        assert sim_features() == [], "older simulator without features"
    finally:
        SIM["info"] = keep
    return (f"{n['mw']} groups MoveEye, {n['sim']} simulator, {n['both']} on both sides, {n['bar']} texts of the bar - same as the file"
            + ("" if n["simsrc"] else " (simulator folder not here)"))


SELFTEST_EXTRA.append(("One menu file MoveEye ↔ simulator (simulator3d/ui_gemeinsam.json: groups, symbols, texts)", ui_gem_selftest))
