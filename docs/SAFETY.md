# Safety & Ethics

Apothecary provides pharmacological information. It does not provide medical advice. This document defines the guardrails that keep users informed without putting them at risk.

---

## Core Principle

**Apothecary is a literacy tool, not a clinical tool.**

It helps users understand what they're taking and how it works together. It does not tell users what to take, what to stop taking, or what dose to use. It surfaces information and reasoning that enables productive conversations with healthcare professionals.

---

## What Apothecary Does and Does Not Do

### Does
- Flag known and inferred interactions between substances
- Explain the biological mechanism behind interactions
- Show the evidence basis and confidence level for each finding
- Suggest optimal timing based on pharmacokinetic data
- Identify nutrient depletions caused by medications
- Generate reports users can share with their prescriber or pharmacist

### Does Not
- Recommend specific substances, brands, or doses
- Tell users to start, stop, or change any medication
- Diagnose conditions or symptoms
- Replace professional pharmacist interaction checks
- Guarantee safety of any combination
- Provide emergency medical guidance

---

## Interaction Severity Framework

### CRITICAL (Red)
Life-threatening or seriously harmful combinations.
**User action**: DO NOT combine without direct medical supervision.
**Examples**: SSRI + MAO inhibitor, warfarin + high-dose vitamin K, serotonin syndrome risk combinations.
**Platform behavior**: Prominent warning, cannot be dismissed without acknowledgment.

### HIGH (Orange)
Clinically significant interactions that may cause harm or major efficacy changes.
**User action**: Discuss with prescriber or pharmacist before combining.
**Examples**: CBD + medications metabolized by CYP2C19, significant CYP450 inhibitor/substrate overlaps.
**Platform behavior**: Clear warning with mechanism explanation.

### MODERATE (Yellow)
Interactions that may affect efficacy or cause manageable side effects.
**User action**: Be aware; consider timing adjustments; mention to prescriber at next visit.
**Examples**: Magnesium reducing stimulant absorption if taken simultaneously, additive sedation.
**Platform behavior**: Informational flag with timing suggestion if applicable.

### LOW (Blue)
Minor or theoretical interactions with limited clinical significance.
**User action**: Informational awareness only.
**Examples**: Theoretical nutrient competition, minor absorption delays.
**Platform behavior**: Available in detailed view, not prominently flagged.

### BENEFICIAL (Green)
Combinations where substances complement or protect each other.
**User action**: No action needed; this combination may be helpful.
**Examples**: NAC providing antioxidant protection alongside stimulants, magnesium addressing stimulant-induced depletion.
**Platform behavior**: Positive indicator with mechanism explanation.

---

## Confidence Display Rules

1. **Established** findings are presented as statements: "Escitalopram is metabolized by CYP2C19."
2. **Probable** findings use qualified language: "Stimulant medications are associated with increased magnesium excretion."
3. **Possible** findings are clearly hedged: "Animal studies suggest NAC may modulate glutamate signaling, which could affect stimulant response."
4. **Theoretical** findings are explicitly labeled: "Based on known pharmacology, this interaction is theoretically possible but has not been studied directly."
5. **Anecdotal** findings are separated from evidence-based content and labeled as community-reported.

---

## Disclaimers

Every analysis output includes:

> This report is for informational purposes only and does not constitute medical advice. Apothecary identifies potential interactions based on published pharmacological data and does not guarantee the safety or efficacy of any combination. Always consult a qualified healthcare professional — particularly your prescriber and pharmacist — before starting, stopping, or changing any medication or supplement. If you experience adverse effects, contact your healthcare provider or call emergency services immediately.

---

## Dangerous Combination Handling

Certain combinations are **hardcoded blocks** regardless of computed inference:

- SSRI/SNRI + MAO inhibitor
- SSRI/SNRI + high-dose 5-HTP or tryptophan supplementation
- Warfarin + substances with major anticoagulant interaction
- Lithium + NSAIDs (without explicit medical supervision flag)
- Methotrexate + NSAIDs
- Any combination flagged by FDA black box warnings

These are not computed from tags — they are explicitly listed and maintained as a safety-critical override layer. The computed engine may catch them too, but the hardcoded list ensures they are never missed.

---

## Edge Cases

### "I already take this combination and I'm fine"
The platform should acknowledge that individual variation exists and that many interactions are risk-elevating rather than deterministic. A flag does not mean harm is certain — it means risk is elevated and awareness is warranted.

### Users who want to ignore warnings
Warnings can be acknowledged but not permanently dismissed. The platform does not gatekeep — it informs. But CRITICAL-level warnings require explicit acknowledgment and include a recommendation to verify with a pharmacist.

### Pregnancy and lactation
Phase 1 does not provide pregnancy-specific interaction data. When a user indicates pregnancy, the platform should state that its data does not account for pregnancy-specific risks and recommend consultation with an OB-GYN or maternal-fetal medicine specialist.

### Pediatric use
Phase 1 does not provide pediatric dosing or interaction data. When a user indicates the stack is for a minor, the platform should recommend consultation with a pediatrician.

---

## Data Integrity

- Every substance profile must cite at least one primary source
- Community-submitted data undergoes review before inclusion in the main database
- Version history is maintained for all substance profiles
- Corrections and updates are logged with timestamps and rationale
- Annual review cycle for high-traffic substance profiles
