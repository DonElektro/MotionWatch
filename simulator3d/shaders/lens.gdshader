// the lens and sensor of a camera (from 3D-2.5; exposure from 3D-2.6): the picture behind the quad is read (screen texture),
// multiplied with the exposure (at night: little light, limited amplification -> dark), then grain (stronger the more the
// camera amplifies), dark corners and raindrops. A quad just in front of the camera, only on its own layer.
shader_type spatial;
render_mode unshaded, blend_mix, depth_test_disabled, depth_draw_never, cull_disabled, shadows_disabled;

uniform float noise = 0.0;          // 0..1
uniform float vignette = 0.3;       // 0..1
uniform float drops = 0.0;          // 0..1 share of the places with a drop
uniform vec2 res = vec2(960.0, 540.0);
uniform float expo = 1.0;           // only for the brightness of raindrops (the exposure itself: expo.gdshader)

float h(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }

void fragment() {
	vec2 uv = UV;
	float d = distance(uv, vec2(0.5));
	float al = smoothstep(0.38, 0.9, d) * vignette;   // dark corners
	vec3 c = vec3(0.0);
	// grain: every pixel a bit brighter or darker, new each frame
	vec2 px = floor(uv * res);
	float g = (h(px + floor(TIME * 30.0) * vec2(17.31, 43.77)) - 0.5) * noise * 0.85;
	float ga = abs(g);
	vec3 gc = g > 0.0 ? vec3(1.0) : vec3(0.0);
	float na = ga + al * (1.0 - ga);
	c = (gc * ga + c * al * (1.0 - ga)) / max(na, 0.0001);
	al = na;
	// raindrops: a few round blurred spots, each comes and dries up again
	if (drops > 0.0) {
		vec2 grid = uv * vec2(8.0, 4.5);
		vec2 id = floor(grid);
		vec2 f = fract(grid) - 0.5;
		float r = h(id);
		float life = fract(TIME * 0.05 + r * 7.0);
		vec2 cc = (vec2(h(id + 3.1), h(id + 7.7)) - 0.5) * 0.6;
		float rad = 0.1 + 0.2 * h(id + 1.3);
		float dd = length((f - cc) * vec2(1.0, 1.25));
		float on = step(r, drops) * smoothstep(1.0, 0.6, life);
		float da = smoothstep(rad, rad * 0.4, dd) * on * 0.45;
		vec3 dc = vec3(0.82, 0.87, 0.93) * max(0.2, expo);
		float na2 = da + al * (1.0 - da);
		c = (dc * da + c * al * (1.0 - da)) / max(na2, 0.0001);
		al = na2;
	}
	ALBEDO = c;
	ALPHA = clamp(al, 0.0, 1.0);
}
