"""Visualization-related schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field


class VisualizationPanel(BaseModel):
    """Metadata describing a required UI visualization surface."""

    panel_id: str = Field(..., description="Stable panel identifier.")
    title: str = Field(..., description="Human-readable panel title.")
    panel_type: str = Field(..., description="Visualization category.")
    status: str = Field(default="placeholder", description="Implementation status.")


class TradeoffPoint(BaseModel):
    """A named point in tradeoff space for charting or comparison."""

    label: str = Field(..., description="Point label.")
    latency: float = Field(..., ge=0.0, le=1.0, description="Latency axis position.")
    robustness: float = Field(..., ge=0.0, le=1.0, description="Robustness axis position.")
    simplicity: float = Field(..., ge=0.0, le=1.0, description="Simplicity axis position.")
    cost: float = Field(..., ge=0.0, le=1.0, description="Cost axis position.")
    explainability: float = Field(..., ge=0.0, le=1.0, description="Explainability axis position.")


class DesignDiffEntry(BaseModel):
    """A placeholder summary of a detected design change."""

    field_name: str = Field(..., description="Changed field or section.")
    change_summary: str = Field(..., description="Human-readable description of the change.")
    impact_level: Optional[str] = Field(default=None, description="Expected impact classification.")


class VisualizationBundle(BaseModel):
    """Collection of visualization-ready data derived from the current design state."""

    panels: List[VisualizationPanel] = Field(default_factory=list, description="Available UI panels.")
    tradeoff_points: List[TradeoffPoint] = Field(default_factory=list, description="Chartable tradeoff positions.")
    diff_entries: List[DesignDiffEntry] = Field(default_factory=list, description="Structured design diff entries.")

