#version 330 core

layout(location = 0) in vec3 aVertexPosition_M;
layout(location = 1) in vec3 aVertexColor;
layout(location = 2) in vec2 aVertexUV;
layout(location = 3) in vec3 aVertexNormal_M;
layout(location = 4) in vec3 aVertexTangent_M;

out vec2 vUV;
out vec3 vColor;
out vec3 vPosition_W;
out vec3 vNormal_W;
out vec3 vEyeDirection_W;
out mat3 vTBN_W;

uniform mat4 uMVP;
uniform mat4 uModel; // Model matrix (transforms Model space -> World space)
uniform mat4 uNormalMatrix;     // Transforms Normal vectors -> World space
uniform vec3 uCameraPosition_W; // Find view vector in world space

void main() {
  vUV = aVertexUV;
  vColor = aVertexColor;

  gl_Position = uMVP * vec4(aVertexPosition_M, 1.0);

  vPosition_W = (uModel * vec4(aVertexPosition_M, 1.0)).xyz;

  vEyeDirection_W = uCameraPosition_W - vPosition_W;

  vNormal_W = (uNormalMatrix * vec4(aVertexNormal_M, 0.0)).xyz;

  mat3 normalMat3 = mat3(uNormalMatrix);
  vec3 N = normalize(normalMat3 * aVertexNormal_M);
  vec3 T = normalize(normalMat3 * aVertexTangent_M);
  T = normalize(T - dot(T, N) * N);
  vec3 B = cross(N, T);

  vTBN_W = mat3(T, B, N);
}