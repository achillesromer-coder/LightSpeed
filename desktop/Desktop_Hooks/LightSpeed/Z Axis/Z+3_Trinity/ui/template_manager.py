"""
Template Manager UI Component
LightSpeed operator setup and template surface.

User-friendly interface for browsing, customizing, and generating templates.

Features:
- Browse templates by category (Document, UI, Test)
- Customize template settings with live preview
- Default-settings, current-template, and custom-template workflows
- Save custom templates to database
- Integration with Settings Dialog

Author: LightSpeed Team
Version: 5.1.2
Date: April 8, 2026
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from typing import Dict, Any, Optional, List
import json
from pathlib import Path

from core.services import (
    get_template_registry,
    BaseTemplate,
    DocumentTemplate,
    UITemplate,
    TestTemplate,
    get_db
)

GENERATION_MODE_OPTIONS = [
    ("Use current customizations", "template"),
    ("Reset to defaults before generate", "defaults"),
]


class TemplateManagerDialog:
    """
    Template Manager Dialog - Browse and customize templates.

    Provides user-friendly interface for:
    - Browsing available templates by category
    - Customizing template settings
    - Live preview of changes
    - Generating outputs from templates
    - Saving custom template configurations

    Usage:
        dialog = TemplateManagerDialog(parent_window)
        dialog.show()
    """

    def __init__(self, parent: tk.Tk):
        """
        Initialize Template Manager Dialog.

        Args:
            parent: Parent window
        """
        self.parent = parent
        self.registry = get_template_registry()
        self.db = get_db()
        self.current_template: Optional[BaseTemplate] = None
        self.custom_settings: Dict[str, Any] = {}
        self.generation_mode = tk.StringVar(value="template")

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Template Manager - LightSpeed Platform")
        self.dialog.geometry("1000x700")
        self.dialog.transient(parent)

        self._setup_ui()
        self._load_templates()

    def _setup_ui(self):
        """Setup UI layout."""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Template Manager",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Subtitle
        subtitle_label = ttk.Label(
            main_frame,
            text="Create professional documents, UI themes, and test environments from customizable templates",
            font=("Segoe UI", 9)
        )
        subtitle_label.pack(pady=(0, 20))

        # Content area (3 columns: category, templates, customization)
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left column - Category selection
        self._setup_category_panel(content_frame)

        # Middle column - Template list
        self._setup_template_list_panel(content_frame)

        # Right column - Customization panel
        self._setup_customization_panel(content_frame)

        # Bottom buttons
        self._setup_action_buttons(main_frame)

    def _setup_category_panel(self, parent):
        """Setup category selection panel."""
        category_frame = ttk.LabelFrame(parent, text="Categories", padding=10)
        category_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Category listbox
        self.category_listbox = tk.Listbox(
            category_frame,
            font=("Segoe UI", 10),
            selectmode=tk.SINGLE,
            height=15
        )
        self.category_listbox.pack(fill=tk.BOTH, expand=True)

        # Add categories
        categories = ["All Templates", "Document Templates", "UI Templates", "Data Templates", "Test Templates"]
        for cat in categories:
            self.category_listbox.insert(tk.END, cat)

        self.category_listbox.selection_set(0)
        self.category_listbox.bind("<<ListboxSelect>>", self._on_category_select)

        # Category stats
        self.category_stats_label = ttk.Label(
            category_frame,
            text="0 templates available",
            font=("Segoe UI", 8)
        )
        self.category_stats_label.pack(pady=(10, 0))

    def _setup_template_list_panel(self, parent):
        """Setup template list panel."""
        template_frame = ttk.LabelFrame(parent, text="Templates", padding=10)
        template_frame.grid(row=0, column=1, sticky="nsew", padx=5)

        # Template listbox with scrollbar
        list_container = ttk.Frame(template_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.template_listbox = tk.Listbox(
            list_container,
            font=("Segoe UI", 10),
            selectmode=tk.SINGLE,
            yscrollcommand=scrollbar.set
        )
        self.template_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.template_listbox.yview)

        self.template_listbox.bind("<<ListboxSelect>>", self._on_template_select)

        # Template description
        desc_frame = ttk.LabelFrame(template_frame, text="Description", padding=5)
        desc_frame.pack(fill=tk.X, pady=(10, 0))

        self.template_desc_text = tk.Text(
            desc_frame,
            height=4,
            wrap=tk.WORD,
            font=("Segoe UI", 9),
            state=tk.DISABLED
        )
        self.template_desc_text.pack(fill=tk.BOTH, expand=True)

    def _setup_customization_panel(self, parent):
        """Setup customization panel with live settings editor."""
        custom_frame = ttk.LabelFrame(parent, text="Customize Template", padding=10)
        custom_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))

        # Scrollable customization area
        canvas = tk.Canvas(custom_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(custom_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.custom_container = ttk.Frame(canvas)

        self.custom_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.custom_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.settings_widgets: Dict[str, tk.Widget] = {}

        # Preview button
        preview_btn = ttk.Button(
            custom_frame,
            text="Preview Changes",
            command=self._preview_template
        )
        preview_btn.pack(pady=(10, 0))

        # Configure grid weights
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=2)
        parent.grid_columnconfigure(2, weight=2)
        parent.grid_rowconfigure(0, weight=1)

    def _setup_action_buttons(self, parent):
        """Setup action buttons at bottom."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        template_btn = ttk.Menubutton(button_frame, text="Template Actions")
        template_menu = tk.Menu(template_btn, tearoff=0)
        mode_menu = tk.Menu(template_menu, tearoff=0)
        for label, value in GENERATION_MODE_OPTIONS:
            mode_menu.add_radiobutton(
                label=label,
                variable=self.generation_mode,
                value=value,
            )
        template_menu.add_cascade(label="Generate Mode", menu=mode_menu)
        template_menu.add_separator()
        template_menu.add_command(label="Generate Output", command=self._create_output)
        template_menu.add_command(label="Save as Custom", command=self._save_custom_template)
        template_menu.add_command(label="Generate", command=self._generate_output)
        template_menu.add_separator()
        template_menu.add_command(label="Close", command=self.dialog.destroy)
        template_btn.config(menu=template_menu)
        template_btn.pack(side=tk.RIGHT)

    def _load_templates(self):
        """Load all available templates from registry."""
        # Get all registered templates
        all_templates = self.registry.list_templates()

        # Populate template listbox
        self.template_listbox.delete(0, tk.END)
        for template_name in sorted(all_templates):
            self.template_listbox.insert(tk.END, template_name)

        # Update stats
        self.category_stats_label.config(text=f"{len(all_templates)} templates available")

    def _on_category_select(self, event):
        """Handle category selection."""
        selection = self.category_listbox.curselection()
        if not selection:
            return

        category = self.category_listbox.get(selection[0])

        all_templates = self.registry.list_templates()

        def _category_of(template_name: str) -> str:
            try:
                inst = self.registry.get_template(template_name)
                return str(getattr(getattr(inst, "metadata", None), "category", "") or "").strip().lower()
            except Exception:
                return ""

        filtered: List[str] = []
        if category == "All Templates":
            filtered = all_templates
        elif category == "Document Templates":
            filtered = [t for t in all_templates if _category_of(t) == "document"]
        elif category == "UI Templates":
            filtered = [t for t in all_templates if _category_of(t) == "ui"]
        elif category == "Data Templates":
            filtered = [t for t in all_templates if _category_of(t) == "data"]
        elif category == "Test Templates":
            filtered = [t for t in all_templates if _category_of(t) == "test"]

        # Update template list
        self.template_listbox.delete(0, tk.END)
        for template_name in sorted(filtered):
            self.template_listbox.insert(tk.END, template_name)

        self.category_stats_label.config(text=f"{len(filtered)} templates in category")

    def _on_template_select(self, event):
        """Handle template selection."""
        selection = self.template_listbox.curselection()
        if not selection:
            return

        template_name = self.template_listbox.get(selection[0])

        # Get template instance
        self.current_template = self.registry.get_template(template_name)
        if not self.current_template:
            return

        # Update description
        self._update_description()

        # Build customization UI
        self._build_customization_ui()

    def _update_description(self):
        """Update template description text."""
        if not self.current_template:
            return

        # Get template info
        template_class = type(self.current_template).__name__
        template_doc = self.current_template.__doc__ or "No description available"

        # Extract first line of docstring
        desc_lines = template_doc.strip().split('\n')
        description = desc_lines[0].strip()

        # Update text widget
        self.template_desc_text.config(state=tk.NORMAL)
        self.template_desc_text.delete("1.0", tk.END)
        self.template_desc_text.insert("1.0", f"{template_class}\n\n{description}")
        self.template_desc_text.config(state=tk.DISABLED)

    def _build_customization_ui(self):
        """Build dynamic customization UI based on template settings."""
        # Clear existing widgets
        for widget in self.custom_container.winfo_children():
            widget.destroy()
        self.settings_widgets.clear()

        if not self.current_template:
            return

        # Get default settings
        default_settings = self.current_template.get_default_settings()
        self.custom_settings = default_settings.copy()

        # Create widgets for each setting
        row = 0
        for key, value in default_settings.items():
            # Label
            label = ttk.Label(
                self.custom_container,
                text=key.replace('_', ' ').title() + ":",
                font=("Segoe UI", 9)
            )
            label.grid(row=row, column=0, sticky="w", pady=5, padx=(0, 10))

            # Widget based on value type
            if isinstance(value, bool):
                # Checkbox for boolean
                var = tk.BooleanVar(value=value)
                widget = ttk.Checkbutton(
                    self.custom_container,
                    variable=var,
                    command=lambda k=key, v=var: self._update_setting(k, v.get())
                )
                self.settings_widgets[key] = var

            elif isinstance(value, int):
                # Spinbox for integer
                var = tk.IntVar(value=value)
                widget = ttk.Spinbox(
                    self.custom_container,
                    from_=1,
                    to=100,
                    textvariable=var,
                    width=10,
                    command=lambda k=key, v=var: self._update_setting(k, v.get())
                )
                self.settings_widgets[key] = var

            elif isinstance(value, str) and value.startswith('#'):
                # Color picker for hex colors
                widget = ttk.Frame(self.custom_container)
                color_var = tk.StringVar(value=value)

                color_entry = ttk.Entry(widget, textvariable=color_var, width=10)
                color_entry.pack(side=tk.LEFT, padx=(0, 5))

                def pick_color(k=key, v=color_var):
                    color = colorchooser.askcolor(initialcolor=v.get())[1]
                    if color:
                        v.set(color)
                        self._update_setting(k, color)

                color_btn = ttk.Button(widget, text="Pick", command=pick_color, width=6)
                color_btn.pack(side=tk.LEFT)

                self.settings_widgets[key] = color_var

            else:
                # Entry for strings
                var = tk.StringVar(value=str(value))
                widget = ttk.Entry(
                    self.custom_container,
                    textvariable=var,
                    width=20
                )
                widget.bind(
                    "<KeyRelease>",
                    lambda e, k=key, v=var: self._update_setting(k, v.get())
                )
                self.settings_widgets[key] = var

            widget.grid(row=row, column=1, sticky="ew", pady=5)
            row += 1

        # Configure column weights
        self.custom_container.grid_columnconfigure(1, weight=1)

    def _update_setting(self, key: str, value: Any):
        """Update setting value."""
        self.custom_settings[key] = value

    def _preview_template(self):
        """Preview template with current settings."""
        if not self.current_template:
            messagebox.showwarning("No Template", "Please select a template first.")
            return

        try:
            # Apply custom settings
            self.current_template.customize(self.custom_settings)

            # Validate settings
            if self.current_template.validate(self.custom_settings):
                messagebox.showinfo(
                    "Preview",
                    f"Template: {type(self.current_template).__name__}\n\n"
                    f"Settings validated successfully!\n\n"
                    f"Customizations:\n" +
                    "\n".join(f"  {k}: {v}" for k, v in self.custom_settings.items())
                )
            else:
                messagebox.showerror(
                    "Validation Error",
                    "Template settings validation failed. Please check your inputs."
                )
        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to preview template:\n{str(e)}")

    def _create_blank(self):
        """Create output from blank template (default settings)."""
        if not self.current_template:
            messagebox.showwarning("No Template", "Please select a template first.")
            return

        # Reset to defaults
        default_settings = self.current_template.get_default_settings()
        self.current_template.customize(default_settings)

        # Generate output
        self._generate_with_data_prompt()

    def _create_from_template(self):
        """Create output from template with current customizations."""
        if not self.current_template:
            messagebox.showwarning("No Template", "Please select a template first.")
            return

        # Apply current settings
        self.current_template.customize(self.custom_settings)

        # Generate output
        self._generate_with_data_prompt()

    def _create_output(self):
        """Create output using the selected generation mode."""
        if str(self.generation_mode.get() or "template") == "defaults":
            self._create_blank()
            return
        self._create_from_template()

    def _generate_with_data_prompt(self):
        """Prompt for data and generate template output."""
        # Create data input dialog
        data_dialog = tk.Toplevel(self.dialog)
        data_dialog.title("Template Data")
        data_dialog.geometry("500x400")
        data_dialog.transient(self.dialog)
        data_dialog.grab_set()
        data_dialog.protocol("WM_DELETE_WINDOW", data_dialog.destroy)

        ttk.Label(
            data_dialog,
            text="Enter template data (JSON format):",
            font=("Segoe UI", 10)
        ).pack(pady=10)

        # Text area for JSON input
        text_frame = ttk.Frame(data_dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        data_text = tk.Text(
            text_frame,
            font=("Consolas", 9),
            yscrollcommand=scrollbar.set
        )
        data_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=data_text.yview)

        # Insert example data
        example_data = self._get_example_data()
        data_text.insert("1.0", json.dumps(example_data, indent=2))

        def generate():
            try:
                # Parse JSON data
                data_str = data_text.get("1.0", tk.END).strip()
                data = json.loads(data_str)

                # Generate output
                output = self.current_template.render(data)

                messagebox.showinfo(
                    "Success",
                    f"Template generated successfully!\n\nOutput: {output}"
                )

                # Optional: Stage generated Z Direct payloads into Trinity's append-only streams.
                # This keeps Template Manager non-destructive (no durable commits) while enabling
                # "generate -> stage -> approve/commit" workflows via the IT Portal.
                try:
                    meta = getattr(self.current_template, "metadata", None)
                    category = str(getattr(meta, "category", "") or "").strip().lower()
                    if category == "data":
                        self._maybe_stage_output_to_z_direct(output)
                except Exception:
                    pass
                try:
                    import webbrowser
                    from pathlib import Path

                    path_obj: Optional[Path] = None
                    if isinstance(output, Path):
                        path_obj = output
                    elif isinstance(output, str):
                        p = Path(output)
                        path_obj = p if p.exists() else None

                    if path_obj and path_obj.suffix.lower() in {".html", ".htm"}:
                        if messagebox.askyesno("Open Output", "Open generated HTML in your browser?", parent=data_dialog):
                            webbrowser.open(path_obj.resolve().as_uri(), new=2)
                except Exception:
                    pass
                data_dialog.destroy()
            except json.JSONDecodeError as e:
                messagebox.showerror("JSON Error", f"Invalid JSON format:\n{str(e)}")
            except Exception as e:
                messagebox.showerror("Generation Error", f"Failed to generate:\n{str(e)}")

        # Buttons
        button_frame = ttk.Frame(data_dialog)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Generate Output", command=generate).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=data_dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _maybe_stage_output_to_z_direct(self, output: Any) -> None:
        """
        Best-effort staging helper for data-template outputs.

        Only stages when:
        - output is a JSON file path
        - parsed payload is a dict with payload.kind and payload.id
        """
        try:
            from pathlib import Path

            out_path: Optional[Path] = None
            if isinstance(output, Path):
                out_path = output
            elif isinstance(output, str):
                p = Path(output)
                out_path = p if p.exists() else None

            if out_path is None or out_path.suffix.lower() != ".json":
                return

            try:
                payload = json.loads(out_path.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                return

            if not isinstance(payload, dict):
                return

            # Template render helpers often include a "filename" key for output naming;
            # remove it before staging so it doesn't pollute durable registries.
            if "filename" in payload:
                try:
                    payload.pop("filename", None)
                except Exception:
                    pass

            pk = payload.get("kind")
            pid = payload.get("id")
            if not isinstance(pk, str) or not pk.strip():
                return
            if pid is None or (isinstance(pid, str) and not pid.strip()):
                return

            if not messagebox.askyesno(
                "Stage To Z Direct?",
                "Stage this payload to Trinity Z Direct streams (Z+3 objects.jsonl)?\n\n"
                "This does NOT commit to the durable registry; use IT Portal to approve/commit.",
                parent=self.dialog,
            ):
                return

            # Lazy-import core services to keep UI resilient in partial installs.
            try:
                from core.services import get_z_direct  # type: ignore

                z_direct = get_z_direct()
            except Exception as e:
                messagebox.showwarning("Z Direct Unavailable", f"Cannot access Z Direct service:\n{e}", parent=self.dialog)
                return

            tags: List[str] = []
            try:
                meta = getattr(self.current_template, "metadata", None)
                raw_tags = getattr(meta, "tags", None)
                if isinstance(raw_tags, list):
                    tags = [str(t) for t in raw_tags if isinstance(t, (str, int, float)) and str(t).strip()]
            except Exception:
                tags = []
            tags = list(dict.fromkeys((tags or []) + ["template_manager", "staged"]))

            env = z_direct.make_envelope(
                kind="object",
                channel="Z+3",
                payload=payload,
                z_context="Trinity",
                source="Z+3_Trinity.ui.template_manager",
                tags=tags,
            )
            z_direct.append_object("Z+3", env)
            try:
                z_direct.append_event(
                    "Z+3",
                    z_direct.make_envelope(
                        kind="event",
                        channel="Z+3",
                        payload={"type": "template.stage", "payload_kind": pk, "payload_id": str(pid)},
                        z_context="Trinity",
                        source="Z+3_Trinity.ui.template_manager",
                        tags=["template_manager", "stage"],
                    ),
                )
            except Exception:
                pass

            messagebox.showinfo(
                "Staged",
                f"Staged to Z+3 objects.jsonl:\n\nkind={pk}\nid={pid}",
                parent=self.dialog,
            )
        except Exception:
            return

    def _get_example_data(self) -> Dict[str, Any]:
        """Get example data for current template."""
        template_name = type(self.current_template).__name__

        if "QRCode" in template_name:
            return {
                "content": "https://lightspeed-platform.com",
                "filename": "output_qr.png"
            }
        elif "Table" in template_name:
            return {
                "title": "Sample Data Table",
                "headers": ["Name", "Value", "Status"],
                "rows": [
                    ["Item 1", "100", "Active"],
                    ["Item 2", "200", "Pending"],
                    ["Item 3", "300", "Complete"]
                ],
                "filename": "output_table.html"
            }
        elif "Image" in template_name:
            return {
                "image_path": "input_image.png",
                "title": "LightSpeed Platform",
                "filename": "output_image.png"
            }
        elif "AchillesDesktop" in template_name:
            return {
                "base_url": "https://romer.industries",
                "default_route": "/dash",
                "filename": "achilles_desktop.html"
            }
        elif "Theme" in template_name:
            return {
                "theme_name": "Custom Dark",
                "filename": "custom_theme.json"
            }
        elif "KnowledgeNode" in template_name:
            return {
                "concept": "LightSpeed Z Direct",
                "definition": "Append-only staging streams with Trinity as the approval gate for durable registries.",
                "domain": "GENERAL",
                "sources": [{"kind": "vault_file", "id": "3041"}],
                "confidence": 0.8,
                "filename": "knowledge_node_example.json",
            }
        elif "Citation" in template_name:
            return {
                "vault_file_id": "3041",
                "note": "Example citation note.",
                "span": {"start": 0, "end": 120},
                "filename": "citation_example.json",
            }
        elif "Workspace" in template_name:
            return {
                "name": "Cognigrex Research Workspace",
                "domain": "GENERAL",
                "purpose": "Collect vault artifacts -> propose knowledge -> review/commit -> surface in library.",
                "datasets": [],
                "queries": [],
                "outputs": [],
                "filename": "workspace_example.json",
            }
        elif "LearningModule" in template_name:
            return {
                "title": "Getting Started: Z Axis + Z Direct",
                "objectives": ["Understand staging vs durable registry", "Learn commit gate workflow"],
                "steps": ["Ingest a file to Oracle", "Propose knowledge", "Commit to registry", "Search library"],
                "filename": "learning_module_example.json",
            }
        elif "SimulationResult" in template_name:
            return {
                "sim_type": "raphael",
                "status": "complete",
                "params": {"mass": 1.0, "velocity": 2.0},
                "result": {"energy": 0.0},
                "filename": "simulation_result_example.json",
            }
        elif "BentoWidgetDefinition" in template_name:
            return {
                "title": "Oracle Registry",
                "floor": "Z-2_Oracle",
                "widget_type": "BUTTON",
                "config": {
                    "icon": "ZDIR",
                    "description": "Committed objects + schemas (read-only)",
                    "host_action": "open_oracle_registry",
                    "host_action_args": {},
                    "span_cols": 1,
                    "span_rows": 1,
                },
                "enabled": True,
                "filename": "bento_widget_example.json",
            }
        elif "ZDirectSchema" in template_name:
            return {
                "id": "simulation_result",
                "name": "simulation_result",
                "json_schema": {
                    "type": "object",
                    "required": ["kind", "id", "sim_type"],
                    "properties": {
                        "kind": {"type": "string"},
                        "id": {"type": "string"},
                        "sim_type": {"type": "string"},
                        "status": {"type": "string"},
                        "params": {"type": "object"},
                        "result": {"type": "object"},
                        "started_at": {"type": "string"},
                        "completed_at": {"type": "string"},
                        "metadata": {"type": "object"},
                        "provenance": {"type": "object"},
                    },
                },
                "filename": "schema_simulation_result_example.json",
            }
        elif "ActionDefinition" in template_name:
            return {
                "title": "Toggle Bento Panel",
                "description": "Show/hide the Bento menu panel.",
                "category": "Actions / Commands",
                "host_action": "toggle_bento_panel",
                "host_action_args": {},
                "params": [],
                "enabled": True,
                "filename": "action_def_toggle_bento_example.json",
            }
        elif "SimulationDefinition" in template_name:
            return {
                "title": "Raphael Equations",
                "description": "Compute forces/energy using Raphael equations.",
                "sim_type": "raphael",
                "entrypoint": {"host_action": "run_simulation", "args_mode": "kwargs"},
                "params": [
                    {"name": "protons", "type": "int", "required": True, "default": 1, "ui": {"control": "spinbox", "min": 0, "max": 500, "step": 1}},
                    {"name": "neutrons", "type": "int", "required": True, "default": 1, "ui": {"control": "spinbox", "min": 0, "max": 500, "step": 1}},
                    {"name": "electrons", "type": "int", "required": True, "default": 1, "ui": {"control": "spinbox", "min": 0, "max": 500, "step": 1}},
                ],
                "output_kind": "simulation_result",
                "enabled": True,
                "filename": "simulation_def_raphael_example.json",
            }
        elif "WorkflowDefinition" in template_name:
            return {
                "title": "Example Workflow",
                "description": "Multi-step workflow example.",
                "steps": [
                    {"kind": "action", "ref_id": "act_toggle_bento", "params": {}},
                    {"kind": "simulation", "ref_id": "simdef_raphael", "params": {"protons": 1, "neutrons": 1, "electrons": 1}},
                ],
                "enabled": True,
                "filename": "workflow_def_example.json",
            }
        elif "ArchitectureScorecard" in template_name:
            return {
                "title": "LightSpeed Architecture Scorecard (Romer Standard)",
                "system_context": "Local-first modular monolith with approval-gated exchange (Z Direct). Trinity is the only commit gate.",
                "characteristics": [
                    {"name": "Modifiability", "target": "High", "notes": "Z-floor modules evolve independently; templates standardize outputs."},
                    {"name": "Usability", "target": "High", "notes": "Readable overlays + browse-first library surfaces."},
                    {"name": "Security/Governance", "target": "High", "notes": "Stage-only by default; operator approval in Trinity for durable registry writes."},
                    {"name": "Observability", "target": "High", "notes": "Append-only streams + durable registries + IT Portal review trail."},
                ],
                "tradeoffs": [
                    {
                        "decision": "Templates-first pipeline (artifacts) with tests as fitness functions (guardrails)",
                        "benefits": ["faster iteration", "explicit workflows", "operator trust"],
                        "costs": ["more upfront template design", "requires governance discipline"],
                    }
                ],
                "fitness_functions": [
                    "python __main__.py --smoke passes",
                    "Z-3_Smith/tools/verify_integration.py passes",
                    "No durable registry writes without Trinity approval",
                ],
                "adrs": [{"id": "ADR-0001", "summary": "Z Direct governance: stage -> Trinity -> Oracle registry", "status": "accepted"}],
                "filename": "architecture_scorecard_example.md",
            }
        else:
            return {
                "filename": "output.txt"
            }

    def _save_custom_template(self):
        """Save current customizations as custom template."""
        if not self.current_template:
            messagebox.showwarning("No Template", "Please select a template first.")
            return

        # Prompt for name
        name = tk.simpledialog.askstring(
            "Save Custom Template",
            "Enter a name for your custom template:",
            parent=self.dialog
        )

        if not name:
            return

        try:
            # Save to database
            self._ensure_custom_templates_table()

            template_type = type(self.current_template).__name__
            settings_json = json.dumps(self.custom_settings)

            self.db.execute("""
                INSERT INTO custom_templates (name, template_type, settings_json, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (name, template_type, settings_json))

            messagebox.showinfo(
                "Success",
                f"Custom template '{name}' saved successfully!"
            )
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save template:\n{str(e)}")

    def _ensure_custom_templates_table(self):
        """Ensure custom_templates table exists."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS custom_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                template_type TEXT NOT NULL,
                settings_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _generate_output(self):
        """Generate output from current template."""
        self._create_from_template()

    def show(self):
        """Show the dialog."""
        self.dialog.grab_set()
        self.dialog.wait_window()


def show_template_manager(parent: tk.Tk):
    """
    Show Template Manager dialog.

    Args:
        parent: Parent window

    Usage:
        from core.ui.template_manager import show_template_manager
        show_template_manager(root_window)
    """
    dialog = TemplateManagerDialog(parent)
    dialog.show()


if __name__ == "__main__":
    # Test Template Manager UI
    root = tk.Tk()
    root.withdraw()  # Hide root window

    show_template_manager(root)
