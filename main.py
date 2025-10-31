from src.camera import Camera
from src.renderer import Renderer

def main():
    cam = Camera()
    renderer = Renderer()

    try:
        while not renderer.should_close():
            frame = cam.get_frame()
            if frame is None:
                continue
            renderer.draw_frame(frame)
    except KeyboardInterrupt:
        pass
    finally:
        cam.release()
        renderer.terminate()

if __name__ == "__main__":
    main()
