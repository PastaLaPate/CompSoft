#version 330 core

in vec2 UV;

out vec3 color;

uniform sampler2D positionTexture;
uniform sampler2D normalTexture;
uniform sampler2D colorTexture;
uniform float time;

void main() {
    color = texture(colorTexture, UV).xyz;
}