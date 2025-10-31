"""3D object rendering with shader management."""
import logging
from typing import Optional, Dict, Any
import numpy as np
from OpenGL.GL import *

from src.shader_manager import ShaderManager
from src.mat_utils import MatUtils

logger = logging.getLogger(__name__)


# Default shader sources
DEFAULT_VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 a_position;
layout (location = 1) in vec2 a_texCoord;
layout (location = 2) in vec3 a_normal;

uniform mat4 u_mvp;

out vec2 TexCoord;
out vec3 Normal;

void main() {
    gl_Position = u_mvp * vec4(a_position, 1.0);
    TexCoord = a_texCoord;
    Normal = a_normal;
}
"""

DEFAULT_FRAGMENT_SHADER = """
#version 330 core
in vec2 TexCoord;
in vec3 Normal;
out vec4 FragColor;
uniform sampler2D tex;

void main() {
    vec3 light = normalize(vec3(0.2, 0.5, 1.0));
    float diff = max(dot(normalize(Normal), light), 0.3);
    vec3 color = texture(tex, TexCoord).rgb * diff;
    FragColor = vec4(color, 1.0);
}
"""

DEPTH_VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 a_position;
layout (location = 1) in vec2 a_texCoord;
layout (location = 2) in vec3 a_normal;

uniform mat4 u_mvp;

out vec2 TexCoord;
out vec3 Normal;
out vec3 coords;

void main() {
    gl_Position = u_mvp * vec4(a_position, 1.0);
    TexCoord = a_texCoord;
    Normal = a_normal;
    coords = a_position;
}
"""

DEPTH_FRAGMENT_SHADER = """
#version 330 core
in vec2 TexCoord;
in vec3 Normal;
in vec3 coords;

out vec4 FragColor;
uniform sampler2D tex;

void main() {
    FragColor = vec4(coords, 1.0);
}
"""


class ObjectRenderer:
    """Handles rendering of 3D objects with lighting and depth."""
    
    def __init__(
        self,
        fov_y: float = 60.0,
        near: float = 0.01,
        far: float = 3.0,
        vertex_shader: Optional[str] = None,
        fragment_shader: Optional[str] = None
    ):
        """
        Initialize object renderer.
        
        Args:
            fov_y: Field of view in Y direction (degrees)
            near: Near clipping plane
            far: Far clipping plane
            vertex_shader: Custom vertex shader source
            fragment_shader: Custom fragment shader source
        """
        self._fov_y = fov_y
        self._near_plane = near
        self._far_plane = far
        
        # View matrix: look from origin toward +Z with up +Y
        self._view = MatUtils.look_at([0, 0, 0], [0, 0, 1], [0, 1, 0])
        
        # Shader manager
        self._shader_manager = ShaderManager()
        
        # Create shader programs
        self._setup_shaders(vertex_shader, fragment_shader)
        
        # Float framebuffer for depth rendering
        self._float_framebuffer: Optional[Dict[str, Any]] = None
        
        logger.info("ObjectRenderer initialized")
    
    def _setup_shaders(
        self,
        vertex_shader: Optional[str],
        fragment_shader: Optional[str]
    ) -> None:
        """Setup shader programs."""
        # Main rendering program
        vs = vertex_shader if vertex_shader else DEFAULT_VERTEX_SHADER
        fs = fragment_shader if fragment_shader else DEFAULT_FRAGMENT_SHADER
        self._shader_manager.create_program("main", vs, fs)
        
        # Depth rendering program
        self._shader_manager.create_program(
            "depth",
            DEPTH_VERTEX_SHADER,
            DEPTH_FRAGMENT_SHADER
        )
    
    @property
    def fov_y(self) -> float:
        """Get field of view."""
        return self._fov_y
    
    @property
    def near_plane(self) -> float:
        """Get near clipping plane."""
        return self._near_plane
    
    @property
    def far_plane(self) -> float:
        """Get far clipping plane."""
        return self._far_plane
    
    @property
    def view(self) -> np.ndarray:
        """Get view matrix."""
        return self._view.copy()
    
    @property
    def program(self) -> int:
        """Get main shader program ID."""
        return self._shader_manager.get_program("main")
    
    @property
    def obj_program(self) -> int:
        """Get OBJ shader program ID (same as main for now)."""
        return self.program
    
    def render(
        self,
        pose: np.ndarray,
        object_creator,
        width: int,
        height: int
    ) -> np.ndarray:
        """
        Render object with color and lighting.
        
        Args:
            pose: Model transformation matrix
            object_creator: ObjectCreator instance
            width: Viewport width
            height: Viewport height
            
        Returns:
            Projection matrix used
        """
        glViewport(0, 0, width, height)
        
        # Enable depth testing
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        # Calculate projection matrix
        projection = MatUtils.perspective(
            self._fov_y,
            width / height,
            self._near_plane,
            self._far_plane
        )
        
        # Choose appropriate program
        is_obj = getattr(object_creator, "is_obj_loaded", False)
        program_name = "main"  # Could use different program for OBJ files
        program = self._shader_manager.use_program(program_name)
        
        # Calculate MVP matrix
        model_view = np.dot(self._view, pose)
        mvp = np.dot(projection, model_view)
        
        # Set uniforms
        self._set_mvp_uniform(program, mvp)
        
        # Bind object and render
        object_creator.bind(program)
        self._draw_elements(object_creator)
        
        return projection
    
    def render_coords(
        self,
        pose: np.ndarray,
        object_creator,
        width: int,
        height: int
    ) -> np.ndarray:
        """
        Render object coordinates to float framebuffer.
        
        Args:
            pose: Model transformation matrix
            object_creator: ObjectCreator instance
            width: Viewport width
            height: Viewport height
            
        Returns:
            Projection matrix used
        """
        # Ensure float framebuffer exists and matches size
        if (self._float_framebuffer is None or
            self._float_framebuffer["width"] != width or
            self._float_framebuffer["height"] != height):
            self._cleanup_float_framebuffer()
            self._float_framebuffer = self._create_float_framebuffer(width, height)

        # Bind framebuffer
        fb = self._float_framebuffer["framebuffer"]
        glBindFramebuffer(GL_FRAMEBUFFER, fb)
        glViewport(0, 0, width, height)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        # Calculate projection
        projection = MatUtils.perspective(
            self._fov_y,
            width / height,
            self._near_plane,
            self._far_plane
        )
        
        # Use depth program
        program = self._shader_manager.use_program("depth")
        
        # Calculate MVP
        model_view = np.dot(self._view, pose)
        mvp = np.dot(projection, model_view)
        
        # Set uniforms
        self._set_mvp_uniform(program, mvp)
        
        # Bind and render
        object_creator.bind(program)
        self._draw_elements(object_creator)

        # Unbind framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        
        return projection
    
    def _set_mvp_uniform(self, program: int, mvp: np.ndarray) -> None:
        """Set MVP uniform in shader."""
        loc = glGetUniformLocation(program, "u_mvp")
        if loc != -1:
            glUniformMatrix4fv(loc, 1, GL_FALSE, mvp.astype(np.float32))
    
    def _draw_elements(self, object_creator) -> None:
        """Draw object using indexed rendering."""
        index_count = object_creator.index_count
        
        # Determine index type
        indices = getattr(object_creator, "_indices", None)
        if isinstance(indices, np.ndarray) and indices.dtype == np.uint16:
            index_type = GL_UNSIGNED_SHORT
        else:
            index_type = GL_UNSIGNED_INT
        
        glDrawElements(GL_TRIANGLES, index_count, index_type, None)
    
    def _create_float_framebuffer(self, width: int, height: int) -> Dict[str, Any]:
        """
        Create framebuffer with float color attachment.
        
        Args:
            width: Framebuffer width
            height: Framebuffer height
            
        Returns:
            Dict with framebuffer, texture, depthbuffer, width, height
        """
        # Create texture
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA32F,
            width, height, 0,
            GL_RGBA, GL_FLOAT, None
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        # Create depth renderbuffer
        depthbuffer = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, depthbuffer)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, width, height)

        # Create framebuffer
        framebuffer = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            GL_TEXTURE_2D,
            texture,
            0
        )
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER,
            GL_DEPTH_ATTACHMENT,
            GL_RENDERBUFFER,
            depthbuffer
        )

        # Check status
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            logger.error(f"Framebuffer incomplete: {hex(status)}")

        # Unbind
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glBindRenderbuffer(GL_RENDERBUFFER, 0)
        glBindTexture(GL_TEXTURE_2D, 0)

        logger.info(f"Created float framebuffer: {width}x{height}")
        
        return {
            "framebuffer": framebuffer,
            "texture": texture,
            "depthbuffer": depthbuffer,
            "width": width,
            "height": height,
        }
    
    def _cleanup_float_framebuffer(self) -> None:
        """Cleanup float framebuffer resources."""
        if self._float_framebuffer:
            glDeleteFramebuffers(1, [self._float_framebuffer["framebuffer"]])
            glDeleteRenderbuffers(1, [self._float_framebuffer["depthbuffer"]])
            glDeleteTextures(1, [self._float_framebuffer["texture"]])
            self._float_framebuffer = None
    
    def get_float_framebuffer(self) -> Optional[int]:
        """Get float framebuffer ID."""
        if self._float_framebuffer is None:
            return None
        return self._float_framebuffer["framebuffer"]
    
    def cleanup(self) -> None:
        """Cleanup renderer resources."""
        self._cleanup_float_framebuffer()
        self._shader_manager.cleanup()
        logger.info("ObjectRenderer cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()