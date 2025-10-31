"""Texture management for OpenGL."""
import numpy as np
from OpenGL.GL import *
import logging

logger = logging.getLogger(__name__)


class TextureManager:
    """Manages OpenGL textures."""
    
    def __init__(self):
        """Initialize texture manager."""
        self._textures = {}
        
    def create_texture(
        self,
        name: str,
        min_filter: int = GL_LINEAR,
        mag_filter: int = GL_LINEAR,
        wrap_s: int = GL_CLAMP_TO_EDGE,
        wrap_t: int = GL_CLAMP_TO_EDGE
    ) -> int:
        """
        Create a new texture.
        
        Args:
            name: Unique identifier for the texture
            min_filter: Minification filter
            mag_filter: Magnification filter
            wrap_s: Wrapping mode for S coordinate
            wrap_t: Wrapping mode for T coordinate
            
        Returns:
            Texture ID
        """
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, min_filter)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, mag_filter)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap_s)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap_t)
        
        self._textures[name] = tex_id
        logger.info(f"Created texture '{name}' with ID {tex_id}")
        return tex_id
    
    def update_texture(self, tex_id: int, image: np.ndarray) -> None:
        """
        Update texture data.
        
        Args:
            tex_id: Texture ID to update
            image: Image data as numpy array (RGB format)
        """
        glBindTexture(GL_TEXTURE_2D, tex_id)
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) > 2 else 1
        
        format_map = {1: GL_RED, 3: GL_RGB, 4: GL_RGBA}
        gl_format = format_map.get(channels, GL_RGB)
        
        glTexImage2D(
            GL_TEXTURE_2D, 0, gl_format,
            width, height, 0,
            gl_format, GL_UNSIGNED_BYTE, image
        )
    
    def get_texture(self, name: str) -> int:
        """Get texture ID by name."""
        return self._textures.get(name, 0)
    
    def bind_texture(self, tex_id: int, unit: int = 0) -> None:
        """Bind texture to a texture unit."""
        glActiveTexture(GL_TEXTURE0 + unit)
        glBindTexture(GL_TEXTURE_2D, tex_id)
    
    def delete_texture(self, name: str) -> None:
        """Delete a texture by name."""
        if name in self._textures:
            glDeleteTextures(1, [self._textures[name]])
            del self._textures[name]
            logger.info(f"Deleted texture '{name}'")
    
    def cleanup(self) -> None:
        """Delete all managed textures."""
        for name, tex_id in self._textures.items():
            glDeleteTextures(1, [tex_id])
            logger.debug(f"Deleted texture '{name}'")
        self._textures.clear()
        logger.info("Texture manager cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()