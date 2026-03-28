"""Tests for heuristic candidate generation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from agent_design_studio.engines.candidate_compare import build_candidate_comparison, build_candidate_comparison_entry
from agent_design_studio.engines.candidate_transforms import compute_candidate_diff, load_candidate_profiles
from agent_design_studio.engines.candidates import HeuristicCandidateGenerator
from agent_design_studio.schemas import CandidateCollection, CandidateComparisonEntry, CandidateDesign
from agent_design_studio.ui.state import (
    adopt_selected_candidate,
    build_current_design_state,
    default_tradeoffs,
    generate_candidates_from_app_state,
    get_active_design_evolution_diff,
    get_selected_candidate,
    initialize_app_state,
    select_candidate_in_app_state,
    update_task_text,
    update_tradeoffs,
)
from agent_design_studio.schemas.user_profile import InvolvementMode


def test_candidate_schema_construction() -> None:
    base_state = initialize_app_state(session_id="candidate-schema")
    candidate_state = base_state.current_design_state
    candidate_preview = base_state.current_design_doc_preview

    candidate = CandidateDesign(
        id="balanced",
        label="Balanced",
        short_description="Moderate design candidate.",
        strategy_differences=["Use moderate validation.", "Keep workflow readable."],
        candidate_design_state=candidate_state,
        candidate_design_summary="Balanced candidate summary.",
        candidate_design_doc_preview=candidate_preview,
    )
    collection = CandidateCollection(
        base_session_id=base_state.session_id,
        base_design_summary=base_state.current_design_summary,
        candidates=[candidate],
    )

    assert collection.candidates[0].label == "Balanced"
    assert collection.base_session_id == "candidate-schema"


def test_candidate_generation_from_current_state() -> None:
    state = initialize_app_state(session_id="candidate-gen")
    state = update_task_text(state, "Create an agent that drafts weekly analyst briefings.")
    state = update_tradeoffs(state, {"robustness": 0.8, "simplicity": 0.7})

    generator = HeuristicCandidateGenerator()
    collection = generator.generate_candidates(
        task_text=state.raw_task_text,
        tradeoffs=state.tradeoffs,
        design_hints=state.design_hints,
        involvement_mode=state.involvement_mode,
        current_design_state=state.current_design_state,
    )

    assert len(collection.candidates) == 4
    assert all(candidate.candidate_design_state.task_spec is not None for candidate in collection.candidates)


def test_candidate_profiles_are_loaded_from_yaml() -> None:
    profiles = load_candidate_profiles()

    assert len(profiles) == 4
    assert [profile.label for profile in profiles] == ["Fast", "Balanced", "Robust", "Simple"]
    assert Path("configs/candidate_profiles.yaml").exists()


def test_candidate_generator_uses_custom_yaml_profiles_instead_of_hardcoded_branching(tmp_path) -> None:
    custom_config = tmp_path / "candidate_profiles.yaml"
    custom_config.write_text(
        """
profiles:
  - id: custom
    label: Custom
    short_description: Custom profile from test config.
    tradeoff_overrides:
      latency: 0.12
      cost: 0.88
      robustness: 0.77
      simplicity: 0.66
    design_hints:
      - Custom hint from YAML.
    strategy:
      validation_depth: targeted
      control_style: explicit_steps
      memory_usage: minimal
      workflow_complexity: shallow
""".strip(),
        encoding="utf-8",
    )
    state = initialize_app_state(session_id="candidate-custom")
    state = update_task_text(state, "Design an agent that summarizes research interviews.")

    generator = HeuristicCandidateGenerator(config_path=custom_config)
    collection = generator.generate_candidates(
        task_text=state.raw_task_text,
        tradeoffs=state.tradeoffs,
        design_hints=state.design_hints,
        involvement_mode=state.involvement_mode,
        current_design_state=state.current_design_state,
    )

    assert [candidate.label for candidate in collection.candidates] == ["Custom"]
    assert collection.candidates[0].candidate_design_state.tradeoffs is not None
    assert collection.candidates[0].candidate_design_state.tradeoffs.latency == 0.12
    assert "Custom hint from YAML." in collection.candidates[0].strategy_differences


def test_malformed_candidate_profile_config_is_rejected(tmp_path) -> None:
    bad_config = tmp_path / "bad_candidate_profiles.yaml"
    bad_config.write_text(
        """
profiles:
  - id: broken
    label: Broken
    tradeoff_overrides:
      latency: 0.5
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_candidate_profiles(bad_config)


def test_candidate_diversity_has_distinct_labels_and_strategies() -> None:
    state = initialize_app_state(session_id="candidate-diversity")
    state = update_task_text(state, "Design an agent that monitors price changes and explains alerts.")

    collection = generate_candidates_from_app_state(state).candidate_collection

    assert collection is not None
    labels = [candidate.label for candidate in collection.candidates]
    assert len(set(labels)) == len(labels)
    strategy_signatures = [tuple(candidate.strategy_differences) for candidate in collection.candidates]
    assert len(set(strategy_signatures)) == len(strategy_signatures)


def test_candidates_are_not_just_relabeled_copies_of_base_design() -> None:
    state = initialize_app_state(session_id="candidate-not-copies")
    state = update_task_text(state, "Create an agent that prepares market summaries.")
    state = update_tradeoffs(state, {"robustness": 0.8, "cost": 0.4})

    collection = generate_candidates_from_app_state(state).candidate_collection

    assert collection is not None
    base_tradeoffs = state.current_design_state.tradeoffs
    candidate_tradeoff_snapshots = [
        candidate.candidate_design_state.tradeoffs.model_dump() for candidate in collection.candidates if candidate.candidate_design_state.tradeoffs
    ]
    assert any(snapshot != base_tradeoffs.model_dump() for snapshot in candidate_tradeoff_snapshots)
    assert any(candidate.candidate_design_state.design_hints != state.current_design_state.design_hints for candidate in collection.candidates)


def test_candidate_design_doc_preview_is_generated() -> None:
    state = initialize_app_state(session_id="candidate-preview")
    state = update_task_text(state, "Create an agent that summarizes customer calls.")

    collection = generate_candidates_from_app_state(state).candidate_collection

    assert collection is not None
    preview_titles = [section.title for section in collection.candidates[0].candidate_design_doc_preview.sections]
    assert "Task Summary" in preview_titles
    assert "Candidate Strategy Differences" in preview_titles


def test_candidate_summary_and_preview_are_recomputed_not_copied_from_base_design() -> None:
    state = initialize_app_state(session_id="candidate-recomputed")
    state = update_task_text(state, "Create an agent that summarizes customer calls.")
    state = update_tradeoffs(state, {"latency": 0.25, "cost": 0.2})
    base_summary = state.current_design_summary
    base_preview_titles = [section.title for section in state.current_design_doc_preview.sections]

    collection = generate_candidates_from_app_state(state).candidate_collection

    assert collection is not None
    fast_candidate = next(candidate for candidate in collection.candidates if candidate.label == "Fast")
    assert fast_candidate.candidate_design_summary != base_summary
    assert "Fast candidate:" in fast_candidate.candidate_design_summary
    candidate_preview_titles = [section.title for section in fast_candidate.candidate_design_doc_preview.sections]
    assert candidate_preview_titles != base_preview_titles
    assert "Candidate Strategy Differences" in candidate_preview_titles


def test_candidate_generation_preserves_base_current_design_state() -> None:
    state = initialize_app_state(session_id="candidate-preserve")
    state = update_task_text(state, "Create an agent that prepares executive research notes.")
    original_design_state = state.current_design_state.model_copy(deep=True)

    updated_state = generate_candidates_from_app_state(state)

    assert updated_state.current_design_state == original_design_state
    assert updated_state.candidate_collection is not None


def test_candidate_generation_is_deterministic_for_same_input_state() -> None:
    state = initialize_app_state(session_id="candidate-deterministic")
    state = update_task_text(state, "Create an agent that drafts investor update memos.")
    state = update_tradeoffs(state, {"latency": 0.4, "simplicity": 0.7})

    first = generate_candidates_from_app_state(state).candidate_collection
    second = generate_candidates_from_app_state(state).candidate_collection

    assert first == second


def test_candidate_generation_handles_empty_task_without_crashing() -> None:
    state = initialize_app_state(session_id="candidate-empty-task")

    collection = generate_candidates_from_app_state(state).candidate_collection

    assert collection is not None
    assert all(candidate.candidate_design_state.status == "draft" for candidate in collection.candidates)
    assert all("candidate" in candidate.candidate_design_summary.lower() for candidate in collection.candidates)


def test_candidate_comparison_reflects_actual_candidate_state() -> None:
    state = initialize_app_state(session_id="candidate-compare")
    state = update_task_text(state, "Create an agent that summarizes user interviews.")

    updated_state = generate_candidates_from_app_state(state)

    assert updated_state.candidate_collection is not None
    comparison = build_candidate_comparison(updated_state.candidate_collection)
    fast_entry = next(entry for entry in comparison.entries if entry.label == "Fast")

    assert fast_entry.validation_style == "light"
    assert fast_entry.control_style == "short_loop"
    assert fast_entry.memory_posture == "minimal"
    assert "L 0.90" in fast_entry.tradeoff_summary


def test_candidate_comparison_changes_when_candidate_state_changes() -> None:
    state = initialize_app_state(session_id="candidate-compare-change")
    state = update_task_text(state, "Create an agent that summarizes user interviews.")
    collection = generate_candidates_from_app_state(state).candidate_collection
    assert collection is not None

    original_comparison = build_candidate_comparison(collection)
    mutated_candidate = collection.candidates[0].model_copy(deep=True)
    mutated_candidate.candidate_design_state.design_strategy["memory_usage"] = "heavy"
    mutated_collection = collection.model_copy(update={"candidates": [mutated_candidate] + collection.candidates[1:]})

    updated_comparison = build_candidate_comparison(mutated_collection)

    assert original_comparison.entries[0].memory_posture != updated_comparison.entries[0].memory_posture


def test_identical_candidate_states_yield_identical_comparison_entries() -> None:
    state = initialize_app_state(session_id="candidate-identical-compare")
    state = update_task_text(state, "Create an agent that summarizes user interviews.")
    collection = generate_candidates_from_app_state(state).candidate_collection
    assert collection is not None

    candidate = collection.candidates[0]
    duplicate = candidate.model_copy(update={"id": "duplicate", "label": "Duplicate"}, deep=True)

    entry_a = build_candidate_comparison_entry(candidate)
    entry_b = build_candidate_comparison_entry(duplicate)

    normalized_a = entry_a.model_dump()
    normalized_b = entry_b.model_dump()
    normalized_a.pop("candidate_id")
    normalized_b.pop("candidate_id")
    normalized_a.pop("label")
    normalized_b.pop("label")

    assert normalized_a == normalized_b


def test_candidate_comparison_is_deterministic() -> None:
    state = initialize_app_state(session_id="candidate-compare-deterministic")
    state = update_task_text(state, "Create an agent that drafts board briefings.")
    collection = generate_candidates_from_app_state(state).candidate_collection
    assert collection is not None

    first = build_candidate_comparison(collection)
    second = build_candidate_comparison(collection)

    assert first == second


def test_candidate_comparison_is_not_just_candidate_labels() -> None:
    state = initialize_app_state(session_id="candidate-compare-semantic")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    collection = generate_candidates_from_app_state(state).candidate_collection
    assert collection is not None

    comparison = build_candidate_comparison(collection)
    entries_by_label = {entry.label: entry for entry in comparison.entries}

    assert entries_by_label["Fast"].validation_style != entries_by_label["Robust"].validation_style
    assert entries_by_label["Fast"].tradeoff_summary != entries_by_label["Robust"].tradeoff_summary


def test_selecting_candidate_updates_shared_state_correctly() -> None:
    state = initialize_app_state(session_id="candidate-select")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    state = generate_candidates_from_app_state(state)

    updated_state = select_candidate_in_app_state(state, "robust")

    assert updated_state.selected_candidate_id == "robust"
    assert get_selected_candidate(updated_state).label == "Robust"


def test_only_one_candidate_is_selected_at_a_time() -> None:
    state = initialize_app_state(session_id="candidate-single-select")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    state = generate_candidates_from_app_state(state)

    selected_once = select_candidate_in_app_state(state, "fast")
    selected_twice = select_candidate_in_app_state(selected_once, "simple")

    assert selected_twice.selected_candidate_id == "simple"
    assert get_selected_candidate(selected_twice).label == "Simple"
    assert selected_twice.candidate_comparison is not None
    assert sum(1 for entry in selected_twice.candidate_comparison.entries if entry.is_selected) == 1


def test_selection_persists_across_rerun_like_state_reads() -> None:
    state = initialize_app_state(session_id="candidate-persist-select")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    state = generate_candidates_from_app_state(state)
    selected_state = select_candidate_in_app_state(state, "balanced")

    assert selected_state.selected_candidate_id == "balanced"
    assert get_selected_candidate(selected_state).label == "Balanced"


def test_selection_is_cleared_when_regenerated_candidates_no_longer_match() -> None:
    state = initialize_app_state(session_id="candidate-clear-select")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    state = generate_candidates_from_app_state(state)
    state = select_candidate_in_app_state(state, "fast")

    stale_collection = state.candidate_collection.model_copy(
        update={"candidates": [candidate for candidate in state.candidate_collection.candidates if candidate.id != "fast"]}
    )
    stale_state = state.model_copy(update={"candidate_collection": stale_collection})
    regenerated_state = generate_candidates_from_app_state(stale_state)

    assert regenerated_state.selected_candidate_id == "fast"


def test_selection_does_not_affect_candidate_generation_logic() -> None:
    state = initialize_app_state(session_id="candidate-select-isolated")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    generated_state = generate_candidates_from_app_state(state)
    selected_state = select_candidate_in_app_state(generated_state, "robust")
    regenerated_state = generate_candidates_from_app_state(selected_state)

    assert generated_state.candidate_collection == regenerated_state.candidate_collection


def test_comparison_reflects_selected_candidate_correctly() -> None:
    state = initialize_app_state(session_id="candidate-compare-select")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    state = generate_candidates_from_app_state(state)

    updated_state = select_candidate_in_app_state(state, "simple")

    assert updated_state.candidate_comparison is not None
    selected_entries = [entry for entry in updated_state.candidate_comparison.entries if entry.is_selected]
    assert len(selected_entries) == 1
    assert selected_entries[0].label == "Simple"


def test_adopting_selected_candidate_updates_current_design_state() -> None:
    state = initialize_app_state(session_id="candidate-adopt")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    state = generate_candidates_from_app_state(state)
    state = select_candidate_in_app_state(state, "robust")
    selected_candidate = get_selected_candidate(state)

    adopted_state = adopt_selected_candidate(state)

    assert adopted_state.current_design_state == selected_candidate.candidate_design_state
    assert adopted_state.tradeoffs == selected_candidate.candidate_design_state.tradeoffs
    assert adopted_state.design_hints == selected_candidate.candidate_design_state.design_hints
    assert adopted_state.active_design_version == 2
    assert adopted_state.previous_active_design is not None
    assert adopted_state.current_design_diff is not None


def test_current_summary_and_doc_reflect_adopted_candidate() -> None:
    state = initialize_app_state(session_id="candidate-adopt-summary")
    state = update_task_text(state, "Create an agent that summarizes support calls.")
    state = generate_candidates_from_app_state(state)
    state = select_candidate_in_app_state(state, "simple")

    adopted_state = adopt_selected_candidate(state)

    assert adopted_state.last_adopted_candidate_label == "Simple"
    assert adopted_state.last_evolution_summary == "v2 adopted from candidate: Simple"
    assert "Active hints:" in adopted_state.current_design_summary
    assert adopted_state.current_design_doc_preview is not None
    preview_titles = [section.title for section in adopted_state.current_design_doc_preview.sections]
    assert "Candidate Strategy Differences" in preview_titles


def test_candidate_adoption_produces_meaningful_active_design_diff() -> None:
    state = initialize_app_state(session_id="candidate-adopt-diff")
    state = update_task_text(state, "Create an agent that summarizes support calls.")
    state = generate_candidates_from_app_state(state)
    state = select_candidate_in_app_state(state, "robust")
    selected_candidate = get_selected_candidate(state)

    adopted_state = adopt_selected_candidate(state)

    assert adopted_state.current_design_diff is not None
    assert "tradeoff_differences" in adopted_state.current_design_diff
    assert selected_candidate.diff is not None
    assert adopted_state.previous_design_state is not None


def test_adopt_does_nothing_when_nothing_is_selected() -> None:
    state = initialize_app_state(session_id="candidate-adopt-none")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    state = generate_candidates_from_app_state(state)

    adopted_state = adopt_selected_candidate(state)

    assert adopted_state == state


def test_adoption_is_deterministic() -> None:
    state = initialize_app_state(session_id="candidate-adopt-deterministic")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    state = generate_candidates_from_app_state(state)
    state = select_candidate_in_app_state(state, "fast")

    first = adopt_selected_candidate(state)
    second = adopt_selected_candidate(state)

    assert first == second


def test_candidate_generation_still_works_after_adoption() -> None:
    state = initialize_app_state(session_id="candidate-adopt-regenerate")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    state = generate_candidates_from_app_state(state)
    state = select_candidate_in_app_state(state, "balanced")
    adopted_state = adopt_selected_candidate(state)

    regenerated_state = generate_candidates_from_app_state(adopted_state)

    assert regenerated_state.candidate_collection is not None
    assert regenerated_state.selected_candidate_id is None
    assert regenerated_state.current_design_state == adopted_state.current_design_state


def test_second_adopt_moves_prior_active_design_into_previous_active_design() -> None:
    state = initialize_app_state(session_id="candidate-adopt-twice")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    state = generate_candidates_from_app_state(state)
    state = select_candidate_in_app_state(state, "fast")
    first_adopted = adopt_selected_candidate(state)

    regenerated = generate_candidates_from_app_state(first_adopted)
    regenerated = select_candidate_in_app_state(regenerated, "robust")
    second_adopted = adopt_selected_candidate(regenerated)

    assert second_adopted.active_design_version == 3
    assert second_adopted.previous_active_design == first_adopted.current_design_state


def test_evolution_diff_reflects_changes_between_previous_and_current_active_designs() -> None:
    state = initialize_app_state(session_id="candidate-evolution-diff")
    state = update_task_text(state, "Create an agent that summarizes support calls.")
    state = generate_candidates_from_app_state(state)
    state = select_candidate_in_app_state(state, "robust")

    adopted_state = adopt_selected_candidate(state)
    evolution_diff = get_active_design_evolution_diff(adopted_state)

    assert evolution_diff is not None
    assert "tradeoff_differences" in evolution_diff
    assert "strategy_differences" in evolution_diff


def test_no_active_design_evolution_diff_exists_before_any_adoption() -> None:
    state = initialize_app_state(session_id="candidate-no-evolution")
    state = update_task_text(state, "Create an agent that summarizes support calls.")

    assert state.previous_active_design is None
    assert state.active_design_version == 1
    assert state.design_history == []
    assert state.last_evolution_summary is None
    assert get_active_design_evolution_diff(state) is None


def test_design_history_is_empty_initially() -> None:
    state = initialize_app_state(session_id="candidate-history-empty")

    assert state.design_history == []


def test_design_history_grows_after_each_adoption() -> None:
    state = initialize_app_state(session_id="candidate-history-grow")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    state = generate_candidates_from_app_state(state)
    state = select_candidate_in_app_state(state, "fast")
    first_adopted = adopt_selected_candidate(state)

    regenerated = generate_candidates_from_app_state(first_adopted)
    regenerated = select_candidate_in_app_state(regenerated, "robust")
    second_adopted = adopt_selected_candidate(regenerated)

    assert len(first_adopted.design_history) == 1
    assert len(second_adopted.design_history) == 2


def test_design_history_versions_match_active_design_version_progression() -> None:
    state = initialize_app_state(session_id="candidate-history-version")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    state = generate_candidates_from_app_state(state)
    state = select_candidate_in_app_state(state, "balanced")
    adopted_state = adopt_selected_candidate(state)

    assert adopted_state.active_design_version == 2
    assert adopted_state.design_history[-1]["version"] == 2


def test_design_history_source_candidate_matches_selected_candidate() -> None:
    state = initialize_app_state(session_id="candidate-history-source")
    state = update_task_text(state, "Create an agent that prepares executive updates.")
    state = generate_candidates_from_app_state(state)
    state = select_candidate_in_app_state(state, "simple")
    adopted_state = adopt_selected_candidate(state)

    assert adopted_state.design_history[-1]["source_candidate"] == "Simple"
    assert adopted_state.design_history[-1]["summary"] == "v2 from Simple"


def test_candidate_diff_detects_meaningful_actual_state_differences() -> None:
    base_state = build_current_design_state(
        session_id="diff-base",
        task_text="Create an agent that summarizes product feedback.",
        tradeoffs=default_tradeoffs(),
        involvement_mode=InvolvementMode.review,
        previous_state=None,
        design_hints=[],
        chat_history=[],
        design_strategy={},
    )
    candidate_state = build_current_design_state(
        session_id="diff-candidate",
        task_text="Create an agent that summarizes product feedback.",
        tradeoffs=default_tradeoffs().model_copy(update={"latency": 0.9, "cost": 0.2}),
        involvement_mode=InvolvementMode.review,
        previous_state=base_state,
        design_hints=["Keep the workflow shallow with very few major steps."],
        chat_history=[],
        design_strategy={
            "validation_depth": "light",
            "control_style": "short_loop",
            "memory_usage": "minimal",
            "workflow_complexity": "lean",
        },
    )

    diff = compute_candidate_diff(base_state, candidate_state)

    assert "tradeoff_differences" in diff
    assert diff["tradeoff_differences"]["latency"]["candidate"] == 0.9
    assert "strategy_differences" in diff
    assert diff["strategy_differences"]["validation_depth"]["candidate"] == "light"
    assert "design_hint_differences" in diff
    assert "Keep the workflow shallow with very few major steps." in diff["design_hint_differences"]["added"]


def test_candidate_diff_is_empty_for_identical_states() -> None:
    state = build_current_design_state(
        session_id="diff-identical",
        task_text="Create an agent that summarizes product feedback.",
        tradeoffs=default_tradeoffs(),
        involvement_mode=InvolvementMode.review,
        previous_state=None,
        design_hints=[],
        chat_history=[],
        design_strategy={},
    )

    diff = compute_candidate_diff(state, state.model_copy(deep=True))

    assert diff == {}


def test_candidate_diff_reflects_config_driven_strategy_changes() -> None:
    state = initialize_app_state(session_id="candidate-diff-config")
    state = update_task_text(state, "Create an agent that drafts board meeting notes.")

    collection = generate_candidates_from_app_state(state).candidate_collection

    assert collection is not None
    robust_candidate = next(candidate for candidate in collection.candidates if candidate.label == "Robust")
    assert "strategy_differences" in robust_candidate.diff
    assert robust_candidate.diff["strategy_differences"]["validation_depth"]["candidate"] == "deep"
    assert "tradeoff_differences" in robust_candidate.diff


def test_candidate_diff_would_expose_relabeled_copy_candidates() -> None:
    state = initialize_app_state(session_id="candidate-diff-copy")
    state = update_task_text(state, "Create an agent that prepares investor summaries.")

    collection = generate_candidates_from_app_state(state).candidate_collection

    assert collection is not None
    assert any(candidate.diff for candidate in collection.candidates)
