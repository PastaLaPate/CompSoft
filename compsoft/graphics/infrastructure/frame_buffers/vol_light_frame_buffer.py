from OpenGL.GL import (
    GL_BLEND,
    GL_CLAMP_TO_EDGE,
    GL_COLOR_ATTACHMENT0,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_COMPONENT24,
    GL_DRAW_FRAMEBUFFER,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_COMPLETE,
    GL_NEAREST,
    GL_READ_FRAMEBUFFER,
    GL_RENDERBUFFER,
    GL_RGBA,
    GL_RGBA16F,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNSIGNED_BYTE,
    glBindFramebuffer,
    glBindRenderbuffer,
    glBindTexture,
    glBlitFramebuffer,
    glCheckFramebufferStatus,
    glClear,
    glClearColor,
    glDeleteFramebuffers,
    glDeleteRenderbuffers,
    glDeleteTextures,
    glDisable,
    glDrawBuffers,
    glFramebufferRenderbuffer,
    glFramebufferTexture2D,
    glGenFramebuffers,
    glGenRenderbuffers,
    glGenTextures,
    glRenderbufferStorage,
    glTexImage2D,
    glTexParameteri,
    glViewport,
)


class VolumetricLightFrameBuffer:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

        self.fbo = 0
        self.color_tex = 0

        self.drb = 0  # depth render buffer

        self.build()

    def build(self) -> None:
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        self.color_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.color_tex)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA16F,  # More precision than ints
            self.width,
            self.height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            None,
        )

        self.apply_texture_parameters()
        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            GL_TEXTURE_2D,
            self.color_tex,
            0,
        )

        self.drb = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.drb)
        glRenderbufferStorage(
            GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height
        )
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.drb
        )

        glDrawBuffers(
            1,
            [
                GL_COLOR_ATTACHMENT0,
            ],
        )  # "1" is the size of DrawBuffers

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            print("shit smth went wrong")

    def apply_texture_parameters(self):
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)

    def _on_window_size_changed(self, w: int, h: int) -> None:
        if w == self.width and h == self.height:
            return
        self.width = w
        self.height = h

        glBindTexture(GL_TEXTURE_2D, self.color_tex)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            self.width,
            self.height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            None,
        )

        glBindRenderbuffer(GL_RENDERBUFFER, self.drb)
        glRenderbufferStorage(
            GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height
        )

    def bind(self) -> None:
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glViewport(0, 0, self.width, self.height)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glClear(GL_DEPTH_BUFFER_BIT)
        glDisable(GL_BLEND)

    def unbind(self) -> None:
        # Keep depth buffer
        glBindFramebuffer(GL_READ_FRAMEBUFFER, self.fbo)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glBlitFramebuffer(
            0,
            0,
            self.width,
            self.height,
            0,
            0,
            self.width,
            self.height,
            GL_DEPTH_BUFFER_BIT,
            GL_NEAREST,
        )
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        glViewport(0, 0, self.width, self.height)

    def destroy(self):
        if self.fbo:
            glDeleteFramebuffers(1, [self.fbo])
        if self.color_tex:
            glDeleteTextures(
                1,
                [
                    self.color_tex,
                ],
            )
        if self.drb:
            glDeleteRenderbuffers(1, [self.drb])
