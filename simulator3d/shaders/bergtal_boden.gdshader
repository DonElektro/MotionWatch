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

// Foto-Texturen (3.30, Texturen aus eigenen Fotos von DonElektro; bergtal_texturen.gd): Schalter «Foto-Texturen»
// (main.foto_tex), nie in Lite (photo = 0: alles wie vorher, es wird keine Textur gelesen). Die Fotos geben nur die Struktur
// und einen Teil der Farbe: Farbe der Zone (Vertex-Farbe) × Foto / Mittelwert des Fotos (avg_*) - so bleiben Zonen,
// Jahreszeit und die Farben der anderen Teile stimmig. Gegen sichtbare Wiederholung: zwei Kacheln mit Versatz und Hash-Drehung je Fleck
// (Index aus dem Rauschen, weich überblendet), ein zweiter, grosser Massstab desselben Fotos (big_scale) und Makro-Flecken
// (zwei Wiesen gemischt, grosses Rauschen). Fels: ohne Drehung (die Schichten bleiben waagrecht), zweiter Massstab 31 m.
uniform float photo = 0.0;
uniform sampler2D t_wiese : source_color, repeat_enable, filter_linear_mipmap_anisotropic;      // wiese_alp_01 (scharf)
uniform sampler2D t_wiese2 : source_color, repeat_enable, filter_linear_mipmap_anisotropic;     // wiese_hellgruen_01
uniform sampler2D t_alp : source_color, repeat_enable, filter_linear_mipmap_anisotropic;        // wiese_alp_steinig_01
uniform sampler2D t_geroell : source_color, repeat_enable, filter_linear_mipmap_anisotropic;    // geroell_gras_02
uniform sampler2D t_rose : source_color, repeat_enable, filter_linear_mipmap_anisotropic;       // zwergstrauch_alpenrose_01
uniform sampler2D t_fels : source_color, repeat_enable, filter_linear_mipmap_anisotropic;       // fels_kalk_grau_01
uniform sampler2D t_fels2 : source_color, repeat_enable, filter_linear_mipmap_anisotropic;      // fels_platte_hell_01
uniform sampler2D t_wald : source_color, repeat_enable, filter_linear_mipmap_anisotropic;       // wald_von_oben_02 (unscharf: nur Makro)
uniform vec3 avg_wiese = vec3(0.5);
uniform vec3 avg_wiese2 = vec3(0.5);
uniform vec3 avg_alp = vec3(0.5);
uniform vec3 avg_geroell = vec3(0.5);
uniform vec3 avg_rose = vec3(0.5);
uniform vec3 avg_fels = vec3(0.5);
uniform vec3 avg_fels2 = vec3(0.5);
uniform vec3 avg_wald = vec3(0.5);

varying vec3 lpos;
varying vec3 lnrm;
varying vec3 wpos;

// one photo without visible repetition: two copies with an offset per patch (index from the noise), blended softly
// (I. Quilez «texture repetition» 3). textureGrad with the derivatives of the plain uv: no seams at the patch borders.
// dx, dy: the derivatives of uv - taken outside the branches (no derivatives in non-uniform control flow)
// rot = 1: each patch also turned by a hash angle (grass, scree from above); rot = 0: no turn (rock layers stay level)
vec2 rot_h(vec2 v, float h) {
	float a = fract(sin(h * 12.9898) * 43758.5453) * 6.2831;
	float cs = cos(a);
	float sn = sin(a);
	return vec2(cs * v.x - sn * v.y, sn * v.x + cs * v.y);
}

// the mean colour of a photo, read from its smallest mip level (1 × 1): in the same colour space as the samples, so
// photo / mean is 1 on average in every renderer (the avg_* uniforms from bergtal_texturen.gd are only a fallback note)
vec3 mean_of(sampler2D t) {
	return max(textureLod(t, vec2(0.5), 12.0).rgb, vec3(0.01));
}

vec3 tex_var(sampler2D t, vec2 uv, vec2 dx, vec2 dy, float k, float rot) {
	float l = k * 8.0;
	float ia = floor(l);
	float f = fract(l);
	vec2 oa = sin(vec2(3.0, 7.0) * ia);
	vec2 ob = sin(vec2(3.0, 7.0) * (ia + 1.0));
	float ha = (ia + 0.37) * rot;
	float hb = (ia + 1.37) * rot;
	vec3 ca = textureGrad(t, rot_h(uv, ha) + oa, rot_h(dx, ha), rot_h(dy, ha)).rgb;
	vec3 cb = textureGrad(t, rot_h(uv, hb) + ob, rot_h(dx, hb), rot_h(dy, hb)).rgb;
	return mix(ca, cb, smoothstep(0.2, 0.8, f - 0.1 * dot(ca - cb, vec3(1.0))));
}

// second scale: the same photo about 4.3× bigger, only as a soft brightness pattern (breaks the grid seen from afar)
vec3 big_scale(sampler2D t, vec2 uv, vec2 dx, vec2 dy, vec3 avg, float s) {
	vec3 b = textureGrad(t, rot_h(uv, 5.1) / 4.3 + 0.41, rot_h(dx, 5.1) / 4.3, rot_h(dy, 5.1) / 4.3).rgb;
	return mix(vec3(1.0), b / max(avg, vec3(0.01)), s);
}

// the structure of a photo on the colour of the zone: c × (photo / its mean), plus a part of the photo's own colour
vec3 on_photo(vec3 c, vec3 t, vec3 avg, float s, float own) {
	vec3 r = c * mix(vec3(1.0), t / max(avg, vec3(0.01)), s);
	return mix(r, t * dot(c, vec3(0.333)) / max(dot(avg, vec3(0.333)), 0.01), own);
}

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
	float pk = 0.0;                                 // Foto-Texturen: how much photo here (for the fine noise below)
	if (photo > 0.5) {
		// zones from the vertex colour (sRGB): grass (meadow, alp, golden slopes), stones (scree, shore), forest floor
		vec3 s0 = COLOR.rgb;
		float sat = max(s0.r, max(s0.g, s0.b)) - min(s0.r, min(s0.g, s0.b));
		float grassy = smoothstep(0.1, 0.2, s0.g - s0.b);
		float forest = smoothstep(0.34, 0.27, s0.r) * smoothstep(0.31, 0.26, s0.g) * smoothstep(0.05, 0.09, s0.g - s0.b);
		float stony = smoothstep(0.085, 0.035, sat) * smoothstep(0.38, 0.5, s0.r);
		grassy *= 1.0 - forest;
		float k1 = texture(noise_tex, lpos.xz * 0.011).r;            // index of the patches (repetition)
		float k2 = texture(noise_tex, lpos.xz * 0.0031 + 0.37).r;    // macro: lush or dry meadow
		float dist = length(wpos - CAMERA_POSITION_WORLD);
		vec2 gx = dFdx(lpos.xz);                                     // derivatives for textureGrad (see tex_var)
		vec2 gy = dFdy(lpos.xz);
		float rn = texture(noise_tex, lpos.xz * 0.009 + 0.71).r;
		float near = 1.0 - smoothstep(250.0, 700.0, dist);           // far away: only the colour of the zone
		vec3 g = c;
		if (grassy > 0.01) {
			vec3 wa = tex_var(t_wiese, lpos.xz / 3.2, gx / 3.2, gy / 3.2, k1, 1.0)
					* big_scale(t_wiese, lpos.xz / 3.2, gx / 3.2, gy / 3.2, mean_of(t_wiese), 0.45);
			vec3 wb = tex_var(t_wiese2, lpos.xz / 6.5 + 0.21, gx / 6.5, gy / 6.5, k2 * 1.7, 1.0);
			float lush = smoothstep(0.38, 0.62, k2 + 0.25 * (mid - 0.5));
			vec3 gm = mix(on_photo(c, wa, mean_of(t_wiese), 0.9, 0.25), on_photo(c, wb, mean_of(t_wiese2), 0.85, 0.2), lush * 0.6);
			// high up: the stony alpine meadow
			float hi = smoothstep(300.0, 560.0, lpos.y + 90.0 * (big - 0.5));
			if (hi > 0.01) {
				vec3 al = tex_var(t_alp, lpos.xz / 3.6 + 0.5, gx / 3.6, gy / 3.6, k1 * 1.3, 1.0);
				gm = mix(gm, on_photo(c, al, mean_of(t_alp), 0.9, 0.25), hi);
			}
			// dwarf shrubs (alpine roses, bilberries) in patches on the ridges, not on steep rock
			float rose = smoothstep(330.0, 420.0, lpos.y) * (1.0 - smoothstep(640.0, 720.0, lpos.y))
					* smoothstep(0.55, 0.68, rn + 0.2 * (mid - 0.5))
					* (1.0 - smoothstep(0.25, 0.4, slope));
			if (rose > 0.01) {
				vec3 ro = tex_var(t_rose, lpos.xz / 3.0 + 0.13, gx / 3.0, gy / 3.0, k1 * 0.7, 1.0);
				gm = mix(gm, on_photo(c, ro, mean_of(t_rose), 1.0, 0.6) * mix(vec3(1.0), grass_tint, 0.5), rose);
			}
			g = mix(g, gm, grassy);
		}
		if (stony > 0.01) {
			vec3 st = tex_var(t_geroell, lpos.xz / 4.2 + 0.77, gx / 4.2, gy / 4.2, k1 * 1.1, 1.0)
					* big_scale(t_geroell, lpos.xz / 4.2, gx / 4.2, gy / 4.2, mean_of(t_geroell), 0.4);
			g = mix(g, on_photo(c, st, mean_of(t_geroell), 0.95, 0.2), stony);
		}
		if (forest > 0.01) {                              // the forest seen from far (above): crowns, gaps
			vec3 fw = textureGrad(t_wald, lpos.xz / 95.0, gx / 95.0, gy / 95.0).rgb;
			g = mix(g, on_photo(c, fw, mean_of(t_wald), 0.8, 0.3), forest * smoothstep(40.0, 160.0, dist));
		}
		pk = near * max(grassy, max(stony, forest * 0.5));
		c = mix(c, g, near);
	}
	c = mix(c, c * grass_tint, green);
	// rock on steep ground («wie auf den Fotos», Stockhorn): mostly light grey limestone in oblique layers (darker grey
	// bands between), a little rusty iron and dark serpentine (big noise); same cost as before
	vec3 gneis = vec3(0.24, 0.235, 0.22);
	vec3 kalk = vec3(0.46, 0.45, 0.42);
	vec3 rost = vec3(0.24, 0.15, 0.10);
	vec3 serp = vec3(0.09, 0.11, 0.09);
	vec3 rock = mix(kalk, gneis, smoothstep(0.62, 0.74, fract(dot(lpos, vec3(0.006, 0.014, -0.004)) + big * 0.8)));
	rock = mix(rock, rost, smoothstep(0.66, 0.74, big) * 0.6);
	rock = mix(rock, serp, smoothstep(0.34, 0.26, big) * 0.6);
	rock = mix(rock, kalk * 1.12, smoothstep(520.0, 760.0, lpos.y) * 0.6);     // the high walls and summits: light
	rock *= 0.75 + 0.5 * mid + 0.25 * (fine - 0.5);
	if (detail > 0.5 && slope > 0.3) {
		// water streaks down the walls (dark, vertical) - not in Lite
		vec2 t2 = normalize(vec2(-lnrm.z, lnrm.x) + vec2(0.0001, 0.0));
		float streak = texture(noise_tex, vec2(dot(lpos.xz, t2) * 0.11, lpos.y * 0.004)).r;
		rock *= 1.0 - 0.35 * smoothstep(0.58, 0.75, streak);
	}
	float rk = smoothstep(0.2, 0.36, slope + 0.08 * (mid - 0.5)) * rockable;
	if (photo > 0.5) {                              // (uniform: in Lite nothing of this runs)
		// Foto-Texturen: limestone wall along the wall (like the noise above), light slabs high up; the colours of the
		// procedural rock (bands, rust, serpentine) stay as the colour, the photo gives cracks, ledges and shadows
		// projected onto the slope itself (level tangent T, down-slope B): no stretching on half-steep ground
		vec3 t3 = normalize(vec3(-lnrm.z, 0.0, lnrm.x) + vec3(0.0001, 0.0, 0.0));
		vec3 b3 = normalize(cross(normalize(lnrm), t3));
		vec2 ruv = vec2(dot(lpos, t3), dot(lpos, b3));
		vec2 rx = dFdx(ruv);
		vec2 ry = dFdy(ruv);
		float k3 = texture(noise_tex, ruv * 0.013 + 0.5).r;
		if (rk > 0.01) {
			vec3 fa = tex_var(t_fels, ruv / 9.0, rx / 9.0, ry / 9.0, k3, 0.0);
			vec3 fb = textureGrad(t_fels, ruv / 31.0 + 0.3, rx / 31.0, ry / 31.0).rgb;   // second scale: big structure
			vec3 fr = on_photo(rock, fa, mean_of(t_fels), 0.85, 0.05) * mix(vec3(1.0), fb / max(mean_of(t_fels), vec3(0.01)), 0.35);
			float hl = smoothstep(480.0, 720.0, lpos.y + 100.0 * (big - 0.5)) * 0.8;
			if (hl > 0.01) {
				vec3 fp = tex_var(t_fels2, ruv / 6.0 + 0.6, rx / 6.0, ry / 6.0, k3 * 1.4, 0.0);
				fr = mix(fr, on_photo(rock, fp, mean_of(t_fels2), 0.9, 0.3), hl);
			}
			rock = mix(rock, fr, 1.0 - smoothstep(350.0, 900.0, length(wpos - CAMERA_POSITION_WORLD)) * 0.6);
			pk = max(pk, rk);
		}
	}
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
	c *= 1.0 + detail * (0.22 * (fine - 0.5) * (1.0 - 0.7 * pk) + 0.18 * (mid - 0.5)) * (1.0 - 0.7 * sk);
	float pd = puddle * smoothstep(0.30, 0.22, texture(noise_tex, lpos.xz * 0.012).r + 0.15 * (mid - 0.5)) * (1.0 - green * 0.6) * (1.0 - smoothstep(0.05, 0.12, slope));
	ALBEDO = mix(clamp(c, 0.0, 1.0) * (1.0 - 0.35 * wet * (1.0 - sk)), vec3(0.05, 0.055, 0.06), pd);
	ROUGHNESS = mix(mix(0.95, 0.4, wet), 0.04, pd) * (1.0 - 0.15 * sk);
	SPECULAR = mix(0.5, 0.9, pd);
}
