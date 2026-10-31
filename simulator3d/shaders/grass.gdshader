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
uniform float tex_far = 70.0;                // weiter weg wieder das Rauschen (keine sichtbaren Wiederholungen)

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
		vec3 ga = mix(ta, ta * grass.rgb / max(ref_a, vec3(0.02)), 0.65);
		vec3 gb = mix(tb, tb * dry.rgb / max(ref_b, vec3(0.02)), 0.5);
		vec3 tc = mix(ga, gb, sd) * (0.85 + 0.3 * big);
		c = mix(c, tc, f);
		vec3 na = tex2(tex_a_nrm, w.xz * scale_a, k);
		vec3 nb = tex2(tex_b_nrm, w.xz * scale_b, k);
		nm = mix(nm, mix(na, nb, sd), f * (1.0 - snow_amount));
	}
	c = mix(c, snow.rgb * (0.92 + 0.08 * fine), snow_amount);
	float pd = puddle * smoothstep(0.34, 0.26, big + 0.15 * (mid - 0.5)) * (1.0 - snow_amount);
	c *= 1.0 - cloud_amt * smoothstep(0.52, 0.68, texture(noise_tex, (w.xz + cloud_off) * 0.0035).r);
	ALBEDO = mix(c * (1.0 - 0.35 * wet), vec3(0.05, 0.055, 0.06), pd);
	ROUGHNESS = mix(mix(0.95, 0.35, wet), 0.04, pd);
	SPECULAR = mix(0.5, 0.9, pd);
	NORMAL_MAP = mix(nm, vec3(0.5, 0.5, 1.0), pd);
}
