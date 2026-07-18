from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DESKTOP_ROOT = REPO_ROOT / "desktop" / "Desktop_Hooks" / "LightSpeed"
RUNTIME_ROOT = REPO_ROOT / "desktop" / "LightSpeed_Runtime"

sys.path.insert(0, str(RUNTIME_ROOT))
sys.path.insert(0, str(DESKTOP_ROOT))

from lightspeed_runtime.ls_go_bridge import start_server


if __name__ == "__main__":
    root = Path(os.environ.get("LIGHTSPEED_ROOT", DESKTOP_ROOT))
    start_server(root=root)
