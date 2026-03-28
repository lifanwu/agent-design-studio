# Architecture

This document sketches the intended structure of Agent Design Studio. The diagrams below include both current foundation concepts and clearly marked future flows.

## End-to-End Workflow

```mermaid
flowchart TD
    A[User Task + Context] --> B[Chat-First Co-Design Session]
    B --> C[Shared Design State]
    D[Persistent Sliders] --> C
    C --> E[Workflow Graph View]
    C --> F[Tradeoff Chart View]
    C --> G[Design Diff View]
    C --> H[Active DesignDoc / Design IR View]
    H --> I[Deterministic Candidate Generation]
    I --> J[Candidate Diff + Comparison]
    J --> K[User Selection + Adoption]
    K --> L[Active Design Evolution Diff]
    L --> M[Future Evaluation]
    M --> N[Future Compilation]
    N --> O[Future Generated Artifacts]
    O --> P[Future Local Patch Loop]
```

## Chat + Slider Interaction

```mermaid
flowchart LR
    A[User Chat Message] --> B[Interpret Intent]
    C[Slider Update] --> D[Update Shared Tradeoff State]
    B --> D
    D --> E[Update Design State]
    E --> F[Refresh Visualization Panels]
    E --> G[Draft Design Doc]
    D --> H[Explain Impact In Chat]
```

## Partial Design State To Compile (Future Flow)

```mermaid
flowchart TD
    A[Partial Design State] --> B{Enough Detail To Compile?}
    B -- No --> C[Show Missing Sections]
    C --> D[Allow One-Click Generate From Current State]
    B -- Yes --> E[Create Structured Design Doc]
    D --> E
    E --> F[Future Compiler Pipeline]
    F --> G[Future Runnable Task Agent]
```

## Candidate Evaluation / Selection (Future Flow)

```mermaid
flowchart TD
    A[Design State] --> B[Future Candidate Generator]
    B --> C[Candidate A]
    B --> D[Candidate B]
    B --> E[Candidate N]
    C --> F[Future Task Runs]
    D --> F
    E --> F
    F --> G[Evidence Bundle]
    G --> H[Selection Summary]
    H --> I[Choose Best Supported Candidate]
```

## Candidate Inspection + Adoption

```mermaid
flowchart TD
    A[Current Shared Design State] --> B[Generate Candidates]
    B --> C[Candidate Diff]
    B --> D[Candidate Comparison]
    C --> E[User Selects Candidate]
    D --> E
    E --> F[Explicit Adopt Action]
    F --> G[New Active DesignDoc]
    G --> H[Active Design Evolution Diff]
```

## Patch / Local Replacement (Future Flow)

```mermaid
flowchart TD
    A[Existing Design Doc] --> B[Requested Change]
    B --> C[Locate Affected Sections]
    C --> D[Future Patch Planner]
    D --> E[Local Replacement Plan]
    E --> F[Update Design Doc]
    F --> G[Future Regenerate Only Affected Artifacts]
```
