// Meadow: patches of greener and drier grass, finer pattern near the camera.
shader_type spatial;

uniform vec4 grass : source_color = vec4(0.22, 0.42, 0.16, 1.0);
uniform vec4 dry : source_color = vec4(0.45, 0.47, 0.25, 1.0);
uniform vec4 snow : source_color = vec4(0.93, 0.94, 0.96, 1.0);
uniform float snow_amount = 0.0;
uniform float wet = 0.0;
uniform float puddle = 0.0;           // 3D-3.98: puddles in the hollows after long rain (0 … 1)
uniform sampler2D noise_tex;
uniform float cloud_amt = 0.0;      // 3D-4.x gelaende.gd: cloud shadows drift over the ground (0 = off)
uniform vec2 cloud_off = vec2(0.0);
// F2 «echte Inhalte» (inhalte.gd, 31.10.2026): Foto-Texturen (CC0) statt Rauschen – nur wenn das Paket da ist, nicht in Lite.
// tex_on = 0: genau wie bisher. A = sattes Gras, B = trockenere Stellen (Gras mit Erde); die Farbe der Jahreszeit bleibt.
uniform float tex_on = 0.0;
uniform sampler2D tex_a_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_a_nrm : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_b_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_b_nrm : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec3 ref_a = vec3(0.3, 0.35, 0.2);   // mittlere Farbe der Texturen (zum Einfärben nach der Jahreszeit)
uniform vec3 ref_b = vec3(0.35, 0.33, 0.22);
uniform float scale_a = 0.5;                 // 1 / Kachelgrösse in m
uniform float scale_b = 0.33;
uniform float tex_far = 70.0;
// «Flora und Fauna» Paket 2 (scripts/gras.gd): p2 = 1: photos fade into their own mean colour (no line at tex_far), a third
// sample near against tiles, worn edges along the paths (pfad: segments a.xy -> b.xy, pfad_r: half width), the far ring of
// the meadow (fell_k: grass texture, flower speckles) and the gust sheen (same wave as grass and crowns). p2 = 0: as before.
uniform float p2 = 0.0;
uniform vec4 pfad[48];
uniform float pfad_r[48];
uniform int pfad_n = 0;
uniform float fell_k = 0.0;
uniform float wind = 0.0;
uniform float gust_amt = 0.0;
uniform vec2 dir = vec2(0.8, 0.6);
uniform float ref_auto = 0.0;                // «Flora und Fauna» (flora.gd): mean colour from the smallest mip (same in every renderer)                // weiter weg wieder das Rauschen (keine sichtbaren Wiederholungen)

vec3 tex2(sampler2D t, vec2 uv, float k) {
	// zwei gedrehte Abtastungen, gemischt nach dem Rauschen: keine sichtbaren Kacheln
	vec2 uv2 = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * uv * 0.43 + vec2(0.37, 0.71);
	return mix(texture(t, uv).rgb, texture(t, uv2).rgb, k);
}

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float big = texture(noise_tex, w.xz * 0.012).r;
	float mid = texture(noise_tex, w.xz * 0.09).r;
	float fine = texture(noise_tex, w.xz * 0.9).r;
	vec3 c = mix(grass.rgb, dry.rgb, smoothstep(0.45, 0.75, big));
	c *= 0.75 + 0.35 * mid + 0.25 * (fine - 0.5);
	vec3 nm = vec3(0.5, 0.5, 1.0);
	if (tex_on > 0.0) {
		float f = tex_on * (1.0 - smoothstep(tex_far * 0.6, tex_far, length(VERTEX)));
		float k = smoothstep(0.3, 0.7, mid);
		float sd = smoothstep(0.45, 0.75, big);
		vec3 ta = tex2(tex_a_alb, w.xz * scale_a, k);
		vec3 tb = tex2(tex_b_alb, w.xz * scale_b, k);
		vec3 ra = ref_auto > 0.0 ? textureLod(tex_a_alb, vec2(0.5), 12.0).rgb : ref_a;
		vec3 rb = ref_auto > 0.0 ? textureLod(tex_b_alb, vec2(0.5), 12.0).rgb : ref_b;
		vec3 ga = mix(ta, ta * grass.rgb / max(ra, vec3(0.02)), 0.65);
		vec3 gb = mix(tb, tb * dry.rgb / max(rb, vec3(0.02)), 0.5);
		vec3 tc = mix(ga, gb, sd) * (0.85 + 0.3 * big) * (ref_auto > 0.0 ? 0.82 : 1.0);   // flora.gd: own photos a bit darker
		if (p2 > 0.0) {
			float dc = length(VERTEX);
			f = tex_on * (1.0 - smoothstep(tex_far * 0.45, tex_far * 1.5, dc));
			vec3 tn = tex2(tex_a_alb, w.xz * scale_a * 2.7 + 0.13, 1.0 - k);           // a third sample near: no tiles
			tc = mix(tc, tc * tn / max(ra, vec3(0.02)), 0.3 * (1.0 - smoothstep(6.0, 18.0, dc)));
			vec3 tm = mix(mix(ra, ra * grass.rgb / max(ra, vec3(0.02)), 0.65), mix(rb, rb * dry.rgb / max(rb, vec3(0.02)), 0.5), sd);
			vec3 cf = tm * (0.85 + 0.3 * big) * (ref_auto > 0.0 ? 0.82 : 1.0) * (0.82 + 0.3 * mid + 0.15 * (fine - 0.5));   // far: the mean colour of the photos
			c = mix(cf, c * (ref_auto > 0.0 ? 0.9 : 1.0), 0.5);                   // ... with the dry / lush patches of the meadow
		}
		c = mix(c, tc, f);
		vec3 na = tex2(tex_a_nrm, w.xz * scale_a, k);
		vec3 nb = tex2(tex_b_nrm, w.xz * scale_b, k);
		nm = mix(nm, mix(na, nb, sd), f * (1.0 - snow_amount));
	}
	if (p2 > 0.0) {
		float dc2 = length(VERTEX);
		float wear = 0.0;
		if (dc2 < 90.0) {
			for (int i = 0; i < 48; i++) {
				if (i >= pfad_n) {
					break;
				}
				vec2 a = pfad[i].xy;
				vec2 ab = pfad[i].zw - a;
				float t = clamp(dot(w.xz - a, ab) / max(dot(ab, ab), 1e-4), 0.0, 1.0);
				float d = length(w.xz - a - ab * t);
				wear = max(wear, smoothstep(pfad_r[i] + 0.9, pfad_r[i] * 0.6, d));
			}
		}
		float brk = texture(noise_tex, w.xz * 0.55 + 0.4).r;
		wear *= smoothstep(0.1, 0.55, brk + wear * 0.45);                      // ragged, not a clean band
		vec3 soil = vec3(0.33, 0.28, 0.2) * (0.75 + 0.5 * fine) * (0.85 + 0.3 * mid);
		vec3 trod = mix(c * vec3(1.06, 1.0, 0.78) * 0.9, soil, smoothstep(0.7, 1.0, wear) * smoothstep(0.25, 0.6, brk));   // grass left in tufts
		c = mix(c, trod, wear * 0.85 * (1.0 - snow_amount));
		float ff = smoothstep(8.0, 30.0, dc2) * fell_k * (1.0 - snow_amount);   // far ring: the meadow, no clumps any more
		float fn = texture(noise_tex, w.xz * 2.3).r;
		c *= mix(1.0, 0.82 + 0.32 * fn, ff * 0.7);
		float fl = texture(noise_tex, w.xz * 1.1 + 5.3).r;
		float pat = smoothstep(0.5, 0.78, texture(noise_tex, w.xz * 0.05 + 1.7).r);
		float dots = smoothstep(0.84, 0.9, fl) * pat * ff * (1.0 - wear);
		vec3 fcol = fract(fl * 37.0) < 0.5 ? vec3(0.92, 0.92, 0.86) : vec3(0.92, 0.78, 0.2);
		c = mix(c, fcol * 0.8, dots * 0.55);
		if (gust_amt > 0.0) {                                                  // the gust: a lighter wave over the meadow
			float g = smoothstep(0.3, 0.8, texture(noise_tex, (w.xz - dir * TIME * (0.6 + wind * 0.03)) * 0.02).r);
			c *= 1.0 + 0.1 * g * gust_amt * clamp(wind / 25.0, 0.0, 1.0) * (1.0 - wear) * (1.0 - snow_amount);
		}
	}
	c = mix(c, snow.rgb * (0.92 + 0.08 * fine), snow_amount);
	float pd = puddle * smoothstep(0.34, 0.26, big + 0.15 * (mid - 0.5)) * (1.0 - snow_amount);
	c *= 1.0 - cloud_amt * smoothstep(0.52, 0.68, texture(noise_tex, (w.xz + cloud_off) * 0.0035).r);
	ALBEDO = mix(c * (1.0 - 0.35 * wet), vec3(0.05, 0.055, 0.06), pd);
	ROUGHNESS = mix(mix(0.95, 0.35, wet), 0.04, pd);
	SPECULAR = mix(0.5, 0.9, pd);
	NORMAL_MAP = mix(nm, vec3(0.5, 0.5, 1.0), pd);
}
