#version 330 core

layout(location = 0) out vec3 gPosition;   // Color Attach 0
layout(location = 1) out vec3 gNormal;     // Color Attach 1
layout(location = 2) out vec4 gAlbedoSpec; // Color Attach 2
layout(location = 3) out float gSelection; // Color Attach 3

uniform sampler2D uAlbedo;
uniform sampler2D uNormal;
uniform bool uIsSelected;

in vec2 vUV;
in vec3 vColor;
in vec3 vPosition_W;
in vec3 vNormal_W;
in vec3 vEyeDirection_W;
in mat3 vTBN_W;

void main() {
  vec3 NormalTangentspace = texture(uNormal, vUV).rgb * 2.0 - 1.0;

  gPosition = vPosition_W;
  gNormal = normalize(vTBN_W * NormalTangentspace);

  gAlbedoSpec.rgb = texture(uAlbedo, vUV).rgb * vColor;
  gAlbedoSpec.a = .3;

  gSelection = uIsSelected ? 1.0 : 0.0;
}