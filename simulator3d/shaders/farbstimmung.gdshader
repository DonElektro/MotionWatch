// «Flora und Fauna» Paket 2 (scripts/farbstimmung.gd): colour grading of the FREE VIEW only. A CanvasLayer under the controls in
// the window's viewport (and in the picture tool's viewport): it reads what the 3D view drew. The MoveEye cameras render
// into their own SubViewports - they never see this (checked pixel by pixel, werkzeuge/farbstimmung_pruefen.gd).
shader_type canvas_item;

uniform sampler2D screen : hint_screen_texture, filter_linear_mipmap;
uniform float amt = 1.0;
uniform vec3 tint = vec3(1.0);       // time of day: warm in the golden hour, a little blue at dusk / night
uniform float sat = 1.06;
uniform float contrast = 0.12;       // 0 = none; gentle S-curve
uniform vec3 lift = vec3(0.0);       // shadows a little lifted / tinted
uniform float vign = 0.16;

void fragment() {
	vec3 c0 = texture(screen, SCREEN_UV).rgb;
	vec3 c = c0;
	float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
	c = mix(vec3(l), c, sat);
	c = mix(c, c * c * (3.0 - 2.0 * c), contrast);
	c = c * tint + lift * (1.0 - smoothstep(0.0, 0.5, l));
	vec2 d = SCREEN_UV - 0.5;
	c *= 1.0 - vign * smoothstep(0.25, 0.75, dot(d, d) * 2.2);
	COLOR = vec4(mix(c0, clamp(c, 0.0, 1.0), amt), 1.0);
}
