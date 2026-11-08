// «Wege und Strassen» (scripts/wege.gd, nur Normal / Hoch): eine Asphalt-Strasse. UV = (quer in m ab der Mitte, längs in m),
// UV2 = (halbe Breite des Asphalts, Bankett in m). Alles aus dem Ort gerechnet (kein Zufall), wenige Abtastungen (HD 4600).
shader_type spatial;

uniform vec4 asphalt : source_color = vec4(0.29, 0.29, 0.3, 1.0);
uniform vec4 gravel : source_color = vec4(0.45, 0.43, 0.39, 1.0);
uniform vec4 snow : source_color = vec4(0.93, 0.94, 0.96, 1.0);
uniform float laub = 0.0;             // Schritt 2: autumn leaves at the edge (jahreszeiten.gd via wege.gd)
uniform sampler2D noise_tex : repeat_enable;
#include "res://shaders/wege_laub.gdshaderinc"
uniform sampler2D photo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float photo_on = 0.0;
uniform float fine = 0.6;             // fine detail (Hoch 1.0)
uniform float centre_line = 1.0;      // dashed white centre line (Leitlinie 3 m / 6 m)
uniform float edge_line = 1.0;        // white edge lines
uniform vec3 park = vec3(0.0);        // yellow parking fields: along from .x to .y (m), side .z (±1, 0 = none)
uniform float snow_amount = 0.0;
uniform float wet = 0.0;
uniform float puddle = 0.0;
uniform float cloud_amt = 0.0;
uniform vec2 cloud_off = vec2(0.0);

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float dc = length(VERTEX);
	float x = UV.x;                       // across (m)
	float y = UV.y;                       // along (m)
	float hw = UV2.x;
	float rim = UV2.y;
	float ax = abs(x);
	float big = texture(noise_tex, w.xz * 0.045).r;
	float mid = texture(noise_tex, w.xz * 0.31 + 0.7).r;
	float nf = texture(noise_tex, w.xz * 2.1).r;
	float near = 1.0 - smoothstep(25.0, 70.0, dc);

	// ---- asphalt ----
	vec3 c = asphalt.rgb * (0.86 + 0.28 * big);                       // bleached / older parts
	if (photo_on > 0.0) {
		vec3 tp = texture(photo, w.xz / 3.0).rgb;
		vec3 tm = textureLod(photo, vec2(0.5), 12.0).rgb;
		c *= mix(vec3(1.0), tp / max(tm, vec3(0.02)), 0.8 * near);
	}
	float agg = hash(floor(w.xz * 34.0));                             // aggregate: light and dark stones
	c *= 1.0 + (agg - 0.5) * 0.22 * fine * (1.0 - smoothstep(6.0, 18.0, dc));
	// wheel tracks: darker and a little polished (two lanes, or one in the middle of a narrow road)
	float lane = hw > 2.4 ? hw * 0.5 : 0.0;
	float tr = 0.0;
	for (int s = -1; s <= 1; s += 2) {
		float lc = lane * float(s);
		tr = max(tr, 1.0 - smoothstep(0.18, 0.42, abs(abs(x - lc) - 0.8)));
	}
	tr *= 0.75 + 0.5 * mid;
	c *= 1.0 - 0.16 * tr;
	// patches (Flicken): rectangles along the road, fresher (darker) bitumen with a sealed seam
	float cell = floor(y / 9.0);
	float hp = hash(vec2(cell, 3.1));
	float flick = 0.0;
	float seam = 0.0;
	if (hp < 0.38) {
		float y0 = cell * 9.0 + 1.0 + hash(vec2(cell, 7.7)) * 3.0;
		float y1 = y0 + 1.4 + hash(vec2(cell, 1.3)) * 3.5;
		float x0 = -hw + hash(vec2(cell, 5.5)) * hw;
		float x1 = min(x0 + 1.0 + hash(vec2(cell, 9.2)) * 2.2, hw);
		vec2 dd = vec2(max(x0 - x, x - x1), max(y0 - y, y - y1));
		float dbox = max(dd.x, dd.y);
		flick = 1.0 - step(0.0, dbox);
		seam = 1.0 - smoothstep(0.02, 0.06, abs(dbox));
	}
	c = mix(c, asphalt.rgb * 0.72 * (0.9 + 0.2 * nf), flick * 0.85);
	c *= 1.0 - 0.35 * seam * near;
	// cracks: thin dark lines along the ridges of the noise, only in older parts; a long crack near the edge
	float cr1 = abs(texture(noise_tex, w.xz * 0.21 + 3.3).r - 0.5);
	float cr2 = abs(texture(noise_tex, w.xz * 0.6 + 1.9).r - 0.5);
	float old = smoothstep(0.45, 0.7, big) * (1.0 - flick);
	float crack = (1.0 - smoothstep(0.004, 0.012, cr1)) * old + (1.0 - smoothstep(0.004, 0.01, cr2)) * old * 0.6;
	float ec = abs(ax - (hw - 0.35 - 0.12 * mid));
	crack = max(crack, (1.0 - smoothstep(0.01, 0.03, ec)) * smoothstep(0.55, 0.75, nf));
	c *= 1.0 - 0.5 * clamp(crack, 0.0, 1.0) * near;
	// manhole covers: some 9 m cells, in a lane, cast iron with a ring and a grid
	float mh = 0.0;
	float mcell = floor(y / 23.0);
	if (hash(vec2(mcell, 4.4)) < 0.45) {
		vec2 mc = vec2((hash(vec2(mcell, 8.1)) < 0.5 ? -1.0 : 1.0) * max(lane, 0.0) * 0.9, mcell * 23.0 + 11.5);
		float r = length(vec2(x, y) - mc);
		mh = 1.0 - smoothstep(0.3, 0.32, r);
		float ring = smoothstep(0.26, 0.28, r) * mh;
		vec2 gq = fract((vec2(x, y) - mc) * 9.0);
		float grid = step(0.75, max(gq.x, gq.y));
		vec3 iron = vec3(0.19, 0.19, 0.2) * (0.85 + 0.3 * nf) * (1.0 - 0.3 * grid) * (1.0 - 0.35 * ring);
		c = mix(c, iron, mh);
	}
	// markings (worn a little; lighter and smoother)
	float wl = 0.0;
	if (edge_line > 0.5 && hw >= 1.9) {
		wl = max(wl, 1.0 - smoothstep(0.065, 0.08, abs(ax - (hw - 0.28))));
	}
	if (centre_line > 0.5 && hw >= 2.45) {
		float dash = step(fract(y / 9.0), 0.333);
		wl = max(wl, (1.0 - smoothstep(0.05, 0.065, ax)) * dash);
	}
	float yl = 0.0;
	if (park.z != 0.0 && y > park.x && y < park.y && x * park.z > 0.0) {
		float px = abs(x);
		float inner = hw - 2.1;                                       // fields 2 m wide on the side lane, 6 m long
		float frame = 1.0 - smoothstep(0.05, 0.065, abs(px - inner));
		float stop = 1.0 - smoothstep(0.05, 0.065, abs(mod(y - park.x + 0.06, 6.0) - 0.06));
		yl = max(frame, stop * step(inner, px) * step(px, hw - 0.28));
		wl *= 1.0 - step(inner - 0.1, px) * step(px, hw);            // no white edge line along the fields
		yl = max(yl, (1.0 - smoothstep(0.065, 0.08, abs(px - (hw - 0.28)))));
	}
	float wear = smoothstep(0.25, 0.65, texture(noise_tex, w.xz * 1.3 + 0.2).r + 0.25 * (1.0 - tr));
	wl *= wear * (1.0 - mh);
	yl *= wear * (1.0 - mh);
	c = mix(c, vec3(0.86, 0.86, 0.83), wl * 0.9);
	c = mix(c, vec3(0.88, 0.7, 0.12), yl * 0.9);
	float rough = mix(0.88, 0.78, tr) - 0.12 * (wl + yl);

	// ---- edge: the asphalt breaks off unevenly into the gravel shoulder (Bankett), which fades into the meadow ----
	float edge = hw + 0.08 * (mid - 0.5) + 0.04 * (nf - 0.5);
	float sh = smoothstep(edge - 0.02, edge + 0.02, ax);
	vec3 gc = gravel.rgb * (0.75 + 0.45 * nf) * (0.85 + 0.3 * mid);
	float st = hash(floor(w.xz * 11.0));
	gc *= 0.8 + 0.4 * st;
	c = mix(c, gc, sh);
	rough = mix(rough, 0.95, sh);
	float out_k = (ax - hw) / max(rim, 0.01);                          // 0 at the asphalt … 1 at the end of the strip
	ALPHA = 1.0;
	if (rim > 0.0) {
		float soft = out_k + 0.55 * (texture(noise_tex, w.xz * 1.7 + 0.5).r - 0.5) + 0.25 * (st - 0.5);
		ALPHA = 1.0 - step(0.72, soft) * sh;
	}
	ALPHA_SCISSOR_THRESHOLD = 0.5;

	c = laub_mix(c, w.xz, laub * (0.12 + 0.88 * smoothstep(hw - 1.0, hw + 0.2, ax)) * (1.0 - 0.7 * tr) * (0.5 + mid), near, wet, noise_tex);
	// ---- weather ----
	float pd = 0.0;
	if (puddle > 0.0) {                                                 // in the wheel tracks and along the edge
		float low = max(tr * 0.9, (1.0 - smoothstep(0.0, 0.6, abs(ax - hw + 0.25))) * 0.8) * (1.0 - sh);
		float spot = texture(noise_tex, vec2(w.x * 0.18 + w.z * 0.05, w.z * 0.5 - w.x * 0.02) + 2.7).r;
		pd = smoothstep(0.66, 0.71, spot * (0.55 + 0.6 * low) + 0.2 * puddle) * puddle * (1.0 - mh);
	}
	c *= 1.0 - 0.45 * wet * (1.0 - sh * 0.4);
	rough = mix(rough, 0.3, wet * (1.0 - sh * 0.5));
	float sn = snow_amount * (1.0 - 0.75 * tr * (1.0 - sh));            // tyres keep the tracks free
	c = mix(c, snow.rgb * (0.9 + 0.1 * nf), clamp(sn * (0.8 + 0.4 * mid), 0.0, 1.0));
	rough = mix(rough, 0.8, sn);
	c *= 1.0 - cloud_amt * smoothstep(0.52, 0.68, texture(noise_tex, (w.xz + cloud_off) * 0.0035).r);
	ALBEDO = mix(c, vec3(0.03, 0.035, 0.04), pd * (1.0 - sn));
	ROUGHNESS = mix(rough, 0.02, pd * (1.0 - sn));
	SPECULAR = mix(0.5, 1.0, pd);
	METALLIC = 0.12 * mh;
}
