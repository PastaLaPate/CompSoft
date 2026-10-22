#version 330 core

layout(location = 0) in vec3 aVertexPosition_M;
layout(location = 1) in vec3 aVertexColor;
layout(location = 2) in vec2 aVertexUV;
layout(location = 3) in vec3 aVertexNormal_M;
layout(location = 4) in vec3 aVertexTangent_M;

out vec2 vUV;
out vec3 vColor;

uniform mat4 uMVP;
uniform mat4 uModel; // Model matrix (transforms Model space -> World space)
uniform mat4 uNormalMatrix;     // Transforms Normal vectors -> World space
uniform vec3 uCameraPosition_W; // Find view vector in world space

void main() {
  vUV = aVertexUV;
  vColor = aVertexColor;

  gl_Position = uMVP * vec4(aVertexPosition_M, 1.0);
}