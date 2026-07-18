#version 330 core

/*
struct Light {
    vec3 position;
    vec3 color;
    float intensity;
};

#define MAX_LIGHTS 8
uniform Light u_lights[MAX_LIGHTS];
uniform int u_active_light_count;
*/
uniform sampler2D albedo;

uniform mat4 MV;
uniform vec3 LightPosition_worldspace;
uniform vec3 LightColor;

in vec2 UV;
in vec3 fragmentColor;

in vec3 Position_worldspace;
in vec3 Normal_cameraspace;
in vec3 EyeDirection_cameraspace;
in vec3 LightDirection_cameraspace;

out vec4 color;

void main() {
  vec3 mixedColor = texture(albedo, UV).rgb * fragmentColor;
  vec3 MaterialAmbientColor = vec3(0.1) * mixedColor;
  vec3 MaterialSpecularColor = vec3(0.3);

  float distance = length(LightPosition_worldspace - Position_worldspace);
  float attenuation = 1.0 / (1.0 + 0.1 * distance + 0.01 * distance * distance);

  vec3 n = normalize(Normal_cameraspace);
  vec3 l = normalize(LightDirection_cameraspace);
  vec3 E = normalize(EyeDirection_cameraspace);
  vec3 R = reflect(-l, n);

  // Calculate light components
  float cosTheta = max(dot(n, l), 0.0);
  float cosAlpha = max(dot(E, R), 0.0);

  vec3 diffuse = mixedColor * LightColor * cosTheta;
  vec3 specular = MaterialSpecularColor * LightColor * pow(cosAlpha, 32.0);

  // Combine with attenuation
  color = vec4(clamp(MaterialAmbientColor + (diffuse + specular) * attenuation, 0, 1), 1.0);
}