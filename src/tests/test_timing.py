"""Tests for the timing engine — validates schedule generation."""

import pytest
from pathlib import Path

from apothecary.data.loader import SubstanceDatabase
from apothecary.engine.timing_engine import generate_timeline


DATA_DIR = Path(__file__).parent.parent / "apothecary" / "data" / "curated"


@pytest.fixture(scope="module")
def db():
    database = SubstanceDatabase()
    database.load_directory(DATA_DIR)
    return database


@pytest.fixture
def full_stack(db):
    return db.all()


@pytest.fixture
def get_substances(db):
    def _get(*ids):
        return [db.get(sid) for sid in ids]
    return _get


class TestTimelineGeneration:
    def test_timeline_generates_without_error(self, full_stack):
        tl = generate_timeline(full_stack)
        assert tl is not None

    def test_timeline_has_correct_wake_time(self, full_stack):
        tl = generate_timeline(full_stack, wake_time="08:00")
        assert tl.wake_time == "08:00"

    def test_timeline_has_active_blocks(self, full_stack):
        tl = generate_timeline(full_stack)
        assert len(tl.active_blocks) >= 3  # At least morning, midday/evening, pre-bed

    def test_custom_wake_time_shifts_blocks(self, full_stack):
        tl = generate_timeline(full_stack, wake_time="09:00")
        morning_block = next(b for b in tl.blocks if b.name == "wake")
        assert morning_block.clock_time == "09:00"


class TestSubstancePlacement:
    def test_adderall_in_morning(self, get_substances):
        tl = generate_timeline(get_substances("adderall"))
        morning_ids = [d.substance_id for b in tl.blocks if b.name == "wake" for d in b.doses]
        assert "adderall" in morning_ids

    def test_lexapro_in_morning(self, get_substances):
        tl = generate_timeline(get_substances("escitalopram"))
        morning_ids = [d.substance_id for b in tl.blocks if b.name == "wake" for d in b.doses]
        assert "escitalopram" in morning_ids

    def test_l_theanine_colocated_with_stimulant(self, get_substances):
        """L-theanine should be in the morning block when a stimulant is present."""
        tl = generate_timeline(get_substances("adderall", "l_theanine"))
        morning_ids = [d.substance_id for b in tl.blocks if b.name == "wake" for d in b.doses]
        assert "l_theanine" in morning_ids

    def test_nac_in_midday(self, get_substances):
        """NAC should be midday — 4h separation from morning stimulant."""
        tl = generate_timeline(get_substances("adderall", "nac"))
        midday_ids = [d.substance_id for b in tl.blocks if b.name == "midday" for d in b.doses]
        assert "nac" in midday_ids

    def test_magnesium_in_evening(self, get_substances):
        """Magnesium should be evening — 8h separation from stimulant."""
        tl = generate_timeline(get_substances("adderall", "magnesium_glycinate"))
        evening_ids = [d.substance_id for b in tl.blocks if b.name == "evening" for d in b.doses]
        assert "magnesium_glycinate" in evening_ids

    def test_melatonin_pre_bed(self, get_substances):
        tl = generate_timeline(get_substances("melatonin"))
        pre_bed_ids = [d.substance_id for b in tl.blocks if b.name == "pre_bed" for d in b.doses]
        assert "melatonin" in pre_bed_ids

    def test_creatine_in_morning(self, get_substances):
        tl = generate_timeline(get_substances("creatine"))
        morning_ids = [d.substance_id for b in tl.blocks if b.name == "wake" for d in b.doses]
        assert "creatine" in morning_ids

    def test_omega3_in_morning(self, get_substances):
        tl = generate_timeline(get_substances("omega3"))
        morning_ids = [d.substance_id for b in tl.blocks if b.name == "wake" for d in b.doses]
        assert "omega3" in morning_ids


class TestFullProtocol:
    """Test that the full 9-substance stack produces the expected 4-wave protocol."""

    def test_four_active_blocks(self, full_stack):
        tl = generate_timeline(full_stack)
        assert len(tl.active_blocks) == 4  # morning, midday, evening, pre-bed

    def test_morning_wave_contents(self, full_stack):
        tl = generate_timeline(full_stack)
        morning = next(b for b in tl.blocks if b.name == "wake")
        morning_ids = {d.substance_id for d in morning.doses}
        assert "adderall" in morning_ids
        assert "escitalopram" in morning_ids
        assert "l_theanine" in morning_ids
        assert "omega3" in morning_ids
        assert "creatine" in morning_ids
        assert "caffeine" in morning_ids

    def test_midday_wave_contents(self, full_stack):
        tl = generate_timeline(full_stack)
        midday = next(b for b in tl.blocks if b.name == "midday")
        midday_ids = {d.substance_id for d in midday.doses}
        assert "nac" in midday_ids

    def test_evening_wave_contents(self, full_stack):
        tl = generate_timeline(full_stack)
        evening = next(b for b in tl.blocks if b.name == "evening")
        evening_ids = {d.substance_id for d in evening.doses}
        assert "magnesium_glycinate" in evening_ids

    def test_pre_bed_wave_contents(self, full_stack):
        tl = generate_timeline(full_stack)
        pre_bed = next(b for b in tl.blocks if b.name == "pre_bed")
        pre_bed_ids = {d.substance_id for d in pre_bed.doses}
        assert "melatonin" in pre_bed_ids

    def test_meal_notes_present(self, full_stack):
        tl = generate_timeline(full_stack)
        morning = next(b for b in tl.blocks if b.name == "wake")
        assert morning.meal_note is not None
        assert "protein" in morning.meal_note.lower() or "tyrosine" in morning.meal_note.lower()

    def test_hydration_note_present(self, full_stack):
        tl = generate_timeline(full_stack)
        assert any("hydration" in n.lower() for n in tl.notes)

    def test_all_substances_placed(self, full_stack):
        """Every substance in the stack should appear in exactly one block."""
        tl = generate_timeline(full_stack)
        all_placed = set()
        for block in tl.blocks:
            for dose in block.doses:
                all_placed.add(dose.substance_id)
        input_ids = {s.id for s in full_stack}
        assert all_placed == input_ids, f"Missing: {input_ids - all_placed}, Extra: {all_placed - input_ids}"
