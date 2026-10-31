// Thermal camera for the figures with a skeleton (figur.gd, 3D-4.12): every corner of the body has its own temperature,
// stored in the vertex colour (r + g / 255 = (T + 40) / 120). Written like thermal.gdshader (14-bit code, air in between).
shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/thermal_inc.gdshaderinc"

uniform float spread = 0.6;
uniform float offset = 0.0;   // °C added to the whole figure (e.g. wet clothes)

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float n = (hash(floor(w.xz * 2.0)) - 0.5) * spread;
	float t = (COLOR.r + COLOR.g / 255.0) * 120.0 - 40.0 + offset;
	ALBEDO = th_encode(th_atm(t + n, length(VERTEX)));
}
