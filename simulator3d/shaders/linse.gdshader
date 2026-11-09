// Paket «Wetter physikalisch» (real-wetter): Tropfen und Beschlag auf der Linse (scripts/linse.gd rechnet die Physik und
// schreibt eine kleine Karte). Ein eigenes Viereck vor der Kamera, nach camfx und vor lens (Körnung bleibt obendrauf).
// Im Tropfen: das Bild hinter dem Viereck, gebrochen (verkehrt), verschwommen, Rand dunkel, ein Glanzpunkt.
// Beschlag: weich gezeichnet und milchig; wo ein Tropfen hinuntergeronnen ist, ist die Linse wieder klar.
// Das gelesene Bild ist noch nicht belichtet (expo.gdshader kommt im Bild erst danach) - darum hier × expo.
shader_type spatial;
render_mode unshaded, blend_mix, depth_test_disabled, depth_draw_never, cull_disabled, shadows_disabled;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear;
uniform sampler2D drop_map : filter_linear;
uniform vec2 res = vec2(960.0, 540.0);
uniform float expo = 1.0;
uniform float fog = 0.0;            // Beschlag 0..1
uniform float strength = 1.0;
uniform float refr = 0.055;         // wie stark ein Tropfen das Bild verschiebt (Anteil der Bildbreite)
uniform float blur_px = 3.0;
uniform float mul_expo = 1.0;      // 1 = das gelesene Bild ist noch unbelichtet (Test: 0)
// sim-kamerabild (Normal / Hoch, nicht in festen Testläufen): die Tropfen sitzen auf dem Fenster des Gehäuses, ein paar mm vor
// der Linse - weit unscharf: weiche, durchscheinende, etwas milchige Flecken statt scharfer Scheiben mit dunklem Rand.
// 0 = wie vorher (Lite, Prüfstand: gleiche Bilder).
uniform float soft_drops = 0.0;

// Godot 4.3 Kompatibilität (GLES3): das Bildschirm-Bild (color_buffer) ist erst nach den eigenen Funktionen deklariert -
// darum wird es nicht in einer Funktion gelesen, sondern mit einem Makro direkt in fragment() (sonst «color_buffer undeclared»
// im Kompatibilitäts-Renderer, jeder Treiber). Gleiche Rechnung wie vorher: Mitte 0.28, vier Nachbarn je 0.12, vier schräge je 0.06.
#define GRAB(G_UV, G_R) (texture(screen_tex, (G_UV)).rgb * 0.28 + texture(screen_tex, (G_UV) + vec2((vec2(G_R) / res).x, 0.0)).rgb * 0.12 + texture(screen_tex, (G_UV) - vec2((vec2(G_R) / res).x, 0.0)).rgb * 0.12 + texture(screen_tex, (G_UV) + vec2(0.0, (vec2(G_R) / res).y)).rgb * 0.12 + texture(screen_tex, (G_UV) - vec2(0.0, (vec2(G_R) / res).y)).rgb * 0.12 + texture(screen_tex, (G_UV) + (vec2(G_R) / res) * 0.7).rgb * 0.06 + texture(screen_tex, (G_UV) - (vec2(G_R) / res) * 0.7).rgb * 0.06 + texture(screen_tex, (G_UV) + vec2((vec2(G_R) / res).x, -(vec2(G_R) / res).y) * 0.7).rgb * 0.06 + texture(screen_tex, (G_UV) + vec2(-(vec2(G_R) / res).x, (vec2(G_R) / res).y) * 0.7).rgb * 0.06)

void fragment() {
	vec4 m = texture(drop_map, UV);
	float th = m.b;
	float fg = fog * m.a;
	if (th < 0.03 && fg < 0.01) {
		discard;
	}
	vec2 n = (m.rg - 0.5) * 2.0;
	float e = mix(1.0, clamp(expo, 0.0, 1.0), mul_expo);
	vec3 col;
	float a;
	if (th > 0.77) {
		// Schnee auf der Linse: weiss, kaum durchsichtig, nimmt das Licht der Umgebung an
		vec3 bg = GRAB(SCREEN_UV, blur_px * 3.0) * e;
		float l = dot(bg, vec3(0.333));
		col = vec3(0.55 + 0.45 * clamp(l * 2.0, 0.0, 1.0)) * mix(0.35, 1.0, e);
		a = 0.92;
	} else if (th >= 0.03) {
		th = th / 0.745;                                                   // Wasser: B bis 190 (darüber Schnee)
		if (soft_drops > 0.5) {
			// unscharf: das Bild dahinter weich gezeichnet und nur wenig verschoben, ein heller Schleier (Streulicht im Wasser),
			// durchscheinend mit weichem Rand - so sehen Tropfen auf der Scheibe vor einer Kamera mit Fokus auf die Ferne aus
			vec2 uv = clamp(SCREEN_UV - n * refr * 0.3 * th, vec2(0.002), vec2(0.998));
			vec3 bl = (GRAB(uv, blur_px * (3.0 + 3.0 * th)) + GRAB(uv, blur_px * (1.5 + 1.5 * th))) * 0.5 * e;
			col = mix(bl, vec3(dot(bl, vec3(0.333))), 0.2) * 0.95 + vec3(0.045 * (0.3 + 0.7 * e));
			float spec = pow(max(0.0, dot(normalize(n + vec2(0.0001)), normalize(vec2(-0.55, -0.75)))), 6.0) * th;
			col += vec3(spec * 0.18 * (0.25 + 0.75 * e));
			a = smoothstep(0.0, 0.9, th) * 0.55;
		} else {
		// Wassertropfen: kleine Linse - verkehrtes, verschwommenes Bild der Umgebung
		vec2 uv = clamp(SCREEN_UV - n * refr * (0.4 + th), vec2(0.002), vec2(0.998));
		col = GRAB(uv, blur_px * (1.0 + 1.5 * th)) * e;
		col *= mix(0.45, 1.05, smoothstep(0.05, 0.55, th));                 // Rand dunkel (Totalreflexion)
		float spec = pow(max(0.0, dot(normalize(n + vec2(0.0001)), normalize(vec2(-0.55, -0.75)))), 12.0) * smoothstep(0.35, 0.75, 1.0 - th) * th;
		col += vec3(spec * 1.6 * (0.25 + 0.75 * e));
		a = smoothstep(0.03, 0.16, th) * 0.96;
		}
	} else {
		col = vec3(0.0);
		a = 0.0;
	}
	if (fg > 0.01) {
		// Beschlag: viele winzige Tröpfchen streuen das Licht - weich, weniger Kontrast, ein heller Schleier
		vec3 soft = GRAB(SCREEN_UV, 4.0 + 10.0 * fg) * e;
		vec3 veil = mix(soft, vec3(dot(soft, vec3(0.333))) * 0.6 + vec3(0.35) * (0.25 + 0.75 * e), 0.45 * fg);
		float fa = clamp(fg * 1.1, 0.0, 0.95);
		col = mix(veil, col, a);
		a = max(a, fa);
	}
	ALBEDO = col;
	ALPHA = clamp(a * strength, 0.0, 1.0);
}
