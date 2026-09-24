"""Deterministic evidence aggregation (Core §33-36, §43, FR-EVID-004..006, FR-LINEAGE-002).

Pure functions: no persistence, no AI. Rules:
- Independence is counted in *origin clusters*: works connected by dependency
  lineage (derived from, uses data from, summarizes, reanalyzes, translates)
  share an origin and count once (Core §35, §74.7).
- A single origin never establishes more than PROMISING.
- CONTESTED requires meaningful conflict between nontrivial evidence; weak
  contrary evidence does not create it when stronger support is one-sided (Core §43).
- There is no numeric truth score (Core §34).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from research_api.contracts.enums import EvidenceRole, EvidenceStrength, HypothesisEpistemicState, LineageRelation

S = EvidenceStrength
H = HypothesisEpistemicState

STRENGTH_RANK: dict[EvidenceStrength, int] = {
    S.UNSUBSTANTIATED: 0,
    S.WEAK: 1,
    S.PROMISING: 2,
    S.SUPPORTED: 3,
    S.STRONG: 4,
    S.ESTABLISHED_WITHIN_SCOPE: 5,
}
HYPOTHESIS_RANK: dict[HypothesisEpistemicState, int] = {
    H.REFUTED: 0,
    H.WEAKENED: 1,
    H.CONTESTED: 2,
    H.UNRESOLVED: 3,
    H.PROMISING: 4,
    H.SUPPORTED: 5,
}

# Relations meaning "B depends on A's evidence". CITES and REPLICATES do not create
# dependence: a citation is not reuse of data, and a replication is new data.
DEPENDENCY_RELATIONS = frozenset(
    {
        LineageRelation.DERIVED_FROM,
        LineageRelation.USES_DATA_FROM,
        LineageRelation.SUMMARIZES,
        LineageRelation.REANALYZES,
        LineageRelation.TRANSLATES,
    }
)


@dataclass(frozen=True)
class AcceptedEvidence:
    role: EvidenceRole
    strength: EvidenceStrength
    work_id: UUID


@dataclass(frozen=True)
class Lineage:
    from_work_id: UUID
    relation: LineageRelation
    to_work_id: UUID


@dataclass(frozen=True)
class Summary:
    support_origins: int
    contra_origins: int
    strongest_support: EvidenceStrength
    strongest_contra: EvidenceStrength
    effective_support: EvidenceStrength
    meaningful_conflict: bool
    shared_origin_groups: list[list[UUID]]


def origin_clusters(work_ids: Iterable[UUID], lineage: Iterable[Lineage]) -> dict[UUID, UUID]:
    """Union-find over dependency lineage; returns work_id -> cluster representative."""
    parent: dict[UUID, UUID] = {}

    def find(x: UUID) -> UUID:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for work in work_ids:
        find(work)
    for edge in lineage:
        if edge.relation in DEPENDENCY_RELATIONS:
            a, b = find(edge.from_work_id), find(edge.to_work_id)
            if a != b:
                parent[a] = b
    return {work: find(work) for work in parent}


def _strongest(items: list[AcceptedEvidence]) -> EvidenceStrength:
    return max((i.strength for i in items), key=STRENGTH_RANK.__getitem__, default=S.UNSUBSTANTIATED)


def summarize(evidence: list[AcceptedEvidence], lineage: list[Lineage]) -> Summary:
    clusters = origin_clusters((e.work_id for e in evidence), lineage)
    support = [e for e in evidence if e.role is EvidenceRole.SUPPORTS]
    contra = [e for e in evidence if e.role is EvidenceRole.CONTRADICTS]
    support_origins = len({clusters[e.work_id] for e in support})
    contra_origins = len({clusters[e.work_id] for e in contra})
    strongest_support = _strongest(support)
    strongest_contra = _strongest(contra)

    effective = strongest_support
    if support_origins < 2 and STRENGTH_RANK[effective] > STRENGTH_RANK[S.PROMISING]:
        effective = S.PROMISING  # one origin cannot establish more than "promising"
    meaningful = STRENGTH_RANK[strongest_contra] >= STRENGTH_RANK[S.PROMISING] and (
        STRENGTH_RANK[strongest_contra] >= STRENGTH_RANK[effective] - 1
    )
    if meaningful and STRENGTH_RANK[effective] > STRENGTH_RANK[S.PROMISING]:
        effective = S.PROMISING

    groups: dict[UUID, set[UUID]] = {}
    for work, root in clusters.items():
        groups.setdefault(root, set()).add(work)
    shared = [sorted(g, key=str) for g in groups.values() if len(g) > 1]
    return Summary(
        support_origins=support_origins,
        contra_origins=contra_origins,
        strongest_support=strongest_support,
        strongest_contra=strongest_contra,
        effective_support=effective,
        meaningful_conflict=meaningful,
        shared_origin_groups=shared,
    )


def suggested_claim_strength(summary: Summary) -> EvidenceStrength:
    return summary.effective_support


def suggested_hypothesis_state(summary: Summary) -> HypothesisEpistemicState:
    """Suggest an epistemic state from accepted evidence. REFUTED is never suggested: humans refute."""
    support_rank = STRENGTH_RANK[summary.strongest_support]
    if summary.meaningful_conflict:
        return H.CONTESTED if support_rank >= STRENGTH_RANK[S.PROMISING] else H.WEAKENED
    if STRENGTH_RANK[summary.effective_support] >= STRENGTH_RANK[S.SUPPORTED]:
        return H.SUPPORTED
    if support_rank >= STRENGTH_RANK[S.WEAK]:
        return H.PROMISING
    return H.UNRESOLVED


def is_downgrade(current: HypothesisEpistemicState, suggested: HypothesisEpistemicState) -> bool:
    return HYPOTHESIS_RANK[suggested] < HYPOTHESIS_RANK[current] and current is not H.REFUTED
