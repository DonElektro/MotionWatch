// Tree crowns that move in the wind.
shader_type spatial;
render_mode cull_disabled;

uniform vec4 color : source_color = vec4(0.18, 0.4, 0.17, 1.0);
uniform float wind = 0.0;      // km/h
uniform sampler2D noise_tex;

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float a = wind / 60.0;
	float s = sin(TIME * (1.2 + a) + wp.x * 0.37 + wp.z * 0.21);
	float f = sin(TIME * 4.3 + wp.z + VERTEX.y * 3.0) * 0.25;
	VERTEX.x += (s + f) * a * 0.35 * clamp(VERTEX.y + 1.0, 0.0, 2.0);
	VERTEX.z += (s * 0.4) * a * 0.2 * clamp(VERTEX.y + 1.0, 0.0, 2.0);
}

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float n = texture(noise_tex, w.xz * 0.15 + w.y * 0.1).r;
	ALBEDO = color.rgb * (0.65 + 0.6 * n);
	ROUGHNESS = 0.9;
}
