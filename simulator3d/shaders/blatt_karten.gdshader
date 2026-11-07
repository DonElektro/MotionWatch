// «Flora und Fauna» Phase 1 (scripts/flora.gd): leaf / needle cards on the crowns. Alpha test (no blending: fast on old
// Intel graphics too), the crown's colour, season (bare / blossom), wind (the same sway as foliage.gdshader, with the
// centre of the crown part from INSTANCE_CUSTOM.xyz and the height in it from INSTANCE_CUSTOM.w), cloud shadows.
// Lit like a round crown (the normal points out of the crown, not out of the card), a little light comes through (backlight).
// Far away the cards shrink to nothing (the crown stays) - no shimmer, less to draw.
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;

uniform sampler2D leaf_tex : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D noise_tex;
uniform vec4 color : source_color = vec4(0.18, 0.4, 0.17, 1.0);
uniform float wind = 0.0;
uniform float bare = 0.0;
uniform float blossom = 0.0;
uniform float cloud_amt = 0.0;
uniform vec2 cloud_off = vec2(0.0);
uniform float gust_amt = 0.0;
uniform vec2 dir = vec2(0.8, 0.6);
uniform float far = 55.0;
uniform float backlight_k = 0.3;

varying vec3 wpos;
varying vec3 outn;
varying float hue;

void vertex() {
	vec3 cardw = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;   // MODEL_MATRIX includes the instance (MultiMesh)
	vec3 cw = cardw + INSTANCE_CUSTOM.xyz;            // centre of the crown part = the card + offset (scene root: no turn / scale)
	float d = length(cardw - CAMERA_POSITION_WORLD);
	float shrink = 1.0 - smoothstep(far * 0.7, far, d);
	VERTEX *= shrink;
	// sway like the crown (foliage.gdshader): origin of the part + height in it
	float a = wind / 60.0 * (1.0 - 0.75 * bare);
	float up = clamp(INSTANCE_CUSTOM.w, 0.0, 2.0);
	float s = sin(TIME * (1.2 + a) + cw.x * 0.37 + cw.z * 0.21);
	float f = sin(TIME * 4.3 + cw.z + (INSTANCE_CUSTOM.w - 1.0) * 3.0) * 0.25;
	vec3 sway = vec3((s + f) * a * 0.35 * up * (1.0 - 0.5 * gust_amt), 0.0, (s * 0.4) * a * 0.2 * up * (1.0 - 0.5 * gust_amt));
	vec3 vw0 = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vec3 vw = vw0;
	if (gust_amt > 0.0) {
		float g = smoothstep(0.3, 0.8, texture(noise_tex, (cw.xz - dir * TIME * (0.6 + wind * 0.03)) * 0.02).r);
		float lean = (0.3 + 1.1 * g) * a + sin(TIME * (1.6 + a) + cw.x * 0.5) * 0.25 * a * g;
		sway += vec3(dir.x, 0.0, dir.y) * lean * 0.3 * up * gust_amt;
	}
	float flutter = sin(TIME * (6.0 + 6.0 * a) + vw.x * 5.0 + vw.y * 4.0 + vw.z * 6.0) * 0.03 * min(a * 2.0 + 0.15, 1.2);
	vw += sway + vec3(flutter, flutter * 0.6, -flutter);
	VERTEX += inverse(mat3(MODEL_MATRIX)) * (vw - vw0);
	wpos = vw;
	outn = normalize(vw - cw + vec3(0.0, 0.25, 0.0));
	hue = fract(sin(dot(cw.xz, vec2(12.9898, 78.233))) * 43758.5453);
	NORMAL = (inverse(MODEL_MATRIX) * vec4(outn, 0.0)).xyz;
}

void fragment() {
	vec4 t = texture(leaf_tex, UV);
	float keep = t.a;
	if (bare > 0.0) {
		float fb = texture(noise_tex, wpos.xz * 1.9 + vec2(wpos.y)).r;
		keep *= step(bare * 1.05, fb + 0.02);          // in autumn / winter the leaves go
	}
	if (keep < 0.5) {
		discard;
	}
	float n = texture(noise_tex, wpos.xz * 0.15 + wpos.y * 0.1).r;
	vec3 col = color.rgb * (0.62 + 0.62 * n) * (0.55 + 0.6 * t.r);
	col *= mix(vec3(0.92, 1.0, 0.9), vec3(1.08, 1.02, 0.86), hue);    // every tree a little different
	float inner = clamp(dot(outn, normalize(CAMERA_POSITION_WORLD - wpos)), 0.0, 1.0);
	col *= 0.8 + 0.25 * inner;
	if (blossom > 0.0 && texture(noise_tex, wpos.xz * 1.7 + vec2(wpos.y * 1.3)).r > 1.0 - 0.45 * blossom) {
		col = mix(vec3(0.86, 0.84, 0.82), vec3(0.88, 0.7, 0.76), n);
	}
	col *= 1.0 - cloud_amt * smoothstep(0.52, 0.68, texture(noise_tex, (wpos.xz + cloud_off) * 0.0035).r);
	ALBEDO = col;
	NORMAL = normalize((VIEW_MATRIX * vec4(outn, 0.0)).xyz);
	ROUGHNESS = 0.85;
	SPECULAR = 0.25;
	BACKLIGHT = col * backlight_k;
}
