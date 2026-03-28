"""Task specification schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class TaskConstraint(BaseModel):
    """A plain-language constraint that shapes the task design."""

    name: str = Field(..., description="Short identifier for the constraint.")
    description: str = Field(..., description="Human-readable description of the constraint.")


class TaskSpec(BaseModel):
    """Structured description of the user task the agent should support."""

    title: str = Field(..., description="Name of the target task.")
    summary: str = Field(..., description="Short explanation of what the task agent should do.")
    primary_goal: str = Field(..., description="Primary success condition for the task.")
    inputs: List[str] = Field(default_factory=list, description="Expected inputs or input channels.")
    outputs: List[str] = Field(default_factory=list, description="Expected outputs or deliverables.")
    constraints: List[TaskConstraint] = Field(default_factory=list, description="Task-specific constraints.")
    sample_tasks: List[str] = Field(default_factory=list, description="Example tasks for future evaluation.")
    notes: Optional[str] = Field(default=None, description="Optional extra context from the user.")

