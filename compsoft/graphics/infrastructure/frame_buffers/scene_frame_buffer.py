from OpenGL.GL import (
    GL_COLOR_ATTACHMENT0,
    GL_COLOR_ATTACHMENT1,
    GL_COLOR_ATTACHMENT2,
    GL_COLOR_ATTACHMENT3,
    GL_FLOAT,
    GL_R16F,
    GL_RED,
    GL_RGBA,
    GL_RGBA16F,
    GL_UNSIGNED_BYTE,
)

from compsoft.graphics.infrastructure.frame_buffers.frame_buffer import (
    ColorAttachment,
    FrameBuffer,
)


class SceneFrameBuffer(FrameBuffer):
    def color_attachments(self):
        return [
            ColorAttachment(GL_COLOR_ATTACHMENT0, GL_RGBA16F, GL_RGBA, GL_FLOAT),
            ColorAttachment(GL_COLOR_ATTACHMENT1, GL_RGBA16F, GL_RGBA, GL_FLOAT),
            ColorAttachment(
                GL_COLOR_ATTACHMENT2, GL_RGBA16F, GL_RGBA, GL_UNSIGNED_BYTE
            ),
            ColorAttachment(GL_COLOR_ATTACHMENT3, GL_R16F, GL_RED, GL_FLOAT),
        ]

    @property
    def position_tex(self) -> int:
        return self.textures[0]

    @property
    def normal_tex(self) -> int:
        return self.textures[1]

    @property
    def color_tex(self) -> int:
        return self.textures[2]

    @property
    def selection_tex(self) -> int:
        return self.textures[3]
