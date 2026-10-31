# Quellen und Lizenzen der Foto-Inhalte (Fotorealismus F2)

Stand: 31.10.2026 · gilt für das nachladbare Paket `MoveEye_Inhalte_F2.zip` und die Einzeldateien, die der Simulator
beim ersten Start der Szene «Camping-Platz» nach `user://inhalte/` lädt (`scripts/inhalte.gd`, Liste
`inhalte/katalog.json`). Das Paket liegt im Repository unter `pakete/MoveEye_Inhalte_F2.zip` (geladen von
raw.githubusercontent.com, Prüfsumme im Katalog); es ist **nicht** im Simulator-ZIP. Figuren-Paket (Quaternius, CC0): siehe `LIZENZEN.md`.

Alle Inhalte stehen unter **CC0 1.0 Universal** (gemeinfrei, <https://creativecommons.org/publicdomain/zero/1.0/>):
Nutzung, Änderung und Weitergabe – auch in einem verkauften Produkt – sind ohne Namensnennung erlaubt. Wir nennen die
Quellen trotzdem gerne.

| Inhalt | Verwendet für | Quelle | Asset | Auflösung | Seite |
|---|---|---|---|---|---|
| Himmel Tag | HDRI-Himmel bei Sonne | Poly Haven | rooitou_park | 1K (HDR) | <https://polyhaven.com/a/rooitou_park> |
| Himmel Dämmerung | HDRI-Himmel Morgen/Abend | Poly Haven | industrial_sunset_puresky | 2K (HDR) | <https://polyhaven.com/a/industrial_sunset_puresky> |
| Wiese | Boden (trockenere Stellen) | ambientCG | Ground037 | 1K JPG | <https://ambientcg.com/view?id=Ground037> |
| Rasen | Boden (sattes Gras) | ambientCG | Grass004 | 1K JPG | <https://ambientcg.com/view?id=Grass004> |
| Erde | ausgetretene Stellen vor Zelt und Grill | Poly Haven | brown_mud_leaves_01 | 1K JPG | <https://polyhaven.com/a/brown_mud_leaves_01> |
| Kies | Rand der Strasse | ambientCG | Gravel022 | 1K JPG | <https://ambientcg.com/view?id=Gravel022> |
| Asphalt | Strasse | Poly Haven (Rob Tuytel) | asphalt_02 | 1K JPG | <https://polyhaven.com/a/asphalt_02> |
| Rinde | Baumstämme, Holzstapel | Poly Haven | bark_brown_02 | 1K JPG | <https://polyhaven.com/a/bark_brown_02> |
| Holz | Bank, Holzkisten | ambientCG | Wood049 | 1K JPG | <https://ambientcg.com/view?id=Wood049> |
| Stein | Steine auf der Wiese | ambientCG | Rock023 | 1K JPG | <https://ambientcg.com/view?id=Rock023> |
| Zeltstoff | Gewebe-Struktur von Zelt und Vordach (Farbe bleibt) | Poly Haven | fabric_pattern_07 | 1K JPG (nur Normal + ARM) | <https://polyhaven.com/a/fabric_pattern_07> |

«ambientCG» = <https://ambientcg.com> (Lennart Demes, CC0). «Poly Haven» = <https://polyhaven.com> (CC0).

## Woher die Dateien beim Bau des ersten Pakets kamen (31.10.2026)

Von der Arbeitsumgebung aus waren polyhaven.com und ambientcg.com gesperrt. Darum stammen die Dateien des ersten Pakets aus
Spiegeln auf GitHub, die dieselben CC0-Originale enthalten:

- `rooitou_park_1k.hdr` – github.com/pmndrs/drei-assets (`hdri/`), unverändert.
- `industrial_sunset_puresky_2k.hdr` – github.com/godotengine/godot-demo-projects (`compute/texture/assets/polyhaven/`,
  dort mit Hinweis «downloaded from polyhaven.com, CC0»), unverändert.
- `asphalt_02_diff_1k.jpg`, `asphalt_02_rough_1k.jpg` – github.com/KhronosGroup/glTF-Sample-Assets
  (`Models/TrafficCone/glTF/`, LICENSE: «© 2020 PolyHaven, CC0 – Rob Tuytel for Asphalt 02 textures»), unverändert.
  Die Normal-Karte fehlte dort.
- `fabric_pattern_07_nor_gl_1k.jpg`, `fabric_pattern_07_arm_1k.jpg` – github.com/godotengine/godot-demo-projects
  (`3d/soft_body_physics/textures/polyhaven/`), unverändert.
- `Ground037_1K-JPG_*`, `Rock023_1K-JPG_*` – github.com/TokisanGames/Terrain3D (`project/demo/assets/textures/`), dort
  gepackt (Farbe + Höhe, Normal + Rauheit in je einem PNG); mit `werkzeuge/inhalte_paket.py` in die ambientCG-Namen zerlegt
  und als JPG gespeichert. Die Dateinamen stimmen mit den ambientCG-Kennungen überein; ein Lizenzhinweis steht im
  Terrain3D-Repository nicht – ambientCG veröffentlicht ausschliesslich CC0.

Die übrigen Dateien (Grass004, brown_mud_leaves_01, Gravel022, bark_brown_02, Wood049, Normal-Karte von asphalt_02) lädt der
Simulator beim ersten Start direkt von ambientCG / Poly Haven (oder `werkzeuge/inhalte_paket.py --laden ORDNER`).

## Nicht verwendet

- Quaternius (Pflanzen, CC0): quaternius.com war von hier nicht erreichbar; Pflanzen sind ein eigenes Paket.
- Source-2-Spiegel von ambientCG (github.com/MrBrax/…, github.com/patrickjnr/cc0-texture-pack): nur als kompilierte
  `.vtex_c` (Source-2-Format), nicht als Bilder.
