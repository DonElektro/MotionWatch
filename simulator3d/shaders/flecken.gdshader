// F2 «echte Inhalte» (inhalte.gd): ein Fleck ausgetretene Erde (Foto-Textur) auf der Wiese, mit weichem, unregelmässigem Rand.
shader_type spatial;
render_mode depth_draw_opaque, cull_back;

uniform sampler2D alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D nrm : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D noise_tex;
uniform float scale = 0.5;

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float r = length(UV - vec2(0.5)) * 2.0;
	float n = texture(noise_tex, w.xz * 0.35).r;
	float a = 1.0 - smoothstep(0.45, 0.95, r + (n - 0.5) * 0.5);
	ALBEDO = texture(alb, w.xz * scale).rgb;
	NORMAL_MAP = texture(nrm, w.xz * scale).rgb;
	ROUGHNESS = 0.9;
	ALPHA = a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
}
