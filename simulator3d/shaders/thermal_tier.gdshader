// Wärmebild der Tier-Modelle mit Skelett (tier_modell.gd, Paket 3 «Tiere echt»): der Zwilling hat dasselbe Netz und
// dieselbe Haut wie das sichtbare Modell, die Temperatur kommt aus der Ruhelage des Punkts (UV / UV2.x) und seiner
// Wärme-Klasse (UV2.y, werkzeuge/tier_modelle.py: 0 Fell, 1 Auge, 2 Nase, 3 kühl – Stacheln, Hufe).
// Rumpf, Kopf, Beine, Augen: dieselben Werte wie bisher die Grundformen (actor.gd, waerme.gd) – das Tier ist so warm wie
// vorher, nur die Form stimmt jetzt mit dem sichtbaren Tier überein. Geschrieben wie thermal.gdshader (14-bit-Code).
shader_type spatial;
render_mode unshaded, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/thermal_inc.gdshaderinc"

uniform float spread = 0.6;
uniform float t_rumpf = 25.0;
uniform float t_kopf = 27.0;
uniform float t_beine = 21.0;
uniform float t_auge = 36.5;
uniform float t_kuehl = 17.0;
uniform float kopf_z = 99.0;       // Modell-Einheiten (Ruhelage)
uniform float kopf_y = 99.0;
uniform float bein_y = 0.0;
uniform float schwanz_z = -99.0;
uniform float einheit = 0.17;      // m pro Modell-Einheit (für weiche Übergänge von etwa 4 cm)

varying vec3 rest;
varying float klasse;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }

void vertex() {
	rest = vec3(UV.x, UV.y, UV2.x);
	klasse = UV2.y;
}

void fragment() {
	vec3 w = (INV_VIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float n = (hash(floor(w.xz * 2.0)) - 0.5) * spread;
	float b = 0.04 / einheit;
	float t = t_rumpf;
	float kopf = smoothstep(kopf_z - b, kopf_z + b, rest.z) * smoothstep(kopf_y - b * 2.0, kopf_y + b, rest.y);
	float bein = smoothstep(bein_y + b, bein_y - b, rest.y) * (1.0 - kopf);
	float schw = smoothstep(schwanz_z + b, schwanz_z - b, rest.z) * (1.0 - bein);
	t = mix(t, t_kopf, kopf);
	t = mix(t, t_beine, bein);
	t = mix(t, t_kuehl, schw * 0.7);
	if (klasse > 0.5 && klasse < 1.5) {
		t = t_auge;
	} else if (klasse > 1.5 && klasse < 2.5) {
		t = t_kopf - 2.5;                    // die feuchte Nase ist kühler als das Gesicht
	} else if (klasse > 2.5) {
		t = t_kuehl;
	}
	ALBEDO = th_encode(th_atm(t + n, length(VERTEX)));
}
