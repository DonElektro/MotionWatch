// Walls of the houses at a real place (3D-3.4): plaster colour × facade picture (windows, shutters); at night some
// windows glow (own shader: the Compatibility renderer lit the whole wall with an emission texture).
shader_type spatial;

uniform vec4 color : source_color = vec4(0.93, 0.91, 0.86, 1.0);
uniform sampler2D facade : source_color, filter_linear_mipmap;
uniform sampler2D lit : source_color, filter_linear_mipmap;
uniform float night = 0.0;

void fragment() {
	ALBEDO = color.rgb * texture(facade, UV).rgb;
	EMISSION = texture(lit, UV).rgb * night;
	ROUGHNESS = 0.9;
}
