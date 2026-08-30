from OpenGL.GL import (
    GL_BLEND,
    GL_CLAMP_TO_EDGE,
    GL_COLOR_ATTACHMENT0,
    GL_COLOR_ATTACHMENT1,
    GL_COLOR_ATTACHMENT2,
    GL_COLOR_ATTACHMENT3,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_COMPONENT24,
    GL_DRAW_FRAMEBUFFER,
    GL_FLOAT,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_COMPLETE,
    GL_NEAREST,
    GL_R16F,
    GL_READ_FRAMEBUFFER,
    GL_RED,
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


class FrameBuffer:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

        self.fbo = 0
        self.position_tex = 0
        self.normal_tex = 0
        self.color_tex = 0
        self.selection_tex = 0

        self.drb = 0  # depth render buffer

        self.build()

    def build(self) -> None:
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        # Position texture

        self.position_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.position_tex)
        # TODO: Store this in a depth comp / depth texture
        # I guess: GL_TEXTURE_2D: target, mipmap level, GPU pixel format, w, h, legacy parameter lol,
        # cpu source format, size, pointer to cpu data
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA16F,  # More precision than ints
            self.width,
            self.height,
            0,
            GL_RGBA,
            GL_FLOAT,
            None,
        )

        self.apply_texture_parameters()
        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            GL_TEXTURE_2D,
            self.position_tex,
            0,
        )

        # Normal

        self.normal_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.normal_tex)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA16F,  # More precision than ints
            self.width,
            self.height,
            0,
            GL_RGBA,
            GL_FLOAT,
            None,
        )

        self.apply_texture_parameters()
        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT1,
            GL_TEXTURE_2D,
            self.normal_tex,
            0,
        )

        # Albedo

        self.color_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.color_tex)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,  # More precision than ints
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
            GL_COLOR_ATTACHMENT2,
            GL_TEXTURE_2D,
            self.color_tex,
            0,
        )

        # Selection
        self.selection_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.selection_tex)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_R16F,
            self.width,
            self.height,
            0,
            GL_RED,
            GL_FLOAT,
            None,
        )
        self.apply_texture_parameters()

        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT3,
            GL_TEXTURE_2D,
            self.selection_tex,
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
            4,
            [
                GL_COLOR_ATTACHMENT0,
                GL_COLOR_ATTACHMENT1,
                GL_COLOR_ATTACHMENT2,
                GL_COLOR_ATTACHMENT3,
            ],
        )  # "4" is the size of DrawBuffers

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

        glBindTexture(GL_TEXTURE_2D, self.position_tex)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA16F,  # More precision than ints
            self.width,
            self.height,
            0,
            GL_RGBA,
            GL_FLOAT,
            None,
        )

        glBindTexture(GL_TEXTURE_2D, self.normal_tex)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA16F,  # More precision than ints
            self.width,
            self.height,
            0,
            GL_RGBA,
            GL_FLOAT,
            None,
        )

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

        glBindTexture(GL_TEXTURE_2D, self.selection_tex)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_R16F,
            self.width,
            self.height,
            0,
            GL_RED,
            GL_FLOAT,
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
        if (
            self.position_tex
            and self.normal_tex
            and self.color_tex
            and self.selection_tex
        ):
            glDeleteTextures(
                4,
                [
                    self.position_tex,
                    self.normal_tex,
                    self.color_tex,
                    self.selection_tex,
                ],
            )
        if self.drb:
            glDeleteRenderbuffers(1, [self.drb])
