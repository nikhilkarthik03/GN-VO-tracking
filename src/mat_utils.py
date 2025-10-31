"""Matrix utilities for 3D transformations."""
import numpy as np
from math import tan, radians, cos, sin
from typing import Tuple, Union, List


class MatUtils:
    """Utility class for creating transformation matrices."""
    
    @staticmethod
    def perspective(
        fov_y: float,
        aspect: float,
        near: float,
        far: float
    ) -> np.ndarray:
        """
        Create perspective projection matrix.
        
        Args:
            fov_y: Field of view in Y direction (degrees)
            aspect: Aspect ratio (width / height)
            near: Near clipping plane
            far: Far clipping plane
            
        Returns:
            4x4 perspective projection matrix
        """
        f = 1.0 / tan(radians(fov_y) / 2.0)
        mat = np.zeros((4, 4), dtype=np.float32)
        mat[0, 0] = f / aspect
        mat[1, 1] = f
        mat[2, 2] = (far + near) / (near - far)
        mat[2, 3] = (2 * far * near) / (near - far)
        mat[3, 2] = -1.0
        return mat

    @staticmethod
    def look_at(
        eye: Union[List[float], np.ndarray],
        target: Union[List[float], np.ndarray],
        up: Union[List[float], np.ndarray]
    ) -> np.ndarray:
        """
        Create look-at view matrix.
        
        Args:
            eye: Camera position
            target: Point to look at
            up: Up direction vector
            
        Returns:
            4x4 view matrix
        """
        eye = np.array(eye, dtype=np.float32)
        target = np.array(target, dtype=np.float32)
        up = np.array(up, dtype=np.float32)

        # Calculate forward vector (from eye to target)
        forward = target - eye
        forward /= np.linalg.norm(forward)

        # Calculate right vector
        right = np.cross(forward, up)
        right /= np.linalg.norm(right)

        # Recalculate up vector
        up_recalc = np.cross(right, forward)

        # Build view matrix
        mat = np.identity(4, dtype=np.float32)
        mat[0, :3] = right
        mat[1, :3] = up_recalc
        mat[2, :3] = -forward
        mat[0, 3] = -np.dot(right, eye)
        mat[1, 3] = -np.dot(up_recalc, eye)
        mat[2, 3] = np.dot(forward, eye)
        
        return mat

    @staticmethod
    def translate(x: float, y: float, z: float) -> np.ndarray:
        """
        Create translation matrix.
        
        Args:
            x: Translation in X direction
            y: Translation in Y direction
            z: Translation in Z direction
            
        Returns:
            4x4 translation matrix
        """
        mat = np.identity(4, dtype=np.float32)
        mat[0, 3] = x
        mat[1, 3] = y
        mat[2, 3] = z
        return mat

    @staticmethod
    def rotate_x(angle_deg: float) -> np.ndarray:
        """
        Create rotation matrix around X axis.
        
        Args:
            angle_deg: Rotation angle in degrees
            
        Returns:
            4x4 rotation matrix
        """
        angle = radians(angle_deg)
        c, s = cos(angle), sin(angle)
        mat = np.identity(4, dtype=np.float32)
        mat[1, 1] = c
        mat[1, 2] = -s
        mat[2, 1] = s
        mat[2, 2] = c
        return mat

    @staticmethod
    def rotate_y(angle_deg: float) -> np.ndarray:
        """
        Create rotation matrix around Y axis.
        
        Args:
            angle_deg: Rotation angle in degrees
            
        Returns:
            4x4 rotation matrix
        """
        angle = radians(angle_deg)
        c, s = cos(angle), sin(angle)
        mat = np.identity(4, dtype=np.float32)
        mat[0, 0] = c
        mat[0, 2] = s
        mat[2, 0] = -s
        mat[2, 2] = c
        return mat

    @staticmethod
    def rotate_z(angle_deg: float) -> np.ndarray:
        """
        Create rotation matrix around Z axis.
        
        Args:
            angle_deg: Rotation angle in degrees
            
        Returns:
            4x4 rotation matrix
        """
        angle = radians(angle_deg)
        c, s = cos(angle), sin(angle)
        mat = np.identity(4, dtype=np.float32)
        mat[0, 0] = c
        mat[0, 1] = -s
        mat[1, 0] = s
        mat[1, 1] = c
        return mat

    @staticmethod
    def scale(x: float, y: float, z: float) -> np.ndarray:
        """
        Create scale matrix.
        
        Args:
            x: Scale factor in X direction
            y: Scale factor in Y direction
            z: Scale factor in Z direction
            
        Returns:
            4x4 scale matrix
        """
        mat = np.identity(4, dtype=np.float32)
        mat[0, 0] = x
        mat[1, 1] = y
        mat[2, 2] = z
        return mat

    @staticmethod
    def multiply(*matrices: np.ndarray) -> np.ndarray:
        """
        Multiply multiple matrices together.
        
        Args:
            *matrices: Variable number of matrices to multiply
            
        Returns:
            Result of matrix multiplication
        """
        if len(matrices) == 0:
            return np.identity(4, dtype=np.float32)
        
        result = matrices[0].astype(np.float32)
        for mat in matrices[1:]:
            result = np.dot(result, mat.astype(np.float32))
        
        return result.astype(np.float32)
    
    @staticmethod
    def inverse(mat: np.ndarray) -> np.ndarray:
        """
        Calculate matrix inverse.
        
        Args:
            mat: Input matrix
            
        Returns:
            Inverse matrix
        """
        return np.linalg.inv(mat).astype(np.float32)
    
    @staticmethod
    def transpose(mat: np.ndarray) -> np.ndarray:
        """
        Transpose matrix.
        
        Args:
            mat: Input matrix
            
        Returns:
            Transposed matrix
        """
        return mat.T.astype(np.float32)