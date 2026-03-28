"""Structured schema models for Agent Design Studio."""

from agent_design_studio.schemas.candidate import CandidateCollection, CandidateDesign
from agent_design_studio.schemas.comparison import CandidateComparison, CandidateComparisonEntry
from agent_design_studio.schemas.design_doc import DesignDoc, DesignSection, GeneratedArtifact
from agent_design_studio.schemas.design_ir import DesignIR
from agent_design_studio.schemas.design_space import DesignAxis, DesignConstraint, DesignOption, DesignSpace, StrategyAxis
from agent_design_studio.schemas.design_state import DesignState
from agent_design_studio.schemas.evaluation_result import EvaluationEvidence, EvaluationMetric, EvaluationResult
from agent_design_studio.schemas.patch import Patch, PatchOperation
from agent_design_studio.schemas.task_spec import TaskConstraint, TaskSpec
from agent_design_studio.schemas.tradeoff_spec import TradeoffSpec
from agent_design_studio.schemas.user_profile import InvolvementMode, UserProfile
from agent_design_studio.schemas.visualization import DesignDiffEntry, TradeoffPoint, VisualizationBundle, VisualizationPanel
from agent_design_studio.schemas.workflow_graph import WorkflowEdge, WorkflowGraph, WorkflowNode

__all__ = [
    "CandidateCollection",
    "CandidateDesign",
    "CandidateComparison",
    "CandidateComparisonEntry",
    "DesignAxis",
    "DesignConstraint",
    "DesignOption",
    "DesignDiffEntry",
    "DesignDoc",
    "DesignIR",
    "DesignSection",
    "DesignSpace",
    "DesignState",
    "EvaluationEvidence",
    "EvaluationMetric",
    "EvaluationResult",
    "GeneratedArtifact",
    "InvolvementMode",
    "Patch",
    "PatchOperation",
    "TaskConstraint",
    "StrategyAxis",
    "TaskSpec",
    "TradeoffPoint",
    "TradeoffSpec",
    "UserProfile",
    "VisualizationBundle",
    "VisualizationPanel",
    "WorkflowEdge",
    "WorkflowGraph",
    "WorkflowNode",
]
