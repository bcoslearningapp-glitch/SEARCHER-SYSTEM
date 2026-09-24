"""Design requirements and concepts (PRD §32); design hypotheses and experiments (PRD §33-34).

Requirement text is never edited (a revision supersedes). Design hypothesis content is
versioned. Observations, results, interpretations, human-impact assessments and
experiment transitions are append-only.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from research_api.platform.db import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class DesignRequirement(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "design_requirements"
    __table_args__ = (UniqueConstraint("series_id", "version_number"),)

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    series_id: Mapped[UUID] = mapped_column(index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    supersedes_id: Mapped[UUID | None] = mapped_column(ForeignKey("design_requirements.id"))
    statement: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(10))
    traces: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), index=True)
    change_reason: Mapped[str | None] = mapped_column(Text)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DesignConcept(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "design_concepts"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    origin: Mapped[str] = mapped_column(String(30))
    origin_reference: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), index=True)
    hypothesis_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    mechanism_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    derived_from_concept_ids: Mapped[list[str]] = mapped_column(JSONB, default=list)
    rejection: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    selection: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)


class ConceptCoverage(Base):
    """How a concept addresses a requirement series (the current version is what counts)."""

    __tablename__ = "design_concept_coverage"

    concept_id: Mapped[UUID] = mapped_column(ForeignKey("design_concepts.id"), primary_key=True)
    requirement_series_id: Mapped[UUID] = mapped_column(primary_key=True)
    requirement_id: Mapped[UUID] = mapped_column(ForeignKey("design_requirements.id"))  # version judged
    coverage: Mapped[str] = mapped_column(String(20))
    note: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class DesignHypothesis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "design_hypotheses"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    concept_id: Mapped[UUID] = mapped_column(ForeignKey("design_concepts.id"), index=True)
    current_version: Mapped[int] = mapped_column(Integer)
    affects_people: Mapped[bool] = mapped_column(Boolean)
    epistemic_state: Mapped[str] = mapped_column(String(20))
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)


class DesignHypothesisVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "design_hypothesis_versions"
    __table_args__ = (UniqueConstraint("design_hypothesis_id", "version_number"),)

    design_hypothesis_id: Mapped[UUID] = mapped_column(ForeignKey("design_hypotheses.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    epistemic_state: Mapped[str] = mapped_column(String(20))
    change_reason: Mapped[str] = mapped_column(Text)
    actor: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Experiment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "experiments"

    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), index=True)
    design_hypothesis_id: Mapped[UUID] = mapped_column(ForeignKey("design_hypotheses.id"), index=True)
    title: Mapped[str] = mapped_column(Text)
    protocol: Mapped[dict[str, Any]] = mapped_column(JSONB)
    state: Mapped[str] = mapped_column(String(30), index=True)
    paused_from: Mapped[str | None] = mapped_column(String(30))
    affects_people: Mapped[bool] = mapped_column(Boolean)
    invalidation_reason: Mapped[str | None] = mapped_column(Text)
    approval_id: Mapped[UUID | None]
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB)


class ExperimentTransition(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "experiment_transitions"

    experiment_id: Mapped[UUID] = mapped_column(ForeignKey("experiments.id"), index=True)
    from_state: Mapped[str] = mapped_column(String(30))
    to_state: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str | None] = mapped_column(Text)
    gate_evaluation_id: Mapped[UUID | None]
    actor: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class HumanImpactAssessment(UUIDPrimaryKeyMixin, Base):
    """One dimension of the human-impact review; the latest per dimension counts."""

    __tablename__ = "human_impact_assessments"

    experiment_id: Mapped[UUID] = mapped_column(ForeignKey("experiments.id"), index=True)
    dimension: Mapped[str] = mapped_column(String(30))
    finding: Mapped[str] = mapped_column(String(30))
    note: Mapped[str] = mapped_column(Text)
    external_authority: Mapped[str | None] = mapped_column(Text)
    operational_constraint_id: Mapped[UUID | None]
    assessed_by: Mapped[dict[str, Any]] = mapped_column(JSONB)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Observation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "experiment_observations"

    experiment_id: Mapped[UUID] = mapped_column(ForeignKey("experiments.id"), index=True)
    description: Mapped[str] = mapped_column(Text)
    measurements: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recorded_by: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ExperimentResult(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "experiment_results"

    experiment_id: Mapped[UUID] = mapped_column(ForeignKey("experiments.id"), index=True)
    observation_ids: Mapped[list[str]] = mapped_column(JSONB)
    method: Mapped[str] = mapped_column(Text)
    summary: Mapped[str] = mapped_column(Text)
    values: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    recorded_by: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Interpretation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "experiment_interpretations"

    experiment_id: Mapped[UUID] = mapped_column(ForeignKey("experiments.id"), index=True)
    result_ids: Mapped[list[str]] = mapped_column(JSONB)
    outcome: Mapped[str] = mapped_column(String(20))
    statement: Mapped[str] = mapped_column(Text)
    limitations: Mapped[str | None] = mapped_column(Text)
    interpreted_by: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LearningReview(UUIDPrimaryKeyMixin, Base):
    """Human review that closes an experiment; append-only, the latest counts."""

    __tablename__ = "learning_reviews"

    experiment_id: Mapped[UUID] = mapped_column(ForeignKey("experiments.id"), index=True)
    learned: Mapped[str] = mapped_column(Text)
    hypothesis_effect: Mapped[str] = mapped_column(Text)
    surprises: Mapped[str | None] = mapped_column(Text)
    limitations: Mapped[list[str]] = mapped_column(JSONB)
    validity_threats: Mapped[list[str]] = mapped_column(JSONB)
    next_steps: Mapped[list[str]] = mapped_column(JSONB)
    reviewed_by: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
