#!/usr/bin/env python3
"""ACHILLES T5 independent synthetic project-browser symlink audit.

No real credentials, host paths, native FileSpace or effectful tools.
Zero exit means the negative experiment and denial controls ran, not that
the project browser is secure or approved for private/public release.
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "desktop" / "LightSpeed_Runtime"))

from lightspeed_runtime.project_file_browser import (
    ProjectFileBlocked,
    ProjectFilePathRejected,
    open_project_file,
)

SCHEMA = "ACHILLES-PROJECT-FILE-SYMLINK-NEGATIVE-AUDIT/0.1"


class SyntheticPipeline:
    def __init__(self, authority_root: Path, project_root: Path):
        self.config = {
            "drive_writeback": {
                "blocked_artifact_patterns": [".env", ".env.*", "*.pem", "*.key"]
            }
        }
        self._authority_root = authority_root
        self._project_root = project_root

    def project_roots(self):
        return [SimpleNamespace(root_id="fixture-root", path=self._authority_root)]

    def scan_projects(self):
        return {"projects": [{
            "project_id": "fixture-project",
            "root_id": "fixture-root",
            "path": str(self._project_root),
            "name": "Synthetic Project",
            "authority": "synthetic-local-fixture",
            "condition": "review-only",
        }]}


def denied(exc_type, pipeline, relative_path: str) -> bool:
    try:
        open_project_file(
            pipeline, project_id="fixture-project", relative_path=relative_path
        )
    except exc_type:
        return True
    except Exception:
        return False
    return False


def run() -> int:
    with TemporaryDirectory(prefix="achilles-t5-synthetic-") as tmp:
        base = Path(tmp)
        authority = base / "authority"
        project = authority / "project"
        project.mkdir(parents=True)
        marker = "SYNTHETIC_PRIVATE_SENTINEL_NOT_A_REAL_SECRET"
        (project / ".env").write_text(marker, encoding="utf-8")
        (project / "safe.txt").write_text("SYNTHETIC_PUBLIC_TEXT", encoding="utf-8")
        outside = base / "outside.txt"
        outside.write_text("SYNTHETIC_OUTSIDE_TEXT", encoding="utf-8")
        (project / "review.txt").symlink_to(project / ".env")
        (project / "outside_alias.txt").symlink_to(outside)
        pipeline = SyntheticPipeline(authority, project)

        safe = open_project_file(
            pipeline, project_id="fixture-project", relative_path="safe.txt"
        )
        safe_control = safe["preview"]["text"] == "SYNTHETIC_PUBLIC_TEXT"
        direct_blocked = denied(ProjectFileBlocked, pipeline, ".env")
        external_blocked = denied(
            ProjectFilePathRejected, pipeline, "outside_alias.txt"
        )
        traversal_blocked = denied(
            ProjectFilePathRejected, pipeline, "../outside.txt"
        )
        try:
            alias = open_project_file(
                pipeline, project_id="fixture-project", relative_path="review.txt"
            )
        except (ProjectFileBlocked, ProjectFilePathRejected):
            alias_exposed = False
        else:
            alias_exposed = alias["preview"].get("text") == marker

    controls = safe_control and direct_blocked and external_blocked and traversal_blocked
    print(json.dumps({
        "schema": SCHEMA,
        "evidence_class": "SOURCE_ONLY_SYNTHETIC_NEGATIVE",
        "candidate_filespace": "Cognigrex.cgx:/LS.cgx/project-file-browser",
        "source_under_review": "desktop/LightSpeed_Runtime/lightspeed_runtime/project_file_browser.py",
        "synthetic_blocked_target_via_in_root_symlink": (
            "ALLOW" if alias_exposed else "DENY"
        ),
        "controls": {
            "direct_blocked_name": "DENY" if direct_blocked else "NOT_VERIFIED",
            "outside_root_symlink": "DENY" if external_blocked else "NOT_VERIFIED",
            "lexical_parent_traversal": "DENY" if traversal_blocked else "NOT_VERIFIED",
            "ordinary_read_only_preview": "ALLOW" if safe_control else "NOT_VERIFIED",
        },
        "gate": "HOLD" if alias_exposed else "REQUIRES_INDEPENDENT_ACCEPTANCE",
        "limits": (
            "Synthetic fixture only. No real private data, credential, remote user, "
            "host installation, Windows reparse-point or TOCTOU behavior tested. "
            "Downstream authorization and real release permissions unverified."
        ),
        "controls_verified": controls,
        "native_admitted": False,
        "source_only": True,
    }, sort_keys=True))
    return 0 if controls else 1


if __name__ == "__main__":
    raise SystemExit(run())
