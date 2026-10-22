#version 330 core

// Input vertex data, different for all executions of this shader.
layout(location = 0) in vec3 aVertexPosition_M;

// Output data ; will be interpolated for each fragment.
out vec2 vTexCoords;

void main() {
  gl_Position = vec4(aVertexPosition_M, 1);
  vTexCoords = (aVertexPosition_M.xy + vec2(1, 1)) / 2.0;
}
