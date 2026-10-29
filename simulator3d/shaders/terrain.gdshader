// Ground of a real place (scene «ort», from 3D-3.3): the aerial picture of swisstopo, with a fine pattern of grass on
// green parts near the camera (the picture has only ~0.4 m per pixel), snow and wet ground like the meadow.
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D photo : source_color, filter_linear_mipmap, repeat_disable;
uniform vec4 rect = vec4(-200.0, -200.0, 400.0, 400.0);   // x0, z0, width, depth (local metres)
uniform sampler2D noise_tex;
uniform vec4 snow : source_color = vec4(0.93, 0.94, 0.96, 1.0);
uniform float snow_amount = 0.0;
uniform float wet = 0.0;
uniform float puddle = 0.0;           // 3D-3.98: puddles after long rain
uniform float detail = 1.0;

varying vec3 wpos;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 uv = (wpos.xz - rect.xy) / rect.zw;
	vec3 c = texture(photo, uv).rgb;
	// aerial pictures are taken in bright sun from above: a bit less contrast, the sun of the simulator makes its own light
	c = mix(vec3(dot(c, vec3(0.3, 0.5, 0.2))), c, 1.15) * 0.82;
	float fine = texture(noise_tex, wpos.xz * 0.9).r;
	float mid = texture(noise_tex, wpos.xz * 0.11).r;
	float green = smoothstep(0.0, 0.06, c.g - max(c.r, c.b) * 0.95);
	float near = detail * (1.0 - smoothstep(30.0, 90.0, length(VERTEX)));
	c *= 1.0 + near * green * (0.35 * (fine - 0.5) + 0.2 * (mid - 0.5));
	c = mix(c, snow.rgb * (0.92 + 0.08 * fine), snow_amount);
	float pd = puddle * smoothstep(0.30, 0.22, texture(noise_tex, wpos.xz * 0.012).r + 0.15 * (mid - 0.5));
	ALBEDO = mix(clamp(c, 0.0, 1.0) * (1.0 - 0.35 * wet), vec3(0.05, 0.055, 0.06), pd);
	ROUGHNESS = mix(mix(0.95, 0.35, wet), 0.04, pd);
	SPECULAR = mix(0.5, 0.9, pd);
}
