// «Flora und Fauna» Paket 1 (scripts/baeume.gd): bark of the new branch frames (all trees of a 32 m cell in one mesh).
// COLOR.a = (species + 0.5) / 16: colour bark_cols, pattern bark_p (0 scales, 1 smooth, 2 pores, 3 pine, 4 birch, 5 furrows). UV.x = around, UV.y = along (m), UV2 = (wind weight, radius m).
// CUSTOM0 = (centre of the crown xyz, height in the crown part + 1): the same sway as the leaf cards (baum_karten.gdshader).
// Beyond near_d (per tree, from the centre of the crown) the tree is drawn as a far picture: the bark collapses.
shader_type spatial;

uniform sampler2D noise_tex;
uniform float wind = 0.0;
uniform float gust_amt = 0.0;
uniform vec2 dir = vec2(0.8, 0.6);
uniform float cloud_amt = 0.0;
uniform vec2 cloud_off = vec2(0.0);
uniform float near_d = 45.0;
uniform float fine = 0.0;          // Hoch: bumpier bark
uniform vec4 bark_cols[16] : source_color;  // per species (baeume.gd RINDE, RINDE_ARTEN)
uniform vec4 bark_p[16];                     // pattern, scale x, scale y, relief (baeume.gd RINDE_P)

varying vec3 wpos;
varying float v_pat;
varying float v_rad;

void vertex() {
	vec3 cw = CUSTOM0.xyz;
	float up = clamp(CUSTOM0.w, 0.0, 2.0);
	float wgt = UV2.x;
	v_rad = UV2.y;
	v_pat = COLOR.a;
	if (length(cw - CAMERA_POSITION_WORLD) > near_d) {
		VERTEX = vec3(0.0);
	} else {
		float a = wind / 60.0;
		float s = sin(TIME * (1.2 + a) + cw.x * 0.37 + cw.z * 0.21);
		float f = sin(TIME * 4.3 + cw.z + (CUSTOM0.w - 1.0) * 3.0) * 0.25;
		vec3 sway = vec3((s + f) * a * 0.35 * up * (1.0 - 0.5 * gust_amt), 0.0, (s * 0.4) * a * 0.2 * up * (1.0 - 0.5 * gust_amt));
		if (gust_amt > 0.0) {
			float g = smoothstep(0.3, 0.8, texture(noise_tex, (cw.xz - dir * TIME * (0.6 + wind * 0.03)) * 0.02).r);
			float lean = (0.3 + 1.1 * g) * a + sin(TIME * (1.6 + a) + cw.x * 0.5) * 0.25 * a * g;
			sway += vec3(dir.x, 0.0, dir.y) * lean * 0.3 * up * gust_amt;
		}
		VERTEX += inverse(mat3(MODEL_MATRIX)) * (sway * wgt);
	}
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	// coordinates on the bark: around in m (radius * angle), along in m
	vec2 bc = vec2(UV.x * 6.2832 * max(v_rad, 0.01), UV.y);
	float n1 = texture(noise_tex, bc * vec2(1.6, 0.45) + vec2(wpos.x * 0.07, 0.0)).r;
	float n2 = texture(noise_tex, bc * vec2(5.0, 2.2) + 0.37).r;
	float h;
	int sid = clamp(int(v_pat * 16.0), 0, 15);
	vec3 col = bark_cols[sid].rgb;
	vec4 bpar = bark_p[sid];
	int pid = int(bpar.x + 0.5);
	float bump = bpar.w;
	if (pid == 0) {                           // small scales / plates (spruce, maple, fruit tree, stone pine)
		float sc = texture(noise_tex, bc * bpar.yz).r;
		h = smoothstep(0.35, 0.65, sc) * 0.7 + n1 * 0.3;
		col *= mix(0.62, 1.12, h) * mix(vec3(1.0), vec3(1.08, 0.95, 0.88), n2);
	} else if (pid == 1) {                    // smooth (beech, fir): faint rings, lighter spots of lichen
		h = n1 * 0.4 + n2 * 0.2;
		col *= 0.85 + 0.3 * n1;
		float lic = smoothstep(0.62, 0.72, texture(noise_tex, bc * vec2(0.9, 0.7) + 0.71).r);
		col = mix(col, vec3(0.6, 0.64, 0.52), lic * 0.45);
		col *= 1.0 - 0.12 * smoothstep(0.45, 0.5, fract(UV.y * 1.3 + n1 * 0.4)) * (1.0 - smoothstep(0.5, 0.56, fract(UV.y * 1.3 + n1 * 0.4)));
	} else if (pid == 3) {                    // pine: thick grey-brown plates below, thin orange bark up in the crown
		float pl = texture(noise_tex, bc * bpar.yz).r;
		h = smoothstep(0.3, 0.7, pl);
		col *= mix(0.45, 1.1, h);
		vec3 orange = vec3(0.72, 0.42, 0.24) * (0.85 + 0.3 * n2);
		col = mix(col, orange * orange, smoothstep(0.16, 0.09, v_rad));
	} else if (pid == 4) {                    // birch: white, black dashes across, dark and cracked at the foot, thin twigs brown
		h = n1 * 0.3;
		float dash = smoothstep(0.7, 0.76, texture(noise_tex, bc * vec2(2.5, 9.0) + 0.13).r);
		col *= 0.9 + 0.15 * n2;
		col = mix(col, vec3(0.03), dash * 0.85);
		col = mix(col, vec3(0.16, 0.15, 0.14) * (0.6 + n1), 0.7 * smoothstep(0.6, 0.15, UV.y + n1 * 0.3) * smoothstep(0.08, 0.12, v_rad) * step(n2, 0.7));
		col = mix(col, vec3(0.09, 0.06, 0.05), smoothstep(0.035, 0.02, v_rad));
	} else if (pid == 5) {                    // long furrows (oak, larch, ash net, elder cork)
		float fu = texture(noise_tex, bc * bpar.yz).r;
		h = smoothstep(0.25, 0.75, fu);
		col *= mix(0.4, 1.15, h) * (0.9 + 0.2 * n2);
	} else {                                  // smooth with small light cork pores across (hazel, alpine rose, privet)
		h = n1 * 0.5;
		col *= 0.85 + 0.3 * n1;
		float pore = smoothstep(0.78, 0.84, texture(noise_tex, bc * bpar.yz + 0.21).r);
		col = mix(col, vec3(0.62, 0.56, 0.46), pore * 0.6);
	}
	// bumps from h (screen-space derivative, no tangents needed)
	vec3 sx = dFdx(VERTEX);
	vec3 sy = dFdy(VERTEX);
	float hx = dFdx(h);
	float hy = dFdy(h);
	vec3 r1 = cross(sy, NORMAL);
	vec3 r2 = cross(NORMAL, sx);
	float det = dot(sx, r1);
	vec3 grad = sign(det) * (hx * r1 + hy * r2);
	NORMAL = normalize(abs(det) * NORMAL - grad * (0.25 + 0.35 * fine) * bump);
	col *= 1.0 - cloud_amt * smoothstep(0.52, 0.68, texture(noise_tex, (wpos.xz + cloud_off) * 0.0035).r);
	ALBEDO = col;
	ROUGHNESS = 0.92;
	SPECULAR = 0.2;
}
