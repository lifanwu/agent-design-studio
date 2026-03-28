"""Streamlit app for the shared co-design session shell."""

from pathlib import Path
import sys

if __package__ in (None, ""):
    repo_src = Path(__file__).resolve().parents[2]
    if str(repo_src) not in sys.path:
        sys.path.insert(0, str(repo_src))

import streamlit as st
from agent_design_studio.ui.state import (
    adopt_selected_candidate,
    AppState,
    apply_chat_adjustment,
    generate_candidates_from_app_state,
    get_active_design_evolution_diff,
    get_selected_candidate,
    initialize_app_state,
    select_candidate_in_app_state,
    summarize_design_state,
    update_involvement_mode,
    update_task_text,
    update_tradeoffs,
)


MODE_OPTIONS = ["exploratory", "review", "one_click"]


def _get_app_state() -> AppState:
    """Load or initialize the shared app state from Streamlit session storage."""

    if "app_state" not in st.session_state:
        st.session_state.app_state = initialize_app_state()
    return st.session_state.app_state


def _set_app_state(app_state: AppState) -> AppState:
    """Persist the app state back into Streamlit session storage."""

    st.session_state.app_state = app_state
    return app_state


def _widget_defaults_from_app_state(app_state: AppState) -> dict[str, object]:
    """Build widget values directly from the canonical shared app state."""

    return {
        "task_input": app_state.raw_task_text,
        "follow_up_adjustment": app_state.latest_chat_adjustment,
        "involvement_mode_widget": app_state.involvement_mode.value,
        "slider_latency": float(app_state.tradeoffs.latency),
        "slider_robustness": float(app_state.tradeoffs.robustness),
        "slider_simplicity": float(app_state.tradeoffs.simplicity),
        "slider_cost": float(app_state.tradeoffs.cost),
        "slider_explainability": float(app_state.tradeoffs.explainability),
    }


def _ensure_widget_state() -> None:
    """Sync widget-backed session state from the canonical shared app state."""

    app_state = _get_app_state()
    defaults = _widget_defaults_from_app_state(app_state)
    for key, value in defaults.items():
        if key == "follow_up_adjustment" and key in st.session_state:
            continue
        st.session_state[key] = value


def _sync_task_input() -> None:
    """Push the task input widget value into shared app state."""

    app_state = _get_app_state()
    _set_app_state(update_task_text(app_state, st.session_state.task_input))


def _sync_involvement_mode() -> None:
    """Push the involvement mode widget value into shared app state."""

    app_state = _get_app_state()
    _set_app_state(update_involvement_mode(app_state, st.session_state.involvement_mode_widget))


def _sync_tradeoffs() -> None:
    """Push the slider widget values into shared app state."""

    app_state = _get_app_state()
    slider_updates = {
        "latency": float(st.session_state.slider_latency),
        "robustness": float(st.session_state.slider_robustness),
        "simplicity": float(st.session_state.slider_simplicity),
        "cost": float(st.session_state.slider_cost),
        "explainability": float(st.session_state.slider_explainability),
    }
    _set_app_state(update_tradeoffs(app_state, slider_updates))


def _apply_follow_up_adjustment() -> None:
    """Parse and apply the follow-up chat adjustment from the widget state."""

    app_state = _get_app_state()
    _set_app_state(apply_chat_adjustment(app_state, st.session_state.follow_up_adjustment))


def _generate_candidates() -> None:
    """Generate candidate designs from the current shared app state."""

    app_state = _get_app_state()
    _set_app_state(generate_candidates_from_app_state(app_state))


def _select_candidate(candidate_id: str) -> None:
    """Select a candidate as the currently preferred design."""

    app_state = _get_app_state()
    _set_app_state(select_candidate_in_app_state(app_state, candidate_id))


def _adopt_selected_candidate() -> None:
    """Promote the currently selected candidate into the active design state."""

    app_state = _get_app_state()
    _set_app_state(adopt_selected_candidate(app_state))


def main() -> None:
    """Render the stateful co-design shell."""

    st.set_page_config(page_title="Agent Design Studio", layout="wide")
    st.title("Agent Design Studio")
    st.caption("Chat-first agent architecture co-design with shared session state.")
    _ensure_widget_state()
    app_state = _get_app_state()

    left, right = st.columns([1, 2])

    with left:
        st.subheader("Controls")
        st.selectbox(
            "Involvement mode",
            options=MODE_OPTIONS,
            key="involvement_mode_widget",
            on_change=_sync_involvement_mode,
        )

        for label in app_state.tradeoffs.model_dump().keys():
            st.slider(
                label.capitalize(),
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                key=f"slider_{label}",
                on_change=_sync_tradeoffs,
            )

        st.divider()
        st.text_area(
            "Task input",
            placeholder="Describe the task, goals, or preferred agent behavior...",
            height=140,
            key="task_input",
            on_change=_sync_task_input,
        )

        st.text_input(
            "Follow-up design adjustment",
            placeholder="Example: make it cheaper, keep it simple, use no memory",
            key="follow_up_adjustment",
        )
        st.button("Apply Chat Adjustment", on_click=_apply_follow_up_adjustment)
        st.button("Generate Candidates", on_click=_generate_candidates)

        st.divider()
        st.markdown("### Current Tradeoff Values")
        tradeoff_rows = [
            {
                "Axis": key.capitalize(),
                "Value": f"{value:.2f}",
            }
            for key, value in app_state.tradeoffs.model_dump().items()
        ]
        st.table(tradeoff_rows)

        st.button("Refresh Current Design", type="primary", on_click=_sync_task_input)

    app_state = _get_app_state()

    with right:
        st.subheader("Visualization")
        panel_a, panel_b, panel_c = st.columns(3)

        with panel_a:
            st.markdown("### Workflow Graph")
            if app_state.current_design_state.workflow_graph:
                for node in app_state.current_design_state.workflow_graph.nodes:
                    st.write(f"- {node.label}: {node.description or 'Current workflow step.'}")
            else:
                st.info("No workflow graph has been built yet.")

        with panel_b:
            st.markdown("### Tradeoff Chart")
            current_tradeoffs = app_state.tradeoffs.model_dump()
            st.bar_chart(current_tradeoffs, horizontal=True)

        with panel_c:
            st.markdown("### Design Evolution Diff")
            evolution_diff = get_active_design_evolution_diff(app_state)
            if evolution_diff:
                st.caption(
                    f"Previous active version: v{app_state.active_design_version - 1} | "
                    f"Current active version: v{app_state.active_design_version}"
                )
                if app_state.last_evolution_summary:
                    st.write(app_state.last_evolution_summary)
                if app_state.last_adopted_candidate_label:
                    st.write(f"Source candidate: {app_state.last_adopted_candidate_label}")
                st.json(evolution_diff)
            else:
                st.info("No active-design evolution yet.")

        st.divider()
        st.markdown("### Task Summary")
        if app_state.current_design_state.task_spec:
            st.write(app_state.current_design_state.task_spec.summary)
        else:
            st.info("Add task text to populate the current task summary.")

        st.markdown("### Tradeoff Summary")
        tradeoff_summary_lines = [
            f"{key.capitalize()}: {value:.2f}"
            for key, value in app_state.tradeoffs.model_dump().items()
        ]
        st.write("\n".join(tradeoff_summary_lines))

        st.markdown("### Design Hints")
        if app_state.design_hints:
            for hint in app_state.design_hints:
                st.write(f"- {hint}")
        else:
            st.info("No chat-derived design hints yet.")

        st.markdown("### Current Design Summary")
        st.write(app_state.current_design_summary or summarize_design_state(app_state.current_design_state))
        if app_state.last_adopted_candidate_label:
            st.caption(f"Active design currently reflects adopted candidate: {app_state.last_adopted_candidate_label}")

        st.markdown("### Design Evolution History")
        if app_state.design_history:
            for entry in reversed(app_state.design_history):
                marker = " (current)" if entry["version"] == app_state.active_design_version else ""
                st.write(f"v{entry['version']} <- {entry['source_candidate']}{marker}")
        else:
            st.info("No design evolution history yet.")

        chat_intent_summary = (
            app_state.last_intent_result.explanation
            if app_state.last_intent_result
            else "No parsed follow-up chat adjustment."
        )
        with st.expander(f"Last Chat Intent: {chat_intent_summary}", expanded=False):
            if app_state.last_intent_result:
                st.write(app_state.last_intent_result.explanation)
                st.json(app_state.last_intent_result.model_dump(mode="json"))
            else:
                st.info("No follow-up chat adjustment has been parsed yet.")

        state_payload = app_state.current_design_state.model_dump(mode="json", exclude_none=True)
        state_summary = (
            f"Status: {app_state.current_design_state.status} | "
            f"Hints: {len(app_state.current_design_state.design_hints)} | "
            f"Chat messages: {len(app_state.current_design_state.chat_history)}"
        )
        with st.expander(f"Current Design State: {state_summary}", expanded=False):
            st.json(state_payload)

        st.markdown("### DesignDoc Preview")
        if app_state.current_design_doc_preview:
            for section in app_state.current_design_doc_preview.sections:
                st.markdown(f"**{section.title}**")
                st.write(section.content)
        else:
            st.info("No design document preview is available yet.")

        st.divider()
        st.markdown("### Candidates")
        if app_state.candidate_comparison and app_state.candidate_comparison.entries:
            st.markdown("**Candidate Comparison**")
            comparison_rows = [
                {
                    "Candidate": entry.label,
                    "Selected": "Yes" if entry.is_selected else "",
                    "Tradeoffs": entry.tradeoff_summary,
                    "Validation": entry.validation_style,
                    "Control": entry.control_style,
                    "Memory": entry.memory_posture,
                    "Workflow": entry.workflow_complexity,
                    "Hints": entry.design_hint_summary,
                }
                for entry in app_state.candidate_comparison.entries
            ]
            st.table(comparison_rows)

        if app_state.candidate_collection and app_state.candidate_collection.candidates:
            for candidate in app_state.candidate_collection.candidates:
                header = f"{candidate.label}: {candidate.short_description}"
                if app_state.selected_candidate_id == candidate.id:
                    header = f"{header} [Selected]"
                with st.expander(header, expanded=False):
                    st.write(candidate.candidate_design_summary)
                    st.button(
                        "Select this design",
                        key=f"select_candidate_{candidate.id}",
                        on_click=_select_candidate,
                        args=(candidate.id,),
                    )
                    st.markdown("**Base vs Candidate Diff**")
                    if candidate.diff:
                        st.json(candidate.diff)
                    else:
                        st.write("No differences detected from the base design.")
                    st.markdown("**Strategy Differences**")
                    for item in candidate.strategy_differences:
                        st.write(f"- {item}")
                    st.markdown("**Candidate DesignDoc Preview**")
                    for section in candidate.candidate_design_doc_preview.sections:
                        st.markdown(f"**{section.title}**")
                        st.write(section.content)
        else:
            st.info("Generate candidates to inspect multiple design directions from the current base state.")

        st.divider()
        st.markdown("### Selected Candidate")
        selected_candidate = get_selected_candidate(app_state)
        if selected_candidate:
            st.write(f"**{selected_candidate.label}**")
            st.write(selected_candidate.candidate_design_summary)
            st.button("Adopt selected design", on_click=_adopt_selected_candidate)
            if selected_candidate.diff:
                st.markdown("**Selected Candidate Diff**")
                st.json(selected_candidate.diff)
        else:
            st.info("No candidate is currently selected.")

        st.divider()
        st.markdown("### Debug Panel")
        st.markdown("**Current Task Text**")
        st.write(app_state.raw_task_text or "No task entered yet.")
        st.markdown("**Current Tradeoff State**")
        st.json(app_state.tradeoffs.model_dump(mode="json"))
        st.markdown("**Current Design Hints**")
        st.write(app_state.design_hints or ["No design hints yet."])
        st.markdown("**Current DesignState Summary**")
        st.write(app_state.current_design_summary)


if __name__ == "__main__":
    main()
