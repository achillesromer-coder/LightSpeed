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
    list_project_files,
)

SCHEMA = "ACHILLES-PROJECT-FILE-SYMLINK-NEGATIVE-AUDIT/0.3"


class SyntheticPipeline:
    def __init__(self, authority_root: Path, project_root: Path):
        self.config = {
            "scan_policy": {"ignored_files": ["internal_note.txt"]},
            "drive_writeback": {
                "blocked_artifact_patterns": [".env", ".env.*", "*.pem", "*.key", "credentials*.json"]
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
        (project / "credentials.json").write_text(marker, encoding="utf-8")
        (project / "safe.txt").write_text("SYNTHETIC_PUBLIC_TEXT", encoding="utf-8")
        (project / "internal_note.txt").write_text(
            "SYNTHETIC_IGNORED_FILE_ONLY", encoding="utf-8"
        )
        outside = base / "outside.txt"
        outside.write_text("SYNTHETIC_OUTSIDE_TEXT", encoding="utf-8")
        (project / "review.txt").symlink_to(project / "credentials.json")
        # Independent hardlink case: lexical and resolved paths both have a
        # benign basename, but the inode is the blocked synthetic fixture.
        (project / "linked_copy.json").hardlink_to(project / "credentials.json")
        hardlink_same_file = (project / "linked_copy.json").samefile(
            project / "credentials.json"
        )
        (project / "outside_alias.txt").symlink_to(outside)
        # Independent T5 case: in-root directory symlink to an ignored tree.
        ignored_dir = project / ".git"
        ignored_dir.mkdir()
        (ignored_dir / "synthetic_note.txt").write_text(
            "SYNTHETIC_INTERNAL_ONLY", encoding="utf-8"
        )
        (project / "docs_alias").symlink_to(ignored_dir, target_is_directory=True)
        pipeline = SyntheticPipeline(authority, project)

        # T5 follow-on: the listing route must apply blocked-file policy to
        # the resolved target, not only to the caller-visible alias name.
        listed = list_project_files(
            pipeline, project_id="fixture-project", limit=20
        )
        listed_names = {
            item["relative_path"] for item in listed["files"]
        }
        alias_listed = "review.txt" in listed_names
        hardlink_listed = "linked_copy.json" in listed_names
        direct_hidden_in_list = "credentials.json" not in listed_names
        external_hidden_in_list = "outside_alias.txt" not in listed_names
        safe_listed = "safe.txt" in listed_names
        ignored_file_hidden_in_list = "internal_note.txt" not in listed_names

        safe = open_project_file(
            pipeline, project_id="fixture-project", relative_path="safe.txt"
        )
        safe_control = safe["preview"]["text"] == "SYNTHETIC_PUBLIC_TEXT"
        direct_blocked = denied(ProjectFileBlocked, pipeline, "credentials.json")
        ignored_direct_blocked = denied(
            ProjectFileBlocked, pipeline, ".git/synthetic_note.txt"
        )
        try:
            ignored_alias = open_project_file(
                pipeline, project_id="fixture-project",
                relative_path="docs_alias/synthetic_note.txt",
            )
        except (ProjectFileBlocked, ProjectFilePathRejected):
            ignored_alias_exposed = False
        else:
            ignored_alias_exposed = (
                ignored_alias["preview"].get("text") == "SYNTHETIC_INTERNAL_ONLY"
            )
        # T5 independent inode-alias case: filename and symlink-target checks
        # alone cannot identify a hardlink to a blocked in-root file.
        try:
            hardlink = open_project_file(
                pipeline, project_id="fixture-project",
                relative_path="linked_copy.json",
            )
        except (ProjectFileBlocked, ProjectFilePathRejected):
            hardlink_exposed = False
        else:
            hardlink_exposed = hardlink["preview"].get("text") == marker
        # T5/T4 policy consistency: direct open must not bypass scan-policy ignored files.
        try:
            ignored_file = open_project_file(
                pipeline, project_id="fixture-project",
                relative_path="internal_note.txt",
            )
        except (ProjectFileBlocked, ProjectFilePathRejected):
            ignored_file_exposed = False
        else:
            ignored_file_exposed = (
                ignored_file["preview"].get("text") == "SYNTHETIC_IGNORED_FILE_ONLY"
            )
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

    controls = (
        safe_control and direct_blocked and ignored_direct_blocked
        and external_blocked and traversal_blocked
        and direct_hidden_in_list and external_hidden_in_list and safe_listed
        and ignored_file_hidden_in_list and hardlink_same_file
    )
    print(json.dumps({
        "schema": SCHEMA,
        "evidence_class": "SOURCE_ONLY_SYNTHETIC_NEGATIVE",
        "candidate_filespace": "Cognigrex.cgx:/LS.cgx/project-file-browser",
        "source_under_review": "desktop/LightSpeed_Runtime/lightspeed_runtime/project_file_browser.py",
        "test_id": "T5-INROOT-HARDLINK-BLOCKED-TARGET",
        "synthetic_blocked_json_via_in_root_symlink": (
            "ALLOW" if alias_exposed else "DENY"
        ),
        "synthetic_blocked_json_metadata_via_list_alias": (
            "ALLOW" if alias_listed else "DENY"
        ),
        "synthetic_blocked_json_via_in_root_hardlink": (
            "ALLOW" if hardlink_exposed else "DENY"
        ),
        "synthetic_blocked_json_metadata_via_list_hardlink": (
            "ALLOW" if hardlink_listed else "DENY"
        ),
        "synthetic_ignored_directory_via_in_root_symlink": (
            "ALLOW" if ignored_alias_exposed else "DENY"
        ),
        "synthetic_ignored_file_via_direct_open": (
            "ALLOW" if ignored_file_exposed else "DENY"
        ),
        "controls": {
            "direct_blocked_name": "DENY" if direct_blocked else "NOT_VERIFIED",
            "hardlink_fixture_same_file": "PASS" if hardlink_same_file else "FAIL",
            "direct_ignored_directory": (
                "DENY" if ignored_direct_blocked else "NOT_VERIFIED"
            ),
            "outside_root_symlink": "DENY" if external_blocked else "NOT_VERIFIED",
            "lexical_parent_traversal": "DENY" if traversal_blocked else "NOT_VERIFIED",
            "ordinary_read_only_preview": "ALLOW" if safe_control else "NOT_VERIFIED",
            "direct_blocked_name_absent_from_listing": (
                "PASS" if direct_hidden_in_list else "FAIL"
            ),
            "outside_root_alias_absent_from_listing": (
                "PASS" if external_hidden_in_list else "FAIL"
            ),
            "ordinary_safe_name_present_in_listing": (
                "PASS" if safe_listed else "FAIL"
            ),
            "configured_ignored_file_absent_from_listing": (
                "PASS" if ignored_file_hidden_in_list else "FAIL"
            ),
        },
        "gate": (
            "HOLD" if alias_exposed or alias_listed or ignored_alias_exposed
            or ignored_file_exposed or hardlink_exposed or hardlink_listed
            else "REQUIRES_INDEPENDENT_ACCEPTANCE"
        ),
        "limits": (
            "Synthetic fixture only. Listing reveals alias metadata, not target bytes. "
            "Ignored-directory symlink case concerns preview bytes only. "
            "Configured ignored-file direct open is synthetic only. "
            "In-root hardlink alias uses the same inode as a synthetic blocked "
            "fixture; it does not demonstrate real secret exfiltration. "
            "No real private data, credential, remote user, "
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
