// «Wege und Strassen» (scripts/wege.gd, nur Normal / Hoch): Feldweg («erde»: zwei Kies-Fahrspuren, Gras in der Mitte) oder
// Kiesweg («kies»). UV = (quer in m ab der Mitte, längs in m), UV2 = (halbe Breite, weicher Rand in m). Wo Gras ist (Mitte,
// Rand), wird nicht gezeichnet: der Boden darunter scheint durch (gleiches Gras, gleiche Jahreszeit, gleicher Schnee).
shader_type spatial;

uniform vec4 base : source_color = vec4(0.36, 0.28, 0.19, 1.0);
uniform vec4 grit : source_color = vec4(0.27, 0.21, 0.15, 1.0);
uniform vec4 snow : source_color = vec4(0.93, 0.94, 0.96, 1.0);
uniform float tracks = 0.0;
uniform float snow_amount = 0.0;
uniform float wet = 0.0;
uniform float puddle = 0.0;
uniform float cloud_amt = 0.0;
uniform vec2 cloud_off = vec2(0.0);
uniform float laub = 0.0;             // Schritt 2: autumn leaves (jahreszeiten.gd via wege.gd)
uniform sampler2D noise_tex : repeat_enable;
#include "res://shaders/wege_laub.gdshaderinc"

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float dc = length(VERTEX);
	float x = UV.x;
	float hw = UV2.x;
	float rim = UV2.y;
	float ax = abs(x);
	float big = texture(noise_tex, w.xz * 0.08).r;
	float mid = texture(noise_tex, w.xz * 0.4 + 0.3).r;
	float nf = texture(noise_tex, w.xz * 1.9).r;
	float near = 1.0 - smoothstep(10.0, 30.0, dc);
	// gravel: earth with grey-beige gravel and stones of two sizes (jittered, not a grid)
	vec3 c = mix(base.rgb, grit.rgb, smoothstep(0.35, 0.75, big));
	c = mix(c, vec3(0.5, 0.47, 0.41) * (0.85 + 0.3 * mid), 0.45 * smoothstep(0.3, 0.7, mid + 0.2 * tracks));
	c *= 0.8 + 0.35 * nf;
	float pebble = 0.0;
	vec3 stone = c;
	for (int l = 0; l < 2; l++) {
		float k = l == 0 ? 6.0 : 15.0;
		vec2 sc = floor(w.xz * k + float(l) * 0.37);
		vec2 sf = fract(w.xz * k + float(l) * 0.37) - 0.5;
		float h = hash(sc + float(l) * 17.0);
		vec2 jit = (vec2(hash(sc + 1.3), hash(sc + 2.9)) - 0.5) * 0.5;
		float r = 0.12 + 0.18 * hash(sc + 7.7);
		float pb = (1.0 - smoothstep(r * 0.75, r, length((sf - jit) * vec2(1.0, 1.0 + 0.5 * hash(sc + 3.3))))) * step(0.82, h);
		if (pb > pebble) {
			pebble = pb;
			stone = mix(vec3(0.6, 0.58, 0.54), vec3(0.38, 0.36, 0.33), hash(sc + 5.1)) * (0.85 + 0.4 * (0.25 - sf.y - jit.y));
		}
	}
	pebble *= 1.0 - smoothstep(8.0, 20.0, dc);
	c = mix(c, c * (0.78 + 0.44 * hash(floor(w.xz * 26.0))), 0.5 * near);
	// tracks: two wheel tracks (ruts: darker, compacted), grass between them
	float trk = 1.0;
	float rut = 0.0;
	float grass = 0.0;
	if (tracks > 0.5) {
		float tc = clamp(hw * 0.62, 0.45, 0.85) + 0.05 * (mid - 0.5);
		float d = abs(ax - tc);
		trk = 1.0 - smoothstep(0.24, 0.4, d + 0.08 * (nf - 0.5));
		rut = 1.0 - smoothstep(0.0, 0.14, d);
		c *= 1.0 - 0.18 * rut;
		grass = 1.0 - trk;
		// a few stones also in the grass strip and loose stones at the side of the tracks
		pebble *= mix(0.35, 1.0, trk);
	}
	c = mix(c, stone, pebble * 0.85);
	float rough = 0.95;
	// soft edge: the outer rim and (field path) the middle strip are grass: not drawn, the meadow shows through
	float out_k = (ax - hw) / max(rim, 0.01);
	float br = texture(noise_tex, w.xz * 1.4 + 0.5).r - 0.5;
	float keep = 1.0 - smoothstep(-0.25, 0.75, out_k + 0.9 * br + 0.35 * (hash(floor(w.xz * 12.0)) - 0.5));
	if (tracks > 0.5) {
		keep = min(keep, smoothstep(0.35, 0.65, trk + 0.6 * br + 0.3 * (hash(floor(w.xz * 12.0)) - 0.5) + 0.25 * pebble));
	}
	ALPHA = keep;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	// darker towards the edge (earth with grass roots)
	c *= 1.0 - 0.2 * smoothstep(-0.6, 0.6, out_k);
	c = laub_mix(c, w.xz, laub * (0.4 + 0.6 * max(1.0 - trk, smoothstep(-0.8, 0.4, out_k))) * (0.5 + mid), near, wet, noise_tex);
	// weather: wet, puddles in the ruts (long, along the path), snow (tracks show)
	float pd = 0.0;
	if (puddle > 0.0) {
		float along = texture(noise_tex, vec2(UV.y * 0.09, x * 0.6) + 4.1).r;
		float low = tracks > 0.5 ? rut : (1.0 - smoothstep(0.0, hw * 0.7, ax));
		pd = smoothstep(0.6, 0.66, along * (0.55 + 0.6 * low) + 0.25 * puddle) * puddle;
	}
	c *= 1.0 - 0.4 * wet;
	rough = mix(rough, 0.45, wet);
	float sn = snow_amount * (1.0 - 0.45 * rut);
	c = mix(c, snow.rgb * (0.88 + 0.12 * nf), clamp(sn * (0.85 + 0.3 * mid), 0.0, 1.0));
	c *= 1.0 - cloud_amt * smoothstep(0.52, 0.68, texture(noise_tex, (w.xz + cloud_off) * 0.0035).r);
	vec3 water = mix(c * 0.35, vec3(0.05, 0.05, 0.05), 0.6);           // muddy water
	ALBEDO = mix(c, water, pd);
	ROUGHNESS = mix(rough, 0.03, pd);
	SPECULAR = mix(0.5, 1.0, pd);
}
