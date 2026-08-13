from OpenGL.GL import (
    GL_COLOR_ATTACHMENT0,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_COMPONENT,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_COMPLETE,
    GL_NEAREST,
    GL_RENDERBUFFER,
    GL_RGB,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE,
    glBindFramebuffer,
    glBindRenderbuffer,
    glBindTexture,
    glCheckFramebufferStatus,
    glClear,
    glDrawBuffers,
    glFramebufferRenderbuffer,
    glFramebufferTexture,
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
        self.rendered_tex = 0

        self.drb = 0  # depth render buffer

        self.build()

    def build(self) -> None:
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        self.rendered_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.rendered_tex)
        # I guess: GL_TEXTURE_2D: target, mipmap level, GPU pixel format, w, h, legacy parameter lol,
        # cpu source format, size, pointer to cpu data
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            self.width,
            self.height,
            0,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            None,
        )

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        self.drb = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.drb)
        glRenderbufferStorage(
            GL_RENDERBUFFER, GL_DEPTH_COMPONENT, self.width, self.height
        )
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.drb
        )

        glFramebufferTexture(
            GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.rendered_tex, 0
        )
        glDrawBuffers(
            1, [GL_COLOR_ATTACHMENT0]
        )  # "1" is the size of DrawBuffers

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            print("shit smth went wrong")

    def _on_window_size_changed(self, w: int, h: int) -> None:
        if w == self.width and h == self.height:
            return
        self.width = w
        self.height = h

        glBindTexture(GL_TEXTURE_2D, self.rendered_tex)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            self.width,
            self.height,
            0,
            GL_RGB,
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
