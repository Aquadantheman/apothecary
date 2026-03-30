# Timing Engine

The timing engine is Apothecary's most differentiated feature. Existing interaction checkers treat a user's stack as a static list. Apothecary treats it as a dynamic system across 24 hours.

---

## Why Timing Matters

Many interactions are only relevant when substances are taken simultaneously. Magnesium can interfere with amphetamine absorption — but only if taken at the same time. Separated by 10 hours, the same combination is not only safe but beneficial (magnesium replenishes stimulant-induced depletion). The interaction engine flags the risk; the timing engine resolves it.

Beyond interactions, timing affects efficacy. Stimulants taken earlier clear earlier, improving sleep. Melatonin taken 30-60 minutes before bed aligns with the natural circadian onset. Protein in the morning provides tyrosine for dopamine synthesis during stimulant activity. Carbohydrates in the evening shift amino acid competition toward tryptophan for serotonin/melatonin production.

---

## Time Blocks

The engine works with six time blocks relative to wake time (not clock time, since users have different schedules):

| Block | Relative Time | Typical Clock | Character |
|-------|---------------|---------------|-----------|
| Wake | 0-1h after waking | 7-8 AM | Anchor block for medications with morning timing |
| Mid-Morning | 2-4h | 9-11 AM | Secondary morning doses |
| Midday | 5-7h | 12-2 PM | Midday supplements, antioxidant window |
| Afternoon | 8-10h | 3-5 PM | Caffeine cutoff, transition period |
| Evening | 11-13h | 6-8 PM | Dinner-timed supplements, nutrient replenishment |
| Pre-Bed | 14-16h (30-60min before sleep) | 9-11 PM | Sleep support, circadian signaling |

---

## Placement Rules

### Priority 1: Fixed Anchors
Some substances have non-negotiable timing:
- Levothyroxine: must be taken on empty stomach, 30-60min before food
- Prescription medications with specific timing instructions from prescriber
- Medications with "take with food" requirements anchor to meal times

### Priority 2: Spacing Requirements
Substances that interfere with each other's absorption must be separated:
- Calcium and iron: separate by 2+ hours
- Calcium/magnesium and levothyroxine: separate by 4+ hours
- Magnesium and amphetamine: separate by 8+ hours (evening mag, morning stim)
- Fiber supplements and medications: separate by 2+ hours

### Priority 3: Pharmacokinetic Alignment
Place substances where their PK curve aligns with the desired effect:
- Stimulants: as early as feasible to clear before bedtime
- L-theanine with stimulant: co-administration for synergistic modulation
- NAC midday: antioxidant protection during peak dopamine metabolism
- Melatonin IR/XR: 30-60min before target sleep time
- Magnesium glycinate: evening, allows GABA support during sleep onset

### Priority 4: Nutrient Timing
Align with metabolic context:
- Tyrosine/protein: morning, to fuel dopamine synthesis during stimulant activity
- Antioxidants (NAC, vitamin C, berry polyphenols): midday, during peak oxidative load
- Tryptophan-promoting foods (carbs): evening, to shift amino acid balance toward serotonin
- Fat-soluble vitamins (D3, E, K, omega-3): with meals containing fat for absorption

### Priority 5: Circadian Alignment
Some substances affect circadian biology:
- Vitamin D3: morning or midday (may interfere with melatonin production if taken late)
- B vitamins: morning (energizing, may disrupt sleep if taken late)
- Magnesium: evening (calming, supports sleep)
- Melatonin: pre-bed only

---

## Output Format

The timeline output is a structured schedule with rationale:

```yaml
daily_timeline:
  wake_time: "07:00"
  sleep_target: "23:00"

  blocks:
    - block: "wake"
      time: "07:00"
      substances:
        - name: "Lexapro 10mg"
          rationale: "Consistent daily timing; morning standard for SSRIs"
        - name: "Creatine 5g"
          rationale: "Daily maintenance; timing not critical, morning for consistency"
        - name: "Omega-3 (2 softgels)"
          rationale: "Fat-soluble; take with breakfast for absorption"
        - name: "L-Theanine 200mg"
          rationale: "Co-administer with stimulant for synergistic alpha-wave modulation"
        - name: "Adderall XR 20mg"
          rationale: "As early as feasible; 12h duration clears by ~19:00"
      meal_note: "Protein-forward breakfast (eggs, meat) — provides tyrosine for dopamine synthesis"

    - block: "midday"
      time: "12:30"
      substances:
        - name: "NAC 600mg"
          rationale: "Antioxidant protection during peak dopamine metabolism; glutathione precursor"
      meal_note: "Blueberries or dark berries — anthocyanins provide additional antioxidant support"

    - block: "evening"
      time: "18:30"
      substances:
        - name: "Magnesium Glycinate 240mg"
          rationale: "8+ hours after stimulant (no absorption interference); glycine supports GABA; replenishes stimulant-induced depletion"
      meal_note: "Strategic carb portion (sweet potato, rice) on stimulant days — insulin response promotes tryptophan transport across BBB for serotonin/melatonin synthesis"

    - block: "pre_bed"
      time: "22:00"
      substances:
        - name: "Melatonin IR/XR 1.5mg"
          rationale: "Immediate-release for sleep onset; extended-release for sleep maintenance through the night; 30-60min before target sleep time"
      note: "Warm shower before bed — thermoregulatory drop promotes sleep onset"
```

---

## Conflict Resolution

When spacing requirements create impossible schedules (e.g., three substances that all need to be separated from each other by 4+ hours), the engine prioritizes by:

1. Safety-critical spacing (drug-drug interactions) — never compromised
2. Efficacy-critical spacing (absorption interference) — prioritized
3. Optimization spacing (synergistic timing) — best-effort
4. Convenience — minimizing the number of daily "waves"

The output notes when a perfect schedule isn't achievable and explains the tradeoff made.

---

## Personalization Inputs

The timing engine accepts optional user context that improves recommendations:

- **Wake time and sleep target**: Shifts all blocks accordingly
- **Meal times**: Anchors food-dependent substances
- **Work schedule**: Adjusts stimulant timing for peak cognitive demand
- **Exercise timing**: Some supplements (creatine, BCAAs) benefit from exercise-proximate dosing
- **Stimulant-on vs stimulant-off days**: Different protocols for each (e.g., skip L-theanine and NAC on off days)
