from __future__ import annotations

import argparse
import json
from pathlib import Path

from lightspeed_runtime.web_integration import build_romer_web_integration


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate the committed GST-063 web/Drive bridge from canonical route source.")
    parser.add_argument("--check", action="store_true", help="Do not write; return non-zero if the committed payload differs.")
    args = parser.parse_args()

    app_root = Path(__file__).resolve().parents[1]
    destination = app_root / "config" / "web_drive_bridge.json"
    payload = build_romer_web_integration(app_root)

    # Preserve the generated payload as deterministic JSON apart from generated_at.
    expected = json.dumps(payload, indent=2, sort_keys=False) + "\n"

    if args.check:
        if not destination.exists():
            print(f"missing: {destination}")
            return 1
        current = destination.read_text(encoding="utf-8")
        try:
            current_payload = json.loads(current)
        except json.JSONDecodeError as exc:
            print(f"invalid JSON: {exc}")
            return 1

        # generated_at is receipt metadata, not route semantics.
        current_payload.pop("generated_at", None)
        check_payload = dict(payload)
        check_payload.pop("generated_at", None)
        if current_payload != check_payload:
            print("GST-063 bridge differs from canonical source")
            return 1
        print("GST-063 bridge matches canonical source")
        return 0

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(expected, encoding="utf-8")
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
