#version 330 core
layout(location = 0) in vec3 aPos;

out vec2 vTexCoords;

void main() {
  vTexCoords = (aPos.xy + vec2(1.0, 1.0)) / 2.0;
  gl_Position = vec4(aPos, 1.0);
}