"""
Seed Knowledge Graph
Creates nodes and edges for system architecture visualization

NOTE (2026-02-03): This seed script includes legacy Z+4 entries for historical completeness.
Canonical runtime stack is now 8 floors (Z+3..Z-4); `Z+4_FirstRun` is legacy-only (setup/login consolidated
into Trinity). See `dataindex/02_MASTER_BUILD_SPEC_SHEET.md`.
"""

import sys
from pathlib import Path

# Add current directory to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

# Import from local modules
from models import (
    KnowledgeGraphNode, KnowledgeGraphEdge,
    CalculatorModule, ScientificDataset, ZFloorFunction
)
from base import get_session

# Z Floor nodes
Z_FLOORS = [
    {
        'node_type': 'floor',
        'node_name': 'Z-4_Merovingian',
        'description': 'Data Exchange & Integration - External data sources, API adapters, import/export',
        'properties': '{"level": -4, "role": "data_exchange", "color": "#8000FF"}',
    },
    {
        'node_type': 'floor',
        'node_name': 'Z-3_Smith',
        'description': 'Code Generation & Synthesis - Automated code generation, templates, optimization',
        'properties': '{"level": -3, "role": "code_generation", "color": "#FF0000"}',
    },
    {
        'node_type': 'floor',
        'node_name': 'Z-2_Oracle',
        'description': 'Knowledge Base & Documentation - System documentation, learning resources, archives',
        'properties': '{"level": -2, "role": "knowledge", "color": "#FF8000"}',
    },
    {
        'node_type': 'floor',
        'node_name': 'Z-1_Morpheus',
        'description': 'Data Processing & Memory - Database, ORM, data organization, memory management',
        'properties': '{"level": -1, "role": "data_processing", "color": "#0080FF"}',
    },
    {
        'node_type': 'floor',
        'node_name': 'Z0_TheConstruct',
        'description': 'Physics Engines & Calculators - Scientific simulations, physics calculations, datasets',
        'properties': '{"level": 0, "role": "physics_engine", "color": "#FFFF00"}',
    },
    {
        'node_type': 'floor',
        'node_name': 'Z+1_Architect',
        'description': 'Design & Orchestration - System architecture, workflow coordination, task management',
        'properties': '{"level": 1, "role": "orchestration", "color": "#00FF80"}',
    },
    {
        'node_type': 'floor',
        'node_name': 'Z+2_Neo',
        'description': 'AI & Machine Learning - AI agents, Achilles, Cognigrex, ML models, training',
        'properties': '{"level": 2, "role": "ai_ml", "color": "#FF0080"}',
    },
    {
        'node_type': 'floor',
        'node_name': 'Z+3_Trinity',
        'description': 'UI Components & Visualization - User interface, spatial UI, Bento grid, wizards',
        'properties': '{"level": 3, "role": "ui", "color": "#00FFFF"}',
    },
    {
        'node_type': 'floor',
        'node_name': 'Z+4_FirstRun',
        'description': 'Application Entry & Initialization - Startup, configuration, first-run wizards',
        'properties': '{"level": 4, "role": "initialization", "color": "#80FF00"}',
    },
]

# Concept nodes
CONCEPTS = [
    {
        'node_type': 'concept',
        'node_name': 'Gravitational Waves',
        'description': 'Ripples in spacetime caused by massive accelerating objects',
        'properties': '{"domain": "physics", "subdomain": "general_relativity"}',
    },
    {
        'node_type': 'concept',
        'node_name': 'Cosmic Microwave Background',
        'description': 'Thermal radiation left over from the Big Bang',
        'properties': '{"domain": "physics", "subdomain": "cosmology"}',
    },
    {
        'node_type': 'concept',
        'node_name': 'Black Hole Merger',
        'description': 'Collision and coalescence of two black holes',
        'properties': '{"domain": "physics", "subdomain": "astrophysics"}',
    },
    {
        'node_type': 'concept',
        'node_name': 'Quantum Mechanics',
        'description': 'Physical theory describing nature at atomic and subatomic scales',
        'properties': '{"domain": "physics", "subdomain": "quantum"}',
    },
    {
        'node_type': 'concept',
        'node_name': 'Raphael Field Synthesis',
        'description': 'Theoretical framework for unified field calculations',
        'properties': '{"domain": "theory", "subdomain": "rfs"}',
    },
]


def seed_floor_nodes(session):
    """Create nodes for all Z Floors"""
    print("[SEED] Creating Z Floor nodes...")
    created = 0

    for floor_data in Z_FLOORS:
        existing = KnowledgeGraphNode.find_node(
            session,
            node_type='floor',
            node_name=floor_data['node_name']
        )

        if existing:
            print(f"[SKIP] Floor node exists: {floor_data['node_name']}")
            continue

        node = KnowledgeGraphNode(**floor_data)
        session.add(node)
        created += 1
        print(f"[OK] Created floor node: {floor_data['node_name']}")

    session.commit()
    print(f"[SUCCESS] Created {created} floor nodes\n")
    return created


def seed_concept_nodes(session):
    """Create nodes for key concepts"""
    print("[SEED] Creating concept nodes...")
    created = 0

    for concept_data in CONCEPTS:
        existing = KnowledgeGraphNode.find_node(
            session,
            node_type='concept',
            node_name=concept_data['node_name']
        )

        if existing:
            print(f"[SKIP] Concept node exists: {concept_data['node_name']}")
            continue

        node = KnowledgeGraphNode(**concept_data)
        session.add(node)
        created += 1
        print(f"[OK] Created concept node: {concept_data['node_name']}")

    session.commit()
    print(f"[SUCCESS] Created {created} concept nodes\n")
    return created


def seed_calculator_nodes(session):
    """Create nodes for calculator modules from database"""
    print("[SEED] Creating calculator module nodes...")
    created = 0

    # Get all calculators from database
    calculators = session.query(CalculatorModule).all()

    for calc in calculators:
        existing = KnowledgeGraphNode.find_node(
            session,
            node_type='module',
            node_name=calc.name
        )

        if existing:
            continue

        node = KnowledgeGraphNode(
            node_type='module',
            node_name=calc.name,
            node_id_ref=calc.id,
            description=calc.description or f"{calc.category} calculator module",
            properties=f'{{"category": "{calc.category}", "floor": "{calc.floor}"}}'
        )
        session.add(node)
        created += 1
        print(f"[OK] Created module node: {calc.name} ({calc.category})")

    session.commit()
    print(f"[SUCCESS] Created {created} calculator module nodes\n")
    return created


def seed_dataset_nodes(session):
    """Create nodes for scientific datasets from database"""
    print("[SEED] Creating dataset nodes...")
    created = 0

    # Get all datasets from database
    datasets = session.query(ScientificDataset).all()

    for dataset in datasets:
        existing = KnowledgeGraphNode.find_node(
            session,
            node_type='dataset',
            node_name=dataset.filename
        )

        if existing:
            continue

        node = KnowledgeGraphNode(
            node_type='dataset',
            node_name=dataset.filename,
            node_id_ref=dataset.id,
            description=dataset.description or f"{dataset.category} scientific data",
            properties=f'{{"category": "{dataset.category}", "format": "{dataset.format}", "size_gb": {dataset.size_gb:.2f}}}'
        )
        session.add(node)
        created += 1
        print(f"[OK] Created dataset node: {dataset.filename[:50]}...")

    session.commit()
    print(f"[SUCCESS] Created {created} dataset nodes\n")
    return created


def seed_relationships(session):
    """Create edges between nodes"""
    print("[SEED] Creating knowledge graph edges...")
    created = 0

    # Floor containment relationships
    construct_node = KnowledgeGraphNode.find_node(session, 'floor', 'Z0_TheConstruct')
    morpheus_node = KnowledgeGraphNode.find_node(session, 'floor', 'Z-1_Morpheus')

    if construct_node:
        # TheConstruct contains calculator modules
        calc_nodes = KnowledgeGraphNode.get_nodes_by_type(session, 'module')
        for calc_node in calc_nodes:
            existing_edge = session.query(KnowledgeGraphEdge).filter_by(
                source_node_id=construct_node.id,
                target_node_id=calc_node.id,
                relationship_type='contains'
            ).first()

            if not existing_edge:
                edge = KnowledgeGraphEdge(
                    source_node_id=construct_node.id,
                    target_node_id=calc_node.id,
                    relationship_type='contains',
                    strength=1.0
                )
                session.add(edge)
                created += 1

    if morpheus_node:
        # Morpheus contains datasets
        dataset_nodes = KnowledgeGraphNode.get_nodes_by_type(session, 'dataset')
        for dataset_node in dataset_nodes:
            existing_edge = session.query(KnowledgeGraphEdge).filter_by(
                source_node_id=morpheus_node.id,
                target_node_id=dataset_node.id,
                relationship_type='contains'
            ).first()

            if not existing_edge:
                edge = KnowledgeGraphEdge(
                    source_node_id=morpheus_node.id,
                    target_node_id=dataset_node.id,
                    relationship_type='contains',
                    strength=1.0
                )
                session.add(edge)
                created += 1

    # Calculator → Dataset relationships (uses)
    # Link cosmic_microwave_background calculator to Planck datasets
    cmb_calc_node = KnowledgeGraphNode.find_node(session, 'module', 'cosmic_microwave_background')
    if cmb_calc_node:
        planck_datasets = session.query(ScientificDataset).filter_by(category='planck_cmb').all()
        for dataset in planck_datasets:
            dataset_node = KnowledgeGraphNode.find_node(session, 'dataset', dataset.filename)
            if dataset_node:
                existing_edge = session.query(KnowledgeGraphEdge).filter_by(
                    source_node_id=cmb_calc_node.id,
                    target_node_id=dataset_node.id,
                    relationship_type='uses'
                ).first()

                if not existing_edge:
                    edge = KnowledgeGraphEdge(
                        source_node_id=cmb_calc_node.id,
                        target_node_id=dataset_node.id,
                        relationship_type='uses',
                        strength=0.9,
                        extra_metadata='{"purpose": "CMB analysis"}'
                    )
                    session.add(edge)
                    created += 1

    # Link black_hole_simulation calculator to LIGO datasets
    bh_calc_node = KnowledgeGraphNode.find_node(session, 'module', 'black_hole_simulation')
    if bh_calc_node:
        ligo_datasets = session.query(ScientificDataset).filter_by(category='ligo_gw').all()
        for dataset in ligo_datasets:
            dataset_node = KnowledgeGraphNode.find_node(session, 'dataset', dataset.filename)
            if dataset_node:
                existing_edge = session.query(KnowledgeGraphEdge).filter_by(
                    source_node_id=bh_calc_node.id,
                    target_node_id=dataset_node.id,
                    relationship_type='uses'
                ).first()

                if not existing_edge:
                    edge = KnowledgeGraphEdge(
                        source_node_id=bh_calc_node.id,
                        target_node_id=dataset_node.id,
                        relationship_type='uses',
                        strength=0.9,
                        extra_metadata='{"purpose": "gravitational wave analysis"}'
                    )
                    session.add(edge)
                    created += 1

    session.commit()
    print(f"[SUCCESS] Created {created} knowledge graph edges\n")
    return created


def seed_knowledge_graph():
    """Main seeding function"""
    session = get_session()

    try:
        print("="*60)
        print(" KNOWLEDGE GRAPH SEEDING")
        print("="*60)
        print()

        total_nodes = 0
        total_edges = 0

        # Seed nodes
        total_nodes += seed_floor_nodes(session)
        total_nodes += seed_concept_nodes(session)
        total_nodes += seed_calculator_nodes(session)
        total_nodes += seed_dataset_nodes(session)

        # Seed relationships
        total_edges += seed_relationships(session)

        # Summary
        print("="*60)
        print(" KNOWLEDGE GRAPH SUMMARY")
        print("="*60)
        print(f"Total nodes created: {total_nodes}")
        print(f"Total edges created: {total_edges}")
        print()

        # Count by type
        print("Nodes by type:")
        for node_type in ['floor', 'module', 'dataset', 'concept']:
            count = session.query(KnowledgeGraphNode).filter_by(node_type=node_type).count()
            print(f"  {node_type}: {count}")

        print()
        print("Edges by relationship:")
        for rel_type in ['contains', 'uses', 'calls', 'produces']:
            count = session.query(KnowledgeGraphEdge).filter_by(relationship_type=rel_type).count()
            print(f"  {rel_type}: {count}")

        print()
        print("[SUCCESS] Knowledge graph seeding complete!")

    except Exception as e:
        print(f"[ERROR] Failed to seed knowledge graph: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_knowledge_graph()
