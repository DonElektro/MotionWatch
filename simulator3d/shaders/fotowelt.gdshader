// 3D-4.27 Foto-Modus: the real photo(s) of the place on a big sphere round the MoveEye camera (fotomodus.gd).
// Opaque and far away: the simulated figures stand in front, the soft shadows are drawn into the photo (foto.gdshaderinc).
shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;

#include "res://shaders/foto.gdshaderinc"

varying vec3 wp;

void vertex() {
	wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	ALBEDO = foto_bg(normalize(wp - foto_eye)).rgb;
}
