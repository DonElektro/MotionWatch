extends Node
## Simulator-Werte (30.10.2026, Wunsch Daniel): what MoveEye would measure on the real device, simulated here and sent with
## every answer to MoveEye (main.gd world_reply):
##   battery  the Waveshare UPS HAT (2 x 18650 in series = 2S): charge from the consumption (Pi, servos, lights, siren,
##            CPU load of MoveEye) and the charge of the simulated solar panel (or a mains adapter); cold lowers the usable
##            capacity. Empty = «MoveEye wäre jetzt aus».
##   pi_temp  the CPU temperature in the case: outside temperature + own heat (load) + sun on the case.
##   net      a test switch «WLAN weg» / «Internet weg»: MoveEye then treats its push channels as offline (it keeps the
##            alarms and sends them later) - the real network is not touched.
##   clock / place / forecast: the time (date, hour, day counter over midnight in the time-lapse), the place and the gusts
##            MoveEye would get from the weather forecast.
## Settings in user://simwerte.json (own file, main.gd KEEP stays as it is). Time: the simulated time (x «Zeit läuft x-fach»).

var main
var batt_on := true                  # the UPS HAT is simulated (off = MoveEye uses its own values)
var cell_mah := 3450.0               # one cell; 2S: 7.4 V nominal
var mains := false                   # a mains adapter at the HAT (camping: usually not)
var soc := 0.8                       # state of charge 0 … 1 (at 20 °C)
var temp_c := 40.0                   # CPU of the Pi
var hot_test := false                # «Lüftung blockiert»: +30 °C
var wifi := true                     # test switches of the network (MoveEye's view)
var internet := true
var load_w := 4.5
var solar_w := 0.0
var net_w := 0.0                     # + = into the battery
var volts := 7.6
var amps := 0.0
var empty := false
var day_off := 0                     # days since the start (the time-lapse goes over midnight)
var _last_h := -1.0
var _save_t := 0.0
var _dirty := false
var info_label: Label
const FILE := "user://simwerte.json"
const CURVE := [[3.00, 0.0], [3.30, 5.0], [3.50, 15.0], [3.60, 28.0], [3.70, 45.0], [3.80, 60.0], [3.90, 72.0], [4.00, 83.0], [4.10, 93.0], [4.20, 100.0]]


func _ready() -> void:
	if FileAccess.file_exists(FILE):
		var d = JSON.parse_string(FileAccess.get_file_as_string(FILE))
		if typeof(d) == TYPE_DICTIONARY:
			batt_on = bool(d.get("batt_on", batt_on))
			cell_mah = clampf(float(d.get("cell_mah", cell_mah)), 500.0, 6000.0)
			mains = bool(d.get("mains", mains))
			soc = clampf(float(d.get("soc", soc)), 0.0, 1.0)
			if d.has("solar_wp"):
				main.solar_wp = clampf(float(d["solar_wp"]), 0.0, 200.0)
	temp_c = main.ambient + 22.0


func save() -> void:
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f != null:
		f.store_string(JSON.stringify({"batt_on": batt_on, "cell_mah": cell_mah, "mains": mains, "soc": snappedf(soc, 0.001), "solar_wp": main.solar_wp}))
	_dirty = false


func mw_mah() -> float:
	"""Aufräumen 2: the battery size of MoveEye (its setting «ups_mah», sim_state) while it is connected, else -1 (own slider)"""
	if main.now() - main.mw_t > 10.0 or main.mw.get("ups_mah", null) == null:
		return -1.0
	return clampf(float(main.mw.get("ups_mah", cell_mah)), 500.0, 6000.0)


func cell() -> float:
	var m := mw_mah()
	return m if m > 0.0 else cell_mah


func _set_mah(v) -> void:
	if mw_mah() > 0.0:
		return                                        # MoveEye's value counts while it is connected
	cell_mah = clampf(float(v), 500.0, 6000.0)
	save()


func cap_wh() -> float:
	return cell() / 1000.0 * 7.4 * 0.9


func batt_temp() -> float:
	"""the cells sit in the case next to the Pi: a bit warmer than outside"""
	return main.ambient + 0.25 * (temp_c - main.ambient)


func cold_k() -> float:
	"""usable share of the capacity: 100 % from 20 °C, about 85 % at 0 °C, 70 % at -20 °C (lithium cells in the cold)"""
	return clampf(1.0 - (20.0 - batt_temp()) * 0.0075, 0.55, 1.0)


func pct() -> int:
	return int(round(clampf(soc * cold_k(), 0.0, 1.0) * 100.0))


func _cell_v(p: float) -> float:
	for i in range(1, CURVE.size()):
		if p <= float(CURVE[i][1]):
			var a: Array = CURVE[i - 1]
			var b: Array = CURVE[i]
			return float(a[0]) + (float(b[0]) - float(a[0])) * (p - float(a[1])) / maxf(0.01, float(b[1]) - float(a[1]))
	return 4.2


func mw_on() -> bool:
	return main.now() - main.mw_t < 3.0


func pi_load() -> float:
	"""0 … 100: the CPU of MoveEye (share of the PC it runs on, scaled to the 4 cores of the Pi); unknown = 35 %"""
	if not mw_on():
		return 20.0
	var c = null
	var cd = main.mw.get("cpu", null)
	if cd is Dictionary:
		c = cd.get("mw", null)
	if c == null:
		return 35.0
	return clampf(float(c) * float(OS.get_processor_count()) / 4.0, 5.0, 100.0)


func consumption() -> float:
	"""watts the Pi draws from the HAT: Pi 5 + camera, CPU load, servos while moving, lights, loudspeaker"""
	var w := 3.6 + 3.4 * pi_load() / 100.0
	if mw_on():
		var sv: Dictionary = main.mw.get("servo", {}) if main.mw.get("servo") is Dictionary else {}
		var L: Dictionary = main.mw.get("lights", {}) if main.mw.get("lights") is Dictionary else {}
		if bool(sv.get("moving", false)):
			w += 1.6
		if bool(L.get("white", false)):
			w += 0.6
		if bool(L.get("ir", false)):
			w += 1.0
		if str(main.mw.get("sound", "")) != "":
			w += 1.5
	return w


func _process(delta: float) -> void:
	var dt: float = minf(delta, 0.5) * float(main.speed if not main.real_time else 1.0)
	var h: float = main.hour()
	if _last_h >= 0.0 and _last_h > 20.0 and h < 4.0:
		day_off += 1                                    # over midnight (forwards)
	_last_h = h
	# the heat of the Pi: outside + own heat + sun on the case, slow (a few minutes)
	var sr: Dictionary = main.solar_reading()
	var irr: float = clampf(float(sr["v"]) * float(sr["a"]) / maxf(1.0, main.solar_wp), 0.0, 1.0) if main.solar_wp > 0.0 else clampf(sin(deg_to_rad(maxf(0.0, main.sun_el()))), 0.0, 1.0)
	var target: float = main.ambient + 20.0 + 24.0 * pi_load() / 100.0 + 16.0 * irr + (30.0 if hot_test else 0.0)
	temp_c += (minf(target, 92.0) - temp_c) * (1.0 - exp(-dt / 200.0))
	# the battery
	load_w = consumption()
	solar_w = float(sr["v"]) * float(sr["a"])
	var inp: float = solar_w * 0.85 + (18.0 if mains else 0.0)
	net_w = inp - load_w
	if mains:
		net_w = minf(net_w, 15.0)                       # the charger of the HAT: about 2 A
	if not batt_on:
		return
	var was_empty := empty
	if soc >= 1.0 and net_w > 0.0:
		net_w = 0.0                                     # full
	soc = clampf(soc + net_w * dt / 3600.0 / cap_wh(), 0.0, 1.0)
	empty = soc * cold_k() <= 0.002 and net_w <= 0.0
	if empty and not was_empty:
		main.start_info = "Akku leer: MoveEye wäre jetzt aus (der Simulator lädt mit der Sonne oder dem Netzteil wieder)"
	var p: float = clampf(soc * 100.0, 0.0, 100.0)
	volts = 2.0 * _cell_v(p) + (0.12 if net_w > 0.05 else -0.04 * load_w / 5.0)
	amps = net_w / maxf(5.5, volts)
	if main.now() - _save_t > 30.0:
		_save_t = main.now()
		save()
	if info_label != null and Engine.get_process_frames() % 15 == 0:
		info_label.text = main.no_emoji(status_text()).replace("\n ", "\n")   # 3D-4.21: no empty boxes for 🔋 🔌 🌡 (no emoji font)


func _fmt_h(h: float) -> String:
	return "%d h %02d" % [int(h), int(fmod(h, 1.0) * 60.0)]


func status_text() -> String:
	"""the same words and symbols as MoveEye shows them (530 battery line, 598 «🧪»-line) - one look in both"""
	var t := "🧪 Werte für MoveEye"
	if batt_on:
		var line := "🔋 USV-Akku: %d %% · %.2f V · " % [pct(), volts]
		if not mains:
			line = line + "⚡ Akkubetrieb · ca. %s übrig · %.1f W" % [_fmt_h(soc * cap_wh() * cold_k() / maxf(0.5, -net_w)) if net_w < -0.05 else "–", load_w]
		else:
			line = "🔌" + line.substr(2) + ("🔌 lädt" if net_w > 0.05 and soc < 1.0 else "🔌 Netzstrom")
		t += "\n" + line + " · ☀ Solar %.1f W" % solar_w
		if mw_mah() > 0.0:
			t += "\n2 × %d mAh (von MoveEye)" % int(mw_mah())
		if cold_k() < 0.99:
			t += " · ❄ Kälte: nur %d %% nutzbar" % int(round(cold_k() * 100.0))
		if empty:
			t += "\n⏻ Akku leer – das Gerät wäre jetzt aus"
	else:
		t += "\nAkku nicht simuliert – MoveEye nimmt seine eigenen Werte"
	t += "\n🌡 Pi %.0f °C" % temp_c + (" (Lüftung blockiert)" if hot_test else "")
	if not wifi or not internet:
		t += "\n📵 " + ("WLAN weg" if not wifi else "Internet weg") + " – Simulator-Test: Push-Nachrichten warten und werden nachgeschickt"
	return t


func add_controls() -> void:
	"""the controls (card «Sensoren»; also in the Simulator control of MoveEye)"""
	var g := "Sensoren"
	var A := {"sub": "Akku und Strom"}
	main.add_control("toggle", "batt_on", "🔋 Akku simulieren (USV-HAT, 2 × 18650)", func(): return batt_on, func(v): batt_on = bool(v); save(), g, A)
	main.add_control("slider", "batt_level", "Ladung jetzt", func(): return snappedf(soc * 100.0, 1.0), func(v): soc = clampf(float(v) / 100.0, 0.0, 1.0); empty = false; save(), g,
			{"sub": "Akku und Strom", "min": 0, "max": 100, "step": 1, "unit": "%"})
	# one source (Aufräumen 2): while MoveEye is connected its setting «ups_mah» counts - the slider only shows it («von MoveEye»)
	main.add_control("slider", "batt_mah", "Kapazität einer Zelle (verbunden: von MoveEye)", func(): return cell(), _set_mah, g,
			{"sub": "Akku und Strom", "min": 1000, "max": 5000, "step": 50, "unit": "mAh"})
	main.controls[-1]["ro"] = func(): return mw_mah() > 0.0
	main.add_control("toggle", "batt_mains", "🔌 Netzteil angeschlossen (lädt mit etwa 2 A)", func(): return mains, func(v): mains = bool(v); save(), g, A)
	main.add_control("slider", "solar_wp", "☀ Solarpanel (Watt bei voller Sonne)", func(): return main.solar_wp, func(v): main.solar_wp = clampf(float(v), 0.0, 200.0); save(), g,
			{"sub": "Akku und Strom", "min": 0, "max": 100, "step": 1, "unit": "W"})
	main.add_control("toggle", "pi_hot", "🌡 Pi überhitzt (Test: Lüftung blockiert, +30 °C)", func(): return hot_test, func(v): hot_test = bool(v), g, A)
	var N := {"sub": "Netz-Ausfall testen"}
	# on = the outage (blue = active, like the red badge «📵 WLAN weg» in MoveEye); the same switches in the Simulator control of MoveEye
	main.add_control("toggle", "net_wifi_off", "📵 WLAN weg (Test: MoveEye ohne WLAN)", func(): return not wifi, func(v): wifi = not bool(v), g, N)
	main.add_control("toggle", "net_internet_off", "📵 Internet weg (Test: WLAN da, aber kein Internet)", func(): return not internet, func(v): internet = not bool(v), g, N)


func add_info(parent: Control, ui) -> void:
	info_label = ui.small(main.no_emoji(status_text()))
	info_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	parent.add_child(info_label)


func sim_date() -> String:
	"""the date of the scene: today (or the chosen month) + the days the time-lapse went over midnight"""
	var base: float
	if main.season == "today":
		base = Time.get_unix_time_from_system()
	else:
		var y := int(Time.get_date_dict_from_system()["year"])
		base = Time.get_unix_time_from_datetime_dict({"year": y, "month": 1, "day": 1, "hour": 12, "minute": 0, "second": 0}) + (main.day_of_year() - 1) * 86400.0
	return Time.get_date_string_from_unix_time(int(base + day_off * 86400.0))


func reply() -> Dictionary:
	"""the part of world_reply: «battery», «pi_temp», «net», «clock», «place», «forecast»"""
	var la: float = main.ort_lat if main.ort_lat != 0.0 else 46.8
	var lo: float = main.ort_lon if main.ort_lon != 0.0 else 8.2
	var doy: int = main.day_of_year()
	var gust: float = main.wind * (1.6 if main.gusts else 1.25)
	if main.storm_t > 0.0:
		gust = maxf(gust, 75.0 + minf(35.0, (main.now() - main.storm_t) / 60.0))
	var d := {"pi_temp": snappedf(temp_c, 0.1), "net": {"wifi": wifi, "internet": internet and wifi},
			"clock": {"date": sim_date(), "hour": snappedf(main.hour(), 0.0001), "speed": 1.0 if main.real_time else float(main.speed), "tz_h": 2.0 if doy >= 88 and doy < 300 else 1.0},
			"place": {"lat": snappedf(la, 0.0001), "lon": snappedf(lo, 0.0001), "name": main.ort_name if main.ort_name != "" and main.ort_lat != 0.0 else "Schweiz (Mitte)"},
			"forecast": {"gust_kmh": snappedf(gust, 1.0), "weather": main.weather, "storm": main.storm_t > 0.0,
					"tmax": snappedf(main.ambient + 4.0, 0.1), "tmin": snappedf(main.ambient - 5.0, 0.1)}}
	if batt_on:
		var wh := cap_wh() * cold_k()
		d["battery"] = {"v": snappedf(volts, 0.01), "a": snappedf(amps, 0.001), "pct": pct(), "charging": net_w > 0.05 and soc < 1.0,
				"on_battery": not mains, "temp": snappedf(batt_temp(), 0.1), "cap_wh": snappedf(wh, 0.1), "load_w": snappedf(load_w, 0.1),
				"solar_w": snappedf(solar_w, 0.1), "mains": mains, "empty": empty, "full": soc >= 1.0,
				"min_left": int(soc * wh * 60.0 / maxf(0.5, -net_w)) if net_w < -0.05 else null}
	return d
