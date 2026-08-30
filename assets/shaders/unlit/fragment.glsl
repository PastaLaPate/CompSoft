#version 330 core

in vec2 vTexCoords;

out vec3 color;

uniform sampler2D uPositionTexture;
uniform sampler2D uNormalTexture;
uniform sampler2D uColorTexture;
uniform float uTime;

void main() { color = texture(uColorTexture, vTexCoords).xyz; }