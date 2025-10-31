from src.camera import Camera
from src.renderer import Renderer

def main():
    camera = Camera()
    renderer = Renderer()

    try:
        while not renderer.should_close():
            frame = camera.get_frame()
            if frame is None:
                continue
            renderer.draw_frame(frame)
    except KeyboardInterrupt:
        pass
    finally:
        camera.release()
        renderer.terminate()

if __name__ == "__main__":
    main()
