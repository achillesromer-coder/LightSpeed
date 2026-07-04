"""
LightSpeed V0.9.5 - Multi-Floor Document Objectification
AI-powered document parsing and cross-floor distribution

Achilles AI Integration:
- Extract constants → table them (Morpheus floor)
- Extract tests → simulate them (TheConstruct floor)
- Extract objects → 3D draft them (Design floor)
- Extract tasks → create jobs (Smith floor)
- Track conversation context → store in encyclopedia

Author: LightSpeed Team / ACHILLES
Version: 0.9.5
Date: January 3, 2026
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import sys
import uuid


def _safe_read_text(path: Path, *, max_bytes: int = 200_000) -> str:
    """
    Best-effort text read with a size cap.

    This is used for knowledge proposals; binary/huge files should not be fully loaded.
    """
    try:
        raw = path.read_bytes()
    except Exception:
        return ""

    if not raw:
        return ""

    raw = raw[: max(0, int(max_bytes))]
    # Heuristic: reject "very binary" payloads.
    try:
        nul_ratio = raw.count(b"\x00") / float(len(raw))
        if nul_ratio > 0.02:
            return ""
    except Exception:
        pass

    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(enc, errors="replace")
        except Exception:
            continue
    return ""


def _find_z_direct_service() -> Optional[Any]:
    """
    Load Z Direct service from the Merovingian core (best-effort).

    We keep this dynamic because Z-axis folders use names that aren't always valid
    import packages.
    """
    try:
        ls_root = _find_lightspeed_root()
        z_axis_root = (ls_root / "Z Axis").resolve()
        merovingian_root = (z_axis_root / "Z-4_Merovingian").resolve()
        for p in (ls_root, z_axis_root, merovingian_root):
            try:
                if p.exists() and str(p) not in sys.path:
                    sys.path.insert(0, str(p))
            except Exception:
                pass
        from core.services.dataspace import get_z_direct  # type: ignore

        return get_z_direct()
    except Exception:
        return None

def _find_lightspeed_root() -> Path:
    here = Path(__file__).resolve()
    for cand in (here, *here.parents):
        if (cand / "N.py").exists() and (cand / "Z Axis").exists():
            return cand
    return here.parents[3]


class ObjectType(Enum):
    """Types of objects extracted from documents"""
    CONSTANT = "constant"          # Physical/mathematical constants
    TEST = "test"                  # Test parameters/scenarios
    SIMULATION = "simulation"      # Simulation definitions
    OBJECT_3D = "object_3d"       # 3D models/objects
    TASK = "task"                  # Action items/jobs
    EQUATION = "equation"          # Mathematical equations
    CODE_SNIPPET = "code_snippet" # Code examples
    CONVERSATION = "conversation"  # AI interaction context
    REFERENCE = "reference"        # Cross-references


@dataclass
class ExtractedObject:
    """Object extracted from document"""
    obj_type: ObjectType
    content: str
    context: str  # Surrounding text for context
    target_floor: str  # Which Z-floor should handle this
    metadata: Dict[str, Any]
    source_file: str
    line_number: Optional[int] = None


class DocumentObjectifier:
    """
    AI-powered document parser that distributes content across Z-floors.

    Implements Achilles AI's multi-dimensional tagging wishlist:
    - One document can spawn objects on multiple floors
    - Automatic categorization and routing
    - Relationship tracking across floors
    """

    # Patterns for different object types
    PATTERNS = {
        ObjectType.CONSTANT: [
            r'([A-Z_]+)\s*=\s*([\d.e+-]+)',  # CONSTANT = value
            r'const\s+(\w+)\s*=\s*(.+)',     # const name = value
            r'([A-Z_]+):\s*([\d.e+-]+)\s*\w+',  # CONSTANT: value unit
        ],
        ObjectType.TEST: [
            r'test[_\s](\w+)',  # test_name or test name
            r'def\s+test_(\w+)',  # def test_function
            r'scenario[:\s]+(.+)',  # scenario: description
        ],
        ObjectType.SIMULATION: [
            r'simulate?\s+(.+)',  # simulate something
            r'run[_\s]simulation\s*\((.+)\)',  # run_simulation(params)
        ],
        ObjectType.EQUATION: [
            r'\$(.+?)\$',  # LaTeX: $equation$
            r'\\begin\{equation\}(.+?)\\end\{equation\}',  # LaTeX equation environment
        ],
        ObjectType.CODE_SNIPPET: [
            r'```(\w+)?\n(.+?)\n```',  # Markdown code blocks
            r'`([^`]+)`',  # Inline code
        ],
        ObjectType.TASK: [
            r'TODO[:\s]+(.+)',  # marker: task
            r'\[ \]\s+(.+)',  # [ ] checkbox task
            r'Task[:\s]+(.+)',  # Task: description
        ],
        ObjectType.CONVERSATION: [
            r'(User|Assistant|ACHILLES):\s*(.+)',  # Conversation format
        ],
    }

    # Floor routing rules
    FLOOR_ROUTING = {
        ObjectType.CONSTANT: 'Morpheus',  # Encyclopedia
        ObjectType.TEST: 'TheConstruct',  # Physics/testing
        ObjectType.SIMULATION: 'TheConstruct',
        ObjectType.EQUATION: 'Morpheus',
        ObjectType.CODE_SNIPPET: 'Oracle',  # Archive
        ObjectType.TASK: 'Smith',  # Background jobs
        ObjectType.CONVERSATION: 'Morpheus',  # Knowledge base
        ObjectType.OBJECT_3D: 'Architect',  # Planning/design
    }

    def __init__(self):
        """Initialize document objectifier"""
        self.extracted_objects: List[ExtractedObject] = []

    # =========================================================================
    # Z Direct knowledge proposal staging (Cognigrex spine bootstrap)
    # =========================================================================

    def _extract_title(self, text: str, fallback: str) -> str:
        text = (text or "").strip()
        if not text:
            return fallback
        for line in text.splitlines()[:40]:
            s = (line or "").strip()
            if not s:
                continue
            if s.startswith("#"):
                s = s.lstrip("#").strip()
            if len(s) >= 3:
                return s[:120]
        return fallback

    def _extract_definition(self, text: str) -> str:
        # Keep it short and UI-safe; full content stays in the Oracle vault.
        t = (text or "").strip()
        if not t:
            return ""
        return t[:1600]

    def propose_knowledge_node_from_vault_file(self, vault_file: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a minimal `knowledge_node` payload from an Oracle `vault_file` object payload.

        This is intentionally conservative: it creates one node that summarizes the file.
        """
        if not isinstance(vault_file, dict):
            return None
        if vault_file.get("kind") != "vault_file":
            return None

        path = vault_file.get("path")
        src_name = vault_file.get("source_name") or vault_file.get("name") or "Vault File"
        sha = str(vault_file.get("sha256") or "").strip()
        vault_id = str(vault_file.get("id") or "").strip()

        fp = None
        try:
            fp = Path(str(path)).resolve()
        except Exception:
            fp = None

        text = _safe_read_text(fp) if fp and fp.exists() else ""
        concept = self._extract_title(text, str(src_name))
        definition = self._extract_definition(text)
        if not definition:
            # Fall back to describing the artifact when it's not text.
            definition = f"Artifact: {src_name}"

        node_id = f"kn_{sha[:16]}" if sha else (f"kn_vault_{vault_id}" if vault_id else f"kn_{hashlib.sha256(concept.encode('utf-8', errors='ignore')).hexdigest()[:16]}")

        return {
            "kind": "knowledge_node",
            "id": node_id,
            "concept": concept,
            "definition": definition,
            "domain": "GENERAL",
            "related_concepts": [],
            "sources": [
                {
                    "kind": "vault_file",
                    "id": vault_id,
                    "sha256": sha,
                    "name": str(src_name),
                    "path": str(path) if path is not None else "",
                }
            ],
            "confidence": 0.55 if not text else 0.75,
            "metadata": {
                "proposed_by": "neo.document_objectifier",
                "vault_file_id": vault_id,
                "vault_file_sha256": sha,
            },
        }

    def propose_knowledge_nodes_from_vault_file(
        self,
        vault_file: Dict[str, Any],
        *,
        max_nodes: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Create multiple `knowledge_node` payloads from a vault_file (best-effort).

        This is still conservative and local-only: it uses heuristics to extract a small
        set of candidate concepts, then creates one node per concept. The goal is to
        stage richer proposals for Trinity review without invoking external services.
        """
        if not isinstance(vault_file, dict) or vault_file.get("kind") != "vault_file":
            return []

        base = self.propose_knowledge_node_from_vault_file(vault_file)
        if not isinstance(base, dict):
            return []

        path = vault_file.get("path")
        src_name = vault_file.get("source_name") or vault_file.get("name") or "Vault File"
        sha = str(vault_file.get("sha256") or "").strip()
        vault_id = str(vault_file.get("id") or "").strip()

        fp = None
        try:
            fp = Path(str(path)).resolve()
        except Exception:
            fp = None

        text = _safe_read_text(fp) if fp and fp.exists() else ""
        if not text:
            return [base]

        concepts = self._extract_candidate_concepts(text, fallback=str(src_name))
        if not concepts:
            return [base]

        concepts = concepts[: max(1, int(max_nodes or 1))]
        rels = self._extract_relationships(text, concepts, max_edges=14)
        nodes: List[Dict[str, Any]] = []

        for c in concepts:
            c = (c or "").strip()
            if not c:
                continue
            definition = self._extract_definition_for_concept(text, c) or base.get("definition") or f"Artifact: {src_name}"
            cid = hashlib.sha256(c.lower().encode("utf-8", errors="ignore")).hexdigest()[:8]
            node_id = f"kn_{sha[:12]}_{cid}" if sha else (f"kn_vault_{vault_id}_{cid}" if vault_id else f"kn_{cid}")
            c_rels = [r for r in rels if r.get("from") == c]
            nodes.append(
                {
                    "kind": "knowledge_node",
                    "id": node_id,
                    "concept": c,
                    "definition": definition,
                    "domain": "GENERAL",
                    "related_concepts": [x for x in concepts if x != c],
                    "relationships": c_rels,
                    "sources": list(base.get("sources") or []),
                    "confidence": 0.65,
                    "metadata": {
                        "proposed_by": "neo.document_objectifier",
                        "vault_file_id": vault_id,
                        "vault_file_sha256": sha,
                        "heuristic": True,
                    },
                }
            )

        return nodes or [base]

    def _extract_candidate_concepts(self, text: str, *, fallback: str = "") -> List[str]:
        """
        Heuristic concept extraction (no ML deps).

        Prefer:
        - title-ish first line
        - capitalized multi-word phrases (e.g. "Z Direct", "Romer Industries")
        - common project terms from the snippet
        """
        if not isinstance(text, str):
            return [fallback] if fallback else []

        head = (text.strip().splitlines()[:40] or [])
        first_line = ""
        for ln in head:
            s = (ln or "").strip()
            if s and len(s) <= 120:
                first_line = s
                break

        # Capture short, readable concept phrases.
        # Examples: "Z Direct", "Trinity", "Oracle Smart Floor", "Bento UI"
        phrase_re = re.compile(r"\b[A-Z][A-Za-z0-9_]+(?:\s+[A-Z][A-Za-z0-9_]+){0,3}\b")
        candidates: Dict[str, int] = {}

        for m in phrase_re.finditer(text[:8000]):
            p = (m.group(0) or "").strip()
            if not p:
                continue
            if len(p) < 3 or len(p) > 60:
                continue
            # Drop overly generic phrases.
            if p.lower() in {"this", "that", "these", "those"}:
                continue
            candidates[p] = candidates.get(p, 0) + 1

        ordered = sorted(candidates.items(), key=lambda kv: (-kv[1], len(kv[0])))
        concepts = [c for c, _n in ordered][:12]

        if first_line and first_line not in concepts:
            concepts.insert(0, first_line)

        # Ensure fallback at least exists.
        if fallback and fallback not in concepts:
            concepts.append(fallback)

        # Dedup while preserving order.
        seen = set()
        out = []
        for c in concepts:
            cc = (c or "").strip()
            if not cc:
                continue
            key = cc.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(cc)
        return out

    def _extract_definition_for_concept(self, text: str, concept: str) -> str:
        """Pick a nearby sentence/line as a definition snippet (best-effort)."""
        concept = (concept or "").strip()
        if not concept or not isinstance(text, str) or not text:
            return ""

        # Search for a line containing the concept, then take a small window.
        lines = text.splitlines()
        idx = None
        target = concept.lower()
        for i, ln in enumerate(lines[:600]):
            if target in (ln or "").lower():
                idx = i
                break
        if idx is None:
            return ""

        window = "\n".join([x.strip() for x in lines[idx : idx + 4] if x is not None]).strip()
        if len(window) > 520:
            window = window[:520] + "..."
        return window

    def _extract_relationships(self, text: str, concepts: List[str], *, max_edges: int = 12) -> List[Dict[str, Any]]:
        """
        Heuristic relationship extraction between concepts (no ML deps).

        Current strategy: co-mention proximity within the first chunk of text.
        Returns lightweight edges with an evidence snippet for reviewer context.
        """
        if not isinstance(text, str) or not text or not isinstance(concepts, list) or len(concepts) < 2:
            return []

        chunk = text[:15000]
        low = chunk.lower()

        # First-hit positions (simple + fast). This intentionally trades recall for determinism.
        pos: Dict[str, int] = {}
        for c in concepts:
            cc = (c or "").strip()
            if not cc:
                continue
            i = low.find(cc.lower())
            if i >= 0:
                pos[cc] = i

        edges: List[Dict[str, Any]] = []
        keys = list(pos.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a = keys[i]
                b = keys[j]
                da = abs(pos[a] - pos[b])
                if da > 900:
                    continue

                mid = min(pos[a], pos[b]) + da // 2
                ev_start = max(0, mid - 140)
                ev_end = min(len(chunk), mid + 220)
                evidence = chunk[ev_start:ev_end].replace("\r", " ").replace("\n", " ").strip()
                if len(evidence) > 420:
                    evidence = evidence[:420] + "..."

                edges.append(
                    {
                        "from": a,
                        "to": b,
                        "type": "co_mentioned",
                        "evidence": evidence,
                        "confidence": 0.45,
                    }
                )
                # Mirror edge to make browsing easier without graph logic.
                edges.append(
                    {
                        "from": b,
                        "to": a,
                        "type": "co_mentioned",
                        "evidence": evidence,
                        "confidence": 0.45,
                    }
                )

                if len(edges) >= max(2, int(max_edges or 1)) * 2:
                    return edges[: max(2, int(max_edges or 1)) * 2]

        return edges[: max(2, int(max_edges or 1)) * 2]

    def propose_citation_from_vault_file(self, vault_file: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a minimal citation payload for the top snippet of a vault_file.

        This is a bootstrap citation model so later knowledge nodes can reference
        stable citation IDs rather than duplicating quotes everywhere.
        """
        if not isinstance(vault_file, dict):
            return None
        if vault_file.get("kind") != "vault_file":
            return None

        path = vault_file.get("path")
        src_name = vault_file.get("source_name") or vault_file.get("name") or "Vault File"
        sha = str(vault_file.get("sha256") or "").strip()
        vault_id = str(vault_file.get("id") or "").strip()

        fp = None
        try:
            fp = Path(str(path)).resolve()
        except Exception:
            fp = None

        text = _safe_read_text(fp) if fp and fp.exists() else ""
        snippet = (text or "").strip()
        if snippet:
            snippet = snippet[:800]
        note = f"Snippet from {src_name}"
        quote_hash = hashlib.sha256(snippet.encode("utf-8", errors="ignore")).hexdigest() if snippet else ""
        cit_id = f"cit_{sha[:16]}" if sha else f"cit_vault_{vault_id}" if vault_id else f"cit_{uuid.uuid4().hex[:16]}"

        return {
            "kind": "citation",
            "id": cit_id,
            "vault_file_id": vault_id,
            "note": note,
            "span": {"start": 0, "end": len(snippet)},
            "quote_hash": quote_hash,
            "metadata": {
                "proposed_by": "neo.document_objectifier",
                "vault_file_sha256": sha,
                "snippet": snippet,
            },
        }

    def stage_knowledge_proposal_to_trinity(
        self,
        vault_file: Dict[str, Any],
        *,
        review_channel: str = "Z+3",
        origin_channel: str = "Z+2",
        target_registry_channel: str = "Z-2",
    ) -> Dict[str, Any]:
        """
        Stage a knowledge proposal into Trinity's directed inbox/outbox for approval.

        - The envelope's `channel` is the durable-registry target (default: Z-2 Oracle).
        - The directed peer is the origin (default: Z+2 Neo), so Trinity can send receipts.
        """
        zd = _find_z_direct_service()
        if zd is None:
            return {"success": False, "error": "Z Direct service unavailable"}

        nodes = self.propose_knowledge_nodes_from_vault_file(vault_file, max_nodes=5)
        if not nodes:
            return {"success": False, "error": "Could not build knowledge_node payload(s) from vault_file"}

        citation = self.propose_citation_from_vault_file(vault_file)

        # Stage citation first so reviewers can commit it (optional) before the node.
        staged = 0
        citation_id = None
        if isinstance(citation, dict):
            citation_id = citation.get("id")
            cit_env = zd.make_envelope(
                kind="object",
                channel=str(target_registry_channel),
                z_context="Z+2_Neo",
                source="neo.cognigrex.proposal",
                tags=["proposal", "citation", "cognigrex"],
                payload=citation,
            )
            try:
                zd.append_channel_outbox(from_channel=str(origin_channel), to_channel=str(review_channel), payload=cit_env)
            except Exception:
                pass
            try:
                zd.append_channel_inbox(to_channel=str(review_channel), from_channel=str(origin_channel), payload=cit_env)
            except Exception:
                pass
            staged += 1

        knowledge_ids: List[str] = []
        last_env = None
        for payload in nodes:
            if not isinstance(payload, dict):
                continue
            # If we have a citation, include it in sources for reviewer convenience.
            try:
                if citation_id and isinstance(payload.get("sources"), list):
                    for s in payload["sources"]:
                        if isinstance(s, dict) and "citation_id" not in s:
                            s["citation_id"] = citation_id
            except Exception:
                pass

            env = zd.make_envelope(
                kind="object",
                channel=str(target_registry_channel),
                z_context="Z+2_Neo",
                source="neo.cognigrex.proposal",
                tags=["proposal", "knowledge", "cognigrex"],
                payload=payload,
            )
            last_env = env
            try:
                zd.append_channel_outbox(from_channel=str(origin_channel), to_channel=str(review_channel), payload=env)
            except Exception:
                pass
            try:
                zd.append_channel_inbox(to_channel=str(review_channel), from_channel=str(origin_channel), payload=env)
            except Exception:
                pass
            staged += 1
            try:
                if payload.get("id"):
                    knowledge_ids.append(str(payload.get("id")))
            except Exception:
                pass

        return {
            "success": True,
            "envelope": last_env,
            "knowledge_node_id": (knowledge_ids[0] if knowledge_ids else None),
            "knowledge_node_ids": knowledge_ids,
            "citation_id": citation_id,
            "staged": staged,
        }

    def parse_document(self, file_path: Path) -> List[ExtractedObject]:
        """
        Parse document and extract objects.

        Args:
            file_path: Path to document

        Returns:
            List of extracted objects
        """
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f"[Objectifier] Failed to read {file_path}: {e}")
            return []

        objects = []

        # Extract each object type
        for obj_type, patterns in self.PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)

                for match in matches:
                    # Get context (surrounding lines)
                    start = max(0, match.start() - 100)
                    end = min(len(content), match.end() + 100)
                    context = content[start:end]

                    # Create object
                    obj = ExtractedObject(
                        obj_type=obj_type,
                        content=match.group(0),
                        context=context,
                        target_floor=self.FLOOR_ROUTING.get(obj_type, 'Oracle'),
                        metadata={
                            'pattern': pattern,
                            'groups': match.groups()
                        },
                        source_file=str(file_path),
                        line_number=content[:match.start()].count('\n') + 1
                    )

                    objects.append(obj)

        self.extracted_objects.extend(objects)
        return objects

    def categorize_by_floor(self, objects: Optional[List[ExtractedObject]] = None) -> Dict[str, List[ExtractedObject]]:
        """
        Organize extracted objects by target floor.

        Args:
            objects: Objects to categorize (uses all if None)

        Returns:
            Dictionary mapping floor names to objects
        """
        objects = objects or self.extracted_objects

        by_floor: Dict[str, List[ExtractedObject]] = {}

        for obj in objects:
            floor = obj.target_floor
            if floor not in by_floor:
                by_floor[floor] = []
            by_floor[floor].append(obj)

        return by_floor

    def generate_floor_tasks(self, objects: List[ExtractedObject]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate actionable tasks for each floor from extracted objects.

        Args:
            objects: Extracted objects

        Returns:
            Dictionary mapping floor names to task lists
        """
        tasks_by_floor = {}

        for obj in objects:
            floor = obj.target_floor

            if floor not in tasks_by_floor:
                tasks_by_floor[floor] = []

            # Generate floor-specific task
            task = self._generate_task_for_object(obj)
            if task:
                tasks_by_floor[floor].append(task)

        return tasks_by_floor

    def _generate_task_for_object(self, obj: ExtractedObject) -> Optional[Dict[str, Any]]:
        """Generate task for an object based on type"""

        if obj.obj_type == ObjectType.CONSTANT:
            return {
                'type': 'table_constant',
                'action': 'Add to constants table',
                'data': obj.content,
                'source': obj.source_file,
                'floor': 'Morpheus'
            }

        elif obj.obj_type == ObjectType.TEST:
            return {
                'type': 'create_test',
                'action': 'Create test scenario',
                'data': obj.content,
                'source': obj.source_file,
                'floor': 'TheConstruct'
            }

        elif obj.obj_type == ObjectType.SIMULATION:
            return {
                'type': 'run_simulation',
                'action': 'Execute simulation',
                'data': obj.content,
                'source': obj.source_file,
                'floor': 'TheConstruct'
            }

        elif obj.obj_type == ObjectType.TASK:
            return {
                'type': 'background_job',
                'action': 'Create background job',
                'data': obj.content,
                'source': obj.source_file,
                'floor': 'Smith'
            }

        elif obj.obj_type == ObjectType.CONVERSATION:
            return {
                'type': 'store_context',
                'action': 'Store AI conversation context',
                'data': obj.content,
                'source': obj.source_file,
                'floor': 'Morpheus'
            }

        return None

    def ingest_all_documents(
        self,
        root_directory: str = "Z Axis",
        extensions: List[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        ORACLE INGEST ALL FEATURE
        Recursively ingest all documents from directory tree

        Process:
        1. Scan all Z-floor directories
        2. Identify document types (.txt, .md, .pdf, .json)
        3. Extract all entities (constants, formulas, tasks, etc.)
        4. Build knowledge graph
        5. Create object schemas
        6. Route to appropriate floors

        Args:
            root_directory: Starting directory (default: Z Axis)
            extensions: File extensions to process
            progress_callback: Function to call with progress updates

        Returns:
            Summary of ingested data with counts and categorization
        """
        if extensions is None:
            extensions = ['.txt', '.md', '.json', '.py']  # Skip .pdf for now

        import os
        from datetime import datetime

        ingestion_summary = {
            'start_time': datetime.now().isoformat(),
            'documents_processed': 0,
            'objects_extracted': 0,
            'by_type': {},
            'by_floor': {},
            'by_directory': {},
            'dimensions_found': [],
            'constants_found': [],
            'formulas_found': [],
            'errors': []
        }

        # Build full path
        if not os.path.isabs(root_directory):
            root_path = _find_lightspeed_root() / root_directory
        else:
            root_path = Path(root_directory)

        if not root_path.exists():
            ingestion_summary['errors'].append(f"Root directory not found: {root_path}")
            return ingestion_summary

        # Recursive walk through all files
        for root, dirs, files in os.walk(root_path):
            # Skip certain directories
            skip_dirs = ['__pycache__', '.git', 'node_modules', '.venv', 'legacy_archive']
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            for file in files:
                # Check extension
                if not any(file.endswith(ext) for ext in extensions):
                    continue

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, root_path)

                try:
                    # Process document
                    self.objectify_document(file_path)

                    ingestion_summary['documents_processed'] += 1

                    # Track by directory
                    dir_name = os.path.basename(root)
                    ingestion_summary['by_directory'][dir_name] = \
                        ingestion_summary['by_directory'].get(dir_name, 0) + 1

                    # Progress callback
                    if progress_callback:
                        progress_callback(file_path, ingestion_summary['documents_processed'])

                except Exception as e:
                    ingestion_summary['errors'].append(f"Error processing {rel_path}: {str(e)}")

        # Summarize extracted objects
        ingestion_summary['objects_extracted'] = len(self.extracted_objects)

        # Count by type
        for obj in self.extracted_objects:
            obj_type = obj.obj_type.value
            ingestion_summary['by_type'][obj_type] = \
                ingestion_summary['by_type'].get(obj_type, 0) + 1

        # Count by floor
        by_floor = self.categorize_by_floor()
        for floor, objs in by_floor.items():
            ingestion_summary['by_floor'][floor] = len(objs)

        # Extract specific entities
        for obj in self.extracted_objects:
            if obj.obj_type == ObjectType.CONSTANT:
                ingestion_summary['constants_found'].append(obj.content)
            elif obj.obj_type == ObjectType.EQUATION:
                ingestion_summary['formulas_found'].append(obj.content)

        # Identify dimensions from constants
        dimension_keywords = ['mass', 'length', 'time', 'temperature', 'velocity',
                            'acceleration', 'force', 'energy', 'power', 'charge']
        for const in ingestion_summary['constants_found']:
            for dim in dimension_keywords:
                if dim.lower() in const.lower():
                    if dim not in ingestion_summary['dimensions_found']:
                        ingestion_summary['dimensions_found'].append(dim)

        ingestion_summary['end_time'] = datetime.now().isoformat()

        return ingestion_summary

    def export_to_json(self, output_path: Path):
        """Export extracted objects to JSON"""
        data = {
            'total_objects': len(self.extracted_objects),
            'by_type': {},
            'by_floor': {},
            'objects': [asdict(obj) for obj in self.extracted_objects]
        }

        # Count by type
        for obj in self.extracted_objects:
            obj_type = obj.obj_type.value
            data['by_type'][obj_type] = data['by_type'].get(obj_type, 0) + 1

        # Count by floor
        by_floor = self.categorize_by_floor()
        for floor, objs in by_floor.items():
            data['by_floor'][floor] = len(objs)

        output_path.write_text(json.dumps(data, indent=2, default=str))


class AchillesContextTracker:
    """
    Track Achilles AI conversation context within documents.

    Implements "Conversation Thread Integration" from wishlist.
    """

    def __init__(self):
        self.conversations: List[Dict[str, Any]] = []

    def track_conversation(self, role: str, message: str, document: str, context: Dict[str, Any]):
        """
        Track AI conversation within document context.

        Args:
            role: 'User', 'Assistant', or 'ACHILLES'
            message: Conversation message
            document: Source document
            context: Additional context metadata
        """
        self.conversations.append({
            'role': role,
            'message': message,
            'document': document,
            'timestamp': context.get('timestamp'),
            'floor': context.get('floor'),
            'metadata': context
        })

    def get_document_history(self, document: str) -> List[Dict[str, Any]]:
        """Get all conversations related to a document"""
        return [c for c in self.conversations if c['document'] == document]

    def get_floor_interactions(self, floor: str) -> List[Dict[str, Any]]:
        """Get all AI interactions for a specific floor"""
        return [c for c in self.conversations if c.get('floor') == floor]


# Export
__all__ = ['DocumentObjectifier', 'AchillesContextTracker', 'ExtractedObject', 'ObjectType']
