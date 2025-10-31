import { Camera } from "./camera";
import "./style.css";
import { WebGLRenderer } from "./webgl";

// Set up the app
document.querySelector<HTMLDivElement>("#app")!.innerHTML = `
  <canvas id="gl-canvas"></canvas>
`;

const canvas = document.querySelector<HTMLCanvasElement>("#gl-canvas")!;

const camera = new Camera();
let renderer: WebGLRenderer | null = null;

// Function to calculate canvas dimensions maintaining aspect ratio
function calculateCanvasDimensions(videoAspectRatio: number): {
  width: number;
  height: number;
} {
  const containerWidth = window.innerWidth;
  const containerHeight = window.innerHeight;
  const containerAspectRatio = containerWidth / containerHeight;

  let width: number;
  let height: number;

  if (videoAspectRatio > containerAspectRatio) {
    // Video is wider than container
    width = containerWidth;
    height = containerWidth / videoAspectRatio;
  } else {
    // Video is taller than container
    height = containerHeight;
    width = containerHeight * videoAspectRatio;
  }

  return { width, height };
}

// Function to resize canvas
function resizeCanvas() {
  if (!camera.getVideoWidth() || !camera.getVideoHeight()) return;

  const videoAspectRatio = camera.getAspectRatio();
  const { width, height } = calculateCanvasDimensions(videoAspectRatio);

  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;

  // Set actual canvas resolution to match video
  const videoWidth = camera.getVideoWidth();
  const videoHeight = camera.getVideoHeight();

  if (renderer) {
    renderer.resize(videoWidth, videoHeight);
  }
}

// Render loop
function renderLoop() {
  if (renderer) {
    renderer.render(camera.getVideo());
    requestAnimationFrame(renderLoop);
  }
}

// Start camera automatically
async function startCamera() {
  try {
    await camera.start();

    // Initialize renderer
    renderer = new WebGLRenderer(canvas);

    // Set canvas dimensions
    resizeCanvas();

    // Start render loop
    renderLoop();
  } catch (error) {
    console.error("Failed to start camera:", error);
    alert(
      "Failed to access camera. Please ensure you have granted camera permissions."
    );
  }
}

// Handle window resize
window.addEventListener("resize", () => {
  resizeCanvas();
});

// Start camera on load
startCamera();
