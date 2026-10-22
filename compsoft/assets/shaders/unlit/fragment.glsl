#version 330 core

in vec2 vTexCoords;

out vec3 oColor;

uniform sampler2D uPositionTexture;
uniform sampler2D uNormalTexture;
uniform sampler2D uColorTexture;
uniform float uTime;

void main() { oColor = texture(uColorTexture, vTexCoords).xyz; }