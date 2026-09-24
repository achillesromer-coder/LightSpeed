from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat as stat_module
from typing import Any

from lightspeed_runtime.storage_paths import neo_actions_root


LIST_SCHEMA = "lightspeed-local-results-index-v1"
OPEN_SCHEMA = "lightspeed-local-result-open-v1"
RESULT_SCHEMA = "lightspeed-go-local-result-v1"
MAX_LIST_RESULTS = 200
MAX_SCAN_RESULTS = 1_000
MAX_SCAN_ENTRIES = 5_000
MAX_RECEIPT_BYTES = 256 * 1024
RESULT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,191}$")


class ResultReceiptNotFound(LookupError):
    pass


class ResultReceiptIdRejected(ValueError):
    pass


class ResultReceiptUnavailable(OSError):
    pass


def result_receipts_root(shell_root: Path | str) -> Path:
    return neo_actions_root(Path(shell_root)) / "results"


def _is_reparse_point(path: Path) -> bool:
    try:
        stat_result = path.lstat()
    except OSError:
        return True
    attributes = int(getattr(stat_result, "st_file_attributes", 0) or 0)
    reparse_flag = int(getattr(stat_module, "FILE_ATTRIBUTE_REPARSE_POINT", 0) or 0)
    return path.is_symlink() or bool(reparse_flag and attributes & reparse_flag)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _validated_result_id(value: str) -> str:
    result_id = str(value or "").strip()
    if not RESULT_ID_PATTERN.fullmatch(result_id):
        raise ResultReceiptIdRejected("A bounded result receipt identifier is required")
    return result_id


def _root_for_read(shell_root: Path | str) -> tuple[Path, Path] | None:
    lexical_root = result_receipts_root(shell_root)
    if not lexical_root.exists():
        return None
    if not lexical_root.is_dir() or _is_reparse_point(lexical_root):
        raise ResultReceiptUnavailable("The fixed Neo result receipt root is unavailable")
    try:
        resolved_root = lexical_root.resolve(strict=True)
    except OSError as exc:
        raise ResultReceiptUnavailable("The fixed Neo result receipt root is unavailable") from exc
    if not resolved_root.is_dir():
        raise ResultReceiptUnavailable("The fixed Neo result receipt root is unavailable")
    return lexical_root, resolved_root


def _receipt_record(path: Path, *, resolved_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if path.suffix.casefold() != ".json" or _is_reparse_point(path):
        raise ResultReceiptUnavailable("Result receipt is not an eligible fixed JSON file")
    try:
        resolved_path = path.resolve(strict=True)
        stat_result = resolved_path.stat()
    except OSError as exc:
        raise ResultReceiptUnavailable("Result receipt metadata is unavailable") from exc
    if not _inside(resolved_path, resolved_root) or not resolved_path.is_file():
        raise ResultReceiptUnavailable("Result receipt resolves outside the fixed Neo root")
    if stat_result.st_size > MAX_RECEIPT_BYTES:
        raise ResultReceiptUnavailable("Result receipt exceeds the governed byte limit")
    try:
        content = resolved_path.read_bytes()
    except OSError as exc:
        raise ResultReceiptUnavailable("Result receipt content is unavailable") from exc
    if len(content) > MAX_RECEIPT_BYTES:
        raise ResultReceiptUnavailable("Result receipt exceeds the governed byte limit")
    try:
        payload = json.loads(content.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResultReceiptUnavailable("Result receipt is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != RESULT_SCHEMA:
        raise ResultReceiptUnavailable("Result receipt schema is not eligible for this browser")
    embedded_id = _validated_result_id(str(payload.get("result_id") or ""))
    if embedded_id != path.stem:
        raise ResultReceiptUnavailable("Result receipt identity does not match its fixed filename")
    identity = {
        "result_id": embedded_id,
        "size_bytes": int(stat_result.st_size),
        "modified_utc": datetime.fromtimestamp(stat_result.st_mtime, UTC).isoformat(
            timespec="seconds"
        ),
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    return payload, identity


def _string_or_none(value: Any, maximum: int = 256) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.split()).strip()
    return text[:maximum] or None


def _integer_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError, OverflowError):
        return None


def _boolean_state(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "unknown"


def _metadata(payload: dict[str, Any], identity: dict[str, Any]) -> dict[str, Any]:
    return {
        "result_id": identity["result_id"],
        "command_id": _string_or_none(payload.get("command_id"), maximum=192),
        "task_id": _integer_or_none(payload.get("task_id")),
        "job_id": _integer_or_none(payload.get("job_id")),
        "status": _string_or_none(payload.get("status"), maximum=32) or "unknown",
        "action_type": _string_or_none(payload.get("action_type"), maximum=96),
        "target_floor": _string_or_none(payload.get("target_floor"), maximum=96),
        "created_utc": _string_or_none(payload.get("created_utc"), maximum=64),
        "completed_utc": _string_or_none(payload.get("completed_utc"), maximum=64),
        "public_safe_state": _boolean_state(payload.get("public_safe")),
        "proof_required_state": _boolean_state(payload.get("proof_required")),
        "public_publish_authorized": payload.get("public_publish_authorized") is True,
        "drive_write_executed": payload.get("drive_write_executed") is True,
        "size_bytes": identity["size_bytes"],
        "modified_utc": identity["modified_utc"],
        "sha256": identity["sha256"],
    }


def _sort_key(item: dict[str, Any]) -> tuple[float, str]:
    for field in ("completed_utc", "created_utc", "modified_utc"):
        value = item.get(field)
        if not isinstance(value, str) or not value:
            continue
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.timestamp(), str(item.get("result_id") or "")
        except ValueError:
            continue
    return 0.0, str(item.get("result_id") or "")


def list_result_receipts(
    shell_root: Path | str,
    *,
    limit: int = 50,
) -> dict[str, Any]:
    bounded_limit = max(1, min(int(limit), MAX_LIST_RESULTS))
    root_pair = _root_for_read(shell_root)
    if root_pair is None:
        return {
            "schema_version": LIST_SCHEMA,
            "state": "empty",
            "results": [],
            "summary": {
                "visible_result_count": 0,
                "invalid_file_count": 0,
                "scanned_file_count": 0,
                "limit": bounded_limit,
                "truncated": False,
                "status_counts": {},
            },
            "boundary": (
                "Fixed Neo result receipt metadata only; no filesystem paths, nested payloads, "
                "execution, publication, or source mutation."
            ),
        }

    lexical_root, resolved_root = root_pair
    records: list[dict[str, Any]] = []
    invalid_count = 0
    scanned_count = 0
    scan_truncated = False
    entries: list[Path] = []
    try:
        with os.scandir(lexical_root) as stream:
            for entry_count, entry in enumerate(stream):
                if entry_count >= MAX_SCAN_ENTRIES:
                    scan_truncated = True
                    break
                if not entry.name.casefold().endswith(".json"):
                    continue
                if len(entries) >= MAX_SCAN_RESULTS:
                    scan_truncated = True
                    break
                entries.append(lexical_root / entry.name)
    except OSError as exc:
        raise ResultReceiptUnavailable("Result receipt index is unavailable") from exc
    for path in sorted(entries, key=lambda item: item.name.casefold()):
        scanned_count += 1
        try:
            payload, identity = _receipt_record(path, resolved_root=resolved_root)
        except (ResultReceiptUnavailable, ResultReceiptIdRejected):
            invalid_count += 1
            continue
        records.append(_metadata(payload, identity))

    records.sort(key=_sort_key, reverse=True)
    visible = records[:bounded_limit]
    truncated = scan_truncated or len(records) > bounded_limit
    status_counts: dict[str, int] = {}
    for item in records:
        status = str(item.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "schema_version": LIST_SCHEMA,
        "state": "available" if visible else "restricted" if invalid_count else "empty",
        "results": visible,
        "summary": {
            "visible_result_count": len(visible),
            "invalid_file_count": invalid_count,
            "scanned_file_count": scanned_count,
            "limit": bounded_limit,
            "truncated": truncated,
            "status_counts": status_counts,
        },
        "boundary": (
            "Fixed Neo result receipt metadata only; no filesystem paths, nested payloads, "
            "execution, publication, or source mutation."
        ),
    }


def open_result_receipt(
    shell_root: Path | str,
    *,
    result_id: str,
) -> dict[str, Any]:
    bounded_id = _validated_result_id(result_id)
    root_pair = _root_for_read(shell_root)
    if root_pair is None:
        raise ResultReceiptNotFound("Result receipt not found")
    lexical_root, resolved_root = root_pair
    candidate = lexical_root / f"{bounded_id}.json"
    if not candidate.exists():
        raise ResultReceiptNotFound("Result receipt not found")
    payload, identity = _receipt_record(candidate, resolved_root=resolved_root)
    if identity["result_id"] != bounded_id:
        raise ResultReceiptNotFound("Result receipt not found")
    return {
        "schema_version": OPEN_SCHEMA,
        "state": "opened_read_only",
        "identity": identity,
        "result": payload,
        "source_mutated": False,
        "boundary": (
            "Owner-confirmed unredacted fixed local receipt; the payload may contain local paths "
            "or sensitive context. This read does not execute, edit, upload, or publish it."
        ),
    }
