# Agent Design Studio

Agent Design Studio is a chat-first, **user-steered design evolution system** for task-specific agents.

Instead of generating agents in a single step, the system enables users to iteratively construct, compare, and refine structured **DesignDocs**, which serve as the source of truth for agent behavior.

---

## 🧭 System Overview

The product is structured as a layered system that moves from **user intent → design → implementation → evaluation → improvement**.

```text
User (co-design)
    ↓
Intent & Preferences
    ↓
Design Evolution System
    ↓
DesignDoc (source of truth)
    ↓
Blueprint / Implementation Spec (future)
    ↓
Agent Implementation (future)
    ↓
Evaluation on Sample Tasks (future)
    ↓
Iterative Improvement Loop (future)
```

---

## 🧠 User Co-Design Model

The system is built around **user-steered co-design**, where users continuously shape the design.

### Inputs

* **Task** — what the agent should do
* **Chat** — goals, corrections, and preferences
* **Sliders** — explicit tradeoff controls (latency, robustness, cost, etc.)
* **Selection** — choosing a candidate design

### Key Idea

User preference is not static — it is continuously expressed through:

* sliders (explicit)
* chat (implicit)
* selection (revealed preference)

---

## 🔁 Core Design Evolution Loop

The system operates as an iterative loop:

```text
Intent → Candidates → Compare → Select → Adopt → Evolve → Repeat
```

Each iteration produces a new version of the **DesignDoc**.

---

## 🧱 Internal Architecture

### 1. Intent & Preference Layer

Maps user inputs into structured signals:

* direction (e.g. “more robust”, “faster”)
* constraints
* tradeoff preferences

(Currently implemented with deterministic rules.)

---

### 2. Design Evolution System (Core)

Responsible for:

* deterministic candidate generation
* candidate comparison (diff)
* explicit user selection
* adoption → new active design
* design evolution tracking (history + versions)

This is the core of the current system.

---

### 3. DesignSpace (Internal, upcoming)

An internal **option library** defining:

* design axes (validation, control, memory, workflow)
* available options per axis
* tradeoff semantics
* profile strategies (Fast / Balanced / Robust / Simple)

Used to generate candidates deterministically.

---

### 4. Design IR (Internal, upcoming)

A structured representation of design:

* tradeoffs
* validation / control / memory / workflow
* hints

Used for:

* diff
* history
* comparison
* future compilation

---

### 5. DesignDoc (User-Facing)

The primary artifact in the system.

* structured
* versioned
* evolves over time
* fully reflects the current design

All operations ultimately produce or modify a DesignDoc.

---

## 📍 Current Status

The system already supports a full **deterministic design evolution loop**:

* chat + sliders + task input
* shared design state
* deterministic candidate generation
* candidate comparison (diff)
* candidate selection
* explicit adoption
* active design evolution (diff + history)

This forms a complete **idea → DesignDoc** pipeline.

---

## 🚀 Future Direction

The next stages extend beyond design into implementation:

### Design → Implementation

* Blueprint / implementation spec
* agent generation / compilation

### Implementation → Evaluation

* execution on sample tasks
* performance comparison

### Evaluation → Improvement

* version selection
* local patching
* iterative refinement

---

## 🎯 Key Principles

* **User-steered** — no hidden optimization or auto-selection
* **Deterministic** — no LLM dependency in core loop (for current stage)
* **Explicit** — all changes are visible and diffable
* **Evolution-first** — design is a trajectory, not a one-shot result
* **DesignDoc-centric** — the design is the source of truth

---

## 🧠 What This Is (and Is Not)

### This is:

* a design evolution system
* a co-design environment
* a decision-support tool for agent architecture

### This is not:

* a prompt-to-code generator
* a black-box agent builder
* a one-shot automation tool

---

## 🔄 Summary

Agent Design Studio turns agent creation into a structured, iterative process:

```text
User Idea → Design Evolution → DesignDoc → (future) Agent → Evaluation → Improvement
```

The current focus is making **design itself**:

* structured
* comparable
* controllable
* evolvable
