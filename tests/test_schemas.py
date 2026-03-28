"""Basic schema construction and validation tests."""

import pytest
from pydantic import ValidationError

from agent_design_studio.schemas import (
    DesignDoc,
    DesignSection,
    DesignState,
    InvolvementMode,
    TaskConstraint,
    TaskSpec,
    TradeoffSpec,
    UserProfile,
    VisualizationBundle,
    VisualizationPanel,
    WorkflowEdge,
    WorkflowGraph,
    WorkflowNode,
)


def test_design_state_allows_partial_construction() -> None:
    state = DesignState(session_id="session-001")

    assert state.session_id == "session-001"
    assert state.task_spec is None
    assert state.design_doc is None


def test_schema_construction_with_nested_models() -> None:
    tradeoffs = TradeoffSpec(
        latency=0.4,
        robustness=0.8,
        simplicity=0.7,
        cost=0.5,
        explainability=0.9,
    )
    task = TaskSpec(
        title="PDF Summarizer",
        summary="Summarize uploaded PDFs.",
        primary_goal="Produce reliable summaries.",
        constraints=[TaskConstraint(name="privacy", description="Do not upload files externally.")],
        inputs=["pdf"],
        outputs=["summary"],
    )
    doc = DesignDoc(
        title="PDF Summarizer Design",
        summary="Draft design for a PDF summarization agent.",
        sections=[DesignSection(title="Workflow", content="Ingest, parse, summarize.")],
    )
    graph = WorkflowGraph(
        nodes=[
            WorkflowNode(node_id="ingest", label="Ingest"),
            WorkflowNode(node_id="summarize", label="Summarize"),
        ],
        edges=[WorkflowEdge(source="ingest", target="summarize")],
    )
    visualization = VisualizationBundle(
        panels=[
            VisualizationPanel(panel_id="workflow", title="Workflow Graph", panel_type="graph"),
            VisualizationPanel(panel_id="tradeoffs", title="Tradeoff Chart", panel_type="chart"),
        ]
    )

    state = DesignState(
        session_id="session-002",
        task_spec=task,
        tradeoffs=tradeoffs,
        user_profile=UserProfile(involvement_mode=InvolvementMode.review),
        workflow_graph=graph,
        design_doc=doc,
        visualization=visualization,
    )

    assert state.tradeoffs is not None
    assert state.tradeoffs.robustness == 0.8
    assert state.user_profile is not None
    assert state.user_profile.involvement_mode is InvolvementMode.review


def test_tradeoff_validation_rejects_out_of_range_values() -> None:
    with pytest.raises(ValidationError):
        TradeoffSpec(
            latency=1.5,
            robustness=0.8,
            simplicity=0.7,
            cost=0.5,
            explainability=0.9,
        )


def test_user_profile_accepts_expected_modes() -> None:
    for mode in ("exploratory", "review", "one_click"):
        profile = UserProfile(involvement_mode=mode)
        assert profile.involvement_mode.value == mode

