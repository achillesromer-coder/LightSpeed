from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class WorkspaceContext:
    workspace_id: str
    project_id: str
    active_floor: str
    approvals_pending: int = 0
    selected_assets: list[str] = field(default_factory=list)
    run_ids: list[str] = field(default_factory=list)
    action_ids: list[str] = field(default_factory=list)
    latest_publish_manifest: dict | None = None
    latest_package_metadata: dict | None = None
    status: str = "active"

    def to_dict(self) -> dict:
        return asdict(self)
