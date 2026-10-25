// Thermal camera: every surface shows its temperature as a grey value (decoded again by main.gd).
// T = -40 °C -> 0, T = +80 °C -> 1 (linear). "spread" adds a little natural unevenness.
shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;

uniform float temp = 15.0;
uniform float spread = 0.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float n = (hash(floor(w.xz * 2.0)) - 0.5) * spread;
	float v = clamp((temp + n + 40.0) / 120.0, 0.0, 1.0);
	ALBEDO = vec3(v);
}
