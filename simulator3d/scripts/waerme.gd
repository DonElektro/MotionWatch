extends RefCounted
## Wärme-Tabelle (Paket «P3 Wärme-Signatur», 31.10.2026): EINE Stelle für die Temperaturen, die das Wärmebild zeigt –
## Menschen, Tiere, Fahrzeuge, Feuer, Lampen, Zelte, sonnenwarme Flächen. Andere Teile (Menschen, Tiere, Szenen, Gegenstände)
## holen ihre Werte hier:
##     const Waerme = preload("res://scripts/waerme.gd")
##     Waerme.cloth(amb, "jacket", wet, active)       -> Oberfläche der Kleider (°C)
##     Waerme.skin("face", amb, active)               -> Gesicht / Hände / Hals / Nase (°C)
##     Waerme.animal(kind, amb, part, sun)            -> Fell-Oberfläche eines Tiers (°C)
##     Waerme.engine(part, minutes, amb)              -> Motorhaube / Auspuff / Reifen nach x Minuten Stillstand (°C)
##     Waerme.T(key, amb)                             -> feste Dinge (Feuer, Grill, Lampe, Kerze …) (°C)
##     Waerme.obj(kind, hot_part, default)            -> Gegenstände des Katalogs (objects.gd «w»)
##     Waerme.SUN                                     -> wie stark sich Flächen in der Sonne erwärmen und wie lange sie die Wärme halten
## Alle Werte sind Oberflächen-Temperaturen, wie sie eine Wärmebildkamera (8–14 µm, Emissionsgrad ~0.95) zeigt.
##
## Quellen (allgemein):
##  [Mc07]  McCafferty D.J. (2007): «The value of infrared thermography for research on mammals», Mammal Review 37: 207–223
##          (Fell-Oberflächen liegen meist nur 5–15 K über der Luft, Augen, Nase, Ohren, Beine sind die warmen Stellen).
##  [CR08]  Clarke A., Rothery P. (2008): «Scaling of body temperature in mammals and birds», Functional Ecology 22: 58–67
##          (Körperkern-Temperaturen der Säugetiere 36–39.5 °C).
##  [ISO9920] ISO 9920:2007 Wärmeisolation der Kleidung (clo-Werte: T-Shirt ~0.3 clo, Jacke ~1 clo, Daunenjacke ~2 clo,
##          Schlafsack 4–8 clo) – je mehr Isolation, desto näher liegt die Oberfläche an der Lufttemperatur.
##  [Hou]   Houdas Y., Ring E.F.J. (1982): «Human Body Temperature» (Haut 32–35 °C, Gesicht ~34 °C, Hände 28–33 °C, in der
##          Kälte ziehen sich die Gefässe der Hände und der Nase zusammen: 20–25 °C bei 0 °C).
##  [FLIR]  FLIR-Anwendungsbeispiele «Thermal imaging for security / automotive» (Motorhaube nach der Fahrt 40–60 °C,
##          Auspuff >100 °C, kühlt in 1–2 h auf Lufttemperatur ab) – Schätzwerte, keine Datenblattwerte.
##  [ASPH]  Studien zu städtischen Wärmeinseln (z. B. US EPA «Reducing Urban Heat Islands», Kapitel Cool Pavements):
##          dunkler Asphalt im Sommer bis 27–50 K über der Luft, nachts noch einige K wärmer.
## Was hier steht, ist bewusst einfach (eine Zahl pro Teil) – lieber wenige glaubwürdige Werte als viele erfundene.

const CORE_SKIN := 33.5          # mittlere Haut unter der Kleidung (°C) [Hou]

# ---- Menschen --------------------------------------------------------------------------------------------------------
# Anteil der Wärme, der durch die Kleidung nach aussen kommt: Oberfläche = Luft + (Haut − Luft) · k.  [ISO9920]
# (gemessen an Wärmebildern: T-Shirt-Oberfläche ~2–4 K unter der Haut, Winterjacke nur 2–6 K über der Luft)
const CLOTH := {
	"shirt": 0.72,        # T-Shirt, Hemd (~0.3 clo)
	"light": 0.55,        # Pullover, leichte Jacke (~0.7 clo)
	"jacket": 0.42,       # normale Jacke (~1 clo) - so war es bis 3D-4.25 (simreal.cloth_t)
	"thick": 0.26,        # Daunenjacke, dicker Mantel, Regencape mit Kapuze (~2 clo)
	"blanket": 0.16,      # Wolldecke über den Schultern / im Bett
	"sleeping_bag": 0.10, # Schlafsack (4–8 clo)
}
const ACTIVE_K := 0.12           # nach dem Rennen: mehr Wärme durch die Kleider (Schwitzen, Durchblutung)
const WET_TO_AIR := 0.5          # nasse Kleider: Verdunstung kühlt - die Oberfläche liegt halb so weit über der Luft …
const WET_EVAP := 1.0            # … und noch ~1 K darunter (Verdunstungskälte)


static func cold_k(amb: float) -> float:
	"""0 bei 12 °C und wärmer … 1 bei −8 °C: in der Kälte ziehen sich die Gefässe in Händen, Nase, Ohren zusammen [Hou]"""
	return clampf((12.0 - amb) / 20.0, 0.0, 1.0)


static func skin(part: String, amb: float, active := false) -> float:
	"""offene Haut: face (Stirn, Wangen ~34 °C), nose (kühler), ear, neck, hand, arm (nackter Arm), leg (nacktes Bein) [Hou]"""
	var ck := cold_k(amb)
	var a := 1.0 if active else 0.0
	match part:
		"face":
			return 34.6 - 1.2 * ck + 0.4 * a
		"nose":
			return 33.4 - 4.2 * ck + 0.4 * a
		"ear":
			return 33.0 - 5.0 * ck + 0.6 * a
		"neck":
			return 34.0 - 1.0 * ck + 0.4 * a
		"hand":
			return 31.5 - 6.5 * ck + 1.5 * a       # Hände: bei 0 °C ohne Handschuhe ~26 °C, nach dem Rennen wärmer
		"arm", "leg":
			return 31.5 - 2.0 * ck + 1.0 * a
	return CORE_SKIN


static func cloth_level(amb: float, variant := "") -> String:
	"""was jemand bei dieser Temperatur typischerweise trägt (Schweiz, draussen)"""
	if variant == "hooded":
		return "thick"
	if amb >= 22.0:
		return "shirt"
	if amb >= 14.0:
		return "light"
	if amb >= 4.0:
		return "jacket"
	return "thick"


static func cloth(amb: float, level := "jacket", wet := false, active := false) -> float:
	"""Oberfläche der Kleidung (°C)"""
	var k: float = float(CLOTH.get(level, CLOTH["jacket"])) + (ACTIVE_K if active else 0.0)
	var t: float = amb + (CORE_SKIN - amb) * clampf(k, 0.0, 1.0)
	if wet:
		t = amb + (t - amb) * WET_TO_AIR - WET_EVAP
	return t


# ---- Tiere -----------------------------------------------------------------------------------------------------------
# kind: [Kern-Temperatur °C [CR08], k Fell (Rumpf), k Kopf, Körperlänge m (nur zur Info für andere Pakete)]
# Fell-Oberfläche = Luft + (Kern − Luft) · k [Mc07]; dünnes Fell / kurze Haare = grösseres k; Wolle und Winterfell klein.
const ANIMALS := {
	"fox": [38.7, 0.30, 0.50, 0.65],       # Rotfuchs: dichtes Fell, Gesicht und Beine deutlich wärmer
	"deer": [38.6, 0.32, 0.50, 1.1],       # Reh
	"boar": [39.0, 0.36, 0.50, 1.3],       # Wildschwein: Borsten, wenig Unterwolle
	"cat": [38.6, 0.36, 0.55, 0.45],
	"dog": [38.7, 0.38, 0.55, 0.8],
	"badger": [37.8, 0.30, 0.45, 0.75],
	"hare": [39.0, 0.30, 0.50, 0.55],
	"hedgehog": [35.0, 0.40, 0.55, 0.25],  # aktiv ~35 °C (im Winterschlaf nur ~5 °C - dann unsichtbar)
	"wolf": [38.5, 0.28, 0.45, 1.1],
	"marten": [39.0, 0.33, 0.50, 0.5],
	"squirrel": [39.0, 0.35, 0.50, 0.22],
	"cow": [38.6, 0.48, 0.60, 2.2],        # kurzes Haar, grosser Körper: gut sichtbar
	"sheep": [39.1, 0.14, 0.55, 1.2],      # Wolle isoliert sehr gut: Rumpf fast Lufttemperatur, Kopf und Beine warm
	"horse": [37.8, 0.46, 0.60, 2.2],
	"chamois": [38.8, 0.28, 0.45, 1.2],    # Gämse: dichtes Winterfell
	"ibex": [38.7, 0.30, 0.45, 1.4],
	"lynx": [38.4, 0.28, 0.45, 1.0],
	"bird": [41.0, 0.25, 0.50, 0.2],       # Vögel: Federn isolieren sehr gut
	"bat": [37.0, 0.40, 0.50, 0.08],
}
const FUR_SUN := 6.0             # dunkles Fell in voller Sonne: einige K wärmer [Mc07]


static func animal(kind: String, amb: float, part := "body", sun := 0.0) -> float:
	"""Oberfläche eines Tiers: part = body | head | legs | eyes; sun 0 … 1 (volle Sonne)"""
	var a: Array = ANIMALS.get(kind, ANIMALS["fox"])
	var core: float = a[0]
	match part:
		"eyes":
			return core - 2.0
		"head":
			return amb + (core - amb) * float(a[2]) + FUR_SUN * 0.5 * sun
		"legs":
			return amb + (core - amb) * minf(1.0, float(a[1]) + 0.15)
	return amb + (core - amb) * float(a[1]) + FUR_SUN * sun


static func has_animal(kind: String) -> bool:
	return ANIMALS.has(kind)


# ---- Fahrzeuge -------------------------------------------------------------------------------------------------------
# [Übertemperatur gleich nach der Fahrt (K über der Luft), Abkühl-Zeitkonstante (Minuten)] [FLIR]
# Abkühlen: T = Luft + ΔT · e^(−t/τ) (Newton) - nach 3 τ ist fast nichts mehr zu sehen.
const ENGINE := {
	"hood": [42.0, 35.0],        # Motorhaube aussen (Blech über dem Motor)
	"grille": [38.0, 25.0],      # Kühlergrill / Front
	"exhaust": [140.0, 12.0],    # Auspuff-Endrohr
	"tyre": [12.0, 25.0],        # Reifen (Walkarbeit, Bremsen)
	"block": [60.0, 50.0],       # Motor selbst (Traktor, Motorrad: offen sichtbar)
}


static func engine(part: String, minutes: float, amb: float) -> float:
	var e: Array = ENGINE.get(part, ENGINE["hood"])
	return amb + float(e[0]) * exp(-maxf(0.0, minutes) / float(e[1]))


# ---- feste Dinge -----------------------------------------------------------------------------------------------------
# key: [°C absolut] oder ["+", K über der Luft]. Das Modul misst −40 … +400 °C (Waveshare Thermal-90, Datenblatt) -
# heissere Dinge (Flammen) zeigt es als 400 °C.
const FIXED := {
	"campfire_flame": [650.0],          # Flammen / Glut eines Lagerfeuers 500–900 °C (sättigt den Sensor)
	"campfire_embers": [380.0],
	"campfire_logs": [180.0],           # Holz am Rand des Feuers
	"campfire_stones": [70.0],          # Steine rund ums Feuer
	"bbq_lid": [170.0],                 # Deckel eines Kugelgrills beim Grillen (innen 200–300 °C)
	"bbq_coals": [400.0],
	"bbq_cold": ["+", 0.0],             # Grill nicht in Betrieb
	"candle_flame": [1000.0],           # winzig: das Modul mittelt sie mit der Umgebung (ein Pixel = 1.1° bei 90°/80 px)
	"candle_wax": [42.0],
	"gas_stove": [130.0],               # Topfboden / Brenner
	"sausages": [60.0],
	"lamp_led_on": ["+", 22.0],         # LED-Strassenlampe: Gehäuse / Kühlkörper 15–30 K über der Luft
	"lamp_halogen_on": [110.0],         # Halogen-Scheinwerfer, Glas
	"lantern_on": ["+", 12.0],          # Campinglaterne (LED)
	"headlight_on": ["+", 30.0],        # Autoscheinwerfer (Halogen-Glas warm, LED weniger)
	"laptop": [35.0],
	"phone": [32.0],
	"tv_on": [38.0],
	"power_station": ["+", 6.0],
	"pi_case": ["+", 12.0],             # MoveEye selbst (Pi 5 im Gehäuse)
	"tent_person": ["+", 1.4],          # Zeltwand über einer schlafenden Person (Schlafsack): ein schwacher Fleck [Mc07-ähnlich]
	"bed_blanket_person": [25.0],       # Bettdecke über einer schlafenden Person im Zimmer (~20 °C)
	"window_glass_e": [0.85],           # Emissionsgrad von Glas (8–14 µm): Glas ist für Wärmestrahlung undurchsichtig
	"window_plastic_e": [0.90],         # Acryl / Polycarbonat (Wohnwagenfenster): ebenso undurchsichtig
}


static func T(key: String, amb := 15.0) -> float:
	var v: Array = FIXED.get(key, ["+", 0.0])
	if v.size() == 2 and str(v[0]) == "+":
		return amb + float(v[1])
	return float(v[0])


# ---- Gegenstände des Katalogs (objects.gd / objekte_neu.gd, Schlüssel «w») -------------------------------------------
# kind: [heisse Teile (leuchtende «*»-Teile, Flamme), übrige Teile]
const OBJ := {
	"campfire": ["campfire_flame", "campfire_stones"],
	"kettle_grill": ["bbq_lid", "bbq_lid"],
	"candle": ["candle_flame", "candle_wax"],
	"gas_stove": ["gas_stove", "gas_stove"],
	"bbq_sausages": ["sausages", "sausages"],
	"laptop": ["laptop", "laptop"],
	"cell_phone": ["phone", "phone"],
	"tv": ["tv_on", "tv_on"],
	"power_station": ["power_station", "power_station"],
}


static func obj(kind: String, hot_part: bool, default, amb := 15.0):
	"""Temperatur für ein Teil eines Gegenstands - default (Zahl oder Material-Name) wenn die Tabelle ihn nicht kennt"""
	if not OBJ.has(kind):
		return default
	return T(str(OBJ[kind][0 if hot_part else 1]), amb)


# ---- Sonne -----------------------------------------------------------------------------------------------------------
# Thermal-Material: [Erwärmung in voller Sonne (K über der Luft), wie lange die Fläche die Wärme hält (Stunden)]
# Dunkle, dünne Flächen werden schnell heiss und kühlen schnell ab; Stein und Asphalt speichern bis in die Nacht. [ASPH]
const SUN := {
	"stone": [15.0, 2.6],        # Steine, Mauern, Beton
	"road": [20.0, 3.2],         # dunkler Asphalt
	"caravan": [9.0, 1.3],       # weisses Blech (Wohnwagen)
	"car": [24.0, 0.6],          # Autodach (dunkler Lack, dünnes Blech): wird am Nachmittag heiss, nachts kälter als die Luft
	"tent": [10.0, 0.25],        # Zeltstoff (dünn, keine Masse)
}
# Klare Nacht: Flächen strahlen zum kalten Himmel ab und werden 1–4 K kälter als die Luft (Strahlungsfrost).
const NIGHT_SKY_COOL := {"car": 3.0, "tent": 1.5, "road": 1.0, "caravan": 2.0, "stone": 0.5}


# ---- Himmel und Luft (für das Wärmebild-Modell thermsensor.gd) -------------------------------------------------------
static func sky_zenith(amb: float, clouds: float, humidity: float) -> float:
	"""Strahlungs-Temperatur des Himmels senkrecht nach oben (°C) im Band 8–14 µm: klar 24–36 K unter der Luft (trockene
	Luft kälter), tiefe Wolken nur 3–5 K darunter. Erfahrungswerte der Wolkensensoren (Infrarot-Thermometer zum Himmel,
	z. B. AAG CloudWatcher / Boltwood: «klar» ab Himmel − Luft < −20 … −25 K); Wasserdampf macht den Himmel wärmer."""
	var ah := abs_humidity(amb, humidity)
	var d_clear := 24.0 + 12.0 * clampf(1.0 - ah / 18.0, 0.0, 1.0)
	return amb - lerpf(d_clear, 4.0, clampf(clouds, 0.0, 1.0))


static func abs_humidity(amb: float, humidity: float) -> float:
	"""absolute Feuchte g/m³"""
	var e := 6.112 * exp(17.67 * amb / (amb + 243.5)) * clampf(humidity, 0.0, 100.0) / 100.0
	return 216.7 * e / (amb + 273.15)


static func air_k(weather: String, amb: float, humidity: float, fog_density: float) -> float:
	"""Dämpfung der Wärmestrahlung (8–14 µm) pro Meter.
	  Wasserdampf: ~0.015 /km je g/m³ (klare Luft, 1 km: 80–90 % Durchlass)
	  Nebel: Tröpfchen dämpfen das lange Infrarot etwa halb so stark wie das sichtbare Licht (Sicht V: σ_sicht = 3.9 / V)
	  Regen: fast nichts (0.37 · R^0.63 dB/km, 8 mm/h ≈ 1.4 dB/km) - Regen stört vor allem durch nasse Flächen und Wasser
	         auf dem Sensorfenster (thermsensor.gd)
	  Schnee: Flocken etwa wie Nebel gleicher Sicht"""
	var k := abs_humidity(amb, humidity) * 0.015 / 1000.0
	match weather:
		"fog":
			k += 0.5 * fog_density
		"snow":
			k += 0.5 * fog_density
		"rain":
			k += 0.37 * pow(8.0, 0.63) / 4343.0
	return k
