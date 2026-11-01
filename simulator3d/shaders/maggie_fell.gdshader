// Maggies Fell (maggie_modell.gd, Daniel 01.11.2026): Muster aus den Vertex-Farben (werkzeuge/maggie_modell.py),
// kurze Haare als feines, in Strichrichtung gestrecktes Rauschen (Farbe und Normale), leichtes Randlicht (Gegenlicht im
// Fell). Die Ruhelage jedes Punkts steht in UV / UV2.x: die Struktur klebt am Fell und wandert nicht mit der Bewegung.
shader_type spatial;
render_mode cull_back, diffuse_burley, specular_schlick_ggx;

uniform float fein = 1.0;          // 0 = ohne Haarstruktur (Lite)
uniform float haar = 48.0;         // Haare pro Modell-Einheit quer zum Strich (1 Einheit ≈ 13 cm)
uniform float relief = 0.0012;     // Höhe der Haarstruktur (m) für die Normale
uniform float rand = 0.35;         // Randlicht

varying vec3 rest;

float hash(vec3 p) {
	p = fract(p * 0.3183099 + vec3(0.1, 0.2, 0.3));
	p *= 17.0;
	return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
}

float vnoise(vec3 x) {
	vec3 i = floor(x);
	vec3 f = fract(x);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
			mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}

void vertex() {
	rest = vec3(UV.x, UV.y, UV2.x);
}

void fragment() {
	vec3 base = COLOR.rgb;           // Godot liefert die Vertex-Farbe des GLB schon linear
	// Haarstrich: am Rumpf nach hinten (Modell -z), an den Beinen nach unten - gestreckt entlang dieser Richtung
	vec3 p = rest;
	float leg = smoothstep(1.35, 1.1, p.y);
	vec3 q = mix(vec3(p.x * haar, p.y * haar, p.z * haar * 0.18), vec3(p.x * haar, p.y * haar * 0.18, p.z * haar), leg);
	float n = vnoise(q) * 0.65 + vnoise(q * 2.13 + 7.1) * 0.35;
	// in der Ferne ausblenden (sonst flimmert es)
	float fw = length(fwidth(rest)) * haar;
	float k = fein * (1.0 - smoothstep(0.4, 1.2, fw));
	ALBEDO = base * (1.0 + (n - 0.5) * 0.12 * k);
	ROUGHNESS = 0.82;
	SPECULAR = 0.32;
	// Normale: Mikkelsen-Bump aus dem Rauschen (ohne Tangenten)
	if (k > 0.001) {
		vec3 sx = dFdx(VERTEX);
		vec3 sy = dFdy(VERTEX);
		float hx = dFdx(n);
		float hy = dFdy(n);
		vec3 r1 = cross(sy, NORMAL);
		vec3 r2 = cross(NORMAL, sx);
		float det = dot(sx, r1);
		vec3 grad = sign(det) * (hx * r1 + hy * r2);
		NORMAL = normalize(abs(det) * NORMAL - grad * relief * k);
	}
	RIM = rand;
	RIM_TINT = 0.55;
}
