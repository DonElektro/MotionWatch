// Shared by the thermal shaders (Paket «P2 Wärmebild echt», 31.10.2026).
// 1) The temperature is written with 14 bits over the range of the real module (Waveshare Thermal-90: -40 … +400 °C,
//    0.027 °C steps): red = 128 + high 7 bits, green = 128 + low 7 bits (only the upper half of a channel: the dark end
//    is squeezed by some renderers). Before 3D-4.26 one grey value for -40 … +80 °C (0.47 °C steps, fire = 80 °C).
//    main.gd decode_thermal_img() reads it back. th_srgb_out: the renderer turns the colour into sRGB - write it so that
//    the stored bytes are exact (found out by main._calibrate_thermal()).
// 2) The air between the camera and the surface: a part of the radiation is swallowed and replaced by the air's own
//    (fog, snow, humidity) - transmission tau = exp(-th_atm_k * distance) (thermsensor.gd / waerme.gd air_k()).
// (plain uniforms, set on every thermal material by main.th_reg / th_uniforms - the global shader uniforms of Godot
//  gave wrong values in the Compatibility renderer, 3D-4.26)
uniform float th_atm_k = 0.0;
uniform float th_air = 15.0;
uniform float th_srgb_out = 0.0;

vec3 th_encode(float t) {
	float v = floor(clamp((t + 40.0) / 440.0, 0.0, 1.0) * 16383.0 + 0.5);
	float hi = floor(v / 128.0);
	float lo = v - hi * 128.0;
	vec3 c = vec3(128.0 + hi, 128.0 + lo, 128.0 + hi) / 255.0;
	if (th_srgb_out > 0.5) {
		c = mix(c / 12.92, pow((c + vec3(0.055)) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
	}
	return c;
}

float th_atm(float t, float d) {
	return mix(th_air, t, exp(-th_atm_k * d));
}
