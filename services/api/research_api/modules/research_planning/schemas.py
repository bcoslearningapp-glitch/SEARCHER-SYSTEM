"""Research planning API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from research_api.contracts.enums import ResearchOutcomeKind, ResearchQuestionType, ResearchTrack, SufficiencyResult

Language = str
_LANG = r"^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$"
CONSIDERATIONS = (
    "support_evidence",
    "counter_evidence",
    "alternative_explanations",
    "independence",
    "diversity",
    "context_fit",
    "critical_unknowns",
    "impact",
    "reversibility",
    "remaining_uncertainty",
)


class TrackPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    track: ResearchTrack
    approach: str = Field(min_length=1)
    queries: list[str] = Field(default_factory=list)


class PlanIn(BaseModel):
    question: str = Field(min_length=1)
    decision_served: str = Field(min_length=1, description="What decision or use the answer serves")
    question_type: ResearchQuestionType
    risk_impact: str = ""
    desired_evidence_types: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    tracks: list[TrackPlan]
    sufficiency_criteria: list[str] = Field(min_length=1)
    max_web_searches: int | None = Field(default=None, ge=0)

    @field_validator("languages")
    @classmethod
    def _languages(cls, value: list[str]) -> list[str]:
        import re  # noqa: PLC0415

        bad = [v for v in value if not re.match(_LANG, v)]
        if bad:
            raise ValueError(f"languages must be BCP 47 codes: {bad}")
        return value

    @model_validator(mode="after")
    def _all_tracks(self) -> PlanIn:
        # Settings may change depth but never drop counter-evidence search (FR-BIAS-001/004).
        missing = set(ResearchTrack) - {t.track for t in self.tracks}
        if missing:
            raise ValueError(f"plan must cover every track; missing {sorted(m.value for m in missing)}")
        return self


class PlanRevision(PlanIn):
    change_reason: str = Field(min_length=1)


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    series_id: UUID
    version_number: int
    supersedes_id: UUID | None
    status: Literal["ACTIVE", "SUPERSEDED"]
    question: str
    decision_served: str
    question_type: ResearchQuestionType
    risk_impact: str
    desired_evidence_types: list[str]
    languages: list[str]
    tracks: list[TrackPlan]
    sufficiency_criteria: list[str]
    max_web_searches: int | None
    change_reason: str | None
    provenance: dict[str, Any]
    created_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(
            mode="json", exclude_none=True, exclude={"series_id", "status", "change_reason", "created_at"}
        )


class LocalSearchIn(BaseModel):
    plan_id: UUID | None = None
    track: ResearchTrack | None = None
    question: str | None = None
    queries: list[str] = Field(min_length=1, max_length=8)
    languages: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _question_or_plan(self) -> LocalSearchIn:
        if self.plan_id is None and not (self.question or "").strip():
            raise ValueError("give a plan_id or a question")
        return self


class SearchRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    plan_id: UUID | None
    track: ResearchTrack | None
    question: str
    provider: str
    queries: list[str]
    languages: list[str]
    outcome: ResearchOutcomeKind
    result_count: int
    scope: str
    exclusions: str | None
    actor: dict[str, Any]
    performed_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class LocalSearchOut(BaseModel):
    records: list[SearchRecordOut]
    hits: list[dict[str, Any]]


class SufficiencyIn(BaseModel):
    result: SufficiencyResult
    considerations: dict[str, str]
    rationale: str = Field(min_length=1)
    recommend_experiment: bool = False

    @field_validator("considerations")
    @classmethod
    def _complete(cls, value: dict[str, str]) -> dict[str, str]:
        missing = [k for k in CONSIDERATIONS if not value.get(k, "").strip()]
        extra = sorted(set(value) - set(CONSIDERATIONS))
        if missing or extra:
            raise ValueError(
                f"considerations must address every factor (FR-SUFF-002); missing {missing}, unknown {extra}"
            )
        return {k: value[k].strip() for k in CONSIDERATIONS}


class SufficiencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    plan_id: UUID
    decision_served: str
    result: SufficiencyResult
    considerations: dict[str, str]
    rationale: str
    recommend_experiment: bool
    signals: dict[str, Any]
    assessed_by: dict[str, Any]
    assessed_at: datetime

    def to_contract(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True, exclude={"signals"})


class TrackCoverage(BaseModel):
    track: ResearchTrack
    searches: int
    searched: bool
    last_outcome: ResearchOutcomeKind | None
    execution_failed: bool


class PlanOverview(BaseModel):
    """What was actually searched per track: the stored basis for a sufficiency judgment (§66 'Why?')."""

    plan: PlanOut
    versions: list[PlanOut]
    coverage: list[TrackCoverage]
    web_searches_used: int
    searches: list[SearchRecordOut]
    current_sufficiency: SufficiencyOut | None
    sufficiency_history: list[SufficiencyOut]
