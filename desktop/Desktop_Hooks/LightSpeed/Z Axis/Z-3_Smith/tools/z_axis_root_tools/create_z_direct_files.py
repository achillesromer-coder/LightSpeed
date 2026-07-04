#!/usr/bin/env python
"""
Create Z Direct Inter-Floor Data Files
Systematically generates standardized inter-floor communication files for all Z-Axis floors

Author: LightSpeed Team
Version: 0.9.0
Date: January 11, 2026
"""

from pathlib import Path
import json
from datetime import datetime
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for cand in (start, *start.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return start.parent


LIGHTSPEED_ROOT = _find_lightspeed_root(Path(__file__))
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"

# Floor definitions
FLOORS = [
    {
        "name": "Merovingian",
        "z_level": -4,
        "description": "Core Services Foundation - Database, Event Bus, Storage, Logging, Performance Monitoring",
        "dependencies": [],
        "services": ["database", "event_bus", "storage", "logger", "performance_monitor", "cache_manager", "websocket_server"]
    },
    {
        "name": "Smith",
        "z_level": -3,
        "description": "Security & Validation - Code scanning, threat detection, system integrity",
        "dependencies": ["Merovingian"],
        "services": ["security_scanner", "validator", "integrity_checker"]
    },
    {
        "name": "Oracle",
        "z_level": -2,
        "description": "Predictions & Archives - Historical data, trend forecasting, IP vault",
        "dependencies": ["Merovingian", "Smith"],
        "services": ["prediction_engine", "archive_manager", "ip_vault"]
    },
    {
        "name": "Morpheus",
        "z_level": -1,
        "description": "Knowledge Management - Documentation, semantic search, information retrieval",
        "dependencies": ["Merovingian", "Smith", "Oracle"],
        "services": ["knowledge_base", "indexer", "semantic_search"]
    },
    {
        "name": "TheConstruct",
        "z_level": 0,
        "description": "Physics Simulations & Visualizations - Raphael, BigBang, GMAT integration",
        "dependencies": ["Merovingian", "Smith", "Oracle", "Morpheus"],
        "services": ["simulation_engine", "3d_renderer", "physics_tools"]
    },
    {
        "name": "Architect",
        "z_level": 1,
        "description": "Task Management & Project Planning - OKRs, timelines, cross-floor coordination",
        "dependencies": ["Merovingian", "Smith", "Oracle", "Morpheus", "TheConstruct"],
        "services": ["task_manager", "project_planner", "okr_tracker"]
    },
    {
        "name": "Neo",
        "z_level": 2,
        "description": "AI Orchestration & Cognitive Enhancement - Ollama/Achilles, Cognigrex, perpetual growth",
        "dependencies": ["Merovingian", "Smith", "Oracle", "Morpheus", "TheConstruct", "Architect"],
        "services": ["ai_orchestrator", "cognigrex", "code_assistant", "context_manager"]
    },
    {
        "name": "Trinity",
        "z_level": 3,
        "description": "Dashboard & Coordination Hub - Real-time monitoring, external services, UI layer",
        "dependencies": ["Merovingian", "Smith", "Oracle", "Morpheus", "TheConstruct", "Architect", "Neo"],
        "services": ["dashboard", "service_manager", "portal_glass", "settings_hub"]
    }
]


def create_floor_manifest(floor_dir: Path, floor: dict):
    """Create floor_manifest.json"""

    # Calculate dependents (floors that depend on this floor)
    dependents = []
    for other_floor in FLOORS:
        if floor["name"] in other_floor["dependencies"]:
            dependents.append(other_floor["name"])

    manifest = {
        "floor_name": floor["name"],
        "z_level": floor["z_level"],
        "version": "0.9.0",
        "description": floor["description"],
        "status": "operational",
        "initialized": False,
        "dependencies": floor["dependencies"],
        "dependents": dependents,
        "services": {svc: {"status": "ready"} for svc in floor["services"]},
        "exports": [],
        "metadata": {
            "created": datetime.now().strftime("%Y-%m-%d"),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "author": "LightSpeed Team"
        }
    }

    manifest_file = floor_dir / "floor_manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print(f"  [OK] Created {manifest_file.name}")


def create_inter_floor_events(floor_dir: Path, floor: dict):
    """Create inter_floor_events.json"""

    events = {
        "floor": floor["name"],
        "z_level": floor["z_level"],
        "last_updated": datetime.now().isoformat(),
        "events_published": [],
        "events_subscribed": [],
        "event_log": [],
        "statistics": {
            "total_published": 0,
            "total_consumed": 0,
            "total_subscriptions": 0
        }
    }

    events_file = floor_dir / "inter_floor_events.json"
    with open(events_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2)

    print(f"  [OK] Created {events_file.name}")


def create_performance_metrics(floor_dir: Path, floor: dict):
    """Create performance_metrics.json"""

    metrics = {
        "floor": floor["name"],
        "z_level": floor["z_level"],
        "last_updated": datetime.now().isoformat(),
        "metrics": {
            "response_time_ms": {
                "min": 0,
                "max": 0,
                "avg": 0,
                "p95": 0,
                "p99": 0
            },
            "throughput": {
                "requests_per_second": 0,
                "operations_per_minute": 0
            },
            "resource_usage": {
                "memory_mb": 0,
                "cpu_percent": 0
            },
            "error_rate": {
                "total_errors": 0,
                "error_rate_percent": 0
            }
        },
        "alerts": [],
        "health_status": "healthy"
    }

    metrics_file = floor_dir / "performance_metrics.json"
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    print(f"  [OK] Created {metrics_file.name}")


def create_data_objects(floor_dir: Path, floor: dict):
    """Create data_objects.json for inter-floor data sharing"""

    data_objects = {
        "floor": floor["name"],
        "z_level": floor["z_level"],
        "last_updated": datetime.now().isoformat(),
        "shared_objects": {},
        "object_types": [],
        "access_log": []
    }

    objects_file = floor_dir / "data_objects.json"
    with open(objects_file, 'w', encoding='utf-8') as f:
        json.dump(data_objects, f, indent=2)

    print(f"  [OK] Created {objects_file.name}")


def create_floor_config(floor_dir: Path, floor: dict):
    """Create floor_config.json"""

    config = {
        "floor": floor["name"],
        "z_level": floor["z_level"],
        "version": "0.9.0",
        "settings": {
            "enabled": True,
            "auto_start": True,
            "log_level": "INFO",
            "cache_enabled": True,
            "monitoring_enabled": True
        },
        "paths": {
            "data": f"data/{floor['name'].lower()}/",
            "logs": f"logs/{floor['name'].lower()}/",
            "cache": f"cache/{floor['name'].lower()}/",
            "temp": f"temp/{floor['name'].lower()}/"
        },
        "features": {
            svc: {"enabled": True} for svc in floor["services"]
        }
    }

    config_file = floor_dir / "floor_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    print(f"  [OK] Created {config_file.name}")


def create_communication_log(floor_dir: Path, floor: dict):
    """Create communication_log.txt"""

    log_content = f"""# {floor['name']} Floor - Inter-Floor Communication Log

Floor: {floor['name']}
Z-Level: {floor['z_level']}
Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

═══════════════════════════════════════════════════════════════════

This log tracks all inter-floor communications, event publications,
and subscriptions for the {floor['name']} floor.

Format: [TIMESTAMP] [TYPE] [SOURCE→TARGET] Message

═══════════════════════════════════════════════════════════════════

"""

    log_file = floor_dir / "communication_log.txt"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(log_content)

    print(f"  [OK] Created {log_file.name}")


def create_status_html(floor_dir: Path, floor: dict):
    """Create status.html dashboard"""

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{floor['name']} Floor - Status Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #000B1F 0%, #001B3F 100%);
            color: #00FFFF;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(0, 40, 85, 0.8);
            border: 2px solid #00FFFF;
            border-radius: 10px;
            padding: 30px;
        }}
        h1 {{
            color: #00FFFF;
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #00DDFF;
            margin-bottom: 30px;
        }}
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        .status-card {{
            background: rgba(0, 20, 50, 0.6);
            border: 1px solid #00FFFF;
            border-radius: 8px;
            padding: 20px;
        }}
        .status-card h3 {{
            color: #00FF88;
            margin-top: 0;
        }}
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #00FF00;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 8px;
            background: rgba(0, 255, 255, 0.1);
            border-radius: 4px;
        }}
        .metric-label {{
            color: #00DDFF;
        }}
        .metric-value {{
            color: #FFFFFF;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1> {floor['name']} Floor Status</h1>
        <div class="subtitle">
            Z-Level: {floor['z_level']:+d} | {floor['description']}
        </div>

        <div class="status-grid">
            <div class="status-card">
                <h3><span class="status-indicator"></span>Floor Status</h3>
                <div class="metric">
                    <span class="metric-label">Operational</span>
                    <span class="metric-value">[OK] Active</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Initialized</span>
                    <span class="metric-value">Ready</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Health</span>
                    <span class="metric-value">100%</span>
                </div>
            </div>

            <div class="status-card">
                <h3>Performance</h3>
                <div class="metric">
                    <span class="metric-label">Response Time</span>
                    <span class="metric-value">< 100ms</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Throughput</span>
                    <span class="metric-value">High</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Errors</span>
                    <span class="metric-value">0</span>
                </div>
            </div>

            <div class="status-card">
                <h3>Dependencies</h3>
                <div class="metric">
                    <span class="metric-label">Required Floors</span>
                    <span class="metric-value">{len(floor['dependencies'])}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">All Connected</span>
                    <span class="metric-value">[OK] Yes</span>
                </div>
            </div>

            <div class="status-card">
                <h3>Services</h3>
                <div class="metric">
                    <span class="metric-label">Total Services</span>
                    <span class="metric-value">{len(floor['services'])}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Active</span>
                    <span class="metric-value">{len(floor['services'])}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Status</span>
                    <span class="metric-value">[OK] All Ready</span>
                </div>
            </div>
        </div>

        <div style="margin-top: 40px; text-align: center; color: #00DDFF; font-size: 0.9em;">
            Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | LightSpeed Platform v0.9.0
        </div>
    </div>
</body>
</html>
"""

    html_file = floor_dir / "status.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"  [OK] Created {html_file.name}")


def main():
    """Create all Z Direct files for all floors"""
    print("=" * 70)
    print("Creating Z Direct Inter-Floor Data Files")
    print("=" * 70)
    print()

    for floor in FLOORS:
        # Construct floor directory name
        if floor["z_level"] >= 0:
            floor_dir_name = f"Z+{floor['z_level']}_{floor['name']}" if floor["z_level"] > 0 else f"Z{floor['z_level']}_{floor['name']}"
        else:
            floor_dir_name = f"Z{floor['z_level']}_{floor['name']}"

        floor_dir = Z_AXIS_ROOT / floor_dir_name / "Z Direct"

        if not floor_dir.exists():
            print(f"[WARN]  Creating Z Direct directory: {floor_dir_name}")
            floor_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n[{floor['name']}] Z-Level {floor['z_level']:+d}")
        print(f"  Directory: {floor_dir_name}/Z Direct")

        # Create all data files
        create_floor_manifest(floor_dir, floor)
        create_inter_floor_events(floor_dir, floor)
        create_performance_metrics(floor_dir, floor)
        create_data_objects(floor_dir, floor)
        create_floor_config(floor_dir, floor)
        create_communication_log(floor_dir, floor)
        create_status_html(floor_dir, floor)

    print("\n" + "=" * 70)
    print("[SUCCESS] All Z Direct files created successfully!")
    print("=" * 70)
    print(f"\nTotal floors processed: {len(FLOORS)}")
    print("Files created per floor: 7")
    print(f"Total files created: {len(FLOORS) * 7}")


if __name__ == "__main__":
    main()
