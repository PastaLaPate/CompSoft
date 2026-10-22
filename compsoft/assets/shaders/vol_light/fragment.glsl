#version 330 core

in vec2 vTexCoords;
out vec3 oColor;

struct LightData {
  int type;
  vec3 position;
  vec3 direction;
  vec3 color;
  float intensity;
  float inner_cutoff;
  float outer_cutoff;
};

layout(std140) uniform LightingBlock {
  LightData uLights[8];
  int uActiveLightCount;
};

uniform sampler2D uPosition;
uniform sampler2DArray uShadowMapArray;

uniform mat4 uLightSpaceMatrices[8];
uniform mat4 uInvViewProj;
uniform vec3 uCameraPos;
uniform vec2 uTexelSize;
uniform float uTime;

const int NUM_STEPS = 28;
const float MAX_FOG_DIST = 50.0;

const float PI = 3.14159265;
const float EPSILON = 0.001;

float HenyeyGreenstein(float cosTheta, float g) {
  float g2 = g * g;
  return (1.0 - g2) / (4.0 * PI * pow(1.0 + g2 - 2.0 * g * cosTheta, 1.5));
}

vec3 GetRayDir(vec2 texCoords, mat4 invViewProj, vec3 cameraPos) {
  vec4 ndc = vec4(texCoords * 2.0 - 1.0, 1.0, 1.0); // [0-1] to [-1, 1]
  vec4 worldPos = invViewProj * ndc;
  worldPos /= worldPos.w;
  return normalize(worldPos.xyz - cameraPos);
}

void main() {
  vec3 pos = texture(uPosition, vTexCoords).rgb;
  bool isVoid = length(pos) < EPSILON;

  vec3 rayOrigin = uCameraPos;
  vec3 rayDir;
  float rayLen;

  if (!isVoid) {
    vec3 rayVec = pos - rayOrigin;
    rayLen = min(length(rayVec), MAX_FOG_DIST);
    rayDir = normalize(rayVec);
  } else {
    rayDir = GetRayDir(vTexCoords, uInvViewProj, rayOrigin);
    rayLen = MAX_FOG_DIST;
  }

  float stepSize = rayLen / float(NUM_STEPS);

  float dither = fract(
      52.9829189 * fract(dot(gl_FragCoord.xy, vec2(0.06711056, 0.00583715))));

  vec3 finalColor = vec3(0.0);
  for (int i = 0; i < uActiveLightCount; i++) {
    if (uLights[i].type != 2) {
      continue;
    }

    float distToLight = length(uLights[i].position - rayOrigin);
    if (distToLight > MAX_FOG_DIST + 20.0) {
        continue;  // too far
    }

    vec3 currentPos = rayOrigin + rayDir * (dither * stepSize);
    vec3 accumulatedFog = vec3(0.0);
    for (int j = 0; j < NUM_STEPS; j++) {
      vec3 lightToSample = currentPos - uLights[i].position;
      float dist = max(length(lightToSample), 0.001);
      vec3 dirFromLight = lightToSample / dist;

      float cosAngle = dot(dirFromLight, normalize(uLights[i].direction));
      float spotFactor =
          clamp((cosAngle - uLights[i].outer_cutoff) /
                    (uLights[i].inner_cutoff - uLights[i].outer_cutoff),
                0.0, 1.0);

      float visibility = 1.0;

      if (spotFactor > 0.0) {
        vec4 lightSpacePos = uLightSpaceMatrices[i] * vec4(currentPos, 1.0);
        vec3 projCoords = lightSpacePos.xyz / lightSpacePos.w * 0.5 +
                          0.5; // [-1, 1] to [0, 1]

        if (projCoords.x >= 0.0 && projCoords.x <= 1.0 && projCoords.y >= 0.0 &&
            projCoords.y <= 1.0 && projCoords.z <= 1.0) {
          float shadowMapDepth =
              texture(uShadowMapArray, vec3(projCoords.xy, i)).r;
          float softness = 0.01;
          visibility =
              clamp((shadowMapDepth - projCoords.z) / softness + 0.5, 0.0, 1.0);
        }
      }

      if (spotFactor * visibility > 0.0) {
        vec3 toLight = normalize(uLights[i].position - currentPos);
        float cosTheta = dot(rayDir, toLight);
        float phase = HenyeyGreenstein(cosTheta, 0.3);

        float attenuation = 1.0 / (1.0 + 0.1 * dist + 0.01 * dist * dist);

        accumulatedFog += spotFactor * visibility * phase * uLights[i].color *
                          uLights[i].intensity * attenuation;
        if (dot(accumulatedFog, vec3(0.33)) > 0.95) {
          break; // Almost saturated
        }
      }

      currentPos += rayDir * stepSize;
    }

    finalColor += accumulatedFog * stepSize;
  }

  finalColor = finalColor / (finalColor + vec3(1.0)); // Reinhard

  finalColor = pow(finalColor, vec3(1.0 / 2.2)); // Gamma Correction

  float outputNoise =
      (fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453) -
       0.5) /
      255.0;
  finalColor += outputNoise;

  oColor = max(finalColor, vec3(0.0));
}