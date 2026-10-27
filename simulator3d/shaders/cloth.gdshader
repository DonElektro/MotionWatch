// cloth in the wind (from 3D-2.9): flags and laundry. UV.x = 0 at the fixed edge (pole / line), 1 at the free edge.
shader_type spatial;
render_mode cull_disabled;

uniform vec4 color : source_color = vec4(0.8, 0.1, 0.1, 1.0);
uniform float wind = 10.0;      // km/h (with gusts)
uniform float seed = 0.0;
uniform float hang = 0.0;       // 1 = laundry: fixed at the top edge (UV.y = 0), swings sideways

void vertex() {
	float w = clamp(wind / 50.0, 0.05, 1.6);
	float f = mix(UV.x, UV.y, hang);                 // how far from the fixed edge
	float s = sin(TIME * (2.0 + 3.0 * w) + f * 5.0 + seed) + 0.5 * sin(TIME * (5.1 + 2.0 * w) + f * 9.0 + seed * 1.7);
	VERTEX.z += s * 0.09 * w * f;                    // ripples
	VERTEX.x += mix(0.0, sin(TIME * 1.3 + seed) * 0.12 * w * f, hang);
}

void fragment() {
	ALBEDO = color.rgb * (0.85 + 0.15 * sin(UV.x * 20.0));
	ROUGHNESS = 0.95;
}
