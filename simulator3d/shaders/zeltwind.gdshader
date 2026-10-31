// Paket «Wetter physikalisch» (real-wetter): Zeltwände im Wind. Die Plane eines Zelts (PrismMesh, unterteilt) beult zwischen
// Boden, First und den Giebeln aus und flattert mit den Böen; Boden, First und Ecken bleiben fest (dort ist sie gespannt).
// Der Takt kommt aufsummiert aus dem Wind («phase», wetter.gd), die Stärke aus «wind» (km/h mit Böen, main.gd).
// Nass (nach dem Regen) wird der Stoff dunkler und glänzt.
shader_type spatial;
render_mode cull_disabled;

uniform vec4 color : source_color = vec4(0.9, 0.5, 0.15, 1.0);
uniform vec3 half_size = vec3(1.3, 0.75, 1.2);     // halbe Grösse des Prismas
uniform float wind = 10.0;
uniform float phase = -1.0;
uniform float seed = 0.0;
uniform float wet = 0.0;

void vertex() {
	float t = phase >= 0.0 ? phase : TIME * 1.5;
	float s = clamp((VERTEX.y + half_size.y) / (2.0 * half_size.y), 0.0, 1.0);   // 0 Boden, 1 First
	float zz = clamp(VERTEX.z / half_size.z, -1.0, 1.0);
	float wgt = 4.0 * s * (1.0 - s) * (1.0 - 0.85 * zz * zz);           // fest an Boden, First und Giebeln
	float amp = clamp(wind / 60.0, 0.0, 1.6) * 0.07;
	float fl = 0.55 * sin(t * 1.7 + seed + zz * 1.6) + 0.3 * sin(t * 4.3 + seed * 2.0 + s * 3.0) + 0.15 * sin(t * 9.1 + zz * 5.0);
	float press = -0.45 * sign(NORMAL.x);                                // die Seite im Wind wird eingedrückt, die andere bläht
	VERTEX += NORMAL * amp * wgt * (fl + press * (0.6 + 0.4 * sin(t * 0.7 + seed)));
}

void fragment() {
	ALBEDO = color.rgb * (1.0 - 0.2 * wet);
	ROUGHNESS = mix(0.85, 0.35, wet);
	SPECULAR = mix(0.4, 0.6, wet);
}
