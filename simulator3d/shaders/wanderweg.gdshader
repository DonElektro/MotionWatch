// «Wege und Strassen» Schritt 2 (scripts/wege.gd, nur Normal / Hoch): ein Wanderweg - schmaler, festgetretener Pfad aus Erde
// mit Wurzeln und Steinen, leicht eingesunken (die Mitte heller und glatter, der Rand dunkler unter dem Graswulst), weicher
// Rand ins Gras. UV = (quer in m ab der Mitte, längs in m), UV2 = (halbe Breite, weicher Rand in m).
// Jahreszeit: laub (Herbstlaub), snow_amount (Schnee mit Fussspuren in der Mitte), wet / puddle (Matsch und Pfützen).
shader_type spatial;

uniform vec4 earth : source_color = vec4(0.34, 0.27, 0.19, 1.0);
uniform vec4 earth2 : source_color = vec4(0.25, 0.2, 0.15, 1.0);
uniform float rock = 0.0;            // 0 = Erde (Wald, Wiese) … 1 = Bergweg (Geröll, Fels)
uniform float roots = 1.0;           // Wurzeln (im Wald)
uniform vec4 snow : source_color = vec4(0.93, 0.94, 0.96, 1.0);
uniform float snow_amount = 0.0;
uniform float snow_fest = 0.0;       // Bergtal: snow of its own winter (the weather does not take it away)
uniform float wet = 0.0;
uniform float puddle = 0.0;
uniform float laub = 0.0;
uniform float cloud_amt = 0.0;
uniform vec2 cloud_off = vec2(0.0);
uniform sampler2D noise_tex : repeat_enable;
#include "res://shaders/wege_laub.gdshaderinc"

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float dc = length(VERTEX);
	float x = UV.x;
	float y = UV.y;
	float hw = UV2.x;
	float rim = UV2.y;
	float ax = abs(x);
	float a = ax / max(hw, 0.05);                                       // 0 middle … 1 edge of the trodden part
	float big = texture(noise_tex, w.xz * 0.07).r;
	float mid = texture(noise_tex, w.xz * 0.45 + 0.3).r;
	float nf = texture(noise_tex, w.xz * 2.2).r;
	float near = 1.0 - smoothstep(8.0, 25.0, dc);
	// trodden earth: lighter and smoother in the middle (where people walk), darker under the grass lip at the edge
	vec3 c = mix(earth.rgb, earth2.rgb, smoothstep(0.3, 0.75, big));
	c *= 0.82 + 0.3 * nf;
	c *= 1.06 - 0.3 * smoothstep(0.45, 1.05, a);
	vec3 grey = vec3(0.5, 0.49, 0.46) * (0.75 + 0.4 * mid);
	c = mix(c, grey, rock * (0.45 + 0.4 * smoothstep(0.4, 0.7, big)));
	// stones: a few embedded (bigger, rounded, lit from above) and small gravel
	float stone = 0.0;
	vec3 sc = c;
	for (int l = 0; l < 2; l++) {
		float k = l == 0 ? 3.2 : 9.0;
		vec2 cell = floor(w.xz * k + float(l) * 0.41);
		vec2 f = fract(w.xz * k + float(l) * 0.41) - 0.5;
		vec2 jit = (vec2(hash(cell + 1.7), hash(cell + 4.3)) - 0.5) * 0.45;
		float r = 0.14 + 0.2 * hash(cell + 8.1);
		float s = (1.0 - smoothstep(r * 0.7, r, length((f - jit) * vec2(1.0, 1.3)))) * step(l == 0 ? 0.88 - 0.25 * rock : 0.87, hash(cell + float(l) * 13.0));
		if (s > stone) {
			stone = s * (l == 0 ? 1.0 : 0.6);
			vec3 sbase = l == 0 ? mix(vec3(0.55, 0.53, 0.5), vec3(0.36, 0.35, 0.33), hash(cell + 2.2)) : c * mix(1.25, 0.75, hash(cell + 2.2));
			sc = sbase * (0.8 + 0.4 * clamp(0.3 - (f.y - jit.y) * 1.5, 0.0, 1.0));
		}
	}
	stone *= 1.0 - smoothstep(10.0, 25.0, dc);
	c = mix(c, sc, stone * 0.9);
	// roots: dark winding bands across the path (some stretches only), lit edge on top
	float rr = 0.0;
	if (roots > 0.0) {
		float zone = smoothstep(0.55, 0.7, texture(noise_tex, vec2(y * 0.02, 0.37)).r);
		vec2 rc = vec2(x * 0.9 + 0.35 * sin(y * 1.7), y * 0.33);
		float rn = abs(texture(noise_tex, rc * 0.5 + 1.3).r - 0.5);
		rr = (1.0 - smoothstep(0.012, 0.028, rn)) * zone * roots * near;
		float hi = (1.0 - smoothstep(0.004, 0.012, rn)) * zone * roots * near;
		c = mix(c, vec3(0.2, 0.14, 0.09), rr * 0.9);
		c = mix(c, vec3(0.42, 0.32, 0.22), hi * 0.5);
	}
	float rough = mix(0.95, 0.85, 1.0 - a);
	// soft edge: grass grows in over the rim (the meadow below shows through)
	float out_k = (ax - hw) / max(rim, 0.01);
	float br = texture(noise_tex, w.xz * 1.6 + 0.5).r - 0.5;
	ALPHA = 1.0 - smoothstep(-0.3, 0.7, out_k + 0.9 * br + 0.35 * (hash(floor(w.xz * 14.0)) - 0.5) - 0.3 * stone);
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	// autumn: leaves, more at the edges and in the hollows
	float ldens = laub * (0.35 + 0.65 * smoothstep(0.2, 0.9, a)) * (0.5 + mid);
	c = mix(c, laub_mix(c, w.xz, ldens, near, wet, noise_tex), 1.0 - stone * 0.6);
	// rain: mud (dark, glossy) and puddles in the middle
	float pd = 0.0;
	if (puddle > 0.0) {
		float spot = texture(noise_tex, vec2(y * 0.11, x * 0.8) + 3.7).r;
		pd = smoothstep(0.62, 0.68, spot * (0.5 + 0.6 * (1.0 - a)) + 0.22 * puddle) * puddle * (1.0 - stone);
	}
	c *= 1.0 - 0.45 * wet * (1.0 - 0.4 * rock);
	rough = mix(rough, 0.35, wet * (1.0 - stone * 0.5));
	// snow: lying snow, trodden in the middle (greyer, footprints left / right)
	float sn = max(snow_amount, snow_fest);
	if (sn > 0.0) {
		float trod = (1.0 - smoothstep(0.2, 0.5, a)) * smoothstep(0.1, 0.4, sn);
		float st = fract(y / 0.36);
		float side = mod(floor(y / 0.36), 2.0) < 1.0 ? -1.0 : 1.0;
		vec2 fp = vec2((x - side * 0.11) / 0.06, (st - 0.5) / 0.38);
		float foot = (1.0 - smoothstep(0.75, 1.0, length(fp))) * near * trod;
		vec3 sc2 = snow.rgb * (0.9 + 0.1 * nf);
		sc2 = mix(sc2, sc2 * vec3(0.8, 0.84, 0.9), trod * 0.6);                                     // trodden snow, a little blue-grey
		sc2 = mix(sc2, sc2 * vec3(0.74, 0.78, 0.86), foot * 0.85);
		c = mix(c, sc2, clamp(sn * (0.85 + 0.3 * mid) - stone * 0.3, 0.0, 1.0));
		rough = mix(rough, 0.75, sn);
	}
	c *= 1.0 - cloud_amt * smoothstep(0.52, 0.68, texture(noise_tex, (w.xz + cloud_off) * 0.0035).r);
	vec3 water = mix(c * 0.35, vec3(0.06, 0.05, 0.04), 0.6);
	ALBEDO = mix(c, water, pd * (1.0 - sn));
	ROUGHNESS = mix(rough, 0.04, pd * (1.0 - sn));
	SPECULAR = mix(0.5, 1.0, pd);
}
