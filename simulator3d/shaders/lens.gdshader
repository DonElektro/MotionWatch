// the lens and sensor of a camera (from 3D-2.5; exposure from 3D-2.6): the picture behind the quad is read (screen texture),
// multiplied with the exposure (at night: little light, limited amplification -> dark), then grain (stronger the more the
// camera amplifies), dark corners and raindrops. A quad just in front of the camera, only on its own layer.
shader_type spatial;
render_mode unshaded, blend_mix, depth_test_disabled, depth_draw_never, cull_disabled, shadows_disabled;

uniform float noise = 0.0;          // 0..1
uniform float vignette = 0.3;       // 0..1
uniform float drops = 0.0;          // 0..1 share of the places with a drop
uniform vec2 res = vec2(960.0, 540.0);
uniform float expo = 1.0;           // only for the brightness of raindrops (the exposure itself: expo.gdshader)
// difficult conditions (3D-3.27): low sun into the lens, a spider web in front of the camera, steady drops
uniform float glare = 0.0;          // 0..1 low sun shining into the lens
uniform vec2 glare_pos = vec2(0.82, 0.18);
uniform float web = 0.0;            // 0..1 a spider web in the upper left corner
uniform float web_lit = 0.0;        // 0..1 at night the lamp / infrared light makes it shine
uniform float sway = 0.0;
uniform float fogged = 0.0;         // 3D-3.75: 0..1 the lens is fogged up (dew): a milky veil, stronger at the edges
uniform float dirt = 0.0;           // 3D-3.75: 0..1 dirt / pollen spots on the lens           // 0..1 the wind moves the web and the branches in front of the sun

float seg(vec2 p, vec2 a, vec2 b) { vec2 pa = p - a, ba = b - a; float t = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0); return length(pa - ba * t); }

float h(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
// 3D-3.33: grain without sin() - with a growing TIME the old hash lost precision and drew horizontal streaks
float hn(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }

void fragment() {
	vec2 uv = UV;
	float d = distance(uv, vec2(0.5));
	float al = smoothstep(0.38, 0.9, d) * vignette;   // dark corners
	vec3 c = vec3(0.0);
	// grain: every pixel a bit brighter or darker, new each frame
	vec2 px = floor(uv * res);
	float fr = mod(floor(TIME * 30.0), 251.0);
	float g = ((hn(px + fr * vec2(17.31, 43.77)) + hn(px.yx + fr * vec2(5.17, 3.71)) - 1.0) * 0.5) * noise * 0.4;   // softer, like a sensor with noise filter
	float ga = abs(g);
	vec3 gc = g > 0.0 ? vec3(1.0) : vec3(0.0);
	float na = ga + al * (1.0 - ga);
	c = (gc * ga + c * al * (1.0 - ga)) / max(na, 0.0001);
	al = na;
	// raindrops: a few round blurred spots, each comes and dries up again
	if (drops > 0.0) {
		vec2 grid = uv * vec2(8.0, 4.5);
		vec2 id = floor(grid);
		vec2 f = fract(grid) - 0.5;
		float r = h(id);
		float life = fract(TIME * 0.05 + r * 7.0);
		vec2 cc = (vec2(h(id + 3.1), h(id + 7.7)) - 0.5) * 0.6;
		float rad = 0.1 + 0.2 * h(id + 1.3);
		float dd = length((f - cc) * vec2(1.0, 1.25));
		float on = step(r, drops) * smoothstep(1.0, 0.6, life);
		float da = smoothstep(rad, rad * 0.4, dd) * on * 0.45;
		vec3 dc = vec3(0.82, 0.87, 0.93) * max(0.2, expo);
		float na2 = da + al * (1.0 - da);
		c = (dc * da + c * al * (1.0 - da)) / max(na2, 0.0001);
		al = na2;
	}
	// spider web: threads from the corner, a spiral between them, moving in the wind; at night the light makes it bright
	if (web > 0.0) {
		vec2 asp = vec2(res.x / res.y, 1.0);
		vec2 o = vec2(0.0, 0.0);
		vec2 q = uv * asp + vec2(sin(TIME * 1.7) * 0.010, cos(TIME * 1.3) * 0.006) * (0.3 + sway);
		vec2 ctr = vec2(0.22, 0.24) * asp;
		float wd = 1e3;
		for (int k = 0; k < 9; k++) {                       // spokes
			float an = float(k) * 0.698 + 0.2 + (h(vec2(float(k), 3.0)) - 0.5) * 0.4;
			wd = min(wd, seg(q, ctr, ctr + vec2(cos(an), sin(an)) * (0.24 + 0.1 * h(vec2(float(k), 9.0)))));
		}
		vec2 rv = q - ctr;
		float rr = length(rv);
		float ang = atan(rv.y, rv.x);
		float ring = abs(fract((rr * (1.0 + 0.08 * sin(ang * 3.0)) + ang * 0.0045) * 22.0) - 0.5) / 22.0;   // the spiral
		if (rr < 0.26 && rr > 0.02) wd = min(wd, ring);
		float px1 = 1.4 / res.y;
		float th = smoothstep(px1 * 1.1, 0.0, wd) * (rr < 0.34 ? 1.0 : 0.0) * web;
		float wa = th * mix(0.25, 0.75, web_lit);
		vec3 wc = vec3(0.92, 0.94, 0.96) * mix(0.6, 1.6, web_lit);
		float na3 = wa + al * (1.0 - wa);
		c = (wc * wa + c * al * (1.0 - wa)) / max(na3, 0.0001);
		al = na3;
	}
	// low sun: a bright veil (less contrast), the sun as a big spot, ghosts along the line through the middle; branches in
	// front of the sun make the light flicker (a classic cause of false alarms)
	if (glare > 0.0) {
		vec2 asp = vec2(res.x / res.y, 1.0);
		float fl = 0.75 + 0.25 * sin(TIME * 2.3) * sin(TIME * 3.7 + 1.0) * (0.4 + sway);
		float g = glare * fl;
		float ds = length((uv - glare_pos) * asp);
		float sun = smoothstep(0.32, 0.0, ds) * 0.9 + 0.25;
		vec2 axis = vec2(0.5) - glare_pos;
		float gh = 0.0;
		for (int k = 1; k < 4; k++) {
			vec2 gp = glare_pos + axis * (0.55 * float(k));
			gh += smoothstep(0.05 + 0.02 * float(k), 0.0, length((uv - gp) * asp)) * 0.35;
		}
		float ga2 = clamp((sun + gh) * g, 0.0, 0.92);
		vec3 gc2 = vec3(1.0, 0.93, 0.78);
		float na4 = ga2 + al * (1.0 - ga2);
		c = (gc2 * ga2 + c * al * (1.0 - ga2)) / max(na4, 0.0001);
		al = na4;
	}
	if (fogged > 0.0) {
		float fv = fogged * (0.32 + 0.38 * smoothstep(0.1, 0.75, d)) * (0.9 + 0.1 * sin(TIME * 0.3));
		vec3 fc = vec3(0.86, 0.88, 0.9) * max(0.25, expo);
		float na5 = fv + al * (1.0 - fv);
		c = (fc * fv + c * al * (1.0 - fv)) / max(na5, 0.0001);
		al = na5;
	}
	if (dirt > 0.0) {
		vec2 grid2 = uv * vec2(14.0, 8.0);
		vec2 id2 = floor(grid2);
		vec2 f2 = fract(grid2) - 0.5;
		float r2 = h(id2 + 11.0);
		float on2 = step(r2, dirt * 0.16);
		float da2 = smoothstep(0.32 * (0.5 + h(id2 + 2.0)), 0.05, length(f2 - (vec2(h(id2 + 4.0), h(id2 + 6.0)) - 0.5) * 0.4)) * on2 * 0.55;
		vec3 dc2 = vec3(0.32, 0.27, 0.2);
		float na6 = da2 + al * (1.0 - da2);
		c = (dc2 * da2 + c * al * (1.0 - da2)) / max(na6, 0.0001);
		al = na6;
	}
	ALBEDO = c;
	ALPHA = clamp(al, 0.0, 1.0);
}
