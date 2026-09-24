"""Evidence aggregation rules (Core §33-36, §43)."""

from uuid import uuid4

from research_api.contracts.enums import EvidenceRole as R
from research_api.contracts.enums import EvidenceStrength as S
from research_api.contracts.enums import HypothesisEpistemicState as H
from research_api.contracts.enums import LineageRelation as L
from research_api.modules.claims_evidence.aggregation import (
    AcceptedEvidence,
    Lineage,
    is_downgrade,
    suggested_claim_strength,
    suggested_hypothesis_state,
    summarize,
)

A, B, C = uuid4(), uuid4(), uuid4()


def ev(role: R, strength: S, work: object) -> AcceptedEvidence:
    return AcceptedEvidence(role=role, strength=strength, work_id=work)  # type: ignore[arg-type]


def test_no_evidence_is_unsubstantiated_and_unresolved() -> None:
    summary = summarize([], [])
    assert suggested_claim_strength(summary) is S.UNSUBSTANTIATED
    assert suggested_hypothesis_state(summary) is H.UNRESOLVED


def test_single_origin_cannot_exceed_promising() -> None:
    summary = summarize([ev(R.SUPPORTS, S.STRONG, A)], [])
    assert summary.support_origins == 1
    assert suggested_claim_strength(summary) is S.PROMISING
    assert suggested_hypothesis_state(summary) is H.PROMISING


def test_two_independent_origins_can_support() -> None:
    summary = summarize([ev(R.SUPPORTS, S.STRONG, A), ev(R.SUPPORTS, S.SUPPORTED, B)], [])
    assert summary.support_origins == 2
    assert suggested_claim_strength(summary) is S.STRONG
    assert suggested_hypothesis_state(summary) is H.SUPPORTED


def test_sources_sharing_an_origin_count_once() -> None:
    lineage = [Lineage(B, L.USES_DATA_FROM, A)]
    summary = summarize([ev(R.SUPPORTS, S.STRONG, A), ev(R.SUPPORTS, S.STRONG, B)], lineage)
    assert summary.support_origins == 1, "quantity of citations does not prove independence (Core §74.7)"
    assert suggested_hypothesis_state(summary) is H.PROMISING
    assert summary.shared_origin_groups and set(summary.shared_origin_groups[0]) == {A, B}


def test_citation_and_replication_do_not_merge_origins() -> None:
    lineage = [Lineage(B, L.CITES, A), Lineage(C, L.REPLICATES, A)]
    summary = summarize([ev(R.SUPPORTS, S.SUPPORTED, w) for w in (A, B, C)], lineage)
    assert summary.support_origins == 3


def test_weak_contrary_evidence_does_not_create_contested() -> None:
    summary = summarize([ev(R.SUPPORTS, S.STRONG, A), ev(R.SUPPORTS, S.STRONG, B), ev(R.CONTRADICTS, S.WEAK, C)], [])
    assert not summary.meaningful_conflict
    assert suggested_hypothesis_state(summary) is H.SUPPORTED


def test_much_stronger_one_sided_support_is_not_contested() -> None:
    summary = summarize(
        [ev(R.SUPPORTS, S.STRONG, A), ev(R.SUPPORTS, S.STRONG, B), ev(R.CONTRADICTS, S.PROMISING, C)], []
    )
    assert suggested_hypothesis_state(summary) is H.SUPPORTED


def test_nontrivial_conflict_is_contested_and_caps_strength() -> None:
    summary = summarize(
        [ev(R.SUPPORTS, S.SUPPORTED, A), ev(R.SUPPORTS, S.SUPPORTED, B), ev(R.CONTRADICTS, S.SUPPORTED, C)], []
    )
    assert summary.meaningful_conflict
    assert suggested_hypothesis_state(summary) is H.CONTESTED
    assert suggested_claim_strength(summary) is S.PROMISING


def test_strong_contradiction_of_weak_support_weakens() -> None:
    summary = summarize([ev(R.SUPPORTS, S.WEAK, A), ev(R.CONTRADICTS, S.STRONG, B)], [])
    assert suggested_hypothesis_state(summary) is H.WEAKENED


def test_limits_and_qualifies_do_not_count_as_support() -> None:
    summary = summarize([ev(R.LIMITS, S.STRONG, A), ev(R.QUALIFIES, S.STRONG, B)], [])
    assert suggested_hypothesis_state(summary) is H.UNRESOLVED


def test_downgrade_detection_never_moves_out_of_refuted() -> None:
    assert is_downgrade(H.SUPPORTED, H.CONTESTED)
    assert not is_downgrade(H.PROMISING, H.SUPPORTED)
    assert not is_downgrade(H.REFUTED, H.WEAKENED)
