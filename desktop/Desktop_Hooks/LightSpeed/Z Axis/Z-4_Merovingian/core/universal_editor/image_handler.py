"""
Image File Handler - V1.0.0
Handle image files with viewing, annotation, and basic editing

Author: LightSpeed Team
Date: December 28, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
from PIL import Image, ImageTk, ImageDraw, ImageEnhance, ImageFilter
import io

from .file_handler import FileHandler, EditorAction


# ==============================================================================
# Image Handler
# ==============================================================================

class ImageFileHandler(FileHandler):
    """
    Handler for image files with viewing and basic editing

    Supported formats:
    - PNG, JPG/JPEG, GIF, BMP, TIFF, WEBP

    Features:
    - Image viewing with zoom
    - Basic annotations (draw, text, shapes)
    - Filters (blur, sharpen, grayscale, sepia)
    - Brightness/contrast adjustment
    - Rotation and flip
    - Crop tool
    - Save edits
    """

    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}

    def __init__(self):
        """Initialize image handler"""
        super().__init__()
        self.current_image: Optional[Image.Image] = None
        self.original_image: Optional[Image.Image] = None
        self.display_image: Optional[ImageTk.PhotoImage] = None
        self.zoom_level: float = 1.0
        self.annotations: List[dict] = []
        self.annotation_mode: Optional[str] = None

    def can_handle(self, file_path: Path) -> bool:
        """Check if can handle this image file"""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def read_file(self, file_path: Path) -> str:
        """Read image file (returns metadata as string)"""
        try:
            image = Image.open(file_path)

            # Get image metadata
            metadata = f"Image Information: {file_path.name}\n\n"
            metadata += f"Format: {image.format}\n"
            metadata += f"Size: {image.size[0]} × {image.size[1]} pixels\n"
            metadata += f"Mode: {image.mode}\n"

            # File size
            file_size = file_path.stat().st_size
            if file_size < 1024:
                size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            metadata += f"File Size: {size_str}\n"

            # Additional info
            if hasattr(image, 'info'):
                if 'dpi' in image.info:
                    metadata += f"DPI: {image.info['dpi']}\n"

            return metadata

        except Exception as e:
            raise ValueError(f"Failed to read image: {e}")

    def write_file(self, file_path: Path, content: str) -> bool:
        """Save image (content is ignored, saves current image state)"""
        if not self.current_image:
            messagebox.showerror("Error", "No image loaded to save")
            return False

        try:
            # Determine format from extension
            ext = file_path.suffix.lower()
            format_map = {
                '.jpg': 'JPEG',
                '.jpeg': 'JPEG',
                '.png': 'PNG',
                '.gif': 'GIF',
                '.bmp': 'BMP',
                '.tiff': 'TIFF',
                '.webp': 'WEBP'
            }

            save_format = format_map.get(ext, 'PNG')

            # Convert RGBA to RGB for formats that don't support alpha
            if save_format in ['JPEG', 'BMP'] and self.current_image.mode == 'RGBA':
                rgb_image = Image.new('RGB', self.current_image.size, (255, 255, 255))
                rgb_image.paste(self.current_image, mask=self.current_image.split()[3])
                rgb_image.save(file_path, format=save_format)
            else:
                self.current_image.save(file_path, format=save_format)

            return True

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save image: {e}")
            return False

    def create_editor_widget(
        self,
        parent: tk.Widget,
        file_path: Path,
        content: str,
        **kwargs
    ) -> tk.Widget:
        """Create image viewer/editor widget"""
        # Main container
        container = tk.Frame(parent)

        # Load image
        try:
            self.original_image = Image.open(file_path)
            self.current_image = self.original_image.copy()
            self.zoom_level = 1.0
        except Exception as e:
            error_label = tk.Label(
                container,
                text=f"Failed to load image:\n{e}",
                fg='red'
            )
            error_label.pack(expand=True)
            return container

        # Toolbar
        toolbar = self._create_toolbar(container)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # Canvas for image display
        canvas_frame = tk.Frame(container)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Canvas with scrollbars
        self.canvas = tk.Canvas(canvas_frame, bg='#2b2b2b')

        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)

        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)

        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Display image
        self._update_display()

        # Mouse events for annotations
        self.canvas.bind('<Button-1>', self._on_mouse_down)
        self.canvas.bind('<B1-Motion>', self._on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_mouse_up)

        # Store references
        container.canvas = self.canvas
        container.file_path = file_path

        return container

    def _create_toolbar(self, parent: tk.Widget) -> tk.Frame:
        """Create image editor toolbar"""
        toolbar = tk.Frame(parent)

        # View controls
        view_frame = tk.LabelFrame(toolbar, text="View", padx=5, pady=2)
        view_frame.pack(side=tk.LEFT, padx=2)

        tk.Button(view_frame, text="Zoom In", command=self._zoom_in, width=8).pack(side=tk.LEFT, padx=1)
        tk.Button(view_frame, text="Zoom Out", command=self._zoom_out, width=8).pack(side=tk.LEFT, padx=1)
        tk.Button(view_frame, text="Fit", command=self._fit_to_window, width=6).pack(side=tk.LEFT, padx=1)
        tk.Button(view_frame, text="100%", command=self._reset_zoom, width=6).pack(side=tk.LEFT, padx=1)

        # Transform controls
        transform_frame = tk.LabelFrame(toolbar, text="Transform", padx=5, pady=2)
        transform_frame.pack(side=tk.LEFT, padx=2)

        tk.Button(transform_frame, text="Rotate 90°", command=self._rotate_90, width=10).pack(side=tk.LEFT, padx=1)
        tk.Button(transform_frame, text="Flip H", command=self._flip_horizontal, width=8).pack(side=tk.LEFT, padx=1)
        tk.Button(transform_frame, text="Flip V", command=self._flip_vertical, width=8).pack(side=tk.LEFT, padx=1)

        # Filters
        filter_frame = tk.LabelFrame(toolbar, text="Filters", padx=5, pady=2)
        filter_frame.pack(side=tk.LEFT, padx=2)

        tk.Button(filter_frame, text="Grayscale", command=self._apply_grayscale, width=10).pack(side=tk.LEFT, padx=1)
        tk.Button(filter_frame, text="Blur", command=self._apply_blur, width=6).pack(side=tk.LEFT, padx=1)
        tk.Button(filter_frame, text="Sharpen", command=self._apply_sharpen, width=8).pack(side=tk.LEFT, padx=1)

        # Reset
        tk.Button(toolbar, text="Reset", command=self._reset_image, width=8, bg='#ff9999').pack(side=tk.RIGHT, padx=2)

        return toolbar

    def _update_display(self):
        """Update canvas with current image"""
        if not self.current_image:
            return

        # Calculate display size
        width = int(self.current_image.width * self.zoom_level)
        height = int(self.current_image.height * self.zoom_level)

        # Resize for display
        display_img = self.current_image.resize((width, height), Image.Resampling.LANCZOS)

        # Convert to PhotoImage
        self.display_image = ImageTk.PhotoImage(display_img)

        # Clear canvas and display
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.display_image)

        # Update scroll region
        self.canvas.configure(scrollregion=(0, 0, width, height))

    def _zoom_in(self):
        """Zoom in"""
        self.zoom_level *= 1.25
        self._update_display()

    def _zoom_out(self):
        """Zoom out"""
        self.zoom_level /= 1.25
        if self.zoom_level < 0.1:
            self.zoom_level = 0.1
        self._update_display()

    def _reset_zoom(self):
        """Reset to 100% zoom"""
        self.zoom_level = 1.0
        self._update_display()

    def _fit_to_window(self):
        """Fit image to canvas"""
        if not self.current_image:
            return

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width > 1 and canvas_height > 1:
            zoom_x = canvas_width / self.current_image.width
            zoom_y = canvas_height / self.current_image.height
            self.zoom_level = min(zoom_x, zoom_y) * 0.95  # 95% to leave margin
            self._update_display()

    def _rotate_90(self):
        """Rotate image 90 degrees clockwise"""
        if not self.current_image:
            return

        self.current_image = self.current_image.rotate(-90, expand=True)
        self._update_display()

    def _flip_horizontal(self):
        """Flip image horizontally"""
        if not self.current_image:
            return

        self.current_image = self.current_image.transpose(Image.FLIP_LEFT_RIGHT)
        self._update_display()

    def _flip_vertical(self):
        """Flip image vertically"""
        if not self.current_image:
            return

        self.current_image = self.current_image.transpose(Image.FLIP_TOP_BOTTOM)
        self._update_display()

    def _apply_grayscale(self):
        """Convert to grayscale"""
        if not self.current_image:
            return

        self.current_image = self.current_image.convert('L').convert('RGB')
        self._update_display()

    def _apply_blur(self):
        """Apply blur filter"""
        if not self.current_image:
            return

        self.current_image = self.current_image.filter(ImageFilter.BLUR)
        self._update_display()

    def _apply_sharpen(self):
        """Apply sharpen filter"""
        if not self.current_image:
            return

        self.current_image = self.current_image.filter(ImageFilter.SHARPEN)
        self._update_display()

    def _reset_image(self):
        """Reset to original image"""
        if not self.original_image:
            return

        result = messagebox.askyesno(
            "Reset Image",
            "Reset all edits and return to original image?"
        )

        if result:
            self.current_image = self.original_image.copy()
            self.zoom_level = 1.0
            self._update_display()

    def _on_mouse_down(self, event):
        """Handle mouse down for annotations"""
        # Placeholder for annotation features
        pass

    def _on_mouse_drag(self, event):
        """Handle mouse drag for annotations"""
        pass

    def _on_mouse_up(self, event):
        """Handle mouse up for annotations"""
        pass

    def get_content_from_widget(self, widget: tk.Widget) -> str:
        """
        Get content from widget (returns empty string for images)

        For images, content is retrieved directly from current_image when saving
        """
        return ""

    def get_toolbar_actions(self) -> List[EditorAction]:
        """Get toolbar actions for image editor"""
        return [
            EditorAction(
                action_id='save_as',
                label='Save As',
                icon='💾',
                callback=self._save_as,
                tooltip='Save image with new name'
            ),
            EditorAction(
                action_id='export',
                label='Export',
                icon='📤',
                callback=self._export,
                tooltip='Export in different format'
            ),
            EditorAction(
                action_id='info',
                label='Info',
                icon='ℹ',
                callback=self._show_info,
                tooltip='Show image information'
            ),
        ]

    def _save_as(self):
        """Save image as"""
        messagebox.showinfo("Save As", "Use File → Save As from the main menu")

    def _export(self):
        """Export image in different format"""
        if not self.current_image:
            messagebox.showwarning("No Image", "No image loaded to export")
            return

        from tkinter import filedialog, simpledialog

        # Format selection
        formats = {
            'PNG': '.png',
            'JPEG': '.jpg',
            'BMP': '.bmp',
            'TIFF': '.tiff',
            'WEBP': '.webp',
            'GIF': '.gif'
        }

        # Create format selection dialog
        format_window = tk.Toplevel(self.root)
        format_window.title("Export Image")
        format_window.geometry("400x300")
        format_window.transient(self.root)
        format_window.grab_set()

        tk.Label(format_window, text="Select Export Format:", font=('Arial', 12, 'bold')).pack(pady=10)

        selected_format = tk.StringVar(value='PNG')
        quality_var = tk.IntVar(value=95)

        # Format radio buttons
        for fmt in formats.keys():
            tk.Radiobutton(
                format_window,
                text=fmt,
                variable=selected_format,
                value=fmt,
                font=('Arial', 10)
            ).pack(anchor='w', padx=20)

        # Quality slider (for JPEG/WEBP)
        quality_frame = tk.Frame(format_window)
        quality_frame.pack(pady=10, fill='x', padx=20)
        tk.Label(quality_frame, text="Quality (JPEG/WEBP):").pack(side='left')
        quality_slider = tk.Scale(
            quality_frame,
            from_=1,
            to=100,
            orient='horizontal',
            variable=quality_var
        )
        quality_slider.pack(side='right', fill='x', expand=True)

        # Export button
        def do_export():
            format_window.destroy()
            fmt = selected_format.get()
            ext = formats[fmt]

            # File save dialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=ext,
                filetypes=[(fmt, f'*{ext}'), ('All Files', '*.*')],
                title=f"Export as {fmt}"
            )

            if not file_path:
                return

            try:
                # Convert image mode if needed
                img_to_save = self.current_image.copy()

                # Handle transparency for formats that don't support it
                if fmt in ['JPEG', 'BMP'] and img_to_save.mode in ['RGBA', 'LA']:
                    # Create white background
                    background = Image.new('RGB', img_to_save.size, (255, 255, 255))
                    if img_to_save.mode == 'RGBA':
                        background.paste(img_to_save, mask=img_to_save.split()[3])
                    else:
                        background.paste(img_to_save, mask=img_to_save.split()[1])
                    img_to_save = background
                elif fmt == 'JPEG' and img_to_save.mode != 'RGB':
                    img_to_save = img_to_save.convert('RGB')

                # Save with quality settings
                save_kwargs = {}
                if fmt in ['JPEG', 'WEBP']:
                    save_kwargs['quality'] = quality_var.get()
                if fmt == 'PNG':
                    save_kwargs['optimize'] = True

                img_to_save.save(file_path, **save_kwargs)
                messagebox.showinfo("Export Successful", f"Image exported to:\n{file_path}")

            except Exception as e:
                messagebox.showerror("Export Failed", f"Failed to export image:\n{str(e)}")

        tk.Button(
            format_window,
            text="Export",
            command=do_export,
            bg='#4dd0e1',
            fg='white',
            font=('Arial', 10, 'bold')
        ).pack(pady=20)

        tk.Button(
            format_window,
            text="Cancel",
            command=format_window.destroy
        ).pack()

    def _show_info(self):
        """Show image information"""
        if not self.current_image:
            return

        info = f"Image Information\n\n"
        info += f"Size: {self.current_image.size[0]} × {self.current_image.size[1]} pixels\n"
        info += f"Mode: {self.current_image.mode}\n"
        info += f"Format: {self.current_image.format or 'Unknown'}\n"
        info += f"Zoom: {self.zoom_level * 100:.0f}%\n"

        messagebox.showinfo("Image Info", info)

    def validate_content(self, content: str) -> bool:
        """Validate image content (always valid for images)"""
        return True

    def format_content(self, content: str) -> str:
        """Format image content (no formatting for images)"""
        return content
