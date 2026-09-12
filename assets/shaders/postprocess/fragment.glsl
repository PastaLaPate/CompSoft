#version 330 core

in vec2 vTexCoords;
out vec3 oColor;

uniform sampler2D uColorTexture;
uniform float uExposure = 1.0;
uniform float uTime;

void main() {
  oColor = texture(uColorTexture, vTexCoords).xyz;
}