# Apothecary

**Your full stack, understood.**

Apothecary is an open-source platform that helps people understand how everything they take — prescriptions, supplements, and dietary factors — works together in their body. It checks interactions, explains mechanisms, optimizes timing, and identifies gaps, with full transparency about the evidence behind every insight.

---

## The Problem

Modern healthcare splits pharmacological knowledge across three professionals who don't talk to each other:

- **Your doctor** knows your diagnoses and prescriptions, but probably not your supplements.
- **Your pharmacist** knows drug interactions, but only checks when you ask, and has limited supplement data.
- **The supplement store** knows nothing about your medications.

Meanwhile, tools like Drugs.com only cover drug-drug interactions. NatMed has deep supplement data but is paywalled and clinician-only. Products like Stasis sell pre-packaged supplement bundles without transparency about dosing, evidence, or personalization.

**Nobody sees the full picture. Apothecary does.**

---

## What It Does

You input everything you take. Apothecary tells you:

1. **What interacts** — flagged by severity, with the biological mechanism explained in plain language
2. **What's missing** — nutrients your medications are depleting that you're not replenishing
3. **When to take each thing** — an optimized daily schedule based on pharmacokinetics and absorption
4. **Why** — every recommendation shows its evidence basis and confidence level

Apothecary is **informational, not prescriptive**. It provides medical literacy, not medical advice. It makes you informed enough to have a productive conversation with your prescriber, and catches obvious dangers before you walk into them.

---

## Core Concepts

### The Substance Profile

Every substance in Apothecary's database is tagged with structured pharmacological data:

- **Metabolic pathways** — which CYP450 enzymes metabolize it (substrates, inhibitors, inducers)
- **Receptor targets** — what neurotransmitter systems it affects (serotonergic, dopaminergic, GABAergic, etc.)
- **Nutrient effects** — what it depletes, what it requires for synthesis, what it competes with for absorption
- **Pharmacokinetics** — absorption time, peak plasma, half-life, duration of action
- **Evidence tags** — each data point rated by source quality (RCT, pharmacokinetic study, animal model, case report, theoretical)

### Interaction Inference

Interactions are **computed from structured data**, not manually curated per pair. If Substance A inhibits CYP2D6 and Substance B is metabolized by CYP2D6, the system infers the interaction and explains it. This makes the platform scalable — adding a new substance with proper tags automatically generates all relevant interaction checks.

### The Daily Timeline

Rather than treating a stack as a static list, Apothecary models it as a **dynamic system across 24 hours**. Each substance has a pharmacokinetic curve. The timing optimizer places each substance where it maximizes benefit and minimizes interference, generating a personalized daily schedule with rationale for each placement.

---

## Architecture

```
apothecary/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md        # System design and data flow
│   ├── DATA_MODEL.md          # Substance schema and interaction logic
│   ├── EVIDENCE_FRAMEWORK.md  # Confidence scoring and source hierarchy
│   ├── TIMING_ENGINE.md       # Pharmacokinetic modeling and scheduling
│   ├── SAFETY.md              # Liability, limitations, and ethical guardrails
│   └── ROADMAP.md             # Phased development plan
├── src/
│   ├── apothecary/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── substance.py       # Core substance data model
│   │   │   ├── interaction.py     # Interaction detection and classification
│   │   │   ├── depletion.py       # Nutrient depletion tracking
│   │   │   ├── stack.py           # User's complete substance stack
│   │   │   └── evidence.py        # Evidence rating and source tracking
│   │   ├── engine/
│   │   │   ├── __init__.py
│   │   │   ├── interaction_engine.py  # Pairwise and multi-way interaction computation
│   │   │   ├── timing_engine.py       # Pharmacokinetic scheduling optimizer
│   │   │   ├── depletion_engine.py    # Gap analysis across full stack
│   │   │   └── reasoning.py          # Mechanism explanation generation
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── loader.py          # Database loading and validation
│   │   │   ├── sources.py         # Data source connectors (DrugBank, PubChem, etc.)
│   │   │   └── curated/           # Hand-curated substance profiles (JSON/YAML)
│   │   │       ├── drugs/
│   │   │       ├── supplements/
│   │   │       └── dietary/
│   │   ├── reports/
│   │   │   ├── __init__.py
│   │   │   ├── interaction_report.py  # Full interaction analysis output
│   │   │   ├── timeline_report.py     # Daily schedule visualization data
│   │   │   └── prescriber_export.py   # Clean summary for clinician handoff
│   │   └── api/
│   │       ├── __init__.py
│   │       └── routes.py          # FastAPI endpoints
│   └── tests/
│       ├── __init__.py
│       ├── test_interactions.py
│       ├── test_timing.py
│       └── test_depletions.py
├── data/
│   └── seed/                  # Initial substance database
│       ├── drugs.yaml
│       ├── supplements.yaml
│       └── dietary.yaml
├── pyproject.toml
└── .gitignore
```

---

## Tech Stack

- **Language**: Python 3.12+
- **Backend**: FastAPI
- **Database**: SQLite (dev) → PostgreSQL (prod)
- **Data format**: YAML for curated substance profiles, SQL for relational queries
- **Testing**: pytest
- **Future frontend**: Next.js + TypeScript (separate repo)

---

## Development Phases

### Phase 1: Foundation (Current)
- Define data model for substances, interactions, and evidence
- Curate seed database (~50 common drugs, ~100 supplements, ~20 dietary factors)
- Build interaction engine (CYP450, receptor, depletion, absorption)
- Build CLI tool for stack analysis

### Phase 2: Intelligence
- Timing optimization engine
- Mechanism explanation generation
- Multi-way interaction detection (beyond pairwise)
- Prescriber export (PDF)

### Phase 3: Interface
- Web frontend for stack input and visualization
- Daily timeline view
- Interactive mechanism maps
- User accounts and saved stacks

### Phase 4: Scale
- Expanded substance database
- Community contributions with clinical review
- API for third-party integration
- Mobile app

---

## Principles

1. **Transparency over authority** — Show the evidence, the reasoning, and the confidence level. Never claim certainty where it doesn't exist.
2. **Informational, not prescriptive** — Provide understanding, not instructions. Always direct users toward professional consultation for clinical decisions.
3. **Mechanism over memorization** — Explain *why* things interact, not just *that* they interact. Teach the user to reason about their own body.
4. **Universal by design** — Built for anyone taking anything, not a niche audience. The architecture serves a college student on birth control and an elderly patient on six medications equally.
5. **No conflicts of interest** — No affiliate links, no supplement sales, no sponsored recommendations. Trust is the product.

---

## License

MIT

---

## Status

🚧 **Early development** — Architecture and data model phase.
