"""Shader compilation and program management."""
from OpenGL.GL import *
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class ShaderManager:
    """Manages shader compilation and program linking."""
    
    def __init__(self):
        """Initialize shader manager."""
        self._programs = {}
        
    @staticmethod
    def _compile_shader(source: str, shader_type: int) -> int:
        """
        Compile a shader from source.
        
        Args:
            source: Shader source code
            shader_type: GL_VERTEX_SHADER or GL_FRAGMENT_SHADER
            
        Returns:
            Compiled shader ID
            
        Raises:
            RuntimeError: If compilation fails
        """
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)

        if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
            info = glGetShaderInfoLog(shader).decode()
            shader_type_name = "vertex" if shader_type == GL_VERTEX_SHADER else "fragment"
            raise RuntimeError(f"{shader_type_name.capitalize()} shader compile failed:\n{info}")
            
        return shader
    
    def create_program(
        self,
        name: str,
        vertex_src: str,
        fragment_src: str
    ) -> int:
        """
        Create and link a shader program.
        
        Args:
            name: Unique identifier for the program
            vertex_src: Vertex shader source code
            fragment_src: Fragment shader source code
            
        Returns:
            Program ID
            
        Raises:
            RuntimeError: If linking fails
        """
        vert_shader = self._compile_shader(vertex_src, GL_VERTEX_SHADER)
        frag_shader = self._compile_shader(fragment_src, GL_FRAGMENT_SHADER)
        
        program = glCreateProgram()
        glAttachShader(program, vert_shader)
        glAttachShader(program, frag_shader)
        glLinkProgram(program)

        if glGetProgramiv(program, GL_LINK_STATUS) != GL_TRUE:
            info = glGetProgramInfoLog(program).decode()
            raise RuntimeError(f"Program '{name}' link failed:\n{info}")

        # Shaders can be deleted after linking
        glDeleteShader(vert_shader)
        glDeleteShader(frag_shader)
        
        self._programs[name] = program
        logger.info(f"Created shader program '{name}' with ID {program}")
        return program
    
    def get_program(self, name: str) -> int:
        """Get program ID by name."""
        return self._programs.get(name, 0)
    
    def use_program(self, name: str) -> int:
        """Use a shader program by name."""
        program = self.get_program(name)
        if program:
            glUseProgram(program)
        return program
    
    def delete_program(self, name: str) -> None:
        """Delete a program by name."""
        if name in self._programs:
            glDeleteProgram(self._programs[name])
            del self._programs[name]
            logger.info(f"Deleted program '{name}'")
    
    def cleanup(self) -> None:
        """Delete all managed programs."""
        for name, program in self._programs.items():
            glDeleteProgram(program)
            logger.debug(f"Deleted program '{name}'")
        self._programs.clear()
        logger.info("Shader manager cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()