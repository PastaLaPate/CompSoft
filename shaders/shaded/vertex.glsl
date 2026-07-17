#version 330 core

layout(location = 0) in vec3 vertexPosition_modelspace;
// Notice that the "1" here equals the "1" in glVertexAttribPointer
layout(location = 1) in vec3 vertexColor;
layout(location = 2) in vec2 vertexUV;

out vec2 UV;
out vec3 fragmentColor;

uniform mat4 MVP;
//uniform mat4 V; // View matrix
//uniform mat4 M; // Model matrix

void main(){  
  gl_Position = MVP * vec4(vertexPosition_modelspace,1);
  UV = vertexUV;
  fragmentColor = vertexColor;
}