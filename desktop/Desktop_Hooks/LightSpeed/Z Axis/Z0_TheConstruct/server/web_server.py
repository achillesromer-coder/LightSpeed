"""
LightSpeed Platform - Web Server (FastAPI)

This server is the thin orchestration surface for:
- 3D viewer (Three.js) for tower visualization
- V1 API contract under `/api/v1/*` (job ledger + artifacts + tasks + files)

Non-negotiable direction:
- UI does not compute; UI triggers jobs via API
- Jobs produce immutable artifacts (dataspace) + a manifest.json
"""

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from typing import Optional, Any, Dict, List
import uvicorn
from pathlib import Path
import os
import json
from datetime import datetime, timezone


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_settings_api_key() -> Optional[str]:
    """
    Read API key from `config/settings.json` if present.

    Expected:
      settings["api_keys"]["lightspeed_api"]["api_key"]
    """
    try:
        root = Path(__file__).resolve()
        for cand in (root, *root.parents):
            if (cand / "N.py").exists() and (cand / "config" / "settings.json").exists():
                settings_path = cand / "config" / "settings.json"
                data = json.loads(settings_path.read_text(encoding="utf-8"))
                return (
                    (data.get("api_keys") or {})
                    .get("lightspeed_api", {})
                    .get("api_key")
                ) or None
    except Exception:
        return None
    return None


def _required_api_key() -> Optional[str]:
    return os.environ.get("LIGHTSPEED_API_KEY") or _load_settings_api_key()


def _auth_required(x_api_key: Optional[str]) -> None:
    required = _required_api_key()
    if not required:
        # V1 expects auth, but a missing key is treated as "dev-local" mode.
        return
    if not x_api_key or x_api_key != required:
        raise HTTPException(status_code=401, detail="Unauthorized (X-API-Key required)")


def _try_get_services():
    try:
        from core.services import get_db, get_storage  # type: ignore
        return get_db(), get_storage()
    except Exception:
        return None, None

def create_app(lightspeed_app=None):
    """
    Create FastAPI application with embedded Three.js visualization.

    Args:
        lightspeed_app: Optional reference to main LightSpeedUnified instance

    Returns:
        FastAPI app instance
    """
    app = FastAPI(
        title="LightSpeed Server",
        description="LightSpeed orchestration + V1 API + 3D visualization",
        version="1.0.0",
    )

    db, storage = _try_get_services()

    @app.get("/", response_class=HTMLResponse)
    async def index():
        """Serve embedded Three.js viewer"""
        return THREEJS_HTML

    @app.get("/api/z-floors")
    async def get_z_floors():
        """
        Return Z-floor data for 3D rendering.

        Returns floor information including:
        - name: Floor name
        - z: Z-axis position (-4 to +3)
        - color: Hex color for visualization
        - description: Floor purpose
        - active: Whether floor is currently active
        """
        floors = [
            {
                "name": "Trinity",
                "z": 3,
                "color": "#00d4ff",
                "description": "UI Layer - Advanced interface customization",
                "active": True
            },
            {
                "name": "Neo",
                "z": 2,
                "color": "#00ff88",
                "description": "AI Assistant - Ollama integration & chat",
                "active": True
            },
            {
                "name": "Architect",
                "z": 1,
                "color": "#ff8c00",
                "description": "Mission Planning - Time management & goals",
                "active": True
            },
            {
                "name": "TheConstruct",
                "z": 0,
                "color": "#00ff00",
                "description": "Training Ground - Physics simulations & experiments",
                "active": True
            },
            {
                "name": "Morpheus",
                "z": -1,
                "color": "#9932cc",
                "description": "Knowledge Base - Documentation & file analysis",
                "active": True
            },
            {
                "name": "Oracle",
                "z": -2,
                "color": "#ffd700",
                "description": "IP Vault - Long-term archiving & storage",
                "active": True
            },
            {
                "name": "Smith",
                "z": -3,
                "color": "#ff3333",
                "description": "Background Jobs - Automated task execution",
                "active": True
            },
            {
                "name": "Merovingian",
                "z": -4,
                "color": "#8b0000",
                "description": "System Core - Health monitoring & diagnostics",
                "active": True
            }
        ]

        return JSONResponse({"floors": floors, "tower_height": 8, "total_floors": 9})

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint"""
        return JSONResponse({
            "status": "operational",
            "version": "3.1.0",
            "server": "FastAPI + Three.js"
        })

    # ======================================================================
    # V1 API
    # ======================================================================

    @app.get("/api/v1/status")
    async def v1_status(x_api_key: Optional[str] = Header(default=None, alias="X-API-Key")):
        _auth_required(x_api_key)
        payload: Dict[str, Any] = {
            "ok": True,
            "time_utc": _utc_now_iso(),
            "auth": {"configured": bool(_required_api_key())},
            "services": {"db": bool(db), "storage": bool(storage)},
        }
        if db:
            payload["db"] = {
                "path": str(getattr(db, "db_path", "")),
                "schema_ok": getattr(db, "schema_ok", None),
                "schema_report": getattr(db, "schema_report", None),
            }
        return JSONResponse(payload)

    @app.get("/api/v1/tasks")
    async def v1_list_tasks(
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
        limit: int = 200,
    ):
        _auth_required(x_api_key)
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        rows = db.execute_query(
            "SELECT id, title, description, project_id, status, priority, created_at, updated_at, metadata_json FROM tasks ORDER BY id DESC LIMIT ?",
            (int(limit),),
        )
        return JSONResponse({"tasks": rows})

    @app.post("/api/v1/tasks")
    async def v1_create_task(
        body: Dict[str, Any],
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    ):
        _auth_required(x_api_key)
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        title = str(body.get("title") or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="title is required")
        description = body.get("description")
        project_id = body.get("project_id")
        status = body.get("status") or "pending"
        priority = body.get("priority") or "normal"
        metadata_json = json.dumps(body.get("metadata") or {}, ensure_ascii=False)
        now = _utc_now_iso()
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO tasks (title, description, project_id, status, priority, created_at, updated_at, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (title, description, project_id, status, priority, now, now, metadata_json),
            )
            tid = int(cur.lastrowid)
        return JSONResponse({"task_id": tid})

    @app.get("/api/v1/jobs")
    async def v1_list_jobs(
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
        limit: int = 200,
    ):
        _auth_required(x_api_key)
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        rows = db.execute_query(
            "SELECT id, job_type, tool_key, z_context, status, created_at, started_at, completed_at, manifest_path FROM jobs ORDER BY id DESC LIMIT ?",
            (int(limit),),
        )
        return JSONResponse({"jobs": rows})

    @app.get("/api/v1/jobs/{job_id}")
    async def v1_get_job(
        job_id: int,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    ):
        _auth_required(x_api_key)
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        rows = db.execute_query("SELECT * FROM jobs WHERE id = ?", (int(job_id),))
        if not rows:
            raise HTTPException(status_code=404, detail="job not found")
        return JSONResponse({"job": rows[0]})

    @app.post("/api/v1/jobs")
    async def v1_create_job(
        body: Dict[str, Any],
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    ):
        _auth_required(x_api_key)
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        job_type = str(body.get("job_type") or body.get("tool_key") or "job").strip()
        tool_key = str(body.get("tool_key") or job_type).strip()
        z_context = str(body.get("z_context") or "unknown").strip()
        params = body.get("params") if isinstance(body.get("params"), dict) else {}
        task_id = body.get("task_id")
        project_id = body.get("project_id")
        tags = body.get("tags") if isinstance(body.get("tags"), list) else []
        inputs = body.get("inputs") if isinstance(body.get("inputs"), list) else []
        created = db.create_job_v1(
            job_type=job_type,
            tool_key=tool_key,
            z_context=z_context,
            params=params,
            task_id=task_id,
            project_id=project_id,
            tags=tags,
            inputs=inputs,
        )
        return JSONResponse(created)

    @app.get("/api/v1/jobs/{job_id}/artifacts")
    async def v1_list_job_artifacts(
        job_id: int,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    ):
        _auth_required(x_api_key)
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        rows = db.execute_query("SELECT * FROM artifacts WHERE job_id = ? ORDER BY id ASC", (int(job_id),))
        return JSONResponse({"artifacts": rows})

    @app.get("/api/v1/files")
    async def v1_list_files(
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
        limit: int = 200,
    ):
        _auth_required(x_api_key)
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        rows = db.execute_query(
            "SELECT id, path, name, extension, size_bytes, hash_sha256, status, created_at, project_id FROM files ORDER BY id DESC LIMIT ?",
            (int(limit),),
        )
        return JSONResponse({"files": rows})

    @app.get("/api/v1/files/{file_id}/download")
    async def v1_download_file(
        file_id: int,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    ):
        _auth_required(x_api_key)
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        rows = db.execute_query("SELECT path, name FROM files WHERE id = ?", (int(file_id),))
        if not rows:
            raise HTTPException(status_code=404, detail="file not found")
        path = Path(rows[0].get("path") or "")
        if not path.exists():
            raise HTTPException(status_code=404, detail="file path missing on disk")
        return FileResponse(path, filename=rows[0].get("name") or path.name)

    return app


# Embedded Three.js HTML - No separate template files needed!
THREEJS_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LightSpeed 3D Tower - Z-Floor Visualization</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #00ff88;
            overflow: hidden;
        }

        #canvas-container {
            width: 100vw;
            height: 100vh;
            position: relative;
        }

        canvas {
            display: block;
        }

        #info-panel {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0, 0, 0, 0.8);
            border: 2px solid #00ff88;
            border-radius: 10px;
            padding: 20px;
            max-width: 350px;
            backdrop-filter: blur(10px);
        }

        #info-panel h1 {
            color: #00d4ff;
            font-size: 24px;
            margin-bottom: 10px;
            text-shadow: 0 0 10px #00d4ff;
        }

        #info-panel p {
            color: #aaa;
            font-size: 14px;
            margin-bottom: 15px;
        }

        #floor-list {
            margin-top: 15px;
        }

        .floor-item {
            padding: 8px;
            margin: 5px 0;
            border-left: 3px solid;
            background: rgba(255, 255, 255, 0.05);
            cursor: pointer;
            transition: all 0.3s;
        }

        .floor-item:hover {
            background: rgba(255, 255, 255, 0.15);
            transform: translateX(5px);
        }

        .floor-name {
            font-weight: bold;
            font-size: 16px;
        }

        .floor-desc {
            font-size: 12px;
            color: #888;
            margin-top: 3px;
        }

        #controls {
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            border: 2px solid #00ff88;
            border-radius: 10px;
            padding: 15px;
            color: #00ff88;
        }

        #controls h3 {
            margin-bottom: 10px;
            color: #00d4ff;
        }

        #controls p {
            font-size: 12px;
            margin: 5px 0;
            color: #aaa;
        }

        .status {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(0, 255, 136, 0.2);
            border: 2px solid #00ff88;
            border-radius: 20px;
            padding: 10px 20px;
            font-weight: bold;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
    </style>
</head>
<body>
    <div id="canvas-container">
        <div id="info-panel">
            <h1>⚡ LightSpeed Platform</h1>
            <p>Interactive Z-Floor Tower Architecture</p>
            <div id="floor-list"></div>
        </div>

        <div class="status">● OPERATIONAL</div>

        <div id="controls">
            <h3>Controls</h3>
            <p>🖱️ Rotate: Click + Drag</p>
            <p>🔍 Zoom: Scroll Wheel</p>
            <p>📍 Pan: Right Click + Drag</p>
        </div>
    </div>

    <script>
        // Scene setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a0a0a);
        scene.fog = new THREE.Fog(0x0a0a0a, 10, 50);

        // Camera
        const camera = new THREE.PerspectiveCamera(
            75,
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        camera.position.set(12, 8, 12);
        camera.lookAt(0, 0, 0);

        // Renderer
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        document.getElementById('canvas-container').appendChild(renderer.domElement);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
        scene.add(ambientLight);

        const mainLight = new THREE.DirectionalLight(0xffffff, 0.8);
        mainLight.position.set(10, 20, 10);
        mainLight.castShadow = true;
        mainLight.shadow.camera.left = -20;
        mainLight.shadow.camera.right = 20;
        mainLight.shadow.camera.top = 20;
        mainLight.shadow.camera.bottom = -20;
        scene.add(mainLight);

        // Point lights for dramatic effect
        const pointLight1 = new THREE.PointLight(0x00d4ff, 1, 20);
        pointLight1.position.set(0, 10, 0);
        scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight(0xff00ff, 0.8, 15);
        pointLight2.position.set(5, -5, 5);
        scene.add(pointLight2);

        // Grid helper
        const gridHelper = new THREE.GridHelper(30, 30, 0x00ff88, 0x003333);
        gridHelper.position.y = -8;
        scene.add(gridHelper);

        // Floor meshes storage
        const floorMeshes = [];

        // Fetch and render Z-floors
        fetch('/api/z-floors')
            .then(response => response.json())
            .then(data => {
                const floorList = document.getElementById('floor-list');

                data.floors.forEach((floor, index) => {
                    // Create floor mesh
                    const geometry = new THREE.BoxGeometry(5, 0.6, 5);
                    const material = new THREE.MeshPhongMaterial({
                        color: floor.color,
                        emissive: floor.color,
                        emissiveIntensity: 0.3,
                        shininess: 100,
                        transparent: true,
                        opacity: 0.9
                    });

                    const mesh = new THREE.Mesh(geometry, material);
                    mesh.position.y = floor.z * 2.5;
                    mesh.castShadow = true;
                    mesh.receiveShadow = true;
                    mesh.userData = floor;

                    // Add edge lines
                    const edges = new THREE.EdgesGeometry(geometry);
                    const lineMaterial = new THREE.LineBasicMaterial({
                        color: 0xffffff,
                        transparent: true,
                        opacity: 0.4
                    });
                    const wireframe = new THREE.LineSegments(edges, lineMaterial);
                    mesh.add(wireframe);

                    scene.add(mesh);
                    floorMeshes.push(mesh);

                    // Add to info panel
                    const floorDiv = document.createElement('div');
                    floorDiv.className = 'floor-item';
                    floorDiv.style.borderLeftColor = floor.color;
                    floorDiv.innerHTML = `
                        <div class="floor-name" style="color: ${floor.color}">
                            Z${floor.z > 0 ? '+' : ''}${floor.z}: ${floor.name}
                        </div>
                        <div class="floor-desc">${floor.description}</div>
                    `;

                    // Click to focus
                    floorDiv.addEventListener('click', () => {
                        focusOnFloor(mesh);
                    });

                    floorList.appendChild(floorDiv);
                });
            })
            .catch(error => {
                console.error('Error loading Z-floors:', error);
            });

        // Camera controls (simple rotation)
        let isDragging = false;
        let previousMousePosition = { x: 0, y: 0 };
        let cameraAngle = { theta: Math.PI / 4, phi: Math.PI / 4 };
        let cameraDistance = 18;

        renderer.domElement.addEventListener('mousedown', (e) => {
            isDragging = true;
            previousMousePosition = { x: e.clientX, y: e.clientY };
        });

        window.addEventListener('mouseup', () => {
            isDragging = false;
        });

        window.addEventListener('mousemove', (e) => {
            if (isDragging) {
                const deltaX = e.clientX - previousMousePosition.x;
                const deltaY = e.clientY - previousMousePosition.y;

                cameraAngle.theta -= deltaX * 0.01;
                cameraAngle.phi -= deltaY * 0.01;

                // Clamp phi
                cameraAngle.phi = Math.max(0.1, Math.min(Math.PI - 0.1, cameraAngle.phi));

                previousMousePosition = { x: e.clientX, y: e.clientY };
            }
        });

        renderer.domElement.addEventListener('wheel', (e) => {
            e.preventDefault();
            cameraDistance += e.deltaY * 0.01;
            cameraDistance = Math.max(8, Math.min(30, cameraDistance));
        });

        function focusOnFloor(mesh) {
            const targetY = mesh.position.y;
            cameraDistance = 12;
            // Smooth transition could be added here
        }

        // Animation loop
        function animate() {
            requestAnimationFrame(animate);

            // Update camera position based on spherical coordinates
            camera.position.x = cameraDistance * Math.sin(cameraAngle.phi) * Math.cos(cameraAngle.theta);
            camera.position.y = cameraDistance * Math.cos(cameraAngle.phi);
            camera.position.z = cameraDistance * Math.sin(cameraAngle.phi) * Math.sin(cameraAngle.theta);
            camera.lookAt(0, 0, 0);

            // Gentle rotation of floors
            floorMeshes.forEach((mesh, index) => {
                mesh.rotation.y += 0.001 * (index % 2 === 0 ? 1 : -1);
            });

            renderer.render(scene, camera);
        }

        animate();

        // Handle window resize
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        console.log('LightSpeed 3D Viewer initialized');
    </script>
</body>
</html>
'''


def start_server(host: str = "127.0.0.1", port: int = 8080, app_ref=None):
    """
    Start the web server in the current thread (blocking).

    Args:
        host: Server host address
        port: Server port
        app_ref: Reference to main LightSpeed application
    """
    app = create_app(app_ref)
    uvicorn.run(app, host=host, port=port, log_level="error")


if __name__ == "__main__":
    # For standalone testing
    print("[LightSpeed Web Server]")
    print("Starting on http://127.0.0.1:8080")
    print("Press Ctrl+C to stop")
    start_server()
