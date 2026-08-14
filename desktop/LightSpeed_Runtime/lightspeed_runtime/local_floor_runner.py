from __future__ import annotations

import argparse
from contextlib import AbstractContextManager
import ctypes
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_CONTRACT_PATH = Path(__file__).resolve().parents[1] / "exports" / "agent_home" / "local_agent_wakeup_contract.json"
DEFAULT_TIMEOUT_SECONDS = 90
DEFAULT_NUM_PREDICT = 512
MAX_NUM_PREDICT = 1024
HEAVY_MODEL_PATTERN = re.compile(r"(?:(?:27|70|120|405|671)b)|cloud", re.IGNORECASE)
DEFAULT_WARNING_FREE_MEMORY_PERCENT = 15.0
DEFAULT_CRITICAL_FREE_MEMORY_PERCENT = 8.0
DEFAULT_MINIMUM_FREE_MEMORY_BYTES = 4 * 1024**3
LAST_RECEIPT_TAIL_BYTES = 64 * 1024

HttpPost = Callable[[str, dict[str, Any], float], dict[str, Any]]
OllamaStatusProbe = Callable[[str, float], dict[str, Any]]
MemorySnapshot = Callable[[], tuple[int, int]]


class LocalFloorRunnerError(RuntimeError):
    """Raised when a local floor run cannot proceed safely."""


@dataclass(frozen=True)
class FloorRunSelection:
    contract: dict[str, Any]
    floor: dict[str, Any]


class SingleSessionLock(AbstractContextManager["SingleSessionLock"]):
    """Small process lock to avoid overlapping local model sessions."""

    def __init__(self, path: Path, *, enabled: bool = True) -> None:
        self.path = path
        self.enabled = enabled
        self._fd: int | None = None

    def __enter__(self) -> "SingleSessionLock":
        if not self.enabled:
            return self
        self.path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            self._fd = os.open(str(self.path), flags)
        except FileExistsError as exc:
            raise LocalFloorRunnerError(f"another local floor runner session is active: {self.path}") from exc
        payload = {"pid": os.getpid(), "created_at": _utc_now_iso()}
        os.write(self._fd, json.dumps(payload, sort_keys=True).encode("utf-8"))
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> bool:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        if self.enabled:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
        return False


def load_contract(path: Path = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
    try:
        contract = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LocalFloorRunnerError(f"contract not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LocalFloorRunnerError(f"contract is not valid JSON: {path}") from exc
    if not isinstance(contract, dict) or not isinstance(contract.get("floors"), list):
        raise LocalFloorRunnerError(f"contract does not contain a floors list: {path}")
    return contract


def select_floor(contract: dict[str, Any], *, floor: str | None = None, order: int | None = None) -> FloorRunSelection:
    if bool(floor) == bool(order is not None):
        raise LocalFloorRunnerError("select exactly one floor by --floor or --order")

    floors = contract.get("floors") or []
    selected: dict[str, Any] | None = None
    if floor:
        floor_key = floor.casefold()
        selected = next((item for item in floors if str(item.get("floor", "")).casefold() == floor_key), None)
    else:
        selected = next((item for item in floors if item.get("order") == order), None)

    if selected is None:
        available = ", ".join(str(item.get("floor")) for item in floors)
        raise LocalFloorRunnerError(f"floor selection not found; available floors: {available}")
    return FloorRunSelection(contract=contract, floor=selected)


def run_floor(
    *,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
    floor: str | None = None,
    order: int | None = None,
    dry_run: bool = True,
    allow_heavy: bool = False,
    receipt_target: str = "neo",
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    num_predict: int | None = None,
    http_post: HttpPost | None = None,
    ollama_status_probe: OllamaStatusProbe | None = None,
    memory_snapshot: MemorySnapshot | None = None,
    lock: bool = True,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    selection = select_floor(contract, floor=floor, order=order)
    floor_row = selection.floor
    conn = floor_row.get("ollama_connection") or {}
    endpoint = str(conn.get("endpoint") or (contract.get("ollama") or {}).get("endpoint") or "http://localhost:11434")
    model = str(conn.get("model") or "")
    request_body = build_ollama_request(contract, floor_row, num_predict=num_predict)
    receipt_path = resolve_receipt_path(contract, floor_row, receipt_target=receipt_target)
    lock_path = resolve_lock_path(contract)

    blocked_reason = _blocked_heavy_reason(floor_row, model, allow_heavy=allow_heavy)
    resource_status = build_resource_preflight(
        contract,
        endpoint=endpoint,
        probe_ollama=not dry_run and not bool(blocked_reason),
        timeout_seconds=min(max(float(timeout_seconds), 0.1), 5.0),
        ollama_status_probe=ollama_status_probe,
        memory_snapshot=memory_snapshot,
    )
    if not blocked_reason and not dry_run and resource_status["execution_state"] == "stop":
        blocked_reason = "resource stop threshold reached: " + "; ".join(resource_status["stop_reasons"])
    if blocked_reason:
        receipt = build_receipt(
            contract,
            floor_row,
            dry_run=dry_run,
            status="blocked",
            receipt_path=receipt_path,
            contract_path=contract_path,
            request_body=request_body,
            blocked_reason=blocked_reason,
            resource_status=resource_status,
        )
        write_receipt(contract, receipt_path, receipt)
        return receipt

    if dry_run:
        receipt = build_receipt(
            contract,
            floor_row,
            dry_run=True,
            status="dry_run",
            receipt_path=receipt_path,
            contract_path=contract_path,
            request_body=request_body,
            resource_status=resource_status,
        )
        write_receipt(contract, receipt_path, receipt)
        return receipt

    post = http_post or post_ollama_generate
    started = time.monotonic()
    with SingleSessionLock(lock_path, enabled=lock):
        try:
            response = post(f"{endpoint.rstrip('/')}/api/generate", request_body, timeout_seconds)
            status = "completed"
            error = None
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, LocalFloorRunnerError) as exc:
            response = {}
            status = "failed"
            error = str(exc)
    elapsed_ms = int((time.monotonic() - started) * 1000)

    receipt = build_receipt(
        contract,
        floor_row,
        dry_run=False,
        status=status,
        receipt_path=receipt_path,
        contract_path=contract_path,
        request_body=request_body,
        response=response,
        error=error,
        elapsed_ms=elapsed_ms,
        resource_status=resource_status,
    )
    write_receipt(contract, receipt_path, receipt)
    return receipt


def build_ollama_request(
    contract: dict[str, Any],
    floor: dict[str, Any],
    *,
    num_predict: int | None = None,
) -> dict[str, Any]:
    conn = floor.get("ollama_connection") or {}
    policy = contract.get("policy") or {}
    overrides = dict(policy.get("receipt_prompt_overrides") or {})

    bounded_num_predict = int(num_predict if num_predict is not None else overrides.get("num_predict", DEFAULT_NUM_PREDICT))
    bounded_num_predict = max(1, min(bounded_num_predict, MAX_NUM_PREDICT))

    return {
        "model": str(conn.get("model") or ""),
        "prompt": build_floor_prompt(contract, floor),
        "stream": False,
        "think": False,
        "keep_alive": 0,
        "options": {"num_predict": bounded_num_predict},
    }


def build_floor_prompt(contract: dict[str, Any], floor: dict[str, Any]) -> str:
    training = floor.get("training_context") or {}
    draw = floor.get("assimilation_draw") or {}
    receipt_route = resolve_receipt_path(contract, floor, receipt_target="neo")
    priority_paths = draw.get("priority_paths") or []
    path_lines = [f"- {item.get('relative_path', item.get('name', 'unknown'))}" for item in priority_paths[:12]]
    if not path_lines:
        path_lines = ["- No priority paths matched in the bounded contract scan."]

    do_not_do = "\n".join(f"- {item}" for item in training.get("do_not_do") or [])
    sequence = "\n".join(f"- {item}" for item in training.get("learning_sequence") or [])
    return "\n".join(
        [
            f"You are the {floor.get('floor')} smart floor agent for LightSpeed.",
            "Run one bounded local wake-up receipt only. Do not recurse, promote, publish, or write source files.",
            f"Contract: {contract.get('contract_id')}",
            f"Floor order: {floor.get('order')}",
            f"Activation mode: {(floor.get('activation') or {}).get('mode')}",
            f"Wake goal: {training.get('wake_goal', 'unknown')}",
            f"Assimilation role: {training.get('assimilation_role', 'unknown')}",
            f"Approved receipt route: {receipt_route}",
            "Use that route verbatim for safe_artifact_route. Do not invent or suggest an alternate path.",
            "Learning sequence:",
            sequence or "- Return a concise floor summary, one safe artifact route, and one blocker if present.",
            "Priority source paths:",
            "\n".join(path_lines),
            "Do not do:",
            do_not_do or "- Do not run heavy/manual models or parallel sessions without approval.",
            "Keep the entire response under 90 words. Do not use Markdown fences.",
            "Return JSON-compatible text with keys: floor_summary, safe_artifact_route, blocker.",
        ]
    )


def resolve_receipt_path(contract: dict[str, Any], floor: dict[str, Any], *, receipt_target: str = "neo") -> Path:
    safe_floor = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(floor.get("floor") or "floor")).strip("_")
    filename = f"local_floor_runner_receipt_{safe_floor}_latest.json"

    if receipt_target == "floor":
        return Path(str(floor["floor_root"])) / "data" / "wakeup" / filename
    if receipt_target == "neo":
        shell_root = resolve_contract_shell_root(contract)
        return shell_root / "Z Axis" / "Z+2_Neo" / "data" / "temp_shells" / "outputs" / filename
    raise LocalFloorRunnerError("receipt_target must be 'neo' or 'floor'")


def resolve_contract_shell_root(contract: dict[str, Any]) -> Path:
    """Prefer the canonical operator-shell path over a stale exported route."""
    requested = Path(str(contract["shell_root"]))
    root = Path(str(contract.get("root") or DEFAULT_CONTRACT_PATH.parents[2]))
    agent_home_path = root / "config" / "agent_home.json"
    try:
        agent_home = json.loads(agent_home_path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return requested
    if not isinstance(agent_home, dict):
        return requested
    environment = agent_home.get("environment") if isinstance(agent_home.get("environment"), dict) else {}
    configured = str(environment.get("desktop_shell_root") or "").strip()
    return Path(configured) if configured else requested


def resolve_lock_path(contract: dict[str, Any]) -> Path:
    root = Path(str(contract.get("root") or DEFAULT_CONTRACT_PATH.parents[2]))
    return root / "reports" / "local_floor_runner.active.lock"


def build_receipt(
    contract: dict[str, Any],
    floor: dict[str, Any],
    *,
    dry_run: bool,
    status: str,
    receipt_path: Path,
    contract_path: Path,
    request_body: dict[str, Any],
    response: dict[str, Any] | None = None,
    error: str | None = None,
    blocked_reason: str | None = None,
    elapsed_ms: int | None = None,
    resource_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prompt = str(request_body.get("prompt") or "")
    safe_floor = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(floor.get("floor") or "floor")).strip("_")
    receipt: dict[str, Any] = {
        "receipt_id": f"local_floor_runner_receipt_{safe_floor}_{_receipt_timestamp()}",
        "created_at": _utc_now_iso(),
        "status": status,
        "dry_run": dry_run,
        "contract_id": contract.get("contract_id"),
        "contract_path": str(contract_path),
        "floor": floor.get("floor"),
        "order": floor.get("order"),
        "activation_mode": (floor.get("activation") or {}).get("mode"),
        "model": request_body.get("model"),
        "endpoint": (floor.get("ollama_connection") or {}).get("endpoint") or (contract.get("ollama") or {}).get("endpoint"),
        "receipt_path": str(receipt_path),
        "session_policy": "one_floor_prompt_at_a_time",
        "manual_heavy_allowed": not bool(blocked_reason) and _is_heavy_or_manual(floor, str(request_body.get("model") or "")),
        "request_overrides": {
            "stream": request_body.get("stream"),
            "think": request_body.get("think"),
            "num_predict": (request_body.get("options") or {}).get("num_predict"),
        },
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prompt_preview": prompt[:600],
        "resource_preflight": resource_status or {},
    }
    if blocked_reason:
        receipt["blocked_reason"] = blocked_reason
    if response is not None:
        receipt["response"] = _summarize_response(response)
        response_text = response.get("response")
        if isinstance(response_text, str) and response_text.strip():
            receipt["response_contract"] = normalize_floor_response(
                response_text,
                expected_route=str(receipt_path),
            )
    if error:
        receipt["error"] = error
    if elapsed_ms is not None:
        receipt["elapsed_ms"] = elapsed_ms
    return receipt


def post_ollama_generate(url: str, payload: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout_seconds) as response:
        response_body = response.read().decode("utf-8")
    decoded = json.loads(response_body) if response_body.strip() else {}
    if not isinstance(decoded, dict):
        raise LocalFloorRunnerError("Ollama response was not a JSON object")
    return decoded


def probe_ollama_processes(endpoint: str, timeout_seconds: float) -> dict[str, Any]:
    """Return a compact read-only view of models currently loaded by local Ollama."""
    request = Request(f"{endpoint.rstrip('/')}/api/ps", method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            response_body = response.read().decode("utf-8")
        decoded = json.loads(response_body) if response_body.strip() else {}
        if not isinstance(decoded, dict):
            raise LocalFloorRunnerError("Ollama process response was not a JSON object")
        models = decoded.get("models") if isinstance(decoded.get("models"), list) else []
        loaded = []
        for row in models[:16]:
            if not isinstance(row, dict):
                continue
            loaded.append(
                {
                    "name": row.get("name") or row.get("model"),
                    "size_bytes": row.get("size"),
                    "size_vram_bytes": row.get("size_vram"),
                    "expires_at": row.get("expires_at"),
                }
            )
        return {
            "state": "available",
            "loaded_model_count": len(models),
            "loaded_models": loaded,
            "truncated": len(models) > len(loaded),
        }
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError, LocalFloorRunnerError) as exc:
        return {
            "state": "unavailable",
            "loaded_model_count": None,
            "loaded_models": [],
            "error": str(exc),
        }


def build_resource_preflight(
    contract: dict[str, Any],
    *,
    endpoint: str,
    probe_ollama: bool,
    timeout_seconds: float = 2.0,
    ollama_status_probe: OllamaStatusProbe | None = None,
    memory_snapshot: MemorySnapshot | None = None,
) -> dict[str, Any]:
    """Build the bounded, read-only resource signal recorded before each floor run."""
    policy = contract.get("policy") if isinstance(contract.get("policy"), dict) else {}
    guard = policy.get("resource_guard") if isinstance(policy.get("resource_guard"), dict) else {}
    warning_percent = _float_setting(
        guard,
        "warning_free_memory_percent",
        DEFAULT_WARNING_FREE_MEMORY_PERCENT,
    )
    critical_percent = _float_setting(
        guard,
        "critical_free_memory_percent",
        DEFAULT_CRITICAL_FREE_MEMORY_PERCENT,
    )
    minimum_free_bytes = _int_setting(
        guard,
        "minimum_free_memory_bytes",
        DEFAULT_MINIMUM_FREE_MEMORY_BYTES,
    )

    snapshot = memory_snapshot or _memory_snapshot
    memory: dict[str, Any]
    stop_reasons: list[str] = []
    try:
        total_bytes, free_bytes = snapshot()
        if total_bytes <= 0 or free_bytes < 0:
            raise ValueError("memory snapshot returned invalid byte counts")
        free_percent = round((free_bytes / total_bytes) * 100, 2)
        memory_state = "ready"
        if free_percent <= critical_percent or free_bytes < minimum_free_bytes:
            memory_state = "stop"
        elif free_percent <= warning_percent:
            memory_state = "warning"
        if free_percent <= critical_percent:
            stop_reasons.append(f"free memory {free_percent}% is at or below {critical_percent}%")
        if free_bytes < minimum_free_bytes:
            stop_reasons.append(f"free memory {free_bytes} bytes is below {minimum_free_bytes} bytes")
        memory = {
            "state": memory_state,
            "total_bytes": total_bytes,
            "free_bytes": free_bytes,
            "free_percent": free_percent,
        }
    except (OSError, ValueError, TypeError) as exc:
        memory = {
            "state": "unavailable",
            "total_bytes": None,
            "free_bytes": None,
            "free_percent": None,
            "error": str(exc),
        }

    endpoint_host = (urlparse(endpoint).hostname or "").casefold()
    local_endpoint = endpoint_host in {"localhost", "127.0.0.1", "::1"}
    if stop_reasons:
        ollama = {
            "state": "not_probed",
            "loaded_model_count": None,
            "loaded_models": [],
            "reason": "resource_stop",
        }
    elif probe_ollama and not local_endpoint:
        ollama = {
            "state": "not_probed",
            "loaded_model_count": None,
            "loaded_models": [],
            "reason": "nonlocal_endpoint_blocked",
        }
    elif probe_ollama:
        probe = ollama_status_probe or probe_ollama_processes
        try:
            ollama = probe(endpoint, timeout_seconds)
        except Exception as exc:  # A telemetry probe must never crash or bypass the run gate.
            ollama = {
                "state": "unavailable",
                "loaded_model_count": None,
                "loaded_models": [],
                "error": str(exc),
            }
    else:
        ollama = {
            "state": "not_probed",
            "loaded_model_count": None,
            "loaded_models": [],
            "reason": "dry_run_or_preexisting_gate",
        }

    return {
        "observed_at": _utc_now_iso(),
        "execution_state": "stop" if stop_reasons else "ready_with_warning" if memory["state"] in {"warning", "unavailable"} else "ready",
        "stop_reasons": stop_reasons,
        "thresholds": {
            "warning_free_memory_percent": warning_percent,
            "critical_free_memory_percent": critical_percent,
            "minimum_free_memory_bytes": minimum_free_bytes,
        },
        "memory": memory,
        "ollama": ollama,
        "last_receipt": _last_receipt_summary(contract),
    }


def _memory_snapshot() -> tuple[int, int]:
    if os.name == "nt":
        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            raise OSError("GlobalMemoryStatusEx failed")
        return int(status.ullTotalPhys), int(status.ullAvailPhys)

    page_size = int(os.sysconf("SC_PAGE_SIZE"))
    return page_size * int(os.sysconf("SC_PHYS_PAGES")), page_size * int(os.sysconf("SC_AVPHYS_PAGES"))


def _last_receipt_summary(contract: dict[str, Any]) -> dict[str, Any] | None:
    root = Path(str(contract.get("root") or DEFAULT_CONTRACT_PATH.parents[2]))
    ledger_root = root / "logs" / "receipts"
    ledgers = sorted(ledger_root.glob("local_floor_runner_*.jsonl"), reverse=True)
    for ledger_path in ledgers[:4]:
        raw = _read_bounded_last_line(ledger_path)
        if not raw:
            continue
        try:
            receipt = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(receipt, dict):
            continue
        return {
            "receipt_id": receipt.get("receipt_id"),
            "created_at": receipt.get("created_at"),
            "floor": receipt.get("floor"),
            "status": receipt.get("status"),
            "ledger_path": str(ledger_path),
        }
    return None


def _read_bounded_last_line(path: Path) -> str:
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - LAST_RECEIPT_TAIL_BYTES))
            tail = handle.read(LAST_RECEIPT_TAIL_BYTES).decode("utf-8", errors="replace")
    except OSError:
        return ""
    lines = [line.strip() for line in tail.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def _float_setting(settings: dict[str, Any], key: str, default: float) -> float:
    try:
        return float(settings.get(key, default))
    except (TypeError, ValueError):
        return default


def _int_setting(settings: dict[str, Any], key: str, default: int) -> int:
    try:
        return int(settings.get(key, default))
    except (TypeError, ValueError):
        return default


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_receipt(contract: dict[str, Any], latest_path: Path, payload: dict[str, Any]) -> None:
    """Append full history to one weekly ledger and refresh one floor snapshot."""
    root = Path(str(contract.get("root") or DEFAULT_CONTRACT_PATH.parents[2]))
    stamp = datetime.now(UTC)
    iso = stamp.isocalendar()
    ledger_path = root / "logs" / "receipts" / f"local_floor_runner_{iso.year}_W{iso.week:02d}.jsonl"
    payload["receipt_ledger_path"] = str(ledger_path)
    payload["receipt_path"] = str(latest_path)

    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def normalize_receipt_file(path: Path) -> dict[str, Any]:
    """Upgrade one existing latest receipt without calling the model again."""
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    response_text = ((payload.get("response") or {}).get("response"))
    if isinstance(response_text, str) and response_text.strip():
        payload["response_contract"] = normalize_floor_response(
            response_text,
            expected_route=str(payload.get("receipt_path") or path),
        )
        write_json(path, payload)
    return payload


def _blocked_heavy_reason(floor: dict[str, Any], model: str, *, allow_heavy: bool) -> str | None:
    if allow_heavy:
        return None
    if _is_heavy_or_manual(floor, model):
        return "manual/heavy floor model blocked; pass allow_heavy=True or --allow-heavy to run"
    return None


def _is_heavy_or_manual(floor: dict[str, Any], model: str) -> bool:
    activation_mode = str((floor.get("activation") or {}).get("mode") or "")
    load_policy = str((floor.get("ollama_connection") or {}).get("load_policy") or "")
    return activation_mode == "manual_heavy" or "manual_heavy" in load_policy or bool(HEAVY_MODEL_PATTERN.search(model))


def _summarize_response(response: dict[str, Any]) -> dict[str, Any]:
    summary = dict(response)
    text = summary.get("response")
    if isinstance(text, str) and len(text) > 2000:
        summary["response"] = text[:2000]
        summary["response_truncated"] = True
    return summary


def normalize_floor_response(text: str, *, expected_route: str) -> dict[str, Any]:
    """Return a stable receipt contract for JSON or concise labeled text."""
    raw = text.strip()
    unfenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.IGNORECASE).strip()
    payload: dict[str, Any] | None = None
    try:
        decoded = json.loads(unfenced)
        if isinstance(decoded, dict):
            payload = decoded
    except json.JSONDecodeError:
        payload = None

    source_format = "json" if payload is not None else "normalized_text"
    if payload is None:
        summary_parts = re.split(r"\s*Safe artifact route:\s*", raw, maxsplit=1, flags=re.IGNORECASE)
        floor_summary = summary_parts[0].strip()
        blocker = None
        blocker_match = re.search(r"\bblocker:\s*(.+)$", raw, flags=re.IGNORECASE)
        if blocker_match and not blocker_match.group(1).strip().lower().startswith(("none", "no blocker")):
            blocker = blocker_match.group(1).strip()
        payload = {
            "floor_summary": floor_summary,
            "safe_artifact_route": expected_route if expected_route in raw else None,
            "blocker": blocker,
        }

    route = str(payload.get("safe_artifact_route") or "")
    return {
        "floor_summary": str(payload.get("floor_summary") or "").strip(),
        "safe_artifact_route": route,
        "blocker": payload.get("blocker"),
        "route_verified": route == expected_route,
        "source_format": source_format,
    }


def _receipt_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one safe local Ollama floor wake-up from the generated contract.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH, help="Path to local_agent_wakeup_contract.json")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--floor", help="Floor name to run, for example Neo")
    selector.add_argument("--order", type=int, help="Floor order to run")
    parser.add_argument("--execute", action="store_true", help="Call Ollama. Omit for dry-run receipt only.")
    parser.add_argument("--allow-heavy", action="store_true", help="Allow manual/heavy floor models such as gemma3:27b.")
    parser.add_argument("--receipt-target", choices=["neo", "floor"], default="neo")
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--num-predict", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        receipt = run_floor(
            contract_path=args.contract,
            floor=args.floor,
            order=args.order,
            dry_run=not args.execute,
            allow_heavy=args.allow_heavy,
            receipt_target=args.receipt_target,
            timeout_seconds=args.timeout_seconds,
            num_predict=args.num_predict,
        )
    except LocalFloorRunnerError as exc:
        print(f"local_floor_runner: {exc}")
        return 2
    print(json.dumps({"status": receipt["status"], "receipt_path": receipt["receipt_path"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
