export class Camera {
  private stream: MediaStream | null = null;
  private video: HTMLVideoElement;

  constructor() {
    this.video = document.createElement("video");
    this.video.autoplay = true;
    this.video.playsInline = true;
  }

  async start(constraints?: MediaStreamConstraints): Promise<void> {
    try {
      const defaultConstraints: MediaStreamConstraints = {
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: "user",
        },
        audio: false,
      };

      this.stream = await navigator.mediaDevices.getUserMedia(
        constraints || defaultConstraints
      );

      this.video.srcObject = this.stream;

      // Wait for video to be ready
      await new Promise<void>((resolve) => {
        this.video.onloadedmetadata = () => {
          this.video.play();
          resolve();
        };
      });
    } catch (error) {
      console.error("Error accessing camera:", error);
      throw error;
    }
  }

  stop(): void {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
  }

  getVideo(): HTMLVideoElement {
    return this.video;
  }

  getAspectRatio(): number {
    return this.video.videoWidth / this.video.videoHeight;
  }

  getVideoWidth(): number {
    return this.video.videoWidth;
  }

  getVideoHeight(): number {
    return this.video.videoHeight;
  }
}
