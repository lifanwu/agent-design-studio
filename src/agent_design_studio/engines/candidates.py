"""Config-driven heuristic candidate generation for the current co-design shell."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from agent_design_studio.engines.candidate_transforms import (
    append_candidate_preview_section,
    apply_profile_to_design_state,
    compute_candidate_diff,
    candidate_strategy_differences,
    candidate_summary_from_profile,
    load_candidate_profiles,
)
from agent_design_studio.schemas.candidate import CandidateCollection, CandidateDesign
from agent_design_studio.schemas.design_state import DesignState
from agent_design_studio.schemas.tradeoff_spec import TradeoffSpec
from agent_design_studio.schemas.user_profile import InvolvementMode
from agent_design_studio.ui.state import build_design_doc_preview, summarize_design_state


class CandidateGenerator(ABC):
    """Interface for producing candidate designs from the current shared state."""

    @abstractmethod
    def generate_candidates(
        self,
        task_text: str,
        tradeoffs: TradeoffSpec,
        design_hints: List[str],
        involvement_mode: InvolvementMode,
        current_design_state: DesignState,
    ) -> CandidateCollection:
        """Generate a candidate collection from the current shared state."""


class HeuristicCandidateGenerator(CandidateGenerator):
    """Small config-driven generator for a few strategy-differentiated candidates."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self.config_path = config_path

    def generate_candidates(
        self,
        task_text: str,
        tradeoffs: TradeoffSpec,
        design_hints: List[str],
        involvement_mode: InvolvementMode,
        current_design_state: DesignState,
    ) -> CandidateCollection:
        """Generate explicit candidate variants from YAML profiles."""

        profiles = load_candidate_profiles(self.config_path)
        base_summary = summarize_design_state(current_design_state)
        candidates = [
            self._build_candidate(
                task_text=task_text,
                base_tradeoffs=tradeoffs,
                base_design_hints=design_hints,
                involvement_mode=involvement_mode,
                current_design_state=current_design_state,
                profile=profile,
            )
            for profile in profiles
        ]
        return CandidateCollection(
            base_session_id=current_design_state.session_id,
            base_design_summary=base_summary,
            candidates=candidates,
        )

    def _build_candidate(
        self,
        task_text: str,
        base_tradeoffs: TradeoffSpec,
        base_design_hints: List[str],
        involvement_mode: InvolvementMode,
        current_design_state: DesignState,
        profile,
    ) -> CandidateDesign:
        """Build one candidate variant from a declarative profile."""

        candidate_state = apply_profile_to_design_state(
            base_design_state=current_design_state,
            task_text=task_text,
            base_tradeoffs=base_tradeoffs,
            base_design_hints=base_design_hints,
            involvement_mode=involvement_mode,
            profile=profile,
        )
        candidate_preview = build_design_doc_preview(candidate_state)
        candidate_preview = append_candidate_preview_section(candidate_preview, profile)
        return CandidateDesign(
            id=profile.id,
            label=profile.label,
            short_description=profile.short_description,
            strategy_differences=candidate_strategy_differences(profile),
            diff=compute_candidate_diff(current_design_state, candidate_state),
            candidate_design_state=candidate_state,
            candidate_design_summary=candidate_summary_from_profile(candidate_state, profile),
            candidate_design_doc_preview=candidate_preview,
        )
