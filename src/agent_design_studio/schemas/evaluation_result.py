"""Evaluation result schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class EvaluationMetric(BaseModel):
    """A single measured or judged metric from future candidate evaluation."""

    name: str = Field(..., description="Metric identifier.")
    score: float = Field(..., description="Metric score.")
    rationale: Optional[str] = Field(default=None, description="Why the metric received this score.")


class EvaluationEvidence(BaseModel):
    """Evidence captured during future candidate execution or review."""

    source: str = Field(..., description="Origin of the evidence.")
    summary: str = Field(..., description="Short evidence summary.")
    reference: Optional[str] = Field(default=None, description="Optional link, path, or identifier.")


class EvaluationResult(BaseModel):
    """Placeholder structured result for future evidence-based candidate selection."""

    candidate_id: str = Field(..., description="Identifier for the evaluated candidate.")
    status: str = Field(default="pending", description="Evaluation status.")
    metrics: List[EvaluationMetric] = Field(default_factory=list, description="Collected metrics.")
    evidence: List[EvaluationEvidence] = Field(default_factory=list, description="Supporting evidence.")
    recommendation: Optional[str] = Field(default=None, description="Future selection recommendation.")

