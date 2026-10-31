// 3D-4.x «Vier kompakte Szenen» (kompakt.gd): the painted ground of a compact place INSIDE a world (Bergtal, Ferienpark) -
// only the painted parts (paths, plazas, worn grass, yards) lie on the flat area of the world; where nothing is painted
// (alpha 0) the ground of the world shows. Same look as ferienpark_boden.gdshader (fine pattern, snow, wet, puddles).
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D photo : source_color, filter_linear_mipmap, repeat_disable;
uniform vec4 rect = vec4(-64.0, -64.0, 128.0, 128.0);   // x0, z0, width, depth (place metres)
uniform sampler2D noise_tex;
uniform vec4 snow : source_color = vec4(0.93, 0.94, 0.96, 1.0);
uniform float snow_amount = 0.0;
uniform float wet = 0.0;
uniform float puddle = 0.0;
uniform float detail = 1.0;

varying vec3 lpos;
varying vec3 wpos;

void vertex() {
	lpos = VERTEX;
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 uv = (lpos.xz - rect.xy) / rect.zw;
	vec4 t = texture(photo, uv);
	vec3 c = t.rgb;
	float fine = texture(noise_tex, wpos.xz * 0.9).r;
	float mid = texture(noise_tex, wpos.xz * 0.11).r;
	float big = texture(noise_tex, wpos.xz * 0.013).r;
	float green = smoothstep(0.0, 0.06, c.g - max(c.r, c.b) * 0.95);
	float near = detail * (1.0 - smoothstep(40.0, 140.0, length(wpos.xz)));
	c *= 1.0 + near * (0.3 * (fine - 0.5) + 0.25 * (mid - 0.5)) * (0.4 + 0.6 * green) + 0.16 * (big - 0.5);
	c = mix(c, snow.rgb * (0.92 + 0.08 * fine), snow_amount);
	float pd = puddle * smoothstep(0.30, 0.22, texture(noise_tex, wpos.xz * 0.012).r + 0.15 * (mid - 0.5)) * (1.0 - green * 0.6);
	ALBEDO = mix(clamp(c, 0.0, 1.0) * (1.0 - 0.35 * wet), vec3(0.05, 0.055, 0.06), pd);
	ROUGHNESS = mix(mix(0.95, 0.35, wet), 0.04, pd);
	SPECULAR = mix(0.5, 0.9, pd);
	// ragged edge of the painted parts (the ground of the world shows between): alpha scissor, no sorting
	ALPHA = t.a - 0.35 * (fine - 0.5);
	ALPHA_SCISSOR_THRESHOLD = 0.5;
}
