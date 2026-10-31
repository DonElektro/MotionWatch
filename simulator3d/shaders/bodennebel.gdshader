// Paket «Wetter physikalisch» (real-wetter): Bodennebel im Kamerabild. Ein Viereck vor der Kamera liest die Tiefe jedes
// Bildpunkts und rechnet, wie viel Nebel der Blick durchquert: Dichte am Boden «dens0» (1/m), nach oben exponentiell
// dünner (Schichthöhe «hscale» m). Optische Dicke entlang des Strahls (geschlossene Formel), Transmission exp(-τ).
// Fleckig und ziehend: die Dichte schwankt mit einem Rauschen über dem Boden, das mit dem Wind wandert («drift»).
// Die Ansicht im Fenster nimmt den Höhennebel der Umgebung (main.env), dieses Viereck sehen nur die Kameras.
shader_type spatial;
render_mode unshaded, blend_mix, depth_test_disabled, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform float dens0 = 0.0;
uniform float hscale = 1.2;
uniform float ground_y = 0.0;
uniform vec3 fcol = vec3(0.8);
uniform vec2 drift = vec2(0.0);
uniform float patchy = 0.5;
uniform float expo = 1.0;
uniform float max_dist = 600.0;
uniform bool compat = false;       // wetter.gd: true im Compatibility-Renderer

float hh(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float vn(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hh(i), hh(i + vec2(1, 0)), u.x), mix(hh(i + vec2(0, 1)), hh(i + vec2(1, 1)), u.x), u.y);
}
float patches(vec2 xz) {
	vec2 q = (xz + drift) / 38.0;
	return 0.6 * vn(q) + 0.4 * vn(q * 2.3 + 7.1);
}

void fragment() {
	if (dens0 <= 0.00001) {
		discard;
	}
	float depth = texture(depth_tex, SCREEN_UV).r;
	// Compatibility-Renderer (Lite / Pi): Tiefe 0..1 statt NDC (Godot 4.3 kennt CURRENT_RENDERER noch nicht -> Uniform)
	vec3 ndc = compat ? vec3(SCREEN_UV, depth) * 2.0 - 1.0 : vec3(SCREEN_UV * 2.0 - 1.0, depth);
	vec4 vw = INV_PROJECTION_MATRIX * vec4(ndc, 1.0);
	vec3 vpos = vw.xyz / vw.w;
	vec3 cp = CAMERA_POSITION_WORLD;
	vec3 dir = normalize((INV_VIEW_MATRIX * vec4(vpos, 0.0)).xyz);
	float L = min(length(vpos), max_dist);
	vec3 wp = cp + dir * L;
	float y0 = max(cp.y - ground_y, 0.0);
	float y1 = max(wp.y - ground_y, 0.0);
	float H = max(hscale, 0.1);
	float dy = y1 - y0;
	float od;
	if (abs(dy) > 0.02) {
		od = dens0 * H * L / dy * (exp(-y0 / H) - exp(-y1 / H));
	} else {
		od = dens0 * L * exp(-y0 / H);
	}
	// fleckig: Dichte an drei Stellen entlang des Blicks
	float pm = (patches(mix(cp.xz, wp.xz, 0.2)) + patches(mix(cp.xz, wp.xz, 0.55)) + patches(wp.xz)) / 3.0;
	od *= mix(1.0, 0.25 + 1.5 * pm, patchy);
	float a = 1.0 - exp(-max(od, 0.0));
	ALBEDO = fcol * clamp(expo, 0.0, 1.0);
	ALPHA = clamp(a, 0.0, 0.97);
}
