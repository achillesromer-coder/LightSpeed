from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lightspeed_runtime.cgx_object_context import CGXObjectContextError, resolve_object_context


@pytest.mark.parametrize('query', ['cgx:root:cognigrex', 'cgx:domain:romer', 'WT-999', 'cgx:WT-001', 'COM-1675'])
def test_unregistered_identity_cannot_fall_back_to_project_words(query):
    with pytest.raises(CGXObjectContextError, match='no current object match'):
        resolve_object_context(query)


@pytest.mark.parametrize('query', ['WT-001', 'wt-001'])
def test_registered_object_id_keeps_its_binding(query):
    result = resolve_object_context(query)
    assert result['resolved_twin_id'] == 'watchtower'
    assert result['semantic_resolution']['semantic_object_id'] == 'WT-001'


def test_natural_language_still_resolves_specific_object_name():
    assert resolve_object_context('inspect WatchTower geometry')['resolved_twin_id'] == 'watchtower'


def test_duplicate_exact_identity_is_ambiguous_instead_of_first_record_winning(monkeypatch):
    from copy import deepcopy
    from lightspeed_runtime import cgx_object_context as context

    read = context._read_object

    def conflicting_registry(path):
        payload = read(path)
        if path == context.DEFAULT_LINEAGE_PATH:
            duplicate = deepcopy(next(r for r in payload['records'] if r['twin_id'] == 'watchtower'))
            duplicate['twin_id'] = 'watchtower_duplicate'
            payload['records'].append(duplicate)
        elif path == context.DEFAULT_MANIFEST_PATH:
            duplicate = deepcopy(next(a for a in payload['assets'] if a['twin_id'] == 'watchtower'))
            duplicate['twin_id'] = 'watchtower_duplicate'
            payload['assets'].append(duplicate)
        return payload

    monkeypatch.setattr(context, '_read_object', conflicting_registry)
    with pytest.raises(CGXObjectContextError, match='ambiguous object query'):
        resolve_object_context('WT-001')
