#version 330 core
out vec4 FragColor;
in vec2 TexCoords;

uniform sampler2DArray shadowMapArray;
uniform int debugLayer;

void main() {
  float depthValue =
      texture(shadowMapArray, vec3(TexCoords, float(debugLayer))).r;
  FragColor = vec4(vec3(depthValue), 1.0);
}