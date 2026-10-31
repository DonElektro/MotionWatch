// F6 (31.10.2026): grass tufts of the meadow bend in the wind (wind_fx.gd). Gusts roll over the meadow as waves in the
// direction of the wind; every tuft moves a little on its own (flutter). The root stays put (only the top bends).
shader_type spatial;
render_mode cull_disabled;

uniform vec4 color : source_color = vec4(0.3, 0.5, 0.18, 1.0);
uniform float wind = 8.0;          // km/h, with gusts (main.wind * main.gust())
uniform float amount = 1.0;        // 0 = still (Lite, switched off)
uniform vec2 dir = vec2(0.8, 0.6); // where the wind blows to (world x, z)
uniform float blade_h = 0.28;      // height of the mesh (PrismMesh: y from -h/2 to h/2)
uniform sampler2D noise_tex;

void vertex() {
	vec3 wp = MODEL_MATRIX[3].xyz;                                   // the tuft (MultiMesh instance)
	float h = clamp(VERTEX.y / blade_h + 0.5, 0.0, 1.0);
	float w = clamp(wind / 50.0, 0.0, 1.6) * amount;
	float spd = 0.6 + wind * 0.03;                                   // gust fronts move faster in strong wind
	float g = texture(noise_tex, (wp.xz - dir * TIME * spd) * 0.035).r;       // gust waves over the meadow
	g = smoothstep(0.3, 0.75, g);
	float flut = sin(TIME * (5.0 + 4.0 * w) + wp.x * 7.1 + wp.z * 5.3) * (0.25 + 0.35 * w);
	float bend = (0.25 + 0.9 * g) * w + flut * w * 0.35;
	vec3 off = vec3(dir.x, 0.0, dir.y) * bend * 0.16 * h * h;
	off.y = -abs(bend) * 0.05 * h * h;                               // bending also makes it a bit lower
	VERTEX += inverse(mat3(MODEL_MATRIX)) * off;
}

void fragment() {
	ALBEDO = color.rgb * (0.8 + 0.3 * UV.y);
	ROUGHNESS = 0.9;
}
