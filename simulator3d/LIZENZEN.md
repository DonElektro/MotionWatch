# Lizenzen der Inhalte im 3D-Simulator

Stand: 3.37 (November 2026)

## Figuren (Menschen) – `scripts/figur.gd`

Die Figuren mit Skelett (ab Grafik «mittel») sind **selbst gebaut**: Knochen (Skeleton3D), gehäuteter Körper und
Wärmebild-Temperaturen werden beim Start im Programmcode erzeugt. Es gibt **keine fremde Modell- oder Animationsdatei**,
also auch keine fremde Lizenz und keinen Namensnachweis. Die Bewegungen (Gehen, Rennen, Ducken, Kriechen, Stehen, Tragen)
kommen wie bisher aus `scripts/actor.gd`. Teil von MoveEye, gleiche Bedingungen wie der übrige Programmcode.

Geprüft und **nicht** verwendet (30.10.2026):

| Quelle | Lizenz | Warum nicht |
|---|---|---|
| Khronos glTF Sample Assets «CesiumMan», «RiggedFigure» | CC-BY 4.0 (Cesium, Markenhinweis) | nur ein Gang, kein Ducken / Kriechen / Tragen; Namensnachweis nötig |
| Quaternius «Universal Animation Library» | CC0 | nur über quaternius.com / itch.io – von diesem Rechner aus nicht erreichbar |
| three.js-Beispiele (Soldier, Xbot, Michelle) | Mixamo | Weitergabe der Modelle nicht frei erlaubt |

Wer später ein fertiges CC0-Modell (glTF/GLB) einbauen will: hier mit Quelle, Autor und Lizenz eintragen;
bei CC-BY zusätzlich den Namensnachweis in «Über MoveEye» und «Lies mich» aufnehmen.

## Klänge der Trailer (ab 01.11.2026) – `klang/`, `scripts/trailer_ton.gd`

Musik und Geräusche der beiden Trailer sind aus freien Aufnahmen gebaut (`werkzeuge/klang_bauen.py`): Streicher, Pauken,
Blech und Glockenspiel aus **VSCO-2 Community Edition** (Versilian Studios, CC0), Regen, Bach und Donner von **rubberduck**
(OpenGameArt, CC0) und **Fugue State Audio** (gemeinfrei), Schritte, Holz und Glocke von **Kenney** (CC0), Papier und Luftzug
von **Ben Burnes** (CC0); dazu eigene Synthese. Alles CC0 bzw. gemeinfrei, keine Namensnennung nötig. Datei für Datei mit
Repository und Commit: `klang/LIZENZEN.txt`.

## Spielton (ab 01.11.2026) – `klang/sp_*.ogg`, `scripts/klang.gd`

Klänge in Spielen und Geschichten (`werkzeuge/spielton_bauen.py`): Glockenspiel, Trompeten, Harfe, Flöte, Marimba, Streicher
und Pauke aus **VSCO-2 Community Edition** (CC0), Kleine Trommel und Becken aus der **Versilian Community Sample Library**
(VCSL, CC0), Schritte und Klick von **Kenney** (CC0), Knistern von **Ben Burnes** (CC0), Holz von **rubberduck** (CC0);
dazu eigene Synthese. Alles CC0, keine Namensnennung nötig. Datei für Datei: `klang/LIZENZEN.txt`, Abschnitt «Spielton».

## Figuren-Paket (ab 3D-4.56) – `pakete/figuren_v1.zip`, `scripts/figur_paket.gd`

Das nachladbare Figuren-Paket (nicht im Simulator-ZIP; Download aus dem Repository oder neben die .exe legen) ist aus
Figuren von **Quaternius** gebaut (`werkzeuge/figuren_paket.py`). Lizenz **CC0 1.0 Universal** (gemeinfrei,
<https://creativecommons.org/publicdomain/zero/1.0/>) – Nutzung und Weitergabe ohne Namensnennung erlaubt; wir nennen die
Quelle trotzdem: Quaternius (<https://quaternius.com>) «Universal Base Characters», «Modular Outfits Fantasy»,
«Universal Animation Library» 1 und 2.

## Menschen-Paket (ab 3.36, «Figuren menschlicher») – `pakete/menschen_v1.zip`, `scripts/figur_mensch.gd`

Nachladbar wie das Figuren-Paket (nicht im Simulator-ZIP). Gebaut mit `werkzeuge/menschen_paket.py` aus:

| Teil | Quelle | Lizenz |
|---|---|---|
| Grundkörper `3dobjs/base.obj` (MakeHuman «hm08»), Makro-Formen `targets/macrodetails` (Geschlecht, Alter, Muskeln, Gewicht, Grösse, Herkunft), Skelett `rigs/standard/rig.game_engine.json` + Gewichte, Masken `textures/mpfb_*.jpg` | MakeHuman / MPFB2, <https://github.com/makehumancommunity/mpfb2> (Ordner `src/mpfb/data`, Datei `LICENSE.ASSETS.md`); Rechteinhaber vor der Freigabe: Data Collection AB, Joel Palmius, Jonas Hauquier | **CC0 1.0 Universal** |
| Bewegungen `anim_1.glb`, `anim_2.glb` (aus `figuren_v1.zip` übernommen) | Quaternius «Universal Animation Library» 1 + 2, <https://quaternius.com> | **CC0 1.0 Universal** |
| Haare, Kleider, Schuhe, Kapuze, Augen, Brauen, Stoff- und Haar-Struktur | aus den Körpern berechnet (MoveEye) | wie der übrige Programmcode |

Der MPFB2-**Programmcode** (GPL) wird nicht verwendet, nur die freigegebenen Daten. Geprüft, aber von hier nicht
erreichbar (01.11.2026): pip / npm (keine Namensauflösung), quaternius.com, polyhaven.org, ambientcg.com.

## Maggie (Hund der Geschichte «Maggie und der Bergkristall») – `modelle/maggie_hund_glb.bin`, `scripts/maggie_modell.gd`

Ab Grafik «mittel» ist Maggie ein Modell mit Skelett. Grundlage: **Quaternius «Ultimate Animated Animals»** (Juli 2021),
Modell «ShibaInu» (`glTF/ShibaInu.gltf`, SHA-256 `3236979b…0f6b`), Lizenz **CC0 1.0 Universal** (gemeinfrei,
<https://creativecommons.org/publicdomain/zero/1.0/>) – Nutzung, Änderung und Weitergabe ohne Namensnennung erlaubt; wir
nennen die Quelle trotzdem: Quaternius (<https://quaternius.com>). Bezogen am 01.11.2026 aus einer öffentlichen
GitHub-Kopie des Pakets (laoniutoushx/TD-demo-2024-04-03; Prüfsumme gleich wie die Git-LFS-Datei in anderen Kopien, die
Lizenzdatei des Pakets liegt z. B. in francisb1996/brave-chicken-assets). Angepasst mit `werkzeuge/maggie_modell.py`
(Proportionen eines Jack Russell, Kippohren, Schwanz, Glätten, Maggies Muster, ohne Animationen). Fellstruktur und
Randlicht: `shaders/maggie_fell.gdshader` (selbst geschrieben). Mit Grafik «einfach» (Lite) baut `scripts/maggie_einfach.gd`
sie aus eigenen Grundformen (keine fremde Datei). Andere Hunde und Tiere sind unverändert.

## Fuchs mit Skelett und Pflanzen («Flora und Fauna», Phase 1, Zweig sim-flora-fauna) – `modelle/fuchs_glb.bin`, `scripts/tier_modell.gd`, `scripts/flora.gd`

Ab Stufe «Normal» (nicht Lite) ist der Fuchs ein Modell mit Skelett und eigenen Bewegungen (Gehen, Galopp, Sprung, Stehen,
Schnüffeln, Fressen). Grundlage: **Quaternius «Ultimate Animated Animals»** (Juli 2021), Modell «Fox» (`glTF/Fox.gltf`,
SHA-256 `2f36e3c9…64c7`), Lizenz **CC0 1.0 Universal** (gemeinfrei, <https://creativecommons.org/publicdomain/zero/1.0/>) –
dasselbe Paket wie Maggie, bezogen am 07.11.2026 aus derselben öffentlichen GitHub-Kopie (laoniutoushx/TD-demo-2024-04-03).
Angepasst mit `werkzeuge/tier_modelle.py` (ein Netz, Fell-Farben eines Rotfuchses als Vertex-Farben, weiche Normalen, nur die
gebrauchten Bewegungen). Fell: `shaders/maggie_fell.gdshader` (selbst geschrieben). Das Wärmebild kam bis Paket 2 aus den Grundformen, seit Paket 3 aus
einem Zwilling des Modells mit denselben Temperaturen.

## Tiere mit Skelett («Flora und Fauna», Paket 3 «Tiere echt», Zweig sim-flora-tiere) – `modelle/{reh,hund_husky,hund_shiba,katze,igel,fuchs}_glb.bin`

Ab Stufe «Normal» (nicht Lite, nicht im Prüfstand) sind Reh, Hund (Husky- und Shiba-Form in vier Farbschlägen), Katze
(vier Farbschläge), Igel und Fuchs Modelle mit Skelett. Grundlage: **Quaternius «Ultimate Animated Animals»** (Juli 2021),
Modelle «Deer» (`glTF/Deer.gltf`, SHA-256 `b8afd064…7e7333`), «Husky» (`glTF/Husky.gltf`, `0cfd85dd…0f8d97`), «ShibaInu»
(`3236979b…0f6b`) und «Fox» (`2f36e3c9…64c7`), Lizenz **CC0 1.0 Universal** (gemeinfrei,
<https://creativecommons.org/publicdomain/zero/1.0/>), bezogen am 08.11.2026 aus derselben öffentlichen GitHub-Kopie
(laoniutoushx/TD-demo-2024-04-03). Katze und Igel sind mit `werkzeuge/tier_modelle.py` aus dem Fuchs umgeformt (Knochenlängen,
Dicke, kürzere Schnauze; Igel-Stacheln im Code erzeugt), alle Fell-Farben, das Rehbock-Gehörn (`scripts/tier_modell.gd`) und
das Wärmebild der Modelle (`shaders/thermal_tier.gdshader`) sind selbst gebaut.

Schritt 2 (Zweig sim-flora-tiere2): Wolf aus «Wolf» (`glTF/Wolf.gltf`, SHA-256 `cc02e9d1…37d415`, CC0, gleiche Quelle),
Wildschwein aus dem Wolf, Dachs und Feldhase aus dem Fuchs umgeformt (`werkzeuge/tier_modelle.py`) –
`modelle/{wolf,wildschwein,dachs,hase}_glb.bin`. Die Vögel (Krähe, Elster, Möwe, Ringeltaube, Schwarm-Vögel,
`scripts/vogel_modell.gd`) sind im Code gebaut, keine fremde Datei. Im Pi-Paket (Lite) fehlen die neuen Modell-Dateien
(`export_presets.cfg`, «Linux Pi»): dort bleiben die Grundformen.

Blatt- und Nadelbilder der Baumkronen, Blätterbüschel, Gras-Farben (`scripts/flora.gd`, `shaders/blatt_karten.gdshader`,
`shaders/foliage.gdshader`, `shaders/gras_halme.gdshader`): **selbst gebaut**, beim Start im Code erzeugt, keine fremde Datei.
Der Wiesenboden nutzt die eigenen Fotos von Elektro (`texturen/wiese_alp_01.jpg`, `texturen/wiese_alp_steinig_01.jpg`,
Abschnitt «Foto-Texturen im Bergtal»).

Bäume und Sträucher mit Ästen («Flora und Fauna», Paket 1, Zweig sim-flora-baeume: Fichte, Tanne, Lärche, Kiefer, Arve, Legföhre,
Buche, Ahorn, Esche, Eiche, Birke, Obstbaum, Hasel, Holunder, Alpenrose, Blätter auf Hecken –
`scripts/baeume.gd`, `shaders/rinde.gdshader`, `shaders/baum_karten.gdshader`, `shaders/baum_fern.gdshader`): **selbst gebaut**.
Äste, Rinde und Zweig-Bilder entstehen im Code; die Ferne-Bilder `texturen/flora_fern_<art>.png` (zwölf Bilder, zusammen
~1.2 MB) sind mit `werkzeuge/flora_fernbilder.gd` aus genau diesen Bäumen gerendert.
Keine fremde Datei.

Wege und Strassen («Wege und Strassen», Zweig sim-wege: Asphalt mit Rissen, Flicken, Markierung, Schachtdeckeln, Bankett,
Randsteine, Feldwege mit Fahrspuren und Steinen – `scripts/wege.gd`, `shaders/strasse.gdshader`, `shaders/feldweg.gdshader`):
**selbst gebaut**, alles Muster im Shader aus dem Ort gerechnet. Die Asphalt-Struktur nutzt das eigene Foto von Elektro
`texturen/weg_asphalt_01.jpg` (Abschnitt «Foto-Texturen im Bergtal»). Keine fremde Datei, keine Marken oder Logos.
Dazu (Schritt 2): Wanderwege, Stufen, Wegweiser und Pfosten mit Raute (`shaders/wanderweg.gdshader`, `shaders/wege_laub.gdshaderinc`),
Leitpfosten, Strassenlampen, Bank, Leitplanke, Zaun, Hundekot-Kasten (Robidog-artig, ohne Marke) und Briefkasten – ebenfalls im
Code gebaut; die Orts- und Zielnamen auf den Wegweisern sind erfunden.

## Foto-Texturen im Bergtal (ab 3.37) – `texturen/`, `scripts/bergtal_texturen.gd`

Die Foto-Texturen (Wiese, Alpweide, Geröll, Alpenrosen, Kalkfels, Felsplatten, Wald von oben, Seegrund, Asphalt) sind aus
**eigenen Fotos von Elektro** gebaut (Ausschnitte, nahtlos gemacht; Quellfoto und Ausschnitt je Datei in
`texturen/QUELLEN.txt`, aufbereitet mit `werkzeuge/texturen_bauen.py`). Verwendung im Simulator **mit seiner Erlaubnis** (01.11.2026).
Keine fremde Lizenz. Weitergabe der Bilder ausserhalb von MoveEye nur mit Zustimmung von Elektro.
Nicht benutzte Fotos liegen in `texturen/unbenutzt/` (nicht im Export).

## Übrige Inhalte

Gelände, Pflanzen, Gebäude, Tiere, Himmel, Töne und Texturen (ausser den Foto-Texturen oben) entstehen ebenfalls im Code (Formen, Rauschen,
Shader in `shaders/`). Kartendaten eines echten Orts kommen beim Laden von swisstopo / OpenStreetMap
(Nachweis in der Karte des Simulators).

**Draco-Entpacker** (`scripts/draco.gd`, ab Sim 3.66.0): eigene GDScript-Umsetzung nach dem veröffentlichten Draco-Datenformat
(Google Draco, Apache-2.0); kein fremder Code übernommen, keine Bibliothek beigelegt. Nötig für die 3D-Gebäude von swisstopo
(swissBUILDINGS3D © swisstopo, freie Nutzung mit Quellenangabe), die Draco-komprimiert geliefert werden.
