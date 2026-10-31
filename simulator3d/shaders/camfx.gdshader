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
// 3D-4.4 (simreal.gd): the lens and sensor of the Camera Module 3
uniform float distort = 0.0;        // barrel distortion (0.05 normal lens, ~0.16 wide lens): straight lines bend at the edges
// P9 (weitwinkel.gd): the equidistant fisheye of the Camera Module 3 Wide - the angle from the middle grows linearly with the
// distance in the picture (model of the case report v5.2). The camera renders a wider straight picture (tan fe_tan at its
// edges), here every pixel fetches the ray of its angle. fe_vig: the dark corners the ISP leaves.
uniform float fe_on = 0.0;
uniform vec2 fe_half = vec2(0.8901, 0.5847);   // half angles of the picture (rad): 51° to the side edge, 33.5° to the top
uniform vec2 fe_tan = vec2(1.796, 1.010);      // tan of the half width / height of the rendered straight picture
uniform float fe_vig = 0.0;                    // 0..1 darker in the corners (by the angle from the middle)
uniform float rshutter = 0.0;       // rolling shutter: the rows are read one after the other - turning fast skews the picture
uniform float shot = 0.0;           // sensor noise that depends on the light: dark parts grainy, bright parts clean
uniform float bloom = 0.0;          // near things in the infrared light blow out and glow over their edges
uniform float haze = 0.0;           // fog / rain / snow in the camera's own light: backscatter veil in the cone, far parts fade
uniform float flakes = 0.0;         // drops / flakes right in front of the lens lit by the camera's light (bright streaks / dots)
uniform float flake_kind = 0.0;     // 0 rain (short slanted streaks), 1 snow (soft dots)
uniform vec2 cone_c = vec2(0.5, 0.56);
uniform float veil_k = 1.0;         // the veil and the flakes are lit by the same light: they follow the exposure

float h21(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }

void fragment() {
	vec2 suv = SCREEN_UV;
	vec2 uv = suv;
	float fe_k = 1.0;
	if (fe_on > 0.5) {
		vec2 an = (suv - 0.5) * 2.0 * fe_half;            // the angles of this pixel along x / y
		float th = length(an);
		vec2 dir = th > 0.00001 ? an / th : vec2(0.0);
		uv = dir * tan(min(th, 1.45)) / fe_tan * 0.5 + 0.5;
		float rr = th / length(fe_half);                   // 1 in the corners
		fe_k = 1.0 - fe_vig * rr * rr;
	} else if (distort > 0.0) {
		float asp = res.x / res.y;
		vec2 q = (uv - 0.5) * vec2(asp, 1.0);
		float r2 = dot(q, q) / (0.25 * (asp * asp + 1.0));   // 1 in the corners: the corners stay, the middle grows a little
		q *= (1.0 + distort * r2) / (1.0 + distort);
		uv = q / vec2(asp, 1.0) + 0.5;
	}
	if (rshutter != 0.0) {
		uv.x += rshutter * (uv.y - 0.5);
	}
	uv = clamp(uv, vec2(0.001), vec2(0.999));
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
	c *= fe_k;                                             // P9: vignetting of the wide lens (before the last picture is mixed in)
	if (trail > 0.0) {
		// 3D-4.1: the last picture is the finished one (after the lens: gain, grain) - never let it be brighter than now,
		// otherwise it adds up from picture to picture (the infrared picture at night turned completely white)
		vec3 pv = texture(prev_tex, suv).rgb;
		float lc = dot(c, vec3(0.299, 0.587, 0.114)), lp = dot(pv, vec3(0.299, 0.587, 0.114));
		// 3D-4.4: really never brighter (before: down to half only - the last picture is after the night curve of the
		// environment, so it was still up to 2x brighter and the infrared picture ran up to white again)
		pv *= min(1.0, (lc + 0.02) / (lp + 0.02));
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
	if (haze > 0.0 || flakes > 0.0) {
		vec2 dq = (uv - cone_c) * vec2(res.x / res.y, 1.0);
		float cone = exp(-dot(dq, dq) * 2.6);                 // the LED cone: the veil is brightest in its middle
		if (haze > 0.0) {
			float lum = dot(c, vec3(0.299, 0.587, 0.114));
			c *= 1.0 - haze * (1.0 - smoothstep(0.08, 0.7, lum));         // far (dim) parts vanish in the fog, near stays
			c = mix(c, vec3(0.5 * veil_k), haze * 0.1);                    // less contrast
			c += vec3(haze * (0.26 * cone + 0.03) * veil_k);               // light scattered back from the droplets
		}
		if (flakes > 0.0) {
			vec2 cell = flake_kind > 0.5 ? vec2(7.0, 7.0) : vec2(3.0, 18.0);
			vec2 g = (uv * res + vec2((1.0 - uv.y) * res.y * 0.18 * (1.0 - flake_kind), 0.0)) / cell;
			vec2 id = floor(g);
			vec2 f = fract(g) - 0.5;
			if (h21(id + seed * 0.37) < flakes * 0.016 * (0.3 + cone)) {
				float a = flake_kind > 0.5 ? smoothstep(0.5, 0.1, length(f)) : smoothstep(0.5, 0.1, abs(f.x)) * smoothstep(0.5, 0.3, abs(f.y));
				c += vec3(a * (0.35 + 0.65 * h21(id + 1.7)) * (0.15 + 0.95 * cone) * clamp(veil_k * 1.5, 0.3, 1.0));
			}
		}
	}
	if (bloom > 0.0) {
		vec2 o = vec2(4.0) / res;
		float hs = 0.0;
		for (int k = 0; k < 6; k++) {
			float an = float(k) * 1.0472;
			vec3 sb = texture(screen_tex, uv + vec2(cos(an), sin(an)) * o).rgb;
			vec3 sb2 = texture(screen_tex, uv + vec2(cos(an + 0.52), sin(an + 0.52)) * o * 2.6).rgb;
			hs += max(0.0, dot(sb, vec3(0.333)) - 0.78) + 0.6 * max(0.0, dot(sb2, vec3(0.333)) - 0.8);
		}
		c += vec3(hs / 6.0) * bloom * 2.2;
	}
	if (shot > 0.0) {
		vec2 px2 = floor(uv * res) + seed * 1.37;
		float n2 = h21(px2 + 3.3) + h21(px2.yx + 9.1) - 1.0;
		float lum = dot(c, vec3(0.299, 0.587, 0.114));
		c += vec3(n2 * shot * (0.3 + 0.7 * (1.0 - lum)) * (0.35 + sqrt(max(lum, 0.0))));
	}
	ALBEDO = clamp(c, 0.0, 1.0);
	ALPHA = 1.0;
}
