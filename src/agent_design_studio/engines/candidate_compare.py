"""Deterministic candidate comparison builder."""

from agent_design_studio.schemas import CandidateCollection, CandidateComparison, CandidateComparisonEntry


def build_candidate_comparison(
    candidate_collection: CandidateCollection,
    selected_candidate_id: str | None = None,
) -> CandidateComparison:
    """Build a compact side-by-side comparison artifact from actual candidate state."""

    entries = [
        build_candidate_comparison_entry(candidate, selected_candidate_id=selected_candidate_id)
        for candidate in candidate_collection.candidates
    ]
    return CandidateComparison(
        base_session_id=candidate_collection.base_session_id,
        entries=entries,
    )


def build_candidate_comparison_entry(candidate, selected_candidate_id: str | None = None) -> CandidateComparisonEntry:
    """Build one comparison entry from the candidate's actual state and diff."""

    tradeoffs = candidate.candidate_design_state.tradeoffs
    strategy = candidate.candidate_design_state.design_strategy or {}
    added_hints = candidate.diff.get("design_hint_differences", {}).get("added", [])
    tradeoff_summary = (
        f"L {tradeoffs.latency:.2f} | R {tradeoffs.robustness:.2f} | "
        f"S {tradeoffs.simplicity:.2f} | C {tradeoffs.cost:.2f} | E {tradeoffs.explainability:.2f}"
        if tradeoffs
        else "No tradeoff data"
    )
    design_hint_summary = "; ".join(added_hints[:3]) if added_hints else "No additional hints"

    return CandidateComparisonEntry(
        candidate_id=candidate.id,
        label=candidate.label,
        is_selected=candidate.id == selected_candidate_id,
        tradeoff_summary=tradeoff_summary,
        validation_style=str(strategy.get("validation_depth", "unspecified")),
        control_style=str(strategy.get("control_style", "unspecified")),
        memory_posture=str(strategy.get("memory_usage", "unspecified")),
        workflow_complexity=str(strategy.get("workflow_complexity", "unspecified")),
        design_hint_summary=design_hint_summary,
    )
