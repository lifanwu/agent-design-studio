"""Workflow graph schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class WorkflowNode(BaseModel):
    """A node in the visual workflow graph."""

    node_id: str = Field(..., description="Stable node identifier.")
    label: str = Field(..., description="Display label for the node.")
    node_type: str = Field(default="step", description="Node category for visualization.")
    description: Optional[str] = Field(default=None, description="Optional node explanation.")


class WorkflowEdge(BaseModel):
    """A directed edge between two workflow nodes."""

    source: str = Field(..., description="Source node identifier.")
    target: str = Field(..., description="Target node identifier.")
    label: Optional[str] = Field(default=None, description="Optional edge label.")


class WorkflowGraph(BaseModel):
    """Graph representation of the current or planned workflow."""

    nodes: List[WorkflowNode] = Field(default_factory=list, description="Workflow nodes.")
    edges: List[WorkflowEdge] = Field(default_factory=list, description="Workflow edges.")
    description: Optional[str] = Field(default=None, description="Graph-level description.")

