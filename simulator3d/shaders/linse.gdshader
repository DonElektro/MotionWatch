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

vec3 grab(vec2 uv, float r) {
	vec2 o = vec2(r) / res;
	vec3 c = texture(screen_tex, uv).rgb * 0.28;
	c += texture(screen_tex, uv + vec2(o.x, 0.0)).rgb * 0.12;
	c += texture(screen_tex, uv - vec2(o.x, 0.0)).rgb * 0.12;
	c += texture(screen_tex, uv + vec2(0.0, o.y)).rgb * 0.12;
	c += texture(screen_tex, uv - vec2(0.0, o.y)).rgb * 0.12;
	c += texture(screen_tex, uv + o * 0.7).rgb * 0.06;
	c += texture(screen_tex, uv - o * 0.7).rgb * 0.06;
	c += texture(screen_tex, uv + vec2(o.x, -o.y) * 0.7).rgb * 0.06;
	c += texture(screen_tex, uv + vec2(-o.x, o.y) * 0.7).rgb * 0.06;
	return c;
}

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
		vec3 bg = grab(SCREEN_UV, blur_px * 3.0) * e;
		float l = dot(bg, vec3(0.333));
		col = vec3(0.55 + 0.45 * clamp(l * 2.0, 0.0, 1.0)) * mix(0.35, 1.0, e);
		a = 0.92;
	} else if (th >= 0.03) {
		th = th / 0.745;                                                   // Wasser: B bis 190 (darüber Schnee)
		// Wassertropfen: kleine Linse - verkehrtes, verschwommenes Bild der Umgebung
		vec2 uv = clamp(SCREEN_UV - n * refr * (0.4 + th), vec2(0.002), vec2(0.998));
		col = grab(uv, blur_px * (1.0 + 1.5 * th)) * e;
		col *= mix(0.45, 1.05, smoothstep(0.05, 0.55, th));                 // Rand dunkel (Totalreflexion)
		float spec = pow(max(0.0, dot(normalize(n + vec2(0.0001)), normalize(vec2(-0.55, -0.75)))), 12.0) * smoothstep(0.35, 0.75, 1.0 - th) * th;
		col += vec3(spec * 1.6 * (0.25 + 0.75 * e));
		a = smoothstep(0.03, 0.16, th) * 0.96;
	} else {
		col = vec3(0.0);
		a = 0.0;
	}
	if (fg > 0.01) {
		// Beschlag: viele winzige Tröpfchen streuen das Licht - weich, weniger Kontrast, ein heller Schleier
		vec3 soft = grab(SCREEN_UV, 4.0 + 10.0 * fg) * e;
		vec3 veil = mix(soft, vec3(dot(soft, vec3(0.333))) * 0.6 + vec3(0.35) * (0.25 + 0.75 * e), 0.45 * fg);
		float fa = clamp(fg * 1.1, 0.0, 0.95);
		col = mix(veil, col, a);
		a = max(a, fa);
	}
	ALBEDO = col;
	ALPHA = clamp(a * strength, 0.0, 1.0);
}
