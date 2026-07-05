from __future__ import annotations

import argparse
from contextlib import AbstractContextManager
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
from urllib.request import Request, urlopen


DEFAULT_CONTRACT_PATH = Path(__file__).resolve().parents[1] / "exports" / "agent_home" / "local_agent_wakeup_contract.json"
DEFAULT_TIMEOUT_SECONDS = 90
DEFAULT_NUM_PREDICT = 512
MAX_NUM_PREDICT = 1024
HEAVY_MODEL_PATTERN = re.compile(r"(?:(?:27|70|120|405|671)b)|cloud", re.IGNORECASE)

HttpPost = Callable[[str, dict[str, Any], float], dict[str, Any]]


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
        "options": {"num_predict": bounded_num_predict},
    }


def build_floor_prompt(contract: dict[str, Any], floor: dict[str, Any]) -> str:
    training = floor.get("training_context") or {}
    draw = floor.get("assimilation_draw") or {}
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
            "Learning sequence:",
            sequence or "- Return a concise floor summary, one safe artifact route, and one blocker if present.",
            "Priority source paths:",
            "\n".join(path_lines),
            "Do not do:",
            do_not_do or "- Do not run heavy/manual models or parallel sessions without approval.",
            "Return JSON-compatible text with keys: floor_summary, safe_artifact_route, blocker.",
        ]
    )


def resolve_receipt_path(contract: dict[str, Any], floor: dict[str, Any], *, receipt_target: str = "neo") -> Path:
    safe_floor = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(floor.get("floor") or "floor")).strip("_")
    filename = f"local_floor_runner_receipt_{safe_floor}_latest.json"

    if receipt_target == "floor":
        return Path(str(floor["floor_root"])) / "data" / "wakeup" / filename
    if receipt_target == "neo":
        shell_root = Path(str(contract["shell_root"]))
        return shell_root / "Z Axis" / "Z+2_Neo" / "data" / "temp_shells" / "outputs" / filename
    raise LocalFloorRunnerError("receipt_target must be 'neo' or 'floor'")


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
    }
    if blocked_reason:
        receipt["blocked_reason"] = blocked_reason
    if response is not None:
        receipt["response"] = _summarize_response(response)
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
