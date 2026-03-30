# Evidence Framework

Trust is Apothecary's product. Every claim must be traceable to a source, rated for confidence, and transparent about its limitations.

---

## Confidence Tiers

| Tier | Label | Source Types | Display Treatment |
|------|-------|-------------|-------------------|
| 1 | **Established** | Human RCTs, systematic reviews, FDA labels, pharmacokinetic studies with clinical validation | Stated as fact |
| 2 | **Probable** | Human observational studies, consistent case report series, PK modeling validated against human data | Qualified statement |
| 3 | **Possible** | Animal studies, in-vitro studies with plausible human extrapolation, mechanistic reasoning supported by partial human data | Clearly hedged |
| 4 | **Theoretical** | Inferred from known pharmacology with no direct study of the specific combination | Explicitly labeled as theoretical |
| 5 | **Anecdotal** | Community reports, user experiences, forum consensus without formal study | Separated from evidence-based content |

---

## Source Hierarchy

When multiple sources provide conflicting information, priority follows:

1. **FDA prescribing information** — authoritative for drug pharmacology
2. **Cochrane reviews / systematic reviews** — highest quality synthesis
3. **Randomized controlled trials** — gold standard for individual studies
4. **Pharmacokinetic studies** — authoritative for metabolism and timing
5. **Prospective observational studies** — useful for real-world signal
6. **Case report series** — useful for rare interactions
7. **Animal / in-vitro studies** — informative but not directly translatable
8. **Expert consensus / clinical guidelines** — useful for practice patterns
9. **Mechanistic inference** — useful when no direct data exists
10. **Community reports** — signal only, never treated as evidence

---

## Citation Format

Every data point in the substance database links to its evidence:

```yaml
evidence:
  - claim: "Escitalopram is primarily metabolized by CYP2C19"
    confidence: "established"
    sources:
      - type: "fda_label"
        reference: "Lexapro prescribing information, Section 12.3"
        url: "https://www.accessdata.fda.gov/drugsatfda_docs/label/..."
      - type: "pubmed"
        pmid: "12345678"
        title: "CYP2C19 polymorphism and escitalopram metabolism"
        study_type: "pharmacokinetic"
        sample_size: 24
        year: 2004
    last_reviewed: "2026-03-30"
```

---

## Rules for Presenting Uncertain Information

1. **Never present theoretical interactions with the same visual weight as established ones.** A theoretical CYP450 overlap and a confirmed serotonin syndrome risk must look different to the user.

2. **Always show what you don't know.** If an interaction is flagged as "possible" based on animal data, say so. If a supplement's CYP450 profile hasn't been studied in humans, say so.

3. **Absence of evidence is not evidence of absence.** If no interaction data exists for a combination, the platform says "No known interactions found. This does not guarantee safety — limited research exists for this combination." It does not say "Safe to combine."

4. **Quantify when possible.** "NAC 600mg has been studied in 3 human trials for glutamate modulation" is better than "NAC may affect glutamate."

5. **Date the evidence.** A 2004 study and a 2024 study carry different weight. The platform shows when each claim was last reviewed.

---

## Handling Contradictory Evidence

When sources disagree:

1. Note the disagreement explicitly — do not silently pick one side
2. Present the stronger evidence first (per source hierarchy)
3. Explain what might account for the difference (dose, population, study design)
4. Default to the more conservative interpretation for safety-relevant claims
5. Flag the contradiction for priority review in the next curation cycle

---

## Community Contributions

User-submitted interaction reports or substance data follow a gated review process:

1. **Submission**: User reports an interaction or suggests a data correction
2. **Triage**: Automated checks for completeness and source citation
3. **Review**: Flagged for pharmacological review (initially by the founding team, eventually by advisory board)
4. **Integration**: Accepted submissions enter the database tagged as "community-submitted" until independently verified
5. **Promotion**: After independent verification, tag is upgraded to the appropriate confidence tier

Community data is never silently mixed with curated data. Users can always distinguish between professionally curated and community-contributed information.

---

## Annual Review Cycle

High-traffic substance profiles (top 100 by user query frequency) undergo annual review:

1. Check for new systematic reviews or meta-analyses
2. Check for new FDA safety communications
3. Check for significant new RCTs
4. Verify all source URLs are still accessible
5. Update confidence ratings if new evidence changes the picture
6. Log all changes with rationale
