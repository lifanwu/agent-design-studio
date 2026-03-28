"""Lightweight chat intent parsing for shared UI state updates."""

from __future__ import annotations

from typing import Dict, List, Literal

from pydantic import BaseModel, Field


IntentKind = Literal["tradeoff_update", "design_hint_update", "mixed_update", "no_op"]


class ChatIntentResult(BaseModel):
    """Structured output from simple keyword-based chat intent parsing."""

    raw_message: str = Field(..., description="Original user chat adjustment.")
    normalized_message: str = Field(..., description="Lowercased normalized message text.")
    intent_kind: IntentKind = Field(..., description="High-level category for the parsed message.")
    tradeoff_updates: Dict[str, float] = Field(default_factory=dict, description="Requested tradeoff deltas by axis.")
    design_hints: List[str] = Field(default_factory=list, description="Lightweight design hints derived from the message.")
    explanation: str = Field(..., description="Readable explanation of the parser outcome.")


TRADEOFF_PATTERNS = [
    (("make it cheaper", "cheaper", "reduce cost", "lower cost"), {"cost": -0.2}),
    (("keep it simple", "simpler", "avoid a complex workflow", "less complex"), {"simplicity": 0.2}),
    (("make it more robust", "more robust", "increase robustness"), {"robustness": 0.2}),
    (("prioritize speed", "more speed", "faster", "less latency"), {"latency": 0.2}),
    (("more explainable", "increase explainability", "make it explainable"), {"explainability": 0.2}),
]

DESIGN_HINT_PATTERNS = [
    (("use no memory", "no memory"), "Avoid memory-heavy workflow state where possible."),
    (("avoid a complex workflow",), "Keep the workflow shallow and easy to inspect."),
    (("keep it simple",), "Favor a small number of explicit workflow steps."),
]


def parse_chat_intent(message: str) -> ChatIntentResult:
    """Parse a small set of natural-language adjustment messages into structured updates."""

    normalized = " ".join(message.lower().split())
    tradeoff_updates: Dict[str, float] = {}
    design_hints: List[str] = []

    for phrases, updates in TRADEOFF_PATTERNS:
        if any(phrase in normalized for phrase in phrases):
            for axis, delta in updates.items():
                tradeoff_updates[axis] = tradeoff_updates.get(axis, 0.0) + delta

    for phrases, hint in DESIGN_HINT_PATTERNS:
        if any(phrase in normalized for phrase in phrases) and hint not in design_hints:
            design_hints.append(hint)

    if tradeoff_updates and design_hints:
        intent_kind: IntentKind = "mixed_update"
        explanation = "Parsed both tradeoff changes and lightweight design hints."
    elif tradeoff_updates:
        intent_kind = "tradeoff_update"
        explanation = "Parsed tradeoff changes from the chat adjustment."
    elif design_hints:
        intent_kind = "design_hint_update"
        explanation = "Parsed lightweight design hints from the chat adjustment."
    else:
        intent_kind = "no_op"
        explanation = "No supported design adjustment was detected in the chat message."

    return ChatIntentResult(
        raw_message=message,
        normalized_message=normalized,
        intent_kind=intent_kind,
        tradeoff_updates=tradeoff_updates,
        design_hints=design_hints,
        explanation=explanation,
    )
