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
uniform float rshutter = 0.0;       // rolling shutter: the rows are read one after the other - turning fast skews the picture
uniform float shot = 0.0;           // sensor noise that depends on the light: dark parts grainy, bright parts clean
uniform float bloom = 0.0;          // near things in the infrared light blow out and glow over their edges
uniform float haze = 0.0;           // fog / rain / snow in the camera's own light: backscatter veil in the cone, far parts fade
uniform float flakes = 0.0;         // drops / flakes right in front of the lens lit by the camera's light (bright streaks / dots)
uniform float flake_kind = 0.0;     // 0 rain (short slanted streaks), 1 snow (soft dots)
uniform vec2 cone_c = vec2(0.5, 0.56);
uniform float veil_k = 1.0;         // the veil and the flakes are lit by the same light: they follow the exposure
// 3D-4.x «Kamera-Physik» (camphys.gd): the sensor noise of the IMX708 from its gain, hot pixels, glow of bright lights
uniform float sn_on = 0.0;          // 1: this noise instead of «shot» / «cnoise»
uniform float sn_read = 0.0;        // read noise × gain (same in dark and bright parts)
uniform float sn_shot = 0.0;        // photon noise: × sqrt(brightness)
uniform float sn_chroma = 0.0;      // colour noise the denoise of the ISP leaves: blotches of ~2 px
uniform float sn_blob = 1.0;        // 0 (Lite): colour noise per pixel instead of blotches (cheaper)
uniform float hotpx = 0.0;          // 0..1 hot pixels (long exposure, high gain)
uniform float ir_tint = 0.0;        // infrared picture: grey with a magenta touch (850 nm through the colour filters)
uniform float flare = 0.0;          // glow round bright lights at night (headlights, torch) - the more gain, the more
uniform float vig = 0.0;            // lens shading left after the ISP's correction (more in the light of the infrared LED)

float h21(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }

void fragment() {
	vec2 suv = SCREEN_UV;
	vec2 uv = suv;
	if (distort > 0.0) {
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
		// 3D-4.x (camphys): also dark, dull green (grass in the shade) counts - relative to its brightness; leaves reflect
		// 40-50 % in near infrared (vs ~10 % green light), so vegetation gets lighter and washed out
		float rg = clamp((c.g - max(c.r, c.b)) / max(c.g, 0.04) * 2.5, 0.0, 1.0);
		float lv = dot(c, vec3(0.299, 0.587, 0.114));
		vec3 nc = c + vec3(green * 0.9, -green * 0.55, green * 0.75);
		nc = mix(nc, vec3(lv * 1.3 + 0.03) * vec3(1.08, 0.9, 1.04), rg * 0.6);
		nc *= vec3(1.08, 0.93, 1.06);
		c = mix(c, nc, noir);
	}
	if (ir_tint > 0.0) {
		float li = dot(c, vec3(0.299, 0.587, 0.114));
		c = mix(c, li * vec3(1.06, 0.95, 1.05), ir_tint);
	}
	if (vig > 0.0) {
		vec2 qv = (suv - 0.5) * vec2(res.x / res.y, 1.0);
		float rv = dot(qv, qv) / (0.25 * (res.x * res.x / (res.y * res.y) + 1.0));   // 1 in the corners
		c *= 1.0 - vig * (0.6 * rv + 0.4 * rv * rv);
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
	if (flare > 0.0) {
		// a wide soft halo round lights that blow out the sensor (two rings of 8 samples, 14 and 34 px)
		float hl = 0.0;
		for (int k = 0; k < 8; k++) {
			float an = float(k) * 0.7854 + 0.3;
			vec2 dv = vec2(cos(an), sin(an)) / res;
			hl += max(0.0, dot(texture(screen_tex, uv + dv * 14.0).rgb, vec3(0.333)) - 0.9);
			hl += 0.6 * max(0.0, dot(texture(screen_tex, uv + dv * 34.0).rgb, vec3(0.333)) - 0.92);
		}
		c += vec3(1.0, 0.97, 0.92) * hl / 8.0 * flare * 3.0;
	}
	if (sn_on > 0.5) {
		vec2 px3 = floor(uv * res);
		float lum3 = clamp(dot(c, vec3(0.299, 0.587, 0.114)), 0.0, 1.0);
		float sig = sqrt(sn_shot * sn_shot * lum3 + sn_read * sn_read);
		// two uniform hashes ≈ a triangle distribution (close enough to Gaussian for the eye and for MoveEye)
		float nl = (h21(px3 + seed * 1.37 + 3.3) + h21(px3.yx + seed * 0.71 + 9.1) - 1.0) * 2.45;
		c += vec3(nl * sig);
		if (sn_chroma > 0.0) {
			vec3 cn;
			if (sn_blob > 0.5) {
				vec2 q3 = uv * res / 2.2 + seed * 0.53;
				vec2 i3 = floor(q3);
				vec2 f3 = fract(q3);
				f3 = f3 * f3 * (3.0 - 2.0 * f3);
				vec3 a00 = vec3(h21(i3), h21(i3 + 17.1), h21(i3 + 41.7));
				vec3 a10 = vec3(h21(i3 + vec2(1.0, 0.0)), h21(i3 + vec2(18.1, 17.1)), h21(i3 + vec2(42.7, 41.7)));
				vec3 a01 = vec3(h21(i3 + vec2(0.0, 1.0)), h21(i3 + vec2(17.1, 18.1)), h21(i3 + vec2(41.7, 42.7)));
				vec3 a11 = vec3(h21(i3 + 1.0), h21(i3 + 18.1), h21(i3 + 42.7));
				cn = mix(mix(a00, a10, f3.x), mix(a01, a11, f3.x), f3.y) - 0.5;
				cn *= 1.8;
			} else {
				cn = vec3(h21(px3 + seed), h21(px3 + seed + 17.1), h21(px3 + seed + 41.7)) - 0.5;
			}
			c += (cn - dot(cn, vec3(0.333))) * sn_chroma * sig * 4.0;
		}
		if (hotpx > 0.0) {
			// fixed places (the same every picture): a few pixels with a high dark current, one colour of the Bayer pattern
			float hp = h21(px3 * 1.013 + 77.0);
			if (hp < 0.00005) {
				float ch = h21(px3 + 5.0);
				vec3 hc = ch < 0.33 ? vec3(1.0, 0.25, 0.2) : (ch < 0.66 ? vec3(0.3, 1.0, 0.3) : vec3(0.25, 0.35, 1.0));
				c += hc * hotpx * (0.4 + 0.6 * h21(px3 + 9.0));
			}
		}
	}
	ALBEDO = clamp(c, 0.0, 1.0);
	ALPHA = 1.0;
}
