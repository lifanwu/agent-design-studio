"""Design document schemas.

This project currently treats ``DesignDoc`` as the active design artifact.
The same structure also serves as the current Design IR surface through a
lightweight accessor layer, so we can evolve the abstraction later without
rewriting the current deterministic system.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DesignSection(BaseModel):
    """A named section in the structured design document."""

    title: str = Field(..., description="Section heading.")
    content: str = Field(..., description="Section body.")


class GeneratedArtifact(BaseModel):
    """A future artifact expected to be generated from the design document."""

    artifact_type: str = Field(..., description="Artifact category, such as manual or code.")
    path_hint: Optional[str] = Field(default=None, description="Suggested output path or identifier.")
    status: str = Field(default="planned", description="Lifecycle status for the artifact.")


class DesignDoc(BaseModel):
    """Structured source-of-truth document describing a designed task agent.

    Minimal IR-friendly optional fields are included so the current active
    design can also be viewed as a Design IR without introducing a new layer.
    """

    title: str = Field(..., description="Design document title.")
    version: str = Field(default="0.1.0", description="Document version.")
    status: str = Field(default="draft", description="Current maturity of the design.")
    summary: str = Field(..., description="Short description of the designed agent.")
    problem_statement: Optional[str] = Field(default=None, description="Problem the agent is intended to solve.")
    objective: Optional[str] = Field(default=None, description="Optional high-level objective for the design.")
    inputs: Optional[List[str]] = Field(default=None, description="Optional IR-style input channels or artifacts.")
    outputs: Optional[List[str]] = Field(default=None, description="Optional IR-style outputs or deliverables.")
    constraints: Optional[List[str]] = Field(default=None, description="Optional IR-style design constraints.")
    tradeoffs: Optional[Dict[str, float]] = Field(default=None, description="Optional IR-style tradeoff map.")
    structure: Optional[Dict[str, Any]] = Field(default=None, description="Optional IR-style structural summary.")
    components: Optional[List[str]] = Field(default=None, description="Optional IR-style component list.")
    sections: List[DesignSection] = Field(default_factory=list, description="Ordered content sections.")
    assumptions: List[str] = Field(default_factory=list, description="Known assumptions in the design.")
    open_questions: List[str] = Field(default_factory=list, description="Outstanding unresolved questions.")
    artifacts: List[GeneratedArtifact] = Field(default_factory=list, description="Expected generated outputs.")
