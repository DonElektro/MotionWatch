#!/usr/bin/env python3
"""MoveEye-Selbstbau-Paket (Bausatz) aus den Daten im Repository erzeugen.

    python3 werkzeuge/bausatz.py                       # alles, Ausgabe nach ausgabe_bausatz/ (nicht im Repository)
    python3 werkzeuge/bausatz.py --aus ORDNER          # anderer Ausgabe-Ordner
    python3 werkzeuge/bausatz.py --sprachen de         # nur deutsche Anleitung (Standard: de,fr,it,rm,en)
    python3 werkzeuge/bausatz.py --ohne-bilder         # Anleitung ohne 3D-Bilder (schneller, kein WebGL nötig)
    python3 werkzeuge/bausatz.py --fest                # zusätzlich MoveEye_Bausatz.zip (fester Name für GitHub-Releases)
    python3 werkzeuge/bausatz.py --unsigniert          # auch ohne Signatur in versions.json (nur zum Testen)

Ergebnis: MoveEye_Bausatz_X.Y.Z.zip mit (alle Namen mit der laufenden Version, real-abgleich-v52)
  1_Anleitung/     MoveEye_Bauanleitung_X.Y.Z_de.pdf (Schweizer Deutsch; dazu fr / it / rm / en aus bau.json)
  2_MoveEye_v5-2_Druck_X.Y.Z/  3MF v5.2 (Platten A/B, alle Einzelteile mit Stopfen, Namen wie im Repository) + LIESMICH_Druck.txt
  3_Bestellliste/  MoveEye_Bestellliste_<Paket>_X.Y.Z.csv (Basis / Komplett / Autark), Preise geschätzt
  4_Software/      webcam_bewegung_X_Y_Z.py + moveeye_daten_X_Y_Z.zip + versions.json (signiert) + werkzeuge/einrichten.sh,
                   INSTALLATION.txt, Einrichtung_Raspberry_Pi.md
  LIESMICH.txt

Quellen (eine Quelle, nichts doppelt): hardware/gehaeuse/bau.json (Teile, Materialliste, Pakete, Schritte, Verkabelung,
Software, Inbetriebnahme, Wartung, Sicherheit), simulator3d/fehler_katalog.json (Fehlersuche),
simulator3d/inhalte/gehaeuse/gehaeuse.glb + modelle.json (3D-Bilder, gerendert mit three.js aus werkzeuge/three/ in
Chromium/Playwright), docs/Einrichtung_Raspberry_Pi.md, versions.json + Release-Dateien im Repository-Stamm.
PDF: HTML -> Chromium (Playwright) print-to-pdf. Gebraucht: python3 -m pip install playwright (Chromium vorhanden).
Keine Schlüssel, Passwörter oder ntfy-Themen: das Paket enthält nur Dateien aus dem öffentlichen Repository.
"""
import argparse
import base64
import csv
import hashlib
import html
import io
import json
import os
import re
import shutil
import sys
import time
import urllib.parse
import zipfile

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEH = os.path.join(R, "hardware", "gehaeuse")
DRUCK52 = os.path.join(GEH, "Druckdateien", "v5-2")
SPRACHEN = ["de", "fr", "it", "rm", "en"]
SPR_NAME = {"de": "Deutsch", "fr": "Français", "it": "Italiano", "rm": "Rumantsch", "en": "English"}

# ---- Texte, die nicht in bau.json stehen (Schlüssel = Deutsch) --------------------------------------------------------------
TX = {
    "MoveEye – Bauanleitung": {"en": "MoveEye – build guide", "fr": "MoveEye – notice de construction", "it": "MoveEye – istruzioni di costruzione", "rm": "MoveEye – instrucziun da construcziun"},
    "Selbstbau-Paket": {"en": "Self-build kit", "fr": "Kit à construire soi-même", "it": "Kit fai da te", "rm": "Pachet per construir sez"},
    "Gehäuse v5.2 (Standard)": {"en": "Case v5.2 (standard)", "fr": "Boîtier v5.2 (standard)", "it": "Custodia v5.2 (standard)", "rm": "Chascha v5.2 (standard)"},
    "Stand": {"en": "Status", "fr": "État", "it": "Stato", "rm": "Stadi"},
    "Inhalt": {"en": "Contents", "fr": "Sommaire", "it": "Indice", "rm": "Cuntegn"},
    "Die drei Pakete": {"en": "The three packages", "fr": "Les trois kits", "it": "I tre pacchetti", "rm": "Ils trais pachets"},
    "Paket": {"en": "Package", "fr": "Kit", "it": "Pacchetto", "rm": "Pachet"},
    "Was drin ist": {"en": "What is included", "fr": "Contenu", "it": "Contenuto", "rm": "Cuntegn"},
    "Summe (geschätzt)": {"en": "Total (estimate)", "fr": "Total (estimation)", "it": "Totale (stima)", "rm": "Total (stimà)"},
    "Masse": {"en": "Dimensions", "fr": "Dimensions", "it": "Dimensioni", "rm": "Dimensiuns"},
    "Bestellliste": {"en": "Order list", "fr": "Liste de commande", "it": "Lista d'ordine", "rm": "Glista da cumanda"},
    "Händler / Suchbegriff": {"en": "Shop / search term", "fr": "Magasin / recherche", "it": "Negozio / ricerca", "rm": "Butia / tschertga"},
    "Preis CHF": {"en": "Price CHF", "fr": "Prix CHF", "it": "Prezzo CHF", "rm": "Pretsch CHF"},
    "Optional (nicht in der Summe)": {"en": "Optional (not in the total)", "fr": "En option (hors total)", "it": "Opzionale (non nel totale)", "rm": "Opziunal (betg en il total)"},
    "Alle Preise sind Schätzungen in CHF ohne Versand (Stand %s) – im Shop prüfen. Die Links sind Suchlinks beim Händler.":
        {"en": "All prices are estimates in CHF without shipping (as of %s) – check at the shop. The links are search links at the shop.",
         "fr": "Tous les prix sont des estimations en CHF sans frais de port (état %s) – vérifier au magasin. Les liens sont des recherches chez le marchand.",
         "it": "Tutti i prezzi sono stime in CHF senza spedizione (stato %s) – verificare nel negozio. I link sono ricerche nel negozio.",
         "rm": "Tut ils pretschs èn stimaziuns en CHF senza spediziun (stadi %s) – controllar en la butia. Las colliaziuns èn tschertgas en la butia."},
    "Druckteile v5.2": {"en": "Print parts v5.2", "fr": "Pièces imprimées v5.2", "it": "Pezzi stampati v5.2", "rm": "Parts da stampa v5.2"},
    "Datei": {"en": "File", "fr": "Fichier", "it": "File", "rm": "Datoteca"},
    "Farbe": {"en": "Colour", "fr": "Couleur", "it": "Colore", "rm": "Colur"},
    "orange": {"en": "orange", "fr": "orange", "it": "arancione", "rm": "oransch"},
    "grau": {"en": "grey", "fr": "gris", "it": "grigio", "rm": "grisch"},
    "natur/weiss": {"en": "natural/white", "fr": "naturel/blanc", "it": "naturale/bianco", "rm": "natural/alv"},
    "schwarz": {"en": "black", "fr": "noir", "it": "nero", "rm": "nair"},
    "Farben: alles, was sich dreht oder neigt (Drehteller, Gabel, Arm 2, Kopf, Seitendeckel, Lampenhalter), in Orange; Unterteil, Deckel, Zwischenboden, Füsse und Stopfen in Grau; Diffusor natur/weiss, Pupillenring schwarz.":
        {"en": "Colours: everything that turns or tilts (turntable, yoke, arm 2, head, side cover, lamp holders) in orange; lower part, lid, shelf, feet and plugs in grey; diffuser natural/white, pupil ring black.",
         "fr": "Couleurs : tout ce qui tourne ou s'incline (plateau, fourche, bras 2, tête, couvercle latéral, supports de lampe) en orange ; partie inférieure, couvercle, plancher, pieds et bouchons en gris ; diffuseur naturel/blanc, anneau de pupille noir.",
         "it": "Colori: tutto ciò che ruota o si inclina (piatto, forcella, braccio 2, testa, coperchio laterale, portalampade) in arancione; parte inferiore, coperchio, ripiano, piedini e tappi in grigio; diffusore naturale/bianco, anello pupilla nero.",
         "rm": "Colurs: tut quai che rotescha u s'inclina (platta, furtga, bratsch 2, chau, viertgel lateral, tegnalampas) en oransch; part sut, viertgel, palantschieu, peis e tappuns en grisch; diffusur natural/alv, anel da la pupilla nair."},
    "Stopfen je Paket": {"en": "Plugs per package", "fr": "Bouchons par kit", "it": "Tappi per pacchetto", "rm": "Tappuns per pachet"},
    "Stopfen kommen in Öffnungen für Teile, die das Paket nicht hat. 17 (Reserve-Öffnung) braucht jedes Paket.":
        {"en": "Plugs close openings for parts the package does not have. Every package needs 17 (spare opening).",
         "fr": "Les bouchons ferment les ouvertures des pièces absentes du kit. Chaque kit a besoin du 17 (ouverture de réserve).",
         "it": "I tappi chiudono le aperture dei pezzi che il pacchetto non ha. Ogni pacchetto ha bisogno del 17 (apertura di riserva).",
         "rm": "Ils tappuns serran las avertüras per parts ch'il pachet n'ha betg. Mintga pachet basegna il 17 (avertüra da reserva)."},
    "keine weiteren": {"en": "no others", "fr": "aucun autre", "it": "nessun altro", "rm": "nagins auters"},
    "Vor dem Druck nachmessen": {"en": "Measure before printing", "fr": "Mesurer avant l'impression", "it": "Misurare prima della stampa", "rm": "Mesirar avant la stampa"},
    "Ergänzungen": {"en": "Additions", "fr": "Compléments", "it": "Aggiunte", "rm": "Cumplements"},
    "Stand MoveEye %s": {"en": "as of MoveEye %s", "fr": "état MoveEye %s", "it": "stato MoveEye %s", "rm": "stadi MoveEye %s"},
    "für Basis und Komplett (ohne Akku)": {"en": "for Basic and Complete (without battery)", "fr": "pour Base et Complet (sans batterie)", "it": "per Base e Completo (senza batteria)", "rm": "per Basa e Cumplet (senza accu)"},
    "nur mit Akku (Autark)": {"en": "only with battery (Autonomous)", "fr": "seulement avec batterie (Autonome)", "it": "solo con batteria (Autonomo)", "rm": "mo cun accu (Autarc)"},
    "nur ohne Akku (Basis, Komplett)": {"en": "only without battery (Basic, Complete)", "fr": "seulement sans batterie (Base, Complet)", "it": "solo senza batteria (Base, Completo)", "rm": "mo senza accu (Basa, Cumplet)"},
    "nur v5.2 mit dem Teil (Komplett, Autark)": {"en": "only v5.2 with the part (Complete, Autonomous)", "fr": "seulement v5.2 avec la pièce (Complet, Autonome)", "it": "solo v5.2 con il pezzo (Completo, Autonomo)", "rm": "mo v5.2 cun la part (Cumplet, Autarc)"},
    "unklar": {"en": "unclear", "fr": "pas clair", "it": "non chiaro", "rm": "nunclera"},
    "Verbindung": {"en": "Connection", "fr": "Connexion", "it": "Collegamento", "rm": "Colliaziun"},
    "Pins / Kanal": {"en": "Pins / channel", "fr": "Broches / canal", "it": "Pin / canale", "rm": "Pins / chanal"},
    "Installation auf dem Raspberry Pi": {"en": "Installation on the Raspberry Pi", "fr": "Installation sur le Raspberry Pi", "it": "Installazione sul Raspberry Pi", "rm": "Installaziun sin il Raspberry Pi"},
    "Was tun": {"en": "What to do", "fr": "Que faire", "it": "Cosa fare", "rm": "Tge far"},
    "Teil": {"en": "Part", "fr": "Pièce", "it": "Pezzo", "rm": "Part"},
    "Wann": {"en": "When", "fr": "Quand", "it": "Quando", "rm": "Cura"},
    "Anhang: Entwicklungs-Variante ohne Akku": {"en": "Appendix: development variant without battery", "fr": "Annexe : variante de développement sans batterie", "it": "Appendice: variante di sviluppo senza batteria", "rm": "Agiunta: variante da svilup senza accu"},
    "Für Tests am Schreibtisch: Sockel 13 statt UPS HAT (E) und Akkus, der Pi läuft an seinem eigenen Netzteil.":
        {"en": "For tests at the desk: socket 13 instead of UPS HAT (E) and cells, the Pi runs on its own power supply.",
         "fr": "Pour les essais au bureau : socle 13 au lieu de l'UPS HAT (E) et des accus, le Pi fonctionne sur sa propre alimentation.",
         "it": "Per prove alla scrivania: zoccolo 13 al posto dell'UPS HAT (E) e delle batterie, il Pi va con il suo alimentatore.",
         "rm": "Per tests a la maisa: zocla 13 empè da l'UPS HAT (E) ed ils accus, il Pi va cun sia atgna alimentaziun."},
    "Zusätzlich kaufen": {"en": "Buy in addition", "fr": "À acheter en plus", "it": "Da comprare in più", "rm": "Cumprar ultra"},
    "Zusätzlich drucken": {"en": "Print in addition", "fr": "À imprimer en plus", "it": "Da stampare in più", "rm": "Stampar ultra"},
    "Weglassen": {"en": "Leave out", "fr": "À omettre", "it": "Da tralasciare", "rm": "Laschar davent"},
    "Bild: Teile dieses Schritts blau hervorgehoben und leicht abgehoben.": {"en": "Picture: the parts of this step are highlighted in blue and lifted a little.", "fr": "Image : les pièces de cette étape sont en bleu et un peu soulevées.", "it": "Immagine: i pezzi di questo passo sono evidenziati in blu e un po' sollevati.", "rm": "Maletg: las parts da quest pass èn blauas ed in pau auzadas."},
    "Die Bilder zeigen das 3D-Modell aus dem Simulator (Werkstatt).": {"en": "The pictures show the 3D model from the simulator (workshop).", "fr": "Les images montrent le modèle 3D du simulateur (atelier).", "it": "Le immagini mostrano il modello 3D del simulatore (officina).", "rm": "Ils maletgs mussan il model 3D dal simulatur (ufficina)."},
    "Übersicht (zerlegt)": {"en": "Overview (exploded)", "fr": "Vue d'ensemble (éclatée)", "it": "Panoramica (esploso)", "rm": "Survista (decumponì)"},
    "Nicht geprüft": {"en": "Not tested", "fr": "Non testé", "it": "Non verificato", "rm": "Betg verifitgà"},
    "Gehäuse v5.2 ist berechnet und am Modell geprüft, aber noch nicht gedruckt und nicht mit echten Teilen zusammengebaut. Masse mit «Nachmessen» vor dem Druck prüfen.":
        {"en": "Case v5.2 is calculated and checked on the model, but not yet printed and not assembled with real parts. Check the «measure first» dimensions before printing.",
         "fr": "Le boîtier v5.2 est calculé et vérifié sur le modèle, mais pas encore imprimé ni monté avec de vraies pièces. Vérifier les cotes «à mesurer» avant l'impression.",
         "it": "La custodia v5.2 è calcolata e verificata sul modello, ma non ancora stampata né montata con pezzi veri. Verificare le misure «da misurare» prima della stampa.",
         "rm": "La chascha v5.2 è calculada e verifitgada vi dal model, ma anc betg stampada e betg montada cun parts veras. Controllar las mesiras «mesirar» avant la stampa."},
    # Installation aus dem Paket
    "Mit diesem Paket": {"en": "With this package", "fr": "Avec ce kit", "it": "Con questo pacchetto", "rm": "Cun quest pachet"},
    "Ordner 4_Software auf den Pi kopieren": {"en": "Copy the folder 4_Software to the Pi", "fr": "Copier le dossier 4_Software sur le Pi", "it": "Copiare la cartella 4_Software sul Pi", "rm": "Copiar l'ordinatur 4_Software sin il Pi"},
    "Mit USB-Stick oder vom PC aus mit scp (Benutzer und IP anpassen).": {"en": "With a USB stick or from the PC with scp (adjust user and IP).", "fr": "Avec une clé USB ou depuis le PC avec scp (adapter utilisateur et IP).", "it": "Con una chiavetta USB o dal PC con scp (adattare utente e IP).", "rm": "Cun in stick USB u dal PC cun scp (adattar utilisader ed IP)."},
    "Einrichten (ohne sudo)": {"en": "Set up (without sudo)", "fr": "Installer (sans sudo)", "it": "Installare (senza sudo)", "rm": "Installar (senza sudo)"},
    "Das Skript nimmt die MoveEye-Datei, die Zusatzdatei und versions.json aus diesem Ordner (signiert, kein Internet nötig für MoveEye selbst), installiert die Pakete, schaltet I2C, SPI und Kamera ein, richtet den Dienst ein und macht den Selbsttest. Zuerst mit --trocken ansehen.":
        {"en": "The script takes the MoveEye file, the data file and versions.json from this folder (signed, MoveEye itself needs no internet), installs the packages, switches on I2C, SPI and the camera, sets up the service and runs the self-test. Look first with --trocken.",
         "fr": "Le script prend le fichier MoveEye, le fichier de données et versions.json de ce dossier (signés, MoveEye lui-même n'a pas besoin d'internet), installe les paquets, active I2C, SPI et la caméra, crée le service et fait l'autotest. D'abord regarder avec --trocken.",
         "it": "Lo script prende il file MoveEye, il file dati e versions.json da questa cartella (firmati, MoveEye stesso non ha bisogno di internet), installa i pacchetti, attiva I2C, SPI e la fotocamera, crea il servizio e fa l'autotest. Prima guardare con --trocken.",
         "rm": "Il script prenda la datoteca MoveEye, la datoteca da datas e versions.json ord quest ordinatur (signadas, MoveEye sez na dovra betg internet), installescha ils pachets, activescha I2C, SPI e la camera, installescha il servetsch e fa l'autotest. L'emprim guardar cun --trocken."},
    "Ohne dieses Paket": {"en": "Without this package", "fr": "Sans ce kit", "it": "Senza questo pacchetto", "rm": "Senza quest pachet"},
    "Weiter wie in der Liste": {"en": "Then as in the list", "fr": "Ensuite comme dans la liste", "it": "Poi come nella lista", "rm": "Lura sco en la glista"},
    "Ausführlich (Pakete von Hand, Autostart, Tailscale): 4_Software/Einrichtung_Raspberry_Pi.md.": {"en": "In detail (packages by hand, autostart, Tailscale): 4_Software/Einrichtung_Raspberry_Pi.md (German).", "fr": "En détail (paquets à la main, démarrage auto, Tailscale) : 4_Software/Einrichtung_Raspberry_Pi.md (en allemand).", "it": "In dettaglio (pacchetti a mano, avvio automatico, Tailscale): 4_Software/Einrichtung_Raspberry_Pi.md (in tedesco).", "rm": "En detagl (pachets a maun, autostart, Tailscale): 4_Software/Einrichtung_Raspberry_Pi.md (per tudestg)."},
    "Software im Paket": {"en": "Software in the package", "fr": "Logiciel dans le kit", "it": "Software nel pacchetto", "rm": "Software en il pachet"},
    "signiert": {"en": "signed", "fr": "signé", "it": "firmato", "rm": "signà"},
    "NICHT signiert (Testpaket)": {"en": "NOT signed (test package)", "fr": "NON signé (kit de test)", "it": "NON firmato (pacchetto di prova)", "rm": "BETG signà (pachet da test)"},
}


def tx(de, L, *a):
    s = de if L == "de" else (TX.get(de, {}).get(L) or TX.get(de, {}).get("en") or de)
    return (s % a) if a else s


_EMOJI = re.compile("[\U0001F000-\U0001FAFF\uFE0F\u200D]+ ?")


def clean(s, L="de"):
    s = _EMOJI.sub("", str(s))
    return s.replace("\u00df", "ss") if L == "de" else s


def ohne_qr(s):
    """Sätze, die auf den QR-Code der Web-Seite zeigen, gibt es im Papier nicht"""
    return " ".join(x for x in re.split(r"(?<=[.!?])\s+", s) if "QR" not in x)


def lx(v, L):
    """ein Feld aus bau.json in Sprache L (wie gx im Web: rm -> de, sonst -> en)"""
    if v is None:
        return ""
    if isinstance(v, str):
        return clean(v, L)
    return clean(v.get(L) or (v.get("de") if L == "rm" else v.get("en")) or v.get("de") or "", L)


def esc(s):
    return html.escape(str(s), quote=True)


# ---- Daten ------------------------------------------------------------------------------------------------------------------
def lade():
    B = json.load(open(os.path.join(GEH, "bau.json"), encoding="utf-8"))
    K = json.load(open(os.path.join(R, "simulator3d", "fehler_katalog.json"), encoding="utf-8"))
    M = json.load(open(os.path.join(R, "simulator3d", "inhalte", "gehaeuse", "modelle.json"), encoding="utf-8"))
    src = open(os.path.join(R, "quelle", "010_grundlagen.py"), encoding="utf-8").read()
    ver = re.search(r'^APP_VERSION = "([0-9.]+)"', src, re.M).group(1)
    return B, K, M, ver


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def release_dateien(ver, unsigniert):
    """die Release-Dateien dieser Version aus dem Repository-Stamm, gegen versions.json geprüft"""
    u = ver.replace(".", "_")
    py, zd = os.path.join(R, "webcam_bewegung_%s.py" % u), os.path.join(R, "moveeye_daten_%s.zip" % u)
    vj = os.path.join(R, "versions.json")
    for p in (py, zd, vj):
        if not os.path.isfile(p):
            sys.exit("fehlt: %s (zuerst bauen.py)" % os.path.relpath(p, R))
    e = next((x for x in json.load(open(vj, encoding="utf-8")).get("versions") or [] if x.get("version") == ver), None)
    signiert = bool(e and e.get("sig") and e.get("sha256") == sha(py) and isinstance(e.get("data"), dict)
                    and e["data"].get("sig") and e["data"].get("sha256") == sha(zd))
    if not signiert and not unsigniert:
        sys.exit("versions.json: %s nicht (passend) signiert – erst «bauen.py --signieren», oder --unsigniert zum Testen" % ver)
    return py, zd, vj, signiert


# ---- Auswahl der Teile (Standard v5.2) --------------------------------------------------------------------------------------
# neue Teile v5.2 ohne Vorgänger: in welchem Montageschritt sie im Bild erscheinen (Lage laut LIESMICH_Montage_v5-2.md)
SCHRITT_V52 = {"wide": 3, "irled": 3, "lampdrv": 6, "fuseh": 7, "buttons": 7, "resplug": 7, "sled": 10, "diff52": 10,
               "sdplug": 13, "cable_cam1": 13}
# Bedingungen («wenn») in den Standard-Paketen: v5.2, mit oder ohne Akku; nicht: v5.1, Entwicklung, Mover
STANDARD_WENN = {None, "", "v52", "ups", "netz"}


def wenn_tag(w, L):
    return {"ups": tx("nur mit Akku (Autark)", L), "netz": tx("nur ohne Akku (Basis, Komplett)", L)}.get(w, "")


def druckteile52(B):
    """Druckteile der Standard-Pakete v5.2: v5.1-Teile, die v5.2 ersetzt (gleiche Nummer), fallen weg"""
    T = (B.get("druck") or {}).get("teile") or []
    nr52 = {p["datei"][:2] for p in T if p.get("wenn") == "v52"}
    out = [p for p in T if (not p.get("wenn") and p["datei"][:2] not in nr52) or p.get("wenn") == "v52"]
    return sorted(out, key=lambda p: p["datei"])


def druck_farbe(B, datei):
    kopf = set((B.get("farben") or {}).get("kopf_teile") or [])
    ids = [t["id"] for t in B.get("teile") or [] if t.get("datei") == datei]
    if "14_" in datei[:3]:
        return "natur/weiss"
    if "15_" in datei[:3]:
        return "schwarz"
    return "orange" if any(i in kopf for i in ids) else "grau"


def druck_datei52(datei):
    return "MoveEye_v5-2_%s.3mf" % datei


def teil_name(B, datei, L):
    t = next((x for x in B.get("teile") or [] if x.get("datei") == datei and x.get("name")), None)
    return lx(t["name"], L) if t else datei.replace("_", " ")


# ---- 3D-Bilder (three.js in Chromium) ---------------------------------------------------------------------------------------
RENDER_HTML = r"""<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#fff}</style>
<script type="importmap">{"imports":{"three":"./three/three.module.min.js","three/addons/":"./three/"}}</script></head>
<body><script type="module">
import * as THREE from "three";
import {GLTFLoader} from "three/addons/loaders/GLTFLoader.js";
const W = 1200, H = 760;
const renderer = new THREE.WebGLRenderer({antialias: true, preserveDrawingBuffer: true});
renderer.setPixelRatio(1); renderer.setSize(W, H); document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color("#f2f4f7");
scene.add(new THREE.HemisphereLight(0xffffff, 0x8a94a3, 1.25));
const sun = new THREE.DirectionalLight(0xffffff, 1.5); sun.position.set(-0.5, 1.0, 0.6); scene.add(sun);
const fill = new THREE.DirectionalLight(0xffffff, 0.6); fill.position.set(0.6, 0.4, -0.8); scene.add(fill);
const cam = new THREE.PerspectiveCamera(32, W / H, 0.005, 10);
const parts = {};
window.R = {fehler: ""};
new GLTFLoader().load("./gehaeuse.glb", g => {
  g.scene.traverse(o => { if (o.isMesh) { o.material = o.material.clone(); o.material.side = THREE.DoubleSide; o.material.roughness = 0.65; o.material.metalness = 0; parts[o.name] = o; } });
  scene.add(g.scene); g.scene.updateMatrixWorld(true);
  window.R.teile = Object.keys(parts);
}, undefined, e => { window.R.fehler = String(e && e.message || e); });
// spec: {zeigen: [id], hi: [id], farbe: {id: "#hex"}, versatz: {id: [x,y,z]}, yaw, pitch, rand}
window.R.bild = spec => {
  const box = new THREE.Box3();
  for (const id in parts) {
    const m = parts[id], on = spec.zeigen.includes(id); m.visible = on;
    const v = (spec.versatz || {})[id] || [0, 0, 0]; m.position.set(v[0], v[1], v[2]);
    const f = (spec.farbe || {})[id]; if (f) m.material.color.set(f);
    const hi = (spec.hi || []).includes(id);
    m.material.emissive.set(hi ? 0x2f6fe0 : 0x000000); m.material.emissiveIntensity = hi ? 0.5 : 0;
    m.updateMatrixWorld(true); if (on) box.expandByObject(m);
  }
  const c = box.getCenter(new THREE.Vector3()), r = box.getSize(new THREE.Vector3()).length() / 2 || 0.1;
  const y = spec.yaw * Math.PI / 180, p = spec.pitch * Math.PI / 180;
  const d = r / Math.sin(cam.fov * Math.PI / 360) * (spec.rand || 0.92);
  cam.position.set(c.x + d * Math.cos(p) * Math.sin(y), c.y + d * Math.sin(p), c.z + d * Math.cos(p) * Math.cos(y));
  cam.lookAt(c); cam.updateProjectionMatrix();
  renderer.render(scene, cam);
  return renderer.domElement.toDataURL("image/jpeg", 0.86);
};
</script></body></html>"""


def bild_specs(B, M):
    """welche Teile in welchem Bild: Schritt n zeigt alles bis n, die Teile von n hervorgehoben und leicht abgehoben"""
    E = {e["id"]: e for e in M.get("teile") or []}
    T = {t["id"]: t for t in B.get("teile") or []}
    ers = dict((M.get("v52") or {}).get("ersetzt") or {})
    dev_ers = {k: v for k, v in ers.items() if k == "sockel"}
    ers = {k: v for k, v in ers.items() if k != "sockel"}
    alt_weg = set(ers.values())
    F = B.get("farben") or {}
    kopf = set(F.get("kopf_teile") or [])
    grau = F.get("grau") or "#6d7074"                    # ein Grau für alle (bau.json «farben»), wie Szene und Werkstatt
    farbe = {}
    for i, t in T.items():
        if t.get("datei") or t.get("art") == "druck":
            farbe[i] = (F.get("kopf") or "#f59a4a") if i in kopf else ("#f4f1ea" if i == "diff52" else grau)
    farbe["sockel"] = grau
    schritt, druck = {}, set()
    for i, t in T.items():
        if i in alt_weg or t.get("art") == "dev" or i not in E or t.get("ohne"):   # «ohne»: 12 Blindstopfen (nur ohne Weitwinkel)
            continue
        if i in ers:
            s = (T.get(ers[i]) or {}).get("schritt")
            if (T.get(ers[i]) or {}).get("art") == "druck":
                druck.add(i)
        elif t.get("art") == "v52":
            s = SCHRITT_V52.get(i)
        else:
            s = t.get("schritt")
        if t.get("art") == "druck" or (t.get("art") == "v52" and t.get("datei")):
            druck.add(i)
        if s:
            schritt[i] = s
    N = len(B.get("schritte") or [])

    def ex(i, k):
        e = (E.get(i) or {}).get("explosion") or [0, 0, 0]
        return [e[0] * k, e[1] * k, e[2] * k]

    specs = {}
    alle = sorted(schritt)
    specs["gesamt"] = {"zeigen": alle, "yaw": 145, "pitch": 22, "farbe": farbe}
    specs["explosion"] = {"zeigen": alle, "yaw": 145, "pitch": 22, "farbe": farbe, "versatz": {i: ex(i, 1.0) for i in alle}}
    dr = sorted(druck)
    specs["s1"] = {"zeigen": dr, "yaw": 145, "pitch": 30, "farbe": farbe, "versatz": {i: ex(i, 1.0) for i in dr}}
    for n in range(2, N + 1):
        zeig = [i for i in alle if schritt[i] <= n]
        cur = [i for i in zeig if schritt[i] == n] if n < N else []
        if len(cur) == len(zeig):   # Schritt 2: alles ist neu - nichts hervorheben
            cur = []
        vs = {i: [a + b for a, b in zip(ex(i, 0.3 if n < 9 else 0.15), [0, 0.015, 0])] for i in cur}
        innen = n <= 7
        specs["s%d" % n] = {"zeigen": zeig, "hi": cur, "versatz": vs, "farbe": farbe,
                            "yaw": 150 if innen else 145, "pitch": 52 if innen else 22}
    # Anhang Entwicklung: Schritt 4 mit dem Sockel statt UPS HAT
    if "sockel" in E:
        zeig = [i for i in alle if schritt[i] <= 4 and i not in dev_ers.values()] + ["sockel"]
        specs["dev"] = {"zeigen": zeig, "hi": ["sockel"], "versatz": {"sockel": [0, 0.02, 0]}, "farbe": farbe, "yaw": 150, "pitch": 52}
    return specs


def bilder_rendern(B, M, pw_browser):
    """{name: data-URL JPEG} – leer, wenn WebGL nicht geht"""
    specs = bild_specs(B, M)
    dateien = {
        "r.html": (RENDER_HTML.encode(), "text/html"),
        "gehaeuse.glb": (open(os.path.join(R, "simulator3d", "inhalte", "gehaeuse", "gehaeuse.glb"), "rb").read(), "model/gltf-binary"),
    }
    three = os.path.join(R, "werkzeuge", "three")

    def route(rt):
        p = urllib.parse.urlparse(rt.request.url).path.lstrip("/")
        if p in dateien:
            return rt.fulfill(body=dateien[p][0], content_type=dateien[p][1])
        if p.startswith("three/"):
            f = os.path.normpath(os.path.join(three, p[6:]))
            if f.startswith(three) and os.path.isfile(f):
                return rt.fulfill(body=open(f, "rb").read(), content_type="text/javascript")
        return rt.fulfill(status=404, body=b"")

    ctx = pw_browser.new_context(viewport={"width": 1200, "height": 760})
    pg = ctx.new_page()
    pg.route("http://bausatz.invalid/**", route)
    out = {}
    try:
        pg.goto("http://bausatz.invalid/r.html")
        pg.wait_for_function("window.R && (window.R.teile || window.R.fehler)", timeout=90000)
        f = pg.evaluate("window.R.fehler")
        if f:
            raise RuntimeError(f)
        for k, s in specs.items():
            out[k] = pg.evaluate("s => window.R.bild(s)", s)
    except Exception as e:  # noqa: BLE001 – ohne Bilder weiter
        print("  ! 3D-Bilder gehen nicht (%s) – Anleitung ohne Bilder" % str(e)[:200])
        out = {}
    ctx.close()
    return out


# ---- Bestellliste -----------------------------------------------------------------------------------------------------------
def such_link(B, b):
    h = (B.get("haendler") or {}).get(b.get("haendler")) or {}
    return h.get("name", ""), (h.get("suche") or "").replace("{q}", urllib.parse.quote_plus(b.get("suche") or ""))


def chf(n):
    return "%.2f" % (round(n * 20) / 20)


def paket_zeilen(B, p):
    BOM = {b["id"]: b for b in B.get("bom") or []}
    return [BOM[i] for i in p.get("bom") or [] if i in BOM], [BOM[i] for i in p.get("extras") or [] if i in BOM]


def csv_paket(B, p, L="de", ver=""):
    s = io.StringIO()
    w = csv.writer(s, delimiter=";", quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    if ver:
        w.writerow(["MoveEye – Bestellliste %s · Gehäuse v5.2 · Stand MoveEye %s" % (lx(p["name"], L), ver)])
    w.writerow(["Paket", "Gruppe", "Teil", "Menge", "Artikel-Nr.", "Händler", "Suchbegriff", "Link (Suche)", "Preis CHF (geschätzt)", "optional", "Alternative"])
    zeilen, extras = paket_zeilen(B, p)
    G = B.get("bom_gruppen") or {}
    for opt, liste in ((False, zeilen), (True, extras)):
        for b in liste:
            hn, url = such_link(B, b)
            w.writerow([lx(p["name"], L), lx(G.get(b.get("gruppe")), L), lx(b.get("name"), L), b.get("menge", ""), b.get("nr", ""), hn,
                        b.get("suche", ""), url, chf(b["preis"]) if b.get("preis") is not None else "", "x" if opt else "", lx(b.get("alt"), L)])
    summe = sum(b.get("preis") or 0 for b in zeilen)
    w.writerow(["", "", "Summe (geschätzt, ohne optionale Teile und Versand)", "", "", "", "", "", chf(summe), "", ""])
    return "\ufeff" + s.getvalue(), summe


# ---- Anleitung (HTML -> PDF) ------------------------------------------------------------------------------------------------
CSS = r"""
@page { size: A4; margin: 15mm 14mm 17mm 14mm; }
* { box-sizing: border-box; }
body { font-family: Inter, "DejaVu Sans", Arial, sans-serif; font-size: 9.6pt; line-height: 1.38; color: #1d2733; margin: 0; }
h1 { font-size: 21pt; margin: 0 0 2mm; color: #13202e; }
h2 { font-size: 14.5pt; margin: 0 0 3mm; padding-bottom: 1.5mm; border-bottom: 2px solid #f59a4a; color: #13202e; break-after: avoid; }
h3 { font-size: 11pt; margin: 4mm 0 1.5mm; break-after: avoid; }
section { break-before: page; }
section.first { break-before: auto; }
p { margin: 1mm 0 2mm; }
.mut { color: #5b6878; }
.klein { font-size: 8.2pt; }
table { border-collapse: collapse; width: 100%; margin: 1mm 0 3mm; font-size: 8.6pt; }
th, td { border-bottom: 1px solid #d9dee5; padding: 1.2mm 1.4mm; text-align: left; vertical-align: top; }
th { background: #eef1f5; font-weight: 600; }
td.z, th.z { text-align: right; white-space: nowrap; }
tr.summe td { font-weight: 700; border-top: 2px solid #1d2733; border-bottom: none; }
tr.gr td { background: #f7f8fa; font-weight: 600; color: #3a4757; }
tr { break-inside: avoid; }
a { color: #1f5fbf; text-decoration: none; }
.tag { display: inline-block; font-size: 7.6pt; background: #fff1e5; color: #9a4b0b; border-radius: 3px; padding: 0 1.2mm; margin-left: 1mm; }
.tag.u { background: #fff7d6; color: #7a5b00; }
.schritt { break-inside: avoid; margin: 0 0 4mm; display: grid; grid-template-columns: 9mm 1fr; column-gap: 2mm; }
.schritt .nr { width: 8mm; height: 8mm; border-radius: 50%; background: #f59a4a; color: #fff; font-weight: 700; text-align: center; line-height: 8mm; font-size: 11pt; }
.schritt b { font-size: 10.5pt; }
.schritt img { width: 100%; max-height: 92mm; object-fit: contain; border-radius: 2mm; margin-top: 1.5mm; display: block; }
.schritt .sc { color: #3a4757; font-size: 8.6pt; margin-top: .8mm; }
.titel { text-align: left; }
.titel .gross { width: 100%; border-radius: 3mm; margin: 4mm 0; }
.titel .ver { font-size: 12pt; color: #5b6878; }
.inhalt li { margin: .6mm 0; }
pre { background: #f2f4f7; border-radius: 1.5mm; padding: 2mm 2.5mm; font-family: "DejaVu Sans Mono", monospace; font-size: 8.2pt; white-space: pre-wrap; margin: 1mm 0 2mm; break-inside: avoid; }
ol.liste > li, ul.liste > li { margin: 0 0 2mm; break-inside: avoid; }
.kasten { border: 1px solid #f3c79d; background: #fff8f1; border-radius: 2mm; padding: 2mm 3mm; margin: 2mm 0 3mm; break-inside: avoid; }
.fx { break-inside: avoid; margin: 0 0 3mm; }
.fx b { font-size: 10pt; }
.fx ol { margin: 1mm 0 0 0; padding-left: 5mm; }
svg.plan { width: 100%; height: auto; border: 1px solid #d9dee5; border-radius: 2mm; background: #fbfcfd; }
.leg span { display: inline-block; margin-right: 3mm; font-size: 8pt; }
.leg i { display: inline-block; width: 3mm; height: 3mm; border-radius: 1mm; margin-right: 1mm; vertical-align: -.4mm; }
.zwei { display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }
.zwei img { width: 100%; border-radius: 2mm; }
"""

ART_COL = {"i2c": "#3b82f6", "pwm": "#f59e0b", "gpio": "#10b981", "strom": "#ef4444", "usb": "#8b5cf6", "csi": "#ec4899", "spi": "#14b8a6", "audio": "#a3a3a3"}


def ui(B, en, L):
    """Beschriftung aus bau.json ui_bauen / ui_mw (Schlüssel englisch)"""
    for x in B.get("ui_bauen") or []:
        if x.get("en") == en:
            return lx(x, L)
    v = (B.get("ui_mw") or {}).get(en)
    if v:
        return en if L == "en" else lx(v, L)
    return en


def img(bilder, k, alt=""):
    return '<img src="%s" alt="%s">' % (bilder[k], esc(alt)) if k in bilder else ""


def plan_svg(B, L):
    V = B.get("verkabelung") or {}
    K = {k: n for k, n in (V.get("knoten") or {}).items() if n.get("wenn") in STANDARD_WENN}
    out = ['<svg class="plan" viewBox="-1 -1 113 100" xmlns="http://www.w3.org/2000/svg">']
    for v in V.get("verbindungen") or []:
        if v.get("wenn") not in STANDARD_WENN or v["von"] not in K or v["nach"] not in K:
            continue
        a, b = K[v["von"]], K[v["nach"]]
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="0.45"%s/>' % (
            a["x"] + 7.5, a["y"] + 2.75, b["x"] + 7.5, b["y"] + 2.75, ART_COL.get(v["art"], "#888"),
            ' stroke-dasharray="1.2 0.8"' if v.get("unklar") or v.get("wenn") else ""))
    for k, n in K.items():
        nm = lx(n["name"], L)
        nm = nm if len(nm) <= 19 else nm[:18] + "…"
        out.append('<rect x="%s" y="%s" width="15" height="5.5" rx="1.2" fill="%s" stroke="#5b6878" stroke-width="0.25"/>' % (
            n["x"], n["y"], "#fff1e5" if n.get("wenn") else "#ffffff"))
        out.append('<text x="%.1f" y="%.1f" font-size="1.75" text-anchor="middle" font-family="Inter, DejaVu Sans, sans-serif" fill="#1d2733">%s</text>' % (
            n["x"] + 7.5, n["y"] + 3.4, esc(nm)))
    out.append("</svg>")
    return "".join(out)


def anleitung_html(B, K, ver, bilder, L, signiert, py_name, zd_name):
    D = []
    a = D.append
    G = B.get("bom_gruppen") or {}
    pakete = (B.get("pakete") or {}).get("liste") or []
    datum = time.strftime("%d.%m.%Y")
    T = lambda de, *x: esc(tx(de, L, *x))  # noqa: E731
    U = lambda en: esc(ui(B, en, L))  # noqa: E731
    X = lambda v: esc(lx(v, L))  # noqa: E731

    kap = [("uebersicht", U("Overview")), ("sicherheit", U("Safety")), ("einkauf", T("Bestellliste")), ("drucken", U("Printing")),
           ("montage", U("Assembly")), ("verkabeln", U("Wiring")), ("software", U("Software")), ("inbetrieb", U("Commissioning")),
           ("fehler", U("Troubleshooting")), ("wartung", U("Maintenance")), ("anhang", T("Anhang: Entwicklungs-Variante ohne Akku"))]
    # -- Titel
    a('<section class="first titel"><h1>%s</h1><div class="ver">%s · %s · %s · %s %s</div>' % (
        T("MoveEye – Bauanleitung"), T("Selbstbau-Paket"), T("Gehäuse v5.2 (Standard)"), esc(T("Stand MoveEye %s") % ver), T("Stand"), datum))
    if "gesamt" in bilder:
        a('<img class="gross" src="%s" alt="">' % bilder["gesamt"])
    a('<h3>%s</h3><ol class="inhalt">%s</ol>' % (T("Inhalt"), "".join('<li><a href="#%s">%s</a></li>' % (i, n) for i, n in kap)))
    a('<div class="kasten"><b>%s:</b> %s</div></section>' % (T("Nicht geprüft"), T("Gehäuse v5.2 ist berechnet und am Modell geprüft, aber noch nicht gedruckt und nicht mit echten Teilen zusammengebaut. Masse mit «Nachmessen» vor dem Druck prüfen.")))
    # -- Übersicht
    a('<section id="uebersicht"><h2>%s</h2>' % U("Overview"))
    a("<p>%s</p>" % X(B.get("gehaeuse_v52", {}).get("name")))
    a("<p><b>%s:</b> %s</p>" % (T("Masse"), X(B.get("masse"))))
    a('<h3>%s</h3><table><tr><th>%s</th><th>%s</th><th class="z">%s</th></tr>' % (T("Die drei Pakete"), T("Paket"), T("Was drin ist"), T("Summe (geschätzt)")))
    for p in pakete:
        z, _x = paket_zeilen(B, p)
        a('<tr><td><b>%s</b></td><td>%s</td><td class="z">CHF %s</td></tr>' % (X(p["name"]), X(p.get("text")), chf(sum(b.get("preis") or 0 for b in z))))
    a("</table>")
    if "explosion" in bilder:
        a("<h3>%s</h3>%s" % (T("Übersicht (zerlegt)"), img(bilder, "explosion")))
        a('<p class="mut klein">%s</p>' % T("Die Bilder zeigen das 3D-Modell aus dem Simulator (Werkstatt)."))
    a("<h3>%s</h3><ul>%s</ul></section>" % (U("Tools"), "".join("<li>%s</li>" % X(w) for w in B.get("werkzeug") or [])))
    # -- Sicherheit
    a('<section id="sicherheit"><h2>%s</h2><ul class="liste">' % U("Safety"))
    for s in B.get("sicherheit") or []:
        if s.get("wenn") in STANDARD_WENN:
            t = wenn_tag(s.get("wenn"), L)
            a("<li>%s%s</li>" % (X(s.get("text")), ' <span class="tag">%s</span>' % esc(t) if t else ""))
    a("</ul></section>")
    # -- Einkauf
    a('<section id="einkauf"><h2>%s</h2><p class="mut">%s</p>' % (T("Bestellliste"), T("Alle Preise sind Schätzungen in CHF ohne Versand (Stand %s) – im Shop prüfen. Die Links sind Suchlinks beim Händler.", (B.get("pakete") or {}).get("stand", ""))))
    for n, p in enumerate(pakete):
        zeilen, extras = paket_zeilen(B, p)
        a('<h3%s>%s %s</h3><p class="mut klein">%s</p>' % (' style="break-before:page"' if n else "", T("Paket"), X(p["name"]), X(p.get("text"))))
        a('<table><tr><th>%s</th><th class="z">%s</th><th>%s</th><th class="z">%s</th></tr>' % (U("Part"), U("Qty"), T("Händler / Suchbegriff"), T("Preis CHF")))
        gr = None
        for b in sorted(zeilen, key=lambda b: list(G).index(b["gruppe"]) if b.get("gruppe") in G else 99):
            if b.get("gruppe") != gr:
                gr = b.get("gruppe")
                a('<tr class="gr"><td colspan="4">%s</td></tr>' % X(G.get(gr)))
            hn, url = such_link(B, b)
            alt = lx(b.get("alt"), L)
            a('<tr><td>%s%s%s</td><td class="z">%s</td><td><a href="%s">%s</a>: %s</td><td class="z">%s</td></tr>' % (
                X(b.get("name")), ' <span class="mut">(%s)</span>' % esc(b["nr"]) if b.get("nr") else "",
                '<br><span class="mut klein">%s: %s</span>' % (U("Alternative"), esc(alt)) if alt else "",
                esc(b.get("menge", "")), esc(url), esc(hn), esc(b.get("suche", "")), chf(b.get("preis") or 0)))
        a('<tr class="summe"><td colspan="3">%s</td><td class="z">CHF %s</td></tr></table>' % (T("Summe (geschätzt)"), chf(sum(b.get("preis") or 0 for b in zeilen))))
        if extras:
            a('<p class="klein"><b>%s:</b> %s</p>' % (T("Optional (nicht in der Summe)"), "; ".join(
                "%s (CHF %s)" % (X(b.get("name")), chf(b.get("preis") or 0)) for b in extras)))
    a("</section>")
    # -- Drucken
    dt = druckteile52(B)
    a('<section id="drucken"><h2>%s</h2>' % U("Printing"))
    a("<p>%s</p>" % X(B.get("gehaeuse_v52", {}).get("hinweis")))
    a('<table><tr><th>%s</th><th>%s</th><th class="z">%s</th><th class="z">%s</th><th class="z">%s</th><th>%s</th><th>%s</th><th class="z">%s</th></tr>' % (
        U("Part"), T("Farbe"), U("pcs"), U("Infill"), U("Walls"), U("Layer"), U("lies on"), U("Print time")))
    h = 0
    for p in dt:
        h += p.get("zeit_h") or 0
        a('<tr><td>%s<br><span class="mut klein">%s</span></td><td>%s</td><td class="z">%s</td><td class="z">%s %%</td><td class="z">%s</td><td>%s mm%s</td><td class="klein">%s</td><td class="z">%s h</td></tr>' % (
            esc(teil_name(B, p["datei"], L)), esc(druck_datei52(p["datei"])), T(druck_farbe(B, p["datei"])), p.get("stueck", 1), p.get("fuellung", ""), p.get("waende", ""),
            esc(p.get("schicht", "")), " · Brim %s mm" % p["brim"] if p.get("brim") else "", X(p.get("liegt")), p.get("zeit_h", "")))
    a('<tr class="summe"><td colspan="7">%s</td><td class="z">%s</td></tr></table>' % (esc(lx((B.get("druck") or {}).get("zeit_hinweis"), L)), esc(ui(B, "about %s h", L) % round(h, 1))))
    a("<p>%s</p>" % T("Farben: alles, was sich dreht oder neigt (Drehteller, Gabel, Arm 2, Kopf, Seitendeckel, Lampenhalter), in Orange; Unterteil, Deckel, Zwischenboden, Füsse und Stopfen in Grau; Diffusor natur/weiss, Pupillenring schwarz."))
    a("<h3>%s</h3><ul>%s</ul>" % (U("Notes for the Bambu printer"), "".join("<li>%s</li>" % X(x) for x in (B.get("druck") or {}).get("hinweise") or [])))
    a('<h3>%s</h3><p class="klein">%s</p><table>' % (T("Stopfen je Paket"), T("Stopfen kommen in Öffnungen für Teile, die das Paket nicht hat. 17 (Reserve-Öffnung) braucht jedes Paket.")))
    for p in pakete:
        st = [teil_name(B, s, L) for s in p.get("stopfen") or []]
        a("<tr><td><b>%s</b></td><td>%s</td></tr>" % (X(p["name"]), esc(", ".join(st) if st else tx("keine weiteren", L))))
    a("</table>")
    nm = (B.get("gehaeuse_v52") or {}).get("nachmessen") or []
    if nm:
        a('<div class="kasten"><b>%s</b><ul>%s</ul></div>' % (T("Vor dem Druck nachmessen"), "".join("<li>%s</li>" % X(x) for x in nm)))
    a("</section>")
    # -- Montage
    a('<section id="montage"><h2>%s</h2><p class="mut klein">%s</p>' % (U("Assembly"), T("Bild: Teile dieses Schritts blau hervorgehoben und leicht abgehoben.") if bilder else ""))
    for s in B.get("schritte") or []:
        sc = " · ".join("%s %s" % (x["menge"], lx(x["was"], L)) for x in B.get("schrauben") or [] if x.get("schritt") == s["nr"] and x.get("wenn") in STANDARD_WENN)
        a('<div class="schritt"><div class="nr">%d</div><div><b>%s</b><div>%s</div>%s%s%s</div></div>' % (
            s["nr"], X(s.get("titel")), X(s.get("text")), '<div class="tag u">%s</div>' % X(s["unklar"]) if s.get("unklar") else "",
            '<div class="sc">%s: %s</div>' % (U("Screws"), esc(sc)) if sc else "", img(bilder, "s%d" % s["nr"])))
    a("<h3>%s</h3>" % T("Ergänzungen"))
    gesehen = set()
    for s in B.get("extra_schritte") or []:
        w = s.get("wenn")
        if w not in ("v52", "netz"):
            continue
        if w == "v52" and lx(s.get("titel"), "de") == "Variante v5.2":   # Überblick v5.1 -> v5.2: steht hier schon in den Schritten
            continue
        txt = lx(s.get("text"), L)
        if txt in gesehen:   # gleicher Text zweimal in bau.json (z. B. «SD-Karte (v5.2)»): nur einmal zeigen
            continue
        gesehen.add(txt)
        a('<div class="schritt"><div class="nr">+</div><div><b>%s</b>%s<div>%s</div>%s</div></div>' % (
            X(s.get("titel")), ' <span class="tag">%s</span>' % T("für Basis und Komplett (ohne Akku)") if w == "netz" else "", esc(txt),
            '<div class="tag u">%s</div>' % X(s["unklar"]) if s.get("unklar") else ""))
    a("</section>")
    # -- Verkabeln
    V = B.get("verkabelung") or {}
    Kn = V.get("knoten") or {}
    a('<section id="verkabeln"><h2>%s</h2><p class="mut klein">%s</p>%s' % (U("Wiring"), U("Pins and channels come from the MoveEye code and the docs. Unclear points are marked."), plan_svg(B, L)))
    a('<div class="leg">%s</div>' % "".join('<span><i style="background:%s"></i>%s</span>' % (c, "STROM" if k == "strom" and L == "de" else k.upper()) for k, c in ART_COL.items()))
    a('<table><tr><th>%s</th><th>%s</th></tr>' % (T("Verbindung"), T("Pins / Kanal")))
    for v in V.get("verbindungen") or []:
        w = v.get("wenn")
        if w not in STANDARD_WENN:
            continue
        tg = wenn_tag(w, L) or (tx("nur v5.2 mit dem Teil (Komplett, Autark)", L) if w == "v52" else "")
        a('<tr><td><i style="display:inline-block;width:2.6mm;height:2.6mm;border-radius:.8mm;background:%s;margin-right:1mm"></i><b>%s → %s</b>%s</td><td>%s%s</td></tr>' % (
            ART_COL.get(v["art"], "#888"), X((Kn.get(v["von"]) or {}).get("name")), X((Kn.get(v["nach"]) or {}).get("name")),
            ' <span class="tag">%s</span>' % esc(tg) if tg else "", X(v.get("pins")),
            ' <span class="tag u">⚠ %s: %s</span>' % (T("unklar"), X(v["unklar"])) if v.get("unklar") else ""))
    a("</table></section>")
    # -- Software
    sw = B.get("software") or []
    a('<section id="software"><h2>%s</h2>' % T("Installation auf dem Raspberry Pi"))
    a('<p><b>%s:</b> %s, %s (%s)</p>' % (T("Software im Paket"), esc(py_name), esc(zd_name), T("signiert") if signiert else T("NICHT signiert (Testpaket)")))
    a('<ol class="liste">')
    if sw:
        a("<li><b>%s</b><br>%s</li>" % (X(sw[0].get("titel")), X(sw[0].get("text"))))
    a("<li><b>%s</b><br>%s<pre>scp -r 4_Software pi@&lt;IP-des-Pi&gt;:~/MoveEye_Bausatz</pre></li>" % (T("Ordner 4_Software auf den Pi kopieren"), T("Mit USB-Stick oder vom PC aus mit scp (Benutzer und IP anpassen).")))
    a("<li><b>%s</b><br>%s<pre>cd ~/MoveEye_Bausatz\nbash werkzeuge/einrichten.sh --trocken\nbash werkzeuge/einrichten.sh</pre></li>" % (
        T("Einrichten (ohne sudo)"), T("Das Skript nimmt die MoveEye-Datei, die Zusatzdatei und versions.json aus diesem Ordner (signiert, kein Internet nötig für MoveEye selbst), installiert die Pakete, schaltet I2C, SPI und Kamera ein, richtet den Dienst ein und macht den Selbsttest. Zuerst mit --trocken ansehen.")))
    for s in sw[2:]:
        a("<li><b>%s</b><br>%s%s</li>" % (X(s.get("titel")), esc(ohne_qr(lx(s.get("text"), L))), "<pre>%s</pre>" % esc(s["befehl"]) if s.get("befehl") else ""))
    a("</ol>")
    if len(sw) > 1:
        a("<h3>%s</h3><p>%s</p><pre>%s</pre>" % (T("Ohne dieses Paket"), X(sw[1].get("text")), esc(sw[1].get("befehl", ""))))
    a('<p class="mut">%s</p></section>' % T("Ausführlich (Pakete von Hand, Autostart, Tailscale): 4_Software/Einrichtung_Raspberry_Pi.md."))
    # -- Inbetriebnahme
    a('<section id="inbetrieb"><h2>%s</h2><ol class="liste">' % U("Commissioning"))
    for s in B.get("inbetriebnahme") or []:
        a("<li><b>%s</b><br>%s</li>" % (X(s.get("titel")), X(s.get("text"))))
    a("</ol></section>")
    # -- Fehlersuche
    FK = {e["id"]: e for e in K.get("fehler") or []}
    a('<section id="fehler"><h2>%s</h2>' % U("Troubleshooting"))
    for i in B.get("fehlersuche") or []:
        e = FK.get(i)
        if not e:
            continue
        st = (e.get("schritte") or {})
        st = st.get(L) or (st.get("de") if L == "rm" else st.get("en")) or st.get("de") or []
        a('<div class="fx"><b>%s %s</b> <span class="mut klein">(%s)</span><div>%s</div><ol>%s</ol></div>' % (
            "⛔" if e.get("stufe") == "bad" else "⚠", X(e.get("titel")), esc(i), X(e.get("text")), "".join("<li>%s</li>" % esc(clean(x, L)) for x in st)))
    a("</section>")
    # -- Wartung
    a('<section id="wartung"><h2>%s</h2><p class="mut">%s</p><table><tr><th>%s</th><th>%s</th><th>%s</th></tr>' % (
        U("Maintenance"), U("What wears out and when to check"), T("Teil"), T("Wann"), T("Was tun")))
    for w in B.get("wartung") or []:
        if w.get("wenn") in STANDARD_WENN:
            t = wenn_tag(w.get("wenn"), L)
            a("<tr><td>%s%s</td><td>%s</td><td>%s</td></tr>" % (X(w.get("teil")), ' <span class="tag">%s</span>' % esc(t) if t else "", X(w.get("wann")), X(w.get("was"))))
    a("</table></section>")
    # -- Anhang Entwicklung
    a('<section id="anhang"><h2>%s</h2><p>%s</p>' % (T("Anhang: Entwicklungs-Variante ohne Akku"), T("Für Tests am Schreibtisch: Sockel 13 statt UPS HAT (E) und Akkus, der Pi läuft an seinem eigenen Netzteil.")))
    for s in B.get("extra_schritte") or []:
        if s.get("wenn") == "entwicklung":
            a('<div class="schritt"><div class="nr">4</div><div><b>%s</b><div>%s</div>%s</div></div>' % (X(s.get("titel")), X(s.get("text")), img(bilder, "dev")))
    plus = [b for b in B.get("bom") or [] if b.get("wenn") == "entwicklung"]
    weg = [b for b in B.get("bom") or [] if b.get("wenn") == "ups"]
    a('<h3>%s</h3><table>%s</table>' % (T("Zusätzlich kaufen"), "".join('<tr><td>%s</td><td class="z">%s</td><td class="z">CHF %s</td></tr>' % (X(b.get("name")), esc(b.get("menge", "")), chf(b.get("preis") or 0)) for b in plus)))
    a('<p><b>%s:</b> %s</p>' % (T("Weglassen"), esc(", ".join(lx(b.get("name"), L) for b in weg))))
    dev = [p for p in (B.get("druck") or {}).get("teile") or [] if p.get("wenn") == "entwicklung"]
    sc = [x for x in B.get("schrauben") or [] if x.get("wenn") == "entwicklung"]
    a('<p><b>%s:</b> %s%s</p></section>' % (T("Zusätzlich drucken"), esc(", ".join("%s (%s)" % (teil_name(B, p["datei"], L), druck_datei52(p["datei"])) for p in dev)),
                                          (" · " + U("Screws") + ": " + esc(", ".join("%s %s" % (x["menge"], lx(x["was"], L)) for x in sc))) if sc else ""))
    return '<!doctype html><html lang="%s"><head><meta charset="utf-8"><title>%s</title><style>%s</style></head><body>%s</body></html>' % (
        L, T("MoveEye – Bauanleitung"), CSS, "".join(D))


def pdf_aus_html(pw_browser, htm, ziel, fuss):
    ctx = pw_browser.new_context()
    pg = ctx.new_page()
    pg.set_content(htm, wait_until="load")
    pg.pdf(path=ziel, format="A4", print_background=True, display_header_footer=True, header_template="<span></span>",
           footer_template='<div style="font-size:7pt;color:#7a8696;width:100%%;padding:0 14mm;display:flex;justify-content:space-between;font-family:sans-serif">'
                           '<span>%s</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>' % esc(fuss),
           margin={"top": "15mm", "bottom": "17mm", "left": "14mm", "right": "14mm"})
    ctx.close()


# ---- Texte im Paket (Deutsch) -----------------------------------------------------------------------------------------------
def druck_liesmich(B, ver):
    L = "de"
    z = ["MoveEye – Druckdateien Gehäuse v5.2 · Stand MoveEye %s" % ver, "=" * 60, "",
         "Drucker: Bambu Lab X2D (andere Drucker gehen auch), 0,4-mm-Düse, Material PETG.",
         "Keine Stützen: alle Teile liegen schon richtig auf der Platte.",
         "Brim 5 mm nur bei Kopf (06), Gabel (04) und Seitendeckel (07).",
         "Farben: Kopfteile orange (alles, was sich dreht oder neigt: 03, 04, 05, 06, 07, 08), Rest grau;",
         "        Diffusor 14 natur/weiss (durchscheinend), Pupillenring 15 schwarz.", "",
         "Platten (alles fertig verteilt):",
         "  MotionWatch_v5-2_Platte_A_Unterteil.3mf      Unterteil, Zwischenboden, Stopfen, Füsse",
         "  MotionWatch_v5-2_Platte_B_Deckel_Kopf.3mf    Deckel, Drehteller, Gabel, Arm 2, Kopf, Seitendeckel, Lampenhalter, Diffusor, Pupillenring",
         "Einzelteile: MoveEye_v5-2_NN_*.3mf (zum Nachdrucken oder für andere Drucker).", "",
         "Teil                                   Stück  Füllung  Wände  Schicht      Brim   Farbe        ca. h"]
    for p in druckteile52(B):
        z.append("%-38s %5s  %5s %%  %5s  %-11s  %-5s  %-11s  %5s" % (
            p["datei"][:38], p.get("stueck", 1), p.get("fuellung", ""), p.get("waende", ""), str(p.get("schicht", "")) + " mm",
            ("%s mm" % p["brim"]) if p.get("brim") else "–", tx(druck_farbe(B, p["datei"]), L), p.get("zeit_h", "")))
    z += ["", "Hinweise:"] + ["  - " + lx(h, L) for h in (B.get("druck") or {}).get("hinweise") or []]
    z += ["", "Stopfen je Paket (17 Reserve-Öffnung immer):"]
    for p in (B.get("pakete") or {}).get("liste") or []:
        z.append("  %-9s %s" % (lx(p["name"], L) + ":", ", ".join(p.get("stopfen") or []) or "keine weiteren"))
    z += ["  18_Stopfen_Waermebild ist für einen Kopf ohne Wärmebild (später), 22 nur für die 5-mm-IR-LED (nicht im Paket).",
          "  13_Entwicklungs_Sockel nur für die Entwicklungs-Variante ohne Akku (Anhang der Anleitung).", "",
          "Vor dem Druck nachmessen:"] + ["  - " + lx(x, L) for x in (B.get("gehaeuse_v52") or {}).get("nachmessen") or []]
    z += ["", "Kleinteile (Stopfen, Diffusor) zuerst drucken und den Sitz probieren (Spiel 0,2 mm pro Seite).", ""]
    return "\r\n".join(clean(x) if x else "" for x in z)


def installation_txt(B, ver, py_name, zd_name, signiert):
    sw = B.get("software") or []
    z = ["MoveEye %s – Installation auf dem Raspberry Pi 5" % ver, "=" * 60, "",
         "Software in diesem Ordner: %s + %s + versions.json (%s)." % (py_name, zd_name, "signiert" if signiert else "NICHT signiert – Testpaket"), ""]
    if sw:
        z += ["1. " + lx(sw[0]["titel"], "de"), "   " + lx(sw[0]["text"], "de"), ""]
    z += ["2. Diesen Ordner (4_Software) auf den Pi kopieren, z. B. vom PC aus:",
          "     scp -r 4_Software pi@<IP-des-Pi>:~/MoveEye_Bausatz", "",
          "3. Auf dem Pi im Terminal (ohne sudo – das Skript fragt selbst nach dem Passwort):",
          "     cd ~/MoveEye_Bausatz", "     bash werkzeuge/einrichten.sh --trocken     # nur ansehen", "     bash werkzeuge/einrichten.sh", "",
          "   Das Skript kopiert MoveEye, die Zusatzdatei und versions.json nach ~/MoveEye, installiert die Pakete,",
          "   schaltet I2C, SPI und Kamera ein, richtet den Dienst ein, lädt das KI-Modell und macht den Selbsttest.", ""]
    n = 4
    for s in sw[2:]:
        z.append("%d. %s" % (n, lx(s["titel"], "de")))
        z.append("   " + ohne_qr(lx(s["text"], "de")))
        if s.get("befehl"):
            z += ["     " + x for x in s["befehl"].splitlines()]
        z.append("")
        n += 1
    if len(sw) > 1:
        z += ["Ohne dieses Paket (direkt von GitHub):"] + ["     " + x for x in sw[1].get("befehl", "").splitlines()] + [""]
    z += ["Ausführlich: Einrichtung_Raspberry_Pi.md (Pakete von Hand, Autostart, Updates, Tailscale).", ""]
    return "\r\n".join(clean(x) if x else "" for x in z)


def druck_ordner(ver):
    """der Druckordner im Bausatz mit Version (Wunsch Daniel 01.11.2026), z. B. 2_MoveEye_v5-2_Druck_3.46.1"""
    return "2_MoveEye_v5-2_Druck_%s" % ver


def liesmich(ver, sprachen, signiert):
    return "\r\n".join([
        "MoveEye %s – Selbstbau-Paket" % ver, "",
        "1_Anleitung      Bauanleitung (PDF): MoveEye_Bauanleitung_%s_de.pdf" % ver + ("; dazu " + ", ".join(s for s in sprachen if s != "de") if len(sprachen) > 1 else ""),
        "%s   3D-Druck Gehäuse v5.2 (3MF), Kurzanleitung LIESMICH_Druck.txt" % druck_ordner(ver),
        "3_Bestellliste   Teile je Paket (Basis / Komplett / Autark) als CSV, Preise geschätzt",
        "4_Software       MoveEye für den Raspberry Pi 5 (%s), Anleitung INSTALLATION.txt" % ("signiert" if signiert else "NICHT signiert, Testpaket"),
        "", "Anfangen: Anleitung lesen, Paket wählen, Teile bestellen, drucken, bauen, Software einrichten.",
        "Projekt: https://github.com/DonElektro/MotionWatch", ""])


# ---- Hauptteil --------------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="MoveEye-Selbstbau-Paket erzeugen")
    ap.add_argument("--aus", default=os.path.join(R, "ausgabe_bausatz"))
    ap.add_argument("--sprachen", default=",".join(SPRACHEN))
    ap.add_argument("--ohne-bilder", action="store_true")
    ap.add_argument("--fest", action="store_true", help="zusätzlich MoveEye_Bausatz.zip (fester Name)")
    ap.add_argument("--unsigniert", action="store_true", help="auch ohne passende Signatur (nur Test)")
    a = ap.parse_args()
    sprachen = [s for s in a.sprachen.split(",") if s in SPRACHEN] or ["de"]
    B, K, M, ver = lade()
    py, zd, vj, signiert = release_dateien(ver, a.unsigniert)
    os.makedirs(a.aus, exist_ok=True)
    name = "MoveEye_Bausatz_%s" % ver
    t0 = time.time()
    print("MoveEye-Bausatz %s (%s)" % (ver, "signiert" if signiert else "NICHT signiert"))
    from playwright.sync_api import sync_playwright
    pdfs = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        bilder = {} if a.ohne_bilder else bilder_rendern(B, M, br)
        print("  Bilder: %d (%.0f s)" % (len(bilder), time.time() - t0))
        for L in sprachen:
            ziel = os.path.join(a.aus, "MoveEye_Bauanleitung_%s_%s.pdf" % (ver, L))
            htm = anleitung_html(B, K, ver, bilder, L, signiert, os.path.basename(py), os.path.basename(zd))
            pdf_aus_html(br, htm, ziel, "MoveEye %s – %s" % (ver, tx("MoveEye – Bauanleitung", L).split("– ")[-1]))
            pdfs[L] = ziel
            print("  PDF %s: %d kB" % (L, os.path.getsize(ziel) // 1024))
        br.close()
    zp = os.path.join(a.aus, name + ".zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        w = lambda n, d: z.writestr(name + "/" + n, d)  # noqa: E731
        w("LIESMICH.txt", liesmich(ver, sprachen, signiert))
        for L, p in pdfs.items():
            z.write(p, name + "/1_Anleitung/" + os.path.basename(p), compress_type=zipfile.ZIP_STORED)
        druck = (B.get("druckdateien") or []) + (B.get("druckdateien_einzeln") or [])
        dd = druck_ordner(ver)                          # Ordner mit Version, die 3MF behalten ihre Namen
        for f in druck:
            if f.startswith("v5-2/") and os.path.isfile(os.path.join(GEH, "Druckdateien", f)):
                z.write(os.path.join(GEH, "Druckdateien", f), name + "/" + dd + "/" + f[5:], compress_type=zipfile.ZIP_STORED)
        w(dd + "/LIESMICH_Druck.txt", druck_liesmich(B, ver))
        for p in (B.get("pakete") or {}).get("liste") or []:
            c, _s = csv_paket(B, p, ver=ver)
            w("3_Bestellliste/MoveEye_Bestellliste_%s_%s.csv" % (lx(p["name"], "de"), ver), c)
        sw = name + "/4_Software/"
        z.write(py, sw + os.path.basename(py))
        z.write(zd, sw + os.path.basename(zd), compress_type=zipfile.ZIP_STORED)
        z.write(vj, sw + "versions.json")
        z.write(os.path.join(R, "werkzeuge", "einrichten.sh"), sw + "werkzeuge/einrichten.sh")
        z.write(os.path.join(R, "docs", "Einrichtung_Raspberry_Pi.md"), sw + "Einrichtung_Raspberry_Pi.md")
        w("4_Software/INSTALLATION.txt", installation_txt(B, ver, os.path.basename(py), os.path.basename(zd), signiert))
    print("  %s: %.1f MB (%.0f s)" % (os.path.basename(zp), os.path.getsize(zp) / 1e6, time.time() - t0))
    if a.fest:
        shutil.copyfile(zp, os.path.join(a.aus, "MoveEye_Bausatz.zip"))
        print("  MoveEye_Bausatz.zip (fester Name)")
    for p in pdfs.values():   # die PDF stecken im ZIP; ausserhalb nur die deutsche zum Ansehen behalten
        if not p.endswith("_de.pdf"):
            os.remove(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
