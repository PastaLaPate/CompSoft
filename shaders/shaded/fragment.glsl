#version 330 core

/*
struct Light {
    vec3 position;
    vec3 color;
    float intensity;
};

#define MAX_LIGHTS 8
uniform Light u_lights[MAX_LIGHTS];
uniform int u_active_light_count;
*/
uniform sampler2D albedo;


in vec2 UV;
in vec3 fragmentColor;

out vec4 color;

void main(){
  vec3 mixedColor = texture( albedo, UV ).rgb * fragmentColor;
  color = vec4(mixedColor, 1);
}