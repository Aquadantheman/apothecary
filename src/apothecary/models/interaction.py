"""Interaction models — represent detected interactions between substances."""

from enum import Enum
from pydantic import BaseModel

from apothecary.models.evidence import ConfidenceTier


class InteractionType(str, Enum):
    """Categories of interaction the engine checks for."""

    CYP450 = "cyp450"  # Metabolic pathway conflict
    RECEPTOR_STACKING = "receptor_stacking"  # Same neurotransmitter system
    NUTRIENT_DEPLETION = "nutrient_depletion"  # Unaddressed depletion gap
    ABSORPTION = "absorption"  # Absorption interference
    ANTAGONISM = "antagonism"  # Working against each other
    ADDITIVE_SIDE_EFFECT = "additive_side_effect"  # Shared side effects
    BENEFICIAL = "beneficial"  # Complementary or protective
    CONTRAINDICATION = "contraindication"  # Hardcoded dangerous combination


class Severity(str, Enum):
    """How serious the interaction is."""

    CRITICAL = "critical"  # Life-threatening, do not combine without supervision
    HIGH = "high"  # Clinically significant, discuss with prescriber
    MODERATE = "moderate"  # May affect efficacy or cause manageable effects
    LOW = "low"  # Minor or theoretical
    BENEFICIAL = "beneficial"  # Positive interaction


# Map severity to display colors for CLI
SEVERITY_COLORS = {
    Severity.CRITICAL: "red",
    Severity.HIGH: "orange1",
    Severity.MODERATE: "yellow",
    Severity.LOW: "blue",
    Severity.BENEFICIAL: "green",
}

SEVERITY_ICONS = {
    Severity.CRITICAL: "🔴",
    Severity.HIGH: "🟠",
    Severity.MODERATE: "🟡",
    Severity.LOW: "🔵",
    Severity.BENEFICIAL: "🟢",
}


class Interaction(BaseModel):
    """A single detected interaction between two or more substances.

    This is the primary output of the interaction engine.
    """

    substances: list[str]  # IDs of involved substances (usually 2, can be more)
    type: InteractionType
    severity: Severity
    confidence: ConfidenceTier

    # Human-readable explanation
    title: str  # Short summary (e.g. "CYP2D6 pathway overlap")
    mechanism: str  # Detailed mechanism explanation
    recommendation: str  # What the user should do or be aware of

    # Optional details
    pathway: str | None = None  # Specific pathway (e.g. "CYP2D6", "serotonergic")
    timing_relevant: bool = False  # Can this be resolved by timing separation?
    timing_suggestion: str | None = None  # If timing_relevant, what spacing helps?


class DepletionGap(BaseModel):
    """A nutrient being depleted by a medication but not replenished by any supplement."""

    nutrient: str
    depleted_by: list[str]  # Substance IDs causing depletion
    mechanism: str
    confidence: ConfidenceTier
    clinical_significance: str
    suggestion: str  # What supplement could address this
    food_sources: list[str] = []  # Foods rich in this nutrient
    symptoms: list[str] = []  # What deficiency feels like
    lifestyle_tips: list[str] = []  # Non-supplement interventions


class StackAnalysis(BaseModel):
    """Complete analysis output for a user's full substance stack."""

    interactions: list[Interaction]  # All detected interactions
    depletion_gaps: list[DepletionGap]  # Unaddressed nutrient depletions
    aggregate_serotonin_load: float  # Combined serotonergic activity (0-1+)
    aggregate_cardiovascular_flags: int  # Count of cardiovascular-flagged substances

    @property
    def critical_interactions(self) -> list[Interaction]:
        return [i for i in self.interactions if i.severity == Severity.CRITICAL]

    @property
    def high_interactions(self) -> list[Interaction]:
        return [i for i in self.interactions if i.severity == Severity.HIGH]

    @property
    def beneficial_interactions(self) -> list[Interaction]:
        return [i for i in self.interactions if i.severity == Severity.BENEFICIAL]

    @property
    def has_critical(self) -> bool:
        return len(self.critical_interactions) > 0

    @property
    def interaction_count_by_severity(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for i in self.interactions:
            key = i.severity.value
            counts[key] = counts.get(key, 0) + 1
        return counts
