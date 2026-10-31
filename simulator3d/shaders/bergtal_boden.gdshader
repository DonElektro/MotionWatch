// Ground of the «Bergtal» (bergtal.gd, 3D-4.x): the colour of each point comes from the height map (meadow, alpine meadow,
// forest floor, moor, scree, glacier, shore - vertex colour); the shader adds rock on steep ground (several kinds of rock),
// snow by height, slope, the side facing north and the season, the autumn colour of the grass, wet ground and puddles in
// the rain and the snow of the weather (like the other grounds). VERTEX is in valley coordinates (y = height above the north end).
shader_type spatial;
render_mode cull_back;

uniform sampler2D noise_tex;
uniform vec4 snow : source_color = vec4(0.93, 0.94, 0.96, 1.0);
uniform float snow_amount = 0.0;      // weather «Schnee» (main.gd)
uniform float wet = 0.0;
uniform float puddle = 0.0;
uniform float snow_line = 900.0;      // season: above this height the ground is white (valley height, m)
uniform float snow_cover = 0.0;       // season: 1 = everything white (winter), except steep rock
uniform vec3 grass_tint = vec3(1.0);  // season: spring fresh, summer, autumn brown-yellow
uniform float detail = 1.0;
// K3 (31.10.2026): rooms in the hill (bunker, cave - bergtal_orte.gd): the ground is not drawn inside them. Only in a copy
// of this shader with «#define CLIPS» (bergtal.gd clip_ground) on the few chunks with such a room (discard costs a little).
// clip_a = (centre x, centre z, half x, half z), clip_b = (cos, sin of the turn, floor y, ceiling y), all in valley coordinates
uniform int clip_n = 0;
uniform vec4 clip_a[8];
uniform vec4 clip_b[8];

varying vec3 lpos;
varying vec3 lnrm;
varying vec3 wpos;

void vertex() {
	lpos = VERTEX;
	lnrm = NORMAL;
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
#ifdef CLIPS
	for (int k = 0; k < clip_n; k++) {
		vec2 d = lpos.xz - clip_a[k].xy;
		vec2 q = vec2(d.x * clip_b[k].x - d.y * clip_b[k].y, d.x * clip_b[k].y + d.y * clip_b[k].x);
		if (abs(q.x) < clip_a[k].z && abs(q.y) < clip_a[k].w && lpos.y > clip_b[k].z && lpos.y < clip_b[k].w) {
			discard;
		}
	}
#endif
	vec3 c = pow(COLOR.rgb, vec3(2.2));            // vertex colours are sRGB
	float rockable = COLOR.a;
	float slope = 1.0 - clamp(lnrm.y, 0.0, 1.0);
	float fine = texture(noise_tex, lpos.xz * 0.7).r;
	float mid = texture(noise_tex, lpos.xz * 0.06).r;
	// K3: steep walls (gorge, cliffs) - the pattern along the wall instead of from above (no long streaks); Lite: off
	if (detail > 0.5 && slope > 0.3) {
		vec2 t = normalize(vec2(-lnrm.z, lnrm.x) + vec2(0.0001, 0.0));
		vec2 wuv = vec2(dot(lpos.xz, t), lpos.y);
		float ws = smoothstep(0.3, 0.55, slope);
		fine = mix(fine, texture(noise_tex, wuv * 0.7).r, ws);
		mid = mix(mid, texture(noise_tex, wuv * 0.06).r, ws);
	}
	float big = texture(noise_tex, lpos.xz * 0.0045).r;
	// grass: the season
	float green = smoothstep(0.0, 0.05, c.g - max(c.r, c.b) * 0.98);
	c = mix(c, c * grass_tint, green);
	// rock on steep ground: grey gneiss, light limestone bands, rusty iron, dark serpentine (big noise and height)
	vec3 gneis = vec3(0.16, 0.155, 0.145);
	vec3 kalk = vec3(0.32, 0.30, 0.26);
	vec3 rost = vec3(0.24, 0.15, 0.10);
	vec3 serp = vec3(0.09, 0.11, 0.09);
	vec3 rock = mix(gneis, kalk, smoothstep(0.55, 0.7, fract(lpos.y * 0.012 + big * 0.8)));
	rock = mix(rock, rost, smoothstep(0.62, 0.72, big) * 0.8);
	rock = mix(rock, serp, smoothstep(0.38, 0.28, big) * 0.7);
	rock *= 0.75 + 0.5 * mid + 0.25 * (fine - 0.5);
	float rk = smoothstep(0.2, 0.36, slope + 0.08 * (mid - 0.5)) * rockable;
	c = mix(c, rock, rk);
	// snow: above the snow line (lower on the side facing north), never on very steep rock
	float north = clamp(-lnrm.z, 0.0, 1.0);
	float line = snow_line - 90.0 * north + 60.0 * (big - 0.5);
	float sk = max(snow_cover, smoothstep(line, line + 50.0, lpos.y));
	sk = max(sk, snow_amount);
	sk *= 1.0 - smoothstep(0.32, 0.5, slope + 0.1 * (fine - 0.5));
	sk *= smoothstep(0.0, 0.2, rockable + 0.25);   // the lake bed stays (the water lies on it)
	c = mix(c, snow.rgb * (0.9 + 0.1 * fine), clamp(sk, 0.0, 1.0));
	// near the camera a fine pattern
	c *= 1.0 + detail * (0.22 * (fine - 0.5) + 0.18 * (mid - 0.5)) * (1.0 - 0.7 * sk);
	float pd = puddle * smoothstep(0.30, 0.22, texture(noise_tex, lpos.xz * 0.012).r + 0.15 * (mid - 0.5)) * (1.0 - green * 0.6) * (1.0 - smoothstep(0.05, 0.12, slope));
	ALBEDO = mix(clamp(c, 0.0, 1.0) * (1.0 - 0.35 * wet * (1.0 - sk)), vec3(0.05, 0.055, 0.06), pd);
	ROUGHNESS = mix(mix(0.95, 0.4, wet), 0.04, pd) * (1.0 - 0.15 * sk);
	SPECULAR = mix(0.5, 0.9, pd);
}
