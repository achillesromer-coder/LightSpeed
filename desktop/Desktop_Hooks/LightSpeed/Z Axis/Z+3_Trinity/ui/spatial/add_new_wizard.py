"""
LightSpeed V0.9.11 - Ollama-Powered "Add New" Tile Wizard
Smart tile creation wizard with AI-guided suggestions

Features:
- Ollama-powered intelligent suggestions
- Floor-aware creation (adapts to Z-floor context)
- Support for all tile types (venv, parameters, tools, widgets, functions, datasets)
- Real-time validation
- Template library
- Track-as-you-go creation logging

Author: LightSpeed Team / ACHILLES
Version: 0.9.11
Date: January 4, 2026
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import requests

from .enhanced_bento_grid import BentoTile, TileType
from core.config.paths import NEO_CONTEXT, SMITH_LOGS


class WizardStep(Enum):
    """Wizard creation steps"""
    TYPE_SELECTION = "select_type"
    BASIC_INFO = "basic_info"
    ADVANCED_CONFIG = "advanced_config"
    AI_SUGGESTIONS = "ai_suggestions"
    CONFIRMATION = "confirmation"


@dataclass
class TileTemplate:
    """Pre-configured tile template"""
    name: str
    type: TileType
    description: str
    default_config: Dict[str, Any]
    floor_hints: List[str]  # Which Z-floors this is relevant for


class OllamaClient:
    """
    Client for Ollama AI suggestions.
    Provides intelligent guidance for tile creation.
    """

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = "llama2"  # Default model

    def get_suggestion(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Get AI suggestion for tile creation.

        Args:
            context: Dictionary with type, floor, purpose, existing_tiles

        Returns:
            AI-generated suggestion text or None if unavailable
        """
        try:
            prompt = self._build_prompt(context)

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()

            return None

        except Exception as e:
            print(f"[OLLAMA] Connection failed: {e}")
            return None

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for Ollama based on context"""
        tile_type = context.get("type", "unknown")
        floor = context.get("floor", "unknown")
        purpose = context.get("purpose", "")

        prompt = f"""You are an AI assistant helping create a {tile_type} tile for the {floor} floor of LightSpeed platform.

Context:
- Tile Type: {tile_type}
- Z-Floor: {floor}
- Purpose: {purpose}

Based on LightSpeed architecture:
- Z+3 Neo: Internal AI agent coordination
- Z+2 Morpheus: Encyclopedia, empirical knowledge library
- Z+1 Architect: Planning, tools, design
- Z0 TheConstruct: Physics simulations, render engine
- Z-1 Oracle: Archive, immersive visual library
- Z-2 Smith: Background tasks, Neo integration
- Z-3 Merovingian: Non-empirical data, user profiles
- Z-4 Trinity: Settings management, environment rendering

Suggest:
1. Recommended parameters/configuration for this tile
2. How it should integrate with the {floor} floor
3. Any dependencies or prerequisites
4. Best practices for this tile type

Keep response concise (3-5 sentences)."""

        return prompt


class AddNewWizard:
    """
    Ollama-powered wizard for creating new Bento tiles.

    Guides users through tile creation with AI suggestions.
    """

    # Tile templates library
    TEMPLATES = [
        TileTemplate(
            name="Python Virtual Environment",
            type=TileType.VENV,
            description="Create isolated Python environment",
            default_config={
                "python_version": "3.11",
                "packages": ["numpy", "pandas"],
                "location": "./venv"
            },
            floor_hints=["Z+1_Architect", "Z0_TheConstruct"]
        ),
        TileTemplate(
            name="Data Analysis Widget",
            type=TileType.WIDGET,
            description="Interactive data visualization",
            default_config={
                "chart_type": "line",
                "data_source": "",
                "refresh_rate": 5
            },
            floor_hints=["Z-1_Morpheus", "Z0_TheConstruct"]
        ),
        TileTemplate(
            name="Background Task",
            type=TileType.TASK,
            description="Scheduled or automated task",
            default_config={
                "schedule": "daily",
                "priority": "normal",
                "timeout": 3600
            },
            floor_hints=["Z-3_Smith"]
        ),
        TileTemplate(
            name="Dataset Loader",
            type=TileType.DATASET,
            description="Load and manage datasets",
            default_config={
                "format": "csv",
                "path": "",
                "cache": True
            },
            floor_hints=["Z-4_Merovingian", "Z-1_Morpheus"]
        ),
        TileTemplate(
            name="Custom Function",
            type=TileType.FUNCTION,
            description="Python function wrapper",
            default_config={
                "name": "",
                "parameters": [],
                "return_type": "any"
            },
            floor_hints=["Z+1_Architect", "Z0_TheConstruct"]
        ),
        TileTemplate(
            name="Configuration Parameter",
            type=TileType.PARAMETER,
            description="System configuration parameter",
            default_config={
                "name": "",
                "value": "",
                "type": "string",
                "scope": "global"
            },
            floor_hints=["Z+3_Trinity"]
        ),
        TileTemplate(
            name="Project Folder",
            type=TileType.FOLDER,
            description="Organize related tiles",
            default_config={
                "path": "",
                "icon": "folder",
                "children": []
            },
            floor_hints=["All floors"]
        ),
        TileTemplate(
            name="Analysis Tool",
            type=TileType.TOOL,
            description="Data processing or analysis tool",
            default_config={
                "tool_type": "",
                "input_format": "",
                "output_format": ""
            },
            floor_hints=["Z+1_Architect", "Z0_TheConstruct"]
        )
    ]

    def __init__(self, parent: tk.Toplevel, current_floor: str,
                 on_complete: Callable[[BentoTile], None],
                 ollama_url: str = "http://localhost:11434"):
        """
        Initialize Add New wizard.

        Args:
            parent: Parent window
            current_floor: Current Z-floor name (e.g., "Z+2_Morpheus")
            on_complete: Callback when tile is created
            ollama_url: Ollama API base URL
        """
        self.parent = parent
        self.current_floor = current_floor
        self.on_complete = on_complete

        # AI client
        self.ollama = OllamaClient(ollama_url)

        # Wizard state
        self.current_step = WizardStep.TYPE_SELECTION
        self.tile_data: Dict[str, Any] = {
            "type": None,
            "label": "",
            "position": (0.0, 1.5, 0.0),  # Default position
            "size": (200, 120),
            "depth": 0.5,
            "config": {}
        }

        # Create wizard UI
        self._create_ui()

        # Log creation process
        self.creation_log_path = SMITH_LOGS / "tile_creation.log"

    def _create_ui(self):
        """Create wizard UI"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Add New Tile - LightSpeed V0.9.11")
        self.window.geometry("600x500")
        self.window.configure(bg='#0A1628')

        # Title
        title = tk.Label(
            self.window,
            text=f"Create New Tile - {self.current_floor}",
            font=('Segoe UI', 16, 'bold'),
            bg='#0A1628',
            fg='#00FFFF'
        )
        title.pack(pady=20)

        # Content frame (changes per step)
        self.content_frame = tk.Frame(self.window, bg='#0A1628')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # AI suggestion panel (initially hidden)
        self.ai_panel = tk.Frame(self.window, bg='#102040', relief=tk.RAISED, bd=2)
        self.ai_label = tk.Label(
            self.ai_panel,
            text="AI Suggestion",
            font=('Segoe UI', 10, 'bold'),
            bg='#102040',
            fg='#00FFFF'
        )
        self.ai_label.pack(anchor=tk.W, padx=10, pady=5)

        self.ai_text = tk.Text(
            self.ai_panel,
            height=4,
            bg='#0A1628',
            fg='#FFFFFF',
            font=('Segoe UI', 9),
            wrap=tk.WORD,
            relief=tk.FLAT
        )
        self.ai_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Navigation buttons
        nav_frame = tk.Frame(self.window, bg='#0A1628')
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)

        self.back_btn = tk.Button(
            nav_frame,
            text="< Back",
            command=self._go_back,
            bg='#1E3A5F',
            fg='#FFFFFF',
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        self.back_btn.pack(side=tk.LEFT)

        self.cancel_btn = tk.Button(
            nav_frame,
            text="Cancel",
            command=self.window.destroy,
            bg='#601010',
            fg='#FFFFFF',
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=10)

        self.next_btn = tk.Button(
            nav_frame,
            text="Next >",
            command=self._go_next,
            bg='#00FFFF',
            fg='#000000',
            font=('Segoe UI', 10, 'bold'),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        self.next_btn.pack(side=tk.RIGHT)

        # Render first step
        self._render_step()

    def _render_step(self):
        """Render current wizard step"""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Update button states
        self.back_btn.config(state=tk.DISABLED if self.current_step == WizardStep.TYPE_SELECTION else tk.NORMAL)

        # Render based on step
        if self.current_step == WizardStep.TYPE_SELECTION:
            self._render_type_selection()
        elif self.current_step == WizardStep.BASIC_INFO:
            self._render_basic_info()
        elif self.current_step == WizardStep.ADVANCED_CONFIG:
            self._render_advanced_config()
        elif self.current_step == WizardStep.AI_SUGGESTIONS:
            self._render_ai_suggestions()
        elif self.current_step == WizardStep.CONFIRMATION:
            self._render_confirmation()

    def _render_type_selection(self):
        """Step 1: Select tile type"""
        instruction = tk.Label(
            self.content_frame,
            text="Select the type of tile you want to create:",
            font=('Segoe UI', 11),
            bg='#0A1628',
            fg='#FFFFFF'
        )
        instruction.pack(anchor=tk.W, pady=10)

        # Get templates relevant to current floor
        relevant_templates = [
            t for t in self.TEMPLATES
            if "All floors" in t.floor_hints or self.current_floor in t.floor_hints
        ]

        # Create selection buttons
        for template in relevant_templates:
            frame = tk.Frame(self.content_frame, bg='#102040', relief=tk.RAISED, bd=1)
            frame.pack(fill=tk.X, pady=5)

            btn = tk.Button(
                frame,
                text=template.name,
                command=lambda t=template: self._select_template(t),
                bg='#102040',
                fg='#00FFFF',
                font=('Segoe UI', 10, 'bold'),
                relief=tk.FLAT,
                anchor=tk.W,
                padx=15,
                pady=10
            )
            btn.pack(fill=tk.X)

            desc = tk.Label(
                frame,
                text=template.description,
                bg='#102040',
                fg='#AAAAAA',
                font=('Segoe UI', 9),
                anchor=tk.W,
                padx=15,
                pady=5
            )
            desc.pack(fill=tk.X)

    def _select_template(self, template: TileTemplate):
        """Handle template selection"""
        self.tile_data["type"] = template.type
        self.tile_data["template"] = template
        self.tile_data["config"] = template.default_config.copy()

        # Auto-advance
        self._go_next()

    def _render_basic_info(self):
        """Step 2: Basic tile information"""
        instruction = tk.Label(
            self.content_frame,
            text=f"Configure your {self.tile_data['type'].value}:",
            font=('Segoe UI', 11),
            bg='#0A1628',
            fg='#FFFFFF'
        )
        instruction.pack(anchor=tk.W, pady=10)

        # Label input
        label_frame = tk.Frame(self.content_frame, bg='#0A1628')
        label_frame.pack(fill=tk.X, pady=10)

        tk.Label(
            label_frame,
            text="Tile Label:",
            bg='#0A1628',
            fg='#FFFFFF',
            font=('Segoe UI', 10)
        ).pack(side=tk.LEFT)

        self.label_entry = tk.Entry(
            label_frame,
            bg='#102040',
            fg='#FFFFFF',
            font=('Segoe UI', 10),
            relief=tk.FLAT,
            insertbackground='#00FFFF'
        )
        self.label_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        if self.tile_data.get("label"):
            self.label_entry.insert(0, self.tile_data["label"])

        # Position controls
        pos_frame = tk.Frame(self.content_frame, bg='#0A1628')
        pos_frame.pack(fill=tk.X, pady=10)

        tk.Label(
            pos_frame,
            text="Position (Angle):",
            bg='#0A1628',
            fg='#FFFFFF',
            font=('Segoe UI', 10)
        ).pack(side=tk.LEFT)

        self.angle_scale = tk.Scale(
            pos_frame,
            from_=-50,
            to=50,
            orient=tk.HORIZONTAL,
            bg='#102040',
            fg='#00FFFF',
            highlightthickness=0,
            troughcolor='#0A1628'
        )
        self.angle_scale.set(0)
        self.angle_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Depth control
        depth_frame = tk.Frame(self.content_frame, bg='#0A1628')
        depth_frame.pack(fill=tk.X, pady=10)

        tk.Label(
            depth_frame,
            text="Depth (Glass Thickness):",
            bg='#0A1628',
            fg='#FFFFFF',
            font=('Segoe UI', 10)
        ).pack(side=tk.LEFT)

        self.depth_scale = tk.Scale(
            depth_frame,
            from_=0.0,
            to=1.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            bg='#102040',
            fg='#00FFFF',
            highlightthickness=0,
            troughcolor='#0A1628'
        )
        self.depth_scale.set(0.5)
        self.depth_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Request AI suggestion
        self._request_ai_suggestion()

    def _render_advanced_config(self):
        """Step 3: Advanced configuration (template-specific)"""
        instruction = tk.Label(
            self.content_frame,
            text="Advanced Configuration:",
            font=('Segoe UI', 11),
            bg='#0A1628',
            fg='#FFFFFF'
        )
        instruction.pack(anchor=tk.W, pady=10)

        # Create inputs for template config
        template = self.tile_data.get("template")
        if template:
            self.config_entries = {}

            for key, default_value in template.default_config.items():
                frame = tk.Frame(self.content_frame, bg='#0A1628')
                frame.pack(fill=tk.X, pady=5)

                tk.Label(
                    frame,
                    text=f"{key.replace('_', ' ').title()}:",
                    bg='#0A1628',
                    fg='#FFFFFF',
                    font=('Segoe UI', 10),
                    width=20,
                    anchor=tk.W
                ).pack(side=tk.LEFT)

                entry = tk.Entry(
                    frame,
                    bg='#102040',
                    fg='#FFFFFF',
                    font=('Segoe UI', 10),
                    relief=tk.FLAT,
                    insertbackground='#00FFFF'
                )
                entry.insert(0, str(default_value))
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

                self.config_entries[key] = entry

    def _render_ai_suggestions(self):
        """Step 4: Show AI suggestions and recommendations"""
        instruction = tk.Label(
            self.content_frame,
            text="Review AI Recommendations:",
            font=('Segoe UI', 11),
            bg='#0A1628',
            fg='#FFFFFF'
        )
        instruction.pack(anchor=tk.W, pady=10)

        # Show AI panel
        self.ai_panel.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Refresh AI suggestion with full context
        self._request_ai_suggestion(full_context=True)

        # Option to regenerate
        regen_btn = tk.Button(
            self.content_frame,
            text="Regenerate AI Suggestion",
            command=lambda: self._request_ai_suggestion(full_context=True),
            bg='#1E3A5F',
            fg='#FFFFFF',
            font=('Segoe UI', 9),
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        regen_btn.pack(pady=10)

    def _render_confirmation(self):
        """Step 5: Final confirmation"""
        instruction = tk.Label(
            self.content_frame,
            text="Confirm Tile Creation:",
            font=('Segoe UI', 11),
            bg='#0A1628',
            fg='#FFFFFF'
        )
        instruction.pack(anchor=tk.W, pady=10)

        # Summary
        summary_frame = tk.Frame(self.content_frame, bg='#102040', relief=tk.RAISED, bd=2)
        summary_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        summary_text = f"""
Type: {self.tile_data['type'].value}
Label: {self.tile_data['label']}
Floor: {self.current_floor}
Position: Angle {self.tile_data['position'][0]}°, Distance {self.tile_data['position'][1]}m
Depth: {self.tile_data['depth']}

Configuration:
{json.dumps(self.tile_data['config'], indent=2)}
        """.strip()

        summary_label = tk.Label(
            summary_frame,
            text=summary_text,
            bg='#102040',
            fg='#FFFFFF',
            font=('Courier', 9),
            justify=tk.LEFT,
            anchor=tk.NW
        )
        summary_label.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Change next button to "Create"
        self.next_btn.config(text="Create Tile", command=self._create_tile)

    def _request_ai_suggestion(self, full_context: bool = False):
        """Request AI suggestion from Ollama"""
        context = {
            "type": self.tile_data.get("type").value if self.tile_data.get("type") else "unknown",
            "floor": self.current_floor,
            "purpose": self.tile_data.get("label", ""),
        }

        if full_context:
            context["config"] = self.tile_data.get("config", {})

        # Show loading
        if hasattr(self, 'ai_text'):
            self.ai_text.delete('1.0', tk.END)
            self.ai_text.insert('1.0', "Requesting AI suggestion...")

        # Get suggestion (async would be better, but keeping it simple)
        suggestion = self.ollama.get_suggestion(context)

        if suggestion:
            if hasattr(self, 'ai_text'):
                self.ai_text.delete('1.0', tk.END)
                self.ai_text.insert('1.0', suggestion)
        else:
            if hasattr(self, 'ai_text'):
                self.ai_text.delete('1.0', tk.END)
                self.ai_text.insert('1.0', "AI suggestions unavailable (Ollama not running or unreachable)")

    def _go_back(self):
        """Go to previous step"""
        steps = list(WizardStep)
        current_idx = steps.index(self.current_step)

        if current_idx > 0:
            self.current_step = steps[current_idx - 1]
            self._render_step()

    def _go_next(self):
        """Go to next step"""
        # Validate current step
        if self.current_step == WizardStep.TYPE_SELECTION:
            if not self.tile_data.get("type"):
                messagebox.showerror("Error", "Please select a tile type")
                return

        elif self.current_step == WizardStep.BASIC_INFO:
            # Save label
            self.tile_data["label"] = self.label_entry.get().strip()
            if not self.tile_data["label"]:
                messagebox.showerror("Error", "Please enter a tile label")
                return

            # Save position
            angle = self.angle_scale.get()
            self.tile_data["position"] = (angle, 1.5, 0.0)

            # Save depth
            self.tile_data["depth"] = self.depth_scale.get()

        elif self.current_step == WizardStep.ADVANCED_CONFIG:
            # Save config values
            if hasattr(self, 'config_entries'):
                for key, entry in self.config_entries.items():
                    self.tile_data["config"][key] = entry.get()

        # Advance
        steps = list(WizardStep)
        current_idx = steps.index(self.current_step)

        if current_idx < len(steps) - 1:
            self.current_step = steps[current_idx + 1]
            self._render_step()

    def _create_tile(self):
        """Create the tile and close wizard"""
        try:
            # Generate unique ID
            import time
            tile_id = f"{self.tile_data['type'].value}_{int(time.time() * 1000)}"

            # Create BentoTile
            tile = BentoTile(
                id=tile_id,
                type=self.tile_data["type"],
                label=self.tile_data["label"],
                position=self.tile_data["position"],
                size=self.tile_data["size"],
                depth=self.tile_data["depth"],
                data=self.tile_data["config"]
            )

            # Log creation
            self._log_creation(tile)

            # Callback
            self.on_complete(tile)

            # Close wizard
            self.window.destroy()

            messagebox.showinfo("Success", f"Tile '{tile.label}' created successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create tile: {e}")

    def _log_creation(self, tile: BentoTile):
        """Log tile creation to track-as-you-go"""
        import datetime

        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "floor": self.current_floor,
            "tile_id": tile.id,
            "type": tile.type.value,
            "label": tile.label,
            "config": tile.data
        }

        try:
            # Ensure log directory exists
            self.creation_log_path.parent.mkdir(parents=True, exist_ok=True)

            # Append to log
            with open(self.creation_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            print(f"[WIZARD] Failed to log creation: {e}")


# Export
__all__ = ['AddNewWizard', 'OllamaClient', 'TileTemplate']
