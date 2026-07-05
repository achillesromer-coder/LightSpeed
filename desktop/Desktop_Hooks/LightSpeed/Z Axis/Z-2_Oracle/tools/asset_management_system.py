#!/usr/bin/env python
"""
COMPREHENSIVE ASSET MANAGEMENT SYSTEM
Central hub for managing all LightSpeed assets: calculators, datasets, tools, UI components

Features:
- Centralized asset registry
- Auto-discovery and registration
- Version control and updates
- Dependency management
- Usage analytics
- Asset health monitoring
- Integration with smart floor

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 20, 2026
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

# Setup paths
ORACLE_ROOT = Path(__file__).parent.parent.resolve()
LIGHTSPEED_ROOT = ORACLE_ROOT.parent.parent
Z_AXIS_ROOT = LIGHTSPEED_ROOT / "Z Axis"
MORPHEUS_ROOT = Z_AXIS_ROOT / "Z-1_Morpheus"
CONSTRUCT_ROOT = Z_AXIS_ROOT / "Z0_TheConstruct"

sys.path.insert(0, str(LIGHTSPEED_ROOT))
sys.path.insert(0, str(MORPHEUS_ROOT))

# Import database models
try:
    from database.models.calculators import CalculatorModule, CalculatorUsage
    from database.models.datasets import ScientificDataset
    from database.models.floors import ZFloorFunction, FloorDirectoryStructure
    from database.base import get_session, init_db
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False
    print("[WARNING] Database models not available")


class AssetType:
    """Asset type enumeration"""
    CALCULATOR = 'calculator'
    DATASET = 'dataset'
    TOOL = 'tool'
    UI_COMPONENT = 'ui_component'
    DOCUMENTATION = 'documentation'
    FLOOR_FUNCTION = 'floor_function'


class AssetStatus:
    """Asset status enumeration"""
    ACTIVE = 'active'
    DEPRECATED = 'deprecated'
    TESTING = 'testing'
    INACTIVE = 'inactive'
    MISSING = 'missing'
    ERROR = 'error'


class Asset:
    """Represents a single asset"""

    def __init__(self,
                 name: str,
                 asset_type: str,
                 path: str,
                 floor: str,
                 category: str = None,
                 status: str = AssetStatus.ACTIVE,
                 version: str = '1.0.0',
                 dependencies: List[str] = None,
                 metadata: Dict = None):
        self.name = name
        self.asset_type = asset_type
        self.path = path
        self.floor = floor
        self.category = category
        self.status = status
        self.version = version
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.last_accessed = None
        self.access_count = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'asset_type': self.asset_type,
            'path': self.path,
            'floor': self.floor,
            'category': self.category,
            'status': self.status,
            'version': self.version,
            'dependencies': self.dependencies,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'access_count': self.access_count
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Asset':
        """Create from dictionary"""
        asset = cls(
            name=data['name'],
            asset_type=data['asset_type'],
            path=data['path'],
            floor=data['floor'],
            category=data.get('category'),
            status=data.get('status', AssetStatus.ACTIVE),
            version=data.get('version', '1.0.0'),
            dependencies=data.get('dependencies', []),
            metadata=data.get('metadata', {})
        )

        # Restore timestamps
        if 'created_at' in data:
            asset.created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data:
            asset.updated_at = datetime.fromisoformat(data['updated_at'])
        if data.get('last_accessed'):
            asset.last_accessed = datetime.fromisoformat(data['last_accessed'])
        asset.access_count = data.get('access_count', 0)

        return asset

    def record_access(self):
        """Record that this asset was accessed"""
        self.last_accessed = datetime.now()
        self.access_count += 1
        self.updated_at = datetime.now()

    def check_health(self) -> Tuple[bool, str]:
        """
        Check asset health.

        Returns:
            Tuple of (is_healthy, message)
        """
        # Check if file exists
        if not Path(self.path).exists():
            return False, f"File not found: {self.path}"

        # Check dependencies
        for dep in self.dependencies:
            if not self._check_dependency(dep):
                return False, f"Missing dependency: {dep}"

        return True, "OK"

    def _check_dependency(self, dep: str) -> bool:
        """Check if a dependency is available"""
        # Try importing as Python module
        try:
            __import__(dep)
            return True
        except ImportError:
            pass

        # Try as file path
        if Path(dep).exists():
            return True

        return False


class AssetManagementSystem:
    """
    Comprehensive asset management system for LightSpeed.

    Manages all assets across the Z-axis floors.
    """

    def __init__(self):
        """Initialize asset management system"""
        self.session = None
        self.assets = {}  # name -> Asset
        self.assets_by_type = defaultdict(list)
        self.assets_by_floor = defaultdict(list)
        self.assets_by_category = defaultdict(list)

        # Registry file
        self.registry_file = ORACLE_ROOT / "data" / "asset_registry.json"
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database connection
        if HAS_DATABASE:
            try:
                init_db()
                self.session = get_session()
                print("[ASSETS] Database connection established")
            except Exception as e:
                print(f"[ASSETS] Failed to connect to database: {e}")

        # Load registry
        self._load_registry()

        # If empty, discover assets
        if not self.assets:
            self.discover_all_assets()

    def _load_registry(self):
        """Load asset registry from disk"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for asset_data in data.get('assets', []):
                    asset = Asset.from_dict(asset_data)
                    self.register_asset(asset, save=False)

                print(f"[ASSETS] Loaded {len(self.assets)} assets from registry")
            except Exception as e:
                print(f"[ASSETS] Failed to load registry: {e}")

    def _save_registry(self):
        """Save asset registry to disk"""
        try:
            data = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'asset_count': len(self.assets),
                'assets': [asset.to_dict() for asset in self.assets.values()]
            }

            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            print(f"[ASSETS] Saved {len(self.assets)} assets to registry")
        except Exception as e:
            print(f"[ASSETS] Failed to save registry: {e}")

    def register_asset(self, asset: Asset, save: bool = True):
        """Register an asset"""
        # Add to main registry
        self.assets[asset.name] = asset

        # Add to type index
        self.assets_by_type[asset.asset_type].append(asset)

        # Add to floor index
        self.assets_by_floor[asset.floor].append(asset)

        # Add to category index
        if asset.category:
            self.assets_by_category[asset.category].append(asset)

        # Save to disk
        if save:
            self._save_registry()

    def unregister_asset(self, name: str):
        """Unregister an asset"""
        if name in self.assets:
            asset = self.assets[name]

            # Remove from indices
            self.assets_by_type[asset.asset_type].remove(asset)
            self.assets_by_floor[asset.floor].remove(asset)
            if asset.category:
                self.assets_by_category[asset.category].remove(asset)

            # Remove from main registry
            del self.assets[name]

            # Save
            self._save_registry()

    def get_asset(self, name: str) -> Optional[Asset]:
        """Get asset by name"""
        return self.assets.get(name)

    def get_assets_by_type(self, asset_type: str) -> List[Asset]:
        """Get all assets of a specific type"""
        return self.assets_by_type.get(asset_type, [])

    def get_assets_by_floor(self, floor: str) -> List[Asset]:
        """Get all assets on a specific floor"""
        return self.assets_by_floor.get(floor, [])

    def get_assets_by_category(self, category: str) -> List[Asset]:
        """Get all assets in a specific category"""
        return self.assets_by_category.get(category, [])

    def discover_all_assets(self):
        """Discover all assets across the platform"""
        print("[ASSETS] Discovering assets...")

        # Discover calculators
        self._discover_calculators()

        # Discover datasets
        self._discover_datasets()

        # Discover tools
        self._discover_tools()

        # Discover UI components
        self._discover_ui_components()

        # Discover documentation
        self._discover_documentation()

        # Discover floor functions
        self._discover_floor_functions()

        print(f"[ASSETS] Discovery complete: {len(self.assets)} total assets")

        # Save registry
        self._save_registry()

    def _discover_calculators(self):
        """Discover calculator modules"""
        if HAS_DATABASE and self.session:
            try:
                calculators = self.session.query(CalculatorModule).all()

                for calc in calculators:
                    asset = Asset(
                        name=calc.name,
                        asset_type=AssetType.CALCULATOR,
                        path=calc.filepath,
                        floor=calc.floor or 'Z0_TheConstruct',
                        category=calc.category,
                        status=calc.status,
                        version=calc.version or '1.0.0',
                        dependencies=json.loads(calc.dependencies) if calc.dependencies else [],
                        metadata={
                            'subcategory': calc.subcategory,
                            'description': calc.description,
                            'dataset_requirements': calc.dataset_requirements,
                            'usage_count': calc.usage_count
                        }
                    )

                    self.register_asset(asset, save=False)

                print(f"[ASSETS] Discovered {len(calculators)} calculators")
            except Exception as e:
                print(f"[ASSETS] Failed to discover calculators: {e}")

    def _discover_datasets(self):
        """Discover scientific datasets"""
        if HAS_DATABASE and self.session:
            try:
                datasets = self.session.query(ScientificDataset).all()

                for ds in datasets:
                    asset = Asset(
                        name=ds.filename,
                        asset_type=AssetType.DATASET,
                        path=ds.filepath,
                        floor='Z0_TheConstruct',
                        category=ds.category,
                        status=AssetStatus.ACTIVE,
                        version='1.0.0',
                        metadata={
                            'format': ds.format,
                            'size_gb': ds.size_gb,
                            'mission': ds.mission,
                            'observation_date': str(ds.observation_date) if ds.observation_date else None,
                            'description': ds.description,
                            'access_count': ds.access_count
                        }
                    )

                    self.register_asset(asset, save=False)

                print(f"[ASSETS] Discovered {len(datasets)} datasets")
            except Exception as e:
                print(f"[ASSETS] Failed to discover datasets: {e}")

    def _discover_tools(self):
        """Discover tools in floor /tools/ directories"""
        tool_count = 0

        for floor_dir in Z_AXIS_ROOT.iterdir():
            if floor_dir.is_dir() and floor_dir.name.startswith('Z'):
                tools_dir = floor_dir / "tools"

                if tools_dir.exists():
                    for py_file in tools_dir.glob("*.py"):
                        if py_file.name.startswith('_'):
                            continue

                        asset = Asset(
                            name=py_file.stem,
                            asset_type=AssetType.TOOL,
                            path=str(py_file),
                            floor=floor_dir.name,
                            category='tool',
                            metadata={
                                'file_type': 'python',
                                'size_kb': py_file.stat().st_size / 1024
                            }
                        )

                        self.register_asset(asset, save=False)
                        tool_count += 1

        print(f"[ASSETS] Discovered {tool_count} tools")

    def _discover_ui_components(self):
        """Discover UI components"""
        trinity_root = Z_AXIS_ROOT / "Z+3_Trinity"
        component_dirs = ['components', 'ui', 'wizards']
        ui_count = 0

        for comp_dir_name in component_dirs:
            comp_dir = trinity_root / comp_dir_name

            if comp_dir.exists():
                for py_file in comp_dir.glob("*.py"):
                    if py_file.name.startswith('_'):
                        continue

                    asset = Asset(
                        name=py_file.stem,
                        asset_type=AssetType.UI_COMPONENT,
                        path=str(py_file),
                        floor='Z+3_Trinity',
                        category=comp_dir_name,
                        metadata={
                            'file_type': 'python',
                            'size_kb': py_file.stat().st_size / 1024
                        }
                    )

                    self.register_asset(asset, save=False)
                    ui_count += 1

        print(f"[ASSETS] Discovered {ui_count} UI components")

    def _discover_documentation(self):
        """Discover documentation files"""
        docs_path = LIGHTSPEED_ROOT / "ai_logs" / "reports"
        doc_count = 0

        if docs_path.exists():
            for md_file in docs_path.rglob("*.md"):
                asset = Asset(
                    name=md_file.stem,
                    asset_type=AssetType.DOCUMENTATION,
                    path=str(md_file),
                    floor='Z-1_Morpheus',
                    category=md_file.parent.name,
                    metadata={
                        'file_type': 'markdown',
                        'size_kb': md_file.stat().st_size / 1024
                    }
                )

                self.register_asset(asset, save=False)
                doc_count += 1

        print(f"[ASSETS] Discovered {doc_count} documentation files")

    def _discover_floor_functions(self):
        """Discover floor functions from database"""
        if HAS_DATABASE and self.session:
            try:
                functions = self.session.query(ZFloorFunction).all()

                for func in functions:
                    asset = Asset(
                        name=func.function_name,
                        asset_type=AssetType.FLOOR_FUNCTION,
                        path=func.file_location,
                        floor=func.floor,
                        category=func.function_type,
                        status=func.status,
                        metadata={
                            'purpose': func.purpose,
                            'line_number': func.line_number,
                            'input_types': func.input_types,
                            'output_types': func.output_types,
                            'dependencies': func.dependencies
                        }
                    )

                    self.register_asset(asset, save=False)

                print(f"[ASSETS] Discovered {len(functions)} floor functions")
            except Exception as e:
                print(f"[ASSETS] Failed to discover floor functions: {e}")

    def check_asset_health(self, name: str) -> Tuple[bool, str]:
        """Check health of a specific asset"""
        asset = self.get_asset(name)
        if not asset:
            return False, "Asset not found"

        return asset.check_health()

    def check_all_asset_health(self) -> Dict[str, Tuple[bool, str]]:
        """Check health of all assets"""
        results = {}

        for name, asset in self.assets.items():
            results[name] = asset.check_health()

        return results

    def get_broken_assets(self) -> List[Asset]:
        """Get list of broken/unhealthy assets"""
        broken = []

        for asset in self.assets.values():
            is_healthy, _ = asset.check_health()
            if not is_healthy:
                broken.append(asset)

        return broken

    def get_recently_accessed(self, limit: int = 10) -> List[Asset]:
        """Get recently accessed assets"""
        # Filter assets with access timestamp
        accessed = [a for a in self.assets.values() if a.last_accessed]

        # Sort by last accessed (most recent first)
        accessed.sort(key=lambda a: a.last_accessed, reverse=True)

        return accessed[:limit]

    def get_most_used(self, limit: int = 10) -> List[Asset]:
        """Get most frequently used assets"""
        # Filter assets with access count
        used = [a for a in self.assets.values() if a.access_count > 0]

        # Sort by access count (highest first)
        used.sort(key=lambda a: a.access_count, reverse=True)

        return used[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get asset statistics"""
        stats = {
            'total_assets': len(self.assets),
            'by_type': {},
            'by_floor': {},
            'by_status': {},
            'by_category': {},
            'health': {
                'healthy': 0,
                'broken': 0
            },
            'usage': {
                'total_accesses': sum(a.access_count for a in self.assets.values()),
                'accessed_assets': len([a for a in self.assets.values() if a.access_count > 0]),
                'never_accessed': len([a for a in self.assets.values() if a.access_count == 0])
            }
        }

        # Count by type
        for asset_type, assets in self.assets_by_type.items():
            stats['by_type'][asset_type] = len(assets)

        # Count by floor
        for floor, assets in self.assets_by_floor.items():
            stats['by_floor'][floor] = len(assets)

        # Count by status
        for asset in self.assets.values():
            stats['by_status'][asset.status] = stats['by_status'].get(asset.status, 0) + 1

        # Count by category
        for category, assets in self.assets_by_category.items():
            stats['by_category'][category] = len(assets)

        # Check health
        for asset in self.assets.values():
            is_healthy, _ = asset.check_health()
            if is_healthy:
                stats['health']['healthy'] += 1
            else:
                stats['health']['broken'] += 1

        return stats

    def generate_report(self) -> str:
        """Generate comprehensive asset report"""
        stats = self.get_statistics()

        report = []
        report.append("=" * 70)
        report.append("LIGHTSPEED ASSET MANAGEMENT REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Overview
        report.append("OVERVIEW")
        report.append("-" * 70)
        report.append(f"Total Assets: {stats['total_assets']}")
        report.append("")

        # By Type
        report.append("ASSETS BY TYPE")
        report.append("-" * 70)
        for asset_type, count in sorted(stats['by_type'].items()):
            report.append(f"  {asset_type.title()}: {count}")
        report.append("")

        # By Floor
        report.append("ASSETS BY FLOOR")
        report.append("-" * 70)
        for floor, count in sorted(stats['by_floor'].items()):
            report.append(f"  {floor}: {count}")
        report.append("")

        # By Status
        report.append("ASSETS BY STATUS")
        report.append("-" * 70)
        for status, count in sorted(stats['by_status'].items()):
            report.append(f"  {status.title()}: {count}")
        report.append("")

        # Health
        report.append("ASSET HEALTH")
        report.append("-" * 70)
        report.append(f"  Healthy: {stats['health']['healthy']}")
        report.append(f"  Broken: {stats['health']['broken']}")

        if stats['health']['broken'] > 0:
            report.append("")
            report.append("BROKEN ASSETS:")
            for asset in self.get_broken_assets():
                is_healthy, message = asset.check_health()
                report.append(f"  - {asset.name} ({asset.asset_type}): {message}")
        report.append("")

        # Usage
        report.append("USAGE STATISTICS")
        report.append("-" * 70)
        report.append(f"  Total Accesses: {stats['usage']['total_accesses']}")
        report.append(f"  Accessed Assets: {stats['usage']['accessed_assets']}")
        report.append(f"  Never Accessed: {stats['usage']['never_accessed']}")
        report.append("")

        # Most Used
        report.append("MOST USED ASSETS (Top 10)")
        report.append("-" * 70)
        for i, asset in enumerate(self.get_most_used(10), 1):
            report.append(f"  {i}. {asset.name} ({asset.asset_type}): {asset.access_count} accesses")
        report.append("")

        # Recently Accessed
        report.append("RECENTLY ACCESSED (Top 10)")
        report.append("-" * 70)
        for i, asset in enumerate(self.get_recently_accessed(10), 1):
            time_str = asset.last_accessed.strftime('%Y-%m-%d %H:%M:%S') if asset.last_accessed else 'Never'
            report.append(f"  {i}. {asset.name} ({asset.asset_type}): {time_str}")
        report.append("")

        report.append("=" * 70)

        return "\n".join(report)

    def export_to_json(self, filepath: Path = None) -> str:
        """Export all assets to JSON"""
        if not filepath:
            filepath = ORACLE_ROOT / "data" / f"asset_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = {
            'version': '1.0',
            'exported_at': datetime.now().isoformat(),
            'statistics': self.get_statistics(),
            'assets': [asset.to_dict() for asset in self.assets.values()]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        return str(filepath)


def main():
    """Test the asset management system"""
    print("Initializing Asset Management System...")
    ams = AssetManagementSystem()

    print("\n" + ams.generate_report())

    # Export to JSON
    export_path = ams.export_to_json()
    print(f"\nExported to: {export_path}")


if __name__ == "__main__":
    main()
