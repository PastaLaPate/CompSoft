#version 330 core
out vec4 oColor;
in vec2 vTexCoords;

uniform sampler2DArray uShadowMapArray;
uniform int uDebugLayer;

void main() {
  float depthValue =
      texture(uShadowMapArray, vec3(TexCoords, float(uDebugLayer))).r;
  oColor = vec4(vec3(depthValue), 1.0);
}