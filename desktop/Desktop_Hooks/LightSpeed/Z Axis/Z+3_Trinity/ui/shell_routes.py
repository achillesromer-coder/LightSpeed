from __future__ import annotations

from typing import Callable


SHELL_MODES = (
    "workspace",
    "operator",
    "review",
    "publish",
    "settings",
    "holospace",
)
SHELL_FLOORS = (
    "Trinity",
    "Neo",
    "Architect",
    "The Construct",
    "Morpheus",
    "Oracle",
    "Smith",
    "Merovingian",
)
FLOOR_CHANNELS = {
    "Z+3": "Trinity",
    "Z+2": "Neo",
    "Z+1": "Architect",
    "Z0": "The Construct",
    "Z-1": "Morpheus",
    "Z-2": "Oracle",
    "Z-3": "Smith",
    "Z-4": "Merovingian",
}
MODE_CLEARANCE = {
    "workspace": 0,
    "operator": 4,
    "review": 3,
    "publish": 5,
    "settings": 0,
    "holospace": 4,
}


def normalize_floor(value: str) -> str:
    text = str(value or "").strip()
    if text in FLOOR_CHANNELS:
        return FLOOR_CHANNELS[text]
    folded = text.casefold().replace("_", " ").replace("-", " ")
    for floor in SHELL_FLOORS:
        if folded == floor.casefold():
            return floor
        if folded == floor.casefold().replace(" ", ""):
            return floor
    if folded in {"theconstruct", "construct"}:
        return "The Construct"
    raise ValueError(f"unknown floor: {value}")


class ShellRoute:
    __slots__ = ("mode", "active_floor", "workspace_context")

    def __init__(
        self,
        *,
        mode: str,
        active_floor: str,
        workspace_context: str,
    ) -> None:
        self.mode = mode
        self.active_floor = active_floor
        self.workspace_context = workspace_context

    def snapshot(self) -> dict[str, str]:
        return {
            "mode": self.mode,
            "active_floor": self.active_floor,
            "workspace_context": self.workspace_context,
        }


class ShellRouter:
    def __init__(self, *, clearance: int = 0) -> None:
        self.clearance = max(0, int(clearance))

    def default_route(self) -> ShellRoute:
        return ShellRoute(
            mode="workspace",
            active_floor="Trinity",
            workspace_context="",
        )

    def resolve(
        self,
        mode: str,
        *,
        active_floor: str = "Trinity",
        workspace_context: str = "",
    ) -> ShellRoute:
        normalized_mode = str(mode or "").strip().lower()
        if normalized_mode not in SHELL_MODES:
            raise ValueError(f"unknown shell mode: {mode}")
        required = MODE_CLEARANCE[normalized_mode]
        if self.clearance < required:
            raise PermissionError(
                f"{normalized_mode} requires clearance {required}"
            )
        return ShellRoute(
            mode=normalized_mode,
            active_floor=normalize_floor(active_floor),
            workspace_context=str(workspace_context or "").strip(),
        )


class ShellState:
    def __init__(
        self,
        *,
        mode: str = "workspace",
        active_floor: str = "Trinity",
        workspace_context: str = "",
    ) -> None:
        self.mode = ""
        self.active_floor = ""
        self.workspace_context = ""
        self._listeners: list[Callable[[dict[str, str]], None]] = []
        self.transition(
            mode=mode,
            active_floor=active_floor,
            workspace_context=workspace_context,
        )

    def subscribe(self, listener: Callable[[dict[str, str]], None]) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def transition(
        self,
        *,
        mode: str,
        active_floor: str,
        workspace_context: str,
    ) -> None:
        normalized_mode = str(mode or "").strip().lower()
        if normalized_mode not in SHELL_MODES:
            raise ValueError(f"unknown shell mode: {mode}")
        self.mode = normalized_mode
        self.active_floor = normalize_floor(active_floor)
        self.workspace_context = str(workspace_context or "").strip()
        snapshot = self.snapshot()
        for listener in tuple(self._listeners):
            listener(snapshot)

    def snapshot(self) -> dict[str, str]:
        return {
            "mode": self.mode,
            "active_floor": self.active_floor,
            "workspace_context": self.workspace_context,
        }
