"""
Storage Service - File Operations & Management
LightSpeed Type I Civilization Platform

This service provides unified file storage and management across all floors,
handling file uploads, downloads, versioning, and integration with the
Morpheus knowledge layer for file analysis.

Storage Architecture:
- Centralized file repository in Data/files/
- Floor-specific subdirectories for organization
- Automatic checksumming (SHA256) for integrity
- Version control for file updates
- Integration with Morpheus for automatic analysis
- Event publishing for file operations

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
"""

import hashlib
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime
import mimetypes
import os

from .logger import get_services_logger
from .database import get_db
from .event_bus import get_event_bus, Event, EventTypes

logger = get_services_logger()

try:
    from core.config.paths import LIGHTSPEED_ROOT, MEROVINGIAN_DATA  # type: ignore
except Exception:
    LIGHTSPEED_ROOT = Path(__file__).resolve()
    for _cand in (LIGHTSPEED_ROOT, *LIGHTSPEED_ROOT.parents):
        if (_cand / "N.py").exists() and (_cand / "Z Axis").exists():
            LIGHTSPEED_ROOT = _cand
            break
    MEROVINGIAN_DATA = Path(LIGHTSPEED_ROOT) / "Z Axis" / "Z-4_Merovingian" / "data"


class StorageService:
    """
    Unified file storage service for all LightSpeed layers.

    Manages file operations with automatic:
    - Database registration (Morpheus layer)
    - Event publishing (for inter-floor communication)
    - Checksum validation
    - Version tracking
    """

    def __init__(self, base_storage_path: Optional[str] = None):
        """
        Initialize storage service.

        Parameters:
            base_storage_path: Root directory for file storage
                              Default: Data/files/
        """
        if base_storage_path is None:
            # Prefer floor-native Merovingian storage; fall back to legacy root Data during migration.
            legacy_root = Path(LIGHTSPEED_ROOT) / "Data" / "files"
            floor_root = Path(MEROVINGIAN_DATA) / "files"
            self.storage_root = floor_root if floor_root.exists() or not legacy_root.exists() else legacy_root
        else:
            self.storage_root = Path(base_storage_path)

        # Create storage directory structure
        self._initialize_storage()

        self.db = get_db()
        self.event_bus = get_event_bus()

        logger.info(f"Storage service initialized: {self.storage_root}")

    def _initialize_storage(self):
        """Create storage directory structure for all floors."""
        # Main storage directory
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # Floor-specific directories
        self.floors = {
            'neo': self.storage_root / 'neo',           # AI models, prompts
            'morpheus': self.storage_root / 'morpheus', # Analyzed files
            'architect': self.storage_root / 'architect', # Mission plans, timesheets
            'construct': self.storage_root / 'construct', # Simulation outputs
            'oracle': self.storage_root / 'oracle',     # IP documents, archives
            'smith': self.storage_root / 'smith',       # Job outputs, SOPs
            'merovingian': self.storage_root / 'merovingian', # Logs, telemetry
            'trinity': self.storage_root / 'trinity',   # Dashboard exports
            'uploads': self.storage_root / 'uploads',   # User uploads (inbox)
            'temp': self.storage_root / 'temp',         # Temporary files
        }

        for floor_dir in self.floors.values():
            floor_dir.mkdir(exist_ok=True)

    def get_floor_path(self, floor: str) -> Path:
        """
        Return the storage directory for a floor key.

        Compatibility shim: some floor tooling expects this helper for indexing and
        projections into floor-native storage areas.
        """
        key = (floor or "").strip().lower() or "uploads"
        p = self.floors.get(key)
        if p is None:
            p = self.storage_root / key
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return p

    def _calculate_checksum(self, filepath: Path) -> str:
        """
        Calculate SHA256 checksum of file.

        Parameters:
            filepath: Path to file

        Returns:
            Hexadecimal checksum string
        """
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def save_file(self, source_path: Path, floor: str = 'uploads',
                  filename: Optional[str] = None, user_id: int = 1,
                  auto_analyze: bool = True) -> Dict[str, Any]:
        """
        Save file to storage and register in database.

        Parameters:
            source_path: Source file path
            floor: Target floor (neo, morpheus, architect, etc.)
            filename: Target filename (default: source filename)
            user_id: User ID uploading file
            auto_analyze: Whether to trigger Morpheus analysis

        Returns:
            Dict with file info (file_id, path, checksum, etc.)
        """
        source_path = Path(source_path)

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Determine target filename and path
        if filename is None:
            filename = source_path.name

        target_dir = self.floors.get(floor, self.floors['uploads'])
        target_path = target_dir / filename

        # Handle filename conflicts
        if target_path.exists():
            base, ext = os.path.splitext(filename)
            counter = 1
            while target_path.exists():
                filename = f"{base}_{counter}{ext}"
                target_path = target_dir / filename
                counter += 1

        # Copy file to storage
        shutil.copy2(source_path, target_path)
        logger.info(f"File saved: {filename} to {floor} floor")

        # Calculate file metadata
        file_size = target_path.stat().st_size
        checksum = self._calculate_checksum(target_path)
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        extension = Path(filename).suffix or source_path.suffix or ''

        # Register in database (Morpheus layer)
        file_id = self.db.register_file(
            filename=filename,
            filepath=str(target_path),
            file_type=extension,
            size_bytes=file_size,
            checksum=checksum
        )

        # Publish event
        self.event_bus.publish(Event(
            type=EventTypes.FILE_UPLOADED,
            source='Storage',
            data={
                'file_id': file_id,
                'filename': filename,
                'floor': floor,
                'size_bytes': file_size,
                'file_type': extension,
                'mime_type': mime_type,
                'user_id': user_id
            }
        ))

        logger.operation("save_file", status="completed", extra_data={
            'file_id': file_id,
            'filename': filename,
            'floor': floor
        })

        return {
            'file_id': file_id,
            'filename': filename,
            'path': str(target_path),
            'floor': floor,
            'size_bytes': file_size,
            'checksum': checksum,
            'file_type': extension,
            'mime_type': mime_type,
        }

    def store_file(
        self,
        source_path: Path,
        floor: str = "uploads",
        namespace: Optional[str] = None,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: int = 1,
        auto_analyze: bool = True,
    ) -> int:
        """
        Compatibility + project-friendly storage entry point.

        `namespace` creates a subfolder under the floor directory (e.g. `oracle/inbox/`).
        Returns the registered `file_id`.
        """
        source_path = Path(source_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        if filename is None:
            filename = source_path.name

        floor_key = (floor or "uploads").strip().lower()
        base_dir = self.floors.get(floor_key)
        if base_dir is None:
            base_dir = self.storage_root / floor_key
            base_dir.mkdir(parents=True, exist_ok=True)

        target_dir = base_dir
        if namespace:
            ns = str(namespace).strip().strip("/").strip("\\")
            if ns:
                target_dir = base_dir / ns
                target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / filename
        if target_path.exists():
            base, ext = os.path.splitext(filename)
            counter = 1
            while target_path.exists():
                candidate = f"{base}_{counter}{ext}"
                target_path = target_dir / candidate
                counter += 1

        shutil.copy2(source_path, target_path)

        file_size = target_path.stat().st_size
        checksum = self._calculate_checksum(target_path)
        mime_type = mimetypes.guess_type(target_path.name)[0] or "application/octet-stream"
        extension = target_path.suffix

        file_metadata: Dict[str, Any] = {"floor": floor_key, "namespace": namespace, "mime_type": mime_type}
        if metadata:
            try:
                file_metadata.update(metadata)
            except Exception:
                pass

        file_id = self.db.register_file(
            filename=target_path.name,
            filepath=str(target_path),
            file_type=extension,
            size_bytes=file_size,
            checksum=checksum,
            metadata=file_metadata,
        )

        # Best-effort event publish (do not crash if disabled)
        try:
            self.event_bus.publish(
                Event(
                    type=EventTypes.FILE_UPLOADED,
                    source="Storage",
                    data={
                        "file_id": file_id,
                        "filename": target_path.name,
                        "floor": floor_key,
                        "namespace": namespace,
                        "size_bytes": file_size,
                        "file_type": extension,
                        "mime_type": mime_type,
                        "user_id": user_id,
                    },
                )
            )
        except Exception:
            pass

        return int(file_id)

    def get_file_path(self, file_id: int) -> Optional[Path]:
        """
        Get file path from database.

        Parameters:
            file_id: File ID

        Returns:
            Path object or None if not found
        """
        file_info = self.db.get_file_analysis(file_id)
        if file_info and file_info.get('path'):
            return Path(file_info['path'])
        return None

    def read_file(self, file_id: int) -> Optional[bytes]:
        """
        Read file contents.

        Parameters:
            file_id: File ID

        Returns:
            File contents as bytes or None
        """
        filepath = self.get_file_path(file_id)
        if filepath and filepath.exists():
            with open(filepath, 'rb') as f:
                return f.read()
        return None

    def delete_file(self, file_id: int, user_id: int = 1) -> bool:
        """
        Delete file from storage and database.

        Parameters:
            file_id: File ID
            user_id: User requesting deletion

        Returns:
            True if successful
        """
        filepath = self.get_file_path(file_id)

        if filepath and filepath.exists():
            # Move to trash instead of permanent deletion
            trash_dir = self.storage_root / 'trash'
            trash_dir.mkdir(exist_ok=True)

            trash_path = trash_dir / f"{file_id}_{filepath.name}"
            shutil.move(str(filepath), str(trash_path))

            # Update database status
            self.db.execute_update(
                "UPDATE files SET status = 'deleted', deleted_at = ? WHERE id = ?",
                (datetime.now().isoformat(), file_id)
            )

            logger.info(f"File deleted (moved to trash): {filepath.name} (ID: {file_id})")
            return True

        return False

    def list_files(
        self,
        floor: Optional[str] = None,
        namespace: Optional[str] = None,
        file_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List files in storage.

        Parameters:
            floor: Filter by floor
            file_type: Filter by MIME type
            limit: Maximum results

        Returns:
            List of file info dicts
        """
        query = "SELECT * FROM files WHERE status != 'deleted'"
        params = []

        if floor:
            # Stored paths are OS-native; normalize to forward slashes for portable matching.
            floor_clean = str(floor).strip().strip("/").strip("\\")
            ns_clean = str(namespace).strip().strip("/").strip("\\") if namespace else ""
            if ns_clean:
                like_fwd = f"%/{floor_clean}/{ns_clean}/%"
            else:
                like_fwd = f"%/{floor_clean}/%"
            query += " AND REPLACE(path, '\\', '/') LIKE ?"
            params.append(like_fwd)

        if file_type:
            query += " AND extension LIKE ?"
            params.append(f"%{file_type}%")

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        return self.db.execute_query(query, tuple(params))

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dict with storage stats (total files, size, per-floor breakdown)
        """
        stats = {
            'total_files': 0,
            'total_size_bytes': 0,
            'total_size_mb': 0,
            'by_floor': {}
        }

        # Get all active files
        files = self.db.execute_query(
            "SELECT path, size_bytes FROM files WHERE status != 'deleted'"
        )

        stats['total_files'] = len(files)
        stats['total_size_bytes'] = sum(f.get('size_bytes', 0) for f in files)
        stats['total_size_mb'] = stats['total_size_bytes'] / (1024 * 1024)

        # Per-floor breakdown
        for floor_name, floor_path in self.floors.items():
            floor_files = [f for f in files if str(floor_path) in f.get('path', '')]
            if floor_files:
                stats['by_floor'][floor_name] = {
                    'file_count': len(floor_files),
                    'size_bytes': sum(f['size_bytes'] for f in floor_files),
                    'size_mb': sum(f['size_bytes'] for f in floor_files) / (1024 * 1024)
                }

        return stats

    def verify_file_integrity(self, file_id: int) -> bool:
        """
        Verify file integrity using stored checksum.

        Parameters:
            file_id: File ID

        Returns:
            True if checksum matches
        """
        file_info = self.db.get_file_analysis(file_id)
        if not file_info:
            return False

        filepath = Path(file_info['path'])
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return False

        stored_checksum = file_info.get('hash_sha256')
        if not stored_checksum:
            logger.warning(f"No checksum stored for file {file_id}")
            return False

        current_checksum = self._calculate_checksum(filepath)

        if current_checksum != stored_checksum:
            logger.error(f"Checksum mismatch for file {file_id}: {filepath.name}")
            return False

        return True

    def create_backup(self, file_id: int) -> Optional[Path]:
        """
        Create backup copy of file.

        Parameters:
            file_id: File ID

        Returns:
            Path to backup file or None
        """
        filepath = self.get_file_path(file_id)
        if not filepath or not filepath.exists():
            return None

        backup_dir = self.storage_root / 'backups'
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f"{file_id}_{timestamp}_{filepath.name}"

        shutil.copy2(filepath, backup_path)
        logger.info(f"Backup created: {backup_path.name}")

        return backup_path


# Singleton instance
_storage_service = None


def get_storage() -> StorageService:
    """
    Get global storage service instance (singleton).

    Returns:
        StorageService instance
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


if __name__ == "__main__":
    # Test storage service
    print("Storage Service - File Management Test")
    print("=" * 50)

    storage = get_storage()

    # Test 1: Storage initialization
    print("\nTest 1: Storage initialization")
    print(f"  Storage root: {storage.storage_root}")
    print(f"  Floors configured: {len(storage.floors)}")
    for floor_name in list(storage.floors.keys())[:5]:
        print(f"    - {floor_name}")

    # Test 2: Create test file
    print("\nTest 2: Save test file")
    test_file = storage.storage_root / 'test_file.txt'
    test_file.write_text("LightSpeed test file - ACHILLES platform")

    try:
        result = storage.save_file(
            source_path=test_file,
            floor='morpheus',
            user_id=1
        )
        print(f"  File saved: {result['filename']}")
        print(f"  File ID: {result['file_id']}")
        print(f"  Checksum: {result['checksum'][:16]}...")
        print(f"  Size: {result['size_bytes']} bytes")
    except Exception as e:
        print(f"  Error: {e}")

    # Test 3: Storage stats
    print("\nTest 3: Storage statistics")
    stats = storage.get_storage_stats()
    print(f"  Total files: {stats['total_files']}")
    print(f"  Total size: {stats['total_size_mb']:.2f} MB")
    if stats['by_floor']:
        print(f"  Floors with files: {len(stats['by_floor'])}")

    # Test 4: List files
    print("\nTest 4: List files")
    files = storage.list_files(limit=5)
    print(f"  Found {len(files)} file(s)")
    for f in files[:3]:
        print(f"    - {f.get('filename', 'unknown')} ({f.get('size_bytes', 0)} bytes)")

    # Cleanup
    if test_file.exists():
        test_file.unlink()

    print("\n" + "=" * 50)
    print("Storage service ready for file management across all floors!")
