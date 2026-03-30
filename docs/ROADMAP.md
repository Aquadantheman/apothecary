# Roadmap

---

## Phase 1: Foundation
**Goal**: A working CLI tool that analyzes a substance stack and outputs interaction findings, depletions, and a timing schedule.

### Milestones

#### 1.1 — Data Model & Schema
- [ ] Define Pydantic models for Substance, Interaction, Evidence, Stack, Timeline
- [ ] Create JSON Schema for YAML validation
- [ ] Write schema documentation with examples

#### 1.2 — Seed Database (Priority Substances)
- [ ] Curate 20 high-priority drugs (SSRIs, stimulants, common prescriptions)
- [ ] Curate 30 high-priority supplements (magnesium, omega-3, NAC, melatonin, etc.)
- [ ] Curate 10 dietary factors (caffeine, alcohol, grapefruit, dairy)
- [ ] Tag all with CYP450, receptor activity, depletions, PK data, evidence
- [ ] Validate against known interaction databases for accuracy

#### 1.3 — Interaction Engine v1
- [ ] CYP450 pathway conflict detection
- [ ] Serotonergic load computation
- [ ] Receptor stacking detection
- [ ] Absorption interference flagging
- [ ] Hardcoded dangerous combination blocks
- [ ] Severity classification (critical/high/moderate/low/beneficial)
- [ ] Unit tests against known interaction pairs

#### 1.4 — Depletion Engine v1
- [ ] Cross-reference medication depletions against supplement stack
- [ ] Identify unaddressed gaps
- [ ] Suggest nutrients with literature-supported dose ranges

#### 1.5 — Timing Engine v1
- [ ] Fixed anchor placement
- [ ] Spacing rule enforcement
- [ ] PK-aligned placement
- [ ] Time block generation with rationale
- [ ] Handle stimulant-day vs off-day protocols

#### 1.6 — CLI Interface
- [ ] `apothecary analyze` — run full analysis on a stack file (YAML)
- [ ] `apothecary timeline` — output daily schedule
- [ ] `apothecary check <substance1> <substance2>` — quick pairwise check
- [ ] `apothecary info <substance>` — display substance profile
- [ ] Pretty terminal output with color-coded severity

#### 1.7 — Validation
- [ ] Test against 20 known interaction pairs (confirm correct detection)
- [ ] Test against 10 known safe pairs (confirm no false positives)
- [ ] Test timing output against manually designed protocols
- [ ] Review full output with at least one pharmacist or clinical advisor

---

## Phase 2: Intelligence
**Goal**: Deeper reasoning, better explanations, exportable reports.

- [ ] Mechanism explanation generation (template-based from structured data)
- [ ] Multi-way interaction detection (3+ substance serotonergic stacking, etc.)
- [ ] Prescriber export (PDF report)
- [ ] Expand seed database to ~50 drugs, ~100 supplements, ~20 dietary
- [ ] Evidence citation linking (PubMed URLs in output)
- [ ] Confidence tier display in all outputs
- [ ] Contradictory evidence handling

---

## Phase 3: Interface
**Goal**: Web-based UI for non-technical users.

- [ ] FastAPI backend with REST endpoints
- [ ] Next.js frontend (separate repo)
- [ ] Substance search with autocomplete
- [ ] Stack builder UI (add/remove substances)
- [ ] Interactive daily timeline visualization
- [ ] Interaction report view with expandable mechanism explanations
- [ ] Depletion gap view
- [ ] Prescriber export download
- [ ] User accounts and saved stacks

---

## Phase 4: Scale
**Goal**: Comprehensive coverage, community, and sustainability.

- [ ] Expand to full DrugBank coverage (~2000 common drugs)
- [ ] Expand supplements to ~300
- [ ] Community submission pipeline with review workflow
- [ ] Clinical advisory board (pharmacist + physician reviewers)
- [ ] API for third-party integration
- [ ] Mobile app (React Native or Flutter)
- [ ] Subscription model for premium features
- [ ] Anonymized aggregate data insights (with consent)

---

## Non-Goals (Intentionally Excluded)

- Supplement marketplace or product recommendations
- Affiliate links or sponsored content
- Diagnostic tools or symptom checkers
- Prescription management or refill tracking
- Replacement for professional medical consultation
- EHR/pharmacy system integration (too complex for early stages)
