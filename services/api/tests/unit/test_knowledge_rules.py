"""Knowledge lifecycle, temporal validity and Knowledge Promotion Gate rules (Core §45, §52, §60)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from research_api.contracts.enums import EvidenceStrength, KnowledgeStatus, TemporalProfile
from research_api.contracts.enums import KnowledgeLifecycleStage as K
from research_api.contracts.enums import QualityGateResult as G
from research_api.modules.knowledge_memory.rules import (
    PromotionInput,
    effective_status,
    evaluate,
    is_lower,
    next_stage,
    revalidation_due,
)

NOW = datetime(2026, 9, 24, tzinfo=UTC)
READY = PromotionInput(
    target=K.LOCAL_RESULT,
    status=KnowledgeStatus.ACTIVE,
    revalidation_due=False,
    basis_entities=3,
    contexts=2,
    scope="Construction apprenticeships",
    contrary_searched=True,
    contrary_count=0,
    confidence=EvidenceStrength.SUPPORTED,
    temporal_profile=TemporalProfile.SLOW_CHANGING,
)


def _codes(data: PromotionInput) -> tuple[G, set[str]]:
    result, findings = evaluate(data)
    return result, {f.code for f in findings}


def test_lifecycle_moves_one_stage_at_a_time() -> None:
    assert next_stage(K.PROJECT_FINDING) is K.LOCAL_RESULT
    assert next_stage(K.CANDIDATE_OPERATING_RULE) is K.OPERATING_RULE
    assert next_stage(K.OPERATING_RULE) is None
    assert is_lower(K.LOCAL_RESULT, K.OPERATING_RULE)
    assert not is_lower(K.OPERATING_RULE, K.LOCAL_RESULT)


def test_revalidation_policy() -> None:
    recent, old = NOW - timedelta(days=10), NOW - timedelta(days=400)
    assert not revalidation_due(TemporalProfile.STABLE, None, None, NOW)
    assert revalidation_due(TemporalProfile.DYNAMIC, None, None, NOW)
    assert not revalidation_due(TemporalProfile.DYNAMIC, recent, 30, NOW)
    assert revalidation_due(TemporalProfile.SLOW_CHANGING, old, 365, NOW)
    assert effective_status(KnowledgeStatus.ACTIVE, True) is KnowledgeStatus.REVALIDATION_REQUIRED
    assert effective_status(KnowledgeStatus.SUSPENDED, True) is KnowledgeStatus.SUSPENDED


def test_repetition_and_contexts() -> None:
    assert _codes(READY) == (G.PASS, set())
    assert _codes(replace(READY, basis_entities=0))[1] == {"basis.missing"}
    single = replace(READY, target=K.REPEATED_LOCAL_RESULT, basis_entities=1)
    assert _codes(single) == (G.BLOCKED, {"repetition.insufficient"})
    one_context = replace(READY, target=K.ACCUMULATED_LOCAL_KNOWLEDGE, contexts=1)
    assert _codes(one_context) == (G.NEEDS_HUMAN_DECISION, {"contexts.single"})


def test_operating_rules_need_scope_contrary_search_and_confidence() -> None:
    rule = replace(READY, target=K.CANDIDATE_OPERATING_RULE)
    assert _codes(rule) == (G.PASS, set())
    result, codes = _codes(replace(rule, scope=" ", contrary_searched=False, confidence=EvidenceStrength.WEAK))
    assert result is G.BLOCKED
    assert codes == {"scope.missing", "contrary.not_searched", "confidence.weak"}
    assert _codes(replace(rule, contrary_count=1)) == (G.NEEDS_HUMAN_DECISION, {"contrary.present"})
    volatile = replace(rule, target=K.OPERATING_RULE, temporal_profile=TemporalProfile.HIGHLY_VOLATILE)
    assert _codes(volatile) == (G.NEEDS_HUMAN_DECISION, {"temporal.volatile"})
    assert _codes(replace(READY, contrary_count=1)) == (G.PASS_WITH_RESERVATIONS, {"contrary.present"})


def test_standing_and_time_block_promotion() -> None:
    for status in (KnowledgeStatus.CONTESTED, KnowledgeStatus.SUSPENDED, KnowledgeStatus.DOWNGRADED):
        assert _codes(replace(READY, status=status)) == (G.BLOCKED, {"status.not_active"})
    assert _codes(replace(READY, revalidation_due=True)) == (G.BLOCKED, {"temporal.revalidation_required"})
