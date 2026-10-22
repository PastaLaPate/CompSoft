#version 330 core
layout(location = 0) in vec3 aVertexPosition_M;

uniform mat4 uMVP;

void main() { gl_Position = uMVP * vec4(aVertexPosition_M, 1.0); }