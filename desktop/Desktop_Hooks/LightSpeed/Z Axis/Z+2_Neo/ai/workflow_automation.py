"""
LightSpeed V0.9.5 - Cross-Floor Workflow Automation
Automatic task routing and execution across Z-floors

Features:
- Parse documents → distribute objects to floors
- Chain workflows (Constants→Tables→Tests→Simulations)
- Background task execution
- Result aggregation
- Status tracking

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
Date: January 3, 2026
"""

from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import threading
import time

from .document_objectifier import DocumentObjectifier, ExtractedObject, ObjectType
from .achilles_context import AchillesContextSystem, WorkflowTask


class WorkflowAutomation:
    """
    Cross-floor workflow automation system.

    Orchestrates document objectification and task routing:
    1. Parse document with DocumentObjectifier
    2. Route objects to appropriate floors
    3. Create task chains
    4. Execute tasks in background
    5. Track results
    """

    def __init__(self, context_system: AchillesContextSystem):
        """
        Initialize workflow automation.

        Args:
            context_system: Achilles context tracking system
        """
        self.context = context_system
        self.objectifier = DocumentObjectifier()

        # Floor execution callbacks (set by floors on init)
        self.floor_handlers: Dict[str, Callable] = {}

        # Active workflows
        self.active_workflows: Dict[str, threading.Thread] = {}

    def register_floor_handler(self, floor: str, handler: Callable):
        """
        Register a floor task handler.

        Args:
            floor: Floor name (e.g., 'Morpheus', 'TheConstruct')
            handler: Callback function(task: WorkflowTask) -> Any
        """
        self.floor_handlers[floor] = handler

    def process_document(self, document_path: Path,
                        conversation_context: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Process document and create cross-floor workflows.

        Args:
            document_path: Path to document
            conversation_context: Optional conversation ID that triggered this

        Returns:
            Dictionary mapping floor names to created task IDs
        """
        # Parse document
        objects = self.objectifier.parse_document(document_path)

        if not objects:
            return {}

        # Group by floor
        by_floor = self.objectifier.categorize_by_floor(objects)

        # Create tasks for each floor
        created_tasks = {}

        for floor, floor_objects in by_floor.items():
            floor_task_ids = []

            for obj in floor_objects:
                # Generate task
                task_data = self._generate_task_for_object(obj)

                if task_data:
                    # Create workflow task
                    task_id = self.context.create_workflow_task(
                        task_type=task_data['type'],
                        target_floor=floor,
                        action=task_data['action'],
                        data=task_data['data'],
                        source_context=conversation_context
                    )

                    floor_task_ids.append(task_id)

            created_tasks[floor] = floor_task_ids

        # Track in context
        if conversation_context:
            self.context.track_conversation(
                role='ACHILLES',
                message=f"Processed document: {document_path.name}. Created {sum(len(t) for t in created_tasks.values())} tasks across {len(created_tasks)} floors.",
                document=str(document_path),
                floor='ACHILLES',
                metadata={'created_tasks': created_tasks}
            )

        return created_tasks

    def execute_task_chain(self, task_id: str, async_execution: bool = True):
        """
        Execute a task and its dependency chain.

        Args:
            task_id: Root task ID
            async_execution: Execute in background thread (default True)
        """
        if async_execution:
            thread = threading.Thread(
                target=self._execute_task_chain_sync,
                args=(task_id,),
                daemon=True
            )
            thread.start()
            self.active_workflows[task_id] = thread
        else:
            self._execute_task_chain_sync(task_id)

    def _execute_task_chain_sync(self, task_id: str):
        """Execute task chain synchronously"""
        chain = self.context.get_task_chain(task_id)

        for task in chain:
            # Skip already completed
            if task.status == 'completed':
                continue

            # Update status
            self.context.update_task_status(task.task_id, 'in_progress')

            try:
                # Execute task via floor handler
                handler = self.floor_handlers.get(task.target_floor)

                if handler:
                    result = handler(task)
                    self.context.update_task_status(task.task_id, 'completed', result)
                else:
                    # No handler registered
                    self.context.update_task_status(
                        task.task_id, 'failed',
                        f"No handler registered for floor: {task.target_floor}"
                    )

            except Exception as e:
                self.context.update_task_status(task.task_id, 'failed', str(e))

        # Clean up
        if task_id in self.active_workflows:
            del self.active_workflows[task_id]

    def create_chained_workflow(self, document_path: Path,
                               workflow_type: str = 'full') -> List[str]:
        """
        Create a chained workflow from document.

        Workflow types:
        - 'full': Extract all objects → route to all floors
        - 'constants_to_tests': Extract constants → create tests
        - 'tests_to_simulations': Extract tests → run simulations
        - 'tasks_to_jobs': Extract tasks → create background jobs

        Args:
            document_path: Source document
            workflow_type: Type of workflow chain

        Returns:
            List of created task IDs
        """
        objects = self.objectifier.parse_document(document_path)

        if workflow_type == 'full':
            # Standard processing
            created_tasks = self.process_document(document_path)
            return [tid for tids in created_tasks.values() for tid in tids]

        elif workflow_type == 'constants_to_tests':
            # Extract constants → create tests for them
            constants = [o for o in objects if o.obj_type == ObjectType.CONSTANT]

            task_ids = []
            for const in constants:
                # Create constant table task (Morpheus)
                table_task_id = self.context.create_workflow_task(
                    task_type='table_constant',
                    target_floor='Morpheus',
                    action='Add constant to encyclopedia',
                    data={'constant': const.content, 'context': const.context}
                )

                # Create test generation task (TheConstruct) that depends on table task
                test_task_id = self.context.create_workflow_task(
                    task_type='generate_test',
                    target_floor='TheConstruct',
                    action='Generate test for constant',
                    data={'constant': const.content, 'source': const.source_file},
                    dependencies=[table_task_id]
                )

                task_ids.extend([table_task_id, test_task_id])

            return task_ids

        elif workflow_type == 'tests_to_simulations':
            # Extract tests → run simulations
            tests = [o for o in objects if o.obj_type == ObjectType.TEST]

            task_ids = []
            for test in tests:
                sim_task_id = self.context.create_workflow_task(
                    task_type='run_simulation',
                    target_floor='TheConstruct',
                    action='Run simulation from test',
                    data={'test': test.content, 'context': test.context}
                )
                task_ids.append(sim_task_id)

            return task_ids

        elif workflow_type == 'tasks_to_jobs':
            # Extract tasks → create background jobs
            tasks = [o for o in objects if o.obj_type == ObjectType.TASK]

            task_ids = []
            for task_obj in tasks:
                job_task_id = self.context.create_workflow_task(
                    task_type='background_job',
                    target_floor='Smith',
                    action='Create background job',
                    data={'task': task_obj.content, 'source': task_obj.source_file}
                )
                task_ids.append(job_task_id)

            return task_ids

        return []

    def get_workflow_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status of a workflow.

        Args:
            task_id: Task ID

        Returns:
            Status dictionary with chain info
        """
        chain = self.context.get_task_chain(task_id)

        status = {
            'task_id': task_id,
            'total_tasks': len(chain),
            'completed': sum(1 for t in chain if t.status == 'completed'),
            'in_progress': sum(1 for t in chain if t.status == 'in_progress'),
            'pending': sum(1 for t in chain if t.status == 'pending'),
            'failed': sum(1 for t in chain if t.status == 'failed'),
            'is_active': task_id in self.active_workflows,
            'tasks': [
                {
                    'task_id': t.task_id,
                    'type': t.task_type,
                    'floor': t.target_floor,
                    'status': t.status,
                    'action': t.action
                }
                for t in chain
            ]
        }

        return status

    def _generate_task_for_object(self, obj: ExtractedObject) -> Optional[Dict[str, Any]]:
        """Generate task data for an extracted object"""

        if obj.obj_type == ObjectType.CONSTANT:
            return {
                'type': 'table_constant',
                'action': 'Add to constants table',
                'data': {
                    'content': obj.content,
                    'context': obj.context,
                    'source': obj.source_file,
                    'line': obj.line_number
                }
            }

        elif obj.obj_type == ObjectType.TEST:
            return {
                'type': 'create_test',
                'action': 'Create test scenario',
                'data': {
                    'content': obj.content,
                    'context': obj.context,
                    'source': obj.source_file,
                    'line': obj.line_number
                }
            }

        elif obj.obj_type == ObjectType.SIMULATION:
            return {
                'type': 'run_simulation',
                'action': 'Execute simulation',
                'data': {
                    'content': obj.content,
                    'context': obj.context,
                    'source': obj.source_file
                }
            }

        elif obj.obj_type == ObjectType.TASK:
            return {
                'type': 'background_job',
                'action': 'Create background job',
                'data': {
                    'content': obj.content,
                    'context': obj.context,
                    'source': obj.source_file,
                    'line': obj.line_number
                }
            }

        elif obj.obj_type == ObjectType.CONVERSATION:
            return {
                'type': 'store_context',
                'action': 'Store AI conversation context',
                'data': {
                    'content': obj.content,
                    'context': obj.context,
                    'source': obj.source_file
                }
            }

        elif obj.obj_type == ObjectType.EQUATION:
            return {
                'type': 'table_equation',
                'action': 'Add equation to encyclopedia',
                'data': {
                    'content': obj.content,
                    'context': obj.context,
                    'source': obj.source_file
                }
            }

        return None


# Export
__all__ = ['WorkflowAutomation']
