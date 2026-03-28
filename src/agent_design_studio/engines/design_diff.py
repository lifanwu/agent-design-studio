"""Deterministic design diff helpers.

This module stays independent from `ui.state` so both candidate generation and
active-design state updates can import the same diff logic without creating
circular imports during Streamlit reloads.
"""

from agent_design_studio.engines.design_ir import get_design_ir


def compute_design_state_diff(previous_state, current_state) -> dict:
    """Compute a small structured diff between two design artifacts via Design IR."""

    previous_ir = get_design_ir(previous_state)
    current_ir = get_design_ir(current_state)

    diff: dict = {}

    base_tradeoffs = dict(previous_ir.tradeoffs or {})
    candidate_tradeoffs = dict(current_ir.tradeoffs or {})
    tradeoff_differences = {
        key: {"base": base_tradeoffs.get(key), "candidate": candidate_tradeoffs.get(key)}
        for key in sorted(set(base_tradeoffs) | set(candidate_tradeoffs))
        if base_tradeoffs.get(key) != candidate_tradeoffs.get(key)
    }
    if tradeoff_differences:
        diff["tradeoff_differences"] = tradeoff_differences

    base_strategy = {
        "validation_depth": previous_ir.validation.get("depth"),
        "control_style": previous_ir.control.get("style"),
        "memory_usage": previous_ir.memory.get("usage"),
        "workflow_complexity": previous_ir.workflow.get("complexity"),
    }
    candidate_strategy = {
        "validation_depth": current_ir.validation.get("depth"),
        "control_style": current_ir.control.get("style"),
        "memory_usage": current_ir.memory.get("usage"),
        "workflow_complexity": current_ir.workflow.get("complexity"),
    }
    strategy_differences = {
        key: {"base": base_strategy.get(key), "candidate": candidate_strategy.get(key)}
        for key in sorted(set(base_strategy) | set(candidate_strategy))
        if base_strategy.get(key) != candidate_strategy.get(key)
    }
    if strategy_differences:
        diff["strategy_differences"] = strategy_differences

    added_hints = [hint for hint in current_ir.hints if hint not in previous_ir.hints]
    removed_hints = [hint for hint in previous_ir.hints if hint not in current_ir.hints]
    if added_hints or removed_hints:
        diff["design_hint_differences"] = {"added": added_hints, "removed": removed_hints}

    base_workflow = previous_ir.workflow or {}
    candidate_workflow = current_ir.workflow or {}
    workflow_differences = {
        key: {"base": base_workflow.get(key), "candidate": candidate_workflow.get(key)}
        for key in sorted(set(base_workflow) | set(candidate_workflow))
        if base_workflow.get(key) != candidate_workflow.get(key)
    }
    if workflow_differences:
        diff["workflow_differences"] = workflow_differences

    base_status = previous_ir.status
    candidate_status = current_ir.status
    if base_status != candidate_status:
        diff["status_difference"] = {"base": base_status, "candidate": candidate_status}

    return diff
