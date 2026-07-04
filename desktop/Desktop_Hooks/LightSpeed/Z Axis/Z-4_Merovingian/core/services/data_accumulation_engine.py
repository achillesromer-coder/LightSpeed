"""
Data Accumulation Engine - Object-based data management across Z-floors

Converts all incoming data (files, test results, empirical data, digital databases)
into structured objects that are amalgamated into a master dataset. Enables complete
project recall through any portal and supports:

- Empirical and digital database accumulation
- Type and function-based Z-floor distribution
- Scalar and batch test execution
- Visualization and export capabilities
- Complete interweaving and connections across all systems
- Smart floor AI integration for self-expanding capabilities

This is the 'base learning system' that grows with usage.

Author: LightSpeed Team
Date: December 20, 2025
Version: 0.9.5
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Iterable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import hashlib


# ============================================================================
# Data Object Types
# ============================================================================

class DataType(Enum):
    """Types of data objects in the system"""
    EMPIRICAL = "empirical"          # Physical test results, measurements
    DIGITAL = "digital"              # Digital test results, simulations
    CODE = "code"                    # Source code, algorithms
    DATASET = "dataset"              # Research datasets
    VISUALIZATION = "visualization"  # Charts, graphs, 3D renders
    DOCUMENT = "document"            # Text documents, PDFs
    MODEL = "model"                  # AI/ML models
    CONFIGURATION = "configuration"  # System configurations
    TEST_RESULT = "test_result"     # Test execution results
    KNOWLEDGE = "knowledge"          # Knowledge graph entries


class ProcessingStatus(Enum):
    """Status of data object processing"""
    RAW = "raw"                     # Just received, not processed
    PROCESSING = "processing"        # Being processed
    INDEXED = "indexed"             # Indexed and searchable
    AMALGAMATED = "amalgamated"     # Merged into master set
    ARCHIVED = "archived"           # Moved to archives


@dataclass
class DataObject:
    """Universal data object container"""
    id: str
    name: str
    data_type: DataType
    z_floor: str                    # Which floor manages this data
    file_path: Optional[str]        # Original file path if applicable
    content: Optional[str]          # Text content or serialized data
    metadata: Dict[str, Any]        # Extensible metadata
    created_at: str
    updated_at: str
    status: ProcessingStatus
    hash: str                       # Content hash for deduplication
    tags: List[str]                 # Searchable tags
    relationships: List[str]        # IDs of related objects
    version: int                    # Object version


# ============================================================================
# Data Accumulation Engine
# ============================================================================

class DataAccumulationEngine:
    """
    Central engine for accumulating all data across Z-floors

    Converts incoming files/data into objects, distributes by type/function,
    and maintains master amalgamated dataset for complete project recall.
    """

    def __init__(self, lightspeed_root: Path):
        self.lightspeed_root = lightspeed_root
        self.master_index: Dict[str, DataObject] = {}

        # Store the master index in the Merovingian floor (system core) rather than
        # creating a top-level `data/` folder in the LightSpeed root.
        legacy_index = lightspeed_root / "data" / "master_index.json"
        try:
            from core.config.paths import MEROVINGIAN_DATA  # type: ignore
            self.index_path = Path(MEROVINGIAN_DATA) / "master_index.json"
        except Exception:
            self.index_path = lightspeed_root / "Z Axis" / "Z-4_Merovingian" / "data" / "master_index.json"

        # Best-effort one-time migration from legacy path if present.
        try:
            if legacy_index.exists() and not self.index_path.exists():
                self.index_path.parent.mkdir(parents=True, exist_ok=True)
                self.index_path.write_text(legacy_index.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        except Exception:
            pass

        # Floor assignments by data type
        self.floor_assignments = {
            DataType.EMPIRICAL: "Z-4_Merovingian",      # System core - data validation
            DataType.DIGITAL: "Z-4_Merovingian",        # System core - digital data
            DataType.CODE: "Z+2_Neo",                   # AI floor - code analysis
            DataType.DATASET: "Z+2_Neo",                # AI floor - research datasets
            DataType.VISUALIZATION: "Z0_TheConstruct",  # Physics floor - 3D rendering
            DataType.DOCUMENT: "Z-2_Oracle",            # Archive floor - documents
            DataType.MODEL: "Z+2_Neo",                  # AI floor - ML models
            DataType.CONFIGURATION: "Z-4_Merovingian",  # System core - configs
            DataType.TEST_RESULT: "Z-3_Smith",          # Automation - test results
            DataType.KNOWLEDGE: "Z-1_Morpheus",         # Knowledge floor
        }

        # Load existing index
        self._load_index()

    def _load_index(self):
        """Load master index from disk"""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for obj_id, obj_data in data.items():
                        # Reconstruct enum values
                        obj_data['data_type'] = DataType(obj_data['data_type'])
                        obj_data['status'] = ProcessingStatus(obj_data['status'])
                        self.master_index[obj_id] = DataObject(**obj_data)
                print(f"[DataAccumulation] Loaded {len(self.master_index)} objects from master index")
            except Exception as e:
                print(f"[DataAccumulation] Error loading index: {e}")

    def _save_index(self):
        """Save master index to disk"""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)

        # Convert to serializable format
        serializable = {}
        for obj_id, obj in self.master_index.items():
            obj_dict = asdict(obj)
            obj_dict['data_type'] = obj.data_type.value
            obj_dict['status'] = obj.status.value
            serializable[obj_id] = obj_dict

        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, indent=2)

    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def ingest_file(
        self,
        file_path: str,
        data_type: DataType,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> DataObject:
        """
        Ingest a file and convert it to a data object

        Args:
            file_path: Path to file
            data_type: Type of data
            metadata: Additional metadata
            tags: Searchable tags

        Returns:
            Created DataObject
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Binary file - store path only
            content = None

        # Compute hash
        content_hash = self._compute_hash(content if content else file_path)

        # Check for duplicates
        for obj in self.master_index.values():
            if obj.hash == content_hash:
                print(f"[DataAccumulation] Duplicate detected: {os.path.basename(file_path)}")
                return obj

        # Create data object
        obj_id = f"{data_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{content_hash[:8]}"

        data_obj = DataObject(
            id=obj_id,
            name=os.path.basename(file_path),
            data_type=data_type,
            z_floor=self.floor_assignments[data_type],
            file_path=file_path,
            content=content,
            metadata=metadata or {},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            status=ProcessingStatus.RAW,
            hash=content_hash,
            tags=tags or [],
            relationships=[],
            version=1
        )

        # Add to master index
        self.master_index[obj_id] = data_obj
        self._save_index()

        print(f"[DataAccumulation] Ingested: {data_obj.name} -> {data_obj.z_floor}")
        return data_obj

    def ingest_directory(
        self,
        directory: Union[str, Path],
        *,
        include_extensions: Optional[Iterable[str]] = None,
        default_type: DataType = DataType.DOCUMENT,
        max_files: Optional[int] = None,
        extra_tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Ingest a directory tree into the master index.

        Notes:
        - Uses lightweight heuristics based on extension and directory name.
        - Skips files that can't be read; binary files are recorded with `content=None`.
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        if include_extensions is None:
            include_extensions = {'.md', '.txt', '.json', '.py', '.yaml', '.yml'}
        else:
            include_extensions = {e.lower() if e.startswith('.') else f".{e.lower()}" for e in include_extensions}

        counts = {
            "directory": str(directory_path),
            "scanned": 0,
            "ingested": 0,
            "duplicates": 0,
            "errors": 0,
            "by_type": {},
        }

        def infer_type(path: Path) -> DataType:
            ext = path.suffix.lower()
            if ext == '.py':
                return DataType.CODE
            if ext in {'.md'}:
                # docs/knowledge are treated as knowledge objects
                lowered = str(path).lower()
                if 'documentation' in lowered or os.sep + 'docs' + os.sep in lowered or os.sep + 'knowledge' + os.sep in lowered:
                    return DataType.KNOWLEDGE
                return DataType.DOCUMENT
            if ext in {'.yaml', '.yml'}:
                return DataType.CONFIGURATION
            if ext == '.json':
                lowered = str(path).lower()
                if 'config' in lowered or 'manifest' in lowered:
                    return DataType.CONFIGURATION
                if 'extract' in lowered or 'knowledge' in lowered:
                    return DataType.KNOWLEDGE
                return DataType.DOCUMENT
            if ext == '.txt':
                return default_type
            return default_type

        files = []
        for ext in include_extensions:
            files.extend(directory_path.rglob(f"*{ext}"))

        files_sorted = sorted({p.resolve() for p in files if p.is_file()})
        if max_files is not None:
            files_sorted = files_sorted[: max(0, int(max_files))]

        for file_path in files_sorted:
            counts["scanned"] += 1
            try:
                data_type = infer_type(file_path)
                rel = None
                try:
                    rel = str(file_path.relative_to(self.lightspeed_root))
                except Exception:
                    rel = str(file_path)

                tags = []
                if extra_tags:
                    tags.extend(extra_tags)
                tags.append(data_type.value)
                tags.append(file_path.suffix.lower().lstrip("."))
                tags.extend([p for p in Path(rel).parts if p and p not in {'.'}][:6])

                before = len(self.master_index)
                obj = self.ingest_file(
                    file_path=str(file_path),
                    data_type=data_type,
                    metadata={"relative_path": rel},
                    tags=sorted(set(tags)),
                )
                after = len(self.master_index)
                if after == before:
                    counts["duplicates"] += 1
                else:
                    counts["ingested"] += 1

                counts["by_type"].setdefault(data_type.value, 0)
                counts["by_type"][data_type.value] += 1
            except Exception:
                counts["errors"] += 1

        return counts

    def ingest_lightspeed_docs(self, *, max_files: Optional[int] = None) -> Dict[str, Any]:
        """Ingest core LightSpeed documentation/knowledge into the master index."""
        targets = [
            self.lightspeed_root / "README.md",
            self.lightspeed_root / "QUICK_START.md",
            self.lightspeed_root / "Z Axis" / "Z-1_Morpheus" / "documentation",
            self.lightspeed_root / "docs",
            self.lightspeed_root / "knowledge",
        ]

        results = {"targets": [], "total_ingested": 0, "total_duplicates": 0, "total_errors": 0}
        per_target_max = None
        if max_files is not None and len(targets) > 0:
            per_target_max = max(1, int(max_files) // len(targets))

        for target in targets:
            if target.is_file():
                try:
                    before = len(self.master_index)
                    self.ingest_file(
                        file_path=str(target),
                        data_type=DataType.KNOWLEDGE if target.suffix.lower() == ".md" else DataType.DOCUMENT,
                        metadata={"relative_path": str(target.relative_to(self.lightspeed_root))},
                        tags=["docs", "core"],
                    )
                    after = len(self.master_index)
                    if after == before:
                        results["total_duplicates"] += 1
                    else:
                        results["total_ingested"] += 1
                    results["targets"].append({"path": str(target), "type": "file"})
                except Exception:
                    results["total_errors"] += 1
                continue

            if target.is_dir():
                try:
                    counts = self.ingest_directory(
                        target,
                        default_type=DataType.KNOWLEDGE,
                        max_files=per_target_max,
                        extra_tags=["docs"],
                    )
                    results["targets"].append(counts)
                    results["total_ingested"] += int(counts.get("ingested", 0))
                    results["total_duplicates"] += int(counts.get("duplicates", 0))
                    results["total_errors"] += int(counts.get("errors", 0))
                except Exception:
                    results["total_errors"] += 1

        return results

    def ingest_data(
        self,
        name: str,
        data_type: DataType,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> DataObject:
        """
        Ingest raw data (not from file)

        Args:
            name: Object name
            data_type: Type of data
            content: Data content (will be serialized if needed)
            metadata: Additional metadata
            tags: Searchable tags

        Returns:
            Created DataObject
        """
        # Serialize content if needed
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, indent=2)
        else:
            content_str = str(content)

        # Compute hash
        content_hash = self._compute_hash(content_str)

        # Check for duplicates
        for obj in self.master_index.values():
            if obj.hash == content_hash:
                print(f"[DataAccumulation] Duplicate detected: {name}")
                return obj

        # Create data object
        obj_id = f"{data_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{content_hash[:8]}"

        data_obj = DataObject(
            id=obj_id,
            name=name,
            data_type=data_type,
            z_floor=self.floor_assignments[data_type],
            file_path=None,
            content=content_str,
            metadata=metadata or {},
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            status=ProcessingStatus.RAW,
            hash=content_hash,
            tags=tags or [],
            relationships=[],
            version=1
        )

        # Add to master index
        self.master_index[obj_id] = data_obj
        self._save_index()

        print(f"[DataAccumulation] Ingested data: {data_obj.name} -> {data_obj.z_floor}")
        return data_obj

    def process_object(self, obj_id: str) -> bool:
        """
        Process a data object (index, extract metadata, etc.)

        Args:
            obj_id: Object ID

        Returns:
            True if successful
        """
        obj = self.master_index.get(obj_id)
        if not obj:
            return False

        obj.status = ProcessingStatus.PROCESSING
        self._save_index()

        # Type-specific processing
        try:
            if obj.data_type == DataType.CODE:
                # Extract code metadata
                if obj.content:
                    obj.metadata['lines'] = len(obj.content.splitlines())
                    obj.metadata['functions'] = obj.content.count('def ')
                    obj.metadata['classes'] = obj.content.count('class ')

            elif obj.data_type == DataType.DATASET:
                # Count records if CSV
                if obj.file_path and obj.file_path.endswith('.csv'):
                    import csv
                    with open(obj.file_path, 'r') as f:
                        obj.metadata['records'] = sum(1 for _ in csv.reader(f)) - 1

            elif obj.data_type == DataType.TEST_RESULT:
                # Extract test metrics
                if obj.content:
                    try:
                        test_data = json.loads(obj.content)
                        obj.metadata['tests_passed'] = test_data.get('passed', 0)
                        obj.metadata['tests_failed'] = test_data.get('failed', 0)
                    except Exception as e:
                        obj.metadata['test_result_parse_error'] = str(e)
                        obj.metadata['test_result_sample'] = obj.content[:200]

            # Mark as indexed
            obj.status = ProcessingStatus.INDEXED
            obj.updated_at = datetime.now().isoformat()
            self._save_index()

            print(f"[DataAccumulation] Processed: {obj.name}")
            return True

        except Exception as e:
            print(f"[DataAccumulation] Processing error for {obj.name}: {e}")
            obj.status = ProcessingStatus.RAW
            self._save_index()
            return False

    def amalgamate_objects(self, obj_ids: List[str], merged_name: str) -> Optional[DataObject]:
        """
        Amalgamate multiple objects into a single master object

        Args:
            obj_ids: List of object IDs to merge
            merged_name: Name for merged object

        Returns:
            Merged DataObject or None
        """
        if not obj_ids:
            return None

        objects = [self.master_index.get(oid) for oid in obj_ids]
        objects = [obj for obj in objects if obj]

        if not objects:
            return None

        # Determine dominant type
        data_type = max(set(obj.data_type for obj in objects),
                       key=lambda dt: sum(1 for obj in objects if obj.data_type == dt))

        # Merge content
        merged_content = {
            'type': 'amalgamated',
            'source_objects': obj_ids,
            'sources': [{'id': obj.id, 'name': obj.name, 'type': obj.data_type.value}
                       for obj in objects],
            'merged_at': datetime.now().isoformat()
        }

        # Merge metadata
        merged_metadata = {}
        for obj in objects:
            merged_metadata.update(obj.metadata)

        # Merge tags
        merged_tags = list(set(tag for obj in objects for tag in obj.tags))

        # Create amalgamated object
        merged_obj = self.ingest_data(
            name=merged_name,
            data_type=data_type,
            content=merged_content,
            metadata=merged_metadata,
            tags=merged_tags + ['amalgamated']
        )

        # Update source objects
        for obj in objects:
            obj.status = ProcessingStatus.AMALGAMATED
            obj.relationships.append(merged_obj.id)

        self._save_index()
        print(f"[DataAccumulation] Amalgamated {len(objects)} objects into {merged_name}")

        return merged_obj

    def search(
        self,
        query: Optional[str] = None,
        data_type: Optional[DataType] = None,
        z_floor: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[ProcessingStatus] = None
    ) -> List[DataObject]:
        """Search master index"""
        results = list(self.master_index.values())

        if query:
            query_lower = query.lower()
            results = [obj for obj in results
                      if query_lower in obj.name.lower() or
                         query_lower in (obj.content or '').lower()]

        if data_type:
            results = [obj for obj in results if obj.data_type == data_type]

        if z_floor:
            results = [obj for obj in results if obj.z_floor == z_floor]

        if tags:
            results = [obj for obj in results
                      if any(tag in obj.tags for tag in tags)]

        if status:
            results = [obj for obj in results if obj.status == status]

        return results

    def get_floor_summary(self) -> Dict[str, Dict[str, int]]:
        """Get summary of data distribution across floors"""
        summary = {}

        for floor in set(obj.z_floor for obj in self.master_index.values()):
            floor_objs = [obj for obj in self.master_index.values() if obj.z_floor == floor]

            summary[floor] = {
                'total_objects': len(floor_objs),
                'by_type': {},
                'by_status': {}
            }

            for data_type in DataType:
                count = sum(1 for obj in floor_objs if obj.data_type == data_type)
                if count > 0:
                    summary[floor]['by_type'][data_type.value] = count

            for status in ProcessingStatus:
                count = sum(1 for obj in floor_objs if obj.status == status)
                if count > 0:
                    summary[floor]['by_status'][status.value] = count

        return summary


# ============================================================================
# Testing
# ============================================================================

if __name__ == "__main__":
    import argparse

    lightspeed_root = Path(__file__).parent.parent.parent.resolve()
    engine = DataAccumulationEngine(lightspeed_root)

    parser = argparse.ArgumentParser(description="LightSpeed Data Accumulation Engine")
    parser.add_argument("--ingest-docs", action="store_true", help="Ingest docs/knowledge into master index")
    parser.add_argument("--max-files", type=int, default=None, help="Optional cap on ingested files")
    parser.add_argument("--self-test", action="store_true", help="Run a small ingest/process/search sanity test")
    args = parser.parse_args()

    if args.ingest_docs:
        print("\n" + "=" * 60)
        print("DATA ACCUMULATION: INGEST DOCS")
        print("=" * 60)
        results = engine.ingest_lightspeed_docs(max_files=args.max_files)
        print(json.dumps(results, indent=2))
        raise SystemExit(0)

    if args.self_test:
        print("\n" + "=" * 60)
        print("DATA ACCUMULATION ENGINE SELF-TEST")
        print("=" * 60)

        obj1 = engine.ingest_data(
            name="Test Results Batch 1",
            data_type=DataType.TEST_RESULT,
            content={'passed': 42, 'failed': 0, 'skipped': 3},
            tags=['test', 'automated']
        )

        obj2 = engine.ingest_data(
            name="Research Dataset: AI Performance",
            data_type=DataType.DATASET,
            content={'records': 1000, 'accuracy': 0.95},
            tags=['research', 'ai']
        )

        engine.process_object(obj1.id)
        engine.process_object(obj2.id)

        results = engine.search(tags=['test'])
        print(f"Found {len(results)} objects with tag 'test'")

        summary = engine.get_floor_summary()
        for floor, stats in summary.items():
            print(f"\n{floor}:")
            print(f"  Total: {stats['total_objects']}")
            print(f"  By type: {stats['by_type']}")

        raise SystemExit(0)

    parser.print_help()
