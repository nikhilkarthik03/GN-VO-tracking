import glfw
from OpenGL.GL import *
from src.texture_utils import create_texture, update_texture
import cv2

class Renderer:
    def __init__(self, width=640, height=480, title="Camera + OpenGL"):
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")

        self.window = glfw.create_window(width, height, title, None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("Failed to create GLFW window")

        glfw.make_context_current(self.window)
        glViewport(0, 0, width, height)

        # Enable texturing and smooth shading
        glEnable(GL_TEXTURE_2D)
        glShadeModel(GL_SMOOTH)

        # Background color
        glClearColor(0.1, 0.1, 0.1, 1.0)

        # Create texture
        self.texture_id = create_texture()

    def draw_frame(self, frame):
        frame = cv2.flip(frame, 0)  # Flip vertically
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        update_texture(self.texture_id, frame)

        # Clear and draw textured quad
        glClear(GL_COLOR_BUFFER_BIT)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, -1.0)
        glTexCoord2f(1.0, 0.0); glVertex2f( 1.0, -1.0)
        glTexCoord2f(1.0, 1.0); glVertex2f( 1.0,  1.0)
        glTexCoord2f(0.0, 1.0); glVertex2f(-1.0,  1.0)
        glEnd()

        glfw.swap_buffers(self.window)
        glfw.poll_events()

    def should_close(self):
        return glfw.window_should_close(self.window)

    def terminate(self):
        glfw.terminate()
