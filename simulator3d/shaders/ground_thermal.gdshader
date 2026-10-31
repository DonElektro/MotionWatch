// Thermal picture of the ground: warmer near the camera's feet in the sun, a pattern of warmer / cooler patches,
// further away it looks colder (flat angle: the ground reflects more of the cold sky), the air in between (fog).
shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/thermal_inc.gdshaderinc"

uniform float temp = 15.0;
uniform float far_temp = 10.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float d = length(VERTEX);
	float n = vnoise(w.xz * 0.35) * 1.6 + vnoise(w.xz * 2.0) * 0.6 - 1.1;
	float t = mix(temp + n, far_temp, clamp(d / 600.0, 0.0, 1.0));
	ALBEDO = th_encode(th_atm(t, d));
}
