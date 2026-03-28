"""Declarative transforms for config-driven candidate generation."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import yaml
from pydantic import BaseModel, Field

from agent_design_studio.engines.design_diff import compute_design_state_diff
from agent_design_studio.engines.design_space import build_internal_design_space, resolve_strategy_option
from agent_design_studio.schemas.design_doc import DesignSection
from agent_design_studio.schemas.design_space import DesignOption, DesignSpace
from agent_design_studio.schemas.design_state import DesignState
from agent_design_studio.schemas.tradeoff_spec import TradeoffSpec
from agent_design_studio.schemas.user_profile import InvolvementMode
from agent_design_studio.ui.state import build_current_design_state, summarize_design_state


class CandidateStrategy(BaseModel):
    """Structured strategy metadata for a candidate profile."""

    validation_depth: str = Field(..., description="How much validation the candidate applies.")
    control_style: str = Field(..., description="The control loop style for the candidate.")
    memory_usage: str = Field(..., description="Expected memory usage pattern.")
    workflow_complexity: str = Field(..., description="Expected workflow complexity.")


class CandidateProfile(BaseModel):
    """Declarative config profile for one candidate."""

    id: str = Field(..., description="Stable candidate profile id.")
    label: str = Field(..., description="Human-readable candidate label.")
    short_description: str = Field(..., description="Compact description of the candidate.")
    tradeoff_overrides: Dict[str, float] = Field(default_factory=dict, description="Tradeoff overrides for this profile.")
    design_hints: List[str] = Field(default_factory=list, description="Candidate-specific design hints.")
    strategy: CandidateStrategy = Field(..., description="Structured strategy metadata.")


def default_candidate_profile_path() -> Path:
    """Return the default YAML path for candidate profiles."""

    return Path(__file__).resolve().parents[3] / "configs" / "candidate_profiles.yaml"


def load_candidate_profiles(config_path: Path | None = None) -> List[CandidateProfile]:
    """Load declarative candidate profiles from YAML."""

    resolved_path = config_path or default_candidate_profile_path()
    with resolved_path.open("r", encoding="utf-8") as handle:
        raw_data = yaml.safe_load(handle) or {}
    return [CandidateProfile.model_validate(profile) for profile in raw_data.get("profiles", [])]


def apply_profile_tradeoffs(base_tradeoffs: TradeoffSpec, profile: CandidateProfile) -> TradeoffSpec:
    """Apply declarative tradeoff overrides to a tradeoff model."""

    merged = base_tradeoffs.model_dump()
    for key, value in profile.tradeoff_overrides.items():
        merged[key] = float(value)
    return TradeoffSpec(**merged)


def strategy_to_hints(strategy: CandidateStrategy) -> List[str]:
    """Convert structured strategy metadata into readable design hints."""

    return [
        f"Validation depth: {strategy.validation_depth}.",
        f"Control style: {strategy.control_style}.",
        f"Memory usage: {strategy.memory_usage}.",
        f"Workflow complexity: {strategy.workflow_complexity}.",
    ]


def resolve_profile_options(
    profile: CandidateProfile,
    design_space: DesignSpace | None = None,
) -> Dict[str, DesignOption]:
    """Resolve a profile's strategy selections against the internal DesignSpace."""

    resolved_design_space = design_space or build_internal_design_space()
    return {
        "validation": resolve_strategy_option(resolved_design_space, "validation", profile.strategy.validation_depth),
        "control": resolve_strategy_option(resolved_design_space, "control", profile.strategy.control_style),
        "memory": resolve_strategy_option(resolved_design_space, "memory", profile.strategy.memory_usage),
        "workflow": resolve_strategy_option(resolved_design_space, "workflow", profile.strategy.workflow_complexity),
    }


def options_to_design_strategy(options: Dict[str, DesignOption]) -> Dict[str, str]:
    """Convert resolved DesignSpace options back into the current strategy dict shape."""

    return {
        "validation_depth": options["validation"].name,
        "control_style": options["control"].name,
        "memory_usage": options["memory"].name,
        "workflow_complexity": options["workflow"].name,
    }


def apply_profile_to_design_state(
    base_design_state: DesignState,
    task_text: str,
    base_tradeoffs: TradeoffSpec,
    base_design_hints: List[str],
    involvement_mode: InvolvementMode,
    profile: CandidateProfile,
) -> DesignState:
    """Copy the base state, apply declarative transforms, and rebuild a candidate state."""

    copied_base_state = base_design_state.model_copy(deep=True)
    candidate_tradeoffs = apply_profile_tradeoffs(base_tradeoffs, profile)
    candidate_hints = list(base_design_hints)
    design_space = copied_base_state.design_space or build_internal_design_space()
    resolved_options = resolve_profile_options(profile, design_space)
    resolved_strategy = options_to_design_strategy(resolved_options)

    for hint in profile.design_hints + strategy_to_hints(profile.strategy):
        if hint not in candidate_hints:
            candidate_hints.append(hint)

    if copied_base_state.design_doc:
        for assumption in copied_base_state.design_doc.assumptions:
            if assumption not in candidate_hints:
                candidate_hints.append(assumption)

    return build_current_design_state(
        session_id=f"{copied_base_state.session_id}-{profile.id}",
        task_text=task_text,
        tradeoffs=candidate_tradeoffs,
        involvement_mode=involvement_mode,
        previous_state=copied_base_state,
        design_hints=candidate_hints,
        chat_history=copied_base_state.chat_history,
        design_strategy=resolved_strategy,
    )


def candidate_strategy_differences(profile: CandidateProfile) -> List[str]:
    """Return readable strategy differences for UI display."""

    differences = list(profile.design_hints)
    differences.extend(strategy_to_hints(profile.strategy))
    return differences


def append_candidate_preview_section(candidate_preview, profile: CandidateProfile):
    """Add candidate-specific strategy details to the preview document."""

    candidate_preview.sections.append(
        DesignSection(
            title="Candidate Strategy Differences",
            content="\n".join(f"- {item}" for item in candidate_strategy_differences(profile)),
        )
    )
    return candidate_preview


def candidate_summary_from_profile(candidate_state: DesignState, profile: CandidateProfile) -> str:
    """Build a readable candidate-level summary from the profile and recomputed state."""

    base_summary = summarize_design_state(candidate_state)
    return f"{profile.label} candidate: {profile.short_description} {base_summary}"


def compute_candidate_diff(base_state: DesignState, candidate_state: DesignState) -> dict:
    """Compute a small structured diff between the base design and a candidate."""

    return compute_design_state_diff(base_state, candidate_state)
