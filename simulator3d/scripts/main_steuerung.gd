extends Object
## Teil von main.gd (Vorschlag 24 «main.gd zerlegen»): die Fernsteuerung: alle /control-Aktionen (Fenster, Web-Seite von MoveEye, Tests).
## main.gd lädt diesen Teil erst beim ersten Aufruf (_mod) und leitet seine Funktionen weiter: main.xyz bleibt gleich.
## Hier steht «main.» vor allem, was zu main.gd gehört.

var main                              # main.gd
const Kompakt := preload("res://scripts/kompakt.gd")
const Worlds := preload("res://scripts/worlds.gd")


func _control(d: Dictionary) -> Dictionary:
	var a := str(d.get("action", "get"))
	var cid := str(d.get("id", ""))
	if a == "scenario":
		main.solo_scene = cid if bool(d.get("solo", false)) else ""   # 3D-4.x: this scene alone, without its world (training night)
		if not main.set_scene(cid):
			return {"ok": false, "error": "unknown scenario"}
	elif a == "welt":                                  # 3D-4.x Welten: the worlds, their places and what is loaded (worlds.gd)
		return Worlds.info(main)
	elif a == "delete":
		return {"ok": false, "error": "cannot be deleted"}
	elif a == "kopf":                                  # 639t: the one header - state, or {"press": id} like a click
		if main.kopf == null:
			return {"ok": false, "error": "no header"}
		if d.has("press"):
			main.kopf.press(str(d["press"]), main.kopf.btns.get(str(d["press"]), main.kopf.btns.get("menu")))
		return {"ok": true, "kopf": main.kopf.state()}
	elif a == "lang":                                  # Sprachen (i18n.gd): switch / translate, for tests
		return preload("res://scripts/i18n.gd").control(d)
	elif a == "ui_width":                              # for tests: is the content of the panel wider than the panel?
		main._fold_all("open")
		var sim_was = main.ui_simple
		main.set_simple(false)
		var w = main.ui_box.get_combined_minimum_size().x
		main.set_simple(sim_was)
		var wide := []
		var stack: Array = [main.ui_box]
		while not stack.is_empty():
			var n: Node = stack.pop_back()
			for ch in n.get_children():
				if ch is Control and ch.visible:
					var mw_: float = ch.get_combined_minimum_size().x
					if mw_ > 330.0:
						wide.append("%s %s %d" % [ch.get_class(), str(ch.get("text")).left(30), int(mw_)])
					stack.append(ch)
		return {"ok": true, "content_min": w, "panel": main.ui_root.size.x, "scroll_space": main.ui_box.get_parent().size.x, "wide": wide}
	elif a == "world":                                 # for tests: life in the world
		var sm := []
		for n in main.get_tree().get_nodes_in_group("smoke"):
			sm.append([n.emitting, n.global_position, n.visible, n.is_visible_in_tree()])
		return {"ok": true, "smoke": str(sm), "fireflies": [main.fireflies.emitting, main.fireflies.is_visible_in_tree()], "cloth": main.get_tree().get_nodes_in_group("cloth").size()}
	elif a == "busy":                                  # one lock with MoveEye: who has the world right now ('' = free)
		if bool(d.get("with_mw", false)):              # for tests / display: also what MoveEye itself does
			main._ctl_frame = -1
		return {"ok": true, "busy": main.busy_with(str(d.get("except", "")))}
	elif a == "test_report":                           # the test run: progress and the last report
		return main.testrun.state()
	elif a == "test_start":                            # MoveEye starts a test run (3D-3.27): {"plan": "standard" | "quick" | "hard" | "night"}
		var err: String = main.testrun.start(str(d.get("plan", main.testrun.plan)), d.get("cams", []) if typeof(d.get("cams", [])) == TYPE_ARRAY else [], int(d.get("mult", 1)), int(d.get("seed", 1)))
		var st: Dictionary = main.testrun.state()
		st["ok"] = err == ""
		if err != "":
			st["error"] = err
		return st
	elif a == "test_stop":
		main.testrun.stop(false)
		return main.testrun.state()
	elif a == "game":                                  # for tests: the game (players, meter, round)
		var ps := []
		for p in main.game.players:
			if p != null:
				ps.append({"slot": p["slot"], "name": p["name"], "x": snappedf(p["actor"].position.x, 0.01), "z": snappedf(p["actor"].position.z, 0.01),
						"susp": snappedf(p["susp"], 0.1), "seen": p["seen"], "state": p["state"], "caught": p["caught"], "posture": p["actor"].ctl_posture,
						"online": p["sock"] != null, "vis": snappedf(main.game.visibility(p), 0.01), "cams": main.game.vis_debug(p)})
		return {"ok": true, "open": main.game.open, "round": main.game.round_state, "players": ps, "guard": main.game.guard_auto, "guard_yaw": snappedf(main.game.guard_yaw, 0.01),
				"goal": [snappedf(main.game.goal.x, 0.01), snappedf(main.game.goal.z, 0.01)], "address": main.game.address(),
				"items": main.game.items.map(func(it): return [snappedf(it["pos"].x, 0.1), snappedf(it["pos"].z, 0.1), it["by"], snappedf(it["pos"].y, 0.01), snappedf(main.ground_y(it["pos"].x, it["pos"].z), 0.01)]),
				"goal_y": [snappedf(main.game.goal.y, 0.01), snappedf(main.ground_y(main.game.goal.x, main.game.goal.z), 0.01)], "insects": main.insects.emitting,
				"powers": main.game.powers.map(func(w): return [w["kind"], snappedf(w["pos"].x, 0.1), snappedf(w["pos"].z, 0.1), float(w["back"]) > 0.0]),
				"last_minute": main.game.last_minute,
				"hides": main.game.hides.map(func(h): return [snappedf(h["pos"].x, 0.1), snappedf(h["pos"].z, 0.1)]),
				"cps": main.game.checkpoints.map(func(h): return [snappedf(h["pos"].x, 0.1), snappedf(h["pos"].z, 0.1)]),
				"ev": main.game.ev_kind, "gallery": main.game.gallery.size(), "board": main.game.board_list(), "hour": snappedf(main.hour(), 0.1)}
	elif a == "game_put":                              # for tests: put a player somewhere
		var p2 = main.game.players[clampi(int(d.get("slot", 0)), 0, 3)]
		if p2 == null:
			return {"ok": false, "error": "no such player"}
		p2["actor"].position = main.free_spot(Vector3(float(d.get("x", 0.0)), 0, float(d.get("z", 0.0))), 0.4, true)
		return {"ok": true}
	elif a == "ui_scroll":                             # for tests: fold the cards (open / close / groups) and scroll the panel
		if d.has("fold"):
			main._fold_all(str(d["fold"]))
		if d.has("simple"):
			main.set_simple(bool(d["simple"]))
		if d.has("open"):                                  # one card open, with all its parts
			for b in main.fold_bodies:
				if str(b.get_meta("title", "")) == str(d["open"]):
					main.UI.set_open(b, true)
					for sb in main.sub_bodies:
						if b.is_ancestor_of(sb):
							main.UI.set_sub_open(sb, true)
		main.show_panel(true)
		if d.has("y"):
			main._test_scroll(float(d["y"]))
		elif d.has("open") and d.get("top", false):        # P1 ui_gemeinsam (tests, Bildschirmfotos): die geöffnete Karte nach oben
			for b in main.fold_bodies:
				if str(b.get_meta("title", "")) == str(d["open"]) and b.get_parent() != null:
					main._test_scroll_to(b.get_parent())
		return {"ok": true, "max": (main.ui_box.get_parent() as ScrollContainer).get_v_scroll_bar().max_value}
	elif a == "tunnel":                                # 3D-3.45: for tests / remote: {"host", "code", "on"}
		if d.has("host"):
			main.tunnel_host = str(d["host"])
			main.tunnel.host = main.tunnel_host
		if d.has("code"):
			main.tunnel_code = str(d["code"])
			main.tunnel.code = main.tunnel_code
		if d.has("on"):
			main.tunnel_on = bool(d["on"])
			main.tunnel.set_on(false)
			main.tunnel.set_on(main.tunnel_on)
		var tst: Dictionary = main.tunnel.state()
		tst["ok"] = true
		return tst
	elif a == "dataset":                               # Trainingsbilder (3D-3.44)
		var op2 := str(d.get("op", "get"))
		if op2 == "start":
			return main.dataset.start(int(d.get("n", 40)), d.get("conds", []) if typeof(d.get("conds", [])) == TYPE_ARRAY else [])
		if op2 == "game":                                # 3D-3.53: the «missed» pictures of the game
			return main.dataset.load_game()
		if op2 == "export":                              # 3D-3.74: a training set (YOLO) for an own AI model
			return main.dataset.export_pack(int(d.get("n", 500)), bool(d.get("scenes", true)), str(d.get("vielfalt", "")))
		if op2 == "stop":
			main.dataset.stop()
		if op2 == "packs" or op2 == "clean":            # «KI-Daten aufräumen» (kidaten.gd)
			var KD = preload("res://scripts/kidaten.gd")
			if op2 == "packs":
				return KD.state()
			if main.dataset.busy or main.kitrain.running:
				return KD.state({"ok": false, "error": "busy"})
			return KD.state(KD.aufraeumen(true, str(main.dataset.last_pack.get("dir", "")).get_file()))
		var st2: Dictionary = main.dataset.state()
		if op2 == "list":
			st2["items"] = main.dataset.list()
		return st2
	elif a == "kitrain":                               # «KI trainieren»: get / start {n, vielfalt, dry} / upload {dry}
		var op3 := str(d.get("op", "get"))
		if op3 == "start":
			return main.kitrain.start(int(d.get("n", 200)), str(d.get("vielfalt", main.dataset.vielfalt)), bool(d.get("dry", false)))
		if op3 == "upload":
			return main.kitrain.upload_last(bool(d.get("dry", false)))
		return main.kitrain.state()
	elif a == "netmap":                                # Empfangskarte (3D-3.44): measured spots as patches on the ground
		return {"ok": true, "n": main.show_netmap(d.get("points", []))}
	elif a == "replay":                                # Alarm-Rückblick in 3D (3D-3.44)
		if bool(d.get("stop", false)):
			main.replay.stop()
			return {"ok": true}
		if typeof(d.get("track")) != TYPE_DICTIONARY:
			return {"ok": false, "error": "track missing"}
		return main.replay.start(d["track"])
	elif a == "pruefstand":                            # Prüfstand (3D-3.49): get / open / start (for tests)
		var w_: String = str(d.get("do", "get"))
		if w_ == "open":
			main.pruef.open(true)
		elif w_ == "start":
			main.pruef.open(true)
			for k_ in main.pruef.plan_cbs:
				main.pruef.plan_cbs[k_].button_pressed = k_ in (d.get("plans", ["quick"]) as Array)
			main.pruef.reps.value = int(d.get("reps", 1))
			main.pruef.start()
		elif w_ == "send":
			main.pruef.send()
		elif w_ == "auto":                             # 3D-3.75: {on} - automatically after every update of MoveEye
			main.pruef.set_auto(bool(d.get("on", true)))
			if d.has("last"):
				var ad: Dictionary = main.pruef._auto_data()
				ad["last"] = str(d["last"])
				main.pruef._auto_save(ad)
			if d.has("touch_ago"):
				main.pruef._touch_t = main.now() - float(d["touch_ago"])
		return main.pruef.state()
	elif a == "planner":                               # Aufstell-Planer (3D-3.44): get / open / close / best / put
		var op := str(d.get("op", "get"))
		if op == "open":
			main.planner.open(true)
		elif op == "close":
			main.planner.open(false)
		elif op == "best":
			if not main.planner.visible:
				main.planner.open(true)
			main.planner.search_best()                    # runs on over a few frames; "busy" in the answer
		elif op == "put":
			main.planner.place_here()
		elif op == "home":
			main.set_home(Vector3.ZERO, 0.0)
		return main.planner.state()
	elif a == "tv":                                    # TV mode (3D-3.44): {"on": true/false, "info_url": "...", "fullscreen": true}
		if d.has("info_url"):
			main.tv.info_url = str(d["info_url"]).substr(0, 200)
		if d.has("on"):
			main.tv.set_on(bool(d["on"]), bool(d.get("fullscreen", true)))
		return {"ok": true, "tv": main.tv.state()}
	elif a == "ui_wide":                               # for tests: which parts of the panel are wider than it (3D-3.43)
		var lim := float(d.get("w", 360.0))
		var out := []
		var stack: Array = [main.ui_root]
		while stack.size() > 0:
			var n = stack.pop_back()
			if n is Control:
				var w: float = (n as Control).get_combined_minimum_size().x
				if w > lim and (n as Control).is_visible_in_tree():
					var t := ""
					if n is Label or n is Button:
						t = str(n.text).substr(0, 40)
					out.append([n.get_class(), int(w), t, str(n.get_path()).right(80)])
			for ch in n.get_children():
				stack.append(ch)
		return {"ok": true, "panel": [int(main.ui_root.size.x), int(main.ui_root.position.x)], "win": main.get_viewport().get_visible_rect().size, "wide": out.slice(0, 60), "float": [main.cam_float.position, main.cam_float.size, main.cam_float.visible] if main.cam_float != null else []}
	elif a == "geo":                                   # for tests: the place (loading, what was built)
		return {"ok": true, "busy": main.geo.busy, "loaded": main.geo.loaded, "info": main.geo.info, "counts": main.geo.counts, "terrain": main.terrain,
				"h0": main.geo.h0, "src": main.geo.dem_source, "note": main.geo_note, "y": main.ground_y(float(d.get("x", 0.0)), float(d.get("z", 0.0))),
				"map": main.karte.visible, "map_info": main.karte.status_text(), "dark": main.is_dark(), "anims": main.anims.size(), "b3d_night": main.geo.b3d_mat.get_shader_parameter("night") if main.geo.b3d_mat != null else -1, "sun": [snappedf(main.sun_pos().x, 0.1), snappedf(main.sun_pos().y, 0.1),
				snappedf(main.horizon_el(main.sun_pos().y), 0.1), main.sun_behind_hills(), snappedf(main.sun.light_energy, 0.01)]}
	elif a == "map":                                   # for tests: open the map at a place, zoom
		main.show_panel(false)
		main.karte.open(float(d.get("lat", 46.95)), float(d.get("lon", 7.44)), int(d.get("zoom", 0)))
		return {"ok": true}
	elif a == "wizard":                                # for tests: the place wizard (karte.gd) step by step
		var op := str(d.get("op", ""))
		if op == "pick":
			main.karte.sel = Vector2(float(d.get("lat", 46.95)), float(d.get("lon", 7.45)))
			main.karte.sel_name = str(d.get("name", ""))
			main.karte._show_step(1)
		elif op == "next":
			main.karte._next()
		elif op == "set":
			main.karte.set("w_" + str(d.get("key", "")), d.get("value"))
			main.karte._show_step(main.karte.step)
		return {"ok": true, "step": main.karte.step, "env": main.geo.env, "why": main.geo.env_why, "info": main.karte.info.text, "waiting": main.karte.waiting,
				"counts": main.geo.counts, "ort_env": main.ort_env, "visible": main.karte.visible}
	elif a == "input":                                 # the simulator window seen in MoveEye: mouse / finger / keys from there
		var ev = d.get("ev", [])
		return {"ok": true, "n": main.view_input(ev if ev is Array else [])}
	elif a == "game_handicap":                         # MoveEye: handicap for a player (0 … 2)
		main.game.set_handicap(int(d.get("slot", -1)), int(d.get("level", 0)))
		return {"ok": true}
	elif a == "view_look":                             # the phone as a window (3D-3.27): turn the phone = look round in the free view
		main._to_free_view()
		if d.get("start", false) or main._look_base.is_empty():
			main._look_base = [main.view_cam.rotation.y, main.view_cam.rotation.x]
		var yw = float(main._look_base[0]) + deg_to_rad(clampf(float(d.get("yaw", 0.0)), -360.0, 360.0))
		var pt = clampf(float(main._look_base[1]) + deg_to_rad(float(d.get("pitch", 0.0))), deg_to_rad(-85.0), deg_to_rad(60.0))
		main.view_cam.rotation = Vector3(pt, yw, 0)
		main.view_want_t = main.now()
		return {"ok": true}
	elif a == "game_compare":                          # 3D-4.x: «Mensch gegen KI» (gamecompare.gd) - state / start / stop
		return main.game.cmp.command(d) if main.game != null and main.game.cmp != null else {"ok": false, "error": "not supported"}
	elif a == "game_kig":                              # 3D-4.x: «MoveEye als KI-Wächter» (gamekiwaechter.gd): info / set / reset
		return main.game.kig.command(d) if main.game != null and main.game.kig != null else {"ok": false, "error": "no game"}
	elif a == "game_shut":                             # 3D-4.x: «Auslöser» (gameshutter.gd) - info / aim / fire, for tests
		return main.game.shut.command(d) if main.game != null and main.game.shut != null else {"ok": false, "error": "no game"}
	elif a == "game_more":                             # «Gameplay ausfeilen» (gamemore.gd): info / set / probe … (tests, MoveEye)
		return main.game.more.command(d) if main.game != null and main.game.more != null else {"ok": false, "error": "no game"}
	elif a == "game_tool":                             # 3D-4.x: a tool of the guard (gametools.gd): {tool, slot} or {op: "info"}
		return main.game.tools.command(d) if main.game != null and main.game.tools != null else {"ok": false, "error": "no game"}
	elif a == "game_rules":                            # 3D-4.x: for tests - fairness, next guard, winner (gamerules.gd)
		var grd: Dictionary = main.game.rules.debug() if main.game != null and main.game.rules != null else {}
		grd["ok"] = not grd.is_empty()
		return grd
	elif a == "game_test":                             # 3D-3.52: for tests - where a player is in the head camera / move him there
		if main.game == null or not d.has("slot") or int(d["slot"]) < 0 or int(d["slot"]) >= main.game.players.size() or main.game.players[int(d["slot"])] == null:
			return {"ok": false, "error": "no player"}
		var gp: Dictionary = main.game.players[int(d["slot"])]
		if d.has("x") and d.has("z"):
			gp["actor"].position = Vector3(float(d["x"]), main.ground_y(float(d["x"]), float(d["z"])), float(d["z"]))
		if d.get("hit", false):
			main.game._caught(gp, null)
		var hp: Vector3 = main.cams[0].global_position
		var ap: Vector3 = gp["actor"].position
		return {"ok": true, "box": main.game.learn.box(gp), "sees": main.game.cam_sees(gp, 0), "state": gp["state"], "fx": main.game.fx_nodes.size(),
				"head": [hp.x, hp.y, hp.z], "pos": [ap.x, ap.y, ap.z], "goal": [main.game.goal.x, main.game.goal.z], "report": main.game.learn.report_dict() if d.get("report", false) else {}}
	elif a == "padview":                               # the «Controller-Ansicht» of MoveEye (padview.gd)
		return main.padview.command(d) if main.padview != null else {"ok": false, "error": "no padview"}
	elif a == "pad":                                   # 3D-3.59: a game controller at the browser (MoveEye page): axes and buttons
		if main.explore == null:
			return {"ok": false, "error": "no explore"}
		main.explore.remote_pad(d.get("ax", []), d.get("bt", []), str(d.get("name", "")))
		if d.has("hold"):                              # for tests on a slow PC: the values stay valid for «hold» s
			main.explore.rp_t = main.now() + clampf(float(d["hold"]), 0.0, 30.0)
		return {"ok": true, "on": main.explore.on, "view": main.explore.view, "rumble": main.padmap.take_web_rumble() if main.padmap != null else ""}
	elif a == "padmap":                                # 3D-4.13: the controller mapping (tests): state, act, menu, roles, help, rumble
		return main.padmap.command(d) if main.padmap != null else {"ok": false, "error": "no padmap"}
	elif a == "patrol":                                # 3D-3.61: «Patrouille» (for tests and remote): {on, points: [[x, z], …], area: [x, z, w, d], mode}
		if main.patrol == null:
			return {"ok": false, "error": "no patrol"}
		if d.has("points"):
			main.patrol.points = []
			for q in d["points"]:
				main.patrol.points.append(Vector2(float(q[0]), float(q[1])))
			main.patrol.mode = "points"
			main.patrol._dirty = true
		if d.has("area"):
			var ar: Array = d["area"]
			main.patrol.area = Rect2(float(ar[0]), float(ar[1]), float(ar[2]), float(ar[3]))
			main.patrol.mode = "area"
			main.patrol._dirty = true
		if d.has("mode"):
			main.patrol.mode = str(d["mode"])
		if d.has("guard"):                             # 3D-3.76: {guard: [x, z, radius, name]} - plan the route round it and start
			var gd: Array = d["guard"]
			main.patrol.guard_start(Vector2(float(gd[0]), float(gd[1])), float(gd[2]) if gd.size() > 2 else 10.0, str(gd[3]) if gd.size() > 3 else "Ort")
		if d.has("ask"):
			main.patrol.ask()
		if d.has("on"):
			main.patrol.set_active(bool(d["on"]))
		return main.patrol.state_dict()
	elif a == "explore":                               # 3D-3.55: explore with the rover (for tests and remote)
		if main.explore == null:
			return {"ok": false, "error": "no explore"}
		if d.has("on"):
			main.explore.set_on(bool(d["on"]))
		if d.has("view") and str(d["view"]) in main.explore.VIEWS:
			main.explore.view = str(d["view"])
		if d.has("invite"):
			main.explore.set_invite(bool(d["invite"]))
		if d.has("spectate"):
			main.explore.spectator(bool(d["spectate"]))
		if d.has("place"):                               # [x, z]: the rover there (3D-3.60)
			var pl: Array = d["place"]
			if main.mover_on:
				main.rig.position = Vector3(float(pl[0]), main.ground_y(float(pl[0]), float(pl[1])), float(pl[1]))
			else:
				main.home_pos = Vector3(float(pl[0]), 0, float(pl[1]))
				main.mover_home()
		if d.has("drive"):                             # [forward, turn, seconds] for a test drive
			var dv: Array = d["drive"]
			main.explore.test_drive = Vector2(float(dv[0]), float(dv[1]))
			main.explore.test_until = main.explore.main.now() + (float(dv[2]) if dv.size() > 2 else 2.0)
		return main.explore.state()
	elif a == "inventar":                              # 3D-3.86: {do: info | open | close | add (kind, x, z, r) | clear}
		var iv := str(d.get("do", "info"))
		if iv == "open":
			main.inventar.open()
			if d.has("tab"):
				main.inventar.tabs.current_tab = int(d["tab"])
		elif iv == "close":
			main.inventar.close()
		elif iv == "add":
			main.inventar.add_object(str(d.get("kind", "")), Vector3(float(d.get("x", 0)), 0, float(d.get("z", -8))), float(d.get("r", 0)))
		elif iv == "clear":
			main.inventar.clear_scene()
		return {"ok": true, "inventar": main.inventar.info()}
	elif a == "blindmap":                              # 3D-3.85: makeover 22 / 23 {do: start (az, dist, hour, walk) | info | stop}
		var bd := str(d.get("do", "info"))
		if bd == "game":                               # 3D-3.90: the blind spots the players found (az°, m), for MoveEye's map
			return {"ok": true, "pts": main.game.learn.blind_pts if main.game != null and main.game.learn != null else [],
					"badges": main.game.badges_all() if main.game != null else {}}                       # 3D-3.92: the badges of the players
		if bd == "start":
			return main.blindmap.start(d)
		if bd == "stop":
			main.blindmap.stop()
		return main.blindmap.info()
	elif a == "farecreate":                            # 3D-3.85: makeover 21 - re-enact the cause of a false alarm
		return main.farecreate(d)
	elif a == "rover":                                 # 3D-3.84: makeover 17 {do: info | patrol (on) | alarm | dock | goto (x, z)}
		var rd := str(d.get("do", "info"))
		if rd == "patrol":
			main.patrol.set_active(bool(d.get("on", true)))
		elif rd == "alarm":
			var ap = main.patrol.alarm_point()
			main.patrol.goto_point(ap, "alarm")
		elif rd == "dock":
			main.patrol.goto_point(Vector2(main.home_pos.x, main.home_pos.z), "dock")
		elif rd == "goto":
			main.patrol.goto_point(Vector2(float(d.get("x", 0)), float(d.get("z", -8))), "goto")
		return {"ok": true, "rover": main.patrol.rover_info()}
	elif a == "overlay":
		return {"ok": true, "overlay": main.overlay.info()}
	elif a == "kompakt":                               # 3D-4.x: the four compact scenes {do: info | spot (value) | perf} (kompakt.gd)
		return Kompakt.control(main, d)
	elif a == "bergtal":                               # 3D-4.x: {do: info | spot | bed | season | here | goto | event | ride | morning | rate | horn | perf} (bergtal.gd)
		return preload("res://scripts/bergtal.gd").control(main, d)
	elif a == "vorfuehrung":                           # Vorführmodus «Maggie» (maggie_vorfuehrung.gd): {do: start (len) | pause | weiter | kapitel (n) | stop | info}
		return preload("res://scripts/maggie_vorfuehrung.gd").control(main, d)
	elif a == "trailer":                               # Trailer der Geschichten (trailer.gd): {do: start (id, sprache, untertitel, ab) | stop | info}
		return preload("res://scripts/trailer.gd").control(main, d)
	elif a == "maggie":                                # «Maggie und der Bergkristall» (maggie_story.gd): {do: info | open | start | region …}
		return main.maggie.control(d) if main.maggie != null else {"ok": false, "error": "no maggie"}
	elif a == "horror":                                # Bergtal · Horror-Modus: {do: info | open | unlock | start | skip | pause | stop …} (bergtal_horror.gd)
		return main.horror.command(d) if main.horror != null else {"ok": false, "error": "no horror"}
	elif a == "ferienpark":                            # 3D-4.x: {do: info | spot (value) | kinds | perf} (ferienpark.gd)
		return preload("res://scripts/ferienpark.gd").control(main, d)
	elif a == "szenen":                                # 3D-4.x: the new scenes {do: info | spawn (kind) | restore}
		return main.szenen.control(d)
	elif a == "simreal":                               # 3D-4.4: {do: info | set (key, value) | sweep | bird | spawn (kind, from, to)}
		return main.simreal.control(d)
	elif a == "camphys":                               # 3D-4.x P1: {do: info | set (key: blur_k | noir_k, value)} - exposure, gain, light
		return main.camphys.control(d)
	elif a == "objekte":                               # 3D-4.x «Gegenstände»: {do: info | lure | test_place | test_clear | set}
		return main.objplus.control(d)
	elif a == "wind_fx":                               # F6: {do: info | set (on)}
		return main.wind_fx.control(d)
	elif a == "inhalte":                               # F2: {do: info | set (value) | laden | anwenden | zuruecksetzen}
		return main.inhalte.control(d)
	elif a == "umgebung":                              # 3D-4.x: {do: info | set (key, value) | spawn (kind) | snow_puff | clear_tracks}
		return main.umgebung.control(d)
	elif a == "statisten":                             # Paket «Statisten»: {do: info | set (mode, value) | spawn (n, group) | clear}
		return main.statisten.control(d)
	elif a == "menschen":                              # P10: {do: info | set (key, value) | spawn (kind) | api (id, fn, args) | probe (gait, dist, dark)}
		return main.menschen.control(d)
	elif a == "tiere":                                 # Paket «Tiere»: {do: info | spawn (kind, from, to) | threat (x, z, secs) | curl | pounce | car}
		return main.tiere.control(d)
	elif a == "fahrzeuge":                             # Paket «Fahrzeuge»: {do: info | set | spawn | arrive | toward | leave | reset}
		return main.fahrzeuge.control(d)
	elif a == "maggie_gefahr":                         # «Maggie und der Bergkristall» S3: böse Tiere, Schutzdinge (maggie_gefahr.gd)
		return load("res://scripts/maggie_gefahr.gd").control(main, d)
	elif a == "maggie_hund":                           # «Maggie und der Bergkristall», Paket S2: {do: info | start (region) | befehl (f) | spieler | loesen | stop}
		return preload("res://scripts/maggie_hund.gd").control(main, d)
	elif a == "licht":                                 # «Licht & Nacht»: {do: info | set | sources (cam) | lux | attach | headlights | at}
		return main.licht.control(d)
	elif a == "jahreszeiten":                          # «Jahreszeiten»: {do: info | set (key, value) | sun (doy, lat, lon) | year}
		return main.jahreszeiten.control(d)
	elif a == "gelaende":                              # 3D-4.x: {do: info | set (key, value) | height (x, z) | los (from, to) | cloud (x, z)}
		return main.gelaende.control(d)
	elif a == "wetter":                                # real-wetter: {do: info | set | flash | wipe | splash | fog | snow | morning}
		return main.wetter.control(d)
	elif a == "weit":                                  # 3D-4.17: wide camera {mount, tilt, tilt_follow, fisheye, pan_limit, do: info | probe | spawn}
		return main.weit.control(d)
	elif a == "nacht":                                 # Nacht-Testlauf: {do: info | start | stop | state | truth | plan} (nachtlauf.gd)
		return main.nacht.control(d)
	elif a == "abenteuer":                             # Bergtal-Abenteuer: {do: state | open | start | pick | next | choose | night | save | replay | report …}
		return main.abenteuer.op(d)
	elif a == "parcours":                              # 3D-4.18: {do: info | start (lessons, night, seed, prep_s) | stop | state | result | game | steer ...}
		return main.parcours.control(d)
	elif a == "privat":                                # Wunsch Nr. 2: {} -> the private circle, how many visitors keep off it
		return main.privat.control(d)
	elif a == "einbruch":                              # {do: info | start (ablauf, seed, zeit) | serie | stop | state | result}
		return main.einbruch.control(d)
	elif a == "zwilling":                              # 3D-4.4: {do: info | import (path) | set (key, value) | item (k, x, z, r) | clear | remove | on}
		return main.zwilling.control(d)
	elif a == "fotomodus":                             # 3D-4.27: {do: info | on | set | mask_rect | mask_clear | more | measure | size | debug}
		return main.zwilling.fm.control(d)
	elif a == "whatif":                                # 3D-3.83: makeover 8 - MoveEye re-enacts a real recording
		return main.whatif(d)
	elif a == "twin":                                  # 3D-3.83: makeover 9 - the twin of the real place
		if str(d.get("op", "")) == "info":
			return {"ok": true, "twin": main.twin_info()}
		main.twin = {"name": str(d.get("name", "")), "t": Time.get_datetime_string_from_system()}
		if d.has("lat") and d.has("lon"):
			main.twin["lat"] = float(d["lat"])
			main.twin["lon"] = float(d["lon"])
			main.karte.open(main.twin["lat"], main.twin["lon"], 17)
			main.karte.sel = Vector2(main.twin["lat"], main.twin["lon"])
			main.karte.sel_name = "Dein Platz: " + main.twin["name"]
			main.karte._show_step(1)
			main.start_info = "Dein Platz («%s»): Karte an diesem Ort – «Diesen Ort laden» bestätigen" % main.twin["name"]
		else:
			main.start_info = "Dein Platz: MoveEye kennt seinen Ort nicht (GPS oder Ort in den Einstellungen) – Zonen und Patrouille kommen trotzdem"
		main._settings_dirty = true
		return {"ok": true, "twin": main.twin_info(), "map": d.has("lat")}
	elif a == "news":                                  # 3D-3.82: {do: info | show | close | go (v: Version, Links zu Neuerungen)}
		if str(d.get("do", "")) == "show":
			main.news.show_news(main.news.pick(d.get("vs", [])))   # vs: these versions (tests), otherwise the new ones
		elif str(d.get("do", "")) == "go":
			return {"ok": true, "go": main.news.go(str(d.get("v", ""))), "news": main.news.info()}
		elif str(d.get("do", "")) == "close":
			main.news.close(bool(d.get("off", false)))
		return {"ok": true, "news": main.news.info()}
	elif a == "templates":                             # 3D-3.82: {do: info|open|import|remove|adjust, path, i, key, d, tab}
		var dd := str(d.get("do", "info"))
		if dd == "open":
			main.templates.toggle(int(d.get("tab", 0)))
		elif dd == "close":
			main.templates.visible = false
		elif dd == "import":
			return {"ok": main.templates.import_file(str(d.get("path", "")), bool(d.get("show", true))), "info": main.templates.info(), "msg": main.templates._msg.text}
		elif dd == "drop":
			main.templates._on_drop(PackedStringArray([str(d.get("path", ""))]))
		elif dd == "remove":
			main.templates.remove(int(d.get("i", 0)))
		elif dd == "adjust":
			main.templates._adjust(int(d.get("i", 0)), str(d.get("key", "x")), float(d.get("d", 1.0)))
		return {"ok": true, "info": main.templates.info(), "obstacles": main.obstacles.size(), "scene": main.scene}
	elif a == "visits":                                # 3D-3.80: finished visits for the diary of MoveEye {since: id}
		return {"ok": true, "visits": main.visitlog.since(int(d.get("since", 0))), "seq": main.visitlog.seq, "live": main.visitlog.live.size(), "sim": main.VERSION}
	elif a == "localplay":                             # 3D-3.77: play here at the PC (tests): {do: start | stop | get, role}
		var dl := str(d.get("do", "get"))
		if dl == "start":
			main.localplay.start(str(d.get("role", "runner")))
		elif dl == "stop":
			main.localplay.stop()
		elif dl == "key":
			var ke := InputEventKey.new()
			ke.keycode = int(d.get("key", KEY_ENTER))
			ke.pressed = true
			main.localplay._input(ke)
		return main.localplay.debug()
	elif a == "surprise":                              # 3D-3.75: {op: get | on | off | start (kind) | morning}
		var op_ := str(d.get("op", "get"))
		if op_ == "on" or op_ == "off":
			main.surprise.set_on(op_ == "on")
		elif op_ == "start":
			main.surprise.start(str(d.get("kind", "power")))
		elif op_ == "morning":
			main.surprise.morning()
		return {"ok": true, "surprise": main.surprise.info()}
	elif a == "entdecken":                             # Erlebniswelt 20–23: {do: info | open | close | photo | mark (id) | reset | hint | set | where (id)}
		return main.entdecken.control(d) if main.entdecken != null else {"ok": false, "error": "no entdecken"}
	elif a == "spielton":                              # Spielton (klang.gd): {do: info | test (art) | erleben (id) | gefahr (quelle, stufe, dauer)}
		return main.klang.control(d) if main.klang != null else {"ok": false, "error": "no klang"}
	elif a == "spielbereich":                          # Paket «Spielbereich»: {do: info | open | close | start (id) | seen | reset}
		return main.spielbereich.control(d) if main.spielbereich != null else {"ok": false, "error": "no spielbereich"}
	elif a == "dev":                                   # Entwicklertool 1 (devtool.gd): {do: places | goto (id) | fly (on, speed) | open | close | info}
		return main.mehr.dev.control(d) if main.mehr != null and main.mehr.dev != null else {"ok": false, "error": "not ready"}
	elif a == "fehler":                                # Fehler-QR (fehler_hilfe.gd): {do: info | zeige (id) | fix (aktion: sim_verbinden | sim_neustart | sim_notfall)}
		return preload("res://scripts/fehler_hilfe.gd").control(main, main.mehr, d)
	elif a == "werk":                                  # Werksrücksetzung (werk.gd): {do: info | open | close | reset (confirm: true)}
		return main.mehr.werk.control(d) if main.mehr != null and main.mehr.werk != null else {"ok": false, "error": "not ready"}
	elif a == "werkstatt":                             # real-gehaeuse: {do: open | close | info | explode | xray | inner | v52 | v53 | pick | step | next | prev | view | real_case}
		return main.werkstatt.control(d) if main.werkstatt != null else {"ok": false, "error": "not ready"}
	elif a == "egg":                                   # Entwickler-Test (bergtal_ei.gd)
		return main.bt_ei.control(d) if main.bt_ei != null and is_instance_valid(main.bt_ei) else {"ok": false, "error": "only in the Bergtal"}
	elif a == "sicherung":                             # System → Sicherung (sicherung.gd): {do: info | make | send | get | ack | check | restore}
		return main.sicherung.control(d) if main.sicherung != null else {"ok": false, "error": "not ready"}
	elif a == "mehr":                                  # 3D-4.2x: «Mehr» (tests): {"do": open | theme | tour | diag | log | fb_* | shot}
		return main.mehr.control(d) if main.mehr != null else {"ok": false, "error": "not ready"}
	elif a == "feedback":                              # MoveEye 2.98.33: the dialog «Rückmeldung» (tests: {text, kind, stars, shot})
		main._feedback_open()
		if main.feedback_dlg != null and str(d.get("text", "")) != "" and main.feedback_dlg.visible:
			main.feedback_dlg.fill_and_send(d)
		return {"ok": true, "open": main.feedback_dlg != null and main.feedback_dlg.visible, "connected": main.feedback_dlg != null and main.feedback_dlg.connected()}
	elif a == "mw_request":                            # 3D-3.71: like the buttons «Referenz-Scan» / «Vergleichen» (tests, remote)
		main.mw_request(str(d.get("op", "")))
		return {"ok": true, "cmd": main.mw_cmd}
	elif a == "bike":
		main.set_bike(bool(d.get("on", true)))
		return {"ok": true}
	elif a == "prop":                                  # 3D-3.72: test aids {name: Velo | Zelt | Tisch | Kühlboxen | Grill, on}
		main.set_prop(str(d.get("name", "")), bool(d.get("on", true)))
		return {"ok": true, "props": main.test_props.keys()}
	elif a == "sabotage":                              # {cover: bool, turn: degrees}
		main.set_sabotage(d.get("cover", null), d.get("turn", null))
		return {"ok": true, "cover": main.sabotage_cover, "turn": rad_to_deg(main.sabotage_turn)}
	elif a == "ref_night_test":
		main.ref_night_test()
		return {"ok": true}
	elif a == "home":                                  # 3D-3.73: «Mein Zuhause» {op: get | set (items) | edit (on)}
		var op := str(d.get("op", "get"))
		if op == "set" and d.get("items") is Array:
			main.home_items = (d["items"] as Array).filter(func(x): return typeof(x) == TYPE_DICTIONARY).slice(0, 400)
			main.home_save()
			main.home_rebuild()
		elif op == "edit":
			main.home_editor.open(bool(d.get("on", true)))
		return {"ok": true, "items": main.home_items, "kinds": main.Scenes.HOME_KINDS, "scene": main.scene}
	elif a == "shoot":                                 # 3D-3.70: a shot / trigger from MoveEye at a spot of the head camera picture
		if bool(d.get("shutter", false)) and main.game != null and main.game.shut.human_mode() == "mw":   # 3D-4.x: «Auslöser» (gameshutter.gd)
			return main.game.shut.fire(null, str(d.get("who", "")).left(30))
		return main.mw_shot(float(d.get("x", 0.5)), float(d.get("y", 0.5)), str(d.get("who", "")).left(30))
	elif a == "game_mwcatch":                          # «Team gegen MoveEye»: «Erwischt!» pressed at MoveEye (3D-3.27)
		if main.game == null:
			return {"ok": false, "error": "no game"}
		return main.game.mw_catch(str(d.get("who", "")).left(30), float(d.get("x", -1.0)), float(d.get("y", -1.0)))
	elif a == "gps":                                   # 3D-3.98: {steal: true | false} - the device is carried away
		if d.has("steal"):
			return main.gps_steal(bool(d["steal"]))
		var gr = main.gps_reading()
		gr["ok"] = true
		gr["steal"] = main.gps_steal_t > 0.0
		gr["solar"] = main.solar_reading()
		return gr
	elif a == "pir":                                   # real-pir-ton: {do: info | fire | set (key, value) | reset} (pir.gd)
		return main.pir.op(d)
	elif a == "mikro":                                 # real-pir-ton: {do: info | set (key, value) | probe (kind, db1m, x, z)} (mikrofon.gd)
		return main.mikro.op(d)
	elif a == "servo":                                 # «Servo-Mechanik»: {do: info | set (key, value) | sim (deg, mass, play, v)} (servo.gd)
		return main.servo.control(d)
	elif a == "simint":                                # 30.10.2026: {do: info | uv | pca | i2c | block (axis) | off | model (m) | hand (on)} (simint.gd)
		return main.simint.op(d)
	elif a == "sound":                                 # 3D-3.98: {kind: clap | sneeze | voice | shout, n, x, z}
		var sp = null
		if d.has("x") and d.has("z"):
			sp = Vector3(float(d["x"]), main.ground_y(float(d["x"]), float(d["z"])) + 1.5, float(d["z"]))
		return main.emit_sound(str(d.get("kind", "clap")), int(d.get("n", 2)), sp)
	elif a == "zimmertiere":                           # Erlebniswelt «mehr Tiere drinnen»: {do: info | lens (dist, hold) | set (pets, spider) | state (who, state)}
		return main.zimmertiere.control(d) if main.zimmertiere != null else {"ok": false, "error": "no zimmertiere"}
	elif a == "sleeper":                               # 3D-3.96: the person in the bed (bedroom scene)
		if main.sleeper == null:
			return {"ok": false, "error": "no sleeper"}
		return main.sleeper.command(d)
	elif a == "fenster":                               # Paket «Fenster» (fenster.gd): info / drag / resize / close / list / check / reset
		return main.fenster.control(d) if main.fenster != null else {"ok": false, "error": "no fenster"}
	elif a == "smalltv":                               # 3D-4.19: virtueller SmallTV - Zähler, letztes Bild (Tests, Prüfstand)
		return main.smalltv.control(d) if main.smalltv != null else {"ok": false, "error": "no smalltv"}
	elif a == "game_info":                             # the spectators in MoveEye: the game in numbers (3D-3.22)
		if main.game == null:
			return {"ok": false, "error": "no game"}
		var gi: Dictionary = main.game.spectator_info()
		gi["ok"] = true
		return gi
	elif a == "mover":                                 # for tests: where the mover is
		return {"ok": true, "pad": [main.pad_drive.x, main.pad_drive.y, main.now() - main.pad_t, main._pad_l, main._pad_r, main.rover_pad.dragging, main.sim_active, main.now() - main._drive_t], "on": main.mover_on, "x": snappedf(main.rig.position.x, 0.01), "z": snappedf(main.rig.position.z, 0.01),
				"yaw": snappedf(rad_to_deg(main.rig.rotation.y), 0.1), "drive": main.mw.get("drive", {}),
				"near": main._ob_near(Vector2(main.rig.position.x, main.rig.position.z - 0.3)).map(func(o): return [o["c"], main._ob_closest(o, Vector2(main.rig.position.x, main.rig.position.z))[1]])}
	elif a == "grafik":                                # F1 «Grafikstufe Hoch» (tests, measuring): {do: info | set (value) | dof | off_session | on_session}
		return main.hoch.op(d)
	elif a == "view":                                  # for tests: the free view from a point to a point, panel away
		var vp_: Array = d.get("pos", [0, 3, 6])
		var la_: Array = d.get("look", [0, 1, 0])
		main.view_mode = 0
		main.view_cam.position = Vector3(float(vp_[0]), float(vp_[1]), float(vp_[2]))
		main.view_cam.look_at(Vector3(float(la_[0]), float(la_[1]), float(la_[2])))
		main.show_panel(bool(d.get("panel", false)))
		return {"ok": true}
	elif a == "window":                                # for tests: minimized? (2 = minimized) and how many frames were drawn
		return {"ok": true, "mode": DisplayServer.window_get_mode(), "frames": Engine.get_frames_drawn(), "autostart": main.autostart_on}
	elif a == "visitors":                              # for tests: where every visitor is, and whether it is inside an object
		var out := []
		for v in main.visitors.get_children():
			var p2 := Vector2(v.position.x, v.position.z)
			var deepest := 99.0
			for o in main._ob_near(p2):
				if o["po"] and v.kind != "person":
					continue
				deepest = min(deepest, float(main._ob_closest(o, p2)[1]))
			var sp = main.view_cam.unproject_position(v.global_position + Vector3(0, 0.6, 0))
			out.append({"kind": v.kind, "x": snappedf(v.position.x, 0.01), "z": snappedf(v.position.z, 0.01), "gap": snappedf(deepest, 0.01), "variant": v.variant, "route": v.route.size(), "wait": snappedf(max(0.0, v.wait_until - v.now_s()), 0.1), "tx": snappedf(v.target.x, 0.1), "tz": snappedf(v.target.z, 0.1), "spd": snappedf(v.cur_speed, 0.01), "r": v.radius,
					"y": snappedf(v.position.y, 0.01), "sx": int(sp.x), "sy": int(sp.y), "selected": v == main.selected})
		return {"ok": true, "visitors": out}
	elif a == "wheel_probe":                           # for tests (3D-3.35): a mouse wheel at a point, through the whole input path
		var e := InputEventMouseButton.new()
		e.button_index = MOUSE_BUTTON_WHEEL_UP if int(d.get("dir", 1)) > 0 else MOUSE_BUTTON_WHEEL_DOWN
		e.pressed = true
		e.position = Vector2(float(d.get("x", 0)), float(d.get("y", 0)))
		e.global_position = e.position
		var cam_before = main.view_cam.global_position
		main.get_viewport().push_input(e)
		var e2 := e.duplicate()
		e2.pressed = false
		main.get_viewport().push_input(e2)
		return {"ok": true, "moved": snappedf(main.view_cam.global_position.distance_to(cam_before), 0.001), "over": main._over_hud(e.position)}
	elif a == "pose_probe":                            # for tests: a person standing still in a given pose (joints in radians)
		var px := float(d.get("x", 0.0))
		var pz := float(d.get("z", -10.0))
		var pv = main.spawn("person", Vector3(px, 0, pz), Vector3(px, 0, pz - 5.0))
		pv.preview = true
		pv.heading = float(d.get("heading", 0.0))
		pv.rotation.y = pv.heading
		var jt: Dictionary = d.get("j", {})
		for i in range(2):
			pv.legs[i][0].rotation = Vector3(float(jt.get("hip%d" % i, 0.0)), 0, float(jt.get("hipz%d" % i, 0.0)))
			pv.legs[i][2].rotation.x = float(jt.get("knee%d" % i, 0.0))
			pv.arms[i][0].rotation = Vector3(float(jt.get("sh%d" % i, 0.0)), 0, float(jt.get("shz%d" % i, 0.0)))
			pv.arms[i][2].rotation.x = float(jt.get("el%d" % i, 0.0))
		pv.torso.rotation.x = float(jt.get("torso", 0.0))
		pv.head.rotation.x = float(jt.get("head", 0.0))
		pv.body_root.rotation.x = float(jt.get("body", 0.0))
		pv.body_root.position = Vector3(0, float(jt.get("by", 0.0)), float(jt.get("bz", 0.0)))
		return {"ok": true}
	elif a == "anim":                                  # «Animationen verbessern» (tests): anim_mensch.op
		return preload("res://scripts/anim_mensch.gd").op(main, d)
	elif a == "spawn_at":                              # for tests: a visitor from one point to another
		var f: Array = d.get("from", [0, 0])
		var t: Array = d.get("to", [10, 0])
		var sv = main.spawn(str(d.get("kind", "person")), Vector3(float(f[0]), 0, float(f[1])), Vector3(float(t[0]), 0, float(t[1])))
		if d.has("wait"):                              # stand there for a while, looking at the head camera
			sv.route = [[Vector3(float(t[0]), 0, float(t[1])), float(d["wait"]), 0.0, Vector3(0, 0, 0)], Vector3(float(t[0]) + 40.0, 0, float(t[1]))]
			sv.next_idle = main.now() + 999.0
		return {"ok": true}
	elif a == "gamewiz":                               # the game wizard, worked from the page of MoveEye (3D-3.41)
		return main.gamewiz.op(d)
	elif a == "game_debug":                            # 3D-4.x: for tests - results, duel, levels, bots, votes
		return main.game.debug_info()
	elif a == "gameplus":                              # 3D-4.x: weather change, camouflage things, theft (gameplus.gd, tests)
		return main.game.plus.op(d)
	elif a == "figuren":                               # 3D-4.12: for tests - figures in a row, a picture, frames per second (figur.gd)
		return preload("res://scripts/figur.gd").op(main, d)
	elif a == "set" or a == "press":
		var c = null
		for x in main.controls:
			if x.id == cid:
				c = x
		if c == null or c["set"] == null:
			return {"ok": false, "error": "unknown control"}
		main._ctl_frame = -1                                 # a button / switch pressed from the page counts like one in the window (one lock)
		if a == "press":
			c["set"].call()
		else:
			var v = d.get("value")
			match c.type:
				"slider":
					v = clamp(float(v), float(c.extra.get("min", -1e9)), float(c.extra.get("max", 1e9)))
				"toggle":
					v = bool(v)
				_:
					v = str(v)
			c["set"].call(v)
		main._sync_ui()
	elif a != "get":
		return {"ok": false, "error": "unknown action"}
	return main.control_info()
