# Agent Design Studio

Agent Design Studio is a chat-first, visual, interactive system for co-designing agent architectures.

This repository is the initial foundation only. It defines the product shape, core schemas, documentation, repo rules, placeholder UI, and basic tests. It does not yet implement candidate execution, evidence-based selection, compilation, audit, or patch application logic.

## Why This Exists

Most agent-building tools jump directly from a prompt to generated code. That skips the design work:

- clarifying the design space,
- expressing tradeoffs explicitly,
- iterating with shared context,
- visualizing how an agent is structured,
- preserving a durable source of truth for future generation and patching.

Agent Design Studio treats agent design itself as a first-class workflow.

## Core Ideas

- Chat is the primary interaction mode.
- Sliders are persistent and share one tradeoff state with chat.
- Visualization is mandatory, not optional decoration.
- Design states may be partial and still valid for iteration.
- Each generated task agent will eventually have a structured `DesignDoc` as its source of truth.
- Future selection should be evidence-based rather than preference-only.
- Future changes should support local patching instead of full regeneration.

## High-Level Workflow

1. The user describes a task and goals through chat.
2. Persistent sliders express tradeoff preferences like latency, robustness, simplicity, cost, and explainability.
3. Chat and sliders update a shared design state.
4. The system visualizes the current workflow, tradeoff position, and active-design diff.
5. The system can generate deterministic candidate designs, compare them, let the user select one, and adopt it into the active design.
6. Future versions will evaluate candidates with evidence, compile artifacts, and support local patching.

## Repository Structure

```text
agent-design-studio/
├── AGENTS.md
├── README.md
├── LICENSE
├── configs/
├── docs/
├── examples/
├── src/agent_design_studio/
│   ├── compilers/
│   ├── engines/
│   ├── evaluation/
│   ├── runtime/
│   ├── schemas/
│   ├── templates/
│   └── ui/
└── tests/
```

## Run The Placeholder App

Create a virtual environment, install dependencies, and start Streamlit:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/agent_design_studio/ui/app.py
```

## Current MVP Status

Current status:

- product definition is documented,
- architecture flows are documented,
- schema layer is scaffolded with Pydantic models,
- shared-state UI is available,
- deterministic candidate generation is available,
- candidate diff / comparison / selection / adoption is available,
- active-design evolution diff is available,
- tests cover current design-system behavior.

Not implemented yet:

- candidate execution,
- evidence-based evaluation and selection,
- compilation into runnable agents,
- local patch application,
- audit and repair loops.

Those capabilities are intentionally left as TODO scaffolding for later steps.
