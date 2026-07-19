#version 330 core

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

uniform sampler2D albedo;
uniform vec3 LightColor;
uniform vec3 LightPosition_worldspace;

in vec2 UV;
in vec3 fragmentColor;
in vec3 Position_worldspace;
in vec3 Normal_worldspace;
in vec3 EyeDirection_worldspace;
in vec3 LightDirection_worldspace;

out vec4 color;

void main() {
  float LightIntensity = 1.0;

  vec3 mixedColor = texture(albedo, UV).rgb * fragmentColor;
  vec3 MaterialAmbientColor = vec3(0.1) * mixedColor;
  vec3 MaterialSpecularColor = vec3(0.3);

  float distance = length(LightPosition_worldspace - Position_worldspace);
  float attenuation = 1.0 / (1.0 + 0.1 * distance + 0.01 * distance * distance);

  vec3 n = normalize(Normal_worldspace);
  vec3 l = normalize(LightDirection_worldspace);
  vec3 E = normalize(EyeDirection_worldspace);

  vec3 R = reflect(-l, n);

  float cosTheta = max(dot(n, l), 0.0);
  float cosAlpha = max(dot(E, R), 0.0);

  vec3 diffuse = mixedColor * LightColor * cosTheta;
  vec3 specular = MaterialSpecularColor * LightColor * pow(cosAlpha, 32.0);

  color = vec4(clamp(MaterialAmbientColor + (diffuse + specular) * LightIntensity * attenuation, 0.0, 1.0), 1.0);
}