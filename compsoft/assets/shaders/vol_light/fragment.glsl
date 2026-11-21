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

// Interval of the camera ray that lies inside a spot light's outer cone: in
// front of the apex and within the half-angle whose cosine is `cosOuter`.
//
// A cone is convex, so the answer is a single interval. The quadratic's roots
// only split the candidate range into segments; each segment's midpoint is
// tested against the cone directly. That avoids special-casing rays that run
// parallel to (or straight along) the axis, where the quadratic degenerates.
//
// Returns (start, end), with start > end when the ray misses the cone.
vec2 ConeInterval(vec3 origin, vec3 dir, vec3 apex, vec3 axis, float cosOuter,
                  float maxT) {
  float c2 = cosOuter * cosOuter;
  vec3 w = origin - apex;
  float m = dot(w, axis);
  float n = dot(dir, axis);
  float e = dot(w, dir);

  // In front of the apex: m + n*t >= 0.
  float start = 0.0;
  float end = maxT;
  if (abs(n) < 1e-6) {
    if (m < 0.0)
      return vec2(1.0, 0.0);
  } else if (n > 0.0) {
    start = max(start, -m / n);
  } else {
    end = min(end, -m / n);
  }
  if (end <= start)
    return vec2(1.0, 0.0);

  // Inside the double cone: A*t^2 + B*t + C >= 0.
  float A = n * n - c2;
  float B = 2.0 * (m * n - c2 * e);
  float C = m * m - c2 * dot(w, w);

  float r0 = start;
  float r1 = start;
  if (abs(A) > 1e-6) {
    float disc = B * B - 4.0 * A * C;
    if (disc > 0.0) {
      float sq = sqrt(disc);
      r0 = (-B - sq) / (2.0 * A);
      r1 = (-B + sq) / (2.0 * A);
    }
  } else if (abs(B) > 1e-6) {
    r0 = -C / B;
    r1 = r0;
  }

  float rootMin = clamp(min(r0, r1), start, end);
  float rootMax = clamp(max(r0, r1), start, end);
  float bounds[4] = float[](start, rootMin, rootMax, end);

  for (int i = 0; i < 3; ++i) {
    float lo = bounds[i];
    float hi = bounds[i + 1];
    if (hi - lo <= 1e-5)
      continue;
    vec3 v = w + dir * (0.5 * (lo + hi));
    float axisDist = dot(v, axis);
    if (axisDist >= 0.0 && axisDist * axisDist >= c2 * dot(v, v))
      return vec2(lo, hi);
  }
  return vec2(1.0, 0.0);
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

    vec3 lightDir = normalize(uLights[i].direction);
    // March only the part of the ray that is inside the cone: spotFactor is 0
    // everywhere else, so this drops no light and spends the same 28 steps where
    // the fog actually is.
    vec2 interval =
        ConeInterval(rayOrigin, rayDir, uLights[i].position, lightDir,
                     clamp(uLights[i].outer_cutoff, 0.001, 0.999), rayLen);
    if (interval.x > interval.y) {
      continue;  // the ray never enters this light's cone
    }

    // Keep the old step spacing (the whole ray used NUM_STEPS of them) and spend
    // the steps only inside the cone: a short interval marches a short loop
    // rather than 28 mostly-empty ones. Spacing - and therefore the integrated
    // result - matches the unclipped march, but the shadow fetch now only runs
    // where it can contribute.
    float maxStepLength = rayLen / float(NUM_STEPS);
    float span = interval.y - interval.x;
    int stepCount = int(clamp(ceil(span / maxStepLength), 1.0, float(NUM_STEPS)));
    float stepLength = span / float(stepCount);
    vec3 currentPos = rayOrigin + rayDir * (interval.x + dither * stepLength);
    vec3 accumulatedFog = vec3(0.0);
    for (int j = 0; j < stepCount; j++) {
      vec3 lightToSample = currentPos - uLights[i].position;
      float dist = max(length(lightToSample), 0.001);
      vec3 dirFromLight = lightToSample / dist;

      float cosAngle = dot(dirFromLight, lightDir);
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

      currentPos += rayDir * stepLength;
    }

    finalColor += accumulatedFog * stepLength;
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