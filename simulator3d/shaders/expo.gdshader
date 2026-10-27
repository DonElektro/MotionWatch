// exposure of a camera at night (from 3D-2.9): multiplies the picture behind it (blend_mul) - darker at night with limited
// amplification. Unlike reading the screen texture, this keeps transparent things (rain, smoke, fireflies) in the picture.
shader_type spatial;
render_mode unshaded, blend_mul, depth_test_disabled, depth_draw_never, cull_disabled, shadows_disabled;

uniform float expo = 1.0;

void fragment() {
	ALBEDO = vec3(clamp(expo, 0.0, 1.0));
}
