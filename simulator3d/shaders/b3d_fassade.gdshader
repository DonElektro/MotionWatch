// Walls of the swisstopo houses with a look per house (sim-fassaden, fassaden.gd; Normal / Hoch only - Lite keeps b3d.gdshader).
// Per vertex: COLOR = facade colour (a = kind), CUSTOM0 = (u0 of the flat wall, its length, ground, eave),
// CUSTOM1 = (storey height, Fensterläden 0 none / 1 green / 2 red / 3 brown / 4 grey, house seed, wall seed).
// Everything is drawn here from the position on the wall: windows by storey, shutters, plinth, entrance door, garage doors,
// shop windows, balconies (apartments), wood and wooden balconies (chalets), boards and big doors (barns), cladding (industry).
// Kinds: 0 house, 1 apartments, 2 farm house, 3 chalet, 4 barn, 5 commercial, 6 industrial, 7 garage, 8 church.
shader_type spatial;
render_mode cull_disabled;

uniform float night = 0.0;
varying vec3 wpos;
varying vec3 wnrm;
varying vec4 col;
varying vec4 c0;
varying vec4 c1;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	col = COLOR;
	c0 = CUSTOM0;
	c1 = CUSTOM1;
}

void fragment() {
	vec3 n = normalize(wnrm);
	vec3 alb;
	float rough = 0.9;
	float lit = 0.0;
	if (c0.y < 0.5) {
		// no facade data (a mesh from before / a tiny wall): the old look
		float cell = hash(floor(wpos.xz / 14.0));
		float uu = abs(n.x) > abs(n.z) ? wpos.z : wpos.x;
		vec2 g = vec2(uu / 3.0, wpos.y / 3.0);
		vec2 f = fract(g);
		float w = step(0.3, f.x) * step(f.x, 0.7) * step(0.35, f.y) * step(f.y, 0.85);
		alb = mix(mix(vec3(0.92, 0.9, 0.85), vec3(0.86, 0.8, 0.7), step(0.5, cell)), vec3(0.18, 0.21, 0.25), w);
		lit = w * step(0.72, hash(floor(g) + cell * 7.0));
	} else {
		int k = int(floor(col.a * 16.0));
		vec2 hn = normalize(n.xz + vec2(1e-5, 0.0));
		vec2 tg = vec2(-hn.y, hn.x);
		float len = c0.y;
		float u = clamp(dot(wpos.xz, tg) - c0.x, 0.0, len);
		float y = wpos.y - c0.z;
		float eh = c0.w - c0.z;
		float st = max(2.3, c1.x);
		int shut = int(c1.y + 0.5);
		float hs = c1.z;
		float ws = c1.w;
		alb = col.rgb * (0.97 + 0.05 * hash(floor(wpos.xz * 2.0) + floor(wpos.y * 2.0)));
		// per kind: column spacing, window size, sill
		float spacing = 3.0;
		float winw = 1.1;
		float winh = 1.35;
		float sill = 0.95;
		if (k == 0) { spacing = 2.7 + hs * 0.8; winw = 1.0 + hs * 0.25; }
		else if (k == 1) { spacing = 2.6 + hs * 0.5; winw = 1.3; winh = 1.5; sill = 0.85; }
		else if (k == 2) { spacing = 2.6 + hs * 0.6; winw = 0.9; winh = 1.15; sill = 1.0; }
		else if (k == 3) { spacing = 2.2 + hs * 0.4; winw = 0.85; winh = 1.1; }
		else if (k == 4) { spacing = 5.0; winw = 0.6; winh = 0.6; sill = 2.2; }
		else if (k == 5) { spacing = 3.2 + hs * 0.6; winw = 2.0; winh = 1.8; sill = 0.8; }
		else if (k == 6) { spacing = 1.6; winw = 1.5; winh = 1.0; sill = 0.0; }
		else if (k == 7) { spacing = 3.0; winw = 0.0; winh = 0.0; }
		else { spacing = 4.0; winw = 1.2; winh = 3.2; sill = 2.2; }
		float ncol = max(1.0, floor((len - 0.6) / spacing));
		float cw = len / ncol;
		float ci = floor(u / cw);
		float fu = u - (ci + 0.5) * cw;                    // metres from the middle of the column
		float nfl = max(1.0, floor((eh - 0.4) / st + 0.25));
		float fi = floor(y / st);
		float fv = y - fi * st;                            // metres above the floor of this storey
		bool below = y < eh - 0.25;
		// the surface of the wall
		if (k == 3 && y > st - 0.1) {                      // chalet: wood above the ground floor
			vec3 wood = vec3(0.50, 0.33, 0.20) * (0.85 + 0.3 * hs);
			alb = wood * (0.84 + 0.16 * step(0.1, fract(y * 5.0))) * (0.94 + 0.1 * hash(vec2(floor(y * 5.0), floor(u * 0.5))));
		} else if (k == 4) {                               // barn: vertical boards
			alb = col.rgb * (0.80 + 0.20 * step(0.07, fract(u * 4.0))) * (0.9 + 0.2 * hash(vec2(floor(u * 4.0), hs * 13.0)));
		} else if (k == 6) {                               // industry: corrugated cladding
			alb = col.rgb * (0.86 + 0.14 * abs(sin(y * 31.4)));
			rough = 0.55;
		}
		if (y < 0.45 && k != 4 && k != 6) {
			alb = mix(alb, vec3(0.56, 0.55, 0.53), 0.85);  // plinth
		}
		bool win = false;
		bool frame = false;
		bool shutter = false;
		if (below && fi < nfl && winw > 0.0) {
			float hw = winw * 0.5;
			if (k == 6) {                                  // a band of windows high up
				float yb = max(2.5, eh * 0.55);
				win = y > yb && y < yb + 1.0 && abs(fu) < cw * 0.46;
				frame = y > yb - 0.06 && y < yb + 1.06 && abs(fu) < cw * 0.5 && !win;
			} else if (k == 8) {                           // church: tall windows with a round top
				float top = sill + winh;
				float dy = max(0.0, fv - (top - hw));
				win = fi < 1.0 && abs(fu) < hw && fv > sill && (fu * fu + dy * dy) < hw * hw;
			} else if (hash(vec2(ci + ws * 37.0, fi + hs * 11.0)) > 0.07 || k > 3) {
				bool inw = abs(fu) < hw && fv > sill && fv < sill + winh;
				frame = !inw && abs(fu) < hw + 0.07 && fv > sill - 0.08 && fv < sill + winh + 0.07;
				win = inw;
				shutter = shut > 0 && k <= 3 && fv > sill && fv < sill + winh && abs(fu) >= hw + 0.07 && abs(fu) < hw + 0.07 + hw * 0.92;
			}
		}
		// gable: one small window in the middle above the eave (houses, farm houses, chalets)
		if (!below && k <= 3 && len > 5.0 && abs(u - len * 0.5) < 0.45 && y > eh + 0.5 && y < eh + 1.5) {
			win = true;
		}
		// the ground floor
		if (fi < 1.0 && below) {
			if (k == 7) {                                  // garage doors
				if (abs(fu) < min(cw * 0.42, 1.3) && fv < 2.15 && ws < 0.75) {
					alb = mix(vec3(0.86, 0.86, 0.84), vec3(0.45, 0.46, 0.48), step(0.5, hs)) * (0.84 + 0.16 * step(0.12, fract(fv * 3.3)));
					win = false;
					frame = false;
				}
			} else if (k == 5) {                           // shop windows
				if (abs(fu) < cw * 0.4 && fv > 0.35 && fv < 2.8) { win = true; frame = false; shutter = false; }
			} else if (k == 4) {                           // big barn door
				if (ws < 0.6 && abs(u - len * 0.5) < min(2.2, len * 0.25) && fv < 3.8) {
					alb = vec3(0.30, 0.20, 0.13) * (0.85 + 0.15 * step(0.08, fract(u * 3.0)));
					win = false;
				}
			} else if (k == 6) {                           // loading door
				if (ws < 0.5 && ci == mod(floor(ws * 53.0), ncol) && abs(fu) < 1.6 && fv < 3.6) {
					alb = vec3(0.62, 0.64, 0.66) * (0.85 + 0.15 * step(0.15, fract(fv * 2.5)));
					win = false;
					frame = false;
				}
			} else if (ws < 0.45 && len > 4.0 && ci == mod(floor(ws * 97.0), ncol)) {   // entrance door
				if (abs(fu) < 0.55 && fv < 2.2) {
					alb = mix(vec3(0.38, 0.25, 0.16), vec3(0.22, 0.23, 0.25), step(0.6, hs));
					win = false;
					shutter = false;
					frame = false;
				} else if (abs(fu) < 0.63 && fv < 2.28) {
					alb = vec3(0.9);
					win = false;
					shutter = false;
					frame = false;
				}
			}
		}
		// balconies: apartments on some walls, chalets in wood on the first floor
		if (k == 1 && ws > 0.5 && fi >= 1.0 && below && abs(fu) < cw * 0.46) {
			if (fv < 0.18) { alb = vec3(0.64, 0.64, 0.62); win = false; shutter = false; frame = false; }
			else if (fv < 1.05) {
				alb = mix(vec3(0.30, 0.32, 0.36), alb, 0.3) * (0.8 + 0.2 * step(0.85, fract(fu * 6.0)));
				win = false;
				shutter = false;
				frame = false;
			}
		}
		if (k == 3 && ws > 0.35 && fi > 0.5 && fi < 1.5 && fv < 1.0 && below) {
			alb = mix(vec3(0.42, 0.27, 0.16), vec3(0.58, 0.40, 0.24), step(0.5, fract(u * 5.0)));
			if (fv < 0.15) { alb = vec3(0.33, 0.21, 0.12); }
			win = false;
			shutter = false;
			frame = false;
		}
		if (frame) {
			alb = (k == 2 || k == 3) ? vec3(0.45, 0.30, 0.20) : vec3(0.95, 0.95, 0.93);
		}
		if (shutter) {
			vec3 sc = shut == 1 ? vec3(0.18, 0.38, 0.22) : (shut == 2 ? vec3(0.58, 0.16, 0.12) : (shut == 3 ? vec3(0.40, 0.26, 0.16) : vec3(0.55, 0.57, 0.58)));
			alb = sc * (0.78 + 0.22 * step(0.3, fract(fv * 9.0)));
			rough = 0.8;
		}
		if (win) {
			alb = vec3(0.15, 0.18, 0.22) + 0.04 * hash(vec2(ci, fi + hs * 3.0));
			if (k != 6 && k != 5 && (abs(fu) < 0.03 || abs(fv - sill - winh * 0.62) < 0.03)) {
				alb = vec3(0.9);                           // window bars
			}
			rough = 0.15;
			lit = step(0.7, hash(vec2(ci * 3.1 + fi, hs * 17.0 + ws * 5.0)));
		}
	}
	ALBEDO = alb;
	ROUGHNESS = rough;
	EMISSION = vec3(1.0, 0.75, 0.42) * lit * night;
}
