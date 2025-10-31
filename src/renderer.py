"""Main renderer combining camera feed and 3D objects."""
import glfw
from OpenGL.GL import *
import numpy as np
import cv2
import logging
from typing import Optional

from src.shader_manager import ShaderManager
from src.texture_manager import TextureManager
from src.object_renderer import ObjectRenderer
from src.object_creator import ObjectCreator
from src.image_loader import load_image_from_url
from src.mat_utils import MatUtils

logger = logging.getLogger(__name__)


# Shader sources
CAMERA_VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec2 aTexCoord;
out vec2 TexCoord;
void main() {
    gl_Position = vec4(aPos, 1.0);
    TexCoord = aTexCoord;
}
"""

CAMERA_FRAGMENT_SHADER = """
#version 330 core
in vec2 TexCoord;
out vec4 FragColor;
uniform sampler2D tex;
void main() {
    FragColor = texture(tex, TexCoord);
}
"""


class Renderer:
    """Main rendering system combining camera feed and 3D objects."""
    
    def __init__(
        self,
        width: int = 640,
        height: int = 480,
        title: str = "Camera + OpenGL + 3D Objects"
    ):
        """
        Initialize the renderer.
        
        Args:
            width: Window width
            height: Window height
            title: Window title
            
        Raises:
            RuntimeError: If GLFW or window initialization fails
        """
        self._width = width
        self._height = height
        self._window = None
        self._vao = None
        self._vbo = None
        self._ebo = None
        
        # Managers
        self._shader_manager = ShaderManager()
        self._texture_manager = TextureManager()
        
        # 3D rendering
        self._object_creator = ObjectCreator()
        self._object_renderer = None
        
        self._initialize_glfw(width, height, title)
        self._setup_camera_quad()
        self._setup_3d_scene()
        
    def _initialize_glfw(self, width: int, height: int, title: str) -> None:
        """Initialize GLFW and create window."""
        if not glfw.init():
            raise RuntimeError("Failed to initialize GLFW")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        self._window = glfw.create_window(width, height, title, None, None)
        if not self._window:
            glfw.terminate()
            raise RuntimeError("Failed to create GLFW window")

        glfw.make_context_current(self._window)
        glfw.set_framebuffer_size_callback(self._window, self._framebuffer_size_callback)
        
        # Get actual framebuffer size
        fb_width, fb_height = glfw.get_framebuffer_size(self._window)
        glViewport(0, 0, fb_width, fb_height)
        glClearColor(0.1, 0.1, 0.1, 1.0)
        
        logger.info(f"GLFW initialized: window={width}x{height}, framebuffer={fb_width}x{fb_height}")
    
    def _setup_camera_quad(self) -> None:
        """Setup fullscreen quad for camera feed."""
        # Create shader program for camera
        self._shader_manager.create_program(
            "camera",
            CAMERA_VERTEX_SHADER,
            CAMERA_FRAGMENT_SHADER
        )
        
        # Fullscreen quad vertices (position + texcoord)
        vertices = np.array([
            # x     y     z     u     v
            -1.0, -1.0, 0.0,  0.0,  1.0,  # Bottom-left (flipped V)
             1.0, -1.0, 0.0,  1.0,  1.0,  # Bottom-right
             1.0,  1.0, 0.0,  1.0,  0.0,  # Top-right
            -1.0,  1.0, 0.0,  0.0,  0.0,  # Top-left
        ], dtype=np.float32)
        
        indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

        # Create VAO, VBO, EBO
        self._vao = glGenVertexArrays(1)
        self._vbo = glGenBuffers(1)
        self._ebo = glGenBuffers(1)

        glBindVertexArray(self._vao)
        
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        stride = 5 * 4  # 5 floats per vertex
        
        # Position attribute
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        # Texcoord attribute
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)

        glBindVertexArray(0)

        # Create camera texture
        self._texture_manager.create_texture("camera")
        
        logger.info("Camera quad setup complete")
    
    def _setup_3d_scene(self) -> None:
        """Setup 3D object and renderer."""
        self._object_renderer = ObjectRenderer()
        
        # Load texture from URL
        url = "https://storage.googleapis.com/bucket-fi-production-apps-0672ab2d/original/images/tlx4czh0flso7d9f54vayrl4.webp"
        texture_img = load_image_from_url(url)
        
        # Create object from image
        aspect_ratio = texture_img.shape[1] / texture_img.shape[0]
        self._object_creator.create_from_image(aspect_ratio)
        self._object_creator.set_texture(texture_img)
        
        logger.info("3D scene setup complete")
    
    def draw_frame(self, frame: np.ndarray) -> None:
        """
        Render a complete frame with camera feed and 3D objects.
        
        Args:
            frame: Camera frame (BGR format from OpenCV)
        """
        if frame is None:
            return
        
        # Get actual framebuffer size
        fb_width, fb_height = glfw.get_framebuffer_size(self._window)
        
        # Process camera frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_flipped = cv2.flip(frame_rgb, 0)  # Flip vertically for OpenGL
        
        # Resize frame to match window aspect ratio to avoid distortion
        window_aspect = fb_width / fb_height
        frame_aspect = frame.shape[1] / frame.shape[0]
        
        if abs(window_aspect - frame_aspect) > 0.01:
            # Calculate dimensions to maintain aspect ratio
            if window_aspect > frame_aspect:
                # Window is wider - fit height
                new_height = fb_height
                new_width = int(fb_height * frame_aspect)
            else:
                # Window is taller - fit width
                new_width = fb_width
                new_height = int(fb_width / frame_aspect)
            
            frame_resized = cv2.resize(frame_flipped, (new_width, new_height))
            
            # Create black canvas and center the frame
            canvas = np.zeros((fb_height, fb_width, 3), dtype=np.uint8)
            y_offset = (fb_height - new_height) // 2
            x_offset = (fb_width - new_width) // 2
            canvas[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = frame_resized
            frame_final = canvas
        else:
            frame_final = cv2.resize(frame_flipped, (fb_width, fb_height))
        
        # Update camera texture
        camera_tex = self._texture_manager.get_texture("camera")
        self._texture_manager.update_texture(camera_tex, frame_final)
        
        # Set viewport to full framebuffer
        glViewport(0, 0, fb_width, fb_height)
        
        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # ===== STEP 1: Draw camera feed as background =====
        self._render_camera_feed(camera_tex)

        # ===== STEP 2: Draw 3D objects on top =====
        self._render_3d_objects(fb_width, fb_height)

        # Swap buffers and poll events
        glfw.swap_buffers(self._window)
        glfw.poll_events()
    
    def _render_camera_feed(self, camera_tex: int) -> None:
        """Render camera feed as fullscreen background."""
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        
        program = self._shader_manager.use_program("camera")
        self._texture_manager.bind_texture(camera_tex, 0)
        
        glBindVertexArray(self._vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
    
    def _render_3d_objects(self, width: int, height: int) -> None:
        """Render 3D objects with depth testing."""
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glClear(GL_DEPTH_BUFFER_BIT)  # Clear only depth buffer
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Create pose matrix - position object in view
        pose = np.eye(4, dtype=np.float32)
        pose[2, 3] = 1.5  # Move forward (toward camera)
        
        # Render object
        self._object_renderer.render(pose, self._object_creator, width, height)
        
        glDisable(GL_BLEND)
    
    def _framebuffer_size_callback(self, window, width: int, height: int) -> None:
        """Handle window resize events."""
        glViewport(0, 0, width, height)
        logger.info(f"Window resized: {width}x{height}")
    
    @property
    def should_close(self) -> bool:
        """Check if window should close."""
        return glfw.window_should_close(self._window)
    
    @property
    def window_size(self) -> tuple:
        """Get window size."""
        return (self._width, self._height)
    
    def terminate(self) -> None:
        """Cleanup and terminate renderer."""
        # Cleanup OpenGL resources
        if self._vao is not None:
            glDeleteVertexArrays(1, [self._vao])
        if self._vbo is not None:
            glDeleteBuffers(1, [self._vbo])
        if self._ebo is not None:
            glDeleteBuffers(1, [self._ebo])
        
        # Cleanup managers
        self._shader_manager.cleanup()
        self._texture_manager.cleanup()
        self._object_creator.cleanup()
        if self._object_renderer:
            self._object_renderer.cleanup()
        
        # Terminate GLFW
        glfw.terminate()
        logger.info("Renderer terminated")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.terminate()