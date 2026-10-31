// Bergsee im «Bergtal» (bergtal_landschaft.gd, «wie auf den Fotos», nicht in Lite): türkis bis smaragdgrün, in der Tiefe
// dunkel, am flachen Ufer hell und klar mit sichtbarem Grund (Steine, Sand) und leicht grünlichem Rand, dazu die
// Spiegelung von Wald und Fels ringsum. Die Spiegelung kommt aus einem Horizont-Profil des Sees (128 Richtungen: Farbe des
// Landes und sein Höhenwinkel, einmal berechnet) - keine zweite Kamera. Der Himmel im Spiegel kommt wie bisher von der
// Umgebung (Glanz). Ohne TIME: die Oberfläche bewegt sich nicht (keine Bewegung für MoveEye).
// UV.x = wie weit draussen (0 Mitte … 1 Ufer), VERTEX in Tal-Koordinaten.
shader_type spatial;
render_mode cull_back;

uniform sampler2D noise_tex : repeat_enable, filter_linear_mipmap;
uniform sampler2D horizon : repeat_enable, filter_linear;
uniform float spring = 0.0;          // Schmelzwasser: etwas milchiger

varying vec3 lpos;
varying vec3 lcam;
varying float e;

void vertex() {
	lpos = VERTEX;
	e = UV.x;
	lcam = (inverse(MODEL_MATRIX) * vec4(CAMERA_POSITION_WORLD, 1.0)).xyz;
}

void fragment() {
	vec3 v = normalize(lcam - lpos);                       // to the camera (valley coordinates)
	float cosv = clamp(v.y, 0.0, 1.0);
	float rn = texture(noise_tex, lpos.xz * 0.35).r - 0.5;
	float rn2 = texture(noise_tex, lpos.xz * 0.09 + vec2(0.3)).r - 0.5;
	// the mirror: the reflected ray, a little wobbly (small waves, standing still)
	vec3 r = vec3(-v.x, v.y, -v.z);
	r.xz += vec2(rn, rn2) * 0.035;
	float az = atan(r.x, r.z);
	float el = asin(clamp(r.y, -1.0, 1.0)) / 1.5707963;
	vec4 hz = texture(horizon, vec2(az / 6.2831853 + 0.5, 0.5));
	float tips = (texture(noise_tex, vec2(az * 3.0, 0.37)).r - 0.5) * 0.025;   // tree tops: a jagged edge
	float land = smoothstep(hz.a + tips + 0.006, hz.a + tips - 0.006, el);
	// the water: deep dark emerald, then turquoise, near the shore clear with the bottom
	float sh = smoothstep(0.7, 0.97, e);
	float bt = texture(noise_tex, lpos.xz * 0.22).r;
	float bt2 = texture(noise_tex, lpos.xz * 0.9).r;
	vec3 bed = mix(vec3(0.16, 0.17, 0.11), vec3(0.42, 0.41, 0.32), smoothstep(0.42, 0.68, bt));        // stones, sand, mud
	bed *= 0.8 + 0.4 * bt2;
	vec3 deep = vec3(0.004, 0.06, 0.055);
	vec3 turq = vec3(0.01, 0.2, 0.17);
	vec3 body = mix(deep, turq, smoothstep(0.35, 0.85, e));
	body = mix(body, vec3(0.06, 0.2, 0.19), spring * 0.5);
	float see = sh * (0.3 + 0.7 * cosv);
	body = mix(body, bed * vec3(0.55, 0.75, 0.6), see * 0.85);
	body = mix(body, vec3(0.1, 0.22, 0.06), smoothstep(0.94, 1.0, e) * 0.35);        // green rim (algae, grass under water)
	// how much mirror (Fresnel), stronger at a flat view - like the photos: forest and rock mirrored in the lake
	float F = 0.03 + 0.97 * pow(1.0 - cosv, 5.0);
	F = clamp(F * 1.15 + 0.08, 0.0, 1.0);
	vec3 lc = pow(hz.rgb, vec3(2.2)) * 0.65;
	ALBEDO = mix(body, lc, F * land);
	ROUGHNESS = 0.03 + 0.03 * abs(rn);
	METALLIC = 0.0;
	SPECULAR = 0.5 * (1.0 - land);                           // where the land is in the mirror: no sky in it
}
