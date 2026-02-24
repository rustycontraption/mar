//glsl

#version 330

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform float wave_time;
uniform float swell_amplitude;
uniform float swell_period;
uniform float swell_wavelength;
uniform float swell_dir_x;
uniform float swell_dir_y;
uniform float swell_wavelength_offset;
uniform float swell_amplitude_offset;
uniform float swell_period_offset;
uniform float swell_x_offset;
uniform float swell_y_offset;
uniform float swell_sharpness;

float chopAmplitude = .1;
float chopPeriod = 3;
//float chopWavelength = 1.56 * (chopPeriod * chopPeriod);
float chopWavelength = 10;
float chopDirX = 0;
float chopDirY = 0;


in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec4 p3d_Color;

out float swellAmplitudeFactor;
out float chopAmplitudeFactor;

vec3 gerstnerWave(vec2 position, float wavelength, float amplitude,
                  float period, vec2 direction, float sharpness, float time) {
    float wave_number = 2.0 * 3.14159265 / wavelength;
    float angular_freq = 2.0 * 3.14159265 / period;
    vec2 d = normalize(direction);
    float wave_phase = wave_number * dot(d, position) - angular_freq * time;

    float x = d.x * amplitude * cos(wave_phase) * sharpness;
    float y = d.y * amplitude * cos(wave_phase) * sharpness;
    float z = amplitude * sin(wave_phase);

    return vec3(x, y, z);
}

vec3 swell_displacement(vec3 position, vec3 displacement) {
    displacement += gerstnerWave(
        position.xy,
        swell_wavelength,
        swell_amplitude,
        swell_period,
        vec2(swell_dir_x, swell_dir_y),
        swell_sharpness,
        wave_time
    );

    displacement += gerstnerWave(
        position.xy,
        swell_wavelength * swell_wavelength_offset,
        swell_amplitude * swell_amplitude_offset,
        swell_period * swell_period_offset,
        vec2(swell_dir_x * swell_x_offset, swell_dir_y * swell_y_offset),
        swell_sharpness,
        wave_time
    );
    
    return displacement;
}

vec3 chop_displacement(vec3 position, vec3 displacement) {
    chopAmplitude = chopAmplitude + swell_amplitude / 16;
    displacement += gerstnerWave(
        position.xy,
        chopWavelength,
        chopAmplitude,
        chopPeriod,
        vec2(7.0, 3.0),
        0.0,
        wave_time
    );

    displacement += gerstnerWave(
        position.xy,
        chopWavelength * 1.1,
        chopAmplitude * 1.1,
        chopPeriod * 2,
        vec2(5.0, -2.0),
        0.0,
        wave_time
    );

    displacement += gerstnerWave(
        position.xy,
        chopWavelength * 1.5,
        chopAmplitude * 0.8,
        chopPeriod * 3,
        vec2(-8.0, 4.0),
        0.0,
        wave_time
    );

    displacement += gerstnerWave(
        (position + displacement).xy,
        chopWavelength * 0.9,
        chopAmplitude * 0.5,
        chopPeriod * 1.3,
        vec2(6.0, 6.0),
        0.0,
        wave_time
    );

    return displacement;
}

void main() {
    vec3 position = p3d_Vertex.xyz;
    vec3 displacement = vec3(0.0);
    vec3 chopDisplacement = vec3(0.0);
    
    displacement = swell_displacement(position, displacement);
    
    chopDisplacement = chop_displacement(position, chopDisplacement);


    vec3 finalDisplacement = chopDisplacement + displacement;
    vec3 finalPosition = position + finalDisplacement;
    gl_Position = p3d_ModelViewProjectionMatrix * vec4(finalPosition, 1.0);
    
    float swellTotalAmplitude = swell_amplitude * (1.0 + swell_amplitude_offset);
    swellAmplitudeFactor = (swellTotalAmplitude > 0.0) ? clamp((finalDisplacement.z + swellTotalAmplitude) / (2.0 * swellTotalAmplitude), 0.0, 1.0) : 0.5;
    
    //chopAmplitudeFactor = clamp((chopDisplacement.z + chopAmplitude) / (2.0 * chopAmplitude), 0.0, 1.0);
}


