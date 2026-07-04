"""
Smart Theme Extractor
LightSpeed Type I Civilization Platform

Extracts color schemes from uploaded background photos using intelligent
color analysis to create cohesive, accessible UI themes.

Features:
- Dominant color extraction from images
- Complementary color generation
- Accessibility validation (WCAG contrast ratios)
- Automatic light/dark theme generation
- Integration with ThemeManager

Author: LightSpeed Team
Version: 5.1.2
Date: April 8, 2026
"""

from typing import Dict, Tuple, List, Optional
from pathlib import Path
import colorsys

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class SmartThemeExtractor:
    """
    Extract intelligent color schemes from background images.

    Uses color theory and accessibility guidelines to generate
    complete UI themes from a single background image.
    """

    def __init__(self):
        """Initialize smart theme extractor."""
        self.last_extracted_colors = None
        self.default_opacity = 0.95  # Default glassy opacity
        self.glassy_enabled = True  # Enable futuristic glassy interfaces

    def extract_dominant_colors(self, image_path: str, num_colors: int = 5) -> List[Tuple[int, int, int]]:
        """
        Extract dominant colors from image.

        Args:
            image_path: Path to image file
            num_colors: Number of dominant colors to extract

        Returns:
            List of RGB tuples representing dominant colors
        """
        if not HAS_PIL:
            raise ImportError("PIL (Pillow) required for image color extraction. Install with: pip install pillow")

        # Load and resize image for faster processing
        img = Image.open(image_path)
        img = img.convert('RGB')
        img.thumbnail((200, 200))

        # Get all pixels
        pixels = list(img.getdata())

        # Simple color quantization - group similar colors
        color_counts = {}
        for r, g, b in pixels:
            # Round to nearest 32 to group similar colors
            key = (r // 32 * 32, g // 32 * 32, b // 32 * 32)
            color_counts[key] = color_counts.get(key, 0) + 1

        # Get most common colors
        sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
        dominant = [color for color, count in sorted_colors[:num_colors]]

        return dominant

    def rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """
        Convert RGB tuple to hex color string.

        Args:
            rgb: RGB tuple (r, g, b)

        Returns:
            Hex color string (e.g., '#ff0000')
        """
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def rgba_to_hex(self, rgba: Tuple[int, int, int, float]) -> str:
        """
        Convert RGBA tuple to hex color string with alpha.

        Args:
            rgba: RGBA tuple (r, g, b, alpha) where alpha is 0.0-1.0

        Returns:
            Hex color string with alpha (e.g., '#ff0000cc')
        """
        r, g, b, a = rgba
        alpha_hex = int(a * 255)
        return f"#{r:02x}{g:02x}{b:02x}{alpha_hex:02x}"

    def rgb_with_opacity(self, rgb: Tuple[int, int, int], opacity: float = None) -> Tuple[int, int, int, float]:
        """
        Add opacity to RGB color for glassy interfaces.

        Args:
            rgb: RGB tuple (r, g, b)
            opacity: Opacity value (0.0-1.0), defaults to self.default_opacity

        Returns:
            RGBA tuple (r, g, b, alpha)
        """
        if opacity is None:
            opacity = self.default_opacity
        return (rgb[0], rgb[1], rgb[2], max(0.0, min(1.0, opacity)))

    def apply_glassy_effect(self, rgb: Tuple[int, int, int], opacity: float = 0.95) -> Dict[str, str]:
        """
        Apply glassy/translucent effect to color for futuristic UI.

        Args:
            rgb: RGB tuple (r, g, b)
            opacity: Opacity value (0.0-1.0)

        Returns:
            Dictionary with hex color and CSS-compatible rgba string
        """
        rgba = self.rgb_with_opacity(rgb, opacity)
        return {
            'hex': self.rgb_to_hex(rgb),
            'hex_alpha': self.rgba_to_hex(rgba),
            'rgba': f"rgba({rgba[0]}, {rgba[1]}, {rgba[2]}, {rgba[3]})",
            'opacity': opacity
        }

    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """
        Convert hex color to RGB tuple.

        Args:
            hex_color: Hex color string (e.g., '#ff0000')

        Returns:
            RGB tuple (r, g, b)
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def adjust_brightness(self, rgb: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """
        Adjust brightness of RGB color.

        Args:
            rgb: RGB tuple (r, g, b)
            factor: Brightness factor (< 1 darker, > 1 lighter)

        Returns:
            Adjusted RGB tuple
        """
        h, l, s = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        l = max(0, min(1, l * factor))
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return (int(r * 255), int(g * 255), int(b * 255))

    def adjust_saturation(self, rgb: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """
        Adjust saturation of RGB color.

        Args:
            rgb: RGB tuple (r, g, b)
            factor: Saturation factor (< 1 less saturated, > 1 more saturated)

        Returns:
            Adjusted RGB tuple
        """
        h, l, s = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        s = max(0, min(1, s * factor))
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return (int(r * 255), int(g * 255), int(b * 255))

    def get_complementary_color(self, rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Get complementary color (opposite on color wheel).

        Args:
            rgb: RGB tuple (r, g, b)

        Returns:
            Complementary RGB tuple
        """
        h, l, s = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        h = (h + 0.5) % 1.0  # Rotate 180 degrees
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return (int(r * 255), int(g * 255), int(b * 255))

    def calculate_contrast_ratio(self, rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int]) -> float:
        """
        Calculate WCAG contrast ratio between two colors.

        Args:
            rgb1: First RGB tuple
            rgb2: Second RGB tuple

        Returns:
            Contrast ratio (1.0 to 21.0)
        """
        def relative_luminance(rgb):
            r, g, b = [x / 255.0 for x in rgb]
            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        l1 = relative_luminance(rgb1)
        l2 = relative_luminance(rgb2)

        if l1 > l2:
            return (l1 + 0.05) / (l2 + 0.05)
        else:
            return (l2 + 0.05) / (l1 + 0.05)

    def ensure_contrast(self, fg_rgb: Tuple[int, int, int], bg_rgb: Tuple[int, int, int],
                       min_ratio: float = 4.5) -> Tuple[int, int, int]:
        """
        Adjust foreground color to ensure sufficient contrast with background.

        Args:
            fg_rgb: Foreground RGB tuple
            bg_rgb: Background RGB tuple
            min_ratio: Minimum WCAG contrast ratio (4.5 for normal text, 3.0 for large text)

        Returns:
            Adjusted foreground RGB tuple
        """
        current_ratio = self.calculate_contrast_ratio(fg_rgb, bg_rgb)

        if current_ratio >= min_ratio:
            return fg_rgb

        # Try adjusting brightness
        for factor in [0.3, 0.5, 0.7, 1.5, 2.0, 2.5]:
            adjusted = self.adjust_brightness(fg_rgb, factor)
            if self.calculate_contrast_ratio(adjusted, bg_rgb) >= min_ratio:
                return adjusted

        # If brightness adjustment doesn't work, use pure white or black
        bg_luminance = sum(bg_rgb) / 3
        return (255, 255, 255) if bg_luminance < 128 else (0, 0, 0)

    def generate_theme_from_image(self, image_path: str, theme_type: str = "auto") -> Dict[str, str]:
        """
        Generate complete UI theme from background image.

        Args:
            image_path: Path to background image
            theme_type: "light", "dark", or "auto" (auto-detect based on image)

        Returns:
            Dictionary of theme colors compatible with ThemeManager
        """
        if not HAS_PIL:
            raise ImportError("PIL (Pillow) required for smart theme generation. Install with: pip install pillow")

        # Extract dominant colors
        dominant_colors = self.extract_dominant_colors(image_path, num_colors=5)
        self.last_extracted_colors = dominant_colors

        # Primary color is most dominant
        primary_rgb = dominant_colors[0]

        # Secondary color is second most dominant
        secondary_rgb = dominant_colors[1] if len(dominant_colors) > 1 else self.get_complementary_color(primary_rgb)

        # Accent color is third most dominant, with increased saturation
        accent_rgb = dominant_colors[2] if len(dominant_colors) > 2 else primary_rgb
        accent_rgb = self.adjust_saturation(accent_rgb, 1.3)

        # Determine if we should use light or dark theme
        avg_brightness = sum(sum(color) for color in dominant_colors) / (len(dominant_colors) * 3)

        if theme_type == "auto":
            is_dark = avg_brightness < 128
        elif theme_type == "dark":
            is_dark = True
        else:
            is_dark = False

        # Build theme
        if is_dark:
            theme = self._generate_dark_theme(primary_rgb, secondary_rgb, accent_rgb)
        else:
            theme = self._generate_light_theme(primary_rgb, secondary_rgb, accent_rgb)

        return theme

    def _generate_light_theme(self, primary_rgb: Tuple[int, int, int],
                             secondary_rgb: Tuple[int, int, int],
                             accent_rgb: Tuple[int, int, int]) -> Dict[str, str]:
        """Generate light theme from base colors."""
        # Ensure colors work on light background
        primary_dark = self.adjust_brightness(primary_rgb, 0.7)

        theme = {
            "bg": "#f7f7f9",
            "fg": "#1d1d1f",
            "accent": "#ffffff",
            "highlight": self.rgb_to_hex(self.adjust_brightness(primary_rgb, 1.5)),
            "primary": self.rgb_to_hex(primary_dark),
            "secondary": self.rgb_to_hex(self.adjust_brightness(secondary_rgb, 0.8)),
            "success": "#34c759",
            "warning": "#ff9500",
            "danger": "#ff3b30",
            "border": "#d1d1d6",
            "text_dark": "#1d1d1f",
            "text_light": "#8e8e93",
            "sidebar_bg": "#ffffff",
            "header_bg": "#f7f7f9",
            "card_bg": "#ffffff",
            "hover": self.rgb_to_hex(self.adjust_brightness(primary_rgb, 1.6)),
        }

        return theme

    def _generate_dark_theme(self, primary_rgb: Tuple[int, int, int],
                            secondary_rgb: Tuple[int, int, int],
                            accent_rgb: Tuple[int, int, int]) -> Dict[str, str]:
        """Generate dark theme from base colors."""
        # Ensure colors work on dark background
        primary_light = self.adjust_brightness(primary_rgb, 1.3)

        theme = {
            "bg": "#1f2127",
            "fg": "#e8e8e8",
            "accent": "#2d2f36",
            "highlight": self.rgb_to_hex(self.adjust_brightness(primary_rgb, 0.8)),
            "primary": self.rgb_to_hex(primary_light),
            "secondary": self.rgb_to_hex(self.adjust_brightness(secondary_rgb, 1.2)),
            "success": "#30d158",
            "warning": "#ff9f0a",
            "danger": "#ff453a",
            "border": "#38383a",
            "text_dark": "#e8e8e8",
            "text_light": "#98989d",
            "sidebar_bg": "#2d2f36",
            "header_bg": "#1f2127",
            "card_bg": "#2d2f36",
            "hover": self.rgb_to_hex(self.adjust_brightness(primary_rgb, 0.7)),
        }

        return theme

    def save_theme_to_file(self, theme: Dict[str, str], output_path: str) -> None:
        """
        Save theme to JSON file.

        Args:
            theme: Theme dictionary
            output_path: Path to save theme JSON
        """
        import json

        with open(output_path, 'w') as f:
            json.dump(theme, f, indent=2)

    def get_color_preview_html(self, theme: Dict[str, str]) -> str:
        """
        Generate HTML preview of theme colors.

        Args:
            theme: Theme dictionary

        Returns:
            HTML string with color swatches
        """
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; background: #f0f0f0; }
                .swatch-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 15px; }
                .swatch { border-radius: 8px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .color-box { height: 80px; border-radius: 4px; margin-bottom: 10px; }
                .color-name { font-weight: bold; font-size: 12px; margin-bottom: 5px; }
                .color-value { font-size: 11px; color: #666; font-family: monospace; }
            </style>
        </head>
        <body>
            <h2>Theme Preview</h2>
            <div class="swatch-grid">
        """

        for name, color in theme.items():
            html += f"""
                <div class="swatch" style="background: white;">
                    <div class="color-box" style="background: {color};"></div>
                    <div class="color-name">{name}</div>
                    <div class="color-value">{color}</div>
                </div>
            """

        html += """
            </div>
        </body>
        </html>
        """

        return html


# Global singleton
_smart_theme_extractor = None


def get_smart_theme_extractor() -> SmartThemeExtractor:
    """
    Get global SmartThemeExtractor instance.

    Returns:
        SmartThemeExtractor singleton
    """
    global _smart_theme_extractor
    if _smart_theme_extractor is None:
        _smart_theme_extractor = SmartThemeExtractor()
    return _smart_theme_extractor


# Convenience function
def create_theme_from_image(image_path: str, theme_type: str = "auto") -> Dict[str, str]:
    """
    Create theme from image (convenience function).

    Args:
        image_path: Path to background image
        theme_type: "light", "dark", or "auto"

    Returns:
        Theme dictionary compatible with ThemeManager

    Example:
        theme = create_theme_from_image("background.jpg", "dark")
        theme_manager = ThemeManager(root)
        theme_manager.apply_custom_theme(theme)
    """
    extractor = get_smart_theme_extractor()
    return extractor.generate_theme_from_image(image_path, theme_type)


if __name__ == "__main__":
    # Test smart theme extractor
    print("Smart Theme Extractor Test")
    print("="*50)

    if not HAS_PIL:
        print("PIL (Pillow) not installed. Install with: pip install pillow")
    else:
        print("PIL available - SmartThemeExtractor ready")

        # Example usage
        extractor = SmartThemeExtractor()

        # Test color utilities
        rgb = (100, 150, 200)
        print(f"\nTest RGB: {rgb}")
        print(f"Hex: {extractor.rgb_to_hex(rgb)}")
        print(f"Brighter: {extractor.adjust_brightness(rgb, 1.3)}")
        print(f"Darker: {extractor.adjust_brightness(rgb, 0.7)}")
        print(f"Complementary: {extractor.get_complementary_color(rgb)}")

        # Test contrast
        white = (255, 255, 255)
        black = (0, 0, 0)
        print(f"\nContrast white/black: {extractor.calculate_contrast_ratio(white, black):.2f}")
        print(f"Contrast rgb/white: {extractor.calculate_contrast_ratio(rgb, white):.2f}")

        print("\nSmartThemeExtractor ready for use!")
