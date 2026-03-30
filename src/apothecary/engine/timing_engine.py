"""Timing engine — generates an optimized daily schedule for a substance stack.

Takes substance profiles with their pharmacokinetic data, spacing requirements,
and optimal windows, and produces a daily timeline organized into waves.
"""

from dataclasses import dataclass, field

from apothecary.models.substance import Substance, FoodRequirement


@dataclass
class ScheduledDose:
    """A single substance placed at a specific time."""

    substance_id: str
    substance_name: str
    time_block: str  # wake, mid_morning, midday, afternoon, evening, pre_bed
    rationale: str
    food_note: str | None = None


@dataclass
class TimeBlock:
    """A block of time in the daily schedule."""

    name: str
    label: str
    relative_hours: float  # Hours after wake time
    clock_time: str  # Computed from wake time
    doses: list[ScheduledDose] = field(default_factory=list)
    meal_note: str | None = None


@dataclass
class DailyTimeline:
    """Complete daily schedule output."""

    wake_time: str
    sleep_target: str
    blocks: list[TimeBlock]
    notes: list[str] = field(default_factory=list)

    @property
    def active_blocks(self) -> list[TimeBlock]:
        """Only blocks that have doses assigned."""
        return [b for b in self.blocks if b.doses]


# Time block definitions with hours relative to wake time
BLOCK_DEFINITIONS = [
    ("wake", "Morning (Wake)", 0.0),
    ("mid_morning", "Mid-Morning", 2.5),
    ("midday", "Midday", 5.5),
    ("afternoon", "Afternoon", 8.0),
    ("evening", "Evening / Dinner", 11.0),
    ("pre_bed", "Pre-Bed", 14.5),
]

# Mapping from substance timing.optimal_window to block name
WINDOW_TO_BLOCK = {
    "morning": "wake",
    "mid_morning": "mid_morning",
    "midday": "midday",
    "afternoon": "afternoon",
    "evening": "evening",
    "pre_bed": "pre_bed",
    "bedtime": "pre_bed",
}

# Substances that should be co-administered with stimulants
STIMULANT_SYNERGIES = {"l_theanine"}

# Categories that count as "stimulant" for spacing rules
STIMULANT_CATEGORIES = {"stimulant"}


def _compute_clock_time(wake_time: str, offset_hours: float) -> str:
    """Compute a clock time from wake time + offset hours."""
    parts = wake_time.split(":")
    wake_hour = int(parts[0])
    wake_min = int(parts[1])
    total_minutes = wake_hour * 60 + wake_min + int(offset_hours * 60)
    hour = (total_minutes // 60) % 24
    minute = total_minutes % 60
    return f"{hour:02d}:{minute:02d}"


def _get_food_note(substance: Substance) -> str | None:
    """Generate a food-related note for a substance."""
    if substance.timing.take_with_food == FoodRequirement.REQUIRED:
        return f"Take {substance.name} with a meal containing fat for absorption"
    if substance.timing.take_with_food == FoodRequirement.EMPTY_STOMACH:
        return f"Take {substance.name} on an empty stomach"
    return None


def _determine_block(substance: Substance, has_stimulant: bool) -> tuple[str, str]:
    """Determine which time block a substance belongs in, with rationale."""

    sid = substance.id
    window = substance.timing.optimal_window

    # Stimulant synergies go with the stimulant (morning)
    if sid in STIMULANT_SYNERGIES and has_stimulant:
        return "wake", (
            f"Co-administer with stimulant — {substance.name} modulates "
            f"stimulant effects for smoother focus and reduced rigidity"
        )

    # Check spacing requirements — adjust block based on separation needed from stimulant
    for spacing in substance.timing.spacing_requirements:
        if spacing.substance_tag in STIMULANT_CATEGORIES or spacing.substance_tag == "stimulant":
            if spacing.rule.value == "separate_8h":
                return "evening", (
                    f"{spacing.reason}. "
                    f"Evening timing provides 8+ hour separation from morning stimulant."
                )
            if spacing.rule.value == "separate_4h":
                # 4h separation = midday is sufficient (5.5h after wake)
                target_block = "midday"
                if window and window in WINDOW_TO_BLOCK:
                    target_block = WINDOW_TO_BLOCK[window]
                return target_block, (
                    f"{spacing.reason}. "
                    f"Midday timing provides 4+ hour separation from morning stimulant "
                    f"and aligns with peak oxidative stress window."
                )

    # Use the substance's declared optimal window
    if window and window in WINDOW_TO_BLOCK:
        block = WINDOW_TO_BLOCK[window]
        rationale = substance.timing.notes or f"Optimal timing: {window}"
        return block, rationale

    # Default: morning for most things
    return "wake", "Default timing — morning for consistency"


def _generate_meal_notes(block_name: str, substances: list[Substance]) -> str | None:
    """Generate meal/food notes for a time block based on what's being taken."""

    if block_name == "wake":
        has_stimulant = any(s.category in STIMULANT_CATEGORIES for s in substances)
        needs_fat = any(s.timing.take_with_food == FoodRequirement.REQUIRED for s in substances)
        parts = []
        if has_stimulant:
            parts.append(
                "Protein-forward breakfast (eggs, meat) — provides tyrosine "
                "for dopamine synthesis during stimulant activity"
            )
        if needs_fat:
            parts.append("Include dietary fat for omega-3 absorption")
        return ". ".join(parts) if parts else None

    if block_name == "midday":
        return "Blueberries or dark berries — anthocyanins provide additional antioxidant support during peak dopamine metabolism"

    if block_name == "evening":
        return (
            "Strategic carb portion on stimulant days (sweet potato, rice, squash) — "
            "insulin response promotes tryptophan transport across blood-brain barrier "
            "for serotonin/melatonin synthesis"
        )

    return None


def generate_timeline(
    substances: list[Substance],
    wake_time: str = "07:00",
    sleep_target: str = "23:00",
) -> DailyTimeline:
    """Generate an optimized daily timeline for a list of substances.

    This is the main entry point for the timing engine.
    """

    has_stimulant = any(s.category in STIMULANT_CATEGORIES for s in substances)

    # Create time blocks
    blocks: dict[str, TimeBlock] = {}
    for name, label, offset in BLOCK_DEFINITIONS:
        clock = _compute_clock_time(wake_time, offset)
        blocks[name] = TimeBlock(
            name=name,
            label=label,
            relative_hours=offset,
            clock_time=clock,
        )

    # Assign each substance to a block
    block_substances: dict[str, list[Substance]] = {name: [] for name, _, _ in BLOCK_DEFINITIONS}

    for substance in substances:
        block_name, rationale = _determine_block(substance, has_stimulant)
        food_note = _get_food_note(substance)

        dose = ScheduledDose(
            substance_id=substance.id,
            substance_name=substance.name,
            time_block=block_name,
            rationale=rationale,
            food_note=food_note,
        )
        blocks[block_name].doses.append(dose)
        block_substances[block_name].append(substance)

    # Generate meal notes per block
    for block_name, block in blocks.items():
        if block.doses:
            block.meal_note = _generate_meal_notes(
                block_name, block_substances[block_name]
            )

    # Generate global notes
    notes = []
    if has_stimulant:
        notes.append(
            "Hydration: Drink extra water throughout the day. "
            "Stimulants are dehydrating and dehydration worsens magnesium loss."
        )
        caffeine_present = any(s.id == "caffeine" for s in substances)
        if caffeine_present:
            notes.append(
                "Caffeine: Limit intake on stimulant days. "
                "Both caffeine and stimulants increase norepinephrine, compounding sleep disruption."
            )
        notes.append(
            "Warm shower 30-60 min before bed — thermoregulatory temperature drop promotes sleep onset."
        )

    # Build ordered block list
    ordered_blocks = [blocks[name] for name, _, _ in BLOCK_DEFINITIONS]

    return DailyTimeline(
        wake_time=wake_time,
        sleep_target=sleep_target,
        blocks=ordered_blocks,
        notes=notes,
    )
