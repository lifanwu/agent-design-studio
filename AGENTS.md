# AGENTS.md

Repository rules for future Codex and human development work on `agent-design-studio`.

## Product Invariants

- Keep the product chat-first. New interaction flows should reinforce chat as the primary control surface.
- Persistent sliders are required. They must remain visible and durable rather than appearing only during setup.
- Chat and sliders must operate over one shared tradeoff state.
- Visualization is required. Workflow graph, tradeoff chart, and design diff are core product surfaces.
- The `DesignDoc` for each generated task agent is the source of truth.
- Candidate selection must eventually be evidence-based, not preference-only.
- Prefer patching and local replacement over full regeneration.

## Engineering Rules

- Keep the MVP simple, modular, and testable.
- Do not over-engineer future systems before they are needed.
- Use explicit schemas, typed data models, and readable code.
- Favor small files, clear names, and direct control flow over clever abstraction.
- Mark future logic as `TODO` or scaffold instead of pretending completeness.
- Preserve partial design states as valid first-class data.
- Treat docs, schemas, and generated artifacts as product surfaces, not secondary output.

## Current Non-Goals

- Do not implement candidate execution, selection, compilation, audit, or patching business logic in the foundation phase.
- Do not collapse the product into a simple prompt-to-code generator.
- Do not hide important tradeoffs in implicit defaults when a schema can express them directly.

