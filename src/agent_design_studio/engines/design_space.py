"""Internal deterministic DesignSpace helpers.

This layer is intentionally internal-only. It formalizes the available
strategy axes and options used by candidate generation without changing the
current user-visible workflow.
"""

from __future__ import annotations

from agent_design_studio.schemas.design_space import DesignOption, DesignSpace, StrategyAxis


def build_internal_design_space() -> DesignSpace:
    """Return the current internal strategy space for deterministic generation."""

    return DesignSpace(
        strategy_axes=[
            StrategyAxis(
                key="validation",
                label="Validation",
                description="How much explicit checking is applied across the workflow.",
                options=[
                    DesignOption(name="light", label="Light", description="Minimal validation focused on final outputs.", tradeoff_effects={"latency": 0.15, "robustness": -0.1}, tags=["fast"]),
                    DesignOption(name="moderate", label="Moderate", description="Balanced validation with visible review checkpoints.", tradeoff_effects={"robustness": 0.05}, tags=["balanced"]),
                    DesignOption(name="deep", label="Deep", description="Validation after each major phase with stronger safeguards.", tradeoff_effects={"robustness": 0.2, "latency": -0.1}, tags=["robust"]),
                    DesignOption(name="targeted", label="Targeted", description="Validation on the most critical steps only.", tradeoff_effects={"simplicity": 0.1}, tags=["simple"]),
                ],
            ),
            StrategyAxis(
                key="control",
                label="Control",
                description="How the system moves between steps and checkpoints.",
                options=[
                    DesignOption(name="short_loop", label="Short Loop", description="Short control loop with minimal intermediate checks.", tradeoff_effects={"latency": 0.15}, tags=["fast"]),
                    DesignOption(name="guided_review", label="Guided Review", description="Moderate control depth with explicit review points.", tradeoff_effects={"explainability": 0.05}, tags=["balanced"]),
                    DesignOption(name="conservative", label="Conservative", description="Conservative control flow with more checkpoints.", tradeoff_effects={"robustness": 0.15}, tags=["robust"]),
                    DesignOption(name="explicit_steps", label="Explicit Steps", description="Straightforward explicit sequence with reduced orchestration.", tradeoff_effects={"simplicity": 0.15}, tags=["simple"]),
                ],
            ),
            StrategyAxis(
                key="memory",
                label="Memory",
                description="How much state or carryover context the design assumes.",
                options=[
                    DesignOption(name="minimal", label="Minimal", description="Avoid persistent memory unless the task clearly requires it.", tradeoff_effects={"cost": 0.1, "simplicity": 0.05}, tags=["fast", "simple"]),
                    DesignOption(name="selective", label="Selective", description="Allow limited memory only where continuity clearly helps.", tradeoff_effects={"robustness": 0.05}, tags=["balanced", "robust"]),
                ],
            ),
            StrategyAxis(
                key="workflow",
                label="Workflow",
                description="How many stages and branches the design prefers.",
                options=[
                    DesignOption(name="lean", label="Lean", description="Lean workflow with very few steps and low overhead.", tradeoff_effects={"latency": 0.15}, tags=["fast"]),
                    DesignOption(name="moderate", label="Moderate", description="Moderate workflow depth with readable structure.", tradeoff_effects={"explainability": 0.05}, tags=["balanced"]),
                    DesignOption(name="layered", label="Layered", description="Layered workflow with stronger guardrails and checkpoints.", tradeoff_effects={"robustness": 0.15}, tags=["robust"]),
                    DesignOption(name="shallow", label="Shallow", description="Shallow architecture with fewer moving parts.", tradeoff_effects={"simplicity": 0.15}, tags=["simple"]),
                ],
            ),
        ],
        notes="Internal deterministic strategy space for candidate construction.",
    )


def resolve_strategy_option(design_space: DesignSpace, axis_key: str, option_name: str) -> DesignOption:
    """Resolve one profile-selected option from the internal DesignSpace."""

    for axis in design_space.strategy_axes:
        if axis.key != axis_key:
            continue
        for option in axis.options:
            if option.name == option_name:
                return option
        raise ValueError(f"Unknown option '{option_name}' for design axis '{axis_key}'.")
    raise ValueError(f"Unknown design axis '{axis_key}'.")
