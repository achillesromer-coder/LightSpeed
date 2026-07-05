"""
Persistence Mixin - Provides JSON save/load functionality for components

This mixin eliminates duplicated persistence code across 20+ components.
Following Clean Code DRY (Don't Repeat Yourself) principle.

Usage:
    class MyComponent(tk.Frame, PersistenceMixin):
        def __init__(self, parent):
            super().__init__(parent)
            self.data_file = "data/my_component.json"
            self.load_data()

        def save_data(self):
            self.save_json(self.data_file, self.my_data)
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import shutil


class PersistenceMixin:
    """Mixin providing JSON persistence functionality"""

    def save_json(self, file_path: str, data: Any, backup: bool = True) -> bool:
        """
        Save data to JSON file with optional backup

        Args:
            file_path: Path to JSON file
            data: Data to save (must be JSON serializable)
            backup: Create backup before overwriting

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Create backup if file exists
            if backup and os.path.exists(file_path):
                backup_path = f"{file_path}.backup"
                shutil.copy2(file_path, backup_path)

            # Write to temporary file first (atomic write)
            temp_path = f"{file_path}.tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=self._json_serializer)

            # Rename to final path (atomic on most filesystems)
            os.replace(temp_path, file_path)

            return True

        except Exception as e:
            print(f"Error saving JSON to {file_path}: {e}")
            return False

    def load_json(self, file_path: str, default: Any = None) -> Any:
        """
        Load data from JSON file

        Args:
            file_path: Path to JSON file
            default: Default value if file doesn't exist or is invalid

        Returns:
            Loaded data or default value
        """
        try:
            if not os.path.exists(file_path):
                return default if default is not None else {}

            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {file_path}: {e}")
            # Try to load backup
            backup_path = f"{file_path}.backup"
            if os.path.exists(backup_path):
                print(f"Attempting to load backup: {backup_path}")
                return self.load_json(backup_path, default)
            return default if default is not None else {}

        except Exception as e:
            print(f"Error loading JSON from {file_path}: {e}")
            return default if default is not None else {}

    def _json_serializer(self, obj: Any) -> str:
        """Custom JSON serializer for non-standard types"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def merge_json_files(self, source_files: List[str], target_file: str) -> bool:
        """
        Merge multiple JSON files into one

        Args:
            source_files: List of JSON file paths to merge
            target_file: Output file path

        Returns:
            True if successful
        """
        try:
            merged_data = {}

            for source_file in source_files:
                data = self.load_json(source_file, {})
                if isinstance(data, dict):
                    merged_data.update(data)
                else:
                    print(f"Skipping {source_file}: not a dict")

            return self.save_json(target_file, merged_data)

        except Exception as e:
            print(f"Error merging JSON files: {e}")
            return False

    def cleanup_old_backups(self, file_path: str, keep_count: int = 5):
        """
        Clean up old backup files, keeping only the most recent

        Args:
            file_path: Original file path
            keep_count: Number of backups to keep
        """
        try:
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)

            # Find all backup files
            backup_pattern = f"{filename}.backup"
            backups = [
                os.path.join(directory, f)
                for f in os.listdir(directory)
                if f.startswith(filename) and 'backup' in f
            ]

            # Sort by modification time (newest first)
            backups.sort(key=os.path.getmtime, reverse=True)

            # Remove old backups
            for old_backup in backups[keep_count:]:
                os.remove(old_backup)
                print(f"Removed old backup: {old_backup}")

        except Exception as e:
            print(f"Error cleaning up backups: {e}")


class PersistentDict(dict, PersistenceMixin):
    """
    Dictionary that automatically persists to JSON file

    Usage:
        data = PersistentDict("data/my_data.json")
        data['key'] = 'value'  # Automatically saved
        data.commit()  # Explicit save
    """

    def __init__(self, file_path: str, auto_save: bool = False):
        """
        Initialize persistent dictionary

        Args:
            file_path: Path to JSON file
            auto_save: Automatically save on every change
        """
        super().__init__()
        self.file_path = file_path
        self.auto_save = auto_save

        # Load existing data
        data = self.load_json(file_path, {})
        self.update(data)

    def __setitem__(self, key: str, value: Any):
        """Set item and optionally auto-save"""
        super().__setitem__(key, value)
        if self.auto_save:
            self.commit()

    def __delitem__(self, key: str):
        """Delete item and optionally auto-save"""
        super().__delitem__(key)
        if self.auto_save:
            self.commit()

    def commit(self) -> bool:
        """Explicitly save to disk"""
        return self.save_json(self.file_path, dict(self))

    def reload(self):
        """Reload data from disk"""
        self.clear()
        data = self.load_json(self.file_path, {})
        self.update(data)


# Example usage and tests
if __name__ == "__main__":
    import tempfile
    import tkinter as tk

    # Test PersistenceMixin
    class TestComponent(tk.Frame, PersistenceMixin):
        def __init__(self, parent):
            super().__init__(parent)
            self.data_file = os.path.join(tempfile.gettempdir(), "test_component.json")

        def save_test_data(self):
            test_data = {
                "name": "Test Component",
                "version": 1.0,
                "timestamp": datetime.now(),
                "settings": {
                    "theme": "dark",
                    "auto_save": True
                }
            }
            return self.save_json(self.data_file, test_data)

        def load_test_data(self):
            return self.load_json(self.data_file)

    # Test PersistentDict
    print("Testing PersistentDict...")
    temp_file = os.path.join(tempfile.gettempdir(), "test_persistent_dict.json")

    # Create and populate
    data = PersistentDict(temp_file)
    data['name'] = 'LightSpeed'
    data['version'] = '2.0'
    data['components'] = ['Trinity', 'Neo', 'Morpheus']
    data.commit()
    print(f"Saved data: {data}")

    # Reload
    data2 = PersistentDict(temp_file)
    print(f"Reloaded data: {data2}")
    assert data2['name'] == 'LightSpeed', "Data persistence failed!"

    print("\n✅ PersistenceMixin tests passed!")
    print(f"Test file: {temp_file}")
