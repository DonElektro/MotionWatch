extends CanvasLayer
## Abenteuer-Kit (Grossvater-Neubau, Besitzer 20.11.2026): der schlanke Bildschirm statt der Seitenspalte – nur das Nötigste:
## Ziel-Zeile (oben links), Kompass mit Ziel-Marke (oben Mitte), Pause (oben rechts), Hinweis zur Aktion (unten Mitte),
## Untertitel (Sprecher farbig), Kino-Balken, Blende, Rückblenden-Farbe, Hochzieh- / Balance-Anzeige, kurze Meldungen.
## Handy / iPad (Touch): Stick links, rechts «Aktion» und «Springen/Greifen», Wischen in der rechten Hälfte = umschauen;
## die Kamera folgt sonst von selbst (kit_regie.gd). Pause-Menü: Weiter · (nach 90 s ohne Fortschritt: Zum nächsten Abschnitt
## springen) · Zum Checkpoint · Steuerung · Beenden.
## Alle anderen Ebenen (Bedienfeld, Fenster, Leiste) blendet kit_abenteuer.gd aus, solange gespielt wird.
## Gebaut wird einmal; jedes Bild werden nur Texte / Positionen gesetzt, wenn sie sich ändern (kein Neubau).

const T = preload("res://scripts/i18n.gd")
const UI = preload("res://scripts/ui_style.gd")

const SEPIA := """
shader_type canvas_item;
uniform sampler2D scr : hint_screen_texture, filter_linear_mipmap;
uniform float k = 0.0;
uniform float ir = 0.0;                  // MoveEye's infrared view: bright green-grey, noisy
uniform float wipe = 1.1;                // > 1: the whole picture (the wipe of the flashback runs 0 -> 1.1)
void fragment() {
	vec3 c = texture(scr, SCREEN_UV).rgb;
	float l = dot(c, vec3(0.3, 0.59, 0.11));
	vec3 s = vec3(l * 1.08 + 0.06, l * 0.9 + 0.03, l * 0.68);
	vec2 d = SCREEN_UV - 0.5;
	float v = 1.0 - dot(d, d) * 1.4;
	float grain = fract(sin(dot(floor(SCREEN_UV * 420.0) + floor(TIME * 24.0), vec2(12.9898, 78.233))) * 43758.5453) - 0.5;
	vec3 sep = s * mix(1.0, v, 0.85) + grain * 0.07;             // flashback: sepia, strong vignette, soft grain
	sep = mix(sep, sep * vec3(1.05, 0.95, 0.8), 0.5);
	float wipe_k = smoothstep(wipe - 0.06, wipe, SCREEN_UV.x);   // the opening wipe from the left
	vec3 o = mix(c, sep, k * (1.0 - ir) * (1.0 - wipe_k));
	float g = clamp(l * 3.2 + 0.08, 0.0, 1.0);
	float n = fract(sin(dot(SCREEN_UV * 731.0 + TIME, vec2(12.9898, 78.233))) * 43758.5453);
	o = mix(o, vec3(g * 0.78, g, g * 0.8) * v + (n - 0.5) * 0.06, ir * k);
	COLOR = vec4(o, 1.0);
}
"""

var kit
var root: Control
var touch := false
var _ziel: Label
var _ziel_box: PanelContainer
var _kompass: Control
var _pause_btn: Button
var _skip_btn: Button
var _prompt: Label
var _prompt_box: PanelContainer
var _sub: Label
var _sub_wer: Label
var _sub_box: VBoxContainer
var _bars: Array = []
var _fade: ColorRect
var _sepia: ColorRect
var _meter: ProgressBar
var _meter_lab: Label
var _toast: Label
var _toast_bis := 0.0
var _menu: PanelContainer
var _hilfe: Label
var stick: Control
var _btn_akt: Button
var _btn_sprung: Button
var _swipe: Control
var _fade_tw: Tween
var _sepia_k := 0.0
var _sepia_ziel := 0.0
var _last := {}
# touch state (read by kit_abenteuer.gd)
var stick_v := Vector2.ZERO
var _stick_idx := -2
var _stick_c := Vector2.ZERO
var look_d := Vector2.ZERO
var _swipe_idx := -2
var _swipe_last := Vector2.ZERO
var tap_akt := false
var tap_sprung := false
var halt_sprung := false


func _init(k) -> void:
	kit = k
	layer = 115
	name = "kit_hud"


func _ready() -> void:
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = UI.theme()
	add_child(root)
	_sepia = ColorRect.new()
	_sepia.set_anchors_preset(Control.PRESET_FULL_RECT)
	_sepia.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sh := Shader.new()
	sh.code = SEPIA
	var sm := ShaderMaterial.new()
	sm.shader = sh
	_sepia.material = sm
	_sepia.visible = false
	root.add_child(_sepia)
	_swipe = Control.new()
	_swipe.set_anchors_preset(Control.PRESET_FULL_RECT)
	_swipe.anchor_left = 0.45
	_swipe.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_swipe.gui_input.connect(_swipe_input)
	root.add_child(_swipe)
	for top in [true, false]:
		var b := ColorRect.new()
		b.color = Color.BLACK
		b.mouse_filter = Control.MOUSE_FILTER_IGNORE
		b.anchor_right = 1.0
		b.anchor_top = 0.0 if top else 1.0
		b.anchor_bottom = 0.0 if top else 1.0
		root.add_child(b)
		_bars.append(b)
	# goal line
	_ziel_box = PanelContainer.new()
	_ziel_box.add_theme_stylebox_override("panel", UI.box(Color(0.03, 0.05, 0.07, 0.55), Color(0, 0, 0, 0), 10, 8, 0))
	_ziel_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_ziel_box)
	_ziel = _label(16, Color(1, 0.93, 0.75))
	_ziel.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_ziel_box.add_child(_ziel)
	# compass
	_kompass = Control.new()
	_kompass.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_kompass.draw.connect(_kompass_draw)
	root.add_child(_kompass)
	# pause / skip
	_pause_btn = Button.new()
	_pause_btn.text = "II"
	_pause_btn.focus_mode = Control.FOCUS_NONE
	_pause_btn.tooltip_text = T.t("Pause (Esc)")
	_pause_btn.pressed.connect(func(): kit.pause(true))
	root.add_child(_pause_btn)
	_skip_btn = Button.new()
	_skip_btn.text = T.t("Überspringen ›")
	_skip_btn.focus_mode = Control.FOCUS_NONE
	_skip_btn.pressed.connect(func(): kit.ueberspringen())
	root.add_child(_skip_btn)
	# subtitles
	_sub_box = VBoxContainer.new()
	_sub_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_sub_box.alignment = BoxContainer.ALIGNMENT_END
	root.add_child(_sub_box)
	_sub_wer = _label(15, Color(1, 0.86, 0.55))
	_sub_wer.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_sub_box.add_child(_sub_wer)
	_sub = _label(19, Color(0.95, 0.96, 0.98))
	_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_sub_box.add_child(_sub)
	# prompt
	_prompt_box = PanelContainer.new()
	_prompt_box.add_theme_stylebox_override("panel", UI.box(Color(0.04, 0.06, 0.08, 0.72), Color(1, 0.8, 0.45, 0.8), 18, 10, 2))
	_prompt_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_prompt_box)
	_prompt = _label(17, Color(1, 0.92, 0.75))
	_prompt_box.add_child(_prompt)
	# meter (pull up / balance)
	_meter = ProgressBar.new()
	_meter.min_value = 0.0
	_meter.max_value = 1.0
	_meter.show_percentage = false
	_meter.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_meter)
	_meter_lab = _label(14, Color(1, 1, 1))
	_meter_lab.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	root.add_child(_meter_lab)
	_toast = _label(18, Color(0.75, 1.0, 0.8))
	_toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_toast.visible = false
	root.add_child(_toast)
	# touch controls
	stick = Control.new()
	stick.mouse_filter = Control.MOUSE_FILTER_STOP
	stick.draw.connect(_stick_draw)
	stick.gui_input.connect(_stick_input)
	root.add_child(stick)
	_btn_akt = _rund(T.t("Aktion"), Color(0.95, 0.7, 0.3))
	_btn_akt.button_down.connect(func(): tap_akt = true)
	_btn_sprung = _rund(T.t("Springen/\nGreifen"), Color(0.4, 0.75, 1.0))
	_btn_sprung.button_down.connect(func(): tap_sprung = true; halt_sprung = true)
	_btn_sprung.button_up.connect(func(): halt_sprung = false)
	# fade (above everything but the menu)
	_fade = ColorRect.new()
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.color = Color(0, 0, 0, 0)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(_fade)
	_foto_btn = Button.new()
	_foto_btn.text = T.t("Foto")
	_foto_btn.focus_mode = Control.FOCUS_NONE
	_foto_btn.tooltip_text = T.t("Foto mit MoveEye (P)")
	_foto_btn.pressed.connect(func(): tap_foto = true)
	_foto_btn.visible = false
	root.add_child(_foto_btn)
	_bau_menu()
	get_viewport().size_changed.connect(_layout)
	_layout()


func _label(sz: int, col: Color) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", sz)
	l.add_theme_color_override("font_color", col)
	l.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.85))
	l.add_theme_constant_override("outline_size", 6)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.set_meta("sz", sz)
	return l


func _rund(text: String, col: Color) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	for st in ["normal", "hover", "pressed", "focus"]:
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color(col.r, col.g, col.b, 0.32 if st != "pressed" else 0.6)
		sb.border_color = Color(col.r, col.g, col.b, 0.9)
		sb.set_border_width_all(3)
		sb.set_corner_radius_all(999)
		b.add_theme_stylebox_override(st, sb)
	b.add_theme_color_override("font_color", Color.WHITE)
	b.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	b.add_theme_constant_override("outline_size", 4)
	root.add_child(b)
	return b


func _bau_menu() -> void:
	_menu = PanelContainer.new()
	_menu.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.07, 0.1, 0.94), Color(1, 0.8, 0.45, 0.6), 16, 18, 1))
	_menu.visible = false
	root.add_child(_menu)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	_menu.add_child(v)
	var t := _label(22, Color(1, 0.9, 0.7))
	t.text = T.t("Pause")
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(t)
	for e in [["Weiterspielen", func(): kit.pause(false)], ["Zum letzten Checkpoint", func(): kit.pause(false); kit.figur.zurueck()],
			["Steuerung", func(): _hilfe.visible = not _hilfe.visible], ["Kindermodus an / aus", func(): kit.kinder_umschalten()],
			["Abenteuer beenden", func(): kit.stop()]]:
		var b := Button.new()
		b.text = T.t(str(e[0]))
		b.custom_minimum_size = Vector2(260, 46)
		b.pressed.connect(e[1])
		v.add_child(b)
		if str(e[0]) == "Weiterspielen":                       # stuck for 90 s in one step (kit_abenteuer.gd STECKEN_S): the way out
			_abschnitt_btn = Button.new()
			_abschnitt_btn.text = T.t("⏭ Zum nächsten Abschnitt springen")
			_abschnitt_btn.custom_minimum_size = Vector2(260, 46)
			_abschnitt_btn.pressed.connect(func(): kit.abschnitt_springen())
			_abschnitt_btn.visible = false
			UI.primary(_abschnitt_btn)
			v.add_child(_abschnitt_btn)
	_hilfe = _label(14, Color(0.85, 0.9, 0.95))
	_hilfe.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_hilfe.custom_minimum_size = Vector2(260, 0)
	_hilfe.text = T.t("PC: W A S D gehen · Shift rennen · Leertaste springen / greifen · E Aktion · Maus ziehen umschauen · Rad näher / weiter · Esc Pause") + "\n" + \
			T.t("Controller: linker Stick gehen · rechter Stick umschauen · A springen / greifen · X Aktion · R2 rennen · Start Pause") + "\n" + \
			T.t("Handy / iPad: Stick links · rechts «Aktion» und «Springen/Greifen» · in der rechten Hälfte wischen = umschauen")
	_hilfe.visible = false
	v.add_child(_hilfe)


# ---- layout (phone 390×844, iPad 820×1180 / 1180×820, PC 1280×720) ----------------------------------------------------
func _vs() -> Vector2:
	return get_viewport().get_visible_rect().size if is_inside_tree() else Vector2(1280, 720)


func _k() -> float:
	var s := _vs()
	return clampf(minf(s.x, s.y) / 720.0, 0.62, 1.35)


func _layout() -> void:
	var s := _vs()
	var k := _k()
	var pad := 14.0 * k + 4.0
	for l in [_ziel, _prompt, _sub, _sub_wer, _meter_lab, _toast]:
		l.add_theme_font_size_override("font_size", int(float(l.get_meta("sz", 16)) * maxf(k, 0.85)))
	var hoch := s.y > s.x
	var kw := minf(s.x * (0.5 if hoch else 0.36), 420.0)
	_kompass.size = Vector2(kw, 30.0 * maxf(k, 0.85))
	_kompass.position = Vector2((s.x - kw) * 0.5, pad + (58.0 * maxf(k, 0.85) if hoch else 0.0))   # portrait: under the goal line
	_ziel_box.position = Vector2(pad, pad)
	_ziel.custom_minimum_size = Vector2(minf(s.x * (0.62 if hoch else 0.3), 380.0), 0)
	_ziel_box.size = Vector2.ZERO
	var bs := 44.0 * maxf(k, 0.9)
	_pause_btn.size = Vector2(bs, bs)
	_pause_btn.position = Vector2(s.x - bs - pad, pad)
	_skip_btn.size = Vector2(0, bs)
	_skip_btn.position = Vector2(s.x - 190.0 * maxf(k, 0.9) - pad, pad + (bs + 8.0 if hoch else 0.0))
	_skip_btn.custom_minimum_size = Vector2(180.0 * maxf(k, 0.9), bs)
	var sub_w := minf(s.x - 2.0 * pad, 900.0)
	_sub_box.size = Vector2(sub_w, 0)
	_sub.custom_minimum_size = Vector2(sub_w, 0)
	var unten := pad + (270.0 * maxf(k, 0.85) if touch else 30.0)
	if touch and not hoch:
		unten = pad + 60.0 * k
	_sub_box.position = Vector2((s.x - sub_w) * 0.5, s.y - unten - 90.0 * maxf(k, 0.85))
	_prompt_box.position = Vector2(s.x * 0.5, s.y - unten - 150.0 * maxf(k, 0.85))
	_meter.size = Vector2(minf(320.0, s.x * 0.7), 14.0 * maxf(k, 0.9))
	_meter.position = Vector2((s.x - _meter.size.x) * 0.5, s.y * 0.36)
	_meter_lab.size = Vector2(_meter.size.x, 24)
	_meter_lab.position = _meter.position - Vector2(0, 30.0 * maxf(k, 0.9))
	_toast.size = Vector2(s.x, 30)
	_toast.position = Vector2(0, s.y * 0.22)
	# touch controls: big enough for thumbs (≥ 88 pt on the phone)
	var r := clampf(minf(s.x, s.y) * 0.17, 70.0, 120.0)
	stick.size = Vector2(r * 2.6, r * 2.6)
	stick.position = Vector2(pad, s.y - stick.size.y - pad)
	_stick_c = stick.size * 0.5
	var b1 := r * 1.35
	var b2 := r * 1.05
	_btn_sprung.size = Vector2(b1, b1)
	_btn_sprung.position = Vector2(s.x - b1 - pad * 1.5, s.y - b1 - pad * 1.5)
	_btn_akt.size = Vector2(b2, b2)
	_btn_akt.position = _btn_sprung.position + Vector2(-b2 - pad * 0.8, b1 - b2 - r * 0.55)
	for b in [_btn_akt, _btn_sprung]:
		b.add_theme_font_size_override("font_size", int(15.0 * maxf(k, 0.9)))
		for st in ["normal", "hover", "pressed", "focus"]:
			var sb = b.get_theme_stylebox(st)
			if sb is StyleBoxFlat:
				(sb as StyleBoxFlat).set_corner_radius_all(int(b.size.x * 0.5))   # (999 drew a seam)
	_menu.position = (s - _menu.get_combined_minimum_size()) * 0.5
	_last = {}


func set_touch(on: bool) -> void:
	touch = on
	_layout()


# ---- every frame ----------------------------------------------------------------------------------------------------------
var _mess: Label = null
var _mess_t := 0.0
var _mess_ms: Array = []


func _messen(real_dt: float) -> void:
	"""measuring on the phone / iPad (21.11.): with --kit-messen (browser: …&messen=1) a small line top left - frames per second,
	average and slowest frame time of the last second, Lite or not"""
	if _mess == null:
		if not "--kit-messen" in (OS.get_cmdline_user_args() + preload("res://scripts/web.gd").args()):
			set_meta("kein_messen", true)
			return
		_mess = _label(13, Color(0.7, 1.0, 0.7))
		_mess.position = Vector2(10, 8)
		root.add_child(_mess)
	_mess_ms.append(real_dt * 1000.0)
	_mess_t += real_dt
	if _mess_t >= 1.0:
		var sum := 0.0
		var mx := 0.0
		for v in _mess_ms:
			sum += float(v)
			mx = maxf(mx, float(v))
		_mess.text = "%d fps · %.1f ms Mittel · %.0f ms max · %s" % [Engine.get_frames_per_second(), sum / maxf(1.0, _mess_ms.size()),
				mx, "Lite" if preload("res://scripts/quality.gd").lite() else "voll"]
		print("kit-messen: " + _mess.text)
		_mess_ms.clear()
		_mess_t = 0.0


func tick(real_dt: float) -> void:
	if not has_meta("kein_messen"):
		_messen(real_dt)
	var s := _vs()
	var bh: float = float(kit.regie.balken) * s.y * 0.1
	(_bars[0] as ColorRect).size = Vector2(s.x, bh)
	(_bars[0] as ColorRect).position = Vector2(0, 0)
	(_bars[1] as ColorRect).size = Vector2(s.x, bh)
	(_bars[1] as ColorRect).position = Vector2(0, s.y - bh)
	var film: bool = kit.regie.film_an
	var spiel: bool = kit.spielt() and not film
	_setz("ziel_v", spiel and kit.ziel_text != "", func(v): _ziel_box.visible = v)
	_setz("ziel", kit.ziel_text, func(v): _ziel.text = v; _ziel_box.size = Vector2.ZERO)
	_kompass.visible = spiel
	if spiel:
		_kompass.queue_redraw()
	_pause_btn.visible = not film and not _menu.visible
	_foto_btn.visible = spiel and kit.szene_i >= 10
	_foto_btn.size = Vector2(0, _pause_btn.size.y)
	_foto_btn.position = _pause_btn.position - Vector2(_foto_btn.get_combined_minimum_size().x + 10.0, 0)
	_skip_btn.visible = film
	var pr: String = kit.figur.prompt() if spiel else ""
	var ist_qte: bool = not kit.qte.is_empty()
	if ist_qte:
		pr = str(kit.qte["text"]) + ("" if touch else "  [" + T.t("Leertaste") + "]")
	if pr != "" and not ist_qte:
		pr = (T.t("Aktion") + ": " if not touch else "") + T.t(pr)
		if not touch and kit.figur.zustand == "boden":
			pr = "[E] " + T.t(kit.figur.prompt()) if kit.figur.prompt() != "Springen!" else "[" + T.t("Leertaste") + "] " + T.t("Springen!")
	_setz("prompt", pr, func(v): _prompt.text = v; _prompt_box.size = Vector2.ZERO)
	_prompt_box.visible = pr != "" and not (kit.qte.is_empty() and film)
	if _prompt_box.visible:
		_prompt_box.position.x = (s.x - _prompt_box.size.x) * 0.5
	var z: String = kit.figur.zustand
	var mv := z in ["haengen", "balance"] and not film
	_meter.visible = mv
	_meter_lab.visible = mv
	if z == "haengen":
		_meter.value = float(kit.figur.hoch)
		_setz("meter", T.t("Tippen oder halten: hochziehen!"), func(v): _meter_lab.text = v)
	elif z == "balance":
		_meter.value = 0.5 + 0.5 * float(kit.figur.balance)
		_setz("meter", T.t("Gleichgewicht: gegensteuern (A / D, Stick)"), func(v): _meter_lab.text = v)
	var tv: bool = touch and spiel and not _menu.visible
	stick.visible = tv
	_btn_akt.visible = tv
	_btn_sprung.visible = tv
	_swipe.mouse_filter = Control.MOUSE_FILTER_STOP if tv else Control.MOUSE_FILTER_IGNORE
	if tv:
		stick.queue_redraw()
	if _toast.visible and kit.uhr > _toast_bis:
		_toast.visible = false
	_sepia_k = move_toward(_sepia_k, _sepia_ziel, real_dt * 0.8)
	_sepia.visible = _sepia_k > 0.01
	if _sepia.visible:
		(_sepia.material as ShaderMaterial).set_shader_parameter("k", _sepia_k)


func _setz(key: String, v, f: Callable) -> void:
	"""only when it changed (no rebuild, no relayout every frame)"""
	if _last.has(key) and _last[key] == v:
		return
	_last[key] = v
	f.call(v)


func untertitel(text: String, wer_name: String, col: Color) -> void:
	_sub.text = text
	_sub_wer.text = wer_name
	_sub_wer.add_theme_color_override("font_color", col)
	_sub_wer.visible = wer_name != ""
	_sub_box.visible = text != ""


func toast(text: String, secs := 3.0) -> void:
	_toast.text = text
	_toast.visible = true
	_toast_bis = kit.uhr + secs


var _abschnitt_btn: Button = null


func menu(on: bool) -> void:
	_menu.visible = on
	if _abschnitt_btn != null:
		_abschnitt_btn.visible = on and bool(kit.abschnitt_angebot)
	_hilfe.visible = false
	_menu.size = Vector2.ZERO
	_menu.position = (_vs() - _menu.get_combined_minimum_size()) * 0.5


func blende(secs: float) -> void:
	"""to black and back (secs together)"""
	if _fade_tw != null:
		_fade_tw.kill()
	_fade_tw = create_tween()
	_fade_tw.tween_property(_fade, "color:a", 1.0, secs * 0.45)
	_fade_tw.tween_interval(secs * 0.1)
	_fade_tw.tween_property(_fade, "color:a", 0.0, secs * 0.45)


func blende_aus() -> void:
	if _fade_tw != null:
		_fade_tw.kill()
	_fade.color.a = 0.0


func farbe(art: String) -> void:
	"""flashback: warm old colours (art «alt»), MoveEye's infrared («ir»), '' = back"""
	_sepia_ziel = 1.0 if art in ["alt", "ir"] else 0.0
	var sm := _sepia.material as ShaderMaterial
	sm.set_shader_parameter("ir", 1.0 if art == "ir" else 0.0)
	if art == "ir":
		_sepia_k = 1.0
	if art == "alt":                                      # the wipe: from the left over the picture in 0.9 s
		_sepia_k = 1.0
		sm.set_shader_parameter("wipe", 0.0)
		var tw := create_tween()
		tw.tween_method(func(x): sm.set_shader_parameter("wipe", x), 0.0, 1.1, 0.9).set_trans(Tween.TRANS_SINE)
	elif art == "":
		sm.set_shader_parameter("wipe", 1.1)


# ---- the map piece (cairn), the flash of the photo, the end card ------------------------------------------------------------
var _karte: Control
var _karte_diff := 0.0
var _ende: PanelContainer
var _foto_btn: Button
var tap_foto := false


func karte(on: bool) -> void:
	if _karte == null:
		_karte = Control.new()
		_karte.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_karte.clip_contents = true
		_karte.draw.connect(_karte_draw)
		root.add_child(_karte)
	_karte.visible = on
	if on:
		var s := _vs()
		var w := minf(s.x * 0.8, 520.0)
		_karte.size = Vector2(w, w * 0.62)
		_karte.position = Vector2((s.x - w) * 0.5, s.y * 0.3)
		toast(T.t("Dreh dich, bis die Linie auf der Karte zur Landschaft passt"), 4.0)


# ---- Kapitel 1: the map card (half / whole) and the backpack choice --------------------------------------------------------
var _kb: Control = null
var _kb_teil := ""


func karte_bild(teil: String) -> void:
	"""the old map: «halb» (torn diagonally, a pencil line), «ganz» (with the corner Maggie found), "" = away"""
	_kb_teil = teil
	if _kb == null:
		_kb = Control.new()
		_kb.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_kb.draw.connect(_kb_draw)
		root.add_child(_kb)
	_kb.visible = teil != ""
	var s := _vs()
	var w := minf(s.x * 0.7, 460.0)
	_kb.size = Vector2(w, w * 0.66)
	_kb.position = Vector2((s.x - w) * 0.5, s.y * 0.18)
	_kb.queue_redraw()


func _kb_draw() -> void:
	var w := _kb.size.x
	var h := _kb.size.y
	var paper := Color(0.9, 0.82, 0.62, 0.95)
	var ink := Color(0.35, 0.22, 0.12, 0.95)
	var pts := PackedVector2Array([Vector2(0, 0), Vector2(w, 0), Vector2(w, h), Vector2(0, h)])
	if _kb_teil == "halb":                                  # the corner is torn off (bottom right)
		pts = PackedVector2Array([Vector2(0, 0), Vector2(w, 0), Vector2(w, h * 0.55), Vector2(w * 0.86, h * 0.62),
				Vector2(w * 0.78, h * 0.78), Vector2(w * 0.66, h * 0.86), Vector2(w * 0.6, h), Vector2(0, h)])
	_kb.draw_colored_polygon(pts, paper)
	for i in range(1, 5):                                    # contour lines
		var y0 := h * (0.15 + i * 0.16)
		var L := PackedVector2Array()
		for k in range(13):
			var x := w * k / 12.0
			L.append(Vector2(x, y0 + sin(k * 0.9 + i) * h * 0.04))
		_kb.draw_polyline(L, Color(0.55, 0.42, 0.25, 0.5), 1.2)
	var bach := PackedVector2Array([Vector2(w * 0.1, h * 0.2), Vector2(w * 0.3, h * 0.45), Vector2(w * 0.5, h * 0.55), Vector2(w * 0.72, h * 0.8), Vector2(w * 0.95, h * 0.95)])
	_kb.draw_polyline(bach, Color(0.25, 0.45, 0.7, 0.8), 2.5)
	var linie := PackedVector2Array([Vector2(w * 0.18, h * 0.16), Vector2(w * 0.35, h * 0.4), Vector2(w * 0.55, h * 0.5)])
	if _kb_teil == "ganz":
		linie.append(Vector2(w * 0.8, h * 0.82))
		_kb.draw_string(ThemeDB.fallback_font, Vector2(w * 0.74, h * 0.94), "×", HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color(0.6, 0.1, 0.08))
	_kb.draw_polyline(linie, ink, 2.0)
	_kb.draw_string(ThemeDB.fallback_font, Vector2(w * 0.06, h * 0.1), "G+T", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, ink)
	_kb.draw_rect(Rect2(Vector2(w * 0.12, h * 0.1), Vector2(10, 10)), ink)        # the hut


var _wahl_panel: PanelContainer = null
var _wahl_fertig := Callable()           # tests: {"action": "kit", "do": "wahl", "ids": [...]}


func wahl(titel: String, optionen: Array, n: int, fertig: Callable) -> void:
	"""choose n of the options ([[id, text], ...]); «Packen» when exactly n are chosen"""
	if _wahl_panel != null:
		_wahl_panel.queue_free()
	_wahl_panel = PanelContainer.new()
	_wahl_panel.add_theme_stylebox_override("panel", UI.box(Color(0.05, 0.07, 0.1, 0.94), Color(1, 0.8, 0.45, 0.6), 16, 18, 1))
	root.add_child(_wahl_panel)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	_wahl_panel.add_child(v)
	var t := _label(20, Color(1, 0.9, 0.7))
	t.text = titel
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(t)
	var g := GridContainer.new()
	g.columns = 2
	g.add_theme_constant_override("h_separation", 8)
	g.add_theme_constant_override("v_separation", 8)
	v.add_child(g)
	var gewaehlt := []
	var ok := Button.new()
	ok.text = T.t("Packen")
	ok.custom_minimum_size = Vector2(200, 46)
	ok.disabled = true
	UI.primary(ok)
	for o in optionen:
		var b := Button.new()
		b.text = str(o[1])
		b.toggle_mode = true
		b.custom_minimum_size = Vector2(150, 46)
		var id := str(o[0])
		b.toggled.connect(func(on: bool):
			if on and gewaehlt.size() >= n:
				b.set_pressed_no_signal(false)
				return
			if on:
				gewaehlt.append(id)
			else:
				gewaehlt.erase(id)
			ok.disabled = gewaehlt.size() != n)
		g.add_child(b)
	_wahl_fertig = fertig
	ok.pressed.connect(func():
		_wahl_panel.queue_free()
		_wahl_panel = null
		fertig.call(gewaehlt.duplicate()))
	v.add_child(ok)
	_wahl_panel.reset_size()
	_wahl_panel.position = (_vs() - _wahl_panel.get_combined_minimum_size()) * 0.5


func wahl_offen() -> bool:
	return _wahl_panel != null


func karte_lage(diff: float) -> void:
	_karte_diff = diff
	if _karte != null:
		_karte.queue_redraw()


func _karte_draw() -> void:
	var c := _karte
	var w := c.size.x
	var h := c.size.y
	var paper := Color(0.9, 0.82, 0.62, 0.86)
	var ink := Color(0.35, 0.22, 0.12, 0.95)
	c.draw_rect(Rect2(Vector2.ZERO, c.size), paper)
	c.draw_rect(Rect2(Vector2.ZERO, c.size), Color(0.5, 0.35, 0.2), false, 3.0)
	var off := clampf(_karte_diff / 1.2, -1.0, 1.0) * w * 0.45      # the drawn ridge moves with the view: it fits at 0
	var pts := PackedVector2Array()
	for i in range(13):
		var x := w * i / 12.0
		pts.append(Vector2(x + off, h * (0.42 + 0.12 * sin(i * 1.3) + 0.05 * sin(i * 3.1))))
	c.draw_polyline(pts, ink, 3.0)
	var mid := Vector2(w * 0.5 + off, h * 0.48)
	c.draw_line(Vector2(w * 0.5, h * 0.9), mid, ink, 2.0)            # the line from the cairn
	c.draw_colored_polygon(PackedVector2Array([mid + Vector2(-8, 14), mid + Vector2(8, 14), mid]), ink)
	for k in range(3):                                                # the cairn
		c.draw_circle(Vector2(w * 0.5, h * 0.9 - k * 9), 9 - k * 2, ink)
	var ok := absf(_karte_diff) < 0.2
	c.draw_string(ThemeDB.fallback_font, Vector2(14, h - 12), T.t("passt!") if ok else (T.t("weiter nach links") if _karte_diff < 0.0 else T.t("weiter nach rechts")),
			HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color(0.15, 0.45, 0.15) if ok else ink)


func blitz() -> void:
	_fade.color = Color(1, 1, 1, 0.85)
	var tw := create_tween()
	tw.tween_property(_fade, "color", Color(1, 1, 1, 0), 0.35)
	tw.tween_callback(func(): _fade.color = Color(0, 0, 0, 0))


func ende(text: String, badges: Array) -> void:
	if _ende != null:
		_ende.queue_free()
	_ende = PanelContainer.new()
	_ende.add_theme_stylebox_override("panel", UI.box(Color(0.04, 0.05, 0.07, 0.9), Color(1, 0.8, 0.45, 0.7), 16, 22, 1))
	root.add_child(_ende)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	_ende.add_child(v)
	var t := _label(24, Color(1, 0.88, 0.6))
	t.text = text
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(t)
	var D = kit.daten
	for id in D.ABZEICHEN:
		var a: Array = D.ABZEICHEN[id]
		var l := _label(16, Color(0.75, 1.0, 0.8) if id in badges else Color(0.6, 0.62, 0.66))
		l.text = ("★ " if id in badges else "☆ ") + T.t(str(a[0])) + " – " + T.t(str(a[1]))
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.custom_minimum_size = Vector2(minf(_vs().x - 80.0, 560.0), 0)
		v.add_child(l)
	var b := Button.new()
	b.text = T.t("Abenteuer beenden")
	b.custom_minimum_size = Vector2(240, 46)
	b.pressed.connect(func(): kit.stop())
	v.add_child(b)
	_ende.position = (_vs() - _ende.get_combined_minimum_size()) * 0.5


# ---- compass ---------------------------------------------------------------------------------------------------------------
func _kompass_draw() -> void:
	var c := _kompass
	var w := c.size.x
	var h := c.size.y
	c.draw_rect(Rect2(Vector2.ZERO, c.size), Color(0.03, 0.05, 0.07, 0.45))
	var cam: Camera3D = kit.main.view_cam
	if cam == null:
		return
	var fw := -cam.global_transform.basis.z
	var yaw := atan2(fw.x, -fw.z)                         # 0 = north (world -z), clockwise
	yaw += float(kit.nord_off())
	var font := ThemeDB.fallback_font
	var fs := int(h * 0.55)
	var span := deg_to_rad(110.0)
	for e in [[0.0, "N"], [PI * 0.5, "O"], [PI, "S"], [PI * 1.5, "W"]]:
		var d := wrapf(float(e[0]) - yaw, -PI, PI)
		if absf(d) < span * 0.5:
			var x := w * 0.5 + d / span * w
			c.draw_string(font, Vector2(x - fs * 0.3, h * 0.72), T.t(str(e[1])), HORIZONTAL_ALIGNMENT_LEFT, -1, fs,
					Color(1, 0.55, 0.45) if e[1] == "N" else Color(0.9, 0.92, 0.95))
	for i in range(12):
		var d2 := wrapf(TAU * i / 12.0 - yaw, -PI, PI)
		if absf(d2) < span * 0.5 and i % 3 != 0:
			var x2 := w * 0.5 + d2 / span * w
			c.draw_line(Vector2(x2, h * 0.25), Vector2(x2, h * 0.5), Color(1, 1, 1, 0.5), 1.0)
	var zp = kit.ziel_welt()
	if zp is Vector3:
		var to: Vector3 = zp - cam.global_position
		var za := atan2(to.x, -to.z) + float(kit.nord_off())
		var d3 := clampf(wrapf(za - yaw, -PI, PI), -span * 0.5, span * 0.5)
		var x3 := w * 0.5 + d3 / span * w
		c.draw_colored_polygon(PackedVector2Array([Vector2(x3 - 7, h), Vector2(x3 + 7, h), Vector2(x3, h - 10)]), Color(1, 0.8, 0.3))
	c.draw_line(Vector2(w * 0.5, 0), Vector2(w * 0.5, h * 0.2), Color(1, 1, 1, 0.9), 2.0)


# ---- touch ---------------------------------------------------------------------------------------------------------------
func _stick_draw() -> void:
	var r := stick.size.x * 0.5
	stick.draw_circle(_stick_c, r * 0.92, Color(0.05, 0.08, 0.1, 0.32))
	stick.draw_arc(_stick_c, r * 0.92, 0.0, TAU, 48, Color(1, 1, 1, 0.45), 2.0)
	stick.draw_circle(_stick_c + stick_v * r * 0.6, r * 0.36, Color(1, 1, 1, 0.55 if _stick_idx != -2 else 0.35))


func _stick_set(p: Vector2) -> void:
	var r := stick.size.x * 0.5 * 0.6
	stick_v = ((p - _stick_c) / r).limit_length(1.0)


func _stick_input(ev: InputEvent) -> void:
	if ev is InputEventScreenTouch:
		if ev.pressed and _stick_idx == -2:
			_stick_idx = ev.index
			_stick_set(ev.position)
		elif not ev.pressed and ev.index == _stick_idx:
			_stick_idx = -2
			stick_v = Vector2.ZERO
		stick.accept_event()
	elif ev is InputEventScreenDrag and ev.index == _stick_idx:
		_stick_set(ev.position)
		stick.accept_event()
	elif ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT and not DisplayServer.is_touchscreen_available():
		if ev.pressed:
			_stick_idx = -1
			_stick_set(ev.position)
		else:
			_stick_idx = -2
			stick_v = Vector2.ZERO
		stick.accept_event()
	elif ev is InputEventMouseMotion and _stick_idx == -1:
		_stick_set(ev.position)
		stick.accept_event()


func _swipe_input(ev: InputEvent) -> void:
	if ev is InputEventScreenTouch:
		if ev.pressed and _swipe_idx == -2:
			_swipe_idx = ev.index
			_swipe_last = ev.position
		elif not ev.pressed and ev.index == _swipe_idx:
			_swipe_idx = -2
	elif ev is InputEventScreenDrag and ev.index == _swipe_idx:
		look_d += (ev.position - _swipe_last)
		_swipe_last = ev.position


func nimm_touch() -> Dictionary:
	"""what the touch controls did since the last frame (then cleared)"""
	var o := {"mv": stick_v, "look": look_d, "aktion": tap_akt, "sprung": tap_sprung, "sprung_h": halt_sprung}
	look_d = Vector2.ZERO
	tap_akt = false
	tap_sprung = false
	return o
