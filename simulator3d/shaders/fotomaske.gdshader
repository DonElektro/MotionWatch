// 3D-4.27 Foto-Modus: a part of the photo painted «vorne» (hedge, tent ...): drawn again at its own distance (fotomodus.gd),
// opaque - figures behind it are hidden, figures in front of it stay visible (depth test).
shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/foto.gdshaderinc"

uniform sampler2D mask_t : filter_linear, repeat_disable;
uniform int mask_i = 0;              // which photo the mask belongs to

varying vec3 wp;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 d = normalize(wp - foto_eye);
	vec2 uv = mask_i == 0 ? foto_uv(foto_b0, foto_p0, d) : (mask_i == 1 ? foto_uv(foto_b1, foto_p1, d) : foto_uv(foto_b2, foto_p2, d));
	if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0 || texture(mask_t, uv).r < 0.5) {
		discard;
	}
	ALBEDO = foto_bg(d).rgb;
}
