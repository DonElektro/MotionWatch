// Ground of the «Ferienpark am See» (ferienpark.gd, 3D-4.x): a painted ground map (meadow, sand, gravel paths, pitches,
// forest floor) in the coordinates of the park node (the park is turned and moved so that MoveEye stands at the origin),
// with a fine pattern near the camera, snow and wet ground like the meadow and the terrain of a real place.
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D photo : source_color, filter_linear_mipmap, repeat_disable;
uniform vec4 rect = vec4(-320.0, -320.0, 640.0, 640.0);   // x0, z0, width, depth (park metres)
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
	vec3 c = texture(photo, uv).rgb;
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
}
