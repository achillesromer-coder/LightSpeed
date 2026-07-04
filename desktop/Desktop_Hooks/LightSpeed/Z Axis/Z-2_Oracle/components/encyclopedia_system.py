#!/usr/bin/env python
"""
Encyclopedia System - Three Volume Knowledge Repository
Volume 1: Empirical Data (Scientific facts, measurements, known values)
Volume 2: Economic Data (Business, competitors, market intelligence)
Volume 3: Applied Data (Our research, novel discoveries, proprietary methods)

Each volume organized A-Z with umbrella terminology and expandable filesets.
Includes hardcoded multilingual dictionary foundation.

Author: Römer Industries / EMASSC
Version: 0.9.5
Date: December 31, 2025
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


class EncyclopediaVolume(Enum):
    """Encyclopedia volume types"""
    EMPIRICAL = 1  # Scientific facts, textbook data, known values
    ECONOMIC = 2   # Business intelligence, competitors, market data
    APPLIED = 3    # Our research, novel proofs, proprietary discoveries


class EncyclopediaSystem:
    """
    Three-Volume Encyclopedia System with Multilingual Dictionary

    Organizes all knowledge into three encyclopedias:
    1. Empirical: Universal scientific facts and measurements
    2. Economic: Business and economic intelligence
    3. Applied: Our proprietary research and discoveries

    Each entry includes:
    - Umbrella term (folder category A-Z)
    - Simplified definition
    - Expanded technical details
    - Related terms and cross-references
    - Multilingual translations
    - Data objects, parameters, ranges
    - Lifecycle information
    - Source references
    """

    def __init__(self, base_path: str = None, db=None, logger=None, *, storage_mode: Optional[str] = None):
        """Initialize Encyclopedia System.

        storage_mode:
            - "disk": JSON-per-entry under `Data/encyclopedia` (legacy)
            - "db": store/load from the unified database only (preferred for consolidation)
            - None: auto ("db" when db is provided, else "disk")
        """
        self.logger = logger
        self.db = db

        mode = (storage_mode or "").strip().lower() or None
        if mode not in (None, "disk", "db"):
            mode = None
        self.storage_mode = mode or ("db" if self.db else "disk")

        # Base path for encyclopedia storage
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(__file__).parent.parent / "Data" / "encyclopedia"

        # Create volume directories (disk mode only)
        self.volumes = {
            EncyclopediaVolume.EMPIRICAL: self.base_path / "Volume_1_Empirical",
            EncyclopediaVolume.ECONOMIC: self.base_path / "Volume_2_Economic",
            EncyclopediaVolume.APPLIED: self.base_path / "Volume_3_Applied"
        }

        if self.storage_mode == "disk":
            for volume_path in self.volumes.values():
                volume_path.mkdir(parents=True, exist_ok=True)

                # Create A-Z umbrella directories
                for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    (volume_path / letter).mkdir(exist_ok=True)

        # Multilingual dictionary (hardcoded foundation)
        self.dictionary = self._initialize_multilingual_dictionary()

        # Entry index (in-memory cache)
        self.entry_index = {}

        # Load existing entries
        if self.storage_mode == "db" and self.db is not None:
            self._load_entry_index_from_db()
        else:
            self._load_entry_index()

        if self.logger:
            self.logger.info("[Encyclopedia] Encyclopedia System initialized (3 volumes, A-Z organization)")

    def _load_entry_index_from_db(self) -> None:
        """Load all existing entries into index from the unified database (preferred)."""
        try:
            rows = self.db.execute_query(
                """
                SELECT id, term, volume, category_letter, definition, data_object, references_json, metadata_json, created_at, updated_at
                FROM encyclopedia_entries
                ORDER BY term ASC
                """
            )
        except Exception as e:
            if self.logger:
                self.logger.warning(f"[Encyclopedia] Failed to load entries from DB: {e}")
            self._load_entry_index()
            return

        for row in rows or []:
            try:
                entry_id = int(row.get('id'))
                term = str(row.get('term') or '').strip()
                volume = str(row.get('volume') or '').strip()
                if not term or not volume:
                    continue

                data_object: Dict[str, Any] = {}
                raw_data = row.get('data_object')
                if isinstance(raw_data, str) and raw_data.strip():
                    try:
                        data_object = json.loads(raw_data)
                    except Exception:
                        data_object = {}

                references: List[str] = []
                raw_refs = row.get('references_json')
                if isinstance(raw_refs, str) and raw_refs.strip():
                    try:
                        parsed = json.loads(raw_refs)
                        if isinstance(parsed, list):
                            references = [str(x) for x in parsed if x is not None]
                    except Exception:
                        references = []

                metadata: Dict[str, Any] = {}
                raw_meta = row.get('metadata_json')
                if isinstance(raw_meta, str) and raw_meta.strip():
                    try:
                        parsed = json.loads(raw_meta)
                        if isinstance(parsed, dict):
                            metadata = parsed
                    except Exception:
                        metadata = {}

                entry = {
                    'term': term,
                    'volume': volume,
                    'category_letter': row.get('category_letter') or (term[0].upper() if term else None),
                    'definition': row.get('definition') or '',
                    'data_object': data_object or {},
                    'references': references or [],
                    'metadata': metadata or {},
                    'created_at': row.get('created_at'),
                    'updated_at': row.get('updated_at'),
                    'entry_id': entry_id,
                }

                if term.lower() in self.dictionary:
                    entry['translations'] = self.dictionary[term.lower()]

                self.entry_index[entry_id] = entry
            except Exception:
                continue

        if self.logger:
            self.logger.info(f"[Encyclopedia] Loaded {len(self.entry_index)} entries from DB")

    def _initialize_multilingual_dictionary(self) -> Dict[str, Dict[str, str]]:
        """
        Initialize hardcoded multilingual dictionary foundation

        Foundation dictionary with essential scientific and technical terms
        in multiple languages (English, German, French, Spanish, Mandarin)
        """
        dictionary = {
            # Physics & Engineering
            "energy": {
                "en": "energy",
                "de": "Energie",
                "fr": "énergie",
                "es": "energía",
                "zh": "能量",
                "definition": "Capacity to do work, measured in Joules (J)",
                "si_unit": "J",
                "formula": "E = mc²",
                "umbrella": "Physics"
            },
            "force": {
                "en": "force",
                "de": "Kraft",
                "fr": "force",
                "es": "fuerza",
                "zh": "力",
                "definition": "Interaction that changes motion, measured in Newtons (N)",
                "si_unit": "N",
                "formula": "F = ma",
                "umbrella": "Physics"
            },
            "mass": {
                "en": "mass",
                "de": "Masse",
                "fr": "masse",
                "es": "masa",
                "zh": "质量",
                "definition": "Amount of matter in object, measured in kilograms (kg)",
                "si_unit": "kg",
                "umbrella": "Physics"
            },
            "temperature": {
                "en": "temperature",
                "de": "Temperatur",
                "fr": "température",
                "es": "temperatura",
                "zh": "温度",
                "definition": "Measure of thermal energy, measured in Kelvin (K)",
                "si_unit": "K",
                "umbrella": "Thermodynamics"
            },
            "velocity": {
                "en": "velocity",
                "de": "Geschwindigkeit",
                "fr": "vitesse",
                "es": "velocidad",
                "zh": "速度",
                "definition": "Rate of change of position, measured in meters per second (m/s)",
                "si_unit": "m/s",
                "formula": "v = Δx/Δt",
                "umbrella": "Kinematics"
            },

            # Mathematics
            "integral": {
                "en": "integral",
                "de": "Integral",
                "fr": "intégrale",
                "es": "integral",
                "zh": "积分",
                "definition": "Mathematical operation finding area under curve",
                "umbrella": "Calculus"
            },
            "derivative": {
                "en": "derivative",
                "de": "Ableitung",
                "fr": "dérivée",
                "es": "derivada",
                "zh": "导数",
                "definition": "Rate of change of function",
                "umbrella": "Calculus"
            },
            "matrix": {
                "en": "matrix",
                "de": "Matrix",
                "fr": "matrice",
                "es": "matriz",
                "zh": "矩阵",
                "definition": "Rectangular array of numbers",
                "umbrella": "Linear Algebra"
            },

            # Chemistry
            "molecule": {
                "en": "molecule",
                "de": "Molekül",
                "fr": "molécule",
                "es": "molécula",
                "zh": "分子",
                "definition": "Group of atoms bonded together",
                "umbrella": "Chemistry"
            },
            "reaction": {
                "en": "reaction",
                "de": "Reaktion",
                "fr": "réaction",
                "es": "reacción",
                "zh": "反应",
                "definition": "Process where substances transform into new substances",
                "umbrella": "Chemistry"
            },

            # Economics & Business
            "revenue": {
                "en": "revenue",
                "de": "Umsatz",
                "fr": "revenu",
                "es": "ingresos",
                "zh": "收入",
                "definition": "Total income from business activities",
                "umbrella": "Economics"
            },
            "profit": {
                "en": "profit",
                "de": "Gewinn",
                "fr": "bénéfice",
                "es": "beneficio",
                "zh": "利润",
                "definition": "Revenue minus expenses",
                "umbrella": "Economics"
            },
            "market": {
                "en": "market",
                "de": "Markt",
                "fr": "marché",
                "es": "mercado",
                "zh": "市场",
                "definition": "System where buyers and sellers exchange goods/services",
                "umbrella": "Economics"
            },

            # Technology
            "algorithm": {
                "en": "algorithm",
                "de": "Algorithmus",
                "fr": "algorithme",
                "es": "algoritmo",
                "zh": "算法",
                "definition": "Step-by-step procedure for calculations",
                "umbrella": "Computer Science"
            },
            "database": {
                "en": "database",
                "de": "Datenbank",
                "fr": "base de données",
                "es": "base de datos",
                "zh": "数据库",
                "definition": "Organized collection of structured information",
                "umbrella": "Computer Science"
            },
            "network": {
                "en": "network",
                "de": "Netzwerk",
                "fr": "réseau",
                "es": "red",
                "zh": "网络",
                "definition": "Interconnected system of computers/devices",
                "umbrella": "Computer Science"
            }
        }

        # Add SI units
        si_units = {
            "meter": {"en": "meter", "de": "Meter", "fr": "mètre", "es": "metro", "zh": "米", "symbol": "m", "type": "length"},
            "kilogram": {"en": "kilogram", "de": "Kilogramm", "fr": "kilogramme", "es": "kilogramo", "zh": "千克", "symbol": "kg", "type": "mass"},
            "second": {"en": "second", "de": "Sekunde", "fr": "seconde", "es": "segundo", "zh": "秒", "symbol": "s", "type": "time"},
            "ampere": {"en": "ampere", "de": "Ampere", "fr": "ampère", "es": "amperio", "zh": "安培", "symbol": "A", "type": "electric_current"},
            "kelvin": {"en": "kelvin", "de": "Kelvin", "fr": "kelvin", "es": "kelvin", "zh": "开尔文", "symbol": "K", "type": "temperature"},
            "mole": {"en": "mole", "de": "Mol", "fr": "mole", "es": "mol", "zh": "摩尔", "symbol": "mol", "type": "amount_of_substance"},
            "candela": {"en": "candela", "de": "Candela", "fr": "candela", "es": "candela", "zh": "坎德拉", "symbol": "cd", "type": "luminous_intensity"}
        }

        dictionary.update(si_units)

        return dictionary

    def add_entry(self, term: str, volume: EncyclopediaVolume,
                 definition: str, data_object: Dict[str, Any] = None,
                 references: List[str] = None, metadata: Dict[str, Any] = None) -> int:
        """
        Add encyclopedia entry

        Parameters:
            term: Term to define (umbrella term)
            volume: Which volume (Empirical, Economic, Applied)
            definition: Simplified definition
            data_object: Data object with parameters, ranges, values
            references: Source references
            metadata: Additional metadata (lifecycle, translations, etc.)

        Returns:
            Entry ID
        """
        # Determine A-Z category
        first_letter = term[0].upper()
        if not first_letter.isalpha():
            first_letter = '0'  # Numbers and symbols go in '0' folder

        # Create entry
        entry = {
            'term': term,
            'volume': volume.name,
            'category_letter': first_letter,
            'definition': definition,
            'data_object': data_object or {},
            'references': references or [],
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # Add multilingual translations if available
        if term.lower() in self.dictionary:
            entry['translations'] = self.dictionary[term.lower()]

        # Generate entry ID
        # - disk mode: local sequential id
        # - db mode: resolve stable row id after upsert
        if self.storage_mode == "db" and self.db is not None:
            entry_id = -1
        else:
            entry_id = len(self.entry_index) + 1
        entry['entry_id'] = entry_id

        # Save to file system (legacy disk mode only)
        if self.storage_mode == "disk":
            volume_path = self.volumes[volume]
            category_path = volume_path / first_letter
            entry_file = category_path / f"{term.replace(' ', '_')}.json"

            with open(entry_file, 'w', encoding='utf-8') as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)

        # Add to index (disk mode). DB mode inserts after resolving row id.
        if self.storage_mode != "db":
            self.entry_index[entry_id] = entry

        # Save to database (preferred for consolidation)
        if self.db:
            try:
                self.db.execute(
                    """
                    INSERT INTO encyclopedia_entries
                        (term, volume, category_letter, definition, data_object, references_json, metadata_json, created_at, updated_at)
                    VALUES
                        (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(term, volume) DO UPDATE SET
                        category_letter=excluded.category_letter,
                        definition=excluded.definition,
                        data_object=excluded.data_object,
                        references_json=excluded.references_json,
                        metadata_json=excluded.metadata_json,
                        updated_at=excluded.updated_at
                    """,
                    (
                        term,
                        volume.name,
                        first_letter,
                        definition,
                        json.dumps(data_object or {}, ensure_ascii=False),
                        json.dumps(references or [], ensure_ascii=False),
                        json.dumps(metadata or {}, ensure_ascii=False),
                        entry['created_at'],
                        entry['updated_at'],
                    )
                )

                # In db-only mode, prefer the stable DB row id for indexing.
                if self.storage_mode == "db":
                    rid = None
                    try:
                        rows = self.db.execute_query(
                            "SELECT id FROM encyclopedia_entries WHERE term = ? AND volume = ?",
                            (term, volume.name),
                        )
                        if rows:
                            rid = int(rows[0].get("id"))
                    except Exception:
                        rid = None

                    if rid is None:
                        # Fallback: keep in-memory index usable even if DB lookup fails.
                        try:
                            rid = (max(int(k) for k in self.entry_index.keys()) + 1) if self.entry_index else 1
                        except Exception:
                            rid = 1

                    entry['entry_id'] = rid
                    self.entry_index[rid] = entry
                    entry_id = rid
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"[Encyclopedia] DB upsert skipped: {e}")

        if self.logger:
            self.logger.info(f"[Encyclopedia] Added entry: {term} (Vol.{volume.value}, {first_letter})")

        return entry_id

    def search(self, query: str, volume: EncyclopediaVolume = None) -> List[Dict[str, Any]]:
        """
        Search encyclopedia entries

        Parameters:
            query: Search term
            volume: Optional volume to search (None = all volumes)

        Returns:
            List of matching entries
        """
        results = []

        for entry_id, entry in self.entry_index.items():
            # Volume filter
            if volume and entry['volume'] != volume.name:
                continue

            # Search in term, definition, and translations
            if query.lower() in entry['term'].lower():
                results.append(entry)
            elif query.lower() in entry['definition'].lower():
                results.append(entry)
            elif 'translations' in entry:
                for lang, translation in entry['translations'].items():
                    if query.lower() in str(translation).lower():
                        results.append(entry)
                        break

        return results

    def get_entry(self, term: str = None, entry_id: int = None) -> Optional[Dict[str, Any]]:
        """Get encyclopedia entry by term or ID"""
        if entry_id:
            return self.entry_index.get(entry_id)

        if term:
            for entry in self.entry_index.values():
                if entry['term'].lower() == term.lower():
                    return entry

        return None

    def get_category(self, letter: str, volume: EncyclopediaVolume) -> List[Dict[str, Any]]:
        """Get all entries in A-Z category"""
        letter = letter.upper()
        return [
            entry for entry in self.entry_index.values()
            if entry['category_letter'] == letter and entry['volume'] == volume.name
        ]

    def _load_entry_index(self):
        """Load all existing entries into index"""
        for volume in EncyclopediaVolume:
            volume_path = self.volumes[volume]

            for letter_dir in volume_path.iterdir():
                if not letter_dir.is_dir():
                    continue

                for entry_file in letter_dir.glob("*.json"):
                    try:
                        with open(entry_file, encoding='utf-8') as f:
                            entry = json.load(f)
                            entry_id = entry.get('entry_id', len(self.entry_index) + 1)
                            self.entry_index[entry_id] = entry
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"[Encyclopedia] Failed to load {entry_file}: {e}")

        if self.logger and self.entry_index:
            self.logger.info(f"[Encyclopedia] Loaded {len(self.entry_index)} entries from disk")

    def get_statistics(self) -> Dict[str, Any]:
        """Get encyclopedia statistics"""
        stats = {
            'total_entries': len(self.entry_index),
            'volumes': {}
        }

        for volume in EncyclopediaVolume:
            volume_entries = [e for e in self.entry_index.values() if e['volume'] == volume.name]
            stats['volumes'][volume.name] = {
                'count': len(volume_entries),
                'categories': {}
            }

            # Count by letter
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                letter_count = sum(1 for e in volume_entries if e['category_letter'] == letter)
                if letter_count > 0:
                    stats['volumes'][volume.name]['categories'][letter] = letter_count

        return stats

    def export_volume(self, volume: EncyclopediaVolume, format: str = 'json') -> str:
        """Export entire volume to file"""
        volume_entries = [e for e in self.entry_index.values() if e['volume'] == volume.name]

        export_data = {
            'volume': volume.name,
            'entry_count': len(volume_entries),
            'exported_at': datetime.now().isoformat(),
            'entries': volume_entries
        }

        export_file = self.base_path / f"export_{volume.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        if self.logger:
            self.logger.info(f"[Encyclopedia] Exported {volume.name}: {export_file}")

        return str(export_file)

    def translate_term(self, term: str, target_language: str) -> Optional[str]:
        """
        Translate term using multilingual dictionary

        Parameters:
            term: English term
            target_language: Target language code (de, fr, es, zh)

        Returns:
            Translated term or None
        """
        term_lower = term.lower()
        if term_lower in self.dictionary:
            return self.dictionary[term_lower].get(target_language)
        return None


# Initialize foundation entries
def initialize_foundation_encyclopedia(encyclopedia: EncyclopediaSystem):
    """Initialize encyclopedia with foundation empirical data"""

    # Physical constants (Empirical Volume)
    constants = [
        {
            'term': 'Speed of Light',
            'definition': 'Maximum speed at which energy/information can travel in vacuum',
            'data_object': {
                'symbol': 'c',
                'value': 299792458,
                'unit': 'm/s',
                'exact': True,
                'si_defining_constant': True
            },
            'references': ['CODATA 2018', 'SI Brochure 9th Edition']
        },
        {
            'term': 'Gravitational Constant',
            'definition': 'Fundamental constant in Newton\'s law of universal gravitation',
            'data_object': {
                'symbol': 'G',
                'value': 6.67430e-11,
                'unit': 'm³/(kg⋅s²)',
                'uncertainty': 1.5e-15,
                'exact': False
            },
            'references': ['CODATA 2018']
        },
        {
            'term': 'Planck Constant',
            'definition': 'Quantum of electromagnetic action relating photon energy to frequency',
            'data_object': {
                'symbol': 'h',
                'value': 6.62607015e-34,
                'unit': 'J⋅s',
                'exact': True,
                'si_defining_constant': True
            },
            'references': ['CODATA 2018', 'SI Brochure 9th Edition']
        }
    ]

    for const in constants:
        encyclopedia.add_entry(
            term=const['term'],
            volume=EncyclopediaVolume.EMPIRICAL,
            definition=const['definition'],
            data_object=const['data_object'],
            references=const['references']
        )

    print(f"[Encyclopedia] Initialized {len(constants)} foundation constants")


# Standalone test
if __name__ == '__main__':
    encyclopedia = EncyclopediaSystem()
    print(f"[Encyclopedia] Encyclopedia System ready")
    print(f"Base path: {encyclopedia.base_path}")
    print(f"Multilingual dictionary: {len(encyclopedia.dictionary)} terms")

    # Initialize foundation entries
    initialize_foundation_encyclopedia(encyclopedia)

    # Test search
    results = encyclopedia.search("light")
    print(f"\nSearch 'light': {len(results)} results")

    # Test translation
    translation = encyclopedia.translate_term("energy", "de")
    print(f"\nTranslation 'energy' → German: {translation}")

    # Statistics
    stats = encyclopedia.get_statistics()
    print(f"\nStatistics: {json.dumps(stats, indent=2)}")
