#!/usr/bin/env python
"""
Floor API Endpoints - RESTful APIs for all Z-floors
LightSpeed Type I Civilization Platform

Provides REST API endpoints for each floor, enabling:
- External integrations
- Web-based access
- Mobile app connectivity
- Third-party plugins

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import sys

# Add paths
_parent = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_parent))

from core.services import get_db, get_event_bus, get_storage


# FastAPI app
app = FastAPI(
    title="LightSpeed Platform API",
    description="RESTful API for all Z-axis floors",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class TaskCreate(BaseModel):
    title: str
    description: str
    project_id: Optional[int] = None
    priority: Optional[str] = "normal"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class InterFloorTask(BaseModel):
    source_floor: str
    target_floor: str
    task_type: str
    payload: Dict[str, Any]
    priority: Optional[str] = "normal"
    deadline: Optional[str] = None


class EventPublish(BaseModel):
    topic: str
    data: Dict[str, Any]


class FloorStatus(BaseModel):
    floor: str
    z_level: int
    status: str
    capabilities: List[str]
    metrics: Optional[Dict[str, Any]] = None


# Dependency: API key validation (placeholder)
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key"""
    if not x_api_key:
        # For now, allow without key (development mode)
        return None

    # In production, validate against database
    # if x_api_key not in valid_keys:
    #     raise HTTPException(status_code=401, detail="Invalid API key")

    return x_api_key


# === Global Endpoints ===

@app.get("/")
async def root():
    """API root"""
    return {
        "name": "LightSpeed Platform API",
        "version": "1.0.0",
        "status": "operational",
        "floors": [
            "Z+3 Trinity", "Z+2 Neo", "Z+1 Architect",
            "Z0 TheConstruct", "Z-1 Morpheus", "Z-2 Oracle",
            "Z-3 Smith", "Z-4 Merovingian"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "operational",
            "event_bus": "operational",
            "storage": "operational"
        }
    }


# === Trinity Floor (Z+3) - UI & Dashboards ===

@app.get("/api/v1/trinity/status")
async def trinity_status(api_key: Optional[str] = Depends(verify_api_key)):
    """Get Trinity floor status"""
    return FloorStatus(
        floor="Trinity",
        z_level=3,
        status="operational",
        capabilities=["ui_dashboards", "3d_visualization", "theme_management"],
        metrics={"active_users": 1, "dashboard_widgets": 12}
    ).__dict__


@app.get("/api/v1/trinity/widgets")
async def list_trinity_widgets():
    """List available Trinity widgets"""
    return {
        "widgets": [
            {"id": "task_board", "name": "Task Board", "type": "interactive"},
            {"id": "metrics_dashboard", "name": "Metrics", "type": "chart"},
            {"id": "3d_navigation", "name": "3D Navigator", "type": "immersive"}
        ]
    }


# === Neo Floor (Z+2) - AI Integration ===

@app.get("/api/v1/neo/status")
async def neo_status():
    """Get Neo floor status"""
    return FloorStatus(
        floor="Neo",
        z_level=2,
        status="operational",
        capabilities=["ai_inference", "code_generation", "training"],
        metrics={"ai_backend": "connected", "models_loaded": 2}
    ).__dict__


@app.post("/api/v1/neo/inference")
async def neo_inference(prompt: str, context: Optional[Dict] = None):
    """Run AI inference"""
    # Placeholder - would call actual AI backend
    return {
        "prompt": prompt,
        "response": f"AI response to: {prompt}",
        "model": "default",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/neo/models")
async def list_neo_models():
    """List available AI models"""
    return {
        "models": [
            {"id": "achilles", "name": "Achilles", "status": "ready", "type": "general"},
            {"id": "cognigrex", "name": "Cognigrex", "status": "ready", "type": "code"}
        ]
    }


# === Architect Floor (Z+1) - Mission Planning ===

@app.get("/api/v1/architect/status")
async def architect_status():
    """Get Architect floor status"""
    return FloorStatus(
        floor="Architect",
        z_level=1,
        status="operational",
        capabilities=["mission_planning", "project_management", "okrs"],
        metrics={"active_projects": 5, "tasks_tracked": 47}
    ).__dict__


@app.get("/api/v1/architect/projects")
async def list_projects():
    """List all projects"""
    db = get_db()
    projects = db.get_all_projects()
    return {"projects": projects}


@app.post("/api/v1/architect/tasks")
async def create_task(task: TaskCreate):
    """Create new task"""
    db = get_db()
    task_id = db.create_task(task.title, task.description, project_id=task.project_id)
    return {"task_id": task_id, "status": "created"}


@app.get("/api/v1/architect/tasks/{task_id}")
async def get_task(task_id: int):
    """Get task by ID"""
    db = get_db()
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/api/v1/architect/tasks/{task_id}")
async def update_task(task_id: int, task: TaskUpdate):
    """Update task"""
    db = get_db()
    updates = {k: v for k, v in task.dict().items() if v is not None}
    db.update_task(task_id, **updates)
    return {"task_id": task_id, "status": "updated"}


# === TheConstruct Floor (Z0) - Physics & Simulations ===

@app.get("/api/v1/construct/status")
async def construct_status():
    """Get TheConstruct floor status"""
    return FloorStatus(
        floor="TheConstruct",
        z_level=0,
        status="operational",
        capabilities=["physics_simulations", "raphael_equations", "3d_rendering"],
        metrics={"active_simulations": 2, "physics_engine": "ready"}
    ).__dict__


@app.post("/api/v1/construct/simulate/raphael")
async def simulate_raphael(protons: int, neutrons: int, electrons: int):
    """Run Raphael equations simulation"""
    from core.services import get_physics_tools

    physics = get_physics_tools()
    result = physics.calculate_raphael_equations(protons, neutrons, electrons)

    return {
        "input": {"protons": protons, "neutrons": neutrons, "electrons": electrons},
        "output": result,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/construct/simulations")
async def list_simulations():
    """List available simulations"""
    return {
        "simulations": [
            {"id": "raphael", "name": "Raphael Equations", "type": "physics"},
            {"id": "bigbang", "name": "Big Bang", "type": "cosmology"},
            {"id": "orbital", "name": "Orbital Mechanics", "type": "physics"},
            {"id": "quantum", "name": "Quantum Mechanics", "type": "physics"}
        ]
    }


# === Morpheus Floor (Z-1) - Knowledge & Code Analysis ===

@app.get("/api/v1/morpheus/status")
async def morpheus_status():
    """Get Morpheus floor status"""
    return FloorStatus(
        floor="Morpheus",
        z_level=-1,
        status="operational",
        capabilities=["code_analysis", "documentation", "knowledge_base"],
        metrics={"indexed_files": 150, "documentation_pages": 45}
    ).__dict__


@app.get("/api/v1/morpheus/docs")
async def list_documentation():
    """List documentation"""
    storage = get_storage()
    docs_path = storage.get_floor_path("morpheus") / "documentation"

    if docs_path.exists():
        docs = [
            {"name": f.name, "path": str(f.relative_to(docs_path)), "size": f.stat().st_size}
            for f in docs_path.glob("*.md")
        ]
        return {"documents": docs}

    return {"documents": []}


@app.get("/api/v1/morpheus/search")
async def search_knowledge(query: str, limit: int = 10):
    """Search knowledge base"""
    # Placeholder - would implement full-text search
    return {
        "query": query,
        "results": [
            {"title": "Cross-Floor Integration", "relevance": 0.95, "path": "CROSS_FLOOR_INTEGRATION_ARCHITECTURE.md"},
            {"title": "System Enhancement Plan", "relevance": 0.87, "path": "SYSTEM_ENHANCEMENT_PLAN.md"}
        ]
    }


# === Oracle Floor (Z-2) - Archive & Ingestion ===

@app.get("/api/v1/oracle/status")
async def oracle_status():
    """Get Oracle floor status"""
    return FloorStatus(
        floor="Oracle",
        z_level=-2,
        status="operational",
        capabilities=["file_ingestion", "archive_management", "encyclopedia"],
        metrics={"archived_files": 234, "active_ingestions": 3}
    ).__dict__


@app.get("/api/v1/oracle/files")
async def list_archived_files(floor: Optional[str] = None):
    """List archived files"""
    storage = get_storage()

    if floor:
        files = storage.list_files(floor=floor)
    else:
        files = storage.list_files(floor="oracle")

    return {"files": files}


@app.post("/api/v1/oracle/ingest")
async def trigger_ingestion(file_path: str, target_floors: Optional[List[str]] = None):
    """Trigger file ingestion"""
    # Placeholder - would trigger Oracle Smart Floor Integrator
    return {
        "status": "queued",
        "file": file_path,
        "targets": target_floors or ["all"],
        "timestamp": datetime.now().isoformat()
    }


# === Smith Floor (Z-3) - Automation & Background Jobs ===

@app.get("/api/v1/smith/status")
async def smith_status():
    """Get Smith floor status"""
    return FloorStatus(
        floor="Smith",
        z_level=-3,
        status="operational",
        capabilities=["task_scheduling", "automation", "workflows"],
        metrics={"active_jobs": 5, "scheduled_tasks": 12}
    ).__dict__


@app.post("/api/v1/smith/tasks/interfloor")
async def create_interfloor_task(task: InterFloorTask):
    """Create inter-floor task"""
    db = get_db()

    task_id = db.create_interfloor_task(
        source_floor=task.source_floor,
        target_floor=task.target_floor,
        task_type=task.task_type,
        payload=task.payload,
        priority=task.priority,
        deadline=task.deadline
    )

    return {"task_id": task_id, "status": "created"}


@app.get("/api/v1/smith/tasks/floor/{floor_name}")
async def get_floor_tasks(floor_name: str):
    """Get tasks for specific floor"""
    db = get_db()
    tasks = db.get_interfloor_tasks_by_floor(floor_name)
    return {"floor": floor_name, "tasks": tasks}


@app.get("/api/v1/smith/workflows")
async def list_workflows():
    """List available workflows"""
    return {
        "workflows": [
            {"id": "wf_1", "name": "Daily Backup", "schedule": "0 2 * * *", "status": "active"},
            {"id": "wf_2", "name": "Data Sync", "schedule": "0 */4 * * *", "status": "active"}
        ]
    }


# === Merovingian Floor (Z-4) - System Health ===

@app.get("/api/v1/merovingian/status")
async def merovingian_status():
    """Get Merovingian floor status"""
    return FloorStatus(
        floor="Merovingian",
        z_level=-4,
        status="operational",
        capabilities=["system_health", "diagnostics", "predictive_maintenance"],
        metrics={"health_score": 98, "alerts": 0}
    ).__dict__


@app.get("/api/v1/merovingian/health")
async def system_health():
    """Get system health metrics"""
    return {
        "overall_health": "excellent",
        "score": 98,
        "components": {
            "database": {"status": "healthy", "response_time_ms": 12},
            "event_bus": {"status": "healthy", "messages_per_sec": 45},
            "storage": {"status": "healthy", "available_gb": 150}
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/merovingian/metrics")
async def get_metrics():
    """Get platform metrics"""
    db = get_db()
    event_bus = get_event_bus()
    storage = get_storage()

    return {
        "database": {
            "tables": len(db.get_all_tables()),
            "connection_pool": "healthy"
        },
        "event_bus": event_bus.get_stats(),
        "storage": storage.get_storage_stats(),
        "timestamp": datetime.now().isoformat()
    }


# === Event Bus API ===

@app.post("/api/v1/events/publish")
async def publish_event(event: EventPublish):
    """Publish event to event bus"""
    event_bus = get_event_bus()
    event_bus.publish(event.topic, event.data)
    return {"status": "published", "topic": event.topic}


@app.get("/api/v1/events/recent")
async def get_recent_events(topic: Optional[str] = None, limit: int = 50):
    """Get recent events"""
    event_bus = get_event_bus()
    events = event_bus.get_recent_events(topic=topic, limit=limit)
    return {"events": [e.__dict__ for e in events]}


# === Run server ===

def start_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Start API server"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    print("Starting LightSpeed Platform API Server...")
    print("Documentation: http://localhost:8000/docs")
    start_api_server()
