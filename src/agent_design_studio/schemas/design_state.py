"""Design state schema."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from agent_design_studio.schemas.design_doc import DesignDoc
from agent_design_studio.schemas.design_ir import DesignIR
from agent_design_studio.schemas.design_space import DesignSpace
from agent_design_studio.schemas.task_spec import TaskSpec
from agent_design_studio.schemas.tradeoff_spec import TradeoffSpec
from agent_design_studio.schemas.user_profile import UserProfile
from agent_design_studio.schemas.visualization import VisualizationBundle
from agent_design_studio.schemas.workflow_graph import WorkflowGraph


class DesignState(BaseModel):
    """Current working state of a design session.

    This model intentionally supports partial states so the product can evolve
    a design from sparse user input toward a fuller structured artifact.
    """

    session_id: str = Field(..., description="Stable identifier for the design session.")
    task_spec: Optional[TaskSpec] = Field(default=None, description="Current task specification, if known.")
    tradeoffs: Optional[TradeoffSpec] = Field(default=None, description="Shared tradeoff preferences.")
    user_profile: Optional[UserProfile] = Field(default=None, description="User collaboration preferences.")
    design_space: Optional[DesignSpace] = Field(default=None, description="Available design space context.")
    workflow_graph: Optional[WorkflowGraph] = Field(default=None, description="Current workflow graph.")
    design_doc: Optional[DesignDoc] = Field(default=None, description="Current source-of-truth document draft.")
    design_ir: Optional[DesignIR] = Field(default=None, description="Explicit Design IR view of the current design.")
    visualization: Optional[VisualizationBundle] = Field(default=None, description="Visualization-ready summaries.")
    design_strategy: Dict[str, str] = Field(default_factory=dict, description="Structured strategy metadata for the current design.")
    design_hints: List[str] = Field(default_factory=list, description="Lightweight design hints derived from chat or controls.")
    chat_history: List[str] = Field(default_factory=list, description="Captured chat messages for the session.")
    status: str = Field(default="draft", description="Current lifecycle status of the design session.")
