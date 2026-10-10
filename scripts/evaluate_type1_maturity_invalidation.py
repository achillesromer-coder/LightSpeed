#!/usr/bin/env python3
"""Evaluate bounded CGX Type-I maturity invalidation fixtures.

This is a deterministic dependency-closure helper. It does not change owner records,
physical evidence, carrier state, or authority.
"""
import argparse
import json
from collections import defaultdict, deque
from pathlib import Path


def load_fixture(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def dependency_children(nodes):
    children = defaultdict(set)
    kinds = {}
    for node in nodes:
        node_id = node["id"]
        kinds[node_id] = node["kind"]
        for parent in node.get("depends_on", []):
            children[parent].add(node_id)
    return children, kinds


def affected_descendants(nodes, changed_nodes, traversal_exclusions=None):
    children, kinds = dependency_children(nodes)
    exclusions = set(traversal_exclusions or [])
    changed = set(changed_nodes)
    stale = set()
    queue = deque(changed_nodes)
    seen = set(changed_nodes)
    while queue:
        parent = queue.popleft()
        for child in sorted(children.get(parent, ())):
            if child in seen:
                continue
            seen.add(child)
            if kinds.get(child) in exclusions:
                continue
            stale.add(child)
            queue.append(child)
    return changed, stale


def evaluate_event(fixture, event):
    changed, stale = affected_descendants(
        fixture["nodes"],
        event["changed_nodes"],
        event.get("traversal_exclusions"),
    )
    expected_stale = set(event.get("expected_stale", []))
    expected_preserved = set(event.get("expected_preserved", []))
    result = {
        "event_id": event["id"],
        "trigger": event["trigger"],
        "changed": sorted(changed),
        "stale": sorted(stale),
        "expected_stale_match": stale == expected_stale,
        "preserved_violations": sorted(stale & expected_preserved),
    }
    result["pass"] = result["expected_stale_match"] and not result["preserved_violations"]
    return result


def evaluate_fixture(fixture):
    results = [evaluate_event(fixture, event) for event in fixture["events"]]
    return {
        "schema": "CGX-TYPE1-MATURITY-INVALIDATION-RESULT/0.1",
        "artifact_id": fixture["artifact_id"],
        "status": "PASS" if all(r["pass"] for r in results) else "FAIL",
        "results": results,
        "physical_evidence": "UNCHANGED / NO_PHYSICAL_EXECUTION",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "fixture",
        nargs="?",
        default="cgx/component_atlas/type1_maturity_invalidation_fixture_v0_1.json",
    )
    args = parser.parse_args()
    result = evaluate_fixture(load_fixture(Path(args.fixture)))
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
