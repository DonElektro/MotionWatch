// F6 (31.10.2026): tent fabric in the wind (wind_fx.gd). The fabric is held at the bottom (pegs) and at the ridge (pole):
// the slopes between billow in and out with the gusts, in strong wind they flap. Mesh: PrismMesh (y from -h/2 to h/2).
shader_type spatial;

uniform vec4 color : source_color = vec4(0.9, 0.5, 0.15, 1.0);
uniform float wind = 8.0;          // km/h, with gusts
uniform float amount = 1.0;
uniform float tent_h = 1.5;
uniform float seed = 0.0;
uniform sampler2D noise_tex;

void vertex() {
	vec3 wp = MODEL_MATRIX[3].xyz;
	float f = clamp(VERTEX.y / tent_h + 0.5, 0.0, 1.0);
	float belly = sin(f * 3.14159);                                  // 0 at pegs and ridge, most in the middle
	float w = clamp(wind / 45.0, 0.0, 1.8) * amount;
	float g = texture(noise_tex, wp.xz * 0.05 + vec2(TIME * 0.11, TIME * 0.07)).r;
	float t = TIME * (2.2 + 3.5 * w) + seed;
	float s = 0.6 * sin(t + VERTEX.x * 2.3) + 0.4 * sin(t * 1.7 + VERTEX.z * 3.1 + seed);
	float snap = pow(abs(sin(TIME * (0.7 + 0.5 * w) + seed * 1.9)), 6.0) * step(0.7, w);  // strong wind: a slap now and then
	float d = (0.5 * g + s * (0.25 + 0.5 * w) + snap) * w * 0.045 * belly;
	VERTEX += NORMAL * d;
	NORMAL = normalize(NORMAL + vec3(cos(t + VERTEX.x * 2.3), 0.0, sin(t * 1.3 + VERTEX.z * 3.1)) * 0.25 * w * belly);
}

void fragment() {
	ALBEDO = color.rgb;
	ROUGHNESS = 0.75;
}
