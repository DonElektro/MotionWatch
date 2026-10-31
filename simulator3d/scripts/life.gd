extends Node
## Daily life (3D-3.27): who comes when. Animals and people come at their own times of the day (fox and badger at
## night, deer at dawn and dusk, squirrels by day ...), and some come every day at about the same time: the neighbour
## with the dog in the morning, the postman, children in the afternoon, a jogger in the evening. MoveEye can learn
## what is «normal». Also: the real weather and the real time of the place (Open-Meteo, no key needed).

var main
var info := ""
var _prev_h := -1.0
var _wx_t := -10000.0
var _wx_busy := false
var _http: HTTPRequest

# hour of the day, kind, name
const EVENTS := [[7.1, "neighbour", "Nachbar mit Hund"], [10.0, "postman", "Briefträger"], [16.2, "children", "Kinder nach der Schule"],
		[19.0, "jogger", "Jogger am Abend"], [21.6, "cat_round", "Katze auf ihrer Runde"]]


func _band(h: float, a: float, b: float) -> bool:
	return h >= a and h < b if a <= b else (h >= a or h < b)


func activity(kind: String, h: float) -> float:
	"""how likely a visitor of this kind is now (1 = normal)"""
	var night := _band(h, 21.5, 5.0)
	var dawn := _band(h, 5.0, 8.5)
	var dusk := _band(h, 18.0, 21.5)
	var day := not night and not dawn and not dusk
	match kind:
		"person", "garden_person", "bench":
			return 0.08 if night else 1.0
		"child":
			return 1.4 if _band(h, 13.0, 19.0) else (0.0 if night or _band(h, 5.0, 7.5) else 0.6)
		"jogger":
			return 1.6 if dawn or dusk else (0.04 if night else 0.5)
		"dogwalk":
			return 2.0 if dawn or dusk else (0.1 if night else 0.7)
		"car", "car_park":
			return 0.25 if night else 1.0
		"fox":
			return 1.6 if night else (1.0 if dawn or dusk else 0.12)
		"boar", "badger", "hedgehog":
			return 1.8 if night else (0.4 if dawn or dusk else 0.02)
		"wolf":
			return 0.7 if night else (0.3 if dawn or dusk else 0.01)
		"marten":
			return 1.4 if night else (0.3 if dawn or dusk else 0.03)
		"deer", "herd", "feed_deer":
			return 2.0 if dawn or dusk else (0.5 if night else 0.25)
		"hare", "feed_hare":
			return 1.6 if dawn or dusk else (0.7 if night else 0.4)
		"cat":
			return 1.3 if night or dusk else 0.6
		"squirrel":
			return 1.4 if day or dawn else 0.0
		"cyclist", "stroller", "couple":                    # 3D-3.39
			return 0.03 if night else (1.2 if day else 0.6)
		"courier":
			return 1.3 if _band(h, 11.0, 13.5) or _band(h, 18.0, 21.5) else (0.0 if night else 0.3)
		"police":
			return 0.6 if night else 0.2
		"drunk":
			return 1.0 if _band(h, 22.0, 3.0) else 0.0
		"cows", "sheep_flock", "cow", "sheep", "horse_walk", "tractor":
			return 0.05 if night else (1.0 if day else 0.4)
		"chamois", "ibex":
			return 1.5 if dawn or dusk else (0.6 if day else 0.1)
		"lynx":
			return 0.6 if night else (0.3 if dawn or dusk else 0.0)
		"bats", "owl":
			return 1.5 if night or dusk else 0.0
		"moto", "van", "camper":
			return 0.2 if night else 1.0
		"burglar":                                          # 3D-3.40: the stories
			return 1.6 if _band(h, 23.0, 4.0) else 0.0
		"bbq":
			return 1.5 if _band(h, 17.5, 21.5) else 0.0
		"homecoming":
			return 1.4 if _band(h, 21.0, 1.0) else (0.4 if dusk else 0.05)
		"parcel":
			return 1.2 if _band(h, 9.0, 17.0) else 0.0
		"fox_trash", "boar_group":
			return 1.5 if night else (0.3 if dawn or dusk else 0.0)
		"kids_tag":
			return 1.3 if _band(h, 14.0, 19.0) else 0.0
		"mowing":
			return 1.0 if _band(h, 8.0, 18.0) else 0.0
	return 1.0


func pick(kinds: Array) -> String:
	var h: float = main.hour()
	var tot := 0.0
	var w := []
	var cal := calendar()
	for k in kinds:
		var a := activity(str(k), h)
		if main.tiere != null:
			a *= main.tiere.season_k(str(k))              # Paket «Tiere»: hedgehog and bats sleep in winter, the badger rests
		if str(k) in main.PEOPLE_KINDS or str(k) in ["bbq", "homecoming", "parcel", "kids_tag", "burglar"]:
			a *= cal
		w.append(a)
		tot += a
	if tot <= 0.0:
		return ""
	var r := randf() * tot
	for i in range(kinds.size()):
		r -= float(w[i])
		if r <= 0.0:
			return str(kinds[i])
	return str(kinds[-1])


func _crossed(a: float, b: float, x: float) -> bool:
	if a < 0.0:
		return false
	if b >= a:
		return x > a and x <= b
	return x > a or x <= b                                       # over midnight


func _quiet() -> bool:
	"""no daily visitors during a test run or a game round"""
	return (main.testrun != null and main.testrun.running) or (main.game != null and main.game.round_state in ["countdown", "play"])


func _process(_dt: float) -> void:
	if main == null or not main.is_inside_tree():
		return
	var h: float = main.hour()
	if main.daily_life and main.auto_visitors and not _quiet():
		for e in EVENTS:
			if _crossed(_prev_h, h, float(e[0])):
				_event(str(e[1]), str(e[2]))
	_prev_h = h
	if main.real_time and main.busy_with() == "":       # 3D-3.88: a test sets its own time
		var t := Time.get_time_dict_from_system()
		var lh := float(t["hour"]) + float(t["minute"]) / 60.0 + float(t["second"]) / 3600.0
		if main.speed != 1.0 or abs(h - lh) > 0.03 and abs(h - lh) < 23.97:
			main.speed = 1.0
			main.set_hour(lh)
	if main.real_weather and main.now() - _wx_t > 600.0 and not _wx_busy and main.busy_with() == "":
		_wx_t = main.now()
		_fetch_weather()


func _event(k: String, name: String) -> void:
	var door: Vector3 = main.obj["door"]
	var near: Vector3 = door + Vector3(0, 0, 1.2) if door != Vector3.ZERO else main.head.global_position + Vector3(1.5, 0, -3.0)
	near.y = 0.0
	match k:
		"neighbour":
			main.visit("dogwalk")
		"postman":
			var side := 1.0 if randf() < 0.5 else -1.0
			var start := Vector3(side * 40.0, 0, near.z - 14.0)
			var p = main.spawn("person", start, near)
			p.speed = 1.5
			p.route = [[near, 6.0, 0.0], start + Vector3(-side * 6.0, 0, 0)]
		"children":
			var a = main.spawn("child")
			var b = main.spawn("child", a.position + Vector3(1.2, 0, 0.6), a.target + Vector3(1.2, 0, 0.6))
			b.speed = a.speed
		"jogger":
			main.spawn("jogger")
		"cat_round":
			main.spawn("cat")
	info = "%02d:%02d %s" % [int(main.hour()), int(fmod(main.hour(), 1.0) * 60.0), name]


# ---- the real weather of the place (Open-Meteo) --------------------------------------------------------------------
func _fetch_weather() -> void:
	_wx_busy = true
	var la: float = main.ort_lat if main.ort_lat != 0.0 else 46.8
	var lo: float = main.ort_lon if main.ort_lon != 0.0 else 8.2
	if _http == null:
		_http = HTTPRequest.new()
		_http.timeout = 20.0
		add_child(_http)
	var u := "https://api.open-meteo.com/v1/forecast?latitude=%.4f&longitude=%.4f&current=temperature_2m,relative_humidity_2m,weather_code,cloud_cover,wind_speed_10m,surface_pressure&timezone=auto" % [la, lo]
	var err := _http.request(u, PackedStringArray(["User-Agent: MotionWatch3D-Simulator/%s" % str(main.VERSION)]))
	if err != OK:
		info = "Wetter: keine Anfrage möglich"
		_wx_busy = false
		return
	var r: Array = await _http.request_completed
	_wx_busy = false
	if int(r[0]) != HTTPRequest.RESULT_SUCCESS or int(r[1]) != 200:
		info = "Wetter: keine Verbindung zu open-meteo.com"
		_wx_t = main.now() - 480.0                               # try again in 2 minutes
		return
	var j = JSON.parse_string((r[3] as PackedByteArray).get_string_from_utf8())
	if typeof(j) != TYPE_DICTIONARY or typeof(j.get("current")) != TYPE_DICTIONARY:
		info = "Wetter: unerwartete Antwort"
		return
	apply_weather(j["current"])


func apply_weather(c: Dictionary) -> void:
	var code := int(c.get("weather_code", 0))
	var wx := "clear"
	if code in [2, 3]:
		wx = "cloudy"
	elif code in [45, 48]:
		wx = "fog"
	elif (code >= 51 and code <= 67) or (code >= 80 and code <= 82) or code >= 95:
		wx = "rain"
	elif (code >= 71 and code <= 77) or code in [85, 86]:
		wx = "snow"
	elif int(c.get("cloud_cover", 0)) > 60:
		wx = "cloudy"
	main.weather = wx
	main.wind = clampf(float(c.get("wind_speed_10m", main.wind)), 0.0, 120.0)
	main.ambient = clampf(float(c.get("temperature_2m", main.ambient)), -15.0, 40.0)
	main.humidity = clampf(float(c.get("relative_humidity_2m", main.humidity)), 10.0, 100.0)
	main.pressure = clampf(float(c.get("surface_pressure", main.pressure)), 960.0, 1040.0)
	info = "Echtes Wetter: %s, %.0f °C, Wind %.0f km/h" % [{"clear": "klar", "cloudy": "bewölkt", "rain": "Regen", "fog": "Nebel", "snow": "Schnee"}[wx], main.ambient, main.wind]
	main._sync_ui()


func calendar() -> float:
	"""more people at the weekend, fewer in winter, more in summer (3D-3.40)"""
	if not main.calendar_on:
		return 1.0
	var f := 1.0
	var wd := int(Time.get_date_dict_from_system()["weekday"])         # 0 = Sunday
	if wd == 0 or wd == 6:
		f *= 1.5
	var d: int = main.day_of_year()
	if d < 60 or d > 334:
		f *= 0.5
	elif d > 152 and d < 244:
		f *= 1.3
	return f
