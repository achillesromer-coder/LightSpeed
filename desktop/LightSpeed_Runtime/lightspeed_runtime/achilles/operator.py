from __future__ import annotations

from lightspeed_runtime.contracts import AchillesActionEnvelope, stable_id
from lightspeed_runtime.domain_registry import get_source_type_definition
from lightspeed_runtime.reservoirs.registry import ReservoirRegistry


class AchillesOperator:
    def __init__(self, registry: ReservoirRegistry) -> None:
        self.registry = registry
        self._actions: dict[str, AchillesActionEnvelope] = {}

    def retrieve(self, query: str, limit: int = 10) -> list[dict]:
        tokens = [token.lower() for token in query.split() if token.strip()]
        scored: list[tuple[int, int, dict]] = []
        for manifest in self.registry.manifests():
            source_type_definition = get_source_type_definition(manifest.source_type)
            manifest_haystack = " ".join(
                [
                    manifest.source_id,
                    manifest.source_label,
                    manifest.source_type,
                    manifest.classification,
                    manifest.floor_owner,
                    manifest.definition,
                    manifest.operator_notes,
                    " ".join(manifest.trusted_documents),
                    source_type_definition.summary if source_type_definition else "",
                    source_type_definition.operator_usage if source_type_definition else "",
                ]
            ).lower()
            for asset in self.registry.get_assets(manifest.source_id):
                haystack = " ".join(
                    [
                        asset.title.lower(),
                        asset.summary.lower(),
                        asset.relative_path.lower(),
                        asset.canonical_rank.lower(),
                        manifest_haystack,
                    ]
                )
                score = sum(1 for token in tokens if token in haystack)
                if score:
                    canonical_bias = 1 if asset.canonical_rank == "canonical" else 0
                    scored.append((score, canonical_bias, asset.to_dict()))
        scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [item[2] for item in scored[:limit]]

    def propose_action(
        self,
        workspace: str,
        target_scope: str,
        action_type: str,
        inputs: dict,
        requires_approval: bool = True,
    ) -> AchillesActionEnvelope:
        envelope = AchillesActionEnvelope(
            action_id=stable_id("action"),
            actor="Achilles",
            workspace=workspace,
            target_scope=target_scope,
            action_type=action_type,
            inputs=inputs,
            requires_approval=requires_approval,
            approval_state="pending" if requires_approval else "approved",
        )
        self._actions[envelope.action_id] = envelope
        return envelope

    def approve_action(self, action_id: str, audit_ref: str | None = None) -> AchillesActionEnvelope:
        envelope = self._actions[action_id]
        envelope.approve(audit_ref=audit_ref)
        return envelope

    def reject_action(self, action_id: str, audit_ref: str | None = None) -> AchillesActionEnvelope:
        envelope = self._actions[action_id]
        envelope.reject(audit_ref=audit_ref)
        return envelope

    def list_actions(self) -> list[dict]:
        return [action.to_dict() for action in self._actions.values()]
