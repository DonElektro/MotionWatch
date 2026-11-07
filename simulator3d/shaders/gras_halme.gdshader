// 3D-4.x (vegetation.gd): grass clumps and flowers as MultiMesh. COLOR = colour of the instance, VERTEX.y = height in the
// clump (the tip sways in the wind, the root stays). Snow covers them partly, cloud shadows like the ground.
shader_type spatial;
render_mode cull_disabled;

uniform float wind = 0.0;               // km/h
uniform float stiff = 1.0;              // flowers a bit stiffer than grass
uniform vec4 tint : source_color = vec4(0.22, 0.42, 0.16, 1.0);   // the colour of the meadow now (season, colors.gd)
uniform float tint_amt = 0.5;           // grass 0.5 (follows the season), flowers 0
uniform float snow_amount = 0.0;
uniform float cloud_amt = 0.0;
uniform vec2 cloud_off = vec2(0.0);
uniform sampler2D noise_tex : repeat_enable;
// «Flora und Fauna» Phase 1 (scripts/flora.gd): neu = colour patches in two sizes (lush / dry / yellowish), dry tips, darker
// at the root, every clump its own shade; fade_far > 0: the clumps thin out softly over the last 14 m (they shrink away
// one by one, no alpha test) instead of all ending at one line. neu = 0: as before.
uniform float neu = 0.0;
uniform float fade_far = 0.0;

varying vec3 wpos;
varying float tip;
varying float cl_rand;
varying float cam_d;

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	tip = clamp(VERTEX.y / 0.5, 0.0, 1.0);
	float a = (0.15 + wind / 45.0) / stiff;
	float s = sin(TIME * (1.6 + wind / 30.0) + wp.x * 0.45 + wp.z * 0.3) + 0.35 * sin(TIME * 4.1 + wp.x * 2.0);
	vec3 bend = vec3(s * 0.09, 0.0, s * 0.04) * a * tip * tip;
	VERTEX += (inverse(MODEL_MATRIX) * vec4(bend, 0.0)).xyz;
	wpos = wp;
	vec3 o = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;            // the clump (MultiMesh instance)
	cl_rand = fract(sin(dot(o.xz, vec2(12.9898, 78.233))) * 43758.5453);
	cam_d = length(o - CAMERA_POSITION_WORLD);
	if (neu > 0.0 && fade_far > 0.0) {                                   // soft end: clumps shrink away one by one
		float th = smoothstep(fade_far - 14.0, fade_far, cam_d);
		VERTEX *= smoothstep(th - 0.15, th + 0.05, cl_rand * 0.95 + 0.05);
	}
	NORMAL = vec3(0.0, 1.0, 0.0);          // lit like the ground below (no dark back sides)
}

void fragment() {
	float n = texture(noise_tex, wpos.xz * 0.11).r;
	vec3 c = mix(COLOR.rgb, tint.rgb * 1.15, tint_amt) * (0.8 + 0.45 * tip) * (0.85 + 0.3 * n);
	if (neu > 0.0) {
		float big = texture(noise_tex, wpos.xz * 0.018).r;               // patches of ~20 m: lush or drier meadow
		float mid = texture(noise_tex, wpos.xz * 0.09 + 3.1).r;          // ~4 m
		vec3 lush = vec3(0.78, 1.0, 0.72);
		vec3 dry = vec3(1.22, 1.08, 0.62);
		c *= mix(lush, dry, smoothstep(0.35, 0.75, big * 0.65 + mid * 0.35));
		c = mix(c, vec3(dot(c, vec3(0.3, 0.55, 0.15))) * vec3(1.0, 1.02, 0.78), 0.35);  // less garish: meadow green is greyish
		c *= 0.86;
		c *= 0.82 + 0.36 * cl_rand;                                      // every clump its own shade
		c = mix(c, c * vec3(1.35, 1.18, 0.7), smoothstep(0.65, 1.0, tip) * (0.35 + 0.4 * mid));   // dry, light tips
		c *= mix(0.55, 1.0, smoothstep(0.0, 0.35, tip));                 // dark at the root (shade in the sward)
	}
	c = mix(c, vec3(0.92, 0.93, 0.95), snow_amount * 0.7 * tip);
	c *= 1.0 - cloud_amt * smoothstep(0.52, 0.68, texture(noise_tex, (wpos.xz + cloud_off) * 0.0035).r);
	ALBEDO = c;
	NORMAL = normalize((VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz);   // lit like the ground, also the back side (cull_disabled flips it)
	ROUGHNESS = 0.9;
}
