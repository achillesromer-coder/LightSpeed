#!/usr/bin/env python3
"""Run one bounded Neo-supervised Cognigrex workflow on the existing runtime.

Default mode is dry-run. Use --execute only on the canonical local host after
its runtime/bridge/install gates are satisfied. The script does not merge Git,
write Drive canon, publish Web, dispatch LS GO tasks, or ingest De Sporte data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / "desktop" / "LightSpeed_Runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from lightspeed_runtime.cognigrex_supervisor import run_supervised_workflow
from lightspeed_runtime.local_floor_runner import DEFAULT_CONTRACT_PATH


def read_instruction(args: argparse.Namespace) -> str:
    if args.instruction_file:
        return args.instruction_file.read_text(encoding="utf-8").strip()
    if args.instruction:
        return args.instruction.strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    raise SystemExit("Provide --instruction, --instruction-file, or pipe the bounded task on stdin.")


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--instruction")
    source.add_argument("--instruction-file", type=Path)
    parser.add_argument("--task-id")
    parser.add_argument("--project-id")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT_PATH)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-heavy", action="store_true")
    parser.add_argument("--continue-on-failure", action="store_true")
    args = parser.parse_args()

    receipt = run_supervised_workflow(
        read_instruction(args),
        contract_path=args.contract,
        task_id=args.task_id,
        project_id=args.project_id,
        dry_run=not args.execute,
        allow_heavy=args.allow_heavy,
        stop_on_failure=not args.continue_on_failure,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt.get("complete_workflow") and receipt.get("status") != "failed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
