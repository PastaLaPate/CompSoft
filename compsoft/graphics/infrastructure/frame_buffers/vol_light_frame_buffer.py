from OpenGL.GL import (
    GL_COLOR_ATTACHMENT0,
    GL_RGBA,
    GL_RGBA16F,
    GL_UNSIGNED_BYTE,
)

from compsoft.graphics.infrastructure.frame_buffers.frame_buffer import (
    ColorAttachment,
    FrameBuffer,
)


class VolumetricLightFrameBuffer(FrameBuffer):
    def color_attachments(self):
        return [
            ColorAttachment(GL_COLOR_ATTACHMENT0, GL_RGBA16F, GL_RGBA, GL_UNSIGNED_BYTE)
        ]

    @property
    def color_tex(self):
        return self.textures[0]
