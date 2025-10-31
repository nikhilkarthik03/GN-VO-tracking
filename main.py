"""Main entry point for the application."""
import logging
from src.camera import Camera
from src.renderer import Renderer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main application loop."""
    camera = None
    renderer = None
    
    try:
        # Initialize camera and renderer
        camera = Camera(index=0, width=640, height=480)
        renderer = Renderer(width=640, height=480)
        
        logger.info("Application started - Press ESC or close window to exit")
        
        # Main render loop
        while not renderer.should_close:
            frame = camera.get_frame()
            if frame is not None:
                renderer.draw_frame(frame)
                
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        
    except Exception as e:
        logger.error(f"Error in main loop: {e}", exc_info=True)
        
    finally:
        # Cleanup resources
        if camera is not None:
            camera.release()
        if renderer is not None:
            renderer.terminate()
        logger.info("Application terminated")


if __name__ == "__main__":
    main()