// 3D-4.x (gelaende.gd): a path of gravel, earth or stone slabs on the ground. UV.x = across (0..1), UV.y = along (m).
shader_type spatial;

uniform vec4 base : source_color = vec4(0.58, 0.55, 0.49, 1.0);
uniform vec4 grit : source_color = vec4(0.38, 0.36, 0.33, 1.0);
uniform vec4 edge_grass : source_color = vec4(0.25, 0.4, 0.16, 1.0);
uniform vec4 snow : source_color = vec4(0.93, 0.94, 0.96, 1.0);
uniform float grain = 1.0;          // gravel stones (1) … fine earth (0.3)
uniform float tracks = 0.0;         // 1 = two wheel tracks with grass in the middle (field path)
uniform float tiles = 0.0;          // 1 = stone slabs
uniform float snow_amount = 0.0;
uniform float wet = 0.0;
uniform float cloud_amt = 0.0;
uniform vec2 cloud_off = vec2(0.0);
uniform sampler2D noise_tex : repeat_enable;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float big = texture(noise_tex, w.xz * 0.08).r;
	float fine = texture(noise_tex, w.xz * 1.7).r;
	vec2 cell = floor(w.xz * 9.0);
	float stone = hash(cell);                           // single little stones
	vec3 c = mix(base.rgb, grit.rgb, smoothstep(0.35, 0.75, big));
	c *= 0.82 + 0.3 * fine;
	c = mix(c, c * (0.7 + 0.6 * stone), grain * 0.55);
	float across = abs(UV.x - 0.5) * 2.0;               // 0 middle … 1 edge
	if (tracks > 0.5) {                                  // field path: grass in the middle strip
		float mid = 1.0 - smoothstep(0.12, 0.3, across + 0.08 * (fine - 0.5));
		c = mix(c, edge_grass.rgb * (0.8 + 0.4 * fine), mid);
	}
	if (tiles > 0.5) {
		vec2 t = fract(vec2(UV.x * 2.0, UV.y / 0.6));
		float joint = step(0.94, max(t.x, t.y)) + step(max(t.x, t.y), 0.04);
		c *= 1.0 - 0.35 * clamp(joint, 0.0, 1.0);
	}
	float e = smoothstep(0.72, 1.0, across + 0.25 * (big - 0.5));   // the edge goes over into the meadow
	c = mix(c, edge_grass.rgb * (0.75 + 0.4 * fine), e * 0.85);
	c = mix(c, snow.rgb * (0.9 + 0.1 * fine), snow_amount * (0.75 + 0.25 * e));
	c *= 1.0 - cloud_amt * smoothstep(0.52, 0.68, texture(noise_tex, (w.xz + cloud_off) * 0.0035).r);
	ALBEDO = c * (1.0 - 0.4 * wet);
	ROUGHNESS = mix(0.95, 0.4, wet);
}
