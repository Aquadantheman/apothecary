# Architecture

## System Overview

Apothecary is a layered system: structured data at the bottom, inference engines in the middle, and user-facing reports at the top.

```
┌─────────────────────────────────────────────────┐
│                  USER INTERFACE                  │
│         (CLI → Web → Mobile, phased)             │
├─────────────────────────────────────────────────┤
│                  REPORT LAYER                    │
│   Interaction Report │ Timeline │ Prescriber PDF │
├─────────────────────────────────────────────────┤
│                 ENGINE LAYER                     │
│  Interaction  │  Timing   │ Depletion │ Reasoning│
│   Engine      │  Engine   │  Engine   │  Engine  │
├─────────────────────────────────────────────────┤
│                  DATA LAYER                      │
│   Substance DB  │  User Stacks  │  Evidence DB   │
└─────────────────────────────────────────────────┘
```

---

## Data Layer

### Substance Database
Curated YAML files (phase 1) → SQLite/PostgreSQL (phase 2+).

Each substance is a structured document following the schema defined in DATA_MODEL.md. YAML is used initially because it's human-readable, version-controllable, and easy to review and edit during the curation phase. Migration to SQL happens when query complexity or dataset size demands it.

### User Stack
A user's complete list of substances with their specific details:
- Substance ID (reference to database)
- Dose
- Frequency (daily, as-needed, cyclical)
- Formulation (IR, XR, specific brand if relevant)
- Current timing (when they currently take it)
- Start date (for tracking adaptation/tolerance)

### Evidence Database
Citations and source metadata for every claim in the substance database. Each evidence entry includes PubMed ID or URL, study type (RCT, observational, case report, animal, in-vitro), sample size (if applicable), and a brief summary of the finding.

---

## Engine Layer

### Interaction Engine
The core analysis system. Takes a user's full stack and runs every substance against every other substance across all interaction dimensions:

```
Input: User Stack (list of substances with doses)
Process:
  1. Load full profiles for all substances
  2. For each pair (A, B):
     a. Check CYP450 overlap (substrate/inhibitor/inducer conflicts)
     b. Check receptor stacking (serotonergic, dopaminergic, GABAergic load)
     c. Check absorption interference
     d. Check physiological antagonism
     e. Check additive side effects
  3. For the full stack:
     a. Compute aggregate serotonin load
     b. Compute aggregate cardiovascular load
     c. Identify unaddressed depletions
  4. Rank all findings by severity and confidence
Output: InteractionReport (list of findings with mechanisms and evidence)
```

Multi-way interactions (3+ substances contributing to a single risk) are checked at step 3. Example: Lexapro (serotonin_load: 0.7) + L-theanine (0.1) + ashwagandha (0.2) = combined load of 1.0, which triggers a serotonin stacking warning even though no pairwise combination exceeds the threshold.

### Timing Engine
Takes the interaction report and each substance's pharmacokinetic profile to generate an optimal daily schedule.

```
Input: User Stack + InteractionReport + PK profiles
Process:
  1. Identify fixed anchors (medications with strict timing requirements)
  2. Identify spacing requirements (substances that must be separated)
  3. Identify synergistic pairings (substances that benefit from co-administration)
  4. Map absorption windows (food requirements, pH sensitivity)
  5. Optimize placement across time blocks:
     - Wake/Morning (0-1hr after waking)
     - Mid-Morning (2-4hr after waking)
     - Midday (5-7hr after waking)
     - Afternoon (8-10hr after waking)
     - Evening/Dinner (11-13hr after waking)
     - Pre-Bed (30-60min before sleep)
  6. Generate rationale for each placement
Output: DailyTimeline (ordered list of timed doses with explanations)
```

### Depletion Engine
Cross-references medication-induced depletions against the user's supplement stack.

```
Input: User Stack (medications + supplements)
Process:
  1. Collect all depletions from medications
  2. Collect all nutrients provided by supplements
  3. Compare: which depletions are addressed, which are gaps
  4. For gaps, suggest specific nutrients with dosing ranges from literature
Output: DepletionReport (addressed depletions, gaps, suggestions)
```

### Reasoning Engine
Generates plain-language mechanism explanations for interactions and timing decisions. Phase 1 uses template-based generation from structured data. Phase 2+ may incorporate LLM reasoning grounded in the substance database for novel or complex explanations.

```
Input: Interaction finding (substances, type, mechanism tags)
Process:
  1. Retrieve mechanism descriptions from substance profiles
  2. Compose explanation from templates:
     "[Substance A] [action] [enzyme/receptor/nutrient],
      which [effect] on [Substance B] because [Substance B]
      [depends on / is processed by / targets] the same [pathway]."
  3. Append evidence summary and confidence rating
Output: MechanismExplanation (plain-language string with citations)
```

---

## Report Layer

### Interaction Report
The primary output. Contains all findings organized by severity, each with mechanism explanation, evidence basis, confidence rating, and actionable context (timing adjustment, dose consideration, or professional consultation recommendation).

### Daily Timeline
Visual schedule showing when to take each substance, grouped into waves, with brief rationale for each placement. Designed to be glanceable — the user should be able to follow it without reading the full interaction report.

### Prescriber Export
A clean, professional one-page PDF summary designed to be handed to a doctor or pharmacist. Contains: complete substance list with doses, flagged interactions with severity, identified depletions, and the user's current timing schedule. No jargon, no supplement marketing language — clinical framing only.

---

## API Layer (Phase 2+)

FastAPI endpoints for web and mobile clients:

```
POST /stack                    # Create/update user stack
GET  /stack/{user_id}          # Retrieve user stack
POST /analyze                  # Run full analysis on a stack
GET  /analyze/{user_id}        # Retrieve cached analysis
GET  /substance/{id}           # Substance profile lookup
GET  /substance/search?q=      # Substance search/autocomplete
POST /timeline                 # Generate optimized daily timeline
POST /export/prescriber        # Generate prescriber PDF
```

---

## Data Flow: User Journey

```
User inputs substances
        │
        ▼
  Stack validated against Substance DB
        │
        ▼
  Interaction Engine runs full analysis
        │
        ├──► Interaction Report (what interacts and why)
        │
        ▼
  Depletion Engine identifies gaps
        │
        ├──► Depletion Report (what's missing)
        │
        ▼
  Timing Engine optimizes schedule
        │
        ├──► Daily Timeline (when to take what)
        │
        ▼
  Reasoning Engine generates explanations
        │
        ├──► Mechanism explanations attached to all findings
        │
        ▼
  Reports rendered for user
  Prescriber export available
```

---

## Technical Decisions

### Why YAML for seed data?
- Human-readable and editable without tooling
- Git-diffable for review and collaboration
- Supports comments for annotation during curation
- Easy to validate with JSON Schema
- Migrates cleanly to SQL when needed

### Why FastAPI?
- Async support for concurrent analysis requests
- Auto-generated OpenAPI docs
- Pydantic models enforce data validation
- Python ecosystem for scientific/pharmacological libraries

### Why SQLite first?
- Zero infrastructure for local development
- Single-file database, easy to distribute
- Sufficient for single-user CLI and small-scale web
- Clean migration path to PostgreSQL via SQLAlchemy

### Why not start with an LLM reasoning layer?
- Accuracy requirements are too high for ungrounded LLM output
- Structured inference from tagged data is deterministic and auditable
- LLM hallucination in medical context is unacceptable
- Template-based explanations from verified data are safer for v1
- LLM layer can be added in v2 for novel combinations where structured data is insufficient, with clear "AI-generated, lower confidence" labeling
