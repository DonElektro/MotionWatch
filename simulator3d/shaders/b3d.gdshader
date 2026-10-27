// Buildings of swisstopo (3D Tiles, from 3D-3.10): no pictures on them - roofs get a roof colour, walls plaster with windows
// every 3 m (from the position in the world), at night some windows glow.
shader_type spatial;
render_mode cull_disabled;

uniform float night = 0.0;
varying vec3 wpos;
varying vec3 wnrm;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

void fragment() {
	vec3 n = normalize(wnrm);
	float cell = hash(floor(wpos.xz / 14.0));
	if (abs(n.y) > 0.4) {
		vec3 roof = mix(vec3(0.5, 0.24, 0.17), vec3(0.33, 0.31, 0.32), step(0.6, cell));
		ALBEDO = roof * (0.9 + 0.1 * hash(floor(wpos.xz * 2.0)));
		ROUGHNESS = 0.8;
	} else {
		float u = abs(n.x) > abs(n.z) ? wpos.z : wpos.x;
		vec2 g = vec2(u / 3.0, wpos.y / 3.0);
		vec2 f = fract(g);
		float win = step(0.3, f.x) * step(f.x, 0.7) * step(0.35, f.y) * step(f.y, 0.85);
		vec3 wall = mix(vec3(0.92, 0.9, 0.85), vec3(0.86, 0.8, 0.7), step(0.5, cell));
		ALBEDO = mix(wall, vec3(0.18, 0.21, 0.25), win);
		float lit = step(0.72, hash(floor(g) + cell * 7.0));
		EMISSION = vec3(1.0, 0.75, 0.42) * win * lit * night;
		ROUGHNESS = 0.9;
	}
}
