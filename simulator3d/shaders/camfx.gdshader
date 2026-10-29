// 3D-3.94: what a real camera does to the picture (between the exposure quad and the lens quad, so it works on the exposed
// picture and the grain of the lens comes on top): motion blur from the exposure time (a share of the last picture stays,
// longer at night) and when the head turns, a little softness, the colours of the sensor (saturation, contrast, tint - the
// «Echt-Abgleich» sets them from real pictures of MoveEye) and the pink cast of the NoIR camera by day (no infrared filter).
shader_type spatial;
render_mode unshaded, blend_mix, depth_test_disabled, depth_draw_never, cull_disabled, shadows_disabled;

uniform sampler2D screen_tex : hint_screen_texture, filter_linear_mipmap;
uniform sampler2D prev_tex : filter_linear;
uniform float trail = 0.0;          // 0..0.6 share of the last picture (exposure time / time between pictures)
uniform vec2 pan_blur = vec2(0.0);  // blur along the turning of the head (uv over the exposure time)
uniform float soft = 0.0;           // 0..2 px softness of the lens
uniform vec2 res = vec2(960.0, 540.0);
uniform float sat = 1.0;
uniform float con = 1.0;
uniform vec3 tint = vec3(1.0);
uniform float noir = 0.0;           // 0..1 pink cast by day (NoIR camera)
uniform float cnoise = 0.0;         // 3D-3.97: colour grain in the dark (each pixel a little red / green / blue, new every picture)
uniform float seed = 0.0;

float h21(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }

void fragment() {
	vec2 uv = SCREEN_UV;
	vec3 c;
	if (length(pan_blur) > 0.0008) {
		c = vec3(0.0);
		for (int k = -3; k <= 3; k++) {
			c += texture(screen_tex, uv + pan_blur * float(k) / 6.0).rgb;
		}
		c /= 7.0;
	} else if (soft > 0.05) {
		vec2 o = vec2(soft) / res;
		c = texture(screen_tex, uv).rgb * 0.4 + (texture(screen_tex, uv + vec2(o.x, 0.0)).rgb + texture(screen_tex, uv - vec2(o.x, 0.0)).rgb
			+ texture(screen_tex, uv + vec2(0.0, o.y)).rgb + texture(screen_tex, uv - vec2(0.0, o.y)).rgb) * 0.15;
	} else {
		c = texture(screen_tex, uv).rgb;
	}
	if (trail > 0.0) {
		// 3D-4.1: the last picture is the finished one (after the lens: gain, grain) - never let it be brighter than now,
		// otherwise it adds up from picture to picture (the infrared picture at night turned completely white)
		vec3 pv = texture(prev_tex, uv).rgb;
		float lc = dot(c, vec3(0.299, 0.587, 0.114)), lp = dot(pv, vec3(0.299, 0.587, 0.114));
		pv *= clamp((lc + 0.04) / (lp + 0.04), 0.5, 1.0);
		c = mix(c, pv, trail);
	}
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	c = mix(vec3(l), c, sat);
	c = (c - 0.45) * con + 0.45;
	c *= tint;
	if (noir > 0.0) {
		// without an infrared filter: plants reflect infrared - green turns grey-pink, the whole picture gets a magenta cast
		float green = clamp(c.g - max(c.r, c.b), 0.0, 1.0);
		vec3 nc = c + vec3(green * 0.9, -green * 0.55, green * 0.75);
		nc *= vec3(1.08, 0.93, 1.06);
		c = mix(c, nc, noir);
	}
	if (cnoise > 0.0) {
		vec2 px = floor(uv * res) + seed;
		vec3 n = vec3(h21(px), h21(px + 17.1), h21(px + 41.7)) - 0.5;
		c += (n - dot(n, vec3(0.333))) * cnoise;              // only the colour moves, hardly the brightness
	}
	ALBEDO = clamp(c, 0.0, 1.0);
	ALPHA = 1.0;
}
