from abc import ABC, abstractmethod
from dataclasses import dataclass

from OpenGL.constant import Constant
from OpenGL.GL import (
    GL_BLEND,
    GL_CLAMP_TO_EDGE,
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
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
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


@dataclass(frozen=True)
class ColorAttachment:
    attachment: int | Constant
    internal_format: int | Constant
    format: int | Constant
    type: int | Constant


class FrameBuffer(ABC):
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

        self.fbo = 0
        self.drb = 0  # depth render buffer

        self.textures = []

        self.build()

    @abstractmethod
    def color_attachments(self) -> list[ColorAttachment]:
        """Get the framebuffer's color attachments

        Returns:
            list[ColorAttachment]: attachments.
        """
        ...

    def build(self) -> None:
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)

        self._build_color_attachments()
        self._build_depth_attachment()

        attachments = [attachment.attachment for attachment in self.color_attachments()]
        glDrawBuffers(len(attachments), attachments)

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            print("shit smth went wrong")

    def _build_color_attachments(self) -> None:
        for attachment in self.color_attachments():
            texture = glGenTextures(1)
            self.textures.append(texture)

            glBindTexture(GL_TEXTURE_2D, texture)

            glTexImage2D(
                GL_TEXTURE_2D,
                0,
                attachment.internal_format,
                self.width,
                self.height,
                0,
                attachment.format,
                attachment.type,
                None,
            )

            self.apply_texture_parameters()

            glFramebufferTexture2D(
                GL_FRAMEBUFFER,
                attachment.attachment,
                GL_TEXTURE_2D,
                texture,
                0,
            )

    def _build_depth_attachment(self) -> None:
        self.drb = glGenRenderbuffers(1)

        glBindRenderbuffer(GL_RENDERBUFFER, self.drb)
        glRenderbufferStorage(
            GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height
        )

        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self.drb
        )

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

        for tex, attachment in zip(self.textures, self.color_attachments()):
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexImage2D(
                GL_TEXTURE_2D,
                0,
                attachment.internal_format,
                self.width,
                self.height,
                0,
                attachment.format,
                attachment.type,
                None,
            )

        glBindRenderbuffer(GL_RENDERBUFFER, self.drb)
        glRenderbufferStorage(
            GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height
        )

    def __enter__(self):
        self.bind()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.unbind()
        return False

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
        if self.textures:
            glDeleteTextures(len(self.textures), self.textures)
        if self.drb:
            glDeleteRenderbuffers(1, [self.drb])
