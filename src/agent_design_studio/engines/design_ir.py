"""Lightweight Design IR helpers.

Current conceptual alignment:
- the active/current design artifact is treated as the DesignDoc
- the current config-like structure is treated as Design IR

To avoid a large refactor, the deterministic system still moves mostly through
``DesignState`` objects. This module provides one explicit, stable IR surface
that those states can populate and downstream logic can consume.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

from agent_design_studio.schemas.design_doc import DesignDoc
from agent_design_studio.schemas.design_ir import DesignIR
from agent_design_studio.schemas.design_state import DesignState
from agent_design_studio.schemas.task_spec import TaskConstraint
from agent_design_studio.schemas.tradeoff_spec import TradeoffSpec


def build_design_ir(
    *,
    tradeoffs: TradeoffSpec | Mapping[str, float] | None,
    validation: Mapping[str, Any] | None,
    control: Mapping[str, Any] | None,
    memory: Mapping[str, Any] | None,
    workflow: Mapping[str, Any] | None,
    hints: Iterable[str] | None,
    objective: Optional[str] = None,
    inputs: Optional[list[str]] = None,
    outputs: Optional[list[str]] = None,
    constraints: Optional[list[str]] = None,
    structure: Optional[Mapping[str, Any]] = None,
    components: Optional[list[str]] = None,
    assumptions: Optional[list[str]] = None,
    status: Optional[str] = None,
) -> DesignIR:
    """Construct a valid Design IR object from explicit deterministic inputs."""

    tradeoff_map = tradeoffs.model_dump() if isinstance(tradeoffs, TradeoffSpec) else dict(tradeoffs or {})
    return DesignIR(
        tradeoffs=tradeoff_map,
        validation=dict(validation or {}),
        control=dict(control or {}),
        memory=dict(memory or {}),
        workflow=dict(workflow or {}),
        hints=list(hints or []),
        objective=objective,
        inputs=list(inputs) if inputs is not None else None,
        outputs=list(outputs) if outputs is not None else None,
        constraints=list(constraints) if constraints is not None else None,
        structure=dict(structure) if structure is not None else None,
        components=list(components) if components is not None else None,
        assumptions=list(assumptions) if assumptions is not None else None,
        status=status,
    )


def build_design_ir_from_state(design_state: DesignState) -> DesignIR:
    """Construct a Design IR object from the current deterministic DesignState."""

    strategy = design_state.design_strategy or {}
    task_spec = design_state.task_spec
    design_doc = design_state.design_doc
    workflow_graph = design_state.workflow_graph
    constraint_descriptions = []
    if task_spec:
        constraint_descriptions.extend(_constraint_descriptions(task_spec.constraints))
    if design_doc and design_doc.constraints:
        constraint_descriptions.extend(design_doc.constraints)

    component_labels = [node.label for node in workflow_graph.nodes] if workflow_graph else None
    structure = design_doc.structure if design_doc and design_doc.structure else None
    if structure is None and workflow_graph:
        structure = {
            "node_ids": [node.node_id for node in workflow_graph.nodes],
            "edge_count": len(workflow_graph.edges),
        }

    return build_design_ir(
        tradeoffs=design_state.tradeoffs,
        validation={"depth": strategy.get("validation_depth", "unspecified")},
        control={"style": strategy.get("control_style", "unspecified")},
        memory={"usage": strategy.get("memory_usage", "unspecified")},
        workflow={
            "complexity": strategy.get("workflow_complexity", "unspecified"),
            "node_count": len(workflow_graph.nodes) if workflow_graph else 0,
            "edge_count": len(workflow_graph.edges) if workflow_graph else 0,
        },
        hints=design_state.design_hints,
        objective=(design_doc.objective if design_doc and design_doc.objective else (task_spec.primary_goal if task_spec else None)),
        inputs=(design_doc.inputs if design_doc and design_doc.inputs is not None else (task_spec.inputs if task_spec else None)),
        outputs=(design_doc.outputs if design_doc and design_doc.outputs is not None else (task_spec.outputs if task_spec else None)),
        constraints=constraint_descriptions or None,
        structure=structure,
        components=(design_doc.components if design_doc and design_doc.components is not None else component_labels),
        assumptions=(design_doc.assumptions if design_doc and design_doc.assumptions else None),
        status=design_state.status,
    )


def get_design_ir(design_artifact: Any) -> DesignIR:
    """Return the Design IR view of a supported design artifact."""

    if isinstance(design_artifact, DesignIR):
        return design_artifact
    if isinstance(design_artifact, DesignState):
        return design_artifact.design_ir or build_design_ir_from_state(design_artifact)
    if isinstance(design_artifact, DesignDoc):
        return build_design_ir(
            tradeoffs=design_artifact.tradeoffs,
            validation={},
            control={},
            memory={},
            workflow={},
            hints=[],
            objective=design_artifact.objective,
            inputs=design_artifact.inputs,
            outputs=design_artifact.outputs,
            constraints=design_artifact.constraints,
            structure=design_artifact.structure,
            components=design_artifact.components,
            assumptions=design_artifact.assumptions or None,
            status=design_artifact.status,
        )
    return design_artifact


def _constraint_descriptions(constraints: list[TaskConstraint]) -> list[str]:
    """Return plain-language task constraint descriptions."""

    return [constraint.description for constraint in constraints]
