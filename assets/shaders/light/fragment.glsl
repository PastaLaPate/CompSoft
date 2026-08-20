#version 330 core

out vec3 color;

uniform sampler2D albedo;
uniform sampler2D normal in vec2 UV;
in vec3 fragmentColor;

void main() {
color = texture(albedo, UV).rgb * fragmentColor;
}