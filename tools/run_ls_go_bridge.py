from __future__ import annotations

import os
import sys
import threading
from pathlib import Path


def resolve_runtime_layout(
    repo_root: Path,
    environ: dict[str, str] | None = None,
) -> tuple[Path, Path, Path]:
    source = os.environ if environ is None else environ
    configured = source.get("LIGHTSPEED_CANONICAL_ROOT")
    if configured:
        canonical_root = Path(configured)
        return canonical_root, canonical_root / "App", canonical_root / "Core"

    if (repo_root / "App").is_dir() and (repo_root / "Core").is_dir():
        return repo_root, repo_root / "App", repo_root / "Core"

    return (
        repo_root,
        repo_root / "desktop" / "Desktop_Hooks" / "LightSpeed",
        repo_root / "desktop" / "LightSpeed_Runtime",
    )


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ROOT, DESKTOP_ROOT, RUNTIME_ROOT = resolve_runtime_layout(REPO_ROOT)

os.environ["LIGHTSPEED_CANONICAL_ROOT"] = str(CANONICAL_ROOT)
os.environ["LIGHTSPEED_RUNTIME_ROOT"] = str(RUNTIME_ROOT)
os.environ["LIGHTSPEED_SHELL_ROOT"] = str(DESKTOP_ROOT)

sys.path.insert(0, str(RUNTIME_ROOT))
sys.path.insert(0, str(DESKTOP_ROOT))

from lightspeed_runtime.ls_go_bridge import start_server
from lightspeed_runtime.ls_go_job_consumer import LSGoJobConsumer


def start_local_bridge(root: Path) -> None:
    """Start the local bridge with its Smith-owned durable DB consumer.

    The consumer is deliberately hosted in the same singleton process as the
    localhost bridge. A healthy bridge therefore has one durable command
    consumer, while the consumer's own lock prevents duplicate threads/processes
    from draining the same persisted job ledger.
    """
    consumer = LSGoJobConsumer(root)
    thread = threading.Thread(
        target=consumer.run_forever,
        kwargs={"poll_seconds": 1.0},
        name="lightspeed-ls-go-job-consumer",
        daemon=True,
    )
    thread.start()
    try:
        start_server(root=root)
    finally:
        consumer.stop()
        thread.join(timeout=3.0)


if __name__ == "__main__":
    root = Path(os.environ.get("LIGHTSPEED_ROOT", DESKTOP_ROOT))
    start_local_bridge(root=root)
