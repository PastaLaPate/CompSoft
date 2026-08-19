#version 330 core

out vec3 color;

uniform sampler2D albedo;
uniform sampler2D normal;

in vec2 UV;
in vec3 fragmentColor;
in vec3 Position_worldspace;
in vec3 Normal_worldspace;
in vec3 EyeDirection_worldspace;
in mat3 TBN_worldspace;

void main() {
  color = texture(albedo, UV) * fragmentColor;
}