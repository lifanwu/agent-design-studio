"""User profile schemas."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class InvolvementMode(str, Enum):
    """How actively the user wants to participate in design iteration."""

    exploratory = "exploratory"
    review = "review"
    one_click = "one_click"


class UserProfile(BaseModel):
    """Preferences describing how the user wants to collaborate with the system."""

    involvement_mode: InvolvementMode = Field(
        default=InvolvementMode.exploratory,
        description="Desired interaction depth while designing the agent.",
    )
    domain_experience: Optional[str] = Field(
        default=None,
        description="Optional note about the user's familiarity with the task domain.",
    )
    notes: Optional[str] = Field(default=None, description="Additional user-specific preferences.")

