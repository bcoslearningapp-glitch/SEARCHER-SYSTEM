"""Reliability registry API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OperationalRow(BaseModel):
    """Live reliability from the request log: what actually happened, per provider/model/task."""

    provider: str
    model: str
    task: str
    calls: int
    succeeded: int
    invalid_output: int
    refusals: int
    unavailable: int
    blocked: int
    structured_output_reliability: float | None
    fallback_served: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Decimal


class EvaluationIn(BaseModel):
    provider: str = Field(min_length=1, max_length=40)
    model: str = Field(min_length=1, max_length=200)
    dimension: str
    score: float
    sample_size: int = Field(ge=1)
    method: Literal["AUTOMATED_GOLDEN", "AUTOMATED_AUDIT", "HUMAN_GRADED"] = "HUMAN_GRADED"
    fixture_set: str | None = Field(default=None, max_length=80)
    notes: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class EvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider: str
    model: str
    dimension: str
    score: float
    threshold: float
    comparator: str
    passed: bool
    sample_size: int
    method: str
    fixture_set: str | None
    notes: str | None
    details: dict[str, Any]
    recorded_by: dict[str, Any]
    run_id: UUID | None
    created_at: datetime


class DimensionOut(BaseModel):
    key: str
    label: str
    comparator: str
    threshold: float
    blocking: bool


class ModelStanding(BaseModel):
    """Latest result per dimension for one model; blocking gaps keep it off default use (FR-EVAL-002)."""

    provider: str
    model: str
    latest: dict[str, EvaluationOut]
    blocking_failures: list[str]
    blocking_unevaluated: list[str]


class ReliabilityOut(BaseModel):
    dimensions: list[DimensionOut]
    operational: list[OperationalRow]
    models: list[ModelStanding]
