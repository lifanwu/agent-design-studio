"""Tests for explicit Design IR construction and usage."""

from agent_design_studio.engines.design_diff import compute_design_state_diff
from agent_design_studio.engines.design_ir import build_design_ir, get_design_ir
from agent_design_studio.schemas import DesignIR
from agent_design_studio.ui.state import (
    adopt_selected_candidate,
    default_tradeoffs,
    generate_candidates_from_app_state,
    initialize_app_state,
    select_candidate_in_app_state,
    update_task_text,
)


def test_design_ir_builds_with_required_fields_only() -> None:
    design_ir = build_design_ir(
        tradeoffs=default_tradeoffs(),
        validation={"depth": "light"},
        control={"style": "short_loop"},
        memory={"usage": "minimal"},
        workflow={"complexity": "lean", "node_count": 3, "edge_count": 2},
        hints=["Keep the workflow shallow."],
    )

    assert isinstance(design_ir, DesignIR)
    assert design_ir.tradeoffs["latency"] == 0.5
    assert design_ir.validation["depth"] == "light"
    assert design_ir.objective is None
    assert design_ir.assumptions is None


def test_current_design_state_exposes_explicit_design_ir() -> None:
    state = initialize_app_state(session_id="design-ir-state")
    state = update_task_text(state, "Create an agent that drafts weekly portfolio updates.")

    design_ir = state.current_design_state.design_ir

    assert design_ir is not None
    assert design_ir.tradeoffs == state.tradeoffs.model_dump()
    assert design_ir.objective == state.current_design_state.task_spec.primary_goal
    assert design_ir.hints == state.design_hints
    assert design_ir.workflow["node_count"] == len(state.current_design_state.workflow_graph.nodes)


def test_candidate_generation_returns_candidates_with_valid_design_ir() -> None:
    state = initialize_app_state(session_id="design-ir-candidates")
    state = update_task_text(state, "Create an agent that summarizes expert interviews.")
    state = generate_candidates_from_app_state(state)

    assert state.candidate_collection is not None
    robust_candidate = next(candidate for candidate in state.candidate_collection.candidates if candidate.id == "robust")

    assert robust_candidate.candidate_design_state.design_ir is not None
    assert robust_candidate.candidate_design_state.design_ir.validation["depth"] == "deep"
    assert robust_candidate.candidate_design_state.design_ir.control["style"] == "conservative"
    assert robust_candidate.candidate_design_state.design_ir.memory["usage"] == "selective"


def test_diff_helpers_work_directly_on_design_ir_objects() -> None:
    base_ir = build_design_ir(
        tradeoffs=default_tradeoffs(),
        validation={"depth": "light"},
        control={"style": "short_loop"},
        memory={"usage": "minimal"},
        workflow={"complexity": "lean", "node_count": 3, "edge_count": 2},
        hints=["Keep it simple."],
        status="draft",
    )
    candidate_ir = build_design_ir(
        tradeoffs=default_tradeoffs().model_copy(update={"latency": 0.9, "robustness": 0.9}),
        validation={"depth": "deep"},
        control={"style": "gated_review"},
        memory={"usage": "contextual"},
        workflow={"complexity": "layered", "node_count": 4, "edge_count": 3},
        hints=["Keep it simple.", "Add stronger checks."],
        status="partial",
    )

    diff = compute_design_state_diff(base_ir, candidate_ir)

    assert diff["tradeoff_differences"]["latency"]["candidate"] == 0.9
    assert diff["strategy_differences"]["validation_depth"]["candidate"] == "deep"
    assert diff["design_hint_differences"]["added"] == ["Add stronger checks."]
    assert diff["status_difference"]["candidate"] == "partial"


def test_adoption_and_history_continue_to_work_after_ir_formalization() -> None:
    state = initialize_app_state(session_id="design-ir-adoption")
    state = update_task_text(state, "Create an agent that prepares earnings call digests.")
    state = generate_candidates_from_app_state(state)
    state = select_candidate_in_app_state(state, "fast")

    adopted_state = adopt_selected_candidate(state)

    assert adopted_state.current_design_state.design_ir is not None
    assert adopted_state.active_design_version == 2
    assert adopted_state.design_history[-1]["source_candidate"] == "Fast"
    assert adopted_state.current_design_state.design_ir.tradeoffs == adopted_state.tradeoffs.model_dump()


def test_get_design_ir_can_reconstruct_when_explicit_field_is_omitted() -> None:
    state = initialize_app_state(session_id="design-ir-rebuild")
    state = update_task_text(state, "Create an agent that summarizes support escalations.")
    state_without_ir = state.current_design_state.model_copy(update={"design_ir": None})

    rebuilt_ir = get_design_ir(state_without_ir)

    assert rebuilt_ir.tradeoffs == state.tradeoffs.model_dump()
    assert rebuilt_ir.workflow["node_count"] == len(state.current_design_state.workflow_graph.nodes)
    assert rebuilt_ir.assumptions == state.current_design_state.design_doc.assumptions
