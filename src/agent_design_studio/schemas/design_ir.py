"""Minimal Design IR schema for the deterministic design system.

This schema formalizes the current lightweight internal representation used by
the design shell. It intentionally stays small and compatible with the
existing DesignState-driven architecture.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DesignIR(BaseModel):
    """Explicit internal representation of the current design.

    Required fields capture the deterministic structure already used by the
    current product. Optional fields reserve space for future design detail
    without forcing any current UI or workflow changes.
    """

    tradeoffs: Dict[str, float] = Field(default_factory=dict, description="Shared normalized tradeoff values.")
    validation: Dict[str, Any] = Field(default_factory=dict, description="Validation posture for the design.")
    control: Dict[str, Any] = Field(default_factory=dict, description="Control-loop posture for the design.")
    memory: Dict[str, Any] = Field(default_factory=dict, description="Memory posture for the design.")
    workflow: Dict[str, Any] = Field(default_factory=dict, description="Workflow posture and structure summary.")
    hints: List[str] = Field(default_factory=list, description="Explicit lightweight design hints.")
    objective: Optional[str] = Field(default=None, description="Optional high-level objective.")
    inputs: Optional[List[str]] = Field(default=None, description="Optional input channels or artifacts.")
    outputs: Optional[List[str]] = Field(default=None, description="Optional output channels or artifacts.")
    constraints: Optional[List[str]] = Field(default=None, description="Optional plain-language design constraints.")
    structure: Optional[Dict[str, Any]] = Field(default=None, description="Optional structural summary.")
    components: Optional[List[str]] = Field(default=None, description="Optional named components.")
    assumptions: Optional[List[str]] = Field(default=None, description="Optional design assumptions.")
    status: Optional[str] = Field(default=None, description="Optional lifecycle/status marker for diff compatibility.")
