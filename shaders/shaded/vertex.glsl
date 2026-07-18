#version 330 core

layout(location = 0) in vec3 vertexPosition_modelspace;
// Notice that the "1" here equals the "1" in glVertexAttribPointer
layout(location = 1) in vec3 vertexColor;
layout(location = 2) in vec2 vertexUV;
layout(location = 3) in vec3 vertexNormal_modelspace;


out vec2 UV;
out vec3 fragmentColor;

out vec3 Position_worldspace;
out vec3 Normal_cameraspace;
out vec3 EyeDirection_cameraspace;
out vec3 LightDirection_cameraspace;

uniform mat4 MVP;
uniform mat4 V; // View matrix
uniform mat4 M; // Model matrix
uniform mat4 NormalMatrix; // Normal matrix
uniform vec3 LightPosition_worldspace;

void main(){  
  UV = vertexUV;
  fragmentColor = vertexColor;

  gl_Position = MVP * vec4(vertexPosition_modelspace,1);

  // Position of the vertex, in worldspace : M * position
  Position_worldspace = (M * vec4(vertexPosition_modelspace,1)).xyz;


  // Vector that goes from the vertex to the camera, in camera space.
  // In camera space, the camera is at the origin (0,0,0).
  vec3 vertexPosition_cameraspace = ( V * M * vec4(vertexPosition_modelspace,1)).xyz;
  EyeDirection_cameraspace = vec3(0,0,0) - vertexPosition_cameraspace;


  // Vector that goes from the vertex to the light, in camera space. M is ommited because it's identity.
  vec3 LightPosition_cameraspace = ( V * vec4(LightPosition_worldspace,1)).xyz;
  LightDirection_cameraspace = normalize(LightPosition_cameraspace - vertexPosition_cameraspace);
  Normal_cameraspace = normalize((NormalMatrix * vec4(vertexNormal_modelspace, 0.0)).xyz);
}
