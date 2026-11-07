// «Flora und Fauna» Paket 1 (scripts/baeume.gd): tufts of leaf / needle cards at the ends of the branches. Alpha test.
// INSTANCE_CUSTOM.xyz = from the card to the centre of the crown (the same for the whole tree: same sway as the bark, same
// near / far switch), .w = height in the crown part + 1 (0..2) + 4 * index of the crown material (cols / states).
// Image: R = brightness, G = 1 leaf / 0 twig, B = 1 flower / berry, A = cover. Season per crown material: states[k].x bare, .y blossom.
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;

uniform sampler2D leaf_tex : filter_linear_mipmap, repeat_disable;
uniform sampler2D noise_tex;
uniform vec4 cols[16] : source_color;
uniform vec4 states[16];
uniform vec4 twig_col : source_color = vec4(0.35, 0.27, 0.2, 0.0);
uniform float conifer = 0.0;
uniform float wind = 0.0;
uniform float gust_amt = 0.0;
uniform vec2 dir = vec2(0.8, 0.6);
uniform float cloud_amt = 0.0;
uniform vec2 cloud_off = vec2(0.0);
uniform float near_d = 45.0;
uniform float backlight_k = 0.15;
uniform vec4 bluete_col : source_color = vec4(0.8, 0.8, 0.8, 1.0);   // image B = 1: flowers / berries (alpine rose, elder)
uniform float bluete_an = 1.0;

varying vec3 wpos;
varying vec3 outn;
varying float hue;
varying vec3 v_col;
varying float v_bl;

void vertex() {
	vec3 cardw = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	vec3 cw = cardw + INSTANCE_CUSTOM.xyz;
	float kf = floor(INSTANCE_CUSTOM.w / 4.0);
	float up = INSTANCE_CUSTOM.w - kf * 4.0;
	int k = clamp(int(kf + 0.5), 0, 15);
	float bare = states[k].x;
	v_bl = states[k].y;
	v_col = cols[k].rgb;
	hue = fract(sin(dot(cw.xz, vec2(12.9898, 78.233))) * 43758.5453);
	float drop = fract(sin(dot(cardw.xz + cardw.y, vec2(39.346, 11.135))) * 24634.634);
	if (length(cw - CAMERA_POSITION_WORLD) > near_d || drop < bare * 1.02) {
		VERTEX = vec3(0.0);                        // far away: the far picture; in autumn / winter the tufts fall one by one
		wpos = cardw;
	} else {
		float a = wind / 60.0 * (1.0 - 0.75 * bare);
		float s = sin(TIME * (1.2 + a) + cw.x * 0.37 + cw.z * 0.21);
		float f = sin(TIME * 4.3 + cw.z + (up - 1.0) * 3.0) * 0.25;
		vec3 sway = vec3((s + f) * a * 0.35 * up * (1.0 - 0.5 * gust_amt), 0.0, (s * 0.4) * a * 0.2 * up * (1.0 - 0.5 * gust_amt));
		vec3 vw0 = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
		vec3 vw = vw0;
		if (gust_amt > 0.0) {
			float g = smoothstep(0.3, 0.8, texture(noise_tex, (cw.xz - dir * TIME * (0.6 + wind * 0.03)) * 0.02).r);
			float lean = (0.3 + 1.1 * g) * a + sin(TIME * (1.6 + a) + cw.x * 0.5) * 0.25 * a * g;
			sway += vec3(dir.x, 0.0, dir.y) * lean * 0.3 * up * gust_amt;
		}
		float flutter = sin(TIME * (6.0 + 6.0 * a) + vw.x * 5.0 + vw.y * 4.0 + vw.z * 6.0) * 0.025 * min(a * 2.0 + 0.15, 1.2) * (1.0 - conifer * 0.7);
		vw += sway + vec3(flutter, flutter * 0.6, -flutter);
		VERTEX += inverse(mat3(MODEL_MATRIX)) * (vw - vw0);
		wpos = vw;
	}
	outn = normalize(wpos - cw + vec3(0.0, 0.6, 0.0));
}

void fragment() {
	vec4 t = texture(leaf_tex, UV);
	if (t.a < 0.5) {
		discard;
	}
	float n = texture(noise_tex, wpos.xz * 0.15 + wpos.y * 0.1).r;
	vec3 leaf = v_col * (0.65 + 0.6 * n) * (0.35 + 0.7 * t.r);
	leaf *= mix(vec3(0.92, 1.0, 0.9), vec3(1.08, 1.02, 0.86), hue);
	vec3 col = mix(twig_col.rgb * (0.6 + 0.6 * t.r), leaf, step(0.5, t.g));
	if (t.b > 0.5 && t.g > 0.5) {
		col = bluete_an > 0.5 ? bluete_col.rgb * (0.55 + 0.6 * t.r) : leaf;
	}
	if (v_bl > 0.0 && t.g > 0.5 && texture(noise_tex, wpos.xz * 1.7 + vec2(wpos.y * 1.3)).r > 1.0 - 0.45 * v_bl) {
		col = mix(vec3(0.86, 0.84, 0.82), vec3(0.88, 0.7, 0.76), n);
	}
	// lit like a crown (normal out of the crown) with a bit of the card's own face: single sprays catch the light
	vec3 cn = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz) * (FRONT_FACING ? 1.0 : -1.0);
	vec3 nw = normalize(outn * 0.7 + cn * 0.3);
	float inner = clamp(dot(outn, normalize(CAMERA_POSITION_WORLD - wpos)), 0.0, 1.0);
	col *= 0.78 + 0.25 * inner;
	col *= 1.0 - cloud_amt * smoothstep(0.52, 0.68, texture(noise_tex, (wpos.xz + cloud_off) * 0.0035).r);
	ALBEDO = col;
	NORMAL = normalize((VIEW_MATRIX * vec4(nw, 0.0)).xyz);
	ROUGHNESS = conifer > 0.5 ? 0.8 : 0.7;
	SPECULAR = conifer > 0.5 ? 0.2 : 0.35;
	BACKLIGHT = col * backlight_k * (1.0 - conifer * 0.6);
}
