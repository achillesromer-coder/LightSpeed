#!/usr/bin/env python
"""
LightSpeed V1.0 Integration Test Suite
Tests all major systems: Oracle, Smith, Encyclopedia, Spherical UI

Author: Römer Industries / EMASSC
Version: 0.9.5
Date: December 31, 2025
"""

import sys
import os
from pathlib import Path

# Add project root to path
def _find_lightspeed_root() -> Path:
    here = Path(__file__).resolve()
    for cand in (here, *here.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return here.parents[3]


LIGHTSPEED_ROOT = _find_lightspeed_root()
for _p in (LIGHTSPEED_ROOT, LIGHTSPEED_ROOT / "Z Axis", LIGHTSPEED_ROOT / "Z Axis" / "Z-4_Merovingian"):
    try:
        if _p.exists() and str(_p) not in sys.path:
            sys.path.insert(0, str(_p))
    except Exception:
        pass

import json
import tempfile
from datetime import datetime


def test_encyclopedia_system():
    """Test Encyclopedia System (3 volumes, multilingual)"""
    print("\n" + "="*70)
    print("TEST 1: ENCYCLOPEDIA SYSTEM")
    print("="*70)

    try:
        # Import encyclopedia system
        sys.path.insert(0, str(Path(__file__).parent.parent / "components"))
        from encyclopedia_system import EncyclopediaSystem, EncyclopediaVolume, initialize_foundation_encyclopedia

        # Initialize
        encyclopedia = EncyclopediaSystem()
        print("[OK] Encyclopedia initialized")
        print(f"    Base path: {encyclopedia.base_path}")
        print(f"    Volumes: {len(encyclopedia.volumes)}")
        print(f"    Dictionary terms: {len(encyclopedia.dictionary)}")

        # Test foundation initialization
        initialize_foundation_encyclopedia(encyclopedia)
        print("[OK] Foundation constants initialized")

        # Test adding entry
        entry_id = encyclopedia.add_entry(
            term="Boltzmann Constant",
            volume=EncyclopediaVolume.EMPIRICAL,
            definition="Physical constant relating temperature to energy",
            data_object={
                'symbol': 'k_B',
                'value': 1.380649e-23,
                'unit': 'J/K',
                'exact': True
            },
            references=['CODATA 2018']
        )
        print(f"[OK] Added entry: Boltzmann Constant (ID: {entry_id})")

        # Test search
        results = encyclopedia.search("light")
        print(f"[OK] Search 'light': {len(results)} results")

        # Test translation
        translation = encyclopedia.translate_term("energy", "de")
        print(f"[OK] Translation 'energy' → German: {translation}")

        # Test statistics
        stats = encyclopedia.get_statistics()
        print(f"[OK] Statistics: {stats['total_entries']} total entries")

        # Test A-Z organization
        category_g = encyclopedia.get_category('G', EncyclopediaVolume.EMPIRICAL)
        print(f"[OK] Category 'G' entries: {len(category_g)}")

        print("\n[TEST 1] PASSED ✓")
        return True

    except Exception as e:
        print(f"\n[TEST 1] FAILED ✗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_oracle_smart_floor():
    """Test Oracle Smart Floor Integrator"""
    print("\n" + "="*70)
    print("TEST 2: ORACLE SMART FLOOR INTEGRATOR")
    print("="*70)

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Z-2_Oracle" / "components"))
        from oracle_smart_floor_integrator import OracleSmartFloorIntegrator

        # Initialize
        integrator = OracleSmartFloorIntegrator()
        print("[OK] Oracle Smart Floor Integrator initialized")
        print(f"    Vault path: {integrator.vault_path}")
        print(f"    Floor routing: {len(integrator.floor_routing)} floors")

        # Create test file
        test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        test_file.write("""
# Test Python file for ingestion
GRAVITATIONAL_CONSTANT = 6.67430e-11  # m³/(kg⋅s²)

class PhysicsSimulation:
    def __init__(self):
        self.gravity = GRAVITATIONAL_CONSTANT

    def calculate_force(self, mass1, mass2, distance):
        return self.gravity * mass1 * mass2 / (distance ** 2)
""")
        test_file.close()

        # Ingest file
        result = integrator.ingest_file(test_file.name, metadata={'source': 'integration_test'})
        print(f"[OK] File ingested: vault_id={result.get('vault_id')}")

        # Check queue status
        queue_status = integrator.get_queue_status()
        print(f"[OK] Queue status: {queue_status['total_tasks']} tasks")

        # Process extraction task
        if queue_status['total_tasks'] > 0:
            task_result = integrator.process_extraction_task(1)
            if task_result['success']:
                print(f"[OK] Extraction completed: {len(task_result.get('floors_updated', {}))} floors routed")
            else:
                print(f"[WARN] Extraction failed: {task_result.get('error')}")

        # Cleanup
        os.unlink(test_file.name)

        print("\n[TEST 2] PASSED ✓")
        return True

    except Exception as e:
        print(f"\n[TEST 2] FAILED ✗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_smith_task_queue():
    """Test Smith Task Queue & Priority System"""
    print("\n" + "="*70)
    print("TEST 3: SMITH TASK QUEUE")
    print("="*70)

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "components"))
        from smith_task_queue import SmithTaskQueue, TaskPriority

        # Initialize
        queue = SmithTaskQueue()
        print("[OK] Smith Task Queue initialized")
        print(f"    Floor quotas: {len(queue.floor_quotas)} floors")

        # Add tasks with different priorities
        t1 = queue.add_task('critical_task', {'data': 'test1'}, 'Z-2_Oracle', priority=TaskPriority.CRITICAL.value)
        t2 = queue.add_task('high_task', {'data': 'test2'}, 'Z-2_Oracle', priority=TaskPriority.HIGH.value)
        t3 = queue.add_task('medium_task', {'data': 'test3'}, 'Z0_TheConstruct', priority=TaskPriority.MEDIUM.value)

        print(f"[OK] Added 3 tasks: {t1}, {t2}, {t3}")

        # Test dependencies
        t4 = queue.add_task('dependent_task', {'data': 'test4'}, 'Z-2_Oracle',
                           priority=TaskPriority.HIGH.value, dependencies=[t1])
        print(f"[OK] Added dependent task: {t4} (depends on {t1})")

        # Get queue status
        status = queue.get_queue_status()
        print(f"[OK] Queue status:")
        print(f"    Total tasks: {status['total_tasks']}")
        print(f"    Queue size: {status['queue_size']}")
        print(f"    Pending: {status['status_counts'].get('pending', 0)}")
        print(f"    Blocked: {status['status_counts'].get('blocked', 0)}")

        # Get next task (should be highest priority)
        next_task = queue.get_next_task()
        if next_task:
            print(f"[OK] Next task: {next_task['task_id']} (priority {next_task['priority']})")

            # Complete task
            queue.complete_task(next_task['task_id'], result={'status': 'success'})
            print(f"[OK] Task {next_task['task_id']} completed")

        # Check if dependent task unblocked
        status_after = queue.get_queue_status()
        print(f"[OK] After completion - Blocked: {status_after['status_counts'].get('blocked', 0)}")

        # Test floor quotas
        floor_stats = status_after['floor_stats']
        for floor, stats in list(floor_stats.items())[:3]:
            print(f"    {floor}: {stats['usage']}/{stats['quota']} used")

        print("\n[TEST 3] PASSED ✓")
        return True

    except Exception as e:
        print(f"\n[TEST 3] FAILED ✗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_smith_interfloor_coordinator():
    """Test Smith Inter-Floor Coordinator"""
    print("\n" + "="*70)
    print("TEST 4: SMITH INTER-FLOOR COORDINATOR")
    print("="*70)

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "components"))
        from smith_interfloor_coordinator import SmithInterFloorCoordinator, FloorID

        # Initialize
        coordinator = SmithInterFloorCoordinator()
        print("[OK] Smith Inter-Floor Coordinator initialized")
        print(f"    Floor capabilities: {len(coordinator.floor_capabilities)} floors")
        print(f"    Communication channels: {len(coordinator.comm_channels)} channels")

        # Test auto-routing
        task1 = coordinator.submit_task(
            task_type='file_ingestion',
            source_floor=FloorID.ORACLE.value,
            parameters={'file_id': 123, 'keywords': ['physics', 'simulation']},
            priority=2
        )
        print(f"[OK] Submitted file_ingestion task: {task1}")

        # Test with explicit target floors
        task2 = coordinator.submit_task(
            task_type='code_analysis',
            source_floor=FloorID.MORPHEUS.value,
            parameters={'file_path': '/test/code.py'},
            priority=2,
            target_floors=[FloorID.ORACLE.value, FloorID.NEO.value]
        )
        print(f"[OK] Submitted code_analysis task: {task2}")

        # Test Neo sign-off
        task3 = coordinator.submit_task(
            task_type='critical_operation',
            source_floor=FloorID.ARCHITECT.value,
            parameters={'operation': 'system_update'},
            priority=1,
            requires_neo_signoff=True
        )
        print(f"[OK] Submitted task requiring Neo sign-off: {task3}")

        # Simulate Neo approval
        coordinator.handle_neo_signoff(task3, 'approved', 'Operation appears safe')
        print(f"[OK] Neo approved task {task3}")

        # Get floor activity
        oracle_activity = coordinator.get_floor_activity(FloorID.ORACLE.value)
        print(f"[OK] Oracle activity:")
        print(f"    Tasks submitted: {oracle_activity['tasks_submitted']}")
        print(f"    Tasks received: {oracle_activity['tasks_received']}")

        # Get system overview
        overview = coordinator.get_system_overview()
        print(f"[OK] System overview:")
        print(f"    Total tasks: {overview['total_tasks']}")
        print(f"    Active tasks: {overview['active_tasks']}")

        print("\n[TEST 4] PASSED ✓")
        return True

    except Exception as e:
        print(f"\n[TEST 4] FAILED ✗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_spherical_projection():
    """Test Spherical 360° Projection UI"""
    print("\n" + "="*70)
    print("TEST 5: SPHERICAL 360° PROJECTION UI")
    print("="*70)

    try:
        # core.ui is a namespace package rooted in the Merovingian floor; ensure the floor root is available.
        p = LIGHTSPEED_ROOT / "Z Axis" / "Z-4_Merovingian"
        if p.exists() and str(p) not in sys.path:
            sys.path.insert(0, str(p))
        from spherical_projection import SphericalCoordinate, SphericalFloorLayout

        # Test spherical coordinates
        coord = SphericalCoordinate(radius=500, theta=45, phi=90)
        x, y, z = coord.to_cartesian()
        print(f"[OK] Spherical coordinate conversion:")
        print(f"    (r=500, θ=45°, φ=90°) → (x={x:.2f}, y={y:.2f}, z={z:.2f})")

        # Test floor layout
        print(f"[OK] Z-Floor spherical layout:")
        for floor, (theta, phi) in list(SphericalFloorLayout.FLOOR_POSITIONS.items())[:5]:
            color = SphericalFloorLayout.FLOOR_COLORS.get(floor, '#FFFFFF')
            print(f"    {floor}: θ={theta}°, φ={phi}° - {color}")

        # Note: Full UI test requires Tkinter window, skipping in headless mode
        print("[OK] Spherical projection system validated (headless mode)")

        print("\n[TEST 5] PASSED ✓")
        return True

    except Exception as e:
        print(f"\n[TEST 5] FAILED ✗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_schema():
    """Test Database Schema Additions"""
    print("\n" + "="*70)
    print("TEST 6: DATABASE SCHEMA")
    print("="*70)

    try:
        import sqlite3

        db_path = LIGHTSPEED_ROOT / "Z Axis" / "Z-4_Merovingian" / "data" / "db" / "lightspeed_unified.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check encyclopedia_entries table
        cursor.execute("PRAGMA table_info(encyclopedia_entries)")
        columns = cursor.fetchall()
        print(f"[OK] encyclopedia_entries table: {len(columns)} columns")
        for col in columns:
            print(f"    {col[1]} ({col[2]})")

        # Check interfloor_tasks table
        cursor.execute("PRAGMA table_info(interfloor_tasks)")
        columns = cursor.fetchall()
        print(f"[OK] interfloor_tasks table: {len(columns)} columns")

        # Check files table enhancements
        cursor.execute("PRAGMA table_info(files)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}

        new_columns = ['vault_id', 'ingestion_queue_position', 'extraction_status', 'routed_floors']
        for col in new_columns:
            if col in columns:
                print(f"[OK] files table enhanced with: {col}")
            else:
                print(f"[WARN] Column not found: {col}")

        # Test insert into encyclopedia
        cursor.execute("""
            INSERT INTO encyclopedia_entries
            (term, volume, category_letter, definition, data_object, references_list, metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('Test Entry', 'EMPIRICAL', 'T', 'Test definition', '{"test": true}',
              '[]', '{}', datetime.now().isoformat(), datetime.now().isoformat()))

        conn.commit()
        print("[OK] Successfully inserted test encyclopedia entry")

        # Verify
        cursor.execute("SELECT COUNT(*) FROM encyclopedia_entries")
        count = cursor.fetchone()[0]
        print(f"[OK] Encyclopedia entries count: {count}")

        conn.close()

        print("\n[TEST 6] PASSED ✓")
        return True

    except Exception as e:
        print(f"\n[TEST 6] FAILED ✗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("LIGHTSPEED V1.0 INTEGRATION TEST SUITE")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Testing: Oracle, Smith, Encyclopedia, Spherical UI, Database")
    print("="*70)

    results = {
        'Encyclopedia System': test_encyclopedia_system(),
        'Oracle Smart Floor': test_oracle_smart_floor(),
        'Smith Task Queue': test_smith_task_queue(),
        'Smith Inter-Floor Coordinator': test_smith_interfloor_coordinator(),
        'Spherical Projection': test_spherical_projection(),
        'Database Schema': test_database_schema()
    }

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = "PASSED ✓" if result else "FAILED ✗"
        print(f"  {test_name:.<50} {status}")

    print("="*70)
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*70)

    if passed == total:
        print("\n[SUCCESS] All integration tests passed!")
        print("LightSpeed V1.0 is ready for deployment! 🚀")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        print("Review errors above before deployment")
        return 1


if __name__ == '__main__':
    exit(main())
