from OpenGL.GL import (
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_COMPONENT,
    GL_FRAMEBUFFER,
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
    glFramebufferRenderbuffer,
    glGenFramebuffers,
    glGenRenderbuffers,
    glGenTextures,
    glRenderbufferStorage,
    glTexImage2D,
    glTexParameteri,
)


class FrameBuffer:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

        self.fbo = 0
        self.rendered_tex = 0

        self.drb = 0  # depth render buffer

    def build(self) -> None:
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        self.rendered_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.rendered_tex)
        # I guess: gpu id 0, gpu format: rgb, w, h, cpu id, cpu format, data (0: black)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            self.width,
            self.height,
            0,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            0,
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
