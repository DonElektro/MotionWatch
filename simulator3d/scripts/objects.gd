extends RefCounted
## 3D-3.86: alle Dinge, die die KI von MoveEye kennt (die 80 COCO-Klassen), als Gegenstände für das Inventar - einfach aus
## Grundformen gebaut, in echter Grösse, mit der Farbe, an der man sie erkennt. Menschen und die laufenden Tiere kommen aus
## den Besuchern (VISITOR_LIST); hier stehen die übrigen. Jeder Eintrag: Name, Kategorie, COCO-Name, Symbol, Teile, Hindernis.
## Teil: [Form, a, b, c, x, y, z, Farbe, Drehung x, y, z (Grad)]
##   b = Kiste (a × b × c) · c = Zylinder (Radius a, Höhe b, Radius unten c - 0 = wie oben) · s = Kugel (Radius a, Höhe b)
##   p = Prisma / Dach (a × b × c) · k = Kegel (Radius unten a, Höhe b)
## Wärme (für das Wärmebild): «w» im Eintrag = warm (Geräte), sonst kalt.

const CATS := [["people", "Menschen", "🚶"], ["animals", "Tiere", "🦊"], ["vehicles", "Fahrzeuge", "🚗"], ["street", "Draussen", "🚦"],
		["bags", "Sport & Gepäck", "🎒"], ["food", "Essen", "🍕"], ["home", "Haus", "🛋"]]

const OBJ := {
	# ---- vehicles -------------------------------------------------------------------------------------------------------
	"bicycle_static": {"n": "Velo (abgestellt)", "cat": "vehicles", "coco": "bicycle", "i": "🚲", "o": [1.8, 0.5], "p": [
		["c", 0.34, 0.04, 0, -0.55, 0.34, 0, "151515", 90, 90, 0], ["c", 0.34, 0.04, 0, 0.55, 0.34, 0, "151515", 90, 90, 0],
		["b", 1.0, 0.05, 0.05, 0, 0.62, 0, "b01818", 0, 0, 0], ["b", 0.05, 0.5, 0.05, -0.15, 0.6, 0, "b01818", 0, 0, 25],
		["b", 0.22, 0.05, 0.1, -0.25, 0.9, 0, "222222", 0, 0, 0], ["b", 0.05, 0.05, 0.5, 0.5, 0.95, 0, "333333", 0, 0, 0]]},
	"car_static": {"n": "Auto (parkiert)", "cat": "vehicles", "coco": "car", "i": "🚗", "o": [4.2, 1.9], "p": [
		["b", 4.2, 0.7, 1.8, 0, 0.6, 0, "2b5fa8", 0, 0, 0], ["b", 2.3, 0.6, 1.6, -0.2, 1.2, 0, "2b5fa8", 0, 0, 0],
		["b", 2.2, 0.45, 1.62, -0.2, 1.2, 0, "26323c", 0, 0, 0],
		["c", 0.33, 0.25, 0, 1.3, 0.33, 0.85, "111111", 90, 0, 0], ["c", 0.33, 0.25, 0, -1.3, 0.33, 0.85, "111111", 90, 0, 0],
		["c", 0.33, 0.25, 0, 1.3, 0.33, -0.85, "111111", 90, 0, 0], ["c", 0.33, 0.25, 0, -1.3, 0.33, -0.85, "111111", 90, 0, 0]]},
	"motorcycle": {"n": "Motorrad", "cat": "vehicles", "coco": "motorcycle", "i": "🏍", "o": [2.1, 0.7], "p": [
		["c", 0.32, 0.12, 0, -0.75, 0.32, 0, "111111", 90, 90, 0], ["c", 0.32, 0.12, 0, 0.75, 0.32, 0, "111111", 90, 90, 0],
		["b", 1.0, 0.35, 0.3, 0, 0.6, 0, "c0392b", 0, 0, 0], ["b", 0.6, 0.12, 0.3, -0.25, 0.85, 0, "202020", 0, 0, 0],
		["b", 0.06, 0.06, 0.7, 0.6, 1.05, 0, "999999", 0, 0, 0], ["b", 0.35, 0.3, 0.25, 0.1, 0.45, 0, "8a8a8a", 0, 0, 0]]},
	"bus": {"n": "Bus", "cat": "vehicles", "coco": "bus", "i": "🚌", "o": [11.0, 2.6], "p": [
		["b", 11.0, 2.6, 2.5, 0, 1.7, 0, "e8b21e", 0, 0, 0], ["b", 10.0, 0.9, 2.52, 0, 2.2, 0, "2a3540", 0, 0, 0],
		["c", 0.5, 0.3, 0, 3.6, 0.5, 1.2, "111111", 90, 0, 0], ["c", 0.5, 0.3, 0, -3.6, 0.5, 1.2, "111111", 90, 0, 0],
		["c", 0.5, 0.3, 0, 3.6, 0.5, -1.2, "111111", 90, 0, 0], ["c", 0.5, 0.3, 0, -3.6, 0.5, -1.2, "111111", 90, 0, 0]]},
	"truck": {"n": "Lastwagen", "cat": "vehicles", "coco": "truck", "i": "🚚", "o": [8.0, 2.5], "p": [
		["b", 2.2, 2.6, 2.4, 2.9, 1.7, 0, "c43c2c", 0, 0, 0], ["b", 5.6, 2.9, 2.5, -1.1, 2.0, 0, "d8d8d8", 0, 0, 0],
		["b", 0.1, 0.9, 2.2, 4.0, 2.2, 0, "26323c", 0, 0, 0],
		["c", 0.5, 0.35, 0, 2.9, 0.5, 1.15, "111111", 90, 0, 0], ["c", 0.5, 0.35, 0, -2.5, 0.5, 1.15, "111111", 90, 0, 0],
		["c", 0.5, 0.35, 0, 2.9, 0.5, -1.15, "111111", 90, 0, 0], ["c", 0.5, 0.35, 0, -2.5, 0.5, -1.15, "111111", 90, 0, 0]]},
	"train": {"n": "Eisenbahnwagen", "cat": "vehicles", "coco": "train", "i": "🚆", "o": [16.0, 3.0], "p": [
		["b", 16.0, 3.2, 2.9, 0, 2.3, 0, "b52025", 0, 0, 0], ["b", 15.0, 0.9, 2.92, 0, 2.7, 0, "2a3540", 0, 0, 0],
		["b", 16.0, 0.12, 1.5, 0, 0.06, 0, "6b5a46", 0, 0, 0], ["b", 3.0, 0.6, 2.2, 5.5, 0.5, 0, "222222", 0, 0, 0],
		["b", 3.0, 0.6, 2.2, -5.5, 0.5, 0, "222222", 0, 0, 0]]},
	"airplane": {"n": "Kleinflugzeug", "cat": "vehicles", "coco": "airplane", "i": "🛩", "o": [8.0, 9.0], "p": [
		["c", 0.6, 7.5, 0.45, 0, 1.3, 0, "f2f2f2", 0, 0, 90], ["b", 1.6, 0.12, 10.0, 0.6, 1.5, 0, "f2f2f2", 0, 0, 0],
		["b", 0.9, 1.4, 0.1, -3.4, 2.2, 0, "c0392b", 0, 0, 0], ["b", 0.8, 0.1, 3.0, -3.4, 1.5, 0, "f2f2f2", 0, 0, 0],
		["b", 0.1, 1.8, 0.15, 3.8, 1.3, 0, "333333", 0, 0, 0], ["c", 0.18, 0.7, 0, 0.6, 0.35, 0.9, "222222", 0, 0, 0],
		["c", 0.18, 0.7, 0, 0.6, 0.35, -0.9, "222222", 0, 0, 0]]},
	"boat": {"n": "Boot", "cat": "vehicles", "coco": "boat", "i": "🚤", "o": [4.5, 1.7], "p": [
		["b", 4.2, 0.6, 1.6, 0, 0.3, 0, "f0f0f0", 0, 0, 0], ["p", 1.6, 0.6, 1.0, 2.4, 0.3, 0, "f0f0f0", 0, 0, -90],
		["b", 4.2, 0.12, 1.62, 0, 0.55, 0, "1f5fa0", 0, 0, 0], ["b", 1.0, 0.5, 1.2, -0.5, 0.9, 0, "dddddd", 0, 0, 0]]},
	# ---- street / outside -----------------------------------------------------------------------------------------------
	"traffic_light": {"n": "Ampel", "cat": "street", "coco": "traffic light", "i": "🚦", "o": [0.3, 0.3], "p": [
		["c", 0.06, 2.6, 0, 0, 1.3, 0, "555555", 0, 0, 0], ["b", 0.32, 0.9, 0.28, 0, 2.95, 0, "1d1d1d", 0, 0, 0],
		["s", 0.09, 0.18, 0, 0, 3.25, 0.15, "e02020", 0, 0, 0], ["s", 0.09, 0.18, 0, 0, 2.95, 0.15, "e8b21e", 0, 0, 0],
		["s", 0.09, 0.18, 0, 0, 2.65, 0.15, "22c040", 0, 0, 0]]},
	"fire_hydrant": {"n": "Hydrant", "cat": "street", "coco": "fire hydrant", "i": "🧯", "o": [0.4, 0.4], "p": [
		["c", 0.14, 0.7, 0, 0, 0.35, 0, "c62020", 0, 0, 0], ["s", 0.15, 0.2, 0, 0, 0.72, 0, "c62020", 0, 0, 0],
		["c", 0.06, 0.3, 0, 0, 0.5, 0, "c62020", 90, 0, 0], ["c", 0.2, 0.06, 0, 0, 0.03, 0, "8a1515", 0, 0, 0]]},
	"stop_sign": {"n": "Stopp-Schild", "cat": "street", "coco": "stop sign", "i": "🛑", "o": [0.2, 0.2], "p": [
		["c", 0.04, 2.2, 0, 0, 1.1, 0, "9a9a9a", 0, 0, 0], ["c", 0.38, 0.04, 0, 0, 2.15, 0.03, "d01818", 90, 0, 0],
		["b", 0.5, 0.12, 0.01, 0, 2.15, 0.06, "ffffff", 0, 0, 0]]},
	"parking_meter": {"n": "Parkuhr", "cat": "street", "coco": "parking meter", "i": "🅿", "o": [0.3, 0.3], "p": [
		["c", 0.05, 1.1, 0, 0, 0.55, 0, "666666", 0, 0, 0], ["b", 0.25, 0.45, 0.2, 0, 1.3, 0, "3b4a5c", 0, 0, 0],
		["b", 0.16, 0.12, 0.01, 0, 1.38, 0.105, "c8e0f0", 0, 0, 0]]},
	"bench_static": {"n": "Parkbank", "cat": "street", "coco": "bench", "i": "🪑", "o": [1.8, 0.7], "p": [
		["b", 1.8, 0.06, 0.45, 0, 0.45, 0, "8a5a32", 0, 0, 0], ["b", 1.8, 0.4, 0.06, 0, 0.75, -0.22, "8a5a32", -12, 0, 0],
		["b", 0.06, 0.45, 0.5, -0.8, 0.22, 0, "333333", 0, 0, 0], ["b", 0.06, 0.45, 0.5, 0.8, 0.22, 0, "333333", 0, 0, 0]]},
	"potted_plant": {"n": "Topfpflanze", "cat": "street", "coco": "potted plant", "i": "🪴", "o": [0.5, 0.5], "p": [
		["c", 0.22, 0.4, 0.16, 0, 0.2, 0, "a0522d", 0, 0, 0], ["s", 0.32, 0.5, 0, 0, 0.62, 0, "3f8f2f", 0, 0, 0],
		["s", 0.2, 0.35, 0, 0.12, 0.85, 0.05, "4fa83a", 0, 0, 0]]},
	"umbrella": {"n": "Sonnenschirm", "cat": "street", "coco": "umbrella", "i": "⛱", "o": [0.3, 0.3], "p": [
		["c", 0.025, 2.2, 0, 0, 1.1, 0, "dddddd", 0, 0, 0], ["k", 1.2, 0.45, 0, 0, 2.15, 0, "d8392b", 0, 0, 0],
		["c", 0.3, 0.06, 0, 0, 0.03, 0, "444444", 0, 0, 0]]},
	"kite": {"n": "Drachen (im Baum / am Boden)", "cat": "bags", "coco": "kite", "i": "🪁", "o": null, "p": [
		["b", 0.7, 0.9, 0.02, 0, 1.6, 0, "e83e8c", 0, 0, 45], ["b", 0.02, 1.4, 0.02, 0, 0.8, 0, "dddddd", 0, 0, 10]]},
	# ---- animals that do not walk (yet) ---------------------------------------------------------------------------------
	"bird": {"n": "Vogel (sitzt)", "cat": "animals", "coco": "bird", "i": "🐦", "o": null, "w": true, "p": [
		["s", 0.09, 0.14, 0, 0, 0.1, 0, "5a4632", 0, 0, 0], ["s", 0.055, 0.1, 0, 0.08, 0.2, 0, "5a4632", 0, 0, 0],
		["k", 0.02, 0.05, 0, 0.14, 0.2, 0, "e0a020", 0, 0, -90], ["b", 0.12, 0.02, 0.05, -0.12, 0.12, 0, "4a3828", 0, 0, 20]]},
	"bear": {"n": "Bär", "cat": "animals", "coco": "bear", "i": "🐻", "o": [2.0, 0.9], "w": true, "p": [
		["s", 0.55, 0.9, 0, 0, 0.9, 0, "4a3020", 0, 0, 90], ["s", 0.3, 0.55, 0, 0.85, 1.05, 0, "4a3020", 0, 0, 0],
		["s", 0.12, 0.14, 0, 1.1, 0.98, 0, "6a4a30", 0, 0, 0], ["s", 0.08, 0.08, 0, 0.8, 1.32, 0.18, "3a2418", 0, 0, 0],
		["s", 0.08, 0.08, 0, 0.8, 1.32, -0.18, "3a2418", 0, 0, 0],
		["c", 0.14, 0.55, 0, 0.45, 0.28, 0.25, "3a2418", 0, 0, 0], ["c", 0.14, 0.55, 0, 0.45, 0.28, -0.25, "3a2418", 0, 0, 0],
		["c", 0.14, 0.55, 0, -0.45, 0.28, 0.25, "3a2418", 0, 0, 0], ["c", 0.14, 0.55, 0, -0.45, 0.28, -0.25, "3a2418", 0, 0, 0]]},
	"elephant": {"n": "Elefant", "cat": "animals", "coco": "elephant", "i": "🐘", "o": [4.0, 1.8], "w": true, "p": [
		["s", 1.3, 2.0, 0, 0, 2.0, 0, "8a8a8a", 0, 0, 90], ["s", 0.7, 1.2, 0, 1.6, 2.5, 0, "8a8a8a", 0, 0, 0],
		["c", 0.18, 1.6, 0.1, 2.15, 1.6, 0, "8a8a8a", 0, 0, 12], ["b", 0.08, 0.9, 0.8, 1.4, 2.6, 0.7, "7a7a7a", 0, 30, 0],
		["b", 0.08, 0.9, 0.8, 1.4, 2.6, -0.7, "7a7a7a", 0, -30, 0], ["k", 0.07, 0.6, 0, 2.0, 2.0, 0.3, "f2efe0", 0, 0, -70],
		["c", 0.32, 1.4, 0, 0.8, 0.7, 0.55, "7a7a7a", 0, 0, 0], ["c", 0.32, 1.4, 0, 0.8, 0.7, -0.55, "7a7a7a", 0, 0, 0],
		["c", 0.32, 1.4, 0, -0.8, 0.7, 0.55, "7a7a7a", 0, 0, 0], ["c", 0.32, 1.4, 0, -0.8, 0.7, -0.55, "7a7a7a", 0, 0, 0]]},
	"zebra": {"n": "Zebra", "cat": "animals", "coco": "zebra", "i": "🦓", "o": [2.2, 0.7], "w": true, "p": [
		["b", 1.6, 0.6, 0.5, 0, 1.2, 0, "f2f2f2", 0, 0, 0], ["b", 0.12, 0.62, 0.52, -0.5, 1.2, 0, "151515", 0, 0, 0],
		["b", 0.12, 0.62, 0.52, -0.1, 1.2, 0, "151515", 0, 0, 0], ["b", 0.12, 0.62, 0.52, 0.3, 1.2, 0, "151515", 0, 0, 0],
		["b", 0.3, 0.75, 0.25, 0.85, 1.65, 0, "f2f2f2", 0, 0, -30], ["b", 0.45, 0.25, 0.22, 1.15, 1.9, 0, "f2f2f2", 0, 0, 20],
		["c", 0.06, 0.95, 0, 0.6, 0.47, 0.18, "e8e8e8", 0, 0, 0], ["c", 0.06, 0.95, 0, 0.6, 0.47, -0.18, "e8e8e8", 0, 0, 0],
		["c", 0.06, 0.95, 0, -0.6, 0.47, 0.18, "e8e8e8", 0, 0, 0], ["c", 0.06, 0.95, 0, -0.6, 0.47, -0.18, "e8e8e8", 0, 0, 0]]},
	"giraffe": {"n": "Giraffe", "cat": "animals", "coco": "giraffe", "i": "🦒", "o": [2.2, 0.8], "w": true, "p": [
		["b", 1.5, 0.7, 0.6, 0, 2.0, 0, "d9a441", 0, 0, 0], ["b", 0.28, 2.0, 0.28, 0.65, 3.2, 0, "d9a441", 0, 0, -15],
		["b", 0.5, 0.28, 0.25, 1.05, 4.2, 0, "d9a441", 0, 0, 10], ["s", 0.12, 0.12, 0, 0.1, 2.2, 0.31, "7a4a1a", 0, 0, 0],
		["s", 0.12, 0.12, 0, -0.4, 1.9, 0.31, "7a4a1a", 0, 0, 0],
		["c", 0.07, 1.65, 0, 0.55, 0.82, 0.2, "c99431", 0, 0, 0], ["c", 0.07, 1.65, 0, 0.55, 0.82, -0.2, "c99431", 0, 0, 0],
		["c", 0.07, 1.65, 0, -0.55, 0.82, 0.2, "c99431", 0, 0, 0], ["c", 0.07, 1.65, 0, -0.55, 0.82, -0.2, "c99431", 0, 0, 0]]},
	# ---- bags & sport ---------------------------------------------------------------------------------------------------
	"backpack": {"n": "Rucksack", "cat": "bags", "coco": "backpack", "i": "🎒", "o": null, "p": [
		["b", 0.32, 0.5, 0.2, 0, 0.25, 0, "2f6f3f", 0, 0, 0], ["s", 0.16, 0.12, 0, 0, 0.5, 0, "2f6f3f", 0, 0, 0],
		["b", 0.24, 0.18, 0.06, 0, 0.18, 0.12, "285e35", 0, 0, 0]]},
	"handbag": {"n": "Handtasche", "cat": "bags", "coco": "handbag", "i": "👜", "o": null, "p": [
		["b", 0.32, 0.24, 0.12, 0, 0.12, 0, "8b3a3a", 0, 0, 0], ["c", 0.1, 0.02, 0, 0, 0.3, 0, "5a2525", 90, 0, 0]]},
	"suitcase": {"n": "Koffer", "cat": "bags", "coco": "suitcase", "i": "🧳", "o": [0.5, 0.3], "p": [
		["b", 0.45, 0.65, 0.25, 0, 0.36, 0, "34495e", 0, 0, 0], ["b", 0.18, 0.04, 0.04, 0, 0.72, 0, "222222", 0, 0, 0],
		["c", 0.03, 0.04, 0, 0.17, 0.03, 0, "111111", 90, 0, 0], ["c", 0.03, 0.04, 0, -0.17, 0.03, 0, "111111", 90, 0, 0]]},
	"tie": {"n": "Krawatte (an der Leine)", "cat": "bags", "coco": "tie", "i": "👔", "o": null, "p": [
		["b", 1.6, 0.01, 0.01, 0, 1.6, 0, "dddddd", 0, 0, 0], ["b", 0.1, 0.55, 0.01, 0, 1.32, 0, "1f3f8f", 0, 0, 0],
		["b", 0.06, 0.08, 0.02, 0, 1.6, 0, "1f3f8f", 0, 0, 0]]},
	"frisbee": {"n": "Frisbee", "cat": "bags", "coco": "frisbee", "i": "🥏", "o": null, "p": [["c", 0.13, 0.03, 0, 0, 0.02, 0, "f39c12", 0, 0, 0]]},
	"skis": {"n": "Ski (angelehnt)", "cat": "bags", "coco": "skis", "i": "🎿", "o": null, "p": [
		["b", 0.08, 1.7, 0.02, -0.05, 0.85, 0, "d63031", 10, 0, 0], ["b", 0.08, 1.7, 0.02, 0.05, 0.85, 0, "d63031", 10, 0, 0]]},
	"snowboard": {"n": "Snowboard", "cat": "bags", "coco": "snowboard", "i": "🏂", "o": null, "p": [["b", 0.28, 1.5, 0.02, 0, 0.75, 0, "6c5ce7", 12, 0, 0]]},
	"sports_ball": {"n": "Ball", "cat": "bags", "coco": "sports ball", "i": "⚽", "o": null, "p": [["s", 0.11, 0.22, 0, 0, 0.11, 0, "f5f5f5", 0, 0, 0],
		["s", 0.04, 0.04, 0, 0.08, 0.17, 0.05, "111111", 0, 0, 0], ["s", 0.04, 0.04, 0, -0.07, 0.14, -0.07, "111111", 0, 0, 0]]},
	"baseball_bat": {"n": "Baseballschläger", "cat": "bags", "coco": "baseball bat", "i": "🏏", "o": null, "p": [["c", 0.035, 0.85, 0.015, 0, 0.04, 0, "c8a165", 0, 0, 90]]},
	"baseball_glove": {"n": "Baseballhandschuh", "cat": "bags", "coco": "baseball glove", "i": "🧤", "o": null, "p": [["s", 0.13, 0.12, 0, 0, 0.06, 0, "8b5a2b", 0, 0, 0]]},
	"skateboard": {"n": "Skateboard", "cat": "bags", "coco": "skateboard", "i": "🛹", "o": null, "p": [
		["b", 0.8, 0.02, 0.2, 0, 0.09, 0, "222222", 0, 0, 0], ["c", 0.03, 0.04, 0, 0.28, 0.03, 0.07, "f1c40f", 90, 0, 0],
		["c", 0.03, 0.04, 0, -0.28, 0.03, 0.07, "f1c40f", 90, 0, 0], ["c", 0.03, 0.04, 0, 0.28, 0.03, -0.07, "f1c40f", 90, 0, 0],
		["c", 0.03, 0.04, 0, -0.28, 0.03, -0.07, "f1c40f", 90, 0, 0]]},
	"surfboard": {"n": "Surfbrett", "cat": "bags", "coco": "surfboard", "i": "🏄", "o": [2.0, 0.5], "p": [["s", 1.0, 0.07, 0, 0, 0.04, 0, "00b894", 0, 0, 0]], "scl": [1.0, 1.0, 0.27]},
	"tennis_racket": {"n": "Tennisschläger", "cat": "bags", "coco": "tennis racket", "i": "🎾", "o": null, "p": [
		["c", 0.13, 0.02, 0, 0, 0.02, 0.15, "2d3436", 0, 0, 0], ["b", 0.03, 0.02, 0.35, 0, 0.02, -0.12, "2d3436", 0, 0, 0]]},
	# ---- kitchen & food -------------------------------------------------------------------------------------------------
	"bottle": {"n": "Flasche", "cat": "food", "coco": "bottle", "i": "🍾", "o": null, "p": [
		["c", 0.04, 0.22, 0, 0, 0.11, 0, "2e7d32", 0, 0, 0], ["c", 0.015, 0.08, 0.04, 0, 0.26, 0, "2e7d32", 0, 0, 0]]},
	"wine_glass": {"n": "Weinglas", "cat": "food", "coco": "wine glass", "i": "🍷", "o": null, "p": [
		["c", 0.035, 0.005, 0, 0, 0.003, 0, "dfe6e9", 0, 0, 0], ["c", 0.005, 0.1, 0, 0, 0.055, 0, "dfe6e9", 0, 0, 0],
		["c", 0.04, 0.09, 0.02, 0, 0.15, 0, "8e1c3a", 0, 0, 0]]},
	"cup": {"n": "Tasse", "cat": "food", "coco": "cup", "i": "☕", "o": null, "p": [
		["c", 0.045, 0.09, 0.04, 0, 0.045, 0, "f5f5f5", 0, 0, 0], ["c", 0.025, 0.012, 0, 0.055, 0.05, 0, "f5f5f5", 90, 0, 0]]},
	"fork": {"n": "Gabel", "cat": "food", "coco": "fork", "i": "🍴", "o": null, "p": [["b", 0.02, 0.005, 0.19, 0, 0.003, 0, "c0c0c0", 0, 0, 0]]},
	"knife": {"n": "Messer", "cat": "food", "coco": "knife", "i": "🔪", "o": null, "p": [
		["b", 0.025, 0.005, 0.12, 0, 0.003, 0.05, "d0d0d0", 0, 0, 0], ["b", 0.02, 0.012, 0.1, 0, 0.006, -0.06, "3b2a1a", 0, 0, 0]]},
	"spoon": {"n": "Löffel", "cat": "food", "coco": "spoon", "i": "🥄", "o": null, "p": [
		["s", 0.022, 0.01, 0, 0, 0.005, 0.07, "c0c0c0", 0, 0, 0], ["b", 0.012, 0.005, 0.13, 0, 0.003, -0.03, "c0c0c0", 0, 0, 0]]},
	"bowl": {"n": "Schüssel", "cat": "food", "coco": "bowl", "i": "🥣", "o": null, "p": [["c", 0.09, 0.07, 0.05, 0, 0.035, 0, "e17055", 0, 0, 0]]},
	"banana": {"n": "Banane", "cat": "food", "coco": "banana", "i": "🍌", "o": null, "p": [["c", 0.02, 0.18, 0.015, 0, 0.02, 0, "f6d743", 0, 0, 80]]},
	"apple": {"n": "Apfel", "cat": "food", "coco": "apple", "i": "🍎", "o": null, "p": [["s", 0.04, 0.075, 0, 0, 0.04, 0, "c0392b", 0, 0, 0],
		["c", 0.004, 0.02, 0, 0, 0.085, 0, "4a3020", 0, 0, 0]]},
	"orange": {"n": "Orange", "cat": "food", "coco": "orange", "i": "🍊", "o": null, "p": [["s", 0.04, 0.08, 0, 0, 0.04, 0, "f39c12", 0, 0, 0]]},
	"sandwich": {"n": "Sandwich", "cat": "food", "coco": "sandwich", "i": "🥪", "o": null, "p": [
		["b", 0.12, 0.015, 0.12, 0, 0.008, 0, "e6c48a", 0, 0, 0], ["b", 0.12, 0.012, 0.12, 0, 0.022, 0, "6ab04c", 0, 0, 0],
		["b", 0.12, 0.012, 0.12, 0, 0.034, 0, "e17055", 0, 0, 0], ["b", 0.12, 0.015, 0.12, 0, 0.048, 0, "e6c48a", 0, 0, 0]]},
	"broccoli": {"n": "Broccoli", "cat": "food", "coco": "broccoli", "i": "🥦", "o": null, "p": [
		["c", 0.015, 0.06, 0, 0, 0.03, 0, "7cb342", 0, 0, 0], ["s", 0.05, 0.07, 0, 0, 0.08, 0, "2e7d32", 0, 0, 0]]},
	"carrot": {"n": "Rüebli", "cat": "food", "coco": "carrot", "i": "🥕", "o": null, "p": [["k", 0.02, 0.16, 0, 0, 0.02, 0, "e67e22", 0, 0, 90]]},
	"hot_dog": {"n": "Hot Dog", "cat": "food", "coco": "hot dog", "i": "🌭", "o": null, "p": [
		["c", 0.03, 0.17, 0, 0, 0.03, 0, "e6c48a", 0, 0, 90], ["c", 0.017, 0.2, 0, 0, 0.05, 0, "a0412d", 0, 0, 90]]},
	"pizza": {"n": "Pizza", "cat": "food", "coco": "pizza", "i": "🍕", "o": null, "p": [["c", 0.16, 0.015, 0, 0, 0.008, 0, "e6b35a", 0, 0, 0],
		["c", 0.14, 0.004, 0, 0, 0.017, 0, "c0392b", 0, 0, 0], ["s", 0.02, 0.006, 0, 0.05, 0.02, 0.04, "b33939", 0, 0, 0]]},
	"donut": {"n": "Donut", "cat": "food", "coco": "donut", "i": "🍩", "o": null, "p": [["t", 0.025, 0.06, 0, 0, 0.025, 0, "fd79a8", 0, 0, 0]]},
	"cake": {"n": "Kuchen", "cat": "food", "coco": "cake", "i": "🎂", "o": null, "p": [
		["c", 0.12, 0.09, 0, 0, 0.045, 0, "fdf6e3", 0, 0, 0], ["c", 0.12, 0.015, 0, 0, 0.095, 0, "e84393", 0, 0, 0]]},
	# ---- home & electronics ---------------------------------------------------------------------------------------------
	"chair": {"n": "Stuhl", "cat": "home", "coco": "chair", "i": "🪑", "o": [0.5, 0.5], "p": [
		["b", 0.45, 0.05, 0.45, 0, 0.45, 0, "8e6e53", 0, 0, 0], ["b", 0.45, 0.5, 0.05, 0, 0.72, -0.2, "8e6e53", 0, 0, 0],
		["b", 0.04, 0.45, 0.04, 0.2, 0.22, 0.2, "6d5340", 0, 0, 0], ["b", 0.04, 0.45, 0.04, -0.2, 0.22, 0.2, "6d5340", 0, 0, 0],
		["b", 0.04, 0.45, 0.04, 0.2, 0.22, -0.2, "6d5340", 0, 0, 0], ["b", 0.04, 0.45, 0.04, -0.2, 0.22, -0.2, "6d5340", 0, 0, 0]]},
	"couch": {"n": "Sofa", "cat": "home", "coco": "couch", "i": "🛋", "o": [2.0, 0.9], "p": [
		["b", 2.0, 0.45, 0.85, 0, 0.25, 0, "5f6caf", 0, 0, 0], ["b", 2.0, 0.5, 0.2, 0, 0.7, -0.33, "5f6caf", 0, 0, 0],
		["b", 0.2, 0.3, 0.85, 0.9, 0.6, 0, "4f5c9f", 0, 0, 0], ["b", 0.2, 0.3, 0.85, -0.9, 0.6, 0, "4f5c9f", 0, 0, 0]]},
	"bed": {"n": "Bett / Liege", "cat": "home", "coco": "bed", "i": "🛏", "o": [2.0, 1.0], "p": [
		["b", 2.0, 0.3, 0.95, 0, 0.25, 0, "8b6b4a", 0, 0, 0], ["b", 1.95, 0.15, 0.9, 0, 0.47, 0, "f2f2f2", 0, 0, 0],
		["b", 0.45, 0.12, 0.6, -0.7, 0.6, 0, "ffffff", 0, 0, 0], ["b", 1.2, 0.06, 0.92, 0.35, 0.57, 0, "4a90d9", 0, 0, 0],
		["b", 0.08, 0.8, 0.95, -1.0, 0.5, 0, "8b6b4a", 0, 0, 0]]},
	"dining_table": {"n": "Esstisch", "cat": "home", "coco": "dining table", "i": "🍽", "o": [1.6, 0.9], "p": [
		["b", 1.6, 0.05, 0.9, 0, 0.75, 0, "b08a5a", 0, 0, 0], ["b", 0.06, 0.73, 0.06, 0.72, 0.37, 0.38, "8b6b4a", 0, 0, 0],
		["b", 0.06, 0.73, 0.06, -0.72, 0.37, 0.38, "8b6b4a", 0, 0, 0], ["b", 0.06, 0.73, 0.06, 0.72, 0.37, -0.38, "8b6b4a", 0, 0, 0],
		["b", 0.06, 0.73, 0.06, -0.72, 0.37, -0.38, "8b6b4a", 0, 0, 0]]},
	"toilet": {"n": "WC (Camping-WC)", "cat": "home", "coco": "toilet", "i": "🚽", "o": [0.5, 0.7], "p": [
		["c", 0.18, 0.4, 0.14, 0, 0.2, 0.05, "f5f5f5", 0, 0, 0], ["c", 0.2, 0.04, 0, 0, 0.42, 0.05, "eeeeee", 0, 0, 0],
		["b", 0.4, 0.4, 0.18, 0, 0.6, -0.25, "f5f5f5", 0, 0, 0]]},
	"tv": {"n": "Fernseher", "cat": "home", "coco": "tv", "i": "📺", "o": [1.0, 0.3], "w": true, "p": [
		["b", 1.1, 0.65, 0.06, 0, 0.75, 0, "111111", 0, 0, 0], ["b", 1.02, 0.57, 0.01, 0, 0.75, 0.035, "2a6fb0", 0, 0, 0],
		["b", 0.3, 0.42, 0.2, 0, 0.21, 0, "222222", 0, 0, 0]]},
	"laptop": {"n": "Laptop", "cat": "home", "coco": "laptop", "i": "💻", "o": null, "w": true, "p": [
		["b", 0.34, 0.02, 0.24, 0, 0.01, 0, "9aa0a6", 0, 0, 0], ["b", 0.34, 0.24, 0.015, 0, 0.13, -0.12, "9aa0a6", -15, 0, 0],
		["b", 0.31, 0.2, 0.002, 0, 0.13, -0.11, "3a7bd5", -15, 0, 0]]},
	"mouse": {"n": "Computermaus", "cat": "home", "coco": "mouse", "i": "🖱", "o": null, "p": [["s", 0.035, 0.035, 0, 0, 0.018, 0, "333333", 0, 0, 0]], "scl": [1.0, 1.0, 1.6]},
	"remote": {"n": "Fernbedienung", "cat": "home", "coco": "remote", "i": "📟", "o": null, "p": [["b", 0.05, 0.02, 0.18, 0, 0.01, 0, "222222", 0, 0, 0]]},
	"keyboard": {"n": "Tastatur", "cat": "home", "coco": "keyboard", "i": "⌨", "o": null, "p": [["b", 0.44, 0.025, 0.14, 0, 0.012, 0, "dddddd", 0, 0, 0]]},
	"cell_phone": {"n": "Handy", "cat": "home", "coco": "cell phone", "i": "📱", "o": null, "w": true, "p": [
		["b", 0.075, 0.01, 0.15, 0, 0.005, 0, "111111", 0, 0, 0], ["b", 0.068, 0.002, 0.14, 0, 0.011, 0, "3a7bd5", 0, 0, 0]]},
	"microwave": {"n": "Mikrowelle", "cat": "home", "coco": "microwave", "i": "🍳", "o": null, "w": true, "p": [
		["b", 0.5, 0.3, 0.38, 0, 0.15, 0, "dfe6e9", 0, 0, 0], ["b", 0.32, 0.22, 0.01, -0.06, 0.15, 0.19, "2d3436", 0, 0, 0]]},
	"oven": {"n": "Grill / Ofen", "cat": "home", "coco": "oven", "i": "🔥", "o": [0.6, 0.6], "w": true, "p": [
		["b", 0.6, 0.85, 0.6, 0, 0.43, 0, "2d3436", 0, 0, 0], ["b", 0.45, 0.35, 0.01, 0, 0.45, 0.3, "111111", 0, 0, 0],
		["c", 0.02, 0.4, 0, 0, 0.78, 0.31, "b2bec3", 0, 0, 90]]},
	"toaster": {"n": "Toaster", "cat": "home", "coco": "toaster", "i": "🍞", "o": null, "w": true, "p": [
		["b", 0.28, 0.2, 0.16, 0, 0.1, 0, "b2bec3", 0, 0, 0], ["b", 0.2, 0.01, 0.03, 0, 0.2, 0.03, "222222", 0, 0, 0]]},
	"sink": {"n": "Spülbecken", "cat": "home", "coco": "sink", "i": "🚰", "o": [0.8, 0.6], "p": [
		["b", 0.8, 0.85, 0.6, 0, 0.43, 0, "8e6e53", 0, 0, 0], ["b", 0.6, 0.06, 0.45, 0, 0.86, 0, "b2bec3", 0, 0, 0],
		["c", 0.02, 0.3, 0, 0, 1.0, -0.2, "b2bec3", 0, 0, 0]]},
	"refrigerator": {"n": "Kühlschrank", "cat": "home", "coco": "refrigerator", "i": "🧊", "o": [0.7, 0.7], "p": [
		["b", 0.7, 1.8, 0.65, 0, 0.9, 0, "f5f6fa", 0, 0, 0], ["b", 0.02, 0.5, 0.03, 0.28, 1.2, 0.34, "b2bec3", 0, 0, 0],
		["b", 0.7, 0.01, 0.66, 0, 1.25, 0.001, "b2bec3", 0, 0, 0]]},
	"book": {"n": "Buch", "cat": "home", "coco": "book", "i": "📖", "o": null, "p": [["b", 0.17, 0.03, 0.24, 0, 0.015, 0, "c0392b", 0, 0, 0],
		["b", 0.16, 0.026, 0.235, 0.006, 0.015, 0, "f5f0e1", 0, 0, 0]]},
	"clock": {"n": "Uhr", "cat": "home", "coco": "clock", "i": "🕰", "o": null, "p": [
		["c", 0.15, 0.04, 0, 0, 0.15, 0, "f5f5f5", 90, 0, 0], ["b", 0.01, 0.1, 0.005, 0, 0.18, 0.022, "111111", 0, 0, 0],
		["b", 0.07, 0.01, 0.005, 0.03, 0.15, 0.022, "111111", 0, 0, 0]]},
	"vase": {"n": "Vase", "cat": "home", "coco": "vase", "i": "🏺", "o": null, "p": [["c", 0.05, 0.25, 0.09, 0, 0.125, 0, "0984e3", 0, 0, 0],
		["s", 0.08, 0.08, 0, 0, 0.3, 0, "e84393", 0, 0, 0]]},
	"scissors": {"n": "Schere", "cat": "home", "coco": "scissors", "i": "✂", "o": null, "p": [
		["b", 0.015, 0.005, 0.12, 0.01, 0.003, 0.03, "c0c0c0", 0, 15, 0], ["b", 0.015, 0.005, 0.12, -0.01, 0.003, 0.03, "c0c0c0", 0, -15, 0],
		["t", 0.008, 0.025, 0, 0.025, 0.004, -0.06, "e74c3c", 0, 0, 0], ["t", 0.008, 0.025, 0, -0.025, 0.004, -0.06, "e74c3c", 0, 0, 0]]},
	"teddy_bear": {"n": "Teddybär", "cat": "home", "coco": "teddy bear", "i": "🧸", "o": null, "p": [
		["s", 0.14, 0.26, 0, 0, 0.14, 0, "b07a4a", 0, 0, 0], ["s", 0.1, 0.18, 0, 0, 0.36, 0, "b07a4a", 0, 0, 0],
		["s", 0.04, 0.04, 0, 0.07, 0.45, 0, "8a5a32", 0, 0, 0], ["s", 0.04, 0.04, 0, -0.07, 0.45, 0, "8a5a32", 0, 0, 0],
		["s", 0.05, 0.08, 0, 0.13, 0.15, 0.06, "b07a4a", 0, 0, 0], ["s", 0.05, 0.08, 0, -0.13, 0.15, 0.06, "b07a4a", 0, 0, 0]]},
	"hair_drier": {"n": "Föhn", "cat": "home", "coco": "hair drier", "i": "💨", "o": null, "p": [
		["c", 0.04, 0.18, 0, 0, 0.04, 0, "e84393", 0, 0, 90], ["b", 0.04, 0.12, 0.04, -0.04, 0.02, 0, "e84393", 0, 0, 90]]},
	"toothbrush": {"n": "Zahnbürste", "cat": "home", "coco": "toothbrush", "i": "🪥", "o": null, "p": [
		["b", 0.012, 0.012, 0.18, 0, 0.006, 0, "00cec9", 0, 0, 0], ["b", 0.012, 0.02, 0.03, 0, 0.016, 0.075, "ffffff", 0, 0, 0]]},
}

# 3D-4.x «Gegenstände»: the new things (fruit, valuables, camping, garden, lures, false-alarm sources) - objekte_neu.gd
const Neu = preload("res://scripts/objekte_neu.gd")


static func def(kind: String) -> Dictionary:
	"""the entry of a thing - the 80 COCO things here or the new ones of objekte_neu.gd"""
	return OBJ.get(kind, Neu.OBJ.get(kind, {}))


static func kinds() -> Array:
	return OBJ.keys() + Neu.OBJ.keys()


static func cats() -> Array:
	"""the tabs: the categories here + the new ones (Wertsachen, Camping, Garten & Haus, Lockt Tiere an, Fehlalarm-Quellen)"""
	return CATS + Neu.CATS


# COCO classes that are already visitors (they walk): name -> visitor kind
const COCO_VISITORS := {"person": "person", "bicycle": "cyclist", "car": "car", "motorcycle": "moto", "cat": "cat", "dog": "dog",
		"horse": "horse", "sheep": "sheep", "cow": "cow", "bird": "", "truck": "van", "bench": ""}


static func coco_count() -> int:
	var s := {}
	for k in OBJ:
		s[OBJ[k]["coco"]] = true
	for k in COCO_VISITORS:
		s[k] = true
	return s.size()


static func build(main, kind: String) -> Node3D:
	"""the object as a node (not yet in the world)"""
	var d: Dictionary = def(kind)
	var n := Node3D.new()
	n.name = "obj_" + kind
	if d.is_empty():
		return n
	var wv = d.get("w", false)
	var warm: bool = typeof(wv) == TYPE_BOOL and bool(wv)
	var tk = float(wv) if typeof(wv) in [TYPE_FLOAT, TYPE_INT] else (30.0 if warm else "stone")
	var pivs := {}                                         # 3D-4.x: moving parts (objekte_plus.gd): role -> Node3D
	var nfruit := 0
	for p in d["p"]:
		var parent: Node3D = n
		var off := Vector3.ZERO
		if p.size() > 11:                                  # a part with a role: under its pivot (a fruit: its own)
			var role := str(p[11])
			if role == "fruit":
				var fp := Node3D.new()
				fp.name = "fruit_%d" % nfruit
				nfruit += 1
				fp.position = Vector3(p[4], p[5], p[6])
				fp.set_meta("role", "fruit")
				n.add_child(fp)
				parent = fp
				off = fp.position
			else:
				if not pivs.has(role):
					var pv := Node3D.new()
					pv.name = "piv_" + role
					var pp: Array = (d.get("piv", {}) as Dictionary).get(role, [0, 0, 0])
					pv.position = Vector3(pp[0], pp[1], pp[2])
					pv.set_meta("role", role)
					n.add_child(pv)
					pivs[role] = pv
				parent = pivs[role]
				off = (pivs[role] as Node3D).position
		var col := str(p[7])
		if str(p[0]) == "f":                               # cloth that flaps in the wind (objekte_plus gives it the wind)
			var q := QuadMesh.new()
			q.size = Vector2(p[1], p[2])
			q.subdivide_width = 8
			q.subdivide_depth = 6
			var sm := ShaderMaterial.new()
			sm.shader = load("res://shaders/flap.gdshader")
			sm.set_shader_parameter("color", Color("#" + col.trim_prefix("*")))
			sm.set_shader_parameter("seed", randf() * 10.0)
			sm.set_shader_parameter("hang", 1.0 if float(p[3]) > 0.5 else 0.0)
			sm.set_shader_parameter("strength", 0.8)
			sm.set_shader_parameter("wind", 10.0)
			var fm := MeshInstance3D.new()
			fm.mesh = q
			fm.position = Vector3(p[4], p[5], p[6]) - off
			fm.rotation = Vector3(deg_to_rad(p[8]), deg_to_rad(p[9]), deg_to_rad(p[10]))
			fm.material_override = sm
			fm.set_meta("flap", sm)
			parent.add_child(fm)
			var fth := MeshInstance3D.new()                # the thermal twin
			fth.mesh = q
			fth.position = fm.position
			fth.rotation = fm.rotation
			fth.material_override = main.tmat("tent")
			fth.layers = 2
			fth.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			parent.add_child(fth)
			continue
		var mesh: Mesh
		match str(p[0]):
			"b":
				var b := BoxMesh.new()
				b.size = Vector3(p[1], p[2], p[3])
				mesh = b
			"c":
				var c := CylinderMesh.new()
				c.top_radius = p[1]
				c.bottom_radius = p[3] if float(p[3]) > 0.0 else p[1]
				c.height = p[2]
				c.radial_segments = 14
				mesh = c
			"s":
				var s := SphereMesh.new()
				s.radius = p[1]
				s.height = p[2] if float(p[2]) > 0.0 else 2.0 * float(p[1])
				s.radial_segments = 14
				s.rings = 8
				mesh = s
			"p":
				var pr := PrismMesh.new()
				pr.size = Vector3(p[1], p[2], p[3])
				mesh = pr
			"k":
				var k := CylinderMesh.new()
				k.top_radius = 0.0
				k.bottom_radius = p[1]
				k.height = p[2]
				k.radial_segments = 14
				mesh = k
			"t":
				var t := TorusMesh.new()
				t.inner_radius = p[1]
				t.outer_radius = p[2]
				mesh = t
		var m := StandardMaterial3D.new()
		m.albedo_color = Color("#" + col.trim_prefix("*"))
		m.roughness = 0.75
		if col.begins_with("*"):                           # 3D-4.x: it glows (lamp, flame, screen) - objekte_plus switches it
			m.emission_enabled = true
			m.emission = m.albedo_color
			m.emission_energy_multiplier = 2.0
		var rot := Vector3(deg_to_rad(p[8]), deg_to_rad(p[9]), deg_to_rad(p[10]))
		var mi: MeshInstance3D = main.add_mesh(parent, mesh, Vector3(p[4], p[5], p[6]) - off, m, tk, rot)
		if col.begins_with("*"):
			mi.set_meta("glow", m)
	if d.has("scl"):
		var sc: Array = d["scl"]
		n.scale = Vector3(sc[0], sc[1], sc[2])
	return n
