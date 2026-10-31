// Tree crowns that move in the wind.
shader_type spatial;
render_mode cull_disabled;

uniform vec4 color : source_color = vec4(0.18, 0.4, 0.17, 1.0);
uniform float wind = 0.0;      // km/h
uniform sampler2D noise_tex;
// «Jahreszeiten» (jahreszeiten.gd): broad-leaved trees bare in winter (only branches left) and blossoming in spring
uniform float bare = 0.0;       // 0 = full crown, 1 = bare (only twigs)
uniform float blossom = 0.0;    // 0 .. 1: white-pink blossoms between the leaves
uniform float cloud_amt = 0.0;      // 3D-4.x gelaende.gd: cloud shadows (0 = off)
uniform vec2 cloud_off = vec2(0.0);

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float a = wind / 60.0 * (1.0 - 0.75 * bare);   // bare twigs hardly sway
	float s = sin(TIME * (1.2 + a) + wp.x * 0.37 + wp.z * 0.21);
	float f = sin(TIME * 4.3 + wp.z + VERTEX.y * 3.0) * 0.25;
	VERTEX.x += (s + f) * a * 0.35 * clamp(VERTEX.y + 1.0, 0.0, 2.0);
	VERTEX.z += (s * 0.4) * a * 0.2 * clamp(VERTEX.y + 1.0, 0.0, 2.0);
}

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float n = texture(noise_tex, w.xz * 0.15 + w.y * 0.1).r;
	vec3 col = color.rgb * (0.65 + 0.6 * n);
	if (bare > 0.0 || blossom > 0.0) {
		float f = texture(noise_tex, w.xz * 1.7 + vec2(w.y * 1.3, w.y * 0.6)).r;   // fine pattern: twigs, blossoms
		if (bare > 0.0) {
			if (f < bare * 0.82) {
				discard;                                     // the crown gets see-through: only a web of branches
			}
			col = mix(col, vec3(0.26, 0.2, 0.15) * (0.7 + 0.5 * n), bare);   // what is left: brown twigs
		}
		if (blossom > 0.0 && f > 1.0 - 0.45 * blossom) {
			col = mix(vec3(0.86, 0.84, 0.82), vec3(0.88, 0.7, 0.76), n);    // apple / cherry blossom
		}
	}
	ALBEDO = col * (1.0 - cloud_amt * smoothstep(0.52, 0.68, texture(noise_tex, (w.xz + cloud_off) * 0.0035).r));   // gelaende.gd: cloud shadows
	ROUGHNESS = 0.9;
}
