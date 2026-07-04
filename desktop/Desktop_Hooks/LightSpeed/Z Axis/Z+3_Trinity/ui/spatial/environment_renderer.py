"""
LightSpeed V0.9.11 - 3D Environment Renderer
Creates 3D background environments from images/videos using depth estimation

Features:
- Fake LIDAR from image (depth estimation)
- 3D point cloud generation
- Parallax occlusion mapping
- Video-based environment capture
- Real-time environment updates
- Trinity settings integration

Author: LightSpeed Team / ACHILLES
Version: 0.9.11
Date: January 4, 2026
"""

import tkinter as tk
from PIL import Image, ImageTk, ImageFilter, ImageEnhance
import numpy as np
from typing import Optional, Tuple, List
from pathlib import Path
from dataclasses import dataclass
import json

from core.config.paths import TRINITY_ENVIRONMENT, TRINITY_SETTINGS


@dataclass
class DepthPoint:
    """3D point with depth information"""
    x: float  # Screen X coordinate
    y: float  # Screen Y coordinate
    depth: float  # Estimated depth (0.0 = far, 1.0 = near)
    color: Tuple[int, int, int]  # RGB color


@dataclass
class EnvironmentLayer:
    """Parallax layer for 3D effect"""
    image: Image.Image
    depth: float  # Layer depth (0.0 = background, 1.0 = foreground)
    offset_x: float  # Parallax offset X
    offset_y: float  # Parallax offset Y


class FakeLidarDepthEstimator:
    """
    Fake LIDAR depth estimation from 2D images.

    Uses edge detection, brightness, and blur to estimate depth.
    This is a simplified approach - for production, consider using
    proper depth estimation models (MiDaS, DPT, etc.)
    """

    def estimate_depth(self, image: Image.Image) -> np.ndarray:
        """
        Estimate depth map from image.

        Args:
            image: Input PIL image

        Returns:
            Numpy array (H, W) with depth values 0.0-1.0
        """
        # Convert to grayscale for analysis
        gray = image.convert('L')
        width, height = gray.size

        # Method 1: Edge detection (edges are likely closer)
        edges = gray.filter(ImageFilter.FIND_EDGES)
        edge_array = np.array(edges, dtype=np.float32) / 255.0

        # Method 2: Brightness (darker = farther, assuming typical lighting)
        brightness = np.array(gray, dtype=np.float32) / 255.0

        # Method 3: Blur gradient (sharp = near, blurry = far)
        blurred = gray.filter(ImageFilter.GaussianBlur(5))
        sharpness = np.abs(np.array(gray, dtype=np.float32) - np.array(blurred, dtype=np.float32))
        sharpness = sharpness / (sharpness.max() + 1e-6)  # Normalize

        # Combine methods (weighted average)
        depth_map = (
            0.4 * edge_array +
            0.3 * brightness +
            0.3 * sharpness
        )

        # Normalize to 0-1 range
        depth_map = (depth_map - depth_map.min()) / (depth_map.max() - depth_map.min() + 1e-6)

        # Invert if needed (we want near=1.0, far=0.0)
        # For this heuristic, edges/bright areas are near

        return depth_map

    def generate_point_cloud(self, image: Image.Image, depth_map: np.ndarray,
                            sample_rate: int = 4) -> List[DepthPoint]:
        """
        Generate 3D point cloud from image and depth map.

        Args:
            image: Source image
            depth_map: Depth map (same size as image)
            sample_rate: Sample every Nth pixel (for performance)

        Returns:
            List of DepthPoint objects
        """
        width, height = image.size
        pixels = image.load()
        points = []

        for y in range(0, height, sample_rate):
            for x in range(0, width, sample_rate):
                depth = depth_map[y, x]
                color = pixels[x, y]

                # Convert to RGB if needed
                if isinstance(color, int):
                    color = (color, color, color)

                points.append(DepthPoint(
                    x=float(x),
                    y=float(y),
                    depth=float(depth),
                    color=color[:3]  # RGB only
                ))

        return points


class EnvironmentRenderer:
    """
    3D environment renderer for spatial UI backgrounds.

    Renders layered 3D environments from images/videos with parallax.
    """

    def __init__(self, canvas: tk.Canvas, width: int, height: int):
        """
        Initialize environment renderer.

        Args:
            canvas: Tkinter canvas for rendering
            width: Canvas width
            height: Canvas height
        """
        self.canvas = canvas
        self.width = width
        self.height = height

        # Depth estimator
        self.lidar = FakeLidarDepthEstimator()

        # Environment state
        self.layers: List[EnvironmentLayer] = []
        self.point_cloud: List[DepthPoint] = []
        self.background_image: Optional[Image.Image] = None

        # Camera state (for parallax)
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.camera_z = 0.0  # Z-floor position

        # Rendering settings
        self.parallax_strength = 0.3
        self.depth_layers = 5  # Number of parallax layers
        self.enable_point_cloud = False  # Render point cloud overlay

        # Load settings from Trinity
        self._load_settings()

    def _load_settings(self):
        """Load environment rendering settings from Trinity"""
        settings_file = TRINITY_SETTINGS / "environment.json"

        try:
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)

                self.parallax_strength = settings.get("parallax_strength", 0.3)
                self.depth_layers = settings.get("depth_layers", 5)
                self.enable_point_cloud = settings.get("enable_point_cloud", False)

        except Exception as e:
            print(f"[ENV] Failed to load settings: {e}")

    def load_from_image(self, image_path: Path):
        """
        Load environment from image file.

        Args:
            image_path: Path to image file
        """
        try:
            # Load image
            image = Image.open(image_path)

            # Resize to canvas size
            image = image.resize((self.width, self.height), Image.Resampling.LANCZOS)

            self.background_image = image

            # Generate depth map
            print("[ENV] Generating depth map...")
            depth_map = self.lidar.estimate_depth(image)

            # Create parallax layers
            print(f"[ENV] Creating {self.depth_layers} parallax layers...")
            self._create_layers(image, depth_map)

            # Generate point cloud (optional)
            if self.enable_point_cloud:
                print("[ENV] Generating point cloud...")
                self.point_cloud = self.lidar.generate_point_cloud(image, depth_map, sample_rate=8)

            print("[ENV] Environment loaded successfully")

        except Exception as e:
            print(f"[ENV] Failed to load image: {e}")

    def _create_layers(self, image: Image.Image, depth_map: np.ndarray):
        """Create parallax layers from image and depth map"""
        self.layers.clear()

        height, width = depth_map.shape

        # Split into depth layers
        for i in range(self.depth_layers):
            # Depth range for this layer
            depth_min = i / self.depth_layers
            depth_max = (i + 1) / self.depth_layers

            # Create mask for this depth range
            mask = np.logical_and(depth_map >= depth_min, depth_map < depth_max)

            # Create layer image with alpha channel
            layer_array = np.array(image.convert('RGBA'))

            # Apply mask to alpha channel
            alpha = (mask * 255).astype(np.uint8)
            layer_array[:, :, 3] = alpha

            layer_image = Image.fromarray(layer_array, 'RGBA')

            # Create layer
            layer = EnvironmentLayer(
                image=layer_image,
                depth=(depth_min + depth_max) / 2,  # Average depth
                offset_x=0.0,
                offset_y=0.0
            )

            self.layers.append(layer)

    def update_camera(self, x: float, y: float, z: float):
        """
        Update camera position for parallax effect.

        Args:
            x: Camera X offset
            y: Camera Y offset
            z: Z-floor position
        """
        self.camera_x = x
        self.camera_y = y
        self.camera_z = z

        # Update layer offsets based on camera
        for layer in self.layers:
            # Parallax: farther layers move less
            parallax_factor = layer.depth * self.parallax_strength

            layer.offset_x = -self.camera_x * parallax_factor
            layer.offset_y = -self.camera_y * parallax_factor

    def render(self):
        """Render environment to canvas"""
        # Clear previous environment
        self.canvas.delete('environment')

        if not self.background_image:
            return

        # Render layers back-to-front (painter's algorithm)
        sorted_layers = sorted(self.layers, key=lambda l: l.depth)

        for layer in sorted_layers:
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(layer.image)

            # Render with offset
            x = self.width // 2 + layer.offset_x
            y = self.height // 2 + layer.offset_y

            self.canvas.create_image(
                x, y,
                image=photo,
                anchor=tk.CENTER,
                tags='environment'
            )

            # Keep reference to prevent garbage collection
            if not hasattr(self, '_layer_photos'):
                self._layer_photos = []
            self._layer_photos.append(photo)

        # Render point cloud overlay (if enabled)
        if self.enable_point_cloud and self.point_cloud:
            self._render_point_cloud()

        # Send to back (behind tiles)
        self.canvas.tag_lower('environment')

    def _render_point_cloud(self):
        """Render point cloud overlay"""
        for point in self.point_cloud:
            # Apply parallax
            parallax_factor = point.depth * self.parallax_strength
            x = point.x - self.camera_x * parallax_factor
            y = point.y - self.camera_y * parallax_factor

            # Point size based on depth
            size = int(1 + point.depth * 3)

            # Color with depth-based brightness
            brightness = 0.5 + point.depth * 0.5
            r = int(point.color[0] * brightness)
            g = int(point.color[1] * brightness)
            b = int(point.color[2] * brightness)
            color = f'#{r:02x}{g:02x}{b:02x}'

            # Render point
            self.canvas.create_oval(
                x - size, y - size,
                x + size, y + size,
                fill=color,
                outline='',
                tags='environment'
            )

    def load_from_video(self, video_path: Path, frame_index: int = 0):
        """
        Load environment from video frame.

        Args:
            video_path: Path to video file
            frame_index: Which frame to use
        """
        try:
            # This requires opencv-python (cv2)
            import cv2

            # Open video
            cap = cv2.VideoCapture(str(video_path))

            # Seek to frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

            # Read frame
            ret, frame = cap.read()
            cap.release()

            if not ret:
                print(f"[ENV] Failed to read frame {frame_index} from video")
                return

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image
            image = Image.fromarray(frame_rgb)

            # Save to temp file and load
            temp_path = TRINITY_ENVIRONMENT / "temp_frame.png"
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(temp_path)

            self.load_from_image(temp_path)

            print(f"[ENV] Loaded video frame {frame_index}")

        except ImportError:
            print("[ENV] opencv-python not installed (pip install opencv-python)")
        except Exception as e:
            print(f"[ENV] Failed to load video: {e}")

    def apply_3d_structure(self, depth_threshold: float = 0.6):
        """
        Apply 3D structure to environment (make structures pop out).

        Args:
            depth_threshold: Depth value above which structures are enhanced
        """
        if not self.background_image:
            return

        # Regenerate depth map
        depth_map = self.lidar.estimate_depth(self.background_image)

        # Enhance near structures
        enhanced_image = self.background_image.copy().convert('RGBA')
        pixels = enhanced_image.load()

        height, width = depth_map.shape

        for y in range(height):
            for x in range(width):
                if depth_map[y, x] > depth_threshold:
                    # Enhance brightness and saturation for near objects
                    r, g, b, a = pixels[x, y]

                    # Increase brightness
                    factor = 1.2
                    r = min(255, int(r * factor))
                    g = min(255, int(g * factor))
                    b = min(255, int(b * factor))

                    pixels[x, y] = (r, g, b, a)

        # Update background
        self.background_image = enhanced_image

        # Recreate layers
        self._create_layers(self.background_image, depth_map)

        print("[ENV] 3D structure enhancement applied")

    def save_environment(self, name: str):
        """
        Save current environment configuration.

        Args:
            name: Environment preset name
        """
        if not self.background_image:
            return

        try:
            # Save image
            env_dir = TRINITY_ENVIRONMENT / name
            env_dir.mkdir(parents=True, exist_ok=True)

            image_path = env_dir / "background.png"
            self.background_image.save(image_path)

            # Save metadata
            metadata = {
                "name": name,
                "parallax_strength": self.parallax_strength,
                "depth_layers": self.depth_layers,
                "enable_point_cloud": self.enable_point_cloud,
                "width": self.width,
                "height": self.height
            }

            metadata_path = env_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"[ENV] Environment '{name}' saved to {env_dir}")

        except Exception as e:
            print(f"[ENV] Failed to save environment: {e}")

    def load_environment(self, name: str):
        """
        Load saved environment configuration.

        Args:
            name: Environment preset name
        """
        try:
            env_dir = TRINITY_ENVIRONMENT / name

            if not env_dir.exists():
                print(f"[ENV] Environment '{name}' not found")
                return

            # Load metadata
            metadata_path = env_dir / "metadata.json"
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            # Load image
            image_path = env_dir / "background.png"
            self.load_from_image(image_path)

            # Apply settings
            self.parallax_strength = metadata.get("parallax_strength", 0.3)
            self.depth_layers = metadata.get("depth_layers", 5)
            self.enable_point_cloud = metadata.get("enable_point_cloud", False)

            print(f"[ENV] Environment '{name}' loaded")

        except Exception as e:
            print(f"[ENV] Failed to load environment: {e}")


# Export
__all__ = ['EnvironmentRenderer', 'FakeLidarDepthEstimator', 'DepthPoint', 'EnvironmentLayer']
