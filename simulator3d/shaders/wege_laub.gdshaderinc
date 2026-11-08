// «Wege und Strassen» Schritt 2: Herbstlaub auf Wegen und Strassen (wanderweg / feldweg / strasse .gdshader). dens 0 … 1 (wie
// dicht, schon mit der Jahreszeit «laub» malgenommen), near 1 = nah (einzelne Blätter), lwet: nasses Laub ist dunkler.
float laub_hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

vec3 laub_mix(vec3 c, vec2 wxz, float dens, float near, float lwet, sampler2D nz) {
	if (dens <= 0.0) {
		return c;
	}
	vec2 lc = floor(wxz * 11.0);
	vec2 lf = fract(wxz * 11.0) - 0.5;
	float ang = laub_hash(lc + 3.3) * 6.283;
	vec2 lr = mat2(vec2(cos(ang), sin(ang)), vec2(-sin(ang), cos(ang))) * lf;
	float leaf = 1.0 - smoothstep(0.26, 0.32, length(lr * vec2(1.0, 1.9)));
	leaf *= step(1.0 - dens * 0.9, laub_hash(lc + 7.7));
	vec3 lcol = mix(vec3(0.62, 0.32, 0.08), vec3(0.75, 0.55, 0.12), laub_hash(lc + 1.1)) * mix(1.0, 0.5, laub_hash(lc + 9.9));
	lcol = mix(lcol, vec3(0.3, 0.2, 0.12), lwet * 0.5);
	float mush = dens * smoothstep(0.35, 0.8, texture(nz, wxz * 0.9 + 2.0).r) * 0.5;      // old, flattened leaves
	c = mix(c, vec3(0.32, 0.2, 0.1) * (0.8 + 0.4 * texture(nz, wxz * 2.2).r), mush);
	c = mix(c, lcol, leaf * near * 0.95);
	return mix(c, vec3(0.5, 0.33, 0.14), dens * 0.3 * (1.0 - near));                    // far: only the colour
}
