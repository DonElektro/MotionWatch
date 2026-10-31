// Sky of the 3D simulator (3D-3.33): colour gradient, sun with halo, moon, stars at night and moving clouds.
// Runs in the Compatibility (OpenGL) renderer and in Forward+ (Vulkan).
shader_type sky;

uniform vec3 top_color : source_color = vec3(0.25, 0.45, 0.8);
uniform vec3 horizon_color : source_color = vec3(0.7, 0.78, 0.88);
uniform vec3 ground_color : source_color = vec3(0.1, 0.12, 0.08);
uniform float energy = 1.0;
uniform float cloud_cover = 0.3;      // 0 = clear … 1 = overcast
uniform vec3 cloud_light : source_color = vec3(1.0);
uniform vec3 cloud_shadow : source_color = vec3(0.55, 0.6, 0.68);
uniform float night = 0.0;            // 0 = day … 1 = night (stars)
uniform vec2 wind = vec2(0.004, 0.0015);
uniform float moon_phase = 0.5;       // 3D-3.98: 0 = new moon, 0.5 = full moon, 1 = new moon again
uniform float detail = 1.0;           // 0 = no clouds / stars (simple graphics)

float hash3(vec3 p) {
	p = fract(p * 0.3183099 + vec3(0.71, 0.113, 0.419));
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float hash2(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash2(i), b = hash2(i + vec2(1.0, 0.0)), c = hash2(i + vec2(0.0, 1.0)), d = hash2(i + vec2(1.0, 1.0));
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
	float s = 0.0, a = 0.5;
	for (int i = 0; i < 5; i++) {
		s += a * vnoise(p);
		p = p * 2.03 + vec2(1.7, 9.2);
		a *= 0.5;
	}
	return s;
}

// F2 «echte Inhalte» (inhalte.gd, 31.10.2026): Foto-Himmel (HDRI, CC0) am Tag (a) und in der Dämmerung (b).
// hdri_mix_* = 0: genau wie bisher. Der Himmel wird so gedreht, dass die Sonne des Fotos dort steht, wo die Sonne
// der Simulation steht; zu helle Stellen (die Sonne des Fotos) werden gekappt – die Sonne zeichnet der Shader selbst.
uniform sampler2D hdri_a : filter_linear, repeat_enable, hint_default_black;
uniform sampler2D hdri_b : filter_linear, repeat_enable, hint_default_black;
uniform float hdri_mix_a = 0.0;
uniform float hdri_mix_b = 0.0;
uniform float hdri_rot_a = 0.0;       // Drehung (Anteil einer Runde)
uniform float hdri_rot_b = 0.0;
uniform float hdri_gain_a = 1.0;      // Helligkeit angleichen
uniform float hdri_gain_b = 1.0;
uniform float hdri_cap_a = 3.0;       // höchstens so hell (nach gain)
uniform float hdri_cap_b = 3.0;

vec3 hdri_at(sampler2D t, vec3 d, float rot, float gain, float cap) {
	float u = atan(d.x, -d.z) / 6.2831853 + 0.5;
	float v = acos(clamp(d.y, -1.0, 1.0)) / 3.1415927;
	vec3 c = textureLod(t, vec2(fract(u + rot), v), 0.0).rgb * gain;
	return min(c, vec3(cap));
}

void sky() {
	vec3 d = normalize(EYEDIR);
	float h = d.y;
	vec3 col;
	if (h >= 0.0) {
		col = mix(horizon_color, top_color, pow(clamp(h, 0.0, 1.0), 0.45));
	} else {
		col = mix(horizon_color, ground_color, clamp(-h * 5.0, 0.0, 1.0));
	}
	float hs = 0.0;                                          // how much of the photo sky
	float hw = hdri_mix_a + hdri_mix_b;
	if (hw > 0.001 && h > -0.06) {
		vec3 hc = vec3(0.0);
		if (hdri_mix_a > 0.001) {
			hc += hdri_at(hdri_a, d, hdri_rot_a, hdri_gain_a, hdri_cap_a) * hdri_mix_a;
		}
		if (hdri_mix_b > 0.001) {
			hc += hdri_at(hdri_b, d, hdri_rot_b, hdri_gain_b, hdri_cap_b) * hdri_mix_b;
		}
		hc /= max(hw, 0.001);
		hs = min(hw, 1.0) * smoothstep(-0.06, 0.0, h);
		col = mix(col, hc, hs);
	}
	float sun_vis = 0.0;
	vec3 sun_col = vec3(0.0);
	if (LIGHT0_ENABLED) {
		float sd = dot(d, LIGHT0_DIRECTION);
		sun_col = LIGHT0_COLOR;
		sun_vis = clamp(LIGHT0_ENERGY, 0.0, 2.0);
		float disk = smoothstep(0.99955, 0.99975, sd);
		float halo = pow(max(sd, 0.0), 300.0) * 0.8 + pow(max(sd, 0.0), 24.0) * 0.18;
		float hz = pow(max(sd, 0.0), 6.0) * 0.25 * (1.0 - clamp(h * 3.0, 0.0, 1.0));     // warm glow round the sun near the horizon
		col += sun_col * (disk * 12.0 + halo + hz) * sun_vis * (1.0 - cloud_cover * 0.85);
	}
	col *= energy;
	col += vec3(0.010, 0.016, 0.034) * night * (0.4 + 0.6 * clamp(h * 2.0, 0.0, 1.0)) * (1.0 - cloud_cover * 0.5);   // the night sky is deep blue, not black
	if (LIGHT1_ENABLED) {                                   // the moon (not darkened with the sky)
		float md = dot(d, LIGHT1_DIRECTION);
		float mdisk = smoothstep(0.99965, 0.9998, md);
		vec3 mr = normalize(cross(LIGHT1_DIRECTION, vec3(0.0, 1.0, 0.0)) + vec3(1e-4));
		vec3 mu = cross(mr, LIGHT1_DIRECTION);
		vec3 off = d - md * LIGHT1_DIRECTION;
		float mx = dot(off, mr) / 0.0195, my = dot(off, mu) / 0.0195;
		float lit = 0.5 - 0.5 * cos(moon_phase * 6.2832);              // lit part of the disk
		float edge = (1.0 - 2.0 * lit) * sqrt(max(0.0, 1.0 - my * my));
		float sx = moon_phase < 0.5 ? mx : -mx;                          // waxing: lit on the right
		mdisk *= mix(0.04, 1.0, smoothstep(edge - 0.08, edge + 0.08, sx));
		col += vec3(0.85, 0.88, 0.95) * mdisk * 1.6 * night * (1.0 - cloud_cover) + vec3(0.4, 0.45, 0.6) * pow(max(md, 0.0), 120.0) * 0.12 * night;
	}
	if (detail > 0.5 && h > 0.0) {
		// stars: small dots that twinkle a little, only at night and where there are no clouds
		vec3 p = d * 220.0;
		vec3 cell = floor(p);
		float r = hash3(cell);
		float star = step(0.993, r) * smoothstep(0.5, 0.0, length(fract(p) - 0.5)) * (0.35 + 2.6 * pow((r - 0.993) / 0.007, 3.0));
		// (no twinkling: a camera does not see it, and it would look like movement)
		col += vec3(0.9, 0.93, 1.0) * star * night * (1.0 - cloud_cover) * smoothstep(0.02, 0.2, h) * 2.2;
		// clouds: noise on a high plane, moving with the wind
		vec2 uv = d.xz / (h + 0.06) * 0.55 + wind * TIME;
		float n = fbm(uv * 1.3);
		float cov = clamp(cloud_cover, 0.0, 1.0);
		float c = smoothstep(0.78 - cov * 0.55, 1.02 - cov * 0.45, n);
		float shade = fbm(uv * 1.3 + vec2(0.08, 0.05));      // lighter on the side of the sun
		vec3 cc = mix(cloud_shadow, cloud_light, clamp(0.55 + (n - shade) * 3.0, 0.0, 1.0));
		cc += sun_col * sun_vis * 0.25 * pow(max(dot(d, LIGHT0_DIRECTION), 0.0), 8.0);
		float fade = smoothstep(0.0, 0.12, h);
		col = mix(col, cc * energy, c * fade * (0.55 + 0.45 * cov) * (1.0 - hs * 0.9));
	}
	COLOR = col;
}
