"""
LightSpeed V0.9.5 - Achilles AI Context System
Conversation tracking and cross-floor workflow automation

Features:
- Track AI conversations across documents
- Build context encyclopedia (Morpheus)
- Automatic task routing to appropriate floors
- Conversation history and relationships
- Cross-floor workflow chains

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
Date: January 3, 2026
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import json


@dataclass
class ConversationContext:
    """AI conversation context"""
    role: str  # 'User', 'Assistant', 'ACHILLES'
    message: str
    document: str
    floor: str
    timestamp: datetime
    metadata: Dict[str, Any]
    related_objects: List[str] = None  # IDs of related ExtractedObjects
    workflow_chain: List[str] = None  # IDs of tasks spawned from this

    def __post_init__(self):
        if self.related_objects is None:
            self.related_objects = []
        if self.workflow_chain is None:
            self.workflow_chain = []


@dataclass
class WorkflowTask:
    """Cross-floor workflow task"""
    task_id: str
    task_type: str  # 'table_constant', 'create_test', 'run_simulation', 'background_job'
    target_floor: str
    action: str
    data: Any
    source_context: Optional[str] = None  # ConversationContext ID
    dependencies: List[str] = None  # Task IDs this depends on
    status: str = 'pending'  # 'pending', 'in_progress', 'completed', 'failed'
    result: Optional[Any] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at is None:
            self.created_at = datetime.now()


class AchillesContextSystem:
    """
    Achilles AI Context & Workflow System.

    Implements the AI integration wishlist:
    - Conversation tracking across floors
    - Document objectification context
    - Cross-floor task automation
    - Encyclopedia building (Morpheus)
    """

    def __init__(self, data_dir: Path):
        """
        Initialize Achilles context system.

        Args:
            data_dir: Directory for storing context database
        """
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.conversations: List[ConversationContext] = []
        self.workflows: Dict[str, WorkflowTask] = {}
        self.context_index: Dict[str, List[str]] = {}  # document -> conversation IDs

        # Load existing context
        self._load_context()

    def track_conversation(self, role: str, message: str, document: str,
                          floor: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Track an AI conversation.

        Args:
            role: Speaker role ('User', 'Assistant', 'ACHILLES')
            message: Conversation message
            document: Source document path
            floor: Z-floor where conversation occurred
            metadata: Additional context data

        Returns:
            Conversation ID
        """
        context = ConversationContext(
            role=role,
            message=message,
            document=document,
            floor=floor,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

        self.conversations.append(context)

        # Index by document
        context_id = f"conv_{len(self.conversations)-1}"
        if document not in self.context_index:
            self.context_index[document] = []
        self.context_index[document].append(context_id)

        # Auto-save
        self._save_context()

        return context_id

    def create_workflow_task(self, task_type: str, target_floor: str,
                            action: str, data: Any,
                            source_context: Optional[str] = None,
                            dependencies: Optional[List[str]] = None) -> str:
        """
        Create a cross-floor workflow task.

        Args:
            task_type: Type of task
            target_floor: Target Z-floor
            action: Action description
            data: Task data
            source_context: Optional conversation context ID
            dependencies: Optional list of task IDs this depends on

        Returns:
            Task ID
        """
        task_id = f"task_{len(self.workflows)}_{int(datetime.now().timestamp())}"

        task = WorkflowTask(
            task_id=task_id,
            task_type=task_type,
            target_floor=target_floor,
            action=action,
            data=data,
            source_context=source_context,
            dependencies=dependencies or []
        )

        self.workflows[task_id] = task

        # Auto-save
        self._save_context()

        return task_id

    def get_document_history(self, document: str) -> List[ConversationContext]:
        """Get all conversations related to a document"""
        context_ids = self.context_index.get(document, [])
        return [self.conversations[int(cid.split('_')[1])] for cid in context_ids
                if int(cid.split('_')[1]) < len(self.conversations)]

    def get_floor_interactions(self, floor: str) -> List[ConversationContext]:
        """Get all AI interactions for a specific floor"""
        return [c for c in self.conversations if c.floor == floor]

    def get_pending_tasks(self, floor: Optional[str] = None) -> List[WorkflowTask]:
        """
        Get pending workflow tasks.

        Args:
            floor: Optional filter by target floor

        Returns:
            List of pending tasks
        """
        tasks = [t for t in self.workflows.values() if t.status == 'pending']

        if floor:
            tasks = [t for t in tasks if t.target_floor == floor]

        return tasks

    def get_task_chain(self, task_id: str) -> List[WorkflowTask]:
        """
        Get full dependency chain for a task.

        Args:
            task_id: Task ID

        Returns:
            List of tasks in dependency order
        """
        chain = []
        visited = set()

        def traverse(tid):
            if tid in visited or tid not in self.workflows:
                return

            visited.add(tid)
            task = self.workflows[tid]

            # Process dependencies first
            for dep_id in task.dependencies:
                traverse(dep_id)

            chain.append(task)

        traverse(task_id)
        return chain

    def update_task_status(self, task_id: str, status: str,
                          result: Optional[Any] = None):
        """
        Update task status.

        Args:
            task_id: Task ID
            status: New status
            result: Optional task result
        """
        if task_id not in self.workflows:
            return

        task = self.workflows[task_id]
        task.status = status
        task.result = result

        if status == 'completed':
            task.completed_at = datetime.now()

        self._save_context()

    def build_encyclopedia_entry(self, topic: str, document: str) -> Dict[str, Any]:
        """
        Build encyclopedia entry from document conversations.

        This aggregates all AI interactions about a topic into a structured entry
        for the Morpheus encyclopedia.

        Args:
            topic: Topic name
            document: Source document

        Returns:
            Encyclopedia entry data
        """
        history = self.get_document_history(document)

        entry = {
            'topic': topic,
            'source_document': document,
            'conversation_count': len(history),
            'first_interaction': history[0].timestamp.isoformat() if history else None,
            'last_interaction': history[-1].timestamp.isoformat() if history else None,
            'interactions': [],
            'extracted_knowledge': [],
            'related_tasks': []
        }

        # Process conversations
        for conv in history:
            entry['interactions'].append({
                'role': conv.role,
                'message': conv.message[:200] + '...' if len(conv.message) > 200 else conv.message,
                'timestamp': conv.timestamp.isoformat(),
                'floor': conv.floor
            })

            # Extract knowledge (simple keyword extraction)
            keywords = self._extract_keywords(conv.message)
            entry['extracted_knowledge'].extend(keywords)

        # Deduplicate knowledge
        entry['extracted_knowledge'] = list(set(entry['extracted_knowledge']))

        # Find related tasks
        for task in self.workflows.values():
            if task.source_context in self.context_index.get(document, []):
                entry['related_tasks'].append({
                    'task_id': task.task_id,
                    'type': task.task_type,
                    'floor': task.target_floor,
                    'status': task.status
                })

        return entry

    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction"""
        # Remove common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are', 'was', 'were'}

        words = text.lower().split()
        keywords = [w.strip('.,!?;:') for w in words
                   if len(w) > 3 and w.lower() not in stopwords]

        return keywords[:10]  # Top 10

    def _save_context(self):
        """Save context to disk"""
        data = {
            'conversations': [
                {
                    **asdict(c),
                    'timestamp': c.timestamp.isoformat()
                }
                for c in self.conversations
            ],
            'workflows': {
                tid: {
                    **asdict(task),
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'completed_at': task.completed_at.isoformat() if task.completed_at else None
                }
                for tid, task in self.workflows.items()
            },
            'context_index': self.context_index
        }

        context_file = self.data_dir / 'achilles_context.json'
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    def _load_context(self):
        """Load context from disk"""
        context_file = self.data_dir / 'achilles_context.json'

        if not context_file.exists():
            return

        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Load conversations
            self.conversations = [
                ConversationContext(
                    role=c['role'],
                    message=c['message'],
                    document=c['document'],
                    floor=c['floor'],
                    timestamp=datetime.fromisoformat(c['timestamp']),
                    metadata=c['metadata'],
                    related_objects=c.get('related_objects', []),
                    workflow_chain=c.get('workflow_chain', [])
                )
                for c in data.get('conversations', [])
            ]

            # Load workflows
            self.workflows = {
                tid: WorkflowTask(
                    task_id=task_data['task_id'],
                    task_type=task_data['task_type'],
                    target_floor=task_data['target_floor'],
                    action=task_data['action'],
                    data=task_data['data'],
                    source_context=task_data.get('source_context'),
                    dependencies=task_data.get('dependencies', []),
                    status=task_data.get('status', 'pending'),
                    result=task_data.get('result'),
                    created_at=datetime.fromisoformat(task_data['created_at']) if task_data.get('created_at') else None,
                    completed_at=datetime.fromisoformat(task_data['completed_at']) if task_data.get('completed_at') else None
                )
                for tid, task_data in data.get('workflows', {}).items()
            }

            # Load index
            self.context_index = data.get('context_index', {})

        except Exception as e:
            print(f"[AchillesContext] Failed to load context: {e}")


# Export
__all__ = ['AchillesContextSystem', 'ConversationContext', 'WorkflowTask']
