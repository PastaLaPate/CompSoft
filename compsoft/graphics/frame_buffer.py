from OpenGL.GL import (
    GL_COLOR_ATTACHMENT0,
    GL_COLOR_ATTACHMENT1,
    GL_COLOR_ATTACHMENT2,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_COMPONENT,
    GL_FLOAT,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_COMPLETE,
    GL_NEAREST,
    GL_RENDERBUFFER,
    GL_RGBA,
    GL_RGBA16F,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE,
    glBindFramebuffer,
    glBindRenderbuffer,
    glBindTexture,
    glCheckFramebufferStatus,
    glClear,
    glDeleteFramebuffers,
    glDeleteRenderbuffers,
    glDeleteTextures,
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

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
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

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
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

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT2,
            GL_TEXTURE_2D,
            self.color_tex,
            0,
        )

        self.drb = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.drb)
        glRenderbufferStorage(
            GL_RENDERBUFFER, GL_DEPTH_COMPONENT, self.width, self.height
        )
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.drb
        )

        glDrawBuffers(
            3,
            [GL_COLOR_ATTACHMENT0, GL_COLOR_ATTACHMENT1, GL_COLOR_ATTACHMENT2],
        )  # "1" is the size of DrawBuffers

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            print("shit smth went wrong")

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

        glBindRenderbuffer(GL_RENDERBUFFER, self.drb)
        glRenderbufferStorage(
            GL_RENDERBUFFER, GL_DEPTH_COMPONENT, self.width, self.height
        )

    def bind(self) -> None:
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT)
        glClear(GL_DEPTH_BUFFER_BIT)

    def unbind(self) -> None:
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, self.width, self.height)

    def destroy(self):
        if self.fbo:
            glDeleteFramebuffers(1, [self.fbo])
        if self.position_tex and self.normal_tex and self.color_tex:
            glDeleteTextures(
                3, [self.position_tex, self.normal_tex, self.color_tex]
            )
        if self.drb:
            glDeleteRenderbuffers(1, [self.drb])
