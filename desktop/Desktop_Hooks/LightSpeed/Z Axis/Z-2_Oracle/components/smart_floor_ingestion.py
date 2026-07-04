"""
LightSpeed V0.9.11+ - Oracle Smart Floor Auto-Ingestion System
Continuous background file processing with <5% CPU usage

Features:
- Auto-ingestion on startup
- Continuous monitoring (low CPU)
- Multi-select and select-all support
- Systematic file breakdown across Z-floors
- Auto-archiving after processing
- Object/dataset/string extraction
- Smart routing to appropriate floors

Process:
1. Monitor Oracle/incoming directory
2. Process files in batches (CPU-limited)
3. Extract objects, datasets, strings
4. Route to appropriate Z-floors
5. Archive processed files
6. Generate metadata and indexes

CPU Management:
- Max 5% CPU usage
- Batch processing with delays
- Priority queue system
- Pause/resume capability

Author: LightSpeed Team / ACHILLES
Version: 0.9.11+
Date: January 4, 2026
"""

import os
import sys
import time
import threading
import queue
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
import re
import hashlib
import psutil  # For CPU monitoring

def _find_lightspeed_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in (start, *start.parents):
        try:
            if (candidate / "N.py").exists() and (candidate / "Z Axis").exists():
                return candidate
        except Exception:
            continue
    try:
        cwd = Path.cwd().resolve()
        if (cwd / "N.py").exists() and (cwd / "Z Axis").exists():
            return cwd
    except Exception:
        pass
    return start.parent


try:
    from core.config.paths import LIGHTSPEED_ROOT as _ROOT  # type: ignore
except Exception:
    _ROOT = _find_lightspeed_root(Path(__file__))

LIGHTSPEED_ROOT = Path(_ROOT)

for _p in (LIGHTSPEED_ROOT, LIGHTSPEED_ROOT / "Z Axis", LIGHTSPEED_ROOT / "Z Axis" / "core"):
    try:
        if _p.exists():
            sys.path.insert(0, str(_p))
    except Exception:
        pass

from core.config.paths import (
    ORACLE_ROOT,
    MORPHEUS_LIBRARY,
    SMITH_LOGS,
    MEROVINGIAN_DATA,
    CONSTRUCT_ROOT,
    ARCHITECT_TOOLS
)


@dataclass
class FileIngestionTask:
    """File ingestion task"""
    file_path: Path
    priority: int = 5  # 1-10, lower = higher priority
    timestamp: datetime = field(default_factory=datetime.now)
    file_size: int = 0
    file_type: str = ""
    processed: bool = False


@dataclass
class ExtractedObject:
    """Extracted object from file"""
    object_type: str  # 'constant', 'function', 'class', 'dataset', 'string'
    name: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    target_floor: str = ""


class SmartFloorIngestion:
    """
    Oracle Smart Floor continuous ingestion system.

    Monitors directories and processes files with <5% CPU usage.
    """

    # Constants
    MAX_CPU_PERCENT = 5.0  # Maximum CPU usage
    BATCH_SIZE = 5  # Files per batch
    BATCH_DELAY = 2.0  # Seconds between batches
    CHECK_INTERVAL = 10.0  # Seconds between directory checks

    # File type routing
    FLOOR_ROUTING = {
        'constant': MORPHEUS_LIBRARY,
        'function': ARCHITECT_TOOLS,
        'class': CONSTRUCT_ROOT,
        'dataset': MEROVINGIAN_DATA,
        'string': MORPHEUS_LIBRARY,
        'task': SMITH_LOGS,
    }

    def __init__(self):
        """Initialize smart ingestion system"""
        # Directories
        self.incoming_dir = ORACLE_ROOT / "incoming"
        self.archive_dir = ORACLE_ROOT / "archive"
        self.processing_dir = ORACLE_ROOT / "processing"

        # Create directories
        for dir_path in [self.incoming_dir, self.archive_dir, self.processing_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Task queue
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.processed_files: Set[str] = set()
        self.error_files: List[str] = []

        # Threading
        self.running = False
        self.paused = False
        self.worker_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = {
            'files_processed': 0,
            'objects_extracted': 0,
            'total_size_processed': 0,
            'started_at': None,
            'current_cpu': 0.0
        }

        # Load processed files list
        self._load_processed_list()

    def _stage_file_into_incoming(self, file_path: Path) -> Optional[Path]:
        """
        Stage a file into Oracle's incoming directory (non-destructive ingestion).

        The worker moves (renames) files from incoming -> processing, so callers should
        only queue files that are already in incoming or are staged here.
        """
        try:
            if not file_path.exists() or not file_path.is_file():
                return None

            try:
                file_path.resolve().relative_to(self.incoming_dir.resolve())
                return file_path
            except Exception:
                pass

            file_hash = self._get_file_hash(file_path)
            staged_name = f"{file_hash[:8]}__{file_path.name}"
            staged_path = self.incoming_dir / staged_name

            if staged_path.exists():
                return staged_path

            shutil.copy2(str(file_path), str(staged_path))
            return staged_path
        except Exception:
            return None

    def start(self):
        """Start ingestion system"""
        if self.running:
            print("[ORACLE] Already running")
            return

        self.running = True
        self.stats['started_at'] = datetime.now()

        # Start worker thread
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

        # Start monitor thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        print("[ORACLE] Smart Floor Ingestion started")

    def stop(self):
        """Stop ingestion system"""
        self.running = False

        if self.worker_thread:
            self.worker_thread.join(timeout=5)

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        self._save_processed_list()

        print("[ORACLE] Smart Floor Ingestion stopped")

    def pause(self):
        """Pause processing"""
        self.paused = True
        print("[ORACLE] Processing paused")

    def resume(self):
        """Resume processing"""
        self.paused = False
        print("[ORACLE] Processing resumed")

    def add_file(self, file_path: Path, priority: int = 5):
        """Manually add file to queue (non-destructive: stages into incoming)."""
        if not file_path.exists():
            print(f"[ORACLE] File not found: {file_path}")
            return

        staged = self._stage_file_into_incoming(file_path)
        if staged is None:
            print(f"[ORACLE] Could not stage file: {file_path}")
            return

        file_hash = self._get_file_hash(staged)
        if file_hash in self.processed_files:
            print(f"[ORACLE] File already processed: {file_path.name}")
            return

        task = FileIngestionTask(
            file_path=staged,
            priority=priority,
            file_size=staged.stat().st_size,
            file_type=staged.suffix
        )

        self.task_queue.put((priority, time.time(), task))
        print(f"[ORACLE] Added to queue: {file_path.name}")

    def add_directory(
        self,
        dir_path: Path,
        recursive: bool = False,
        priority: int = 5,
        include_extensions: Optional[Set[str]] = None,
        exclude_dirs: Optional[Set[str]] = None,
    ):
        """Add all files in directory (staged into incoming; originals remain untouched)."""
        if not dir_path.exists():
            print(f"[ORACLE] Directory not found: {dir_path}")
            return

        count = 0
        pattern = "**/*" if recursive else "*"
        exclude_dirs = exclude_dirs or set()

        for file_path in dir_path.glob(pattern):
            try:
                if not file_path.is_file():
                    continue
                if any(part in exclude_dirs for part in file_path.parts):
                    continue
                if include_extensions is not None:
                    if file_path.suffix.lower() not in include_extensions:
                        continue
                self.add_file(file_path, priority)
                count += 1
            except Exception:
                continue

        print(f"[ORACLE] Added {count} files from {dir_path}")

    def _monitor_loop(self):
        """Monitor incoming directory for new files"""
        while self.running:
            try:
                # Check incoming directory
                for file_path in self.incoming_dir.iterdir():
                    if file_path.is_file():
                        self.add_file(file_path, priority=5)

                # Wait before next check
                time.sleep(self.CHECK_INTERVAL)

            except Exception as e:
                print(f"[ORACLE] Monitor error: {e}")
                time.sleep(self.CHECK_INTERVAL)

    def _worker_loop(self):
        """Process files from queue"""
        while self.running:
            try:
                # Check if paused
                if self.paused:
                    time.sleep(1)
                    continue

                # Check CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                self.stats['current_cpu'] = cpu_percent

                if cpu_percent > self.MAX_CPU_PERCENT:
                    # CPU too high, wait
                    time.sleep(self.BATCH_DELAY * 2)
                    continue

                # Process batch
                batch_processed = 0

                while batch_processed < self.BATCH_SIZE:
                    try:
                        # Get task (non-blocking with timeout)
                        priority, timestamp, task = self.task_queue.get(timeout=1)

                        # Process file
                        self._process_file(task)

                        batch_processed += 1
                        self.task_queue.task_done()

                    except queue.Empty:
                        break

                # Delay between batches
                if batch_processed > 0:
                    time.sleep(self.BATCH_DELAY)
                else:
                    # Queue empty, longer delay
                    time.sleep(self.CHECK_INTERVAL)

            except Exception as e:
                print(f"[ORACLE] Worker error: {e}")
                time.sleep(self.BATCH_DELAY)

    def _process_file(self, task: FileIngestionTask):
        """Process a single file"""
        file_path = task.file_path

        try:
            print(f"[ORACLE] Processing: {file_path.name}")

            # Move to processing directory
            processing_path = self.processing_dir / file_path.name
            file_path.rename(processing_path)

            # Extract objects
            objects = self._extract_objects(processing_path)

            # Route to floors
            for obj in objects:
                self._route_object(obj)

            # Archive file
            archive_path = self.archive_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.name}"
            processing_path.rename(archive_path)

            # Update statistics
            self.stats['files_processed'] += 1
            self.stats['objects_extracted'] += len(objects)
            self.stats['total_size_processed'] += task.file_size

            # Mark as processed
            file_hash = self._get_file_hash(archive_path)
            self.processed_files.add(file_hash)

            print(f"[ORACLE] Completed: {file_path.name} ({len(objects)} objects)")

        except Exception as e:
            print(f"[ORACLE] Processing error: {file_path.name}: {e}")
            try:
                self.error_files.append(f"{file_path}: {e}")
            except Exception:
                pass

            # Move back to incoming on error
            try:
                processing_path = self.processing_dir / file_path.name
                if processing_path.exists():
                    processing_path.rename(file_path)
            except:
                pass

    def _extract_objects(self, file_path: Path) -> List[ExtractedObject]:
        """Extract objects from file"""
        objects = []

        try:
            # Avoid loading huge files into memory (e.g., GPT exports, large PDFs converted to text).
            file_size = 0
            try:
                file_size = file_path.stat().st_size
            except Exception:
                file_size = 0

            # For large files, only sample the head and store a dataset object for later deep processing.
            if file_size >= 20 * 1024 * 1024:
                try:
                    with open(file_path, "rb") as f:
                        head = f.read(256 * 1024)
                    try:
                        sample = head.decode("utf-8", errors="ignore")
                    except Exception:
                        sample = ""
                except Exception:
                    sample = ""

                objects.append(
                    ExtractedObject(
                        object_type="dataset",
                        name=file_path.stem,
                        content=(sample[:2000] if sample else ""),
                        metadata={
                            "source": str(file_path),
                            "size_bytes": file_size,
                            "note": "Large file sampled; deep parse deferred",
                        },
                        target_floor="Merovingian",
                    )
                )
                return objects

            # Read file content (small/medium only)
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Extract different object types
            objects.extend(self._extract_constants(content, file_path))
            objects.extend(self._extract_functions(content, file_path))
            objects.extend(self._extract_classes(content, file_path))
            objects.extend(self._extract_strings(content, file_path))
            objects.extend(self._extract_datasets(content, file_path))

        except Exception as e:
            print(f"[ORACLE] Extraction error: {file_path.name}: {e}")

        return objects

    def _extract_constants(self, content: str, source: Path) -> List[ExtractedObject]:
        """Extract constants"""
        objects = []

        # Pattern: CONSTANT_NAME = value
        pattern = r'^([A-Z_]+)\s*=\s*(.+)$'

        for match in re.finditer(pattern, content, re.MULTILINE):
            name = match.group(1)
            value = match.group(2).strip()

            obj = ExtractedObject(
                object_type='constant',
                name=name,
                content=f"{name} = {value}",
                metadata={
                    'source': str(source),
                    'value': value
                },
                target_floor='Morpheus'
            )
            objects.append(obj)

        return objects

    def _extract_functions(self, content: str, source: Path) -> List[ExtractedObject]:
        """Extract functions"""
        objects = []

        # Pattern: def function_name(...):
        pattern = r'def\s+(\w+)\s*\(([^)]*)\):'

        for match in re.finditer(pattern, content):
            name = match.group(1)
            params = match.group(2).strip()

            obj = ExtractedObject(
                object_type='function',
                name=name,
                content=f"def {name}({params}):",
                metadata={
                    'source': str(source),
                    'parameters': params
                },
                target_floor='Architect'
            )
            objects.append(obj)

        return objects

    def _extract_classes(self, content: str, source: Path) -> List[ExtractedObject]:
        """Extract classes"""
        objects = []

        # Pattern: class ClassName:
        pattern = r'class\s+(\w+)(?:\([^)]*\))?:'

        for match in re.finditer(pattern, content):
            name = match.group(1)

            obj = ExtractedObject(
                object_type='class',
                name=name,
                content=match.group(0),
                metadata={
                    'source': str(source)
                },
                target_floor='TheConstruct'
            )
            objects.append(obj)

        return objects

    def _extract_strings(self, content: str, source: Path) -> List[ExtractedObject]:
        """Extract significant strings"""
        objects = []

        # Pattern: Long strings (docs, comments)
        pattern = r'"""(.{50,}?)"""'

        for i, match in enumerate(re.finditer(pattern, content, re.DOTALL)):
            text = match.group(1).strip()

            obj = ExtractedObject(
                object_type='string',
                name=f"doc_string_{i}",
                content=text[:200],  # Truncate
                metadata={
                    'source': str(source),
                    'length': len(text)
                },
                target_floor='Morpheus'
            )
            objects.append(obj)

        return objects

    def _extract_datasets(self, content: str, source: Path) -> List[ExtractedObject]:
        """Extract dataset definitions"""
        objects = []

        # Pattern: Lists, dicts, data structures
        # Simplified for now - would need more sophisticated parsing

        # Look for large lists/dicts
        if '[' in content or '{' in content:
            obj = ExtractedObject(
                object_type='dataset',
                name=source.stem,
                content=content[:500],  # Sample
                metadata={
                    'source': str(source),
                    'size': len(content)
                },
                target_floor='Merovingian'
            )
            objects.append(obj)

        return objects

    def _route_object(self, obj: ExtractedObject):
        """Route object to appropriate Z-floor"""
        # Get target directory
        target_dir = self.FLOOR_ROUTING.get(obj.object_type)

        if not target_dir:
            print(f"[ORACLE] Unknown object type: {obj.object_type}")
            return

        # Create subdirectory for object type
        type_dir = target_dir / f"{obj.object_type}s"
        type_dir.mkdir(parents=True, exist_ok=True)

        # Create object file
        obj_file = type_dir / f"{obj.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"

        # Save object
        obj_data = {
            'type': obj.object_type,
            'name': obj.name,
            'content': obj.content,
            'metadata': obj.metadata,
            'created_at': datetime.now().isoformat(),
            'target_floor': obj.target_floor
        }

        with open(obj_file, 'w') as f:
            json.dump(obj_data, f, indent=2)

    def _get_file_hash(self, file_path: Path) -> str:
        """Get SHA256 hash of file"""
        sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)

        return sha256.hexdigest()

    def _load_processed_list(self):
        """Load list of processed file hashes"""
        processed_file = ORACLE_ROOT / "processed_files.json"

        try:
            if processed_file.exists():
                with open(processed_file, 'r') as f:
                    data = json.load(f)
                    self.processed_files = set(data.get('hashes', []))
        except Exception as e:
            print(f"[ORACLE] Failed to load processed list: {e}")

    def _save_processed_list(self):
        """Save list of processed file hashes"""
        processed_file = ORACLE_ROOT / "processed_files.json"

        try:
            data = {
                'hashes': list(self.processed_files),
                'count': len(self.processed_files),
                'last_saved': datetime.now().isoformat()
            }

            with open(processed_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ORACLE] Failed to save processed list: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        uptime = None
        if self.stats['started_at']:
            uptime = (datetime.now() - self.stats['started_at']).total_seconds()

        return {
            **self.stats,
            'uptime_seconds': uptime,
            'queue_size': self.task_queue.qsize(),
            'paused': self.paused,
            'running': self.running,
            'processed_count': len(self.processed_files)
        }


# Global instance
_oracle_ingestion: Optional[SmartFloorIngestion] = None


def get_oracle_ingestion() -> SmartFloorIngestion:
    """Get global Oracle ingestion instance"""
    global _oracle_ingestion

    if _oracle_ingestion is None:
        _oracle_ingestion = SmartFloorIngestion()

    return _oracle_ingestion


def start_oracle_ingestion():
    """Start Oracle ingestion system"""
    ingestion = get_oracle_ingestion()
    ingestion.start()
    return ingestion


def stop_oracle_ingestion():
    """Stop Oracle ingestion system"""
    global _oracle_ingestion

    if _oracle_ingestion:
        _oracle_ingestion.stop()
        _oracle_ingestion = None


# CLI for testing
if __name__ == "__main__":
    print("="*60)
    print("Oracle Smart Floor Ingestion System")
    print("="*60)
    print()

    ingestion = SmartFloorIngestion()
    ingestion.start()

    print("Commands: add <file>, adddir <dir>, stats, pause, resume, quit")
    print()

    try:
        while True:
            cmd = input("> ").strip().lower()

            if cmd == "quit":
                break
            elif cmd == "stats":
                stats = ingestion.get_stats()
                print(json.dumps(stats, indent=2))
            elif cmd == "pause":
                ingestion.pause()
            elif cmd == "resume":
                ingestion.resume()
            elif cmd.startswith("add "):
                file_path = Path(cmd[4:].strip())
                ingestion.add_file(file_path)
            elif cmd.startswith("adddir "):
                dir_path = Path(cmd[7:].strip())
                ingestion.add_directory(dir_path, recursive=True)
            else:
                print("Unknown command")

    except KeyboardInterrupt:
        print("\nShutting down...")

    finally:
        ingestion.stop()


__all__ = [
    'SmartFloorIngestion',
    'get_oracle_ingestion',
    'start_oracle_ingestion',
    'stop_oracle_ingestion'
]
