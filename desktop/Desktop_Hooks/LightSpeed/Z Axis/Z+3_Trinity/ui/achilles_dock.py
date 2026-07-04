from __future__ import annotations

import json
import os
import threading
import tkinter as tk
from tkinter import scrolledtext
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class LocalOllamaClient:
    def __init__(self, endpoint: str | None = None, model: str | None = None) -> None:
        self.endpoint = (
            endpoint
            or os.environ.get("OLLAMA_HOST")
            or "http://127.0.0.1:11434"
        ).rstrip("/")
        self.model = model or os.environ.get("LIGHTSPEED_OLLAMA_MODEL") or ""
        parsed = urlparse(self.endpoint)
        if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Achilles dock accepts local Ollama endpoints only")

    def _request(
        self,
        path: str,
        *,
        payload: dict | None = None,
        timeout: float = 8,
    ) -> dict:
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(
            f"{self.endpoint}{path}",
            data=data,
            headers=headers,
            method="POST" if data is not None else "GET",
        )
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def models(self) -> list[str]:
        payload = self._request("/api/tags", timeout=3)
        return [
            str(item.get("name"))
            for item in payload.get("models", [])
            if item.get("name")
        ]

    def chat(self, messages: list[dict[str, str]]) -> tuple[str, str]:
        model = self.model
        if not model:
            available = self.models()
            if not available:
                raise RuntimeError("Ollama is available but has no local models")
            model = available[0]
            self.model = model
        payload = self._request(
            "/api/chat",
            payload={
                "model": model,
                "messages": messages[-12:],
                "stream": False,
                "keep_alive": "5m",
                "options": {
                    "num_ctx": 4096,
                    "temperature": 0.2,
                },
            },
            timeout=120,
        )
        message = payload.get("message") or {}
        return str(message.get("content") or "").strip(), model


class AchillesDock(tk.Frame):
    """Persistent local-AI dock shared by every shell mode."""

    def __init__(
        self,
        parent,
        *,
        colors: dict | None = None,
        context_provider=None,
    ) -> None:
        palette = colors or {}
        self._bg = palette.get("bg_dark", "#031A2D")
        self._panel = palette.get("bg_panel", "#082B4B")
        self._text = palette.get("text_white", "#F7F3E8")
        self._accent = palette.get("accent_cyan", "#30D5C8")
        self._error = palette.get("error_red", "#D66A6A")
        super().__init__(parent, bg=self._panel, width=340)
        self.pack_propagate(False)
        self._context_provider = context_provider
        self._messages: list[dict[str, str]] = []
        self._busy = False
        try:
            self._client = LocalOllamaClient()
        except ValueError:
            self._client = LocalOllamaClient("http://127.0.0.1:11434")

        header = tk.Frame(self, bg=self._panel)
        header.pack(fill="x", padx=12, pady=(12, 6))
        tk.Label(
            header,
            text="ACHILLES",
            bg=self._panel,
            fg=self._accent,
            font=("Garamond", 14, "bold"),
        ).pack(side="left")
        self.status = tk.Label(
            header,
            text="checking local AI",
            bg=self._panel,
            fg=self._text,
            font=("Garamond", 9),
        )
        self.status.pack(side="right")

        self.context_label = tk.Label(
            self,
            text="Trinity / workspace",
            anchor="w",
            bg=self._panel,
            fg=self._text,
            font=("Garamond", 9),
        )
        self.context_label.pack(fill="x", padx=12, pady=(0, 6))

        self.transcript = scrolledtext.ScrolledText(
            self,
            wrap="word",
            bg=self._bg,
            fg=self._text,
            insertbackground=self._accent,
            relief="flat",
            font=("Garamond", 10),
            state="disabled",
        )
        self.transcript.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        composer = tk.Frame(self, bg=self._panel)
        composer.pack(fill="x", padx=12, pady=(0, 12))
        self.entry = tk.Entry(
            composer,
            bg=self._bg,
            fg=self._text,
            insertbackground=self._accent,
            relief="flat",
            font=("Garamond", 10),
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=7)
        self.entry.bind("<Return>", lambda _event: self.submit())
        self.send = tk.Button(
            composer,
            text="SEND",
            command=self.submit,
            bg=self._accent,
            fg=self._bg,
            activebackground=self._text,
            relief="flat",
            font=("Garamond", 9, "bold"),
            padx=10,
        )
        self.send.pack(side="left", padx=(8, 0), ipady=5)
        self.after(50, self._check_health)

    def _append(self, speaker: str, message: str) -> None:
        self.transcript.configure(state="normal")
        self.transcript.insert("end", f"{speaker}\n", ("speaker",))
        self.transcript.insert("end", f"{message.strip()}\n\n")
        self.transcript.tag_configure(
            "speaker",
            foreground=self._accent,
            font=("Garamond", 10, "bold"),
        )
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def _check_health(self) -> None:
        def worker() -> None:
            try:
                models = self._client.models()
                label = f"local / {len(models)} model{'s' if len(models) != 1 else ''}"
                color = self._accent
            except (OSError, ValueError, URLError, RuntimeError):
                label = "local AI offline"
                color = self._error
            self.after(0, lambda: self.status.configure(text=label, fg=color))

        threading.Thread(target=worker, daemon=True).start()

    def update_context(self, snapshot: dict[str, str]) -> None:
        floor = snapshot.get("active_floor") or "Trinity"
        mode = snapshot.get("mode") or "workspace"
        workspace = snapshot.get("workspace_context") or "general"
        self.context_label.configure(text=f"{floor} / {mode} / {workspace}")

    def focus_input(self) -> None:
        self.entry.focus_set()

    def submit(self) -> None:
        if self._busy:
            return
        prompt = self.entry.get().strip()
        if not prompt:
            return
        self.entry.delete(0, "end")
        snapshot = (
            self._context_provider()
            if callable(self._context_provider)
            else {}
        )
        system = (
            "You are Achilles, local oversight for LightSpeed Desktop. "
            "Remain concise, evidence-aware, local-first, and gated. "
            f"Current shell context: {json.dumps(snapshot, sort_keys=True)}"
        )
        self._messages = [
            message
            for message in self._messages
            if message.get("role") != "system"
        ]
        self._messages.insert(0, {"role": "system", "content": system})
        self._messages.append({"role": "user", "content": prompt})
        self._append("YOU", prompt)
        self._busy = True
        self.send.configure(state="disabled")
        self.status.configure(text="thinking", fg=self._accent)

        def worker() -> None:
            try:
                response, model = self._client.chat(self._messages)
                if not response:
                    response = "No response returned by the local model."
                self._messages.append({"role": "assistant", "content": response})
                self.after(0, lambda: self._complete(response, f"local / {model}"))
            except Exception as exc:
                message = f"Local Ollama unavailable: {exc}"
                self.after(0, lambda: self._complete(message, "local AI offline", error=True))

        threading.Thread(target=worker, daemon=True).start()

    def _complete(self, response: str, status: str, *, error: bool = False) -> None:
        self._busy = False
        self.send.configure(state="normal")
        self.status.configure(text=status, fg=self._error if error else self._accent)
        self._append("ACHILLES", response)
