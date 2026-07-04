"""
Smart Floor Framework - Intelligent capabilities for all Z-floors

Provides each floor with:
- Automated dataset generation based on floor function
- Phased testing with goal tracking
- Self-documenting behavior
- Performance metrics
- Smart task execution

This framework enables floors to autonomously:
- Generate test data appropriate to their domain
- Execute phased testing based on goals
- Track progress toward objectives
- Create reports and datasets
- Learn and adapt behavior

Author: LightSpeed Team
Date: December 19, 2025
Version: 0.9.5
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import json
import os
from pathlib import Path


# ============================================================================
# Enums and Data Classes
# ============================================================================

class FloorDomain(Enum):
    """Z-floor functional domains"""
    SYSTEM_CORE = "Z-4_Merovingian"      # Health, diagnostics, core operations
    AUTOMATION = "Z-3_Smith"              # Jobs, workflows, scheduling
    ARCHIVES = "Z-2_Oracle"               # Storage, IP vault, archives
    KNOWLEDGE = "Z-1_Morpheus"            # Documentation, learning
    PHYSICS = "Z0_TheConstruct"           # Simulations, rendering
    PLANNING = "Z+1_Architect"            # Goals, missions, tasks
    AI = "Z+2_Neo"                        # AI, LLM, intelligence
    UI = "Z+3_Trinity"                    # Interface, visualization
    INIT = "Z+3_Trinity"                  # Initialization (consolidated into Trinity)


class TestPhase(Enum):
    """Testing phases"""
    UNIT = "unit"                         # Individual component tests
    INTEGRATION = "integration"           # Cross-component tests
    SYSTEM = "system"                     # Full system tests
    ACCEPTANCE = "acceptance"             # User acceptance tests
    PERFORMANCE = "performance"           # Performance benchmarks
    REGRESSION = "regression"             # Regression tests


class GoalStatus(Enum):
    """Goal tracking statuses"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass
class Goal:
    """Trackable goal for a floor"""
    id: str
    title: str
    description: str
    floor: FloorDomain
    target_date: datetime
    status: GoalStatus = GoalStatus.PENDING
    progress: float = 0.0  # 0-100%
    metrics: Dict[str, Any] = field(default_factory=dict)
    tests: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def update_progress(self, value: float):
        """Update progress and change status if needed"""
        self.progress = max(0.0, min(100.0, value))
        if self.progress >= 100.0 and self.status != GoalStatus.COMPLETED:
            self.status = GoalStatus.COMPLETED
        elif self.progress > 0 and self.status == GoalStatus.PENDING:
            self.status = GoalStatus.IN_PROGRESS


@dataclass
class TestCase:
    """Test case with phasing"""
    id: str
    name: str
    phase: TestPhase
    floor: FloorDomain
    function: Callable
    expected_result: Any
    actual_result: Any = None
    passed: bool = False
    execution_time: float = 0.0
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class Dataset:
    """Generated dataset for floor"""
    id: str
    name: str
    floor: FloorDomain
    data_type: str  # 'test', 'production', 'simulation', 'benchmark'
    records: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def save(self, directory: Optional[str] = None):
        """
        Save dataset to JSON file.

        V1: avoid writing to root-level `data/` folders; keep outputs floor-native.
        Default location is under Merovingian data: `Z Axis/Z-4_Merovingian/data/generated/`.
        """
        if directory is None:
            try:
                from core.config.paths import MEROVINGIAN_DATA  # type: ignore
                directory = str(Path(MEROVINGIAN_DATA) / "generated")
            except Exception:
                directory = str(Path.cwd() / "Z Axis" / "Z-4_Merovingian" / "data" / "generated")

        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, f"{self.id}_{self.name}.json")

        with open(filepath, 'w') as f:
            json.dump({
                'id': self.id,
                'name': self.name,
                'floor': self.floor.value,
                'data_type': self.data_type,
                'records': self.records,
                'metadata': self.metadata,
                'created_at': self.created_at.isoformat()
            }, f, indent=2)

        return filepath


# ============================================================================
# Abstract Smart Floor Interface
# ============================================================================

class ISmartFloor(ABC):
    """Interface that all smart floors must implement"""

    @abstractmethod
    def get_floor_domain(self) -> FloorDomain:
        """Return the floor's functional domain"""
        pass

    @abstractmethod
    def generate_test_dataset(self, size: int = 100) -> Dataset:
        """Generate test data appropriate for this floor's domain"""
        pass

    @abstractmethod
    def create_floor_tests(self) -> List[TestCase]:
        """Create test cases for this floor's functionality"""
        pass

    @abstractmethod
    def define_floor_goals(self) -> List[Goal]:
        """Define goals for this floor"""
        pass

    @abstractmethod
    def execute_smart_task(self, task_name: str, **kwargs) -> Any:
        """Execute a smart task specific to this floor"""
        pass


# ============================================================================
# Smart Floor Manager
# ============================================================================

class SmartFloorManager:
    """Central manager for all smart floor capabilities"""

    def __init__(self):
        self.floors: Dict[FloorDomain, ISmartFloor] = {}
        self.goals: Dict[str, Goal] = {}
        self.tests: Dict[str, TestCase] = {}
        self.datasets: Dict[str, Dataset] = {}
        self.test_results: List[Dict[str, Any]] = []

    def register_floor(self, floor: ISmartFloor):
        """Register a smart floor"""
        domain = floor.get_floor_domain()
        self.floors[domain] = floor
        print(f"[SmartFloor] Registered {domain.value}")

        # Initialize floor goals and tests
        self._initialize_floor(floor)

    def _initialize_floor(self, floor: ISmartFloor):
        """Initialize floor with goals and tests"""
        # Register goals
        for goal in floor.define_floor_goals():
            self.goals[goal.id] = goal

        # Register tests
        for test in floor.create_floor_tests():
            self.tests[test.id] = test

    def generate_datasets_for_all_floors(self, size: int = 100) -> Dict[FloorDomain, Dataset]:
        """Generate test datasets for all registered floors"""
        datasets = {}

        for domain, floor in self.floors.items():
            print(f"[SmartFloor] Generating dataset for {domain.value}...")
            dataset = floor.generate_test_dataset(size)
            datasets[domain] = dataset
            self.datasets[dataset.id] = dataset

            # Save dataset
            filepath = dataset.save()
            print(f"  → Saved: {filepath}")

        return datasets

    def run_phased_tests(self, phase: TestPhase) -> Dict[str, Any]:
        """Run all tests for a specific phase"""
        print(f"\n[SmartFloor] Running {phase.value} tests...")

        phase_tests = [t for t in self.tests.values() if t.phase == phase]
        results = {
            'phase': phase.value,
            'total': len(phase_tests),
            'passed': 0,
            'failed': 0,
            'errors': [],
            'execution_time': 0.0,
            'timestamp': datetime.now().isoformat()
        }

        import time
        for test in phase_tests:
            start_time = time.perf_counter()

            try:
                test.actual_result = test.function()
                test.passed = (test.actual_result == test.expected_result)

                if test.passed:
                    results['passed'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'test': test.name,
                        'expected': test.expected_result,
                        'actual': test.actual_result
                    })

            except Exception as e:
                test.passed = False
                test.error_message = str(e)
                results['failed'] += 1
                results['errors'].append({
                    'test': test.name,
                    'error': str(e)
                })

            test.execution_time = time.perf_counter() - start_time
            test.executed_at = datetime.now()
            results['execution_time'] += test.execution_time

            status = "✓" if test.passed else "✗"
            print(f"  {status} {test.name} ({test.execution_time:.3f}s)")

        self.test_results.append(results)

        print(f"\n[SmartFloor] Phase complete: {results['passed']}/{results['total']} passed")
        return results

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test phases sequentially"""
        all_results = {
            'phases': {},
            'total_passed': 0,
            'total_failed': 0,
            'total_time': 0.0,
            'timestamp': datetime.now().isoformat()
        }

        for phase in TestPhase:
            results = self.run_phased_tests(phase)
            all_results['phases'][phase.value] = results
            all_results['total_passed'] += results['passed']
            all_results['total_failed'] += results['failed']
            all_results['total_time'] += results['execution_time']

        return all_results

    def update_goal_progress(self, goal_id: str, progress: float):
        """Update progress for a goal"""
        if goal_id in self.goals:
            goal = self.goals[goal_id]
            goal.update_progress(progress)
            print(f"[SmartFloor] Goal '{goal.title}': {progress:.1f}% ({goal.status.value})")

    def get_floor_status(self, domain: FloorDomain) -> Dict[str, Any]:
        """Get status report for a floor"""
        floor_goals = [g for g in self.goals.values() if g.floor == domain]
        floor_tests = [t for t in self.tests.values() if t.floor == domain]

        return {
            'domain': domain.value,
            'registered': domain in self.floors,
            'goals': {
                'total': len(floor_goals),
                'completed': len([g for g in floor_goals if g.status == GoalStatus.COMPLETED]),
                'in_progress': len([g for g in floor_goals if g.status == GoalStatus.IN_PROGRESS]),
                'avg_progress': sum(g.progress for g in floor_goals) / len(floor_goals) if floor_goals else 0
            },
            'tests': {
                'total': len(floor_tests),
                'passed': len([t for t in floor_tests if t.passed]),
                'failed': len([t for t in floor_tests if not t.passed and t.executed_at]),
                'pending': len([t for t in floor_tests if not t.executed_at])
            }
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'floors_registered': len(self.floors),
            'total_goals': len(self.goals),
            'total_tests': len(self.tests),
            'datasets_generated': len(self.datasets),
            'floors': {domain.value: self.get_floor_status(domain)
                      for domain in self.floors.keys()},
            'timestamp': datetime.now().isoformat()
        }

    def execute_smart_task(self, domain: FloorDomain, task_name: str, **kwargs) -> Any:
        """Execute a smart task on a specific floor"""
        if domain not in self.floors:
            raise ValueError(f"Floor {domain.value} not registered")

        floor = self.floors[domain]
        return floor.execute_smart_task(task_name, **kwargs)

    def save_report(self, filepath: str = "data/smart_floor_report.json"):
        """Save comprehensive status report"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        report = {
            'system_status': self.get_system_status(),
            'test_results': self.test_results,
            'goals': {gid: {
                'title': g.title,
                'floor': g.floor.value,
                'status': g.status.value,
                'progress': g.progress,
                'target_date': g.target_date.isoformat()
            } for gid, g in self.goals.items()},
            'generated': datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"[SmartFloor] Report saved: {filepath}")
        return filepath


# ============================================================================
# Example Smart Floor Implementation
# ============================================================================

class MerovingianSmartFloor(ISmartFloor):
    """Smart floor implementation for Merovingian (System Core)"""

    def get_floor_domain(self) -> FloorDomain:
        return FloorDomain.SYSTEM_CORE

    def generate_test_dataset(self, size: int = 100) -> Dataset:
        """Generate system metrics test data"""
        import random

        records = []
        for i in range(size):
            records.append({
                'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(),
                'cpu_percent': random.uniform(10, 90),
                'memory_percent': random.uniform(30, 85),
                'disk_percent': random.uniform(20, 70),
                'health_score': random.uniform(70, 100),
                'incidents': random.randint(0, 3)
            })

        return Dataset(
            id=f"merovingian_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="system_metrics_test_data",
            floor=FloorDomain.SYSTEM_CORE,
            data_type="test",
            records=records,
            metadata={'generator': 'MerovingianSmartFloor', 'size': size}
        )

    def create_floor_tests(self) -> List[TestCase]:
        """Create system core tests"""
        tests = []

        # Unit test
        tests.append(TestCase(
            id="merovingian_health_check",
            name="Health Monitor - Calculate Score",
            phase=TestPhase.UNIT,
            floor=FloorDomain.SYSTEM_CORE,
            function=lambda: 85.5,  # Mock health check
            expected_result=85.5
        ))

        # Integration test
        tests.append(TestCase(
            id="merovingian_auto_heal",
            name="Auto-Healing - Trigger Remediation",
            phase=TestPhase.INTEGRATION,
            floor=FloorDomain.SYSTEM_CORE,
            function=lambda: True,  # Mock auto-heal
            expected_result=True
        ))

        return tests

    def define_floor_goals(self) -> List[Goal]:
        """Define system core goals"""
        goals = []

        goals.append(Goal(
            id="merovingian_goal_1",
            title="Maintain 99.9% System Uptime",
            description="Keep system health score above 95% at all times",
            floor=FloorDomain.SYSTEM_CORE,
            target_date=datetime.now() + timedelta(days=30),
            metrics={'uptime_target': 99.9, 'health_threshold': 95.0}
        ))

        goals.append(Goal(
            id="merovingian_goal_2",
            title="Zero Critical Incidents",
            description="Prevent all critical system failures through auto-healing",
            floor=FloorDomain.SYSTEM_CORE,
            target_date=datetime.now() + timedelta(days=7),
            metrics={'critical_incidents_target': 0}
        ))

        return goals

    def execute_smart_task(self, task_name: str, **kwargs) -> Any:
        """Execute Merovingian smart tasks"""
        if task_name == "health_check":
            return {"status": "healthy", "score": 95.5}
        elif task_name == "trigger_healing":
            return {"healing_triggered": True, "action": "memory_cleanup"}
        elif task_name == "performance_report":
            return {"cpu": 45.2, "memory": 62.1, "disk": 38.9}
        else:
            raise ValueError(f"Unknown task: {task_name}")


# ============================================================================
# Global Smart Floor Manager Instance
# ============================================================================

_smart_floor_manager: Optional[SmartFloorManager] = None

def get_smart_floor_manager() -> SmartFloorManager:
    """Get or create global smart floor manager"""
    global _smart_floor_manager
    if _smart_floor_manager is None:
        _smart_floor_manager = SmartFloorManager()
    return _smart_floor_manager


# ============================================================================
# Example Usage and Demo
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SMART FLOOR FRAMEWORK DEMO")
    print("=" * 60)

    # Create manager
    manager = SmartFloorManager()

    # Register example floor
    merovingian = MerovingianSmartFloor()
    manager.register_floor(merovingian)

    # Generate datasets
    print("\n" + "=" * 60)
    print("GENERATING DATASETS")
    print("=" * 60)
    datasets = manager.generate_datasets_for_all_floors(size=50)

    # Run tests
    print("\n" + "=" * 60)
    print("RUNNING PHASED TESTS")
    print("=" * 60)
    test_results = manager.run_all_tests()

    # Update goals
    print("\n" + "=" * 60)
    print("UPDATING GOALS")
    print("=" * 60)
    manager.update_goal_progress("merovingian_goal_1", 45.0)
    manager.update_goal_progress("merovingian_goal_2", 78.5)

    # Execute smart task
    print("\n" + "=" * 60)
    print("EXECUTING SMART TASKS")
    print("=" * 60)
    result = manager.execute_smart_task(
        FloorDomain.SYSTEM_CORE,
        "health_check"
    )
    print(f"Health Check Result: {result}")

    # Get status
    print("\n" + "=" * 60)
    print("SYSTEM STATUS")
    print("=" * 60)
    status = manager.get_system_status()
    print(json.dumps(status, indent=2))

    # Save report
    print("\n" + "=" * 60)
    print("SAVING REPORT")
    print("=" * 60)
    report_path = manager.save_report()

    print("\n" + "=" * 60)
    print("✅ SMART FLOOR FRAMEWORK DEMO COMPLETE")
    print("=" * 60)
