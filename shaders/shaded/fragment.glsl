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
uniform sampler2D normal;

in vec2 UV;
in vec3 fragmentColor;
in vec3 Position_worldspace;
in vec3 Normal_worldspace;
in vec3 EyeDirection_worldspace;
in mat3 TBN_worldspace;

layout(location = 0) out vec4 color; // Colorattachment0

void main() {
  vec3 mixedColor = texture(albedo, UV).rgb * fragmentColor;
  vec3 MaterialAmbientColor = vec3(0.1) * mixedColor;
  vec3 MaterialSpecularColor = vec3(0.3);
  vec3 NormalTangentspace = texture(normal, UV).rgb * 2.0 - 1.0;
  vec3 n = normalize(TBN_worldspace * NormalTangentspace);
  vec3 E = normalize(EyeDirection_worldspace);

  vec3 total_diffuse = vec3(0.0);
  vec3 total_specular = vec3(0.0);
  for(int i = 0; i < u_active_light_count; i++) {
    vec3 l;
    float attenuation = 1.0;
    LightData light_data = u_lights[i];
    if(light_data.type == 0) { // Point light
      float distance = length(u_lights[i].position - Position_worldspace);
      attenuation = 1.0 / (1.0 + 0.1 * distance + 0.01 * distance * distance);
      l = normalize(u_lights[i].position - Position_worldspace);
    } else if(light_data.type == 1) { // Directional light
      l = normalize(-u_lights[i].direction);
    }
    vec3 R = reflect(-l, n);
    float cosTheta = max(dot(n, l), 0.0);
    float cosAlpha = max(dot(E, R), 0.0);

        // Accumulate light contributions, factoring in unique intensities and attenuation
    total_diffuse += mixedColor * u_lights[i].color * cosTheta * u_lights[i].intensity * attenuation;
    total_specular += MaterialSpecularColor * u_lights[i].color * pow(cosAlpha, 32.0) * u_lights[i].intensity * attenuation;

  }
  vec3 final_color = MaterialAmbientColor + total_diffuse + total_specular;
  color = vec4(clamp(final_color, 0.0, 1.0), 1.0);
}