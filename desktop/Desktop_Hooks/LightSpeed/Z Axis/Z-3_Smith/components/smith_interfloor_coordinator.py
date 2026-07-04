#!/usr/bin/env python
"""
Smith Inter-Floor Coordinator
Manages tasks and coordination across ALL 8 Z-floors

Smith is the central automation hub that:
1. Receives tasks FROM all floors (Oracle, Morpheus, Trinity, Neo, etc.)
2. Routes tasks TO appropriate floors
3. Coordinates dependencies between floors
4. Uses Neo for AI-assisted task planning when smart floor systems need guidance
5. Ensures all floors work together harmoniously

Floor Communication Matrix:
- Oracle -> Smith -> All Floors (file distribution)
- Morpheus -> Smith -> Oracle (knowledge archival)
- TheConstruct -> Smith -> Oracle (simulation results)
- Neo -> Smith -> All Floors (AI assistance sign-off)
- Trinity -> Smith -> All Floors (UI updates)
- Architect -> Smith -> All Floors (task assignments)
- Merovingian -> Smith -> All Floors (system health monitoring)
- Smith -> Smith (self-optimization)

Author: Romer Industries / EMASSC
Version: 0.9.5
Date: December 31, 2025
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class FloorID(Enum):
    """Z-Floor identifiers"""
    TRINITY = 'Z+3_Trinity'
    NEO = 'Z+2_Neo'
    ARCHITECT = 'Z+1_Architect'
    CONSTRUCT = 'Z0_TheConstruct'
    MORPHEUS = 'Z-1_Morpheus'
    ORACLE = 'Z-2_Oracle'
    SMITH = 'Z-3_Smith'
    MEROVINGIAN = 'Z-4_Merovingian'


@dataclass
class InterFloorTask:
    """Task that spans multiple floors"""
    task_id: int
    task_type: str
    source_floor: str
    target_floors: List[str]
    parameters: Dict[str, Any]
    priority: int
    dependencies: List[int]
    status: str
    created_at: str
    requires_neo_signoff: bool = False
    neo_approval: Optional[str] = None
    floor_results: Dict[str, Any] = None


class SmithInterFloorCoordinator:
    """
    Smith Inter-Floor Coordinator

    Central hub for all cross-floor communication and task coordination
    """

    def __init__(self, db=None, event_bus=None, logger=None, smith_queue=None):
        """Initialize inter-floor coordinator"""
        self.db = db
        self.event_bus = event_bus
        self.logger = logger
        self.smith_queue = smith_queue

        # Inter-floor task registry
        self.interfloor_tasks = {}
        self.task_counter = 0

        # Floor capabilities (what each floor can do)
        self.floor_capabilities = {
            FloorID.TRINITY.value: ['ui', 'visualization', 'theme', 'frontend', 'user_interaction'],
            FloorID.NEO.value: ['ai', 'ml', 'ollama', 'gpt', 'decision', 'analysis', 'signoff'],
            FloorID.ARCHITECT.value: ['planning', 'tasks', 'missions', 'goals', 'scheduling'],
            FloorID.CONSTRUCT.value: ['physics', 'simulation', '3d', 'visualization', 'testing'],
            FloorID.MORPHEUS.value: ['knowledge', 'learning', 'analysis', 'code_review', 'indexing'],
            FloorID.ORACLE.value: ['archival', 'vault', 'documents', 'ip', 'legal', 'storage'],
            FloorID.SMITH.value: ['automation', 'workflows', 'jobs', 'coordination', 'sop'],
            FloorID.MEROVINGIAN.value: ['system', 'health', 'diagnostics', 'monitoring', 'optimization']
        }

        # Communication channels (event bus topics)
        self.comm_channels = {}
        self._setup_communication_channels()

        # Task routing rules
        self.routing_rules = self._define_routing_rules()

        if self.logger:
            self.logger.info("[SmithCoordinator] Inter-Floor Coordinator initialized (8 floors)")

    def _setup_communication_channels(self):
        """Setup event bus communication channels for all floors"""
        for floor in FloorID:
            floor_id = floor.value

            # Inbound channel (tasks TO this floor)
            self.comm_channels[f'to_{floor_id}'] = f'smith.to.{floor_id.lower()}'

            # Outbound channel (tasks FROM this floor)
            self.comm_channels[f'from_{floor_id}'] = f'smith.from.{floor_id.lower()}'

            # Subscribe to outbound if event bus available
            if self.event_bus:
                self.event_bus.subscribe(
                    self.comm_channels[f'from_{floor_id}'],
                    lambda event, floor=floor_id: self._handle_floor_task(event, floor)
                )

    def _define_routing_rules(self) -> Dict[str, List[str]]:
        """
        Define routing rules for common task types

        Returns:
            Dictionary of task_type -> list of target floors
        """
        return {
            # File ingestion: Oracle -> Morpheus (index) + target floors
            'file_ingestion': [FloorID.ORACLE.value, FloorID.MORPHEUS.value],

            # Code analysis: Morpheus -> Oracle (archive) + Neo (AI review)
            'code_analysis': [FloorID.MORPHEUS.value, FloorID.ORACLE.value, FloorID.NEO.value],

            # Simulation: TheConstruct -> Oracle (results) + Morpheus (knowledge)
            'simulation': [FloorID.CONSTRUCT.value, FloorID.ORACLE.value, FloorID.MORPHEUS.value],

            # UI update: Trinity -> All (UI components on all floors)
            'ui_update': [floor.value for floor in FloorID],

            # System health: Merovingian -> Smith (auto-healing) + All (notifications)
            'system_health': [FloorID.MEROVINGIAN.value, FloorID.SMITH.value],

            # Task planning: Architect -> All (distribute tasks)
            'task_planning': [FloorID.ARCHITECT.value],

            # AI decision: Neo -> requesting floor
            'ai_decision': [FloorID.NEO.value],

            # Knowledge update: Morpheus -> Oracle (archive) + All (index updates)
            'knowledge_update': [FloorID.MORPHEUS.value, FloorID.ORACLE.value],

            # Workflow execution: Smith -> target floors (dynamic)
            'workflow': [FloorID.SMITH.value]
        }

    def submit_task(self, task_type: str, source_floor: str,
                   parameters: Dict[str, Any], priority: int = 3,
                   target_floors: List[str] = None,
                   requires_neo_signoff: bool = False) -> int:
        """
        Submit inter-floor task

        Parameters:
            task_type: Type of task
            source_floor: Originating floor
            parameters: Task parameters
            priority: Priority (1=critical, 5=low)
            target_floors: List of target floors (None = auto-route)
            requires_neo_signoff: Whether task needs Neo AI approval

        Returns:
            Task ID
        """
        self.task_counter += 1
        task_id = self.task_counter

        # Auto-route if no targets specified
        if target_floors is None:
            target_floors = self._auto_route(task_type, source_floor, parameters)

        # Create task
        task = InterFloorTask(
            task_id=task_id,
            task_type=task_type,
            source_floor=source_floor,
            target_floors=target_floors,
            parameters=parameters,
            priority=priority,
            dependencies=[],
            status='pending',
            created_at=datetime.now().isoformat(),
            requires_neo_signoff=requires_neo_signoff,
            floor_results={}
        )

        self.interfloor_tasks[task_id] = task

        # Emit to event bus
        if self.event_bus:
            self.event_bus.publish('smith.interfloor.task_submitted', asdict(task))

        if self.logger:
            self.logger.info(f"[SmithCoordinator] Task {task_id} submitted: {source_floor} -> {target_floors}")

        # Process task
        self._process_interfloor_task(task)

        return task_id

    def _auto_route(self, task_type: str, source_floor: str,
                   parameters: Dict[str, Any]) -> List[str]:
        """
        Auto-route task to appropriate floors based on task type and parameters

        Parameters:
            task_type: Type of task
            source_floor: Originating floor
            parameters: Task parameters

        Returns:
            List of target floor IDs
        """
        # Check routing rules
        if task_type in self.routing_rules:
            return self.routing_rules[task_type].copy()

        # Analyze parameters for keywords
        param_str = json.dumps(parameters).lower()
        target_floors = []

        for floor, capabilities in self.floor_capabilities.items():
            for capability in capabilities:
                if capability in param_str or capability in task_type.lower():
                    if floor not in target_floors and floor != source_floor:
                        target_floors.append(floor)

        # If no matches, route to Morpheus (knowledge base) for analysis
        if not target_floors:
            target_floors = [FloorID.MORPHEUS.value]

        return target_floors

    def _process_interfloor_task(self, task: InterFloorTask):
        """Process inter-floor task by distributing to target floors"""

        # Check if Neo signoff required
        if task.requires_neo_signoff:
            self._request_neo_signoff(task)
            return

        # Distribute to target floors
        for target_floor in task.target_floors:
            # Create floor-specific sub-task in Smith queue
            if self.smith_queue:
                sub_task_id = self.smith_queue.add_task(
                    task_type=f"{task.task_type}_for_{target_floor}",
                    parameters={
                        **task.parameters,
                        'interfloor_task_id': task.task_id,
                        'source_floor': task.source_floor
                    },
                    source_floor=target_floor,
                    priority=task.priority
                )

                if self.logger:
                    self.logger.info(f"[SmithCoordinator] Sub-task {sub_task_id} -> {target_floor}")

            # Emit to floor-specific channel
            if self.event_bus:
                channel = self.comm_channels[f'to_{target_floor}']
                self.event_bus.publish(channel, {
                    'interfloor_task_id': task.task_id,
                    'task_type': task.task_type,
                    'source_floor': task.source_floor,
                    'parameters': task.parameters,
                    'priority': task.priority
                })

        task.status = 'distributed'

    def _request_neo_signoff(self, task: InterFloorTask):
        """Request Neo AI signoff for task"""
        if self.logger:
            self.logger.info(f"[SmithCoordinator] Requesting Neo signoff for task {task.task_id}")

        # Send to Neo for AI analysis
        if self.event_bus:
            self.event_bus.publish('neo.signoff_request', {
                'task_id': task.task_id,
                'task_type': task.task_type,
                'source_floor': task.source_floor,
                'parameters': task.parameters,
                'callback': 'smith.neo_signoff_response'
            })

        task.status = 'awaiting_neo_signoff'

    def handle_neo_signoff(self, task_id: int, approval: str, reasoning: str = None):
        """
        Handle Neo AI signoff response

        Parameters:
            task_id: Task ID
            approval: 'approved' or 'rejected'
            reasoning: AI reasoning for decision
        """
        if task_id not in self.interfloor_tasks:
            return

        task = self.interfloor_tasks[task_id]
        task.neo_approval = approval

        if self.logger:
            self.logger.info(f"[SmithCoordinator] Neo signoff for task {task_id}: {approval}")

        if approval == 'approved':
            # Proceed with task distribution
            self._process_interfloor_task(task)
        else:
            # Reject task
            task.status = 'rejected_by_neo'
            if self.event_bus:
                self.event_bus.publish('smith.task_rejected', {
                    'task_id': task_id,
                    'reason': reasoning or 'Neo AI rejected'
                })

    def report_floor_result(self, task_id: int, floor: str, result: Dict[str, Any]):
        """
        Report floor task completion result

        Parameters:
            task_id: Inter-floor task ID
            floor: Floor reporting result
            result: Result data
        """
        if task_id not in self.interfloor_tasks:
            return

        task = self.interfloor_tasks[task_id]

        # Store result
        task.floor_results[floor] = {
            'result': result,
            'completed_at': datetime.now().isoformat()
        }

        if self.logger:
            self.logger.info(f"[SmithCoordinator] Floor result: {floor} -> task {task_id}")

        # Check if all floors completed
        if len(task.floor_results) >= len(task.target_floors):
            self._complete_interfloor_task(task)

    def _complete_interfloor_task(self, task: InterFloorTask):
        """Complete inter-floor task after all floors finish"""
        task.status = 'completed'

        # Aggregate results
        aggregated_result = {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'source_floor': task.source_floor,
            'target_floors': task.target_floors,
            'floor_results': task.floor_results,
            'completed_at': datetime.now().isoformat()
        }

        # Emit completion event
        if self.event_bus:
            self.event_bus.publish('smith.interfloor.task_completed', aggregated_result)

            # Notify source floor
            source_channel = self.comm_channels[f'to_{task.source_floor}']
            self.event_bus.publish(source_channel, {
                'type': 'task_completion',
                'task_id': task.task_id,
                'results': aggregated_result
            })

        if self.logger:
            self.logger.info(f"[SmithCoordinator] Task {task.task_id} completed across {len(task.target_floors)} floors")

    def _handle_floor_task(self, event: Dict[str, Any], floor: str):
        """Handle task submission from floor"""
        # Extract task info
        task_type = event.get('task_type')
        parameters = event.get('parameters', {})
        priority = event.get('priority', 3)
        target_floors = event.get('target_floors')
        requires_neo = event.get('requires_neo_signoff', False)

        # Submit inter-floor task
        task_id = self.submit_task(
            task_type=task_type,
            source_floor=floor,
            parameters=parameters,
            priority=priority,
            target_floors=target_floors,
            requires_neo_signoff=requires_neo
        )

        return task_id

    def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get status of inter-floor task"""
        if task_id not in self.interfloor_tasks:
            return None

        task = self.interfloor_tasks[task_id]
        return asdict(task)

    def get_floor_activity(self, floor: str) -> Dict[str, Any]:
        """Get activity summary for specific floor"""
        tasks_from_floor = [
            task for task in self.interfloor_tasks.values()
            if task.source_floor == floor
        ]

        tasks_to_floor = [
            task for task in self.interfloor_tasks.values()
            if floor in task.target_floors
        ]

        return {
            'floor': floor,
            'tasks_submitted': len(tasks_from_floor),
            'tasks_received': len(tasks_to_floor),
            'active_tasks': len([t for t in tasks_to_floor if t.status in ['pending', 'distributed']]),
            'completed_tasks': len([t for t in tasks_to_floor if t.status == 'completed'])
        }

    def get_system_overview(self) -> Dict[str, Any]:
        """Get system-wide coordination overview"""
        overview = {
            'total_tasks': len(self.interfloor_tasks),
            'active_tasks': len([t for t in self.interfloor_tasks.values()
                                if t.status in ['pending', 'distributed', 'awaiting_neo_signoff']]),
            'completed_tasks': len([t for t in self.interfloor_tasks.values()
                                   if t.status == 'completed']),
            'floor_activity': {}
        }

        # Per-floor activity
        for floor in FloorID:
            overview['floor_activity'][floor.value] = self.get_floor_activity(floor.value)

        return overview


# Example usage scenarios
def example_usage():
    """Example usage of inter-floor coordinator"""

    coordinator = SmithInterFloorCoordinator()

    print("[Example 1] Oracle file ingestion -> Morpheus + target floors")
    task1 = coordinator.submit_task(
        task_type='file_ingestion',
        source_floor=FloorID.ORACLE.value,
        parameters={
            'vault_id': 123,
            'file_type': 'research_paper',
            'keywords': ['physics', 'raphael']
        },
        priority=2
    )
    print(f"Task {task1} submitted")

    print("\n[Example 2] TheConstruct simulation -> Oracle (archive) + Morpheus (knowledge)")
    task2 = coordinator.submit_task(
        task_type='simulation',
        source_floor=FloorID.CONSTRUCT.value,
        parameters={
            'simulation_type': 'orbital',
            'results_path': '/path/to/results'
        },
        priority=2
    )
    print(f"Task {task2} submitted")

    print("\n[Example 3] Architect task planning -> All floors (requires Neo signoff)")
    task3 = coordinator.submit_task(
        task_type='task_planning',
        source_floor=FloorID.ARCHITECT.value,
        parameters={
            'mission': 'Complete V1.0',
            'deadline': '2025-12-31'
        },
        priority=1,
        target_floors=[floor.value for floor in FloorID],
        requires_neo_signoff=True
    )
    print(f"Task {task3} submitted (awaiting Neo signoff)")

    print("\n[System Overview]")
    print(json.dumps(coordinator.get_system_overview(), indent=2))


if __name__ == '__main__':
    example_usage()
