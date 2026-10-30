extends CanvasLayer
## 3D-4.2x «Mehr» (Wunsch Daniel 30.10.2026): Hell / Rotlicht / Dunkel wie MoveEye (Reihenfolge Hell → Rotlicht → Dunkel,
## Farben aus ui_style.palette). Die Bedienelemente sind dunkel gebaut (ui_style.gd); dieses Ebene legt über das Bedienfeld
## und die Fenster (nicht über die 3D-Ansicht) einen Farbfilter:
##   * Hell: die Helligkeit wird umgedreht, der Farbton bleibt (dunkles Blau-Grau -> fast Weiss, helle Schrift -> dunkel,
##     Blau bleibt Blau) – ergibt fast genau die Farben von MoveEye «body.light».
##   * Rotlicht: alles sehr dunkel und rot (wie html.sxnight von MoveEye: für einen kurzen Blick im Zelt in der Nacht);
##     auch die Leiste unten wird rot, die 3D-Ansicht selbst bleibt.
##   * Dunkel: nichts (die Farben, wie sie gebaut sind).
## Ein einziges Rechteck über das ganze Fenster mit einer Liste von Bereichen (Shader liest das Bild darunter).

var main
var mode := "dark"
var _rect: ColorRect
var _mat: ShaderMaterial
var _targets: Array = []               # [Control, "all" | "red"]

const MAXR := 12
const UI = preload("res://scripts/ui_style.gd")
const SHADER := """
shader_type canvas_item;
uniform sampler2D scr : hint_screen_texture, repeat_disable, filter_nearest;
uniform int mode = 0;
uniform int n = 0;
uniform vec4 rects[12];
void fragment() {
	vec2 uv = SCREEN_UV;
	bool inside = false;
	for (int i = 0; i < 12; i++) {
		if (i >= n) break;
		vec4 r = rects[i];
		if (uv.x >= r.x && uv.y >= r.y && uv.x <= r.x + r.z && uv.y <= r.y + r.w) { inside = true; }
	}
	if (!inside) discard;
	vec3 c = textureLod(scr, uv, 0.0).rgb;
	if (mode == 1) {
		float l = (max(c.r, max(c.g, c.b)) + min(c.r, min(c.g, c.b))) * 0.5;
		c = clamp(c + vec3(1.0 - 2.0 * l), 0.0, 1.0);       // HSL: lightness turned round, hue and chroma stay
	} else {
		float l = dot(c, vec3(0.299, 0.587, 0.114));
		c = vec3(0.75, 0.13, 0.07) * pow(l, 1.1);             // red light: dark, red, no blue
	}
	COLOR = vec4(c, 1.0);
}
"""


func _ready() -> void:
	layer = 62                                        # above the panel (1) and the windows of «Mehr» (60), below the tour (63)
	_rect = ColorRect.new()
	_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	var sh := Shader.new()
	sh.code = SHADER
	_mat = ShaderMaterial.new()
	_mat.shader = sh
	_rect.material = _mat
	_rect.visible = false
	add_child(_rect)


func register(c: Control, which := "all") -> void:
	"""a control that follows the look: «all» (light and red) or «red» (only the red light, e.g. the bar over the 3D view)"""
	for t in _targets:
		if t[0] == c:
			return
	_targets.append([c, which])


func set_mode(m: String) -> void:
	mode = m if m in ["light", "red", "dark"] else "dark"
	UI.theme_now = mode
	_mat.set_shader_parameter("mode", 1 if mode == "light" else 2)
	_process(0.0)


func _process(_dt: float) -> void:
	if mode == "dark":
		_rect.visible = false
		return
	var vs: Vector2 = get_viewport().get_visible_rect().size
	var rs := []
	_targets = _targets.filter(func(t): return is_instance_valid(t[0]))
	for t in _targets:
		var c: Control = t[0]
		if rs.size() >= MAXR or not c.is_visible_in_tree() or (t[1] == "red" and mode != "red"):
			continue
		var r := c.get_global_rect()
		if r.size.x < 2.0 or r.size.y < 2.0:
			continue
		rs.append(Vector4(r.position.x / vs.x, r.position.y / vs.y, r.size.x / vs.x, r.size.y / vs.y))
	while rs.size() < MAXR:
		rs.append(Vector4.ZERO)
	var n := 0
	for r in rs:
		if (r as Vector4).z > 0.0:
			n += 1
	_mat.set_shader_parameter("rects", rs)
	_mat.set_shader_parameter("n", n)
	_rect.visible = n > 0
