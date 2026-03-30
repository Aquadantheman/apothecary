"""Substance data model — the foundation of Apothecary.

Every drug, supplement, and dietary factor is represented as a Substance
with structured pharmacological tags that the interaction engine uses
to compute interactions, timing, and depletions.
"""

from enum import Enum
from pydantic import BaseModel, Field

from apothecary.models.evidence import ConfidenceTier


# === Enums ===


class SubstanceType(str, Enum):
    PRESCRIPTION = "prescription"
    SUPPLEMENT = "supplement"
    OTC = "otc"
    DIETARY = "dietary"


class CYPRole(str, Enum):
    """How a substance relates to a CYP450 enzyme."""

    SUBSTRATE = "substrate"  # Metabolized by this enzyme
    INHIBITOR = "inhibitor"  # Blocks this enzyme (raises levels of substrates)
    INDUCER = "inducer"  # Upregulates this enzyme (lowers levels of substrates)


class Significance(str, Enum):
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"


class NeurotransmitterSystem(str, Enum):
    SEROTONERGIC = "serotonergic"
    DOPAMINERGIC = "dopaminergic"
    NORADRENERGIC = "noradrenergic"
    GABAERGIC = "gabaergic"
    GLUTAMATERGIC = "glutamatergic"
    CHOLINERGIC = "cholinergic"
    HISTAMINERGIC = "histaminergic"
    OPIOIDERGIC = "opioidergic"
    ENDOCANNABINOID = "endocannabinoid"
    ANTIOXIDANT = "antioxidant"  # Not a neurotransmitter but a relevant system


class Direction(str, Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    MODULATE = "modulate"  # Bidirectional or context-dependent


class Magnitude(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    MILD = "mild"


class ClinicalSignificance(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class FoodRequirement(str, Enum):
    REQUIRED = "required"  # Must take with food
    RECOMMENDED = "recommended"  # Better with food
    EITHER = "either"  # No preference
    EMPTY_STOMACH = "empty_stomach"  # Must take without food


class SpacingRule(str, Enum):
    AVOID_CONCURRENT = "avoid_concurrent"
    SEPARATE_2H = "separate_2h"
    SEPARATE_4H = "separate_4h"
    SEPARATE_8H = "separate_8h"
    CAUTION = "caution"  # Not a hard rule, but be aware


class AbsorptionEffect(str, Enum):
    INCREASES_EFFECT = "increases_effect"
    DECREASES_EFFECT = "decreases_effect"
    INCREASES_DURATION = "increases_duration"
    DECREASES_DURATION = "decreases_duration"
    DELAYS_ABSORPTION = "delays_absorption"


class ReviewStatus(str, Enum):
    CURATED = "curated"  # Reviewed by team/advisor
    AUTO_GENERATED = "auto_generated"  # Pulled from database, not manually reviewed
    COMMUNITY = "community"  # User-submitted, pending review


class DataTier(str, Enum):
    """Quality tier for substance data.

    Tier 1: Hand-curated with full pharmacological context (timing, depletions, oxidative profile)
    Tier 2: Auto-generated from DrugBank/PubChem — CYP450 and basic targets only
    Tier 3: Community-submitted, unverified — display only, not used by interaction engine
    """

    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"


# === Component Models ===


class Formulation(BaseModel):
    """A specific formulation of a substance (IR, XR, tablet, etc.)."""

    name: str
    label: str = ""
    absorption_minutes: int | None = None
    peak_plasma_hours: float | None = None
    half_life_hours: float | None = None
    duration_hours: float | None = None


class Pharmacokinetics(BaseModel):
    """How the substance moves through the body."""

    formulations: list[Formulation] = []
    food_effect: str | None = None
    ph_sensitivity: str | None = None


class CYP450Entry(BaseModel):
    """A single CYP450 enzyme relationship."""

    enzyme: str  # e.g. "CYP2D6", "CYP3A4", "CYP2C19"
    role: CYPRole
    significance: Significance
    evidence: ConfidenceTier = ConfidenceTier.ESTABLISHED


class Metabolism(BaseModel):
    """How the substance is metabolized."""

    cyp450: list[CYP450Entry] = []
    renal_excretion: bool = False
    ph_dependent: bool = False
    notes: str | None = None
    # Prodrug activation: list of CYP enzymes that ACTIVATE this drug
    # (convert it from inactive prodrug to active metabolite).
    # When these enzymes are inhibited, the drug becomes LESS effective, not more.
    prodrug_activation: list[str] = []  # e.g. ["CYP2D6"] for codeine


class ReceptorActivity(BaseModel):
    """Effect on a neurotransmitter or biological system."""

    system: NeurotransmitterSystem
    mechanism: str  # Plain-language description
    direction: Direction
    magnitude: Magnitude


class NutrientDepletion(BaseModel):
    """A nutrient that this substance depletes."""

    nutrient: str
    mechanism: str
    evidence: ConfidenceTier = ConfidenceTier.PROBABLE
    clinical_significance: ClinicalSignificance = ClinicalSignificance.LOW


class NutrientRequirement(BaseModel):
    """A nutrient this substance requires or increases demand for."""

    nutrient: str
    mechanism: str
    evidence: ConfidenceTier = ConfidenceTier.ESTABLISHED


class NutrientProvision(BaseModel):
    """A nutrient or precursor this substance provides."""

    nutrient: str
    mechanism: str
    evidence: ConfidenceTier = ConfidenceTier.ESTABLISHED


class NutrientEffects(BaseModel):
    """Complete nutrient interaction profile."""

    depletions: list[NutrientDepletion] = []
    requirements: list[NutrientRequirement] = []
    provides: list[NutrientProvision] = []


class OxidativeProfile(BaseModel):
    """Oxidative stress and neuroprotective properties."""

    generates_ros: bool = False
    mechanism: str | None = None
    mitochondrial_impact: str | None = None
    neuroinflammation: str | None = None
    evidence: str | None = None


class AbsorptionInteraction(BaseModel):
    """How another substance affects this one's absorption."""

    substance_id: str  # Reference to another substance
    mechanism: str
    net_effect: AbsorptionEffect
    timing_note: str | None = None


class AbsorptionProfile(BaseModel):
    """Absorption interactions with other substances."""

    enhancers: list[AbsorptionInteraction] = []
    inhibitors: list[AbsorptionInteraction] = []


class SpacingRequirement(BaseModel):
    """A timing constraint relative to another substance or class."""

    substance_tag: str  # ID or tag of the other substance/class
    rule: SpacingRule
    reason: str


class TimingProfile(BaseModel):
    """When and how to take this substance."""

    optimal_window: str | None = None  # "morning", "midday", "evening", "pre_bed"
    take_with_food: FoodRequirement = FoodRequirement.EITHER
    latest_recommended: dict[str, str] | str | None = None
    spacing_requirements: list[SpacingRequirement] = []
    notes: str | None = None


class CommonDose(BaseModel):
    """A commonly studied or used dose."""

    dose_mg: float
    frequency: str
    evidence: str | None = None


class SafetyProfile(BaseModel):
    """Safety flags and contraindications."""

    serotonin_load: float = Field(default=0.0, ge=0.0, le=1.0)
    cardiovascular_flag: bool = False
    appetite_suppression: bool = False
    sleep_disruption: bool = False
    emotional_blunting: bool = False
    tolerance_development: bool = False
    common_doses: list[CommonDose] = []
    side_effects: list[str] = []
    contraindications: list[str] = []


class SubstanceMetadata(BaseModel):
    """Source and review tracking."""

    data_sources: list[str] = []
    last_reviewed: str | None = None
    review_status: ReviewStatus = ReviewStatus.AUTO_GENERATED
    data_tier: DataTier = DataTier.TIER_1  # Default tier_1 for existing curated substances


# === Main Model ===


class Substance(BaseModel):
    """A drug, supplement, or dietary factor with full pharmacological profile.

    This is the core data structure of Apothecary. Every feature —
    interaction checking, timing optimization, depletion tracking —
    derives from how substances are tagged here.
    """

    id: str
    name: str
    type: SubstanceType
    category: str  # Functional category (e.g. "stimulant", "ssri", "antioxidant")
    common_names: list[str] = []

    pharmacokinetics: Pharmacokinetics = Pharmacokinetics()
    metabolism: Metabolism = Metabolism()
    receptor_activity: list[ReceptorActivity] = []
    nutrient_effects: NutrientEffects = NutrientEffects()
    oxidative_profile: OxidativeProfile = OxidativeProfile()
    absorption: AbsorptionProfile = AbsorptionProfile()
    timing: TimingProfile = TimingProfile()
    safety: SafetyProfile = SafetyProfile()
    metadata: SubstanceMetadata = SubstanceMetadata()

    def has_cyp_role(self, enzyme: str, role: CYPRole) -> bool:
        """Check if this substance has a specific CYP450 relationship."""
        return any(
            entry.enzyme == enzyme and entry.role == role
            for entry in self.metabolism.cyp450
        )

    def get_cyp_enzymes(self, role: CYPRole | None = None) -> list[str]:
        """Get all CYP450 enzymes this substance interacts with, optionally filtered by role."""
        entries = self.metabolism.cyp450
        if role:
            entries = [e for e in entries if e.role == role]
        return [e.enzyme for e in entries]

    def get_systems(self) -> list[NeurotransmitterSystem]:
        """Get all neurotransmitter systems this substance affects."""
        return [r.system for r in self.receptor_activity]

    def affects_system(self, system: NeurotransmitterSystem) -> bool:
        """Check if this substance affects a given neurotransmitter system."""
        return system in self.get_systems()

    def get_depletions(self) -> list[str]:
        """Get list of nutrients this substance depletes."""
        return [d.nutrient for d in self.nutrient_effects.depletions]

    def get_provisions(self) -> list[str]:
        """Get list of nutrients/precursors this substance provides."""
        return [p.nutrient for p in self.nutrient_effects.provides]
