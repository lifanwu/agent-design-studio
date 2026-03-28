"""Candidate comparison schemas."""

from typing import List

from pydantic import BaseModel, Field


class CandidateComparisonEntry(BaseModel):
    """A compact side-by-side comparison entry for one candidate."""

    candidate_id: str = Field(..., description="Stable candidate id.")
    label: str = Field(..., description="Candidate label.")
    is_selected: bool = Field(default=False, description="Whether this candidate is currently selected by the user.")
    tradeoff_summary: str = Field(..., description="Compact tradeoff summary.")
    validation_style: str = Field(..., description="Validation posture for this candidate.")
    control_style: str = Field(..., description="Control style for this candidate.")
    memory_posture: str = Field(..., description="Memory usage posture for this candidate.")
    workflow_complexity: str = Field(..., description="Workflow complexity posture for this candidate.")
    design_hint_summary: str = Field(..., description="Short summary of candidate-specific design hints.")


class CandidateComparison(BaseModel):
    """A deterministic comparison artifact for candidate-to-candidate inspection."""

    base_session_id: str = Field(..., description="Session id for the originating base design.")
    entries: List[CandidateComparisonEntry] = Field(default_factory=list, description="Comparison entries for all candidates.")
