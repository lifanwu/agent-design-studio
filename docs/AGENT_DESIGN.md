# Agent Design Studio

## What The Product Does

Agent Design Studio is a chat-first, visual, interactive **user-steered design evolution system** for task-specific agents.

It enables users to move from an idea or task brief toward a structured, evolving **DesignDoc**, which serves as the central source of truth for the agent design. Rather than generating agents in a single step, the system supports iterative refinement through deterministic candidate generation, explicit user-driven adoption, and transparent design evolution.

Users actively steer the evolution of the DesignDoc through a combination of chat (intent), persistent tradeoff controls (preferences), and explicit selection and adoption of candidate designs. The system does not rely on hidden optimization or automated decision-making.

The product centers design as an explicit, inspectable process. Users can describe goals conversationally, adjust durable tradeoff controls, inspect the evolving architecture visually, and continuously refine the design even when it is incomplete.

Downstream capabilities such as evaluation, compilation, documentation, and patching are treated as future extensions derived from the DesignDoc, rather than the primary focus of the system.

## What The Product Is Not

* It is not a one-shot prompt-to-code generator.
* It is not only a setup wizard with temporary controls.
* It is not a preference-only chooser without future evidence.
* It is not a system that requires complete specifications before any useful output appears.
* It is not a black-box agent generator with hidden decision logic.

## Key Abstractions

### Design Space

The `DesignSpace` defines the available axes, constraints, archetypes, tools, and structural options that can be used when designing an agent. It is the bounded space within which the system can reason about alternatives.

### Design State

The `DesignState` is the current working state of the design session. It may be partial. It combines task information, tradeoff preferences, user involvement mode, workflow intent, visualization state, and the current design document draft.

### Design Doc

The `DesignDoc` is a structured, first-class artifact describing the resulting task agent. It is the **evolving source of truth** for the system.

All generation, comparison, and adoption operations operate on or produce DesignDocs. The system does not mutate hidden internal state without reflecting it in the DesignDoc.

In future stages, the DesignDoc can serve as the basis for downstream artifacts such as generated agents, documentation, and patch plans.

### Design IR

The system maintains a structured internal representation referred to as the `Design IR`. This IR provides a stable, schema-aligned view of the design that supports diffing, comparison, and evolution across iterations.

In the current MVP, the `Design IR` is intentionally aligned with the active `DesignDoc` and surrounding structured design state. This allows the system to evolve without requiring a large refactor.

Over time, the IR will become the foundation for downstream capabilities such as compilation and artifact generation.

## Major Components

* Chat interface for conversational co-design
* Persistent slider controls for tradeoff management
* Shared tradeoff state linking chat and controls
* Visualization surfaces for workflow, tradeoffs, and diffs
* Schema layer for structured design artifacts (DesignDoc / IR)
* Deterministic candidate generation layer
* Candidate diff, comparison, selection, and adoption flow
* **Design evolution tracking (diff + history) for active designs**
* Future evaluation engine (evidence-based, not ranking-first)
* Future compiler layer for runnable artifacts (derived from DesignDoc)
* Future patch planning and local replacement workflow

## Interaction Model

### Chat-First

Chat is the primary interaction mode. Users should be able to express tasks, corrections, preferences, and questions in natural language without being forced through a rigid form-first flow.

### Persistent Sliders

Tradeoff sliders are always present. They are not a one-time onboarding mechanism. They remain visible as a durable way to steer design direction throughout the session.

### Shared Tradeoff State

Chat and sliders write to the same underlying tradeoff state. If a user changes a slider, the system should update the design state and explain the effect in chat. If chat changes the tradeoff intent, the sliders should reflect that shared state.

### Visualization

Visualization is required. The system must surface:

* workflow graph
* tradeoff chart
* design diff
* design evolution (trajectory over time)

These views are core to understanding design evolution, not optional extras.

## High-Level Workflow

1. A user describes a task, context, and goals.
2. The system captures a partial design state.
3. The user adjusts persistent tradeoff sliders and involvement mode.
4. Chat and controls update the shared design state.
5. Visualizations reflect the current architecture, tradeoff position, and active design evolution.
6. The system generates multiple deterministic candidate DesignDocs from the current shared state.
7. The user inspects candidate diffs, compares candidates side by side, selects one, and explicitly adopts it into the active DesignDoc.
8. The system records design evolution (diff + history) to make each change interpretable.
9. Future versions will evaluate candidates with evidence, compile artifacts, and support local patching.

## Generated Artifacts

Future versions of the system are expected to generate:

* design documents (DesignDocs)
* agent blueprints or runnable task-agent artifacts
* user manuals
* agent rules markdown
* workflow configuration files
* patch plans and local replacement instructions

These artifacts are derived from the DesignDoc rather than independently generated.

## MVP Scope

This repository foundation covers:

* product definition
* architecture documentation
* repository structure
* core schemas
* long-term instruction files
* stateful co-design UI
* deterministic candidate generation
* candidate diff / comparison / selection / adoption
* active-design evolution diff
* design evolution history (trajectory)
* tests for current design-system behavior

This phase intentionally excludes evaluation, execution, ranking, compilation, and patch execution logic.