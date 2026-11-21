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
    """A framebuffer whose color attachments are textures.

    `needs_depth` controls whether a depth renderbuffer is allocated. Screen-space
    passes (lighting composite, blur, volumetrics) draw exactly one quad and never
    depth-test, so they must opt out: a depth attachment costs
    width*height*4 bytes of VRAM and forces the depth blit in `unbind()`.
    """

    needs_depth: bool = True

    def __init__(self, width: int, height: int, scale: float = 1.0) -> None:
        # scale < 1 allocates the target at a fraction of the window size: the
        # volumetric chain runs at 0.5 and is upsampled at composite time.
        self.scale = scale
        self.width = self._scaled(width)
        self.height = self._scaled(height)

        self.fbo = 0
        self.drb = 0  # depth render buffer

        self.textures = []

        self.build()

    def _scaled(self, value: int) -> int:
        return max(1, round(value * self.scale))

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
        if self.needs_depth:
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
        w = self._scaled(w)
        h = self._scaled(h)
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

        if self.needs_depth:
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
        if self.needs_depth:
            glClear(GL_DEPTH_BUFFER_BIT)

        glDisable(GL_BLEND)

    def unbind(self) -> None:
        # Keep depth buffer: the forward pass renders into the default framebuffer
        # and needs the depth the deferred pass wrote.
        if self.needs_depth:
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
