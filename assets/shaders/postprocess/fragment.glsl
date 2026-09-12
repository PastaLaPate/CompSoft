#version 330 core

in vec2 vTexCoords;

out vec3 oColor;

uniform sampler2D uColorTexture;
uniform float uTime;

void main() {
  vec3 color = texture(uColorTexture, vTexCoords).xyz;
  color = color / (color + 1.0);
  color = pow(color, vec3(1.0 / 2.2));
  oColor = color;
}