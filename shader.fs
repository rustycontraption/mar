//glsl

#version 330

in float swellAmplitudeFactor;
in float chopAmplitudeFactor;
out vec4 fragColor;

void main() {
    float steps = 4.0;
    float edgeSmooth = 0.2; 
    float steppedHeight = floor(swellAmplitudeFactor * steps) / steps
        + smoothstep(1.0 - edgeSmooth, 1.0, fract(swellAmplitudeFactor * steps)) / steps;
    float crest = smoothstep(0.82, 0.88, steppedHeight);
    float base_r = 0.05 + 0.15 * steppedHeight;
    float base_g = 0.15 + 0.20 * steppedHeight;
    float base_b = 0.40 + 0.35 * steppedHeight;
    float r = base_r + (0.9 - base_r) * crest;
    float g = base_g + (0.9 - base_g) * crest;
    float b = base_b + (0.9 - base_b) * crest;

    vec3 swellColor = vec3(r, g, b);

    // Chop layer
    float chopSteps = 2.0;
    float chopEdgeSmooth = 0.18;
    float chopSteppedHeight = floor(chopAmplitudeFactor * chopSteps) / chopSteps
        + smoothstep(1.0 - chopEdgeSmooth, 1.0, fract(chopAmplitudeFactor * chopSteps)) / chopSteps;
    float chopCrest = smoothstep(0.75, 0.85, chopSteppedHeight);
    float chop_base_r = 0.10 + 0.10 * chopSteppedHeight;
    float chop_base_g = 0.18 + 0.18 * chopSteppedHeight;
    float chop_base_b = 0.32 + 0.25 * chopSteppedHeight;
    float chop_r = chop_base_r + (0.8 - chop_base_r) * chopCrest;
    float chop_g = chop_base_g + (0.8 - chop_base_g) * chopCrest;
    float chop_b = chop_base_b + (0.8 - chop_base_b) * chopCrest;
    vec3 chopColor = vec3(chop_r, chop_g, chop_b);

    // Blend layers: chop is more visible at crests, less at troughs
    float blendFactor = 0.5 * chopAmplitudeFactor + 0.2 * crest;
    vec3 finalColor = mix(swellColor, chopColor, blendFactor);
    fragColor = vec4(swellColor, 1.0);

}
