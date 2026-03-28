"""Patch planning schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class PatchOperation(BaseModel):
    """A future local replacement action against a structured artifact."""

    target: str = Field(..., description="Artifact or section to update.")
    action: str = Field(..., description="Operation type, such as replace or insert.")
    rationale: Optional[str] = Field(default=None, description="Why the patch is needed.")


class Patch(BaseModel):
    """Placeholder patch plan for local replacement workflows."""

    patch_id: str = Field(..., description="Stable identifier for the patch plan.")
    summary: str = Field(..., description="Short explanation of the requested change.")
    operations: List[PatchOperation] = Field(default_factory=list, description="Planned patch operations.")
    status: str = Field(default="draft", description="Current patch lifecycle state.")

