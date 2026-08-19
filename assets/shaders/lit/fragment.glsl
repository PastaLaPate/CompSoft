#version 330 core

in vec2 UV;

out vec3 color;

uniform sampler2D positionTexture;
uniform sampler2D normalTexture;
uniform sampler2D colorTexture;
uniform vec3 cameraPos;
uniform float time;

struct LightData {
    int type;        // 4 bytes  -> Offset 0. bytes 4-15 are empty
    vec3 position;   // 12 bytes -> Offset 16. 4 last bytes are empty, needs to start in a 16 byte chunk
    vec3 direction;  // 12 bytes -> Offset 32. 4 last bytes are empty, needs to start in a 16 byte chunk
    vec3 color;      // 12 bytes -> Offset 48. 4 last bytes are empty, needs to start in a 16 byte chunk
    float intensity; // 4 bytes  -> Offset 60
    float cutoff;      // 4 bytes  -> Offset 64
    // END at 68 bytes
    // Needs 16 multiple size, total size: 80 bytes
};

layout(std140) uniform LightingBlock {
    LightData u_lights[8];         // 8 lights * 80 bytes = 640 bytes
    int u_active_light_count;  // Size: 4 bytes. Offset: 640.
};

void main() {
    vec3 pos = texture(positionTexture, UV).rgb;
    vec3 normal = texture(normalTexture, UV).rgb;
    vec3 albedo = texture(colorTexture, UV).rgb;
    float specular = texture(colorTexture, UV).a;

    vec3 EyeDirection = normalize(cameraPos - pos);

    vec3 FragToLight = normalize(u_lights[0].position - pos); // Re center space on the  frag pos

    float theta = clamp(dot(normal, FragToLight), 0, 1); // How much the light is positioned perpendicular to the frag, 1 = fully over
    float distance = length(u_lights[0].position - pos);
    float attenuation = 1.0 / (1.0 + 0.1 * distance + 0.01 * distance * distance); // OpenGL Attenuation Equation, better than distance², avoids /0

    vec3 LightReflectionDir = reflect(-FragToLight, normal);
    float alpha = clamp(dot(EyeDirection, LightReflectionDir), 0, 1);

    color = albedo * theta * u_lights[0].color * u_lights[0].intensity * attenuation + specular * u_lights[0].intensity * pow(alpha, 5) * attenuation;
}