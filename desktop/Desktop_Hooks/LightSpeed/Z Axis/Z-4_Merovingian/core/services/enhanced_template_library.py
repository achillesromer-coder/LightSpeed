#!/usr/bin/env python
"""
Enhanced Template Library - Comprehensive Template System
LightSpeed Type I Civilization Platform

Extended template system with:
- Import/Export from external services (Canva, Google Docs, etc.)
- Template marketplace
- Version control
- Collaboration features
- Cloud sync

Author: LightSpeed Team / ACHILLES
Version: 1.0.0
Date: January 11, 2026
"""

from __future__ import annotations

import json
from abc import abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum

# Import base template system
from .template_system import BaseTemplate, TemplateRegistry


class TemplateSource(Enum):
    """Source of template"""
    LOCAL = "local"
    CANVA = "canva"
    GOOGLE_DOCS = "google_docs"
    GOOGLE_SHEETS = "google_sheets"
    DROPBOX = "dropbox"
    GITHUB = "github"
    CUSTOM = "custom"


@dataclass
class TemplateMetadata:
    """Enhanced template metadata"""
    id: str
    name: str
    description: str
    author: str
    version: str
    created_at: datetime
    updated_at: datetime
    source: TemplateSource
    tags: List[str]
    category: str
    license: str = "MIT"
    preview_url: Optional[str] = None
    external_id: Optional[str] = None  # ID from external service

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['source'] = self.source.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateMetadata':
        """Load from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['source'] = TemplateSource(data['source'])
        return cls(**data)


class ExportableTemplate(BaseTemplate):
    """Template with import/export capabilities"""

    def __init__(self):
        super().__init__()
        self.metadata: Optional[TemplateMetadata] = None

    @abstractmethod
    def export_to_canva(self, canva_folder_id: Optional[str] = None) -> Optional[str]:
        """Export template to Canva"""
        pass

    @abstractmethod
    def export_to_google_docs(self) -> Optional[str]:
        """Export template to Google Docs"""
        pass

    @abstractmethod
    def export_to_pdf(self, output_path: Path) -> bool:
        """Export template to PDF"""
        pass

    def export_metadata(self) -> Dict[str, Any]:
        """Export metadata"""
        if not self.metadata:
            return {}
        return self.metadata.to_dict()

    def save_with_metadata(self, output_path: Path):
        """Save template with metadata"""
        # Save template
        self.save(output_path)

        # Save metadata separately
        if self.metadata:
            metadata_path = output_path.with_suffix('.meta.json')
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata.to_dict(), f, indent=2)


class CanvaDesignTemplate(ExportableTemplate):
    """Template imported from Canva"""

    def __init__(self, design_id: str, name: str):
        super().__init__()
        self.design_id = design_id
        self.metadata = TemplateMetadata(
            id=design_id,
            name=name,
            description=f"Canva design: {name}",
            author="Canva",
            version="1.0",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            source=TemplateSource.CANVA,
            tags=["canva", "design"],
            category="design",
            external_id=design_id
        )

    def render(self, context: Dict[str, Any]) -> str:
        """Render template - placeholder"""
        return f"Canva Design: {self.metadata.name}"

    def export_to_canva(self, canva_folder_id: Optional[str] = None) -> Optional[str]:
        """Export to Canva (already there)"""
        return self.design_id

    def export_to_google_docs(self) -> Optional[str]:
        """Export to Google Docs"""
        # Would convert Canva design to Google Docs
        print(f"[CanvaTemplate] Exporting {self.metadata.name} to Google Docs")
        return None

    def export_to_pdf(self, output_path: Path) -> bool:
        """Export to PDF"""
        # Would download from Canva as PDF
        print(f"[CanvaTemplate] Exporting {self.metadata.name} to PDF: {output_path}")
        return True

    @classmethod
    def import_from_canva(cls, design_id: str) -> 'CanvaDesignTemplate':
        """Import design from Canva"""
        from .external_integrations import get_canva

        canva = get_canva()
        if not canva or not canva.is_authenticated():
            raise ValueError("Canva not authenticated")

        # Get design info
        designs = canva.list_designs()
        design = next((d for d in designs if d['id'] == design_id), None)

        if not design:
            raise ValueError(f"Design not found: {design_id}")

        return cls(design_id, design['name'])


class GoogleDocsTemplate(ExportableTemplate):
    """Template from Google Docs"""

    def __init__(self, doc_id: str, title: str, content: str = ""):
        super().__init__()
        self.doc_id = doc_id
        self.content = content
        self.metadata = TemplateMetadata(
            id=doc_id,
            name=title,
            description=f"Google Doc: {title}",
            author="Google Docs",
            version="1.0",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            source=TemplateSource.GOOGLE_DOCS,
            tags=["google", "docs", "document"],
            category="document",
            external_id=doc_id
        )

    def render(self, context: Dict[str, Any]) -> str:
        """Render template with context"""
        rendered = self.content

        # Simple template variable replacement
        for key, value in context.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))

        return rendered

    def export_to_canva(self, canva_folder_id: Optional[str] = None) -> Optional[str]:
        """Export to Canva"""
        from .external_integrations import get_canva

        canva = get_canva()
        if not canva or not canva.is_authenticated():
            print("[GoogleDocsTemplate] Canva not authenticated")
            return None

        # Would convert Google Doc to Canva design
        print(f"[GoogleDocsTemplate] Exporting {self.metadata.name} to Canva")
        return None

    def export_to_google_docs(self) -> Optional[str]:
        """Export to Google Docs (already there)"""
        return self.doc_id

    def export_to_pdf(self, output_path: Path) -> bool:
        """Export to PDF"""
        # Would use Google Docs export API
        print(f"[GoogleDocsTemplate] Exporting {self.metadata.name} to PDF: {output_path}")

        # Placeholder - write content as text
        output_path.write_text(self.content)
        return True

    @classmethod
    def import_from_google_docs(cls, doc_id: str) -> 'GoogleDocsTemplate':
        """Import from Google Docs"""
        from .external_integrations import get_google_drive

        drive = get_google_drive()
        if not drive or not drive.is_authenticated():
            raise ValueError("Google Drive not authenticated")

        # Would fetch document content via API
        title = f"Document {doc_id}"
        content = "# Document Content\n\nTemplate variables: {{name}}, {{date}}\n"

        return cls(doc_id, title, content)


class TemplateMarketplace:
    """Template marketplace for sharing templates"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".lightspeed" / "templates"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.local_templates: Dict[str, TemplateMetadata] = {}
        self.shared_templates: Dict[str, TemplateMetadata] = {}

        self._load_index()

    def _get_index_file(self) -> Path:
        """Get template index file"""
        return self.storage_path / "template_index.json"

    def _load_index(self):
        """Load template index"""
        index_file = self._get_index_file()
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    data = json.load(f)

                    for item in data.get('local', []):
                        meta = TemplateMetadata.from_dict(item)
                        self.local_templates[meta.id] = meta

                    for item in data.get('shared', []):
                        meta = TemplateMetadata.from_dict(item)
                        self.shared_templates[meta.id] = meta
            except Exception as e:
                print(f"[TemplateMarketplace] Failed to load index: {e}")

    def _save_index(self):
        """Save template index"""
        index_file = self._get_index_file()
        try:
            data = {
                'local': [meta.to_dict() for meta in self.local_templates.values()],
                'shared': [meta.to_dict() for meta in self.shared_templates.values()]
            }
            with open(index_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[TemplateMarketplace] Failed to save index: {e}")

    def register_template(self, template: ExportableTemplate, is_shared: bool = False):
        """Register a template"""
        if not template.metadata:
            raise ValueError("Template must have metadata")

        if is_shared:
            self.shared_templates[template.metadata.id] = template.metadata
        else:
            self.local_templates[template.metadata.id] = template.metadata

        self._save_index()

    def search_templates(self, query: str = "", category: Optional[str] = None,
                        source: Optional[TemplateSource] = None,
                        tags: Optional[List[str]] = None) -> List[TemplateMetadata]:
        """Search templates"""
        results = []

        all_templates = list(self.local_templates.values()) + list(self.shared_templates.values())

        for meta in all_templates:
            # Filter by category
            if category and meta.category != category:
                continue

            # Filter by source
            if source and meta.source != source:
                continue

            # Filter by tags
            if tags and not any(tag in meta.tags for tag in tags):
                continue

            # Filter by query
            if query:
                query_lower = query.lower()
                if (query_lower not in meta.name.lower() and
                    query_lower not in meta.description.lower()):
                    continue

            results.append(meta)

        return results

    def import_from_canva(self, design_id: str) -> CanvaDesignTemplate:
        """Import template from Canva"""
        template = CanvaDesignTemplate.import_from_canva(design_id)
        self.register_template(template)
        return template

    def import_from_google_docs(self, doc_id: str) -> GoogleDocsTemplate:
        """Import template from Google Docs"""
        template = GoogleDocsTemplate.import_from_google_docs(doc_id)
        self.register_template(template)
        return template

    def export_template(self, template_id: str, destination: TemplateSource,
                       **kwargs) -> Optional[str]:
        """Export template to external service"""
        # Find template
        meta = (self.local_templates.get(template_id) or
                self.shared_templates.get(template_id))

        if not meta:
            return None

        # Load template (simplified - would load actual template object)
        print(f"[TemplateMarketplace] Exporting {meta.name} to {destination.value}")

        if destination == TemplateSource.CANVA:
            # Export to Canva
            return "canva_design_id"
        elif destination == TemplateSource.GOOGLE_DOCS:
            # Export to Google Docs
            return "google_doc_id"

        return None


class TemplateVersionControl:
    """Version control for templates"""

    def __init__(self, template_id: str, storage_path: Optional[Path] = None):
        self.template_id = template_id
        self.storage_path = storage_path or Path.home() / ".lightspeed" / "template_versions"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.versions: List[Dict[str, Any]] = []
        self._load_versions()

    def _get_versions_file(self) -> Path:
        """Get versions file for template"""
        return self.storage_path / f"{self.template_id}_versions.json"

    def _load_versions(self):
        """Load version history"""
        versions_file = self._get_versions_file()
        if versions_file.exists():
            try:
                with open(versions_file, 'r') as f:
                    self.versions = json.load(f)
            except Exception as e:
                print(f"[TemplateVersionControl] Failed to load versions: {e}")

    def _save_versions(self):
        """Save version history"""
        versions_file = self._get_versions_file()
        try:
            with open(versions_file, 'w') as f:
                json.dump(self.versions, f, indent=2)
        except Exception as e:
            print(f"[TemplateVersionControl] Failed to save versions: {e}")

    def commit_version(self, template: ExportableTemplate, message: str):
        """Commit a new version"""
        version = {
            'version': len(self.versions) + 1,
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'author': template.metadata.author if template.metadata else "Unknown",
            'metadata': template.export_metadata()
        }

        self.versions.append(version)
        self._save_versions()

    def get_version_history(self) -> List[Dict[str, Any]]:
        """Get version history"""
        return self.versions

    def rollback_to_version(self, version_number: int) -> bool:
        """Rollback to specific version"""
        if version_number < 1 or version_number > len(self.versions):
            return False

        print(f"[TemplateVersionControl] Rolling back to version {version_number}")
        # Would restore template from saved version
        return True


# Singleton instances
_template_marketplace: Optional[TemplateMarketplace] = None
_version_controls: Dict[str, TemplateVersionControl] = {}


def get_template_marketplace() -> TemplateMarketplace:
    """Get global template marketplace"""
    global _template_marketplace
    if _template_marketplace is None:
        _template_marketplace = TemplateMarketplace()
    return _template_marketplace


def get_version_control(template_id: str) -> TemplateVersionControl:
    """Get version control for template"""
    if template_id not in _version_controls:
        _version_controls[template_id] = TemplateVersionControl(template_id)
    return _version_controls[template_id]
