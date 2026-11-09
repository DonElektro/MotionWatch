// Roofs of the swisstopo houses (sim-fassaden, fassaden.gd; Normal / Hoch only - Lite keeps b3d.gdshader).
// COLOR = roof colour of this house (from the aerial picture SWISSIMAGE, an OSM tag or a palette), a = 1: flat roof.
// CUSTOM0 = (house seed, kind, ground, eave). Pitched: rows of tiles with a little variation; flat: gravel / membrane.
shader_type spatial;
render_mode cull_disabled;

varying vec3 wpos;
varying vec3 wnrm;
varying vec4 col;
varying vec4 c0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	col = COLOR;
	c0 = CUSTOM0;
}

void fragment() {
	vec3 n = normalize(wnrm);
	vec3 rc = col.rgb;
	float rough = 0.8;
	if (c0.w == 0.0 && c0.z == 0.0) {
		// no roof data: the old look
		float cell = hash(floor(wpos.xz / 14.0));
		rc = mix(vec3(0.5, 0.24, 0.17), vec3(0.33, 0.31, 0.32), step(0.6, cell)) * (0.9 + 0.1 * hash(floor(wpos.xz * 2.0)));
	} else if (col.a > 0.5 || n.y > 0.97) {
		rc *= (0.9 + 0.18 * hash(floor(wpos.xz * 6.0))) * (0.94 + 0.12 * hash(floor(wpos.xz * 0.5) + c0.x * 9.0));
		rough = 0.95;
	} else {
		vec2 hn = normalize(n.xz + vec2(1e-5, 0.0));
		vec2 tg = vec2(-hn.y, hn.x);
		float u = dot(wpos.xz, tg);
		float row = wpos.y / 0.24;
		float ri = floor(row);
		float cu = u / 0.3 + 0.5 * mod(ri, 2.0);
		float tile = hash(vec2(floor(cu), ri) + c0.x * 91.0);
		rc *= (0.78 + 0.22 * smoothstep(0.0, 0.3, fract(row))) * (0.9 + 0.16 * tile);
		rc = mix(rc, vec3(0.33, 0.32, 0.29), 0.16 * hash(floor(wpos.xz * 0.6) + c0.x));   // weathering
		rough = 0.75;
	}
	ALBEDO = rc;
	ROUGHNESS = rough;
}
