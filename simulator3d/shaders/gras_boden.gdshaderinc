// «Flora und Fauna» Paket 2 (scripts/gras.gd Gras.boden): the meadow on the big ground shaders (world maps terrain.gdshader,
// Ferienpark / kompakt ferienpark_boden.gdshader, Bergtal bergtal_boden.gdshader). p2 = 0: nothing changes (Lite, alt).
//   - near (near_k > 0): the owner's close-up meadow photo on the green parts, tinted to the colour there (photo / its mean)
//   - far ring: grass texture and flower speckles where no grass clumps stand
//   - gust sheen: the same wave as grass blades and crowns (wind_fx.gd sets wind, gust_amt, dir)
uniform float p2 = 0.0;
uniform sampler2D p2_wiese : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float p2_scale = 0.3;
uniform float wind = 0.0;
uniform float gust_amt = 0.0;
uniform vec2 dir = vec2(0.8, 0.6);

vec3 p2_boden(vec3 c, vec2 wxz, float dc, float green, float near_k, sampler2D nz) {
	if (p2 <= 0.0) {
		return c;
	}
	float nf = green * near_k * (1.0 - smoothstep(20.0, 60.0, dc));
	if (nf > 0.001) {
		vec3 tp = texture(p2_wiese, wxz * p2_scale).rgb;
		vec3 tm = textureLod(p2_wiese, vec2(0.5), 12.0).rgb;
		c = mix(c, c * tp / max(tm, vec3(0.02)), nf * 0.85);
	}
	float ff = smoothstep(8.0, 30.0, dc) * green;
	float fn = texture(nz, wxz * 2.3).r;
	c *= mix(1.0, 0.82 + 0.32 * fn, ff * 0.6);
	float fl = texture(nz, wxz * 1.1 + 5.3).r;
	float pat = smoothstep(0.5, 0.78, texture(nz, wxz * 0.05 + 1.7).r);
	float dots = smoothstep(0.84, 0.9, fl) * pat * ff;
	vec3 fcol = fract(fl * 37.0) < 0.5 ? vec3(0.92, 0.92, 0.86) : vec3(0.92, 0.78, 0.2);
	c = mix(c, fcol * 0.8, dots * 0.5);
	if (gust_amt > 0.0) {
		float g = smoothstep(0.3, 0.8, texture(nz, (wxz - dir * TIME * (0.6 + wind * 0.03)) * 0.02).r);
		c *= 1.0 + 0.1 * g * gust_amt * clamp(wind / 25.0, 0.0, 1.0) * green;
	}
	return c;
}
