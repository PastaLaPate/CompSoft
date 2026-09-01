#version 330 core

in vec2 vTexCoords;
out vec3 oColor;

struct LightData {
  int type;
  vec3 position;
  vec3 direction;
  vec3 color;
  float intensity;
  float cutoff;
};

layout(std140) uniform LightingBlock {
  LightData uLights[8];
  int uActiveLightCount;
};

uniform sampler2D uPosition;
uniform sampler2D uNormal;
uniform sampler2D uColor;
uniform sampler2D uSelection;
uniform sampler2DArray uShadowMapArray;

uniform mat4 uLightSpaceMatrices[8];
uniform vec3 uCameraPos;
uniform vec2 uTexelSize;
uniform float uTime;

float ShadowCalculation(vec4 fragPosLightSpace, vec3 normal, vec3 lightDir) {
  vec3 projCoords = fragPosLightSpace.xyz / fragPosLightSpace.w;
  projCoords = projCoords * 0.5 + 0.5;
  if (projCoords.x < 0.0 || projCoords.x > 1.0 || projCoords.y < 0.0 ||
      projCoords.y > 1.0 || projCoords.z > 1.0)
    return 0.0;

  float currentDepth = projCoords.z;

  float bias = max(0.05 * (1.0 - dot(normal, lightDir)), 0.01) /
               49.9; // 49.9: far_plane - near_plane
  float shadow = 0.0;
  vec2 texelSize = (1.0 / textureSize(uShadowMapArray, 0)).xy;
  for (int x = -1; x <= 1; ++x) {
    for (int y = -1; y <= 1; ++y) {
      float pcfDepth = texture(uShadowMapArray,
                               vec3(projCoords.xy + vec2(x, y) * texelSize, 0))
                           .r;
      shadow += currentDepth - bias > pcfDepth ? 1.0 : 0.0;
    }
  }
  shadow /= 9.0;
  return shadow;
}

void main() {
  vec3 pos = texture(uPosition, vTexCoords).rgb;
  vec3 normal = texture(uNormal, vTexCoords).rgb;
  vec3 albedo = texture(uColor, vTexCoords).rgb;
  float specular = texture(uColor, vTexCoords).a;

  vec3 eyeDirection = normalize(uCameraPos - pos);
  vec3 fragToLight = normalize(uLights[0].position - pos);
  vec4 fragPosLightSpace = uLightSpaceMatrices[0] * vec4(pos, 1.0);

  float shadow = ShadowCalculation(fragPosLightSpace, normal, fragToLight);
  float theta = clamp(dot(normal, fragToLight), 0, 1);
  float distanceToLight = length(uLights[0].position - pos);
  float attenuation = 1.0 / (1.0 + 0.1 * distanceToLight +
                             0.01 * distanceToLight * distanceToLight);

  vec3 lightReflectionDir = reflect(-fragToLight, normal);
  float alpha = clamp(dot(eyeDirection, lightReflectionDir), 0, 1);

  oColor =
      albedo * theta * uLights[0].color * uLights[0].intensity * attenuation +
      specular * theta * uLights[0].intensity * pow(alpha, 5) * attenuation;
  oColor = oColor * (1 - shadow);

  // --- Depth-Aware Sobel Edge Detection ---
  float centerSel = texture(uSelection, vTexCoords).r;
  float edge = 0.0;

  float outlineWidth = 4.0;
  vec2 offset = uTexelSize * outlineWidth;

  if (centerSel > 0.5) {
    float distCenter = distance(uCameraPos, pos);

    // Sample using the scaled offset
    vec2 uvN = vTexCoords + vec2(0.0, offset.y);
    vec2 uvS = vTexCoords + vec2(0.0, -offset.y);
    vec2 uvE = vTexCoords + vec2(offset.x, 0.0);
    vec2 uvW = vTexCoords + vec2(-offset.x, 0.0);

    // Neighbor Selection Values
    float selN = texture(uSelection, uvN).r;
    float selS = texture(uSelection, uvS).r;
    float selE = texture(uSelection, uvE).r;
    float selW = texture(uSelection, uvW).r;

    // Neighbor Positions
    vec3 posN = texture(uPosition, uvN).rgb;
    vec3 posS = texture(uPosition, uvS).rgb;
    vec3 posE = texture(uPosition, uvE).rgb;
    vec3 posW = texture(uPosition, uvW).rgb;

    // Check each neighbor. If it's unselected (a boundary), we check depth.
    // We only outline if the unselected neighbor is FURTHER away than the
    // selected mesh. We also check dot(pos, pos) < 0.001 to handle the
    // skybox/background correctly

    if (selN < 0.5 &&
        (distance(uCameraPos, posN) > distCenter || dot(posN, posN) < 0.001))
      edge += 1.0;
    if (selS < 0.5 &&
        (distance(uCameraPos, posS) > distCenter || dot(posS, posS) < 0.001))
      edge += 1.0;
    if (selE < 0.5 &&
        (distance(uCameraPos, posE) > distCenter || dot(posE, posE) < 0.001))
      edge += 1.0;
    if (selW < 0.5 &&
        (distance(uCameraPos, posW) > distCenter || dot(posW, posW) < 0.001))
      edge += 1.0;
  }

  vec3 outlineColor = vec3(0.0, 0.3, 0.9);

  if (edge > 0.1) {
    oColor = outlineColor;
  }
}