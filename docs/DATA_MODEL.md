# Data Model

The substance data model is the foundation of Apothecary. Every feature — interaction checking, timing optimization, depletion tracking, mechanism explanation — derives from how substances are structured and tagged.

---

## Design Philosophy

Interactions are **computed, not curated**. Rather than manually documenting that "NAC may reduce Adderall efficacy," we tag NAC with its glutamate-modulating properties and Adderall with its dopaminergic mechanism, and the engine infers the relevant relationship. This makes the system scalable — adding a properly tagged substance automatically generates all interaction checks against every other substance in the database.

Manual curation is reserved for **overrides and edge cases** where computed inference is insufficient or misleading.

---

## Substance Schema

```yaml
# Example: Adderall (mixed amphetamine salts)
substance:
  id: "adderall"
  name: "Adderall (Mixed Amphetamine Salts)"
  type: "prescription"            # prescription | supplement | otc | dietary
  category: "stimulant"           # functional category
  common_names:
    - "Adderall"
    - "Adderall XR"
    - "mixed amphetamine salts"
    - "amphetamine/dextroamphetamine"

  # === PHARMACOKINETICS ===
  pharmacokinetics:
    formulations:
      - name: "IR (Immediate Release)"
        absorption_minutes: 30        # time to onset
        peak_plasma_hours: 3          # Tmax
        half_life_hours: 10           # T1/2 (average, varies by individual)
        duration_hours: 6             # effective duration
      - name: "XR (Extended Release)"
        absorption_minutes: 60
        peak_plasma_hours: 7
        half_life_hours: 11
        duration_hours: 12
    food_effect: "may delay absorption slightly"
    ph_sensitivity: "alkaline urine slows excretion, acidic urine accelerates"

  # === METABOLIC PATHWAYS ===
  metabolism:
    cyp450:
      - enzyme: "CYP2D6"
        role: "substrate"             # substrate | inhibitor | inducer
        significance: "major"         # major | minor
        evidence: "established"       # established | probable | theoretical
    other_enzymes: []
    renal_excretion: true
    ph_dependent: true                # urinary pH affects clearance

  # === RECEPTOR / NEUROTRANSMITTER ACTIVITY ===
  receptor_activity:
    - system: "dopaminergic"
      mechanism: "Reverses DAT (dopamine transporter), increasing synaptic dopamine"
      direction: "increase"           # increase | decrease | modulate
      magnitude: "strong"             # strong | moderate | mild
    - system: "noradrenergic"
      mechanism: "Reverses NET (norepinephrine transporter), increasing synaptic norepinephrine"
      direction: "increase"
      magnitude: "strong"
    - system: "serotonergic"
      mechanism: "Mild serotonin release at higher doses"
      direction: "increase"
      magnitude: "mild"

  # === NUTRIENT EFFECTS ===
  nutrient_effects:
    depletions:
      - nutrient: "magnesium"
        mechanism: "Increased urinary magnesium excretion"
        evidence: "probable"
        clinical_significance: "moderate"
      - nutrient: "vitamin_c"
        mechanism: "Accelerated utilization under oxidative stress"
        evidence: "theoretical"
        clinical_significance: "low"
    requirements:
      - nutrient: "tyrosine"
        mechanism: "Precursor for dopamine synthesis; increased demand under stimulant-driven release"
        evidence: "established"

  # === OXIDATIVE / INFLAMMATORY PROFILE ===
  oxidative_profile:
    generates_ros: true
    mechanism: "Dopamine auto-oxidation produces reactive quinones; MAO metabolism produces H2O2"
    mitochondrial_impact: "Chronic use may impair mitochondrial complex I function"
    neuroinflammation: "Microglial activation documented at high doses in animal models"
    evidence: "established in animal models, probable at therapeutic doses"

  # === ABSORPTION INTERACTIONS ===
  absorption:
    enhancers:
      - substance: "vitamin_c"
        mechanism: "Acidifies urine, accelerating excretion (reduces duration)"
        net_effect: "negative"
    inhibitors:
      - substance: "antacids"
        mechanism: "Alkalinizes GI, may increase absorption"
        net_effect: "increases_effect"
      - substance: "magnesium"
        mechanism: "May affect absorption if taken simultaneously"
        timing_note: "Separate by 8+ hours; evening magnesium avoids interference"

  # === TIMING CONSTRAINTS ===
  timing:
    optimal_window: "morning"
    take_with_food: "recommended"
    latest_recommended_hour: 10       # 10 AM for XR to clear by bedtime
    spacing_requirements:
      - substance_tag: "alkalinizing"
        rule: "avoid_concurrent"
        reason: "Alkaline substances slow amphetamine excretion, prolonging effects"
      - substance_tag: "magnesium"
        rule: "separate_8h"
        reason: "Potential absorption interference"

  # === SAFETY FLAGS ===
  safety:
    serotonin_load: 0.2               # 0-1 scale of serotonergic activity
    cardiovascular_flag: true
    appetite_suppression: true
    sleep_disruption: true
    contraindications:
      - "MAO inhibitors (hypertensive crisis risk)"
      - "Severe cardiovascular disease"

  # === METADATA ===
  metadata:
    data_sources:
      - "DrugBank DB00182"
      - "FDA prescribing information"
      - "PubMed PMID:16808729"
    last_reviewed: "2026-03-30"
    review_status: "curated"          # curated | auto-generated | community-submitted
```

---

## Substance Types

### Prescription Drugs
Full pharmacokinetic profiles, FDA-sourced interaction data, CYP450 metabolism well-documented.
Primary source: DrugBank, FDA labels.

### Supplements
Variable evidence quality. CYP450 data available for common supplements (St. John's Wort, CBD, curcumin). Receptor activity and nutrient data from clinical studies and monographs.
Primary sources: NatMed (where accessible), Examine.com, PubMed, MSKCC About Herbs.

### OTC Medications
Treated like prescription drugs but with consumer-accessible framing.
Primary source: FDA OTC monographs, DrugBank.

### Dietary Factors
Foods and beverages with pharmacological relevance. Includes grapefruit (CYP3A4 inhibitor), dairy (calcium absorption interference), leafy greens (vitamin K / warfarin), caffeine (adenosine antagonist, CYP1A2 substrate), alcohol (CYP2E1 inducer, CNS depressant).
Primary sources: FDA food-drug interaction guidance, clinical literature.

---

## Interaction Types

The engine checks for these categories of interaction:

### 1. Metabolic (CYP450)
Two substances sharing a CYP450 pathway. If A inhibits CYP2D6 and B is metabolized by CYP2D6, B's blood level rises.

**Severity mapping:**
- Inhibitor + substrate on same major pathway → HIGH
- Inducer + substrate on same major pathway → MODERATE (reduced efficacy)
- Minor pathway overlap → LOW

### 2. Receptor / Neurotransmitter Stacking
Two or more substances affecting the same neurotransmitter system.

**Severity mapping:**
- Combined serotonin_load > 0.8 → HIGH (serotonin syndrome risk)
- Combined serotonin_load 0.5-0.8 → MODERATE (monitor for symptoms)
- Dual dopaminergic agents → MODERATE
- Dual GABAergic agents → MODERATE (additive sedation)

### 3. Nutrient Depletion
Medication depletes a nutrient that isn't being replenished by any supplement in the stack.

**Severity mapping:**
- Clinically significant depletion with no supplementation → MODERATE
- Depletion with partial supplementation → LOW (informational)

### 4. Absorption Interference
Two substances that interfere with each other's absorption when taken simultaneously.

**Severity mapping:**
- Varies; usually LOW with timing note
- Resolved by timing separation (the timing engine handles this)

### 5. Physiological Antagonism
Substances working against each other's intended effect (e.g., stimulant + sedative, vasodilator + vasoconstrictor).

**Severity mapping:**
- Context-dependent; sometimes intentional (e.g., L-theanine softening stimulant edge)

### 6. Additive Side Effects
Substances that share side effects (e.g., two things that both suppress appetite, two things that both raise blood pressure).

**Severity mapping:**
- Additive cardiovascular effects → HIGH
- Additive appetite suppression → LOW (informational)
- Additive sedation → MODERATE

---

## Evidence Rating Scale

Every data point carries an evidence tag:

| Rating | Definition | Examples |
|--------|-----------|----------|
| **Established** | Confirmed in human RCTs or extensive pharmacokinetic studies | CYP450 substrates from FDA labels |
| **Probable** | Supported by human observational data, PK modeling, or consistent case reports | Magnesium depletion from stimulants |
| **Possible** | Supported by animal studies or mechanistic reasoning with limited human data | NAC modulating stimulant efficacy via glutamate |
| **Theoretical** | Inferred from known pharmacology but no direct studies | Some oxidative stress claims at therapeutic doses |
| **Anecdotal** | Reported by users/communities but no formal study | Timing-specific effects from Reddit/community reports |

Interactions flagged as "theoretical" or "anecdotal" are clearly marked and never presented with the same visual weight as established interactions.

---

## Seed Database Priority

### Phase 1 Drugs (~50)
SSRIs (escitalopram, sertraline, fluoxetine, etc.), SNRIs, stimulants (amphetamine, methylphenidate), benzodiazepines, common antihypertensives, statins, metformin, levothyroxine, PPIs, oral contraceptives, common antibiotics, NSAIDs, acetaminophen, warfarin.

### Phase 1 Supplements (~100)
Magnesium (glycinate, citrate, oxide, threonate), omega-3 (EPA/DHA), vitamin D3, B-complex, B12, iron, calcium, zinc, NAC, L-theanine, melatonin, ashwagandha, curcumin/turmeric, probiotics, CoQ10, creatine, CBD, 5-HTP, St. John's Wort, valerian, GABA, L-tyrosine, tryptophan, vitamin C, vitamin E, selenium, folate/methylfolate, SAMe, rhodiola, lion's mane, berberine, quercetin, resveratrol, alpha-lipoic acid, acetyl-L-carnitine, phosphatidylserine, milk thistle.

### Phase 1 Dietary (~20)
Caffeine, alcohol, grapefruit, dairy/calcium, leafy greens (vitamin K), tyramine-rich foods, activated charcoal, fiber supplements, antacids, tonic water (quinine).

---

## Data Sources

| Source | Coverage | Access | Use |
|--------|----------|--------|-----|
| DrugBank | ~14,000 drugs | Open (academic) | CYP450, targets, PK data |
| PubChem | Molecular data | Open | Chemical properties |
| FDA Labels | Prescription drugs | Open | Official interactions, PK |
| MSKCC About Herbs | ~300 supplements | Free | Interactions, evidence summaries |
| Examine.com | ~400 supplements | Free (basic) | Efficacy, dosing, interactions |
| PubMed | Primary literature | Open (abstracts) | Evidence for specific claims |
| FAERS | Adverse events | Open | Real-world interaction signals |
| Natural Medicines (NatMed) | Comprehensive | Paid ($69-182/yr) | Reference for curation, not direct data |
