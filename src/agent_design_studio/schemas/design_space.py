"""Design space schemas."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class DesignAxis(BaseModel):
    """A controllable axis inside the agent design space."""

    key: str = Field(..., description="Stable axis identifier.")
    label: str = Field(..., description="Human-readable axis name.")
    description: str = Field(..., description="Explanation of what changes along the axis.")
    min_value: float = Field(default=0.0, description="Minimum supported axis value.")
    max_value: float = Field(default=1.0, description="Maximum supported axis value.")
    default_value: float = Field(default=0.5, description="Default axis value.")


class DesignConstraint(BaseModel):
    """A design-level constraint applied to the full agent architecture."""

    name: str = Field(..., description="Constraint identifier.")
    description: str = Field(..., description="Constraint explanation.")
    required: bool = Field(default=True, description="Whether the constraint is mandatory.")


class DesignOption(BaseModel):
    """One selectable option on an internal design axis."""

    name: str = Field(..., description="Stable option identifier.")
    label: str = Field(..., description="Human-readable option label.")
    description: str = Field(..., description="Short explanation of the option semantics.")
    tradeoff_effects: Dict[str, float] = Field(
        default_factory=dict,
        description="Optional lightweight tradeoff metadata for this option.",
    )
    tags: List[str] = Field(default_factory=list, description="Optional tags used for internal grouping.")


class StrategyAxis(BaseModel):
    """An internal non-slider design axis with explicit selectable options."""

    key: str = Field(..., description="Stable axis identifier.")
    label: str = Field(..., description="Human-readable axis name.")
    description: str = Field(..., description="Explanation of what changes along the axis.")
    options: List[DesignOption] = Field(default_factory=list, description="Selectable options for the axis.")


class DesignSpace(BaseModel):
    """The bounded set of options, constraints, and archetypes available for design."""

    axes: List[DesignAxis] = Field(default_factory=list, description="Supported design axes.")
    strategy_axes: List[StrategyAxis] = Field(
        default_factory=list,
        description="Internal deterministic strategy axes used to construct candidate designs.",
    )
    archetypes: List[str] = Field(default_factory=list, description="Available high-level architecture archetypes.")
    available_tools: List[str] = Field(default_factory=list, description="Tools available to future designs.")
    constraints: List[DesignConstraint] = Field(default_factory=list, description="Global design constraints.")
    notes: Optional[str] = Field(default=None, description="Extra explanation about the current design space.")
