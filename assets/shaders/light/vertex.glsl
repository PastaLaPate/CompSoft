#version 330 core

layout (location = 0) in vec3 vertexPosition_modelspace;
layout (location = 1) in vec3 vertexColor;
layout (location = 2) in vec2 vertexUV;
layout (location = 3) in vec3 vertexNormal_modelspace;
layout (location = 4) in vec3 vertexTangent_modelspace;

out vec2 UV;
out vec3 fragmentColor;
out vec3 Position_worldspace;
out vec3 Normal_worldspace;
out vec3 EyeDirection_worldspace;
out mat3 TBN_worldspace;

uniform mat4 MVP;
uniform mat4 M;            // Model matrix (transforms Model space -> World space)
uniform mat4 NormalMatrix; // Transforms Normal vectors -> World space
uniform vec3 cameraPosition_worldspace; // Find view vector in world space

void main() {
  UV = vertexUV;
  fragmentColor = vertexColor;

  gl_Position = MVP * vec4(vertexPosition_modelspace, 1.0);
}