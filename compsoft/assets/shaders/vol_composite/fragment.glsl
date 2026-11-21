#version 330 core

// Volumetric composite: finishes the half-resolution fog and adds it to the
// scene. The vertical half of the separable blur happens here, at full
// resolution, and every tap is weighted by how well the scene depth at that tap
// matches the pixel's own depth - that is the joint-bilateral upsample. Fog from
// a surface must not bleed onto whatever is behind it at a silhouette.
//
// Horizontal bilinear interpolation between the two half-res columns comes for
// free: the fog texture is GL_LINEAR and the taps sit on row centres.

in vec2 vTexCoords;
out vec3 oColor;

uniform sampler2D uFog;       // half-res, horizontally blurred scattering
uniform sampler2D uPosition;  // full-res G-buffer world position
uniform vec3 uCameraPos;
uniform vec2 uFogTexelSize;   // 1 / fog texture size

const int TAPS = 5;
const float WEIGHTS[5] =
    float[](0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);

// Distance from the camera to the surface at `uv`. Sky reads (0,0,0) in the
// position buffer and counts as infinitely far, so sky taps only ever match sky
// taps; the volumetric pass marches sky rays to MAX_FOG_DIST instead, and both
// are "unoccluded" for weighting purposes.
float SceneDistance(vec2 uv) {
  vec3 p = texture(uPosition, uv).rgb;
  return dot(p, p) < 1e-6 ? 1e6 : distance(uCameraPos, p);
}

// 1 when the tap sits at the same depth as the pixel, falling to 0 at the
// tolerance. Squared for a softer shoulder. The tolerance is proportional to
// the pixel's distance, so the rejection band grows with perspective depth
// instead of being one world-space number that is too tight up close and too
// loose far away.
float DepthWeight(float distance_, float centerDistance, float tolerance) {
  float x = 1.0 - abs(distance_ - centerDistance) / tolerance;
  x = clamp(x, 0.0, 1.0);
  return x * x;
}

void main() {
  float centerDistance = SceneDistance(vTexCoords);
  float tolerance = max(0.05, 0.02 * centerDistance);

  vec3 fog = vec3(0.0);
  float weightSum = 0.0;
  for (int i = 0; i < TAPS; ++i) {
    vec2 uv = vTexCoords + vec2(0.0, float(i - 2) * uFogTexelSize.y);
    float weight =
        WEIGHTS[i] * DepthWeight(SceneDistance(uv), centerDistance, tolerance);
    fog += texture(uFog, uv).rgb * weight;
    weightSum += weight;
  }

  // A one-pixel sliver where every tap was rejected (both neighbours at a
  // different depth) falls back to the unblurred fog at the pixel itself.
  oColor = weightSum > 1e-4 ? fog / weightSum : texture(uFog, vTexCoords).rgb;
}
