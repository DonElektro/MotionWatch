// Tree crowns that move in the wind.
shader_type spatial;
render_mode cull_disabled;

uniform vec4 color : source_color = vec4(0.18, 0.4, 0.17, 1.0);
uniform float wind = 0.0;      // km/h
uniform sampler2D noise_tex;
// F6 (31.10.2026, wind_fx.gd): gusts roll through crowns and bushes in the direction of the wind, leaves flutter.
// gust_amt 0 = only the old sway (switched off); Lite: weak.
uniform float gust_amt = 0.0;
uniform vec2 dir = vec2(0.8, 0.6);

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float a = wind / 60.0;
	float s = sin(TIME * (1.2 + a) + wp.x * 0.37 + wp.z * 0.21);
	float f = sin(TIME * 4.3 + wp.z + VERTEX.y * 3.0) * 0.25;
	float up = clamp(VERTEX.y + 1.0, 0.0, 2.0);
	VERTEX.x += (s + f) * a * 0.35 * up * (1.0 - 0.5 * gust_amt);
	VERTEX.z += (s * 0.4) * a * 0.2 * up * (1.0 - 0.5 * gust_amt);
	if (gust_amt > 0.0) {
		float g = smoothstep(0.3, 0.8, texture(noise_tex, (wp.xz - dir * TIME * (0.6 + wind * 0.03)) * 0.02).r);
		float lean = (0.3 + 1.1 * g) * a + sin(TIME * (1.6 + a) + wp.x * 0.5) * 0.25 * a * g;   // pushed downwind, swings back
		vec3 off = vec3(dir.x, 0.0, dir.y) * lean * 0.3 * up;
		vec3 wv = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
		float leaf = sin(TIME * (7.0 + 6.0 * a) + wv.x * 9.0 + wv.y * 7.0 + wv.z * 8.0) * 0.022 * min(a * 1.5, 1.2);   // fluttering leaves
		VERTEX += (inverse(mat3(MODEL_MATRIX)) * off + NORMAL * leaf * (0.4 + g)) * gust_amt;
	}
}

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float n = texture(noise_tex, w.xz * 0.15 + w.y * 0.1).r;
	ALBEDO = color.rgb * (0.65 + 0.6 * n);
	ROUGHNESS = 0.9;
}
