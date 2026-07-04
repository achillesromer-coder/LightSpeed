"""
Tool Runner Dialog (schema-aware launcher)

- Loads tool_catalog.json to pick tool_key
- Loads input_schema.json to render a type-aware payload form
- Runs runner via subprocess (python runner.py [payload.json]) writing manifest/artifacts to the managed tool output tree.
- UI only orchestrates; does not compute.
"""
from __future__ import annotations

import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Any, Dict, List

from . import state_store


class ToolRunnerDialog(tk.Toplevel):
    def __init__(self, parent: tk.Widget, tools: List[Dict[str, Any]], root: Path) -> None:
        super().__init__(parent)
        self.title("Run Tool")
        self.geometry("520x520")
        self.tools = {t.get("tool_key"): t for t in tools}
        self.root = root
        self.payload_vars: Dict[str, tk.Variable] = {}
        self.required_fields: set[str] = set()
        self.schema: Dict[str, Any] = {}
        self.runner_path: Path | None = None
        self.state = state_store.load_state(self.root)

        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Tool:").pack(anchor="w")
        self.tool_var = tk.StringVar()
        tool_combo = ttk.Combobox(frame, textvariable=self.tool_var, values=list(self.tools.keys()), state="readonly")
        tool_combo.pack(fill="x")
        tool_combo.bind("<<ComboboxSelected>>", self._on_tool_select)
        if self.state.get("last_tool") in self.tools:
            self.tool_var.set(self.state["last_tool"])
            self._on_tool_select()

        self.form_frame = ttk.LabelFrame(frame, text="Payload")
        self.form_frame.pack(fill="both", expand=True, pady=8)

        btns = ttk.Frame(frame)
        btns.pack(fill="x", pady=6)
        ttk.Button(btns, text="Run", command=self._run_tool).pack(side="left")
        ttk.Button(btns, text="Close", command=self.destroy).pack(side="right")

        self.status_var = tk.StringVar(value="Select a tool.")
        ttk.Label(frame, textvariable=self.status_var, foreground="#006400").pack(anchor="w", pady=(4, 0))

    def _on_tool_select(self, _event=None) -> None:
        key = self.tool_var.get()
        tool = self.tools.get(key, {})
        if key:
            self.state["last_tool"] = key
            state_store.save_state(self.root, self.state)
        cap_path = self.root / tool.get("capabilities_path", "")
        schema_path = cap_path.with_name(key.replace("capabilities", "input_schema") + ".json")
        runner_guess = cap_path.with_name(key.replace("_capabilities", "") + ".py")

        self.schema = self._load_json(schema_path)
        self.runner_path = runner_guess if runner_guess.exists() else None
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        self.payload_vars.clear()

        props = self.schema.get("properties", {})
        self.required_fields = set(self.schema.get("required", []))
        row = 0
        for name, meta in props.items():
            label_text = f"{name} ({meta.get('type','')})"
            if name in self.required_fields:
                label_text += " *"
            ttk.Label(self.form_frame, text=label_text).grid(row=row, column=0, sticky="w", padx=4, pady=2)

            field_type = meta.get("type")
            if field_type == "boolean":
                var = tk.BooleanVar()
                widget = ttk.Checkbutton(self.form_frame, variable=var)
            elif field_type == "number" or field_type == "integer":
                var = tk.StringVar()
                widget = ttk.Entry(self.form_frame, textvariable=var)
                widget.insert(0, meta.get("default", ""))
            elif field_type == "array":
                var = tk.StringVar()
                widget = ttk.Entry(self.form_frame, textvariable=var)
                widget.insert(0, "[]")
            else:  # string or fallback
                var = tk.StringVar()
                widget = ttk.Entry(self.form_frame, textvariable=var)
                widget.insert(0, meta.get("default", ""))

            widget.grid(row=row, column=1, sticky="ew", padx=4, pady=2)
            self.form_frame.columnconfigure(1, weight=1)
            self.payload_vars[name] = var
            row += 1
        if not props:
            ttk.Label(self.form_frame, text="No schema fields").pack(anchor="w", padx=4, pady=4)

        self.status_var.set(f"Tool {key} ready. Runner: {self.runner_path or 'not found'}")

    def _collect_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        for name, var in self.payload_vars.items():
            if isinstance(var, tk.BooleanVar):
                payload[name] = bool(var.get())
                continue
            text = var.get().strip()
            if not text:
                continue
            try:
                payload[name] = json.loads(text)
            except Exception:
                payload[name] = text
        return payload

    def _run_tool(self) -> None:
        key = self.tool_var.get()
        if not key:
            messagebox.showinfo("Run tool", "Select a tool.")
            return
        if not self.runner_path or not self.runner_path.exists():
            messagebox.showinfo("Run tool", f"Runner not found for {key}.")
            return
        payload = self._collect_payload()
        missing = [f for f in self.required_fields if f not in payload or payload.get(f) in ("", None, [])]
        if missing:
            messagebox.showinfo("Run tool", f"Required fields missing: {', '.join(missing)}")
            return
        payload_path = self.root / "dataindex" / f"payload_{key}.json"
        payload_path.parent.mkdir(parents=True, exist_ok=True)
        payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        try:
            result = subprocess.run(
                ["python", str(self.runner_path), str(payload_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.status_var.set(f"Ran {key}; payload at {payload_path}. Check the tool output folder for the manifest.")
            if result.stdout:
                self._show_output_window(result.stdout.strip())
        except Exception as exc:
            self.status_var.set(f"Error running {key}: {exc}")
            messagebox.showerror("Run tool", f"Error running {key}:\n{exc}")

    def _show_output_window(self, text: str) -> None:
        if not text:
            return
        win = tk.Toplevel(self)
        win.title("Runner output")
        txt = tk.Text(win, wrap="word", width=80, height=20)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", text)
        txt.config(state="disabled")

    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
