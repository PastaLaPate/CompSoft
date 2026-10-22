#version 330 core

out vec3 oColor;

uniform sampler2D uAlbedo;
uniform sampler2D uNormal;

in vec2 vUV;
in vec3 vColor;

void main() { oColor = texture(uAlbedo, vUV).rgb * vColor; }