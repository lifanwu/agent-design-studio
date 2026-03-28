"""Candidate design schemas."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from agent_design_studio.schemas.design_doc import DesignDoc
from agent_design_studio.schemas.design_state import DesignState


class CandidateDesign(BaseModel):
    """A single generated design candidate derived from the current shared state."""

    id: str = Field(..., description="Stable candidate identifier.")
    label: str = Field(..., description="Short candidate label.")
    short_description: str = Field(..., description="Compact explanation of the candidate's strategy.")
    strategy_differences: List[str] = Field(
        default_factory=list,
        description="Distinct strategy choices that separate this candidate from others.",
    )
    diff: Dict[str, Any] = Field(default_factory=dict, description="Structured diff from the base design state.")
    candidate_design_state: DesignState = Field(..., description="Partial design state for this candidate.")
    candidate_design_summary: str = Field(..., description="Readable summary for quick inspection.")
    candidate_design_doc_preview: DesignDoc = Field(..., description="Preview document for this candidate.")


class CandidateCollection(BaseModel):
    """A collection of generated candidates associated with a base design session."""

    base_session_id: str = Field(..., description="Session id of the originating shared design state.")
    base_design_summary: str = Field(..., description="Summary of the base design used for candidate generation.")
    candidates: List[CandidateDesign] = Field(default_factory=list, description="Generated candidate designs.")
