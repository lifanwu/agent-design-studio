"""Tradeoff preference schemas."""

from pydantic import BaseModel, Field, field_validator


class TradeoffSpec(BaseModel):
    """Persistent user-controlled tradeoff preferences shared by chat and sliders."""

    latency: float = Field(..., ge=0.0, le=1.0, description="Preference for lower latency.")
    robustness: float = Field(..., ge=0.0, le=1.0, description="Preference for resilient behavior.")
    simplicity: float = Field(..., ge=0.0, le=1.0, description="Preference for simple architectures.")
    cost: float = Field(..., ge=0.0, le=1.0, description="Preference for lower operating cost.")
    explainability: float = Field(..., ge=0.0, le=1.0, description="Preference for explainable behavior.")

    @field_validator("latency", "robustness", "simplicity", "cost", "explainability")
    @classmethod
    def round_values(cls, value: float) -> float:
        """Normalize values to readable precision for storage and display."""

        return round(value, 3)

