"""Tests for shared UI session state and builders."""

import pytest
from pydantic import ValidationError

from agent_design_studio.ui.app import _widget_defaults_from_app_state, main as app_main
from agent_design_studio.ui.chat_intents import parse_chat_intent
from agent_design_studio.ui.state import (
    apply_chat_adjustment,
    build_design_doc_preview,
    build_current_design_state,
    default_tradeoffs,
    initialize_app_state,
    update_task_text,
    update_tradeoffs,
)
from agent_design_studio.schemas.user_profile import InvolvementMode


def test_app_state_initialization_creates_shared_defaults() -> None:
    state = initialize_app_state(session_id="session-test")

    assert state.session_id == "session-test"
    assert state.raw_task_text == ""
    assert state.tradeoffs.explainability == 0.7
    assert state.design_hints == []
    assert state.current_design_state.session_id == "session-test"
    assert state.current_design_doc_preview is not None
    assert state.involvement_mode.value == "exploratory"
    assert state.current_design_summary != ""


def test_app_module_imports_for_render_smoke() -> None:
    assert callable(app_main)


def test_empty_state_has_preview_sections() -> None:
    state = initialize_app_state(session_id="session-empty")

    assert state.current_design_doc_preview is not None
    preview_titles = [section.title for section in state.current_design_doc_preview.sections]
    assert "Task Summary" in preview_titles
    assert "Current Preferences" in preview_titles


def test_intent_parser_returns_tradeoff_updates_for_supported_messages() -> None:
    intent = parse_chat_intent("make it cheaper and prioritize speed")

    assert intent.intent_kind == "tradeoff_update"
    assert intent.tradeoff_updates["cost"] < 0
    assert intent.tradeoff_updates["latency"] > 0


def test_intent_parser_returns_design_hints_for_supported_messages() -> None:
    intent = parse_chat_intent("use no memory")

    assert intent.intent_kind == "design_hint_update"
    assert "Avoid memory-heavy workflow state where possible." in intent.design_hints


def test_intent_parser_returns_mixed_updates_when_message_contains_both_kinds() -> None:
    intent = parse_chat_intent("avoid a complex workflow")

    assert intent.intent_kind == "mixed_update"
    assert intent.tradeoff_updates["simplicity"] > 0
    assert "Keep the workflow shallow and easy to inspect." in intent.design_hints


def test_intent_parser_returns_no_op_for_unclear_messages() -> None:
    intent = parse_chat_intent("hello there")

    assert intent.intent_kind == "no_op"
    assert intent.tradeoff_updates == {}
    assert intent.design_hints == []


def test_no_op_chat_adjustment_preserves_existing_shared_state() -> None:
    state = initialize_app_state(session_id="session-no-op")
    state = update_task_text(state, "Create an agent that drafts support replies.")
    state = update_tradeoffs(state, {"latency": 0.3, "robustness": 0.8})

    updated_state = apply_chat_adjustment(state, "hello there")

    assert updated_state.raw_task_text == state.raw_task_text
    assert updated_state.tradeoffs == state.tradeoffs
    assert updated_state.design_hints == state.design_hints
    assert updated_state.last_intent_result is not None
    assert updated_state.last_intent_result.intent_kind == "no_op"


def test_tradeoff_updates_replace_shared_state_values() -> None:
    state = initialize_app_state(session_id="session-test")

    updated_state = update_tradeoffs(state, {"latency": 0.2, "cost": 0.3})

    assert updated_state.tradeoffs.latency == 0.2
    assert updated_state.tradeoffs.cost == 0.3
    assert updated_state.current_design_state.tradeoffs is not None
    assert updated_state.current_design_state.tradeoffs.latency == 0.2
    assert updated_state.current_design_diff is not None
    assert updated_state.current_design_diff["tradeoff_differences"]["latency"]["candidate"] == 0.2


def test_widget_defaults_follow_canonical_tradeoff_state_after_chat_update() -> None:
    state = initialize_app_state(session_id="session-widget-sync")
    state = update_task_text(state, "Create an agent that drafts support responses.")

    updated_state = apply_chat_adjustment(state, "make it cheaper")
    widget_defaults = _widget_defaults_from_app_state(updated_state)

    assert widget_defaults["slider_cost"] == updated_state.tradeoffs.cost
    assert widget_defaults["slider_latency"] == updated_state.tradeoffs.latency


def test_invalid_tradeoff_update_is_rejected_loudly() -> None:
    state = initialize_app_state(session_id="session-invalid-slider")

    with pytest.raises(ValidationError):
        update_tradeoffs(state, {"latency": 1.2})


def test_slider_updates_refresh_summary_and_preview_without_losing_task_text() -> None:
    state = initialize_app_state(session_id="session-slider-refresh")
    with_task = update_task_text(state, "Design an agent that reviews CRM notes and flags follow-ups.")

    updated_state = update_tradeoffs(with_task, {"robustness": 0.9, "cost": 0.2})

    assert updated_state.raw_task_text == with_task.raw_task_text
    assert updated_state.current_design_summary != with_task.current_design_summary
    assert updated_state.current_design_doc_preview is not None
    preferences_section = next(
        section for section in updated_state.current_design_doc_preview.sections if section.title == "Current Preferences"
    )
    assert "Robustness: 0.90" in preferences_section.content
    assert "Cost: 0.20" in preferences_section.content


def test_task_text_updates_shared_state_and_builds_task_spec() -> None:
    state = initialize_app_state(session_id="session-task")

    updated_state = update_task_text(state, "Design an agent that triages incoming support requests.")

    assert updated_state.raw_task_text == "Design an agent that triages incoming support requests."
    assert updated_state.current_design_state.task_spec is not None
    assert "triages incoming support requests" in updated_state.current_design_state.task_spec.summary
    assert updated_state.current_design_diff is not None
    assert updated_state.current_design_diff["status_difference"]["candidate"] == "partial"


def test_task_update_refreshes_summary_and_preview_without_resetting_sliders() -> None:
    state = initialize_app_state(session_id="session-task-refresh")
    with_slider_changes = update_tradeoffs(state, {"latency": 0.3, "simplicity": 0.75})

    updated_state = update_task_text(with_slider_changes, "Create an agent that drafts concise client update emails.")

    assert updated_state.tradeoffs.latency == 0.3
    assert updated_state.tradeoffs.simplicity == 0.75
    assert updated_state.current_design_summary != with_slider_changes.current_design_summary
    assert updated_state.current_design_doc_preview is not None
    task_section = next(section for section in updated_state.current_design_doc_preview.sections if section.title == "Task Summary")
    assert "drafts concise client update emails" in task_section.content


def test_task_text_and_sliders_persist_without_overwriting_each_other() -> None:
    state = initialize_app_state(session_id="session-persist")
    with_task = update_task_text(state, "Create a lightweight analyst copilot for weekly reports.")

    combined_state = update_tradeoffs(with_task, {"latency": 0.25, "simplicity": 0.8})

    assert combined_state.raw_task_text == "Create a lightweight analyst copilot for weekly reports."
    assert combined_state.tradeoffs.latency == 0.25
    assert combined_state.tradeoffs.simplicity == 0.8
    assert combined_state.current_design_state.task_spec is not None
    assert "weekly reports" in combined_state.current_design_state.task_spec.summary
    assert combined_state.current_design_state.tradeoffs is not None
    assert combined_state.current_design_state.tradeoffs.latency == 0.25


def test_chat_adjustment_updates_tradeoffs_without_overwriting_task_text() -> None:
    state = initialize_app_state(session_id="session-chat")
    with_task = update_task_text(state, "Create an agent that drafts concise research digests.")

    updated_state = apply_chat_adjustment(with_task, "make it cheaper")

    assert updated_state.raw_task_text == "Create an agent that drafts concise research digests."
    assert updated_state.tradeoffs.cost < with_task.tradeoffs.cost
    assert updated_state.current_design_state.tradeoffs is not None
    assert updated_state.current_design_state.tradeoffs.cost == updated_state.tradeoffs.cost


def test_chat_adjustment_stores_design_hints_in_shared_state() -> None:
    state = initialize_app_state(session_id="session-hints")
    with_task = update_task_text(state, "Design a lightweight agent for monitoring price changes.")

    updated_state = apply_chat_adjustment(with_task, "use no memory")

    assert "Avoid memory-heavy workflow state where possible." in updated_state.design_hints
    assert "Avoid memory-heavy workflow state where possible." in updated_state.current_design_state.design_hints


def test_design_doc_preview_refreshes_after_chat_adjustment() -> None:
    state = initialize_app_state(session_id="session-preview-refresh")
    with_task = update_task_text(state, "Create an agent that summarizes meeting notes.")

    updated_state = apply_chat_adjustment(with_task, "keep it simple")

    assert updated_state.current_design_summary != with_task.current_design_summary
    assert updated_state.current_design_doc_preview is not None
    design_doc_section_titles = [section.title for section in updated_state.current_design_doc_preview.sections]
    assert "Design Hints" in design_doc_section_titles
    design_hints_section = next(section for section in updated_state.current_design_doc_preview.sections if section.title == "Design Hints")
    assert "Favor a small number of explicit workflow steps." in design_hints_section.content
    assert updated_state.current_design_diff is not None
    assert "design_hint_differences" in updated_state.current_design_diff


def test_task_sliders_and_chat_adjustments_persist_together() -> None:
    state = initialize_app_state(session_id="session-consistency")
    with_task = update_task_text(state, "Create an agent that prepares weekly market briefs.")
    with_sliders = update_tradeoffs(with_task, {"latency": 0.2, "robustness": 0.85})
    combined_state = apply_chat_adjustment(with_sliders, "use no memory")

    assert combined_state.raw_task_text == "Create an agent that prepares weekly market briefs."
    assert combined_state.tradeoffs.latency == 0.2
    assert combined_state.tradeoffs.robustness == 0.85
    assert "Avoid memory-heavy workflow state where possible." in combined_state.design_hints
    assert combined_state.current_design_state.task_spec is not None
    assert "weekly market briefs" in combined_state.current_design_state.task_spec.summary


def test_repeated_mixed_tradeoff_updates_remain_consistent() -> None:
    state = initialize_app_state(session_id="session-mixed-tradeoffs")
    state = update_task_text(state, "Create an agent that summarizes research notes.")
    after_slider = update_tradeoffs(state, {"cost": 0.6, "robustness": 0.8})
    after_chat = apply_chat_adjustment(after_slider, "make it cheaper")
    final_state = update_tradeoffs(after_chat, {"cost": 0.15, "latency": 0.7})
    widget_defaults = _widget_defaults_from_app_state(final_state)
    preferences_section = next(
        section for section in final_state.current_design_doc_preview.sections if section.title == "Current Preferences"
    )

    assert final_state.tradeoffs.cost == 0.15
    assert final_state.tradeoffs.latency == 0.7
    assert widget_defaults["slider_cost"] == 0.15
    assert widget_defaults["slider_latency"] == 0.7
    assert "Cost: 0.15" in preferences_section.content
    assert "Latency: 0.70" in preferences_section.content


def test_current_design_state_is_built_from_task_and_preferences() -> None:
    design_state = build_current_design_state(
        session_id="session-build",
        task_text="Design an agent that summarizes uploaded PDFs for analysts.",
        tradeoffs=default_tradeoffs(),
        involvement_mode=InvolvementMode.review,
        previous_state=None,
        design_hints=[],
        chat_history=[],
        design_strategy={},
    )

    assert design_state.task_spec is not None
    assert "summarizes uploaded PDFs" in design_state.task_spec.summary
    assert design_state.user_profile is not None
    assert design_state.user_profile.involvement_mode is InvolvementMode.review
    assert design_state.workflow_graph is not None
    assert len(design_state.workflow_graph.nodes) >= 3


def test_partial_design_state_handles_empty_task_without_fake_specificity() -> None:
    design_state = build_current_design_state(
        session_id="session-empty-task",
        task_text="",
        tradeoffs=default_tradeoffs(),
        involvement_mode=InvolvementMode.exploratory,
        previous_state=None,
        design_hints=[],
        chat_history=[],
        design_strategy={},
    )

    assert design_state.task_spec is None
    assert design_state.status == "draft"
    assert design_state.design_doc is not None
    assert "awaiting task details" in design_state.design_doc.summary.lower()


def test_design_doc_preview_contains_required_sections() -> None:
    design_state = build_current_design_state(
        session_id="session-preview",
        task_text="Create a monitoring assistant for price changes across a watchlist.",
        tradeoffs=default_tradeoffs(),
        involvement_mode=InvolvementMode.exploratory,
        previous_state=None,
        design_hints=["Avoid memory-heavy workflow state where possible."],
        chat_history=[],
        design_strategy={},
    )

    preview = build_design_doc_preview(design_state)
    section_titles = [section.title for section in preview.sections]

    assert "Task Summary" in section_titles
    assert "Current Preferences" in section_titles
    assert "Design Hints" in section_titles
    assert "Current Design Assumptions" in section_titles
    assert "Current Limitations / Unresolved Areas" in section_titles


def test_design_doc_preview_reflects_current_tradeoffs_not_stale_defaults() -> None:
    design_state = build_current_design_state(
        session_id="session-preview-tradeoffs",
        task_text="Create an agent that reviews contract drafts.",
        tradeoffs=default_tradeoffs().model_copy(update={"cost": 0.1, "robustness": 0.95}),
        involvement_mode=InvolvementMode.review,
        previous_state=None,
        design_hints=[],
        chat_history=[],
        design_strategy={},
    )

    preview = build_design_doc_preview(design_state)
    preferences_section = next(section for section in preview.sections if section.title == "Current Preferences")

    assert "Cost: 0.10" in preferences_section.content
    assert "Robustness: 0.95" in preferences_section.content


def test_no_active_design_diff_exists_before_first_meaningful_update() -> None:
    state = initialize_app_state(session_id="session-no-diff-yet")

    assert state.previous_design_state is None
    assert state.current_design_diff is None


def test_active_design_diff_is_deterministic_for_same_update_sequence() -> None:
    state_a = initialize_app_state(session_id="session-diff-det-a")
    state_a = update_task_text(state_a, "Create an agent that drafts support responses.")
    state_a = update_tradeoffs(state_a, {"cost": 0.2})

    state_b = initialize_app_state(session_id="session-diff-det-b")
    state_b = update_task_text(state_b, "Create an agent that drafts support responses.")
    state_b = update_tradeoffs(state_b, {"cost": 0.2})

    assert state_a.current_design_diff == state_b.current_design_diff
