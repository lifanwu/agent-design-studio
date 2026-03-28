"""Shared UI session state for the Streamlit co-design shell."""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from agent_design_studio.schemas.candidate import CandidateCollection
from agent_design_studio.schemas.comparison import CandidateComparison
from agent_design_studio.schemas.design_doc import DesignDoc, DesignSection, GeneratedArtifact
from agent_design_studio.schemas.design_state import DesignState
from agent_design_studio.schemas.task_spec import TaskSpec
from agent_design_studio.schemas.tradeoff_spec import TradeoffSpec
from agent_design_studio.schemas.user_profile import InvolvementMode, UserProfile
from agent_design_studio.schemas.visualization import DesignDiffEntry, TradeoffPoint, VisualizationBundle, VisualizationPanel
from agent_design_studio.schemas.workflow_graph import WorkflowEdge, WorkflowGraph, WorkflowNode
from agent_design_studio.ui.chat_intents import ChatIntentResult, parse_chat_intent


DEFAULT_SESSION_ID_PREFIX = "studio-session"


class AppState(BaseModel):
    """Shared UI state that keeps chat, sliders, and design artifacts aligned."""

    session_id: str = Field(..., description="Stable session identifier for the current UI session.")
    raw_task_text: str = Field(default="", description="Latest raw task description entered by the user.")
    latest_chat_adjustment: str = Field(default="", description="Latest follow-up design adjustment entered in chat.")
    tradeoffs: TradeoffSpec = Field(..., description="Normalized tradeoff state shared across UI surfaces.")
    design_hints: List[str] = Field(default_factory=list, description="Shared lightweight design hints derived from chat.")
    involvement_mode: InvolvementMode = Field(..., description="Current user collaboration mode.")
    current_design_state: DesignState = Field(..., description="Current partial design state.")
    current_design_doc_preview: Optional[DesignDoc] = Field(
        default=None,
        description="Lightweight preview of the current design document.",
    )
    previous_active_design: Optional[DesignState] = Field(
        default=None,
        description="Snapshot of the active design immediately before the latest adoption.",
    )
    previous_design_state: Optional[DesignState] = Field(
        default=None,
        description="Previous design state snapshot for future diff support.",
    )
    active_design_version: int = Field(
        default=1,
        description="Monotonic version for the current active design.",
    )
    design_history: List[dict] = Field(
        default_factory=list,
        description="Minimal deterministic evolution history for adopted active designs.",
    )
    current_design_summary: str = Field(
        default="",
        description="Readable summary of the current design state for the UI.",
    )
    current_design_diff: Optional[dict] = Field(
        default=None,
        description="Structured diff between the previous and current active design states.",
    )
    last_evolution_summary: Optional[str] = Field(
        default=None,
        description="Deterministic summary of the latest active-design evolution event.",
    )
    candidate_collection: Optional[CandidateCollection] = Field(
        default=None,
        description="Most recently generated candidate collection derived from the base design state.",
    )
    candidate_comparison: Optional[CandidateComparison] = Field(
        default=None,
        description="Compact side-by-side comparison view for current candidates.",
    )
    selected_candidate_id: Optional[str] = Field(
        default=None,
        description="The currently preferred candidate chosen by the user.",
    )
    last_adopted_candidate_label: Optional[str] = Field(
        default=None,
        description="Most recently adopted candidate label for lightweight UI feedback.",
    )
    last_intent_result: Optional[ChatIntentResult] = Field(
        default=None,
        description="Most recent parsed chat intent result.",
    )


def default_tradeoffs() -> TradeoffSpec:
    """Return the baseline shared tradeoff state for a new session."""

    return TradeoffSpec(
        latency=0.5,
        robustness=0.7,
        simplicity=0.6,
        cost=0.5,
        explainability=0.7,
    )


def initialize_app_state(session_id: Optional[str] = None) -> AppState:
    """Create the initial app state for a new or restored session."""

    resolved_session_id = session_id or f"{DEFAULT_SESSION_ID_PREFIX}-{uuid4().hex[:8]}"
    tradeoffs = default_tradeoffs()
    current_design_state = build_current_design_state(
        session_id=resolved_session_id,
        task_text="",
        tradeoffs=tradeoffs,
        involvement_mode=InvolvementMode.exploratory,
        previous_state=None,
    )
    current_design_doc_preview = build_design_doc_preview(current_design_state)
    return AppState(
        session_id=resolved_session_id,
        tradeoffs=tradeoffs,
        design_hints=[],
        involvement_mode=InvolvementMode.exploratory,
        current_design_state=current_design_state,
        current_design_doc_preview=current_design_doc_preview,
        previous_active_design=None,
        active_design_version=1,
        design_history=[],
        current_design_summary=summarize_design_state(current_design_state),
        current_design_diff=None,
        last_evolution_summary=None,
    )


def update_task_text(state: AppState, task_text: str) -> AppState:
    """Store new raw task text and rebuild the shared partial design state."""

    return rebuild_app_state(state, raw_task_text=task_text)


def update_tradeoffs(state: AppState, updates: Mapping[str, float]) -> AppState:
    """Apply slider changes and rebuild the shared partial design state."""

    normalized_tradeoffs = normalize_tradeoffs(state.tradeoffs, updates)
    return rebuild_app_state(state, tradeoffs=normalized_tradeoffs)


def update_involvement_mode(state: AppState, involvement_mode: InvolvementMode | str) -> AppState:
    """Update collaboration mode and rebuild the shared partial design state."""

    normalized_mode = InvolvementMode(involvement_mode)
    return rebuild_app_state(state, involvement_mode=normalized_mode)


def apply_chat_adjustment(state: AppState, message: str) -> AppState:
    """Parse a follow-up chat message and apply its structured updates to shared state."""

    intent_result = parse_chat_intent(message)
    next_tradeoffs = state.tradeoffs
    next_design_hints = list(state.design_hints)

    if intent_result.tradeoff_updates:
        next_tradeoffs = apply_tradeoff_deltas(state.tradeoffs, intent_result.tradeoff_updates)

    for hint in intent_result.design_hints:
        if hint not in next_design_hints:
            next_design_hints.append(hint)

    return rebuild_app_state(
        state,
        tradeoffs=next_tradeoffs,
        design_hints=next_design_hints,
        latest_chat_adjustment=message,
        last_intent_result=intent_result,
        append_chat_message=message if message.strip() else None,
    )


def generate_candidates_from_app_state(state: AppState) -> AppState:
    """Generate heuristic candidates from the current shared base design state."""

    from agent_design_studio.engines.candidate_compare import build_candidate_comparison
    from agent_design_studio.engines.candidates import HeuristicCandidateGenerator

    generator = HeuristicCandidateGenerator()
    candidate_collection = generator.generate_candidates(
        task_text=state.raw_task_text,
        tradeoffs=state.tradeoffs,
        design_hints=state.design_hints,
        involvement_mode=state.involvement_mode,
        current_design_state=state.current_design_state,
    )
    candidate_ids = {candidate.id for candidate in candidate_collection.candidates}
    selected_candidate_id = state.selected_candidate_id if state.selected_candidate_id in candidate_ids else None
    candidate_comparison = build_candidate_comparison(
        candidate_collection,
        selected_candidate_id=selected_candidate_id,
    )
    return state.model_copy(
        update={
            "candidate_collection": candidate_collection,
            "candidate_comparison": candidate_comparison,
            "selected_candidate_id": selected_candidate_id,
        }
    )


def select_candidate_in_app_state(state: AppState, candidate_id: str) -> AppState:
    """Mark exactly one generated candidate as the currently preferred design."""

    from agent_design_studio.engines.candidate_compare import build_candidate_comparison

    if not state.candidate_collection:
        raise ValueError("Cannot select a candidate before candidates have been generated.")

    valid_ids = {candidate.id for candidate in state.candidate_collection.candidates}
    if candidate_id not in valid_ids:
        raise ValueError(f"Unknown candidate id: {candidate_id}")

    candidate_comparison = (
        build_candidate_comparison(state.candidate_collection, selected_candidate_id=candidate_id)
        if state.candidate_collection
        else None
    )
    return state.model_copy(
        update={
            "selected_candidate_id": candidate_id,
            "candidate_comparison": candidate_comparison,
        }
    )


def get_selected_candidate(state: AppState):
    """Return the currently selected candidate object, if any."""

    if not state.candidate_collection or not state.selected_candidate_id:
        return None
    for candidate in state.candidate_collection.candidates:
        if candidate.id == state.selected_candidate_id:
            return candidate
    return None


def get_active_design_evolution_diff(state: AppState) -> Optional[dict]:
    """Return the adoption-based evolution diff for the active design, if available."""

    if state.previous_active_design is None:
        return None

    from agent_design_studio.engines.design_diff import compute_design_state_diff

    return compute_design_state_diff(state.previous_active_design, state.current_design_state)


def adopt_selected_candidate(state: AppState) -> AppState:
    """Promote the selected candidate into the active current design state.

    Post-adoption behavior is explicit:
    - current/base design becomes the selected candidate's design
    - summaries and previews are refreshed from that adopted design
    - candidate collection, comparison, and selection are cleared
    """

    selected_candidate = get_selected_candidate(state)
    if selected_candidate is None:
        return state

    from agent_design_studio.engines.design_diff import compute_design_state_diff

    previous_active_design = state.current_design_state.model_copy(deep=True)
    previous_design_state = state.current_design_state.model_copy(deep=True)
    adopted_design_state = selected_candidate.candidate_design_state.model_copy(deep=True)
    adopted_design_doc_preview = selected_candidate.candidate_design_doc_preview.model_copy(deep=True)
    current_design_diff = compute_design_state_diff(previous_active_design, adopted_design_state)

    next_tradeoffs = adopted_design_state.tradeoffs or state.tradeoffs
    next_involvement_mode = (
        adopted_design_state.user_profile.involvement_mode
        if adopted_design_state.user_profile
        else state.involvement_mode
    )
    next_active_design_version = state.active_design_version + 1
    last_evolution_summary = f"v{next_active_design_version} adopted from candidate: {selected_candidate.label}"
    next_design_history = list(state.design_history)
    next_design_history.append(
        {
            "version": next_active_design_version,
            "source_candidate": selected_candidate.label,
            "summary": f"v{next_active_design_version} from {selected_candidate.label}",
        }
    )

    return state.model_copy(
        update={
            "tradeoffs": next_tradeoffs,
            "design_hints": list(adopted_design_state.design_hints),
            "involvement_mode": next_involvement_mode,
            "current_design_state": adopted_design_state,
            "current_design_doc_preview": adopted_design_doc_preview,
            "previous_active_design": previous_active_design,
            "previous_design_state": previous_design_state,
            "active_design_version": next_active_design_version,
            "design_history": next_design_history,
            "current_design_summary": summarize_design_state(adopted_design_state),
            "current_design_diff": current_design_diff,
            "last_evolution_summary": last_evolution_summary,
            "candidate_collection": None,
            "candidate_comparison": None,
            "selected_candidate_id": None,
            "last_adopted_candidate_label": selected_candidate.label,
        }
    )


def normalize_tradeoffs(base_tradeoffs: TradeoffSpec, updates: Mapping[str, float]) -> TradeoffSpec:
    """Return a normalized tradeoff model after a slider update."""

    merged_values: Dict[str, float] = base_tradeoffs.model_dump()
    for key, value in updates.items():
        merged_values[key] = float(value)
    return TradeoffSpec(**merged_values)


def apply_tradeoff_deltas(base_tradeoffs: TradeoffSpec, deltas: Mapping[str, float]) -> TradeoffSpec:
    """Apply bounded tradeoff deltas from a parsed chat intent."""

    updated_values = base_tradeoffs.model_dump()
    for key, delta in deltas.items():
        current_value = float(updated_values.get(key, 0.5))
        updated_values[key] = min(1.0, max(0.0, round(current_value + float(delta), 3)))
    return TradeoffSpec(**updated_values)


def rebuild_app_state(
    state: AppState,
    raw_task_text: Optional[str] = None,
    tradeoffs: Optional[TradeoffSpec] = None,
    involvement_mode: Optional[InvolvementMode] = None,
    design_hints: Optional[List[str]] = None,
    latest_chat_adjustment: Optional[str] = None,
    last_intent_result: Optional[ChatIntentResult] = None,
    append_chat_message: Optional[str] = None,
) -> AppState:
    """Recompute the current design state and preview from explicit inputs."""

    next_task_text = raw_task_text if raw_task_text is not None else state.raw_task_text
    next_tradeoffs = tradeoffs or state.tradeoffs
    next_mode = involvement_mode or state.involvement_mode
    next_design_hints = design_hints if design_hints is not None else state.design_hints
    next_chat_adjustment = latest_chat_adjustment if latest_chat_adjustment is not None else state.latest_chat_adjustment
    previous_design_state = state.current_design_state
    next_chat_history = list(previous_design_state.chat_history) if previous_design_state else []
    if append_chat_message and append_chat_message.strip():
        next_chat_history.append(append_chat_message.strip())
    current_design_state = build_current_design_state(
        session_id=state.session_id,
        task_text=next_task_text,
        tradeoffs=next_tradeoffs,
        involvement_mode=next_mode,
        previous_state=previous_design_state,
        design_hints=next_design_hints,
        chat_history=next_chat_history,
    )
    current_design_doc_preview = build_design_doc_preview(current_design_state)
    current_design_diff = None
    if previous_design_state is not None:
        from agent_design_studio.engines.design_diff import compute_design_state_diff

        current_design_diff = compute_design_state_diff(previous_design_state, current_design_state)
    return state.model_copy(
        update={
            "raw_task_text": next_task_text,
            "latest_chat_adjustment": next_chat_adjustment,
            "tradeoffs": next_tradeoffs,
            "design_hints": next_design_hints,
            "involvement_mode": next_mode,
            "current_design_state": current_design_state,
            "current_design_doc_preview": current_design_doc_preview,
            "previous_design_state": previous_design_state,
            "current_design_summary": summarize_design_state(current_design_state),
            "current_design_diff": current_design_diff,
            "last_intent_result": last_intent_result if latest_chat_adjustment is not None else state.last_intent_result,
        }
    )


def build_current_design_state(
    session_id: str,
    task_text: str,
    tradeoffs: TradeoffSpec,
    involvement_mode: InvolvementMode,
    previous_state: Optional[DesignState],
    design_hints: Optional[List[str]] = None,
    chat_history: Optional[List[str]] = None,
    design_strategy: Optional[Dict[str, str]] = None,
) -> DesignState:
    """Build a heuristic partial design state from the current UI inputs."""

    from agent_design_studio.engines.design_ir import build_design_ir
    from agent_design_studio.engines.design_space import build_internal_design_space

    trimmed_task_text = task_text.strip()
    task_spec = _build_task_spec(trimmed_task_text)
    workflow_graph = _build_workflow_graph(task_spec, involvement_mode)
    visualization = _build_visualization_bundle(tradeoffs, task_spec, workflow_graph, previous_state)
    shared_design_hints = design_hints or []
    assumptions = _derive_assumptions(task_spec, tradeoffs, involvement_mode, shared_design_hints)
    limitations = _derive_limitations(task_spec)
    design_doc = DesignDoc(
        title=f"{task_spec.title} Design Preview" if task_spec else "Untitled Design Preview",
        summary=f"Partial design state for {task_spec.title.lower()}." if task_spec else "Partial design state awaiting task details.",
        problem_statement=task_spec.summary if task_spec else None,
        objective=task_spec.primary_goal if task_spec else None,
        inputs=task_spec.inputs if task_spec else None,
        outputs=task_spec.outputs if task_spec else None,
        constraints=limitations or None,
        tradeoffs=tradeoffs.model_dump(),
        structure={
            "validation": {"depth": (design_strategy or {}).get("validation_depth", "unspecified")},
            "control": {"style": (design_strategy or {}).get("control_style", "unspecified")},
            "memory": {"usage": (design_strategy or {}).get("memory_usage", "unspecified")},
            "workflow": {
                "complexity": (design_strategy or {}).get("workflow_complexity", "unspecified"),
                "node_count": len(workflow_graph.nodes),
                "edge_count": len(workflow_graph.edges),
            },
        },
        components=[node.label for node in workflow_graph.nodes],
        assumptions=assumptions,
        open_questions=limitations,
        sections=[
            DesignSection(
                title="Current Task Framing",
                content=task_spec.summary if task_spec else "No task description has been provided yet.",
            ),
            DesignSection(
                title="Interaction Mode",
                content=f"The current collaboration mode is `{involvement_mode.value}`.",
            ),
            DesignSection(
                title="Design Hints",
                content=_join_lines(shared_design_hints) or "No additional design hints have been provided yet.",
            ),
        ],
        artifacts=[
            GeneratedArtifact(artifact_type="design_doc_preview", status="preview"),
        ],
    )
    design_ir = build_design_ir(
        tradeoffs=tradeoffs,
        validation={"depth": (design_strategy or {}).get("validation_depth", "unspecified")},
        control={"style": (design_strategy or {}).get("control_style", "unspecified")},
        memory={"usage": (design_strategy or {}).get("memory_usage", "unspecified")},
        workflow={
            "complexity": (design_strategy or {}).get("workflow_complexity", "unspecified"),
            "node_count": len(workflow_graph.nodes),
            "edge_count": len(workflow_graph.edges),
        },
        hints=shared_design_hints,
        objective=task_spec.primary_goal if task_spec else None,
        inputs=task_spec.inputs if task_spec else None,
        outputs=task_spec.outputs if task_spec else None,
        constraints=limitations or None,
        structure=design_doc.structure,
        components=design_doc.components,
        assumptions=assumptions or None,
        status="partial" if trimmed_task_text else "draft",
    )
    return DesignState(
        session_id=session_id,
        task_spec=task_spec,
        tradeoffs=tradeoffs,
        user_profile=UserProfile(involvement_mode=involvement_mode),
        design_space=build_internal_design_space(),
        workflow_graph=workflow_graph,
        design_doc=design_doc,
        design_ir=design_ir,
        visualization=visualization,
        design_strategy=design_strategy or {},
        design_hints=shared_design_hints,
        chat_history=chat_history if chat_history is not None else ([trimmed_task_text] if trimmed_task_text else []),
        status="partial" if trimmed_task_text else "draft",
    )


def build_design_doc_preview(design_state: DesignState) -> DesignDoc:
    """Generate a readable preview document from the current partial design state."""

    task_summary = (
        design_state.task_spec.summary
        if design_state.task_spec
        else "Task summary is still blank. The user has not described the task yet."
    )
    tradeoff_summary = _format_tradeoffs(design_state.tradeoffs or default_tradeoffs())
    assumptions = design_state.design_doc.assumptions if design_state.design_doc else []
    limitations = design_state.design_doc.open_questions if design_state.design_doc else []
    design_hints = design_state.design_hints

    return DesignDoc(
        title=f"{design_state.task_spec.title if design_state.task_spec else 'Untitled'} Preview",
        summary="Readable preview of the current partial design document.",
        problem_statement=task_summary,
        assumptions=assumptions,
        open_questions=limitations,
        sections=[
            DesignSection(title="Task Summary", content=task_summary),
            DesignSection(title="Current Preferences", content=tradeoff_summary),
            DesignSection(
                title="Design Hints",
                content=_join_lines(design_hints) or "No additional design hints have been captured yet.",
            ),
            DesignSection(
                title="Current Design Assumptions",
                content=_join_lines(assumptions) or "No assumptions have been captured yet.",
            ),
            DesignSection(
                title="Current Limitations / Unresolved Areas",
                content=_join_lines(limitations) or "No limitations have been captured yet.",
            ),
        ],
        artifacts=[GeneratedArtifact(artifact_type="preview_only", status="preview")],
    )


def summarize_design_state(design_state: DesignState) -> str:
    """Create a short human-readable summary for the current design state."""

    if not design_state.task_spec or not design_state.tradeoffs or not design_state.user_profile:
        return "The design shell is ready. Add a task description to build the first partial design state."

    return (
        f"Current design focuses on '{design_state.task_spec.title}' in "
        f"`{design_state.user_profile.involvement_mode.value}` mode. "
        f"Tradeoff emphasis: robustness {design_state.tradeoffs.robustness:.2f}, "
        f"explainability {design_state.tradeoffs.explainability:.2f}, "
        f"latency {design_state.tradeoffs.latency:.2f}. "
        f"Active hints: {len(design_state.design_hints)}."
    )


def _build_task_spec(task_text: str) -> Optional[TaskSpec]:
    """Create a simple task spec from raw task text."""

    if not task_text:
        return None

    summary = " ".join(task_text.split())
    first_line = summary.split(".")[0].strip() or summary
    words = first_line.split()
    title = " ".join(words[:6]).strip().title() or "Untitled Task"
    return TaskSpec(
        title=title,
        summary=summary,
        primary_goal=f"Co-design a useful agent architecture for: {first_line}.",
        inputs=["chat task description", "persistent tradeoff settings"],
        outputs=["partial design state", "design doc preview"],
        notes="Heuristic task extraction only. This is not candidate generation.",
    )


def _build_workflow_graph(task_spec: Optional[TaskSpec], involvement_mode: InvolvementMode) -> WorkflowGraph:
    """Create a small workflow graph that reflects the current design state."""

    nodes = [
        WorkflowNode(node_id="capture", label="Capture Task", description="Take the latest chat/task input."),
        WorkflowNode(node_id="shape", label="Shape Design", description="Apply shared tradeoff preferences."),
        WorkflowNode(
            node_id="review",
            label="Review With User" if involvement_mode != InvolvementMode.one_click else "Prepare Fast Draft",
            description=f"Current involvement mode: {involvement_mode.value}.",
        ),
    ]
    edges = [
        WorkflowEdge(source="capture", target="shape"),
        WorkflowEdge(source="shape", target="review"),
    ]

    if task_spec:
        nodes.append(
            WorkflowNode(
                node_id="task",
                label=task_spec.title,
                node_type="task",
                description="Current task anchor for the partial design state.",
            )
        )
        edges.insert(0, WorkflowEdge(source="task", target="capture"))

    return WorkflowGraph(
        nodes=nodes,
        edges=edges,
        description="Heuristic workflow graph for the current co-design session.",
    )


def _build_visualization_bundle(
    tradeoffs: TradeoffSpec,
    task_spec: Optional[TaskSpec],
    workflow_graph: WorkflowGraph,
    previous_state: Optional[DesignState],
) -> VisualizationBundle:
    """Create visualization-ready placeholder data from the current design state."""

    diff_entries = []
    if previous_state and previous_state.task_spec and task_spec:
        if previous_state.task_spec.summary != task_spec.summary:
            diff_entries.append(
                DesignDiffEntry(
                    field_name="task_spec.summary",
                    change_summary="Task framing changed from the previous state.",
                    impact_level="medium",
                )
            )
    elif previous_state and previous_state.tradeoffs != tradeoffs:
        diff_entries.append(
            DesignDiffEntry(
                field_name="tradeoffs",
                change_summary="Tradeoff preferences changed from the previous state.",
                impact_level="medium",
            )
        )

    return VisualizationBundle(
        panels=[
            VisualizationPanel(panel_id="workflow_graph", title="Workflow Graph", panel_type="graph", status="active"),
            VisualizationPanel(panel_id="tradeoff_chart", title="Tradeoff Chart", panel_type="chart", status="active"),
            VisualizationPanel(panel_id="design_diff", title="Design Diff", panel_type="diff", status="placeholder"),
        ],
        tradeoff_points=[
            TradeoffPoint(
                label="Current",
                latency=tradeoffs.latency,
                robustness=tradeoffs.robustness,
                simplicity=tradeoffs.simplicity,
                cost=tradeoffs.cost,
                explainability=tradeoffs.explainability,
            )
        ],
        diff_entries=diff_entries,
    )


def _derive_assumptions(
    task_spec: Optional[TaskSpec],
    tradeoffs: TradeoffSpec,
    involvement_mode: InvolvementMode,
    design_hints: List[str],
) -> list[str]:
    """Derive a few explicit assumptions from the current inputs."""

    assumptions = [
        "Chat remains the primary control surface for design changes.",
        "Persistent sliders continue to represent the shared tradeoff state.",
        f"The user currently prefers `{involvement_mode.value}` collaboration.",
    ]
    if task_spec:
        assumptions.append(f"The task can be reasonably framed as '{task_spec.title}'.")
    if tradeoffs.robustness >= 0.7:
        assumptions.append("The design should bias toward reliability over aggressive speed optimization.")
    if tradeoffs.simplicity >= 0.7:
        assumptions.append("The current design should stay deliberately simple and easy to inspect.")
    assumptions.extend(design_hints)
    return assumptions


def _derive_limitations(task_spec: Optional[TaskSpec]) -> list[str]:
    """List current unresolved areas for the partial design state."""

    limitations = [
        "No candidate generation has been run yet.",
        "No evidence-based evaluation has been performed yet.",
        "No compile or runtime logic has been produced yet.",
    ]
    if not task_spec:
        limitations.insert(0, "The task description is still empty, so the design is only a shell.")
    else:
        limitations.append("The workflow is heuristic and should be refined as the task becomes more specific.")
    return limitations


def _format_tradeoffs(tradeoffs: TradeoffSpec) -> str:
    """Format current tradeoff values for human-readable display."""

    return (
        f"Latency: {tradeoffs.latency:.2f}\n"
        f"Robustness: {tradeoffs.robustness:.2f}\n"
        f"Simplicity: {tradeoffs.simplicity:.2f}\n"
        f"Cost: {tradeoffs.cost:.2f}\n"
        f"Explainability: {tradeoffs.explainability:.2f}"
    )


def _join_lines(items: list[str]) -> str:
    """Join bullet-like lines into a readable text block."""

    return "\n".join(f"- {item}" for item in items)
