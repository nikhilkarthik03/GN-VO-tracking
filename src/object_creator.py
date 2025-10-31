"""3D object creation and management."""
import numpy as np
from OpenGL.GL import *
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class ObjectCreator:
    """Creates and manages 3D object geometry and textures."""
    
    def __init__(self):
        """Initialize object creator."""
        self._vertices = np.array([], dtype=np.float32)
        self._indices = np.array([], dtype=np.uint32)
        self._vertex_buffer = None
        self._index_buffer = None
        self._texture = None
        self._corner_points = []
        self._is_obj_loaded = False
        
    @property
    def is_initialized(self) -> bool:
        """Check if buffers are initialized."""
        return self._vertex_buffer is not None and self._index_buffer is not None
    
    @property
    def is_obj_loaded(self) -> bool:
        """Check if OBJ was loaded."""
        return self._is_obj_loaded
    
    @property
    def index_count(self) -> int:
        """Get number of indices."""
        return len(self._indices)
    
    @property
    def corner_points(self) -> List[Tuple[float, float]]:
        """Get corner points of the object."""
        return self._corner_points.copy()
    
    def create_from_image(self, aspect_ratio: float) -> None:
        """
        Create a textured quad from aspect ratio.
        
        Args:
            aspect_ratio: Width / height ratio
        """
        half_width = 0.5
        half_height = 0.5

        if aspect_ratio > 1.0:
            half_width = aspect_ratio * 0.5
        else:
            half_height = 0.5 / aspect_ratio

        # Vertex format: x, y, z, u, v, nx, ny, nz
        vertices = np.array([
            [ half_width, -half_height, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
            [-half_width, -half_height, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            [-half_width,  half_height, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0],
            [ half_width,  half_height, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0],
        ], dtype=np.float32)

        indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)

        self._corner_points = [
            ( half_width, -half_height),
            (-half_width, -half_height),
            (-half_width,  half_height),
            ( half_width,  half_height),
        ]

        self._load_geometry(vertices, indices)
        logger.info(f"Created quad with aspect ratio {aspect_ratio:.2f}")
    
    def load_from_obj_string(self, obj_data: str) -> None:
        """
        Parse and load geometry from OBJ format string.
        
        Args:
            obj_data: OBJ format string
        """
        positions, texcoords, normals = [], [], []
        vertex_data = []
        index_data = []
        unique_vertex_map = {}

        for line in obj_data.splitlines():
            line = line.strip()
            
            if line.startswith("v "):
                parts = line.split()
                positions.append([float(parts[1]), float(parts[2]), float(parts[3])])
                
            elif line.startswith("vt "):
                parts = line.split()
                texcoords.append([float(parts[1]), float(parts[2])])
                
            elif line.startswith("vn "):
                parts = line.split()
                normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
                
            elif line.startswith("f "):
                parts = line.split()[1:]
                parts.reverse()  # Reverse winding order
                
                for part in parts:
                    vals = part.split("/")
                    vi = int(vals[0]) - 1 if len(vals) > 0 and vals[0] else 0
                    ti = int(vals[1]) - 1 if len(vals) > 1 and vals[1] else 0
                    ni = int(vals[2]) - 1 if len(vals) > 2 and vals[2] else 0
                    
                    key = f"{vi}/{ti}/{ni}"
                    if key not in unique_vertex_map:
                        pos = positions[vi] if vi < len(positions) else [0, 0, 0]
                        tex = texcoords[ti] if ti < len(texcoords) else [0, 0]
                        nor = normals[ni] if ni < len(normals) else [0, 0, 1]
                        vertex_data.append(pos + tex + nor)
                        unique_vertex_map[key] = len(vertex_data) - 1
                        
                    index_data.append(unique_vertex_map[key])

        vertices = np.array(vertex_data, dtype=np.float32)
        indices = np.array(index_data, dtype=np.uint32)
        
        self._is_obj_loaded = True
        self._load_geometry(vertices, indices)
        logger.info(f"Loaded OBJ: {len(vertices)} vertices, {len(indices)} indices")
    
    def _load_geometry(self, vertices: np.ndarray, indices: np.ndarray) -> None:
        """
        Load vertex and index data into GPU buffers.
        
        Args:
            vertices: Vertex data array
            indices: Index data array
        """
        self._vertices = vertices
        self._indices = indices

        # Generate and upload vertex buffer
        if self._vertex_buffer is None:
            self._vertex_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self._vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        # Generate and upload index buffer
        if self._index_buffer is None:
            self._index_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._index_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
    
    def set_texture(self, image_data: np.ndarray) -> None:
        """
        Upload texture data to GPU.
        
        Args:
            image_data: Image as numpy array (RGB format)
            
        Raises:
            TypeError: If image_data is not a numpy array
        """
        if not isinstance(image_data, np.ndarray):
            raise TypeError("Image data must be a numpy array")
        
        if self._texture is None:
            self._texture = glGenTextures(1)
            
        glBindTexture(GL_TEXTURE_2D, self._texture)
        
        height, width = image_data.shape[:2]
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGB, width, height,
            0, GL_RGB, GL_UNSIGNED_BYTE, image_data
        )
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        logger.info(f"Texture uploaded: {width}x{height}")
    
    def bind(self, program: int) -> None:
        stride = 8 * 4  # 8 floats per vertex (x,y,z, u,v, nx,ny,nz)

        glUseProgram(program)  # <-- ensure program is active

        glBindBuffer(GL_ARRAY_BUFFER, self._vertex_buffer)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._index_buffer)

        pos_loc = glGetAttribLocation(program, "a_position")
        tex_loc = glGetAttribLocation(program, "a_texCoord")
        norm_loc = glGetAttribLocation(program, "a_normal")

        logger.debug(f"Attrib locations: pos={pos_loc}, tex={tex_loc}, norm={norm_loc}")

        if pos_loc != -1:
            glEnableVertexAttribArray(pos_loc)
            glVertexAttribPointer(pos_loc, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        else:
            logger.warning("a_position attribute not found in shader")

        if tex_loc != -1:
            glEnableVertexAttribArray(tex_loc)
            glVertexAttribPointer(tex_loc, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(3 * 4))
        else:
            logger.warning("a_texCoord attribute not found in shader")

        if norm_loc != -1:
            glEnableVertexAttribArray(norm_loc)
            glVertexAttribPointer(norm_loc, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(5 * 4))
        else:
            logger.warning("a_normal attribute not found in shader")

        if self._texture is not None:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self._texture)

    def cleanup(self) -> None:
        """Release GPU resources."""
        if self._vertex_buffer is not None:
            glDeleteBuffers(1, [self._vertex_buffer])
            self._vertex_buffer = None
            
        if self._index_buffer is not None:
            glDeleteBuffers(1, [self._index_buffer])
            self._index_buffer = None
            
        if self._texture is not None:
            glDeleteTextures(1, [self._texture])
            self._texture = None
            
        logger.info("ObjectCreator cleaned up")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()