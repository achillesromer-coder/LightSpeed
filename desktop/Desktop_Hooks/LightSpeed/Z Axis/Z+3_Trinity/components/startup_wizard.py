"""
Startup Wizard Panel (Trinity, 2D)

Provides quick actions to run setup/refresh scripts:
- list_capabilities.py (tool catalog)
- generate_dataindex.py (index + depmap + catalog)
- process_registry_queue.py (embed/depmap refresh after registry edits)
"""
from __future__ import annotations

import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path


class StartupTasksPanel(ttk.Frame):
    def __init__(self, parent: tk.Widget, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self.root_path = self._find_root(Path(__file__).resolve())
        self._build_ui()

    def _find_root(self, start: Path) -> Path:
        for candidate in (start, *start.parents):
            if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
                return candidate
        return start

    def _build_ui(self) -> None:
        ttk.Label(self, text="Startup Wizard", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=8, pady=(4, 6))

        desc = (
            "Run initial setup and refresh tasks. This panel triggers scripts only; outputs are written to the runtime catalog and tool output folders."
        )
        ttk.Label(self, text=desc, wraplength=720, foreground="#444").pack(anchor="w", padx=8, pady=(0, 8))

        buttons = [
            ("Run list_capabilities (tool catalog)", self._run_list_capabilities),
            ("Run generate_dataindex (index + depmap + catalog)", self._run_generate_dataindex),
            ("Process registry queue (embeds/depmap refresh)", self._run_process_registry_queue),
        ]
        for text, cmd in buttons:
            ttk.Button(self, text=text, command=cmd).pack(anchor="w", padx=8, pady=4)

        self.status_var = tk.StringVar(value="Idle.")
        ttk.Label(self, textvariable=self.status_var, foreground="#006400").pack(anchor="w", padx=8, pady=(6, 4))

    def _run_script(self, rel_path: str) -> None:
        script = self.root_path / rel_path
        if not script.exists():
            messagebox.showinfo("Run script", f"Script not found: {rel_path}")
            return
        try:
            subprocess.run(["python", str(script)], check=True)
            self.status_var.set(f"Completed: {rel_path}")
        except Exception as exc:
            self.status_var.set(f"Error running {rel_path}: {exc}")
            messagebox.showerror("Run script", f"Error running {rel_path}:\n{exc}")

    def _run_list_capabilities(self) -> None:
        self._run_script(Path("Z Axis") / "Z-3_Smith" / "tools" / "list_capabilities.py")

    def _run_generate_dataindex(self) -> None:
        self._run_script(Path("Z Axis") / "Z-3_Smith" / "tools" / "generate_dataindex.py")

    def _run_process_registry_queue(self) -> None:
        self._run_script(Path("Z Axis") / "Z-3_Smith" / "tools" / "process_registry_queue.py")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Startup Wizard")
    panel = StartupTasksPanel(root)
    panel.pack(fill="both", expand=True)
    root.mainloop()


# Back-compat: older Trinity components import `StartupWizard` from this module.
# Keep the alias so we can consolidate UX without breaking imports.
StartupWizard = StartupTasksPanel
