// Thermal camera: every surface shows its temperature (14-bit code, see thermal_inc.gdshaderinc - decoded by main.gd).
// "spread" adds a little natural unevenness. sky > 0.5: the dome of the sky - cold at the zenith, near the air at the
// horizon (the path through the air gets long: emissivity 1 - (1 - e_zenith)^(1 / sin elevation)).
shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/thermal_inc.gdshaderinc"

uniform float temp = 15.0;
uniform float spread = 0.0;
uniform float sky = 0.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float t;
	if (sky > 0.5) {
		vec3 dir = normalize(w - INV_VIEW_MATRIX[3].xyz);
		float s = max(dir.y, 0.03);
		float ta = th_air + 273.15;
		float ez = clamp(pow((temp + 273.15) / ta, 4.0), 0.0, 1.0);
		float e = 1.0 - pow(1.0 - ez, 1.0 / s);
		t = ta * pow(max(e, 0.01), 0.25) - 273.15;
		t = mix(th_air, t, exp(-th_atm_k * 300.0));       // fog / snow: the sky looks like the air
	} else {
		float n = (hash(floor(w.xz * 2.0)) - 0.5) * spread;
		t = th_atm(temp + n, length(VERTEX));
	}
	ALBEDO = th_encode(t);
}
