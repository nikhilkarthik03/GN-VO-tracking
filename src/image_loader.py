"""Image loading utilities."""
import numpy as np
import cv2
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ImageLoadError(Exception):
    """Exception raised for image loading errors."""
    pass


def load_image_from_url(url: str, timeout: int = 10) -> np.ndarray:
    """
    Download and load image from a URL.
    
    Args:
        url: Image URL
        timeout: Request timeout in seconds
        
    Returns:
        Image as numpy array in RGB format
        
    Raises:
        ImageLoadError: If download or decoding fails
    """
    try:
        logger.info(f"Downloading image from {url}")
        response = requests.get(url, timeout=timeout)
        
        if response.status_code != 200:
            raise ImageLoadError(
                f"Failed to download image. Status code: {response.status_code}"
            )
        
        # Decode image from bytes
        data = np.frombuffer(response.content, np.uint8)
        img_bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)
        
        if img_bgr is None:
            raise ImageLoadError("Failed to decode image data")
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        logger.info(f"Image loaded: {img_rgb.shape[1]}x{img_rgb.shape[0]}")
        return img_rgb
        
    except requests.RequestException as e:
        raise ImageLoadError(f"Network error while downloading image: {e}")
    except Exception as e:
        raise ImageLoadError(f"Unexpected error loading image: {e}")


def load_image_from_file(filepath: str) -> np.ndarray:
    """
    Load image from local file.
    
    Args:
        filepath: Path to image file
        
    Returns:
        Image as numpy array in RGB format
        
    Raises:
        ImageLoadError: If file cannot be read or decoded
    """
    try:
        logger.info(f"Loading image from {filepath}")
        img_bgr = cv2.imread(filepath, cv2.IMREAD_COLOR)
        
        if img_bgr is None:
            raise ImageLoadError(f"Failed to load image from {filepath}")
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        logger.info(f"Image loaded: {img_rgb.shape[1]}x{img_rgb.shape[0]}")
        return img_rgb
        
    except Exception as e:
        raise ImageLoadError(f"Error loading image from file: {e}")


def resize_image(
    image: np.ndarray,
    width: Optional[int] = None,
    height: Optional[int] = None,
    maintain_aspect: bool = True
) -> np.ndarray:
    """
    Resize image to specified dimensions.
    
    Args:
        image: Input image
        width: Target width (None to calculate from height)
        height: Target height (None to calculate from width)
        maintain_aspect: If True, maintain aspect ratio
        
    Returns:
        Resized image
        
    Raises:
        ValueError: If neither width nor height is specified
    """
    if width is None and height is None:
        raise ValueError("Must specify at least width or height")
    
    h, w = image.shape[:2]
    
    if maintain_aspect:
        if width is not None and height is None:
            aspect = w / h
            height = int(width / aspect)
        elif height is not None and width is None:
            aspect = w / h
            width = int(height * aspect)
    else:
        if width is None:
            width = w
        if height is None:
            height = h
    
    resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)
    logger.debug(f"Image resized: {w}x{h} -> {width}x{height}")
    
    return resized