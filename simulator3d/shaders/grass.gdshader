// Meadow: patches of greener and drier grass, finer pattern near the camera.
shader_type spatial;

uniform vec4 grass : source_color = vec4(0.22, 0.42, 0.16, 1.0);
uniform vec4 dry : source_color = vec4(0.45, 0.47, 0.25, 1.0);
uniform vec4 snow : source_color = vec4(0.93, 0.94, 0.96, 1.0);
uniform float snow_amount = 0.0;
uniform float wet = 0.0;
uniform float puddle = 0.0;           // 3D-3.98: puddles in the hollows after long rain (0 … 1)
uniform sampler2D noise_tex;

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float big = texture(noise_tex, w.xz * 0.012).r;
	float mid = texture(noise_tex, w.xz * 0.09).r;
	float fine = texture(noise_tex, w.xz * 0.9).r;
	vec3 c = mix(grass.rgb, dry.rgb, smoothstep(0.45, 0.75, big));
	c *= 0.75 + 0.35 * mid + 0.25 * (fine - 0.5);
	c = mix(c, snow.rgb * (0.92 + 0.08 * fine), snow_amount);
	float pd = puddle * smoothstep(0.34, 0.26, big + 0.15 * (mid - 0.5)) * (1.0 - snow_amount);
	ALBEDO = mix(c * (1.0 - 0.35 * wet), vec3(0.05, 0.055, 0.06), pd);
	ROUGHNESS = mix(mix(0.95, 0.35, wet), 0.04, pd);
	SPECULAR = mix(0.5, 0.9, pd);
}
