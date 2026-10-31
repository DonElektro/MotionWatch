// 3D-4.27 Foto-Modus (fotomodus.gd): the real photo of the place IS the world. Shared by fotowelt.gdshader (the photo
// round the camera), fotomaske.gdshader (painted parts that stand in front) and camfx.gdshader (fits the simulated
// figures to the photo). Up to 3 photos: pinhole (phone photo) or cylinder (panorama), soft blend where they overlap.
// A direction in the world -> the colour of the photo there (.a = how much a photo covers it).
// Soft shadows of the figures on the ground of the photo (a flat plane), drawn into the photo itself.

uniform sampler2D foto_t0 : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D foto_t1 : source_color, filter_linear_mipmap, repeat_disable;
uniform sampler2D foto_t2 : source_color, filter_linear_mipmap, repeat_disable;
uniform int foto_n = 0;
uniform mat3 foto_b0;               // world -> camera of the photo
uniform mat3 foto_b1;
uniform mat3 foto_b2;
uniform vec4 foto_p0 = vec4(0.65, 0.37, 0.0, 0.08);   // pinhole: tan(h/2), tan(v/2), 0, feather · cylinder: span (rad), tan range, 1 (2 = 360°), feather
uniform vec4 foto_p1 = vec4(0.65, 0.37, 0.0, 0.08);
uniform vec4 foto_p2 = vec4(0.65, 0.37, 0.0, 0.08);
uniform vec3 foto_fill = vec3(0.3);  // where no photo is
uniform float foto_k = 1.0;          // brightness (darker at dusk / night)
uniform vec3 foto_eye = vec3(0.0, 1.5, 0.0);
uniform float foto_gy = 0.0;         // height of the ground of the photo
uniform vec4 foto_sh[16];            // shadows: x, z, radius, height (height 0 = none)
uniform int foto_shn = 0;
uniform vec3 foto_sun = vec3(0.0, 0.0, 1.0);   // ground direction the shadows fall (x, z) and length per height (z)
uniform float foto_shk = 0.0;        // 0..1 strength of the shadows

vec2 foto_uv(mat3 b, vec4 p, vec3 d) {
	vec3 q = b * d;
	if (p.z < 0.5) {
		if (q.z > -0.0001) {
			return vec2(-1.0);
		}
		return vec2(0.5 + q.x / (-q.z) / (2.0 * p.x), 0.5 - q.y / (-q.z) / (2.0 * p.y));
	}
	float az = atan(q.x, -q.z);
	float hl = max(length(q.xz), 0.0001);
	float u = 0.5 + az / p.x;
	if (p.z > 1.5) {
		u = fract(u);
	}
	return vec2(u, 0.5 - (q.y / hl) / p.y);
}

float foto_w(vec2 uv, vec4 p) {
	if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) {
		return 0.0;
	}
	vec2 e = min(uv, vec2(1.0) - uv);
	if (p.z > 1.5) {
		e.x = 1.0;                   // a whole panorama has no left / right edge
	}
	return smoothstep(0.0, p.w, e.x) * smoothstep(0.0, p.w * 0.5, e.y) + 0.0001;
}

float foto_shadow(vec3 d) {
	if (foto_shk <= 0.0 || foto_shn <= 0 || d.y > -0.0005) {
		return 1.0;
	}
	float t = (foto_eye.y - foto_gy) / -d.y;
	if (t > 250.0) {
		return 1.0;
	}
	vec2 g = foto_eye.xz + d.xz * t;
	vec2 sd = normalize(foto_sun.xy + vec2(0.00001));
	vec2 sp = vec2(-sd.y, sd.x);
	float s = 0.0;
	for (int i = 0; i < 16; i++) {
		if (i >= foto_shn) {
			break;
		}
		vec4 o = foto_sh[i];
		vec2 r = g - o.xy;
		float len = o.w * foto_sun.z;                      // the sun: long in the evening, short at noon
		float al = dot(r, sd) - len * 0.5;
		float ac = dot(r, sp);
		float e = length(vec2(al / (len * 0.5 + o.z), ac / o.z));
		float cast = (1.0 - smoothstep(0.35, 1.0, e)) * 0.75;
		float foot = 1.0 - smoothstep(0.2, 1.25, length(r) / (o.z * 1.1));   // contact shadow under the feet
		s = max(s, max(cast * clamp(foto_sun.z * 1.5, 0.0, 1.0), foot * 0.8));
	}
	return 1.0 - s * foto_shk;
}

vec4 foto_bg(vec3 d) {
	vec3 c = vec3(0.0);
	float w = 0.0;
	if (foto_n > 0) {
		vec2 uv = foto_uv(foto_b0, foto_p0, d);
		float k = foto_w(uv, foto_p0);
		if (k > 0.0) { c += texture(foto_t0, uv).rgb * k; w += k; }
	}
	if (foto_n > 1) {
		vec2 uv = foto_uv(foto_b1, foto_p1, d);
		float k = foto_w(uv, foto_p1);
		if (k > 0.0) { c += texture(foto_t1, uv).rgb * k; w += k; }
	}
	if (foto_n > 2) {
		vec2 uv = foto_uv(foto_b2, foto_p2, d);
		float k = foto_w(uv, foto_p2);
		if (k > 0.0) { c += texture(foto_t2, uv).rgb * k; w += k; }
	}
	if (w < 0.0005) {
		return vec4(foto_fill * foto_k, 0.0);
	}
	vec3 col = c / w;
	float cov = clamp(w, 0.0, 1.0);
	col = mix(foto_fill, col, cov);
	return vec4(col * foto_k * foto_shadow(d), cov);
}
