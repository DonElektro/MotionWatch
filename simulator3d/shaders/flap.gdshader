// 3D-4.4 (simreal): a loose tarp or a pennant that flaps hard in the wind (stronger than cloth.gdshader: whole folds snap
// back and forth with the gusts - a classic cause of false alarms at night in the infrared light). UV.x = 0 at the fixed
// edge (pole / tent pole), 1 at the free edge; hang = 1: fixed at the top edge (a tarp over a line).
shader_type spatial;
render_mode cull_disabled;

uniform vec4 color : source_color = vec4(0.2, 0.35, 0.6, 1.0);
uniform float wind = 10.0;      // km/h (with gusts, set by main.gd like the cloth)
uniform float seed = 0.0;
uniform float hang = 0.0;
uniform float strength = 1.0;
uniform float phase = -1.0;     // real-wetter: the beat summed up from the wind (wetter.gd); < 0 = TIME as before

void vertex() {
	float w = clamp(wind / 35.0, 0.12, 1.8) * strength;
	float f = mix(UV.x, UV.y, hang);
	float t = (phase >= 0.0 ? phase * 3.0 : TIME * (3.0 + 4.0 * w)) + seed;
	float snap = pow(abs(sin((phase >= 0.0 ? phase * 0.9 : TIME * (0.9 + 0.6 * w)) + seed * 2.3)), 3.0);   // now and then a hard snap
	float s = sin(t + f * 4.0) + 0.6 * sin(t * 1.9 + f * 7.5 + seed) + 1.4 * snap * sin(t * 0.5 + f * 2.0);
	VERTEX.z += s * 0.16 * w * f * f;
	VERTEX.y += cos(t * 0.8 + f * 3.0) * 0.05 * w * f;
	NORMAL = normalize(NORMAL + vec3(0.0, 0.0, cos(t + f * 4.0) * 0.6 * w));
}

void fragment() {
	ALBEDO = color.rgb * (0.82 + 0.18 * sin(UV.x * 14.0 + UV.y * 3.0));
	ROUGHNESS = 0.9;
}
