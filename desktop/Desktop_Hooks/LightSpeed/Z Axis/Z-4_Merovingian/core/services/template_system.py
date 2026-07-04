"""
Template System - Unified Template Architecture
LightSpeed Type I Civilization Platform

Provides base template classes for:
- Document Templates (QR codes, tables, images, PDFs)
- UI Templates (themes, widgets, screens, layouts)
- Test Templates (validation, venv setup, integration tests)
- Data Templates (import/export formats, Z Direct object/schema templates)

All demos and tests become productive template generators.

Author: LightSpeed Team
Version: 0.9.5
Date: December 22, 2025
"""

import json
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass, field, asdict
from datetime import datetime

from .database import get_db
from .storage import get_storage
from .logger import get_services_logger

def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for cand in (start, *start.parents):
        try:
            if (cand / "N.py").exists() and (cand / "Z Axis").exists():
                return cand
        except Exception:
            continue
    return start.parent


def _load_romer_standard() -> Dict[str, Any]:
    """
    Load the Romer "premium theme" config (if present) and expose a small, stable
    palette/typography dict for template defaults.
    """
    standard: Dict[str, Any] = {
        "palette": {
            # Safe defaults (dark, high-contrast).
            "primary": "#0A4D4D",
            "secondary": "#1A5F5F",
            "accent_phthalo_green": "#123524",
            "accent_deep_gold": "#B8860B",
            "accent_velvet_blue": "#191970",
            "tortoise_eggshell": "#F0EAD6",
            "text_primary": "#F5F5DC",
            "text_secondary": "#D3D3D3",
            "border": "#2F4F4F",
            # Tk-safe (alpha is handled by renderers; do not store rgba() here).
            "shadow": "#052626",
        },
        "typography": {
            "font_primary": "Garamond",
            "font_secondary": "Arial",
            "font_code": "Consolas",
        },
    }

    root = _find_lightspeed_root(Path(__file__))
    cfg = root / "config" / "premium_theme_config.json"
    if not cfg.exists():
        return standard

    try:
        payload = json.loads(cfg.read_text(encoding="utf-8", errors="replace"))
        palettes = payload.get("color_palettes") if isinstance(payload, dict) else None
        dark = (palettes or {}).get("dark_mode") if isinstance(palettes, dict) else None
        typo = payload.get("typography") if isinstance(payload, dict) else None
        if isinstance(dark, dict):
            standard["palette"].update({k: v for k, v in dark.items() if isinstance(v, str)})
        if isinstance(typo, dict):
            for key in ("font_primary", "font_secondary", "font_code"):
                val = typo.get(key)
                if isinstance(val, str) and val.strip():
                    standard["typography"][key] = val.strip()
    except Exception:
        return standard

    return standard


ROMER_STANDARD: Dict[str, Any] = _load_romer_standard()


# ============================================================================
# BASE TEMPLATE CLASSES
# ============================================================================

@dataclass
class TemplateMetadata:
    """Metadata for all templates"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: str = ""  # document, ui, test, data
    subcategory: str = ""  # qr, table, theme, widget, etc.
    version: str = "1.0.0"
    author: str = "LightSpeed Team"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    is_base: bool = False  # True for base templates
    parent_template_id: Optional[str] = None  # Inherit from parent


class BaseTemplate(ABC):
    """
    Abstract base class for all templates.

    All templates (document, UI, test, data) inherit from this.
    Provides common interface for:
    - Rendering/generation
    - Customization
    - Validation
    - Export/import
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        self.metadata = metadata or TemplateMetadata()
        self.settings: Dict[str, Any] = {}
        self.logger = get_services_logger()

    @abstractmethod
    def render(self, data: Dict[str, Any]) -> Any:
        """
        Render template with given data.

        Args:
            data: Template data/parameters

        Returns:
            Rendered output (file path, widget, etc.)
        """
        pass

    @abstractmethod
    def get_default_settings(self) -> Dict[str, Any]:
        """Return default template settings"""
        pass

    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate template data.

        Args:
            data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def customize(self, settings: Dict[str, Any]):
        """
        Customize template settings.

        Args:
            settings: Custom settings to apply
        """
        self.settings.update(settings)
        self.metadata.updated_at = datetime.now().isoformat()

    def export_template(self) -> Dict[str, Any]:
        """Export template configuration"""
        return {
            'metadata': asdict(self.metadata),
            'settings': self.settings,
            'type': self.__class__.__name__
        }

    def import_template(self, config: Dict[str, Any]):
        """Import template configuration"""
        self.metadata = TemplateMetadata(**config['metadata'])
        self.settings = config['settings']

    def save_to_db(self):
        """Save template to database"""
        db = get_db()
        db.execute("""
            INSERT OR REPLACE INTO templates (
                id, name, description, category, subcategory,
                version, author, settings_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.metadata.id, self.metadata.name, self.metadata.description,
            self.metadata.category, self.metadata.subcategory,
            self.metadata.version, self.metadata.author,
            json.dumps(self.settings),
            self.metadata.created_at, self.metadata.updated_at
        ))


# ============================================================================
# DOCUMENT TEMPLATES
# ============================================================================

class DocumentTemplate(BaseTemplate):
    """Base class for document templates (QR, tables, PDFs, images)"""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        if not self.metadata.category:
            self.metadata.category = "document"

    def get_output_path(self, filename: str) -> Path:
        """Get output path for generated document"""
        storage = get_storage()
        output_dir = Path(storage.storage_root) / "templates" / self.metadata.subcategory
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / filename


class QRCodeTemplate(DocumentTemplate):
    """
    QR Code generator template.

    Customizable:
    - Size, border
    - Error correction level
    - Fill/background colors
    - Logo overlay
    - Output format (PNG, SVG)
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.subcategory = "qr_code"
        self.metadata.name = self.metadata.name or "QR Code Template"
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        pal = (ROMER_STANDARD.get("palette") or {}) if isinstance(ROMER_STANDARD, dict) else {}
        return {
            'size': 10,  # Box size
            'border': 4,  # Border boxes
            # Keep high contrast for scan reliability.
            'fill_color': pal.get("accent_phthalo_green", "black"),
            'back_color': pal.get("tortoise_eggshell", "white"),
            'error_correction': 'M',  # L, M, Q, H
            'format': 'PNG',  # PNG, SVG
            'add_logo': False,
            'logo_path': None,
            'logo_size_ratio': 0.3
        }

    def render(self, data: Dict[str, Any]) -> Path:
        """
        Render QR code.

        Args:
            data: {'content': str, 'filename': str}

        Returns:
            Path to generated QR code
        """
        import qrcode
        from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H

        error_levels = {'L': ERROR_CORRECT_L, 'M': ERROR_CORRECT_M, 'Q': ERROR_CORRECT_Q, 'H': ERROR_CORRECT_H}

        qr = qrcode.QRCode(
            version=1,
            error_correction=error_levels[self.settings['error_correction']],
            box_size=self.settings['size'],
            border=self.settings['border']
        )
        qr.add_data(data['content'])
        qr.make(fit=True)

        img = qr.make_image(fill_color=self.settings['fill_color'],
                           back_color=self.settings['back_color'])

        # Add logo if enabled
        if self.settings['add_logo'] and self.settings['logo_path']:
            try:
                from PIL import Image
                logo = Image.open(self.settings['logo_path'])
                # Resize logo
                qr_width, qr_height = img.size
                logo_size = int(qr_width * self.settings['logo_size_ratio'])
                logo = logo.resize((logo_size, logo_size))
                # Paste logo in center
                pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
                img.paste(logo, pos)
            except Exception as e:
                self.logger.warning(f"Could not add logo: {e}")

        output_path = self.get_output_path(data.get('filename', 'qr_code.png'))
        img.save(str(output_path))

        self.logger.info(f"QR code generated: {output_path}")
        return output_path

    def validate(self, data: Dict[str, Any]) -> bool:
        return 'content' in data and isinstance(data['content'], str)


class TableTemplate(DocumentTemplate):
    """
    Data table generator template.

    Customizable:
    - Headers, column widths
    - Cell padding, borders
    - Font family, size
    - Colors (header, rows, alternating)
    - Output format (CSV, Excel, PDF, HTML)
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.subcategory = "table"
        self.metadata.name = self.metadata.name or "Data Table Template"
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        pal = (ROMER_STANDARD.get("palette") or {}) if isinstance(ROMER_STANDARD, dict) else {}
        typo = (ROMER_STANDARD.get("typography") or {}) if isinstance(ROMER_STANDARD, dict) else {}
        return {
            'font_family': typo.get("font_secondary", "Arial"),
            'font_size': 10,
            'header_font_size': 12,
            'header_bg_color': pal.get("accent_velvet_blue", "#007acc"),
            'header_text_color': pal.get("tortoise_eggshell", "#ffffff"),
            'row_bg_color': pal.get("tortoise_eggshell", "#ffffff"),
            'alt_row_bg_color': "#ffffff",
            'border_color': pal.get("accent_deep_gold", "#cccccc"),
            'border_width': 1,
            'cell_padding': 5,
            'format': 'HTML',  # CSV, Excel, PDF, HTML
            'show_index': False,
            'auto_width': True
        }

    def render(self, data: Dict[str, Any]) -> Path:
        """
        Render table.

        Args:
            data: {
                'headers': List[str],
                'rows': List[List[Any]],
                'filename': str
            }

        Returns:
            Path to generated table file
        """
        headers = data['headers']
        rows = data['rows']
        filename = data.get('filename', 'table.html')

        if self.settings['format'] == 'HTML':
            return self._render_html(headers, rows, filename)
        elif self.settings['format'] == 'CSV':
            return self._render_csv(headers, rows, filename)
        # Add Excel, PDF support as needed

    def _render_html(self, headers: List[str], rows: List[List[Any]], filename: str) -> Path:
        """Render as HTML table"""
        html = ['<table style="border-collapse: collapse; width: 100%;">']

        # Headers
        html.append('<thead><tr>')
        for header in headers:
            style = f"background-color: {self.settings['header_bg_color']}; " \
                   f"color: {self.settings['header_text_color']}; " \
                   f"font-size: {self.settings['header_font_size']}pt; " \
                   f"padding: {self.settings['cell_padding']}px; " \
                   f"border: {self.settings['border_width']}px solid {self.settings['border_color']};"
            html.append(f'<th style="{style}">{header}</th>')
        html.append('</tr></thead>')

        # Rows
        html.append('<tbody>')
        for i, row in enumerate(rows):
            bg_color = self.settings['row_bg_color'] if i % 2 == 0 else self.settings['alt_row_bg_color']
            html.append('<tr>')
            for cell in row:
                style = f"background-color: {bg_color}; " \
                       f"font-size: {self.settings['font_size']}pt; " \
                       f"padding: {self.settings['cell_padding']}px; " \
                       f"border: {self.settings['border_width']}px solid {self.settings['border_color']};"
                html.append(f'<td style="{style}">{cell}</td>')
            html.append('</tr>')
        html.append('</tbody></table>')

        output_path = self.get_output_path(filename)
        output_path.write_text('\n'.join(html))
        self.logger.info(f"Table generated: {output_path}")
        return output_path

    def _render_csv(self, headers: List[str], rows: List[List[Any]], filename: str) -> Path:
        """Render as CSV"""
        import csv
        output_path = self.get_output_path(filename)
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        self.logger.info(f"CSV generated: {output_path}")
        return output_path

    def validate(self, data: Dict[str, Any]) -> bool:
        return 'headers' in data and 'rows' in data and \
               isinstance(data['headers'], list) and isinstance(data['rows'], list)


class ImageTemplate(DocumentTemplate):
    """
    Image processing template.

    Customizable:
    - Border style, color, width
    - Title placement, font
    - Watermark
    - Resize, crop
    - Filters, effects
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.subcategory = "image"
        self.metadata.name = self.metadata.name or "Image Processing Template"
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        pal = (ROMER_STANDARD.get("palette") or {}) if isinstance(ROMER_STANDARD, dict) else {}
        typo = (ROMER_STANDARD.get("typography") or {}) if isinstance(ROMER_STANDARD, dict) else {}
        return {
            'border_width': 10,
            'border_color': pal.get("accent_deep_gold", "#000000"),
            'border_style': 'solid',  # solid, dashed, double
            'title': None,
            'title_position': 'bottom',  # top, bottom, center
            'title_font_family': typo.get("font_primary", "Arial"),
            'title_font_size': 24,
            'title_color': pal.get("tortoise_eggshell", "#ffffff"),
            'title_bg_color': pal.get("accent_phthalo_green", "#000000"),
            'watermark': None,
            'watermark_opacity': 0.3,
            'resize_width': None,
            'resize_height': None,
            'maintain_aspect': True
        }

    def render(self, data: Dict[str, Any]) -> Path:
        """
        Process image.

        Args:
            data: {'image_path': str/Path, 'filename': str}

        Returns:
            Path to processed image
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            self.logger.error("PIL not installed: pip install Pillow")
            raise

        img = Image.open(data['image_path'])

        # Resize if needed
        if self.settings['resize_width'] or self.settings['resize_height']:
            new_size = self._calculate_resize(img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Add border
        if self.settings['border_width'] > 0:
            img = self._add_border(img)

        # Add title
        if self.settings['title']:
            img = self._add_title(img)

        # Add watermark
        if self.settings['watermark']:
            img = self._add_watermark(img)

        output_path = self.get_output_path(data.get('filename', 'image_processed.png'))
        img.save(str(output_path))
        self.logger.info(f"Image processed: {output_path}")
        return output_path

    def _calculate_resize(self, original_size):
        """Calculate new size maintaining aspect ratio"""
        width, height = original_size
        target_w = self.settings['resize_width']
        target_h = self.settings['resize_height']

        if self.settings['maintain_aspect']:
            if target_w and not target_h:
                ratio = target_w / width
                return (target_w, int(height * ratio))
            elif target_h and not target_w:
                ratio = target_h / height
                return (int(width * ratio), target_h)
            else:
                # Both specified, use smallest ratio
                ratio = min(target_w / width, target_h / height)
                return (int(width * ratio), int(height * ratio))
        else:
            return (target_w or width, target_h or height)

    def _add_border(self, img):
        """Add border to image"""
        from PIL import ImageOps
        border_color = self.settings['border_color']
        border_width = self.settings['border_width']
        return ImageOps.expand(img, border=border_width, fill=border_color)

    def _add_title(self, img):
        """Add title to image"""
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)

        # Try to load font, fall back to default
        try:
            font = ImageFont.truetype(self.settings['title_font_family'], self.settings['title_font_size'])
        except:
            font = ImageFont.load_default()

        # Calculate title position
        bbox = draw.textbbox((0, 0), self.settings['title'], font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        if self.settings['title_position'] == 'bottom':
            x = (img.width - text_width) // 2
            y = img.height - text_height - 10
        elif self.settings['title_position'] == 'top':
            x = (img.width - text_width) // 2
            y = 10
        else:  # center
            x = (img.width - text_width) // 2
            y = (img.height - text_height) // 2

        # Draw background rectangle
        padding = 5
        draw.rectangle([x - padding, y - padding, x + text_width + padding, y + text_height + padding],
                      fill=self.settings['title_bg_color'])

        # Draw text
        draw.text((x, y), self.settings['title'], fill=self.settings['title_color'], font=font)
        return img

    def _add_watermark(self, img):
        """Add watermark to image"""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            return img

        watermark = self.settings.get('watermark')
        if not watermark:
            return img

        opacity = float(self.settings.get('watermark_opacity', 0.3) or 0.3)
        opacity = max(0.0, min(1.0, opacity))

        base = img.convert('RGBA')
        overlay = Image.new('RGBA', base.size, (0, 0, 0, 0))

        # If watermark points to an image file, composite it; otherwise treat as text.
        watermark_str = str(watermark)
        watermark_path = Path(watermark_str) if watermark_str else None

        if watermark_path and watermark_path.exists() and watermark_path.is_file():
            try:
                wm = Image.open(str(watermark_path)).convert('RGBA')

                # Scale watermark to ~25% of base width (preserve aspect)
                target_w = max(1, int(base.width * 0.25))
                ratio = target_w / wm.width if wm.width else 1.0
                target_h = max(1, int(wm.height * ratio))
                wm = wm.resize((target_w, target_h), Image.Resampling.LANCZOS)

                # Apply configured opacity
                if wm.mode != 'RGBA':
                    wm = wm.convert('RGBA')
                r, g, b, a = wm.split()
                a = a.point(lambda v: int(v * opacity))
                wm.putalpha(a)

                margin = 10
                x = base.width - wm.width - margin
                y = base.height - wm.height - margin
                overlay.paste(wm, (x, y), wm)
            except Exception:
                return img
        else:
            draw = ImageDraw.Draw(overlay)

            # Font sizing relative to image
            font_size = max(12, int(min(base.size) * 0.04))
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), watermark_str, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

            margin = 14
            x = max(0, base.width - text_w - margin)
            y = max(0, base.height - text_h - margin)

            fill = (255, 255, 255, int(255 * opacity))
            shadow = (0, 0, 0, int(255 * opacity * 0.6))
            draw.text((x + 2, y + 2), watermark_str, font=font, fill=shadow)
            draw.text((x, y), watermark_str, font=font, fill=fill)

        try:
            combined = Image.alpha_composite(base, overlay)
            return combined.convert(img.mode) if img.mode in ("RGB", "RGBA") else combined.convert("RGB")
        except Exception:
            return img

    def validate(self, data: Dict[str, Any]) -> bool:
        return 'image_path' in data


class AchillesDesktopTemplate(DocumentTemplate):
    """
    Achilles AI Desktop (Romer web shell).

    Renders a self-contained HTML page based on Trinity's web asset:
    `Z Axis/Z+3_Trinity/assets/web/achilles_desktop.html`.
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.subcategory = "web"
        self.metadata.name = self.metadata.name or "Achilles AI Desktop"
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "base_url": "https://romer.industries",
            "default_route": "/dash",
            "filename": "achilles_desktop.html",
        }

    def _find_lightspeed_root(self) -> Path:
        here = Path(__file__).resolve()
        for cand in (here, *here.parents):
            try:
                if (cand / "N.py").exists() and (cand / "Z Axis").exists():
                    return cand
            except Exception:
                continue
        return here.parent

    def render(self, data: Dict[str, Any]) -> Path:
        base_url = str(data.get("base_url") or self.settings.get("base_url") or "https://romer.industries").rstrip("/")
        default_route = str(data.get("default_route") or self.settings.get("default_route") or "/dash")
        filename = str(data.get("filename") or self.settings.get("filename") or "achilles_desktop.html")

        ls_root = self._find_lightspeed_root()
        asset = (ls_root / "Z Axis" / "Z+3_Trinity" / "assets" / "web" / "achilles_desktop.html").resolve()
        if not asset.exists():
            raise FileNotFoundError(asset)

        html = asset.read_text(encoding="utf-8", errors="replace")

        # Keep the template portable: rewrite romer.industries endpoints if caller specifies a custom base_url.
        html = html.replace("https://romer.industries/dash", f"{base_url}{default_route}")
        html = html.replace("https://romer.industries/", f"{base_url}/")
        html = html.replace("https://romer.industries", base_url)

        out = self.get_output_path(filename)
        out.write_text(html, encoding="utf-8")
        return out

    def validate(self, data: Dict[str, Any]) -> bool:
        base_url = data.get("base_url", self.settings.get("base_url"))
        if not isinstance(base_url, str) or not base_url.strip():
            return False
        return True


# ============================================================================
# ARCHITECTURE DOCUMENT TEMPLATES
# ============================================================================

class ArchitectureScorecardTemplate(DocumentTemplate):
    """
    Architecture Scorecard (Markdown).

    This generator captures:
    - architectural characteristics (quality attributes)
    - explicit tradeoffs
    - decision records and fitness functions
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.subcategory = "architecture"
        self.metadata.name = self.metadata.name or "Architecture Scorecard"
        self.metadata.description = self.metadata.description or "Architecture characteristics, tradeoffs, decisions, and fitness functions."
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "title": "LightSpeed Architecture Scorecard",
            "system_context": "Local-first modular monolith with approval-gated exchange (Z Direct).",
            "characteristics": [
                {"name": "Modifiability", "target": "High", "notes": "Z-floor modularity + governed interfaces."},
                {"name": "Security", "target": "High", "notes": "Trinity is the commit gate; no silent schema mutation."},
                {"name": "Observability", "target": "High", "notes": "Append-only streams + durable registries + IT Portal."},
                {"name": "Performance", "target": "Medium", "notes": "Tk rendering; file-based exchange; optimize hotspots as needed."},
                {"name": "Simplicity", "target": "High", "notes": "Prefer explicit workflows over invisible automation."},
            ],
            "tradeoffs": [
                {
                    "decision": "File-based Z Direct (JSONL + JSON) instead of a message broker",
                    "benefits": ["transparent", "easy to inspect/backup", "offline-friendly"],
                    "costs": ["not built for high throughput", "manual governance required"],
                }
            ],
            "fitness_functions": [
                "Integration verifier PASS (no regressions in core wiring).",
                "No runtime DB schema mutation (validation-only at runtime).",
                "All durable registry writes are operator-approved via Trinity.",
            ],
            "adrs": [],
            "filename": "architecture_scorecard.md",
        }

    def render(self, data: Dict[str, Any]) -> Path:
        cfg = dict(self.settings)
        cfg.update(data or {})

        title = str(cfg.get("title") or "Architecture Scorecard")
        ctx = str(cfg.get("system_context") or "")
        characteristics = cfg.get("characteristics") if isinstance(cfg.get("characteristics"), list) else []
        tradeoffs = cfg.get("tradeoffs") if isinstance(cfg.get("tradeoffs"), list) else []
        fitness = cfg.get("fitness_functions") if isinstance(cfg.get("fitness_functions"), list) else []
        adrs = cfg.get("adrs") if isinstance(cfg.get("adrs"), list) else []
        filename = str(cfg.get("filename") or "architecture_scorecard.md")

        lines: List[str] = []
        lines.append(f"# {title}")
        lines.append("")
        if ctx:
            lines.append("## System Context")
            lines.append(ctx)
            lines.append("")

        lines.append("## Architectural Characteristics")
        if not characteristics:
            lines.append("- (none)")
        else:
            for ch in characteristics:
                if not isinstance(ch, dict):
                    continue
                name = str(ch.get("name") or "").strip() or "Characteristic"
                target = str(ch.get("target") or "").strip() or "N/A"
                notes = str(ch.get("notes") or "").strip()
                lines.append(f"- {name}: target={target}" + (f" | {notes}" if notes else ""))
        lines.append("")

        lines.append("## Tradeoffs")
        if not tradeoffs:
            lines.append("- (none)")
        else:
            for t in tradeoffs:
                if not isinstance(t, dict):
                    continue
                decision = str(t.get("decision") or "").strip() or "Decision"
                benefits = t.get("benefits") if isinstance(t.get("benefits"), list) else []
                costs = t.get("costs") if isinstance(t.get("costs"), list) else []
                lines.append(f"- {decision}")
                if benefits:
                    lines.append(f"  - benefits: {', '.join([str(x) for x in benefits if x is not None])}")
                if costs:
                    lines.append(f"  - costs: {', '.join([str(x) for x in costs if x is not None])}")
        lines.append("")

        lines.append("## Fitness Functions")
        if not fitness:
            lines.append("- (none)")
        else:
            for f in fitness:
                if f is None:
                    continue
                lines.append(f"- {str(f)}")
        lines.append("")

        lines.append("## Decision Records (ADRs)")
        if not adrs:
            lines.append("- (none)")
        else:
            for a in adrs:
                if not isinstance(a, dict):
                    continue
                aid = str(a.get("id") or "").strip() or "ADR"
                summary = str(a.get("summary") or "").strip()
                status = str(a.get("status") or "").strip()
                suffix = (f": {summary}" if summary else "") + (f" [{status}]" if status else "")
                lines.append(f"- {aid}{suffix}")
        lines.append("")

        out = self.get_output_path(filename)
        out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return out

    def validate(self, data: Dict[str, Any]) -> bool:
        fn = data.get("filename", self.settings.get("filename"))
        return isinstance(fn, str) and fn.strip().endswith(".md")


# ============================================================================
# UI TEMPLATES
# ============================================================================

class UITemplate(BaseTemplate):
    """Base class for UI templates (themes, widgets, screens)"""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        if not self.metadata.category:
            self.metadata.category = "ui"


class ThemeTemplate(UITemplate):
    """
    Theme template for UI customization.

    Defines complete color scheme, fonts, spacing.
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.subcategory = "theme"
        self.metadata.name = self.metadata.name or "UI Theme Template"
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        pal = (ROMER_STANDARD.get("palette") or {}) if isinstance(ROMER_STANDARD, dict) else {}
        typo = (ROMER_STANDARD.get("typography") or {}) if isinstance(ROMER_STANDARD, dict) else {}
        return {
            'name': 'Romer Standard (Dark)',
            'colors': {
                'primary': pal.get("primary", "#0A4D4D"),
                'secondary': pal.get("secondary", "#1A5F5F"),
                'success': pal.get("matrix_green", "#00FF41"),
                'warning': pal.get("accent_deep_gold", "#B8860B"),
                'danger': pal.get("error", "#DC143C"),
                'bg': pal.get("accent_phthalo_green", "#123524"),
                'fg': pal.get("text_primary", "#F5F5DC"),
                'panel': pal.get("secondary", "#1A5F5F"),
                'border': pal.get("border", "#2F4F4F")
            },
            'fonts': {
                'heading': (typo.get("font_primary", "Segoe UI"), 16, 'bold'),
                'subheading': (typo.get("font_primary", "Segoe UI"), 12, 'bold'),
                'body': (typo.get("font_secondary", "Segoe UI"), 10),
                'code': (typo.get("font_code", "Consolas"), 10)
            },
            'spacing': {
                'padding': 10,
                'margin': 5,
                'border_width': 1
            }
        }

    def render(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render theme (returns theme configuration).

        Args:
            data: Optional overrides

        Returns:
            Complete theme configuration
        """
        theme = self.settings.copy()
        theme.update(data)
        return theme

    def validate(self, data: Dict[str, Any]) -> bool:
        return True  # Themes always valid


# ============================================================================
# DATA TEMPLATES (Z DIRECT OBJECTS / SCHEMAS)
# ============================================================================

class DataTemplate(BaseTemplate):
    """Base class for data templates (export formats, schemas, object payloads)."""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        if not self.metadata.category:
            self.metadata.category = "data"

    def get_output_path(self, filename: str) -> Path:
        storage = get_storage()
        output_dir = Path(storage.storage_root) / "templates" / (self.metadata.subcategory or "data")
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / filename


class ZDirectObjectTemplate(DataTemplate):
    """
    Template for producing Z Direct object payloads as JSON.

    This does not write to any Z Direct streams/registries. It generates payloads
    (or files containing payloads) that operators can stage/commit via Trinity.
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.subcategory = self.metadata.subcategory or "z_direct"
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {"kind": "", "id": ""}

    def validate(self, data: Dict[str, Any]) -> bool:
        kind = data.get("kind", self.settings.get("kind"))
        obj_id = data.get("id", self.settings.get("id"))
        if not isinstance(kind, str) or not kind.strip():
            return False
        if obj_id is None or (isinstance(obj_id, str) and not obj_id.strip()):
            return False
        return True

    def render(self, data: Dict[str, Any]) -> Path:
        payload = dict(self.settings)
        payload.update(data or {})
        if not self.validate(payload):
            raise ValueError("Invalid Z Direct object payload")
        filename = str(payload.get("filename") or f"{payload.get('kind')}_{payload.get('id')}.json")
        out = self.get_output_path(filename)
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return out


class VaultFileTemplate(ZDirectObjectTemplate):
    """Oracle vault file payload template (kind=vault_file)."""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Vault File"
        self.metadata.description = self.metadata.description or "Oracle vault file payload (Z Direct object kind=vault_file)."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["oracle", "vault", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "kind": "vault_file",
            "id": f"vf_{uuid.uuid4().hex[:16]}",
            "sha256": "0" * 64,
            "name": "example.bin",
            "path": r"C:\example\example.bin",
            "size_bytes": 0,
            "mime_type": "application/octet-stream",
            "source_name": "",
            "source_path": "",
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "vault_file":
            return False
        obj_id = data.get("id")
        if obj_id is None or (isinstance(obj_id, str) and not obj_id.strip()):
            return False
        sha = data.get("sha256")
        name = data.get("name")
        path = data.get("path")
        if not isinstance(sha, str) or len(sha.strip()) != 64:
            return False
        if not isinstance(name, str) or not name.strip():
            return False
        if not isinstance(path, str) or not path.strip():
            return False
        return True


class ResearchQueryTemplate(ZDirectObjectTemplate):
    """Research query payload template (kind=research_query)."""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Research Query"
        self.metadata.description = self.metadata.description or "Research query payload for Cognigrex workflows (Z Direct object kind=research_query)."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["cognigrex", "research", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "kind": "research_query",
            "id": f"rq_{uuid.uuid4().hex[:16]}",
            # Align with builtin schema (`query_text`, `domain` are required).
            "workspace_id": "",
            "query_text": "What is the objective? What evidence do we have? What should we test next?",
            "domain": "GENERAL",
            "context": {"project_id": ""},
            "results": [],
            "confidence": 0.0,
            "status": "draft",
            "tags": ["cognigrex"],
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "research_query":
            return False
        if not isinstance(data.get("id"), str) or not str(data.get("id")).strip():
            return False
        if not isinstance(data.get("query_text"), str) or not str(data.get("query_text")).strip():
            return False
        if not isinstance(data.get("domain"), str) or not str(data.get("domain")).strip():
            return False
        return True


class DatasetTemplate(ZDirectObjectTemplate):
    """Dataset payload template (kind=dataset)."""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Dataset"
        self.metadata.description = self.metadata.description or "Dataset payload (Z Direct object kind=dataset)."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["data", "dataset", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "kind": "dataset",
            "id": f"ds_{uuid.uuid4().hex[:16]}",
            "name": "Dataset Name",
            # Align with builtin schema (path is required).
            "path": "data/datasets/example_dataset.csv",
            "domain": "GENERAL",
            "dataset_type": "",
            "description": "",
            "source_paths": [],
            "schema_ref": "",
            "stats": {"rows": 0, "cols": 0},
            "tags": [],
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "dataset":
            return False
        if not isinstance(data.get("id"), str) or not str(data.get("id")).strip():
            return False
        if not isinstance(data.get("name"), str) or not str(data.get("name")).strip():
            return False
        if not isinstance(data.get("path"), str) or not str(data.get("path")).strip():
            return False
        return True


class ExperimentRunTemplate(ZDirectObjectTemplate):
    """Experiment run payload template (kind=experiment_run)."""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Experiment Run"
        self.metadata.description = self.metadata.description or "Experiment run payload (Z Direct object kind=experiment_run)."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["experiment", "run", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "kind": "experiment_run",
            "id": f"exp_{uuid.uuid4().hex[:16]}",
            "title": "Experiment Title",
            "tool_key": "",
            "status": "planned",
            "inputs": {},
            "outputs": {},
            "artifacts": [],
            "tags": [],
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "experiment_run":
            return False
        if not isinstance(data.get("id"), str) or not str(data.get("id")).strip():
            return False
        if not isinstance(data.get("title"), str) or not str(data.get("title")).strip():
            return False
        return True


class ProjectTemplate(ZDirectObjectTemplate):
    """Project payload template (kind=project)."""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Project"
        self.metadata.description = self.metadata.description or "Project payload (Z Direct object kind=project)."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["project", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "kind": "project",
            "id": f"proj_{uuid.uuid4().hex[:16]}",
            "title": "Project Title",
            "summary": "",
            "status": "active",
            "tags": [],
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "project":
            return False
        if not isinstance(data.get("id"), str) or not str(data.get("id")).strip():
            return False
        if not isinstance(data.get("title"), str) or not str(data.get("title")).strip():
            return False
        return True


class KnowledgeNodeTemplate(ZDirectObjectTemplate):
    """Cognigrex knowledge node payload template (kind=knowledge_node)."""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Knowledge Node"
        self.metadata.description = self.metadata.description or "Cognigrex knowledge node payload (Z Direct object kind=knowledge_node)."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["cognigrex", "knowledge", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "kind": "knowledge_node",
            "id": f"kn_{uuid.uuid4().hex[:16]}",
            "concept": "Concept Title",
            "definition": "Short definition / summary.",
            "domain": "GENERAL",
            "related_concepts": [],
            "sources": [],
            "confidence": 0.75,
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict):
            return False
        if data.get("kind") != "knowledge_node":
            return False
        for k in ("id", "concept", "definition"):
            v = data.get(k)
            if not isinstance(v, str) or not v.strip():
                return False
        return True


class CitationTemplate(ZDirectObjectTemplate):
    """Citation payload template (kind=citation) that references a vault_file."""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Citation"
        self.metadata.description = self.metadata.description or "Citation payload referencing an Oracle vault_file."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["citation", "vault", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "kind": "citation",
            "id": f"cit_{uuid.uuid4().hex[:16]}",
            "vault_file_id": "",
            "note": "",
            "span": {},
            "quote_hash": "",
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "citation":
            return False
        if not isinstance(data.get("id"), str) or not str(data.get("id")).strip():
            return False
        if not isinstance(data.get("vault_file_id"), str) or not str(data.get("vault_file_id")).strip():
            return False
        return True


class WorkspaceTemplate(ZDirectObjectTemplate):
    """Workspace payload template (kind=workspace)."""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Workspace"
        self.metadata.description = self.metadata.description or "Research workspace container for Cognigrex work."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["workspace", "cognigrex", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "kind": "workspace",
            "id": f"ws_{uuid.uuid4().hex[:16]}",
            "name": "Workspace Name",
            "domain": "GENERAL",
            "purpose": "",
            "datasets": [],
            "queries": [],
            "outputs": [],
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "workspace":
            return False
        if not isinstance(data.get("id"), str) or not str(data.get("id")).strip():
            return False
        if not isinstance(data.get("name"), str) or not str(data.get("name")).strip():
            return False
        return True


class LearningModuleTemplate(ZDirectObjectTemplate):
    """Learning module payload template (kind=learning_module)."""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Learning Module"
        self.metadata.description = self.metadata.description or "Learning module for the digital library / onboarding."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["learning", "library", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "kind": "learning_module",
            "id": f"lm_{uuid.uuid4().hex[:16]}",
            "title": "Module Title",
            "objectives": [],
            "prereqs": [],
            "steps": [],
            "assessments": [],
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "learning_module":
            return False
        if not isinstance(data.get("id"), str) or not str(data.get("id")).strip():
            return False
        if not isinstance(data.get("title"), str) or not str(data.get("title")).strip():
            return False
        return True


class SimulationResultTemplate(ZDirectObjectTemplate):
    """Simulation result payload template (kind=simulation_result)."""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Simulation Result"
        self.metadata.description = self.metadata.description or "TheConstruct simulation output payload (staged to Z Direct; can be committed for provenance)."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["simulation", "construct", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "kind": "simulation_result",
            "id": f"sim_{uuid.uuid4().hex[:16]}",
            "sim_type": "raphael",
            "status": "complete",
            "params": {},
            "result": {},
            "started_at": "",
            "completed_at": "",
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "simulation_result":
            return False
        if not isinstance(data.get("id"), str) or not str(data.get("id")).strip():
            return False
        if not isinstance(data.get("sim_type"), str) or not str(data.get("sim_type")).strip():
            return False
        if data.get("params") is not None and not isinstance(data.get("params"), dict):
            return False
        return True


class BentoWidgetDefinitionTemplate(ZDirectObjectTemplate):
    """
    Bento widget definition payload template (kind=bento_widget).

    This enables new Bento tiles to be defined as data and committed via Z Direct,
    without requiring new Python code for simple host actions.
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Bento Widget Definition"
        self.metadata.description = self.metadata.description or "Defines a Bento widget tile that Trinity can load from the committed registry."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["bento", "ui", "trinity", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "kind": "bento_widget",
            "id": f"bw_{uuid.uuid4().hex[:12]}",
            "title": "New Widget",
            "floor": "Z+3_Trinity",
            "widget_type": "BUTTON",
            "config": {
                "icon": "NEW",
                "description": "Describe what this does",
                # Host method name to invoke when clicked (wired by N host at runtime).
                "host_action": "toggle_bento_panel",
                "host_action_args": {},
                # Optional layout hints for the Bento grid.
                "span_cols": 1,
                "span_rows": 1,
            },
            "enabled": True,
            "tags": ["romer_standard"],
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "bento_widget":
            return False
        for key in ("id", "title", "floor", "widget_type"):
            val = data.get(key)
            if not isinstance(val, str) or not val.strip():
                return False
        cfg = data.get("config")
        if cfg is not None and not isinstance(cfg, dict):
            return False
        enabled = data.get("enabled")
        if enabled is not None and not isinstance(enabled, bool):
            return False
        return True


class ZDirectSchemaTemplate(ZDirectObjectTemplate):
    """Schema payload template (kind=schema) to stage/commit custom JSON schemas."""

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Z Direct Schema"
        self.metadata.description = self.metadata.description or "Defines a committed schema (kind=schema) used by Trinity's approval gate for validation."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["schema", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        # `id` should match the payload kind being described (convention used by Z Direct).
        return {
            "kind": "schema",
            "id": "my_payload_kind",
            "name": "my_payload_kind",
            "json_schema": {
                "type": "object",
                "required": ["kind", "id"],
                "properties": {
                    "kind": {"type": "string"},
                    "id": {"type": "string"},
                    "metadata": {"type": "object"},
                    "provenance": {"type": "object"},
                },
            },
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "schema":
            return False
        if not isinstance(data.get("id"), str) or not str(data.get("id")).strip():
            return False
        js = data.get("json_schema")
        if not isinstance(js, dict):
            return False
        if not isinstance(js.get("type"), str) or not str(js.get("type")).strip():
            return False
        return True


class ActionDefinitionTemplate(ZDirectObjectTemplate):
    """
    Action definition template (kind=action_def).

    An action_def describes an actionable command with typed parameters + UI hints.
    Host shells (e.g. N.py) can wire these to real callables via `host_action`.
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Action Definition"
        self.metadata.description = self.metadata.description or "Defines a callable action with parameter specs + UI control hints."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["action", "ui", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        # Parameter specs are intentionally explicit to enable consistent control rendering.
        return {
            "kind": "action_def",
            "id": f"act_{uuid.uuid4().hex[:12]}",
            "title": "Action Title",
            "description": "What this action does.",
            "category": "Actions / Commands",
            # Host method name (e.g. N.toggle_bento_panel). Use args for keyword arguments.
            "host_action": "toggle_bento_panel",
            "host_action_args": {},
            "params": [
                {
                    "name": "confirm",
                    "type": "bool",
                    "required": False,
                    "default": False,
                    "ui": {"control": "toggle", "label": "Confirm"},
                }
            ],
            "safety": {"requires_confirm": False},
            "enabled": True,
            "tags": ["romer_standard"],
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "action_def":
            return False
        for k in ("id", "title", "host_action"):
            v = data.get(k)
            if not isinstance(v, str) or not v.strip():
                return False
        if data.get("host_action_args") is not None and not isinstance(data.get("host_action_args"), dict):
            return False
        params = data.get("params")
        if params is not None and not isinstance(params, list):
            return False
        return True


class SimulationDefinitionTemplate(ZDirectObjectTemplate):
    """
    Simulation definition template (kind=simulation_def).

    Describes a simulation entrypoint + parameter specs. Intended to power
    "simulation runner" UIs that render the right control types without
    embedding placeholder text into inputs.
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Simulation Definition"
        self.metadata.description = self.metadata.description or "Defines a simulation (entrypoint + parameter specs + output kind)."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["simulation", "construct", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "kind": "simulation_def",
            "id": f"simdef_{uuid.uuid4().hex[:12]}",
            "title": "Raphael Equations",
            "description": "Compute forces/energy using Raphael equations.",
            # TheConstruct.run_simulation expects sim_type + params; keep it data-driven.
            "sim_type": "raphael",
            "entrypoint": {"host_action": "run_simulation", "args_mode": "kwargs"},
            "params": [
                {
                    "name": "protons",
                    "type": "int",
                    "required": True,
                    "default": 1,
                    "ui": {"control": "spinbox", "min": 0, "max": 500, "step": 1, "label": "Protons"},
                },
                {
                    "name": "neutrons",
                    "type": "int",
                    "required": True,
                    "default": 1,
                    "ui": {"control": "spinbox", "min": 0, "max": 500, "step": 1, "label": "Neutrons"},
                },
                {
                    "name": "electrons",
                    "type": "int",
                    "required": True,
                    "default": 1,
                    "ui": {"control": "spinbox", "min": 0, "max": 500, "step": 1, "label": "Electrons"},
                },
            ],
            "output_kind": "simulation_result",
            "enabled": True,
            "tags": ["romer_standard"],
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "simulation_def":
            return False
        for k in ("id", "title", "sim_type"):
            v = data.get(k)
            if not isinstance(v, str) or not v.strip():
                return False
        params = data.get("params")
        if params is not None and not isinstance(params, list):
            return False
        return True


class WorkflowDefinitionTemplate(ZDirectObjectTemplate):
    """
    Workflow definition template (kind=workflow_def).

    A workflow_def is an actionable series: steps that reference action_def and/or
    simulation_def ids with parameter bindings.
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.name = self.metadata.name or "Workflow Definition"
        self.metadata.description = self.metadata.description or "Defines a multi-step workflow (actions + simulations) with parameter bindings."
        self.metadata.tags = list(set((self.metadata.tags or []) + ["workflow", "automation", "z_direct"]))
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            "kind": "workflow_def",
            "id": f"wf_{uuid.uuid4().hex[:12]}",
            "title": "Example Workflow",
            "description": "Multi-step workflow example.",
            "steps": [
                {"kind": "action", "ref_id": "act_toggle_bento", "params": {}},
                {"kind": "simulation", "ref_id": "simdef_raphael", "params": {"protons": 1, "neutrons": 1, "electrons": 1}},
            ],
            "enabled": True,
            "tags": ["romer_standard"],
            "metadata": {"romer_standard": True},
        }

    def validate(self, data: Dict[str, Any]) -> bool:
        if not isinstance(data, dict) or data.get("kind") != "workflow_def":
            return False
        for k in ("id", "title"):
            v = data.get(k)
            if not isinstance(v, str) or not v.strip():
                return False
        steps = data.get("steps")
        if steps is not None and not isinstance(steps, list):
            return False
        return True


# ============================================================================
# TEST TEMPLATES
# ============================================================================

class TestTemplate(BaseTemplate):
    """
    Base class for test templates.

    Converts tests into productive validation/setup tools.
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        if not self.metadata.category:
            self.metadata.category = "test"

    @abstractmethod
    def run_test(self) -> Dict[str, Any]:
        """
        Run test and return results.

        Returns:
            Dictionary with test results
        """
        pass


class VenvSetupTemplate(TestTemplate):
    """
    Virtual environment setup template.

    Creates venv, installs requirements, validates installation.
    """

    def __init__(self, metadata: Optional[TemplateMetadata] = None):
        super().__init__(metadata)
        self.metadata.subcategory = "venv_setup"
        self.metadata.name = self.metadata.name or "Virtual Environment Setup"
        self.settings = self.get_default_settings()

    def get_default_settings(self) -> Dict[str, Any]:
        return {
            'venv_name': '.venv',
            'python_version': '3.10',
            'requirements_file': 'requirements.txt',
            'validate_imports': True
        }

    def render(self, data: Dict[str, Any]) -> Path:
        """Create venv with given configuration"""
        import subprocess
        import sys

        venv_path = Path(data.get('venv_name', self.settings['venv_name']))

        # Create venv
        subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)

        # Install requirements
        pip_path = venv_path / 'Scripts' / 'pip.exe' if sys.platform == 'win32' else venv_path / 'bin' / 'pip'
        requirements = data.get('requirements_file', self.settings['requirements_file'])
        if Path(requirements).exists():
            subprocess.run([str(pip_path), 'install', '-r', requirements], check=True)

        self.logger.info(f"Virtual environment created: {venv_path}")
        return venv_path

    def run_test(self) -> Dict[str, Any]:
        """Validate venv setup"""
        import subprocess
        import sys

        venv_name = self.settings.get("venv_name", ".venv")
        requirements_file = self.settings.get("requirements_file", "requirements.txt")
        validate_imports = bool(self.settings.get("validate_imports", True))

        venv_path = Path(venv_name)
        if sys.platform == "win32":
            python_path = venv_path / "Scripts" / "python.exe"
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            python_path = venv_path / "bin" / "python"
            pip_path = venv_path / "bin" / "pip"

        result: Dict[str, Any] = {
            "status": "error",
            "venv": str(venv_path),
            "venv_exists": venv_path.exists(),
            "python_path": str(python_path),
            "pip_path": str(pip_path),
            "python_ok": False,
            "pip_ok": False,
            "requirements_file": str(requirements_file),
            "requirements_exists": Path(requirements_file).exists(),
            "pip_check_ok": None,
            "pip_check_output": None,
        }

        if not result["venv_exists"]:
            result["message"] = "Virtual environment directory not found"
            return result

        if not python_path.exists():
            result["message"] = "Venv python executable not found"
            return result

        try:
            py_ver = subprocess.run([str(python_path), "--version"], capture_output=True, text=True, timeout=10)
            result["python_ok"] = py_ver.returncode == 0
            result["python_version"] = (py_ver.stdout or py_ver.stderr or "").strip()
        except Exception as e:
            result["python_ok"] = False
            result["python_error"] = str(e)

        if pip_path.exists():
            try:
                pip_ver = subprocess.run([str(pip_path), "--version"], capture_output=True, text=True, timeout=10)
                result["pip_ok"] = pip_ver.returncode == 0
                result["pip_version"] = (pip_ver.stdout or pip_ver.stderr or "").strip()
            except Exception as e:
                result["pip_ok"] = False
                result["pip_error"] = str(e)
        else:
            # `venv` should normally include pip; if it's missing, report clearly.
            result["pip_ok"] = False
            result["pip_error"] = "pip executable not found in venv"

        if result["pip_ok"] and validate_imports:
            try:
                check = subprocess.run([str(pip_path), "check"], capture_output=True, text=True, timeout=20)
                result["pip_check_ok"] = check.returncode == 0
                result["pip_check_output"] = (check.stdout or check.stderr or "").strip()
            except Exception as e:
                result["pip_check_ok"] = False
                result["pip_check_output"] = str(e)

        if result["python_ok"] and result["pip_ok"]:
            result["status"] = "success"
            result["message"] = "Venv is present and operational"
        else:
            result["status"] = "error"
            result["message"] = "Venv is incomplete or not operational"

        return result

    def validate(self, data: Dict[str, Any]) -> bool:
        venv_name = data.get("venv_name", self.settings.get("venv_name", ".venv"))
        if not isinstance(venv_name, str) or not venv_name.strip():
            return False

        requirements_file = data.get("requirements_file", self.settings.get("requirements_file", "requirements.txt"))
        if requirements_file is not None and not isinstance(requirements_file, str):
            return False

        return True


# ============================================================================
# TEMPLATE REGISTRY & MANAGER
# ============================================================================

class TemplateRegistry:
    """
    Central registry for all templates.

    Manages template discovery, instantiation, and storage.
    """

    def __init__(self):
        self.templates: Dict[str, Type[BaseTemplate]] = {}
        self.logger = get_services_logger()
        self._register_builtin_templates()

    def _register_builtin_templates(self):
        """Register built-in templates"""
        self.register(QRCodeTemplate)
        self.register(TableTemplate)
        self.register(ImageTemplate)
        self.register(AchillesDesktopTemplate)
        self.register(ArchitectureScorecardTemplate)
        self.register(ThemeTemplate)
        # Data templates (Z Direct objects / library primitives).
        self.register(VaultFileTemplate)
        self.register(ResearchQueryTemplate)
        self.register(DatasetTemplate)
        self.register(ExperimentRunTemplate)
        self.register(ProjectTemplate)
        self.register(KnowledgeNodeTemplate)
        self.register(CitationTemplate)
        self.register(WorkspaceTemplate)
        self.register(LearningModuleTemplate)
        self.register(SimulationResultTemplate)
        self.register(BentoWidgetDefinitionTemplate)
        self.register(ZDirectSchemaTemplate)
        self.register(ActionDefinitionTemplate)
        self.register(SimulationDefinitionTemplate)
        self.register(WorkflowDefinitionTemplate)
        self.register(VenvSetupTemplate)

    def register(self, template_class: Type[BaseTemplate]):
        """Register a template class"""
        self.templates[template_class.__name__] = template_class
        self.logger.debug(f"Registered template: {template_class.__name__}")

    def get_template(self, template_name: str) -> Optional[BaseTemplate]:
        """Get template instance by name"""
        if template_name in self.templates:
            return self.templates[template_name]()
        return None

    def list_templates(self, category: Optional[str] = None) -> List[str]:
        """List available templates, optionally filtered by category"""
        if category:
            return [name for name, cls in self.templates.items()
                   if cls().metadata.category == category]
        return list(self.templates.keys())

    def create_from_config(self, config: Dict[str, Any]) -> Optional[BaseTemplate]:
        """Create template from exported configuration"""
        template_type = config.get('type')
        if template_type in self.templates:
            template = self.templates[template_type]()
            template.import_template(config)
            return template
        return None


# Global registry instance
_template_registry = TemplateRegistry()


def get_template_registry() -> TemplateRegistry:
    """Get global template registry"""
    return _template_registry


if __name__ == "__main__":
    # Test suite
    print("=" * 70)
    print("TEMPLATE SYSTEM - Test Suite")
    print("=" * 70)

    registry = get_template_registry()

    # Test 1: QR Code Template
    print("\n[1] QR Code Template")
    qr_template = registry.get_template("QRCodeTemplate")
    qr_template.customize({'fill_color': 'blue', 'size': 15})
    qr_path = qr_template.render({
        'content': 'https://lightspeed.platform',
        'filename': 'lightspeed_qr.png'
    })
    print(f"  QR code generated: {qr_path}")

    # Test 2: Table Template
    print("\n[2] Table Template")
    table_template = registry.get_template("TableTemplate")
    table_path = table_template.render({
        'headers': ['Name', 'Age', 'City'],
        'rows': [
            ['Alice', 30, 'New York'],
            ['Bob', 25, 'San Francisco'],
            ['Charlie', 35, 'Chicago']
        ],
        'filename': 'demo_table.html'
    })
    print(f"  Table generated: {table_path}")

    # Test 3: Theme Template
    print("\n[3] Theme Template")
    theme_template = registry.get_template("ThemeTemplate")
    theme_config = theme_template.render({'name': 'Custom Dark Theme'})
    print(f"  Theme colors: {theme_config['colors']['primary']}")

    # Test 4: List Templates
    print("\n[4] Available Templates")
    print(f"  Document templates: {registry.list_templates('document')}")
    print(f"  UI templates: {registry.list_templates('ui')}")
    print(f"  Test templates: {registry.list_templates('test')}")

    print("\n" + "=" * 70)
    print("All tests passed! Template System ready.")
    print("=" * 70)
