from OpenGL.GL import (
    GL_CLAMP_TO_EDGE,
    GL_COLOR_ATTACHMENT0,
    GL_LINEAR,
    GL_RGBA,
    GL_RGBA16F,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNSIGNED_BYTE,
    glTexParameteri,
)

from compsoft.graphics.infrastructure.frame_buffers.frame_buffer import (
    ColorAttachment,
    FrameBuffer,
)


class VolumetricLightFrameBuffer(FrameBuffer):
    # Only ever receives a full-screen quad: no depth attachment, no depth blit.
    needs_depth = False

    def color_attachments(self):
        return [
            ColorAttachment(GL_COLOR_ATTACHMENT0, GL_RGBA16F, GL_RGBA, GL_UNSIGNED_BYTE)
        ]

    def apply_texture_parameters(self):
        # LINEAR: the volumetric chain is half resolution, so the composite pass
        # bilinearly upsamples horizontally as part of its tap pattern. Sampling
        # one-to-one (the post copy) is unaffected - the sample points sit on
        # texel centres either way.
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)

    @property
    def color_tex(self):
        return self.textures[0]
