#version 330 core

layout(location = 0) in vec3 vertexPosition_modelspace;
layout(location = 1) in vec3 vertexColor;
layout(location = 2) in vec2 vertexUV;
layout(location = 3) in vec3 vertexNormal_modelspace;

out vec2 UV;
out vec3 fragmentColor;
out vec3 Position_worldspace;
out vec3 Normal_worldspace;
out vec3 EyeDirection_worldspace;

uniform mat4 MVP;
uniform mat4 M;            // Model matrix (transforms Model space -> World space)
uniform mat4 NormalMatrix; // Now transforms Normal vectors -> World space
uniform vec3 cameraPosition_worldspace; // Added to find view vector in world space

void main() {
  UV = vertexUV;
  fragmentColor = vertexColor;

  gl_Position = MVP * vec4(vertexPosition_modelspace, 1.0);

  Position_worldspace = (M * vec4(vertexPosition_modelspace, 1.0)).xyz;

  EyeDirection_worldspace = cameraPosition_worldspace - Position_worldspace;

  Normal_worldspace = (NormalMatrix * vec4(vertexNormal_modelspace, 0.0)).xyz;
}