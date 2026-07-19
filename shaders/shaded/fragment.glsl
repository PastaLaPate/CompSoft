#version 330 core

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