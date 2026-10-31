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

varying vec3 wpos;
varying float tip;

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	tip = clamp(VERTEX.y / 0.5, 0.0, 1.0);
	float a = (0.15 + wind / 45.0) / stiff;
	float s = sin(TIME * (1.6 + wind / 30.0) + wp.x * 0.45 + wp.z * 0.3) + 0.35 * sin(TIME * 4.1 + wp.x * 2.0);
	vec3 bend = vec3(s * 0.09, 0.0, s * 0.04) * a * tip * tip;
	VERTEX += (inverse(MODEL_MATRIX) * vec4(bend, 0.0)).xyz;
	wpos = wp;
	NORMAL = vec3(0.0, 1.0, 0.0);          // lit like the ground below (no dark back sides)
}

void fragment() {
	float n = texture(noise_tex, wpos.xz * 0.11).r;
	vec3 c = mix(COLOR.rgb, tint.rgb * 1.15, tint_amt) * (0.8 + 0.45 * tip) * (0.85 + 0.3 * n);
	c = mix(c, vec3(0.92, 0.93, 0.95), snow_amount * 0.7 * tip);
	c *= 1.0 - cloud_amt * smoothstep(0.52, 0.68, texture(noise_tex, (wpos.xz + cloud_off) * 0.0035).r);
	ALBEDO = c;
	ROUGHNESS = 0.9;
}
