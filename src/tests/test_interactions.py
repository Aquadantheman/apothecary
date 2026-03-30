"""Tests for the interaction engine — validates detection accuracy.

Tests known interaction pairs (should detect) and known safe pairs
(should not false-positive), plus aggregate calculations.
"""

import pytest
from pathlib import Path

from apothecary.data.loader import SubstanceDatabase
from apothecary.engine.interaction_engine import analyze_stack
from apothecary.models.interaction import Severity, InteractionType


# === Fixtures ===

DATA_DIR = Path(__file__).parent.parent / "apothecary" / "data" / "curated"


@pytest.fixture(scope="module")
def db():
    """Load the full substance database once for all tests."""
    database = SubstanceDatabase()
    count = database.load_directory(DATA_DIR)
    assert count >= 9, f"Expected at least 9 substances, loaded {count}"
    return database


@pytest.fixture
def get_substances(db):
    """Helper to resolve a list of substance IDs into Substance objects."""
    def _get(*ids):
        substances = []
        for sid in ids:
            s = db.get(sid)
            assert s is not None, f"Substance '{sid}' not found in database"
            substances.append(s)
        return substances
    return _get


# === Database Loading Tests ===

class TestDatabaseLoading:
    def test_all_substances_loaded(self, db):
        assert db.count >= 9

    def test_substance_lookup_by_id(self, db):
        assert db.get("adderall") is not None
        assert db.get("escitalopram") is not None
        assert db.get("nac") is not None
        assert db.get("l_theanine") is not None
        assert db.get("magnesium_glycinate") is not None
        assert db.get("omega3") is not None
        assert db.get("creatine") is not None
        assert db.get("melatonin") is not None
        assert db.get("caffeine") is not None

    def test_nonexistent_substance_returns_none(self, db):
        assert db.get("doesnt_exist") is None

    def test_search_by_common_name(self, db):
        results = db.search("Lexapro")
        assert len(results) == 1
        assert results[0].id == "escitalopram"

    def test_search_by_partial_name(self, db):
        results = db.search("magnesium")
        assert len(results) >= 1
        assert any(r.id == "magnesium_glycinate" for r in results)

    def test_substance_types_correct(self, db):
        assert db.get("adderall").type.value == "prescription"
        assert db.get("nac").type.value == "supplement"
        assert db.get("caffeine").type.value == "dietary"


# === Pairwise Interaction Tests ===

class TestKnownInteractions:
    """Tests that known interactions ARE detected."""

    def test_adderall_lexapro_serotonergic_stacking(self, get_substances):
        result = analyze_stack(get_substances("adderall", "escitalopram"))
        serotonin_interactions = [
            i for i in result.interactions
            if i.type == InteractionType.RECEPTOR_STACKING
            and "serotonergic" in i.title.lower()
        ]
        assert len(serotonin_interactions) >= 1
        # Combined load should be 0.9 (0.2 + 0.7)
        assert "0.9" in serotonin_interactions[0].title

    def test_adderall_caffeine_cardiovascular(self, get_substances):
        result = analyze_stack(get_substances("adderall", "caffeine"))
        cv_interactions = [
            i for i in result.interactions
            if i.type == InteractionType.ADDITIVE_SIDE_EFFECT
            and "cardiovascular" in i.title.lower()
        ]
        assert len(cv_interactions) == 1
        assert cv_interactions[0].severity == Severity.HIGH

    def test_adderall_caffeine_sleep_disruption(self, get_substances):
        result = analyze_stack(get_substances("adderall", "caffeine"))
        sleep_interactions = [
            i for i in result.interactions
            if "sleep" in i.title.lower()
        ]
        assert len(sleep_interactions) >= 1

    def test_adderall_caffeine_appetite_suppression(self, get_substances):
        result = analyze_stack(get_substances("adderall", "caffeine"))
        appetite_interactions = [
            i for i in result.interactions
            if "appetite" in i.title.lower()
        ]
        assert len(appetite_interactions) >= 1

    def test_adderall_magnesium_absorption_flag(self, get_substances):
        result = analyze_stack(get_substances("adderall", "magnesium_glycinate"))
        absorption_interactions = [
            i for i in result.interactions
            if i.type == InteractionType.ABSORPTION
        ]
        assert len(absorption_interactions) >= 1
        # Should mention timing
        assert any(i.timing_relevant for i in absorption_interactions)

    def test_lexapro_l_theanine_serotonergic(self, get_substances):
        result = analyze_stack(get_substances("escitalopram", "l_theanine"))
        serotonin_interactions = [
            i for i in result.interactions
            if i.type == InteractionType.RECEPTOR_STACKING
            and "serotonergic" in i.title.lower()
        ]
        assert len(serotonin_interactions) >= 1
        # Combined load should be 0.8 (0.7 + 0.1)
        assert "0.8" in serotonin_interactions[0].title

    def test_l_theanine_magnesium_gabaergic_stacking(self, get_substances):
        result = analyze_stack(get_substances("l_theanine", "magnesium_glycinate"))
        gaba_interactions = [
            i for i in result.interactions
            if "gaba" in i.title.lower()
        ]
        assert len(gaba_interactions) >= 1
        assert gaba_interactions[0].severity == Severity.MODERATE


class TestBeneficialInteractions:
    """Tests that beneficial combinations ARE detected."""

    def test_nac_protects_against_adderall_oxidative_stress(self, get_substances):
        result = analyze_stack(get_substances("adderall", "nac"))
        beneficial = [
            i for i in result.interactions
            if i.type == InteractionType.BENEFICIAL
            and "oxidative" in i.title.lower()
        ]
        assert len(beneficial) == 1
        assert beneficial[0].severity == Severity.BENEFICIAL

    def test_magnesium_addresses_adderall_depletion(self, get_substances):
        result = analyze_stack(get_substances("adderall", "magnesium_glycinate"))
        beneficial = [
            i for i in result.interactions
            if i.type == InteractionType.BENEFICIAL
            and "depletion" in i.title.lower()
        ]
        assert len(beneficial) == 1

    def test_omega3_complements_adderall_dopaminergic(self, get_substances):
        result = analyze_stack(get_substances("adderall", "omega3"))
        beneficial = [
            i for i in result.interactions
            if i.type == InteractionType.BENEFICIAL
            and "dopaminergic" in i.title.lower()
        ]
        assert len(beneficial) >= 1


class TestSafePairs:
    """Tests that safe/neutral pairs do NOT produce false positives at HIGH or CRITICAL."""

    def test_creatine_lexapro_no_high_interactions(self, get_substances):
        result = analyze_stack(get_substances("creatine", "escitalopram"))
        dangerous = [
            i for i in result.interactions
            if i.severity in (Severity.CRITICAL, Severity.HIGH)
        ]
        assert len(dangerous) == 0

    def test_creatine_magnesium_no_high_interactions(self, get_substances):
        result = analyze_stack(get_substances("creatine", "magnesium_glycinate"))
        dangerous = [
            i for i in result.interactions
            if i.severity in (Severity.CRITICAL, Severity.HIGH)
        ]
        assert len(dangerous) == 0

    def test_omega3_nac_no_high_interactions(self, get_substances):
        result = analyze_stack(get_substances("omega3", "nac"))
        dangerous = [
            i for i in result.interactions
            if i.severity in (Severity.CRITICAL, Severity.HIGH)
        ]
        assert len(dangerous) == 0

    def test_creatine_omega3_no_high_interactions(self, get_substances):
        result = analyze_stack(get_substances("creatine", "omega3"))
        dangerous = [
            i for i in result.interactions
            if i.severity in (Severity.CRITICAL, Severity.HIGH)
        ]
        assert len(dangerous) == 0

    def test_melatonin_magnesium_no_high_interactions(self, get_substances):
        result = analyze_stack(get_substances("melatonin", "magnesium_glycinate"))
        dangerous = [
            i for i in result.interactions
            if i.severity in (Severity.CRITICAL, Severity.HIGH)
        ]
        assert len(dangerous) == 0


# === Aggregate / Full Stack Tests ===

class TestFullStackAnalysis:
    """Tests on Dan's 9-substance stack (not the full database)."""

    DANS_STACK = [
        "adderall", "escitalopram", "l_theanine", "nac",
        "magnesium_glycinate", "omega3", "creatine", "melatonin", "caffeine",
    ]

    @pytest.fixture
    def dans_substances(self, db):
        return [db.get(sid) for sid in self.DANS_STACK]

    def test_full_stack_runs_without_error(self, dans_substances):
        result = analyze_stack(dans_substances)
        assert result is not None

    def test_full_database_runs_without_error(self, db):
        result = analyze_stack(db.all())
        assert result is not None

    def test_aggregate_serotonin_load(self, dans_substances):
        result = analyze_stack(dans_substances)
        # Sum of all serotonin loads: 0.2 + 0.7 + 0.1 + 0.0 + 0.0 + 0.0 + 0.05 + 0.0 + 0.0 = 1.05
        assert result.aggregate_serotonin_load == pytest.approx(1.05, abs=0.01)

    def test_aggregate_cardiovascular_flags(self, dans_substances):
        result = analyze_stack(dans_substances)
        # Adderall and caffeine both have cardiovascular flags
        assert result.aggregate_cardiovascular_flags == 2

    def test_no_critical_interactions_in_dans_stack(self, dans_substances):
        """Dan's actual stack should have no CRITICAL interactions.
        Adderall + Lexapro is a common prescribed combo."""
        result = analyze_stack(dans_substances)
        assert not result.has_critical, (
            f"Unexpected CRITICAL interactions: "
            f"{[i.title for i in result.critical_interactions]}"
        )

    def test_magnesium_depletion_addressed(self, dans_substances):
        """Magnesium glycinate should address the adderall-induced depletion,
        so magnesium should NOT appear in depletion gaps."""
        result = analyze_stack(dans_substances)
        gap_nutrients = [g.nutrient for g in result.depletion_gaps]
        assert "magnesium" not in gap_nutrients

    def test_vitamin_c_depletion_still_flagged(self, dans_substances):
        """No vitamin C supplement in the stack, so it should appear as a gap."""
        result = analyze_stack(dans_substances)
        gap_nutrients = [g.nutrient for g in result.depletion_gaps]
        assert "vitamin_c" in gap_nutrients

    def test_interaction_count_reasonable(self, dans_substances):
        """With 9 substances, there are 36 possible pairs.
        We should detect a reasonable number of interactions (not 0, not 100)."""
        result = analyze_stack(dans_substances)
        assert 5 <= len(result.interactions) <= 30

    def test_has_beneficial_interactions(self, dans_substances):
        result = analyze_stack(dans_substances)
        assert len(result.beneficial_interactions) >= 2


# === Depletion Engine Tests ===

class TestDepletionDetection:
    def test_adderall_alone_flags_magnesium(self, get_substances):
        result = analyze_stack(get_substances("adderall"))
        gap_nutrients = [g.nutrient for g in result.depletion_gaps]
        assert "magnesium" in gap_nutrients

    def test_adderall_plus_magnesium_resolves_gap(self, get_substances):
        result = analyze_stack(get_substances("adderall", "magnesium_glycinate"))
        gap_nutrients = [g.nutrient for g in result.depletion_gaps]
        assert "magnesium" not in gap_nutrients

    def test_lexapro_flags_folate(self, get_substances):
        result = analyze_stack(get_substances("escitalopram"))
        gap_nutrients = [g.nutrient for g in result.depletion_gaps]
        assert "folate" in gap_nutrients

    def test_caffeine_flags_iron(self, get_substances):
        result = analyze_stack(get_substances("caffeine"))
        gap_nutrients = [g.nutrient for g in result.depletion_gaps]
        assert "iron" in gap_nutrients

    def test_depletion_suggestions_present(self, get_substances):
        result = analyze_stack(get_substances("adderall"))
        for gap in result.depletion_gaps:
            assert gap.suggestion, f"No suggestion for {gap.nutrient} depletion"
            assert len(gap.suggestion) > 10


# === Substance Model Tests ===

class TestSubstanceModel:
    def test_adderall_has_cyp2d6(self, db):
        adderall = db.get("adderall")
        assert adderall.has_cyp_role("CYP2D6", "substrate")

    def test_lexapro_has_cyp2c19(self, db):
        lexapro = db.get("escitalopram")
        assert lexapro.has_cyp_role("CYP2C19", "substrate")

    def test_nac_has_no_cyp(self, db):
        nac = db.get("nac")
        assert len(nac.get_cyp_enzymes()) == 0

    def test_adderall_affects_dopaminergic(self, db):
        from apothecary.models.substance import NeurotransmitterSystem
        adderall = db.get("adderall")
        assert adderall.affects_system(NeurotransmitterSystem.DOPAMINERGIC)

    def test_adderall_depletes_magnesium(self, db):
        adderall = db.get("adderall")
        assert "magnesium" in adderall.get_depletions()

    def test_magnesium_provides_magnesium(self, db):
        mag = db.get("magnesium_glycinate")
        provisions = mag.get_provisions()
        assert any("magnesium" in p for p in provisions)

    def test_serotonin_loads_reasonable(self, db):
        """All serotonin loads should be between 0 and 1."""
        for s in db.all():
            assert 0.0 <= s.safety.serotonin_load <= 1.0, (
                f"{s.id} has invalid serotonin_load: {s.safety.serotonin_load}"
            )


# === New Substance Interaction Tests ===

class TestExpandedInteractions:
    """Tests for interactions involving newly added substances."""

    def test_5htp_lexapro_critical(self, get_substances):
        """5-HTP + SSRI should trigger CRITICAL serotonin syndrome warning."""
        result = analyze_stack(get_substances("5_htp", "escitalopram"))
        critical = [i for i in result.interactions if i.severity == Severity.CRITICAL]
        assert len(critical) >= 1, "5-HTP + SSRI should be CRITICAL"

    def test_5htp_sertraline_critical(self, get_substances):
        result = analyze_stack(get_substances("5_htp", "sertraline"))
        critical = [i for i in result.interactions if i.severity == Severity.CRITICAL]
        assert len(critical) >= 1, "5-HTP + Zoloft should be CRITICAL"

    def test_5htp_venlafaxine_critical(self, get_substances):
        result = analyze_stack(get_substances("5_htp", "venlafaxine"))
        critical = [i for i in result.interactions if i.severity == Severity.CRITICAL]
        assert len(critical) >= 1, "5-HTP + SNRI should be CRITICAL"

    def test_bupropion_adderall_cyp2d6(self, get_substances):
        """Bupropion inhibits CYP2D6; Adderall is a CYP2D6 substrate."""
        result = analyze_stack(get_substances("bupropion", "adderall"))
        cyp_interactions = [
            i for i in result.interactions
            if i.type == InteractionType.CYP450
        ]
        assert len(cyp_interactions) >= 1, "Bupropion should flag CYP2D6 interaction with Adderall"

    def test_cbd_lexapro_cyp2c19(self, get_substances):
        """CBD inhibits CYP2C19; Lexapro is a CYP2C19 substrate."""
        result = analyze_stack(get_substances("cbd", "escitalopram"))
        cyp_interactions = [
            i for i in result.interactions
            if i.type == InteractionType.CYP450 and "CYP2C19" in (i.pathway or "")
        ]
        assert len(cyp_interactions) >= 1, "CBD should flag CYP2C19 interaction with Lexapro"

    def test_cbd_alprazolam_cyp3a4(self, get_substances):
        """CBD inhibits CYP3A4; Alprazolam is a CYP3A4 substrate."""
        result = analyze_stack(get_substances("cbd", "alprazolam"))
        cyp_interactions = [
            i for i in result.interactions
            if i.type == InteractionType.CYP450
        ]
        assert len(cyp_interactions) >= 1, "CBD should flag CYP3A4 interaction with Xanax"

    def test_st_johns_wort_lexapro_serotonin(self, get_substances):
        """St. John's Wort + SSRI = high serotonergic stacking."""
        result = analyze_stack(get_substances("st_johns_wort", "escitalopram"))
        serotonin = [
            i for i in result.interactions
            if "serotonergic" in i.title.lower()
            and i.severity in (Severity.HIGH, Severity.MODERATE)
        ]
        assert len(serotonin) >= 1

    def test_st_johns_wort_alprazolam_cyp3a4_induction(self, get_substances):
        """SJW induces CYP3A4; alprazolam is a CYP3A4 substrate — reduced efficacy."""
        result = analyze_stack(get_substances("st_johns_wort", "alprazolam"))
        cyp_interactions = [
            i for i in result.interactions
            if i.type == InteractionType.CYP450
        ]
        assert len(cyp_interactions) >= 1, "SJW should flag CYP3A4 induction reducing Xanax levels"

    def test_statin_coq10_depletion_addressed(self, get_substances):
        """Atorvastatin depletes CoQ10; CoQ10 supplement should resolve the gap."""
        result = analyze_stack(get_substances("atorvastatin", "coq10"))
        gap_nutrients = [g.nutrient for g in result.depletion_gaps]
        assert "coq10" not in gap_nutrients

    def test_statin_without_coq10_flags_gap(self, get_substances):
        """Atorvastatin alone should flag CoQ10 depletion."""
        result = analyze_stack(get_substances("atorvastatin"))
        gap_nutrients = [g.nutrient for g in result.depletion_gaps]
        assert "coq10" in gap_nutrients

    def test_metformin_flags_b12_depletion(self, get_substances):
        result = analyze_stack(get_substances("metformin"))
        gap_nutrients = [g.nutrient for g in result.depletion_gaps]
        assert "vitamin_b12" in gap_nutrients

    def test_omeprazole_flags_magnesium_depletion(self, get_substances):
        result = analyze_stack(get_substances("omeprazole"))
        gap_nutrients = [g.nutrient for g in result.depletion_gaps]
        assert "magnesium" in gap_nutrients
