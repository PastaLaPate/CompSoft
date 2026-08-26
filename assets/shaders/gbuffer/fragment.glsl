#version 330 core

layout (location = 0) out vec3 gPosition; // Color Attach 0 
layout (location = 1) out vec3 gNormal; // Color Attach 1
layout (location = 2) out vec4 gAlbedoSpec; // Color Attach 2
layout (location = 3) out float gSelection; // Color Attach 3

uniform sampler2D albedo;
uniform sampler2D normal;
uniform bool u_IsSelected;

in vec2 UV;
in vec3 fragmentColor;
in vec3 Position_worldspace;
in vec3 Normal_worldspace;
in vec3 EyeDirection_worldspace;
in mat3 TBN_worldspace;

void main() {
  vec3 NormalTangentspace = texture(normal, UV).rgb * 2.0 - 1.0;

  gPosition = Position_worldspace;
  gNormal = normalize(TBN_worldspace * NormalTangentspace);

  gAlbedoSpec.rgb = texture(albedo, UV).rgb * fragmentColor;
  gAlbedoSpec.a = .3;

  gSelection = u_IsSelected ? 1.0 : 0.0;
}