#version 330 core

in vec2 vTexCoords;
out vec3 oColor;

uniform sampler2D uColor;
uniform vec2 uTexelSize;
uniform vec2 uBlurDirection;

void main() {
  vec3 blur = vec3(0.0);
  float weights[5] =
      float[](0.227027, 0.1945946, 0.1216216, 0.054054, 0.016216);
  blur += texture(uColor, vTexCoords).rgb * weights[0];
  for (int i = 1; i < 5; i++) {
    vec2 offset = vec2(float(i)) * uTexelSize * uBlurDirection;
    blur += texture(uColor, vTexCoords + offset).rgb * weights[i];
    blur += texture(uColor, vTexCoords - offset).rgb * weights[i];
  }
  oColor = blur;
}