"""Interaction engine — computes interactions across a user's full substance stack.

This is the core of Apothecary. It takes a list of resolved Substance objects
and checks every pair (and the aggregate stack) for interactions across all
dimensions: CYP450, receptor stacking, depletions, absorption, and safety.
"""

from itertools import combinations

from apothecary.models.evidence import ConfidenceTier
from apothecary.models.substance import (
    CYPRole,
    NeurotransmitterSystem,
    Substance,
)
from apothecary.models.interaction import (
    DepletionGap,
    Interaction,
    InteractionType,
    Severity,
    StackAnalysis,
)


# === Hardcoded Dangerous Combinations ===
# These are never computed — they are explicit safety blocks.
# Format: frozenset of category/ID pairs → (severity, title, mechanism)

DANGEROUS_COMBINATIONS: dict[frozenset[str], tuple[Severity, str, str]] = {
    frozenset({"ssri", "maoi"}): (
        Severity.CRITICAL,
        "SSRI + MAO Inhibitor — Serotonin Syndrome Risk",
        "Combining an SSRI with an MAO inhibitor can cause life-threatening serotonin "
        "syndrome. This combination is contraindicated. Requires a washout period of "
        "at least 2 weeks (5 weeks for fluoxetine) between stopping one and starting the other.",
    ),
    frozenset({"snri", "maoi"}): (
        Severity.CRITICAL,
        "SNRI + MAO Inhibitor — Serotonin Syndrome Risk",
        "Combining an SNRI with an MAO inhibitor can cause life-threatening serotonin "
        "syndrome. This combination is contraindicated.",
    ),
    frozenset({"ssri", "5-htp"}): (
        Severity.CRITICAL,
        "SSRI + 5-HTP — Serotonin Syndrome Risk",
        "5-HTP is a direct serotonin precursor. Combined with an SSRI that blocks serotonin "
        "reuptake, this can cause dangerous serotonin accumulation. Do not combine.",
    ),
    frozenset({"ssri", "5_htp"}): (
        Severity.CRITICAL,
        "SSRI + 5-HTP — Serotonin Syndrome Risk",
        "5-HTP is a direct serotonin precursor. Combined with an SSRI that blocks serotonin "
        "reuptake, this can cause dangerous serotonin accumulation. Do not combine.",
    ),
    frozenset({"ssri", "serotonin_precursor"}): (
        Severity.CRITICAL,
        "SSRI + Serotonin Precursor — Serotonin Syndrome Risk",
        "Serotonin precursors combined with SSRIs can cause dangerous serotonin accumulation. "
        "Do not combine without direct medical supervision.",
    ),
    frozenset({"snri", "5-htp"}): (
        Severity.CRITICAL,
        "SNRI + 5-HTP — Serotonin Syndrome Risk",
        "5-HTP is a direct serotonin precursor. Combined with an SNRI, this can cause "
        "dangerous serotonin accumulation. Do not combine.",
    ),
    frozenset({"snri", "5_htp"}): (
        Severity.CRITICAL,
        "SNRI + 5-HTP — Serotonin Syndrome Risk",
        "5-HTP is a direct serotonin precursor. Combined with an SNRI, this can cause "
        "dangerous serotonin accumulation. Do not combine.",
    ),
    frozenset({"snri", "serotonin_precursor"}): (
        Severity.CRITICAL,
        "SNRI + Serotonin Precursor — Serotonin Syndrome Risk",
        "Serotonin precursors combined with SNRIs can cause dangerous serotonin accumulation. "
        "Do not combine without direct medical supervision.",
    ),
    frozenset({"ssri", "tryptophan_supplement"}): (
        Severity.HIGH,
        "SSRI + Tryptophan Supplement — Elevated Serotonin Risk",
        "Supplemental tryptophan provides additional serotonin precursor material. "
        "Combined with an SSRI, this may elevate serotonin to problematic levels. "
        "Dietary tryptophan from food is generally safe; supplemental doses are not recommended.",
    ),
}


def _check_hardcoded(a: Substance, b: Substance) -> list[Interaction]:
    """Check for hardcoded dangerous combinations."""
    interactions = []
    # Check both category and ID against the hardcoded set
    tags_a = {a.category, a.id}
    tags_b = {b.category, b.id}

    for combo, (severity, title, mechanism) in DANGEROUS_COMBINATIONS.items():
        if tags_a & combo and tags_b & combo and (tags_a & combo) != (tags_b & combo):
            interactions.append(
                Interaction(
                    substances=[a.id, b.id],
                    type=InteractionType.CONTRAINDICATION,
                    severity=severity,
                    confidence=ConfidenceTier.ESTABLISHED,
                    title=title,
                    mechanism=mechanism,
                    recommendation="Do NOT combine without direct medical supervision.",
                )
            )
    return interactions


def _check_cyp450(a: Substance, b: Substance) -> list[Interaction]:
    """Check for CYP450 metabolic pathway conflicts between two substances."""
    interactions = []

    for entry_a in a.metabolism.cyp450:
        for entry_b in b.metabolism.cyp450:
            if entry_a.enzyme != entry_b.enzyme:
                continue

            # Inhibitor + Substrate = raised blood levels of substrate
            if entry_a.role == CYPRole.INHIBITOR and entry_b.role == CYPRole.SUBSTRATE:
                severity = (
                    Severity.HIGH if entry_b.significance.value == "major" else Severity.MODERATE
                )
                interactions.append(
                    Interaction(
                        substances=[a.id, b.id],
                        type=InteractionType.CYP450,
                        severity=severity,
                        confidence=min(entry_a.evidence, entry_b.evidence, key=_confidence_rank),
                        title=f"{entry_a.enzyme} inhibition — {a.name} may raise {b.name} levels",
                        mechanism=(
                            f"{a.name} inhibits {entry_a.enzyme}, which is a {entry_b.significance.value} "
                            f"metabolic pathway for {b.name}. This may slow {b.name}'s clearance "
                            f"and effectively increase its blood concentration."
                        ),
                        recommendation=(
                            f"Discuss with your prescriber. {b.name} blood levels may be higher "
                            f"than expected when combined with {a.name}."
                        ),
                        pathway=entry_a.enzyme,
                    )
                )

            if entry_b.role == CYPRole.INHIBITOR and entry_a.role == CYPRole.SUBSTRATE:
                severity = (
                    Severity.HIGH if entry_a.significance.value == "major" else Severity.MODERATE
                )
                interactions.append(
                    Interaction(
                        substances=[a.id, b.id],
                        type=InteractionType.CYP450,
                        severity=severity,
                        confidence=min(entry_a.evidence, entry_b.evidence, key=_confidence_rank),
                        title=f"{entry_b.enzyme} inhibition — {b.name} may raise {a.name} levels",
                        mechanism=(
                            f"{b.name} inhibits {entry_b.enzyme}, which is a {entry_a.significance.value} "
                            f"metabolic pathway for {a.name}. This may slow {a.name}'s clearance "
                            f"and effectively increase its blood concentration."
                        ),
                        recommendation=(
                            f"Discuss with your prescriber. {a.name} blood levels may be higher "
                            f"than expected when combined with {b.name}."
                        ),
                        pathway=entry_b.enzyme,
                    )
                )

            # Inducer + Substrate = lowered blood levels of substrate
            if entry_a.role == CYPRole.INDUCER and entry_b.role == CYPRole.SUBSTRATE:
                interactions.append(
                    Interaction(
                        substances=[a.id, b.id],
                        type=InteractionType.CYP450,
                        severity=Severity.MODERATE,
                        confidence=min(entry_a.evidence, entry_b.evidence, key=_confidence_rank),
                        title=f"{entry_a.enzyme} induction — {a.name} may reduce {b.name} efficacy",
                        mechanism=(
                            f"{a.name} induces {entry_a.enzyme}, which metabolizes {b.name}. "
                            f"This may accelerate {b.name}'s clearance and reduce its effectiveness."
                        ),
                        recommendation=(
                            f"Monitor {b.name} efficacy. Dose adjustment may be needed."
                        ),
                        pathway=entry_a.enzyme,
                    )
                )

            if entry_b.role == CYPRole.INDUCER and entry_a.role == CYPRole.SUBSTRATE:
                interactions.append(
                    Interaction(
                        substances=[a.id, b.id],
                        type=InteractionType.CYP450,
                        severity=Severity.MODERATE,
                        confidence=min(entry_a.evidence, entry_b.evidence, key=_confidence_rank),
                        title=f"{entry_b.enzyme} induction — {b.name} may reduce {a.name} efficacy",
                        mechanism=(
                            f"{b.name} induces {entry_b.enzyme}, which metabolizes {a.name}. "
                            f"This may accelerate {a.name}'s clearance and reduce its effectiveness."
                        ),
                        recommendation=(
                            f"Monitor {a.name} efficacy. Dose adjustment may be needed."
                        ),
                        pathway=entry_b.enzyme,
                    )
                )

    return interactions


def _check_receptor_stacking(a: Substance, b: Substance) -> list[Interaction]:
    """Check for additive effects on the same neurotransmitter system."""
    interactions = []

    for ra in a.receptor_activity:
        for rb in b.receptor_activity:
            if ra.system != rb.system:
                continue
            if ra.system == NeurotransmitterSystem.ANTIOXIDANT:
                continue  # Antioxidant stacking is generally beneficial

            # Both increasing the same system
            if ra.direction.value == "increase" and rb.direction.value == "increase":
                # Serotonergic stacking is the most dangerous
                if ra.system == NeurotransmitterSystem.SEROTONERGIC:
                    combined_load = a.safety.serotonin_load + b.safety.serotonin_load
                    if combined_load >= 0.9:
                        severity = Severity.HIGH
                    elif combined_load >= 0.6:
                        severity = Severity.MODERATE
                    else:
                        severity = Severity.LOW

                    interactions.append(
                        Interaction(
                            substances=[a.id, b.id],
                            type=InteractionType.RECEPTOR_STACKING,
                            severity=severity,
                            confidence=ConfidenceTier.ESTABLISHED,
                            title=f"Serotonergic stacking — combined load {combined_load:.1f}",
                            mechanism=(
                                f"Both {a.name} and {b.name} increase serotonergic activity. "
                                f"{a.name}: {ra.mechanism}. {b.name}: {rb.mechanism}. "
                                f"Combined serotonin load: {combined_load:.1f}/1.0."
                            ),
                            recommendation=(
                                "Monitor for serotonin syndrome symptoms (agitation, confusion, "
                                "rapid heart rate, dilated pupils, muscle rigidity, tremor). "
                                "Discuss with your prescriber."
                                if severity in (Severity.HIGH, Severity.MODERATE)
                                else "Low combined serotonergic load. Monitor but likely manageable."
                            ),
                            pathway="serotonergic",
                        )
                    )

                # GABAergic stacking — additive sedation
                elif ra.system == NeurotransmitterSystem.GABAERGIC:
                    interactions.append(
                        Interaction(
                            substances=[a.id, b.id],
                            type=InteractionType.RECEPTOR_STACKING,
                            severity=Severity.MODERATE,
                            confidence=ConfidenceTier.ESTABLISHED,
                            title="GABAergic stacking — additive sedation risk",
                            mechanism=(
                                f"Both {a.name} and {b.name} enhance GABAergic activity, "
                                f"which may cause additive sedation."
                            ),
                            recommendation="Be cautious with driving and machinery. Monitor for excessive drowsiness.",
                            pathway="gabaergic",
                        )
                    )

            # One increasing, one modulating the same system — potentially beneficial
            if ra.direction.value == "increase" and rb.direction.value == "modulate":
                interactions.append(
                    Interaction(
                        substances=[a.id, b.id],
                        type=InteractionType.BENEFICIAL,
                        severity=Severity.BENEFICIAL,
                        confidence=ConfidenceTier.POSSIBLE,
                        title=f"{rb.system.value} modulation alongside {ra.system.value} activation",
                        mechanism=(
                            f"{b.name} modulates the {rb.system.value} system ({rb.mechanism}), "
                            f"which may buffer or refine the {ra.system.value} effects of {a.name}."
                        ),
                        recommendation="This combination may be complementary.",
                        pathway=ra.system.value,
                    )
                )

    return interactions


def _check_absorption(a: Substance, b: Substance) -> list[Interaction]:
    """Check if one substance affects the other's absorption."""
    interactions = []

    for inhibitor in a.absorption.inhibitors:
        if inhibitor.substance_id == b.id or inhibitor.substance_id == b.category:
            interactions.append(
                Interaction(
                    substances=[a.id, b.id],
                    type=InteractionType.ABSORPTION,
                    severity=Severity.LOW,
                    confidence=ConfidenceTier.PROBABLE,
                    title=f"{b.name} may affect {a.name} absorption",
                    mechanism=inhibitor.mechanism,
                    recommendation=inhibitor.timing_note or "Consider spacing these apart.",
                    timing_relevant=True,
                    timing_suggestion=inhibitor.timing_note,
                )
            )

    for inhibitor in b.absorption.inhibitors:
        if inhibitor.substance_id == a.id or inhibitor.substance_id == a.category:
            interactions.append(
                Interaction(
                    substances=[a.id, b.id],
                    type=InteractionType.ABSORPTION,
                    severity=Severity.LOW,
                    confidence=ConfidenceTier.PROBABLE,
                    title=f"{a.name} may affect {b.name} absorption",
                    mechanism=inhibitor.mechanism,
                    recommendation=inhibitor.timing_note or "Consider spacing these apart.",
                    timing_relevant=True,
                    timing_suggestion=inhibitor.timing_note,
                )
            )

    return interactions


def _check_additive_side_effects(a: Substance, b: Substance) -> list[Interaction]:
    """Check for shared side effects that may compound."""
    interactions = []

    if a.safety.cardiovascular_flag and b.safety.cardiovascular_flag:
        interactions.append(
            Interaction(
                substances=[a.id, b.id],
                type=InteractionType.ADDITIVE_SIDE_EFFECT,
                severity=Severity.HIGH,
                confidence=ConfidenceTier.ESTABLISHED,
                title="Additive cardiovascular effects",
                mechanism=(
                    f"Both {a.name} and {b.name} have cardiovascular effects. "
                    f"Combining them may increase heart rate, blood pressure, or other CV effects."
                ),
                recommendation="Monitor blood pressure and heart rate. Discuss with prescriber.",
            )
        )

    if a.safety.appetite_suppression and b.safety.appetite_suppression:
        interactions.append(
            Interaction(
                substances=[a.id, b.id],
                type=InteractionType.ADDITIVE_SIDE_EFFECT,
                severity=Severity.LOW,
                confidence=ConfidenceTier.ESTABLISHED,
                title="Additive appetite suppression",
                mechanism=f"Both {a.name} and {b.name} can suppress appetite.",
                recommendation="Ensure adequate nutrition. Consider scheduled meals.",
            )
        )

    if a.safety.sleep_disruption and b.safety.sleep_disruption:
        interactions.append(
            Interaction(
                substances=[a.id, b.id],
                type=InteractionType.ADDITIVE_SIDE_EFFECT,
                severity=Severity.MODERATE,
                confidence=ConfidenceTier.ESTABLISHED,
                title="Additive sleep disruption",
                mechanism=f"Both {a.name} and {b.name} can disrupt sleep.",
                recommendation="Take both as early as possible. Prioritize sleep hygiene.",
            )
        )

    return interactions


def _check_beneficial(a: Substance, b: Substance) -> list[Interaction]:
    """Check for beneficial/complementary combinations."""
    interactions = []

    # Antioxidant protecting against ROS-generating substance
    a_generates_ros = a.oxidative_profile.generates_ros
    b_is_antioxidant = b.affects_system(NeurotransmitterSystem.ANTIOXIDANT) or any(
        "antioxidant" in p.nutrient.lower() or "glutathione" in p.nutrient.lower()
        for p in b.nutrient_effects.provides
    )

    if a_generates_ros and b_is_antioxidant:
        interactions.append(
            Interaction(
                substances=[a.id, b.id],
                type=InteractionType.BENEFICIAL,
                severity=Severity.BENEFICIAL,
                confidence=ConfidenceTier.PROBABLE,
                title=f"{b.name} may protect against {a.name}-induced oxidative stress",
                mechanism=(
                    f"{a.name} generates reactive oxygen species via: "
                    f"{a.oxidative_profile.mechanism}. "
                    f"{b.name} provides antioxidant support: "
                    f"{b.receptor_activity[0].mechanism if b.receptor_activity else 'antioxidant activity'}."
                ),
                recommendation="This is a potentially protective combination.",
            )
        )

    # Supplement addressing a depletion caused by a medication
    for depletion in a.nutrient_effects.depletions:
        for provision in b.nutrient_effects.provides:
            if depletion.nutrient.lower() in provision.nutrient.lower() or provision.nutrient.lower() in depletion.nutrient.lower():
                interactions.append(
                    Interaction(
                        substances=[a.id, b.id],
                        type=InteractionType.BENEFICIAL,
                        severity=Severity.BENEFICIAL,
                        confidence=ConfidenceTier.PROBABLE,
                        title=f"{b.name} addresses {a.name}-induced {depletion.nutrient} depletion",
                        mechanism=(
                            f"{a.name} depletes {depletion.nutrient}: {depletion.mechanism}. "
                            f"{b.name} provides: {provision.mechanism}."
                        ),
                        recommendation="This supplement helps address a medication-induced depletion.",
                    )
                )

    return interactions


from apothecary.data.nutrients import get_nutrient_profile


def _check_depletions(substances: list[Substance]) -> list[DepletionGap]:
    """Find nutrients being depleted by medications but not replenished by supplements."""
    # Collect all depletions
    all_depletions: dict[str, list[tuple[str, str, ConfidenceTier, str]]] = {}
    for s in substances:
        for dep in s.nutrient_effects.depletions:
            if dep.nutrient not in all_depletions:
                all_depletions[dep.nutrient] = []
            all_depletions[dep.nutrient].append(
                (s.id, dep.mechanism, dep.evidence, dep.clinical_significance.value)
            )

    # Collect all provisions
    all_provisions: set[str] = set()
    for s in substances:
        for prov in s.nutrient_effects.provides:
            all_provisions.add(prov.nutrient.lower())
        # Also check if the substance IS the nutrient (e.g., magnesium supplement)
        if s.type.value == "supplement":
            all_provisions.add(s.id.lower())
            all_provisions.add(s.category.lower())
            for name in s.common_names:
                all_provisions.add(name.lower())

    # Find gaps
    gaps = []
    for nutrient, depletion_sources in all_depletions.items():
        # Check if any provision matches this nutrient
        is_addressed = any(
            nutrient.lower() in prov or prov in nutrient.lower()
            for prov in all_provisions
        )
        if not is_addressed:
            depleted_by = [src[0] for src in depletion_sources]
            mechanism = "; ".join(f"{src[0]}: {src[1]}" for src in depletion_sources)
            confidence = min((src[2] for src in depletion_sources), key=_confidence_rank)
            significance = max(src[3] for src in depletion_sources)

            # Generate suggestion based on nutrient
            nutrient_profile = get_nutrient_profile(nutrient)

            if nutrient_profile:
                suggestion = nutrient_profile["supplement"]
                food_sources = nutrient_profile.get("food_sources", [])
                symptoms = nutrient_profile.get("symptoms", [])
                lifestyle_tips = nutrient_profile.get("lifestyle_tips", [])
            else:
                suggestion = f"Consider supplementing {nutrient}"
                food_sources = []
                symptoms = []
                lifestyle_tips = []

            gaps.append(
                DepletionGap(
                    nutrient=nutrient,
                    depleted_by=depleted_by,
                    mechanism=mechanism,
                    confidence=confidence,
                    clinical_significance=significance,
                    suggestion=suggestion,
                    food_sources=food_sources,
                    symptoms=symptoms,
                    lifestyle_tips=lifestyle_tips,
                )
            )

    return gaps


def _confidence_rank(tier: ConfidenceTier) -> int:
    """Rank confidence tiers for comparison (lower = more confident)."""
    ranking = {
        ConfidenceTier.ESTABLISHED: 0,
        ConfidenceTier.PROBABLE: 1,
        ConfidenceTier.POSSIBLE: 2,
        ConfidenceTier.THEORETICAL: 3,
        ConfidenceTier.ANECDOTAL: 4,
    }
    return ranking.get(tier, 5)


def analyze_stack(substances: list[Substance]) -> StackAnalysis:
    """Run full interaction analysis on a list of substances.

    This is the main entry point for the interaction engine.
    """
    all_interactions: list[Interaction] = []

    # Pairwise checks
    for a, b in combinations(substances, 2):
        all_interactions.extend(_check_hardcoded(a, b))
        all_interactions.extend(_check_cyp450(a, b))
        all_interactions.extend(_check_receptor_stacking(a, b))
        all_interactions.extend(_check_absorption(a, b))
        all_interactions.extend(_check_additive_side_effects(a, b))
        all_interactions.extend(_check_beneficial(a, b))

    # Aggregate checks
    depletion_gaps = _check_depletions(substances)

    # Compute aggregate serotonin load
    total_serotonin = sum(s.safety.serotonin_load for s in substances)

    # Count cardiovascular flags
    cv_flags = sum(1 for s in substances if s.safety.cardiovascular_flag)

    # Sort interactions: critical first, then by severity
    severity_order = {
        Severity.CRITICAL: 0,
        Severity.HIGH: 1,
        Severity.MODERATE: 2,
        Severity.LOW: 3,
        Severity.BENEFICIAL: 4,
    }
    all_interactions.sort(key=lambda i: severity_order.get(i.severity, 5))

    return StackAnalysis(
        interactions=all_interactions,
        depletion_gaps=depletion_gaps,
        aggregate_serotonin_load=total_serotonin,
        aggregate_cardiovascular_flags=cv_flags,
    )
