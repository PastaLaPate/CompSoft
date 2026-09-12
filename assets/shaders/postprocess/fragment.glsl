#version 330 core

in vec2 vTexCoords;

out vec3 oColor;

uniform sampler2D uColorTexture;
uniform float uExposure = 2.5;
uniform float uTime;

void main() {
  vec3 color = texture(uColorTexture, vTexCoords).xyz;
  vec3 mapped = vec3(1.0) - exp(-color * uExposure);

  mapped = pow(mapped, vec3(1.0 / 2.2));
  oColor = mapped;
}