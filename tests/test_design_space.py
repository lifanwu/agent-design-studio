"""Tests for the internal deterministic DesignSpace layer."""

from agent_design_studio.engines.candidate_transforms import load_candidate_profiles, resolve_profile_options
from agent_design_studio.engines.design_space import build_internal_design_space
from agent_design_studio.ui.state import (
    adopt_selected_candidate,
    generate_candidates_from_app_state,
    get_active_design_evolution_diff,
    initialize_app_state,
    select_candidate_in_app_state,
    update_task_text,
)


def test_internal_design_space_structure_is_valid() -> None:
    design_space = build_internal_design_space()
    axes_by_key = {axis.key: axis for axis in design_space.strategy_axes}

    assert set(axes_by_key) == {"validation", "control", "memory", "workflow"}
    assert {option.name for option in axes_by_key["validation"].options} == {"light", "moderate", "deep", "targeted"}
    assert {option.name for option in axes_by_key["memory"].options} == {"minimal", "selective"}


def test_profile_mappings_resolve_to_valid_design_space_options() -> None:
    design_space = build_internal_design_space()
    profiles = load_candidate_profiles()

    resolved = {profile.id: resolve_profile_options(profile, design_space) for profile in profiles}

    assert resolved["fast"]["validation"].name == "light"
    assert resolved["balanced"]["control"].name == "guided_review"
    assert resolved["robust"]["memory"].name == "selective"
    assert resolved["simple"]["workflow"].name == "shallow"


def test_candidate_generation_through_design_space_still_produces_valid_ir() -> None:
    state = initialize_app_state(session_id="design-space-candidates")
    state = update_task_text(state, "Create an agent that drafts weekly client update notes.")
    state = generate_candidates_from_app_state(state)

    assert state.candidate_collection is not None
    fast_candidate = next(candidate for candidate in state.candidate_collection.candidates if candidate.id == "fast")
    assert fast_candidate.candidate_design_state.design_space is not None
    assert fast_candidate.candidate_design_state.design_ir is not None
    assert fast_candidate.candidate_design_state.design_ir.workflow["complexity"] == "lean"


def test_current_profile_semantics_remain_stable_after_design_space_refactor() -> None:
    state = initialize_app_state(session_id="design-space-stable")
    state = update_task_text(state, "Create an agent that summarizes support escalations.")
    state = generate_candidates_from_app_state(state)

    assert state.candidate_collection is not None
    entries = {candidate.label: candidate for candidate in state.candidate_collection.candidates}

    assert entries["Fast"].candidate_design_state.design_strategy["validation_depth"] == "light"
    assert entries["Balanced"].candidate_design_state.design_strategy["control_style"] == "guided_review"
    assert entries["Robust"].candidate_design_state.design_strategy["workflow_complexity"] == "layered"
    assert entries["Simple"].candidate_design_state.design_strategy["memory_usage"] == "minimal"


def test_comparison_adoption_and_history_flows_still_work_with_internal_design_space() -> None:
    state = initialize_app_state(session_id="design-space-flow")
    state = update_task_text(state, "Create an agent that prepares portfolio monitoring digests.")
    state = generate_candidates_from_app_state(state)
    state = select_candidate_in_app_state(state, "robust")

    adopted_state = adopt_selected_candidate(state)

    assert adopted_state.current_design_state.design_space is not None
    assert adopted_state.design_history[-1]["source_candidate"] == "Robust"
    assert get_active_design_evolution_diff(adopted_state) is not None
