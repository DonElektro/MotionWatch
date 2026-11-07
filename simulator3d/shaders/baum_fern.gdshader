// «Flora und Fauna» Paket 1 (scripts/baeume.gd): a tree far away = one flat picture that turns to the camera (round the
// upright axis). Picture (texturen/flora_fern_<art>.png, werkzeuge/flora_fernbilder.gd): R = brightness of the leaves,
// G = 1 where leaves are in front, B = brightness of the bark (bark behind the leaves too: shows when bare), A = cover.
// INSTANCE_CUSTOM.xyz = from the foot to the centre of the crown (near / far switch like the cards), .w = crown material index.
// Instance scale: x = size (negative = mirrored), y = height factor.
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;

uniform sampler2D imp_tex : filter_linear_mipmap, repeat_disable;
uniform sampler2D noise_tex;
uniform vec4 cols[16] : source_color;
uniform vec4 states[16];
uniform vec4 bark_col : source_color = vec4(0.4, 0.3, 0.2, 0.0);
uniform vec2 size = vec2(5.0, 7.0);
uniform float near_d = 45.0;
uniform float wind = 0.0;
uniform float cloud_amt = 0.0;
uniform vec2 cloud_off = vec2(0.0);

varying vec3 wpos;
varying vec3 v_col;
varying float v_bare;
varying float v_bl;
varying vec3 v_n;

void vertex() {
	vec3 foot = (MODEL_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	float sx = length(MODEL_MATRIX[0].xyz);
	float flip = sign(dot(MODEL_MATRIX[0].xyz, vec3(1.0, 0.0, 0.0)) + 1e-4);
	float sy = length(MODEL_MATRIX[1].xyz);
	int k = clamp(int(INSTANCE_CUSTOM.w + 0.5), 0, 15);
	v_col = cols[k].rgb;
	v_bare = states[k].x;
	v_bl = states[k].y;
	vec3 cw = foot + INSTANCE_CUSTOM.xyz;
	vec3 to_cam = CAMERA_POSITION_WORLD - foot;
	to_cam.y = 0.0;
	to_cam = length(to_cam) > 0.01 ? normalize(to_cam) : vec3(0.0, 0.0, 1.0);
	vec3 right = normalize(cross(vec3(0.0, 1.0, 0.0), to_cam));
	float a = wind / 60.0;
	float sway = sin(TIME * (1.2 + a) + foot.x * 0.37 + foot.z * 0.21) * a * 0.5 * VERTEX.y * VERTEX.y;
	vec3 w = foot + right * (VERTEX.x * size.x * sx * flip) + vec3(0.0, VERTEX.y * size.y * sy, 0.0) + right * sway;
	if (length(cw - CAMERA_POSITION_WORLD) <= near_d) {
		w = foot;                                   // near: the real tree
	}
	wpos = w;
	v_n = normalize(to_cam + right * VERTEX.x * 1.4 + vec3(0.0, 0.25, 0.0));
	VERTEX = (inverse(MODEL_MATRIX) * vec4(w, 1.0)).xyz;
}

void fragment() {
	vec4 t = texture(imp_tex, UV);
	if (t.a < 0.42) {
		discard;
	}
	vec3 col;
	float leaf = step(0.5, t.g);
	if (leaf > 0.5 && v_bare > 0.0 && texture(noise_tex, UV * vec2(3.0, 5.0) + wpos.xz * 0.05).r < v_bare * 1.02) {
		leaf = 0.0;                                 // autumn / winter: the leaves go, the bark behind them shows
		if (t.b < 0.04) {
			discard;
		}
	}
	if (leaf > 0.5) {
		col = v_col * t.r * 2.1;
		if (v_bl > 0.0 && texture(noise_tex, UV * 9.0 + wpos.xz * 0.1).r > 1.0 - 0.45 * v_bl) {
			col = vec3(0.86, 0.8, 0.8) * t.r * 1.6;
		}
	} else {
		col = bark_col.rgb * max(t.b, 0.2) * 1.8;
	}
	col *= 1.0 - cloud_amt * smoothstep(0.52, 0.68, texture(noise_tex, (wpos.xz + cloud_off) * 0.0035).r);
	ALBEDO = col;
	NORMAL = normalize((VIEW_MATRIX * vec4(v_n, 0.0)).xyz);
	ROUGHNESS = 0.9;
	SPECULAR = 0.2;
	BACKLIGHT = col * 0.1;
}
