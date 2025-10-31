"""Camera module for video capture."""
import cv2
import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)


class Camera:
    """Handles camera capture and frame management."""
    
    def __init__(self, index: int = 0, width: int = 640, height: int = 480):
        """
        Initialize camera capture.
        
        Args:
            index: Camera device index
            width: Desired frame width
            height: Desired frame height
            
        Raises:
            RuntimeError: If camera cannot be opened
        """
        self._index = index
        self._width = width
        self._height = height
        self._cap = None
        self._initialize_camera()
        
    def _initialize_camera(self) -> None:
        """Initialize the video capture device."""
        self._cap = cv2.VideoCapture(self._index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera with index {self._index}")
            
        logger.info(f"Camera initialized: {self._width}x{self._height}")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from the camera.
        
        Returns:
            Frame as numpy array (BGR format) or None if capture failed
        """
        if self._cap is None or not self._cap.isOpened():
            logger.error("Camera not initialized or closed")
            return None
            
        ret, frame = self._cap.read()
        if not ret:
            logger.warning("Failed to capture frame")
            return None
            
        return frame
    
    @property
    def width(self) -> int:
        """Get camera frame width."""
        return self._width
    
    @property
    def height(self) -> int:
        """Get camera frame height."""
        return self._height
    
    @property
    def is_opened(self) -> bool:
        """Check if camera is opened."""
        return self._cap is not None and self._cap.isOpened()
    
    def release(self) -> None:
        """Release the camera resources."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("Camera released")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
        return False
    
    def __del__(self):
        """Destructor to ensure camera is released."""
        self.release()