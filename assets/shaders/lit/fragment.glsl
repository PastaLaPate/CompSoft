#version 330 core

in vec2 UV;
out vec3 color;

uniform sampler2D positionTexture;
uniform sampler2D normalTexture;
uniform sampler2D colorTexture;
uniform sampler2D selectionTexture;

uniform vec3 cameraPos;
uniform vec2 u_TexelSize;
uniform float time;

struct LightData {
    int type;
    vec3 position;
    vec3 direction;
    vec3 color;
    float intensity;
    float cutoff;
};

layout (std140) uniform LightingBlock {
    LightData u_lights[8];
    int u_active_light_count;
};

void main() {
    // --- Existing Lighting Logic ---
    vec3 pos = texture(positionTexture, UV).rgb;
    vec3 normal = texture(normalTexture, UV).rgb;
    vec3 albedo = texture(colorTexture, UV).rgb;
    float specular = texture(colorTexture, UV).a;

    vec3 EyeDirection = normalize(cameraPos - pos);
    vec3 FragToLight = normalize(u_lights[0].position - pos);

    float theta = clamp(dot(normal, FragToLight), 0, 1);
    float distanceToLight = length(u_lights[0].position - pos);
    float attenuation = 1.0 / (1.0 + 0.1 * distanceToLight + 0.01 * distanceToLight * distanceToLight);

    vec3 LightReflectionDir = reflect(-FragToLight, normal);
    float alpha = clamp(dot(EyeDirection, LightReflectionDir), 0, 1);

    color = albedo * theta * u_lights[0].color * u_lights[0].intensity * attenuation +
        specular * u_lights[0].intensity * pow(alpha, 5) * attenuation;

    // --- Depth-Aware Sobel Edge Detection ---
    float centerSel = texture(selectionTexture, UV).r;
    float edge = 0.0;

    float outlineWidth = 4.0;
    vec2 offset = u_TexelSize * outlineWidth;

    if (centerSel > 0.5) {
        float distCenter = distance(cameraPos, pos);

        // Sample using the scaled offset
        vec2 uvN = UV + vec2(0.0, offset.y);
        vec2 uvS = UV + vec2(0.0, -offset.y);
        vec2 uvE = UV + vec2(offset.x, 0.0);
        vec2 uvW = UV + vec2(-offset.x, 0.0);

        // Neighbor Selection Values
        float selN = texture(selectionTexture, uvN).r;
        float selS = texture(selectionTexture, uvS).r;
        float selE = texture(selectionTexture, uvE).r;
        float selW = texture(selectionTexture, uvW).r;

        // Neighbor Positions
        vec3 posN = texture(positionTexture, uvN).rgb;
        vec3 posS = texture(positionTexture, uvS).rgb;
        vec3 posE = texture(positionTexture, uvE).rgb;
        vec3 posW = texture(positionTexture, uvW).rgb;

        // Check each neighbor. If it's unselected (a boundary), we check depth.
        // We only outline if the unselected neighbor is FURTHER away than the selected mesh.
        // We also check dot(pos, pos) < 0.001 to handle the skybox/background correctly

        if (selN < 0.5 && (distance(cameraPos, posN) > distCenter || dot(posN, posN) < 0.001))
            edge += 1.0;
        if (selS < 0.5 && (distance(cameraPos, posS) > distCenter || dot(posS, posS) < 0.001))
            edge += 1.0;
        if (selE < 0.5 && (distance(cameraPos, posE) > distCenter || dot(posE, posE) < 0.001))
            edge += 1.0;
        if (selW < 0.5 && (distance(cameraPos, posW) > distCenter || dot(posW, posW) < 0.001))
            edge += 1.0;
    }

    vec3 outlineColor = vec3(0.0, 0.3, 0.9);

    if (edge > 0.1) {
        color = outlineColor;
    }
}